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

from pybot import mm, hooks, db
import string
import time
import re

HELP = """
You can store shared notes about some specific topic using "[add] note
[about] <topic>: <note>". Topics and notes can optionally contain spaces.
To remove one or more notes, use "del note[s] about <topic> [: <num> ...]".
If you want to know which topics are available, or show all notes about
some topic, use "[show] note[s] [about] <topic>". You need the "notes"
permission to work with notes.
"""

PERM_NOTES = """
The "notes" permission allows users to work with notes. For more information
check "help notes".
"""

SPLITNUMS = re.compile("\s*,\s*|\s+")

class Notes:
    def __init__(self):
        db.table("note", "topic,note,timestamp")
        hooks.register("Message", self.message)
        mm.register("getnotes", self.mm_getnotes)
        mm.register("addnote", self.mm_addnote)
        mm.register("delnotes", self.mm_delnotes)
        mm.register("shownotes", self.mm_shownotes)
        mm.register("getnotetopics", self.mm_getnotetopics)

        # [add|new|create|include] note [about] <topic>: <note>
        self.re1 = re.compile(r"(?:add\s+|new\s+|create\s+|include\s+)?note(?:\s+about)?\s+(?P<topic>[^:]+):\s*(?P<note>.+)$", re.I)
    
        # [del|delete|remove] note[s] [about] <topic> [: <num> [, ...]]
        self.re2 = re.compile(r"(?:del|delete|remove)\s+notes?(?:\s+about)?\s+(?P<topic>[^:]+)(?:\s*:\s*(?P<nums>.+))?\s*$", re.I)
        
        # [show] note[s] [[about] <topic> [?]]
        self.re3 = re.compile(r"(?:show\s+)?notes?(?:(?:\s+about)?\s+(?P<topic>[^?]+))?\s*\?*$", re.I)

        # note[s]
        mm.register_help(r"notes?$", HELP, "notes")

        mm.register_perm("notes", PERM_NOTES)

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister("getnotes")
        mm.unregister("addnote")
        mm.unregister("delnotes")
        mm.unregister("shownotes")
        mm.unregister("getnotetopics")

        mm.unregister_help(HELP)
        mm.unregister_perm("notes")
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "notes"):
                topic = m.group("topic").strip()
                note = m.group("note").strip()
                self.mm_addnote(topic, note)
                msg.answer("%:", "Note", ["created", "included", "added"], ["!", "."])
            else:
                msg.answer("%:", ["You don't have permission for that",
                                  "You can't create notes",
                                  "You're note allowed to add notes"],
                                 [".", "!"])
            return 0
        
        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "notes"):
                topic = m.group("topic").strip()
                nums = m.group("nums")
                if nums:
                    try:
                        notenums = [int(x) for x in SPLITNUMS.split(nums) if x]
                    except ValueError:
                        msg.answer("%:", "Invalid numbers", [".", "!"])
                        return 0
                else:
                    notenums = []
                if self.mm_delnotes(topic, notenums):
                    msg.answer("%:", ["Done", "Removed", "Deleted"], [".", "!"])
                else:
                    msg.answer("%:", ["Sorry!", None],
                                     ["There are no", "No",
                                      "I haven't found"],
                                     "notes about this", [".", "!"])
            else:
                msg.answer("%:", ["You don't have permission for that",
                                  "You can't remove notes",
                                  "You're note allowed to add notes"],
                                 [".", "!"])
            return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(msg, "notes"):
                topic = m.group("topic")
                if topic:
                    if msg.direct:
                        target = msg.user.nick
                    else:
                        target = msg.target
                    if not self.mm_shownotes(msg.server, target,
                                             msg.user.nick, topic):
                        msg.answer("%:", ["Sorry!", None],
                                         ["There are no", "No",
                                          "I haven't found"],
                                         "notes about this", [".", "!"])
                else:
                    topics = self.mm_getnotetopics()
                    for i in range(len(topics)):
                        if "," in topics[i]:
                            topics[i] = "'%s'" % topics[i]
                    msg.answer("%:", "The following note topics are "
                                     "available:", ", ".join(topics))
            else:
                msg.answer("%:", ["You don't have permission for that",
                                  "You can't show notes",
                                  "You're note allowed to add notes"],
                                 [".", "!"])
            return 0
 
    def mm_getnotes(self, topic):
        cursor = db.cursor()
        cursor.execute("select * from note where topic=%s order by timestamp",
                       topic)
        return [x.note for x in cursor.fetchall()]

    def mm_addnote(self, topic, note):
        cursor = db.cursor()
        cursor.execute("insert into note values (%s,%s,%s)",
                       topic, note, int(time.time()))
    
    def mm_delnotes(self, topic, notenums):
        cursor = db.cursor()
        removed = 0
        if notenums:
            notes = self.mm_getnotes(topic)
            for num in notenums:
                cursor.execute("delete from note where topic=%s and note=%s",
                               topic, notes[num])
                removed |= cursor.rowcount
        else:
            cursor.execute("delete from note where topic=%s", topic)
            removed = cursor.rowcount
        return bool(removed)
    
    def mm_shownotes(self, server, target, nick, topic):
        notes = self.mm_getnotes(topic)
        n = 0
        if notes:
            server.sendmsg(target, nick, "%:", "Notes about %s:" % topic)
            for note in notes:
                server.sendmsg(target, nick, "%:", "(%d)"%n, note)
                n = n+1
            return 1

    def mm_getnotetopics(self):
        cursor = db.cursor()
        cursor.execute("select distinct topic from note order by topic")
        return [x.topic for x in cursor.fetchall()]

def __loadmodule__():
    global mod
    mod = Notes()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
