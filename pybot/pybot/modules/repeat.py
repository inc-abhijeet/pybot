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

from pybot import mm, hooks, servers
from string import join
import re

class RepeatDef:
    def __init__(self, notice=0, action=0, server=None, target=None, phrase=""):
        self.notice = notice
        self.action = action
        self.server = server
        self.target = target
        self.phrase = phrase
    
    def __eq__(self, repdef):
        """Used when mm.unhooktimer is called."""
        if isinstance(repdef, RepeatDef):
            return self.notice == repdef.notice and \
                   self.action == repdef.action and \
                   self.server == repdef.server and \
                   self.target == repdef.target and \
                   self.phrase == repdef.phrase

class Repeat:
    def __init__(self, bot):
        hooks.register("Message", self.message)

        # [don[']t|do not] repeat [each <n> seconds] (to|at|on) [channel|user] <target> [[on|at] server <server>] [/me|/notice] ...
        self.re1 = re.compile(r"(?:(?P<dont>don'?t|do\s+not)\s+)?repeat(?:\s+each\s+(?P<interval>[0-9]+)\s*(?P<intervalunit>se?c?o?n?d?s?|mi?n?u?t?e?s?|ho?u?r?s?))?(?:\s+(?:to|at|on)(?:\s+(?:channel|user))?\s+(?P<target>\S+))?(?:\s+(?:on|at)?\s+server\s+(?P<server>\S+))?\s+(?P<action>/me\s)?(?P<notice>/notice\s)?(?P<phrase>.*)$")

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unhooktimer(0, None, self.do_repeat, None)
    
    def do_repeat(self, repdef):
        server = servers.get(repdef.server)
        if server:
            action = repdef.action and "ACTION"
            server.sendmsg(repdef.target, None, repdef.phrase, notice=repdef.notice, ctcp=action)
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "repeat"):
                    repdef = RepeatDef()
                    repdef.notice = m.group("notice") != None
                    repdef.action = m.group("action") != None
                    repdef.server = m.group("server") or msg.server.servername
                    repdef.target = m.group("target") or msg.answertarget
                    repdef.phrase = m.group("phrase")
                    dont = m.group("dont") != None
                    interval = m.group("interval")
                    if interval != None:
                        unit = m.group("intervalunit")[0]
                        unitindex = ["s", "m", "h"].index(unit)
                        unitfactor = [1, 60, 3600][unitindex]
                        try:
                            interval = int(interval)*unitfactor
                            if interval == 0:
                                raise ValueError
                        except ValueError:
                            msg.answer("%:", ["Hummm...", "Oops!", "Heh..."], ["This interval is not valid", "There's something wrong with the interval you provided"], ["!", "."])
                            return 0
                        if dont:
                            mm.unhooktimer(0, interval, self.do_repeat, (repdef,))
                        else:
                            mm.hooktimer(0, interval, self.do_repeat, (repdef,))
                    else:    
                        self.do_repeat(repdef)
                    if m.group("server") or m.group("target") or m.group("interval"):
                        msg.answer("%:", ["Done", "No problems", "At your order"], ["!", "."])
                else:
                    msg.answer("%", ["Sorry, but you", "Sir, you", "No! You"], ["can't tell me what to repeat.", "are not able to make me repeat.", "will have to repeat by yourself."])
                return 0

def __loadmodule__(bot):
    global repeat
    repeat = Repeat(bot)

def __unloadmodule__(bot):
    global repeat
    repeat.unload()
    del repeat

# vim:ts=4:sw=4:et
