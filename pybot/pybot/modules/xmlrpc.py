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

from pybot import hooks, mm, rm, options, servers
from SimpleXMLRPCServer import SimpleXMLRPCServer
from types import StringType
import xmlrpclib
import traceback
import re

HELP = [
("""\
The xmlrpc service is based on method names and permissions. If you \
want to allow a given user to run a method, first you must create \
a xmlrpc user for him, with "(add|create) xmlrpc user <username> \
with pass[word] <password>".\
""",),
("""\
Then, you can give or remove permissions for that user with \
"[don't|do not] allow xmlrpc (func[tion]|method) <func> [(to|for) user \
<xmlrpcuser>] [(to|for|on|at) [user|channel] <target>] [[and] [on|at] \
server <server>]".\
""",),
("""\
To remove a given xmlrpc user, just use "(del[ete]|remove) xmlrpc \
user <user>".\
""",)]

class XmlRpcObject:
    def __init__(self, funcs, hasperm):
        self.__funcs = funcs
        self.__hasperm = hasperm

    def _dispatch(self, name, args):
        func = self.__funcs.get(name)
        if not func:
            return xmlrpclib.Fault(2, "no such method")
        auth = args[0]
        if type(auth) is not dict:
            return xmlrpclib.Fault(1, "invalid authorization")
        try:
            if self.__hasperm(name, auth):
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
    def __init__(self, bot):
        self.user = options.gethard("XmlRpc.users", {})
        self.perm = options.gethard("XmlRpc.permissions", {})
        
        self.server = SimpleXMLRPCServer(("0.0.0.0", 8460))
        self.server.socket.setblocking(0)
        
        rm.register("sendmsg", self.rm_sendmsg)
        
        xro = XmlRpcObject(rm.get_methods(), self.hasperm)
        self.server.register_instance(xro)
        
        hooks.register("Message", self.message)
        hooks.register("Loop", self.loop)

        # (add|create) xmlrpc user <user> with [pass|password] <passwd> [!.]
        self.re1 = re.compile(r"(?:add|create)\s+xmlrpc\s+user\s+(?P<user>\S+)\s+with\s+(?:password|pass)\s+(?P<passwd>\S+)\s*[.!]*$")

        # (del|delete|remove) xmlrpc user <user>
        self.re2 = re.compile(r"(?:del|delete|remove)\s+xmlrpc\s+user\s+(?P<user>\S+)\s*[.!]*$")

        # [don[']t|do not] allow xmlrpc (func[tion]|method) <func> [(to|for) user <user>] [(to|for|on|at) [user|channel] <target>] [[and] [on|at] server <server>]
        self.re3 = re.compile(r"(?P<dont>don'?t\s+|do not\s+)?allow\s+xmlrpc\s+(?:func(?:tion)?|method)\s+(?P<func>\S+)(?:\s+(?:to\s+|for\s+)user\s+(?P<user>\S+))?(?:\s+(?:to|for|on|at)\s+(?:user\s+|channel\s+)?(?P<target>\S+))?(?:\s+(?:and\s+)?(?:on\s+|at\s+)?server\s+(?P<server>\S+))?\s*[.!]*$")
    
        # xmlrpc
        mm.register_help(0, "xmlrpc", HELP)
        
    def unload(self):
        hooks.unregister("Message", self.message)
        hooks.unregister("Loop", self.loop)
        self.server.server_close()
        rm.unregister("sendmsg")
        mm.unregister_help(0, HELP)
    
    def loop(self):
        self.server.handle_request()
    
    def message(self, msg):
        if msg.forme:
            m = self.re1.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "xmlrpc"):
                    user = m.group("user")
                    if self.user.has_key(user):
                        msg.answer("%:", ["I can't do this!", "Sorry!"], ["This user already exists", "This user is already registered"], [".", "!"])
                    else:
                        self.user[user] = m.group("passwd")
                        msg.answer("%:", ["User added", "Ok", "User created", "Done"], [".", "!"])
                else:
                    msg.answer("%:", ["Sorry, you", "You"], ["can't add xmlrpc users.", "don't have this power."])
                return 0
            
            m = self.re2.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "xmlrpc"):
                    try:
                        del self.user[m.group("user")]
                    except KeyError:
                        msg.answer("%:", ["Oops!", "Sorry!"], ["There's no such user", "I haven't found this user"], [".", "!"])
                    else:
                        msg.answer("%:", ["User removed", "No problems", "User deleted", "Done"], [".", "!"])
                else:
                    msg.answer("%:", ["Sorry, you", "You"], ["can't add xmlrpc users.", "don't have this power."])
                return 0

            m = self.re3.match(msg.line)
            if m:
                if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "xmlrpc"):
                    func = m.group("func")
                    tuple = (m.group("user"), m.group("server"), m.group("target"))
                    if m.group("dont"):
                        try:
                            funcperm = self.perm[func]
                            funcperm.index(tuple)
                        except (KeyError, ValueError):
                            msg.answer("%:", ["Sorry!", "Oops!", "Can't do this!"], ["Nobody has this permission", "This permission doesn't exist"], [".", "!"])
                        else:
                            funcperm.remove(tuple)
                            if not funcperm:
                                del self.perm[func]
                            msg.answer("%:", ["Ok", "No problems", "Right now", "Permission removed"], [".", "!"])
                    else:
                        funcperm = self.perm.setdefault(func, [])
                        try:
                            funcperm.index(tuple)
                        except ValueError:
                            funcperm.append(tuple)
                            msg.answer("%:", ["Ok", "No problems", "Right now"], [".", "!"])
                        else:
                            msg.answer("%:", ["Oops!", "It's not necessary!", "I don't have to!"], "This permission already exists", [".", "!"])
                else:
                    msg.answer("%:", ["Sorry, you", "You"], ["can't work with xmlrpc permissions.", "don't have this power."])
                return 0
    
    def hasperm(self, funcname, auth):
        user = auth.get("username")
        passwd = auth.get("password")
        server = auth.get("server")
        target = auth.get("target")
        if passwd == self.user.get(user):
            funcperm = self.perm.get(funcname, [])
            for _user, _server, _target in funcperm:
                if (not _user or user == _user) and \
                    (not _server or not server or _server == server) and \
                    (not _target or not target or _target == target):
                    return 1
    
    def rm_sendmsg(self, auth, msg, notice=0, ctcp=None):
        server = servers.get(auth["server"])
        if server:
            if type(msg) == StringType:
                server.sendmsg(auth["target"], None, msg, notice=notice, ctcp=ctcp)
            else:
                server.sendmsg(auth["target"], None, notice=notice, ctcp=ctcp, *msg)

def __loadmodule__(bot):
    global mod
    mod = XmlRpc(bot)

def __unloadmodule__(bot):
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
