#!/usr/bin/env python3

"""tst_FixedEBNF_grammar.py - runs the unit tests for the FixedEBNF-grammar
"""

import os
import sys

LOGGING = 'LOGS'
DEBUG = True
TEST_DIRNAME = 'tests_grammar'

scriptpath = os.path.dirname(__file__)
dhparserdir = os.path.abspath(os.path.join(scriptpath, '..', '..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparserdir not in sys.path:
    sys.path.append(dhparserdir)

try:
    from DHParser.configuration import access_presets, set_preset_value, \
        finalize_presets
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
        with open('FixedEBNF_ebnf_ERRORS.txt', encoding='utf-8') as f:
            print(f.read())
        sys.exit(1)
    dsl.restore_server_script(grammar_src)


def run_grammar_tests(glob_pattern, get_grammar, get_transformer, get_compiler):
    testdir = os.path.join(scriptpath, TEST_DIRNAME)
    DHParser.log.start_logging(os.path.join(testdir, LOGGING))
    error_report = testing.grammar_suite(
        testdir, get_grammar, get_transformer,
        fn_patterns=[glob_pattern], report='REPORT', verbose=True,
        junctions={('ast', get_compiler, 'py')}, show={'py'})
    return error_report


def cpu_profile(func):
    import cProfile as profile
    import pstats
    pr = profile.Profile()
    pr.enable()
    result = func()
    pr.disable()
    st = pstats.Stats(pr)
    st.strip_dirs()
    st.sort_stats('time').print_stats(40)
    return result


if __name__ == '__main__':
    argv = sys.argv[:]
    try:
        i = argv.index('--profile')
        del argv[i]
        access_presets()
        set_preset_value('test_parallelization', False)
        finalize_presets()
        print("Profiling test run...")
        profile = True
    except ValueError:
        profile = False
    if len(argv) > 1 and sys.argv[1] == "--debug":
        DEBUG = True
        del argv[1]

    access_presets()
    # set_preset_value('test_parallelization', True)
    if DEBUG:  set_preset_value('history_tracking', True)
    finalize_presets()

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
        recompile_grammar(os.path.join(scriptpath, 'FixedEBNF.ebnf'),
                          force=False)
        sys.path.append('.')
        from FixedEBNFParser import get_grammar, get_transformer
        from DHParser.ebnf import get_ebnf_compiler
        if profile:
            error_report = cpu_profile(
                lambda : run_grammar_tests(arg, get_grammar, get_transformer, get_ebnf_compiler))
        else:
            error_report = run_grammar_tests(arg, get_grammar, get_transformer, get_ebnf_compiler)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.\n')
