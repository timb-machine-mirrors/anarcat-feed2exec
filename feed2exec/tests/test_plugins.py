import datetime
import email
import logging

import pytest

from feed2exec.feeds import parse, fetch
from feed2exec.plugins import plugin_output
import feed2exec.plugins.maildir as maildir_plugin
from feed2exec.tests.test_feeds import test_sample, test_db


logging.basicConfig(format='%(message)s', level='DEBUG')


def test_maildir(tmpdir, test_db):

    feed = {'name': 'INBOX'}
    entry = {'summary': 'body',
             'title': 'subject',
             'link': 'http://example.com/',
             'published_parsed': datetime.datetime.now()}

    f = maildir_plugin.output(str(tmpdir.join('Mail')),
                              to_addr='nobody@example.com',
                              feed=feed, entry=entry)
    message = tmpdir.join('Mail', 'INBOX', 'new', f.key)
    assert message.check()
    raw = message.read()
    assert 'base64' not in raw and '==' not in raw

    # subject header hijack protection
    entry['title'] = 'subject\nX-Header-Hijack: true'
    with pytest.raises(email.errors.HeaderParseError):
        maildir_plugin.output(str(tmpdir.join('Mail')),
                              to_addr='nobody@example.com',
                              feed=feed, entry=entry)
    sample = {'name': 'maildir test',
              'url': test_sample['url'],
              'plugin': 'feed2exec.plugins.maildir',
              'args': str(tmpdir.join('Mail'))}
    body = fetch(sample['url'])
    data = parse(body, sample)
    for entry in data['entries']:
        f = plugin_output(sample, entry)
        message = tmpdir.join('Mail', 'maildir test', 'new', f.key)
        assert message.check()
        assert message.read() == '''From: maildir test
To: anarcat@curie.anarc.at
Subject: Example entry
Date: Sun, 06 Sep 2009 21:20:00 -0000
Content-Transfer-Encoding: quoted-printable
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

http://www.example.com/blog/post/1

Here is some text containing an interesting description.'''


def test_echo(capfd):
    plugin_output({'plugin': 'feed2exec.plugins.echo', 'args': 'foobar'}, {})
    out, err = capfd.readouterr()
    assert out == """arguments received: ('foobar',), kwargs: {"entry": {}, "feed": {"args": "foobar", "plugin": "feed2exec.plugins.echo"}}\n"""


def test_error():
    # shouldn't raise
    plugin_output({'plugin': 'feed2exec.plugins.error', 'args': ''}, {})


def test_exec(capfd):
    e = plugin_output({'plugin': 'feed2exec.plugins.exec', 'args': 'seq 1'}, {})
    out, err = capfd.readouterr()
    assert out == "1\n"
    assert e == 0
