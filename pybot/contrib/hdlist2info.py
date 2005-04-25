#!/usr/bin/python
import sys, os
import rpm

def main():
    if len(sys.argv) != 4:
        sys.exit("Usage: hdlist2ipack.py <label> <hdlist> <infopack>")
    label = sys.argv[1]
    hdlistname = sys.argv[2]
    ipackname = sys.argv[3]
    packages = {}
    if os.path.exists(ipackname):
        file = open(ipackname)
        name = None
        for line in file.readlines():
            if line[0] == "K":
                name = line.rstrip().split(":")[1]
            elif name and line[0] == "V":
                value = line.rstrip().split(":", 2)[2]
                for pair in value.split(";"):
                    distrostr, versionstr = pair.split(":", 1)
                    distros = packages.setdefault(name, {})
                    versions = distros.setdefault(distrostr.strip(), {})
                    for version in versionstr.split(","):
                        versions[version.strip()] = 1
        file.close()
    for h in rpm.readHeaderListFromFile(hdlistname):
        if h["epoch"]:
            version = "%s:%s-%s" % (h["epoch"], h["version"], h["release"])
        else:
            version = "%s-%s" % (h["version"], h["release"])
        distros = packages.setdefault(h["name"].lower(), {})
        versions = distros.setdefault(label, {})
        versions[version] = 1
    if os.path.exists(ipackname):
        file = open(ipackname)
        oldlines = file.readlines()
        file.close()
    else:
        oldlines = []
    file = open(ipackname, "w")
    for line in oldlines:
        if line[0] not in ("K", "V"):
            file.write(line)
    packagenames = packages.keys()
    packagenames.sort()
    for packagename in packagenames:
        file.write("K:%s\n" % packagename)
        v = ""
        distros = packages[packagename]
        distronames = [SortStr(x) for x in distros.keys()]
        distronames.sort()
        for distroname in distronames:
            if v:
                v += "; "
            versions = distros[distroname].keys()
            versions.sort()
            v += "%s: %s" % (distroname, ", ".join(versions))
        file.write("V:tm:%s\n" % v)
    file.close()

class SortStr(str):
    def __cmp__(self, other):
        return vercmppart(str(self), str(other))
    def __lt__(self, other):
        return cmp(self, other) < 0
    def __eq__(self, other):
        return cmp(self, other) == 0
    def __gt__(self, other):
        return cmp(self, other) > 0

def vercmppart(a, b):
    if a == b:
        return 0
    ai = 0
    bi = 0
    la = len(a)
    lb = len(b)
    while ai < la and bi < lb:
        while ai < la and not a[ai].isalnum(): ai += 1
        while bi < lb and not b[bi].isalnum(): bi += 1
        aj = ai
        bj = bi
        if a[aj].isdigit():
            while aj < la and a[aj].isdigit(): aj += 1
            while bj < lb and b[bj].isdigit(): bj += 1
            isnum = 1
        else:
            while aj < la and a[aj].isalpha(): aj += 1
            while bj < lb and b[bj].isalpha(): bj += 1
            isnum = 0
        if aj == ai:
            return -1
        if bj == bi:
            return isnum and 1 or -1
        if isnum:
            while ai < la and a[ai] == '0': ai += 1
            while bi < lb and b[bi] == '0': bi += 1
            if aj-ai > bj-bi: return 1
            if bj-bi > aj-ai: return -1
        rc = cmp(a[ai:aj], b[bi:bj])
        if rc:
            return rc
        ai = aj
        bi = bj
    if ai == la and bi == lb:
        return 0
    if ai == la:
        return -1
    else:
        return 1

if __name__ == "__main__":
    main()

