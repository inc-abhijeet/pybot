# Copyright (c) 2000-2002 Gustavo Niemeyer <niemeyer@conectiva.com>
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

from pybot import config, options, hooks, mm, servers, db
from pybot.user import User
import time
import re
import os

HELP_SEEN = [
("""\
You may check when was the last time I've seen somebody with \
"[have you] seen <nick>". I'll also let you know what was the \
last message the user wrote.\
""",)]

HELP_SEARCH = [
("""\
You may search the log files with "[show|search] (log[s]|message[s]) \
[with] /<regexp>/'. You must have the "logsearch" permission for \
this to work.\
""",)]

class LogMsg:
    def __init__(self, data):
        self.time = int(data.timestamp)
        self.servername = data.servername
        self.type = data.type
        self.src = data.src
        self.dest = data.dest
        self.line = data.line
        
    def __str__(self):
        src = User()
        src.setstring(self.src)
        if self.type == "MESSAGE":
            s = "<%s> %s" % (src.nick, self.line)
        elif self.type == "ACTION":
            s = "* %s %s" % (src.nick, self.line)
        else:
            s = ""
        return s

    def timestr(self):
        msg = time.localtime(self.time)
        now = time.localtime()
        if msg[:3] == now[:3]:
            s = "today at %d:%d" % msg[3:5]
        else:
            s = "on %d-%d-%d at %d:%d" % msg[:5]
        return s
 
STRIPNICK = re.compile(r"^[\W_]*([^\W_]+)[\W_]*$")

class Log:
    def __init__(self):
        self.create_database()

    def create_database(self):
        cursor = db.cursor()
        try:
            cursor.execute("create table log "
                           "(timestamp, servername, type,"
                           " nick, src, dest, line)")
        except db.error:
            pass

    def xformnick(self, nick):
        return STRIPNICK.sub(r"\1", nick.lower())

    def append(self, servername, type, nick, src, dest, line):
        nick = self.xformnick(nick)
        cursor = db.cursor()
        values = (int(time.time()), servername, type, nick, src, dest, line)
        places = ','.join(['%s']*len(values))
        cursor.execute("insert into log values (%s)" % places, values)

    def seen(self, nick):
        nick = self.xformnick(nick)
        cursor = db.cursor()
        cursor.execute("select * from log where nick=%s and src != '' "
                       "and dest != '' order by timestamp desc limit 1",
                       (nick,))
        row = cursor.fetchone()
        if row:
            return LogMsg(row)
        return None

    def search(self, regexp, max, searchline):
        p = re.compile(regexp, re.I)
        l = []
        cursor = db.cursor()
        cursor.execute("select * from log where src != '' and dest != '' "
                       "order by timestamp desc")
        row = cursor.fetchone()
        while row:
            if p.search(row.line):
                l.append(LogMsg(row))
            if len(l) > max+1:
                l.pop(0)
            row = cursor.fetchone()
        if l and l[-1].line == searchline:
            l.pop()
        elif len(l) > max:
            l.pop(0)
        return l

class LogModule:
    def __init__(self):
        self.log = Log()
        
        hooks.register("Message", self.message)
        hooks.register("Message", self.log_message, 150)
        hooks.register("CTCP", self.log_ctcp, 150)
        hooks.register("OutMessage", self.log_outmessage, 150)
        hooks.register("OutCTCP", self.log_outctcp, 150)

        # [have you] seen <nick> [!?]
        self.re1 = re.compile(r"(?:have\s+you\s+)?seen\s+(?P<nick>[^\s!?]+)\s*[!?]*$", re.I)

        # [show|search] (log[s]|message[s]) [with] /<regexp>/[.!]
        self.re2 = re.compile("(?:show\s+|search\s+)?(?:log|message)s?\s+(?:with\s+|search\s+)?/(?P<regexp>.*)/\s*[.!?]*$", re.I)

        # seen
        mm.register_help(0, "seen", HELP_SEEN, "seen")

        # log|(search|show) (log[s]|message[s])
        mm.register_help(0, "log|(?:search|show)\s+(?:log|message)s?",
                         HELP_SEARCH, "log")
        
    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("Message", self.log_message, 150)
        hooks.unregister("CTCP", self.log_ctcp, 150)
        hooks.unregister("OutMessage", self.log_outmessage, 150)
        hooks.unregister("OutCTCP", self.log_outctcp, 150)

        mm.unregister_help(0, HELP_SEEN)
        mm.unregister_help(0, HELP_SEARCH)
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                nick = m.group("nick")
                logmsg = self.log.seen(nick)
                if not logmsg:
                    msg.answer("%:", "Sorry, I haven't seen %s for a while..." % nick)
                else:
                    msg.answer("%:", "I have seen %s %s, with the following message:" % (nick, logmsg.timestr()))
                    msg.answer(str(logmsg))
                return 0
            m = self.re2.match(msg.line)
            if m:
                if mm.hasperm(1, msg.server.servername, msg.target, msg.user, "logsearch"):
                    max = 5
                    logmsgs = self.log.search(m.group("regexp"), max,
                                              msg.rawline)
                    if logmsgs:
                        llen = len(logmsgs)
                        if llen == 1:
                            if max == 1:
                                s = "Here is the last entry found:"
                            else:
                                s = "Here is the only entry found:"
                        elif llen == max:
                            s = "Here are the last %d entries found:" % llen
                        else:
                            s = "Here are the only %d entries found:" % llen
                        msg.answer("%:", s)
                        for logmsg in logmsgs:
                            msg.answer(str(logmsg))
                    else:
                        msg.answer("%:", ["Sorry!", "Oops!"], ["No messages found", "Can't find any message", "No entries found"], [".", "!"])
                else:
                    msg.answer("%:", [("You're not", ["allowed to search logs.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
                return 0
    
    def log_message(self, msg):
        if msg.direct:
            target = ""
        else:
            target = msg.target
        self.log.append(msg.server.servername, "MESSAGE", msg.user.nick,
                        msg.user.string, target, msg.rawline)
    
    def log_ctcp(self, msg):
        if msg.ctcp == "ACTION":
            if msg.direct:
                target = ""
            else:
                target = msg.target
            self.log.append(msg.server.servername, "ACTION", msg.user.nick,
                            msg.user.string, target, msg.rawline)

    def log_outmessage(self, msg):
        self.log.append(msg.server.servername, "MESSAGE", "", "",
                        msg.target, msg.rawline)
    
    def log_outctcp(self, msg):
        if msg.ctcp == "ACTION":
            self.log.append(msg.server.servername, "ACTION", "", "",
                            msg.target, msg.rawline)

def __loadmodule__(bot):
    global mod
    mod = LogModule()

def __unloadmodule__(bot):
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
