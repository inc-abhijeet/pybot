#!/usr/bin/python
import sys

def main():
    lastkey = None
    append = 0
    nextisvalue = 0
    for filename in sys.argv[1:]:
        file = open(filename)
        nextisvalue = 0
        for line in file.xreadlines():
            if line[:6] == "@item ":
                key = line[6:].rstrip()
                if key != lastkey:
                    if lastkey and not nextisvalue:
                        sys.stdout.write("\n")
                    lastkey = key
                    sys.stdout.write("K:%s\n" % key)
                    append = 0
                else:
                    append = 1
                nextisvalue = 1
            elif nextisvalue:
                value = line.rstrip()
                if not append:
                    sys.stdout.write("V:tm:%s" % value)
                elif lastkey != "VERA":
                    sys.stdout.write(", %s" % value)
                else:
                    sys.stdout.write("Virtual Entity of Relevant Acronyms")
                nextisvalue = 0
        file.close()
    if lastkey and not nextisvalue:
        sys.stdout.write("\n")

if __name__ == "__main__":
    main()

# vim:ts=4:sw=4:et
