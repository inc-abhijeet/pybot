#!/usr/bin/python
import sys

def main():
	for filename in sys.argv[1:]:
		file = open(filename)
		nextisvalue = 0
		for line in file.xreadlines():
			if line[:6] == "@item ":
				print "K:"+line[6:].rstrip()
				nextisvalue = 1
			elif nextisvalue:
				print "V:tm:"+line.rstrip()
				nextisvalue = 0
		file.close()

if __name__ == "__main__":
	main()
