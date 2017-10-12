from __future__ import division, absolute_import
from __future__ import print_function


import html2text


class filter(object):
    """This filter plugin takes a given feed item and adds a
    ``content_plain`` field with the HTML parsed as text.

    .. important:: the html2text plugin is called automatically from
                   the email output plugins and should normally not be
                   called directly.
    """

    def __init__(self, *args, feed=None, item=None, **kwargs):
        item['summary_plain'] = self.parse(item.get('summary'))
        if item.get('content'):
            item['content_plain'] = ''.join([self.parse(x.value)
                                             for x in item.get('content')])

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
        text_maker.wrap_links = False
        return text_maker.handle(html)
