"""Error plugin
============

The error plugin is a simple plugin which raises an exception when
called. It is designed for use in the test suite and should generally
not be used elsewhere.
"""


class Output(object):
    def __init__(self, *args):
        raise Exception("you should be handling this")
