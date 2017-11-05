import logging

import requests


WAYBACK_URL = 'https://web.archive.org'


def output(*args, feed=None, item=None, **kwargs):
    """This plugin saves the feed items `link` element to the wayback
    machine. It will retry URLs that fail, so it may be necessary to
    manually catchup feeds if they have broken `link` fields.

    Example::

      [NASA IOTD wayback]
      url = https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss
      output = feed2exec.plugins.wayback

    The above will save the Image of the day updates to the wayback
    machine.
    """

    if item and item.get('link'):
        wayback_url = '%s/save/%s' % (WAYBACK_URL, item.get('link'))
        if feed.get('catchup'):
            logging.info('skipping wayback machine save to %s', wayback_url)
            return True
        res = feed.session.head(wayback_url)
        res.headers['status_code'] = res.status_code
        archive_location = WAYBACK_URL + res.headers['Content-Location']
        if res.status_code == requests.codes.ok:
            logging.info('URL %s saved to wayback machine: %s',
                         item.get('link'), archive_location, extra=res)
            return True
        else:
            logging.warn('wayback machine failed to save URL %s, status %d',
                         item.get('link'), res.status_code, extra=res)  # noqa
            return False
