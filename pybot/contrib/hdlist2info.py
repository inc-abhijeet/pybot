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
        distronames = distros.keys()
        distronames.sort()
        for distroname in distronames:
            if v:
                v += "; "
            versions = distros[distroname].keys()
            versions.sort()
            v += "%s: %s" % (distroname, ", ".join(versions))
        file.write("V:tm:%s\n" % v)
    file.close()

if __name__ == "__main__":
    main()

