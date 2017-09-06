"""Exec plugin
===========

The exec plugin is the ultimate security disaster. It simply executes
whatever you feed it without any sort of sanitization.

.. danger:: do not use.
"""

import subprocess


def output(command, *args, **kwargs):
    return subprocess.check_call([command] + list(args))
