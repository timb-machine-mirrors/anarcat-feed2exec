"""Echo plugin
===========

The echo plugin simply outputs, to standard output, the arguments it
receives. It can be useful to test your configuration.
"""


class Output(object):
    def __init__(self, *args, **kwargs):
        print("arguments received: %s, kwargs: %s" % (args, kwargs))
