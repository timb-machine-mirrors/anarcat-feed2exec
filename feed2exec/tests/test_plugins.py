from __future__ import division, absolute_import
from __future__ import print_function

from glob import glob
import datetime
import email
import logging
import logging.handlers
try:  # pragma nocover
    import unittest.mock as mock
except ImportError:  # pragma nocover
    # py2
    import mock
import os
import os.path
from pkg_resources import parse_version
import re
import subprocess

import feedparser
import html2text
import pytest


import feed2exec
import feed2exec.utils as utils
from feed2exec.controller import Feed
import feed2exec.plugins as plugins
import feed2exec.plugins.maildir as maildir_plugin
import feed2exec.plugins.transmission as transmission_plugin
import feed2exec.plugins.archive as archive_plugin
from feed2exec.tests.test_feeds import test_sample, test_params
from feed2exec.tests.fixtures import (feed_manager, static_boundary)  # noqa


def test_maildir(tmpdir, feed_manager, static_boundary):  # noqa
    global LOCK
    LOCK = mock.MagicMock()

    feed = {'name': 'INBOX', "mailbox": str(tmpdir.join('Mail'))}
    item = {'summary': 'body',
            'title': 'subject',
            'link': 'http://example.com/',
            'published_parsed': datetime.datetime.now()}

    f = maildir_plugin.output(to_addr='nobody@example.com', session=feed_manager.session,
                              feed=feed, item=item, lock=LOCK)
    message = tmpdir.join('Mail', 'inbox', 'new', f.key)
    assert message.check()
    raw = message.read()
    assert 'base64' not in raw
    assert '==' not in raw

    # subject header hijack protection
    item['title'] = 'subject\nX-Header-Hijack: true'
    with pytest.raises(email.errors.HeaderParseError):
        maildir_plugin.output(to_addr='nobody@example.com', session=feed_manager.session,
                              feed=feed, item=item, lock=LOCK)
    sample = Feed('maildir test',
                  {'url': test_sample['url'],
                   'email': 'from@example.com',
                   'output': 'feed2exec.plugins.maildir',
                   'mailbox': str(tmpdir.join('Mail')),
                   'args': 'to@example.com'})
    body = feed_manager.session.get(sample['url']).content
    data = feed_manager.dispatch(sample, sample.parse(body), lock=LOCK)
    folder = utils.slug(sample['name'])
    for message in tmpdir.join('Mail', folder, 'new').visit():
        expected = '''Content-Type: multipart/alternative; boundary="===============testboundary=="
MIME-Version: 1.0
Date: Sun, 06 Sep 2009 16:20:00 -0000
To: to@example.com
From: test author <from@example.com>
Subject: Example entry
Message-ID: 7bd204c6-1655-4c27-aeee-53f933c5395f
User-Agent: feed2exec (%s)
Precedence: list
Auto-Submitted: auto-generated
Archived-At: http://www.example.com/blog/post/1

--===============testboundary==
Content-Type: text/html; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 8bit

This is the  body, which should show instead of the above
--===============testboundary==
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 8bit

http://www.example.com/blog/post/1

This is the body, which should show instead of the above


--===============testboundary==--
'''  # noqa
        assert (expected % feed2exec.__version__) == message.read()
    # test if folder setting works
    sample['folder'] = 'folder-test'
    body = feed_manager.session.get(sample['url']).content
    data = feed_manager.dispatch(sample, sample.parse(body), lock=LOCK)
    for item in data['entries']:
        f = plugins.output(sample, item, lock=LOCK, session=feed_manager.session)
        message = tmpdir.join('Mail', 'folder-test', 'new', f.key)
        assert message.check()

    tmpdir.join('Mail', 'inbox').remove()
    feed['catchup'] = True
    f = maildir_plugin.output(to_addr='nobody@example.com', session=feed_manager.session,
                              feed=feed, item=item, lock=LOCK)
    message = tmpdir.join('Mail', 'inbox', 'new', f.key)
    assert not message.check()


@pytest.mark.xfail(condition=parse_version(feedparser.__version__) < parse_version('5.2.1'), reason="older feedparser version do not sort <img> tags, install feedparser 5.2.1 or later")  # noqa
@pytest.mark.xfail(condition=html2text.__version__ < (2019, 9, 26), reason="older html2text output varies, install version 2019.9.26 or later")  # noqa
def test_email(tmpdir, feed_manager, static_boundary):  # noqa
    global LOCK
    LOCK = mock.MagicMock()

    testdir = utils.find_test_file('.')
    for path in glob(os.path.join(testdir, '*.xml')):
        feed = Feed(os.path.basename(path)[:-4],
                    {'url': 'file://' + path,
                     'output': 'feed2exec.plugins.mbox',
                     'mailbox': str(tmpdir.join('Mail')),
                     'email': 'from@example.com',
                     'args': 'to@example.com',
                     'filter': 'feed2exec.plugins.droptitle',
                     'filter_args': 'Trump'})
        body = feed_manager.session.get(feed['url']).content
        feed_manager.dispatch(feed, feed.parse(body), lock=LOCK)
        folder = utils.slug(feed['name']) + '.mbx'
        ua_pattern = re.compile('User-Agent: .*$', flags=re.MULTILINE)
        actual = ua_pattern.sub('', tmpdir.join('Mail', folder).read())
        assert actual

        mbox_path = path[:-3] + 'mbx'
        try:
            with open(mbox_path) as expected:
                expect = ua_pattern.sub('', expected.read())
        except FileNotFoundError:
            # ignore missing mailbox samples
            pass
        else:
            assert expect == actual
    assert path


def test_echo(capfd):
    item = feedparser.FeedParserDict({'title': 'bar'})
    e = plugins.output(feed={'output': 'feed2exec.plugins.echo',
                             'args': 'foo {item[title]}'},
                       item=item)
    assert e.called
    out, err = capfd.readouterr()
    assert "foo bar\n" == out


def test_error():
    # shouldn't raise
    plugins.output(feed={'output': 'feed2exec.plugins.error',
                         'args': ''},
                   item={})


def test_exec(capfd):
    e = plugins.output(feed={'output': 'feed2exec.plugins.exec',
                             'args': 'seq 1'},
                       item={})
    out, err = capfd.readouterr()
    assert "1\n" == out
    assert 0 == e
    e = plugins.output(feed={'output': 'feed2exec.plugins.exec',
                             'args': 'seq 1', 'catchup': 'True'},
                       item={})
    out, err = capfd.readouterr()
    assert "" == out
    assert e


def test_filter():
    item = {'title': 'test'}
    expected = item.copy()
    p = plugins.filter(feed={'filter': 'feed2exec.plugins.echo'}, item=item)
    assert expected == item
    assert p
    assert p.called is not None
    item = {'title': 'test'}
    plugins.filter(feed={'filter': 'feed2exec.plugins.null'}, item=item)
    assert expected != item
    assert p.called is not None


def test_wayback(capfd, feed_manager):  # noqa
    handler = logging.handlers.MemoryHandler(0)
    handler.setLevel('INFO')
    logging.getLogger('').addHandler(handler)
    logging.getLogger('').setLevel('DEBUG')
    feed = Feed('wayback test', {'output': 'feed2exec.plugins.wayback'})
    item = feedparser.FeedParserDict({'link': 'http://example.com/'})
    e = plugins.output(feed=feed, item=item, session=feed_manager.session)
    assert e
    for record in handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'INFO' == record.levelname
    assert 'URL %s saved to wayback machine: %s' == record.msg
    handler.buffer = []
    item = feedparser.FeedParserDict({'link': 'http://example.com/404'})
    e = plugins.output(feed=feed, item=item, session=feed_manager.session)
    assert not e
    for record in handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'WARNING' == record.levelname
    assert 'wayback machine failed to save URL %s, status %d' == record.msg
    handler.buffer = []

    item = feedparser.FeedParserDict({'link':
                                      'https://anarc.at/wikiicons/email.png'})
    e = plugins.output(feed=feed, item=item, session=feed_manager.session)
    assert e

    called = False

    def fake(*args, **kwargs):
        nonlocal called
        called = True
        return mock.MagicMock()

    feed_manager.session.get = fake
    item = feedparser.FeedParserDict({'link': 'http://example.com/'})
    e = plugins.output(feed=feed, item=item, session=feed_manager.session)
    assert called
    feed['catchup'] = True
    called = False
    e = plugins.output(feed=feed, item=item, session=feed_manager.session)
    assert not called


def test_transmission(monkeypatch):
    capture = []

    def fake_call(*args, **kwargs):
        capture.append(*args)

    monkeypatch.setattr(subprocess, 'check_call', fake_call)
    item = {'summary': 'body',
            'title': 'Evil/../../../etc/password',
            'link': 'http://example.com/',
            'published_parsed': datetime.datetime.now()}
    transmission_plugin.output(hostname='example.com',
                               feed=test_sample, item=item)
    assert [['transmission-remote', 'example.com',
             '-a', 'http://example.com/']] == capture
    capture = []
    transmission_plugin.output(hostname='example.com',
                               feed=test_params, item=item)
    assert [['transmission-remote', 'example.com',
             '-a', 'http://example.com/',
             '-w', 'test-folder/Evil.etc.password']] == capture
    test_params['catchup'] = True
    capture = []
    transmission_plugin.output(hostname='example.com',
                               feed=test_params, item=item)
    assert [] == capture


def test_archive(tmpdir, feed_manager):  # noqa
    dest = tmpdir.join('archive')
    feed = Feed('test archive', test_sample)
    item = feedparser.FeedParserDict({'link': 'http://example.com/',
                                      'title': 'example site'})
    assert archive_plugin.output(str(dest), feed=feed, item=item, session=feed_manager.session)
    assert dest.join('example-site').check()
    dest.remove()
    item = feedparser.FeedParserDict({'link': 'http://example.com/404',
                                      'title': 'example site'})
    assert not archive_plugin.output(str(dest), feed=feed, item=item, session=feed_manager.session)
    assert not dest.join('example-site').check()
    # no link
    item = feedparser.FeedParserDict({'title': 'example site'})
    assert archive_plugin.output(str(dest), feed=feed, item=item, session=feed_manager.session)
    assert not dest.join('example-site').check()
    feed['catchup'] = True
    item = feedparser.FeedParserDict({'link': 'http://example.com/',
                                      'title': 'example site'})
    assert archive_plugin.output(str(dest), feed=feed, item=item, session=feed_manager.session)
    assert not dest.join('example-site').check()
