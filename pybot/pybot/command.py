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

from types import TupleType, ListType, IntType
from string import split, lower
from pybot.user import User
import re

class MatchError: pass

class Command:
	re = re.compile("(?::(\\S*) )?(\\w+) ((\\S+) :(?:\01(\\w+) )?((?:\\W*(\\w+)\\W*\\s)?(.*?))(?:\01)?|.*)$")
		
	def __init__(self):
		self.user = User()

	def setline(self, server=None, line=None):
		self.server = server
		## Maintaining temporarly for compatibility with old modules
		tokens = split(line)
		if len(tokens) == 0:
			return
		if tokens[0][0] == ":":
			if len(tokens) == 1:
				return
			self.prefix = tokens[0][1:]
			self.cmd = tokens[1]
			self.params = tokens[2:]
		else:
			self.prefix = ""
			self.cmd = tokens[0]
			self.params = tokens[1:]
		self.line = line
		self._internalset()
		##
		m = self.re.match(line)
		if m:
			nick = self.server.user.nick
			self.prefix = m.group(1) or ""
			self.user.setstring(self.prefix)
			self.cmd = m.group(2)
			# _index is used for speed purposes and shouldn't be
			# used by modules.
			try:
				# Message = 0, Notice = 1
				self._index = ["PRIVMSG", "NOTICE"].index(self.cmd)
			except:
				# Command = 2
				self._index = 2
				self.line = self.rawline = m.group(3)
				self.target = ""
				self.ctcp = ""
				self.forme = 0
				self.direct = 0
				self.answertarget = ""
			else:
				self.target = m.group(4)
				self.ctcp = m.group(5)
				if self.ctcp:
					self._index += 3 # CTCP = 3, CTCPReply = 4
				self.rawline = m.group(6)
				if m.group(7) == nick:
					self.line = m.group(8)
					self.forme = 1
				else:
					self.line = self.rawline
					self.forme = 0
				if self.target == nick:
					self.forme = 1
					self.direct = 1
					self.answertarget = self.user.nick
				else:
					self.direct = 0
					self.answertarget = self.target
		else:
			self.target = ""
			self.answertarget = ""
			self.forme = 0
			self.direct = 0
			self.line = ""
			self.rawline = ""
			self._index = 2
		
	def _internalset(self):
		self.user.setstring(self.prefix)
		if self.params:
			self.target = self.params[0]
			nick = self.server.user.nick
			if len(self.params) > 1:
				self.msg = [self.params[1][1:]] + self.params[2:]
				self.rawmsg = self.msg[:]
				punct = ""
				while self.msg and self.msg[-1] and self.msg[-1][-1] in [".","!","?"]:
					punct = self.msg[-1][-1] + punct
					self.msg[-1] = self.msg[-1][:-1]
					if not self.msg[-1]:
						del self.msg[-1]
				if punct:
					self.msg.append(punct)
				if re.compile("\W*%s\W*$"%nick).match(self.msg[0]):
					del self.msg[0]
					self.forme = 1
				else:
					self.forme = 0
			else:
				self.msg = []
				self.rawmsg = []
				self.forme = 0
			if self.target == nick:
				self.forme = 1
				self.direct = 1
				self.answertarget = self.user.nick
			else:
				self.direct = 0
				self.answertarget = self.target
		else:
			self.target = ""
			self.answertarget = ""
			self.msg = []
			self.rawmsg = []
			self.forme = 0
			self.direct = 0

	def answer(self, *params, **kw):
		self.server.sendmsg(self.answertarget, self.user.nick, *params, **kw)
	
	def match(self, var, varn, *pattern):
		if varn != 0:
			var[:] = [None]*varn
		try:
			n = self._match(var, 0, self.msg, pattern)
		except MatchError:
			return None
		if n == len(self.msg):
			return 1

	def _match(self, var, n, query, pattern):
		l = len(query)
		lp = len(pattern)
		i = 0
		while i < lp:
			tok = pattern[i]
			if type(tok) == TupleType:
				n = self._match(var, n, query, tok)
			elif type(tok) == ListType:
				n = self._matchany(var, n, query, tok)
			elif n >= l:
				raise MatchError
			elif type(tok) == IntType:
				pos = tok
				i = i+1
				tok = pattern[i]
				if tok == "~":
					var[pos] = query[n]
				elif tok[0] == "~":
					if lower(query[n]) != tok[1:]:
						raise MatchError
					var[pos] = query[n]
				elif tok[0] == "^":
					if not re.compile(tok[1:]).match(lower(query[n])):
						raise MatchError
					var[pos] = query[n]
				elif tok[0] == "|":
					n = self._matchmany(var, pos, n, query, pattern[i+1:], tok) - 1
				n = n + 1
			else:
				if tok == "&":
					pass
				elif tok[0] == "&":
					if not re.compile(tok[1:]).match(lower(query[n])):
						raise MatchError
				elif tok == "%":
					if not self.forme:
						raise MatchError
					n = n - 1
				elif tok[0] == "/":
					if not lower(self.server.user.nick)+tok[1:] == query[n]:
						raise MatchError
				elif tok == ".":
					if 0 in map(lambda x: x == ".", query[n]):
						raise MatchError
				elif tok == "!":
					if 0 in map(lambda x: x == "!", query[n]):
						raise MatchError
				elif tok == "?":
					if "?" not in query[n] or 0 in map(lambda x: x in ["!","?"], query[n]):
						raise MatchError
				elif tok[0] == "\\":
					if lower(query[n]) != tok[1:]:
						raise MatchError
				elif lower(query[n]) != tok:
					raise MatchError
				n = n + 1
			i = i + 1
		return n
	
	def _matchany(self, var, n, query, pattern):
		l = len(query)
		lp = len(pattern)
		i = 0
		while i < lp:
			tok = pattern[i]
			if type(tok) == TupleType:
				try:
					return self._match(var, n, query, tok)
				except MatchError: pass
			elif type(tok) == ListType:
				try:
					return self._matchany(var, n, query, tok)
				except MatchError: pass
			elif tok == None:
				return n
			elif n >= l:
				pass
			elif type(tok) == IntType:
				pos = tok
				i = i+1
				tok = pattern[i]
				if tok == "~":
					var[pos] = query[n]
					return n + 1
				elif tok[0] == "~":
					if lower(query[n]) == tok[1:]:
						var[pos] = query[n]
						return n + 1
				elif tok[0] == "^":
					if re.compile(tok[1:]).match(lower(query[n])):
						var[pos] = query[n]
						return n + 1
				elif tok[0] == "|":
					try:
						n = self._matchmany(var, pos, n, query, pattern[i+1:], tok)
						return n
					except MatchError: pass
			else:
				if tok == "&":
					return n + 1
				elif tok[0] == "&":
					if re.compile(tok[1:]).match(lower(query[n])):
						return n + 1
				elif tok == "%":
					if self.forme:
						return n
				elif tok[0] == "/":
					if lower(self.server.user.nick)+tok[1:] == lower(query[n]):
						return n + 1
				elif tok == ".":
					if 0 not in map(lambda x: x == ".", query[n]):
						return n + 1
				elif tok == "!":
					if 0 not in map(lambda x: x == "!", query[n]):
						return n + 1
				elif tok == "?":
					if "?" in query[n] and 0 not in map(lambda x: x in ["!","?"], query[n]):
						return n + 1
				elif tok[0] == "\\":
					if lower(query[n]) == tok[1:]:
						return n + 1
				elif lower(query[n]) == tok:
					return n + 1
			i = i + 1
		raise MatchError
	
	def _matchmany(self, var, pos, n, query, pattern, str):
		l = len(query)
		a = 0
		b = 0
		ab = split(str[1:-1],",")
		if len(ab) == 1:
			try:
				a = b = int(ab[0])
				b = b+n+1
			except ValueError: pass
		elif len(ab) == 2:
			try: a = int(ab[0])
			except ValueError: pass
			try:
				b = int(ab[1])
				b = b+n+1
			except ValueError: pass
		a = a+n
		if a > l:
			raise MatchError
		if b > l:
			b = 0
		if str[-1] == "<":
			if b == 0: b = l+1
			else: b = b+1
			step = 1
		else:
			if b == 0: b = l+1
			step = -1
			a, b = b-1, a-1
		for i in range(a,b,step):
			try:
				self._match(var, i, query, pattern)
				var[pos] = query[n:i]
				return i
			except MatchError: pass
		raise MatchError

# vim:ts=4:sw=4
