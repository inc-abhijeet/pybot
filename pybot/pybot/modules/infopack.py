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

from pybot.locals import *
import random
import re
import os

HELP = """
Infopacks are knowledge packages that you can plug to make me
provide some specific information to all users. To load some
infopack, put it in the infopack directory (check the configuration
file), and use the command "[load|reload|unload] infopack <name>
[in memory]" (the "infopackadmin" permission is needed).
""","""
To show which infopacks are loaded, send me "show infopacks". You
can also ask for help about some specific infopack with "help infopack
<name>".
"""

PERM_INFOPACKADMIN = """
Users with the "infopackadmin" permission can change infopack
settings. Check "help infopack" for more information.
"""

class Info:
    def __init__(self, phrase="", action=0, notice=0, tonick=0):
        self.phrase = phrase
        self.action = action
        self.notice = notice
        self.tonick = tonick

class Infopack:
    def __init__(self, filename):
        self._filename = filename
        self._info = {}
        self._triggers = []
        self._masks = []
        self._defaults = []
        self._help = []

    def help(self):
        return self._help
 
    def load(self):
        self._info = {}
        self._triggers = []
        self._masks = []
        values = []
        file = open(self._filename)
        for line in file.xreadlines():
            if line and line[0] != "#":
                if line[0] == "K":
                    if values != []:
                        values = []
                    self._info[line[2:].rstrip()] = values
                elif line[0] == "V":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    values.append(value)
                elif line[0] == "T":
                    pattern = re.compile(line[2:].rstrip(), re.I)
                    self._triggers.append(pattern)
                elif line[0] == "M":
                    self._masks.append(line[2:].rstrip())
                elif line[0] == "H":
                    self._help.append(line[2:].rstrip())
                elif line[0] == "D":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    self._defaults.append(value)
        file.close()
    
    def loadcore(self):
        self._info = {}
        self._triggers = []
        self._masks = []
        values = []
        file = open(self._filename)
        for line in file.xreadlines():
            if line and line[0] != "#":
                if line[0] == "T":
                    pattern = re.compile(line[2:].rstrip(), re.I)
                    self._triggers.append(pattern)
                elif line[0] == "M":
                    self._masks.append(line[2:].rstrip())
                elif line[0] == "H":
                    self._help.append(line[2:].rstrip())
                elif line[0] == "D":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    self._defaults.append(value)
                else:
                    break
        file.close()
    
    def unload(self):
        self._info = {}
        self._triggers = []
        self._phrases = []
    
    def reload(self):
        hasinfo = self._info != {}
        self.unload()
        if hasinfo:
            self.load()
        else:
            self.loadcore()
    
    def getinfo(self, findkey):
        values = []
        found = 0
        file = open(self._filename)
        for line in file.xreadlines():
            if line and line[0] != "#":
                if not found:
                    if line[0] == "K":
                        key = line[2:].rstrip()
                        if key == findkey:
                            found = 1
                            foundvalue = 0
                else:
                    if line[0] == "V":
                        foundvalue = 1
                        value = line[2:].split(":", 1)
                        value[1] = value[1].rstrip()
                        values.append(value)
                    elif foundvalue:
                        break
        file.close()
        return values
        
    
    def get(self, line):
        for trigger in self._triggers:
            m = trigger.match(line)
            if m:
                key = m.group(1).lower()
                if self._info:
                    values = self._info.get(key)
                else:
                    values = self.getinfo(key)
                if values:
                    value = random.choice(values)
                elif self._defaults:
                    value = random.choice(self._defaults)
                else:
                    break
                flags = value[0]
                info = Info()
                info.action = "a" in flags
                info.notice = "n" in flags
                info.tonick = "t" in flags
                if "m" in flags:
                    mask = random.choice(self._masks)
                    info.phrase = mask%value[1]
                else:
                    info.phrase = value[1]
                return info

class InfopackModule:
    def __init__(self):
        db.table("infopack", "name,flags")
        self.packs = {}
        hooks.register("Message", self.message)

        # Load infopacks
        infopackdir = config.get("infopack", "infopackdir")
        cursor = db.cursor()
        cursor.execute("select * from infopack")
        for row in cursor.fetchall():
            packname = "%s/%s.info" % (infopackdir, row.name)
            if os.path.isfile(packname):
                pack = Infopack(packname)
                self.packs[row.name] = pack
                if "m" in row.flags:
                    pack.load()
                else:
                    pack.loadcore()
        
        # [load|reload|unload] infopack <name> [in memory] [.|!]
        self.re1 = regexp(r"(?P<action>re|un)?load infopack (?P<name>\w+)(?P<inmemory> in memory)?")

        # show infopacks
        self.re2 = regexp(r"show infopacks")

        # infopack[s]
        mm.register_help("infopacks?", HELP, "infopack")

        # infopack <name>
        mm.register_help("infopack (?P<name>\S+)", self.help)

        mm.register_perm("infopackadmin", PERM_INFOPACKADMIN)
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_help(self.help)
        mm.unregister_perm("infopackadmin")

    def help(self, msg, match):
        name = match.group("name")
        try:
            help = self.packs[name].help()
        except KeyError:
            msg.answer("%:", "There's no infopack with that name.")
        else:
            for line in help:
                msg.answer("%:", line)
 
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "infopackadmin"):
                name = m.group("name")
                action = m.group("action")
                infopackdir = config.get("infopack", "infopackdir")
                packname = "%s/%s.info" % (infopackdir, name)
                if not action:
                    # Load infopack
                    cursor = db.cursor()
                    cursor.execute("select * from infopack where "
                                   "name=%s", name)
                    if cursor.rowcount:
                        msg.answer("%:", ["Oops!", "Sorry!"],
                                         "This infopack is already "
                                         "loaded", [".", "!"])
                    else:
                        if os.path.isfile(packname):
                            inmemory = m.group("inmemory")
                            pack = Infopack(packname)
                            self.packs[name] = pack
                            flags = ""
                            if inmemory:
                                flags += "m"
                            cursor.execute("insert into infopack values "
                                           "(%s,%s)", name, flags)
                            if inmemory:
                                pack.load()
                            else:
                                pack.loadcore()
                            msg.answer("%:", ["Loaded", "Done", "Ok"],
                                             [".", "!"])
                        else:
                            msg.answer("%:", ["Infopack not found",
                                              "I can't find this "
                                              "infopack"], [".", "!"])
                elif action == "re":
                    # Reload infopack
                    if not self.packs.has_key(name):
                        msg.answer("%:", ["Oops!", "Sorry!"],
                                         "This infopack is not loaded",
                                         [".", "!"])
                    else:
                        if os.path.isfile(packname):
                            self.packs[name].reload()
                            msg.answer("%:", ["Reloaded", "Done", "Ok"],
                                             [".", "!"])
                        else:
                            msg.answer("%:", "Infopack not found",
                                             "I can't find this infopack",
                                             [".", "!"])
                else:
                    # Unload infopack
                    if not self.packs.has_key(name):
                        msg.answer("%:", ["Oops!", "Sorry!"],
                                         "This infopack is not loaded",
                                         [".", "!"])
                    else:
                        del self.packs[name]
                        msg.answer("%:", ["Unloaded", "Done", "Ok"],
                                         [".", "!"])
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to change infopack options",
                                    "that good",
                                    "allowed to do this"]),
                                  "Nope"], [".", "!"])
            return 0
        
        m = self.re2.match(msg.line)            
        if m:
            s = ", ".join(self.packs.keys())
            if not s:
                msg.answer("%:", "There are no loaded infopacks!")
            else:
                msg.answer("%:", "The following infopacks are loaded:", s)
                msg.answer("%:", "For more information use "
                                 "\"help infopack <name>\".")
            return 0

        found = 0
        for pack in self.packs.values():
            info = pack.get(msg.line)
            if info:
                found = 1
                action = info.action and "ACTION"
                if info.tonick:
                    msg.answer("%:", info.phrase,
                               notice=info.notice, ctcp=action)
                else:
                    msg.answer(info.phrase,
                               notice=info.notice, ctcp=action)
        if found:
            return 0

def __loadmodule__():
    global mod
    mod = InfopackModule()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
