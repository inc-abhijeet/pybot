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

from pybot import hooks, main, mm
import math
import re

class Eval:
    def __init__(self, bot):
        hooks.register("Message", self.message)
        self.dict = {}
        self.dict["__builtins__"] = {}
        self.dict.update(math.__dict__)
        del self.dict["__doc__"]
        del self.dict["__file__"]
        del self.dict["__name__"]
        self.dict["map"] = map
        self.dict["zip"] = zip
        self.dict["len"] = len
        self.dict["min"] = min
        self.dict["max"] = max
        self.dict["chr"] = chr
        self.dict["ord"] = ord
        self.dict["abs"] = abs
        self.dict["hex"] = hex
        self.dict["int"] = int
        self.dict["oct"] = oct
        self.dict["list"] = list
        self.dict["long"] = long
        self.dict["float"] = float
        self.dict["round"] = round
        self.dict["tuple"] = tuple
        self.dict["reduce"] = reduce
        self.dict["filter"] = filter
        self.dict["coerce"] = coerce

        # Match 'eval <expr>[!|.]'
        self.re1 = re.compile(r"eval\s+(?P<expr>.*?)[!.]*$")
    
    def unload(self):
        hooks.unregister("Message", self.message)
    
    def message(self, msg):
        var = []
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "eval"):
                    try:
                        answer = eval(m.group("expr"), self.dict)
                    except:
                        msg.answer("%:", ["Can't evaluate this", "There's something wrong with this expression"], [".", "!"])
                    else:
                        if len(answer) > 255:
                            msg.answer("%:", "Sorry, your answer is too long...")
                        else:
                            msg.answer("%:", str(answer))
                else:
                    msg.answer("%:", ["Sorry...", "Oops!", "Heh!"], "You don't have this power", [".", "!"])
                return 0

def __loadmodule__(bot):
    global _eval
    _eval = Eval(bot)

def __unloadmodule__(bot):
    global _eval
    _eval.unload()
    del _eval

# vim:ts=4:sw=4:et
