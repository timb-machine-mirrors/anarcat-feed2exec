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

.. image:: https://img.shields.io/pypi/l/feed2exec.svg
   :alt: AGPLv3 licensed
   :target: https://gitlab.com/anarcat/feed2exec/blob/master/LICENSE.rst

.. image:: https://gitlab.com/anarcat/feed2exec/badges/master/pipeline.svg
   :alt: pipeline status
   :target: https://gitlab.com/anarcat/feed2exec/commits/master

.. image:: https://gitlab.com/anarcat/feed2exec/badges/master/coverage.svg
   :alt: coverage report
   :target: https://gitlab.com/anarcat/feed2exec/commits/master

.. image:: https://img.shields.io/pypi/v/feed2exec.svg
   :alt: feed2exec version on PyPI
   :target: https://pypi.python.org/pypi/feed2exec

.. image:: https://badges.debian.net/badges/debian/stable/feed2exec/version.svg
   :alt: feed2exec version in stable
   :target: https://packages.debian.org/stable/feed2exec

.. image:: https://badges.debian.net/badges/debian/unstable/feed2exec/version.svg
   :alt: feed2exec version in unstable
   :target: https://packages.debian.org/unstable/feed2exec

.. marker-examples

Examples
--------

Simple run with no side effects::

  feed2exec parse https://www.nasa.gov/rss/dyn/breaking_news.rss --output echo --args '{item.title'}

Saving feed items to a Maildir folder::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --folder nasa
  feed2exec fetch

This creates the equivalent of this configuration file in ``~/.config/feed2exec.ini``::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  mailbox = '~/Maildir'

  [NASA breaking news]
  folder = nasa
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss

Send new feed items to Transmission::

  feed2exec add "Example torrent list" http://example.com/torrents/feed --output transmission --folder /srv/incoming

Send new feed items to Mastodon, using the `toot`_ commandline
client::

  feed2exec add "My site" http://example.com/blog/feed --output exec --args 'toot post "{item.title} {item.link}"'

Send new feed items to Twitter, using the tweet commandline client
from `python-twitter`_::

  feed2exec add "My site on twitter" http://example.com/blog/feed --output exec --args 'tweet "{item.title:40s} {item.link:100s}"'

Show feed contents::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --output echo --args "{item.title} {item.link}"
  feed2exec fetch

.. _toot: https://github.com/ihabunek/toot/
.. _python-twitter: https://github.com/bear/python-twitter

.. marker-installation

Multiple feeds can also be added with the OPML import command. See the
:doc:`usage` document for more information including known issues and
limitations.

Installation
------------

This can be installed using the normal Python procedures::

  pip install feed2exec

It can also be installed from source, using::

  pip install .

It can also be ran straight from the source, using::

  python -m feed2exec

.. important:: feed2exec is explicitly written for Python 3. It may be
               possible to backport it to Python 2 if there is
               sufficient demand, but there are too many convenient
               Python3 constructs to make this useful. Furthermore,
               all dependencies are well-packaged for Py3 and the
               platform is widely available. Upgrade already.

The program may also be available as an official package from your
Linux distribution.

`Source <https://gitlab.com/anarcat/feed2exec/>`_, `documentation
<https://feed2exec.readthedocs.io/>`_ and `issues
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

Design information
------------------

See the :doc:`design` document for more information about how and why the
program was built. The design document also features a comparison with other
similar software.
