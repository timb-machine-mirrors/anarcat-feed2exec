from __future__ import division, absolute_import
from __future__ import print_function

import logging
import mailbox
import os.path
import time


from feed2exec.email import make_message
import feed2exec.utils as utils


class output(object):
    """The mbox plugin will save a feed item in a Mbox mailbox.

    This is mostly for testing purposes, but can of course be used in
    the unlikely event where you prefer mbox folders over the
    :mod:`feed2exec.plugins.maildir` plugin.

    :param str to_addr: the email to use as "to" (defaults to
                        USER@localdomain)

    :todo: There is some overlap between the code here and the maildir
           implementation. Refactoring may be in order, particularly
           if we add another mailbox format, though that is unlikely.
    """
    def __init__(self, to_addr=None, feed=None, item=None, lock=None,
                 *args, **kwargs):
        msg, timestamp = make_message(feed=feed,
                                      item=item,
                                      to_addr=to_addr,
                                      cls=mailbox.mboxMessage)
        msg.set_from(utils.slug(feed.get('name', 'MAILER-DAEMON')),
                     time.gmtime(timestamp))
        prefix = os.path.expanduser(feed.get('mailbox', '~/Mail'))
        folder = os.path.basename(os.path.abspath(utils.slug(feed.get('name'))))  # noqa
        # allow user to override our folder
        folder = feed.get('folder', folder + '.mbx')
        path = os.path.join(prefix, folder)
        logging.debug('established folder path %s', path)
        if lock:
            lock.acquire()
        if feed.get('catchup'):
            self.key = path
        else:
            utils.make_dirs_helper(prefix)
            maildir = mailbox.mbox(path, create=True)
            self.key = maildir.add(msg)
            maildir.flush()
        if lock:
            lock.release()
        guid = item.get('guid', item.get('link', '???'))
        logging.info('saved item %s to %s%s', guid, path,
                     feed.get('catchup', '') and ' (simulated)')
