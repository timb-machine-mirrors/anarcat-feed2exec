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
