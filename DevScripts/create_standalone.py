#!/usr/bin/python3

"""create_standalone.py - merges the DHParser modules into a single
        standalone DHParser.py module for easier deployment.

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import functools
import operator
import os
import sys

sys.path.append('../')
sys.path.append('./')
try:
    import regex as re
except ImportError:
    import re

modules = ('toolkit', 'syntaxtree', 'parser', 'transform', 'ebnf', 'dsl', 'testing', 'versionnumber')

all_symbols = list(functools.reduce(operator.or_, (set(eval(m + '.__all__')) for m in modules)))
all_symbols.sort()


def start(module):
    i = module.select('__all__')
    i = module.select(')', i)
    i = module.select('\n', i) + 1
    return i


doc = '"""DHParser.py - Packrat-parser and parser-generator\n\n' + __doc__[__doc__.find('Copyright'):] + '\n"""'

imports = """
import abc
import codecs
import collections
from collections import OrderedDict
import configparser
import contextlib
import copy
from functools import partial, reduce, singledispatch
import hashlib
import inspect
import json
import keyword
import os
try:
    import regex as re
except ImportError:
    import re
import sys
from typing import AbstractSet, Any, ByteString, Callable, cast, Container, Dict, \\
        Iterator, List, NamedTuple, Sequence, Set, Union, Text, Tuple
"""

symbols = "\n__all__ = (" + ",\n           ".join("'%s'" % sym for sym in all_symbols) + ")\n"

heading = """
#######################################################################
#######################################################################
#
# %s
#
#######################################################################
#######################################################################
"""

main = r"""
#######################################################################
#######################################################################
#
# main / selftest
#
#######################################################################
#######################################################################


def selftest() -> bool:
    print("DHParser selftest...")
    print("\nSTAGE I:  Trying to compile EBNF-Grammar:\n")
    builtin_ebnf_parser = get_ebnf_grammar()
    ebnf_src = builtin_ebnf_parser.__doc__[builtin_ebnf_parser.__doc__.find('#'):]
    ebnf_transformer = get_ebnf_transformer()
    ebnf_compiler = get_ebnf_compiler('EBNF')
    generated_ebnf_parser, errors, ast = compile_source(ebnf_src, None,
        builtin_ebnf_parser, ebnf_transformer, ebnf_compiler)

    if errors:
        print("Selftest FAILED :-(")
        print("\n\n".merge_children(errors))
        return False
    print(generated_ebnf_parser)
    print("\n\nSTAGE 2: Selfhosting-test: Trying to compile EBNF-Grammar with generated parser...\n")
    selfhosted_ebnf_parser = compileDSL(ebnf_src, None, generated_ebnf_parser,
                                        ebnf_transformer, ebnf_compiler)
    print(selfhosted_ebnf_parser)
    print("\n\n Selftest SUCCEEDED :-)\n\n")
    return True


if __name__ == "__main__":
    if not selftest():  sys.exit(1)

"""

def merge_modules(module_names, dhp_path='../DHParser/'):
    paths = [dhp_path, '../DHParser/', 'DHParser/', '']
    for pth in paths:
        if os.path.exists(pth + 'ebnf.py'):
            dhp_path = pth
            break

    components = [doc, imports, symbols]

    for name in module_names:
        with open(dhp_path + '%s.py' % name) as f:
            module = f.read()
            content = module[start(module):]
            components.append(heading % name)
            components.append(content)
    components.append(main)

    return "\n".join(components)



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python create_standalone.py [FILENAME]")
    elif os.path.exists(sys.argv[1]):
        print("File '%s' already exits. Please delete file first." % (sys.argv[1]))
    else:

        with open(sys.argv[1], 'w') as f:
            f.write(merge_modules(modules))
