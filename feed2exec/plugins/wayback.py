import logging

import requests


WAYBACK_URL = 'https://web.archive.org'


def output(*args, feed=None, item=None, session=None, **kwargs):
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
        logging.debug('saving URL %s to wayback machine %s',
                      item.get('link'), wayback_url)
        if feed.get('catchup'):
            return True
        res = session.get(wayback_url, allow_redirects=True)
        res.headers['status_code'] = res.status_code
        if res.history:
            res.headers['Content-Location'] = res.history[0].headers.get('Content-Location')  # noqa
        location = res.headers.get('Content-Location')
        if location:
            archive_location = WAYBACK_URL + location
        else:
            archive_location = 'N/A'
        if res.status_code == requests.codes.ok:
            logging.info('URL %s saved to wayback machine: %s',
                         item.get('link'), archive_location)
            return True
        else:
            logging.warning('wayback machine failed to save URL %s, status %d',
                            item.get('link'), res.status_code)  # noqa
            return False
