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

import traceback
import sys

class Modules:
	def __init__(self):
		self.__modules = {}
	
	def isloaded(self, name):
		return self.__modules.has_key(name)
	
	def loadlist(self, names):
		"""Load list of given modules considering level attribute."""
		modulelist = []
		for name in names:
			try:
				module = __import__("pybot.modules."+name)
				module = getattr(module, "modules")
				module = getattr(module, name)
				reload(module)
				func = getattr(module, "__loadmodule__")
				try:
					level = getattr(module, "__loadlevel__")
				except AttributeError:
					level = 100
				l = len(modulelist)
				i = 0
				while i < l:
					if modulelist[i][-1] > level:
						modulelist.insert(i, (name, module, func, level))
						break
					i = i + 1
				else:
					modulelist.append((name, module, func, level))
			except (AttributeError, ImportError):
				traceback.print_exc()
		ret = []
		for name, module, func, level in modulelist:
			try:
				func(self)
			except:
				traceback.print_exc()
			else:
				self.__modules[name] = module
				ret.append(name)
		return ret
		
	def load(self, name):
		try:
			module = __import__("pybot.modules."+name)
			module = getattr(module, "modules")
			module = getattr(module, name)
			reload(module)
			getattr(module, "__loadmodule__")(self)
			self.__modules[name] = module
			return 1
		except:
			traceback.print_exc()
	
	def unload(self, name):
		module = self.__modules.get(name)
		if module:
			try:
				getattr(module, "__unloadmodule__")(self)
				del self.__modules[name]
				del sys.modules["pybot.modules."+name]
				return 1
			except:
				traceback.print_exc()
	
	def reload(self, name):
		module = self.__modules.get(name)
		if module:
			if self.unload(name):
				return self.load(name)
	

class ModuleMethods:
	"""Intermodule communication class.

	Every module that registers here must have a dummy first parameter.
	When calling a method, if nobody is registered for the named method,
	the first parameter provided will be returned.
	"""
	def __init__(self):
		self.__methods = {}
	
	def __return_defret(self, defret, *other):
		"""Return the first parameter provided.

		This is the dummy method used when a named method that nobody is
		registered for is called.
		"""
		return defret

	def __getattr__(self, name):
		return self.__methods.get(name) or self.__return_defret

	def register(self, name, method):
		self.__methods[name] = method
	
	def unregister(self, name):
		if self.__methods.has_key(name):
			del self.__methods[name]

class SoapMethods:
	def __init__(self):
		self.__func = {}
	
	def register(self, funcname, func):
		self.__func[funcname] = func
	
	def unregister(self, funcname):
		del self.__func[funcname]

	def get_methods(self):
		return self.__func

# vim:ts=4:sw=4
