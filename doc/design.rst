Design
======

This is a quick prototype that turned out to be quite usable. The
design is minimal: some home-made ORM for the feed storage, crude
parallelism with the ``multiprocessing`` module and a simple plugin
API using ``importlib``.

More information about known issues and limitations in the
:doc:`usage` document.

Quick tour
----------

The most common workflow is through the `fetch` subcommand and goes
something like this:

 1. ``__main__.py`` is the main entrypoint, managed through the
    :mod:`click` module, which normally calls functions defined in
    ``controller.py``. The base command (`__main__.main`) creates a
    :class:`feed2exec.controller.FeedManager` object which gets passed to
    subcommands. In our case, it passes the control to the ``fetch``
    subcommand.

 2. The fetch command calls the 
    :func:`feed2exec.controller.FeedManager.fetch` function which creates a
    :class:`feed2exec.model.Feed` object that is then used to parse
    the feed and return it as an opaque `data` object as returned by
    :mod:`feedparser`. The feed is parsed (and, below, dispatched)
    only if it not already present in the cache, managed by the
    `cachecontrol <https://cachecontrol.readthedocs.io/>`_ module.

 3. ``fetch`` then calls the
    :func:`feed2exec.controller.FeedManager.dispatch` function that calls the
    various filter and output plugins, passing in the feed
    configuration and one item at a time. The filters can modify the
    feed items while the output plugins are responsible for writing
    them somewhere. That distinction is mostly arbitrary, but the
    return values of the output plugins matter, while filters do not.

The feed cache is stored in a minimal :mod:`sqlite3` database. A table
keeps track of which feed item has been seen and another is the
backend for the ``cachecontrol`` module and has a copy of the actual
requests, keyed by URL.

Configuration is stored in a ``.ini`` file or whatever
:mod:`configparser` supports. It was originally stored in the database
as well, but it was found inconvenient to modify by hand and a
configuration file was used instead. The ``.ini`` file format was
chosen because it is well supported by Python and allows for default
settings.

There is the possibility for this project to cover more than RSS/Atom
feeds. In theory, the ``parse`` function could also be pluggable and
support *reading* from other data sources like Twitter or Facebook,
which would bring us closer to the `IFTTT
<https://en.wikipedia.org/wiki/IFTTT>`_ concept.

Plugin system
-------------

Plugins are documented in the :doc:`plugins` section. You can also
refer to the :ref:`writing-plugins` section if you wish to write a new
plugin or extend an existing one.

The plugin system uses a simple :mod:`importlib` based architecture
where plugin are simple Python modules loaded at runtime based on a
module path provided by the user. This pattern was inspired by a
`StackOverflow discussion <http://stackoverflow.com/questions/932069/building-a-minimal-plugin-architecture-in-python>`_.

The following options were also considered:

  - `pluggy`_: used by py.test, tox and devpi
  - `yapsy`_
  - `PluginBase`_
  - `plugnplay`_
  - `click-plugins`_: relevant only to add new commands
  - `PyPA plugin discovery`_

.. _pluggy: https://github.com/pytest-dev/pluggy
.. _yapsy: http://yapsy.sourceforge.net/
.. _PluginBase: http://pluginbase.pocoo.org/
.. _plugnplay: https://github.com/daltonmatos/plugnplay
.. _click-plugins: https://github.com/click-contrib/click-plugins
.. _PyPA plugin discovery: https://packaging.python.org/guides/creating-and-discovering-plugins/

Those options were ultimately not used because they add an aditionnal
dependency and are more complicated than a simple ``import``. We also
did not need plugin listing or discovery, which greatly simplifies our
design.

There is some code duplication between different parts (e.g. the
:func:`feed2exec.plugins.output` and :func:`feed2exec.plugins.filter`
plugin interfaces, the ``maildir`` and ``mbox`` plugins, etc), but
never more than twice.

Concurrent processing
---------------------

The threading design may be a little clunky and is certainly less
tested, which is why it is disabled by default (use ``--parallel`` to
use it). There are known deadlocks issues with high concurrency
scenarios (e.g. with ``catchup`` enabled).

I had multiple design in minds: the current one
(``multiprocessing.Pool`` and ``pool.apply_async``) vs ``aiohttp`` (on
the ``asyncio`` branch) vs ``pool.map`` (on the ``threadpoolmap``
branch). The ``aiohttp`` design was very hard to diagnose and debug,
which made me abandon the whole thing. After reading up on `Curio`_
and `Trio`_, I'm tempted to give async/await a try again, but that
would mean completely dropping 2.7 compatibility. The ``pool.map``
design is just badly adapted, as it would load all the feed's
datastructure in memory before processing them.

The current parallel design also doesn't profit much from the caching
system. While before we would spend a lot of time parsing all feeds
(in parallel), now most feeds are not parsed anymore (because
unchanged) so a lot of time is spent doing HTTP requests, which could
be done in parallel (but currently isn't).

 .. _Curio: http://curio.readthedocs.io/
 .. _Trio: https://github.com/python-trio/trio

.. _testsuite:

Test suite
----------

The test suite is in ``feed2exec/tests`` but also as doctest comments
in some functions imported from the `ecdysis`_ project. You can run
all the tests with `pytest`_, using, for example::

  pytest-3

This is also hooked into the ``setup.py`` command, so this also works::

  python3 setup.py test

.. note:: It's recommended to use the ``tox`` command to run tests, as
          some tests are picky about dependencies version
          numbers. That's how the Continuous Integration (CI) system
          runs tests, through the ``.gitlab-ci.yml`` file.

Enabling the `catchlog`_ plugin will also enable logging in the test
suite which will help diagnostics.

.. _catchlog: https://pypi.python.org/pypi/pytest-catchlog/

Note that some tests will fail in Python 2, as the code is written and
tested in Python3. Furthermore, the feed output is taken from an up to
date (5.2.1) feedparser version, so the tests are marked as expected
to fail for lower versions. You should, naturally, run and write tests
before submitting patches. See the :ref:`writing-tests` section for
more information about how to write tests.

.. _pytest: http://pytest.org/
.. _ecdysis: https://gitlab.com/anarcat/ecdysis

The test suite also uses the `betamax`_ module to cache HTTP requests
locally so the test suite can run offline. If a new test requires
networking, you can simply add a new test doing requests with the
right fixture (:func:`betamax_session`) provided by upstream if you
are going to do standalone HTTP request (not going through the
feed2exec libraries). But you would more likely use the existing
session by using the :func:`feed2exec.tests.fixtures.feed_manager`
fixture, which has a `session` member you can use.

If a new test is added in an *existing* test, you may need to
configure `recording
<https://betamax.readthedocs.io/en/latest/record_modes.html>`_ (in
``feed2exec/tests/conftest.py``) to ``new_episodes``::

    config.default_cassette_options['record_mode'] = 'none'

We commit the recordings in git so the test suite actually runs
offline, so be careful about the content added there. Ideally, the
license of that content should be documented in ``debian/copyright``.

`vcrpy`_ was first used for tests since it was simpler and didn't
require using a global :mod:`requests.session.Session` object. But in
the end betamax seems better maintained and more flexible: it supports
pytest fixtures, for example, and multiple cassette storage (including
vcr backwards compatibility). Configuration is also easier, done in
``feed2exec/tests/conftest.py``. Using a session also allows us to use
a custom user agent.

.. _vcrpy: https://pypi.python.org/pypi/vcrpy
.. _betamax: https://pypi.python.org/pypi/betamax

Comparison
----------

``feed2exec`` is a fairly new and minimal program, so features you may
expect from another feed reader may not be present. I chose to write a
new program because, when I started, both existing alternatives were
in a questionable state: feed2imap was mostly abandoned and
rss2email's maintainer was also unresponsive. Both were missing the
features I was looking for, which was to unify my feed parsers in a
single program: i needed something that could deliver mail, run
commands and send tweets. The latter isn't done yet, but I am hoping
to complete this eventually.

The program may not be for everyone, however, so I made those
comparison tables to clarify what feed2exec does compared to the
alternatives.

General information:

========= ======= ==== ==== ========
Program   Version Date SLOC Language
========= ======= ==== ==== ========
feed2exec  0.10   2017  989  Python
feed2imap  1.2.5  2015 3238  Ruby
rss2email  3.9    2014 1754  Python
========= ======= ==== ==== ========

 * version: the version analysed
 * date: the date of that release
 * SLOC: Source Lines of Codes as counted by sloccount, only counting
   dominant language (e.g. excluding XML from test feeds) and
   excluding tests
 * Language: primary programming language

Delivery options:

========= ======= ==== ==== ==== ======== ====
Program   Maildir Mbox IMAP SMTP sendmail exec
========= ======= ==== ==== ==== ======== ====
feed2exec    ✓     ✓    ✗     ✗     ✗      ✓
feed2imap    ✓     ✗    ✓     ✗     ✗      ✗
rss2email    ✗     ✗    ✓     ✓     ✓      ✗
========= ======= ==== ==== ==== ======== ====

 * maildir: writing to `Maildir`_ folders. r2e has a `pull request
   <r2e-maildir_>`_ to implement maildir support, but it's not merged
   at the time of writing
 * IMAP: sending emails to IMAP servers
 * SMTP: delivering emails over the SMTP protocol, with authentication
 * sendmail: delivering local using the local MTA
 * exec: run arbitrary comands to run on new entries. feed2imap has a
   ``execurl`` parameter to execute commands, but it receives an
   unparsed dump of the feed instead of individual entries. rss2email
   has a postprocess filter that is a Python plugin that can act on
   indiviual (or digest) messages which could possibly be extended to
   support arbitrary commands, but that is rather difficult to
   implement for normal users.

 .. _Maildir: https://en.wikipedia.org/wiki/Maildir
 .. _r2e-maildir: https://github.com/wking/rss2email/pull/21

Features:

========= ======= ==== ===== ====== ====== ===== ======
Program   Pause   OPML Retry Images Filter Reply Digest
========= ======= ==== ===== ====== ====== ===== ======
feed2exec    ✓     ✓     ✗     ✗       ✓     ✓     ✗
feed2imap    ✗     ✓     ✓     ✓       ✓     ✗     ✗
rss2email    ✓     ✓     ✓     ✗       ✓     ✓     ✓
========= ======= ==== ===== ====== ====== ===== ======

 * pause: feed reading can be disabled temporarily by user. in
   feed2exec, this is implemented with the ``pause`` configuration
   setting. the ``catchup`` option can also be used to catchup with
   feed entries.
 * retry: tolerate temporary errors. For example, ``feed2imap`` will
   report errors only after 10 failures.
 * images: download images found in feed. ``feed2imap`` can download
   images and attach them to the email.
 * filter: if we can apply arbitrary filters to the feed
   output. feed2imap can apply filters to the unparsed dump of the
   feed.
 * reply: if the generated email 'from' header is usable to make a
   reply. ``rss2email`` has a ``use-publisher-email`` setting (off by
   default) for this, for example. feed2exec does this by default.
 * digest: possibility of sending a single email per run instead of
   one per entry

.. note:: ``feed2imap`` supports only importing OPML feeds, exporting
          is supported by a third-party plugin.

.. note:: ``feed2exec`` might one day be expanded to support other
          feeds than RSS/Atom, and turn into a more generic
          "if-this-then-that" type of program, to support, say, REST
          APIs, or Gemini, or whatever. In the meantime, see
          `gmi2email <https://manpages.debian.org/gmi2email>`_ for an
          alternative supporting Gemini.
