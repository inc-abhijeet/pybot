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

from pybot.locals import *
from string import join
import os

HELP_COMPILETIME = """
You can verify the compile time for a given package in testadora
using "[show] (compiletime|compile time) [for] <package>". You need
the "compiletime" permission for that.
"""

HELP_TESTADORA = """
For now, only the "compile time" command is available. Use "help compile
time" for more information on this command.
"""

PERM_COMPILETIME = """
The "compiletime" permission allows users to ask for compile times from
testadora. Check "help compile time" for more information.
"""

class Testadora:
    def __init__(self):
        self.mondir = config.get("testadora", "mondir")
        
        hooks.register("Message", self.message)
        
        # [show] (compiletime|compile time) [for] <package>
        self.re1 = regexp(r"(?:show )?compile\s*time (?:for )?(?P<package>\S+)")

        # testadora
        mm.register_help("testadora", HELP_TESTADORA, "testadora")

        # (compiletime|compile time)
        mm.register_help("compile\s*time", HELP_COMPILETIME)

        mm.register_perm("compiletime", PERM_COMPILETIME)

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP_TESTADORA)
        mm.unregister_help(HELP_COMPILETIME)
        mm.unregister_perm(PERM_COMPILETIME)

    def get_compiletime(self, package):
        file = open(os.path.join(self.mondir, "timelog.txt"))
        for line in file.readlines():
            tokens = line.split()
            if len(tokens) > 1 and tokens[1] == package:
                try:
                    return int(tokens[0])
                except ValueError:
                    pass
        return None

    def delta_string(self, seconds):
        field = ["year","month","day","hour","minute","second"]
        fieldsize = [31536000, 2592000, 86400, 3600, 60, 1]
        fieldvalue = [0]*6
        for n in range(6):
            fieldvalue[n] = seconds/fieldsize[n]
            seconds -= fieldvalue[n]*fieldsize[n]
        assert seconds == 0
        str = ""
        for n in range(6):
            value = fieldvalue[n]
            if value:
                s = (value > 1) and "s" or ""
                if str:
                    str += ", "
                    if not filter(bool, fieldvalue[n+1:]):
                        str += "and "
                str += "%d %s%s" % (value, field[n], s)
        return str

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "compiletime"):
                try:
                    seconds = self.get_compiletime(m.group("package"))
                except IOError:
                    msg.answer("%", "Couldn't open data file.")
                if not seconds:
                    msg.answer("%", "No time information for that package.")
                else:
                    str = self.delta_string(seconds)
                    msg.answer("%", ["The %s package compiles in" %
                                     m.group("package"),
                                     "This package compiles in",
                                     "The compile time for that package is"],
                                    str, [".", "!"])
            else:
                msg.answer("%", ["Sorry, but you", "No! You"],
                                ["can't verify compile times",
                                 "are not able to check compile times",
                                 "will have to check this by yourself"],
                                 [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = Testadora()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
