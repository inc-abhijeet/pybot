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
import time
import re

HELP = """
This is a module implementation showing a basic but complete module
to serve as reference for other modules. It implements the command
"hello (world|irc)". You will need the "example" permission to use that.
"""

PERM_EXAMPLE = """
The "example" permission allows users to access commands in the "example"
module. For more information, check "help example".
"""

class Example:
    def __init__(self):
        hooks.register("Message", self.message)
    
        # hello (world|irc)
        self.re1 = regexp(r"hello (?P<what>world|irc)")

        mm.register_help(r"example", HELP, "example")

        mm.register_perm("example", PERM_EXAMPLE)

        # This is a volatile variable which will be reset once pybot
        # reboots, but won't be lost if pybot reloads this module. Use
        # "show option Test.firstload" to check it.
        #firstload = options.get("Test.firstload", [int(time.time())])

        # This is a persistent variable which will resist even if
        # pybot dies. Notice that no module in the standard module set
        # is using this kind of persistence (they use sqlite instead),
        # and if no module uses it, the "memory" file is transparently
        # not saved.
        #loads = options.get("Test.loads", [1], reboot=1)
        #loads[0] += 1 

        # This is a simple way of doing the same thing with the sqlite
        # dict system. It is useful for simple variables like this.
        #loads = int(db["loads"] or 0)
        #loads += 1
        #db["loads"] = loads

        # And this is a more complex one, saving the load time as well
        # ('num' wasn't needed in this case since we could use the number
        # of entries in the table, but was included to show a table with
        # more than one field).
        #db.table("test", "num,timestamp")
        #db.execute("select max(num) from test")
        #row = db.fetchone()
        #if row[0]:
        #    loads = int(row[0])+1
        #else:
        #    loads = 1
        #db.execute("insert into test values (?,?)", loads, int(time.time()))

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm(PERM_EXAMPLE)
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "example"):
                what = m.group("what")
                msg.answer("%:", "The", what, "welcomes you",
                                 [(",", "/"), None],
                                 [".", "!"])
            else:
                msg.answer("%:", ["You have no permission for that",
                                  "You are not allowed to do this"],
                                 [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = Example()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
