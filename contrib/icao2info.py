#!/usr/bin/python
#
# Script to convert an ASCII file providing station codes
# to a pybot infopack.
#
# The data file may be obtained from
#
#    http://weather.noaa.gov/tg/site.shtml
#

def main():
    for line in open("nsd_cccc.txt"):
        tokens = [x.strip() for x in line.split(";")]
        print "K:%s" % tokens[0]
        l = []
        l.append(tokens[3]) # Location
        if tokens[4]: # State, for US only
            l.append(tokens[4])
        if tokens[5]: # Country
            l.append(tokens[5])
        if tokens[1] != "--":
            l.append("WMO block %s" % tokens[1])
        if tokens[2] != "---":
            l.append("WMO station %s" % tokens[2])
        l.append("WMO region %s" % tokens[6])
        l.append("latitude %s" % tokens[7])
        l.append("longitude %s" % tokens[8])
        if tokens[9]:
            l.append("upper air latitude %s" % tokens[9])
        if tokens[10]: 
            l.append("upper air longitude %s" % tokens[10])
        if tokens[11]:
            l.append("elevation of %sm" % tokens[11])
        try:
            if tokens[12]:
                l.append("upper air elevation of %sm" % tokens[12])
            if tokens[13] == "P":
                l.append("RBSN")
        except IndexError:
            pass
        print "V:tm:"+", ".join(l)

if __name__ == "__main__":
    main()
