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

 * parse::

     parse URL
         [--output PLUGIN [--args ARG [ARG [...]]]
         [--filter PLUGIN] [--filter_args ARG [ARG [...]]]
         [--mailbox PATH] [--folder PATH]

   The parse command loads and parses a single feed, without touching
   the database. This is similar to calling `add` then `fetch` on a
   single feed, but the feed is not kept in the configuration. This is
   designed to make quick tests with a new feed. The arguments are the
   same as the `add` command.

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

     add NAME URL
         [--output PLUGIN [--args ARG [ARG [...]]]
         [--filter PLUGIN] [--filter_args ARG [ARG [...]]]
         [--mailbox PATH] [--folder PATH]

   The add command adds the given feed ``NAME`` that will be fetched
   from the provided ``URL``.

       --output PLUGIN  use PLUGIN as an output module. defaults to
                        ``maildir`` to store in a mailbox. use
                        ``null`` to just fetch the feed without
                        fetching anything. Modules are searched in the
                        `feed2exec.plugins` package unless the name
                        contains a dot in which case the whole Python
                        search path is used.
       --args ARGS      pass arguments ARGS to the output
                        module. supports interpolation of feed
                        parameters using, for example ``{title}``
       --filter PLUGIN  filter feed items through the PLUGIN filter
                        plugin
       --filter_args A  arguments passed to the filter plugin
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
  args = {title} {link}

Naturally, those settings can be changed directly in the config
file. Note that there is a ``[DEFAULT]`` section that can be used to
apply settings to all feeds. For example, this will make all feeds
store new items in a maildir subfolder::

  [DEFAULT]
  output = feed2exec.plugins.maildir
  folder = feeds

This way individual feeds do not need to be individually configured.

.. note:: feed2exec does not take care of adding the folder to
          "subscriptions" in the mailbox. it is assumed that folders
          are auto-susbcribed or the user ignores subscription. if
          that is a problem, you should subscribe to the folder by
          hand in your email client when you add a new config. you can
          also subscribe to a folder (say ``feeds`` above) directly
          using the ``doveadm mailbox subscribe feeds`` command in
          Dovecot, for example.

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
      Skip to the latest feed items. The feed is still read and
      parsed, and new feed items are added to the database, but output
      plugins are never called. 

  pause
      Completely skip feed during fetch or parse. Similar to catchup,
      but doesn't fetch the feed at all and doesn't touch the cache.

Here is a more complete example configuration with all the settings
used:

.. include:: ../feed2exec.ini
   :literal:

Cache database
~~~~~~~~~~~~~~

The feeds cache is stored in a ``feed2exec.sqlite`` file. It is a
normal SQLite database and can be inspected using the normal sqlite
tools. It is used to keep track of which feed items have been
processed. To clear the cache, you can simply remove the file, which
will make the program process all feeds items from scratch again. In
this case, you may want to use the ``null`` output plugin to avoid
doing any sort of processing to catchup with the feeds.

Limitations
-----------

Feed support is only as good as ``feedparser`` library which isn't as solid as
I expected. In particular, I had issues with `feeds without dates`_ and
`without guid`_.

 .. _feeds without dates: https://github.com/kurtmckee/feedparser/issues/113
 .. _without guid: https://github.com/kurtmckee/feedparser/issues/112

Unit test coverage is incomplete, but still pretty decent, above 90%.

The ``exec`` plugin itself is not well tested and may have serious
security issues.

API, commandline interface, configuration file syntax and database format can
be changed until the 1.0 release is published, at which point normal `Semantic
Versioning <http://semver.org>`_ semantics apply.

The program is written mainly targeting Python 3.5 and should work in
3.6. Python 2.7 is not supported anymore.

The SQL storage layer is badly written and is known to trigger locking
issues with SQLite when doing multiprocessing. The global LOCK object
could be used to work around this issue but that could mean pretty bad
coupling. A good inspiration may be the `beets story about this
problem <http://beets.io/blog/sqlite-nightmare.html>`_. And of course,
another alternative would be to considering something like SQLalchemy
instead of rolling our own ORM.

Older feed items are not purged from the database when they disappear from the
feed, which may lead to database bloat in the long term.

See also
--------

:manpage:`feed2exec-plugins(1)`, :manpage:`feed2imap(1)`, :manpage:`rss2email(1)`
