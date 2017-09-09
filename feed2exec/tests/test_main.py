#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function


import json


from click.testing import CliRunner
from feed2exec.__main__ import main
from feed2exec.tests.test_feeds import ConfFeedStorage, test_data, test_nasa


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0


def test_basics(tmpdir_factory):
    conf_dir = tmpdir_factory.mktemp('main')
    conf_path = conf_dir.join('feed2exec.ini')
    ConfFeedStorage.path = str(conf_path)
    runner = CliRunner()
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add',
                                  test_data['name'],
                                  test_data['url']])
    assert conf_dir.join('feed2exec.ini').check()
    assert result.exit_code == 0
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'ls'])
    assert result.exit_code == 0
    del test_data['output_args']
    del test_data['output']
    assert result.output.strip() == json.dumps(test_data,
                                               indent=2,
                                               sort_keys=True)
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'rm', 'test'])
    assert result.exit_code == 0
    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'ls'])
    assert result.exit_code == 0
    assert result.output == ""

    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'add',
                                  test_nasa['name'],
                                  test_nasa['url']])
    assert conf_dir.join('feed2exec.ini').check()
    assert result.exit_code == 0

    result = runner.invoke(main, ['--config', str(conf_dir),
                                  'fetch'])
