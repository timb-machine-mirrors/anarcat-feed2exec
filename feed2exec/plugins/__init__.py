#!/usr/bin/python3
# coding: utf-8

'''
Plugin interface
~~~~~~~~~~~~~~~~

In this context, a "plugin" is simply a Python module with a defined
interface.
'''

# Copyright (C) 2016-2019 Antoine Beaupré <anarcat@debian.org>
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


def output(feed, item, lock=None, session=None):
    """load and run the given plugin with the given arguments

    an "output plugin" is a simple Python module with an ``output``
    callable defined which will process arguments and should output
    them somewhere, for example by email or through another
    command. the plugin is called (from :func:`feed2exec.feeds.parse`)
    when a new item is found, unless cache is flushed or ignored.

    The "callable" can be a class, in which case only the constructor
    is called or a function. The ``*args`` and ``**kwargs`` parameter
    SHOULD be used in the function definition for
    forward-compatibility (ie. to make sure new parameters added do
    not cause a regression).

    Plugins should also expect to be called in parallel and should use
    the provided ``lock`` (a multiprocessor.Lock object) to acquire
    and release locks around contentious resources.

    Finally, the FeedManager will pass along his own ``session`` that
    should be reused by plugins to do requests. This allows plugins to
    be unit-tested and leverages the built-in cache as well.

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
    arguments. Plugins should especially respect the ``catchup``
    argument that, when set, forbids plugins to do any permanent
    activity. For example, plugins MUST NOT run commands, write files,
    or make network requests. In general, "catchup mode" should be
    *fast*: it allows users to quickly catchup with new feeds without
    firing plugins, but it should *also* allow users to test
    configurations so plugins SHOULD give information to the user
    about what would have been done by the plugin without ``catchup``.

    :param dict feed: the feed metadata
    :param dict item: the updated item
    :return object: the loaded plugin

    .. note:: more information about plugin design is in the
              :ref:`writing-plugins` document.
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
            return plugin.output(*args, feed=feed, item=item, lock=lock, session=session)
        except (BrokenPipeError):
            # handle pipe errors gracefully, e.g. | head
            raise
        except Exception as e:
            logging.exception("plugin generated exception: %s, skipping", e)
            return None
    else:
        return False


def filter(feed, item, lock=None, session=None):
    """call filter plugins.

    very similar to the output plugin, but just calls the ``filter``
    module member instead of ``output``

    .. todo:: common code with output() should be factored out, but
              output() takes arguments...
    """
    plugin = feed.get('filter')
    if plugin:
        if feed.get('filter_args'):
            args = [x.format(feed=feed, item=item)
                    for x in shlex.split(feed['filter_args'])]
        else:
            args = []
        logging.debug('running filter plugin %s with arguments %s',
                      plugin, args)
        plugin = importlib.import_module(plugin)
        try:
            return plugin.filter(*args, feed=feed, item=item, lock=lock, session=session)
        except Exception as e:
            logging.exception("plugin generated exception: %s, ignoring", e)
            return None


def resolve(plugin):
    """resolve a short plugin name to a loadable plugin path

    Some parts of feed2exec allow shorter plugin names. For example,
    on the commandline, users can pass `maildir` instead of
    `feed2exec.plugins.maildir`.

    Plugin resolution works like this:

     1. search for the module in the `feed2exec.plugins` namespace

     2. if that fails, consider the module to be an absolute path
    """

    if plugin is None:
        return None
    try:
        full_plugin = 'feed2exec.plugins.' + plugin
        importlib.import_module(full_plugin)
        plugin = full_plugin
    except ImportError:
        try:
            importlib.import_module(plugin)
        except ImportError:
            logging.warning('cannot find plugin %s, ignored', plugin)
            plugin = None
    return plugin
