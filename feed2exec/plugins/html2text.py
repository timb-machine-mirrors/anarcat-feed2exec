"""html2text filter
================

This filter plugin takes a given feed item and replaces the ``summary``
with its HTML parsed as text.
"""


import html2text


def filter(feed=None, entry=None):
    entry['summary'] = html2text.html2text(entry.get('summary'))
