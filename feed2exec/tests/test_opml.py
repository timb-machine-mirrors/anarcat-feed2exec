from glob import glob
import os.path

from click.testing import CliRunner
import pytest

from feed2exec.__main__ import main
from feed2exec.feeds import (FeedManager)
from feed2exec.tests.fixtures import (db_path, conf_path)  # noqa
import feed2exec.utils as utils

testdir = utils.find_test_file()


@pytest.mark.parametrize("opmlpath", glob(os.path.join(testdir, '*.opml')))  # noqa
def test_import(db_path, conf_path, opmlpath):
    with open(utils.find_test_file(opmlpath), 'rb') as opmlfile:
        FeedManager().opml_import(opmlfile)
        assert conf_path.check()
        try:
            with open(utils.find_test_file(opmlpath[:-4] + 'ini')) as expected:
                assert expected.read() == conf_path.read()
        except FileNotFoundError:
            # output is not considered if ini file is missing, just test parse
            pass
    conf_path.remove()


def test_opml(tmpdir_factory, conf_path, db_path):  # noqa
    runner = CliRunner()

    assert not conf_path.check()
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'import',
                                  utils.find_test_file('simple.opml')])
    assert conf_path.check()
    assert 0 == result.exit_code
    with open(utils.find_test_file('simple.ini')) as p:
        conf_path.read() == p.read()

    opml_path = tmpdir_factory.mktemp('ompl').join('simple.opml')
    result = runner.invoke(main, ['--config', str(conf_path),
                                  '--database', str(db_path),
                                  'export',
                                  str(opml_path)])
    assert conf_path.check()
    assert 0 == result.exit_code
    with open(utils.find_test_file('simple.opml')) as p:
        p.read() == opml_path.read()
