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

from pybot import mm, hooks, options, modls
import re

HELP = [
("""\
You can load, unload, and reload modules with "[re|un]load module <module>". \
I can also show you which modules are loaded at the moment with "show \
[loaded] modules".\
""",)]

class ModuleControl:
    def __init__(self, bot):
        self.modules = options.gethard("ModuleControl.modules", [])
        hooks.register("Message", self.message)
        modls.loadlist(self.modules)
        
        # Match '[re|un]load [the] [module] <module>'
        self.re1 = re.compile("(?P<command>(?:re|un)?load)(?:\s+the)?(?:\s+module)?\s+(?P<module>[\w_-]+)\s*[.!]*$", re.I)

        # Match '(show|list) [loaded] modules'
        self.re2 = re.compile("(?:show|list)(?:\s+loaded)\s+modules\s*[.!]*$", re.I)

        # Match '[[un|re]load] module[s]'
        mm.register_help(0, "(?:(?:un|re)?load\s+)?modules?", HELP)

    def unload(self):
        hooks.unregister("Message", self.message)
    
    def message(self, msg):
        var = []
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(1, msg.server.servername, msg.target, msg.user, None):
                    command, module = m.group("command", "module")
                    isloaded = modls.isloaded(module)
                    if command == "load" and isloaded:
                        msg.answer("%:", ["Sorry sir, but", "Sir,", "Oops, I think that"], "this module is already loaded.")
                    elif not isloaded:
                        msg.answer("%:", ["Sorry sir, but", "Sir,", "Oops, I think that"], "this module is not loaded.")
                    elif command == "load":
                        if modls.load(module):
                            self.modules.append(module)
                            msg.answer("%:", ["Loaded", "Done", "Ready"], ["!", "."])
                        else:
                            msg.answer("%:", ["Something wrong happened while", "Something bad happened while", "There was a problem"],  "loading the module", ["!", "."])
                    elif command == "reload":
                        if modls.reload(module):
                            msg.answer("%:", ["Reloaded", "Done", "Ready"], ["!", ", sir!"])
                        else:
                            if not modls.isloaded(module):
                                self.modules.remove(module)
                            msg.answer("%:", ["Something wrong happened while", "Something bad happened while", "There was a problem"],  "reloading the module", ["!", "."])
                    else:
                        if module in self.modules:
                            self.modules.remove(module)
                            if modls.unload(module):
                                msg.answer("%:", ["Unloaded", "Done", "Ready"], ["!", "."])
                            else:
                                msg.answer("%:", ["Something wrong happened while", "Something bad happened while", "There was a problem"],  "unloading the module", ["!", "."])
                        else:
                            msg.answer("%:", ["Sorry, but", "Oops, I think that"], "this module can't be unloaded.")
                else:
                    msg.answer("%:", ["You're not that good", "You are not able to work with modules", "No, you can't do this"], [".", "!",". I'm sorry!"])
                return 0

            m = self.re2.match(msg.line)
            if m:
                if mm.hasperm(1, msg.server.servername, msg.target, msg.user, None):
                    if not self.modules:
                        msg.answer("%:", ["There are no", "No"], "loaded modules", [".", "!"])
                    else:
                        msg.answer("%:", ["These are the loaded modules:", "The following modules are loaded:", ", ".join(self.modules))
                else:
                    msg.answer("%:", ["You're not that good", "You are not able to work with modules", "No, you can't do this"], [".", "!",". I'm sorry!"])
                return 0

def __loadmodule__(bot):
    global modulecontrol
    modulecontrol = ModuleControl(bot)

def __unloadmodule__(bot):
    global modulecontrol
    modulecontrol.unload()
    del modulecontrol

# vim:ts=4:sw=4:et
