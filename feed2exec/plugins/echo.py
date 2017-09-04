"""Test plugin
===========

This plugin outputs, to standard output, the arguments it receives. It
can be useful to test your configuration. It also creates a side
effect for the test suite to determine if the plugin was called.
"""


class Output(object):
    called = None

    def __init__(self, *args, **kwargs):
        print("arguments received: %s, kwargs: %s" % (args, kwargs))
        Output.called = args
