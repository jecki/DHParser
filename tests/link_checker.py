#!/usr/bin/env python3

"""link_checker.py -- checks the links in README.txt and documentation."""

import os
import sys

scriptdir = os.path.dirname(os.path.abspath(__file__))
dhparserdir = os.path.abspath(os.path.join(scriptdir, os.pardir))
if dhparserdir not in sys.path:
    sys.path.append(dhparserdir)
os.chdir(dhparserdir)

docdir = "documentation_src"
def gather_docs():
    paths = []
    for root, dirs, files in os.walk(os.path.join(dhparserdir, docdir)):
        for f in files:
            if f.endswith('.rst') or f.endswith('.md'):
                paths.append(os.path.join(root, f))
    for f in os.listdir(dhparserdir):
        if f.endswith('.rst') or f.endswith('.md'):
            paths.append(os.path.join(dhparserdir, f))
    return paths

if __name__ == '__main__':
   for path in  gather_docs():
       print(path)
