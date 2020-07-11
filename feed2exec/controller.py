#!/usr/bin/python3
# coding: utf-8

'''fast feed parser that offloads tasks to plugins and commands'''
# Copyright (C) 2016-2019 Antoine Beaupré <anarcat@debian.org>
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


from datetime import datetime
try:
    from lxml import etree
except ImportError:  # pragma: nocover
    import xml.etree.ElementTree as etree
import logging
import multiprocessing
import os
import os.path

import feed2exec
import feed2exec.plugins as plugins
import feed2exec.utils as utils
from feed2exec.model import Feed, FeedConfStorage, FeedContentCacheStorage, FeedItemCacheStorage
import feedparser
import requests
import requests_file
try:
    import cachecontrol
except ImportError:
    cachecontrol = None

try:
    import dateparser
except ImportError:
    dateparser = False


class FeedManager(object):
    """a feed manager fetches and stores feeds.

    this is a "controller" in a "model-view-controller" pattern. it
    derives the "model" (:class:`feed2exec.model.FeedConfStorage`) for
    simplicity's sake, and there is no real "view" (except maybe
    `__main__`).

    on intialization, a new :class:`requests.Session` object is
    created to be used across all requests. it is passed to plugins
    during dispatch as a `session` parameter so it can be reused.
    """

    def __init__(self, conf_path, db_path, pattern=None, session=None):
        self.conf_path = conf_path
        self.db_path = db_path
        self.conf_storage = FeedConfStorage(self.conf_path, pattern=pattern)
        if dateparser:
            def dateparser_tuple_parser(string):
                if string.endswith('-0000'):
                    # workaround bug https://github.com/scrapinghub/dateparser/issues/548
                    # replace the last '-0000' with '+0000' by reversing the string twice
                    string = string[::-1].replace('-0000'[::-1], '+0000'[::-1], 1)[::-1]
                return dateparser.parse(string).utctimetuple()
            feedparser.registerDateHandler(dateparser_tuple_parser)

        self._session = session or requests.Session()
        self.sessionConfig()

    def __repr__(self):
        return 'FeedManager(%s, %s, %s)' % (self.conf_path, self.db_path, self.pattern)

    def sessionConfig(self):
        """our custom session configuration

        we change the user agent and set the file:// hanlder. extra
        configuration may be performed in the future and will override
        your changes.

        this can be used to configure sessions used externally, for
        example by plugins.
        """
        self._session.headers.update({'User-Agent': '%s/%s'
                                      % (feed2exec.__prog__,
                                         feed2exec.__version__)})
        self._session.mount('file://', requests_file.FileAdapter())
        if self.db_path is not None and cachecontrol is not None:
            cache_adapter = cachecontrol.CacheControlAdapter(cache=FeedContentCacheStorage(self.db_path))
            # assume we mount over http and https all at once so check
            # only the latter
            adapter = self._session.adapters.get('https://', None)
            if hasattr(adapter, 'old_adapters'):
                # looks like a betamax session was setup, hook ourselves behind it
                #
                # XXX: this doesn't actually work, as betamax will
                # never pass the query to the cache. this is
                # backwards, but there's no other way. see
                # https://github.com/ionrock/cachecontrol/issues/212
                logging.debug('appending cache adapter (%r) to existing betamax adapter (%r)', cache_adapter, adapter)
                adapter.old_adapters['http://'] = cache_adapter
                adapter.old_adapters['https://'] = cache_adapter
            else:
                logging.debug('mounting cache adapter (%r)', cache_adapter)
                # override existing adapters to use the cache adapter instead
                self._session.mount('http://', cache_adapter)
                self._session.mount('https://', cache_adapter)

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
        self._session = value
        self.sessionConfig()

    @property
    def pattern(self):
        return self.conf_storage.pattern

    @pattern.setter
    def pattern(self, val):
        self.conf_storage.pattern = val

    def fetch(self, parallel=False, force=False, catchup=False):
        """main entry point for the feed fetch routines.

        this iterates through all feeds configured in the linked
        :class:`feed2exec.model.FeedConfStorage` that match the given
        ``pattern``, fetches the feeds and dispatches the parsing,
        which in turn dispatches the plugins.

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
            body = self.fetch_one(feed)
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
                data = feed.parse(body)
                if data:
                    self.dispatch(feed, data, None, force)
        if parallel:
            for feed, result in data_results:
                data = result.get()
                if data:
                    self.dispatch(feed, data, lock, force)
            pool.close()
            pool.join()
        logging.info('%d feeds processed', i+1)

    def fetch_one(self, feed):
        """fetch the feed content and return the body, in binary

        This will call :func:`logging.warning` for exceptions
        :class:`requests.exceptions.Timeout` and
        :class:`requests.exceptions.ConnectionError` as they are
        transient errors and the user may want to ignore those.

        Other exceptions raised from :mod:`requests.exceptions` (like
        TooManyRedirects or HTTPError but basically any other exception)
        may be a configuration error or a more permanent failure so will
        be signaled with :func:`logging.error`.

        this will return the body on success or None on failure and cached entries
        """
        if feed.get('pause'):
            logging.info('feed %s is paused, skipping', feed['name'])
            return None
        logging.info('fetching feed %s', feed['url'])
        try:
            resp = self.session.get(feed['url'])
            if getattr(resp, 'from_cache', False):
                return None
            body = resp.content
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError) as e:
            # XXX: we should count those and warn after a few
            # occurrences
            logging.warning('timeout while fetching feed %s at %s: %s',
                            feed['name'], feed['url'], e)
            return None
        except requests.exceptions.RequestException as e:
            logging.error('exception while fetching feed %s at %s: %s',
                          feed['name'], feed['url'], e)
            return None
        return body

    def dispatch(self, feed, data, lock=None, force=False):
        '''process parsed entries and execute plugins

        This handles locking, caching, and filter and output
        plugins.

        This calls the plugins configured in the ``feed`` (using
        :func:`feed2exec.plugins.output` and
        :func:`feed2exec.plugins.filter`). It also updates the cache
        with the found items if the ``output`` plugin succeeds
        (returns True) and if the ``filter`` plugin doesn't set the
        ``skip`` element in the feed item.

        :param object lock: a :class:`multiprocessing.Lock` object
                            previously initialized. if None, the global
                            `LOCK` variable will be used: this is used in
                            the test suite to avoid having to pass locks
                            all the way through the API. this lock is in
                            turn passed to plugin calls.

        :param bool force: force plugin execution even if entry was
                           already seen. passed to
                           :class:`feed2exec.feeds.parse` as is

        '''
        logging.debug('dispatching plugins for items parsed from %s', feed['name'])
        cache = FeedItemCacheStorage(self.db_path, feed=feed['name'])
        for item in data['entries']:
            feed.normalize(item=item)
            plugins.filter(feed=feed, item=item, session=self.session, lock=lock)
            if item.get('skip'):
                logging.info('item %s of feed %s filtered out',
                             item.get('title'), feed.get('name'))
                continue
            guid = item['id']
            if not force and guid in cache:
                logging.debug('item %s already seen', guid)
            else:
                logging.debug('new item %s <%s>', guid, item['link'])
                if plugins.output(feed, item, session=self.session, lock=lock) is not False and not force:  # noqa
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
