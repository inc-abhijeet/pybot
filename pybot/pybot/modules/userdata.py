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

from pybot import mm, hooks, options, config
import time
import re

HELP_REGISTER = [
("""\
You may register yourself with "register [nick] <password>". After that, \
you can identify yourself with "ident[ify] [nick] <password>". You can \
also configure your nick to be automatically identified with "add identity \
nick!user@host" ('*' is accepted). Be careful since anyone matching \
this identity will have access to your nick's information and permissions.\
""",),
("""\
After using identify, you can make me forget about you using \
"unident[ify]|forget me". This is useful to protect your nick if you can't \
ensure that your IP won't be used by some malicious user before the login \
timeout period.\
""",),
("""\
To change your password, use "set password <newpassword>" (for more \
information on "set" and "add" use "help set"), and to unregister your \
nick, use "unregister [nick] <password>". For more information on the \
"add identity" command, check "help add".\
""",)]

HELP_SET = [
("""\
You can manage information linked to your registered nick (check "help \
register") using the command "(set|add) <type> <value>" and "(unset \
<type>|remove <type> <value>". The 'set' command will set the given \
information type to <value>, while 'add' will append the given value \
to the information type (if accepted).\
""",),
("""\
For example, "add identity *!name@host" will automatically identify \
you when you're logged (you and anyone) with any nick, with name 'name', \
and server 'host', and "remove identity *!name@host" will remove it \
(unset would remove all identities). Another example is the command \
"set email myself@example.com", which will set your email, while \
"unset email" will unset it.\
""",)]

class UserData:
    def __init__(self):
        hooks.register("Message", self.message)
        mm.register("getuserdata", self.mm_getuserdata)
        mm.register("setuserdata", self.mm_setuserdata)
        mm.register("loggednick", self.mm_loggednick)
        mm.register("islogged", self.mm_loggednick)
        mm.register("isregistered", self.mm_isregistered)
        self.data = options.gethard("UserData.data", {})
        self.type = options.getsoft("UserData.type", {})
        self.type["password"] = "str"
        self.type["identity"] = "list"
        self.type["email"] = "str"

        self.login_timeout = config.getint("userdata", "login_timeout")
        self.last_cleanup = 0

        self.logins = options.gethard("UserData.logins", {})

        # ([un]register|ident[ify]) [with] [[nick] <nick> [and]] [password] <passwd>
        self.re1 = re.compile(r"(?P<cmd>(?:un)?register|ident(?:ify)?)\s+(?:with\s+)?(?:(?:nick\s+)?(?P<nick>\S+)\s+(?:and\s+)?)?(?:password\s+)?(?P<passwd>\S+)\s*[!.]?$", re.I)

        # (set|add) <type> <value>
        self.re2 = re.compile(r"(?P<cmd>set|add)\s+(?P<type>\S+)\s+(?P<value>.*?)\s*$", re.I)
    
        # unset <type>|remove <type> <value>
        self.re3 = re.compile(r"unset\s+(?P<type1>\S+)\s*|remove\s+(?P<type2>\S+)\s+(?P<value>.*?)\s*$", re.I)

        # unident[ify]|forget me
        self.re4 = re.compile(r"unident(?:ify)?|forget\s+me", re.I)
    
        # [un]register|identify
        mm.register_help(0, "(?:un)?register|ident(?:ify)?", HELP_REGISTER,
                         "register")

        # set|unset|add|remove
        mm.register_help(0, "set|unset|add|remove", HELP_SET, ["set","unset"])
    
    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister("getuserdata")
        mm.unregister("setuserdata")
        mm.unregister("loggednick")
        mm.unregister("islogged")

        mm.unregister_help(0, HELP_REGISTER)
        mm.unregister_help(0, HELP_SET)

    def logins_add(self, nick, servername, user):
        keypair = (servername, user.string)
        valuepair = (nick, int(time.time()))
        self.logins[keypair] = valuepair

    def logins_maintain(self, msg):
        keypair = (msg.server.servername, msg.user.string)
        valuepair = self.logins.get(keypair)
        curtime = time.time()
        if valuepair:
            nick, lasttime = valuepair
            if lasttime < curtime-self.login_timeout:
                del self.logins[keypair]
            else:
                self.logins[keypair] = (nick, curtime)
        if self.last_cleanup < curtime-self.login_timeout:
            self.last_cleanup = curtime
            self.logins_cleanup()

    def logins_cleanup(self):
        curtime = time.time()
        for keypair in self.logins.keys():
            nick, lasttime = self.logins.get(keypair)
            if lasttime < curtime-self.login_timeout:
                del self.logins[keypair]
    
    def message(self, msg):
        self.logins_maintain(msg)

        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                cmd = m.group("cmd")
                passwd = m.group("passwd")
                nick = m.group("nick") or msg.user.nick
                curpass = self.mm_getuserdata(0, msg.server, nick, "password")
                if cmd == "register":
                    if curpass:
                        msg.answer("%:", ["Oops...", "Sorry!"],
                                         ["Nick", "This nick is"],
                                          "already registered", ["!", "."])
                    else:
                        self.mm_setuserdata(0, msg.server, nick,
                                            "password", passwd)
                        msg.answer("%:", ["Done", "Registered", "Sure",
                                          "No problems"], ["!", "."])
                elif cmd == "unregister":
                    if passwd != curpass:
                        msg.answer("%:", ["Oops...", "Sorry!"],
                                         ["Wrong password",
                                          "This is not your password"],
                                         ["!", "."])
                    else:
                        self.mm_unsetuserdata(0, msg.server, msg.user.nick)
                        msg.answer("%:", ["Done", "Unregistered", "Sure",
                                          "No problems"], ["!", "."])
                else:
                    if passwd != curpass:
                        msg.answer("%:", ["Oops...", "Sorry!"],
                                         ["Wrong password",
                                          "This is not your password"],
                                         ["!", "."])
                    else:
                        msg.answer("%:", ["Welcome back", "Identified",
                                          "Sure", "No problems"],
                                         [".", "!"])
                        self.logins_add(nick, msg.server.servername,
                                              msg.user)
                return 0

            m = self.re2.match(msg.line)
            if m:
                nick = self.mm_loggednick(0, msg.server.servername, msg.user)
                if not nick:
                    msg.answer("%:", ["Identify yourself!",
                                      "Who are you?"])
                    return 0
                type = m.group("type")
                value = m.group("value")
                append = m.group("cmd") != "set"
                datatype = self.type.get(type)
                if not datatype:
                    msg.answer("%:", ["I don't know anything about '%s'!" % type,
                                      "What is '%s'?" % type,
                                      "I've never heard about '%s' before." % type])
                else:
                    self.mm_setuserdata(0, msg.server, nick,
                                        type, value, append=append)
                    msg.answer("%:", ["Done", "Set", "Sure", "Of course",
                                      "Ok", "No problems"], ["!", "."])
                return 0

            m = self.re3.match(msg.line)
            if m:
                nick = self.mm_loggednick(0, msg.server.servername, msg.user)
                if not nick:
                    msg.answer("%:", ["Identify yourself!",
                                      "Who are you?"])
                    return 0
                type = m.group("type1") or m.group("type2")
                value = m.group("value")
                if type == "password":
                    msg.answer("%:", ["Cannot unset password",
                                      "Not for passwords",
                                      "Oops.. no", "Heh"], [".", "!"])
                else:
                    self.mm_unsetuserdata(0, msg.server, nick, type, value)
                    msg.answer("%:", ["Done", "Unset", "Sure", "Of course",
                                      "Ok", "No problems"], ["!", "."])
                return 0

            m = self.re4.match(msg.line)
            if m:
                nick = self.mm_loggednick(0, msg.server.servername, msg.user)
                if not nick:
                    msg.answer("%:", ["I don't even know who you are!",
                                      "What are you talking about?"])
                else:
                    del self.logins[(msg.server.servername, msg.user.string)]
                    msg.answer("%:", ["Done", "Just forgot", "Sure",
                                      "Right now", "Ok", "No problems"],
                                     ["!", "."])
                return 0

    def mm_loggednick(self, defret, servername, user):
        valuepair = self.logins.get((servername, user.string))
        if valuepair:
            nick, lasttime = valuepair
            if lasttime > time.time()-self.login_timeout:
                return nick
        for pair in self.data:
            if pair[0] == servername:
                for ident in self.data[pair].get("identity", []):
                    if user.matchstr(ident):
                        nick = pair[1]
                        self.logins_add(nick, servername, user)
                        return nick
        return None

    def mm_isregistered(self, defret, servername, nick):
        return bool(self.data.get((servername, nick)))
    
    def mm_getuserdata(self, defret, server, nick, name):
        data = self.data.get((server.servername, nick))
        if data:
            return data.get(name)
        return None
    
    def mm_setuserdata(self, defret, server, nick, name, value, append=0):
        tuple = (server.servername, nick)
        data = self.data.setdefault(tuple, {})
        type = self.type.get(name)
        if type:
            if type == "list":
                if append and data.get(name):
                    data[name].append(value)
                else:
                    data[name] = [value]
            else:
                data[name] = value

    def mm_unsetuserdata(self, defret, server, nick,
                         name=None, value=None, append=0):
        tuple = (server.servername, nick)
        if name is None:
            try:
                del self.data[tuple]
            except KeyError:
                pass
        else:
            data = self.data.setdefault(tuple, {})
            if value is None:
                try:
                    del data[name]
                except KeyError:
                    pass
                if not data:
                    del self.data[tuple]
            else:
                if self.type.get(name) == "list":
                    try:
                        data[name].remove(value)
                    except ValueError:
                        pass

def __loadmodule__(bot):
    global mod
    mod = UserData()

def __unloadmodule__(bot):
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
