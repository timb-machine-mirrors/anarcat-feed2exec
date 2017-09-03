#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

from feed2exec.feeds import FeedStorage, FeedCacheStorage
import pytest


@pytest.fixture(scope='session')
def test_db(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp('feed2exec')
    return str(tmpdir.join('feed2exec.db'))


def test_add(test_db):
    st = FeedStorage(path=test_db)
    assert 'test' not in st, 'this is supposed to be empty'
    st.add('test', 'file:///dev/null', '')
    assert 'test' in st, 'contains works'
    for r in st:
        assert r['name'] == 'test', 'iterator works'
    st.remove('test')
    assert 'test' not in st, 'remove works'


def test_cache(test_db):
    st = FeedCacheStorage(path=test_db, feed='test')
    assert 'guid' not in st
    st.add('guid')
    assert 'guid' in st

