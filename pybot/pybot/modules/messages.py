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

from pybot import hooks, options, mm
import string
import time
import re

HELP = [
("""\
You may leave a message to another user with "[priv[ate]] message (to|for) \
<nick>: <message>". I'll let <nick> know about your message when he joins \
or speaks something in one of the channels I'm in.\
""",)]

class Messages:
    def __init__(self, bot):
        hooks.register("Message", self.message)
        hooks.register("UserJoined", self.checkmsgs)
        self.messages = options.gethard("Messages.messages", {})
        self.strip_nick = re.compile(r"^[\W_]*([^\W_]+)[\W_]*$")

        # Match '[priv[ate]] message (to|for) <nick>: <message>'
        self.re1 = re.compile(r"(?P<private>priv(?:ate)?\s+)?message\s+(?:to|for)\s+(?P<nick>\S+?)\s*:\s+(?P<message>.*)$", re.I)

        # Match '[leav(e|ing)] message[s]'
        mm.register_help(0, "(?:leav(?:e|ing)\s+)?messages?", HELP)

    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("UserJoined", self.checkmsgs)

        mm.unregister_help(HELP)

    def checkmsgs(self, server, target, user):
        lowernick = user.nick.lower()
        nicks = [lowernick]
        nicks.append(self.strip_nick.sub(r"\1", lowernick))
        for nick in nicks:
            msgs = self.messages.get((server.servername,nick))
            if msgs:
                for frm, when, priv, what in msgs:
                    if priv:
                        trgt = user.nick
                    else:
                        trgt = target
                    server.sendmsg(trgt, user.nick, "%:", "Message from "+frm+":", what)
                del self.messages[(server.servername,nick)]
        
    def message(self, msg):
        self.checkmsgs(msg.server, msg.target, msg.user)
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                nick = m.group("nick").lower()
                priv = m.group("private") != None
                server = self.messages.setdefault((msg.server.servername, nick), [])
                server.append((msg.user.nick, time.time(), priv, m.group("message")))
                msg.answer("%:", ["I'll let "+nick+" know", "No problems", "Sure", "Ok"], ["!","."])
                return 0

def __loadmodule__(bot):
    global messages
    messages = Messages(bot)

def __unloadmodule__(bot):
    global messages
    messages.unload()
    del messages

# vim:ts=4:sw=4:et
