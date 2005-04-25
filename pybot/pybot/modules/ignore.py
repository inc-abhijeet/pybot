# Copyright (c) 2000-2005 Gustavo Niemeyer <niemeyer@conectiva.com>
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

from pybot.locals import *
from time import time
import re

HELP = """
You can make me ignore and unignore people sending me the message
"[don't] ignore [user <user>] [on|at] [this channel|channel <channel>]
[on|at] [this server|server <server>]. To do that, you must have the
"ignore" permission. You may also give the "neverignore" permission
to the people that should never be ignored, even if matching some
ignore pattern.
"""

PERM_IGNORE = """
This permission allow users to change the ignore settings. For more
information use "help ignore".
"""

PERM_NEVERIGNORE = """
People with the "neverignore" permission will never be ignored by
me, even when they match some active ignore pattern.
"""

class Ignore:
    def __init__(self):
        self.repeat = {}

        db.table("ignore", "servername text, target text, userstr text")
        
        hooks.register("Message", self.message_ignore, 200)
        hooks.register("Message", self.message)

        # [do not|don't] ignore [user <user>] [on|at] [this channel|channel <channel>] [on|at] [this server|server <server>]
        self.re1 = regexp(r"(?P<dont>do not |don't )?ignore (?:user (?P<user>\S+?))?(?:(?:on |at )?(?:(?P<thischannel>this channel)|channel (?P<channel>\S+)))?(?:(?:on |at )?(?:(?P<thisserver>this server)|server (?P<server>\S+?)))?")

        # [un]ignore
        mm.register_help(r"(?:un)?ignore", HELP, "ignore")

        mm.register_perm("ignore", PERM_IGNORE)
        mm.register_perm("neverignore", PERM_NEVERIGNORE)
    
    def unload(self):
        hooks.unregister("Message", self.message_ignore, 200)
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm("ignore")
        mm.unregister_perm("neverignore")

    def message_ignore(self, msg):
        if self.isignored(msg.server.servername, msg.target, msg.user) and \
           not mm.hasperm(msg, "neverignore"):
            return -1

        # Check if message is repeating
        now = time()
        for msgkey in self.repeat.keys():
            if self.repeat[msgkey]+15 < now:
                del self.repeat[msgkey]
        msgkey = (msg.server.servername, msg.server.user.nick,
                  re.sub("[!?,. ]", " ", msg.line.lower()).strip())
        if msgkey in self.repeat:
            return -1
        self.repeat[msgkey] = now

    def message(self, msg):
        if not msg.forme:
            return

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "ignore"):
                userstr = m.group("user")
                if not filter(bool, m.groups()):
                    return
                if m.group("thischannel"):
                    target = msg.target
                    servername = msg.server.servername
                else:
                    target = m.group("channel")
                    if m.group("thisserver"):
                        servername = msg.server.servername
                    else:
                        servername = m.group("server")
                if not m.group("dont"):
                    if self.ignore(servername, target, userstr):
                        msg.answer("%:", ["Done", "Ignored",
                                          "No problems", "Ok"], [".", "!"])
                    else:
                        msg.answer("%:", "I was already ignoring it",
                                         [".", "!"])
                else:
                    if self.dontignore(servername, target, userstr):
                        msg.answer("%:", ["Done", "No problems",
                                          "Ok", "Right now"], [".", "!"])
                    else:
                        msg.answer("%:", "I'm not ignoring it", [".", "!"])
            else:
                msg.answer("%:", ["Sorry, you", "Oops, you", "You"],
                                 ["can't do this", "don't have this power"],
                                 [".", "!"])
            return 0

    def ignore(self, servername, target, userstr):
        existed = self.dontignore(servername, target, userstr, check=1)
        if existed:
            return 0
        db.execute("insert into ignore values (?,?,?)",
                   servername, target, userstr)
        return 1
    
    def dontignore(self, servername, target, userstr, check=0):
        where = []
        wargs = []
        if servername:
            where.append("servername=?")
            wargs.append(servername)
        else:
            where.append("servername isnull")
        if target:
            where.append("target=?")
            wargs.append(target)
        else:
            where.append("target isnull")
        if userstr:
            where.append("userstr=?")
            wargs.append(userstr)
        else:
            where.append("userstr isnull")
        wstr = " and ".join(where)
        if not check:
            db.execute("delete from ignore where "+wstr, *wargs)
        else:
            db.execute("select null from ignore where "+wstr, *wargs)
        return db.changed or db.results
    
    def isignored(self, servername, target, user):
        for row in db.execute("select * from ignore"):
            if (not row.servername or row.servername == servername) and \
               (not row.target or row.target == target) and \
               (not row.userstr or user.matchstr(row.userstr)):
                   return 1

def __loadmodule__():
    global mod
    mod = Ignore()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
