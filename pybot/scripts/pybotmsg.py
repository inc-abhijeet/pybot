#!/usr/bin/python
import xmlrpclib
import sys

# You'll probably want to "chmod 700" this script.

AUTH = {"username":	"<username>",
        "password":	"<password>",
        "server":	"irc.example.com",
        "target":	"#channel"}

PYBOT = "http://pybot.host:8460"

if len(sys.argv) != 2:
    sys.exit("Usage: pybotmsg.py \"Message ...\"")

proxy = xmlrpclib.ServerProxy(PYBOT)
proxy.sendmsg(AUTH, sys.argv[1], 1)
