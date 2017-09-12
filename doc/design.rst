Design
======

This is a quick prototype that turned out to be quite usable. The
design is minimal: some home-made ORM for the feed storage, crude
parallelism with the ``multiprocessing`` module and a simple plugin
API using ``importlib``.

The threading design, in particular, may be a little clunky and is
certainly less tested, which is why it is disabled by default (use
``--parallel`` to use it). I had multiple design in minds: the current
one (``multiprocessing.Pool`` and ``pool.apply_async``) vs ``aiohttp``
(on the ``asyncio`` branch) vs ``pool.map`` (on the ``threadpoolmap``
branch). The ``aiohttp`` design was very hard to diagnose and debug,
which made me abandon the whole thing. After reading up on `Curio`_
and `Trio`_, I'm tempted to give async/await a try again, but that
would mean completely dropping 2.7 compatibility. The ``pool.map``
design is just badly adapted, as it would load all the feed's
datastructure in memory before processing them.

 .. _Curio: http://curio.readthedocs.io/
 .. _Trio: https://github.com/python-trio/trio

Comparison
----------

``feed2exec`` is a fairly new and minimal program, so features you may
expect from another feed reader may not be present.

General information:

========= ======= ==== ==== ========
Program   Version Date SLOC Language
========= ======= ==== ==== ========
feed2exec  0.1    2017 1177  Python
feed2imap  2.5    2015 3348  Ruby
rss2email  3.9    2014 1754  Python
========= ======= ==== ==== ========

 * version: the version analysed
 * date: the date of that release
 * SLOC: Source Lines of Codes as counted by sloccount
 * Language: primary programming language

Delivery options:

========= ======= ==== ==== ========
Program   Maildir IMAP SMTP sendmail
========= ======= ==== ==== ========
feed2exec    ✓     ✗     ✗     ✗
feed2imap    ✓     ✓     ✗     ✗
rss2email    ✗     ✓     ✓     ✓
========= ======= ==== ==== ========

Features:

========= ======= ==== ===== ====== ====== ==== ===== ======
Program   Pause   OPML Retry Images Filter Exec Reply Digest
========= ======= ==== ===== ====== ====== ==== ===== ======
feed2exec    ✗     ✓     ✗     ✗       ✓    ✓     ✓     ✗
feed2imap    ✗     ✓     ✓     ✓       ✓    ✗     ✗     ✗
rss2email    ✓     ✓     ✓     ✗       ✗    ✗     ✓     ✓
========= ======= ==== ===== ====== ====== ==== ===== ======

 * pause: feed reading can be disabled temporarily by user
 * retry: tolerate temporary errors. For example, ``feed2imap`` will
   report errors only after 10 failures.
 * images: download images found in feed. ``feed2imap`` can download
   images and attach them to the email.
 * filter: if we can apply arbitrary filters to the feed
   output. feed2imap can apply filters to the unparsed dump of the
   feed.
 * exec: if users can configure arbitrary comands to run on new
   entries. feed2imap has a ``execurl`` parameter to execute commands,
   but it receives an unparsed dump of the feed instead of individual
   entries
 * reply: if the generated email 'from' header is usable to make a
   reply. ``rss2email`` has a ``use-publisher-email`` setting (off by
   default) for this, for example. feed2exec does this by default.
 * digest: possibility of sending a single email per run instead of
   one per entry

.. note:: ``feed2imap`` supports only importing OPML feeds, exporting
          is supported by a third-party plugin.

Known issues
------------

This is an early prototype and may break in your setup, as the
``feedparser`` library isn't as solid as I expected. In particular, I
had issues with `feeds without dates`_ and `without guid`_.

 .. _feeds without dates: https://github.com/kurtmckee/feedparser/issues/113
 .. _without guid: https://github.com/kurtmckee/feedparser/issues/112

Unit test coverage is incomplete, but still pretty decent, above 80%.

The ``exec`` plugin itself is not well tested and may have serious
security issues.

API, commandline interface, configuration file syntax and database
format can be changed at any moment.

No way to bypass the cache yet, use ``rm
~/.config/feed2exec/feed2exec.db`` to clear the cache for now.

The program is written mainly targeting Python 3.5 and should work in
3.6 but hasn't been explicitly tested there. Tests fail on Python 2.7
and the maildir handler may specifically be vulnerable to header
injections.
