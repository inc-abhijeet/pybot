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

from pybot import hooks, mm
from random import randint
import re

HELP = """
You can give you some random numbers if you send me "[give|tell|show]
[me] [a|one|<n>] [random] number[s] between <num1> and <num2>". You'll
need the "randnum" permission for that.
"""

PERM_RANDNUM = """
The "randnum" permission allows users to ask for random numbers. Check
"help randnum" for more information.
"""

class RandNum:
    def __init__(self):
        hooks.register("Message", self.message)
        
        # [give|tell|show] [me] [a|one|<n>] [random] number[s] between <num1> and <num2>
        self.re1 = re.compile(r"(?:give|tell|show)\s+(?:me\s+)?(?P<n>a|one|\d+)\s+(?:random\s+)?numbers?\s+between\s+(?P<num1>\d+)\s+and\s+(?P<num2>\d+)\s*[.!]*$", re.I)

        # randnum[s]|random number[s]
        mm.register_help("randnums?|random\s+numbers?", HELP, "randnum")

        mm.register_perm("randnum", PERM_RANDNUM)
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm("randnum")
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "randnum"):
                try:
                    n = m.group("n")
                    if n in ["a", "one"]:
                        n = 1
                    else:
                        n = int(var[0])
                    s = int(m.group("num1"))
                    e = int(m.group("num2"))
                    randint(s,e)
                except:
                    msg.answer("%:", ["Your numbers are not valid",
                                      "I need valid numbers",
                                      "You must give me valid numbers",
                                      "There's a problem with your numbers",
                                      "You gave me invalid numbers"],
                                      [".", "!"])
                    return
                if n > 0:
                    if n < 11:
                        nums = str(randint(s,e))
                        i = 1
                        while i < n:
                            num = randint(s,e)
                            if i == n-1:
                                if n > 2:
                                    nums = nums+", and "+str(num)
                                else:
                                    nums = nums+" and "+str(num)
                            else:
                                nums = nums+", "+str(num)
                            i = i + 1
                        if n == 1:
                            isare = "number is"
                        else:
                            isare = "numbers are"
                        msg.answer("%:", ["Your", "The", "The chosen"],
                                         isare, nums, [".", "!"])
                    else:
                        msg.answer("%:", "You",
                                         ["have to", "must", "should"],
                                         "ask for 10 numbers, at most",
                                         [".", "!"])
                else:
                    msg.answer("%:", "You", ["have to", "must", "should"],
                                     "ask for 1 number, at least",
                                     [".", "!"])
            else:
                msg.answer("%:", ["You're not allowed to ask for random "
                                  "number", "You can't do that", "No, "
                                  "you're not allowed"], [".", "!"])
            return 0


def __loadmodule__():
    global mod
    mod = RandNum()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
