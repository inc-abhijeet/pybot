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

from pybot.locals import *
from pybot.util import pymetar

HELP = """
You can check the weather condition at any station registered at the
National Oceanic and Atmospheric Administration (NOAA). To do that,
use the command "[show] weather [for|from|on|at|in] <code>", providing
the four-letters code assigned by The ICAO to the station. You need
the "weather" permission for that.
"""

PERM_WEATHER = """
The "weather" permission allows users check for weather conditions
on serveral stations. For more information, check "help weather".
"""

class Weather:
    def __init__(self):
        hooks.register("Message", self.message)
    
        # [show] weather [for|from|on|at|in] <station>
        self.re1 = regexp(r"(?:show )?weather (?:for |from |on |at |in )?(?P<station>\S+?)")

        mm.register_help(r"weather", HELP, "weather")

        mm.register_perm("weather", PERM_WEATHER)

    def unload(self):
        hooks.unregister("Message", self.message)
        mm.unregister_help(HELP)
        mm.unregister_perm(PERM_WEATHER)
    
    def message(self, msg):
        if not msg.forme:
            return None

        m = self.re1.match(msg.line)
        if m:
            if mm.hasperm(msg, "weather"):
                station = m.group("station")
                try:
                    r = pymetar.MetarReport(station)
                except:
                    msg.answer("%:", "There was an error fetching "
                                     "weather information",
                                     [".", "!"])
                else:
                    l = []
                    l.append("Weather in %s, %s (%s), at %s:" %
                             (r.getStationCity(),
                              r.getStationCountry(), station.upper(),
                              r.getISOTime()))
                    l.append("%s," % r.extractCloudInformation()[0].lower())
                    l.append("temperature of %.2fC (%.2fF)," %
                             (r.getTemperatureCelsius(),
                              r.getTemperatureFahrenheit()))
                    l.append("windspeed of %.2fkm/h (%s)," %
                             (r.getWindSpeed(), r.getWindCompass()))
                    l.append("visibility of %.2fkm." % (r.getWindSpeed()))
                    msg.answer("%", " ".join(l))
            else:
                msg.answer("%:", ["You have no permission for that",
                                  "You are not allowed to do this",
                                  "You can show weather"],
                                 [".", "!"])
            return 0

def __loadmodule__():
    global mod
    mod = Weather()

def __unloadmodule__():
    global mod
    mod.unload()
    del mod

# vim:ts=4:sw=4:et
