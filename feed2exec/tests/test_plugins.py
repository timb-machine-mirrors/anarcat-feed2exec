import datetime
import email
import logging

import pytest

from feed2exec.feeds import FeedStorage, fetch_feeds, parse
from feed2exec.plugins import plugin_output
import feed2exec.plugins.maildir as maildir_plugin
from feed2exec.tests.test_feeds import test_sample, test_db


logging.basicConfig(format='%(message)s', level='DEBUG')


def test_maildir(tmpdir, test_db):
    f = maildir_plugin.Output(str(tmpdir.join('Mail')), 'INBOX',
                              'body', 'subject', datetime.datetime.now(),
                              'devnull@example.com', 'nobody@example.com')
    message = tmpdir.join('Mail', 'INBOX', 'new', f.key)
    assert message.check()
    raw = message.read()
    assert 'base64' not in raw and '==' not in raw

    # subject header hijack protection
    with pytest.raises(email.errors.HeaderParseError):
        maildir_plugin.Output(str(tmpdir.join('Mail')), 'INBOX',
                              'body', 'subject\nX-Header-Hijack: true',
                              datetime.datetime.now(),
                              'devnull@example.com', 'nobody@example.com')
    maildir_sample = {'name': 'maildir test',
                      'url': test_sample['url'],
                      'plugin': 'feed2exec.plugins.maildir',
                      'args': '/home/anarcat/Maildir/ %(name)s %(summary)s%(link)s %(title)s %(published)s foo@example.com me@example.com'}
    data = parse(maildir_sample['url'])
    for entry in data['entries']:
        f = plugin_output(maildir_sample, entry)
        message = tmpdir.join('Mail', 'INBOX', 'new', f.key)
        message.check()
        assert message.read() == ''


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
    assert e.returncode == 0
