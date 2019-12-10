from glob import glob
import os.path

from click.testing import CliRunner
import pytest

from feed2exec.__main__ import main
from feed2exec.controller import (FeedManager)
from feed2exec.tests.fixtures import feed_manager  # noqa
import feed2exec.utils as utils

testdir = utils.find_test_file()


@pytest.mark.parametrize("opmlpath", glob(os.path.join(testdir, '*.opml')))  # noqa
def test_import(tmpdir, opmlpath):
    conf_path = tmpdir.join('feed2exec.ini')
    db_path = tmpdir.join('feed2exec.db')
    with open(utils.find_test_file(opmlpath), 'rb') as opmlfile:
        FeedManager(str(conf_path), str(db_path)).opml_import(opmlfile)
        assert conf_path.check()
        try:
            with open(utils.find_test_file(opmlpath[:-4] + 'ini')) as expected:
                assert expected.read() == conf_path.read()
        except FileNotFoundError:
            # output is not considered if ini file is missing, just test parse
            pass
    conf_path.remove()


def test_opml(tmpdir, feed_manager):  # noqa
    runner = CliRunner()

    assert not os.path.exists(feed_manager.conf_path)
    result = runner.invoke(main, ['import',
                                  utils.find_test_file('simple.opml')],
                           obj={'feed_manager_override': feed_manager})
    assert os.path.exists(feed_manager.conf_path)
    assert 0 == result.exit_code
    with open(utils.find_test_file('simple.ini')) as p, open(feed_manager.conf_path) as fp:
        fp.read() == p.read()

    opml_path = tmpdir.join('simple.opml')
    result = runner.invoke(main, ['export',
                                  str(opml_path)],
                           obj={'feed_manager_override': feed_manager})
    assert os.path.exists(feed_manager.conf_path)
    assert 0 == result.exit_code
    with open(utils.find_test_file('simple.opml')) as p:
        p.read() == opml_path.read()
