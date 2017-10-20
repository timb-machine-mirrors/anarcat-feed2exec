#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Antoine Beaupré <anarcat@debian.org>
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

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import io
import os
import os.path
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

import feed2exec  # noqa


mod = feed2exec


classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Console',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',  # noqa
    'Natural Language :: English',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Topic :: Communications :: Email',
    'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: News/Diary',
    'Topic :: Text Processing :: Markup :: HTML',
]

requires = [
    "click",
    "feedparser",
    "html2text",
    "requests",
    "requests-file",
    "unidecode",
]

packages = [
    mod.__prog__,
    'feed2exec.plugins',
    'feed2exec.tests',
]

package_data = {
    'feed2exec.tests': ['files/*'],
}

try:
    import configparser  # noqa
except ImportError:
    # py2: we need a more recent configparser
    requires.append("configparser")

try:
    import unittest.mock  # noqa
except ImportError:
    # py2: we need the mock module, not in stdlib
    requires.append("mock")

try:
    import html  # noqa
except ImportError:
    # py2: we need futures for this
    requires.append("future")


def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


def sphinx2rst(path):
    """turn a Sphinx file into simpler RST"""
    return re.sub(':[a-z]+:`~?(.*?)`',
                  r'`\1 <%s\1.html>`_' % mod.__website__,
                  read(path))


if __name__ == '__main__':
    setup(name=mod.__prog__,
          author=mod.__author__,
          author_email=mod.__email__,
          description=mod.__description__.replace('\n', ''),
          long_description=sphinx2rst('README.rst'),
          license=mod.__license_short__,
          url=mod.__website__,
          use_scm_version={
              'write_to': '%s/_version.py'
              % mod.__prog__,
          },
          packages=packages,
          package_data=package_data,
          entry_points={
              "console_scripts":
              [
                  "%s = %s.__main__:main"
                  % (mod.__prog__, mod.__prog__),
              ]
          },
          setup_requires=['setuptools_scm',
                          'pytest-runner',
                          'pytest-cov',
                          'sphinx',
                          ],
          install_requires=requires,
          extras_require={
              "dev": [
                  "pytest",
                  "tox",
                  "pyflakes",
              ],
          },
          tests_require=['pytest', 'betamax'],
          data_files=[
              # this completion file is generated with:
              # _FEED2EXEC_COMPLETE=source feed2exec
              # see http://click.pocoo.org/6/bashcomplete/
              #
              # we could also build it on the fly, but it's unlikely
              # to change, see also:
              # http://www.digip.org/blog/2011/01/generating-data-files-in-setup.py.html
              ('share/bash-completion/completions/', ['completion/feed2exec']),
          ],
          classifiers=classifiers,
          )
