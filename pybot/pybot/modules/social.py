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

from pybot import hooks
from time import time
import re

class Social:
	def __init__(self, bot):
		self.hello = {}
		hooks.register("Message", self.message)
		hooks.register("UnhandledMessage", self.unhandled_message)

		# Match '(hi|hello) [there|everybody|all|guys|folks|pybot] [!|.]'
		self.re1 = re.compile(r'(?:hi|hello)(?:\s+(?:there|everybody|all|guys|folks|(?P<nick>\w+)))?\s*[!.]*$', re.I)
		
		# Match 'pybot!'
		self.re2 = re.compile(r'(?P<nick>\w+)\s*!+$', re.I)
		
		# Match '[thank[']s|thank you] [!|.]'
		self.re3 = re.compile(r'thank(?:\'?s)?\s+you(?:\s+(?P<nick>\w+))\s*[!.]*', re.I)
		
		# Match 'are you ok?|how are you [doing]?'
		self.re4 = re.compile(r'(?:are\s+you\s+ok|how\s+are\s+you(?:\s+doing)?)\s*[!?]*$', re.I)
		
		# Match 'pybot?'
		self.re5 = re.compile(r'!*?[?!]*$', re.I)
	
		# Match 'never mind [!|.]'
		self.re6 = re.compile(r'never\s+mind\s*[!.]*$', re.I)

		# Match '[very|pretty] (nice|good|great) [.|!]'
		self.re7 = re.compile(r'(?:(?:very|pretty)\s+)?(?:nice|good|great)\s*[.!]*$', re.I)
		
		# Match ' (gay|stupid|fuck|idiot|imbecile|cretin) '
		self.re8 = re.compile(r'.*(?:gay|stupid|fuck|idiot|imbecile|cretin)', re.I)
		
	def unload(self):
		hooks.unregister("Message", self.message)
		hooks.unregister("UnhandledMessage", self.unhandled_message)
	
	def message(self, msg):
		usernick = msg.server.user.nick
		m = self.re1.match(msg.line) or self.re2.match(msg.rawline)
		if m and (not m.group("nick") or m.group("nick") == usernick):
			for user in self.hello.keys():
				if self.hello[user]+1800 < time():
					del self.hello[user]
			user = msg.user.string+msg.server.servername+msg.target
			usertime = self.hello.get(user)
			if not usertime:
				msg.answer([("%:", ["Hi!", "Hello!"]), (["Hi", "Hello"], "/", [".", "!"])])
				self.hello[user] = time()
			elif msg.forme and usertime+300 < time():
				msg.answer([("%:", ["Hi", "Hello"], "again", [".", "!"]), (["Hi", "Hello"], "again", "/", [".", "!"])])
				self.hello[user] = time()
			return 0

		m = self.re3.match(msg.line)
		if m and (msg.forme or m.group("nick") == usernick):
			msg.answer("%:", ["No problems", "You're welcome", "I'm glad to help you", "I'm here for things like this..."], ["!", "."])
			return 0
		
		if msg.forme:
			if self.re4.match(msg.line):
				msg.answer("%:", ["I'm", "Everything is"], ["ok", "fine"], ["!", ", thanks!"])
				return 0
		
			if self.re5.match(msg.line):
				msg.answer([("%:", "Yes?"), ("%:", "Here!"), ("%", "?")])
				return 0
		
			if self.re6.match(msg.line):
				msg.answer("%:", ["No problems", "Ok", "Sure"], [".", "!"])
				return 0

			if self.re7.match(msg.line):
				msg.answer("%:", ["No problems", "Hey! I'm here for this"], [".", "!", "..."])
				return 0

			if self.re8.match(msg.line):
				msg.answer("%:", ["Be polite while talking to me!", "I should talk to your mother!", "Hey! What's this?", "I'll pretend to be blind."])
				return 0
	
	def unhandled_message(self, msg):
		msg.answer("%:", ["What are you talking about", "What do you mean", "Can I help you", "Huh", "Sorry", "Pardon"], ["?", "!?", "!?!?"])

def __loadmodule__(bot):
	global social
	social = Social(bot)

def __unloadmodule__(bot):
	global social
	social.unload()
	del social

# vim:ts=4:sw=4
