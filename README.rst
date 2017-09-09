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

    feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --output feed2exec.plugins.maildir --args "/home/anarcat/Maildir/" --filter feed2exec.plugins.html2text
    feed2exec fetch

See the complete :doc:`usage` page for more information.

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
