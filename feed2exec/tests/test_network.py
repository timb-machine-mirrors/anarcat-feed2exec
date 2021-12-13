#!/usr/bin/python3
# coding: utf-8

"""tests in this file may use the network

Test failures can be avoided by setting the PYTEST_USENETWORK to
"no".
"""

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

import os

from feed2exec.model import Feed
import pytest


@pytest.mark.xfail(
    condition=os.environ.get('PYTEST_USENETWORK') == 'no',
    reason="network may be unavailable",
)
def test_cachecontrol(feed_manager_networked):
    """test for https://gitlab.com/anarcat/feed2exec/-/issues/22"""
    f = Feed('test', {
        # this URL *MUST* send Expires header to trigger the
        # interoperability bug between feed2exec and cachecontrol
        'url': 'https://anarc.at/blog/index.rss',
        'output': None,
        'args': None,
    })
    assert feed_manager_networked.fetch_one(f) is not None
