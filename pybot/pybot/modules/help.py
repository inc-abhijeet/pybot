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

from pybot import hooks, mm, options
from types import ListType, TupleType
import re

HELP = """
You may ask for help using "[show] help [about] <something>".
"""

PERM_HELP = """
I'll only allow users with the "help" permission to ask for help.
"""

class Help:
    def __init__(self):
        self.data = options.get("Help.data", [])
        self.perm = options.get("Help.perm", {})
        mm.register("register_help", self.mm_register_help)
        mm.register("unregister_help", self.mm_unregister_help)
        mm.register("register_perm", self.mm_register_perm)
        mm.register("unregister_perm", self.mm_unregister_perm)
        hooks.register("Message", self.message)
        
        # [show] help [about] <keyword>
        self.re1 = re.compile(r"(?:show\s+)?help(?:\s+about)?(?:\s+(?P<something>.+?))?\s*[.!]*$", re.I)

        self.mm_register_perm("help", PERM_HELP)
        
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister("register_help")
        mm.unregister("unregister_help")
        mm.unregister("register_perm")
        mm.unregister("unregister_perm")
        self.mm_unregister_perm("help")
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "help"):
                something = m.group("something")
                if something:
                    found = 0
                    for pattern, text, triggers in self.data:
                        match = pattern.match(something)
                        if match:
                            found = 1
                            if callable(text):
                                text(msg, match)
                            elif type(text) in (ListType, TupleType):
                                for line in text:
                                    line = line.replace("\n", " ").strip()
                                    msg.answer("%:", line)
                            else:
                                text = text.replace("\n", " ").strip()
                                msg.answer("%:", text)
                else:
                    found = 1
                    msg.answer("%:", HELP.replace("\n", " ").strip())
                    alltriggers = []
                    for pattern, text, triggers in self.data:
                        alltriggers.extend(triggers)
                    if alltriggers:
                        alltriggers.sort()
                        s = "At least the following help topics are known: "
                        s += ", ".join(alltriggers)
                        msg.answer("%:", s)
                if not found:
                    msg.answer("%:", ["No", "Sorry, no",
                                      "Sorry, but there's no"],
                                     "help about that", [".", "!"])
            else:
                msg.answer("%:", ["Sorry, you", "You"],
                                 ["can't", "are not allowed to"],
                                 "ask for help", [".", "!"])
            return 0

    def mm_register_help(self, pattern, text, triggers=None):
        if not triggers:
            triggers = []
        elif type(triggers) is not ListType:
            triggers = [triggers]
        self.data.append((re.compile(pattern, re.I), text, triggers))

    def mm_unregister_help(self, text):
        for i in range(len(self.data)-1,-1,-1):
            if self.data[i][1] == text:
                del self.data[i]

    def mm_register_perm(self, perm, text):
        self.perm[perm] = text

    def mm_unregister_perm(self, perm):
        try:
            del self.perm[perm]
        except KeyError:
            pass

# Make sure it is loaded first to let mm.register_help()
# available to everyone.
__loadlevel__ = 90

def __loadmodule__():
    global help
    help = Help()

def __unloadmodule__():
    global help
    help.unload()
    del help

# vim:ts=4:sw=4:et
