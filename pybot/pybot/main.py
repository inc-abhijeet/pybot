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

from time import time, sleep
import traceback
import random
import signal
import sys

from pybot.command import Command
import pybot

class Main:
	"""Main pybot class.
	"""
	def __init__(self):
		random.seed(time())
		self.reboot = 0
		self.quit = 0
		# Aaron told SIGQUIT is not available in Windows. We must figure
		# out which platforms it is available and what's the most clean
		# way to use it.
		# signal.signal(signal.SIGQUIT, self.signalhandler)
		signal.signal(signal.SIGTERM, self.signalhandler)
	
	def signalhandler(self, signum, frame):
		self.quit = 1
		for server in self.servers:
			server.sendline("QUIT :Argh!")
	
	def loop(self):
		hooknames = ["Message", "Notice", "Command", "CTCP", "CTCPReply"]
		callhook = pybot.hooks.call
		servers = pybot.servers.getall()
		myrange = range
		killed = []
		try:
			while 1:
				for i in killed:
					del servers[i]
				killed = []
				for i in myrange(len(servers)):
					server = servers[i]
					server.interaction()
					if server.killed:
						killed.append(i)
					else:
						for n in myrange(10):
							line = server.readline()
							if not line:
								break
							cmd = Command()
							cmd.setline(server, line)
							hookname = hooknames[cmd._index]
							ret = callhook(hookname, cmd)
							if cmd.forme and cmd._index == 0 and not (0 in ret or -1 in ret):
								callhook("UnhandledMessage", cmd)
				callhook("Loop")
				sleep(0.5)
				if self.reboot:
					for server in servers:
						server.kill()
						server.interaction()
					callhook("Reboot")
					sleep(2)
					return 0
				elif self.quit:
					for server in servers:
						server.kill()
						server.interaction()
					callhook("Quit")
					return 100
		except KeyboardInterrupt:
			for server in servers:
				server.sendline("QUIT :Argh!")
				server.kill()
				server.interaction()
			callhook("Quit")
			return 100

# vim:ts=4:sw=4
