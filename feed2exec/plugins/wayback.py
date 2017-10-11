import requests

def output(*args, item=None, **kwargs):
    if item and item.get('link'):
        res = requests.head('https://web.archive.org/save/%s' % item.get('link'))
	res.headers['status_code'] = r.status_code
	if r.status_code == requests.codes.ok:
            logging.info('saved to wayback machine (status: %(status_code)s, URL: %(Content-Location)s, cache: %(X-Page-Cache)s)',
                         res.headers))
        else:
            logging.warn('wayback machine failed (status: %(status_code)s, URL: %(Content-Location)s)',
                         res.headers))
