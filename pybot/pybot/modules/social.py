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

from pybot.locals import *
from time import time

class Social:
    def __init__(self):
        self.hello = {}
        hooks.register("Message", self.message)
        hooks.register("UnhandledMessage", self.unhandled_message)

        # (re|hi|hello|hallo|olá|ola|hola|wb|welcome|good (morning|afternoon|evening)|bom dia|boa tarde|gutten tag) [there|back|everybody|all|guys|folks|people|pessoal|(a|para) todos|pybot] [!|.]
        self.re1 = regexp(r'(?:re|hi|hello|hallo|olá|ola|hola|wb|welcome back|good (?:morning|afternoon|evening)|bom dia|boa tarde|gutten tag)(?: (?:there|everybody|all|guys|folks|people|pessoal|(à|a|para) todos|(?P<nick>\w+)))?')
        
        # pybot!
        self.re2 = regexp(r'(?P<nick>\w+)', needpunct=1)
        
        # [thank[']s|thank you|thx|tnk[']s]
        self.re3 = regexp(r'(?:thank|thx|tnk)(?:\'?s| you)(?: (?P<nick>\w+))?')
        
        # are you ok?|how are you [doing]?
        self.re4 = regexp(r'(?:are you ok|how are you(?: doing)?)', question=1)
        
        # pybot[?]
        self.re5 = regexp(r'', question=1)
    
        # never mind
        self.re6 = regexp(r'never mind')

        # [very|pretty] (nice|good|great)
        self.re7 = regexp(r'(?:(?:very|pretty) )?(?:nice|good|great)')
        
        # (gay|stupid|fuck|idiot|imbecile|cretin)
        self.re8 = regexp(r'.*(?:gay|stupid|fuck|idiot|imbecile|cretin).*')
        
        # h[e|u|a]h
        self.re9 = regexp(r'h[eua]h')
        
    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("UnhandledMessage", self.unhandled_message)
    
    def message(self, msg):
        usernick = msg.server.user.nick
        m = self.re1.match(msg.line) or self.re2.match(msg.rawline)
        if m and (not m.group("nick") or m.group("nick") == usernick):
            for user in self.hello.keys():
                if self.hello[user]+1800 < time():
                    del self.hello[user]
            user = msg.user.string+msg.server.servername+msg.target
            usertime = self.hello.get(user)
            if not usertime:
                msg.answer([("%:", ["Hi!", "Hello!"]), (["Hi", "Hello"], "/", [".", "!"])])
                self.hello[user] = time()
            elif msg.forme and usertime+300 < time():
                msg.answer([("%:", ["Hi", "Hello"], "again", [".", "!"]), (["Hi", "Hello"], "again", "/", [".", "!"])])
                self.hello[user] = time()
            return 0

        m = self.re3.match(msg.line)
        if m and (msg.forme or m.group("nick") == usernick):
            msg.answer("%:", ["No problems",
                              "You're welcome",
                              "I'm glad to help you",
                              "I'm here for things like this",
                              "Not at all"], ["!", "."])
            return 0
        
        if msg.forme:
            if self.re4.match(msg.line):
                msg.answer("%:", ["I'm", "Everything is"],
                                 ["ok", "fine"], ["!", ", thanks!"])
                return 0
        
            if self.re5.match(msg.line):
                msg.answer([("%:", "Yes?"), ("%:", "Here!"), ("%", "?")])
                return 0
        
            if self.re6.match(msg.line):
                msg.answer("%:", ["No problems", "Ok", "Sure"], [".", "!"])
                return 0

            if self.re7.match(msg.line):
                msg.answer("%:", ["No problems",
                                  "Hey! I'm here for this"],
                                  [".", "!", "..."])
                return 0

            if self.re8.match(msg.line):
                msg.answer("%:", ["Be polite while talking to me!",
                                  "I should talk to your mother!",
                                  "Hey! What's this?",
                                  "I'll pretend to be blind."])
                return 0
            
            if self.re9.match(msg.line):
                msg.answer("%:", ["Heh", "Huh"], ["?", "!?", "!?!?"])
                return 0
    
    def unhandled_message(self, msg):
        msg.answer("%:", ["What are you talking about", "What do you mean", "Can I help you", "Huh", "Sorry", "Pardon"], ["?", "!?", "!?!?"])

def __loadmodule__():
    global mod
    mod = Social()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
