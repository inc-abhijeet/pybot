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

from pybot import config, options, hooks, mm
from random import randrange
import re
import os

class Info:
    def __init__(self, phrase="", action=0, notice=0, tonick=0):
        self.phrase = phrase
        self.action = action
        self.notice = notice
        self.tonick = tonick

class Infopack:
    def __init__(self, filename):
        self.__filename = filename
        self.__info = {}
        self.__triggers = []
        self.__masks = []
        self.__defaults = []
    
    def load(self):
        self.__info = {}
        self.__triggers = []
        self.__masks = []
        values = []
        file = open(self.__filename)
        for line in file.xreadlines():
            if line and line[0] != "#":
                if line[0] == "K":
                    if values != []:
                        values = []
                    self.__info[line[2:].rstrip()] = values
                elif line[0] == "V":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    values.append(value)
                elif line[0] == "T":
                    pattern = re.compile(line[2:].rstrip(), re.I)
                    self.__triggers.append(pattern)
                elif line[0] == "M":
                    self.__masks.append(line[2:].rstrip())
                elif line[0] == "D":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    self.__defaults.append(value)
        file.close()
    
    def loadcore(self):
        self.__info = {}
        self.__triggers = []
        self.__masks = []
        values = []
        file = open(self.__filename)
        for line in file.xreadlines():
            if line and line[0] != "#":
                if line[0] == "T":
                    pattern = re.compile(line[2:].rstrip(), re.I)
                    self.__triggers.append(pattern)
                elif line[0] == "M":
                    self.__masks.append(line[2:].rstrip())
                elif line[0] == "D":
                    value = line[2:].split(":", 1)
                    value[1] = value[1].rstrip()
                    self.__defaults.append(value)
                else:
                    break
        file.close()
    
    def unload(self):
        self.__info = {}
        self.__triggers = []
        self.__phrases = []
    
    def reload(self):
        hasinfo = self.__info != {}
        self.unload()
        if hasinfo:
            self.load()
        else:
            self.loadcore()
    
    def getinfo(self, findkey):
        values = []
        found = 0
        file = open(self.__filename)
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
        for trigger in self.__triggers:
            m = trigger.match(line)
            if m:
                key = m.group(1).lower()
                if self.__info:
                    values = self.__info.get(key)
                else:
                    values = self.getinfo(key)
                if values:
                    value = values[randrange(len(values))]
                elif self.__defaults:
                    value = self.__defaults[randrange(len(self.__defaults))]
                else:
                    break
                flags = value[0]
                info = Info()
                info.action = "a" in flags
                info.notice = "n" in flags
                info.tonick = "t" in flags
                if "m" in flags:
                    mask = self.__masks[randrange(len(self.__masks))]
                    info.phrase = mask%value[1]
                else:
                    info.phrase = value[1]
                return info

class InfopackModule:
    def __init__(self):
        self.loadpacks = options.gethard("Infopack.loadpacks", [])
        self.packs = {}
        hooks.register("Message", self.message)

        # Load infopacks
        for (name, inmemory) in self.loadpacks:
            infopackdir = config.get("infopack", "infopackdir")
            packname = "%s/%s.info" % (infopackdir, name)
            if os.path.isfile(packname):
                pack = Infopack(packname)
                self.packs[name] = pack
                if inmemory:
                    pack.load()
                else:
                    pack.loadcore()
        
        # Match '[load|reload|unload] infopack <name> [in memory] [.|!]'
        self.re1 = re.compile(r"(?P<action>re|un)?load\s+infopack\s+(?P<name>\w+)(?P<inmemory>\s+in\s+memory)?\s*[.!]*$", re.I)

        # Match 'show infopacks'
        self.re2 = re.compile(r"show\s+infopacks\s*[!.]*$", re.I)
    
    def unload(self):
        hooks.unregister("Message", self.message)
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "infopackadmin"):
                    name = m.group("name")
                    action = m.group("action")
                    infopackdir = config.get("infopack", "infopackdir")
                    packname = "%s/%s.info" % (infopackdir, name)
                    if not action:
                        # Load infopack
                        if self.packs.has_key(name):
                            msg.answer("%:", ["Oops!", "Sorry!"], "This infopack is already loaded", [".", "!"])
                        else:
                            if os.path.isfile(packname):
                                inmemory = m.group("inmemory")
                                pack = Infopack(packname)
                                self.packs[name] = pack
                                self.loadpacks.append((name, inmemory))
                                if inmemory:
                                    pack.load()
                                else:
                                    pack.loadcore()
                                msg.answer("%:", ["Loaded", "Done", "Ok"], [".", "!"])
                            else:
                                msg.answer("%:", ["Infopack not found", "I can't find this infopack"], [".", "!"])
                    elif action == "re":
                        # Reload infopack
                        if not self.packs.has_key(name):
                            msg.answer("%:", ["Oops!", "Sorry!"], "This infopack is not loaded", [".", "!"])
                        else:
                            if os.path.isfile(packname):
                                self.packs[name].reload()
                                msg.answer("%:", ["Reloaded", "Done", "Ok"], [".", "!"])
                            else:
                                msg.answer("%:", "Infopack not found", "I can't find this infopack", [".", "!"])
                    else:
                        # Unload infopack
                        if not self.packs.has_key(name):
                            msg.answer("%:", ["Oops!", "Sorry!"], "This infopack is not loaded", [".", "!"])
                        else:
                            del self.packs[name]
                            msg.answer("%:", ["Unloaded", "Done", "Ok"], [".", "!"])
                else:
                    msg.answer("%:", [("You're not", ["allowed to change infopack options.", "that good...", "allowed to do this..."]), "Nope."])
                return 0
            
            m = self.re2.match(msg.line)            
            if m:
                pass
                return 0

            found = 0
            for pack in self.packs.values():
                info = pack.get(msg.line)
                if info:
                    found = 1
                    action = info.action and "ACTION"
                    if info.tonick:
                        msg.answer("%:", info.phrase, notice=info.notice, ctcp=action)
                    else:
                        msg.answer(info.phrase, notice=info.notice, ctcp=action)
            if found:
                return 0
                    
            

def __loadmodule__(bot):
    global infopack
    infopack = InfopackModule()

def __unloadmodule__(bot):
    global infopack
    infopack.unload()
    del infopack

# vim:ts=4:sw=4:et
