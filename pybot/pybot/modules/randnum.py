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
from random import randint

class Randnum:
	def __init__(self, bot):
		hooks.register("Message", self.message)
	
	def unload(self):
		hooks.unregister("Message", self.message)
	
	def message(self, msg):
		var = []
		if msg.match(var, 3, "%", ["give", "tell", "show"], ["me", None], 0, "~", ["random", None], ["number", "numbers"], "between", 1, "~", "and", 2, "~", ["!", ".", None]):
			try:
				if var[0] in ["a", "one"]:
					n = 1
				else:
					n = int(var[0])
				s = int(var[1])
				e = int(var[2])
				randint(s,e)
			except:
				msg.answer("%:", ["Your numbers are not valid", "I need valid numbers", "You must give me valid numbers", "There's a problem with your numbers", "You gave me invalid numbers"], [", sir!","!","."])
				return
			if n > 0:
				if n < 11:
					nums = str(randint(s,e))
					i = 1
					while i < n:
						num = randint(s,e)
						if i == n-1:
							if n > 2:
								nums = nums+", and "+str(num)
							else:
								nums = nums+" and "+str(num)
						else:
							nums = nums+", "+str(num)
						i = i + 1
					if n == 1:
						isare = "number is"
					else:
						isare = "numbers are"
					msg.answer("%:", ["Your", "The", "The choosen"], isare, nums, ["!", "."])
				else:
					msg.answer("%:", "You", ["have to", "must", "should"], "ask 10 numbers, at most", ["!", "."])
			else:
				msg.answer("%:", "You", ["have to", "must", "should"], "ask 1 number, at least", ["!", "."])
			return 0


def __loadmodule__(bot):
	global randnum
	randnum = Randnum(bot)

def __unloadmodule__(bot):
	global randnum
	randnum.unload()
	del randnum

# vim:ts=4:sw=4
