#!/usr/bin/env python3

"""tst_ArithmeticRightRecursive_grammar.py - runs the unit tests for the ArithmeticRightRecursive-grammar
"""

import os
import sys

LOGGING = 'LOGS'

scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('../../examples', '..'), '.'):
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)


try:
    from DHParser import dsl
    import DHParser.log
    from DHParser import testing, access_presets, finalize_presets, \
        set_preset_value
    from DHParser.testing import create_test_templates
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


def recompile_grammar(grammar_src, force):
    grammar_tests_dir = os.path.join(scriptpath, 'test_grammar')
    create_test_templates(grammar_src, grammar_tests_dir)
    # recompiles Grammar only if it has changed
    name = os.path.splitext(os.path.basename(grammar_src))[0]
    if not dsl.recompile_grammar(grammar_src, force=force,
                                 notify=lambda: print('recompiling ' + grammar_src)):
        print('\nErrors while recompiling "{}":'.format(grammar_src) +
              '\n--------------------------------------\n\n')
        with open('{}_ebnf_MESSAGES.txt'.format(name)) as f:
            print(f.read())
        sys.exit(1)


def run_grammar_tests(glob_pattern):
    DHParser.log.start_logging(LOGGING)
    error_report = testing.grammar_suite(
        os.path.join(scriptpath, 'test_grammar'),
        get_grammar, get_transformer,
        fn_patterns=[glob_pattern], report='REPORT', verbose=True)
    return error_report


if __name__ == '__main__':
    access_presets()
    set_preset_value('AST_serialization', "S-expression")
    set_preset_value('test_parallelization', True)
    finalize_presets()

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
        recompile_grammar(os.path.join(scriptpath, 'ArithmeticRightRecursive.ebnf'),
                          force=False)
        sys.path.append('')
        from ArithmeticRightRecursiveParser import get_grammar, get_transformer
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            sys.exit(1)
        print('ready.\n')
