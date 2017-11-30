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
from feed2exec.feeds import (FeedManager, FeedConfStorage, FeedCacheStorage, Feed)
import feed2exec.logging
import feed2exec.plugins as plugins
from feed2exec.utils import slug


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
@click.option('--config', default=None,
              help='use a different config file [default: %s]' % FeedConfStorage.guess_path())
@click.option('--database', default=None,
              help='use a different database [default: %s]' % FeedCacheStorage.guess_path())
@click.pass_context
def main(ctx, loglevel, syslog, config, database):
    feed2exec.logging.advancedConfig(level=loglevel, syslog=syslog,
                                     logFormat='%(messageq)s')
    if ctx.obj is None:
        ctx.obj = {}
    if database is None:
        database = FeedCacheStorage.guess_path()
        logging.debug('guessed db_path to be %s', database)
    if config is None:
        config = FeedConfStorage.guess_path()
        logging.debug('guessed conf_path to be %s', config)
    ctx.obj['database'] = database
    ctx.obj['config'] = config
    # preload for commands who do not need a specific pattern like add/list/rm
    ctx.obj['feeds'] = FeedManager(config, database)


@click.command(help='add a URL to the configuration')
@click.argument('name')
@click.argument('url')
@click.option('--output', metavar='PLUGIN', show_default=True,
              default='maildir',
              help="output plugin to call on new items")
@click.option('--args', metavar='ARGS',
              help="output plugin arguments, with parameter substitution")
@click.option('--filter', help="filter plugin to call to process items")
@click.option('--filter_args',
              help="filter plugin arguments, also with parameter substitution")
@click.option('--folder', help="subfolder to store email into")
@click.option('--mailbox', help="basic mailbox to store email into")
@click.pass_obj
def add(obj, name, url, output, args, filter, filter_args, folder, mailbox):
    try:
        obj['feeds'].conf_storage.add(name=name, url=url,
                                      output=plugins.resolve(output), args=args,
                                      filter=plugins.resolve(filter), filter_args=filter_args,
                                      folder=folder, mailbox=mailbox)
    except AttributeError as e:
        raise click.BadParameter('feed %s already exists in %s' % (name, obj['feeds'].conf_storage.path))


@click.command(help='list configured feeds')
@click.pass_obj
def ls(obj):
    for feed in obj['feeds'].conf_storage:
        if feed:
            print(json.dumps(feed, indent=2, sort_keys=True))


@click.command(help='remove a feed from the configuration')
@click.argument('name')
@click.pass_obj
def rm(obj, name):
    obj['feeds'].conf_storage.remove(name)


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
    st = FeedManager(obj['config'], obj['database'], pattern=pattern)
    # used for unit testing
    if obj and obj.get('session'):
        Feed._session = obj['session']
    parallel = jobs or parallel
    st.fetch(parallel, force=force, catchup=catchup)


@click.command(help='fetch and parse a single feed')
@click.argument('url')
@click.option('--output', metavar='PLUGIN', show_default=True,
              default='maildir',
              help="output plugin to call on new items")
@click.option('--args', metavar='ARGS',
              help="output plugin arguments, with parameter substitution")
@click.option('--filter', help="filter plugin to call to process items")
@click.option('--filter_args',
              help="filter plugin arguments, also with parameter substitution")
@click.option('--folder', help="subfolder to store email into")
@click.option('--mailbox', help="basic mailbox to store email into")
@click.pass_obj
def parse(obj, url, **kwargs):
    kwargs.update({'url': url})
    for plugin in ('output', 'filter'):
        kwargs[plugin] = plugins.resolve(kwargs[plugin])
    feed = Feed(slug(url), kwargs)
    data = feed.parse(feed.fetch())
    # XXX: i don't like this - we should use a clean environment.
    obj['feeds'].dispatch(feed, data, lock=False, force=True)


@click.command(name='import', help='import feed list from OPML file')
@click.argument('path', type=click.File('rb'))
@click.pass_obj
def import_(obj, path):
    obj['feeds'].opml_import(path)


@click.command(help='export feeds to an OPML file')
@click.argument('path', type=click.File('wb'))
@click.pass_obj
def export(obj, path):
    obj['feeds'].opml_export(path)


main.add_command(add)
main.add_command(ls)
main.add_command(rm)
main.add_command(fetch)
main.add_command(import_)
main.add_command(export)
main.add_command(parse)


if __name__ == '__main__':
    '''workaround a click quirk

    click seems to require a dict to be passed for pass_context to
    work correctly.

    this is so that setuptools works correctly.

    cargo-culted from debmans
    '''
    main(prog_name=feed2exec.__prog__, obj={})
