"""html2text filter
================

This filter plugin takes a given feed item and replaces the ``summary``
with its HTML parsed as text.
"""


from __future__ import division, absolute_import
from __future__ import print_function


import html2text


class filter(object):

    def __init__(self, feed=None, entry=None, *args, **kwargs):
        entry['summary_plain'] = self.parse(entry.get('summary', ''))

    @staticmethod
    def parse(html):
        """parse html to text according to our preferences. this is where
        subclasses can override the HTML2Text settings or use a
        completely different parser
        """
        text_maker = html2text.HTML2Text()
        text_maker.inline_links = False
        text_maker.images_to_alt = True
        text_maker.unicode_snob = True
        text_maker.links_each_paragraph = True
        return text_maker.handle(html)
