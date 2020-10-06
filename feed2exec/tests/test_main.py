#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

import json
import os.path
import re

from click.testing import CliRunner
import html2text
import pytest
import xdg.BaseDirectory

import feed2exec.utils as utils
from feed2exec.__main__ import main
from feed2exec.tests.test_feeds import (test_sample, test_nasa)
from feed2exec.tests.fixtures import (static_boundary, feed_manager)  # noqa


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert 0 == result.exit_code


def test_basics(tmpdir_factory, feed_manager, static_boundary):  # noqa
    runner = CliRunner()
    result = runner.invoke(main, ['add',
                                  '--output', 'feed2exec.plugins.echo',
                                  test_sample['name'],
                                  test_sample['url']],
                           obj={'feed_manager_override': feed_manager})
    assert os.path.exists(feed_manager.conf_path)
    assert 0 == result.exit_code
    result = runner.invoke(main, ['add',
                                  test_sample['name'],
                                  test_sample['url']],
                           obj={'feed_manager_override': feed_manager})
    assert 2 == result.exit_code
    assert 'already exists' in result.output
    result = runner.invoke(main, ['ls'],
                           obj={'feed_manager_override': feed_manager})
    assert 0 == result.exit_code
    del test_sample['args']
    expected = json.dumps(test_sample, indent=2, sort_keys=True)
    assert expected == result.output.strip()
    result = runner.invoke(main, ['rm', test_sample['name']],
                           obj={'feed_manager_override': feed_manager})
    assert 0 == result.exit_code
    result = runner.invoke(main, ['ls'],
                           obj={'feed_manager_override': feed_manager})
    assert 0 == result.exit_code
    assert "" == result.output

    maildir = tmpdir_factory.mktemp('maildir')
    result = runner.invoke(main, ['add',
                                  '--output', 'maildir',
                                  '--mailbox', str(maildir),
                                  test_nasa['name'],
                                  test_nasa['url']],
                           obj={'feed_manager_override': feed_manager})
    assert os.path.exists(feed_manager.conf_path)
    with open(feed_manager.conf_path) as fp:
        assert 'feed2exec.plugins.maildir' in fp.read()
    assert 0 == result.exit_code

    test_path = utils.find_test_file('planet-debian.xml')
    result = runner.invoke(main, ['add', 'planet-debian',
                                  'file://' + test_path,
                                  '--args', 'to@example.com',
                                  '--mailbox', str(maildir)],
                           obj={'feed_manager_override': feed_manager})
    result = runner.invoke(main, ['fetch'],
                           obj={'feed_manager_override': feed_manager})
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


def test_parse(feed_manager):  # noqa
    runner = CliRunner()
    result = runner.invoke(main, ['parse',
                                  '--output', 'feed2exec.plugins.echo',
                                  '--args', 'foo bar',
                                  test_sample['url']],
                           obj={'feed_manager_override': feed_manager})
    assert 0 == result.exit_code
    assert not os.path.exists(feed_manager.conf_path)
    assert os.path.exists(feed_manager.db_path)
    assert "foo bar\n" == result.output


def test_no_maildir(tmpdir, monkeypatch):
    """reproducer for issue 14

    ... which is that folder can get created by mistake or
    intermediate directories do not. specifically:

    1. ~/Maildir (possibly, if not overriden) gets created by mistake

    2. the `mailbox` setting gets created even if overriden by an
    absolute `folder` path

    3. intermediate directories of the `folder` should be created
    correctly, even if outside of `mailbox`
    """
    # 1. set the home directory to the tmpdir
    monkeypatch.setenv('HOME', str(tmpdir))
    home_maildir = tmpdir.join("Maildir")
    # 2. path for the `mailbox` setting, different from the above to
    # test whether home_maildir gets mistakenly created as well
    mailbox_path = tmpdir.join("mailbox")
    # path to another mailbox, different from the above to test
    # whether the set mailbox gets mistakenly created
    another_mailbox_path = tmpdir.join("anothermailbox")
    # 3. make sure we have an intermediate directory
    folder_path = another_mailbox_path.join("folder")

    # create the sample config file to bind all this together. note
    # that home_maildir must NOT be present here for the test to work
    config = tmpdir.join("test.ini")
    config_data = """
[DEFAULT]
output = feed2exec.plugins.maildir
mailbox = %s

[planet-debian]
folder = %s
url = %s
""" % (mailbox_path, folder_path, test_sample['url'])
    config.write(config_data)

    runner = CliRunner()
    with tmpdir.as_cwd():
        result = runner.invoke(main, ['--config', 'test.ini',
                                      '--database', 'test.db',
                                      'fetch'])
        assert 0 == result.exit_code
    assert another_mailbox_path.exists()
    assert folder_path.exists()
    assert not home_maildir.exists(), "home maildir is not used, should not be created"
    assert not mailbox_path.exists(), "default mailbox is not used, should not be created"


def test_missing_conf(tmpdir_factory, monkeypatch):
    """regression for issue 1

    make sure we can live with a missing configuration file on import
    """
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


@pytest.mark.xfail(condition=html2text.__version__ < (2019, 9, 26), reason="older html2text output varies, install version 2019.9.26 or later")  # noqa
def test_planet(tmpdir_factory, static_boundary, feed_manager):  # noqa
    """test i18n feeds for double-encoding

    previously, we would double-encode email bodies and subject, which
    would break display of any feed item with unicode.
    """
    mbox_dir = tmpdir_factory.mktemp('planet').join('Mail')
    runner = CliRunner()

    result = runner.invoke(main, ['add', 'planet-debian',
                                  'http://planet.debian.org/rss20.xml',
                                  '--args', 'to@example.com',
                                  '--output', 'feed2exec.plugins.mbox',
                                  '--mailbox', str(mbox_dir)],
                           obj={'feed_manager_override': feed_manager})
    result = runner.invoke(main, ['fetch'],
                           obj={'feed_manager_override': feed_manager},
                           catch_exceptions=False)
    assert 0 == result.exit_code
    r = re.compile('User-Agent: .*$', flags=re.MULTILINE)
    with open(utils.find_test_file('../cassettes/planet-debian.mbx')) as expected:  # noqa
        expected = r.sub('', expected.read())
        actual = r.sub('', mbox_dir.join('planet-debian.mbx').read())
        assert expected == actual
