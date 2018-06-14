#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

import json
import re

from click.testing import CliRunner
import html2text
import pytest
import xdg.BaseDirectory

import feed2exec.utils as utils
from feed2exec.__main__ import main
from feed2exec.tests.test_feeds import (test_sample, test_nasa)
from feed2exec.tests.fixtures import (static_boundary)  # noqa


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert 0 == result.exit_code


def test_basics(tmpdir_factory, static_boundary):  # noqa
    runner = CliRunner()
    d = tmpdir_factory.mktemp('basics')
    conf_path = d.join('feed2exec.ini')
    db_path = d.join('feed2exec.db')
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add',
                                  '--output', 'feed2exec.plugins.echo',
                                  test_sample['name'],
                                  test_sample['url']])
    assert conf_path.check()
    assert 0 == result.exit_code
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add',
                                  test_sample['name'],
                                  test_sample['url']])
    assert 2 == result.exit_code
    assert 'already exists' in result.output
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'ls'])
    assert 0 == result.exit_code
    del test_sample['args']
    expected = json.dumps(test_sample, indent=2, sort_keys=True)
    assert expected == result.output.strip()
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'rm', test_sample['name']])
    assert 0 == result.exit_code
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'ls'])
    assert 0 == result.exit_code
    assert "" == result.output

    maildir = tmpdir_factory.mktemp('maildir')
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add',
                                  '--output', 'maildir',
                                  '--mailbox', str(maildir),
                                  test_nasa['name'],
                                  test_nasa['url']])
    assert conf_path.check()
    assert 'feed2exec.plugins.maildir' in conf_path.read()
    assert 0 == result.exit_code

    test_path = utils.find_test_file('planet-debian.xml')
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add', 'planet-debian',
                                  'file://' + test_path,
                                  '--args', 'to@example.com',
                                  '--mailbox', str(maildir)])
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'fetch'])
    assert 0 == result.exit_code
    assert maildir.check()
    for path in maildir.join('planet-debian').join('new').visit():
        body = path.read()
        if 'Marier' in body:
            break
    else:  # sanity check
        assert False, "Francois Marier item not found"  # pragma: nocover


def test_relative_conf(tmpdir):
    '''this checks if specifying a config/db without a relative or
    absolute directory works. in older versions of
    utils.make_dirs_helper, this would crash.
    '''
    runner = CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ['--config', 'test.ini',
                                      'add',
                                      test_sample['name'],
                                      test_sample['url']])
        assert 0 == result.exit_code
        result = runner.invoke(main, ['--config', 'test.ini',
                                      '--database', 'test.db',
                                      'fetch', '--catchup'], catch_exceptions=False)
        assert 0 == result.exit_code
    assert tmpdir.join('test.ini').check()
    assert tmpdir.join('test.db').check()
    assert 0 == result.exit_code


def test_parse(tmpdir_factory):  # noqa
    runner = CliRunner()
    d = tmpdir_factory.mktemp('parse')
    conf_path = d.join('feed2exec.ini')
    db_path = d.join('feed2exec.db')
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'parse',
                                  '--output', 'feed2exec.plugins.echo',
                                  '--args', 'foo bar',
                                  test_sample['url']])
    assert 0 == result.exit_code
    assert not conf_path.check()
    assert db_path.check()
    assert "foo bar\n" == result.output


@pytest.mark.regression(issue=1)
def test_missing_conf(tmpdir_factory, monkeypatch):
    tmpdir = tmpdir_factory.mktemp('missing')
    # XXX: dumb xdg limitation: changing the environment doesn't
    # change those variables since they are only set at load time
    # https://bugs.freedesktop.org/show_bug.cgi?id=103943
    monkeypatch.setattr(xdg.BaseDirectory, 'xdg_config_home', str(tmpdir))
    monkeypatch.setattr(xdg.BaseDirectory, 'xdg_config_dirs', [str(tmpdir)])
    runner = CliRunner(env={'XDG_CONFIG_HOME': str(tmpdir)})
    result = runner.invoke(main, ['--debug', 'add', test_sample['name'], test_sample['url']],
                           catch_exceptions=False)
    print("output: " + result.output)
    assert 0 == result.exit_code
    assert tmpdir.join('feed2exec.ini').check()


@pytest.mark.xfail(condition=html2text.__version__ < (2017, 10, 4), reason="older html2text output varies, install version 2017.10.4 or later")  # noqa
def test_planet(tmpdir_factory, static_boundary, betamax_session):  # noqa
    """test i18n feeds for double-encoding

    previously, we would double-encode email bodies and subject, which
    would break display of any feed item with unicode.
    """
    d = tmpdir_factory.mktemp('planet')
    mbox_dir = d.join('Mail')
    conf_path = d.join('feed2exec.ini')
    db_path = d.join('feed2exec.db')
    runner = CliRunner()

    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add', 'planet-debian',
                                  'http://planet.debian.org/rss20.xml',
                                  '--args', 'to@example.com',
                                  '--output', 'feed2exec.plugins.mbox',
                                  '--mailbox', str(mbox_dir)])
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'fetch'],
                           obj={'session': betamax_session},
                           catch_exceptions=False)
    assert 0 == result.exit_code
    r = re.compile('User-Agent: .*$', flags=re.MULTILINE)
    with open(utils.find_test_file('../cassettes/planet-debian.mbx')) as expected:  # noqa
        expected = r.sub('', expected.read())
        actual = r.sub('', mbox_dir.join('planet-debian.mbx').read())
        assert expected == actual
