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
from __future__ import print_function, unicode_literals

import collections
import errno
import json
import logging
import os
import os.path


import click
import feedparser
import requests
import sqlite3

__desc__ = '''This command will take a configured set of feeds and
fire specific commands or plugins for every new item found in the feed.'''
__version__ = '0.0'
__prog__ = 'feed2exec'

# not sure why logging._levelNames are not exposed...
levels = ['CRITICAL',
          'ERROR',
          'WARNING',
          'INFO',
          'DEBUG']


def default_config_dir():
    home_config = os.environ.get('XDG_CONFIG_HOME',
                                 os.path.join(os.environ.get('HOME'),
                                              '.config'))
    return os.path.join(home_config, __prog__)


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


class DbStorage(object):
    pass


class SqliteStorage(DbStorage):
    feedcache_sql = '''CREATE TABLE IF NOT EXISTS
                       feedcache (feed text, guid text,
                       PRIMARY KEY (feed, guid))'''
    feeds_sql = '''CREATE TABLE IF NOT EXISTS
                   feeds (feed text, url text, plugin text,
                   PRIMARY KEY (feed))'''
    feeds_record = collections.namedtuple('feeds_record', 'feed url plugin')
    
    def __init__(self, path):
        make_dirs_helper(os.path.dirname(path))
        self.conn = sqlite3.connect(path)
        self.conn.execute(self.feedcache_sql)
        self.conn.execute(self.feeds_sql)
        self.conn.commit()

    def add_item(self, feed, item):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO feedcache VALUES (?, ?)", (feed, item))
        self.conn.commit()  # XXX

    def contains_item(self, feed, item):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM feedcache WHERE feed=? AND guid=?",
                    (feed, item))
        return cur.fetchone() is not None

    def add_feed(self, feed, url, plugin):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO feeds VALUES (?, ?, ?)", (feed, url, plugin))
        self.conn.commit()  # XXX

    def ls_feed(self):
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM feeds")
        cur.row_factory = sqlite3.Row
        yield cur.fetchone()

    def rm_feed(self, feed):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM feeds WHERE feed=?", (feed, ))
        self.conn.commit()  # XXX


@click.group()
@click.version_option(version=__version__)
@click.option('--loglevel', 'loglevel',
              help='show only warning messages',
              type=click.Choice(levels),
              flag_value='WARNING', default=True)
@click.option('-v', '--verbose', 'loglevel', help='be more verbose',
              flag_value='INFO')
@click.option('-d', '--debug', 'loglevel', help='even more verbose',
              flag_value='DEBUG')
# would love to have a default here when no option is specified
# unfortunately, default= still asks for an argument
@click.option('-s', '--syslog', type=click.Choice(levels),
              help='send logs to syslog')
@click.option('-n', '--dryrun', is_flag=True,
              help='do not write anything')
@click.option('--progress', is_flag=True,
              help='show progress bars')
@click.pass_context
def main(ctx, loglevel, syslog, dryrun, progress):
    logging.basicConfig(format='%(message)s', level=loglevel)


@click.command(help='add a URL to the configuration')
@click.argument('name')
@click.argument('url')
@click.option('--plugin', help="plugin to call when new items are found")
def add(name, url, plugin):
    st = SqliteStorage(path=default_db())
    st.add_feed(name, url, plugin)


@click.command(help='list configured feeds')
def ls():
    st = SqliteStorage(path=default_db())
    it = st.ls_feed()
    for feed in it:
        if feed is not None:
            print(dict(feed))


@click.command(help='remove a feed from the configuration')
@click.argument('name')
def rm(name):
    st = SqliteStorage(path=default_db())
    st.rm_feed(name)


@click.command(help='fetch and process all feeds')
def fetch():
    st = SqliteStorage(path=default_db())
    for feed in st.ls_feed():
        logging.debug('found feed in DB: %s', feed)
        data = _parse(feed['url'])
        for entry in data['entries']:
            if st.contains_item(feed['feed'], entry['id']):
                logging.info('new entry %s <%s>', entry['id'], entry['link'])
                st.add_item(feed['feed'], entry['id'])
            else:
                logging.debug('entry %s already seen', entry['id'])
    

@click.command(help='parse a single URL')
@click.argument('url')
def parse(url):
    _parse(url)


def _parse(url):
    logging.debug('fetching URL %s', url)
    body = ''
    if url.startswith('file://'):
        with open(url[len('file://'):], 'r') as f:
            body = f.read()
    else:
        r = requests.get(url)
        logging.debug('got response %s', r)
        body = r.text
    logging.debug('found body %s', body)
    data = feedparser.parse(body)
    logging.debug('parsed structure %s',
                  json.dumps(data, indent=2, sort_keys=True))
    return data


main.add_command(parse)
main.add_command(add)
main.add_command(ls)
main.add_command(rm)
main.add_command(fetch)


if __name__ == '__main__':
    '''workaround a click quirk

    click seems to require a dict to be passed for pass_context to
    work correctly.

    this is so that setuptools works correctly.

    cargo-culted from debmans
    '''
    main(obj={})
