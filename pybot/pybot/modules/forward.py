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

from pybot import mm, hooks, options, servers
from string import join
import re

class Forward:
	def __init__(self, bot):
		self.data = options.gethard("Forward.data", [])
		hooks.register("Message", self.message_forward, 90)
		hooks.register("OutMessage", self.message_forward, 90)
		hooks.register("Notice", self.notice_forward, 90)
		hooks.register("OutNotice", self.notice_forward, 90)
		hooks.register("CTCP", self.ctcp_forward, 90)
		hooks.register("OutCTCP", self.ctcp_forward, 90)
		hooks.register("UserJoined", self.joined_forward, 90)
		hooks.register("UserParted", self.parted_forward, 90)
		hooks.register("Message", self.message)

		# Match 'forward messages [[(from|on|at) server <fromserver1>] | for you | [(from|on|at) [user|channel] <fromtarget>] [(from|on|at) server <fromserver2>]] to [user|channel] <totarget> [(on|at) server <toserver>] [with (server|channel [and server]|<withstring>)] [!|.]'
		self.re1 = re.compile(r"(?P<dont>do\s+not\s+|don't\s+)?forward\s+messages\s+(?:(?:(?:from\s+|on\s+|at\s+)server\s+(?P<fromserver1>\S+)\s+)|(?:(?P<foryou>for\s+you\s+)?(?:(?:from\s+|on\s+|at\s+)(?:channel\s+|user\s+)?(?P<fromtarget>\S+)\s+)?(?:(?:from\s+|on\s+|at\s+)(?:server\s+)?(?P<fromserver2>\S+)\s+)?))?to\s+(?:user\s+|channel\s+)?(?P<totarget>\S+)(?:\s+(?:on\s+|at\s+)server\s+(?P<toserver>\S+))?(?:\s+with(?:(?P<withserver1>\s+server)|(?P<withchannel>\s+channel)(?:\s+and\s+(?P<withserver2>server))?|(?P<withstring>\S+)))?\s*[!.]*$", re.I)

		# Match 'what['re| are] you forwarding [?]'
		self.re2 = re.compile(r"what(?:'re|\s+are)\s+you\s+forwarding\s*\?*$", re.I)
	
	def unload(self):
		hooks.unregister("Message", self.message_forward, 90)
		hooks.unregister("OutMessage", self.message_forward, 90)
		hooks.unregister("Notice", self.notice_forward, 90)
		hooks.unregister("OutNotice", self.notice_forward, 90)
		hooks.unregister("CTCP", self.ctcp_forward, 90)
		hooks.unregister("OutCTCP", self.ctcp_forward, 90)
		hooks.unregister("UserJoined", self.joined_forward, 90)
		hooks.unregister("UserParted", self.parted_forward, 90)
		hooks.unregister("Message", self.message)
	
	def do_forward(self, server, target, nick, forme, before, after):
		for tuple in self.data:
			if (tuple[0]==None or tuple[0]==server.servername) and \
			   (tuple[1]==None or tuple[1]==target) and \
			   (not tuple[2] or forme):
				fwdserver = servers.get(tuple[3])
				if fwdserver:
					s = nick
					if tuple[6]:
						s = s+"@"+tuple[6]
					else:
						with = tuple[5]
						if with&1:
							s = s+"@"+target
							if with&2:
								s = s+","+server.servername
						elif with&2:
							s = s+"@"+server.servername
					fwdserver.sendmsg(tuple[4], None, before+s+after, outhooks=0)
	
	def message_forward(self, msg):
		self.do_forward(msg.server, msg.target, msg.user.nick, msg.forme, "<", "> "+msg.rawline)
	
	def notice_forward(self, msg):
		self.do_forward(msg.server, msg.target, msg.user.nick, msg.forme, "-", "- "+msg.rawline)
	
	def ctcp_forward(self, msg):
		if msg.ctcp == "ACTION":
			self.do_forward(msg.server, msg.target, msg.user.nick, msg.forme, "* ", " "+msg.rawline)
	
	def joined_forward(self, server, target, user):
		self.do_forward(server, target, user.nick, 0, "--> ", " has joined")

	def parted_forward(self, server, target, user, reason):
		if reason:
			self.do_forward(server, target, user.nick, 0, "--> ", " has leaved: "+reason)
		else:
			self.do_forward(server, target, user.nick, 0, "--> ", " has leaved")
	
	def message(self, msg):
		var = []
		if msg.forme:
			m = self.re1.match(msg.line)
			if m:
				if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "forward"):
					foryou = m.group("foryou") != None
					fromtarget = m.group("fromtarget")
					fromserver = m.group("fromserver1") or m.group("fromserver2")
					totarget = m.group("totarget")
					toserver = m.group("toserver") or msg.server.servername
					with = 0
					if m.group("withchannel"):
						with = with|1
					if m.group("withserver1") or m.group("withserver2"):
						with = with|2
					withstring = m.group("withstring")
					if m.group("dont"):
						try:
							self.data.remove((fromserver, fromtarget, foryou, toserver, totarget, with, withstring))
							msg.answer("%:", ["Sure", "I'll not forward", "Of course", "No problems"], ["!", "."])
						except ValueError:
							msg.answer("%:", ["Sorry, but", "Oops! I think", None], "I'm not forwarding any messages like this", [".", "!"])
					else:
						self.data.append((fromserver, fromtarget, foryou, toserver, totarget, with, withstring))
						msg.answer("%:", ["Sure", "I'll forward", "Right now", "Of course"], ["!", "."])
				return 0
			
			m = self.re2.match(msg.line)
			if m:
				if mm.hasperm(0, msg.server.servername, msg.target, msg.user, "listforward"):
					if self.data:
						for tuple in self.data:
							str = "I'm forwarding messages"
							if tuple[2]:
								str = str+" for me"
							if tuple[0] and tuple[1] and tuple[1] != msg.server.servername:
								str = str+" from "+tuple[1]+" at "+tuple[0]
							elif tuple[1]:
								str = str+" from "+tuple[1]
							elif tuple[0]:
								str = str+" from server "+tuple[0]
							str = str+" to "+tuple[4]
							if tuple[3] and tuple[3] != msg.server.servername:
								str = str+" at "+tuple[3]
							if tuple[5]==3:
								str = str+" with channel and server"
							elif tuple[5]&1:
								str = str+" with channel"
							elif tuple[5]&2:
								str = str+" with server"
							elif tuple[6]:
								str = str+" with "+tuple[6]
							msg.answer("%:", str, [".", "!"])
					else:
						msg.answer("%:", ["Sir,", None], "I'm not forwarding anything", ["!", "."])
				return 0
	
def __loadmodule__(bot):
	global forward
	forward = Forward(bot)

def __unloadmodule__(bot):
	global forward
	forward.unload()
	del forward

# vim:ts=4:sw=4
