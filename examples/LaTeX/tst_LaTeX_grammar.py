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

from DHParser import configuration
from DHParser import dsl
import DHParser.log
from DHParser import testing


configuration.CONFIG_PRESET['test_parallelization'] = True


def recompile_grammar(grammar_src, force):
    with DHParser.log.logging(False):
        # recompiles Grammar only if it has changed
        if not dsl.recompile_grammar(grammar_src, force=force):
            print('\nErrors while recompiling "%s":' % grammar_src +
                  '\n--------------------------------------\n\n')
            with open('LaTeX_ebnf_ERRORS.txt') as f:
                print(f.read())
            sys.exit(1)


def run_grammar_tests(glob_pattern):
    with DHParser.log.logging(False):
        error_report = testing.grammar_suite('grammar_tests', get_grammar, get_transformer,
            fn_patterns=[glob_pattern], report=True, verbose=True)
    return error_report


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '*_test_*.ini'
    if arg.endswith('.ebnf'):
        recompile_grammar(arg, force=True)
    else:
        recompile_grammar('LaTeX.ebnf', force=True)
        sys.path.append('.')
        from LaTeXCompiler import get_grammar, get_transformer
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.')

