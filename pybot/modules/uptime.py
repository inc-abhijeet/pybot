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
import calendar
import time

HELP = """
I can tell you for how much time I'm online with "[show] uptime". You can
also reset the timer with "reset uptime", but you'll need to be an admin
for that.
"""

class Uptime:
    def __init__(self):
        self.uptime = options.get("Uptime.uptime", int(time.time()))
        hooks.register("Message", self.message)

        # [show|display] uptime
        self.re1 = regexp(r"(?:(?:show|display) )?uptime")

        # reset uptime
        self.re2 = regexp(r"reset uptime")

        # uptime
        mm.register_help("uptime", HELP, "uptime")
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
    
    def days_in_last_month(self, tuple):
        year = tuple[0]
        month = tuple[1]
        if month == 1:
            month = 12
            year -= 1
        else:
            month -= 1
        return calendar.monthrange(year, month)[1]

    def uptime_string(self):
        tuple1 = time.localtime(self.uptime)[:6]
        tuple2 = time.localtime(time.time())[:6]
        field = ["year","month","day","hour","minute","second"]
        dilm = self.days_in_last_month(tuple2)
        fieldlimit = [(0,0),(0,12),(0,dilm),(0,24),(0,60),(0,60)]
        str = ""
        valid = 0
        n = 5
        carry = 1
        while n >= 0:
            diff = (fieldlimit[n][1]-tuple1[n])+(tuple2[n]-fieldlimit[n][0])-1
            diff = diff+carry
            if diff >= fieldlimit[n][1]:
                diff = diff - fieldlimit[n][1]
                carry = 1
            else:
                carry = 0
            if diff:
                valid = valid+1
                if diff > 1:
                    s = "s"
                else:
                    s = ""
                if valid == 1:
                    str = "%d %s%s"%(diff, field[n], s)
                elif valid == 2:
                    str = "%d %s%s, and %s"%(diff, field[n], s, str)
                else:
                    str = "%d %s%s, %s"%(diff, field[n], s, str)
            n = n-1
        return str
        
    def message(self, msg):
        var = []
        if msg.forme:
            if self.re1.match(msg.line):
                uptimestr = self.uptime_string()
                msg.answer("%:", "I'm up for", uptimestr, ".")
                return 0
            elif self.re2.match(msg.line):
                if mm.hasperm(msg, "admin"):
                    self.uptime = int(time.time())
                    options.set("Uptime.uptime", self.uptime)
                    msg.answer("%:", ["No problems", "Sure", "Done", "Ok"],
                                     [".", "!"])
                else:
                    msg.answer("%:", ["Heh!", "Sorry!"], "You can't do this",
                                     [".", "!"])
                return 0

def __loadmodule__():
    global mod
    mod = Uptime()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
