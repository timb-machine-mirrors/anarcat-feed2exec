import logging
import subprocess


def output(command, *args, feed=None, **kwargs):
    """The exec plugin is the ultimate security disaster. It simply
    executes whatever you feed it without any sort of sanitization. It
    does avoid to call to the shell and executes the command directly,
    however. Feed contents are also somewhat sanitized by the
    feedparser module, see the `Sanitization
    <https://pythonhosted.org/feedparser/html-sanitization.html>`_
    documentation for more information in that regard. That is limited
    to stripping out hostile HTML tags, however.

    You should be careful when sending arbitrary parameters to other
    programs. Even if we do not use the shell to execute the program,
    an hostile feed could still inject commandline flags to change the
    program behavior without injecting shell commands themselves.

    For example, if a program can write files with the ``-o`` option,
    a feed could set their title to ``-oevil`` to overwrite the
    ``evil`` file. The only way to workaround that issue is to
    carefully craft the commandline so that this cannot happen.

    Alternatively, writing a Python plugin is much safer as you can
    sanitize the arguments yourself.

    Example::

      [NASA Whats up?]
      url = https://www.nasa.gov/rss/dyn/whats_up.rss
      output = feed2exec.plugins.exec
      args = wget -P /srv/archives/nasa/ {item.link}

    The above is the equivalent of the archive plugin: it will save
    feed item links to the given directory.
    """
    logging.info('calling command: %s%s', [command] + list(args),
                 feed.get('catchup', '') and ' (simulated)')
    if feed.get('catchup'):
        return True
    return subprocess.check_call([command] + list(args))
