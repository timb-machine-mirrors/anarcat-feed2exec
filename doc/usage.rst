feed2exec manual page
=====================

Synopsis
--------

**feed2exec** {add,ls,rm,fetch,import,export}

Description
-----------

This command will take a configured set of feeds and fire specific
plugin for every new item found in the feed.

Options
-------

  --version        Show the version and exit.
  --loglevel       show only warning messages
  -v, --verbose    be more verbose
  -d, --debug      even more verbose
  --database TEXT  use given database
  -h, --help       Show this message and exit.

Examples
--------

Saving feed items to a Maildir folder::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --plugin feed2exec.plugins.maildir --args /home/anarcat/Maildir/
  feed2exec fetch

Show feed contents::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --plugin feed2exec.plugins.echo
  feed2exec fetch

See also
--------

:manpage:`feed2imap(1)`, :manpage:`rss2email(1)`
