#!/usr/bin/python
#
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

import cPickle
import random
import string
import time
import sys
import os

# Check if we are inside the development environment
abspath = os.path.basename(os.path.abspath(sys.path[0]))
if os.path.basename(abspath) == "scripts":
    sys.path[:] = [os.path.dirname(abspath)]+sys.path

import pybot

random.seed(time.time())
	
def random_answer(*pattern):
	ret = []
	for tok in pattern:
		if type(tok) == type(()):
			recret = self._answer(tok)
			ret = ret + recret
		elif type(tok) == type([]):
			tmptok = tok[random.randint(0,len(tok)-1)]
			if type(tmptok) == type(""):
				ret.append(tmptok)
			elif tmptok != None:
				recret = self._answer(tmptok)
				ret.append(recret)
		elif tok != None:
			ret.append(tok)
	if ret:
		str = ret[0]
		for tok in ret[1:]:
			if tok[0] in [".","!","?"]:
				str = str+tok
			else:
				str = str+" "+tok
	else:
		str = ""
	return str

if len(sys.argv)==3 and sys.argv[1] in ["show","print"]:
	if os.path.exists("options"):
		file = open("options")
		option = cPickle.load(file)
		file.close()
		if not option.has_key(sys.argv[2]):
			print random_answer(["It seems that", "Sorry, but", "Sir,"], "there's not such option.")
		else:
			print option[sys.argv[2]]
	else:
		print "There's no options file, sir!"
elif len(sys.argv)>5 and sys.argv[1:3]==["set"] and sys.argv[4] == "to":
	if os.path.exists("options"):
		file = open("options")
		option = cPickle.load(file)
		file.close()               
	else:
		option = {}
	option[sys.argv[3]] = eval(string.join(sys.argv[5:]))
	file = open("options", "w")
	option = cPickle.dump(option,file,1)
	file.close()               
	print "Done, sir!"

# vim:ts=4:sw=4
