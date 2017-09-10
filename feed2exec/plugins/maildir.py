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

from feed2exec.feeds import make_dirs_helper


class output(object):
    def __init__(self, prefix, *args,
                 to_addr=None, feed=None, entry=None, lock=None, **kwargs):
        prefix = os.path.expanduser(prefix)
        msg = mailbox.MaildirMessage()
        # feedparser always returns UTC times and obliterates original
        # TZ information. it does do the conversion correctly,
        # however, so just assume UTC.
        #
        # also, default on the feed updated date
        orig = timestamp = datetime.datetime.utcnow().timestamp()
        timestamp = entry.get('_fake') or orig
        if timestamp == orig:
            from pprint import pprint
            pprint(entry)
            pprint(feed)
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
        msg.set_date(timestamp)
        msg['To'] = to_addr or "%s@%s" % (getpass.getuser(), socket.getfqdn())
        params = {'name': feed.get('name'),
                  'email': msg['To']}
        if 'author_detail' in entry:
            params.update(entry['author_detail'])
        elif 'author_detail' in feed:
            params.update(feed['author_detail'])
        msg['From'] = '{name} <{email}>'.format(**params)
        msg['Subject'] = entry.get('title', feed.get('title', u''))
        msg['Date'] = email.utils.formatdate(timeval=timestamp,
                                             localtime=False)
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

        make_dirs_helper(prefix)
        folder = os.path.basename(os.path.abspath(feed.get('name')))
        path = os.path.join(prefix, folder)
        logging.debug('established folder path %s', path)
        lock.acquire()
        maildir = mailbox.Maildir(path, create=True)
        self.key = maildir.add(msg)
        maildir.flush()
        lock.release()
        guid = entry.get('guid', entry.get('link', '???'))
        logging.info('saved entry %s to %s',
                     guid, os.path.join(path, self.key))
