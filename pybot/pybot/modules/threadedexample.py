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

from pybot import mm, hooks
import time

class ThreadedExample:
    def __init__(self, bot):
        hooks.register("Message", self.threadedmessage, threaded=1)
        hooks.register("Message", self.message)
    
    def unload(self):
        hooks.unregister("Message", self.threadedmessage, threaded=1)
        hooks.unregister("Message", self.message)
        mm.unhooktimer(0, None, self.threadedtimer, None);
    
    def threadedmessage(self, msg):
        var = []
        if msg.match(var, 0, "%", "test", "threaded", "message", ["!", ".", None]):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "threadedexample"):
                for i in range(10):
                    msg.answer("%:", "I'm in the thread...")
                    time.sleep(1)

    def message(self, msg):
        var = []
        if msg.match(var, 0, "%", "test", "threaded", "timer", ["!", ".", None]):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "threadedexample"):
                mm.hooktimer(0, 20, self.threadedtimer, (msg,), threaded=1);
                return 0
        elif msg.match(var, 0, "%", "stop", "threaded", "timer", ["!", ".", None]):
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "threadedexample"):
                mm.unhooktimer(0, 20, self.threadedtimer, None, threaded=1);
                return 0

    def threadedtimer(self, msg):
        msg.answer("%:", "Timer thread started!")
        time.sleep(10)
        msg.answer("%:", "Timer thread stopped!")

def __loadmodule__(bot):
    global threadedexample
    threadedexample = ThreadedExample(bot)

def __unloadmodule__(bot):
    global threadedexample
    threadedexample.unload()
    del threadedexample

# vim:ts=4:sw=4:et
