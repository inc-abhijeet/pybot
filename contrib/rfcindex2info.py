#!/usr/bin/python
import re

KEY = re.compile("(?P<key>\d+)\s+(?P<content>.+)$")
MORE = re.compile("\s+(?P<content>.+)$")


def main():
    foundfirst = 0
    for line in open("1rfc_index.txt"): 
        m = KEY.match(line)
        if m:
            foundfirst = 1
            print "K:"+m.group("key")
            print "V:tm:"+m.group("content"),
            continue

        if not foundfirst:
            continue

        m = MORE.match(line)
        if m:
            print m.group("content"),
            continue

        print

if __name__ == "__main__":
    main()
