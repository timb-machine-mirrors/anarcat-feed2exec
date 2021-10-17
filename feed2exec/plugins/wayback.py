import logging

import requests

import html5lib

WAYBACK_URL = 'https://web.archive.org'

ERROR_XPATHS = [
    # XPath query for detecting blocking issues such as
    # URL syntax errors or unresolvable domains.
    #
    # <h2>Sorry</h2>
    # <p>Error text</p>
    # ...
    '//*[text()="Sorry"]/following-sibling::*/text()',

    # XPath query for detecting errors of the saving process,
    # the main one appears to be resaving the page too quickly.
    #
    # <h2 id="spn-title">Saving page https://example.org/</h2>
    # <p>Error text</p>
    # <div id="spn-option-mywebarchive">
    # ...
    '//*[starts-with(text(),"Saving page ")]' \
    '/following-sibling::*[not(@id)]/text()',
]


def _check_response(url, res):
    """Check the wayback machine response for errors

    url is the URL that has been archived
    res is the response from the archive request
    """

    # SPN2 POST requests always return HTML error pages that need parsing
    # SPN1 GET requests return HTML error pages with HTTP error codes
    parse = res.request.method == 'POST' or res.status_code != requests.codes.ok

    if parse and res.text:
        html = html5lib.parse(res.text, treebuilder="lxml")

        for error_xpath in ERROR_XPATHS:
            error = html.xpath(error_xpath)
            if error:
                break

        if error and isinstance(error, list):
            error = error[0]

    else:
        error = []

    if error and res.status_code != requests.codes.ok:
        logging.warning('wayback machine failed to save URL %s, status %d %s: %s',  # noqa
                        url, res.status_code, res.reason, error)
    elif not error and res.status_code != requests.codes.ok:
        logging.warning('wayback machine failed to save URL %s, status %d %s',  # noqa
                        url, res.status_code, res.reason)
    elif error and res.status_code == requests.codes.ok:
        logging.warning('wayback machine failed to save URL %s: %s',
                        url, error)
    elif not error and res.status_code == requests.codes.ok:
        return True

    return False


def output(*args, feed=None, item=None, session=None, **kwargs):
    """This plugin saves the feed items `link` element to the wayback
    machine. It will retry URLs that fail, so it may be necessary to
    manually catchup feeds if they have broken `link` fields.

    There are two wayback machine APIs that can be used, the default one
    archives the full page while the other one archives only the page URLs.

    The mechanism for archiving the full page uses a browser on the server
    to download all the resources used by the page including img/CSS/JS/etc:

    https://blog.archive.org/2019/10/23/the-wayback-machines-save-page-now-is-new-and-improved/

    Unfortunately the SPN2 page is just a HTML form, the response code is
    always 200 OK, any errors are returned in a HTML page and there are
    no easily machine-readable ways to find the errors on the page so we
    have to parse the HTML and query it using XPath based heuristics,
    but if there are errors in a form that is not yet known then the
    unknown errors will not be detected properly.

    Example::

      [NASA IOTD wayback]
      url = https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss
      output = feed2exec.plugins.wayback
      args = full

    The above will save the Image of the day updates to the wayback
    machine. Since the page has images and everything is loaded by JS,
    using the SPN2 API is nessecary to capture the useful information.

    Example::

      [ikiwiki RecentChanges wayback]
      url = https://ikiwiki.info/recentchanges/index.rss
      output = feed2exec.plugins.wayback
      args = page

    The above will save the ikiwiki RecentChanges to the wayback machine.
    Since the page is plain text, saving the full page resources is not
    really nessecary, the CSS does not add information to the page.
    """

    full = not args or 'full' in args

    if item:
        url = item.get('link')

    if item and url:
        if feed.get('catchup'):
            return True

    # Use a browser on the server to download the entire page:
    if item and url and full:
        logging.debug('saving URL %s with resources to wayback machine', url)
        wayback_url = '%s/save' % (WAYBACK_URL)
        form = {
            'url': url,
            'capture_all': 'on',  # Enables saving HTTP error pages
        }
        res = session.post(wayback_url, data=form)
        if _check_response(url, res):
            logging.info('URL %s with resources probably saved to wayback machine', url)  # noqa
            return True

    # Just save the URL and not any resources used by it
    if item and url and not full:
        logging.debug('saving URL %s without resources to wayback machine', url)  # noqa
        wayback_url = '%s/save/%s' % (WAYBACK_URL, url)
        res = session.get(wayback_url, allow_redirects=True)
        if _check_response(url, res):
            logging.info('URL %s saved without resources to wayback machine: %s', url, res.url)  # noqa
            return True

    return False
