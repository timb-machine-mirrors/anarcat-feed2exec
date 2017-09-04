#!/usr/bin/python3
# coding: utf-8

'''
Simple plugin interface
=======================

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


def plugin_output(feed, item):
    """load and run the given plugin with the given arguments

    an "output plugin" is a simple Python module with an "Output"
    class defined which will process arguments and should output them
    somewhere. the plugin is called when a new item is found, unless
    cache is flushed or ignored.

    The following keywords are usually replaced in the arguments:

    * %(link)s
    * %(title)s
    * %(description)s
    * %(published)s
    * %(updated)s
    * %(guid)s

    The full list of such parameters is determined by the
    :module:feedparser module.

    .. caution:: None of those parameters are sanitized in any way
                 other than what feedparser does, so plugins writing
                 files, executing code or talking to the network
                 should be careful to sanitize the input
                 appropriately.

    :param dict feed: the feed metadata
    :param dict item: the updated item
    :return object: the loaded plugin
    """

    if feed['args'] is None:
        args = []
    else:
        args = [x % item for x in shlex.split(feed['args'])]
    plugin = feed['plugin']
    logging.info('running plugin %s with arguments %s', plugin, args)
    plugin = importlib.import_module(plugin)
    try:
        return plugin.Output(*args)
    except Exception as e:
        logging.warning("plugin generated exception: %s, ignoring", e)
        return None
