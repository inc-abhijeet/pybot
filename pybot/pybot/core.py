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

from string import split

class User:
	def __init__(self, nick="", username="", host=""):
		self.nick = nick
		self.username = username
		self.host = host
		self.string = nick+"!"+username+"@"+host

	def setstring(self, str):
		tokens = split(str, "!")
		if len(tokens) == 2:
			self.nick = tokens[0]
			tokens = split(tokens[1],"@")
			if len(tokens) == 2:
				self.username, self.host = tokens
				self.string = str
				return
		self.nick = ""
		self.username = ""
		self.host = ""
		self.string = ""
	
	def set(self, nick="", username="", host=""):
		self.nick = nick
		self.username = username
		self.host = host
		self.string = nick+"!"+username+"@"+host
	
	def match(self, nick="*", username="*", host="*"):
		if (nick=="*" or nick==self.nick) and \
		   (username=="*" or username==self.username) and \
		   (host=="*" or (host[0]=="*" and host[1:]==self.host[-(len(host)-1):]) or host==self.host):
			return 1
	
	def matchstr(self, str):
		tokens = split(str, "!")
		if len(tokens) == 2:
			nick = tokens[0]
			tokens = split(tokens[1],"@")
			if len(tokens) == 2:
				username, host = tokens
				return self.match(nick, username, host)

