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

from errno import EINPROGRESS, EALREADY, EWOULDBLOCK
from thread import allocate_lock, start_new_thread
from select import select
from string import split
from time import time, sleep
import socket

from pybot.misc import buildanswer, breakline
from pybot.command import Command
from pybot.user import User
import pybot

CONNECTDELAY = 30

class Servers:
    def __init__(self):
        self.servers = []

    def add(self, host, servername=None):
        self.servers.append(Server(host, servername))
    
    def add_console(self):
        self.servers.append(ConsoleServer())

    def remove(self, servername):
        for i in range(len(self.servers)):
            if server[i].servername == servername:
                del server[i]
    
    def get(self, servername):
        for server in self.servers:
            if server.servername == servername:
                return server

    def getall(self):
        return self.servers

class BaseServer:
    def __init__(self, host, servername=None):
        if not servername:
            self.servername = host
        else:
            self.servername = servername
        self.host = host
        self.killed = 0
        self._inlines = []
        self.user = User()

    def interaction(self):
        pass

    def changeserver(self, host, servername):
        pass

    def kill(self):
        pass
    
    def reconnect(self):
        pass

    def sendcmd(self, prefix, cmd, *params, **kw):
        pass

    def sendmsg(self, target, nick, *params, **kw):
        pass

    def readline(self):
        """Return one line from the buffer (and remove it).

        This method is not thread safe, since it must be called only
        by the main loop.
        """
        line = None
        if len(self._inlines) > 0:
            line = self._inlines[0]
            del self._inlines[0]
        return line

class Server(BaseServer):
    def __init__(self, host, servername=None):
        BaseServer.__init__(self, host, servername)

        self.changeserver(host, servername)
        self._inbuffer = ""
        self._outlines = []
        self._outlines_lock = allocate_lock()
        self._last_sent = 0
        self._last_sent_timeout = 0;
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(0)
        self._timeout = 0
        self._connect = 1
        self._reconnect = 0
        self._connected = 0
    
    def interaction(self):
        if not self._connected:
            if self._timeout:
                self._timeout = self._timeout-1
            elif self._connect:
                try:
                    self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._socket.connect((self._host, self._port))
                except socket.error, why:
                    if not why[0] in (EINPROGRESS, EALREADY, EWOULDBLOCK):
                        self._timeout = CONNECTDELAY
                        pybot.hooks.call("ConnectingError", self)
                        self._disconnect()
                        return
                self._connected = 1
                pybot.hooks.call("Connected", self)
        else:
            try:
                selret = select([self._socket],[self._socket],[],10)
            except:
                self._disconnect()
                self._timeout = CONNECTDELAY
                pybot.hooks.call("ConnectionError", self)
                return
            if len(selret[0]) != 0:
                try:
                    recv = self._socket.recv(4096)
                except socket.error, why:
                    self._disconnect()
                    self._timeout = CONNECTDELAY
                    pybot.hooks.call("ConnectionError", self)
                    return
                if recv:
                    self._inbuffer = self._inbuffer + recv
                    lines = split(self._inbuffer, "\r\n")
                    if len(lines) > 0:
                            self._inbuffer = lines[-1]
                            self._inlines = self._inlines + lines[:-1]
                else:
                    self._disconnect()
                    self._timeout = CONNECTDELAY
                    pybot.hooks.call("ConnectionError", self)
                    return
            if len(selret[1]) != 0:
                try:
                    self._outlines_lock.acquire()
                    try:
                        lines_sent = 0
                        while lines_sent < 3 and self._outlines and (self._outlines[0][1] <= 20 or self._last_sent < time()):
                            # Disabled for now.
                            #if self._last_sent+1 < time():
                            #    self._last_sent_timeout = 1
                            #elif self._last_sent_timeout < 2 and self._outlines[0][1] > 20:
                            #        self._last_sent_timeout = self._last_sent_timeout+1
                            self._last_sent = time()+self._last_sent_timeout;
                            line = self._outlines[0][0]+"\r\n"
                            del self._outlines[0]
                            self._socket.send(line)
                            lines_sent = lines_sent + 1
                    finally:
                        self._outlines_lock.release()
                except socket.error, why:
                    if why[0] != EWOULDBLOCK:
                        self._disconnect()
                        self._timeout = CONNECTDELAY
                        pybot.hooks.call("ConnectionError", self)
            if self.killed:
                self._disconnect()
                pybot.hooks.call("Disconnected", (self))
            elif self._reconnect:
                self._reconnect = 0
                self._disconnect()

    def changeserver(self, host, servername=None):
        if not servername:
            self.servername = host
        self.host = host
        tokens = split(host,":")
        self._host = tokens[0]
        if len(tokens) == 2:
            self._port = int(tokens[1])
        else:
            self._port = 6667

    def _disconnect(self):
        try:
            self._socket.shutdown()
            self._socket.close()
        except:
            pass
        self._connected = 0
        self._outlines = []

    def kill(self):
        self._connect = 0
        self.killed = 1
    
    def reconnect(self):
        if self._connected:
            self._reconnect = 1
            self._timeout = CONNECTDELAY

    def sendline(self, line, priority=50, outhooks=1):
        """Send one line for the server.

        This method is thread safe.
        """
        self._outlines_lock.acquire()
        l = len(self._outlines)
        i = 0
        while i < l:
            if self._outlines[i][1] > priority:
                self._outlines.insert(i,(line,priority))
                self._outlines_lock.release()
                return
            i = i + 1
        self._outlines.append((line,priority))
        self._outlines_lock.release()

        if outhooks:
            msg = Command()
            msg.setline(self, line)
            msg.user = self.user
            hookname = ["OutMessage", "OutNotice", "OutCommand", "OutCTCP",
                        "OutCTCPReply"][msg._index]
            pybot.hooks.call(hookname, msg)

    def sendcmd(self, prefix, cmd, *params, **kw):
        priority = kw.get("priority", 50)
        outhooks = kw.get("outhooks", 1)
        if prefix:
            lineprefix = ":"+prefix+" "+cmd+" "
        else:
            lineprefix = cmd+" "
        line = buildanswer(params, None, self.user.nick)
        for subline in breakline(line):
            subline = lineprefix+subline
            self.sendline(subline, priority, outhooks)

    def sendmsg(self, target, nick, *params, **kw):
        priority = kw.get("priority", 50)
        outhooks = kw.get("outhooks", 1)
        ctcp = kw.get("ctcp")
        cmd = kw.get("notice") and "NOTICE" or "PRIVMSG"
        if ctcp:
            linemask = "%s %s :\01%s %%s \01"%(cmd, target, ctcp)
        else:
            linemask = "%s %s :%%s"%(cmd, target)
        line = buildanswer(params, target, nick)
        for subline in breakline(line):
            subline = linemask%subline
            self.sendline(subline, priority, outhooks)

from cmd import Cmd

class ConsoleServer(BaseServer, Cmd):
    def __init__(self):
        BaseServer.__init__(self, "console")
        self.user.set("pybot", "pybot", "console")

        Cmd.__init__(self)
        self.prompt = "pybot> "
        start_new_thread(self.cmdloop, ())
        del Cmd.do_help
        
        self._outlines = []
        self._outlines_lock = allocate_lock()

    def sendcmd(self, prefix, cmd, *params, **kw):
        outline = "[CMD] %s %s" % \
                  (cmd, buildanswer(params, None, self.user.nick))
        self._outlines_lock.acquire()
        self._outlines.append(outline)
        self._outlines_lock.release()

    def sendmsg(self, target, nick, *params, **kw):
        outline = "[MSG] %s" % buildanswer(params, target, nick)
        self._outlines_lock.acquire()
        self._outlines.append(outline)
        self._outlines_lock.release()

    def show_lines(self):
        self._outlines_lock.acquire()
        for line in self._outlines:
            print line
        self._outlines = []
        self._outlines_lock.release()

    def default(self, line):
        if line == "EOF":
            print
            return 1
        inline = ":master!master@console PRIVMSG pybot :%s" % line
        self._inlines.append(inline)
        sleep(0.5)
        self.show_lines()

    def emptyline(self):
        self.show_lines()

    def postloop(self):
        pybot.main.quit = 1

# vim:ts=4:sw=4:et
