from datetime import datetime
from time import mktime
from urllib.parse import unquote
import logging
import re


def filter(*args, item=None, **kwargs):
    """the ikiwiki_recentchanges plugin fixes links in ikiwiki feeds

    Ikiwiki recent changes show all the recent edits to pages, but the
    ``<link>`` element doesn't point to the edit page: it points to
    the recent changes page itself, which make them useless for link
    checking or archival purposes.

    This parses the recent changes entries and extracts the relevant
    links from it.

    An alternative to this is to use the following entry to generate a
    special feed in Ikiwiki::

      [[!inline pages="*" feeds=yes feedonly=yes feedfile=archive show=10]]

    This generates a feed with proper ``<link>`` elements but requires
    write access to the wiki.

    This will also add the date to the URL GUID so that we refresh
    when a page is updated. Otherwise feed2exec would think the entry
    has already been passed.
    """

    r = re.search(r'(https?://[^/]*/)ikiwiki.cgi\?do=goto&amp;page=([^"]*)"',
                  item.get('summary', ''))
    if r:
        link = r.group(1) + unquote(r.group(2))
        logging.debug('link changed from %s to %s',
                      item['link'], link)
        item['link'] = link

    # append timestamp
    t = mktime(item['published_parsed'])
    item['id'] = datetime.fromtimestamp(t).isoformat() + '-' + item['id']
