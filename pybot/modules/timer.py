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
from time import time
from thread import start_new_thread

class Timer:
    def __init__(self):
        self.timer = options.get("Timer.data", [])
        mm.register("hooktimer", self.mm_hooktimer)
        mm.register("unhooktimer", self.mm_unhooktimer)
        hooks.register("Loop", self.loop)
    
    def unload(self):
        mm.unregister("hooktimer")
        mm.unregister("unhooktimer")
        hooks.unregister("Loop", self.loop)
    
    def loop(self):
        for list in self.timer:
            curtime = int(time())
            if list[0] <= curtime:
                list[0] = curtime+list[1]
                if list[4]:
                    start_new_thread(list[2], list[3])
                else:
                    apply(list[2], list[3])

    def mm_hooktimer(self, sec, func, params, threaded=0):
        self.timer.append([int(time())+sec, sec, func, params, threaded])

    def mm_unhooktimer(self, sec, func, params, threaded=None):
        ret = 0
        i = 0
        l = len(self.timer)
        r = []
        while i < l:
            list = self.timer[i]
            if (sec is None or list[1] == sec) and \
               (func is None or list[2] == func) and \
               (params is None or list[3] == params) and \
               (threaded is None or list[4] == threaded):
                r.append(i)
                ret = 1
            i = i + 1
        for i in r:
            del self.timer[i]
        return ret

# Load first to let hooktimer() available to other modules.
__loadlevel__ = 90

def __loadmodule__():
    global mod
    mod = Timer()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
