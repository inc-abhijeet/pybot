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

class Permission:
    def __init__(self, bot):
        self.perm = options.gethard("Permission.perm", {})
        self.gosh = options.gethard("Permission.gosh", [])
        mm.register("hasperm", self.mm_hasperm)
        mm.register("setperm", self.mm_setperm)
        mm.register("unsetperm", self.mm_unsetperm)
        hooks.register("Message", self.message)

    def unload(self):
        mm.unregister("hasperm")
        mm.unregister("setperm")
        mm.unregister("unsetperm")
        hooks.unregister("Message", self.message)
    
    def message(self, msg):
        var = []
        if msg.match(var, 6, "%", "give", 0, "~", ["permission", "perm"], "to", [("user", 1, "~"), None], [(["on", "at", None], [(2, "~this", "channel"), ("channel", 3, "^[#&+!][^,^G]+$")]), None], [(["on", "at", "to", None], [(4, "~this", "server"), ("server", 5, "~")]), None], ["!", ".", None]):
            if self.mm_hasperm(0, msg.server.servername, msg.target, msg.user, None):
                if var[1] or var[2] or var[3] or var[4]:
                    if var[2]:
                        channel = msg.target
                        server = msg.server.servername
                    else:
                        if var[3]:
                            channel = var[3]
                        else:
                            channel = None
                        if var[4]:
                            server = msg.server.servername
                        elif var[5]:
                            server = var[5]
                        else:
                            server = None
                    if var[1]:
                        user = User()
                        user.setstring(var[1])
                    else:
                        user = None
                    self.mm_setperm(0, server,channel,user,var[0])
                    msg.answer("%:", ["Done, sir!", "Given, sir!", "No problems!", "Ok!"])
            else:
                msg.answer("%:", ["Sorry, you", "Sir, you", "You"], ["can't work with permissions.", "don't have this power.", "can't give permissions."])
            return 0
        elif msg.match(var, 6, "%", "take", 0, "~", ["permission", "perm"], "from", [("user", 1, "~"), None], [(["on", "at", None], [(2, "~this", "channel"), ("channel", 3, "^[#&+!][^,^G]+$")]), None], [(["on", "at", None], [(4, "~this", "server"), ("server", 5, "~")]), None], ["!", ".", None]):
            if self.mm_hasperm(0, msg.server.servername, msg.target, msg.user, None):
                if var[1] or var[2] or var[3] or var[4]:
                    if var[2]:
                        channel = msg.target
                        server = msg.server.servername
                    else:
                        if var[3]:
                            channel = var[3]
                        else:
                            channel = None
                        if var[4]:
                            server = msg.server.servername
                        elif var[5]:
                            server = var[5]
                        else:
                            server = None
                    if var[1]:
                        user = User()
                        user.setstring(var[1])
                    else:
                        user = None
                    self.mm_unsetperm(0, server,channel,user,var[0])
                    msg.answer("%:", ["Done, sir!", "No problems!", "Ok!", "Right now!", "Right now, sir!"])
            else:
                msg.answer("%:", ["Sorry, you", "Sir, you", "You"], ["can't work with permissions.", "don't have this power.", "can't take permissions."])
            return 0

    def mm_hasperm(self, defret, server, channel, user, perm):
        for _user in self.gosh:
            if user.match(_user.nick, _user.username, _user.host):
                return 1
        if self.perm.has_key(perm):
            for tup in self.perm[perm]:
                if (tup[0] == None or tup[0] == server) and \
                   (tup[1] == None or tup[1] == channel) and \
                   (tup[2] == None or user.match(tup[2].nick, tup[2].username, tup[2].host)):
                       return 1

    def mm_setperm(self, defret, server, channel, user, perm):
        if perm == "gosh":
            self.gosh.append(user)
        else:
            if not self.perm.has_key(perm):
                self.perm[perm] = [(server,channel,user)]
            else:
                self.perm[perm].append((server,channel,user))

    def mm_unsetperm(self, defret, server, channel, user, perm):
        if perm == "gosh":
            for _user in self.gosh:
                if _user.match(user.nick, user.username, user.host):
                    self.gosh.remove(_user)
        elif self.perm.has_key(perm):
            _perm = self.perm[perm]
            for tup in _perm:
                if (tup[0] == None or tup[0] == server) and \
                   (tup[1] == None or tup[1] == channel) and \
                   (tup[2] == None or user.match(tup[2].nick, tup[2].username, tup[2].host)):
                    _perm.remove(tup)
                    if len(_perm) == 0:
                        del self.perm[perm]


def __loadmodule__(bot):
    global permission
    permission = Permission(bot)

def __unloadmodule__(bot):
    global permission
    permission.unload()
    del permission

# vim:ts=4:sw=4:et
