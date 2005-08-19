# -*- encoding: iso-8859-1 -*-
#
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
from time import time
import re

class Social:
    def __init__(self):
        self.hello = {}

        hooks.register("Message", self.message)
        hooks.register("UnhandledMessage", self.unhandled_message)

        # (re|hi|hello|hallo|olá|ola|hola|wb|welcome [back]|greetings|good (morning|afternoon|evening)|bom dia|boa tarde|gutten tag|bonjour) [there|back|everybody|all|guys|folks|people|pessoal|(a|para) todos|pybot] [!|.]
        self.re1 = regexp(r'(?:re|hi|hello|hallo|olá|ola|hola|wb|welcome(?: back)?|greetings|good (?:morning|afternoon|evening)|bom dia|boa tarde|gutten tag|bonjour)(?: (?:there|everybody|all|guys|folks|people|pessoal|(à|a|para) todos|(?P<nick>\w+)))?')
        
        # pybot!
        self.re2 = regexp(r'(?P<nick>\w+)', needpunct=1)
        
        # [thank[']s|thank you|thx|tnk[']s]
        self.re3 = regexp(r'(?:thank|thx|tnk)(?:\'?s| you)(?: (?P<nick>\w+))?')
        
        # are you ok?|how are you [doing]?
        self.re4 = regexp(r'(?:are you ok|how are you(?: doing)?)', question=1)
        
        # pybot[?]
        self.re5 = regexp(r'', question=1)
    
        # (yes|no|yep|great|good|done|whatever|nevermind|good luck|perhaps)
        self.re6 = regexp(r'(?:yes|no|yep|great|good|done|whatever|never ?mind|perhaps)')

        # [very|pretty] (nice|good|great)
        self.re7 = regexp(r'(?:(?:very|pretty) )?(?:nice|good|great)')
        
        # (gay|stupid|fuck|idiot|imbecile|cretin)
        self.re8 = regexp(r'.*(?:gay|stupid|fuck|idiot|imbecile|cretin).*')
        
        # h[e|u|a]h
        self.re9 = regexp(r'h[eua]h')

        # (are you|you are) a (bot|robot|machine|[computer] program|software)?
        self.re10 = regexp(r'(?:are you|you are) a (?:(?:ro)?bot|machine|(?:computer )?program|software)', question=1)

        # !...
        self.re11 = regexp(r'![a-z].*', nopunct=1)

        # :-)|hehehe [:-)]
        self.re12 = regexp(r'(?:[:;8]-?[()bD/]|(?:he)+ [:;8]-?[()bD])', nopunct=1)

        # don't worry ... | worry not ...
        self.re13 = regexp(r'(?:don\'?t worry|worry not).*')

        # do you speak <language> ?
        self.re14 = regexp(r'do you speak \S+', question=1)

        # can I ...
        self.re15 = regexp(r'can I .*', question=1)

        # ((can|could) you|if you (can|could)) ...
        self.re16 = regexp(r'(?:(?:can|could) you|if you (?:can|could)) .*', question=1)

        # are you ...
        self.re17 = regexp(r'are you .*', question=1)

        # (how|when|where|what)['s|'re] ...
        self.re18 = regexp(r'(?:how|when|where|what)(?:\'(?:s|re))? .*', question=1)

        # good luck
        self.re19 = regexp(r'good luck')

        # I don't know ...
        self.re20 = regexp(r'I don\'t know.*')

        # ... bot ...
        self.re21 = regexp(r'.*\bbot\b.*')

        # I (think|thought|belive|wonder if) ...
        self.re22 = regexp(r'I (?:think|thought|belive|wonder if) .*')

    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("UnhandledMessage", self.unhandled_message)

    def message(self, msg):
        usernick = msg.server.user.nick
        m = self.re1.match(msg.line) or self.re2.match(msg.rawline)
        if m and (not m.group("nick") or m.group("nick") == usernick):
            now = time()
            for user in self.hello.keys():
                if self.hello[user]+1800 < now:
                    del self.hello[user]
            user = msg.user.string+msg.server.servername+msg.target
            usertime = self.hello.get(user)
            if not usertime:
                msg.answer([("%:", ["Hi!", "Hello!"]),
                            (["Hi", "Hello"], "/", [".", "!"])])
                self.hello[user] = now
            elif msg.forme and usertime+300 < now:
                msg.answer([("%:", ["Hi", "Hello"], "again", [".", "!"]),
                            (["Hi", "Hello"], "again", "/", [".", "!"])])
                self.hello[user] = now
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
                msg.answer("%:", ["Whatever", "Great", "Ok", "Sure", ":-)"])
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

            if self.re10.match(msg.line):
                msg.answer("%:", [("Of course I'm not", [".", "!", "!!"]),
                                  ("No, I'm not", [".", "!", "!!"]),
                                  ("What are you talking about", ["?", "!?"]),
                                  ":-)", "Hehehe :-)", "Sure"])
                return 0

            if self.re11.match(msg.line):
                msg.answer("%:", ["Why are you talking like !this", "?Yes",
                                  ":-)", "!no", "!funny", "!?"])
                return 0

            if self.re12.match(msg.line):
                msg.answer("%:", [";-)", ":-)", "8-)"])
                return 0

            if self.re13.match(msg.line):
                msg.answer("%:", ["I'm not worried",
                                  "I'm not worried at all",
                                  "I'm calm",
                                  "I'm pretty calm",
                                  "I'm perfectly calm",
                                  "I'm never worried"],
                                  [".", ".."], [";-)", ":-)", None, None])
                return 0

            if self.re14.match(msg.line):
                msg.answer("%:", ["No, I'm sorry", "Nope",
                                  "No", "Not yet"], [".", "..", ":-)"])
                return 0

            if self.re15.match(msg.line):
                msg.answer("%:", ["No", "Nope", "No, you can't"],
                                 ["!", "!!", ".", "..", ":-)", ":-("])
                return 0

            if self.re16.match(msg.line):
                msg.answer("%:", ["No", "Nope", "No, I can't"],
                                 [", sorry", None, None],
                                 [".", "..", ":-)", ":-("])
                return 0

            if self.re17.match(msg.line):
                msg.answer("%:", ["No", "Nope", "No, I'm not"],
                                 [".", "..", ":-)", ":-("])
                return 0

            if self.re18.match(msg.line):
                msg.answer("%:", ["I'm not sure", "I don't know", "No idea",
                                  "Good question", "That's a good question",
                                  "Excellent question"],
                                 [".", "..", ":-("])
                return 0

            if self.re19.match(msg.line):
                msg.answer("%:", ["Thanks", "Thank you", "I don't need luck",
                                  "Luck is always with me"],
                                 [".", "!", ":-)"])
                return 0

            if self.re20.match(msg.line):
                msg.answer("%:", ["If you don't know, I can't help you",
                                  "That's something you should know",
                                  "You'll have to discover on your own",
                                  "Try google", "Google knows it",
                                  "Google knows everything",
                                  "I don't know either"], [".", "!"])
                return 0

            if self.re21.match(msg.line):
                msg.answer("%:", [(["I'm not a bot",
                                    "I'm a human, not a bot"],
                                   [".", "!"]),
                                  (["Have I mentioned that I'm not a bot",
                                    "Bot? What bot", "Bot",
                                    "You think I'm a bot",
                                    "Why do you think I'm a bot"],
                                   ["?", "!?"])])
                return 0

            if self.re22.match(msg.line):
                msg.answer("%:", [(["Might be the case",
                                    "Perhaps",
                                    "Probably",
                                    "I'm not sure"],
                                   [".", "!"]),
                                  (["Why do you think so",
                                    "Why do you beive so",
                                    "Do you think so",
                                    "Do you belive so",
                                    "Do you",
                                    "Are you sure"],
                                   ["?", "!?"])])
                return 0

    def unhandled_message(self, msg):
        msg.answer("%:", ["What are you talking about",
                          "What do you mean",
                          "Can I help you",
                          "Huh", "Sorry", "Pardon"],
                          ["?", "!?", "!?!?"])

def __loadmodule__():
    global mod
    mod = Social()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
