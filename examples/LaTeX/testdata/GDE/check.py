#!/usr/bin/python

import sys

fname = sys.argv[1]
with open(fname, "r") as f:
    for line in f:
        print(line)
