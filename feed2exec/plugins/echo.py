"""Test plugin
===========

This plugin outputs, to standard output, the arguments it receives. It
can be useful to test your configuration. It also creates a side
effect for the test suite to determine if the plugin was called.
"""


import json


from feed2exec.feeds import safe_serial


class output(object):
    called = None

    def __init__(self, *args, **kwargs):
        print("arguments received: %s, kwargs: %s"
              % (args, json.dumps(kwargs, sort_keys=True,
                                  default=safe_serial)))
        output.called = args
