#!/usr/bin/env python

"""Writes the all docstrings from a python-file into one long
reStructuredText-file. Running python -m docutils NAME.rst > NAME.html
yields the exact location of errors in that file, something where
sphinx habitually screws up!"""


import sys, os

fname = sys.argv[1]
with open(fname, 'r') as f:
    source = f.read()

rst_lines = []
lines = source.split('\n')
i = 0
while i < len(lines):
    if lines[i].lstrip()[:3] in ('"""', 'r""'):
        n = 4 if lines[i].lstrip()[:3] == 'r""' else 3
        rst_lines.append(lines[i].lstrip()[n:])
        if rst_lines[-1].rstrip()[-3:] == '"""':
           rst_lines[-1] = rst_lines[-1].rstrip()[:-3]
        else:
            k = i + 1
            indent = len(lines[k]) - len(lines[k].lstrip())
            while lines[k].rstrip()[-3:] != '"""':
                rst_lines.append(lines[k][indent:])
                k += 1
            rst_lines.append(lines[k].rstrip()[indent:-3])
            rst_lines.append('')
            i = k + 1
    i += 1

rst_name = os.path.splitext(fname)[0] + '.rst'
with open(rst_name, 'w') as f:
    f.write('\n'.join(rst_lines))

print('ready.')
