#!/usr/bin/python3
# coding: utf-8

'''
Plugin interface
~~~~~~~~~~~~~~~~

In this context, a "plugin" is simply a Python module with a defined
interface.
'''

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


import importlib
import logging
import shlex


def output(feed, item, lock=None):
    """load and run the given plugin with the given arguments

    an "output plugin" is a simple Python module with an ``output``
    callable defined which will process arguments and
    should output them somewhere, for example by email or through
    another command. the plugin is called when a new item is found,
    unless cache is flushed or ignored.

    The "callable" can be a class, in which case only the constructor
    is called or a function. The ``*args`` and ``**kwargs`` parameter
    SHOULD be used in the function definition for
    forward-compatibility (ie. to make sure new parameters added do
    not cause a regression).

    Plugins should also expect to be called in parallel and should use
    the provided ``lock`` (a multiprocessor.Lock object) to acquire
    and release locks around contentious resources.

    The following keywords are usually replaced in the arguments:

    * {item.link}
    * {item.title}
    * {item.description}
    * {item.published}
    * {item.updated}
    * {item.guid}

    The full list of such parameters is determined by the
    :module:feedparser module.

    Similarly, feed parameters from the configuration file are
    accessible.

    .. caution:: None of those parameters are sanitized in any way
                 other than what feedparser does, so plugins writing
                 files, executing code or talking to the network
                 should be careful to sanitize the input
                 appropriately.

    The feed and items are also passed to the plugin as keyword
    arguments.

    :param dict feed: the feed metadata
    :param dict item: the updated item
    :return object: the loaded plugin

    """

    if feed.get('args'):
        args = [x.format(feed=feed, item=item)
                for x in shlex.split(feed['args'])]
    else:
        args = []
    plugin = feed.get('output')
    if plugin:
        logging.debug('running output plugin %s with arguments %s',
                      plugin, args)
        plugin = importlib.import_module(plugin)
        try:
            return plugin.output(*args, feed=feed, entry=item, lock=lock)
        except Exception as e:
            logging.exception("plugin generated exception: %s, ignoring", e)
            return None
    else:
        return False


def filter(feed, item, lock=None):
    """common code with output() should be factored out, but output()
    takes arguments..."""
    plugin = feed.get('filter')
    if plugin:
        if feed.get('args'):
            args = [x.format(feed=feed, item=item)
                    for x in shlex.split(feed['args'])]
        else:
            args = []
        logging.debug('running filter plugin %s with arguments %s',
                      plugin, args)
        plugin = importlib.import_module(plugin)
        try:
            return plugin.filter(*args, feed=feed, entry=item, lock=lock)
        except Exception as e:
            logging.exception("plugin generated exception: %s, ignoring", e)
            return None
