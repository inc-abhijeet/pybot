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

from pybot import mm, hooks, options, config, db
from pybot.user import User
from types import StringType
import re

HELP = """
I'm able to control what features are available to what users
trough a permission system. Only administrators can give or take
permissions. If you're one of them, you can do it with "(give|take)
perm[ission] <perm> [to|from] [user <user>] [[and] nick <nick>] [on|at]
[this channel|channel <channel>] [on|at|to] [this server|server <server>]".
When using <nick>, it must be registered and logged to have the
permission.
""","""
If you're an administrator, you may also view which permissions are
enabled, and to which users, with "(show|list) perm[ission][s] [<perm>]".
If you don't provide <perm>, you'll get a list of permissions, otherwise
you'll receive a list of users with this permission enabled.
"""

PERM_ADMIN = """
Users with the "admin" permission have access to all restricted commands,
even those restricted by other permissions. This is equivalent to
include the user in the 'admins' option in the configuration file.
"""

VALIDUSER = re.compile(".+!.+@.+")

class Permission:
    def __init__(self):
        db.table("permission", "permission,servername,target,userstr,nick")
        self.help = options.get("Help.perm", {})
        mm.register("hasperm", self.mm_hasperm)
        mm.register("hasperm_raw", self.mm_hasperm_raw)
        mm.register("setperm", self.mm_setperm)
        mm.register("unsetperm", self.mm_unsetperm)
        hooks.register("Message", self.message)

        self.staticadmins = []
        if config.has_option("permission", "admins"):
            for userhost in config.get("permission", "admins").split():
                pair = userhost.split("@")
                if len(pair) == 2:
                    pair.reverse()
                    self.staticadmins.append(tuple(pair))

        # (give|remove|del|delete|take) perm[ission] <perm> [to|from] [everyone | [user <user>] [[and] nick <nick>] [on|at] [this channel|channel <channel>] [on|at|to] [this server|server <server>]]
        self.re1 = re.compile("(?P<cmd>give|remove|del|delete|take)\s+(?:perm(?:ission)?\s+(?P<perm1>\S+)|(?P<perm2>\S+)\s+perm(?:ission)?)(?:\s+to|\s+from)?(?:(?P<everyone>\s+everyone)|(?:\s+user\s+(?P<user>\S+))?(?:(?:\s+and)?\s+nick\s+(?P<nick>\S+))?(?:\s+on|\s+at)?(?:\s+(?P<thischannel>this\s+channel)|\s+channel\s+(?P<channel>\S+))?(?:\s+on|\s+at|\s+to)?(?:\s+(?P<thisserver>this\s+server)|\s+server\s+(?P<server>\S+))?)?\s*[!.]*$", re.I)

        # (show|list) perm[ission][s] [<perm>]
        self.re2 = re.compile("(?:show|list)\s+perm(?:ission)?s?(?:\s+(?P<perm>\w+))?\s*[!.]*$", re.I)

        # perm[ission][s] [system]
        mm.register_help("perm(?:ission)?s?(?:\s+system)?", HELP,
                         "permissions")

        mm.register_perm("admin", PERM_ADMIN)

    def unload(self):
        mm.unregister("hasperm")
        mm.unregister("hasperm_raw")
        mm.unregister("setperm")
        mm.unregister("unsetperm")
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm("admin")
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                if not filter(bool, m.group("thischannel", "channel",
                                            "thisserver", "server",
                                            "user", "nick", "everyone")):
                    if m.group("cmd") == "give":
                        verb = "receive"
                    else:
                        verb = "lose"
                    msg.answer("%:", "Who should %s this permission?" % verb)
                    return 0
                if m.group("thischannel"):
                    found = 1
                    target = msg.target
                    servername = msg.server.servername
                else:
                    if m.group("channel"):
                        found = 1
                        target = m.group("channel")
                    else:
                        target = None
                    if m.group("thisserver"):
                        found = 1
                        servername = msg.server.servername
                    elif m.group("server"):
                        servername = m.group("server")
                    else:
                        servername = None
                userstr = m.group("user")
                if userstr and not VALIDUSER.match(userstr):
                        msg.answer("%:", "Please, provide a user in the "
                                   "format \"<nick>!<username>@<servername>\".")
                        return 0
                nick = m.group("nick")
                perm = m.group("perm1") or m.group("perm2")
                # Everyone is handled transparently, since all
                # items will be None
                if m.group("cmd").lower() == "give":
                    if not mm.setperm(servername, target, userstr, nick, perm):
                        msg.answer("%:", ["I already have this permission",
                                          "This permission was given before",
                                          "Not necessary"],
                                         [".", "!"])
                        return 0
                else:
                    if not mm.unsetperm(servername, target, userstr, nick, perm):
                        msg.answer("%:", "No entries like this were found",
                                         [".", "!"])
                        return 0
                msg.answer("%:", ["Done", "No problems", "Ok"], [".", "!"])
            else:
                msg.answer("%:", ["Sorry, you", "Oops! You", "You"],
                                 ["can't work with permissions",
                                  "don't have this power"], [".", "!"])
            return 0

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                perm = m.group("perm")
                if perm:
                    help = self.help.get(perm)
                    if help:
                        help = help.replace("\n", " ").strip()
                        msg.answer("%:", help)
                    cursor = db.cursor()
                    cursor.execute("select * from permission where "
                                   "permission=%s", perm)
                    if not cursor.rowcount:
                        msg.answer("%:", "Nobody has this permission",
                                         [".", "!"])
                    else:
                        rows = cursor.fetchall()
                        numrows = len(rows)
                        s = ""
                        for i in range(numrows):
                            row = rows[i]
                            first = 1
                            if row.userstr is not None:
                                s += "user "
                                s += row.userstr
                                first = 0
                            if row.nick is not None:
                                join = ""
                                if not first:
                                    s += " with "
                                s += "%s%snick %s" % (s, join, row.nick)
                                first = 0
                            if row.target is not None:
                                join = ""
                                if not first:
                                    join = " at "
                                s = "%s%schannel %s" % (s, join, row.target)
                                first = 0
                            if row.servername is not None:
                                join = ""
                                if not first:
                                    join = " on "
                                s = "%s%sserver %s" % (s, join, row.servername)
                                first = 0
                            if first:
                                s += "everyone"
                            if i == numrows-1:
                                s += "."
                            elif i == numrows-2:
                                s += ", and "
                            else:
                                s += ", "
                        msg.answer("%:", "This permission is available "
                                         "for the following people:", s)
                else:
                    allperms = self.help.keys()
                    if not allperms:
                        msg.answer("%:", "No available permissions",
                                         [".", "!"])
                    else:
                        allperms.sort()
                        s = ", ".join(allperms)
                        msg.answer("%:", "With the currently loaded modules, "
                                         "I understand the following "
                                         "permissions: "+s)
                    cursor = db.cursor()
                    cursor.execute("select distinct permission from permission "
                                   "order by permission")
                    if not cursor.rowcount:
                        msg.answer("%:", "There are no users with allowed "
                                         "permissions", [".", "!"])
                    else:
                        givenperms = [x.permission for x in cursor.fetchall()]
                        msg.answer("%:", "The following permissions are "
                                         "available for some people:",
                                         ", ".join(givenperms))
            else:
                msg.answer("%:", ["Sorry, you", "Oops, you", "You"],
                                 ["can't work with permissions",
                                  "don't have this power"], [".", "!"])
            return 0

    def mm_hasperm_raw(self, servername, target, user, perm):
        if servername == "console":
            return 1
        loggednick = mm.loggednick(servername, user)
        if (servername, loggednick) in self.staticadmins:
            return 1
        cursor = db.cursor()
        cursor.execute("select * from permission where "
                       "permission='admin' or permission=%s", perm)
        for row in cursor.fetchall():
            if (not row.servername or row.servername == servername) and \
               (not row.target or row.target == target) and \
               (not row.userstr or user.matchstr(row.userstr)) and \
               (not row.nick or row.nick == loggednick):
                    return 1
        return 0

    def mm_hasperm(self, msg, perm):
        return self.mm_hasperm_raw(msg.server.servername,
                                   msg.target, msg.user, perm)

    def mm_setperm(self, servername, target, userstr, nick, perm):
        if self.mm_unsetperm(servername, target, userstr, nick,
                             perm, check=1):
            return 0
        cursor = db.cursor()
        cursor.execute("insert into permission values (%s,%s,%s,%s,%s)",
                       perm, servername, target, userstr, nick)

    def mm_unsetperm(self, servername, target, userstr, nick, perm, check=0):
        where = ["permission=%s"]
        wargs = [perm]
        if servername:
            where.append("servername=%s")
            wargs.append(servername)
        else:
            where.append("servername isnull")
        if target:
            where.append("target=%s")
            wargs.append(target)
        else:
            where.append("target isnull")
        if userstr:
            where.append("userstr=%s")
            wargs.append(userstr)
        else:
            where.append("userstr isnull")
        if nick:
            where.append("nick=%s")
            wargs.append(nick)
        else:
            where.append("nick isnull")
        wstr = " and ".join(where)
        cursor = db.cursor()
        if not check:
            cursor.execute("delete from permission where "+wstr, *wargs)
        else:
            cursor.execute("select * from permission where "+wstr, *wargs)
        return bool(cursor.rowcount)

def __loadmodule__():
    global mod
    mod = Permission()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
