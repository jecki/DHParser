"""collect_symbols.py - Lists all exported symbols from DHParser modules

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

import sys
import textwrap

sys.path.append('../')

from DHParser import toolkit
from DHParser import syntaxtree
from DHParser import parse
from DHParser import transform
from DHParser import ebnf
from DHParser import dsl
from DHParser import testing
from DHParser import versionnumber

symbols_table = {
    'toolkit': list(toolkit.__all__),
    'syntaxtree': list(syntaxtree.__all__),
    'parser': list(parse.__all__),
    'transform': list(transform.__all__),
    'ebnf': list(ebnf.__all__),
    'dsl': list(dsl.__all__),
    'testing': list(testing.__all__),
    'versionnumber': list(versionnumber.__all__)
}

DSL_imports = {'parser', 'syntaxtree', 'transform'}

all_symbols = []
for module, symbols in symbols_table.items():
    assert len(set(symbols)) == len(symbols), "Double symbols in field '__all__' of module " + module
    for sym in symbols:
        exec("from DHParser.%s import %s" % (module, sym))
    symbols_copy = tuple(symbols)
    symbols.sort()
    if symbols_copy != tuple(symbols):
        print()
        print(module)
        all = "__all__ = (" + ",\n           ".join("'%s'" % s for s in symbols) + ")"
        print(all)
        print()
        all = "\n    ".join(textwrap.wrap("from DHParser.%s import " % module + ", ".join(symbols), 99))
        print(all)
    if module in DSL_imports:
        all_symbols.extend(symbols)

assert len(set(all_symbols)) == len(all_symbols), "Double symbols in module " + module
all_symbols.extend(['logging', 'is_filename', 'load_if_file'])
all_symbols.sort()
print()
print("DSL-imports")
all = "\n   ".join(textwrap.wrap("from DHParser import " + ", ".join(all_symbols), 99))
print(all)
