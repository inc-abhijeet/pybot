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

from pybot import mm, hooks, servers, config, db
import urllib
import thread
import string
import re

HELP = """
You may tell me which channels/users I have to notify of freshmeat news
with "[don't] show freshmeat news [(on|to) [channel|user] <target> [on
server <server>]]". The "freshmeat" permission is necessary to change
these settings.
"""

PERM_FRESHMEAT = """
The "freshmeat" permission allows you to change what servers and
channels will receive freshmeat news. Check "help freshmeat" for
more information.
"""

class Freshmeat:
    def __init__(self):
        if config.has_option("global", "http_proxy"):
            self.proxy = config.get("global", "http_proxy")
        else:
            self.proxy = None
        self.url = config.get("freshmeat", "url")
        self.interval = config.getint("freshmeat", "interval")

        db.table("freshmeat", "servername,target")

        self.fetch_lock = thread.allocate_lock()

        hooks.register("Message", self.message)

        mm.hooktimer(self.interval*60, self.checknews, ())
        
        # [don[']t|do not] show freshmeat news [(to|on|at|for) [channel|user] <target> [[on|at] server <server>]]
        self.re1 = re.compile(r"(?P<dont>don'?t\s+|do\s+not\s+)?show\s+freshmeat\s+news(?:\s+(?:to|on|at|for)(?:\s+channel|\s+user)?\s+(?P<target>\S+)(?:(?:\s+on|\s+at)?\s+server\s+(?P<server>\S+?))?)?\s*[!.]*$", re.I)
        
        # freshmeat [news]
        mm.register_help("freshmeat(?:\s+news)?", HELP, "freshmeat")

        mm.register_perm("freshmeat", PERM_FRESHMEAT)

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unhooktimer(self.interval*60, self.checknews, ())
        mm.unregister_help(HELP)
        mm.unregister_perm("freshmeat")

    def shownews(self, newslist):
        first = 1
        newsmsg = ""
        for news in newslist:
            if not first:
                newsmsg = newsmsg+", "
            else:
                first = 0
            newsmsg = newsmsg+news[0]
        cursor = db.cursor()
        cursor.execute("select * from freshmeat")
        for row in cursor.fetchall():
            server = servers.get(row.servername)
            if server:
                server.sendmsg(row.target, None,  "Freshmeat news:",
                               newsmsg, notice=1)
    
    def fetchnews(self):
        urlopener = urllib.URLopener()
        if self.proxy:
            proxy = {"http": self.proxy}
            urlopener.proxies.update(proxy)
        try:
            url = urlopener.open(self.url)
        except:
            pass
        else:
            newslist = []
            # We're in a thread. Get our own database object.
            localdb = db.copy()
            last = localdb["freshmeat.last"]
            while 1:
                news_name = string.rstrip(url.readline())
                news_time = string.rstrip(url.readline())
                news_url = string.rstrip(url.readline())
                defstr = ' (Default)'
                defstrlen = len(defstr)
                if news_name[-defstrlen:] == defstr:
                    news_name = news_name[:-defstrlen]
                news_tuple = (news_name, news_time, news_url)
                if not (news_name and news_time and news_url) or str(news_tuple) == last:
                    break
                newslist.append(news_tuple)
            url.close()
            if newslist:
                localdb["freshmeat.last"] = str(newslist[0])
                newslist.reverse()
                self.shownews(newslist)
        self.fetch_lock.release()
    
    def checknews(self):
        cursor = db.cursor()
        cursor.execute("select * from freshmeat")
        if cursor.rowcount and self.fetch_lock.acquire(0):
            thread.start_new_thread(self.fetchnews, ())
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "freshmeat"):
                target = m.group("target") or msg.target
                servername = m.group("server") or msg.server.servername
                cursor = db.cursor()
                if not m.group("dont"):
                    cursor.execute("select * from freshmeat where "
                                   "servername=%s and target=%s",
                                   servername, target)
                    if cursor.rowcount:
                        msg.answer("%:", ["Oops!", "Sorry!", "Nope."],
                                         "I'm already showing news for "
                                         "this target", ["!", "."])
                    else:
                        cursor.execute("insert into freshmeat values (%s,%s)",
                                       servername, target)
                        msg.answer("%:", ["Sure", "I'll show",
                                          "Of course"], ["!", "."])
                else:
                    cursor.execute("delete from freshmeat where "
                                   "servername=%s and target=%s",
                                   servername, target)
                    if not cursor.rowcount:
                        msg.answer("%:", ["Oops!", "Sorry!", "Nope."],
                                         "I'm not showing news for "
                                         "this target", ["!", "."])
                    else:
                        msg.answer("%:", ["Sure", "I won't show",
                                          "Of course"], ["!", "."])
            else:
                msg.answer("%:", ["You can't", "You're not allowed to",
                                  "You're not good enough to"],
                                 ["do this",
                                  "change freshmeat settings"], ["!", "."])
            return 0
    
def __loadmodule__():
    global mod
    mod = Freshmeat()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
