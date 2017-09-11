"""Maildir plugin
==============

The maildir plugin will save a feed item into a Maildir folder.

The configuration is a little clunky, but it should be safe against
hostile feeds.

:param str prefix: trusted prefix path, with ~ expansion
:param str to_addr: the email to use as "to" (defaults to USER@localdomain)
:param dict feed: the feed
:param dict item: the updated item
"""

from __future__ import division, absolute_import
from __future__ import print_function


from collections import defaultdict
import calendar
import datetime
import getpass
import email
import logging
import mailbox
import os.path
import socket
import time

import feed2exec
import feed2exec.utils as utils


def make_message(feed, entry, to_addr=None, cls=email.message.Message):
    msg = cls()
    # feedparser always returns UTC times and obliterates original
    # TZ information. it does do the conversion correctly,
    # however, so just assume UTC.
    #
    # also, default on the feed updated date
    orig = timestamp = datetime.datetime.utcnow().timestamp()
    timestamp = entry.get('updated_parsed') or orig
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
    if 'author_detail' in entry:
        params.update(entry['author_detail'])
    elif 'author_detail' in feed:
        params.update(feed['author_detail'])
    msg['From'] = '{name} <{email}>'.format(**params)
    msg['Subject'] = entry.get('title', feed.get('title', u''))
    # workaround feedparser bug:
    # https://github.com/kurtmckee/feedparser/issues/112
    msg['Message-ID'] = utils.slug(entry.get('id', entry.get('title')))
    msg['User-Agent'] = "%s (%s)" % (feed2exec.__prog__,
                                     feed2exec.__version__)
    msg['Precedence'] = 'list'
    msg['Auto-Submitted'] = 'auto-generated'
    if entry.get('link'):
        msg['Archive-At'] = entry.get('link')
    params = defaultdict(str)
    params.update(entry)
    # default to html summary if html2text filter is not enabled
    params['summary_plain'] = params.get('summary_plain',
                                         params.get('summary'))
    body = u'''{link}

{summary_plain}'''.format(**params)
    msg.add_header('Content-Transfer-Encoding', 'quoted-printable')
    msg.set_payload(body.encode('utf-8'))
    msg.set_charset('utf-8')
    return msg, timestamp


class output(object):
    def __init__(self, prefix, to_addr=None, feed=None, entry=None, lock=None,
                 *args, **kwargs):
        prefix = os.path.expanduser(prefix)
        msg, timestamp = make_message(feed=feed,
                                      entry=entry,
                                      to_addr=to_addr,
                                      cls=mailbox.MaildirMessage)
        msg.set_date(timestamp)
        utils.make_dirs_helper(prefix)
        folder = os.path.basename(os.path.abspath(feed.get('name')))
        path = os.path.join(prefix, folder)
        logging.debug('established folder path %s', path)
        if lock:
            lock.acquire()
        maildir = mailbox.Maildir(path, create=True)
        self.key = maildir.add(msg)
        maildir.flush()
        if lock:
            lock.release()
        guid = entry.get('guid', entry.get('link', '???'))
        logging.info('saved entry %s to %s',
                     guid, os.path.join(path, self.key))
