"""html2text filter
================

This filter plugin takes a given feed item and replaces the ``summary``
with its HTML parsed as text.
"""


from __future__ import division, absolute_import
from __future__ import print_function


from html2text import html2text


def filter(feed=None, entry=None, *args, **kwargs):
    entry['summary_html'] = entry.get('summary', '')
    entry['summary'] = entry['summary_plain'] = html2text(entry.get('summary',
                                                                    ''))
