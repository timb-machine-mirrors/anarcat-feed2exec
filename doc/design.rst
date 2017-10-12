Design
======

This is a quick prototype that turned out to be quite usable. The
design is minimal: some home-made ORM for the feed storage, crude
parallelism with the ``multiprocessing`` module and a simple plugin
API using ``importlib``, since we do not need discovery. There is some
code duplication between different parts (e.g. the
:func:`feed2exec.plugins.output` and :func:`feed2exec.plugins.filter`
plugin interfaces, the ``maildir`` and ``mbox`` plugins, etc), but
never more than twice.

The threading design may be a little clunky and is certainly less
tested, which is why it is disabled by default (use ``--parallel`` to
use it). There are known deadlocks issues with high concurrency
scenarios (e.g. with ``catchup`` enabled). I had multiple design in
minds: the current one (``multiprocessing.Pool`` and
``pool.apply_async``) vs ``aiohttp`` (on the ``asyncio`` branch) vs
``pool.map`` (on the ``threadpoolmap`` branch). The ``aiohttp`` design
was very hard to diagnose and debug, which made me abandon the whole
thing. After reading up on `Curio`_ and `Trio`_, I'm tempted to give
async/await a try again, but that would mean completely dropping 2.7
compatibility. The ``pool.map`` design is just badly adapted, as it
would load all the feed's datastructure in memory before processing
them.

The test suite is heavily coupled with the `pytest module
<https://pytest.org/>`_. It also uses the `vcrpy
<https://pypi.python.org/pypi/vcrpy>`_ module to cache HTTP
requests. `betamax <https://pypi.python.org/pypi/betamax>`_ was also
considered but requires a refactoring of *all* requests to use session
objects. This would have the added benefit of allowing a custom user
agent, so it is still considered and is a work in progress in the
`betamax` branch. The current approach on that branch uses a global
``session`` object which is problematic: a better approach may be to
encapsulate this in a ``FeedFetcher`` or simply ``Feed`` object, at
which point we would end up rearchitecturing the whole ``feeds.py``
file...

More information about known issues and limitations in the
:doc:`usage` section. Information about plugins and how to write them
in the :doc:`plugins` document.

 .. _Curio: http://curio.readthedocs.io/
 .. _Trio: https://github.com/python-trio/trio

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
feed2exec  0.5    2017 1417  Python
feed2imap  1.2.5  2015 3249  Ruby
rss2email  3.9    2014 1986  Python
========= ======= ==== ==== ========

 * version: the version analysed
 * date: the date of that release
 * SLOC: Source Lines of Codes as counted by sloccount, only counting
   dominant language (e.g. excluding XML from test feeds)
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
   <r2e-maildir>`_ to implement maildir support, but it's not merged
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
