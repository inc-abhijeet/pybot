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

from pybot.locals import *
from pybot.util import feedparser
from pybot.misc import striphtml
import thread
import time

HELP = """
You can ask me to show RSS news from any site and for any user/channel
and server with "[dont] show (rss|news) [from] <url> [[in] one line]
[with link[s]] [with desc[ription][s]] [with prefix "<prefix>"]
[each <n>(m|h)] [(on|for) (user|channel) <target>] [(on|at) server
<server>]". Notice that the given interval is the maximum interval.
""","""
To check what is being shown and for which targets, you can send me
"show rss". You need the "rss" permission to use these commands.
"""

PERM_RSS = """
The "rss" permission allows you to change what servers and
channels will receive RSS news. Check "help rss" for
more information.
"""

# Fetching below 30 minutes is evil, but some active services will
# make pybot flood the channel with more than 10 minutes.
MININTERVAL = 10*60
DEFINTERVAL = 30*60

# Maximum number of stored news from each feed
CACHELIMIT = 50

# Maxium news to send from a single feed per minute
ONETIMELIMIT = 5

class RSS:
    def __init__(self):
        db.table("rssfeed", "id integer primary key, "
                            "url unique on conflict ignore, "
                            "lastfetch",
                 triggers=[
                   "create trigger rssfeed1 after delete on rssfeed"
                   " begin"
                   "  delete from rsstarget where feedid=old.id;"
                   "  delete from rssitem where feedid=old.id;"
                   " end"
                 ])
        db.table("rsstarget", "id integer primary key, "
                              "feedid, servername, target, flags, "
                              "prefix, interval, lastitemid",
                 constraints="unique (feedid, servername, target)",
                 triggers=[
                   "create trigger rsstarget1 after delete on rsstarget"
                   " begin"
                   "  delete from rssfeed where id=old.feedid and"
                      " (select count(feedid) from rsstarget where feedid=old.feedid)==0;"
                   " end"
                 ])
        db.table("rssitem", "id integer primary key, feedid, timestamp, "
                            "title, link, description",
                 constraints="unique (feedid, title, link, description)"
                             " on conflict ignore")

        hooks.register("Message", self.message)

        # (rss|news|rss news)
        mm.register_help("news|rss|rss news", HELP, ["rss", "news"])

        mm.register_perm("rss", PERM_RSS)

        mm.hooktimer(60, self.update, ())

        # [dont] show (rss|news|rss news) [from] <url> [[in] one line] [with link[s]] [with desc[ription][s]] [with prefix "<prefix>"] [each <n>(m|h)] [[on|at|in|for] (user|channel) <target>] [[on|at|in|for] server <server>]
        self.re1 = regexp(refrag.dont(optional=1),
                          r"show (?:rss |news |rss news )(?:from )?(?P<url>(?:https?|ftp)\S+)"
                          r"(?P<oneline> (?:in )?one line)?"
                          r"(?P<links> with links?)?"
                          r"(?P<descs> with desc(?:ription)?s?)?"
                          r"(?: with prefix \"(?P<prefix>.*?)\")?",
                          refrag.interval(optional=1),
                          refrag.target(optional=1))

        # show rss [settings]
        self.re2 = regexp(r"show rss")

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unhooktimer(60, self.update, ())
        mm.unregister_help(HELP)
        mm.unregister_perm("rss")

    def update(self):
        cursor = db.cursor()

        # Check if we must fetch something
        cursor.execute("select * from rssfeed")        
        now = int(time.time())
        for feed in cursor.fetchall():
            lastfetch = int(feed.lastfetch)
            if now-lastfetch >= MININTERVAL:
                # Clear old news
                cursor.execute("delete from rssitem where feedid=%s and "
                               "id not in (select id from rssitem "
                                          "where feedid=%s "
                                          "order by id desc limit %s)",
                               (feed.id, feed.id, CACHELIMIT))
                cursor.execute("select min(interval) from rsstarget where "
                               "feedid=%s", (feed.id,))
                row = cursor.fetchone()
                if row: # Should always be true
                    interval = int(row[0])
                    if now-lastfetch >= interval:
                        cursor.execute("update rssfeed set lastfetch=%s "
                                       "where id=%s", (now, feed.id))
                        thread.start_new_thread(self.fetch_news, (feed, now))
                        # Try not to fetch more than one at the same time
                        break
        
        # Now check if we must show something
        cursor.execute("select * from rsstarget")
        for target in cursor.fetchall():
            cursor.execute("select * from rssitem where "
                           "id > %s and feedid=%s order by id limit %s",
                           (target.lastitemid, target.feedid, ONETIMELIMIT))
            if cursor.rowcount:
                server = servers.get(target.servername)
                lastid = None
                if "1" in target.flags:
                    oneline = 1
                    fulltext = ""
                else:
                    oneline = 0
                for item in cursor.fetchall():
                    text = item.title
                    if "l" in target.flags and item.link:
                        text += " [%s]" % item.link
                    if "d" in target.flags and item["description"]:
                        # item.description() is a method
                        text += " - "+item["description"]
                    if oneline:
                        if fulltext:
                            fulltext = "%s; %s" % (fulltext, text)
                        else:
                            fulltext = text
                    else:
                        server.sendmsg(target.target, None,
                                       target.prefix, text, notice=1)
                    lastid = item.id
                if oneline:
                    server.sendmsg(target.target, None,
                                   target.prefix, fulltext, notice=1)
                if lastid: # Should always be true
                    cursor.execute("update rsstarget set lastitemid=%s "
                                   "where id=%s", (lastid, target.id,))

    def fetch_news(self, feed, now):
        news = feedparser.parse(feed.url)
        items = news["items"]
        if items:
            # Reverse, since top items are usually newer
            items.reverse()
            localdb = db.copy() # We're in a thread
            cursor = localdb.cursor()
            for item in items:
                if "title" in item:
                    title = striphtml(item["title"].strip())
                    link = striphtml(item.get("link", "").strip())
                    desc = striphtml(item.get("description", "").strip())
                    cursor.execute("insert into rssitem values "
                                   "(NULL, %s, %s, %s, %s, %s)",
                                   (feed.id, now, title, link, desc))

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "rss"):
                dont = refrag.dont.get(msg, m)
                target, servername = refrag.target.get(msg, m)
                interval = refrag.interval.get(msg, m,
                                               default="%ds" % DEFINTERVAL)
                if interval < MININTERVAL:
                    msg.answer("%:", "That's below the minimum interval",
                                     [".", "!"])
                    return 0
                url = m.group("url")
                prefix = m.group("prefix") or ""
                flags = ""
                if m.group("links"):
                    flags += "l"
                if m.group("descs"):
                    flags += "d"
                if m.group("oneline"):
                    flags += "1"
                cursor = db.cursor()
                if dont:
                    cursor.execute("delete from rsstarget where "
                                   "feedid=(select id from rssfeed where url=%s) "
                                   "and servername=%s and target=%s",
                                   (url, servername, target))
                    if not cursor.rowcount:
                        msg.answer("%:", ["Not needed",
                                          "It's not needed",
                                          "Oops"], [".", "!"],
                                         ["I don't know anything about this"
                                          " news feed",
                                          "This feed is not being shown"
                                          " anywhere",
                                          "I'm not showing news from that"
                                          " feed"],
                                         [".", "!"])
                    else:
                        msg.answer("%:", ["Done", "Ok", "Sure"], [".", "!"])
                else:
                    cursor.execute("insert into rssfeed values (NULL, %s, 0)",
                                   (url,))
                    cursor.execute("select id from rssfeed where url=%s",
                                   (url,))
                    feedid = cursor.fetchone().id
                    try:
                        cursor.execute("insert into rsstarget values "
                                       "(NULL, %s, %s, %s, %s, %s, %s, "
                                       " ifnull("
                                       "  (select max(id) from rssitem where "
                                       "   feedid=%s), -1)"
                                       ")",
                                       (feedid, servername, target, flags,
                                        prefix, interval, feedid))
                    except db.error:
                        msg.answer("%:", ["Not needed", "It's not needed",
                                          "Oops"], [".", "!"],
                                         ["I'm already showing that feed",
                                          "This feed is already being shown",
                                          "I'm already showing news from that"
                                          " feed"], [".", "!"])
                    else:
                        msg.answer("%:", ["Done", "Ok", "Sure"], [".", "!"])
            else:
                msg.answer("%:", ["You can't", "You're not allowed to",
                                  "You're not good enough to"],
                                 ["do this",
                                  "change rss settings"], [".", "!"])
            return 0

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "rss"):
                cursor = db.cursor()
                cursor.execute("select * from rssfeed")
                if not cursor.rowcount:
                    msg.answer("%:", ["No rss feeds are being shown",
                                      "There are no rss feeds being shown",
                                      "No feeds registered"],
                                      [".", "!"])
                    return 0
                msg.answer("%:", "The following feeds are being shown:")
                for feed in cursor.fetchall():
                    msg.answer("-", feed.url)
                    cursor.execute("select * from rsstarget where feedid=%s",
                                   (feed.id,))
                    for target in cursor.fetchall():
                        oneline, links, descs, prefix = ("",)*4
                        if "1" in target.flags:
                            oneline = "in one line"
                        if "l" in target.flags:
                            links = "with links"
                        if "d" in target.flags:
                            descs = "with descriptions"
                        if target.prefix:
                            prefix = "with prefix \"%s\"" % target.prefix
                        target.interval = int(target.interval)
                        if target.interval % (60*60) == 0:
                            i = target.interval/(60*60)
                            s = (i > 0) and "s" or ""
                            interval = "%d hour%s" % (i, s)
                        elif target.interval % 60 == 0:
                            interval = "%d minutes" % (target.interval/60)
                        else:
                            interval = "%d seconds" % target.interval
                        msg.answer("  for", target.target, "on",
                                   target.servername, "each", interval,
                                   oneline, links, descs, prefix)
            else:
                msg.answer("%:", ["You can't", "You're not allowed to",
                                  "You're not good enough to"],
                                 ["do this",
                                  "change rss settings"], ["!", "."])
            return 0

def __loadmodule__():
    global mod
    mod = RSS()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
