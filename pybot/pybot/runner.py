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

import sys
import os

# Add upper directory to search path in case we are in development tree.
sys.path[0] = os.path.dirname(sys.path[0])

import pybot

def print_cmd(cmd):
	print "Command(%s): %s"%(cmd.cmd, cmd.line)

def print_msg(msg):
	print "Message(%s/%s): %s"%(msg.target, msg.user.nick, msg.line)

def print_not(msg):
	print "Notice(%s/%s): %s"%(msg.target, msg.user.nick, msg.line)

def print_connected(server):
	print "Connected to %s!"%server.servername

def print_connection_error(server):
	print "Connection error on %s!"%server.servername

def print_connecting_error(server):
	print "Error connecting to %s!"%server.servername

def main():
	pybot.init() # Initialize globaly acessible data
	pybot.hooks.register("Command", print_cmd)
	pybot.hooks.register("Message", print_msg)
	pybot.hooks.register("Notice", print_not)
	pybot.hooks.register("Connected", print_connected)
	pybot.hooks.register("ConnectionError", print_connection_error)
	pybot.hooks.register("ConnectingError", print_connecting_error)
	pybot.modls.load("options")
	pybot.modls.load("modulecontrol")
	ret = pybot.main.loop()
	sys.exit(ret)

if __name__ == "__main__":
	main()

# vim:ts=4:sw=4:et
