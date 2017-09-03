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
import os
import os.path


import feed2exec
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


def fetch_feeds(pattern=None):
    st = FeedStorage(pattern=pattern)
    for feed in st:
        logging.debug('found feed in DB: %s', dict(feed))
        cache = FeedCacheStorage(feed=feed['name'])
        data = _parse(feed['url'])
        for entry in data['entries']:
            if entry['id'] in cache:
                logging.info('new entry %s <%s>', entry['id'], entry['link'])
                cache.add(entry['id'])
            else:
                logging.debug('entry %s already seen', entry['id'])


def safe_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
        return obj.isoformat()
    elif isinstance(obj, time.struct_time):
        return time.strftime('%c')
    else:
        return str(obj)


def _parse(url):
    logging.debug('fetching URL %s', url)
    body = ''
    if url.startswith('file://'):
        filename = url[len('file://'):]
        logging.debug('opening local file %s', filename)
        with open(filename, 'r') as f:
            body = f.read().decode('utf-8')
    else:
        body = requests.get(url).text
    data = feedparser.parse(body)
    logging.debug(data)
    if len(data) > 0:
        logging.debug('parsed structure %s',
                      json.dumps(data['feed'], indent=2, sort_keys=True, default=safe_serial))
    else:
        logging.info('body of URL %s is empty', url)
    return data


class DbStorage(object):
    pass


class SqliteStorage(DbStorage):
    sql = ''
    record = None

    def __init__(self, path=None):
        if path is None:
            path = default_db()
        make_dirs_helper(os.path.dirname(path))
        self.conn = sqlite3.connect(path)
        self.conn.execute(self.sql)
        self.conn.commit()


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
        cur = self.conn.cursor()
        cur.execute("INSERT INTO feeds VALUES (?, ?, ?, ?)",
                    (name, url, plugin, args))
        self.conn.commit()  # XXX

    def remove(self, name):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM feeds WHERE name=?", (name, ))
        self.conn.commit()  # XXX

    def __contains__(self, name):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM feeds WHERE name=?", (name,))
        return cur.fetchone() is not None

    def __iter__(self):
        self.cur = self.conn.cursor()
        self.cur.row_factory = sqlite3.Row
        return self.cur.execute("SELECT * from feeds WHERE name LIKE ? OR url LIKE ?",
                                (self.pattern, self.pattern))


class FeedCacheStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             feedcache (name text, guid text,
             PRIMARY KEY (name, guid))'''
    record = collections.namedtuple('record', 'name guid')

    def __init__(self, feed, path=None, guid=None):
        self.feed = feed
        if guid is None:
            self.guid = '%'
        else:
            self.guid = '%' + guid + '%'
        super(FeedCacheStorage, self).__init__(path)

    def add(self, guid):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO feedcache VALUES (?, ?)",
                    (self.feed, guid))
        self.conn.commit()  # XXX

    def remove(self, guid):
        assert self.feed is not None
        cur = self.conn.cursor()
        cur.execute("DELETE FROM feedcache WHERE guid = ?", (guid,))
        self.conn.commit()  # XXX

    def __contains__(self, guid):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM feedcache WHERE name=? AND guid=?",
                    (self.feed, guid))
        return cur.fetchone() is not None

    def __iter__(self):
        self.cur = self.conn.cursor()
        self.cur.row_factory = sqlite3.Row
        return self.cur.execute("SELECT * from feedcache WHERE guid LIKE ?",
                                (self.guid, ))
