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


from datetime import datetime
try:
    from lxml import etree
except ImportError:  # pragma: nocover
    import xml.etree.ElementTree as etree
import logging
import multiprocessing
import os
import os.path

import feed2exec.plugins as plugins
import feed2exec.utils as utils
from feed2exec.model import Feed, FeedConfStorage, FeedCacheStorage
import feedparser

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
                if string.endswith('-0000'):
                    # workaround bug https://github.com/scrapinghub/dateparser/issues/548
                    # replace the last '-0000' with '+0000' by reversing the string twice
                    string = string[::-1].replace('-0000'[::-1], '+0000'[::-1], 1)[::-1]
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
