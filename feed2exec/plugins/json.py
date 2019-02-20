import json


class output(object):
    """
    This plugin outputs, to standard output, the feed item it receives as JSON.
    It can be used to pipe a feed into another program or just basic inspection.

    This plugin can also be called as a filter, where it behaves the same way.
    """

    called = None

    def __init__(self, *args, feed=None, item=None, **kwargs):
        print(json.dumps(item))


#: This filter just keeps the feed unmodified. It is just there for testing
#: purposes.
filter = output
