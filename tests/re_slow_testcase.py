#!/usr/bin/env python3

"""This testcase exposes a performance bug in the `re`-module of
the python standard-library:

>>> import re, timeit
>>> rx = re.compile('(\\s*(#.*)?\\s*)*X')
>>> print(timeit.timeit("rx.match('            #  ')", number=1, globals=globals()))
24.814577618999465
>>> print(timeit.timeit("rx.match('             #   ')", number=1, globals=globals()))
291.2432912450022

Please note the number of repetitions: number=1 !!!
"""

import timeit

try:
    import regex

    rx = regex.compile('(\\s*(#.*)?\\s*)*X')
    print("The 'new' regex module:")
    print(timeit.timeit("rx.match('              #    ')",
                        number=1, globals=globals()))


except ImportError:
    pass

import re

rx = re.compile('(\\s*(#.*)?\\s*)*X')
print("The re module of the Python standard library:")
print(timeit.timeit("rx.match('              #    ')",
                    number=1, globals=globals()))
