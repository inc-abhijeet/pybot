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

class Ignore:
    def __init__(self, bot):
        self.ignoredata = options.gethard("Ignore.ignore", [])
        hooks.register("Message", self.message_ignore, 200)
        hooks.register("Message", self.message)
    
    def unload(self):
        hooks.unregister("Message", self.message_ignore, 200)
        hooks.unregister("Message", self.message)

    def message_ignore(self, msg):
        if self.isignored(msg.server.servername, msg.target, msg.user) and \
           not mm.hasperm(0, msg.server.servername, msg.target, msg.user, None):
            return -1

    def message(self, msg):
        var = []
        if msg.match(var, 5, "%", "ignore", [("user", 0, "~"), None], [(["on", "at", None], [(1, "~this", "channel"), ("channel", 2, "^[#&+!][^,^G]+$")]), None], [(["on", "at", None], [(3, "~this", "server"), ("server", 4, "~")]), None], ["!", ".", None]):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "ignore"):
                if var[0] or var[1] or var[2] or var[3] or var[4]:
                    if var[1]:
                        channel = msg.target
                        server = msg.server.servername
                    else:
                        channel = var[2]
                        if var[3]:
                            server = msg.server.servername
                        else:
                            server = var[4]
                    if var[0]:
                        user = User()
                        user.setstring(var[0])
                    else:
                        user = None
                    self.ignore(server,channel,user)
                    msg.answer("%:", ["Done!", "Ignored!", "No problems, sir!", "Ok, sir!"])
            else:
                msg.answer("%:", ["Sorry, you", "Sir, you", "You"], ["can't ignore.", "don't have this power."])
            return 0
        if msg.match(var, 5, "%", "don't", "ignore", [("user", 0, "~"), None], [(["on", "at", None], [(1, "~this", "channel"), ("channel", 2, "^[#&+!][^,^G]+$")]), None], [(["on", "at", None], [(3, "~this", "server"), ("server", 4, "~")]), None], ["!", ".", None]):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "ignore"):
                if var[0] or var[1] or var[2] or var[3] or var[4]:
                    if var[1]:
                        channel = msg.target
                        server = msg.server.servername
                    else:
                        channel = var[2]
                        if var[3]:
                            server = msg.server.servername
                        else:
                            server = var[4]
                    if var[0]:
                        user = User()
                        user.setstring(var[0])
                    else:
                        user = None
                    self.dontignore(server,channel,user)
                    msg.answer("%:", ["Done, sir!", "No problems!", "Ok!", "Right now!", "Right now, sir!"])
            else:
                msg.answer("%:", ["Sorry, you", "Sir, you", "You"], "don't have this power.")
            return 0

    def ignore(self, server, channel, user):
        self.ignoredata.append((server,channel,user))
    
    def dontignore(self, server, channel, user):
        for tup in self.ignoredata:
            if (tup[0] == None or tup[0] == server) and \
               (tup[1] == None or tup[1] == channel) and \
               (tup[2] == None or user.match(tup[2].nick, tup[2].username, tup[2].host)):
                   self.ignoredata.remove(tup)
                   return 1
    
    def isignored(self, server, channel, user):
        for tup in self.ignoredata:
            if (tup[0] == None or tup[0] == server) and \
               (tup[1] == None or tup[1] == channel) and \
               (tup[2] == None or user.match(tup[2].nick, tup[2].username, tup[2].host)):
                   return 1

def __loadmodule__(bot):
    global ignore
    ignore = Ignore(bot)

def __unloadmodule__(bot):
    global ignore
    ignore.unload()
    del ignore

# vim:ts=4:sw=4:et
