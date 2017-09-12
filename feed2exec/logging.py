'''

 * similarly, bup-cron has this GlobalLogger and a Singleton concept
   that may be useful elsewhere? it certainly does a nice job at
   setting up all sorts of handlers and stuff. stressant also has a
   `setup_logging` function that also supports colors and SMTP
   mailers. debmans has a neat log_warnings hook as well.


 * monkeysign also has facilities to (ab)use the logging handlers to
   send stuff to the GTK framework (GTKLoggingHandler) and a error
   handler in GTK (in msg_exception.py)
'''

from __future__ import absolute_import

import getpass
import logging
from logging.handlers import SMTPHandler, MemoryHandler
import socket
import time
import warnings


from feed2exec import __prog__
from feed2exec.utils import find_parent_module


# not sure why logging._levelNames are not exposed...
levels = ['CRITICAL',
          'ERROR',
          'WARNING',
          'INFO',
          'DEBUG']


def _log_warning(message, category, filename, lineno, file=None, line=None):
    '''warnings handler that channels them to the logging module'''
    msg = "{0}:{1}: {2}: {3}".format(filename, lineno,
                                     category.__name__, message)
    logger = logging.getLogger(find_parent_module())
    # Note: the warning will look like coming from here,
    # but msg contains info about where it really comes from
    logger.warning(msg)


def advancedConfig(level='warning', stream=None, syslog=False, prog=None,
                   email=False, smtpparams=None,
                   logfile=None, logFormat='%(levelname)s: %(message)s',
                   **kwargs):
    '''setup standard Python logging facilities

    this was taken from the debmans and stressant loggers, although it
    lacks stressant's color support

    :param str level: logging level, usually one of `levels`

    :param file stream: stream to send logging events to, or None to
    use the logging default (usually stderr)

    :param str syslog: send log events to syslog at the specified
    level. defaults to False, which doesn't send syslog events

    :param str prog: the program name to use in syslog lines, defaults
    to .__prog__

    :param str email: send logs by email to the given email address
    using the BufferedSMTPHandler

    :param dict smtpparams: parameters to use when sending
    email. expected fields are:

       * fromaddr (defaults to $USER@$FQDN)
       * subject (defaults to '')
       * mailhost (defaults to the last part of the destination email)
       * user (to authenticate against the SMTP server, defaults to no auth)
       * pass (password to use, prompted using getpass otherwise)

    :param str logfile: filename to pass to the FileHandler to log
    directly to a file

    :param str logFormat: logformat to use for the FileHandler and
    BufferedSMTPHandler
    '''
    if prog is None:
        prog = __prog__
    logger = logging.getLogger('')
    # disable the base filter, each stream has its own filter
    logger.setLevel('DEBUG')
    warnings.showwarning = _log_warning
    if syslog:
        sl = logging.handlers.SysLogHandler(address='/dev/log')
        sl.setFormatter(logging.Formatter(prog+'[%(process)d]: %(message)s'))
        # convert syslog argument to a numeric value
        sl.setLevel(syslog.upper())
        logger.addHandler(sl)
        logger.debug('configured syslog level %s' % syslog)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    handler.setLevel(level.upper())
    logger.addHandler(handler)
    if logfile:
        handler = logging.FileHandler(logfile)
        handler.setFormatter(logging.Formatter(logFormat))
        logger.addHandler(handler)
    if email:
        subject = smtpparams.get('subject', '')
        fromaddr = smtpparams.get('fromaddr', None)
        smtpserver = smtpparams.get('mailhost', None)
        smtpuser = smtpparams.get('user', None)
        smtppass = smtpparams.get('pass', None)
        # XXX: need to do MX discovery
        if not smtpserver:
            _, smtpserver = email.split('@', 1)
        if not fromaddr:
            fromaddr = getpass.getuser() + '@' + socket.getfqdn()
        credentials = None
        if smtpuser:
            if not smtppass:
                smtppass = getpass.getpass('enter SMTP password for %s: '
                                           % smtpserver)
            credentials = (smtpuser, smtppass)
        handler = BufferedSMTPHandler(smtpserver,
                                      fromaddr,
                                      email,
                                      subject,
                                      secure=(),
                                      credentials=credentials,
                                      flushLevel=logging.CRITICAL)
        handler.setFormatter(logging.Formatter(logFormat))
        logger.addHandler(handler)


class BufferedSMTPHandler(SMTPHandler, MemoryHandler):
    """A handler class which sends records only when the buffer reaches
    capacity. The object is constructed with the arguments from
    SMTPHandler and MemoryHandler and basically behaves as a merge
    between the two classes.

    The SMTPHandler.emit() implementation was copy-pasted here because
    it is not flexible enough to be overridden. We could possibly
    override the format() function to instead look at the internal
    buffer, but that would have possibly undesirable side-effects.
    """

    def __init__(self, mailhost, fromaddr, toaddrs, subject,
                 credentials=None, secure=None,
                 capacity=5000, flushLevel=logging.ERROR, retries=1):
        SMTPHandler.__init__(self, mailhost, fromaddr, toaddrs, subject,
                             credentials=None, secure=None)
        self.retries = retries
        MemoryHandler.__init__(self, capacity=capacity, flushLevel=flushLevel)

    def emit(self, record):
        '''buffer the record in the MemoryHandler'''
        MemoryHandler.emit(self, record)

    def flush(self):
        """Flush all records.

        Format the records and send it to the specified addressees.

        The only change from SMTPHandler here is the way the email
        body is created.

        """
        if self.retries < 0:
            logging.error('Could not send email: %s', self.lastException)
        if len(self.buffer) <= 0:
            return
        body = ''
        for record in self.buffer:
            body += self.format(record) + "\n"
        try:
            import smtplib
            from email.utils import formatdate
            port = self.mailport
            if not port:
                port = smtplib.SMTP_PORT
            smtp = smtplib.SMTP(self.mailhost, port, timeout=self._timeout)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            ",".join(self.toaddrs),
                            self.getSubject(record),
                            formatdate(), body)
            if self.secure is not None:
                smtp.ehlo()
                smtp.starttls(*self.secure)
                smtp.ehlo()
            if self.username:
                smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg)
            smtp.quit()
            logging.info('sent email to %s using %s',
                         self.toaddrs, self.mailhost)
            self.buffer = []
        except (KeyboardInterrupt, SystemExit):
            raise
        except smtplib.SMTPRecipientsRefused as e:
            for email, error in e.recipients.iteritems():
                if error[0] == 450:  # greylisting
                    logging.info('temporary error, waiting 5 minutes to send')
                    self.retries -= 1
                    time.sleep(5*60)
                    self.lastException = e
                    self.flush()
        except:
            self.handleError(record)
