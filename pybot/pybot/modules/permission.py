# Copyright (c) 2000-2001 Gustavo Niemeyer <niemeyer@conectiva.com>
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

from pybot import mm, hooks, options
from pybot.user import User
import re

HELP = [
("""\
I'm able to control what features are available to what users \
trough a permission system. Only administrators can give or take \
permissions. If you're one of them, you can do it with "(give|take) \
perm[ission] <perm> [to|from] [user <user>] [on|at] [this \
channel|channel <channel>] [on|at|to] [this server|server <server>].\
""",),
("""\
If you're an administrator, you may also view which permissions are \
enabled, and to which users, with "(show|list) perm[ission][s] [<perm>]".\
If you don't provide <perm>, you'll get a list of permissions, otherwise \
you'll receive a list of users with this permission enabled.\
""",)]


class Permission:
    def __init__(self, bot):
        self.perm = options.gethard("Permission.perm", {})
        self.gosh = options.gethard("Permission.gosh", [])
        mm.register("hasperm", self.mm_hasperm)
        mm.register("setperm", self.mm_setperm)
        mm.register("unsetperm", self.mm_unsetperm)
        hooks.register("Message", self.message)

        # Matches '(give|take) perm[ission] <perm> [to|from] [user <user>] [on|at] [this channel|channel <channel>] [on|at|to] [this server|server <server>]'
        self.re1 = re.compile("(?P<command>give|take)\s+(?:(?P<perm1>\w+)\s+perm(?:ission)?|perm(?:ission)?\s+(?P<perm2>\w+))(?:\s+to|\s+from)?(?:\s+user\s+(?P<user>\S+))?(?:\s+on|\s+at)?(?:\s+(?P<thischannel>this\s+channel)|\s+channel\s+(?P<channel>\S+))?(?:\s+on|\s+at|\s+to)?(?:\s+(?P<thisserver>this\s+server)|\s+server\s+(?P<server>\S+))?\s*[!.]*$", re.I)

        # Matches '(show|list) perm[ission][s] [<perm>]'
        self.re2 = re.compile("(?:show|list)\s+perm(?:ission)?s?(?:\s+(?P<perm>\w+))?\s*[!.]*$", re.I)

        # Match 'perm[ission][s] [system]'
        mm.register_help(0, "perm(?:ission)?s?(?:\s+system)?", HELP)

    def unload(self):
        mm.unregister("hasperm")
        mm.unregister("setperm")
        mm.unregister("unsetperm")
        hooks.unregister("Message", self.message)
        mm.unregister_help(0, HELP)
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if self.mm_hasperm(0, msg.server.servername, msg.target, msg.user, None):
                    if m.group("thischannel"):
                        found = 1
                        channel = msg.target
                        server = msg.server.servername
                    else:
                        if m.group("channel"):
                            found = 1
                            channel = m.group("channel")
                        else:
                            channel = None
                        if m.group("thisserver"):
                            found = 1
                            server = msg.server.servername
                        elif m.group("server"):
                            server = m.group("server")
                        else:
                            server = None
                    if m.group("user"):
                        userstr = m.group("user")
                        if not re.compile(".+!.+@.+").match(userstr):
                            msg.answer("%:", "Please, provide a user in the format \"<nick>!<username>@<servername>\".")
                            return 0
                        user = User()
                        user.setstring(userstr)
                    else:
                        user = None
                    perm = m.group("perm1") or m.group("perm2")
                    if m.group("command").lower() == "give":
                        self.mm_setperm(0, server, channel, user, perm)
                    else:
                        if not self.mm_unsetperm(0, server, channel,
                                                 user, perm):
                            msg.answer("%:", "No entries like this were found", [".", "!"])
                            return 0
                    msg.answer("%:", ["Done, sir!", "No problems!", "Ok!"])
                else:
                    msg.answer("%:", ["Sorry, you", "Sir, you", "You"], ["can't work with permissions.", "don't have this power."])
                return 0

            m = self.re2.match(msg.line)
            if m:
                if self.mm_hasperm(0, msg.server.servername, msg.target, msg.user, None):
                    perm = m.group("perm")
                    if perm:
                        if not (self.perm.has_key(perm) and self.perm[perm]):
                            msg.answer("%:", "Nobody has this permission", [".", "!"])
                        else:
                            perms = self.perm[perm]
                            permlen = len(self.perm[perm])
                            s = ""
                            for i in range(permlen):
                                tup = perms[i]
                                if tup[2] is not None:
                                    s += tup[2].string
                                if tup[1] is not None:
                                    join = ""
                                    if s:
                                        join = " at "
                                    s = "%s%schannel %s" % (s, join, tup[1])
                                if tup[0] is not None:
                                    join = ""
                                    if s:
                                        join = " on "
                                    s = "%s%sserver %s" % (s, join, tup[0])
                                if i == permlen-1:
                                    s += "."
                                elif i == permlen-2:
                                    s += ", and "
                                else:
                                    s += ", "
                            msg.answer("%:", "This permission is available for the following people:", s)
                    else:
                        if not self.perm:
                            msg.answer("%:", "No given permissions", [".", "!"])
                        else:
                            msg.answer("%:", "The following permissions are available for some users:", ", ".join(self.perm.keys()))
                else:
                    msg.answer("%:", ["Sorry, you", "Sir, you", "You"], ["can't work with permissions.", "don't have this power."])
                return 0
                    
    def mm_hasperm(self, defret, server, channel, user, perm):
        if self.perm.has_key(perm):
            for tup in self.perm[perm]:
                if (tup[0] is None or tup[0] == server) and \
                   (tup[1] is None or tup[1] == channel) and \
                   (tup[2] is None or user.match(tup[2].nick, tup[2].username, tup[2].host)):
                       return 1
        if perm != "admin":
            if not (self.perm.has_key("admin") and self.perm["admin"]):
                return 1
            return self.mm_hasperm(defret, server, channel, user, "admin")
        return 0

    def mm_setperm(self, defret, server, channel, user, perm):
        if not self.perm.has_key(perm):
            self.perm[perm] = [(server,channel,user)]
        else:
            self.perm[perm].append((server,channel,user))

    def mm_unsetperm(self, defret, server, channel, user, perm):
        found = 0
        if self.perm.has_key(perm):
            _perm = self.perm[perm]
            for tup in _perm:
                if (tup[0] is None or tup[0] == server) and \
                   (tup[1] is None or tup[1] == channel) and \
                   (tup[2] is None or user.match(tup[2].nick, tup[2].username, tup[2].host)):
                    _perm.remove(tup)
                    if len(_perm) == 0:
                        del self.perm[perm]
                    found = 1
        return found


def __loadmodule__(bot):
    global permission
    permission = Permission(bot)

def __unloadmodule__(bot):
    global permission
    permission.unload()
    del permission

# vim:ts=4:sw=4:et
