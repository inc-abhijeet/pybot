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

from pybot import mm, hooks, modls, db
import re

HELP = """
You can load, unload, and reload modules with "[re|un]load module <module>".
I can also show you which modules are loaded at the moment with "show
modules". Only admins are allowed to do that.
"""

class ModuleControl:
    def __init__(self):
        db.table("module", "name")
        hooks.register("Message", self.message)

        modls.loadlist(self.get_modules())
        
        # [re|un]load [the] [module] <module>
        self.re1 = re.compile(r"(?P<command>(?:re|un)?load)(?:\s+the)?(?:\s+module)?\s+(?P<module>[\w_-]+)\s*[.!]*$", re.I)

        # show modules
        self.re2 = re.compile(r"show\s+modules\s*[.!]*$", re.I)

        # [[un|re]load] module[s]
        mm.register_help(r"(?:(?:un|re)?load\s+)?modules?", HELP, "modules")

    def get_modules(self):
        cursor = db.cursor()
        cursor.execute("select * from module order by name")
        return [x.name for x in cursor.fetchall()]

    def add_module(self, name):
        cursor = db.cursor()
        cursor.execute("select * from module where name=%s", name)
        if not cursor.rowcount:
            cursor.execute("insert into module values (%s)", name)

    def del_module(self, name):
        cursor = db.cursor()
        cursor.execute("delete from module where name=%s", name)

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
    
    def message(self, msg):
        if not msg.forme:
            return None
            
        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                command, module = m.group("command", "module")
                isloaded = modls.isloaded(module)
                modules = self.get_modules()
                if command == "load" and isloaded:
                    msg.answer("%:", ["Sorry, but",
                                      "Oops, I think that"],
                                     "this module is already loaded",
                                     [".", "!"])
                elif command == "load":
                    if modls.load(module):
                        self.add_module(module)
                        msg.answer("%:", ["Loaded", "Done", "Ready"],
                                         [".", "!"])
                    else:
                        msg.answer("%:", ["Something wrong happened while",
                                          "Something bad happened while",
                                          "There was a problem"],
                                         "loading the module",
                                         ["!", "."])
                elif not isloaded:
                    msg.answer("%:", ["Sorry, but", "Oops, I think that"],
                                     "this module is not loaded",
                                     [".", "!"])
                elif command == "reload":
                    if modls.reload(module):
                        msg.answer("%:", ["Reloaded", "Done", "Ready"],
                                         [".", "!"])
                    else:
                        if not modls.isloaded(module):
                            self.del_module(module)
                        msg.answer("%:", ["Something wrong happened while",
                                          "Something bad happened while",
                                          "There was a problem"],
                                         "reloading the module", ["!", "."])
                else:
                    if module in modules:
                        self.del_module(module)
                        if modls.unload(module):
                            msg.answer("%:", ["Unloaded", "Done", "Ready"],
                                             ["!", "."])
                        else:
                            msg.answer("%:",
                                       ["Something wrong happened while",
                                        "Something bad happened while",
                                        "There was a problem"],
                                       "unloading the module", ["!", "."])
                    else:
                        msg.answer("%:", ["Sorry, but",
                                          "Oops, I think that"],
                                         "this module can't be unloaded.")
            else:
                msg.answer("%:", ["You're not that good",
                                  "You are not able to work with modules",
                                  "No, you can't do this"],
                                 [".", "!",". I'm sorry!"])
            return 0

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                modules = modls.getlist()
                if not modules:
                    msg.answer("%:", ["There are no", "No"],
                                     "loaded modules", [".", "!"])
                else:
                    modules.sort()
                    msg.answer("%:", ["These are the loaded modules:",
                                      "The following modules are loaded:"],
                                     ", ".join(modules))
            else:
                msg.answer("%:", ["You're not that good",
                                  "You are not able to work with modules",
                                  "No, you can't do this"],
                                  [".", "!",". I'm sorry!"])
            return 0

def __loadmodule__():
    global mod
    mod = ModuleControl()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
