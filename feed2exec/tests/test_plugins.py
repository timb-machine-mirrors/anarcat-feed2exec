from __future__ import division, absolute_import
from __future__ import print_function

from glob import glob
import datetime
import email
try:  # pragma nocover
    import unittest.mock as mock
except ImportError:  # pragma nocover
    # py2
    import mock  # type: ignore
import os
import os.path
from pkg_resources import parse_version
import re
import subprocess
from time import sleep

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
from feed2exec.tests.fixtures import (feed_manager, feed_manager_recorder, static_boundary, logging_handler)  # noqa


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
@pytest.mark.xfail(condition=html2text.__version__ < (2020, 1, 16), reason="older html2text output varies, install version 2020.1.16 or later")  # noqa
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


@pytest.fixture(params=['page', 'full'])
def wayback_feed(request):
    config = {'output': 'feed2exec.plugins.wayback', 'args': request.param}
    return Feed('wayback test', config)


def test_wayback_archive(feed_manager, logging_handler, wayback_feed):  # noqa
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    item = feedparser.FeedParserDict({'link': 'http://archive.org/'})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert not e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'WARNING' == record.levelname
    if full:
        assert 'wayback machine failed to save URL %s: %s' == record.msg
        error = record.args[1]
    else:
        assert 'wayback machine failed to save URL %s, status %d %s: %s' == record.msg
        assert 523 == record.args[1]
        error = record.args[3]
    assert 'Cannot save Internet Archive URLs! http://archive.org/.' == error


def test_wayback_invalid_example(feed_manager, logging_handler, wayback_feed):  # noqa
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    item = feedparser.FeedParserDict({'link': 'http://invalid.example.com/'})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert not e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'WARNING' == record.levelname
    if full:
        assert 'wayback machine failed to save URL %s: %s' == record.msg
        error = record.args[1]
    else:
        assert 'wayback machine failed to save URL %s, status %d %s: %s' == record.msg
        assert 523 == record.args[1]
        error = record.args[3]
    assert 'Cannot resolve host invalid.example.com.' == error


def test_wayback_example_invalid(feed_manager, logging_handler, wayback_feed):  # noqa
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    item = feedparser.FeedParserDict({'link': 'http://example.invalid/'})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert not e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'WARNING' == record.levelname
    if full:
        assert 'wayback machine failed to save URL %s: %s' == record.msg
        error = record.args[1]
    else:
        assert 'wayback machine failed to save URL %s, status %d %s: %s' == record.msg
        assert 523 == record.args[1]
        error = record.args[3]
    assert 'http://example.invalid/ URL syntax is not valid.' == error


def test_wayback_example_working(feed_manager, logging_handler, wayback_feed):  # noqa
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    if full:
        link = 'http://example.com/'
    else:
        link = 'http://www.example.com/'
    item = feedparser.FeedParserDict({'link': link})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'INFO' == record.levelname
    if full:
        assert 'URL %s with resources probably saved to wayback machine' == record.msg
    else:
        assert 'URL %s saved without resources to wayback machine: %s' == record.msg
        assert record.args[1].startswith('https://web.archive.org/web/')


def test_wayback_example_too_fast(feed_manager_recorder, logging_handler, wayback_feed):  # noqa
    recorder, feed_manager = feed_manager_recorder  # noqa
    # SPN1 does not error when archiving the same domain too fast
    # so this test is only applicable to the SPN2 API.
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    if not full:
        pytest.skip()
    # Use example.org so we do not get false failures
    # due to other tests, which all use example.com
    item = feedparser.FeedParserDict({'link': 'http://example.org/'})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'INFO' == record.levelname
    assert 'URL %s with resources probably saved to wayback machine' == record.msg

    # Wait for the wayback machine to register the first request for the URL
    # otherwise the second archiving request will succeed instead of failing.
    # Don't bother waiting when we aren't really interacting with archive.org.
    if recorder.current_cassette.is_recording():
        sleep(30)

    # Drop the messages from the first archiving request
    logging_handler.buffer.clear()

    # Now test that second archiving of same URL fails with "too fast" msg
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert not e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'WARNING' == record.levelname
    assert 'wayback machine failed to save URL %s: %s' == record.msg
    assert re.match(
        r'The same snapshot had been made .* ago\. We only allow new captures of the same URL every \d+ minutes\.',
        record.args[1]
    )


def test_wayback_example_404(feed_manager, logging_handler, wayback_feed):  # noqa
    # SPN2 does not return errors for HTTP error codes
    # even if the error page archiving is turned off.
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    if full:
        pytest.skip()
    item = feedparser.FeedParserDict({'link': 'http://example.com/404'})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert not e
    for record in logging_handler.buffer:
        if 'wayback machine' in record.getMessage():
            break
    else:  # sanity check
        raise AttributeError('no wayback logs generated?')  # pragma: nocover
    assert 'WARNING' == record.levelname
    assert 'wayback machine failed to save URL %s, status %d %s: %s' == record.msg
    assert 523 == record.args[1]
    assert 'The server cannot find the requested resource http://example.com/404 (HTTP status=404).' == record.args[3]


def test_wayback_catchup(feed_manager, logging_handler, wayback_feed):  # noqa
    full = 'args' not in wayback_feed or 'full' in wayback_feed['args']
    if full:
        links = [
            'https://anarc.at/wikiicons/diff.png',
            'http://example.net/',
        ]
    else:
        links = [
            'https://anarc.at/wikiicons/email.png',
            'http://www.example.net/',
        ]
    item = feedparser.FeedParserDict({'link': links[0]})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert e

    called = False

    def fake(*args, **kwargs):
        nonlocal called
        called = True
        return mock.MagicMock()

    feed_manager.session.get = fake
    feed_manager.session.post = fake
    item = feedparser.FeedParserDict({'link': links[1]})
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
    assert called
    wayback_feed['catchup'] = True
    called = False
    e = plugins.output(feed=wayback_feed, item=item, session=feed_manager.session)
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
