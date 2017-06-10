#!/usr/bin/python

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

# TODO: This is still a stub...

import os
import sys
from functools import partial

from DHParser.dsl import compileDSL, compile_on_disk
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.parsers import compile_source, nil_scanner
from DHParser.toolkit import logging


def selftest(file_name):
    print(file_name)
    with open('examples/' + file_name, encoding="utf-8") as f:
        grammar = f.read()
    compiler_name = os.path.basename(os.path.splitext(file_name)[0])
    parser = get_ebnf_grammar()
    transformer = get_ebnf_transformer()
    compiler = get_ebnf_compiler(compiler_name, grammar)
    result, errors, syntax_tree = compile_source(grammar, None, parser,
                                                 transformer, compiler)
    print(result)
    if errors:
        print('\n\n'.join(errors))
        sys.exit(1)
    else:
        # compile the grammar again using the result of the previous
        # compilation as parser
        result = compileDSL(grammar, nil_scanner, result, transformer, compiler)
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
        _errors = compile_on_disk(sys.argv[1],
                                  sys.argv[2] if len(sys.argv) > 2 else "")
        if _errors:
            print('\n\n'.join(_errors))
            sys.exit(1)
    else:
        # run self test
        # selftest('EBNF/EBNF.ebnf')
        with logging(False):
            profile(partial(selftest, file_name='EBNF/EBNF.ebnf'))
