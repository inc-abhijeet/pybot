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

from string import split
from pybot.user import User
import re

class Command:
    re = re.compile("(?::(\\S*) )?(\\w+) ((\\S+) :(?:\01(\\w+) )?((?:\\W*(\\w+)\\W*\\s)?(.*?))(?:\01)?|.*)$")
        
    def __init__(self):
        self.user = User()

    def setline(self, server=None, line=None):
        self.server = server
        m = self.re.match(line)
        if m:
            nick = self.server.user.nick
            self.prefix = m.group(1) or ""
            self.user.setstring(self.prefix)
            self.cmd = m.group(2)
            # _index is used for speed purposes and shouldn't be
            # used by modules.
            try:
                # Message = 0, Notice = 1
                self._index = ["PRIVMSG", "NOTICE"].index(self.cmd)
            except:
                # Command = 2
                self._index = 2
                self.line = self.rawline = m.group(3)
                self.target = ""
                self.ctcp = ""
                self.forme = 0
                self.direct = 0
                self.answertarget = ""
                self.answered = 0
            else:
                self.target = m.group(4)
                self.ctcp = m.group(5)
                if self.ctcp:
                    self._index += 3 # CTCP = 3, CTCPReply = 4
                self.rawline = m.group(6)
                if m.group(7) == nick:
                    self.line = m.group(8)
                    self.forme = 1
                else:
                    self.line = self.rawline
                    self.forme = 0
                if self.target == nick:
                    self.forme = 1
                    self.direct = 1
                    self.answertarget = self.user.nick
                else:
                    self.direct = 0
                    self.answertarget = self.target
                self.answered = 0
        else:
            self.prefix = ""
            self.cmd = ""
            self.target = ""
            self.answertarget = ""
            self.forme = 0
            self.direct = 0
            self.line = ""
            self.rawline = ""
            self._index = 2
            self.answered = 0
        
    def answer(self, *params, **kw):
        self.server.sendmsg(self.answertarget, self.user.nick, *params, **kw)
        self.answered = 1
    
# vim:ts=4:sw=4:et
