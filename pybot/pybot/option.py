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

import time

class Options:
    def __init__(self):
        self._dict = {}
    
    def getdict(self):
        return self._dict

    def setdict(self, dict):
        self._dict = dict

    def get(self, name, default=None, keepalive=0, reboot=0):
        """
        You may define for how long the option will be considered
        valid trough the keepalive argument (in seconds). If keepalive
        is 0 (default), option will stay valid while pybot is up, or
        at least until you change the keepalive to something else. If
        reboot is true, the option will be alive even if pybot reboots,
        or quits and returns later.
        """
        curtime = time.time()
        if keepalive:
            keepalive += curtime
        opt = self._dict.get(name)
        if opt:
            if not opt[1] or curtime < opt[1]:
                if keepalive:
                    opt[1] = keepalive
                return opt[0]
            else:
                del self._dict[name]
        self._dict[name] = [default, keepalive, reboot]
        return default

    def set(self, name, value, keepalive=None, reboot=None):
        oldvalue = self.get(name)
        newvalue = [value, keepalive, reboot]
        if oldvalue:
            if ListType == type(oldvalue[0]) == type(newvalue[0]):
                oldvalue[0][:] = newvalue[0]
                newvalue[0] = oldvalue[0]
            elif DictType == type(oldvalue[0]) == type(newvalue[0]):
                oldvalue[0].clear()
                oldvalue[0].update(newvalue[0])
                newvalue[0] = oldvalue[0]
            if keepalive is None:
                newvalue[1] = oldvalue[1]
            if reboot is None:
                newvalue[2] = oldvalue[2]
        self._dict[name] = newvalue

    def remove(self, name):
        try:
            del self._dict[name]
        except KeyError:
            pass

    def keys(self):
        return self._dict.keys()

    def has_key(self, name):
        return self._dict.has_key(name)

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        self.set(name, value)

    def __delitem__(self, name):
        self.remove(name)

    def __contains__(self, name):
        return self.has_key(name)

# vim:ts=4:sw=4:et
