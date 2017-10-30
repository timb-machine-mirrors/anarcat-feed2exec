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


import click
import requests

import feed2exec
from feed2exec.feeds import (FeedManager)
import feed2exec.feeds as feedsmod
import feed2exec.logging


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
@click.option('--config', default=feedsmod.ConfFeedStorage.path,
              show_default=True, help='use a different config file')
@click.option('--database', default=feedsmod.SqliteStorage.path,
              show_default=True, help='use a different database')
@click.pass_context
def main(ctx, loglevel, syslog, config, database):
    feedsmod.SqliteStorage.path = database
    feedsmod.ConfFeedStorage.path = config
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
@click.option('--filter_args',
              help="filter plugin arguments, also with parameter substitution")
@click.option('--folder', help="subfolder to store email into")
@click.option('--mailbox', help="basic mailbox to store email into")
def add(name, url, output, args, filter, filter_args, folder, mailbox):
    st = FeedManager()
    try:
        st.add(name=name, url=url, output=output, args=args,
               filter=filter, filter_args=filter_args,
               folder=folder, mailbox=mailbox)
    except AttributeError as e:
        raise click.BadParameter('feed %s already exists' % name)


@click.command(help='list configured feeds')
def ls():
    st = FeedManager()
    for feed in st:
        if feed:
            print(json.dumps(feed, indent=2, sort_keys=True))


@click.command(help='remove a feed from the configuration')
@click.argument('name')
def rm(name):
    st = FeedManager()
    st.remove(name)


@click.command(help='fetch and process all feeds')
@click.pass_obj
@click.option('--pattern', help='only fetch feeds matchin name or URL')
@click.option('--parallel', help='start jobs in parallel', is_flag=True)
@click.option('--jobs', '-j', help='start N jobs in parallel',
              default=None, type=int, metavar='N')
@click.option('--force', '-f', is_flag=True, help='do not check cache')
@click.option('--catchup', '-n',
              is_flag=True, help='do not call output plugins')
def fetch(obj, pattern, parallel, jobs, force, catchup):
    st = FeedManager(pattern=pattern)
    # used for unit testing
    if obj and type(obj) is requests.sessions.Session:
        st.session = obj
    parallel = jobs or parallel
    st.fetch(parallel, force=force, catchup=catchup)


@click.command(name='import', help='import feed list from OPML file')
@click.argument('path', type=click.File('rb'))
def import_(path):
    FeedManager().opml_import(path)


@click.command(help='export feeds to an OPML file')
@click.argument('path', type=click.File('wb'))
def export(path):
    FeedManager().opml_export(path)


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
