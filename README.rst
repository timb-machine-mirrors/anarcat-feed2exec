============================================
 feed2exec - execute code on new feed items
============================================

``feed2exec`` is a simple program that runs arbitrary commands on
snippets of RSS (or whatever `feedparser`_ can read).

 .. _feedparser: https://pypi.python.org/pypi/feedparser

.. marker-toc

Usage
=====

Quick start
-----------

The user interface is still a bit rough, but this should get you
started::

    feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --output feed2exec.plugins.maildir --args "~/Maildir/" --filter feed2exec.plugins.html2text
    feed2exec fetch

An equivalent configuration file which may be more descriptive in
``~/.config/feed2exec/feed2exec.ini``::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  output_args = '~/Maildir'
  filter = feed2exec.plugins.html2text

  [NASA breaking news]
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

Community guidelines
--------------------

The community guidelines are described in the :doc:`contribute`
document, which provides a nice template that I reuse in other
projects. It includes:

 * a code of conduct
 * how to send patches
 * how documentation works
 * how to report bugs
 * how to make a release

Why the name?
-------------

There are already `feed2tweet`_ and `feed2imap`_ out there so I
figured I would just reuse the prefix and extend *both* programs at
once.
