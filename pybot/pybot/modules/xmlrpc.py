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

from pybot import hooks, mm, rm, servers, db
from SimpleXMLRPCServer import SimpleXMLRPCServer
from types import StringType
import xmlrpclib
import traceback
import re

HELP = """
The xmlrpc service is based on method names and permissions. If you
want to allow a given user to run a method, first you must create
a xmlrpc user for him, with "(add|create) xmlrpc user <username>
with pass[word] <password>".
""","""
Then, you can give or remove permissions for that user with
"[don't|do not] allow xmlrpc (func[tion]|method) <func> [(to|for) user
<xmlrpcuser>] [(to|for|on|at) [user|channel] <target>] [[and] [on|at]
server <server>]".
""","""
To remove a given xmlrpc user, just use "(del[ete]|remove) xmlrpc
user <user>". You must be an admin to change xmlrpc settings.
"""

class XmlRpcObject:
    def __init__(self, funcs, hasperm):
        self._funcs = funcs
        self._hasperm = hasperm

    def _dispatch(self, name, args):
        func = self._funcs.get(name)
        if not func:
            return xmlrpclib.Fault(2, "no such method")
        auth = args[0]
        if type(auth) is not dict:
            return xmlrpclib.Fault(1, "invalid authorization")
        try:
            if self._hasperm(name, auth):
                ret = func(*args)
                if ret is None:
                    ret = 0
                return ret
            else:
                return xmlrpclib.Fault(3, "method not allowed")
        except:
            traceback.print_exc()
            return xmlrpclib.Fault(4, "pybot error")
    
class XmlRpc:
    def __init__(self):
        db.table("xmlrpcuser", "username,password")
        db.table("xmlrpcperm", "username,method,servername,target")
        
        self.server = SimpleXMLRPCServer(("0.0.0.0", 8460))
        self.server.socket.setblocking(0)
        
        xro = XmlRpcObject(rm.get_methods(), self.hasperm)
        self.server.register_instance(xro)
        
        rm.register("sendmsg", self.rm_sendmsg)

        hooks.register("Message", self.message)
        hooks.register("Loop", self.loop)

        # (add|create) xmlrpc user <user> with [pass|password] <passwd> [!.]
        self.re1 = re.compile(r"(?:add|create)\s+xmlrpc\s+user\s+(?P<user>\S+)\s+with\s+(?:password|pass)\s+(?P<passwd>\S+)\s*[.!]*$")

        # (del|delete|remove) xmlrpc user <user>
        self.re2 = re.compile(r"(?:del|delete|remove)\s+xmlrpc\s+user\s+(?P<user>\S+)\s*[.!]*$")

        # [don[']t|do not] allow xmlrpc (func[tion]|method) <method> [(to|for) user <user>] [(to|for|on|at) [user|channel] <target>] [[and] [on|at] server <server>]
        self.re3 = re.compile(r"(?P<dont>don'?t\s+|do not\s+)?allow\s+xmlrpc\s+(?:func(?:tion)?|method)\s+(?P<method>\S+)(?:\s+(?:to\s+|for\s+)user\s+(?P<user>\S+))?(?:\s+(?:to|for|on|at)\s+(?:user\s+|channel\s+)?(?P<target>\S+))?(?:\s+(?:and\s+)?(?:on\s+|at\s+)?server\s+(?P<server>\S+))?\s*[.!]*$")
    
        # xmlrpc
        mm.register_help("xmlrpc", HELP, "xmlrpc")
        
    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("Loop", self.loop)
        self.server.server_close()
        rm.unregister("sendmsg")
        mm.unregister_help(HELP)
    
    def loop(self):
        self.server.handle_request()

    def user_add(self, username, password):
        cursor = db.cursor()
        cursor.execute("select * from xmlrpcuser where username=%s",
                       username)
        if not cursor.rowcount:
            cursor.execute("insert into xmlrpcuser values (%s,%s)",
                           username, password)
            return 1
        return 0

    def user_del(self, username):
        cursor = db.cursor()
        cursor.execute("delete from xmlrpcuser where username=%s",
                       username)
        return bool(cursor.rowcount)

    def perm_add(self, username, method, servername, target):
        if self.perm_del(username, method, servername, target, check=1):
            return 0
        cursor = db.cursor()
        cursor.execute("insert into xmlrpcperm values (%s,%s,%s,%s)",
                       username, method, servername, target)
        return 1

    def perm_del(self, username, method, servername, target, check=0):
        where = ["username=%s", "method=%s"]
        wargs = [username, method]
        if servername:
            where.append("servername=%s")
            wargs.append(servername)
        else:
            where.append("servername isnull")
        if target:
            where.append("target=%s")
            wargs.append(target)
        else:
            where.append("target isnull")
        wstr = " and ".join(where)
        cursor = db.cursor()
        if not check:
            cursor.execute("delete from xmlrpcperm where "+wstr, *wargs)
        else:
            cursor.execute("select * from xmlrpcperm where "+wstr, *wargs)
        return bool(cursor.rowcount)

    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                if self.user_add(m.group("user"), m.group("passwd")):
                    msg.answer("%:", ["User added", "Ok", "User created",
                                      "Done"], [".", "!"])
                else:
                    msg.answer("%:", ["I can't do this!", "Sorry!"],
                                     ["This user already exists",
                                      "This user is already registered"],
                                     [".", "!"])
            else:
                msg.answer("%:", ["Sorry, you", "You"],
                                 ["can't add xmlrpc users.",
                                  "don't have this power."])
            return 0
        
        m = self.re2.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                if self.del_user(m.group("user")):
                    msg.answer("%:", ["User removed", "No problems",
                                      "User deleted", "Done"], [".", "!"])
                else:
                    msg.answer("%:", ["Oops!", "Sorry!"],
                                     ["There's no such user",
                                      "I haven't found this user"],
                                     [".", "!"])
            else:
                msg.answer("%:", ["Sorry, you", "You"],
                                 ["can't add xmlrpc users.",
                                  "don't have this power."])
            return 0

        m = self.re3.match(msg.line)
        if m:
            if mm.hasperm(msg, "admin"):
                if m.group("dont"):
                    if self.perm_del(m.group("user"), m.group("method"),
                                     m.group("server"), m.group("target")):
                        msg.answer("%:", ["Ok", "No problems",
                                          "Right now",
                                          "Permission removed"],
                                         [".", "!"])
                    else:
                        msg.answer("%:", ["Sorry!", "Oops!",
                                          "Can't do this!"],
                                         ["Nobody has this permission",
                                          "This permission doesn't exist"],
                                         [".", "!"])
                else:
                    if self.perm_add(m.group("user"), m.group("method"),
                                     m.group("server"), m.group("target")):
                        msg.answer("%:", ["Ok", "No problems",
                                          "Right now"], [".", "!"])
                    else:
                        msg.answer("%:", ["Oops!", "It's not necessary!",
                                          "I don't have to!"],
                                         "This permission already exists",
                                         [".", "!"])
            else:
                msg.answer("%:", ["Sorry, you", "You"],
                                 ["can't work with xmlrpc permissions.",
                                  "don't have this power."])
            return 0
 
    def hasperm(self, method, auth):
        username = auth.get("username")
        password = auth.get("password")
        server = auth.get("server")
        target = auth.get("target")
        cursor = db.cursor()
        cursor.execute("select * from xmlrpcperm "
                       "natural left join xmlrpcuser where "
                       "xmlrpcuser.username=%s and password=%s and "
                       "(servername isnull or servername=%s) and "
                       "(target isnull or target=%s)",
                       username, password, server, target)
        if cursor.rowcount:
            return 1
        return 0
    
    def rm_sendmsg(self, auth, msg, notice=0, ctcp=None):
        server = servers.get(auth["server"])
        if server:
            if type(msg) == StringType:
                server.sendmsg(auth["target"], None, msg, notice=notice, ctcp=ctcp)
            else:
                server.sendmsg(auth["target"], None, notice=notice, ctcp=ctcp, *msg)

def __loadmodule__():
    global mod
    mod = XmlRpc()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
