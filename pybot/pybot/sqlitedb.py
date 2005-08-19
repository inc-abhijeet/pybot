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

from pysqlite2 import dbapi2 as sqlite
import fcntl
import time
import re

class SQLiteDB(object):

    def __init__(self, path, _copy=False):
        self._path = path
        self._conn = sqlite.connect(self._path)
        self._lockfile = open(path, "r+")
        self.results = []
        self.changed = False
        self.error = sqlite.DatabaseError
        if not _copy:
            self.table("dict", "name text, value")

    def lock(self):
        fcntl.lockf(self._lockfile.fileno(), fcntl.LOCK_EX)

    def unlock(self):
        fcntl.lockf(self._lockfile.fileno(), fcntl.LOCK_UN)

    def copy(self):
        return SQLiteDB(self._path, _copy=True)

    def close(self):
        self._conn.close()

    def commit(self):
        self._conn.commit()
        self.unlock()

    def rollback(self):
        self._conn.rollback()
        self.unlock()

    def execute(self, *args, **kwargs):
        cursor = self._conn.cursor()
        self.lock()
        try:
            cursor.execute(args[0], args[1:])
            names = {}
            if cursor.description:
                for i, item in enumerate(cursor.description):
                    names[item[0]] = i
            unlock = False
            if cursor.rowcount > 0 and not kwargs.get("dontcommit"):
                self._conn.commit()
                unlock = True
            if cursor.rowcount == -1:
                self.results = [Row(row, names) for row in cursor.fetchall()]
                self.changed = False
                unlock = True
            else:
                self.results = []
                self.changed = bool(cursor.rowcount)
            cursor.close()
            if unlock:
                self.unlock()
        except self.error:
            cursor.close()
            self._conn.rollback()
            self.unlock()
        return self

    def fetchone(self):
        return self.results and self.results.pop(0) or None

    def fetchall(self):
        rows, self.results = self.results, []
        return rows

    def __iter__(self):
        rows, self.results = self.results, []
        return iter(rows)

    def __getitem__(self, name):
        self.execute("select value from dict where name=?", name)
        row = self.fetchone()
        if not row:
            return None
        return row[0]

    def __setitem__(self, name, value):
        self.execute("insert into dict values (?,?)", name, value)

    def __delitem__(self, name):
        self.execute("delete from dict where name=?", name)

    def table(self, name, fields, constraints="",
              triggers=[], beforecreate=[], aftercreate=[]):
        """\
        Besides creating tables when they don't exist, this function
        will ensure that the given table has the given fields in the
        given order, and change the table if not.
        """
        self.lock()
        cursor = self._conn.cursor()
        try:
            # First, drop old triggers, if existent
            cursor.execute("select name from sqlite_master where "
                           "type='trigger' and tbl_name=?", (name,))
            for row in cursor.fetchall():
                cursor.execute("drop trigger %s" % row[0])
            # Now check that the table exist.
            cursor.execute("select sql from sqlite_master "
                           "where type='table' and name=?", (name,))
            row = cursor.fetchone()
            if constraints:
                constraints = ","+constraints
            if not row:
                # No, it doesn't exist yet.
                for sql in beforecreate: cursor.execute(sql)
                cursor.execute("create table %s (%s%s)" %
                               (name, fields, constraints))
                for sql in aftercreate: cursor.execute(sql)
            elif getxform(fields+constraints) != getfields(name, row[0]):
                # It exists, but is invalid. We'll have to fix it.
                cursor.execute("create temporary table temp_table (%s)" % fields)
                oldfieldnames = [getname(x) for x in
                                 getfields(name, row[0]).split(",")]
                newfieldnames = [getname(x) for x in
                                 fields.split(",")]
                copyfields = ",".join([x for x in newfieldnames
                                       if x in oldfieldnames])
                cursor.execute("insert into temp_table (%s) select %s from %s"
                               % (copyfields, copyfields, name))
                cursor.execute("drop table %s" % name)
                for sql in beforecreate: cursor.execute(sql)
                createargs = fields
                if constraints:
                    createargs += constraints
                cursor.execute("create table %s (%s)" % (name, createargs))
                cursor.execute("insert into %s select %s from temp_table"
                               % (name, ",".join(newfieldnames)))
                cursor.execute("drop table temp_table")
                for sql in aftercreate: cursor.execute(sql)
                self.commit()
            # Rebuild the triggers
            for sql in triggers:
                cursor.execute(sql)
        finally:
            cursor.close()
            self.unlock()

class Row(tuple):
    
    def __new__(klass, row, names):
        self = tuple.__new__(klass, row)
        self._names = names
        return self

    def __getitem__(self, key):
        if type(key) is int:
            return tuple.__getitem__(self, key)
        names = self._names
        if key in names:
            return self[names[key]]
        raise KeyError, "Key '%s' not in %s" % (key, names.keys())

    def __getattr__(self, name):
        names = self._names
        if name in names:
            return self[names[name]]
        raise AttributeError, "Attribute '%s' not in %s" % (name, names.keys())

def getxform(fields):
    return ",".join([x.strip() for x in fields.split(",")])

def getfields(name, sql, _re=re.compile(r"\((.*)\)")):
    m = _re.search(sql)
    if not m:
        raise ValueError, "invalid sql in table '%s': %s" % (name, sql)
    return getxform(m.group(1))

def getname(field, _re=re.compile(r"^\s*(\S+).*$")):
    return _re.sub(r"\1", field)

# vim:ts=4:sw=4:et
