"""Exec plugin
===========

The exec plugin is the ultimate security disaster. It simply executes
whatever you feed it without any sort of sanitization.

.. danger:: do not use.
"""

import subprocess


class Output(object):
    def __init__(self, command, *args, **kwargs):
        self.returncode = subprocess.check_call([command] + list(args))
