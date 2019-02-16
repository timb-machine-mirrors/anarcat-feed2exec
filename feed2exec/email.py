import calendar
from collections import defaultdict
import datetime
import getpass
import email
from email.header import Header
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import socket
import time
import warnings

import feed2exec
import feed2exec.utils as utils
from feed2exec.plugins.html2text import filter as html2text_filter

boundary = None


def make_message(feed, item, to_addr=None, cls=email.message.Message):
    """generate a message from the feed

    this will generate multipart emails if HTML is detected, but also
    for multipart Atom feeds (which may have multiple Content tags).

    .. todo:: should be moved to utils?

    .. todo:: port to the new email.message.EmailMessage interface,
              only available in 3.6 however. See `this documentation
              <https://docs.python.org/3/library/email.compat32-message.html#compat32-message>`_
              for more information.

    """
    params = defaultdict(str)
    params.update(item)
    cs = email.charset.Charset('utf-8')
    # headers are still not 8-bit clean but body probably is:
    # https://stackoverflow.com/a/23875217
    cs.header_encoding = email.charset.QP
    # also: http://cr.yp.to/smtp/8bitmime.html
    #
    # quote: Do not implement Q-P conversion in an SMTP client. You
    # will find that simply sending an 8-bit message is much more
    # successful than attempting Q-P conversion, whether or not the
    # server announces 8BITMIME.
    cs.body_encoding = '8bit'
    msg = MIMEMultipart('alternative', boundary)
    html_parts = []
    for content in params.get('content', []):
        if not content.value:
            continue
        if content.type == 'application/xhtml+xml':
            content.type = 'text/html'
        basetype, subtype = content.type.split('/', 1)
        if basetype != 'text':
            logging.warning('unhandled mime type %s, skipped', content.type)
            continue
        html = MIMEText(content.value.encode('utf-8'),
                        _subtype=subtype, _charset=cs)
        html.replace_header('Content-Transfer-Encoding', '8bit')
        if subtype == 'html':
            html_parts.append(content.value)
        msg.attach(html)

    if not msg.get_payload() and params.get('summary'):
        # no content found, fallback on summary
        content = params.get('summary')
        # stupid heuristic to guess if content is HTML, because
        # feedparser sure won't tell
        subtype = 'html' if '<' in content else 'plain'
        part = MIMEText(content.encode('utf-8'),
                        _subtype=subtype, _charset=cs)
        if subtype == 'plain':
            msg = part
        else:
            html_parts.append(params.get('summary'))
            msg.attach(part)
    for content in html_parts:
        # plain text version available
        params['content_plain'] = html2text_filter.parse(content)
        body = u'''{link}

{content_plain}'''.format(**params)
        text = MIMEText(body.encode('utf-8'),
                        _subtype='plain', _charset=cs)
        text.replace_header('Content-Transfer-Encoding', '8bit')
        msg.attach(text)
    payload = msg.get_payload()
    if len(payload) == 1:
        msg = payload.pop()
    msg = cls(msg)

    # feedparser always returns UTC times and obliterates original
    # TZ information. it does do the conversion correctly,
    # however, so just assume UTC.
    #
    # also, default on the feed updated date
    orig = timestamp = datetime.datetime.utcnow().timestamp()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        timestamp = item.get('updated_parsed', item.get('published_parsed', orig))
    if isinstance(timestamp, (datetime.datetime,
                              datetime.date,
                              datetime.time)):
        try:
            timestamp = timestamp.timestamp()
        except AttributeError:
            # py2, less precision
            timestamp = int(timestamp.strftime('%s'))
    elif isinstance(timestamp, (time.struct_time, tuple)):
        timestamp = calendar.timegm(timestamp)
    msg['Date'] = email.utils.formatdate(timeval=timestamp,
                                         localtime=False)
    msg['To'] = to_addr or "%s@%s" % (getpass.getuser(), socket.getfqdn())
    params = {'name': feed.get('name'),
              'email': msg['To']}
    if 'author_detail' in item:
        params.update(item['author_detail'])
    elif 'author_detail' in feed:
        params.update(feed['author_detail'])
    # pass header as bytes otherwise it gets forcibly encoded, even if
    # not required. snippet taken from:
    # http://mg.pov.lt/blog/unicode-emails-in-python.html
    msg['From'] = formataddr((str(Header(params['name'].encode('utf-8'),
                                         charset=cs)),
                              params['email']))
    msg['Subject'] = item.get('title', feed.get('title', u''))
    # workaround feedparser bug:
    # https://github.com/kurtmckee/feedparser/issues/112
    msg['Message-ID'] = utils.slug(item.get('id', item.get('title')))
    msg['User-Agent'] = "%s (%s)" % (feed2exec.__prog__,
                                     feed2exec.__version__)
    msg['Precedence'] = 'list'
    msg['Auto-Submitted'] = 'auto-generated'
    if item.get('link'):
        msg['Archived-At'] = item.get('link')
    return msg, timestamp
