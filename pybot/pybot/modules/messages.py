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

from pybot import hooks, mm, db
import string
import time
import re

HELP = """
You may leave a message to another user with "[priv[ate]] message (to|for)
<nick>: <message>". I'll let <nick> know about your message when he joins
or speaks something in one of the channels I'm in. You need the
"messages" permission for that. You may also ask explicitely if there are
messages for you with "[any] message[s]?".
"""

PERM_MESSAGES = """
The "messages" permission allows you to leave messages for other users.
Check "help messages" for more information.
"""

STRIPNICK = re.compile(r"^[\W_]*([^\W_]+)[\W_]*$")

class Messages:
    def __init__(self):
        hooks.register("Message", self.message)
        hooks.register("UserJoined", self.checkmsgs)

        db.table("message", "servername,nickfrom,nickto,timestamp,flags,message")

        # [priv[ate]] message (to|for) <nick>: <message>
        self.re1 = re.compile(r"(?P<private>priv(?:ate)?\s+)?message\s+(?:to|for)\s+(?P<nick>\S+?)\s*:\s+(?P<message>.*)$", re.I)

        # [any] message[s]?
        self.re2 = re.compile(r"(?:any\s+)?messages?\s*\?$", re.I)

        # [leav(e|ing)] message[s]
        mm.register_help("(?:leav(?:e|ing)\s+)?messages?", HELP, "messages")

        mm.register_perm("messages", PERM_MESSAGES)

    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("UserJoined", self.checkmsgs)
        mm.unregister_help(HELP)
        mm.register_perm("messages")

    def checkmsgs(self, server, target, user, asked):
        # XXX: Must check if user is registered and logged!
        nick = STRIPNICK.sub(r"\1", user.nick.lower())
        cursor = db.cursor()
        cursor.execute("select * from message where "
                       "servername=%s and nickto=%s",
                       server.servername, nick)
        for row in cursor.fetchall():
            if "p" in row.flags:
                trgt = nick
            else:
                trgt = target
            if asked:
                server.sendmsg(target, user.nick, "%:",
                               ["Yes!", "Yep!", "I think so!"])
                asked = 0
            server.sendmsg(trgt, user.nick,
                           "%:", "Message from %s:" % row.nickfrom,
                           row.message)
        if cursor.rowcount:
            cursor.execute("delete from message where "
                           "servername=%s and nickto=%s",
                           server.servername, nick)
        if asked:
            server.sendmsg(target, user.nick, "%:",
                           ["No.", "Nope.", "None.", "I don't think so."])
 
    def message(self, msg):
        if msg.forme and self.re2.match(msg.line):
            asked = 1
        else:
            asked = 0

        self.checkmsgs(msg.server, msg.answertarget, msg.user, asked=asked)

        if not msg.forme:
            return None

        if asked:
            return 0

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "messages"):
                nick =  m.group("nick")
                priv = m.group("private") != None
                message = m.group("message")
                snick = STRIPNICK.sub(r"\1", nick.lower())
                if snick == STRIPNICK.sub(r"\1", msg.server.user.nick):
                    msg.answer("%:", ["I'm not used to talk to myself.",
                                      "I don't talk to myself.",
                                      "Are you nuts?"])
                    return 0
                flags = ""
                if priv:
                    flags += "p"
                cursor = db.cursor()
                cursor.execute("insert into message values "
                               "(%s,%s,%s,%s,%s,%s)",
                               msg.server.servername, msg.user.nick, snick,
                               int(time.time()), flags, message)
                msg.answer("%:", ["I'll let "+nick+" know", "No problems",
                                  "Sure", "Ok"], ["!","."])
            else:
                msg.answer("%:", ["You're not allowed to leave messages",
                                  "You can't leave messages",
                                  "No.. you can't leave messages",
                                  "Unfortunately, you can't do that"],
                                 [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = Messages()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
