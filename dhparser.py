#!/usr/bin/python3

"""dhparser.py - command line tool for DHParser

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

import os
import sys
from functools import partial

from DSLsupport import compileDSL, run_compiler
from EBNFcompiler import EBNFGrammar, EBNFTransTable, EBNFCompiler
from parser import full_compilation


def selftest(file_name):
    print(file_name)
    with open('examples/' + file_name, encoding="utf-8") as f:
        grammar = f.read()
    compiler_name = os.path.basename(os.path.splitext(file_name)[0])
    compiler = EBNFCompiler(compiler_name, grammar)
    parser = EBNFGrammar()
    result, errors, syntax_tree = full_compilation(grammar,
                                                   parser, EBNFTransTable, compiler)
    print(result)
    if errors:
        print(errors)
        sys.exit(1)
    else:
        result = compileDSL(grammar, result, EBNFTransTable, compiler)
        print(result)
    return result


def profile(func):
    import cProfile
    pr = cProfile.Profile()
    pr.enable()
    func()
    pr.disable()
    # after your program ends
    pr.print_stats(sort="tottime")


# # Changes in the EBNF source that are not reflected in this file could be
# # a source of sometimes obscure errors! Therefore, we will check this.
# if (os.path.exists('examples/EBNF/EBNF.ebnf')
#     and source_changed('examples/EBNF/EBNF.ebnf', EBNFGrammar)):
#     assert False, "WARNING: Grammar source has changed. The parser may not " \
#         "represent the actual grammar any more!!!"
#     pass

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) > 1:
        _errors = run_compiler(sys.argv[1],
                               sys.argv[2] if len(sys.argv) > 2 else "")
        if (_errors):
            print(_errors)
            sys.exit(1)
    else:
        # run self test
        # selftest('EBNF/EBNF.ebnf')
        profile(partial(selftest, file_name='EBNF/EBNF.ebnf'))
