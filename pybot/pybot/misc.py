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

from types import StringType, TupleType, ListType, InstanceType
from random import randint
from string import rfind
import re

__all__ = ["buildanswer", "breakline"]

MAXLINESIZE = 400

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
        elif tok:
            tok = str(tok)
            if tok[0] == ":":
                tok = tok[1:]
                if tok[0] == "%":
                    if nick != target:
                        ret.append(":"+nick+tok[1:])
                elif tok[0] == "/":
                    ret.append(":"+nick+tok[1:])
                elif tok[0] == "\\":
                    ret.append(":"+tok[1:])
                else:
                    ret.append(":"+tok)
            else:
                if tok[0] == "%":
                    if nick != target:
                        ret.append(nick+tok[1:])
                elif tok[0] == "/":
                    ret.append(nick+tok[1:])
                elif tok[0] == "\\":
                    ret.append(tok[1:])
                else:
                    ret.append(tok)
    if ret:
        s = ret[0]
        for tok in ret[1:]:
            if tok[0] in [".","!","?",","]:
                s += tok
            else:
                s += " "+tok
    else:
        s = ""
    return s

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

def regexp(*args, **kwargs):
    expr = "".join([str(x) for x in args])
    expr = expr.replace(" *", r"\s*")
    expr = expr.replace(" ?", r"\s*")
    expr = expr.replace(" ", r"\s+")
    if kwargs.get("needpunct"):
        if kwargs.get("question"):
            expr += "[!\s]*\?[!?\s*]*$"
        else:
            expr += "\s*[.!][.!\s]*$"
    else:
        if kwargs.get("question"):
            expr += "[!?.\s]*$"
        elif not kwargs.get("nopunct"):
            expr += "[!.\s]*$"
        else:
            expr += "\s*$"
    return re.compile(expr, re.I)

# vim:ts=4:sw=4:et
