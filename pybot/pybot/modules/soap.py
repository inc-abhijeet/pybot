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

from pybot import hooks, mm, sm, options, servers
from inspect import ismethod, getargspec
import pybot.util.SOAP as SOAP
from types import StringType
import traceback
import re

class SoapMethod(SOAP.MethodSig):
	def __init__(self, funcname, func, hasperm):
		self.__funcname = funcname
		self.__func = func
		self.__hasperm = hasperm
		self.keywords = 1
		self.context = 0
		
	def __call__(self, *parm, **kw):
		user = kw.get("user")
		passwd = kw.get("passwd")
		server = kw.get("server")
		target = kw.get("target")
		print parm
		print kw
		try:
			if self.__hasperm(self.__funcname, user, passwd, server, target):
				if ismethod(self.__func):
					argspec = getargspec(self.__func.im_func)
				else:
					argspec = getargspec(self.__func)
				for arg in ["user", "passwd", "server", "target"]:
					if arg not in argspec[0] and kw.has_key(arg):
						del kw[arg]
				self.__func(*parm, **kw)
		except:
			traceback.print_exc()

class SoapObject:
	def __init__(self, func, hasperm):
		self.__func = func
		self.__hasperm = hasperm

	def __dummy(self, *parm, **kw):
		pass
	
	def __getattr__(self, name):
		func = self.__func.get(name)
		if func:
			return SoapMethod(name, func, self.__hasperm)
		else:
			return self.__dummy
	
class Soap:
	def __init__(self, bot):
		self.user = options.gethard("Soap.users", {})
		self.perm = options.gethard("Soap.permissions", {})
		
		self.server = SOAP.SOAPServer(("0.0.0.0", 8450))
		
		sm.register("sendmsg", self.sm_sendmsg)
		
		so = SoapObject(sm.get_methods(), self.hasperm)
		self.server.registerObject(so)
		
		hooks.register("Message", self.message)
		hooks.register("Loop", self.loop)
		
		# (add|create) soap user <user> with [pass|password] <passwd> [!.]
		self.re1 = re.compile(r"(?:add|create)\s+soap\s+user\s+(?P<user>\S+)\s+with\s+(?:password|pass)\s+(?P<passwd>\S+)\s*[.!]*$")

		# (del|delete|remove) soap user <user>
		self.re2 = re.compile(r"(?:del|delete|remove)\s+soap\s+user\s+(?P<user>\S+)\s*[.!]*$")

		# [don[']t|do not] allow soap function <func> [(to|for) user <user>] [(to|for|on|at) [user|channel] <target>] [[and] [on|at] server <server>]
		self.re3 = re.compile(r"(?P<dont>don'?t\s+|do not\s+)?allow\s+soap\s+function\s+(?P<func>\S+)(?:\s+(?:to\s+|for\s+)user\s+(?P<user>\S+))?(?:\s+(?:to|for|on|at)\s+(?:user\s+|channel\s+)?(?P<target>\S+))?(?:\s+(?:and\s+)?(?:on\s+|at\s+)?server\s+(?P<server>\S+))?\s*[.!]*$")
	
	def unload(self):
		hooks.unregister("Message", self.message)
		hooks.unregister("Loop", self.loop)
		self.server.server_close()
		sm.unregister("sendmsg")
	
	def loop(self):
		self.server.handle_request()
	
	def message(self, msg):
		if msg.forme:
			m = self.re1.match(msg.line)
			if m:
				if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "soap"):
					user = m.group("user")
					if self.user.has_key(user):
						msg.answer("%:", ["I can't do this!", "Sorry!"], ["This user already exists", "This user is already registered"], [".", "!"])
					else:
						self.user[user] = m.group("passwd")
						msg.answer("%:", ["User added", "Ok", "User created", "Done"], [".", "!"])
				else:
					msg.answer("%:", ["Sorry, you", "You"], ["can't add soap users.", "don't have this power."])
				return 0
			
			m = self.re2.match(msg.line)
			if m:
				if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "soap"):
					try:
						del self.user[m.group("user")]
					except KeyError:
						msg.answer("%:", ["Oops!", "Sorry!"], ["There's no such user", "I haven't found this user"], [".", "!"])
					else:
						msg.answer("%:", ["User removed", "No problems", "User deleted", "Done"], [".", "!"])
				else:
					msg.answer("%:", ["Sorry, you", "You"], ["can't add soap users.", "don't have this power."])
				return 0

			m = self.re3.match(msg.line)
			if m:
				if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "soap"):
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
					msg.answer("%:", ["Sorry, you", "You"], ["can't work with soap permissions.", "don't have this power."])
				return 0
	
	def hasperm(self, funcname, user, passwd, server=None, target=None):
		print "funcname:", funcname
		print "user:", user
		print "passwd:", passwd
		print "server:", server
		print "target:", target
		if passwd == self.user.get(user):
			funcperm = self.perm.get(funcname, [])
			for _user, _server, _target in funcperm:
				if (not _user or user == _user) and \
					(not _server or not server or _server == server) and \
					(not _target or not target or _target == target):
					return 1
	
	def sm_sendmsg(self, server, target, msg, notice=0, ctcp=None):
		server = servers.get(server)
		if server:
			if type(msg) == StringType:
				server.sendmsg(target, None, msg, notice=notice, ctcp=ctcp)
			else:
				server.sendmsg(target, None, notice=notice, ctcp=ctcp, *msg)

def __loadmodule__(bot):
	global soap
	soap = Soap(bot)

def __unloadmodule__(bot):
	global soap
	soap.unload()
	del soap

# vim:ts=4:sw=4:nowrap
