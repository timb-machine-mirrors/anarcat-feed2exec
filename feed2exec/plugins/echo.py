class output(object):
    """
    This plugin outputs, to standard output, the arguments it receives. It
    can be useful to test your configuration. It also creates a side
    effect for the test suite to determine if the plugin was called.

    This plugin does a similar thing when acting as a filter.
    """

    called = None

    def __init__(self, *args, **kwargs):
        print("arguments received: %s" % str(args))
        output.called = args


#: This filter just keeps the feed unmodified. It is just there for testing
#: purposes.
filter = output
