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

from pybot import mm, hooks, servers, main, db
from pybot.user import User
from string import join
import re

HELP_CONNECT = """
If you want me to connect to another server, use "connect [to] [server]
<server> [[with|using] servername <servername>]". If you provide a
servername, all commands and configurations will use that servername. This
is useful since IRC servers can change their domains.
""","""
To make me to disconnect or reconnect to a given server, you can use
"(re|dis)connect [to|from] <server> [with <reason>]". If a reason is
given, that will be shown to the users which observe my departure.
Only admins are allowed to work with connections.
"""

HELP_JOIN = """
You can ask me to join in a given channel using "join [channel] <channel>
[[with] keyword <keyword>] [[on|at] [server] <server>]. To make me leave,
use "leave [[channel] <channel> [[on|at] [server] <server>] [with
<reason>]]". If a reason is given, that will be shown to the users which
observe my departure. Only admins can make me join or leave channels.
"""

HELP_SHOW = """
If you want to know in which servers I'm connected to, send me "show
servers" (the "showservers" permission is needed), while if you want to
know which channels I'm currently in, send me "show channels [[at|on]
[server] <server>]" (the "showchannels" permission is necessary).
"""

PERM_SHOWSERVERS = """
Users with the "showservers" permission will be allowed to list the servers
I'm connected to. Check "help show servers" for more information.
"""

PERM_SHOWCHANNELS = """
Users with the "showchannels" permission will be allowed to list the
channels I'm currently in. Check "help show channels" for more information.
"""

HELP_QUIT = """
You can make me quit or reboot with the command "(quit|reboot) [with
<reason>]". If a reason is given, that will be shown to the users which
observe my departure. Only admins are able to tell me to do these actions.
"""

class ServerControl:
    def __init__(self):
        self.registered_server = {}
        hooks.register("Connected", self.connected)
        hooks.register("ConnectionError", self.connectionerror) 
        hooks.register("Registered", self.registered)
        hooks.register("Command", self.command)
        hooks.register("Message", self.message)
        db.table("server", "servername,nick,username,mode,realname")
        db.table("host",  "servername,host")
        db.table("channel", "servername,channel,keyword")

        # connect [to] [server] <server> [[with|using] servername <servername>]
        self.re1 = re.compile(r"connect\s+(?:to\s+)?(?:server\s+)?(?P<server>\S+)(?:(?:\s+with|\s+using)?\s+servername\s+(?P<servername>\S+))?\s*$", re.I)

        # (re|dis)connect [to|from] <server> [with <reason>]
        self.re2 = re.compile(r"(?P<cmd>(?:re|dis)connect)(?:\s+(?:to\s+|from\s+)?(?:server\s+)?(?P<server>\S+))?(?:\s+with\s+(?P<reason>.+))?\s*$", re.I)

        # join [channel] <channel> [[with|using] keyword <keyword>] [[on|at] [server] <server>]
        self.re3 = re.compile(r"join\s+(?:channel\s+)?(?P<channel>\S+)(?:(?:\s+with|\s+using)?\s+keyword\s+(?P<keyword>\S+))?(?:(?:\s+on|\s+at)?(?:\s+server)?\s+(?P<server>\S+))?\s*$", re.I)

        # (leave|part) [[from] [channel] <channel> [[on|at] [server] <server>] [with <reason>]]
        self.re4 = re.compile(r"(?:leave|part)(?:\s+(?:from\s+)?(?:channel\s+)?(?P<channel>\S+)(?:(?:\s+on|\s+at)?(?:\s+server)?\s+(?P<server>\S+))?(?:\s+with\s+(?P<reason>\S+))?)?\s*$", re.I)

        # show servers
        self.re5 = re.compile(r"show\s+servers\s*$", re.I)

        # show channels [[at|on|from|in] [server] <server>]
        self.re6 = re.compile(r"show\s+channels(?:(?:\s+on|\s+at|\s+from)?(?:\s+server)?\s+(?P<server>\S+))?\s*$", re.I)

        # (quit|reboot) [with <reason>]
        self.re7 = re.compile(r"(?P<cmd>quit|reboot)(?:\s+with\s+(?P<reason>.+))?$", re.I)

        # [dis|re]connect
        mm.register_help(r"(?:dis|re)?connect$", HELP_CONNECT,
                         ["connect", "disconnect", "reconnect"])

        # (join|leave|part) [channel[s]]
        mm.register_help(r"(?:join|leave|part)(?:channels?)?", HELP_JOIN,
                         ["join", "leave"])

        # show[ ](channels|servers)
        mm.register_help(r"show\s*(?:channels|servers)$", HELP_SHOW,
                         ["show channels", "show servers"])

        mm.register_perm("showchannels", PERM_SHOWCHANNELS)
        mm.register_perm("showservers", PERM_SHOWSERVERS)

        # (quit|reboot)
        mm.register_help(r"quit|reboot", HELP_QUIT, ["quit", "reboot"])

        self.connect_to_all()

    def unload(self):
        hooks.unregister("Connected", self.connected)
        hooks.unregister("ConnectionError", self.connectionerror) 
        hooks.unregister("Registered", self.registered)
        hooks.unregister("Command", self.command)
        hooks.unregister("Message", self.message)

        mm.unregister_help(HELP_CONNECT)
        mm.unregister_help(HELP_JOIN)
        mm.unregister_help(HELP_SHOW)
        mm.unregister_help(HELP_QUIT)

        mm.unregister_perm("showchannels")
        mm.unregister_perm("showservers")


    def connect_to_all(self):
        # In the future we can pass multiple hosts to the same
        # servername, allowing pybot to try to connect to other
        # hosts, if one of them fail. For now, use only the first.
        scursor = db.cursor()
        hcursor = db.cursor()
        scursor.execute("select * from server")
        for srow in scursor.fetchall():
            hcursor.execute("select * from host where servername=%s",
                            srow.servername)
            hrow = hcursor.fetchone()
            servers.add(hrow.host, srow.servername)

    def connected(self, server):
        cursor = db.cursor()
        cursor.execute("select * from server where servername=%s",
                       server.servername)
        row = cursor.fetchone()
        if not row:
            server.sendcmd("", "QUIT")
            server.kill()
            return
        self.registered_server[server] = 0
        server.sendcmd("", "USER", row.username, row.mode, "0",
                                   ":"+row.realname, priority=10)
        server.sendcmd("", "NICK", row.nick, priority=10)
        server.user.set(row.nick, "", "")
    
    def connectionerror(self, server):
        self.registered_server[server] = 0
    
    def send_join(self, server, channel, keyword):
        if keyword:
            server.sendcmd("", "JOIN", "%s %s" % (channel, keyword),
                           priority=10)
        else:
            server.sendcmd("", "JOIN", channel, priority=10)
    
    def registered(self, server):
        self.registered_server[server] = 1
        cursor = db.cursor()
        cursor.execute("select * from channel where servername=%s",
                       server.servername)
        for row in cursor.fetchall():
            self.send_join(server, row.channel, row.keyword)
    
    def command(self, cmd):
        if cmd.cmd == "001":
            cmd.server.sendcmd("", "WHOIS", cmd.server.user.nick, priority=10)
        elif cmd.cmd == "311" and cmd.server.user.nick == cmd.params[1]:
            cmd.server.user.set(cmd.params[1], cmd.params[2], cmd.params[3])
            hooks.call("Registered", cmd.server)
        elif cmd.cmd == "JOIN":
            if cmd.prefix == cmd.server.user.string:
                hooks.call("Joined", cmd.server, cmd.params[0][1:])
            else:
                user = User()
                user.setstring(cmd.prefix)
                hooks.call("UserJoined", cmd.server, cmd.params[0][1:], user)
        elif cmd.cmd == "PART":
            if cmd.prefix == cmd.server.user.string:
                hooks.call("Parted", cmd.server, cmd.params[0])
            else:
                user = User()
                user.setstring(cmd.prefix)
                if len(cmd.params) > 1:
                    reason = join([cmd.params[1][1:]]+cmd.params[2:])
                else:
                    reason = None
                hooks.call("UserParted",
                           cmd.server, cmd.params[0], user, reason)
        elif cmd.cmd == "QUIT":
            user = User()
            user.setstring(cmd.prefix)
            if len(cmd.params) > 0:
                reason = join([cmd.params[0][1:]]+cmd.params[2:])
            else:
                reason = None
            hooks.call("UserQuitted", cmd.server, user, reason)

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                host = m.group("server")
                servername = m.group("servername") or host
                cursor = db.cursor()
                cursor.execute("select * from server where servername=%s",
                               servername)
                if cursor.rowcount:
                    msg.answer("%:", ["Sorry,", "Oops!", "But,", None],
                               "I'm already connected to this server",
                               [".", "!"])
                else:
                    msg.answer("%:", ["Connecting", "I'm going there", "At your order", "No problems", "Right now", "Ok"], [".", "!"])
                    cursor.execute("insert into server values (%s,%s,%s,%s,%s)",
                                   servername, "pybot", "pybot", "0", "PyBot")
                    cursor.execute("insert into host values (%s,%s)",
                                   servername, host)
                    servers.add(host, servername)
            else:
                msg.answer("%:", [("You're not", ["allowed to connect",
                                                  "that good",
                                                  "allowed to do this"]),
                                  "No", "Nope"], [".", "!"])
            return 0

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                servername = m.group("server")
                reason = m.group("reason")
                if servername:
                    server = servers.get(servername)
                    if not server:
                        msg.answer("%:", ["Sorry,", "Oops!", "But,", None],
                                          "I'm not connected to this server",
                                          [".", "!"])
                        return 0
                else:
                    server = msg.server
                if m.group("cmd") == "reconnect":
                    msg.answer("%:", ["Reconnecting", "At your order",
                                      "No problems", "Right now", "Ok"],
                                     [".", "!"])
                    if reason:
                        server.sendcmd("", "QUIT", ":"+reason)
                    else:
                        server.sendcmd("", "QUIT")
                    server.reconnect()
                else:
                    msg.answer("%:", ["Disconnecting", "At your order",
                                      "No problems", "Right now", "Ok"],
                                     [".", "!"])
                    cursor = db.cursor()
                    cursor.execute("delete from server where servername=%s",
                                   server.servername)
                    cursor.execute("delete from channel where servername=%s",
                                   server.servername)
                    cursor.execute("delete from host where servername=%s",
                                   server.servername)
                    server.sendcmd("", "QUIT")
                    server.kill()
            else:
                msg.answer("%:", [("You're not",
                                   ["allowed to work with servers",
                                    "that good",
                                    "allowed to do this"]),
                                  "No", "Nope"], [".", "!"])
            return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                channel = m.group("channel")
                keyword = m.group("keyword")
                servername = m.group("server")
                if servername:
                    server = servers.get(servername)
                    if not server:
                        msg.answer("%:", ["Sorry,", "Oops!", "Hummm..."],
                                         "I'm not in this server", [".", "!"])
                        return 0
                else:
                    server = msg.server
                cursor = db.cursor()
                cursor.execute("select * from channel where "
                               "servername=%s and channel=%s",
                               server.servername, channel)
                if cursor.rowcount:
                    msg.answer("%:", ["Sorry,", "Oops!",
                                      "It's not necessary.", None],
                                     "I'm already there", [".", "!"])
                else:
                    msg.answer("%:", ["I'm going there", "At your order",
                                      "No problems", "Right now", "Ok",
                                      "Joining"], [".", "!"])
                    if self.registered_server.get(server):
                        self.send_join(server, channel, keyword)
                    cursor.execute("insert into channel values (%s,%s,%s)",
                                   server.servername, channel, keyword)
            else:
                msg.answer("%:", [("You're not", ["allowed to join",
                                                  "that good",
                                                  "allowed to do this"]),
                                                 "No", "Nope"], [".", "!"])
            return 0

        m = self.re4.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                channel = m.group("channel")
                reason = m.group("reason")
                servername = m.group("server")
                if not channel and msg.direct:
                    msg.answer("%:", ["You can't part from here.",
                                      "You can't leave from myself.",
                                      "Leave what!?"])
                    return 0
                if servername:
                    server = servers.get(servername)
                    if not server:
                        msg.answer("%:", ["Sorry,", "Oops!", "Hummm..."],
                                         "I'm not in this server", [".", "!"])
                        return 0
                else:
                    server = msg.server
                cursor = db.cursor()
                cursor.execute("select * from channel where "
                               "servername=%s and channel=%s",
                               server.servername, channel)
                if not cursor.rowcount:
                    msg.answer("%:", ["Sorry,", "Oops!",
                                      "It's not necessary.", None],
                                     "I'm not there", [".", "!"])
                else:
                    msg.answer("%:", ["Ok,", "No problems.", None],
                                     "I'm", ["leaving", "parting"],
                                     [".", "!"])
                    if self.registered_server.get(server):
                        if reason:
                            server.sendcmd("", "PART", channel, ":"+reason,
                                           priority=10)
                        else:
                            server.sendcmd("", "PART", channel, priority=10)
                    cursor.execute("delete from channel where "
                                   "servername=%s and channel=%s",
                                   server.servername, channel)
            else:
                msg.answer("%:", [("You're not", ["allowed to leave",
                                                  "that good",
                                                  "allowed to do this",
                                                  "my lord"]),
                                  "No", "Nope"], [".", "!"])
            return 0

        m = self.re5.match(msg.line)
        if m:
            if mm.hasperm(msg, "showservers"):
                d = {}
                cursor = db.cursor()
                cursor.execute("select * from host")
                for row in cursor.fetchall():
                    d.setdefault(row.servername, []).append(row.host)
                l = []
                if d:
                    for servername, hosts in d.items():
                        if len(hosts) == 1 and servername == hosts[0]:
                            l.append(servername)
                        elif len(hosts) == 1:
                            l.append("%s (host: %s)" % (servername, hosts[0]))
                        else:
                            l.append("%s (hosts: %s)" %
                                     (servername, ", ".join(hosts)))
                    msg.answer("%:", "I'm connected to the following "
                                     "servers:", ", ".join(l))
                else:
                    msg.answer("%:", "I'm not connected to any servers",
                                     [".", "!"])
            else:
                msg.answer("%:", [("You're not", ["allowed to show channels",
                                                  "that good",
                                                  "allowed to do this",
                                                  "my lord"]),
                                  "No", "Nope"], [".", "!"])
            return 0 

        m = self.re6.match(msg.line)
        if m:
            if mm.hasperm(msg, "showchannels"):
                servername = m.group("server")
                cursor = db.cursor()
                if servername:
                    cursor.execute("select servername from server "
                                   "where servername=%s", servername)
                    if not cursor.rowcount:
                        msg.answer("%:", ["You're not connected to that "
                                          "server",
                                          "You're not connected to "
                                          "server %s" % servername],
                                         [".", "!"])
                        return 0
                    servernames = [servername]
                else:
                    cursor.execute("select servername from server")
                    servernames = [x.servername for x in cursor.fetchall()]
                for servername in servernames:
                    cursor.execute("select channel from channel where "
                                   "servername=%s", servername)
                    channels = [x.channel for x in cursor.fetchall()]
                    if channels:
                        msg.answer("%:", "In server %s, I'm in the "
                                         "following channels:" % servername,
                                         ", ".join(channels))
                    else:
                        msg.answer("%:", "In server %s, I'm not "
                                         "connected to any channel."
                                         % servername)
                if not servernames:
                    msg.answer("%:", "You're not connected to any servers",
                                     [".", "!"])
            else:
                msg.answer("%:", [("You're not", ["allowed to show servers",
                                                  "that good",
                                                  "allowed to do this",
                                                  "my lord"]),
                                  "No", "Nope"], [".", "!"])
            return 0

        m = self.re7.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                cmd = m.group("cmd")
                reason = m.group("reason")
                if cmd == "quit":
                    msg.answer("%:", ["I'm leaving", "I'm going home",
                                      "I'll do this", "Right now", "Ok",
                                      "See you"], [".", "!"])
                else:
                    msg.answer("%:", ["Rebooting", "No problems",
                                      "I'll do this", "Right now", "Ok",
                                      "I'll be back in a moment"],
                                     [".", "!"])
                for server in servers.getall():
                    if reason:
                        server.sendcmd("", "QUIT", ":"+reason,
                                       priority=10)
                    else:
                        server.sendcmd("", "QUIT", priority=10)
                if cmd == "quit":
                    main.quit = 1
                else:
                    main.reboot = 1
            else:
                msg.answer("%:", [("You're not", ["that good",
                                                  "allowed to do this",
                                                  "my lord"]),
                                  "No", "Nope"], [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = ServerControl()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4
