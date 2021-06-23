#!/usr/bin/python
#check_superfluous.py - looks for superfluous image directories in the 
#    monte carlo series

import sys, os

if len(sys.argv) > 1:  path = sys.argv[1]
else:  path = "."

raw_dir = os.listdir(path)
pages = set([entry[7:-5] for entry in raw_dir if entry.endswith(".html")])
directories = set([entry[:-7] for entry in raw_dir if entry.endswith("_images")])
superfluous_directories = directories - pages
superfluous_pages = pages - directories

print "directories that are not related to any html page:"
for d in superfluous_directories: print d
print

print "html pages for which the image directory is missing:"
for p in superfluous_pages: 
    if p.find("_nav") < 0 and p.find("rames") < 0: print p


