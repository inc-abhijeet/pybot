# Copyright (c) 2000-2005 Gustavo Niemeyer <niemeyer@conectiva.com>
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

from pybot.locals import *
import thread, time
import urllib
import re
import os

HELP = """
You can ask me to load information from remote URLs using
"load remote info [from] <url> [each <n>(s|m|h)] [[with] regex <regex>]"
and to unload or reload using "(re|un)load remote info [from] <url>". To
check what is being remotely loaded, use "show remote[ ]info[s]". To
load and unload remote infos you must be an admin, and to show and reload
you need the "remoteinfoadmin" permission. 
""","""
After you setup some URL for remote loading, you must say explicitly
which users/channels and servers will be able to obtain information from
it. To do that give the permission "remoteinfo(<url>)" for these you
want to allow. The default reload interval is 10 minutes. To understand
how to build the regex for the remote info command or how to build the
remote information check "help remote info syntax".
"""

HELP_SYNTAX = """
Loading remote information consists in reading a remote URL, splitting
that information in lines, checking each line against a regular
expression, and including the matching lines as items in a database for
further processing. Each of these items will have a "trigger", which is
also a regular expression, a corresponding "msg" which will be sent when
the trigger is activated, and some "flags" which configure the item.
""","""
Even though you may provide your own regular expression that is checked
against each item line, the default one is similar to the following:
"(<(?P<flags>.*?)>)? (?P<trigger>.*?) => (?P<msg>.*)". It means that you
could use in the given URL lines like "Does it work\? => Yes! it does!",
or with flags and groups like "<g> Hi (?P<someone>.*) => /me says hi
to %(someone)s as well.".
""","""
Messages may start with /me or /notice to have the expected meanings.
The current supported flags are: 'a' to disable the inclusion of the
user nick at the start of the line on channel messages; 'g' to check
even channel messages not targeted to myself; and 's' which makes the
trigger case sensitive.
"""

PERM_REMOTEINFO = """
Users with the "remoteinfo(<url>)" permission will be able to use
knowledge acquired from the given url. Check "help remoteinfo" for
more information.
"""

PERM_REMOTEINFOADMIN = """
Users with the "remoteinfoadmin" permission can ask me to reload
information from remote URLs, and to show which URLs are being loaded.
"""

DEFAULTREGEX = "\s*(?:<(?P<flags>[^>]*)>\s*)?(?P<trigger>.*?)\s*=>\s*(?P<msg>.*)"
DEFAULTINTERVAL = "10m"

class Info:
    def __init__(self):
        self.lasttime = 0
        self.patterns = {}

    def __repr__(self):
        return "<Info: %s>" % `self.patterns`

class RemoteInfo:
    def __init__(self):
        db.table("remoteinfo", "url text unique, regex text, interval text")
        self.info = options.get("RemoteInfo.info", {})
        self.info_lock = options.get("RemoteInfo.info_lock", {})
        self.lock = thread.allocate_lock()
        hooks.register("Message", self.message)
        hooks.register("Message", self.message_remoteinfo, priority=1000)
        hooks.register("CTCP", self.message_remoteinfo, priority=1000)

        # load remote[ ]info [from] <url> [each <n>[ ](s[econds]|m[inutes]|h[ours])] [[with|using] regex <regex>]
        self.re1 = regexp(r"load remote *info (?:from )?(?P<url>\S+)(?: each (?P<interval>[0-9]+) *(?P<intervalunit>se?c?o?n?d?s?|mi?n?u?t?e?s?|ho?u?r?s?))?(?: (?:with |using )?regex (?P<regex>.*))?")

        # (un|re)load remote[ ]info [from] <url>
        self.re2 = regexp(r"(?P<cmd>un|re)load remote *info (?:from )?(?P<url>\S+)")

        # show remote[ ]info[s]
        self.re3 = regexp(r"show remote *infos?")

        # remote[ ]info
        mm.register_help("remote *info?", HELP, "remoteinfo")
        mm.register_help("remote *infos? *syntax", HELP_SYNTAX,
                         "remoteinfo syntax")

        mm.register_perm("remoteinfo", PERM_REMOTEINFO)
        mm.register_perm("remoteinfoadmin", PERM_REMOTEINFOADMIN)

        mm.hooktimer(30, self.reload_all, ())

        if not self.info:
            self.reload_all()

    def unload(self):
        mm.unhooktimer(30, self.reload_all, ())
        hooks.unregister("Message", self.message)
        hooks.unregister("Message", self.message_remoteinfo, priority=1000)
        hooks.unregister("CTCP", self.message_remoteinfo, priority=1000)
        mm.unregister_help(HELP)
        mm.unregister_help(HELP_SYNTAX)
        mm.unregister_perm("remoteinfo")
        mm.unregister_perm("remoteinfoadmin")

    def lock_url(self, url):
        self.lock.acquire()
        try:
            lock = self.info_lock[url]
        except KeyError:
            lock = thread.allocate_lock()
            self.info_lock[url] = lock
        self.lock.release()
        return lock.acquire(0)

    def unlock_url(self, url):
        try:
            lock = self.info_lock[url].release()
        except KeyError:
            pass

    def reload_all(self):
        now = time.time()
        for row in db.execute("select * from remoteinfo"):
            info = self.info.get(row.url)
            if not info or now-info.lasttime > int(row.interval):
                self.reload(row.url, row.regex)

    def reload(self, url, regex=None):
        if not regex:
            db.execute("select regex from remoteinfo where url=?", url)
            row = db.fetchone()
            if not row: return
            regex = row.regex
        if self.lock_url(url):
            thread.start_new_thread(self._reload, (url, regex))

    def _reload(self, url, regex):
        try:
            try:
                infourl = urllib.urlopen(url)
            except:
                import traceback
                traceback.print_exc()
            else:
                info = Info()
                p = re.compile(regex)
                for line in infourl.read().splitlines():
                    m = p.match(line)
                    if m:
                        try:
                            trigger = m.group("trigger")
                            msg = m.group("msg")
                            flags = m.group("flags") or ""
                        except IndexError:
                            continue
                        if not trigger or not msg:
                            continue
                        trigger = trigger.strip()
                        if trigger[-1] != "$":
                            trigger += "$"
                        msg = msg.strip()
                        flags = flags.strip()
                        try:
                            if 's' in flags:
                                trigger_re = re.compile(trigger)
                            else:
                                trigger_re = re.compile(trigger, re.I)
                        except re.error:
                            continue
                        info.patterns[trigger_re] = (flags, msg)
                infourl.close()
                info.lasttime = time.time()
                self.info[url] = info
        finally:
            self.unlock_url(url)

    def message_remoteinfo(self, msg):
        ret = None
        allowed = mm.permparams(msg, "remoteinfo")
        for url, info in self.info.items():
            if url not in allowed:
                continue
            for p in info.patterns:
                flags, infomsg = info.patterns[p]
                if not ('g' in flags or msg.forme):
                    continue
                if msg.ctcp and (msg.ctcp != "ACTION" or 'c' not in flags):
                    continue
                m = p.match(msg.line)
                if m:
                    try:
                        infomsg %= m.groupdict()
                    except KeyError:
                        continue
                    ctcp = None
                    notice = 0
                    withnick = ("a" not in flags)
                    if infomsg.startswith("/me "):
                        withnick = 0
                        infomsg = infomsg[4:]
                        ctcp = "ACTION"
                    elif infomsg.startswith("/notice "):
                        withnick = 0
                        infomsg = infomsg[8:]
                        notice = 1
                    if withnick:
                        msg.answer("%:", infomsg, ctcp=ctcp, notice=notice)
                    else:
                        msg.answer(infomsg, ctcp=ctcp, notice=notice)
                    ret = 0
        return ret

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                url = m.group("url")
                regex = (m.group("regex") or DEFAULTREGEX).strip()
                interval = m.group("interval")
                if not interval:
                    interval = DEFAULTINTERVAL[:-1]
                    unit = DEFAULTINTERVAL[-1]
                else:
                    unit = m.group("intervalunit")[0]
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
                    return 0
                try:
                    m = re.compile(regex)
                except re.error:
                    msg.answer("%:", ["Hummm...", "Oops!", "Heh..."],
                                     ["This regex is not valid",
                                      "There's something wrong with the "
                                      "regex you provided"],
                                     ["!", "."])
                    return 0

                try:
                    db.execute("insert into remoteinfo values "
                               "(null,?,?,?)", url, regex, interval)
                except db.error:
                    msg.answer("%:", ["I can't do that.", "Nope.", None],
                                     ["I'm already loading that url",
                                      "Can't insert repeated urls",
                                      "This url is already in my database"],
                                     [".", "!"])
                else:
                    msg.answer("%:", ["Loading",
                                      "No problems",
                                      "Starting right now",
                                      "Sure"],
                                     [".", "!"])
                    self.reload(url, regex)
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to change remote info options",
                                    "that good",
                                    "allowed to do this"]),
                                  "Nope"], [".", "!"])
            return 0
        
        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "remoteinfoadmin"):
                cmd = m.group("cmd")
                url = m.group("url")
                db.execute("select null from remoteinfo where url=?", url)
                if not db.results:
                    msg.answer("%:", ["I can't do that.", "Nope.", None],
                                     ["I'm not loading that url",
                                      "This url is not in my database"],
                                     [".", "!"])
                elif cmd == "un":
                        if not self.lock_url(url):
                            msg.answer("%:", "Can't do that now. URL is "
                                             "being loaded in this exact "
                                             "moment. Try again in a few "
                                             "seconds.")
                        else:
                            if url in self.info:
                                del self.info[url]
                            if url in self.info_lock:
                                del self.info_lock[url]
                            # Unlocking is not really necessary, but
                            # politically right. ;-)
                            self.unlock_url(url)
                            db.execute("delete from remoteinfo where url=?",
                                       url)
                            msg.answer("%:", ["Done", "Of course", "Ready"],
                                             [".", "!"])
                else:
                    msg.answer("%:", ["Will do that",
                                      "In a moment",
                                      "Will be ready in a moment",
                                      "Starting right now"], [".", "!"])
                    self.reload(url)
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to touch remote infos",
                                    "that good",
                                    "allowed to do this"]),
                                  "Nope"], [".", "!"])
            return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(msg, "remoteinfoadmin"):
                db.execute("select * from remoteinfo")
                if db.results:
                    msg.answer("%:", "The following remote info urls are "
                                     "being loaded:")
                    for row in db:
                        interval = int(row.interval)
                        if interval % 3600 == 0:
                            interval /= 3600
                            unit = "hour"
                        elif interval % 60 == 0:
                            interval /= 60
                            unit = "minute"
                        else:
                            unit = "second"
                        if interval > 1:
                            unit += "s"
                        regex = row.regex
                        if regex and regex[0] == "\\":
                            regex = "\\"+regex
                        msg.answer("-", row.url, "each", str(interval), unit,
                                   "with regex", regex)
                else:
                    msg.answer("%:", "No remote info urls are currently "
                                     "being loaded", [".", "!"])
            else:
                msg.answer("%:", "You're not",
                                 ["allowed to show remote infos",
                                  "that good",
                                  "allowed to do this"], [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = RemoteInfo()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
