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

import json
import logging


import click
import feed2exec
from feed2exec.feeds import FeedStorage, FeedCacheStorage
import feedparser
import requests

# not sure why logging._levelNames are not exposed...
levels = ['CRITICAL',
          'ERROR',
          'WARNING',
          'INFO',
          'DEBUG']


@click.group(help=feed2exec.__description__)
@click.version_option(version=feed2exec.__version__)
@click.option('--loglevel', 'loglevel',
              help='show only warning messages',
              type=click.Choice(levels),
              flag_value='WARNING', default=True)
@click.option('-v', '--verbose', 'loglevel', help='be more verbose',
              flag_value='INFO')
@click.option('-d', '--debug', 'loglevel', help='even more verbose',
              flag_value='DEBUG')
@click.pass_context
def main(ctx, loglevel):
    logging.basicConfig(format='%(message)s', level=loglevel)


@click.command(help='add a URL to the configuration')
@click.argument('name')
@click.argument('url')
@click.option('--plugin', help="plugin to call when new items are found")
def add(name, url, plugin):
    st = FeedStorage()
    st.add(name, url, plugin)


@click.command(help='list configured feeds')
def ls():
    st = FeedStorage()
    for feed in st:
        if feed is not None:
            print(dict(feed))


@click.command(help='remove a feed from the configuration')
@click.argument('name')
def rm(name):
    st = FeedStorage()
    st.rm(name)


@click.command(help='fetch and process all feeds')
def fetch():
    st = FeedStorage()
    for feed in st:
        logging.debug('found feed in DB: %s', feed)
        cache = FeedCacheStorage(feed=feed['feed'])
        data = _parse(feed['url'])
        for entry in data['entries']:
            if entry['id'] in cache:
                logging.info('new entry %s <%s>', entry['id'], entry['link'])
                cache.add(entry['id'])
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
