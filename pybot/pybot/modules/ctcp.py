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

from pybot import mm, hook, Message, buildanswer
from types import ListType

class CTCP:
    def __init__(self, bot):
        hook.register("Message", self.message, 80)
        hook.register("Notice", self.notice, 80)
        mm.register("sendctcp", self.mm_sendctcp)
        mm.register("answerctcp", self.mm_answerctcp)
        mm.register("answermsgctcp", self.mm_answermsgctcp)
        mm.register("answernotctcp", self.mm_answernotctcp)
    
    def unload(self):
        hook.unregister("Message", self.message, 80)
        hook.unregister("Notice", self.notice, 80)
        mm.unregister("sendctcp")
        mm.unregister("answerctcp")
        mm.unregister("answermsgctcp")
        mm.unregister("answernotctcp")
    
    def message(self, msg):
        var = []
        if msg.msg[0] and msg.msg[0][0]=="\01":
            msg.ctcpcmd = msg.msg[0][1:]
            msg.msg[-1] = msg.msg[-1][:-1]
            del msg.msg[0]
            del msg.rawmsg[0]
            msg.rawmsg[-1] = msg.rawmsg[-1][:-1]
            hook.call("CTCP", msg)
            return -1
    
    def notice(self, msg):
        var = []
        if msg.msg and msg.msg[0][0]=="\01":
            msg.ctcpcmd = msg.msg[0][1:]
            msg.msg[-1] = msg.msg[-1][:-1]
            del msg.msg[0]
            hook.call("CTCPReply", msg)
            return -1

    def handlectcpout(self, server, line):
        msg = message()
        msg.setline(server, line)
        hook.call("OutCommand", msg)
        msg.ctcpcmd = msg.msg[0][1:]
        msg.msg[-1] = msg.msg[-1][:-1]
        del msg.msg[0]
        msg.rawmsg[-1] = msg.rawmsg[-1][:-1]
        del msg.rawmsg[0]
        msg.user = server.user
        if msg.cmd == "PRIVMSG":
            hook.call("OutCTCP", msg)
        else:
            hook.call("OutCTCPReply", msg)

    def mm_sendctcp(self, defret, server, cmd, ctcpcmd, target, nick, params, out=1):
        if type(params) == ListType:
            line = cmd+" "+target+" :\01"+ctcpcmd+" "+buildanswer(params, target, nick)+"\01"
        else:
            line = cmd+" "+target+" :\01"+ctcpcmd+" "+params+"\01"
        server.sendline(line)
        if out: self.handlectcpout(server,line)

    def mm_answerctcp(self, defret, msg, cmd, ctcpcmd, params, outhooks=1):
        if msg.direct:
            target = msg.user.nick
        else:
            target = msg.target
        if type(params) == ListType:
            line = cmd+" "+target+" :\01"+ctcpcmd+" "+buildanswer(params, target, msg.user.nick)+"\01"
        else:
            line = cmd+" "+target+" :\01"+ctcpcmd+" "+params+"\01"
        msg.server.sendline(line)
        if out: self.handlectcpout(msg.server,line)
        
    def mm_answermsgctcp(self, defret, msg, ctcpcmd, params, outhooks=1):
        self.mm_answerctcp(msg, "PRIVMSG", ctcpcmd, params, outhooks)

    def mm_answernotctcp(self, defret, msg, ctcpcmd, params, outhooks=1):
        self.mm_answerctcp(msg, "NOTICE", ctcpcmd, params, outhooks)


def __loadmodule__(bot):
    global ctcp
    ctcp = CTCP(bot)

def __unloadmodule__(bot):
    global ctcp
    ctcp.unload()
    del ctcp

# vim:ts=4:sw=4:et
