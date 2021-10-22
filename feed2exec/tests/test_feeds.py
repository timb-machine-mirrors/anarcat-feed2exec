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

from feed2exec.model import (FeedConfStorage, FeedItemCacheStorage, Feed)
import feed2exec.plugins.echo
import feed2exec.utils as utils
from feed2exec.tests.fixtures import feed_manager  # noqa
import pytest

# XXX: bypass the Feed constructor so we don't create the cache
# database in ~/.cache/feed2exec.db by mistake during tests.
Feed._session = False

test_data = Feed('test',
                 {'url': 'file:///dev/null',
                  'output': None,
                  'args': None})
test_data2 = Feed('test2',
                  {'url': 'http://example.com/',
                   'output': None,
                   'args': None})
test_nasa = Feed('nasa-breaking-news',
                 {'url': 'file://%s'
                  % utils.find_test_file('breaking_news.xml'),
                  'filter': 'feed2exec.plugins.droptitle',
                  'filter_args': 'Trump',
                  'output': 'feed2exec.plugins.echo',
                  'args': 'test_nasa'})
test_sample = Feed('sample',
                   {'url': 'file://%s' % utils.find_test_file('sample.xml'),
                    'output': 'feed2exec.plugins.echo',
                    'args': '1 2 3 4'})
test_udd = Feed('udd',
                {'url': 'file://%s' % utils.find_test_file('udd.xml'),
                 'output': 'feed2exec.plugins.echo',
                 'args': 'test_udd'})
test_restic = Feed('restic',
                   {'url': 'file://%s' % utils.find_test_file('restic.xml'),
                    'filter': 'feed2exec.plugins.emptysummary'})
test_dates = Feed('date test',
                  {'url': 'file://' + utils.find_test_file('weird-dates.xml')})
test_params = Feed('params',
                   {'url': 'file://%s' % utils.find_test_file('sample.xml'),
                    'folder': 'test-folder',
                    'filter': 'feed2exec.plugins.echo',
                    'filter_args': 'test',
                    'output': 'feed2exec.plugins.echo',
                    'args': '1 2 3 4'})


def test_add(feed_manager):  # noqa
    assert test_data['name'] not in feed_manager.conf_storage, 'this is supposed to be empty'
    feed_manager.conf_storage.add(**test_data)
    assert test_data['name'] in feed_manager.conf_storage, 'contains works'
    with pytest.raises(AttributeError):
        feed_manager.conf_storage.add(**test_data)
    for r in feed_manager.conf_storage:
        assert test_data['name'] == r['name'], 'iterator works'
    feed_manager.conf_storage.remove(test_data['name'])
    assert test_data['name'] not in feed_manager.conf_storage, 'remove works'


def test_settings(feed_manager, capfd):  # noqa
    assert 0 == len(list(feed_manager.conf_storage)), "no params set yet"
    feed_manager.conf_storage.add(**test_params)
    assert 1 == len(list(feed_manager.conf_storage)), "params properly added"
    feed2exec.plugins.echo.output.called = False
    feed_manager.fetch()
    assert feed2exec.plugins.echo.output.called, "plugins get called correctly"

    feed2exec.plugins.echo.output.called = False
    feed_manager.conf_storage.set(test_params['name'], 'pause', 'True')
    feed_manager.fetch()
    assert not feed2exec.plugins.echo.output.called, "pause works"

    feed_manager.conf_storage.set(test_params['name'], 'catchup', 'True')
    feed_manager.conf_storage.set(test_params['name'], 'pause', 'False')
    assert not feed2exec.plugins.echo.output.called, "catchup works"
    out, err = capfd.readouterr()
    assert '1 2 3 4' in out, "... but still calls the plugin"

    feed_manager.conf_storage.remove_option(test_params['name'], 'filter')
    feed_manager.conf_storage.remove_option(test_params['name'], 'output')
    feed_manager.fetch()
    assert not feed2exec.plugins.echo.output.called, "removing plugins work"

    feed_manager.conf_storage.remove(test_params['name'])


def test_pattern(feed_manager):  # noqa
    feed_manager.conf_storage.add(**test_data)
    assert test_data['name'] in feed_manager.conf_storage, 'previous test should have ran'
    feed_manager.conf_storage.add(**test_data2)
    assert test_data2['name'] in feed_manager.conf_storage, 'second add works'
    feed_manager.pattern = 'test2'
    feeds = list(feed_manager.conf_storage)
    assert 1 == len(feeds), 'find only one item'
    feed_manager.pattern = 'test'
    feeds = list(feed_manager.conf_storage)
    assert 2 == len(feeds), 'find two items'


def test_cache(feed_manager):  # noqa
    db_path = feed_manager.db_path
    st = FeedItemCacheStorage(db_path, feed=test_data['name'])
    assert 'guid' not in st
    st.add('guid')
    assert 'guid' in st
    tmp = FeedItemCacheStorage(db_path)
    assert 'guid' in tmp
    st.add('another')
    for item in tmp:
        assert item
        if 'another' == item['guid']:
            break
    else:  # sanity check
        assert False, 'failed to iterate through storage'  # pragma: nocover
    for item in FeedItemCacheStorage(db_path, feed=test_data['name'], guid='guid'):
        assert 'another' not in item['guid']
    st.remove('guid')
    assert 'guid' not in st


def test_fetch(feed_manager):  # noqa
    feed_manager.conf_storage.add(**test_sample)

    feed2exec.plugins.echo.output.called = False
    feed_manager.fetch()
    cache = FeedItemCacheStorage(feed_manager.db_path, feed=test_sample['name'])
    assert feed2exec.plugins.echo.output.called
    assert '7bd204c6-1655-4c27-aeee-53f933c5395f' in cache

    feed_manager.conf_storage.add(**test_nasa)
    feed2exec.plugins.echo.output.called = False
    assert not feed2exec.plugins.echo.output.called
    feed_manager.fetch()
    assert ('test_nasa', ) == feed2exec.plugins.echo.output.called
    feed2exec.plugins.echo.output.called = False
    assert not feed2exec.plugins.echo.output.called
    feed_manager.conf_storage.add(**test_udd)
    feed_manager.fetch()
    assert ('test_udd', ) == feed2exec.plugins.echo.output.called


def test_fetch_parallel(feed_manager, capfd):  # noqa
    feed_manager.conf_storage.add(**test_sample)
    feed_manager.fetch(parallel=True, force=True)
    # can't use feed2exec.feeds.plugins.echo.output.called as it is
    # set in a separate process.
    out, err = capfd.readouterr()
    assert '1 2 3 4' in out
    feed_manager.fetch(parallel=2, force=True)
    out, err = capfd.readouterr()
    assert '1 2 3 4' in out


@pytest.mark.xfail(reason="cachecontrol does not know how to chain adapters")  # noqa
def test_fetch_cache(feed_manager):  # noqa
    '''that a second fetch returns no body'''
    feed = Feed('sample',
                {'url': 'http://planet.debian.org/rss20.xml',
                 'output': 'feed2exec.plugins.echo',
                 'args': 'noop'})
    content = feed_manager.fetch_one(feed)
    assert content is not None

    content = feed_manager.fetch_one(feed)
    # XXX: this will fail because betamax will bypass the cache and
    # repeat the request exactly as before. we need a way to put the
    # cache in front of betamax, but that doesn't work. see the mark
    # above and FeedManager.sessionConfig() for details.
    assert content is None


def test_normalize(feed_manager):  # noqa
    '''black box testing for :func:feeds.normalize_item()'''
    data = test_udd.parse(feed_manager.session.get(test_udd['url']).content)
    data = feed_manager.dispatch(test_udd, data)
    for item in data.entries:
        assert item.get('id')
    data = test_restic.parse(feed_manager.session.get(test_restic['url']).content)
    data = feed_manager.dispatch(test_restic, data)
    for item in data.entries:
        assert item.get('link').startswith('file://')
        assert 'restic.atom' not in item.get('link')
        # also test the "github filter"
        assert item.get('summary')
        assert item.get('link') in item.get('summary')
    data = test_dates.parse(feed_manager.session.get(test_dates['url']).content)
    data = feed_manager.dispatch(test_dates, data)
    for item in data['entries']:
        assert item.get('updated_parsed')


def test_config(tmpdir):  # noqa
    conf_path = tmpdir.join('feed2exec.ini')
    conf = FeedConfStorage(str(conf_path))
    conf.add(**test_sample)
    assert conf_path.check()
    expected = '''[sample]
url = %s
output = feed2exec.plugins.echo
args = 1 2 3 4

''' % test_sample['url']
    assert expected == conf_path.read()
    assert 'sample' in conf
    for feed in conf:
        assert type(feed) is feed2exec.model.Feed
    conf.remove('sample')
    assert '' == conf_path.read()
