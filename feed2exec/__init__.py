# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import

try:
    from ._version import version
except ImportError:  # pragma: nocover
    try:
        from setuptools_scm import get_version
        version = get_version()
    except (ImportError, LookupError):
        version = '???'

__description__ = 'The programmable feed reader'
__version__ = version
__website__ = 'https://feed2exec.readthedocs.io/'
__prog__ = 'feed2exec'
__author__ = u'Antoine Beaupré'
__email__ = 'anarcat@debian.org'
__copyright__ = u"Copyright (C) 2016-2019  Antoine Beaupré"
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
