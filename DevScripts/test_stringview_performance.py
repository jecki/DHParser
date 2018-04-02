#!/usr/bin/python

import sys

sys.path.append('../')

from DHParser.stringview import StringView
from timeit import timeit
import re

sv = StringView("          01234567890          ")
rx = re.compile('\s*')

print(timeit('s = sv[10:21]', number=5_000_000, globals=globals()))


print(timeit('m=sv.match(rx)', number=5_000_000, globals=globals()))


print(timeit('sv.strip()', number=10_000_000, globals=globals()))

sv = StringView("100, 200, 300, 400, 500, 600, 700, 800, 900")

print(timeit('sv.split(", ")', number=5_000_000, globals=globals()))

