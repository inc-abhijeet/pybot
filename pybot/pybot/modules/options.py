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

from pybot import mm, hooks, options
from types import *
import os
import string
import cPickle

class Options:
    def __init__(self, bot):
        hooks.register("Message", self.message)
        hooks.register("Reboot", self.write, 1000)
        hooks.register("Quit", self.write, 1000)
        self.path = config.get("options", "path")
        self.read()
        self.safe_env = {"__builtins__": {}, "None": None}
    
    def unload(self):
        self.write()
        hooks.unregister("Message", self.message)
        hooks.unregister("Reboot", self.write, 1000)
        hooks.unregister("Quit", self.write, 1000)

    def write(self):
        file = open(self.path, "w")
        cPickle.dump(options.getharddict(), file, 1)
        file.close()
    
    def read(self):
        if os.path.exists(self.path):
            file = open(self.path)
            newoption = cPickle.load(file)
            oldoption = options.getharddict()
            file.close()
            for key in newoption.keys():
                oldopt = oldoption.get(key)
                if oldopt:
                    newopt = newoption[key]
                    if ListType == type(newopt) == type(oldopt):
                        oldopt[:] = newopt
                        newoption[key] = oldopt
                    elif DictType == type(newopt) == type(oldopt):
                        oldopt.clear()
                        oldopt.update(newopt)
                        newoption[key] = oldopt
            options.setharddict(newoption)
    
    def message(self, msg):
        var = []
        if msg.match(var, 0, "%", "write", "options", ["!", ".", None]):
            if mm.hasperm(1, msg.server.servername, msg.target, msg.user, "readopts"):
                self.write()
                msg.answer("%:", ["Done!", "Written, sir!", "Ok!", "Right now!"])
            else:
                msg.answer("%:", [("You're not", ["allowed to write options.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
            return 0
        elif msg.match(var, 0, "%", "read", "options", ["!", ".", None]):
            if mm.hasperm(1, msg.server.servername, msg.target, msg.user, "writeopts"):
                self.read()
                msg.answer("%:", ["Done!", "Read, sir!", "Ok!", "Right now!"])
            else:
                msg.answer("%:", [("You're not", ["allowed to read options.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
            return 0
        elif msg.match(var, 2, "%", "set", "option", 0, "~", "to", 1, "|>"):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, None):
                opt = options.gethard(var[0], None)
                val = eval(string.join(var[1]), self.safe_env)
                if opt != None:
                    if ListType == type(opt) == type(val):
                        opt[:] = val
                    elif DictType == type(opt) == type(val):
                        opt.clear()
                        opt.update(val)
                    else:
                        opt = val
                else:
                    options.sethard(var[0], val)
                msg.answer("%:", ["Done!", "No problems, sir!", "Ok!", "Right now, sir!"])
            else:
                msg.answer("%:", [("You're not", ["allowed to set options.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
            return 0
        elif msg.match(var, 1, "%", ["remove", "del", "delete"], "option", 0, "~", ["!", ".", None]):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, None):
                if options.hashard(var[0]):
                    options.delhard(var[0])
                    msg.answer("%:", ["Done, sir!", "Removed, sir!", "No problems!", "Ok!", "Right now!"])
                else:
                    msg.answer("%:", ["It seems that", "Sorry, but", "Sir,"], "there's not such option.")
            else:
                msg.answer("%:", [("You're not", ["allowed to remove options.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
            return 0
        elif msg.match(var, 1, "%", ["print","show"], "option", 0, "~", ["!", ".", None]):
            if mm.hasperm(1, msg.server.servername, msg.target, msg.user, None):
                if options.hashard(var[0]):
                    opt = options.gethard(var[0], None)
                    msg.answer("%:", ["This option is", "It is"], "set to", `opt`)
                else:
                    msg.answer("%:", ["It seems that", "Sorry, but", "Sir,"], "there's not such option.")
            else:
                msg.answer("%:", [("You're not", ["allowed to print options.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
            return 0

def __loadmodule__(bot):
    global _options
    _options = Options(bot)

def __unloadmodule__(bot):
    global _options
    _options.unload()
    del _options

# vim:ts=4:sw=4:et
