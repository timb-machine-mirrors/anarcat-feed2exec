import datetime
import email
import logging

import pytest

from feed2exec.plugins import plugin_output
import feed2exec.plugins.maildir as maildir_plugin


logging.basicConfig(format='%(message)s', level='DEBUG')


def test_maildir(tmpdir):
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


def test_echo(capfd):
    plugin_output({'plugin': 'feed2exec.plugins.echo', 'args': 'foobar'}, {})
    out, err = capfd.readouterr()
    assert out == "arguments received: ('foobar',), kwargs: {}\n"


def test_error():
    # shouldn't raise
    plugin_output({'plugin': 'feed2exec.plugins.error', 'args': ''}, {})
