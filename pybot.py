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

import imp
import sys
import os
import time

def main():
    try:
        module = imp.find_module("pybot/runner")
    except ImportError:
        sys.exit("error: couldn't find module pybot.runner")
    module[0].close()
    args = ' '.join(["'%s'"%x for x in sys.argv[1:]])
    while 1:
        ret = os.system("python %s %s" % (module[1], args))
        if ret != 0:
            break
        time.sleep(5)

if __name__ == "__main__":
    main()

# vim:sw=4:ts=4:et
