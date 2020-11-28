# -*- coding: utf-8 -*-

'''various reusable utilities'''

from __future__ import absolute_import

import errno
import inspect
import os
import os.path
import pkg_resources
import re
from unidecode import unidecode

from feed2exec import __prog__


def slug(text):
    """Make a URL-safe, human-readable version of the given text

    This will do the following:

    1. decode unicode characters into ASCII
    2. shift everything to lowercase
    3. strip whitespace
    4. replace other non-word characters with dashes
    5. strip extra dashes

    This somewhat duplicates the :func:`Google.slugify` function but
    slugify is not as generic as this one, which can be reused
    elsewhere.

    >>> slug('test')
    'test'
    >>> slug('Mørdag')
    'mordag'
    >>> slug("l'été c'est fait pour jouer")
    'l-ete-c-est-fait-pour-jouer'
    >>> slug(u"\xe7afe au lait (boisson)")
    'cafe-au-lait-boisson'
    >>> slug(u"Multiple  spaces -- and symbols! -- merged")
    'multiple-spaces-and-symbols-merged'

    This is a simpler, one-liner version of the `slugify module
    <https://github.com/un33k/python-slugify>`_.

    taken from ecdysis
    """
    return re.sub(r'\W+', '-', unidecode(text).lower().strip()).strip('-')


def make_dirs_helper(path):
    """Create the directory if it does not exist

    Return True if the directory was created, false if it was already
    present, throw an OSError exception if it cannot be created

    >>> import tempfile
    >>> import os
    >>> import os.path as p
    >>> d = tempfile.mkdtemp()
    >>> make_dirs_helper(p.join(d, 'foo'))
    True
    >>> make_dirs_helper(p.join(d, 'foo'))
    False
    >>> make_dirs_helper('')
    False
    >>> make_dirs_helper(p.join('/dev/null', 'foo')) # doctest: +ELLIPSIS
    Traceback (most recent call last):
        ...
    NotADirectoryError: [Errno 20] Not a directory: ...
    >>> os.rmdir(p.join(d, 'foo'))
    >>> os.rmdir(d)
    >>>
    """
    if not path:
        return False
    try:
        os.makedirs(path)
        return True
    except OSError as ex:
        if ex.errno != errno.EEXIST or not os.path.isdir(path):
            raise
        return False


def find_test_file(name='.'):
    """need to be updated from ecdysis

    See also https://pypi.org/project/pytest-datadir/
    """
    localpath = os.path.join(os.path.dirname(__file__), 'tests', 'files', name)
    try:
        pkg = pkg_resources.Requirement.parse(__prog__)
        path = os.path.join(__prog__, 'tests', 'files', name)
        path = pkg_resources.resource_filename(pkg, path)
        if os.path.exists(path):
            return path
        else:
            return localpath
    except pkg_resources.DistributionNotFound:
        return localpath


def find_parent_module():
    """find the name of a the first module calling this module

    if we cannot find it, we return the current module's name
    (__name__) instead.

    taken from ecdysis
    """
    try:
        frame = inspect.currentframe().f_back
        module = inspect.getmodule(frame)
        while module is None or module.__name__ == __name__:
            frame = frame.f_back
            module = inspect.getmodule(frame)
        return module.__name__
    except AttributeError:
        # somehow we failed to find our module
        # return the logger module name by default
        return __name__
