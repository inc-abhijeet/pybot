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

from pybot import mm, hooks, options, config
import time
import sys
import os
import re

HELP = [
("""\
You may (un)plock packages using "[force] [un]plock <package> [,<package>]". \
It's also possible to consult your plocks using "my plocks", or from \
somebody else using "plocks of <nick|email>".\
""",),
("""\
Note that to be able to work with plocks, you must first register yourself \
with me, and then register an email with "set email your@email". For more \
information use "help register".\
""",)]

class PLockFile:
    def __init__(self, dir, name):
        self.name = name
        self.file = os.path.join(dir, name)
        self.line = None
        self.isfile = os.path.isfile(self.file)

    def get(self):
        if not self.line and self.isfile:
            self.line = open(self.file, "r").readline()
            if self.line and self.line[-1] == "\n":
                self.line = self.line[:-1]
        return self.line

    def set(self, line):
        self.line = line
        open(self.file, "w").write(line+"\n")

    def exists(self):
        return self.isfile

    def remove(self):
        if self.isfile:
            os.unlink(self.file)

    def gettime(self):
        return time.localtime(os.stat(self.file)[8])

class PLock:
    def __init__(self, bot):
        self.pdir = config.get("plock", "dirpath")
        hooks.register("Message", self.message)
        
        # [force] plock <package> [,<package>] [!|.]
        self.re1 = re.compile(r"(?P<force>force\s+)?plock\s+(?P<package>[\w_\.-]+(?:(?:\s*,?\s*and\s+|[, ]+)[\w_\.-]+)*)\s*[!.]*$")
        
        # [force] (unplock|punlock) <package> [,<package>] [!|.]
        self.re2 = re.compile(r"(?P<force>force\s+)?(?:unplock|punlock)\s+(?P<package>[\w_\.-]+(?:(?:\s*,?\s*and\s+|[, ]+)[\w_\.-]+)*)\s*[!.]*$")
        
        # (my plocks|plocks of <user>) [?]
        self.re3 = re.compile(r"(?:(?P<my>my)\s+plocks|plocks\s+of\s+(?P<user>[\w\.@_-]+))\s*(?:!*\?[?!]*)?$")

        # ([who] [has] plocked|plocker [of]) <package> [,<package>] [?]
        self.re4 = re.compile(r"(?:(?:who\s+)?(?:has\s+)plocked|plocker\s+(?:of\s+)?)(?P<package>[\w_\.-]+(?:(?:\s*,?\s*and\s+|[, ]+)[\w_\.-]+)*)\s*(?:!*\?[?!]*)?$")

        # plock <package> [,<package>] ?
        self.re5 = re.compile(r"plock\s+(?P<package>[\w_\.-]+(?:(?:\s*,?\s*and\s+|[, ]+)[\w_\.-]+)*)\s*(?:!*\?[?!]*)$")

        # [un]plock[ing] | <package|pkg> lock[ing]
        mm.register_help(0, "(?:un)?plock(?:ing)?|(?:package|pkg)\s+lock(?:ing)?",
                         HELP, "plock")

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(0, HELP)
    
    def getnick(self, servername, email):
        data = options.gethard("UserData.data", {})
        for pair in data:
            if pair[0] == servername:
                if data[pair].get("email") == email:
                    return nick
        return None

    def message(self, msg):
        var = []
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "plock"):
                    email = mm.getuserdata(0, msg.server, msg.user.nick, "email")
                    if not email:
                        msg.answer("%:", ["Hummm...", "Nope!", "Sorry!"], "You must register an email (with 'register email <email>')", ["!", "."])
                    else:
                        ok = 1
                        force = m.group("force")
                        split_re = re.compile("(?:\s*,?\s*and\s+|[, ]+)")
                        packages = split_re.split(m.group("package"))
                        for package in packages:
                            file = PLockFile(self.pdir, package)
                            if not force and file.exists():
                                ok = 0
                                msg.answer("%:", ["Oops!", "Sorry!"], "Package %s is already plocked"%package, ["!", "."])
                            else:
                                if msg.direct:
                                    target = msg.user.nick
                                else:
                                    target = msg.target
                                mm.shownotes(None, msg.server, target, msg.user.nick, package)
                                try:
                                    file.set(email)
                                except:
                                    ok = 0
                                    msg.answer("%:", ["Argh!", "Oops!", "Damd!"], "Something wrong happened while trying to plock "+package, ["!", "."])
                        if ok:
                            msg.answer("%:", ["Done", "Ready", "Plocked"], ["!", "."])
                else:
                    msg.answer("%:", ["Sorry, you", "You"], ["can't plock.", "don't have this power."])
                return 0
            
            m = self.re2.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "plock"):
                    email = mm.getuserdata(0, msg.server, msg.user.nick, "email")
                    if not email:
                        msg.answer("%:", ["Hummm...", "Nope!", "Sorry!"], "You must register an email", ["!", "."])
                    else:
                        ok = 1
                        force = m.group("force")
                        split_re = re.compile("(?:\s*,?\s*and\s+|[, ]+)")
                        packages = split_re.split(m.group("package"))
                        for package in packages:
                            file = PLockFile(self.pdir, package)
                            if not file.exists():
                                ok = 0
                                msg.answer("%:", ["Oops!", "Sorry!"], "Package %s is not plocked"%package, ["!", "."])
                            elif not force and file.get() != email:
                                ok = 0
                                msg.answer("%:", ["Oops!", "Sorry!"], "Package %s is not plocked by you"%package, ["!", "."])
                            else:
                                if msg.direct:
                                    target = msg.user.nick
                                else:
                                    target = msg.target
                                mm.shownotes(None, msg.server, target, msg.user.nick, package)
                                try:
                                    file.remove()
                                except:
                                    ok = 0
                                    msg.answer("%:", ["Argh!", "Oops!", "Damd!"], "Something wrong happened while trying to unplock "+package, ["!", "."])
                        if ok:
                            msg.answer("%:", ["Done", "Ready", "Unplocked"], ["!", "."])
                else:
                    msg.answer("%:", ["Sorry, you", "You"], ["can't unplock.", "don't have this power."])
                return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "plock"):
                my = m.group("my") != None
                user = m.group("user")
                if my:
                    email = mm.getuserdata(0, msg.server, msg.user.nick, "email")
                    if not email:
                        msg.answer("%:", ["Hummm...", "Nope!", "Sorry!"], "You must register an email", ["!", "."])
                elif "@" not in user:
                    email = mm.getuserdata(0, msg.server, user, "email")
                    if not email:
                        msg.answer("%:", ["Hummm...", "Nope!", "Sorry!"], "No email registered for this nick", ["!", "."])
                else:
                    email = user 
                if email:
                    plocks = None
                    for name in os.listdir(self.pdir):
                        file = PLockFile(self.pdir, name)
                        if email == file.get():
                            if plocks:
                                plocks = plocks + ", " + name
                            else:
                                plocks = name
                    if my:
                        if plocks:
                            msg.answer("%:", ["Here are your plocks:", "Your plocks:"], plocks)
                        else:
                            msg.answer("%:", ["You're not plocking any package", "No plocks for you"], ["!", "."])
                    else:
                        if plocks:
                            msg.answer("%:", user+" is plocking the following packages:", plocks)
                        else:
                            msg.answer("%:", [user+" is not plocking any package", "No plocks for "+user], ["!", "."])
            else:
                msg.answer("%:", ["Sorry, but you", "You"], ["can't check plocks.", "are not that good."])
            return 0

        m = self.re4.match(msg.line) or self.re5.match(msg.line)
        if m:
            if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "plock"):
                split_re = re.compile("(?:\s*,?\s*and\s+|[, ]+)")
                packages = split_re.split(m.group("package"))
                for package in packages:
                    file = PLockFile(self.pdir, package)
                    if file.exists():
                        locker = file.get()
                        ptime = file.gettime()
                        if self.istoday(ptime):
                            fstr = " today at %H:%M."
                        else:
                            fstr = " on %Y/%m/%d at %H:%M."
                        when = time.strftime(fstr, ptime)
                        email = mm.getuserdata(0, msg.server, msg.user.nick, "email")
                        if locker == email:
                            msg.answer("%:", "You have plocked "+package+when)
                        else:
                            nick = self.getnick(msg.server.servername, locker)
                            if nick: locker = nick
                            msg.answer("%:", locker+" has plocked "+package+when)
                    else:
                        msg.answer("%:", "Package %s is not plocked"%package, ["!", "."])
            else:
                msg.answer("%:", ["Sorry, but you", "You"], ["can't check plocks.", " are not that good."])
            return 0

    def istoday(self, ptimetuple):
        timetuple = time.localtime(time.time())
        if timetuple[:3] == ptimetuple[:3]:
            return 1

def __loadmodule__(bot):
    global plock
    plock = PLock(bot)

def __unloadmodule__(bot):
    global plock
    plock.unload()
    del plock

# vim:ts=4:sw=4:et
