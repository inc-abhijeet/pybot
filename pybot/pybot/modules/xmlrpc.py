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
from SimpleXMLRPCServer import SimpleXMLRPCServer
from types import StringType
import xmlrpclib
import traceback

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
        db.table("xmlrpcuser", "username, password text")
        db.table("xmlrpcperm", "username, method text, servername text, "
                               "target text")
        
        self.server = SimpleXMLRPCServer(("0.0.0.0", 8460))
        self.server.socket.setblocking(0)
        
        xro = XmlRpcObject(rm.get_methods(), self.hasperm)
        self.server.register_instance(xro)
        
        rm.register("sendmsg", self.rm_sendmsg)

        hooks.register("Message", self.message)
        hooks.register("Loop", self.loop)

        # (add|create) xmlrpc user <user> with [pass|password] <passwd> [!.]
        self.re1 = regexp(r"(?:add|create) xmlrpc user (?P<user>\S+) with (?:password|pass) (?P<passwd>\S+)")

        # (del|delete|remove) xmlrpc user <user>
        self.re2 = regexp(r"(?:del|delete|remove) xmlrpc user (?P<user>\S+)")

        # [don[']t|do not] allow xmlrpc (func[tion]|method) <method> [(to|for) user <user>] [(to|for|on|at) [user|channel] <target>] [[and] [on|at] server <server>]
        self.re3 = regexp(r"(?P<dont>don'?t |do not )?allow xmlrpc (?:func(?:tion)?|method) (?P<method>\S+)(?: (?:to |for )user (?P<user>\S+))?(?: (?:to|for|on|at) (?:user |channel )?(?P<target>\S+))?(?: (?:and )?(?:on |at )?server (?P<server>\S+))?")
    
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
        db.execute("select null from xmlrpcuser where username=?",
                   username)
        if not db.results:
            db.execute("insert into xmlrpcuser values (?,?)",
                       username, password)
            return 1
        return 0

    def user_del(self, username):
        db.execute("delete from xmlrpcuser where username=?", username)
        return db.changed

    def perm_add(self, username, method, servername, target):
        if self.perm_del(username, method, servername, target, check=1):
            return 0
        db.execute("insert into xmlrpcperm values (?,?,?,?)",
                   username, method, servername, target)
        return 1

    def perm_del(self, username, method, servername, target, check=0):
        where = ["username=?", "method=?"]
        wargs = [username, method]
        if servername:
            where.append("servername=?")
            wargs.append(servername)
        else:
            where.append("servername isnull")
        if target:
            where.append("target=?")
            wargs.append(target)
        else:
            where.append("target isnull")
        wstr = " and ".join(where)
        if not check:
            db.execute("delete from xmlrpcperm where "+wstr, *wargs)
        else:
            db.execute("select null from xmlrpcperm where "+wstr, *wargs)
        return db.changed or db.results

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
        db.execute("select null from xmlrpcperm "
                   "natural left join xmlrpcuser where "
                   "xmlrpcuser.username=? and password=? and "
                   "(servername isnull or servername=?) and "
                   "(target isnull or target=?)",
                   username, password, server, target)
        if db.results:
            return 1
        return 0
    
    def rm_sendmsg(self, auth, msg, notice=0, ctcp=None):
        server = servers.get(auth["server"])
        if server:
            if type(msg) == StringType:
                server.sendmsg(auth["target"], None,
                               msg, notice=notice, ctcp=ctcp)
            else:
                server.sendmsg(auth["target"], None,
                               notice=notice, ctcp=ctcp, *msg)

def __loadmodule__():
    global mod
    mod = XmlRpc()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
