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

from thread import start_new_thread
import traceback

class Hooks:
	def __init__(self):
		self.__hook = {}
	
	def register(self, hookname, hookfunc, priority=500, threaded=0):
		hook = self.__hook.get(hookname)
		if not hook:
			self.__hook[hookname] = [(hookfunc,priority,threaded)]
		else:
			l = len(hook)
			i = 0
			while i < l:
				if hook[i][1] > priority:
					hook.insert(i,(hookfunc,priority,threaded))
					return
				i = i + 1
			hook.append((hookfunc,priority,threaded))
	
	def unregister(self, hookname, hookfunc, priority=500, threaded=0):
		self.__hook[hookname].remove((hookfunc,priority,threaded))
	
	def call(self, hookname, *hookparam, **hookkwparam):
		ret = []
		if self.__hook.has_key(hookname):
			for hook in self.__hook[hookname][:]:
				try:
					if hook[2]:
						start_new_thread(hook[0], hookparam, hookkwparam)
					else:
						val = apply(hook[0],hookparam,hookkwparam)
					ret.append(val)
					if val == -1: break
				except:
					traceback.print_exc()
		return ret

# vim:ts=4:sw=4
