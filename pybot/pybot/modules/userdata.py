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

from pybot import mm, hooks, options, config, db
import time
import re

HELP_REGISTER = """
You may register yourself with "register [nick] <password>". After that,
you can identify yourself with "ident[ify] [nick] <password>". You can
also configure your nick to be automatically identified with "add identity
nick!user@host" ('*' is accepted). Be careful since anyone matching
this identity will have access to your nick's information and permissions.
""","""
After using identify, you can make me forget about you using
"unident[ify]|forget me". This is useful to protect your nick if you can't
ensure that your IP won't be used by some malicious user before the login
timeout period.
""","""
To change your password, use "set password <newpassword>" (for more
information on "set" and "add" use "help set"), and to unregister your
nick, use "unregister [nick] <password>". For more information on the
"add identity" command, check "help add".
""","""
You need the "userdata" permission to work with user data.
"""

HELP_SET = """
You can manage information linked to your registered nick (check "help
register") using the command "(set|add) <type> <value>" and "(unset
<type>|remove <type> <value>". The 'set' command will set the given
information type to <value>, while 'add' will append the given value
to the information type (if accepted).
""","""
For example, "add identity *!name@host" will automatically identify
you when you're logged (you and anyone) with any nick, with name 'name',
and server 'host', and "remove identity *!name@host" will remove it
(unset would remove all identities). Another example is the command
"set email myself@example.com", which will set your email, while
"unset email" will unset it.
""","""
You need the "userdata" permission to work with user data.
"""

PERM_USERDATA = """
The "userdata" permission allows users to register and set personal
information. Check "help register" and "help set" for more information.
"""

class UserData:
    def __init__(self):
        # Use a lower priority, since we use some
        # regexes which are very generic here.
        hooks.register("Message", self.message, priority=600)
        db.table("userdata", "servername,nick,type,value")
        db.table("login", "servername,userstr,lasttime,nick")
        mm.register("getuserdata", self.mm_getuserdata)
        mm.register("setuserdata", self.mm_setuserdata)
        mm.register("unsetuserdata", self.mm_unsetuserdata)
        mm.register("loggednick", self.mm_loggednick)
        mm.register("islogged", self.mm_loggednick)
        self.type = options.get("UserData.type", {})
        self.type["password"] = "str"
        self.type["identity"] = "list"
        self.type["email"] = "str"

        self.login_timeout = config.getint("userdata", "login_timeout")
        self.last_cleanup = 0

        # ([un]register|ident[ify]) [with] [[nick] <nick> [and]] [password] <passwd>
        self.re1 = re.compile(r"(?P<cmd>(?:un)?register|ident(?:ify)?)\s+(?:with\s+)?(?:(?:nick\s+)?(?P<nick>\S+)\s+(?:and\s+)?)?(?:password\s+)?(?P<passwd>\S+)\s*[!.]?$", re.I)

        # (set|add) <type> <value>
        self.re2 = re.compile(r"(?P<cmd>set|add)\s+(?P<type>\S+)\s+(?P<value>.+?)\s*$", re.I)
    
        # unset <type>|remove <type> <value>
        self.re3 = re.compile(r"unset\s+(?P<type1>\S+)\s*|remove\s+(?P<type2>\S+)\s+(?P<value>.+?)\s*$", re.I)

        # unident[ify]|forget me
        self.re4 = re.compile(r"unident(?:ify)?|forget\s+me", re.I)
    
        # [un]register|identify
        mm.register_help("(?:un)?register|ident(?:ify)?", HELP_REGISTER,
                         "register")

        # set|unset|add|remove
        mm.register_help("set|unset|add|remove", HELP_SET, ["set","unset"])

        mm.register_perm("userdata", PERM_USERDATA)
    
    def unload(self):
        hooks.unregister("Message", self.message, priority=600)
        mm.unregister("getuserdata")
        mm.unregister("setuserdata")
        mm.unregister("unsetuserdata")
        mm.unregister("loggednick")
        mm.unregister("islogged")

        mm.unregister_help(HELP_REGISTER)
        mm.unregister_help(HELP_SET)

        mm.unregister_perm(PERM_USERDATA)

    def login(self, servername, userstr, nick):
        curtime = int(time.time())
        cursor = db.cursor()
        cursor.execute("update login set lasttime=%s where "
                       "servername=%s and userstr=%s and nick=%s",
                       curtime, servername, userstr, nick)
        if not cursor.rowcount:
            cursor.execute("delete from login where "
                           "servername=%s and userstr=%s",
                           servername, userstr)
            cursor.execute("insert into login values (%s,%s,%s,%s)",
                           servername, userstr, curtime, nick)

    def logout(self, servername, userstr):
        cursor = db.cursor()
        cursor.execute("delete from login where "
                       "servername=%s and userstr=%s",
                       servername, userstr)

    def login_update(self, msg):
        curtime = int(time.time())
        cursor = db.cursor()
        cursor.execute("update login set lasttime=%s where "
                       "servername=%s and userstr=%s",
                       curtime, msg.server.servername, msg.user.string)
        if self.last_cleanup < curtime-self.login_timeout:
            self.last_cleanup = curtime
            self.login_cleanup()

    def login_cleanup(self):
        cursor = db.cursor()
        cursor.execute("delete from login where lasttime < %s",
                       int(time.time())-self.login_timeout)
    
    def message(self, msg):
        self.login_update(msg)

        # Check if it's already answered, since we use some
        # regexes which are very generic here.
        if not msg.forme or msg.answered:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "userdata"):
                cmd = m.group("cmd")
                passwd = m.group("passwd")
                nick = m.group("nick") or msg.user.nick
                curpass = mm.getuserdata(msg.server.servername, nick,
                                         "password", single=1)
                if cmd == "register":
                    if curpass:
                        msg.answer("%:", ["Oops...", "Sorry!"],
                                         ["Nick", "This nick is"],
                                          "already registered", ["!", "."])
                    else:
                        mm.setuserdata(msg.server.servername, nick,
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
                        mm.unsetuserdata(msg.server.servername, nick)
                        msg.answer("%:", ["Done", "Unregistered", "Sure",
                                          "No problems"], ["!", "."])
                else:
                    if not curpass:
                        msg.answer("%:", ["I don't know anything about "
                                          "that nick.",
                                          "No information about that nick!",
                                          "Are you sure this is the right "
                                          "nick?"])
                    elif passwd != curpass:
                        msg.answer("%:", ["Oops...", "Sorry!"],
                                         ["Wrong password",
                                          "This is not your password"],
                                         ["!", "."])
                    else:
                        msg.answer("%:", ["Welcome back", "Identified",
                                          "Sure", "No problems"],
                                         [".", "!"])
                        self.login(msg.server.servername,
                                   msg.user.string, nick)
            else:
                msg.answer("%:", ["Oops.", "Sorry.", "Hummm..", None],
                                 "You're not allowed to change user data",
                                 [".", "!"])
            return 0

        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "userdata"):
                type = m.group("type")
                typetype = self.type.get(type)
                if not typetype:
                    return None
                nick = mm.loggednick(msg.server.servername, msg.user)
                if not nick:
                    msg.answer("%:", ["Identify yourself!",
                                      "Who are you?"])
                    return 0
                value = m.group("value")
                append = m.group("cmd") != "set"
                mm.setuserdata(msg.server.servername, nick,
                               type, value, append=append)
                msg.answer("%:", ["Done", "Set", "Sure", "Of course",
                                  "Ok", "No problems"], ["!", "."])
            else:
                msg.answer("%:", ["Oops.", "Sorry.", "Hummm..", None],
                                 "You're not allowed to change user data",
                                 [".", "!"])
            return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(msg, "userdata"):
                nick = mm.loggednick(msg.server.servername, msg.user)
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
                    mm.unsetuserdata(msg.server.servername, nick, type, value)
                    msg.answer("%:", ["Done", "Unset", "Sure", "Of course",
                                      "Ok", "No problems"], ["!", "."])
            else:
                msg.answer("%:", ["Oops.", "Sorry.", "Hummm..", None],
                                 "You're not allowed to change user data",
                                 [".", "!"])
            return 0

        m = self.re4.match(msg.line)
        if m:
            if mm.hasperm(msg, "userdata"):
                nick = mm.loggednick(msg.server.servername, msg.user)
                if not nick:
                    msg.answer("%:", ["I don't even know who you are!",
                                      "What are you talking about?"])
                else:
                    self.logout(msg.server.servername, msg.user.string)
                    msg.answer("%:", ["Done", "Just forgot", "Sure",
                                      "Right now", "Ok", "No problems"],
                                     ["!", "."])
            else:
                msg.answer("%:", ["Oops.", "Sorry.", "Hummm..", None],
                                 "You're not allowed to change user data",
                                 [".", "!"])
            return 0

    def mm_loggednick(self, servername, user):
        cursor = db.cursor()
        cursor.execute("select * from login where "
                       "servername=%s and userstr=%s and lasttime > %s",
                       servername, user.string,
                       time.time()-self.login_timeout)
        if cursor.rowcount:
            return cursor.fetchone().nick
        cursor.execute("select * from userdata where "
                       "servername=%s and type='identity'",
                       servername)
        for row in cursor.fetchall():
            if user.matchstr(row.value):
                self.login(servername, user.string, row.nick)
                return row.nick
        return None

    def mm_getuserdata(self, servername, nick, type, single=0):
        cursor = db.cursor()
        cursor.execute("select value from userdata where "
                       "servername=%s and nick=%s and type=%s",
                       servername, nick, type)
        values = [x.value for x in cursor.fetchall()]
        if single:
            if values:
                return values[0]
            else:
                return None
        return values 

    def mm_setuserdata(self, servername, nick, type, value, append=0):
        typetype = self.type.get(type)
        if typetype:
            if typetype != "list" or not append:
                self.mm_unsetuserdata(servername, nick, type)
            cursor = db.cursor()
            cursor.execute("insert into userdata values (%s,%s,%s,%s)",
                           servername, nick, type, value)

    def mm_unsetuserdata(self, servername, nick,
                         type=None, value=None, append=0):
        where = ["servername=%s", "nick=%s"]
        wargs = [servername, nick]
        cursor = db.cursor()
        if type is not None:
            where.append("type=%s")
            wargs.append(type)
            if value is not None:
                where.append("value=%s")
                wargs.append(value)
        else:
            cursor.execute("delete from login where "
                           "servername=%s and nick=%s",
                           servername, nick)
        wstr = " and ".join(where)
        cursor.execute("delete from userdata where "+wstr, *wargs)

def __loadmodule__():
    global mod
    mod = UserData()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
