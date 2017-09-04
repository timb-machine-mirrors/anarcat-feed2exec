#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function


import json


from click.testing import CliRunner
from feed2exec.__main__ import main
from feed2exec.tests.test_feeds import test_db, test_data
import pytest


def test_usage():
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0


def test_basics(test_db):
    runner = CliRunner()
    result = runner.invoke(main, ['--database', str(test_db),
                                  'add',
                                  test_data['name'],
                                  test_data['url']])
    assert test_db.check()
    assert result.exit_code == 0
    result = runner.invoke(main, ['--database', str(test_db),
                                  'ls'])
    assert result.exit_code == 0
    assert result.output.strip() == json.dumps(test_data,
                                               indent=2,
                                               sort_keys=True)
    result = runner.invoke(main, ['--database', str(test_db),
                                  'rm', 'test'])
    assert result.exit_code == 0
    result = runner.invoke(main, ['--database', str(test_db),
                                  'ls'])
    assert result.exit_code == 0
    assert result.output == ""
