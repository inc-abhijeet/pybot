# Copyright (c) 2000-2003 Gustavo Niemeyer <niemeyer@conectiva.com>
#
# This file is part of pybot.
# 
# pybot is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# pybot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with pybot; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import pybot
import sqlite
import re

FIELDS = re.compile(r"\((.*)\)")

class SQLiteDB:
    def __init__(self):
        self._path = pybot.config.get("sqlite", "path")
        self._conn = sqlite.connect(self._path)
        self.error = sqlite.DatabaseError
        self.autocommit(1)
        self.table("dict", "name,value")

    def copy(self):
        return SQLiteDB()

    def cursor(self):
        return self._conn.cursor()

    def commit(self):
        return self._conn.commit()

    def autocommit(self, enable):
        self._conn.autocommit = enable

    def table(self, name, fields):
        """\
        Besides creating tables when they don't exist, this function
        will ensure that the given table has the given fields in the
        given order, and change the table if not.
        """
        cursor = self.cursor()
        # Check that the table exist.
        cursor.execute("select * from sqlite_master "
                       "where type='table' and name=%s", name)
        row = cursor.fetchone()
        if not row:
            # No, it doesn't exist yet.
            cursor.execute("create table %s (%s)" % (name, fields))
        elif row.sql.find("(%s)" % fields) == -1:
            # It exist, but is invalid. We'll have to fix it.
            self.autocommit(0)
            cursor.execute("create temporary table temp_table (%s)" % fields)
            m = FIELDS.search(row.sql)
            if not m:
                raise ValueError, "invalid sql in table '%s'" % name
            oldfields = [x.strip() for x in m.group(1).split(",")]
            copyfields = ",".join([x for x in fields.split(",")
                                   if x in oldfields])
            cursor.execute("insert into temp_table (%s) select %s from %s"
                           % (copyfields, copyfields, name))
            cursor.execute("drop table %s" % name)
            cursor.execute("create table %s (%s)" % (name, fields))
            cursor.execute("insert into %s select %s from temp_table"
                           % (name, fields))
            cursor.execute("drop table temp_table")
            self.commit()
            self.autocommit(1)

    def __getitem__(self, name):
        cursor = self.cursor()
        cursor.execute("select value from dict where name=%s", name)
        if not cursor.rowcount:
            return None
        return cursor.fetchone().value

    def __setitem__(self, name, value):
        del self[name]
        cursor = self.cursor()
        cursor.execute("insert into dict values (%s,%s)", name, value)

    def __delitem__(self, name):
        cursor = self.cursor()
        cursor.execute("delete from dict where name=%s", name)

# vim:ts=4:sw=4:et
