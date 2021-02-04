# coding: utf-8

'''data structures and storage for feed2exec'''

# Copyright (C) 2019 Antoine Beaupré <anarcat@debian.org>
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
from contextlib import contextmanager
from datetime import datetime
import logging
import os.path
from threading import Lock
try:
    import urllib.parse as urlparse
except ImportError:  # pragma: nocover
    # py2
    import urlparse
import warnings

import feed2exec
import feed2exec.utils as utils

import feedparser
import sqlite3
import xdg.BaseDirectory as xdg_base_dirs


class Feed(feedparser.FeedParserDict):
    """basic data structure representing a RSS or Atom feed.

    it derives from the base :class:`feedparser.FeedParserDict` but
    forces the element to have a ``name``, which is the unique name
    for that feed in the :class:`feed2exec.controller.FeedManager`. We also
    add convenience functions to parse (in parallel) and normalize
    feed items.

    For all intents and purposes, this can be considered like a dict()
    unless otherwise noted.
    """
    locked_keys = ('output', 'args', 'filter', 'filter_args',
                   'folder', 'mailbox', 'url', 'name', 'pause', 'catchup')

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['name'] = name

    def normalize(self, item=None):
        """normalize feeds a little more than what feedparser provides.

        we do the following operation:

         1. add more defaults to item dates (`issue #113
            <https://github.com/kurtmckee/feedparser/issues/113>`_)

         2. missing GUID in some feeds (`issue #112
            <https://github.com/kurtmckee/feedparser/issues/112>`_)

         3. link normalization fails on some feeds, particilarly GitHub,
            where feeds are /foo instead of https://github.com/foo.
            unreported for now.
        """

        # 1. add more defaults (issue #113)
        def pick_first_date():
            """find a valid date in item or feed"""
            fields = ('updated_parsed', 'published_parsed', 'created_parsed')
            # first check the item itself, then fallback on the field
            for scope in (item, self):
                # all the fields to inspect
                for field in fields:
                    if scope.get(field, False):
                        logging.debug('picked field %s for item %s: %s',
                                      field, item.get('id'), scope.get(field))
                        return scope.get(field)

        # ignore deprecation warnings from feedparser:
        # https://github.com/kurtmckee/feedparser/issues/151
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            item['updated_parsed'] = pick_first_date()

        if not item.get('updated_parsed'):
            logging.info('no parseable date found in feed item %s from feed %s, using current time instead',
                         item.get('id'), self.get('url'))
            item['updated_parsed'] = datetime.utcnow().timestamp()

        # 2. add UID if missing (issue #112)
        if not item.get('id'):
            item['id'] = item.get('title')

        # 3. not completely absolute links
        scheme, netloc, *rest = urlparse.urlsplit(item.get('link', ''))
        if not scheme:
            # take missing scheme/host from feed URL
            scheme, netloc, *_ = urlparse.urlsplit(self.get('url', ''))
            item['link'] = urlparse.urlunsplit((scheme, netloc, *rest))

    def parse(self, body):
        """parse the body of the feed

        this parses the given body using :mod:`feedparser` and returns
        the parsed data.

        :todo: this could be moved to a plugin, but then we'd need to take
               out the cache checking logic, which would remove most of
               the code here...

        :param bytes body: the body of the feed, as returned by :func:fetch

        :param dict self: a feed object used to pass to plugins and debugging

        :return dict: the parsed data

        """
        logging.info('parsing feed %s (%d bytes)', self['url'], len(body))
        try:
            data = feedparser.parse(body)
        except Exception as e:
            logging.warning('feedparser failed: either a bug or a malformed feed: %s (feed skipped)', e)
            return None
        # add metadata from the feed without overriding user config
        for (key, val) in data['feed'].items():
            if key not in self and key not in Feed.locked_keys:
                self[key] = val
        # import json
        # logging.debug('parsed structure %s',
        #               json.dumps(data, indent=2, sort_keys=True,
        #                          default=str))
        # massage result for multiprocessing module
        if data['bozo']:
            data['bozo_exception'] = str(data['bozo_exception'])
        return data


class FeedConfStorage(configparser.RawConfigParser):
    """Feed configuration stored in a config file.

    This derives from :class:`configparser.RawConfigParser` and uses
    the ``.ini`` file set in the ``path`` member to read and write
    settings.

    Changes are committed immediately, and no locking is performed so
    loading here should be safe but not editing.

    The particular thing about this configuration is that there is an
    iterator that will yield entries matching the ``pattern``
    substring provided in the constructor.
    """

    def __init__(self, path, pattern=None):
        if path is None:
            path = self.guess_path()
        self.path = os.path.expanduser(path)
        self.pattern = pattern
        super(FeedConfStorage,
              self).__init__(dict_type=OrderedDict)
        self.read(self.path)

    def __repr__(self):
        return 'FeedConfStorage(%s, %s)' % (self.path, self.pattern)

    @classmethod
    def guess_path(cls):
        return xdg_base_dirs.load_first_config(feed2exec.__prog__ + '.ini') or \
            os.path.join(xdg_base_dirs.xdg_config_home, feed2exec.__prog__ + '.ini')

    def add(self, name, url, output=None, args=None,
            filter=None, filter_args=None,
            folder=None, mailbox=None):
        """add the designated feed to the configuration

        this is not thread-safe."""
        if self.has_section(name):
            raise AttributeError('key %s already exists' % name)
        d = OrderedDict()
        # when a new element is added here, it must be added to the
        # Feed.locked_keys config to keep parsed feed elements from
        # overriding potentially secure-sensitive settings
        d['url'] = url
        if output is not None:
            d['output'] = output
        if args is not None:
            d['args'] = args
        if filter is not None:
            d['filter'] = filter
        if filter_args is not None:
            d['filter_args'] = filter_args
        if folder is not None:
            d['folder'] = folder
        if mailbox is not None:
            d['mailbox'] = mailbox
        self[name] = d
        self.commit()

    def set(self, section, option, value=None):
        """override parent to make sure we immediately write changes

        not thread-safe
        """
        super(FeedConfStorage, self).set(section, option, value)
        self.commit()

    def remove_option(self, section, option):
        """override parent to make sure we immediately write changes

        not thread-safe
        """
        super(FeedConfStorage, self).remove_option(section, option)
        self.commit()

    def remove(self, name):
        """convenient alias for
        :func:`configparser.RawConfigParser.remove_section`

        not thread-safe
        """
        self.remove_section(name)
        self.commit()

    def commit(self):
        """write the feed configuration

        see :func:`configparser.RawConfigParser.write`"""
        logging.info('saving feed configuration in %s', self.path)
        utils.make_dirs_helper(os.path.dirname(self.path))
        with open(self.path, 'w') as configfile:
            self.write(configfile)

    def __iter__(self):
        """override iterator to allow for pattern matching"""
        for name in self.sections():
            if self.pattern is None or self.pattern in name:
                yield Feed(name=name, **self[name])


class SqliteStorage(object):
    sql = None
    record = None
    cache = {}
    locks = {}
    table_name = None
    key_name = 'key'
    value_name = 'value'

    def __init__(self, path):
        self.path = os.path.expanduser(path)
        assert self.path
        utils.make_dirs_helper(os.path.dirname(self.path))
        if self.sql:
            with self.connection() as con:
                con.execute(self.sql)

    @contextmanager
    def connection(self, commit=True):
        if self.path not in SqliteStorage.locks:
            SqliteStorage.locks[self.path] = Lock()
        with SqliteStorage.locks[self.path]:
            con = self.connect_cache(self.path)
            yield con
            if commit:
                con.commit()

    @classmethod
    def connect_cache(cls, path):
        if path not in cls.cache:
            logging.info('connecting to database at %s', path)
            conn = sqlite3.connect(path)
            try:
                conn.set_trace_callback(logging.debug)
            except AttributeError:  # pragma: nocover
                logging.debug('no logging support in sqlite')
            cls.cache[path] = conn
        return cls.cache[path]

    @classmethod
    def guess_path(cls):
        cache_home_db = os.path.join(xdg_base_dirs.xdg_cache_home, 'feed2exec.db')
        data_home_db = os.path.join(xdg_base_dirs.xdg_data_home, 'feed2exec.db')
        if os.path.exists(data_home_db):
            return data_home_db
        elif os.path.exists(cache_home_db):
            # we use warnings here because this function is likely to
            # be called before the logging module is initialized,
            # which typicall creates a StreamHandler that's not
            # configured the way we like. A better way to work around
            # this problem would be to use a LoggerAction in argparse
            # but, alas, we are using click, so this insanity
            # continues.
            warnings.warn(
                "falling back on deprecated cache directory, move %s to %s to remove this warning" % (
                    cache_home_db,
                    data_home_db,
                    ),
                DeprecationWarning,
            )
            return cache_home_db
        else:
            # if no DB exists, fallback on the good one
            return data_home_db

    def get(self, key):
        with self.connection(commit=False) as con:
            val = con.execute("""SELECT `%s` FROM `%s` WHERE `%s`=?"""
                              % (self.value_name, self.table_name, self.key_name), (key, )).fetchone()
            return val[0] if val else None

    def set(self, key, value):
        with self.connection() as con:
            con.execute("INSERT OR REPLACE INTO `%s` (`%s`, `%s`) VALUES (?, ?)"
                        % (self.table_name, self.key_name, self.value_name),
                        (key, value))

    def delete(self, key):
        with self.connection() as con:
            con.execute("DELETE FROM `%s` WHERE `%s` = ?"
                        % (self.table_name, self.key_name), (key,))

    def __contains__(self, key):
        return self.get(key) is not None

    def __iter__(self):
        with self.connection(commit=False) as con:
            cur = con.cursor()
            cur.row_factory = sqlite3.Row
            return cur.execute("SELECT * from `%s`" % self.table_name)


class FeedItemCacheStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             feedcache (name text, guid text,
             PRIMARY KEY (name, guid))'''
    record = namedtuple('record', 'name guid')
    table_name = 'feedcache'
    key_name = 'guid'
    value_name = 'name'

    def __init__(self, path, feed=None, guid=None):
        self.feed = feed
        if guid is None:
            self.guid = '%'
        else:
            self.guid = '%' + guid + '%'
        super().__init__(path)

    def __repr__(self):
        return 'FeedItemCacheStorage("%s", "%s", "%s")' % (self.path, self.feed, self.guid)

    def add(self, guid):
        assert self.feed
        self.set(guid, self.feed)

    def remove(self, guid):
        self.delete(guid)

    def __contains__(self, guid):
        '''override base class to look only in the specified feed'''
        if self.feed is None:
            pattern = '%'
        else:
            pattern = self.feed
        with self.connection(commit=False) as con:
            cur = con.execute("""SELECT * FROM feedcache WHERE name LIKE ? AND guid=?""",
                              (pattern, guid))
            return cur.fetchone() is not None

    def __iter__(self):
        '''override base class to look only in the specified feed'''
        if self.feed is None:
            pattern = '%'
        else:
            pattern = self.feed
        with self.connection(commit=False) as con:
            cur = con.cursor()
            cur.row_factory = sqlite3.Row
            return cur.execute("""SELECT * from feedcache WHERE name LIKE ? AND guid LIKE ?""",
                               (pattern, self.guid))


class FeedContentCacheStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             content (key, value,
             PRIMARY KEY (key))'''
    table_name = 'content'
