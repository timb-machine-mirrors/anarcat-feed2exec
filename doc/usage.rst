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
  --config TEXT    configuration directory
  -h, --help       Show this message and exit.

Examples
--------

Saving feed items to a Maildir folder::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --output feed2exec.plugins.maildir --output_args /home/anarcat/Maildir/ --filter feed2exec.plugins.html2text feed2exec fetch

Show feed contents::

  feed2exec add "NASA breaking news" https://www.nasa.gov/rss/dyn/breaking_news.rss --output feed2exec.plugins.echo --output_args "%(title)s %(link)s"
  feed2exec fetch

Files
-----

Any files used by feed2exec is stored in the config directory, in
``~/.config/feed2exec/`` or ``$XDG_CONFIG_HOME/feed2exec``. It can
also be specified with the ``--config`` commandline parameter. The
main configuration file is in called ``feed2exec.ini``. The above
commandline will yield the following configuration::

  [NASA breaking news]
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss
  output = feed2exec.plugins.echo
  output_args = %(title)s %(link)s

Naturally, those settings can be changed directly in the config
file. Note that there is a ``[DEFAULT]`` section that can be used to
apply settings to all feeds. For example, this will make all feeds
store new items in a maildir subfolder::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  output_args = /home/anarcat/Maildir/
  filter = feed2exec.plugins.html2text

This way individual feeds do not need to be indivudually configured.

The feeds cache is stored in a ``feed2exec.sqlite`` file. It is a
normal SQLite database and can be inspected using the normal sqlite
tools. It is used to keep track of which feed items have been
processed. To clear the cache, you can simply remove the file, which
will make the program process all feeds items from scratch again. In
this case, you may want to use the ``null`` output plugin to avoid
doing any sort of processing to catchup with the feeds.

See also
--------

:manpage:`feed2imap(1)`, :manpage:`rss2email(1)`
