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

class Pong:
    def __init__(self):
        hooks.register("Command", self.pong, 0)
        mm.hooktimer(60, self.ping, ())
    
    def unload(self):
        hooks.unregister("Command", self.pong, 0)
        mm.unhooktimer(60, self.ping, ())
        
    def pong(self, cmd):
        if cmd.cmd == "PING":
            cmd.server.sendcmd(None, "PONG", cmd.line, priority=10)
    
    def ping(self):
        for server in servers.getall():
            if server.servername != "console":
                server.sendcmd(None, "PING", server.user.nick)

def __loadmodule__():
    global mod
    mod = Pong()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
