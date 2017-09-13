======================================
 feed2exec - programmable feed reader
======================================

``feed2exec`` is a simple program that runs custom actions on new RSS
feed items (or whatever `feedparser`_ can read). It currently has
support for writing into mailboxes (`Maildir`_ folders) or executing
commands, but more actions can be easily implemented through
plugins. Email are saved as multipart plain/HTML and can be sent to
arbitrary folders.

 .. _feedparser: https://pypi.python.org/pypi/feedparser
 .. _Maildir: https://en.wikipedia.org/wiki/Maildir

.. marker-examples

Examples
--------

Saving feed items to a Maildir folder::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --folder nasa
  feed2exec fetch

This creates the equivalent of this configuration file in ``~/.config/feed2exec/feed2exec.ini``::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  mailbox = '~/Maildir'

  [NASA breaking news]
  folder = nasa
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss


Send new feed items to Transmission::

  feed2exec add "Example torrent list" http://example.com/torrents/feed --output feed2exec.plugins.exec --args 'transmission-remote marcos.anarc.at -a '{item.link}' -w /srv/incoming'

Send new feed items to Mastodon, using the `toot`_ commandline
client::

  feed2exec add "My torrent" http://example.com/blog/feed --output feed2exec.plugins.exec --args 'toot post "{item.title} {item.link}"'

Send new feed items to Twitter, using the tweet commandline client
from `python-twitter`_::

  feed2exec add "My torrent" http://example.com/blog/feed --output feed2exec.plugins.exec --args 'tweet "{item.title:40s} {item.link:100s}"'

Show feed contents::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --output feed2exec.plugins.echo --args "{item.title} {item.link}"
  feed2exec fetch

.. _toot: https://github.com/ihabunek/toot/
.. _python-twitter: https://github.com/bear/python-twitter

.. marker-installation

Multiple feeds can also be added with the OPML import command. See the
:doc:`usage` document for more information.

Installation
------------

This can be installed using the normal Python procedures::

  pip install feed2exec

It can also be installed from source, using::

  pip install .

It can also be ran straight from the source, using::

  python -m feed2exec

.. important:: Make sure you use Python 3. feed2exec is written to
               also support Python 2.7, but there may be performance
               or security issues in that older version. For example,
               Python 2.7 seems to suffer from a header injection flaw
               that currently makes tests fail.

`Source <https://gitlab.com/anarcat/feed2exec/>`_, `documentation
<https://anarcat.gitlab.io/feed2exec/>`_ and `issues
<https://gitlab.com/anarcat/feed2exec/issues>`_ are available on
GitLab.

Why the name?
-------------

There are already `feed2tweet`_ and `feed2imap`_ out there so I
figured I would just reuse the prefix and extend *both* programs at
once.

.. _feed2tweet: https://github.com/chaica/feed2tweet
.. _feed2imap: https://github.com/feed2imap/feed2imap/

.. marker-toc

Design and known issues
-----------------------

See the :doc:`design` document for more information about how and why
the program was built and its limitations. The design document also
features a comparison with other similar software.
