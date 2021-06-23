#!/usr/bin/python

"""fixes wrongly abbreviated strategy names in the statistics' .eps-files"""

from __future__ import with_statement
import os, re

transtable = { "AM: DDHDH \\\\\(TIT FOR TAT" : "AM: DDHDH \\(TIT FOR TAT\\)",
               "AM: HDHDH \\\\\(TAT FOR TIT" : "AM: HDHDH \\(TAT FOR TIT\\)",
               "P_TFT 0.00 0.00 \\\\\(TitFo" : "P_TFT 0.00 0.00 \\(TitForTat\\)",
               "P_TFT 1.00 1.00 \\\\\(Inver" : "P_TFT 1.00 1.00 \\(Inverted\\)" }

def fixFile(name):
    base, ext = os.path.splitext(name)
    backup_name = base + "_backup" + ext
    os.rename(name, backup_name)

    with file(backup_name) as f: eps = f.read()
    for k in transtable.iterkeys():
        # print re.findall(k, eps)
        eps = re.sub(k, transtable[k], eps)
    with file(name, "w") as f: f.write(eps)

def visit(arg, dirname, names):
    if "Statistics" in dirname:
        print dirname
        for name in names:
            if ".eps" in name: fixFile(dirname+"/"+name)
    else:
        for name in names:
            if "Statistics" not in name:  names.remove(name)


if __name__ == "__main__":
    path = "/home/eckhart/Simulations/"
    dirs = ["BigSeries"]
    for d in dirs:
        os.path.walk(path+d, visit, 0)
    #fixFile("test1.eps")
    #fixFile("test2.eps")
