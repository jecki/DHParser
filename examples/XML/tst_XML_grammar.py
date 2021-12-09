#!/usr/bin/env python3

"""tst_XML_grammar.py - runs the unit tests for the XML-grammar
"""

import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('..', '..'), '.'):
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)


try:
    from DHParser import dsl
    import DHParser.log
    from DHParser import testing
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


def recompile_grammar(grammar_src, force):
    # recompiles Grammar only if it has changed

    if not dsl.recompile_grammar(grammar_src, force=force):
        print('\nErrors while recompiling "%s":' % grammar_src +
              '\n--------------------------------------\n\n')
        error_path = os.path.join(grammar_src[:-5] + '_ebnf_ERRORS.txt')
        with open(error_path) as f:
            print(f.read())
        sys.exit(1)


def run_grammar_tests(glob_pattern):
    error_report = testing.grammar_suite(
        os.path.join(scriptpath, 'test_grammar'),
        get_grammar, get_transformer,
        fn_patterns=[glob_pattern], verbose=True)
    return error_report


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '*_test_*.ini'
    if arg.endswith('.ebnf'):
        from DHParser.configuration import set_config_value
        set_config_value('syntax_variant', 'heuristic')
        recompile_grammar(arg, force=True)
    else:
        recompile_grammar(os.path.join(scriptpath, 'XML.ebnf'), force=False)
        sys.path.append('.')
        from XMLParser import get_grammar, get_transformer
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.\n')
