'''

 * similarly, bup-cron has this GlobalLogger and a Singleton concept
   that may be useful elsewhere? it certainly does a nice job at
   setting up all sorts of handlers and stuff. stressant also has a
   `setup_logging` function that also supports colors and SMTP
   mailers. debmans has a neat log_warnings hook as well.


 * monkeysign also has facilities to (ab)use the logging handlers to
   send stuff to the GTK framework (GTKLoggingHandler) and a error
   handler in GTK (in msg_exception.py)

taken from ecdysis
'''

from __future__ import absolute_import

import logging
import logging.handlers
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
    handler.setFormatter(logging.Formatter(logFormat))
    handler.setLevel(level.upper())
    logger.addHandler(handler)
    if logfile:
        handler = logging.FileHandler(logfile)
        handler.setFormatter(logging.Formatter(logFormat))
        logger.addHandler(handler)
