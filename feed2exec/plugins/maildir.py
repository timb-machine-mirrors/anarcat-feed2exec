import mailbox
import os.path

from feed2exec.feeds import make_dirs_helper


class Output(object):
    def __init__(self, prefix, folder, body, subject,
                 date, from_addr, to_addr):
        """output the item into the given maildir folder

        :param str prefix: trusted prefix path
        :param str folder: untrusted folder path, will be sanitized
        :param str body: the whole body of the message
        :param datetime published_date
        :param str subject:
        :param str from:
        :param str to:
        """
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
