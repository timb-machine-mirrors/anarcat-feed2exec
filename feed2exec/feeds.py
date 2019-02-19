#!/usr/bin/python3
# coding: utf-8

'''fast feed parser that offloads tasks to plugins and commands'''
# Copyright (C) 2016 Antoine Beaupré <anarcat@debian.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import division, absolute_import
from __future__ import print_function


try:
    import configparser
except ImportError:  # pragma: nocover
    # py2: should never happen as we depend on the newer one in setup.py
    import ConfigParser as configparser
from collections import OrderedDict, namedtuple
from datetime import datetime
try:
    from lxml import etree
except ImportError:  # pragma: nocover
    import xml.etree.ElementTree as etree
import logging
import multiprocessing
import os
import os.path
try:
    import urllib.parse as urlparse
except ImportError:  # pragma: nocover
    # py2
    import urlparse
import warnings


import feed2exec
import feed2exec.plugins as plugins
import feed2exec.utils as utils
import feedparser
import requests
import requests_file
import sqlite3
import xdg.BaseDirectory as xdg_base_dirs

try:
    import dateparser
except ImportError:
    dateparser = False


class FeedManager(object):
    """a feed manager fetches and stores feeds.

    this is a "controller" in a "model-view-controller" pattern. it
    derives the "model" (:class:`feed2exec.feeds.FeedConfStorage`) for
    simplicity's sake, and there is no real "view" (except maybe
    `__main__`).
    """
    def __init__(self, conf_path, db_path, pattern=None):
        self.conf_path = conf_path
        self.db_path = db_path
        self.conf_storage = FeedConfStorage(self.conf_path, pattern=pattern)
        if dateparser:
            def dateparser_tuple_parser(string):
                return dateparser.parse(string).utctimetuple()
            feedparser.registerDateHandler(dateparser_tuple_parser)

    def __repr__(self):
        return 'FeedManager(%s, %s, %s)' % (self.conf_path, self.db_path, self.pattern)

    @property
    def pattern(self):
        return self.conf_storage.pattern

    @pattern.setter
    def pattern(self, val):
        self.conf_storage.pattern = val

    def fetch(self, parallel=False, force=False, catchup=False):
        """main entry point for the feed fetch routines.

        this iterates through all feeds configured in the parent
        :class:`feed2exec.feeds.FeedConfStorage` that match the given
        ``pattern``, fetches the feeds and dispatches the parsing,
        which in turn dispatches the plugins.

        :param str pattern: restrict operations to feeds named
                            ``pattern``. passed to parent
                            :class:`feed2exec.feeds.FeedConfStorage`
                            as is

        :param bool parallel: parse feeds in parallel, using
                              :mod:`multiprocessing`

        :param bool force: force plugin execution even if entry was
                           already seen. passed to
                           :class:`feed2exec.feeds.parse` as is

        :param bool catchup: set the `catchup` flag on the feed, so
                             that output plugins can avoid doing any
                             permanent changes.
        """
        logging.debug('looking for feeds %s in %s', self.pattern, self.conf_storage)
        if parallel:
            lock = multiprocessing.Lock()
            processes = None
            if isinstance(parallel, int):
                processes = parallel

            def init_global_lock(lock):
                """setup a global lock across pool threads

                this is necessary because Lock objects are not
                serializable so we can't pass them as arguments. An
                alternative pattern is to have a `Manager` process and
                use IPC for locking.

                cargo-culted from this `stackoverflow answer
                <https://stackoverflow.com/a/25558333/1174784>`_

                """
                global LOCK
                LOCK = lock

            pool = multiprocessing.Pool(processes=processes,
                                        initializer=init_global_lock,
                                        initargs=(lock,))
        data_results = []
        i = -1
        for i, feed in enumerate(self.conf_storage):
            logging.debug('found feed in DB: %s', dict(feed))
            # XXX: this is dirty. iterator/getters/??? should return
            # the right thing? or will that break an eventual editor?
            # maybe autocommit is a bad idea in the first place..
            feed = Feed(feed['name'], feed)
            body = feed.fetch()
            if body is None:
                continue
            if catchup:
                feed['catchup'] = catchup
            if parallel:
                # if this fails silently, use plain apply() to see errors
                data_results.append((feed, pool.apply_async(feed.parse, (body,))))
            else:
                global LOCK
                LOCK = None
                self.dispatch(feed, feed.parse(body), None, force)
        if parallel:
            for feed, result in data_results:
                self.dispatch(feed, result.get(), lock, force)
            pool.close()
            pool.join()
        logging.info('%d feeds processed', i+1)

    def dispatch(self, feed, data, lock=None, force=False):
        '''process parsed entries and execute plugins

        This handles locking, caching, and filter and output
        plugins.
        '''
        logging.debug('dispatching plugins for items parsed from %s', feed['name'])
        cache = FeedCacheStorage(self.db_path, feed=feed['name'])
        for item in data['entries']:
            feed.normalize(item=item)
            plugins.filter(feed=feed, item=item, lock=lock)
            if item.get('skip'):
                logging.info('item %s of feed %s filtered out',
                             item.get('title'), feed.get('name'))
                continue
            guid = item['id']
            if not force and guid in cache:
                logging.debug('item %s already seen', guid)
            else:
                logging.debug('new item %s <%s>', guid, item['link'])
                if plugins.output(feed, item, lock=lock) is not False and not force:  # noqa
                    if lock:
                        lock.acquire()
                    cache.add(guid)
                    if lock:
                        lock.release()
        return data

    def opml_import(self, opmlfile):
        """import a file stream as an OPML feed in the feed storage"""
        folders = []
        for (event, node) in etree.iterparse(opmlfile, ['start', 'end']):
            if node.tag != 'outline':
                continue
            logging.debug('found OPML entry: %s', node.attrib)
            if event == 'start' and node.attrib.get('xmlUrl'):
                folder = os.path.join(*folders) if folders else None
                title = node.attrib.get('title', utils.slug(node.attrib['xmlUrl']))
                logging.info('importing element %s <%s> in folder %s',
                             title, node.attrib['xmlUrl'], folder)
                if title in self.conf_storage:
                    if folder:
                        title = folder + '/' + title
                        logging.info('feed %s exists, using folder name: %s',
                                     node.attrib['title'], title)
                if title in self.conf_storage:
                    logging.error('feed %s already exists, skipped',
                                  node.attrib['title'])
                else:
                    self.conf_storage.add(title, node.attrib['xmlUrl'], folder=folder)
            elif node.attrib.get('type') == 'folder':
                if event == 'start':
                    logging.debug('found folder %s', node.attrib.get('text'))
                    folders.append(node.attrib.get('text'))
                else:
                    folders.pop()

    def opml_export(self, path):
        xml_tmpl = u'''<opml version="1.0">
      <head>
        <title>{title}</title>
        <dateModified>{date}</dateModified>
      </head>
      <body>
    {body}</body>
    </opml>'''
        outline_tmpl = u'<outline title="{name}" type="rss" xmlUrl="{url}" />'
        body = u''
        for feed in self.conf_storage:
            if feed:
                body += outline_tmpl.format(**feed) + "\n"
        output = xml_tmpl.format(title=u'feed2exec RSS feeds',
                                 date=datetime.now(),
                                 body=body)
        path.write(output.encode('utf-8'))


class Feed(feedparser.FeedParserDict):
    """basic data structure representing a RSS or Atom feed.

    it derives from the base :class:`feedparser.FeedParserDict` but
    forces the element to have a ``name``, which is the unique name
    for that feed in the :class:`feed2exec.feeds.FeedManager`. We also
    add convenience functions to parse (in parallel) and normalize
    feed items.

    on intialization, a new :class:`requests.Session` object is
    created to be used across all requests. therefore, as long as a
    first FeedManager() object was created, FeedManager._session can
    be used by plugins.

    For all intents and purposes, this can be considered like a dict()
    unless otherwise noted.
    """
    locked_keys = ('output', 'args', 'filter', 'filter_args',
                   'folder', 'mailbox', 'url', 'name', 'pause', 'catchup')

    #: class :class:`request.Session` object that can be used by plugins
    #: to make HTTP requests. initialized in __init__() or in test suite
    _session = None

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self['name'] = name

        # reuse class level session
        if Feed._session is None:
            Feed._session = self.session = requests.Session()
        else:
            self._session = Feed._session

    @property
    def session(self):
        """the session property"""
        return self._session

    @session.setter
    def session(self, value):
        """set the session to the given value

        will configure the session appropriately with sessionConfig

        we could also use a @classproperty here, see `this discussion
        <https://stackoverflow.com/a/7864317/1174784>`_
        """
        Feed.sessionConfig(value)
        self._session = value

    @staticmethod
    def sessionConfig(session):
        """our custom session configuration

        we change the user agent and set the file:// hanlder. extra
        configuration may be performed in the future and will override
        your changes.

        this can be used to configure sessions used externally, for
        example by plugins.
        """
        session.headers.update({'User-Agent': '%s/%s'
                                % (feed2exec.__prog__,
                                   feed2exec.__version__)})
        session.mount('file://', requests_file.FileAdapter())

    def normalize(self, item=None):
        """normalize feeds a little more than what feedparser provides.

        we do the following operation:

         1. add more defaults to item dates (`issue #113
            <https://github.com/kurtmckee/feedparser/issues/113>`_)

         2. missing GUID in some feeds (`issue #112
            <https://github.com/kurtmckee/feedparser/issues/112>`_)

         3. link normalization fails on some feeds, particilarly GitHub,
            where feeds are /foo instead of https://github.com/foo.
            unreported for now.
        """

        # 1. add more defaults (issue #113)
        def pick_first_date():
            """find a valid date in item or feed"""
            fields = ('updated_parsed', 'published_parsed', 'created_parsed')
            # first check the item itself, then fallback on the field
            for scope in (item, self):
                # all the fields to inspect
                for field in fields:
                    if scope.get(field, False):
                        logging.debug('picked field %s for item %s: %s',
                                      field, item.get('id'), scope.get(field))
                        return scope.get(field)

        # ignore deprecation warnings from feedparser:
        # https://github.com/kurtmckee/feedparser/issues/151
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            item['updated_parsed'] = pick_first_date()

        if not item.get('updated_parsed'):
            logging.warning('no parseable date found in feed item %s from feed %s, using current time instead',
                            item.get('id'), self.get('url'))
            item['updated_parsed'] = datetime.utcnow().timestamp()

        # 2. add UID if missing (issue #112)
        if not item.get('id'):
            item['id'] = item.get('title')

        # 3. not completely absolute links
        scheme, netloc, *rest = urlparse.urlsplit(item.get('link', ''))
        if not scheme:
            # take missing scheme/host from feed URL
            scheme, netloc, *_ = urlparse.urlsplit(self.get('url', ''))
            item['link'] = urlparse.urlunsplit((scheme, netloc, *rest))

    def parse(self, body):
        """parse the body of the feed

        this parses the given body using :mod:`feedparser` and calls the
        plugins configured in the ``feed`` (using
        :func:`feed2exec.plugins.output` and
        :func:`feed2exec.plugins.filter`). updates the cache with the
        found items if the ``output`` plugin succeeds (returns True) and
        if the ``filter`` plugin doesn't set the ``skip`` element in the
        feed item.

        :todo: this could be moved to a plugin, but then we'd need to take
               out the cache checking logic, which would remove most of
               the code here...

        :param bytes body: the body of the feed, as returned by :func:fetch

        :param dict self: a feed object used to pass to plugins and debugging

        :param object lock: a :class:`multiprocessing.Lock` object
                            previously initialized. if None, the global
                            `LOCK` variable will be used: this is used in
                            the test suite to avoid having to pass locks
                            all the way through the API. this lock is in
                            turn passed to plugin calls.

        :param bool force: force plugin execution even if entry was
                           already seen. passed to
                           :class:`feed2exec.feeds.parse` as is

        :return dict: the parsed data

        """
        logging.info('parsing feed %s (%d bytes)', self['url'], len(body))
        data = feedparser.parse(body)
        # add metadata from the feed without overriding user config
        for (key, val) in data['feed'].items():
            if key not in self and key not in Feed.locked_keys:
                self[key] = val
        # import json
        # logging.debug('parsed structure %s',
        #               json.dumps(data, indent=2, sort_keys=True,
        #                          default=str))
        # massage result for multiprocessing module
        if data['bozo']:
            data['bozo_exception'] = str(data['bozo_exception'])
        return data

    def fetch(self):
        """fetch the feed content and return the body, in binary

        This will call :func:`logging.warning` for exceptions
        :class:`requests.exceptions.Timeout` and
        :class:`requests.exceptions.ConnectionError` as they are
        transient errors and the user may want to ignore those.

        Other exceptions raised from :mod:`requests.exceptions` (like
        TooManyRedirects or HTTPError but basically any other exception)
        may be a configuration error or a more permanent failure so will
        be signaled with :func:`logging.error`.

        this will return the body on success or None on failure
        """
        if self.get('pause'):
            logging.info('feed %s is paused, skipping', self['name'])
            return None
        logging.info('fetching feed %s', self['url'])
        try:
            body = self.session.get(self['url']).content
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            # XXX: we should count those and warn after a few
            # occurrences
            logging.warning('timeout while fetching feed %s at %s: %s',
                            self['name'], self['url'], e)
            return None
        except requests.exceptions.RequestException as e:
            logging.error('exception while fetching feed %s at %s: %s',
                          self['name'], self['url'], e)
            return None
        return body


class FeedConfStorage(configparser.RawConfigParser):
    """Feed configuration stored in a config file.

    This derives from :class:`configparser.RawConfigParser` and uses
    the ``.ini`` file set in the ``path`` member to read and write
    settings.

    Changes are committed immediately, and no locking is performed so
    loading here should be safe but not editing.

    The particular thing about this configuration is that there is an
    iterator that will yield entries matching the ``pattern``
    substring provided in the constructor.
    """

    def __init__(self, path, pattern=None):
        if path is None:
            path = self.guess_path()
        self.path = os.path.expanduser(path)
        self.pattern = pattern
        super(FeedConfStorage,
              self).__init__(dict_type=OrderedDict)
        self.read(self.path)

    def __repr__(self):
        return 'FeedConfStorage(%s, %s)' % (self.path, self.pattern)

    @classmethod
    def guess_path(cls):
        return xdg_base_dirs.load_first_config(feed2exec.__prog__ + '.ini') or \
            os.path.join(xdg_base_dirs.xdg_config_home, feed2exec.__prog__ + '.ini')

    def add(self, name, url, output=None, args=None,
            filter=None, filter_args=None,
            folder=None, mailbox=None):
        """add the designated feed to the configuration

        this is not thread-safe."""
        if self.has_section(name):
            raise AttributeError('key %s already exists' % name)
        d = OrderedDict()
        # when a new element is added here, it must be added to the
        # Feed.locked_keys config to keep parsed feed elements from
        # overriding potentially secure-sensitive settings
        d['url'] = url
        if output is not None:
            d['output'] = output
        if args is not None:
            d['args'] = args
        if filter is not None:
            d['filter'] = filter
        if filter_args is not None:
            d['filter_args'] = filter_args
        if folder is not None:
            d['folder'] = folder
        if mailbox is not None:
            d['mailbox'] = mailbox
        self[name] = d
        self.commit()

    def set(self, section, option, value=None):
        """override parent to make sure we immediately write changes

        not thread-safe
        """
        super(FeedConfStorage, self).set(section, option, value)
        self.commit()

    def remove_option(self, section, option):
        """override parent to make sure we immediately write changes

        not thread-safe
        """
        super(FeedConfStorage, self).remove_option(section, option)
        self.commit()

    def remove(self, name):
        """convenient alias for
        :func:`configparser.RawConfigParser.remove_section`

        not thread-safe
        """
        self.remove_section(name)
        self.commit()

    def commit(self):
        """write the feed configuration

        see :func:`configparser.RawConfigParser.write`"""
        logging.info('saving feed configuration in %s', self.path)
        utils.make_dirs_helper(os.path.dirname(self.path))
        with open(self.path, 'w') as configfile:
            self.write(configfile)

    def __iter__(self):
        """override iterator to allow for pattern matching"""
        for name in self.sections():
            if self.pattern is None or self.pattern in name:
                yield Feed(name=name, **self[name])


class SqliteStorage(object):
    sql = None
    record = None
    conn = None
    cache = {}

    def __init__(self, path):
        self.path = os.path.expanduser(path)
        assert self.path
        utils.make_dirs_helper(os.path.dirname(self.path))
        if self.path not in SqliteStorage.cache:
            logging.info('connecting to database at %s', self.path)
            conn = sqlite3.connect(self.path)
            try:
                conn.set_trace_callback(logging.debug)
            except AttributeError:  # pragma: nocover
                logging.debug('no logging support in sqlite')
            SqliteStorage.cache[self.path] = conn
        self.conn = SqliteStorage.cache[self.path]
        if self.sql:
            self.conn.execute(self.sql)
            self.conn.commit()


class FeedCacheStorage(SqliteStorage):
    sql = '''CREATE TABLE IF NOT EXISTS
             feedcache (name text, guid text,
             PRIMARY KEY (name, guid))'''
    record = namedtuple('record', 'name guid')

    def __init__(self, path, feed=None, guid=None):
        self.feed = feed
        if guid is None:
            self.guid = '%'
        else:
            self.guid = '%' + guid + '%'
        super().__init__(path)

    def __repr__(self):
        return 'FeedCacheStorage("%s", "%s", "%s")' % (self.path, self.feed, self.guid)

    @classmethod
    def guess_path(cls):
        return os.path.join(xdg_base_dirs.xdg_cache_home, 'feed2exec.db')

    def add(self, guid):
        assert self.feed
        self.conn.execute("INSERT INTO feedcache VALUES (?, ?)",
                          (self.feed, guid))
        self.conn.commit()

    def remove(self, guid):
        assert self.feed
        self.conn.execute("DELETE FROM feedcache WHERE guid = ?", (guid,))
        self.conn.commit()

    def __contains__(self, guid):
        if self.feed is None:
            pattern = '%'
        else:
            pattern = self.feed
        cur = self.conn.execute("""SELECT * FROM feedcache
                                WHERE name LIKE ? AND guid=?""",
                                (pattern, guid))
        return cur.fetchone() is not None

    def __iter__(self):
        if self.feed is None:
            pattern = '%'
        else:
            pattern = self.feed
        cur = self.conn.cursor()
        cur.row_factory = sqlite3.Row
        return cur.execute("""SELECT * from feedcache
                              WHERE name LIKE ? AND guid LIKE ?""",
                           (pattern, self.guid))
