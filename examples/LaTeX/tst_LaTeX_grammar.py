#!/usr/bin/python3

"""tst_LaTeX_grammar.py - runs the unit tests for the LaTeX grammar

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2017 Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys

sys.path.extend(['../../', '../', './'])

import DHParser.dsl
from DHParser import testing

if not DHParser.dsl.recompile_grammar('LaTeX.ebnf', force=False):  # recompiles Grammar only if it has changed
    print('\nErrors while recompiling "LaTeX.ebnf":\n--------------------------------------\n\n')
    with open('LaTeX_ebnf_ERRORS.txt') as f:
        print(f.read())
    sys.exit(1)

from LaTeXCompiler import get_grammar, get_transformer

with toolkit.logging(True):
    error_report = testing.grammar_suite('grammar_tests', get_grammar,
                                         get_transformer, report=True, verbose=True)
if error_report:
    print('\n')
    print(error_report)
    sys.exit(1)
else:
    print('\nSUCCESS! All tests passed :-)')
