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

Example
-------

The user interface is still a bit rough, but this should get you
started::

    feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --filter feed2exec.plugins.html2text --folder nasa
    feed2exec fetch

An equivalent configuration file which may be more descriptive in
``~/.config/feed2exec/feed2exec.ini``::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  mailbox = '~/Maildir'
  filter = feed2exec.plugins.html2text

  [NASA breaking news]
  folder = nasa
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss

Using a standard OPML file, you can also import multiple feeds using
the `feed2exec import` command. See the complete :doc:`usage` page for
more information.

Installation
------------

This can be installed using the normal Python procedures::

  pip install .

It can also be ran straight from the source, using::

  python -m feed2exec

.. important:: Make sure you use Python 3. feed2exec is written to
               also support Python 2.7, but there may be performance
               or security issues in that older version. For example,
               Python 2.7 seems to suffer from a header injection flaw
               that currently makes tests fail.

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
