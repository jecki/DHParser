#!/usr/bin/python3

"""tst_XMLSnippet_grammar.py - runs the unit tests for the XMLSnippet-grammar
"""

import os
import sys

sys.path.append(r'/home/eckhart/Entwicklung/DHParser')

scriptpath = os.path.dirname(__file__)


try:
    from DHParser import dsl
    import DHParser.log
    from DHParser import testing
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


def recompile_grammar(grammar_src, force):
    with DHParser.log.logging(False):
        # recompiles Grammar only if it has changed
        if not dsl.recompile_grammar(grammar_src, force=force):
            print('\nErrors while recompiling "%s":' % grammar_src +
                  '\n--------------------------------------\n\n')
            with open('XMLSnippet_ebnf_ERRORS.txt') as f:
                print(f.read())
            sys.exit(1)


def run_grammar_tests(glob_pattern):
    with DHParser.log.logging(False):
        error_report = testing.grammar_suite(
            os.path.join(scriptpath, 'grammar_tests'),
            get_grammar, get_transformer,
            fn_patterns=[glob_pattern], report=True, verbose=True)
    return error_report


if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else '*_test_*.ini'
    if arg.endswith('.ebnf'):
        recompile_grammar(arg, force=True)
    else:
        recompile_grammar(os.path.join(scriptpath, 'XMLSnippet.ebnf'),
                          force=False)
        sys.path.append('.')
        from XMLSnippetCompiler import get_grammar, get_transformer
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.\n')
