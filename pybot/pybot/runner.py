#!/usr/bin/python
#
# Copyright (c) 2000-2003 Gustavo Niemeyer <niemeyer@conectiva.com>
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

import sys, os
import getopt

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

USAGE = """\
Usage: pybot.py [OPTIONS]

Options:
    -c    Enable console
    -d    Enable debug mode
    -h    Show this message

"""

def parse_options():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "cdh", ["help"])
    except getopt.GetoptError, e:
        sys.exit("error: "+e.msg)
    class Options: pass
    obj = Options()
    obj.console = 0
    obj.debug = 0
    for opt, val in opts:
        if opt == "-c":
            obj.console = 1
        elif opt == "-d":
            obj.debug = 1
        elif opt in ["-h", "--help"]:
            sys.stdout.write(USAGE)
            sys.exit(1)
    return obj

def main():
    pybot.init() # Initialize globally acessible data
    opts = parse_options()
    if opts.console:
        pybot.servers.add_console()
    if opts.debug:
        pybot.hooks.register("Command", print_cmd)
        pybot.hooks.register("Message", print_msg)
        pybot.hooks.register("Notice", print_not)
        pybot.hooks.register("Connected", print_connected)
        pybot.hooks.register("ConnectionError", print_connection_error)
        pybot.hooks.register("ConnectingError", print_connecting_error)

    # Load modules which are part of the basic infrastructure
    defaultlist = [
                    "help",
                    "options",
                    "timer",
                    "modulecontrol",
                    "permission",
                    "pong",
                    "servercontrol",
                    "userdata",
                  ]
    pybot.modls.loadlist(defaultlist)
    ret = pybot.main.loop()
    sys.exit(ret)

if __name__ == "__main__":
    main()

# vim:ts=4:sw=4:et
