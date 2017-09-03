#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

from feed2exec.feeds import FeedStorage, FeedCacheStorage
import pytest
import sqlite3


test_data = {'url': 'file:///dev/null',
             'name': 'test',
             'plugin': None,
             'args': None}
test_data2 = {'url': 'http://example.com/',
              'name': 'test2',
              'plugin': None,
              'args': None}


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

