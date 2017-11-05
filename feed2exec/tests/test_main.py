#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function

import json
import re

from click.testing import CliRunner

import feed2exec.utils as utils
from feed2exec.__main__ import main
from feed2exec.tests.test_feeds import (ConfFeedStorage, test_sample,
                                        test_nasa)
from feed2exec.tests.fixtures import static_boundary  # noqa


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert 0 == result.exit_code


def test_basics(tmpdir_factory, static_boundary):  # noqa
    conf_dir = tmpdir_factory.mktemp('main')
    conf_path = conf_dir.join('feed2exec.ini')
    db_path = conf_dir.join('feed2exec.db')
    ConfFeedStorage.path = str(conf_path)
    runner = CliRunner()
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add',
                                  '--output', 'feed2exec.plugins.echo',
                                  test_sample['name'],
                                  test_sample['url']])
    assert conf_dir.join('feed2exec.ini').check()
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

    maildir = conf_dir.join('maildir')
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add',
                                  '--mailbox', str(maildir),
                                  test_nasa['name'],
                                  test_nasa['url']])
    assert conf_dir.join('feed2exec.ini').check()
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


def test_parse(tmpdir_factory):
    conf_dir = tmpdir_factory.mktemp('parse')
    conf_path = conf_dir.join('feed2exec.ini')
    db_path = conf_dir.join('feed2exec.db')
    runner = CliRunner()
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


def test_opml(tmpdir_factory, static_boundary):  # noqa
    # XXX: copy-pasted from above
    conf_dir = tmpdir_factory.mktemp('main')
    conf_path = conf_dir.join('feed2exec.ini')
    db_path = conf_dir.join('feed2exc.db')
    ConfFeedStorage.path = str(conf_path)
    runner = CliRunner()

    assert not conf_path.check()
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'import',
                                  utils.find_test_file('simple.opml')])
    assert conf_path.check()
    assert 0 == result.exit_code
    with open(utils.find_test_file('simple.ini')) as p:
        conf_dir.join('feed2exec.ini').read() == p.read()

    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'export',
                                  str(conf_dir.join('opml'))])
    assert conf_path.check()
    assert 0 == result.exit_code
    with open(utils.find_test_file('simple.opml')) as p:
        p.read() == conf_dir.join('opml').read()


def test_planet(tmpdir_factory, static_boundary, betamax_session):  # noqa
    """test i18n feeds for double-encoding

    previously, we would double-encode email bodies and subject, which
    would break display of any feed item with unicode.
    """
    # XXX: copy-pasted from above
    conf_dir = tmpdir_factory.mktemp('planet')
    conf_path = conf_dir.join('feed2exec.ini')
    db_path = conf_dir.join('feed2exec.db')
    ConfFeedStorage.path = str(conf_path)
    runner = CliRunner()

    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'add', 'planet-debian',
                                  'http://planet.debian.org/rss20.xml',
                                  '--args', 'to@example.com',
                                  '--output', 'feed2exec.plugins.mbox',
                                  '--mailbox', str(conf_dir)])
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'fetch'],
                           obj=betamax_session, catch_exceptions=False)
    assert 0 == result.exit_code
    r = re.compile('User-Agent: .*$', flags=re.MULTILINE)
    with open(utils.find_test_file('../cassettes/planet-debian.mbx')) as expected:  # noqa
        expected = r.sub('', expected.read())
        actual = r.sub('', conf_dir.join('planet-debian.mbx').read())
        assert expected == actual
