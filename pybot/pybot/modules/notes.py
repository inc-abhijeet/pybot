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

from pybot import mm, hooks, options
import string

class Notes:
    def __init__(self, bot):
        self.notes = options.gethard("Notes.notes", {})
        hooks.register("Message", self.message)
        mm.register("getnotes", self.mm_getnotes)
        mm.register("addnotes", self.mm_addnotes)
        mm.register("delnotes", self.mm_delnotes)
        mm.register("shownotes", self.mm_shownotes)
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister("getnotes")
        mm.unregister("addnotes")
        mm.unregister("delnotes")
        mm.unregister("shownotes")
    
    def message(self, msg):
        var = []
        if msg.match(var, 2, "%", ["add", "new", "create", "include", None], "note", ["about", None], 0, "^.*:$", 1, "|>"):
            note = string.join(msg.rawmsg[msg.msg.index(var[0])+2:])
            self.mm_addnotes(None, var[0][:-1], [note])
            msg.answer("%:", "Note", ["created", "included", "added"], ["!", "."])
            return 0
        elif msg.match(var, 2, "%", ["del", "delete", "remove"], ["note", "notes"], [(["about", None], 0, "^.*:", 1, "|>"), (1, "|1>", "about", 0, "~", ["!", ".", None])]):
            if var[0][-1] == ":":
                var[0] = var[0][:-1]
            notenums = string.split(string.join(var[1]), ",")
            n = 0
            while n < len(notenums):
                try:
                    notenums[n] = int(notenums[n])
                    n = n+1
                except:
                    del notenums[n]
            self.mm_delnotes(None, var[0], notenums)
            msg.answer("%:", ["Done", "Removed", "Deleted"], ["!", "."])
            return 0
        elif msg.match(var, 1, "%", ["show", None], "notes", ["about", None], 0, "~", ["?", None]):
            if msg.direct:
                target = msg.user.nick
            else:
                target = msg.target
            if not self.mm_shownotes(None, msg.server, target, msg.user.nick, var[0]):
                msg.answer("%:", ["Sorry!", None], ["There are no", "No", "I haven't found"], "notes about this", ["!", "."])
            return 0
                    
    def mm_getnotes(self, defret, str):
        return self.notes.get(str) or []

    def mm_addnotes(self, defret, str, notes):
        self.notes.setdefault(str, []).extend(notes)
    
    def mm_delnotes(self, defret, str, notenums):
        notenums = notenums[:]
        notenums.sort()
        notenums.reverse()
        notes = self.notes.get(str)
        if notes:
            for n in notenums:
                if len(notes) > n:
                    del notes[n]
            if not notes:
                del self.notes[str]
    
    def mm_shownotes(self, defret, server, target, nick, str):
        notes = self.mm_getnotes(None, str)
        n = 0
        if notes:
            server.sendmsg(target, nick, "%:", "Notes about %s:"%str)
            for note in notes:
                server.sendmsg(target, nick, "%:", "(%d)"%n, note)
                n = n+1
            return 1

def __loadmodule__(bot):
    global notes
    notes = Notes(bot)

def __unloadmodule__(bot):
    global notes
    notes.unload()
    del notes

# vim:ts=4:sw=4:et
