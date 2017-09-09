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


from . import feed2exec


mod = feed2exec


def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(name=mod.__prog__,
      author="Antoine Beaupré",
      author_email="anarcat@debian.org",
      description=mod.__description__,
      long_description=re.sub(':[a-z]+:`~?(.*?)`', r'``\1``',
                              read('README.rst')),
      platforms='Debian',
      license=mod.__license_short__,
      url=mod.__website__,
      use_scm_version={
          'write_to': '%s/_version.py'
          % mod.__prog__,
      },
      packages=[mod.__prog__],
      entry_points={
          "console_scripts":
          [
              "%s = %s.__main__:main"
              % (mod.__prog__, mod.__prog__),
          ]
      },
      setup_requires=['setuptools_scm',
                      'pytest-runner',
                      'sphinx',
                      ],
      install_requires=[
          "click",
          "feedparser",
          "requests",
          "sqlite3",
      ],
      extras_require={
          "dev": [
              "pytest",
              "tox",
              "pyflakes",
          ],
      },
      tests_require=['pytest'],
      classifiers=[
          'Development Status :: 2 - Pre-Alpha',
          'Environment :: Console',
          'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
          'Natural Language :: English',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          ],
      )
