# -*- coding: utf-8 -*-

'''various reusable utilities'''

from __future__ import absolute_import

from unidecode import unidecode
import re


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
    """
    return re.sub(r'\W+', '-', unidecode(text).lower().strip()).strip('-')
