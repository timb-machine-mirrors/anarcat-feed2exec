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


import datetime
import time
import collections
import errno
import json
import logging
import multiprocessing
import os
import os.path


import feed2exec
from feed2exec.plugins import plugin_output
import feedparser
import requests
import sqlite3


def default_config_dir():
    home_config = os.environ.get('XDG_CONFIG_HOME',
                                 os.path.join(os.environ.get('HOME'),
                                              '.config'))
    return os.path.join(home_config, feed2exec.__prog__)


def default_db():
    return os.path.join(default_config_dir(), 'feed2exec.sqlite')


def make_dirs_helper(path):
    """Create the directory if it does not exist

    Return True if the directory was created, false if it was already
    present, throw an OSError exception if it cannot be created"""
    try:
        os.makedirs(path)
        return True
    except OSError as ex:
        if ex.errno != errno.EEXIST or not os.path.isdir(path):
            raise
        return False


def fetch(url):
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


def parse(body, feed):
    logging.info('parsing feed %s (%d bytes)', feed['url'], len(body))
    data = feedparser.parse(body)
    logging.debug('parsed structure %s',
                  json.dumps(data, indent=2, sort_keys=True,
                             default=safe_serial))
    cache = FeedCacheStorage(feed=feed['name'])
    for entry in data['entries']:
        # workaround feedparser bug:
        # https://github.com/kurtmckee/feedparser/issues/112
        guid = entry.get('id', entry.get('title'))
        if guid in cache:
            logging.info('entry %s already seen', guid)
        else:
            logging.info('new entry %s <%s>', guid, entry['link'])
            if feed['plugin'] is not None:
                if plugin_output(feed=feed, item=entry, lock=LOCK) is not None:
                    cache.add(guid)
            else:
                cache.add(guid)


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


def fetch_feeds(pattern=None):
    logging.debug('looking for feeds %s', pattern)
    st = FeedStorage(pattern=pattern)
    l = multiprocessing.Lock()
    pool = multiprocessing.Pool(initializer=_init_lock, initargs=(l,))
    for feed in st:
        logging.info('found feed in DB: %s', dict(feed))
        body = fetch(feed['url'])
        # if this fails silently, try to remove the `_async` bit to see errors
        pool.apply_async(parse, (body, dict(feed)))
    pool.close()
    pool.join()


def safe_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    elif isinstance(obj, time.struct_time):
        return time.strftime('%c')
    else:
        return str(obj)


class SqliteStorage(object):
    sql = None
    record = None
    conn = None

    def __init__(self, path=None):
        if path is None:
            path = default_db()
        make_dirs_helper(os.path.dirname(path))
        if SqliteStorage.conn is None:
            logging.debug('connecting to database at %s', path)
            SqliteStorage.conn = sqlite3.connect(path)
            try:
                SqliteStorage.conn.set_trace_callback(logging.debug)
            except AttributeError:
                logging.debug('no logging support in sqlite')
        if self.sql is not None:
            SqliteStorage.conn.execute(self.sql)
            SqliteStorage.conn.commit()


class FeedStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             feeds (name text, url text, plugin text, args text,
             PRIMARY KEY (name))'''
    record = collections.namedtuple('record', 'name url plugin args')

    def __init__(self, path=None, pattern=None):
        if pattern is None:
            self.pattern = '%'
        else:
            self.pattern = '%' + pattern + '%'
        super(FeedStorage, self).__init__(path)

    def add(self, name, url, plugin=None, args=None):
        self.conn.execute("INSERT INTO feeds VALUES (?, ?, ?, ?)",
                          (name, url, plugin, args))
        self.conn.commit()  # XXX

    def remove(self, name):
        self.conn.execute("DELETE FROM feeds WHERE name=?", (name, ))
        self.conn.commit()  # XXX

    def __contains__(self, name):
        cur = self.conn.execute("SELECT * FROM feeds WHERE name=?", (name,))
        return cur.fetchone() is not None

    def __iter__(self):
        cur = self.conn.cursor()
        cur.row_factory = sqlite3.Row
        return cur.execute("""SELECT * from feeds WHERE name
                              LIKE ? OR url LIKE ?""",
                           (self.pattern, self.pattern))


class FeedCacheStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             feedcache (name text, guid text,
             PRIMARY KEY (name, guid))'''
    record = collections.namedtuple('record', 'name guid')

    def __init__(self, feed=None, path=None, guid=None):
        self.feed = feed
        if guid is None:
            self.guid = '%'
        else:
            self.guid = '%' + guid + '%'
        super(FeedCacheStorage, self).__init__(path)

    def add(self, guid):
        assert self.feed is not None
        self.conn.execute("INSERT INTO feedcache VALUES (?, ?)",
                          (self.feed, guid))
        self.conn.commit()

    def remove(self, guid):
        assert self.feed is not None
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
