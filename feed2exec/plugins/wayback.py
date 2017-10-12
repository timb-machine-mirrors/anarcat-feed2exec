import logging

import requests


WAYBACK_URL = 'https://web.archive.org'


def output(*args, item=None, **kwargs):
    if item and item.get('link'):
        res = requests.head('%s/save/%s' % (WAYBACK_URL, item.get('link')))
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
