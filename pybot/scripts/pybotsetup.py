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
import shutil

if os.path.isdir("pybot"):
    sys.path.append(".")

if os.path.isfile("options"):
    file = open("options")
    option = cPickle.load(file)
    file.close() 
else:
    option = {}

from pybot.user import User

try:
    print """
This program does the basic setup for pybot. It will allow you to
set the first nick, username and server you want pybot to connect.
Further setup (including setting administrators and connecting to
channels and servers) may be done by talking with him, after connected.

You may also use it to recover a previous setup. You may need to
do so if your nick is takeovered or if pybot is not able to connect
to any servers. In this case, this program will overwrite your
basic configuration (servers and masters), but will preserve
everything else.
"""
    raw_input("Press [ENTER] to continue...")

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

if option["Permission.perm"].has_key("admin"):
    del option["Permission.perm"]["admin"]
option["ServerControl.servers"] = {server:[pybotnick, pybotusername, "0", pybotrealname, {}]}
option["ModuleControl.modules"] = ["servercontrol", "pong", "permission", "help", "social"]

# Clean old permission system
if option.has_key("Permission.gosh"):
    del option["Permission.gosh"]

if os.path.isfile("options"):
    shutil.copyfile("options", "options.old")
file = open("options", "w")
option = cPickle.dump(option,file,1)
file.close()

print """
Options saved!

WARNING: As soon as your bot connects to the new server, you must set
the "admin" permission, otherwise your bot will be free to hack by
anyone. To understand how to do this, ask the bot "help permissions".
"""

# vim:ts=4:sw=4:et
