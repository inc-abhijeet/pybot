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
import time
import re
import os

class Message:
    def __init__(self, time=0, nick="", phrase=""):
        self.phrase = phrase
        self.time = time
        self.nick = nick

class Log:
    def __init__(self):
        self.__logname = config.get("log", "logfile")

    def append(self, servername, type, src, dest, line):
        file = open(self.__logname, "a")
        file.write("%d %s %s %s %s %s\n" %
                   (int(time.time()), servername, type, src, dest, line))
        file.close()

class LogModule:
    def __init__(self):
        self.log = Log()
        
        hooks.register("Message", self.message)
        hooks.register("Message", self.log_message, 90)
        hooks.register("CTCP", self.log_ctcp, 90)
        hooks.register("OutMessage", self.log_outmessage, 90)
        hooks.register("OutCTCP", self.log_outctcp, 90)

        # Match '[have you] seen <nick> [!?]'
        self.re1 = re.compile(r"(?:have\s+you\s+)?seen\s+(?P<nick>\w+)\s*[!?]*$", re.I)

        # Match '[show] log [with] /<regexp>/[.!]'
        #self.re2 = re.compile("", re.I)
        
    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("Message", self.log_message, 90)
        hooks.unregister("CTCP", self.log_ctcp, 90)
        hooks.unregister("OutMessage", self.log_outmessage, 90)
        hooks.nuregister("OutCTCP", self.log_outctcp, 90)
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                msg.answer("%:", ["Oops!", "Sorry!"], "Not yet", [".", "!"])
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
