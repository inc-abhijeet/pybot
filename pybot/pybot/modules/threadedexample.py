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

from pybot import mm, hooks
import time

import re

HELP = """
This is a module implementation showing how to work with threaded
hooks. If you have the "threadedexample" permission, you can test it
with "test threaded message" and "(start|stop) threaded timer".
"""

PERM_THREADEDEXAMPLE = """
This permission allows users to issue commands in the threadedexample
module. For more information check "help threadedexample".
"""

class ThreadedExample:
    def __init__(self):
        hooks.register("Message", self.threadedmessage, threaded=1)
        hooks.register("Message", self.message)
    
        # test threaded message
        self.re1 = re.compile(r"test\s+threaded\s+message\s*[.!]*$", re.I)

        # (start|stop) threaded timer
        self.re2 = re.compile(r"(?P<cmd>start|stop)\s+threaded\s+timer\s*[.!]*$", re.I)

        mm.register_help(r"threadedexample", HELP, "threadedexample")

        mm.register_perm("threadedexample", PERM_THREADEDEXAMPLE)
    
    def unload(self):
        hooks.unregister("Message", self.threadedmessage, threaded=1)
        hooks.unregister("Message", self.message)
        mm.unhooktimer(None, self.threadedtimer, None);

        mm.unregister_help(HELP)
        mm.unregister_perm(PERM_THREADEDEXAMPLE)
    
    def threadedmessage(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "threadedexample"):
                for i in range(10):
                    msg.answer("%:", "I'm in the thread...")
                    time.sleep(1)
            # If the user has no permission don't even bother.
            # return 0

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "threadedexample"):
                if m.group("cmd") == "start":
                    mm.hooktimer(15, self.threadedtimer, (msg,), threaded=1)
                else:
                    mm.unhooktimer(15, self.threadedtimer, None, threaded=1)
                msg.answer("%:", ["Done", "Ok", "Sure"], [".", "!"])
                return 0

    def threadedtimer(self, msg):
        msg.answer("%:", "Timer thread started!")
        time.sleep(5)
        msg.answer("%:", "Timer thread stopped!")

def __loadmodule__():
    global mod
    mod = ThreadedExample()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
