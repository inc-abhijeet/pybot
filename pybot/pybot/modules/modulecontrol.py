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

from pybot import mm, hooks, options, modls

class ModuleControl:
	def __init__(self, bot):
		self.modules = options.gethard("ModuleControl.modules", [])
		hooks.register("Message", self.message)
		modls.loadlist(self.modules)

	def unload(self):
		hooks.unregister("Message", self.message)
	
	def message(self, msg):
		var = []
		if msg.match(var, 1, "%", "reload", [(["the", None], "module"), None], 0, "~", [".", "!", None]):
			if mm.hasperm(1, msg.server.servername, msg.target, msg.user, None):
				if modls.isloaded(var[0]):
					if modls.reload(var[0]):
						msg.answer("%:", ["Reloaded", "Done", "Ready"], ["!", ", sir!"])
					else:
						# If it was able to unload, remove it from our list.
						if not modls.isloaded(var[0]):
							self.modules.remove(var[0])
						msg.answer("%:", ["Something wrong happened while", "Something bad happened while", "There was a problem"],  "reloading the module", ["!", "."])
				else:
					msg.answer("%:", ["Sorry sir, but", "Sir,", "Oops, I think that"], "this module is not loaded.")
			else:
				msg.answer("%:", ["You're not that good", "You are not able to reload modules", "No, you can't do this"], [".", "!",". I'm sorry!"])
			return 0
		elif msg.match(var, 1, "%", "load", [(["the", None], "module"), None], 0, "~", [".", "!", None]):
			if mm.hasperm(1, msg.server.servername, msg.target, msg.user, None):
				if not modls.isloaded(var[0]):
					if modls.load(var[0]):
						self.modules.append(var[0])
						msg.answer("%:", ["Loaded", "Done", "Ready"], ["!", "."])
					else:
						msg.answer("%:", ["Something wrong happened while", "Something bad happened while", "There was a problem"],  "loading the module", ["!", "."])
				else:
					msg.answer("%:", ["Sorry sir, but", "Sir,", "Oops, I think that"], "this module is already loaded.")
			else:
				msg.answer("%:", ["You're not that good", "You are not able to load modules", "No, you can't do this"], [".", "!",". I'm sorry!"])
			return 0
		elif msg.match(var, 1, "%", "unload", [(["the", None], "module"), None], 0, "~", [".", "!", None]):
			if mm.hasperm(1, msg.server.servername, msg.target, msg.user, None):
				if modls.isloaded(var[0]):
					if var[0] in self.modules:
						self.modules.remove(var[0])
						if modls.unload(var[0]):
							msg.answer("%:", ["Unloaded", "Done", "Ready"], ["!", "."])
						else:
							msg.answer("%:", ["Something wrong happened while", "Something bad happened while", "There was a problem"],  "unloading the module", ["!", "."])
					else:
						msg.answer("%:", ["Sorry, but", "Oops, I think that"], "this module can't be unloaded.")
				else:
					msg.answer("%:", ["Sorry, but", "Oops, I think that"], "this module is not loaded.")
			else:
				msg.answer("%:", ["You're not that good", "You are not able to unload modules", "No, you can't do this"], [".", "!",". I'm sorry!"])
			return 0

def __loadmodule__(bot):
	global modulecontrol
	modulecontrol = ModuleControl(bot)

def __unloadmodule__(bot):
	global modulecontrol
	modulecontrol.unload()
	del modulecontrol

# vim:ts=4:sw=4
