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

from pybot import mm, hooks, config
from pybot.util import SOAPpy
import thread
import re

HELP = """
You may ask for google search results using "[search] google [<n>]:
<search>". Unless the parameter n is used, the default is to show the
first result found (with n=0). You'll need the "google" permission to
use that feature.
"""

PERM_GOOGLE = """
The "google" permission allows users to ask for google search results.
Check "help google" for more information.
"""

class Google:
    def __init__(self):
        if config.has_option("global", "http_proxy"):
            self.proxy = config.get("global", "http_proxy")
            self.proxy = re.sub(".*://", "", self.proxy)
        else:
            self.proxy = None
        self.key = config.get("google", "license_key")

        hooks.register("Message", self.message)

        # [search] google [<n>]: <search>
        self.re1 = re.compile(r"(?:search\s+)?google(?:\s+(?P<n>\d+))?:\s*(?P<search>.+)$", re.I)
        
        mm.register_help("(?:search\s+)?google(?:\s+search)?", HELP,
                         "google")

        mm.register_perm("google", PERM_GOOGLE)

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm("google")

    def search(self, msg, search, n):
        try:
            proxy = SOAPpy.SOAPProxy("http://api.google.com/search/beta2",
                                     namespace="urn:GoogleSearch",
                                     http_proxy=self.proxy)
            result = proxy.doGoogleSearch(self.key, search, n, 1,
                                          SOAPpy.booleanType(1), "",
                                          SOAPpy.booleanType(0), "",
                                          "", "")
            if not len(result.resultElements):
                msg.answer("%:", ["Nothing found",
                                  "Google couldn't find anything",
                                  "Google has its mind empty right now",
                                  "Google has never seen such thing"],
                                 [".", "!"])
            else:
                e = result.resultElements[0]
                url = e.URL
                title = re.sub("<.*?>", "", e.title)
                snippet = re.sub("<.*?>", "", e.snippet)
                if snippet:
                    msg.answer("%:", "%s <%s> - %s" % (title, url, snippet))
                else:
                    msg.answer("%:", "%s <%s>" % (title, url))
        except SOAPpy.Errors.Error:
            import traceback
            traceback.print_exc()
            msg.answer("%:", ["There was an error trying to ask google",
                              "Something wrong happened while trying to"
                              "ask google",
                              "I got some problem while trying to do that"],
                             [".", "!"])
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "google"):
                n = int(m.group("n") or 0)
                search = m.group("search")
                thread.start_new_thread(self.search, (msg, search, n))
            else:
                msg.answer("%:", ["You can't", "You're not allowed to",
                                  "You're not good enough to"],
                                 ["do google actions",
                                  "use google"], ["!", "."])
            return 0
    
def __loadmodule__():
    global mod
    mod = Google()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
