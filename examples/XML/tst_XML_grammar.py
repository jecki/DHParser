#!/usr/bin/env python3

"""tst_XML_grammar.py - runs the unit tests for the XML-grammar
"""

import os
import sys

LOGGING = 'LOGS'
DEBUG = True
TEST_DIRNAME = 'tests_grammar'

scriptpath = os.path.dirname(__file__)
if scriptpath not in sys.path:
    sys.path.append(scriptpath)

try:
    from DHParser.configuration import access_presets, set_preset_value, \
        finalize_presets, read_local_config
    from DHParser import dsl
    import DHParser.log
    from DHParser import testing
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


def recompile_grammar(grammar_src, force):
    grammar_tests_dir = os.path.join(scriptpath, TEST_DIRNAME)
    testing.create_test_templates(grammar_src, grammar_tests_dir)
    # recompiles Grammar only if it has changed
    if not dsl.recompile_grammar(grammar_src, force=force,
            notify=lambda: print('recompiling ' + grammar_src)):
        print('\nErrors while recompiling "%s":' % grammar_src +
              '\n--------------------------------------\n\n')
        error_path = os.path.join(grammar_src[:-5] + '_ebnf_MESSAGES.txt')
        with open(error_path, 'r', encoding='utf-8') as f:
            print(f.read())
        sys.exit(1)
    dsl.create_scripts(grammar_src)


def run_grammar_tests(fn_pattern, get_grammar, get_transformer):
    testdir = os.path.join(scriptpath, TEST_DIRNAME)
    DHParser.log.start_logging(os.path.join(testdir, LOGGING))
    error_report = testing.grammar_suite(
        testdir, get_grammar, get_transformer,
        fn_patterns=[fn_pattern], report='REPORT', verbose=True,
        junctions=set(), show=set())
    return error_report


if __name__ == '__main__':
    argv = sys.argv[:]

    access_presets()
    set_preset_value('test_parallelization', True)
    # set_preset_value('history_tracking', True)
    finalize_presets()

    if (len(argv) >= 2 and (argv[1].endswith('.ebnf') or
        os.path.splitext(argv[1])[1].lower() in testing.TEST_READERS.keys())):
        # if called with a single filename that is either an EBNF file or a known
        # test file type then use the given argument
        if argv[1].endswith('.ebnf'):
            cfg_name = argv[1][:-5] + '.ini'
            if os.path.exists(cfg_name):
                read_local_config(cfg_name)
        arg = argv[1]
    else:
        # otherwise run all tests in the test directory
        arg = '*_test_*.ini'
    if arg.endswith('.ebnf'):
        recompile_grammar(arg, force=True)
    else:
        recompile_grammar(os.path.join(scriptpath, 'XML.ebnf'),
                          force=False)
        sys.path.append('.')
        from XMLParser import get_grammar, get_transformer
        error_report = run_grammar_tests(arg, get_grammar, get_transformer)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.\n')
