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
import feed2exec.logging

try:
    from lxml import etree
except ImportError:  # pragma: nocover
    import xml.etree.ElementTree as etree


@click.group(help=feed2exec.__description__,
             context_settings=dict(help_option_names=['-h', '--help']))
@click.version_option(version=feed2exec.__version__)
@click.option('--loglevel', 'loglevel',
              help='choose specific log level [default: WARNING]',
              type=click.Choice(feed2exec.logging.levels),
              flag_value='WARNING', default=True)
@click.option('-v', '--verbose', 'loglevel', flag_value='INFO',
              help='show what is happening (loglevel: VERBOSE)')
@click.option('-d', '--debug', 'loglevel', flag_value='DEBUG',
              help='show debugging information (loglevel: DEBUG)')
@click.option('--syslog', help='send LEVEL logs to syslog', metavar='LEVEL',
              type=click.Choice(feed2exec.logging.levels))
@click.option('--config', default=feed2exec.feeds.default_config_dir(),
              help='use given directory instead of default')
@click.pass_context
def main(ctx, loglevel, syslog, config):
    feedsmod.SqliteStorage.path = os.path.join(config, 'feed2exec.db')
    feedsmod.ConfFeedStorage.path = os.path.join(config, 'feed2exec.ini')
    feed2exec.logging.advancedConfig(level=loglevel, syslog=syslog,
                                     logFormat='%(messageq)s')


@click.command(help='add a URL to the configuration')
@click.argument('name')
@click.argument('url')
@click.option('--output', metavar='PLUGIN', show_default=True,
              default='feed2exec.plugins.maildir',
              help="output plugin to call on new items")
@click.option('--args', metavar='ARGS',
              help="output plugin arguments, with parameter substitution")
@click.option('--filter', help="filter plugin to call to process items")
@click.option('--folder', help="subfolder to store email into")
@click.option('--mailbox', help="basic mailbox to store email into")
def add(name, url, output, args, filter, folder, mailbox):
    st = FeedStorage()
    try:
        st.add(name, url, output, args, filter, folder, mailbox)
    except AttributeError as e:
        raise click.BadParameter('feed %s already exists' % name)


@click.command(help='list configured feeds')
def ls():
    st = FeedStorage()
    for feed in st:
        if feed:
            print(json.dumps(feed, indent=2, sort_keys=True))


@click.command(help='remove a feed from the configuration')
@click.argument('name')
def rm(name):
    st = FeedStorage()
    st.remove(name)


@click.command(help='fetch and process all feeds')
@click.option('--pattern', help='only fetch feeds matchin name or URL')
@click.option('--parallel', help='start jobs in parallel', is_flag=True)
@click.option('--jobs', '-j', help='start N jobs in parallel',
              default=None, type=int, metavar='N')
@click.option('--force', '-f', is_flag=True, help='do not check cache')
@click.option('--catchup', '-n',
              is_flag=True, help='do not call output plugins')
def fetch(pattern, parallel, jobs, force, catchup):
    parallel = jobs or parallel
    fetch_feeds(pattern, parallel, force=force, catchup=catchup)


@click.command(name='import', help='import feed list from OPML file')
@click.argument('path', type=click.File('r'))
def import_(path):
    tree = etree.parse(path)
    st = FeedStorage()
    for child in tree.getiterator():
        if child.tag == 'outline':
            logging.debug('found OPML entry: %s', child.attrib)
            try:
                logging.info('importing element %s <%s>',
                             child.attrib['title'], child.attrib['xmlUrl'])
                st.add(child.attrib['title'], child.attrib['xmlUrl'])
            except AttributeError:
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
        if feed:
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
