#!/usr/bin/python3

"""tst_ArithmeticSimple_grammar.py - runs the unit tests for the ArithmeticSimple-grammar
"""

import os
import sys

LOGGING = ''

scriptpath = os.path.dirname(__file__) or '.'
for path in (os.path.join('..', '..'), '.'):
    fullpath = os.path.abspath(os.path.join(scriptpath, path))
    if fullpath not in sys.path:
        sys.path.append(fullpath)

try:
    from DHParser import dsl
    import DHParser.log
    from DHParser import testing, create_test_templates, access_presets, finalize_presets
except ModuleNotFoundError:
    print('Could not import DHParser. Please adjust sys.path in file '
          '"%s" manually' % __file__)
    sys.exit(1)


def recompile_grammar(grammar_src, force):
    grammar_tests_dir = os.path.join(scriptpath, 'grammar_tests')
    if not os.path.exists(grammar_tests_dir) \
            or not any(os.path.isfile(os.path.join(grammar_tests_dir, entry))
                       for entry in os.listdir(grammar_tests_dir)):
        print('No grammar-tests found, generating test templates.')
        create_test_templates(grammar_src, grammar_tests_dir)
    DHParser.log.start_logging(LOGGING)
    # recompiles Grammar only if it has changed
    name = os.path.splitext(os.path.basename(grammar_src))[0]
    if not dsl.recompile_grammar(grammar_src, force=force):
        print('\nErrors while recompiling "{}":'.format(grammar_src) +
              '\n--------------------------------------\n\n')
        with open('{}_ebnf_ERRORS.txt'.format(name)) as f:
            print(f.read())
        sys.exit(1)


def run_grammar_tests(glob_pattern):
    DHParser.log.start_logging(LOGGING)
    error_report = testing.grammar_suite(
        os.path.join(scriptpath, 'grammar_tests'),
        get_grammar, get_transformer,
        fn_patterns=[glob_pattern], report='REPORT', verbose=True)
    return error_report


if __name__ == '__main__':
    CONFIG_PRESET = access_presets()
    CONFIG_PRESET['ast_serialization'] = "S-expression"
    CONFIG_PRESET['test_parallelization'] = True
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
        recompile_grammar(os.path.join(scriptpath, 'ArithmeticSimple.ebnf'),
                          force=False)
        recompile_grammar(os.path.join(scriptpath, 'ArithmeticRightRecursive.ebnf'),
                          force=False)
        sys.path.append('.')

        failure = False
        from ArithmeticSimpleCompiler import get_grammar, get_transformer
        print('Testing "ArithmeticSimple"')
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            failure = True

        from ArithmeticRightRecursiveCompiler import get_grammar, get_transformer
        print('Testing "ArithmeticRightRecursive"')
        error_report = run_grammar_tests(glob_pattern=arg)
        if error_report:
            print('\n')
            print(error_report)
            failure = True

        if failure:
            sys.exit(1)
        print('ready.\n')
