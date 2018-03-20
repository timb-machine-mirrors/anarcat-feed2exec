import logging
import shlex


class output(object):
    """
    This plugin outputs, to standard output, the arguments it receives. It
    can be useful to test your configuration. It also creates a side
    effect for the test suite to determine if the plugin was called.

    This plugin does a similar thing when acting as a filter.
    """

    called = None

    def __init__(self, *args, feed=None, **kwargs):
        print(" ".join([shlex.quote(x) for x in args]))
        logging.debug('echo plugin called with args%s: %s',
                      feed.get('catchup', '') and ' (simulated)', args)
        if not feed.get('catchup'):
            output.called = args


#: This filter just keeps the feed unmodified. It is just there for testing
#: purposes.
filter = output
