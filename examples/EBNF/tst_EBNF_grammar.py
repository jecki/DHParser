#!/usr/bin/env python3

"""tst_EBNF_grammar.py - runs the unit tests for the EBNF-grammar
"""

import os
import sys

LOGGING = ''

scriptpath = os.path.dirname(__file__)
dhparserdir = os.path.abspath(os.path.join(scriptpath, '../..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparserdir not in sys.path:
    sys.path.append(dhparserdir)

try:
    from DHParser.configuration import get_config_value, set_config_value, \
        EBNF_ANY_SYNTAX_HEURISTICAL, EBNF_ANY_SYNTAX_STRICT
    from DHParser import dsl
    import DHParser.log
    from DHParser import testing
    from DHParser.toolkit import is_filename
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


def recompile_grammar(grammar_src, force):
    grammar_tests_dir = os.path.join(scriptpath, 'test_grammar')
    testing.create_test_templates(grammar_src, grammar_tests_dir)
    DHParser.log.start_logging('LOGS')
    # recompiles Grammar only if it has changed
    saved_syntax_variant = get_config_value('syntax_variant')
    set_config_value('syntax_variant', EBNF_ANY_SYNTAX_HEURISTICAL)
    if not dsl.recompile_grammar(grammar_src, force=force,
            notify=lambda: print('recompiling ' + grammar_src)):
        print('\nErrors while recompiling "%s":' % grammar_src +
              '\n--------------------------------------\n\n')
        if is_filename(grammar_src):
            err_name = grammar_src.replace('.', '_') + '_ERRORS.txt'
        else:
            err_name = 'EBNF_ebnf_ERRORS.txt'
        with open(err_name, encoding='utf-8') as f:
            print(f.read())
        sys.exit(1)
    set_config_value('syntax_variant', saved_syntax_variant)


def run_grammar_tests(glob_pattern, get_grammar, get_transformer):
    DHParser.log.start_logging(LOGGING)
    error_report = testing.grammar_suite(
        os.path.join(scriptpath, 'test_grammar'),
        get_grammar, get_transformer,
        fn_patterns=[glob_pattern], report='REPORT', verbose=True)
    return error_report


if __name__ == '__main__':
    # from DHParser.configuration import access_presets, finalize_presets
    # CONFIG_PRESETS = access_presets()
    # CONFIG_PRESET['test_parallelization'] = True
    # finalize_presets()

    argv = sys.argv[:]
    if len(argv) > 1 and sys.argv[1] == "--debug":
        LOGGING = True
        del argv[1]
    if (len(argv) >= 2 and (argv[1].endswith('.ebnf') or
        os.path.splitext(argv[1])[1].lower() in testing.TEST_READERS.keys())):
        # if called with a single filename that is either an EBNF file or a known
        # test file type then use the given argument
        arg = argv[1]
    else:
        # otherwise run all tests in the test directory
        arg = '*_test_*.ini'
    if arg.endswith('.ebnf'):
        recompile_grammar(arg, force=True)
    else:
        recompile_grammar(os.path.join(scriptpath, 'EBNF.ebnf'),
                          force=False)
        sys.path.append('.')
        from EBNFParser import get_grammar, get_transformer
        error_report = run_grammar_tests(arg, get_grammar, get_transformer)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.\n')
