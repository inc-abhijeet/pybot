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

from pybot import mm, hooks, options, servers, config
import urllib
import thread
import string
import re

HELP = [
("""\
You may tell me which channels/users I have to notify of freshmeat news \
with "[don't] show freshmeat news [(on|to) [channel|user] <target> [on \
server <server>]]".\
""",)]

class Freshmeat:
    def __init__(self, bot):
        self.url = config.get("freshmeat", "url")
        if config.has_option("freshmeat", "proxy"):
            self.proxy = config.get("freshmeat", "proxy")
        else:
            self.proxy = None
        self.interval = config.getint("freshmeat", "interval")
        self.newslast = options.gethard("Freshmeat.newslast", [None])
        self.newstargets = options.gethard("Freshmeat.newstargets", [])
        self.newstargets_lock = thread.allocate_lock()
        self.fetch_lock = thread.allocate_lock()
        hooks.register("Message", self.message)
        mm.hooktimer(0, self.interval*60, self.checknews, ())
        
        # Match '[don[']t|do not] show freshmeat news [(to|on|at|for) [channel|user] <target> [[on|at] server <server>]] [!|.]'
        self.re1 = re.compile(r"(?P<dont>don'?t\s+|do\s+not\s+)?show\s+freshmeat\s+news(?:\s+(?:to|on|at|for)(?:\s+channel|\s+user)?\s+(?P<target>\S+)(?:(?:\s+on|\s+at)?\s+server\s+(?P<server>\S+?))?)?\s*[!.]*$", re.I)
        
        # freshmeat [news]
        mm.register_help(0, "freshmeat(?:\s+news)?", HELP, "freshmeat")

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unhooktimer(0, self.interval*60, self.checknews, ())
    
        mm.unregister_help(0, HELP)

    def shownews(self, newslist):
        first = 1
        newsmsg = ""
        for news in newslist:
            if not first:
                newsmsg = newsmsg+", "
            else:
                first = 0
            newsmsg = newsmsg+news[0]
        self.newstargets_lock.acquire()
        for target in self.newstargets:
            server = servers.get(target[0])
            if server:
                server.sendmsg(target[1], None,  "Freshmeat news:", newsmsg, notice=1)
        self.newstargets_lock.release()
    
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
            while 1:
                news_name = string.rstrip(url.readline())
                news_time = string.rstrip(url.readline())
                news_url = string.rstrip(url.readline())
                defstr = ' (Default)'
                defstrlen = len(defstr)
                if news_name[-defstrlen:] == defstr:
                    news_name = news_name[:-defstrlen]
                news_tuple = (news_name, news_time, news_url)
                if not (news_name and news_time and news_url) or news_tuple == self.newslast[0]:
                    break
                newslist.append(news_tuple)
            url.close()
            if newslist:
                self.newslast[0] = newslist[0]
                newslist.reverse()
                self.shownews(newslist)
        self.fetch_lock.release()
    
    def checknews(self):
        if self.newstargets and self.fetch_lock.acquire(0):
            thread.start_new_thread(self.fetchnews, ())
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "freshmeatnews"):
                    target = m.group("target") or msg.target
                    servername = m.group("server") or msg.server.servername
                    tuple = (servername, target)
                    if not m.group("dont"):
                        try:
                            self.newstargets.index(tuple)
                        except ValueError:
                            self.newstargets.append(tuple)
                            msg.answer("%:", ["Sure", "I'll show", "Of course"], ["!", ", sir!"])
                        else:
                            msg.answer("%:", ["Oops!", "Sorry!", "Nope."], "I'm already showing news for this target", ["!", "."])
                    else:
                        self.newstargets_lock.acquire()
                        try:
                            self.newstargets.remove(tuple)
                        except ValueError:
                            msg.answer("%:", ["Oops!", "Sorry!", "Nope."], "I'm not showing news for this target", ["!", "."])
                        else:
                            msg.answer("%:", ["Sure", "I won't show", "Of course"], ["!", "."])
                        self.newstargets_lock.release()
                else:
                    msg.answer("%:", ["You can't", "You're not allowed to", "You're not good enough to"], ["do this", "You can't change freshmeat news settings"], ["!", "."])
                return 0
    
def __loadmodule__(bot):
    global freshmeat
    freshmeat = Freshmeat(bot)

def __unloadmodule__(bot):
    global freshmeat
    freshmeat.unload()
    del freshmeat

# vim:ts=4:sw=4:et
