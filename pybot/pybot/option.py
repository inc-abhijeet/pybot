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

from time import time

class Options:
	def __init__(self):
		self.__hard = {}
		self.__soft = {}
	
	def gethard(self, name, default):
		return self.__hard.setdefault(name, default)

	def sethard(self, name, value):
		self.__hard[name] = value

	def hashard(self, name):
		return self.__hard.has_key(name)

	def delhard(self, name):
		try:
			del self.__hard[name]
		except KeyError:
			pass

	def getharddict(self):
		return self.__hard

	def setharddict(self, dict):
		self.__hard = dict

	def getsoft(self, name, default, keepalive=None):
		"""Return temporary option.
		You may define for how long the option will be considered
		valid trough the keepalive argument (in seconds). If keepalive
		is None (default), option will stay valid while pybot is up, or
		at least until you change the keepalive to something else."""
		opt = self.__soft.get(name)
		if opt:
			if opt[0] is None or time() < opt[0]:
				if keepalive is None:
					opt[0] = None
				elif keepalive:
					opt[0] = time()+keepalive
				return opt[1]
			else:
				del self.__soft[name]
		if keepalive is None:
			self.__soft[name] = [None, default]
		else:
			self.__soft[name] = [time()+keepalive, default]
		return default

	def setsoft(self, name, value, keepalive):
		return self.getsoft(name, value, keepalive)
		
	def hassoft(self, name):
		return self.__soft.has_key(name)

# vim:ts=4:sw=4
