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

import os
import sys
import string
import random
import time
import cPickle
import pybot

if os.path.isfile("options"):
	file = open("options")
	option = cPickle.load(file)
	file.close()               
else:
	option = {}

try:
	print """
This program does the basic setup for pybot. It will allow you to
set the first nick, username and server you want pybot to connect,
and also who you are (supposing you're the one who pybot will obey
to). Further setup (including connecting to other servers and
setting new masters) may be done talking with him, after connected.

You may also use it to recover a previous setup. You may need to
do so if your nick is takeovered or if pybot is not able to connect
to any servers. In this case, this program will overwrite your
basic configuration (servers and masters), but will preserve
everything else.
"""
	raw_input("Press [ENTER] to continue...")

	print """
Enter the nick you're going to use while talking to pybot."""
	nick = raw_input("Your nick: ")

	print """Enter the username you're going to use while talking to pybot.
Please, note that you may have a '~' added to your username, depending on
your host's configuration. If you want to be sure what your username is,
issue a '/whois %s' while connected to your irc server. You may also
use a wildcard, like *username, if you're not sure at all."""%nick
	username = raw_input("Your username: ")

	print """
Enter the hostname you're going to use while talking to pybot.
If you're not sure, you should also look at the output of the command
'/whois %s' while connected to your irc server. A wildcard like
*.my.host also work here, but be careful!"""%nick
	hostname = raw_input("Your host: ")

	print """
Enter the server name:port where pybot will connect to. This is
just to start it out. You may add and/or remove servers later talking
with him."""
	server = raw_input("Server: ")

	print """
Enter the pybot nick you want to use in this server. That's important
because you'll be able to tell him to join a channel and/or connect
to a server by talking with him, so make sure you remember the nick."""
	pybotnick = raw_input("Pybot's nick: ")

	print """
Enter the username pybot will use in this server."""
	pybotusername = raw_input("Pybot's username: ")

	print """
Enter the real name pybot will use in this server."""
	pybotrealname = raw_input("Pybot's real name: ")
except EOFError:
	sys.exit("Interrupted!")

option["Permission.gosh"] = [pybot.User(nick, username, hostname)]
option["ServerControl.servers"] = {server:[pybotnick, pybotusername, "0", pybotrealname, []]}

file = open("options", "w")
option = cPickle.dump(option,file,1)
file.close()

print "Options saved!"

# vim:ts=4:sw=4
