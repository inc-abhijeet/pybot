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

from types import StringType, TupleType, ListType, InstanceType
from random import randint
from string import rfind

__all__ = ["buildanswer", "breakline"]

MAXLINESIZE = 250

def buildanswer(pattern, target=None, nick=None):
    ret = []
    for tok in pattern:
        if type(tok) == TupleType:
            recret = buildanswer(tok, target, nick)
            ret = ret + recret
        elif type(tok) == ListType or type(tok) == InstanceType:
            tmptok = tok[randint(0,len(tok)-1)]
            if type(tmptok) == StringType:
                # Avoid using string as a list. This must be fixed
                # to handle '%...' strings.
                ret.append(tmptok)
            elif tmptok != None:
                recret = buildanswer(tmptok, target, nick)
                ret.append(recret)
        elif tok[0] == ":":
            tok = tok[1:]
            if tok[0] == "%":
                if nick != target:
                    ret.append(":"+nick+tok[1:])
            elif tok[0] == "/":
                ret.append(":"+nick+tok[1:])
            elif tok[0] == "\\":
                ret.append(":"+tok[1:])
            elif tok != None:
                ret.append(":"+tok)
        else:
            if tok[0] == "%":
                if nick != target:
                    ret.append(nick+tok[1:])
            elif tok[0] == "/":
                ret.append(nick+tok[1:])
            elif tok[0] == "\\":
                ret.append(tok[1:])
            elif tok != None:
                ret.append(tok)
    if ret:
        str = ret[0]
        for tok in ret[1:]:
            if tok[0] in [".","!","?",","]:
                str = str+tok
            else:
                str = str+" "+tok
    else:
        str = ""
    return str

def breakline(line):
    lenline = len(line)
    sublines = []
    startpos = 0
    endpos = MAXLINESIZE
    while 1:
        if endpos > lenline:
            sublines.append(line[startpos:])
            return sublines
        pos = rfind(line, " ", startpos, endpos)
        if pos != -1:
            endpos = pos
        sublines.append(line[startpos:endpos])
        startpos = endpos
        endpos = startpos+MAXLINESIZE

# vim:ts=4:sw=4:et
