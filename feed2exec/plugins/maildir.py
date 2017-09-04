"""Maildir plugin
==============

The maildir plugin will save a feed item into a Maildir folder.

The configuration is a little clunky, but it should be safe against
hostile feeds.

It can be configured as such::

    feed2exec add test http://test.example.com/rss.xml --plugin feed2exec.plugins.maildir --args "/home/anarcat/Maildir/ %(name)s %(description)s%(link)s %(title)s %(published_parsed)s foo@example.com me@example.com"

Notice how the arguments are split on spaces. The expected arguments are:

:param str prefix: trusted prefix path
:param str folder: untrusted folder path, will be sanitized
:param str body: the whole body of the message
:param datetime published_date
:param str subject:
:param str from:
:param str to:
"""

import mailbox
import os.path

from feed2exec.feeds import make_dirs_helper


class Output(object):
    def __init__(self, prefix, folder, body, subject,
                 date, from_addr, to_addr):
        msg = mailbox.MaildirMessage()
        try:
            msg.set_date(date.timestamp())  # py3
        except AttributeError:
            msg.set_date(int(date.strftime('%s')))  # py2, less precision
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Subject'] = subject
        msg.add_header('Content-Transfer-Encoding', 'quoted-printable')
        msg.set_payload(body.encode('utf-8'))
        msg.set_charset('utf-8')

        make_dirs_helper(prefix)
        folder = os.path.basename(os.path.abspath(folder))
        path = os.path.join(prefix, folder)
        # XXX: LOCKING!
        maildir = mailbox.Maildir(path, create=True)
        self.key = maildir.add(msg)
        maildir.flush()
