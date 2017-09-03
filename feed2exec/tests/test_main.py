#!/usr/bin/python3
# coding: utf-8

from __future__ import division, absolute_import
from __future__ import print_function


import os.path


from click.testing import CliRunner
from feed2exec.__main__ import feed2exec
from feed2exec.tests.test_feeds import test_db
import pytest


def test_usage():
    runner = CliRunner()
    result = runner.invoke(feed2exec, ['--help'])
    assert result.exit_code == 0


def test_basics(test_db):
    runner = CliRunner()
    result = runner.invoke(feed2exec, ['--database', str(test_db),
                                       'add', 'test', 'file:///dev/null'])
    assert test_db.check()
    assert result.exit_code == 0
    result = runner.invoke(feed2exec, ['--database', str(test_db),
                                       'ls'])
    assert result.exit_code == 0
    assert result.output == """{'url': u'file:///dev/null', 'name': u'test', 'plugin': None}\n"""
    result = runner.invoke(feed2exec, ['--database', str(test_db),
                                       'rm', 'test'])
    assert result.exit_code == 0
    result = runner.invoke(feed2exec, ['--database', str(test_db),
                                       'ls'])
    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.xfail
def test_fetch():
    assert False
