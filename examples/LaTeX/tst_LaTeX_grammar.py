#!/usr/bin/env python3

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

import os
import sys


scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('..', '..'), '.'):
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)


from DHParser import dsl
import DHParser.log
from DHParser import testing
from DHParser.configuration import access_presets, set_preset_value, finalize_presets


def recompile_grammar(grammar_src, force):
    # recompiles Grammar only if it has changed
    grammar_path = os.path.join(fullpath, grammar_src)
    if not dsl.recompile_grammar(grammar_path, force=force,
                                 notify=lambda :print('grammar changed: recompling')):
        print('\nErrors while recompiling "%s":' % grammar_src +
              '\n--------------------------------------\n\n')
        with open('LaTeX_ebnf_ERRORS.txt') as f:
            print(f.read())
        sys.exit(1)


def run_grammar_tests(glob_pattern):
    test_path = os.path.join(fullpath, 'test_grammar')
    DHParser.log.start_logging(os.path.join(test_path, 'LOGS'))
    error_report = testing.grammar_suite(
        test_path, get_grammar, get_transformer, fn_patterns=[glob_pattern], report='REPORT',
        verbose=True)
    return error_report


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '*_test_*.ini'
    access_presets()
    # set_preset_value('ast_serialization', 'XML')
    set_preset_value('test_parallelization', False)
    set_preset_value('history_tracking', True)
    finalize_presets()
    if arg.endswith('.ebnf'):
        recompile_grammar(arg, force=True)
    else:
        recompile_grammar('LaTeX.ebnf', force=False)
        sys.path.append('.')
        from LaTeXParser import get_grammar, get_transformer
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.')
