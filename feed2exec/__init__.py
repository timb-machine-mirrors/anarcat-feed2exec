# -*- coding: utf-8 -*-

from __future__ import print_function

try:
    from _version import version
except ImportError:
    try:
        from setuptools_scm import get_version
        version = get_version()
    except (ImportError, LookupError):
        version = '???'

__description__ = '''This command will take a configured set of feeds and
fire specific commands or plugins for every new item found in the feed.'''
__version__ = version
__prog__ = 'feed2exec'
__author__ = 'Antoine Beaupré'
__copyright__ = "Copyright (C) 2016  Antoine Beaupré"
__license_short__ = 'AGPLv3'
__license__ = """
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

