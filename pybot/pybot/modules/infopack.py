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
After you load some infopack, you must say explicitly which
users/channels and servers will be able to obtain information from
it. To do that give the permission "infopack(<name>)" for these you
want to allow. To show which infopacks are loaded, send me
"show infopacks". You can also ask for help about some specific
infopack with "help infopack <name>".
"""

PERM_INFOPACKADMIN = """
Users with the "infopackadmin" permission can change infopack
settings. Check "help infopack" for more information.
"""

PERM_INFOPACK = """
Users will be able to access information in some infopack if
they have the "infopack(<name>)" permission. Check "help infopack"
for more information.
"""

MAXSEARCHRESULTS = 3

class Info:
    def __init__(self, phrase="", action=0, notice=0, tonick=0):
        self.phrase = phrase
        self.action = action
        self.notice = notice
        self.tonick = tonick

class Infopack:
    def __init__(self, filename):
        self._filename = filename
        self.reset()

    def reset(self):
        self._info = {}
        self._triggers = []
        self._masks = []
        self._defaults = []
        self._help_patterns = []
        self._help_triggers = []
        self._help_text = []

    def help_match(self, line):
        for pattern in self._help_patterns:
            if pattern.match(line):
                return 1
        return 0

    def help_triggers(self):
        return self._help_triggers

    def help_text(self):
        return self._help_text

    def load(self):
        self.reset()
        values = []
        file = open(self._filename)
        for line in file.xreadlines():
            if line and line[0] != "#":
                if line[0] == "K":
                    values = []
                    self._info[line[2:].rstrip().lower()] = \
                            (line[2:].rstrip(), values)
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
                    self._help_text.append(line[2:].rstrip())
                elif line[0] == "h":
                    tokens = line[2:].rstrip().split(":", 1)
                    if tokens[0]:
                        self._help_triggers.append(tokens[1])
                    if tokens[1]:
                        self._help_patterns.append(re.compile(tokens[0]))
                elif line[0] == "D":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    self._defaults.append(value)
        file.close()
    
    def loadcore(self):
        self.reset()
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
                    self._help_text.append(line[2:].rstrip())
                elif line[0] == "h":
                    tokens = line[2:].rstrip().split(":", 1)
                    if tokens[0]:
                        self._help_triggers.append(tokens[0])
                    if tokens[1]:
                        self._help_patterns.append(re.compile(tokens[1]))
                elif line[0] == "D":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    self._defaults.append(value)
                else:
                    break
        file.close()
    
    def unload(self):
        self.reset()
    
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
        for line in file.readlines():
            if line and line[0] != "#":
                if not found:
                    if line[0] == "K":
                        key = line[2:].rstrip()
                        if key.lower() == findkey:
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
        return key, values
    
    def get(self, line):
        for trigger in self._triggers:
            m = trigger.match(line)
            if m:
                key = m.group(1).lower()
                if self._info:
                    try:
                        key, values = self._info[key]
                    except KeyError:
                        values = None
                else:
                    key, values = self.getinfo(key)
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
                    info.phrase = mask % {"key": key, "value": value[1]}
                else:
                    info.phrase = value[1]
                return info

    def _search(self, pattern, key, values, results):
        found = 0
        if pattern.match(key):
            found = 1
            value = random.choice(values)
        else:
            if len(values) > 1:
                random.shuffle(values)
            for value in values:
                if pattern.match(value[1]):
                    found = 1
                    break
        if found:
            mask = random.choice(self._masks)
            phrase = mask % {"key": key, "value": random.choice(values)[1]}
            results.append(phrase)
 
    def search(self, pattern):
        results = []
        if self._info:
            for key, values in self._info.values():
                self._search(pattern, key, values, results)
        else:
            file = open(self._filename)
            values = []
            for line in file.readlines():
                if line and line[0] != "#":
                    if line[0] == "K":
                        if values:
                            self._search(pattern, key, values, results)
                        key = line[2:].rstrip()
                        values = []
                    elif line[0] == "V":
                        value = line[2:].split(":", 1)
                        value[1] = value[1].rstrip()
                        values.append(value)
            if values:
                self._search(pattern, key, values, results)
            file.close()
        return results

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
        
        # [load|reload|unload] infopack <name> [in memory]
        self.re1 = regexp(r"(?P<action>re|un)?load infopack (?P<name>\w+)(?P<inmemory> in memory)?")

        # show infopacks
        self.re2 = regexp(r"show infopacks")

        # search infopack <name> for /<regexp>/
        self.re3 = regexp(r"search infopack (?P<name>\S+) for /(?P<regexp>.*)/")

        # infopack[s]
        mm.register_help("infopacks?", HELP, "infopack")

        # infopack <name>
        mm.register_help("infopack (?P<name>\S+)", self.help_infopack)

        # .+
        mm.register_help("(?P<something>.+)", self.help_match,
                                              self.help_triggers)

        mm.register_perm("infopackadmin", PERM_INFOPACKADMIN)
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_help(self.help_infopack)
        mm.unregister_help(self.help_match)
        mm.unregister_perm("infopackadmin")

    def help_infopack(self, msg, match):
        name = match.group("name")
        try:
            help = self.packs[name].help_text()
        except KeyError:
            msg.answer("%:", "There's no infopack with that name.")
        else:
            if mm.hasperm(msg, "infopack", name):
                for line in help:
                    msg.answer("%:", line)
            else:
                msg.answer("%:", ["You have no permission to use that"
                                  "infopack",
                                  "You can't use that infopack"],
                                 [".", "!"])
        return 1

    def help_match(self, msg, match):
        something = match.group("something")
        allowed = mm.permparams(msg, "infopack")
        found = 0
        for name, pack in self.packs.items():
            if name not in allowed:
                continue
            if pack.help_match(something):
                found = 1
                for line in pack.help_text():
                    msg.answer("%:", line)
        return found

    def help_triggers(self):
        alltriggers = []
        for pack in self.packs.values():
            alltriggers.extend(pack.help_triggers())
        return alltriggers
 
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
                    cursor = db.cursor()
                    if not self.packs.has_key(name):
                        msg.answer("%:", ["Oops!", "Sorry!"],
                                         "This infopack is not loaded",
                                         [".", "!"])
                    else:
                        del self.packs[name]
                        cursor.execute("delete from infopack where name=%s",
                                       name)
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

        m = self.re3.match(msg.line)            
        if m:
            name = m.group("name")
            regexp = m.group("regexp")
            try:
                pack = self.packs[name]
            except KeyError:
                msg.answer("%:", ["Oops!", "Sorry!"],
                                 "This infopack is not loaded",
                                 [".", "!"])
                return 0
            if mm.hasperm(msg, "infopack", name):
                try:
                    pattern = re.compile(regexp, re.I)
                except re.error:
                    msg.answer("%:", "Invalid pattern", [".", "!"])
                    return 0
                results = pack.search(pattern)
                reslen = len(results)
                if not results:
                    msg.answer("%:", ["Pattern not found",
                                      "Couldn't find anything with that pattern",
                                      "Nothing found"], [".", "!"])
                elif reslen > MAXSEARCHRESULTS:
                    msg.answer("%:", ["Found too many entries",
                                      "There are many entries like this",
                                      "There are many matches"],
                                      ", here are the first %d:"%MAXSEARCHRESULTS)
                elif reslen > 1:
                    msg.answer("%:", ["Found %d entries:" % reslen,
                                      "Found %d matches:" % reslen])
                else:
                    msg.answer("%:", ["Found one entry:",
                                      "Found one match:"])
                n = 0
                for result in results:
                    msg.answer("-", result)
                    n += 1
                    if n == MAXSEARCHRESULTS:
                        break
            else:
                msg.answer("%:", ["You're not allowed to search on "
                                  "this infopack",
                                  "You can't search on this infopack"],
                                  [".", "!"])
            return 0

        allowed = mm.permparams(msg, "infopack")
        found = 0
        for name, pack in self.packs.items():
            if name not in allowed:
                continue
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
