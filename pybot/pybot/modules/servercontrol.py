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

from pybot import mm, hooks, options, servers, main
from pybot.user import User
from string import join

class ServerControl:
	def __init__(self, bot):
		self.servers = options.gethard("ServerControl.servers", {})
		hooks.register("Connected", self.connected)
		hooks.register("ConnectionError", self.connectionerror) 
		hooks.register("Registered", self.registered)
		hooks.register("Command", self.command)
		hooks.register("Message", self.message)
		self.registered = {}
		for server in self.servers.keys():
			servers.add(server)

	def unload(self):
		hooks.unregister("Connected", self.connected)
		hooks.unregister("ConnectionError", self.connectionerror) 
		hooks.unregister("Registered", self.registered)
		hooks.unregister("Command", self.command)
		hooks.unregister("Message", self.message)

	def connected(self, server):
		nick, username, mode, realname, channels = self.servers[server.servername]
		self.registered[server] = 0
		server.sendcmd("", "USER", username, mode, "0", ":"+realname, priority=10)
		server.sendcmd("", "NICK", nick, priority=10)
		server.user.set(nick, "", "")
	
	def connectionerror(self, server):
		self.registered[server] = 0
	
	def send_join(self, server, channel, keyword):
		if keyword:
			server.sendcmd("", "JOIN", "%s %s" % (channel, keyword), priority=10)
		else:
			server.sendcmd("", "JOIN", channel, priority=10)
	
	def registered(self, server):
		self.registered[server] = 1
		channels = self.servers[server.servername][4]
		for channel, attr in channels.items():
			self.send_join(server, channel, attr[0])
	
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
				hooks.call("UserParted", cmd.server, cmd.params[0], user, reason)
		elif cmd.cmd == "QUIT":
			user = User()
			user.setstring(cmd.prefix)
			if len(cmd.params) > 0:
				reason = join([cmd.params[0][1:]]+cmd.params[2:])
			else:
				reason = None
			hooks.call("UserQuited", cmd.server, user, reason)

	def message(self, msg):
		var = []
		if msg.match(var, 3, "%", [("join", ["on", None]), ("go", "to")], ["channel", None], 0, "^[#&+!][^,]+$", [("with", "keyword", 1, "~"), None], [(["at", "on"], 2, "~"), None], ["!",".",None]):
			if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "join"):
				if var[2] != None:
					server = servers.get(var[2])
					if not server:
						msg.answer("%:", ["Sorry,", "Oops!", "Hummm..."], "I'm not in this", ["server!", "server, sir!"])
						return 0
				else:
					server = msg.server
				channels = self.servers[server.servername][4]
				if channels.has_key(var[0]):
					msg.answer("%:", ["Sorry,", "Oops!", "It's not necessary.", None], "I'm already", ["there!", "there, sir!"])
				else:
					msg.answer("%:", ["I'm going there!", "At your order, sir!", "No problems!", "Right now!", "Ok!"])
					if self.registered[server]:
						self.send_join(server, var[0], var[1])
					channels[var[0]] = [var[1]]
			else:
				msg.answer("%:", [("You're not", ["allowed to join.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
			return 0
		elif msg.match(var, 3, "%", [("leave", ["channel", None]), ("part", ["from", None], ["channel", None])], 0, "^[#&+!][^,]+$", [(["at", "on"], 1, "~"), None], [("with", 2, "|>"), None], ["!",".",None]):
			if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "part"):
				if var[1] != None:
					server = servers.get(var[1])
					if not server:
						msg.answer("%:", ["Sorry,", "Oops!", "Hummm..."], "I'm not in this", ["server!", "server, sir!"])
						return 0
				else:
					server = msg.server
				channels = self.servers[server.servername][4]
				if not channels.has_key(var[0]):
					msg.answer("%:", ["Sorry,", "Oops!", "It's not necessary.", None], "I'm not", ["there!", "there, sir!"])
				else:
					msg.answer("%:", ["Ok,", "No problems.", None], "I'm", ["leaving!", "leaving, sir!", "parting!"])
					if self.registered[server]:
						if var[2]:
							server.sendcmd("", "PART", join([var[0], ":"+var[2][0]]+var[2][1:]), priority=10)
						else:
							server.sendcmd("", "PART", var[0], priority=10)
					del channels[var[0]]
			else:
				msg.answer("%:", [("You're not", ["allowed to leave.", "that good...", "allowed to do this...", "my lord."]), "No, sir!", "Nope."])
			return 0
		elif msg.match(var, 1, "%", "connect", ["to", None], 0, "~", ["!",".",None]):
			if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "connect"):
				if self.servers.has_key(var[0]):
					msg.answer("%:", ["Sorry,", "Oops!", "But,", None], "I'm already connected to this", ["server!", "server, sir!"])
				else:
					msg.answer("%:", ["I'm connecting, sir!", "I'm going there!", "At your order, sir!", "No problems!", "Right now!", "Ok!"])
					self.servers[var[0]] = ["pybot", "pybot", "0", "PyBot", {}]
					servers.add(var[0])
			else:
				msg.answer("%:", [("You're not", ["allowed to connect.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
			return 0
		elif msg.match(var, 2, "%", "reconnect", [("to", 0, "~"), None], [("with", 1, "|>"), None], ["!",".",None]):
			if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "reconnect"):
				if var[0]:
					server = servers.get(var[0])
				else:
					server = msg.server
				if not server or not self.servers.has_key(server.servername):
					msg.answer("%:", ["Sorry,", "Oops!", "But,", None], "I'm not connected to this", ["server!", "server, sir!"])
				else:
					msg.answer("%:", ["I'm reconnecting, sir!", "At your order, sir!", "No problems!", "Right now!", "Ok!"])
					if var[1]:
						server.sendcmd("", "QUIT", join([":"+var[1][0]]+var[1][1:]))
					else:
						server.sendcmd("", "QUIT")
					server.reconnect()
			else:
				msg.answer("%:", [("You're not", ["allowed to connect.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
			return 0
		elif msg.match(var, 1, "%", "disconnect", ["from", None], [0, "~", None], ["!", ".", None]):
			if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "disconnect"):
				if var[0]:
					server = servers.get(var[0])
				else:
					server = msg.server
				if not server or not self.servers.has_key(server.servername):
					msg.answer("%:", ["Sorry,", "Oops!", "But,", None], "I'm not connected to this", ["server!", "server, sir!"])
				else:
					msg.answer("%:", ["I'm disconnecting, sir!", "At your order, sir!", "No problems!", "Right now!", "Ok!"])
					del self.servers[server.servername]
					server.sendcmd("", "QUIT")
					server.kill()
			else:
				msg.answer("%:", [("You're not", ["allowed to connect.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
			return 0
		elif msg.match(var, 1, "%", ["reboot", "reset"], ["now", None], [("with", 0, "|>"), "!", ".", None]):
			if mm.hasperm(1, msg.server.servername, msg.target, msg.user, "reboot"):
				msg.answer("%:", ["Rebooting!", "No problems!", "I'll do this!", "Right now, sir!", "Ok, sir!", "I'll be back in a moment."])
				main.reboot = 1
				for server in servers.getall():
					if var[0]:
						server.sendcmd("", "QUIT", join([":"+var[0][0]]+var[0][1:]), priority=10)
					else:
						server.sendcmd("", "QUIT", priority=10)
			else:
				msg.answer("%:", [("You're not", ["allowed to reboot me.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
			return 0
		elif msg.match(var, 1, "%", ["quit", "exit", ("go", "home")], [("with", "|>"), "!", ".", None]):
			if mm.hasperm(1, msg.server.servername, msg.target, msg.user, "quit"):
				msg.answer("%:", ["I'm leaving!", "I'm going home!", "I'll do this!", "Right now, sir!", "Ok, sir!", "See you!"])
				main.quit = 1
				for server in servers.getall():
					if var[0]:
						server.sendcmd("", "QUIT", join([":"+var[0][0]]+var[0][1:]), priority=10)
					else:
						server.sendcmd("", "QUIT", priority=10)
			else:
				msg.answer("%:", [("You're not", ["that good...", "allowed to do this, sir!"]), "Nope."])
			return 0
		elif msg.match(var, 1, "%", ["what", ("list", ["the", None])], "channels", [([("you", "are"), ("are", "you")], ["in", None]), None], [(["on", "at"], ["server", None], 0, "~"), None], ["!", ".", "?", None]):
			if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "listchannels"):
				if var[0] and not self.servers.has_key(var[0]):
					msg.answer("%:", ["Sorry,", "Oops!", "It seems like", None], "I'm not in this", ["server!", "server, sir!"])
				else:
					if var[0]:
						channels = self.servers[var[0]][4].keys()
					else:
						channels = self.servers[msg.server.servername][4].keys()
					clen = len(channels)
					if clen == 0:
						msg.answer("%:", ["In this server,", None], "I'm in no", ["channels.", "channels, sir!", "channels at all.", "channels at all, sir!"])
					elif clen == 1:
						msg.answer("%:", ["In this server,", None], "I'm in the channel", [channels[0]+".", channels[0]+", sir!"])
					else:
						list = channels[0]
						for n in range(1, clen):
							if n == clen-1:
								list = list+", and "+channels[n]
							else:
								list = list+", "+channels[n]
						msg.answer("%:", ["In this server,", None], "I'm in the channels",  [list+".", list+", sir!"])
			else:
				msg.answer("%:", [("You're not", ["allowed to list channels.", "that good...", "allowed to do this..."]), "No, sir!", "Nope."])
			return 0

def __loadmodule__(bot):
	global servercontrol
	servercontrol = ServerControl(bot)

def __unloadmodule__(bot):
	global servercontrol
	servercontrol.unload()
	del servercontrol

# vim:ts=4:sw=4
