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

class Fragment:
    def __init__(self, expr=""):
        self._expr = expr

    def expr(self, optional=0):
        if optional:
            return self._expr+"?"
        return self._expr

    def __str__(self):
        return self.expr()

    def __call__(self, *args, **kwargs):
        return self.expr(*args, **kwargs)

    def get(self, msg, match):
        raise TypeError, "this method must be overloaded"

class Dont(Fragment):
    def __init__(self):
        Fragment.__init__(self, r"(?P<_dont>don'?t\s+|do not\s+)")

    def get(self, msg, match):
        return match.group("_dont")
dont = Dont()

class Interval(Fragment):
    def __init__(self):
        Fragment.__init__(self, r"(?:\s+each\s+(?P<_interval>[0-9]+)\s*(?P<_intervalunit>se?c?o?n?d?s?|mi?n?u?t?e?s?|ho?u?r?s?))")

    def get(self, msg, match, default=None):
        interval = match.group("_interval")
        if not interval:
            if not default:
                msg.answer("%:", "Internal error: no interval and no default.")
                return None
            interval = default[:-1]
            unit = default[-1]
        else:
            unit = match.group("_intervalunit")[0]
        unitindex = ["s", "m", "h"].index(unit)
        unitfactor = [1, 60, 3600][unitindex]
        try:
            interval = int(interval)*unitfactor
            if interval == 0:
                raise ValueError
        except ValueError:
            msg.answer("%:", ["Hummm...", "Oops!", "Heh..."],
                             ["This interval is not valid",
                              "There's something wrong with the "
                              "interval you provided"],
                             ["!", "."])
            return None
        return interval
interval = Interval()

class Target(Fragment):
    def __init__(self):
        Fragment.__init__(self)
        self._expr = r"(?:\s+(?:to|for|on|at|in)\s+(?:(?P<_thischannel>this\s+channel)|(?P<_me>me)|(?:user|channel)\s+(?P<_target>\S+))(?:\s+(?:for|on|at|in)\s+(?:(?P<_thisserver>this\s+server)|server\s+(?P<_server>\S+)))?)"
        self._expr_onlyserverallowed = r"((?:\s+(?:to|for|on|at|in)\s+(?:(?P<_thischannel>this\s+channel)|(?P<_me>me)|(?:user|channel)\s+(?P<_target>\S+)))?(?:\s+(?:for|on|at|in)\s+(?:(?P<_thisserver>this\s+server)|server\s+(?P<_server>\S+)))?)"

    def expr(self, optional=0, onlyserverallowed=0):
        if onlyserverallowed:
            expr = self._expr_onlyserverallowed
        else:
            expr = self._expr
        if optional:
            expr += "?"
        return expr

    def get(self, msg, match, allowempty=0):
        target = match.group("_target") or ""
        if not target and match.group("_thischannel"):
            target = msg.answertarget
        server = match.group("_server") or ""
        if not server and match.group("_thischannel"):
            target = msg.answertarget
        if not target and not server and match.group("_me"):
            target = msg.user.nick
            server = msg.server.servername
        elif not allowempty:
            if not target:
                target = msg.answertarget
            if not server:
                server = msg.server.servername
        return target, server
target = Target()

# vim:ts=4:sw=4:et
