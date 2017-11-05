Plugins
=======

This is a quick overview of the available plugins.

Output plugins
--------------

Archive
~~~~~~~

.. automodule:: feed2exec.plugins.archive
   :members:

Echo
~~~~

.. automodule:: feed2exec.plugins.echo
   :members:

Error
~~~~~

.. automodule:: feed2exec.plugins.error
   :members:

Exec
~~~~

.. automodule:: feed2exec.plugins.exec
   :members:

Maildir
~~~~~~~

.. automodule:: feed2exec.plugins.maildir
   :members:

Mbox
~~~~

.. automodule:: feed2exec.plugins.mbox
   :members:

Null
~~~~

.. automodule:: feed2exec.plugins.null
   :members:

Transmission
~~~~~~~~~~~~

.. automodule:: feed2exec.plugins.transmission
   :members:

Wayback
~~~~~~~

.. automodule:: feed2exec.plugins.wayback
   :members:

Filter plugins
--------------

Droptitle
~~~~~~~~~

.. automodule:: feed2exec.plugins.droptitle
   :members:


Emptysummary
~~~~~~~~~~~~

.. automodule:: feed2exec.plugins.emptysummary
   :members:

Html2text
~~~~~~~~~

.. automodule:: feed2exec.plugins.html2text
   :members:

Ikiwiki Recentchanges
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: feed2exec.plugins.ikiwiki_recentchanges
   :members:

.. _writing-plugins:

Writing new plugins
-------------------

Most of the actual work in the program is performed by plugins. A
plugin is a simple Python module that has a ``output`` or ``filter``
"callable" (function or class) with a predefined interface.

Basic plugin principles
~~~~~~~~~~~~~~~~~~~~~~~

To write a new plugin, you should start by creating a simple Python
module, in your `PYTHONPATH
<https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH>`_. You
can find which directories are in the path by calling::

  $ python3 -c "import sys; print(sys.path)"
  ['', '/usr/lib/python35.zip', '/usr/lib/python3.5', '/usr/lib/python3.5/plat-x86_64-linux-gnu', '/usr/lib/python3.5/lib-dynload', '/usr/local/lib/python3.5/dist-packages', '/usr/lib/python3/dist-packages']

In the above example, a good location would be
``/usr/local/lib/python3.5/dist-packages``. The naming convention is
loose: as long as the plugin matches the expected API, it should just
work. For the purpose of this demonstration, we'll call our plugin
`trumpery <https://en.wiktionary.org/wiki/trumpery>`_, so we will
create the plugin code like this::

  touch /usr/local/lib/python3.5/dist-packages/trumpery.py

Naturally, if you are going to write multiple plugins, you may want to
regroup your multiple plugins in a package, see the `module
documentation <https://docs.python.org/3/tutorial/modules.html>`_ for
more information about this concept in Python.

You are welcome to distribute plugins separately or send them as merge
requests, see :doc:`contribute` for more information on how to
participate in this project. We of course welcome contributions to
this documentation as well!

Filters
~~~~~~~

Now, you need your plugin to do something. In our case, let's say we'd
like to skip any feed entry that has the word `Trump
<https://en.wikipedia.org/wiki/Trump>`_ in it. For that purpose, we'll
create a plugin similar to the already existing
:mod:`feed2exec.plugins.droptitle` plugin, but that operates on the
*body* of the feed, but that also hardcodes the word, because this is
just a demonstration and we want to keep it simple. Let's look at the
title plugin to see how it works:

.. include:: ../feed2exec/plugins/droptitle.py
   :code: python
   :literal:

That may look like complete gibberish to you if you are not familiar
with programming or with Python programming in particular. But let's
take this from the top and copy that in our own plugin. The first line
declares a `function
<https://en.wikibooks.org/wiki/Python_Programming/Functions>`_ that
takes at least a ``feed`` and a ``item`` argument, but can also accept
any other arbitrary argument. This is important because we want to
have the plugin keep on working if the plugin API changes in the
future. This is called "forward-compatibility". So let's copy that in
our plugin and add a ``pass`` statement to make sure the plugin works
(even if it does nothing for now)::

  def filter(*args, feed=None, item=None, **kwargs):
      pass

We can already test our plugin by adding it to our configuration, in
``~/.config/feed2exec/feed2exec.ini``::

  [NASA]
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss
  output = feed2exec.plugins.echo
  args = {item.title}
  filter = trumpery

Notice how we use the ``output`` plugin to show the title of feed
items selected, as a debugging tool. Let's fetch this feed in
debugging mode to see what happens::

  $ python3 -m feed2exec --verbose fetch --force
  opening local file /home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml
  parsing feed file:///home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml (10355 bytes)
  connecting to database at ./doc/feed2exec.db
  arguments received: ('President Trump Welcomes Home Record-breaking NASA Astronaut Peggy Whitson',)
  arguments received: ('Three International Space Station Crewmates Safely Return to Earth',)
  arguments received: ('NASA Statement on Nomination for Agency Administrator',)
  arguments received: ('NASA Television to Air Return of Three International Space Station Crew Members',)
  arguments received: ('NASA and Iconic Museum Honor Voyager Spacecraft 40th Anniversary',)
  arguments received: ('NASA’s Johnson Space Center Closes Through Labor Day for Tropical Storm Harvey',)
  arguments received: ('NASA Cancels Planned Media Availabilities with Astronauts',)
  arguments received: ('NASA Awards $400,000 to Top Teams at Second Phase of 3D-Printing Competition',)
  arguments received: ('NASA Awards Contract for Center Protective Services for Glenn Research Center',)
  arguments received: ('NASA Announces Cassini End-of-Mission Media Activities',)
  1 feeds processed

Good! The feed is fetched and items are displayed. It means our filter
didn't interfere, but now it's time to make it *do* something. To skip
items, we need to set the ``skip`` attribute for the feed item to
`True` if we want to skip it and `False` otherwise. So we'll use a
simple recipe, a bit like `droptitle` does, but simpler, to look at
the feed content to look for our evil word. The :mod:`feedparser`
documentation tells us feed items have a `summary
<https://pythonhosted.org/feedparser/reference-entry-summary.html>`_
field which we can inspect. There's also a `content
<https://pythonhosted.org/feedparser/reference-entry-content.html#reference-entry-content>`_
list, but that's a little more complicated so we'll skip that for
now. So, let's set the ``skip`` parameter to match if there is the
evil word in our feed item, like this::

  def filter(*args, feed=None, item=None, **kwargs):
      item['skip'] = 'Trump' in item.get('summary', '')

And let's see the result (note that we use the ``--force`` argument
here otherwise we would just skip all items because of the cache)::

  $ python3 -m feed2exec --verbose fetch --force
  opening local file /home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml
  parsing feed file:///home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml (10355 bytes)
  connecting to database at ./doc/feed2exec.db
  item President Trump Welcomes Home Record-breaking NASA Astronaut Peggy Whitson of feed NASA filtered out
  arguments received: ('Three International Space Station Crewmates Safely Return to Earth',)
  item NASA Statement on Nomination for Agency Administrator of feed NASA filtered out
  arguments received: ('NASA Television to Air Return of Three International Space Station Crew Members',)
  arguments received: ('NASA and Iconic Museum Honor Voyager Spacecraft 40th Anniversary',)
  arguments received: ('NASA’s Johnson Space Center Closes Through Labor Day for Tropical Storm Harvey',)
  arguments received: ('NASA Cancels Planned Media Availabilities with Astronauts',)
  arguments received: ('NASA Awards $400,000 to Top Teams at Second Phase of 3D-Printing Competition',)
  arguments received: ('NASA Awards Contract for Center Protective Services for Glenn Research Center',)
  arguments received: ('NASA Announces Cassini End-of-Mission Media Activities',)
  1 feeds processed

Successs! We have skipped the two items that contain the fraud we
wanted to remove from the world. Notice how we were able to *modify*
the feed item: we can also use that to *change* the feed
content. Normally, we would use this to fix malformed feeds, but let's
have some fun instead and `rename Trump to Drumpf
<https://en.wikipedia.org/wiki/Donald_Trump_(Last_Week_Tonight)>`_::

  def filter(*args, feed=None, item=None, **kwargs):
      item['title'] = item.get('title', '').replace('Trump', 'Drumpf')

And the result::

  $ python3 -m feed2exec --verbose fetch --force
  opening local file /home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml
  parsing feed file:///home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml (10355 bytes)
  connecting to database at ./doc/feed2exec.db
  arguments received: ('President Drumpf Welcomes Home Record-breaking NASA Astronaut Peggy Whitson',)
  arguments received: ('Three International Space Station Crewmates Safely Return to Earth',)
  arguments received: ('NASA Statement on Nomination for Agency Administrator',)
  arguments received: ('NASA Television to Air Return of Three International Space Station Crew Members',)
  arguments received: ('NASA and Iconic Museum Honor Voyager Spacecraft 40th Anniversary',)
  arguments received: ('NASA’s Johnson Space Center Closes Through Labor Day for Tropical Storm Harvey',)
  arguments received: ('NASA Cancels Planned Media Availabilities with Astronauts',)
  arguments received: ('NASA Awards $400,000 to Top Teams at Second Phase of 3D-Printing Competition',)
  arguments received: ('NASA Awards Contract for Center Protective Services for Glenn Research Center',)
  arguments received: ('NASA Announces Cassini End-of-Mission Media Activities',)
  1 feeds processed

I know, absolutely hilarious, right? More seriously, this is also how
the :class:`feed2exec.plugins.html2text` filter works, which is
enabled by default and helps the email output plugin do its job by
turning HTML into text. At this point, the only limit is your
knowledge of Python programming and your imagination!

Output plugins
~~~~~~~~~~~~~~

Output plugins are another beast entirely. While they operate with the
same principle than filter plugins (search path and function signature
are similar), they are designed to actually output something for each
new feed item found. This can be anything: a file, email, HTTP
request, whatever. If there is a commandline tool that does what you
need, it is probably simpler to just call the ``exec`` plugin and
there are numerous examples of this in the sample configuration
file. For more complex things, however, it may be easier to actually
write this as a Python.

Basic arguments
+++++++++++++++

For our example, we'll write an archival plugin which writes each new
entry to a file hierarchy. First, we start with the same simple
function signature as filters, except we name it output::

  def output(*args, feed=None, item=None, **kwargs):
      pass

This is the equivalent of the ``null`` plugin and basically outputs
nothing at all. To archive the feed items, we'll need to look at the
`link
<https://pythonhosted.org/feedparser/reference-entry-link.html>`_
element feedparser gives us. Let's see what that looks like for the
NASA feed::

  def output(*args, feed=None, item=None, **kwargs):
      # only operate on items that actually have a link
      if item.get('link'):
          print(item.get('link', ''))
      else:
          logging.info('no link for feed item %s, not archiving', item.get('title'))

.. note:: Note that we try to make plugins silent in general. You can
          use :func:`logging.info` to have things show up in
          ``--verbose`` and :func:`logging.debug` for ``--debug`` but
          by default, your plugin should be silent unless there's an
          error that requires the user's intervention, in which case
          you should use :func:`logging.warning` for transient errors
          that may be automatically recovered and
          :func:`logging.error` for errors that require user
          intervention. This is to allow users to ignore warnings
          safely.

Note that here we first check to see if the feed item actually *has* a
link - not all feeds do! After adding the above to our ``trumpery``
plugin and adding it as an output plugin::
  
  [NASA]
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss
  output = trumpery
  filter = trumpery

We can try to see what happens when we call it::

  $ python3 -m feed2exec --verbose fetch --force
  opening local file /home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml
  parsing feed file:///home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml (10355 bytes)
  connecting to database at ./doc/feed2exec.db
  http://www.nasa.gov/press-release/president-trump-welcomes-home-record-breaking-nasa-astronaut-peggy-whitson
  http://www.nasa.gov/press-release/three-international-space-station-crewmates-safely-return-to-earth
  http://www.nasa.gov/press-release/nasa-statement-on-nomination-for-agency-administrator
  http://www.nasa.gov/press-release/nasa-television-to-air-return-of-three-international-space-station-crew-members
  http://www.nasa.gov/press-release/nasa-and-iconic-museum-honor-voyager-spacecraft-40th-anniversary
  http://www.nasa.gov/press-release/nasa-s-johnson-space-center-closes-through-labor-day-for-tropical-storm-harvey
  http://www.nasa.gov/press-release/nasa-cancels-planned-media-availabilities-with-astronauts
  http://www.nasa.gov/press-release/nasa-awards-400000-to-top-teams-at-second-phase-of-3d-printing-competition
  http://www.nasa.gov/press-release/nasa-awards-contract-for-center-protective-services-for-glenn-research-center
  http://www.nasa.gov/press-release/nasa-announces-cassini-end-of-mission-media-activities
  1 feeds processed

Sanitizing contents
+++++++++++++++++++

Good. Those are the URLs we want to save to disk. Let's start by just
writing those to a file. We will also use a simple `slug` function to
make a filesystem-safe name from the feed title and save those files
in a pre-determined location::

  import logging
  import os.path
  from feed2exec.utils import slug
  
  ARCHIVE_DIR='/run/user/1000/feed-archives/'
  
  def output(*args, feed=None, item=None, **kwargs):
      # make a safe path from the item name
      path = slug(item.get('title', 'no-name'))
      # put the file in the archive directory
      path = os.path.join(ARCHIVE_DIR, path)
      # only operate on items that actually have a link
      if item.get('link'):
          # tell the user what's going on, if verbose
          # otherwise, we try to stay silent if all goes well
          logging.info('saving feed item %s to %s from %s',
                       item.get('title'), path, item.get('link'))
          # open the file
          with open(path, 'w') as archive:
              # write the response
              archive.write(item.get('link'))
      else:
          logging.info('no link for feed item %s, not archiving', item.get('title'))

Now I know this may look like a `huge step from the previous one
<http://knowyourmeme.com/memes/how-to-draw-an-owl>`_ but I'm sorry, I
couldn't find a simpler second step. :) The output now looks like
this::
  
  $ python3 -m feed2exec --config ./doc/ --verbose fetch --force
  opening local file /home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml
  parsing feed file:///home/anarcat/src/feed2exec/feed2exec/tests/files/breaking_news.xml (10355 bytes)
  connecting to database at ./doc/feed2exec.db
  saving feed item President Drumpf Welcomes Home Record-breaking NASA Astronaut Peggy Whitson to /run/user/1000/president-drumpf-welcomes-home-record-breaking-nasa-astronaut-peggy-whitson from http://www.nasa.gov/press-release/president-trump-welcomes-home-record-breaking-nasa-astronaut-peggy-whitson
  saving feed item Three International Space Station Crewmates Safely Return to Earth to /run/user/1000/three-international-space-station-crewmates-safely-return-to-earth from http://www.nasa.gov/press-release/three-international-space-station-crewmates-safely-return-to-earth
  saving feed item NASA Statement on Nomination for Agency Administrator to /run/user/1000/nasa-statement-on-nomination-for-agency-administrator from http://www.nasa.gov/press-release/nasa-statement-on-nomination-for-agency-administrator
  saving feed item NASA Television to Air Return of Three International Space Station Crew Members to /run/user/1000/nasa-television-to-air-return-of-three-international-space-station-crew-members from http://www.nasa.gov/press-release/nasa-television-to-air-return-of-three-international-space-station-crew-members
  saving feed item NASA and Iconic Museum Honor Voyager Spacecraft 40th Anniversary to /run/user/1000/nasa-and-iconic-museum-honor-voyager-spacecraft-40th-anniversary from http://www.nasa.gov/press-release/nasa-and-iconic-museum-honor-voyager-spacecraft-40th-anniversary
  saving feed item NASA’s Johnson Space Center Closes Through Labor Day for Tropical Storm Harvey to /run/user/1000/nasa-s-johnson-space-center-closes-through-labor-day-for-tropical-storm-harvey from http://www.nasa.gov/press-release/nasa-s-johnson-space-center-closes-through-labor-day-for-tropical-storm-harvey
  saving feed item NASA Cancels Planned Media Availabilities with Astronauts to /run/user/1000/nasa-cancels-planned-media-availabilities-with-astronauts from http://www.nasa.gov/press-release/nasa-cancels-planned-media-availabilities-with-astronauts
  saving feed item NASA Awards $400,000 to Top Teams at Second Phase of 3D-Printing Competition to /run/user/1000/nasa-awards-400-000-to-top-teams-at-second-phase-of-3d-printing-competition from http://www.nasa.gov/press-release/nasa-awards-400000-to-top-teams-at-second-phase-of-3d-printing-competition
  saving feed item NASA Awards Contract for Center Protective Services for Glenn Research Center to /run/user/1000/nasa-awards-contract-for-center-protective-services-for-glenn-research-center from http://www.nasa.gov/press-release/nasa-awards-contract-for-center-protective-services-for-glenn-research-center
  saving feed item NASA Announces Cassini End-of-Mission Media Activities to /run/user/1000/nasa-announces-cassini-end-of-mission-media-activities from http://www.nasa.gov/press-release/nasa-announces-cassini-end-of-mission-media-activities

Sweet! Now it's not really nice to save this in ``/run/user/1000``. I
just chose this directory because it was a safe place to write but
it's not a persistent directory. Best make that configurable, which is
where plugin arguments come in.

User configuration
++++++++++++++++++

You see that ``*args`` parameter? That comes straight from the
configuration file. So you could set the path in the configuration
file, like this::

  [NASA]
  url = https://www.nasa.gov/rss/dyn/breaking_news.rss
  output = trumpery
  args = /srv/archives/nasa/
  filter = trumpery

We also need to modify the plugin to fetch that configuration, like
this::

  def output(*args, feed=None, item=None, **kwargs):
      # make a safe path from the item name
      path = slug(item.get('title', 'no-name'))
      # take the archive dir from the user or use the default
      archive_dir = ' '.join(args) if args else DEFAULT_ARCHIVE_DIR
      # put the file in the archive directory
      path = os.path.join(archive_dir, path)
      # [...]
      # rest of the function unchanged

Making HTTP requests
++++++++++++++++++++

And now obviously, we only saved the link itself, not the link
*content*. For that we need some help from the :mod:`requests`
module, and do something like this::

  # fetch the URL in memory
  result = requests.get(item.get('link'))
  if result.status_code != requests.codes.ok:
      logging.warning('failed to fetch link %s: %s',
                      item.get('link'), result.status_code)
      # make sure we retry next time
      return False
  # open the file
  with open(path, 'w') as archive:
      # write the response
      archive.write(result.text)

This will save the actual link content (``result.text``) to the
file. The important statement here is::

  # fetch the URL in memory
  result = requests.get(item.get('link'))

which fetches the URL in memory and checks for errors. The other
change in the final plugin is simply::

  archive.write(result.text)

which writes the article content instead of the link.

Plugin return values
++++++++++++++++++++

Notice how we ``return False`` here: this makes the plugin system
avoid adding the item to the cache, so it is retried on the next
run. If the plugin returns ``True`` or nothing (``None``), the plugin
is considered to have succeeded and the entry is added to the
cache. That logic is defined in :func:`feed2exec.feeds.parse`.

Catchup
+++++++

A final thing that is missing that is critical in all plugins is
to respect the ``catchup`` setting. It is propagated up from the
commandline or configuration all the way down to plugins, through the
``feed`` parameters. How you handle it varies from plugin to plugin,
but the basic idea is to give feedback (when verbose) of activity when
the plugin is run *but* to not actually *do* anything. In our case, we
simply return success, right before we fetch the URL::

  if feed.get('catchup'):
      return True
  # fetch the URL in memory
  result = requests.get(item.get('link'))

Notice how we still fetch the actual feed content but stop before
doing any permanent operation. That is the spirit of the "catchup"
operation: we not only skip "write" operation, but also any operation
which could slow down the "catchup": fetching stuff over the network
takes time and while it can be considered a "readonly" operation as
far as the local machine is concerned, we are effectively *writing* to
the network so that operation shouldn't occur.

Hopefully that should get you going with most of the plugins you are
thinking of writing!

See also
--------

:manpage:`feed2exec(1)`
