from __future__ import division, absolute_import
from __future__ import print_function

from glob import glob
import datetime
import email
try:
    import unittest.mock as mock
except ImportError:
    # py2
    import mock
import os
import os.path
import re

import feedparser
import pytest

import feed2exec
import feed2exec.utils as utils
from feed2exec.feeds import parse, fetch
import feed2exec.plugins as plugins
import feed2exec.plugins.maildir as maildir_plugin
from feed2exec.tests.test_feeds import test_sample
from feed2exec.tests.fixtures import (test_db, static_boundary)  # noqa


def test_maildir(tmpdir, test_db, static_boundary):  # noqa
    global LOCK
    LOCK = mock.MagicMock()

    feed = {'name': 'INBOX', "mailbox": str(tmpdir.join('Mail'))}
    entry = {'summary': 'body',
             'title': 'subject',
             'link': 'http://example.com/',
             'published_parsed': datetime.datetime.now()}

    f = maildir_plugin.output(to_addr='nobody@example.com',
                              feed=feed, entry=entry, lock=LOCK)
    message = tmpdir.join('Mail', 'inbox', 'new', f.key)
    assert message.check()
    raw = message.read()
    assert 'base64' not in raw
    assert '==' not in raw

    # subject header hijack protection
    entry['title'] = 'subject\nX-Header-Hijack: true'
    with pytest.raises(email.errors.HeaderParseError):
        maildir_plugin.output(to_addr='nobody@example.com',
                              feed=feed, entry=entry, lock=LOCK)
    sample = {'name': 'maildir test',
              'url': test_sample['url'],
              'email': 'from@example.com',
              'output': 'feed2exec.plugins.maildir',
              'mailbox': str(tmpdir.join('Mail')),
              'args': 'to@example.com'}
    body = fetch(sample['url'])
    data = parse(body, sample, lock=LOCK)
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
Archive-At: http://www.example.com/blog/post/1

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
    body = fetch(sample['url'])
    data = parse(body, sample, lock=LOCK)
    for entry in data['entries']:
        f = plugins.output(sample, entry, lock=LOCK)
        message = tmpdir.join('Mail', 'folder-test', 'new', f.key)
        assert message.check()


def test_email(tmpdir, test_db, static_boundary):  # noqa
    global LOCK
    LOCK = mock.MagicMock()

    testdir = utils.find_test_file('.')
    for path in glob(os.path.join(testdir, '*.xml')):
        feed = {'url': 'file://' + path,
                'name': os.path.basename(path)[:-4],
                'output': 'feed2exec.plugins.mbox',
                'mailbox': str(tmpdir.join('Mail')),
                'email': 'from@example.com',
                'args': 'to@example.com',
                }
        body = fetch(feed['url'])
        parse(body, feed, lock=LOCK)
        p = path[:-3] + 'mbx'
        with open(p) as expected:
            folder = utils.slug(feed['name']) + '.mbx'
            r = re.compile('User-Agent: .*$', flags=re.MULTILINE)
            actual = r.sub('', tmpdir.join('Mail', folder).read())
            expect = r.sub('', expected.read())
            assert actual
            assert actual == expect
    assert path


def test_echo(capfd):
    item = feedparser.FeedParserDict({'title': 'bar'})
    e = plugins.output(feed={'output': 'feed2exec.plugins.echo',
                             'args': 'foo {item[title]}'},
                       item=item)
    assert e.called
    out, err = capfd.readouterr()
    assert out == """arguments received: ('foo', 'bar')\n"""


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
    assert out == "1\n"
    assert e == 0


def test_filter():
    item = {'title': 'test'}
    copy = item.copy()
    p = plugins.filter(feed={'filter': 'feed2exec.plugins.echo'}, item=item)
    assert item == copy
    assert p
    assert p.called is not None
    item = {'title': 'test'}
    plugins.filter(feed={'filter': 'feed2exec.plugins.null'}, item=item)
    assert item != copy
    assert p.called is not None
