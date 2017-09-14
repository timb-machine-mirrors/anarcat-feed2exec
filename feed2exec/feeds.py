#!/usr/bin/python3
# coding: utf-8

'''fast feed parser that offloads tasks to plugins and commands'''
# Copyright (C) 2016 Antoine Beaupré <anarcat@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, absolute_import
from __future__ import print_function


try:
    import configparser
except ImportError:  # pragma: nocover
    # py2: should never happen as we depend on the newer one in setup.py
    import ConfigParser as configparser
from collections import OrderedDict, namedtuple
import logging
import multiprocessing
import os
import os.path
try:
    import urllib.parse as urlparse
except ImportError:  # pragma: nocover
    # py2
    import urlparse


import feed2exec
import feed2exec.plugins as plugins
import feed2exec.utils as utils
import feedparser
import requests
import sqlite3


def default_config_dir():
    home_config = os.environ.get('XDG_CONFIG_HOME',
                                 os.path.join(os.environ.get('HOME'),
                                              '.config'))
    return os.path.join(home_config, feed2exec.__prog__)


def fetch(url):
    """fetch the given URL

    exceptions should be handled by the caller

    :todo: this should be moved to a plugin so it can be overridden,
           but so far I haven't found a use case for this.

    :param str url: the URL to fetch

    :return bytes, tuple: the body of the URL and the modification timestamp

    """
    body = ''
    if url.startswith('file://'):
        filename = url[len('file://'):]
        logging.info('opening local file %s', filename)
        with open(filename, 'rb') as f:
            body = f.read().decode('utf-8')
    else:
        logging.info('fetching URL %s', url)
        body = requests.get(url).text
    return body


def normalize_entry(feed=None, entry=None):
    """normalize feeds a little more than what feedparser provides.

    we do the following operation:

     1. add more defaults to entry dates (`issue #113
        <https://github.com/kurtmckee/feedparser/issues/113>`_):

        * created_parsed of the item
        * updated_parsed of the feed

     2. missing GUID in some feeds (`issue #112
        <https://github.com/kurtmckee/feedparser/issues/112>`_)

     3. link normalization fails on some feeds, particilarly GitHub,
        where feeds are /foo instead of https://github.com/foo.
        unreported for now.
    """
    # 1. add more defaults (issue #113)
    entry['updated_parsed'] = entry.get('updated_parsed', entry.get('created_parsed', feed.get('updated_parsed', False)))  # noqa
    assert entry.get('updated_parsed') is not None

    # 2. add UID if missing (issue #112)
    if not entry.get('id'):
        entry['id'] = entry.get('title')

    # 3. not completely absolute links
    scheme, netloc, *rest = urlparse.urlsplit(entry.get('link'))
    if not scheme:
        # take missing scheme/host from feed URL
        scheme, netloc, *_ = urlparse.urlsplit(feed.get('url', ''))
        entry['link'] = urlparse.urlunsplit((scheme, netloc, *rest))


def parse(body, feed, lock=None, force=False):

    """parse the body of the feed

    this calls the filter and output plugins and updates the cache
    with the found items.

    :todo: this could be moved to a plugin, but then we'd need to take
           out the cache checking logic, which would remove most of
           the code here...

    :param bytes body: the body of the feed, as returned by :func:fetch

    :param dict feed: a feed object used to pass to plugins and debugging

    :return dict: the parsed data

    """
    global LOCK
    if lock is None:
        lock = LOCK
    logging.info('parsing feed %s (%d bytes)', feed['url'], len(body))
    data = feedparser.parse(body)
    # logging.debug('parsed structure %s',
    #               json.dumps(data, indent=2, sort_keys=True,
    #                          default=safe_serial))
    cache = FeedCacheStorage(feed=feed['name'])
    for entry in data['entries']:
        params = feed.copy()
        params.update(data['feed'])
        normalize_entry(feed=params, entry=entry)
        plugins.filter(feed, entry, lock=lock)
        guid = entry['id']
        if guid in cache and not force:
            logging.debug('entry %s already seen', guid)
        else:
            logging.debug('new entry %s <%s>', guid, entry['link'])
            if plugins.output(feed, entry, lock=lock) is not None and not force:  # noqa
                cache.add(guid)
    return data


def _init_lock(l):
    """setup a global lock across pool threads

    this is necessary because Lock objects are not serializable so we
    can't pass them as arguments. An alternative pattern is to have a
    `Manager` process and use IPC for locking.

    cargo-culted from this `stackoverflow answer
    <https://stackoverflow.com/a/25558333/1174784>`_

    """
    global LOCK
    LOCK = l


def fetch_feeds(pattern=None, parallel=False, force=False, catchup=False):
    logging.debug('looking for feeds %s', pattern)
    st = FeedStorage(pattern=pattern)
    if parallel:
        l = multiprocessing.Lock()
        processes = None
        if isinstance(parallel, int):
            processes = parallel
        pool = multiprocessing.Pool(processes=processes,
                                    initializer=_init_lock, initargs=(l,))
    results = []
    for i, feed in enumerate(st):
        logging.debug('found feed in DB: %s', dict(feed))
        if feed.get('pause'):
            logging.info('feed %s is paused, skipping', feed['name'])
            continue
        body = fetch(feed['url'])
        if catchup or feed.get('catchup'):
            logging.info('catching up on feed %s (output plugin disabled)',
                         feed['name'])
            feed['output'] = None
        if parallel:
            # if this fails silently, use plain apply() to see errors
            results.append(pool.apply_async(parse,
                                            (body, dict(feed), None, force)))
        else:
            global LOCK
            LOCK = None
            parse(body=body, feed=dict(feed), force=force)
    if parallel:
        for result in results:
            result.get()
        pool.close()
        pool.join()
    logging.info('%d feeds processed', i+1)


class SqliteStorage(object):
    sql = None
    record = None
    conn = None
    path = None
    cache = {}

    def __init__(self):
        assert self.path
        utils.make_dirs_helper(os.path.dirname(self.path))
        if self.path not in SqliteStorage.cache:
            logging.info('connecting to database at %s', self.path)
            conn = sqlite3.connect(self.path)
            try:
                conn.set_trace_callback(logging.debug)
            except AttributeError:  # pragma: nocover
                logging.debug('no logging support in sqlite')
            SqliteStorage.cache[self.path] = conn
        self.conn = SqliteStorage.cache[self.path]
        if self.sql:
            self.conn.execute(self.sql)
            self.conn.commit()


class ConfFeedStorage(configparser.RawConfigParser):
    path = os.path.join(default_config_dir(), 'feed2exec.ini')

    def __init__(self, pattern=None):
        self.pattern = pattern
        super(ConfFeedStorage,
              self).__init__(dict_type=OrderedDict)
        self.read(self.path)

    def add(self, name, url, output=None, args=None, filter=None,
            folder=None, mailbox=None):
        if self.has_section(name):
            raise AttributeError('key %s already exists' % name)
        d = OrderedDict()
        d['url'] = url
        if output is not None:
            d['output'] = output
        if args is not None:
            d['args'] = args
        if filter is not None:
            d['filter'] = filter
        if folder is not None:
            d['folder'] = folder
        if mailbox is not None:
            d['mailbox'] = mailbox
        self[name] = d
        self.commit()

    def set(self, section, option, value=None):
        super(ConfFeedStorage, self).set(section, option, value)
        self.commit()

    def remove_option(self, section, option):
        super(ConfFeedStorage, self).remove_option(section, option)
        self.commit()

    def remove(self, name):
        self.remove_section(name)
        self.commit()

    def commit(self):
        logging.info('saving feed configuration in %s', self.path)
        utils.make_dirs_helper(os.path.dirname(self.path))
        with open(self.path, 'w') as configfile:
            self.write(configfile)

    def __iter__(self):
        for name in self.sections():
            if self.pattern is None or self.pattern in name:
                d = dict(self[name])
                d.update({'name': name})
                yield d


FeedStorage = ConfFeedStorage


class FeedCacheStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             feedcache (name text, guid text,
             PRIMARY KEY (name, guid))'''
    record = namedtuple('record', 'name guid')

    def __init__(self, feed=None, guid=None):
        self.feed = feed
        if guid is None:
            self.guid = '%'
        else:
            self.guid = '%' + guid + '%'
        super(FeedCacheStorage, self).__init__()

    def add(self, guid):
        assert self.feed
        self.conn.execute("INSERT INTO feedcache VALUES (?, ?)",
                          (self.feed, guid))
        self.conn.commit()

    def remove(self, guid):
        assert self.feed
        self.conn.execute("DELETE FROM feedcache WHERE guid = ?", (guid,))
        self.conn.commit()

    def __contains__(self, guid):
        if self.feed is None:
            pattern = '%'
        else:
            pattern = self.feed
        cur = self.conn.execute("""SELECT * FROM feedcache
                                WHERE name LIKE ? AND guid=?""",
                                (pattern, guid))
        return cur.fetchone() is not None

    def __iter__(self):
        if self.feed is None:
            pattern = '%'
        else:
            pattern = self.feed
        cur = self.conn.cursor()
        cur.row_factory = sqlite3.Row
        return cur.execute("""SELECT * from feedcache
                              WHERE name LIKE ? AND guid LIKE ?""",
                           (pattern, self.guid))
