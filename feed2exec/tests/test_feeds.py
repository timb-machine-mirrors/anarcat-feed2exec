#!/usr/bin/python3
# coding: utf-8

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

import logging
import os.path
import pkg_resources

from feed2exec import __prog__
from feed2exec.feeds import FeedStorage, FeedCacheStorage, fetch_feeds
import feed2exec.plugins.echo
import feed2exec.feeds as feedsmod
import pytest
import sqlite3

logging.basicConfig(format='%(message)s', level='DEBUG')

test_data = {'url': 'file:///dev/null',
             'name': 'test',
             'plugin': None,
             'args': None}
test_data2 = {'url': 'http://example.com/',
              'name': 'test2',
              'plugin': None,
              'args': None}


def find_test_file(name):
    try:
        pkg = pkg_resources.Requirement.parse(__prog__)
        path = os.path.join(__prog__, 'tests', 'files', name)
        return pkg_resources.resource_filename(pkg, path)
    except pkg_resources.DistributionNotFound:
        return os.path.join(os.path.dirname(__file__), 'files', name)


test_sample = {'url': 'file://%s' % find_test_file('sample.xml'),
               'name': 'sample',
               'plugin': 'feed2exec.plugins.echo',
               'args': '1 2 3 4'}


@pytest.fixture(scope='session')
def test_db(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp('feed2exec')
    return tmpdir.join('feed2exec.db')


def test_add(test_db):
    st = FeedStorage(path=str(test_db))
    assert test_data['name'] not in st, 'this is supposed to be empty'
    st.add(**test_data)
    assert test_data['name'] in st, 'contains works'
    with pytest.raises(sqlite3.IntegrityError):
        st.add(**test_data)
    for r in st:
        assert r['name'] == test_data['name'], 'iterator works'
    st.remove(test_data['name'])
    assert test_data['name'] not in st, 'remove works'


def test_pattern(test_db):
    st = FeedStorage(path=str(test_db))
    st.add(**test_data)
    assert test_data['name'] in st, 'previous test should have ran'
    st.add(**test_data2)
    assert test_data2['name'] in st, 'second add works'
    feeds = list(FeedStorage(path=str(test_db), pattern='test2'))
    assert len(feeds) == 1, 'find only one entry'
    feeds = list(FeedStorage(path=str(test_db), pattern='test'))
    assert len(feeds) == 2, 'find two entries'


def test_cache(test_db):
    st = FeedCacheStorage(path=str(test_db), feed=test_data['name'])
    assert 'guid' not in st
    st.add('guid')
    assert 'guid' in st
    tmp = FeedCacheStorage(path=str(test_db))
    assert 'guid' in tmp
    st.remove('guid')
    assert 'guid' not in st


def test_fetch(test_db):
    st = FeedStorage(path=str(test_db))
    st.add(**test_sample)

    fetch_feeds(database=str(test_db))
    logging.info('looking through cache')
    cache = FeedCacheStorage(path=str(test_db), feed=test_sample['name'])
    assert '7bd204c6-1655-4c27-aeee-53f933c5395f' in cache
    assert feed2exec.plugins.echo.Output.called == ('1', '2', '3', '4')
