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
  --loglevel       choose specific log level [default: WARNING]
  -v, --verbose    show what is happening (loglevel: VERBOSE)
  -d, --debug      show debugging information (loglevel: DEBUG)
  --syslog LEVEL   send LEVEL logs to syslog
  --config TEXT    configuration directory
  -h, --help       Show this message and exit.

.. include:: ../README.rst
   :start-after: marker-examples
   :end-before: marker-installation

Commands
--------

 * fetch::

     fetch [--parallel | -p | --jobs N | -j N] [--force | -f] [pattern]

   The fetch command iterates through all the configured feeds or
   those matching the ``pattern`` substring if provided.

       --force     skip reading and writing the cache and
                   will consider all entries as new
       --catchup   do not run output plugins, equivalent of setting
                   the output plugin to ``feed2exec.plugins.null``
       --parallel  run parsing in the background to improve
                   performance
       --jobs N    run N tasks in parallel maximum. implies
                   ``--parallel`` which defaults to the number of CPUs
                   detected on the machine

 * add::

     add [--output PLUGIN [--args ARG [ARG [...]]] [--filter PLUGIN] NAME URL

   The add command adds the given feed ``NAME`` that will be fetched
   from the provided ``URL``.

       --output PLUGIN  use PLUGIN as an output module. defaults to
                        ``feed2exec.plugins.maildir`` to store in a
                        mailbox. use ``feed2exec.plugins.null`` to
                        just fetch the feed without fetching
                        anything.
       --args ARGS      pass arguments ARGS to the output
                        module. supports interpolation of feed
                        parameters using, for example ``%(title)s``
       --filter PLUGIN  filter feed items through the PLUGIN filter
                        plugin
       --mailbox PATH   folder to store email into, defaults to
                        ``~/Maildir``.
       --folder PATH    subfolder to store the email into

   Those parameters are documented more extensively in their
   equivalent settings in the configuration file, see below.

 * ls:

   The ``ls`` command lists all configured feeds as JSON packets.

 * rm::

     rm NAME

   Remove the feed named ``NAME`` from the configuration.

 * import::

     import PATH

   Import feeds from the file named PATH. The file is expected to have
   ``outline`` elements and only the ``title`` and ``xmlUrl`` elements
   are imported, as ``NAME`` and ``URL`` parameters, respectively.

 * export::

     export PATH

   Export feeds into the file named PATH. The file will use the feed
   NAME elements as ``title`` and the URL as ``xmlUrl``.

Files
-----

Configuration file
~~~~~~~~~~~~~~~~~~

Any files used by feed2exec is stored in the config directory, in
``~/.config/feed2exec/`` or ``$XDG_CONFIG_HOME/feed2exec``. It can
also be specified with the ``--config`` commandline parameter. The
main configuration file is in called ``feed2exec.ini``. The above
commandline will yield the following configuration::

  [NASA breaking news]
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss
  output = feed2exec.plugins.echo
  args = %(title)s %(link)s

Naturally, those settings can be changed directly in the config
file. Note that there is a ``[DEFAULT]`` section that can be used to
apply settings to all feeds. For example, this will make all feeds
store new items in a maildir subfolder::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  folder = feeds

This way individual feeds do not need to be indivudually configured.

The following configuration parameters are supported:

  name
      Human readable name for the feed. Equivalent to the ``NAME``
      argument in the ``add`` command.

  url
      Address to fetch the feed from. Can be HTTP or HTTPS, but also
      ``file://`` resources for test purposes.

  output
      Output plugin to use. Equivalent to the ``--output`` option in
      the ``add`` command.

  args
      Arguments to pass to the output plugin. Equivalent to the
      ``--args`` option in the ``add`` command.

  filter
      Filter plugin to use. Equivalent to the ``--filter`` option in
      the ``add`` command.

  mailbox
      Store emails in that mailbox prefix. Defaults to ``~/Maildir``.

  folder
      Subfolder to use when writing to a mailbox. By default, a
      *slugified* version of the feed name (where spaces and special
      character are replaced by ``-``) is used. For example, the feed
      named "NASA breaking news" would be stored in
      ``~/Maildir/nasa-breaking-news/``.

  catchup
      Disable output plugin execution. In this mode, the feed is still
      read and parsed, but new entries are not added to the database.

  pause
      Completely skip feed during fetch. Similar to catchup, but
      doesn't fetch the feed at all and doesn't touch the cache.

Cache database
~~~~~~~~~~~~~~

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
