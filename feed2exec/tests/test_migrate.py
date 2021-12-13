#!/usr/bin/python3
# coding: utf-8

"""
test table migrations
"""

# Copyright (C) 2021 Antoine Beaupré <anarcat@debian.org>
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

import logging

from feed2exec.model import FeedContentCacheStorage


class _OldFeedContentCacheStorage(FeedContentCacheStorage):
    """just like the old class, but without the new column

    used to simulate the migration below.

    should not be used outside the test suite, obviously"""
    sql = '''CREATE TABLE IF NOT EXISTS
             content (key, value,
             PRIMARY KEY (key))'''

    def set(self, key, value):
        """old implementation without expires"""
        with self.connection() as con:
            con.execute("INSERT OR REPLACE INTO `%s` (`%s`, `%s`) VALUES (?, ?)"
                        % (self.table_name, self.key_name, self.value_name),
                        (key, value))


def test_migrate_table_expires_01(tmpdir):  # noqa: F811
    """test for https://gitlab.com/anarcat/feed2exec/-/issues/22"""

    db_path = str(tmpdir.join("test.db"))
    logging.info("creating old storage on %s", db_path)
    cache = _OldFeedContentCacheStorage(db_path)
    logging.info("creating an entry without an expiry record")
    cache.set("foo", "bar")
    assert cache.get("foo") == "bar", "sanity check"

    logging.info("loading new storage on %s", db_path)
    cache = FeedContentCacheStorage(db_path)
    # this will, in theory, trigger the exception that will migrate
    # the table to the new schema
    logging.info("this should trigger an exception")
    cache.set("foo", "baz")
    assert cache.get("foo") == "baz", "sanity check"
    assert cache.expiry("foo") is None
    cache.set("foo", "baz", 1)
    assert cache.expiry("foo") == 1
    cache.set("foo", "baz", 3141592)
