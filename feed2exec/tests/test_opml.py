from glob import glob
import os.path

from feed2exec.feeds import (FeedManager)
from feed2exec.tests.fixtures import (test_db, conf_path)  # noqa
import feed2exec.utils as utils

def test_import(test_db, conf_path):  # noqa
    testdir = utils.find_test_file('.')
    print("looking in testdir %s" % testdir)
    found = False
    for opmlpath in glob(os.path.join(testdir, '*.opml')):
        found = True
        with open(utils.find_test_file(opmlpath), 'rb') as opmlfile, open(utils.find_test_file(opmlpath[:-4] + 'ini')) as expected:  # noqa
            FeedManager().opml_import(opmlfile)
            assert conf_path.check()
            assert expected.read() == conf_path.read()
        conf_path.remove()
    assert found
