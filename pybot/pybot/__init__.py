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

def init():
    from pybot.module import Modules, ModuleMethods, RemoteMethods
    from pybot.option import Options
    from pybot.server import Servers
    from pybot.hook import Hooks
    from pybot.main import Main
    from pybot.sqlitedb import SQLiteDB
    
    from ConfigParser import ConfigParser
    import os
    
    global main, modls, servers, options, hooks, mm, rm, config, db
    
    hooks = Hooks()
    servers = Servers()

    options = Options()
    modls = Modules()
    mm = ModuleMethods()
    rm = RemoteMethods()

    config = ConfigParser()
    defaults = config.defaults()

    if os.path.isfile("./pybot.conf") and os.path.isdir("pybot"):
        config.read("./pybot.conf")
        defaults["datadir"] = os.path.abspath("./data")
    elif os.path.isfile(os.path.expanduser("~/.pybot/config")):
        config.read(os.path.expanduser("~/.pybot/config"))
        defaults["datadir"] = os.path.expanduser("~/.pybot/data")
    elif os.path.isfile("/etc/pybot.conf"):
        config.read("/etc/pybot.conf")
        defaults["datadir"] = ("/var/lib/pybot")

    db = SQLiteDB()
    
    main = Main()
    
# vim:ts=4:sw=4:et
