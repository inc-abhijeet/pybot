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

class UserData:
    def __init__(self, bot):
        hooks.register("Message", self.message)
        mm.register("getuserdata", self.mm_getuserdata)
        mm.register("getuserdataall", self.mm_getuserdataall)
        mm.register("setuserdata", self.mm_setuserdata)
        self.data = options.gethard("UserData.data", {})
        self.type = options.gethard("UserData.type", {})
        self.type.setdefault("password", "~")
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister("getuserdata")
        mm.unregister("getuserdataall")
        mm.unregister("setuserdata")
    
    def message(self, msg):
        var = []
        for name, matchstr in self.type.items():
            if msg.match(var, 2, "%", ["with", None], [("password", 0, "~"), None], "register", name, 1, matchstr):
                password = self.mm_getuserdata(None, msg.server, msg.user.nick, "password")
                if not password or password == var[0]:
                    self.mm_setuserdata(None, msg.server, msg.user.nick, name, var[1])
                    msg.answer("%:", ["Done", "Registered", "Sure", "No problems"], ["!", "."])
                else:
                    msg.answer("%:", ["Oops...", "Sorry!"], ["Wrong password", "This is not your password"], ["!", "."])
                return 0
            elif msg.match(var, 2, "%", ["with", None], [("password", 0, "~"), None], "unregister", name, ["!", ".", None]):
                password = self.mm_getuserdata(None, msg.server, msg.user.nick, "password")
                if not password or password == var[0]:
                    self.mm_setuserdata(None, msg.server, msg.user.nick, name, None)
                    msg.answer("%:", ["Done", "Unregistered", "Sure", "No problems"], ["!", "."])
                else:
                    msg.answer("%:", ["Oops...", "Sorry!"], ["Wrong password", "This is not your password"], ["!", "."])
                return 0
    
    def mm_getuserdata(self, defret, server, nick, name):
        usr = self.data.get((server.servername, name))
        if usr:
            return usr.get(nick)
    
    def mm_getuserdataall(self, defret, server, name):
        return self.data.get((server.servername, name))

    def mm_setuserdata(self, defret, server, nick, name, value):
        usr = self.data.setdefault((server.servername, name), {})
        if value != None:
            usr[nick] = value
        else:
            del usr[nick]
            if not usr:
                del usr

def __loadmodule__(bot):
    global userdata
    userdata = UserData(bot)

def __unloadmodule__(bot):
    global userdata
    userdata.unload()
    del userdata

# vim:ts=4:sw=4:et
