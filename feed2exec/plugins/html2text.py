from __future__ import division, absolute_import
from __future__ import print_function


import html2text


class filter(object):
    """
    This filter plugin takes a given feed item and replaces the
    ``content`` with its HTML parsed as text.
    """

    def __init__(self, *args, feed=None, entry=None, **kwargs):
        entry['summary_plain'] = self.parse(entry.get('summary'))
        if entry.get('content'):
            entry['content_plain'] = ''.join([self.parse(x.value)
                                              for x in entry.get('content')])

    @staticmethod
    def parse(html=None):
        """parse html to text according to our preferences. this is where
        subclasses can override the HTML2Text settings or use a
        completely different parser
        """
        if html is None:
            return None
        text_maker = html2text.HTML2Text()
        text_maker.inline_links = False
        text_maker.images_to_alt = True
        text_maker.unicode_snob = True
        text_maker.links_each_paragraph = True
        text_maker.protect_links = True
        return text_maker.handle(html)
