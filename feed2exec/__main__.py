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

from datetime import datetime
import json
import logging
import os.path


import click
import feed2exec
from feed2exec.feeds import FeedStorage, fetch_feeds
import feed2exec.feeds as feedsmod
try:
    from lxml import etree
except ImportError:
    import xml.etree.ElementTree as etree
import sqlite3

# not sure why logging._levelNames are not exposed...
levels = ['CRITICAL',
          'ERROR',
          'WARNING',
          'INFO',
          'DEBUG']


@click.group(help=feed2exec.__description__,
             context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=feed2exec.__version__)
@click.option('--loglevel', 'loglevel',
              help='show only warning messages',
              type=click.Choice(levels),
              flag_value='WARNING', default=True)
@click.option('-v', '--verbose', 'loglevel', help='be more verbose',
              flag_value='INFO')
@click.option('-d', '--debug', 'loglevel', help='even more verbose',
              flag_value='DEBUG')
@click.option('--database', default=feed2exec.feeds.default_db(),
              help='use given database instead of default %(default)s')
@click.pass_context
def main(ctx, loglevel, database):
    if database != feedsmod.default_db():
        def dummy():
            return os.path.realpath(database)
        feedsmod.default_db = dummy
    logging.basicConfig(format='%(message)s', level=loglevel)


@click.command(help='add a URL to the configuration')
@click.argument('name')
@click.argument('url')
@click.option('--plugin', help="plugin to call when new items are found")
@click.option('--args',
              help="arguments to the plugin, with parameter substitution")
def add(name, url, plugin, args):
    st = FeedStorage()
    try:
        st.add(name, url, plugin, args)
    except sqlite3.IntegrityError:
        logging.error('feed %s already exists', name)


@click.command(help='list configured feeds')
def ls():
    st = FeedStorage()
    for feed in st:
        if feed is not None:
            print(json.dumps(dict(feed), indent=2, sort_keys=True))


@click.command(help='remove a feed from the configuration')
@click.argument('name')
def rm(name):
    st = FeedStorage()
    st.remove(name)


@click.command(help='fetch and process all feeds')
@click.option('--pattern', help='only fetch feeds matchin name or URL')
def fetch(pattern):
    fetch_feeds(pattern)


@click.command(name='import', help='import feed list from OPML file')
@click.argument('path', type=click.File('r'))
def import_(path):
    tree = etree.parse(path)
    st = FeedStorage()
    for child in tree.getiterator():
        if child.tag == 'outline':
            logging.debug(child.attrib)
            try:
                logging.info('importing element %s <%s>',
                             child.attrib['title'], child.attrib['xmlUrl'])
                st.add(child.attrib['title'], child.attrib['xmlUrl'])
            except sqlite3.IntegrityError:
                logging.error('feed %s already exists, skipped',
                              child.attrib['title'])


@click.command(help='export feeds to an OPML file')
@click.argument('path', type=click.File('wb'))
def export(path):
    xml_tmpl = u'''<opml version="1.0">
  <head>
    <title>{title}</title>
    <dateModified>{date}</dateModified>
  </head>
  <body>
{body}</body>
</opml>'''
    outline_tmpl = u'<outline title="{name}" type="rss" xmlUrl="{url}" />'
    st = FeedStorage()
    body = u''
    for feed in st:
        if feed is not None:
            body += outline_tmpl.format(**feed) + "\n"
    output = xml_tmpl.format(title=u'feed2exec RSS feeds',
                             date=datetime.now(),
                             body=body)
    path.write(output.encode('utf-8'))


main.add_command(add)
main.add_command(ls)
main.add_command(rm)
main.add_command(fetch)
main.add_command(import_)
main.add_command(export)


if __name__ == '__main__':
    '''workaround a click quirk

    click seems to require a dict to be passed for pass_context to
    work correctly.

    this is so that setuptools works correctly.

    cargo-culted from debmans
    '''
    main(prog_name=feed2exec.__prog__)
