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

from pybot import mm, hooks, options, config
from types import ListType, DictType
import os
import string
import cPickle
import re

HELP = """
You can read and write persistent options, if they exist, using
"(read|write) options". To set specific options, you can use
"set option <name> to <value>", and to show or remove options, you
may use "(show|del) option <name>". To work with options you must
be an administrator.
"""

class Options:
    def __init__(self):
        hooks.register("Message", self.message)
        hooks.register("Reboot", self.write, 1000)
        hooks.register("Quit", self.write, 1000)
        self.path = config.get("options", "path")
        self.read()
        self.safe_env = {"__builtins__": {}, "None": None}

        # (read|write) options
        self.re1 = re.compile(r"(?P<cmd>read|write)\s+options\s*[!.]*$", re.I)
        
        # set option <name> to <value>
        self.re2 = re.compile(r"set\s+option\s+(?P<name>\S+)\s+to\s+(?P<value>.+)$", re.I)
 
        # (show|del[ete]|remove) option <name>
        self.re3 = re.compile(r"(?P<cmd>show|del|delete|remove)\s+option\s+(?P<name>\S+)$", re.I)

        # show options
        self.re4 = re.compile(r"show\s+options$", re.I)

        # option[s]
        mm.register_help(r"options?$", HELP, "options")
    
    def unload(self):
        self.write()
        hooks.unregister("Message", self.message)
        hooks.unregister("Reboot", self.write, 1000)
        hooks.unregister("Quit", self.write, 1000)

        mm.unregister_help(HELP)

    def write(self):
        optdict = {}
        optdict.update(options.getdict())
        for key in optdict.keys():
            value, keepalive, reboot = optdict[key]
            if not reboot:
                del optdict[key]
        if optdict:
            file = open(self.path, "w")
            cPickle.dump(optdict, file, 1)
            file.close()
        elif os.path.exists(self.path):
            os.unlink(os.path)
    
    def read(self):
        if os.path.exists(self.path):
            file = open(self.path)
            newdict = cPickle.load(file)
            olddict = options.getdict()
            file.close()
            for key in newdict.keys():
                oldopt = olddict.get(key)
                if oldopt:
                    newopt = newdict[key]
                    oldvalue = oldopt[0]
                    newvalue = newopt[0]
                    if ListType == type(newvalue) == type(oldvalue):
                        oldvalue[:] = newvalue
                        newdict[key][0] = oldvalue
                    elif DictType == type(newvalue) == type(oldvalue):
                        oldvalue.clear()
                        oldvalue.update(newvalue)
                        newdict[key][0] = oldvalue
            options.setdict(newdict)
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                if m.group("cmd") == "write":
                    self.write()
                    msg.answer("%:", ["Done", "Written", "Ok", "Right now"],
                                     [".", "!"])
                else:
                    self.read()
                    msg.answer("%:", ["Done", "Read", "Ok", "Right now"],
                                     [".", "!"])
            else:
                msg.answer("%:", [("You're not",
                                   ["that good",
                                    "allowed to do this"]),
                                  "No", "Nope"])
            return 0

        
        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                value = eval(m.group("value"), self.safe_env)
                options[m.group("name")] = value
                msg.answer("%:", ["Done", "No problems", "Ok", "Right now"],
                                 [".", "!"])
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to set options",
                                    "that good",
                                    "allowed to do this"]), "No", "Nope"],
                                 [".", "!"])
            return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                cmd = m.group("cmd")
                name = m.group("name")
                if m.group("cmd") == "show":
                    if name in options:
                        opt = options[name]
                        msg.answer("%:", ["This option is", "It is"],
                                          "set to", `opt`)
                    else:
                        msg.answer("%:", ["It seems that", "Sorry, but"],
                                          "there's not such option",
                                         [".", "!"])
                else:
                    if name in options:
                        del options[name]
                        msg.answer("%:", ["Done", "Removed",
                                          "No problems", "Ok", "Right now"],
                                         [".", "!"])
                    else:
                        msg.answer("%:", ["It seems that", "Sorry, but"],
                                          "there's not such option",
                                         [".", "!"])
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to work with options",
                                    "that good",
                                    "allowed to do this"]), "No", "Nope"],
                                 [".", "!"])
            return 0

        m = self.re4.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                names = options.keys()
                if names:
                    msg.answer("%:", "The following options are available:",
                                     ", ".join(names))
                else:
                    msg.answer("%:", "No available options",
                                     [".", "!"])
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to work with options",
                                    "that good",
                                    "allowed to do this"]), "No", "Nope"],
                                 [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = Options()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
