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

from pybot import config, options, hooks, mm, servers
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
You may search the log files with "[show] (log[s]|message[s]) \
[with] /<regexp>/'. You must have the "logsearch" permission for \
this to work.\
""",)]

class LogMsg:
    def __init__(self, time, servername, type, src, dest, line):
        self.time = time
        self.servername = servername
        self.type = type
        self.src = src
        self.dest = dest
        self.line = line

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
            s = "%d-%d-%d at %d:%d" % msg[:5]
        return s
 

class Log:
    def __init__(self):
        self.__logname = config.get("log", "logfile")

    def append(self, servername, type, src, dest, line):
        file = open(self.__logname, "a")
        file.write("%d %s %s %s %s %s\n" %
                   (int(time.time()), servername, type, src, dest, line))
        file.close()

    def seen(self, nick):
        stripnick = re.compile(r"^[\W_]*([^\W_]+)[\W_]*$")
        nick = stripnick.sub(r"\1", nick.lower())
        file = open(self.__logname)
        logmsg = None
        for line in file.xreadlines():
            stime, servername, type, src, dest, line = line.split(" ", 5)
            if src == "-" or dest == "-":
                continue
            user = User()
            user.setstring(src)
            if stripnick.sub(r"\1", user.nick.lower()) == nick:
                logmsg = LogMsg(int(stime), servername, type, src, dest, line)
        file.close()
        return logmsg

    def search(self, regexp, max):
        p = re.compile(regexp, re.I)
        file = open(self.__logname)
        l = []
        for line in file.xreadlines():
            stime, servername, type, src, dest, line = line.split(" ", 5)
            if src == "-" or dest == "-":
                continue
            if p.search(line):
                l.append(LogMsg(int(stime), servername, type, src, dest, line))
            if len(l) > max:
                l.pop(0)
        file.close()
        return l

class LogModule:
    def __init__(self):
        self.log = Log()
        
        hooks.register("Message", self.message)
        hooks.register("Message", self.log_message, 90)
        hooks.register("CTCP", self.log_ctcp, 90)
        hooks.register("OutMessage", self.log_outmessage, 90)
        hooks.register("OutCTCP", self.log_outctcp, 90)

        # Match '[have you] seen <nick> [!?]'
        self.re1 = re.compile(r"(?:have\s+you\s+)?seen\s+(?P<nick>[^\s!?]+)\s*[!?]*$", re.I)

        # Match '[show] (log[s]|message[s]) [with] /<regexp>/[.!]'
        self.re2 = re.compile("(?:show\s+)?(?:log|message)s?\s+(?:with\s+)?/(?P<regexp>.*)/\s*[.!?]*", re.I)

        # Match 'seen'
        mm.register_help(0, "seen", HELP_SEEN)

        # Match '(log|search (log[s]|message[s]))'
        mm.register_help(0, "log|search\s+(?:log|message)s?", HELP_SEARCH)
        
    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("Message", self.log_message, 90)
        hooks.unregister("CTCP", self.log_ctcp, 90)
        hooks.unregister("OutMessage", self.log_outmessage, 90)
        hooks.unregister("OutCTCP", self.log_outctcp, 90)

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
                    logmsgs = self.log.search(m.group("regexp"), max)
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
        target = msg.direct and "-" or msg.target
        self.log.append(msg.server.servername, "MESSAGE", msg.user.string,
                        target, msg.rawline)
    
    def log_ctcp(self, msg):
        if msg.ctcp == "ACTION":
            target = msg.direct and "-" or msg.target
            self.log.append(msg.server.servername, "ACTION", msg.user.string,
                            target, msg.rawline)

    def log_outmessage(self, msg):
        self.log.append(msg.server.servername, "MESSAGE", "-",
                        msg.target, msg.rawline)
    
    def log_outctcp(self, msg):
        if msg.ctcp == "ACTION":
            self.log.append(msg.server.servername, "ACTION", "-",
                            msg.target, msg.rawline)

def __loadmodule__(bot):
    global module
    module = LogModule()

def __unloadmodule__(bot):
    global module
    module.unload()
    del module

# vim:ts=4:sw=4:et
