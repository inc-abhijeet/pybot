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

from pybot import mm, hooks, config
from string import join
import re
import os

HELP_COMPILETIME = [
("""\
You can verify the compile time for a given package in testadora \
using "[show] (compiletime|compile time) [for] <package>".\
""",)]

HELP_TESTADORA = [
("""\
For now, only the "compile time" command is available. Use "help compile \
time" for more information on this command.\
""",)]

class Testadora:
    def __init__(self):
        self.mondir = config.get("testadora", "mondir")
        
        hooks.register("Message", self.message)
        
        # [show] (compiletime|compile time) [for] <package>
        self.re1 = re.compile(r"(?:show\s+)?compile\s*time\s+(?:for\s+)?(?P<package>\S+)$")

        # (compiletime|compile time)
        mm.register_help(0, "compile\s*time", HELP_COMPILETIME)

        # testadora
        mm.register_help(0, "testadora", HELP_TESTADORA, "testadora")

    def unload(self):
        hooks.unregister("Message", self.message)

        mm.unregister_help(0, HELP_COMPILETIME)
        mm.unregister_help(0, HELP_TESTADORA)

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
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "compiletime"):
                    try:
                        seconds = self.get_compiletime(m.group("package"))
                    except IOError:
                        msg.answer("%", "Couldn't open data file.")
                    if not seconds:
                        msg.answer("%", "No time information for that package.")
                    else:
                        str = self.delta_string(seconds)
                        msg.answer("%", ["The %s package compiles in" % m.group("package"), "This package compiles in", "The compile time for that package is"], str, [".", "!"])
                else:
                    msg.answer("%", ["Sorry, but you", "No! You"], ["can't verify compile times", "are not able to check compile times", "will have to check this by yourself"], [".", "!"])
                return 0

def __loadmodule__(bot):
    global mod
    mod = Testadora()

def __unloadmodule__(bot):
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
