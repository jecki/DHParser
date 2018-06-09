# testing.py - test support for DHParser based grammars and compilers
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""
Module ``testing`` contains support for unit-testing domain specific
languages. Tests for arbitrarily small components of the Grammar can
be written into test files with ini-file syntax in order to test
whether the parser matches or fails as expected. It can also be
tested whether it produces an expected concrete or abstract syntax tree.
Usually, however, unexpected failure to match a certain string is the
main cause of trouble when constructing a context free Grammar.
"""


import collections
# import configparser
import copy
import fnmatch
import inspect
import itertools
import json
import os
import sys

from DHParser.error import is_error, adjust_error_locations
from DHParser.log import is_logging, clear_logs, log_ST, log_parsing_history
from DHParser.parse import UnknownParserError
from DHParser.syntaxtree import Node, RootNode, parse_sxpr, flatten_sxpr, ZOMBIE_PARSER
from DHParser.toolkit import re, typing

from typing import Tuple

__all__ = ('unit_from_configfile',
           'unit_from_json',
           'unit_from_file',
           'get_report',
           'grammar_unit',
           'grammar_suite',
           'reset_unit',
           'runner')

UNIT_STAGES = {'match*', 'match', 'fail', 'ast', 'cst'}
RESULT_STAGES = {'__cst__', '__ast__', '__err__'}

# def unit_from_configfile(config_filename):
#     """
#     Reads a grammar unit test from a config file.
#     """
#     cfg = configparser.ConfigParser(interpolation=None)
#     cfg.read(config_filename, encoding="utf8")
#     OD = collections.OrderedDict
#     unit = OD()
#     for section in cfg.sections():
#         symbol, stage = section.split(':')
#         if stage not in UNIT_STAGES:
#             if symbol in UNIT_STAGES:
#                 symbol, stage = stage, symbol
#             else:
#                 raise ValueError('Test stage %s not in: ' % (stage, str(UNIT_STAGES)))
#         for testkey, testcode in cfg[section].items():
#             if testcode[:3] + testcode[-3:] in {"''''''", '""""""'}:
#                 testcode = testcode[3:-3]
#                 # testcode = testcode.replace('\\#', '#')
#                 testcode = re.sub(r'(?<!\\)\\#', '#', testcode).replace('\\\\', '\\')
#             elif testcode[:1] + testcode[-1:] in {"''", '""'}:
#                 testcode = testcode[1:-1]
#             unit.setdefault(symbol, OD()).setdefault(stage, OD())[testkey] = testcode
#     # print(json.dumps(unit, sort_keys=True, indent=4))
#     return unit

RX_SECTION = re.compile('\s*\[(?P<stage>\w+):(?P<symbol>\w+)\]')
RE_VALUE = '(?:"""((?:.|\n)*?)""")|' + "(?:'''((?:.|\n)*?)''')|" + \
           '(?:"(.*?)")|' + "(?:'(.*?)')|" + '(.*(?:\n(?:\s*\n)*    .*)*)'
# the following does not work with pypy3, because pypy's re-engine does not
# support local flags, e.g. '(?s: )'
# RE_VALUE = '(?:"""((?s:.*?))""")|' + "(?:'''((?s:.*?))''')|" + \
#            '(?:"(.*?)")|' + "(?:'(.*?)')|" + '(.*(?:\n(?:\s*\n)*    .*)*)'
RX_ENTRY = re.compile('\s*(\w+\*?)\s*:\s*(?:{value})\s*'.format(value=RE_VALUE))
RX_COMMENT = re.compile('\s*#.*\n')


def unit_from_configfile(config_filename):
    """ Reads grammar unit tests contained in a file in config file (.ini)
    syntax.

    Args:
        config_filename (str): A config file containing Grammar unit-tests

    Returns:
        A dictionary representing the unit tests.
    """
    # TODO: issue a warning if the same match:xxx or fail:xxx block appears more than once

    def eat_comments(txt, pos):
        m = RX_COMMENT.match(txt, pos)
        while m:
            pos = m.span()[1]
            m = RX_COMMENT.match(txt, pos)
        return pos

    with open(config_filename, 'r', encoding="utf-8") as f:
        cfg = f.read()
        cfg = cfg.replace('\t', '    ')

    OD = collections.OrderedDict
    unit = OD()

    pos = eat_comments(cfg, 0)
    section_match = RX_SECTION.match(cfg, pos)
    while section_match:
        d = section_match.groupdict()
        stage = d['stage']
        if stage not in UNIT_STAGES:
            raise KeyError('Unknown stage ' + stage + " ! must be one of: " + str(UNIT_STAGES))
        symbol = d['symbol']
        pos = eat_comments(cfg, section_match.span()[1])

        entry_match = RX_ENTRY.match(cfg, pos)
        if entry_match is None:
            raise SyntaxError('No entries in section [%s:%s]' % (stage, symbol))
        while entry_match:
            testkey, testcode = [group for group in entry_match.groups() if group is not None]
            lines = testcode.split('\n')
            if len(lines) > 1:
                indent = sys.maxsize
                for line in lines[1:]:
                    indent = min(indent, len(line) - len(line.lstrip()))
                for i in range(1, len(lines)):
                    lines[i] = lines[i][indent:]
                testcode = '\n'.join(lines)
            unit.setdefault(symbol, OD()).setdefault(stage, OD())[testkey] = testcode
            pos = eat_comments(cfg, entry_match.span()[1])
            entry_match = RX_ENTRY.match(cfg, pos)

        section_match = RX_SECTION.match(cfg, pos)

    if pos != len(cfg):
        raise SyntaxError('in file %s in line %i' % (config_filename, cfg[:pos].count('\n') + 1))

    return unit


def unit_from_json(json_filename):
    """
    Reads grammar unit tests from a json file.
    """
    with open(json_filename, 'r', encoding='utf8') as f:
        unit = json.load(f)
    for symbol in unit:
        for stage in unit[symbol]:
            if stage not in UNIT_STAGES:
                raise ValueError('Test stage %s not in: %s' % (stage, str(UNIT_STAGES)))
    return unit

# TODO: add support for yaml, cson, toml


def unit_from_file(filename):
    """
    Reads a grammar unit test from a file. The format of the file is
    determined by the ending of its name.
    """
    if filename.endswith(".json"):
        test_unit = unit_from_json(filename)
    elif filename.endswith(".ini"):
        test_unit = unit_from_configfile(filename)
    else:
        raise ValueError("Unknown unit test file type: " + filename[filename.rfind('.'):])

    # Check for ambiguous Test names
    errors = []
    for parser_name, tests in test_unit.items():
        m_names = set(tests.get('match', dict()).keys())
        f_names = set(tests.get('fail', dict()).keys())
        intersection = list(m_names & f_names)
        intersection.sort()
        if intersection:
            errors.append("Same names %s assigned to match and fail test "
                          "of parser %s." % (str(intersection), parser_name))
    if errors:
        raise EnvironmentError("Error(s) in Testfile %s :\n" % filename
                               + '\n'.join(errors))

    return test_unit


def all_match_tests(tests):
    """Returns all match tests from ``tests``, This includes match tests
    marked with an asterix for CST-output as well as unmarked match-tests.
    """
    return itertools.chain(tests.get('match', dict()).items(),
                           tests.get('match*', dict()).items())


def get_report(test_unit):
    """
    Returns a text-report of the results of a grammar unit test. The report
    lists the source of all tests as well as the error messages, if a test
    failed or the abstract-syntax-tree (AST) in case of success.

    If an asterix has been appended to the test name then the concrete syntax
    tree will also be added to the report in this particular case.

    The purpose of the latter is to help constructing and debugging
    of AST-Transformations. It is better to switch the CST-output on and off
    with the asterix marker when needed than to output the CST for all tests
    which would unnecessarily bloat the test reports.
    """
    def indent(txt):
        lines = txt.split('\n')
        lines[0] = '    ' + lines[0]
        return "\n    ".join(lines)
    report = []
    for parser_name, tests in test_unit.items():
        heading = 'Test of parser: "%s"' % parser_name
        report.append('\n\n%s\n%s\n' % (heading, '=' * len(heading)))
        for test_name, test_code in tests.get('match', dict()).items():
            heading = 'Match-test "%s"' % test_name
            report.append('\n%s\n%s\n' % (heading, '-' * len(heading)))
            report.append('### Test-code:')
            report.append(indent(test_code))
            error = tests.get('__err__', {}).get(test_name, "")
            if error:
                report.append('\n### Error:')
                report.append(error)
            ast = tests.get('__ast__', {}).get(test_name, None)
            cst = tests.get('__cst__', {}).get(test_name, None)
            if cst and (not ast or str(test_name).endswith('*')):
                report.append('\n### CST')
                report.append(indent(cst.as_sxpr()))
            if ast:
                report.append('\n### AST')
                report.append(indent(ast.as_sxpr()))
        for test_name, test_code in tests.get('fail', dict()).items():
            heading = 'Fail-test "%s"' % test_name
            report.append('\n%s\n%s\n' % (heading, '-' * len(heading)))
            report.append('### Test-code:')
            report.append(indent(test_code))
            messages = tests.get('__msg__', {}).get(test_name, "")
            if messages:
                report.append('\n### Messages:')
                report.append(messages)
            error = tests.get('__err__', {}).get(test_name, "")
            if error:
                report.append('\n### Error:')
                report.append(error)
    return '\n'.join(report)


def grammar_unit(test_unit, parser_factory, transformer_factory, report=True, verbose=False):
    """
    Unit tests for a grammar-parser and ast transformations.
    """
    if isinstance(test_unit, str):
        _, unit_name = os.path.split(os.path.splitext(test_unit)[0])
        test_unit = unit_from_file(test_unit)
    else:
        unit_name = 'unit_test_' + str(id(test_unit))
    if verbose:
        print("\nUnit: " + unit_name)
    errata = []
    parser = parser_factory()
    transform = transformer_factory()

    for parser_name, tests in test_unit.items():
        assert parser_name, "Missing parser name in test %s!" % unit_name
        assert not any (test_type in RESULT_STAGES for test_type in tests), \
            ("Test %s in %s already has results. Use reset_unit() before running again!"
             % (parser_name, unit_name))
        assert set(tests.keys()).issubset(UNIT_STAGES), \
            'Unknown test-types: %s ! Must be one of %s' \
            % (set(tests.keys()) - UNIT_STAGES, UNIT_STAGES)
        if verbose:
            print('  Match-Tests for parser "' + parser_name + '"')
        match_tests = set(tests['match'].keys()) if 'match' in tests else set()
        if 'ast' in tests:
            ast_tests = set(tests['ast'].keys())
            if not ast_tests <= match_tests:
                raise AssertionError('AST-Tests %s lack corresponding match-tests!'
                                     % str(ast_tests - match_tests))
        if 'cst' in tests:
            cst_tests = set(tests['cst'].keys())
            if not cst_tests <= match_tests:
                raise AssertionError('CST-Tests %s lack corresponding match-tests!'
                                     % str(cst_tests - match_tests))

        # run match tests

        for test_name, test_code in tests.get('match', dict()).items():
            if verbose:
                infostr = '    match-test "' + test_name + '" ... '
                errflag = len(errata)
            try:
                cst = parser(test_code, parser_name)
            except UnknownParserError as upe:
                cst = cst.new_error(Node(ZOMBIE_PARSER, "").init_pos(0), str(upe))
            clean_test_name = str(test_name).replace('*', '')
            # log_ST(cst, "match_%s_%s.cst" % (parser_name, clean_test_name))
            tests.setdefault('__cst__', {})[test_name] = cst
            if "ast" in tests or report:
                ast = copy.deepcopy(cst)
                transform(ast)
                tests.setdefault('__ast__', {})[test_name] = ast
                # log_ST(ast, "match_%s_%s.ast" % (parser_name, clean_test_name))
            if is_error(cst.error_flag):
                errors = adjust_error_locations(cst.collect_errors(), test_code)
                errata.append('Match test "%s" for parser "%s" failed:\n\tExpr.:  %s\n\n\t%s\n\n' %
                              (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                               '\n\t'.join(str(m).replace('\n', '\n\t\t') for m in errors)))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
                # write parsing-history log only in case of failure!
                if is_logging():
                    log_parsing_history(parser, "match_%s_%s.log" % (parser_name, clean_test_name))
            elif "cst" in tests and parse_sxpr(tests["cst"][test_name]) != cst:
                errata.append('Concrete syntax tree test "%s" for parser "%s" failed:\n%s' %
                              (test_name, parser_name, cst.as_sxpr()))
            elif "ast" in tests:
                try:
                    compare = parse_sxpr(tests["ast"][test_name])
                except KeyError:
                    pass
                if compare != ast:
                    errata.append('Abstract syntax tree test "%s" for parser "%s" failed:'
                                  '\n\tExpr.:     %s\n\tExpected:  %s\n\tReceived:  %s'
                                  % (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                                     flatten_sxpr(compare.as_sxpr()),
                                     flatten_sxpr(ast.as_sxpr())))
                    tests.setdefault('__err__', {})[test_name] = errata[-1]
            if verbose:
                print(infostr + ("OK" if len(errata) == errflag else "FAIL"))

        if verbose and 'fail' in tests:
            print('  Fail-Tests for parser "' + parser_name + '"')

        # run fail tests

        for test_name, test_code in tests.get('fail', dict()).items():
            if verbose:
                infostr = '    fail-test  "' + test_name + '" ... '
                errflag = len(errata)
            # cst = parser(test_code, parser_name)
            try:
                cst = parser(test_code, parser_name)
            except UnknownParserError as upe:
                node = Node(ZOMBIE_PARSER, "").init_pos(0)
                cst = RootNode(node).new_error(node, str(upe))
            if not is_error(cst.error_flag):
                errata.append('Fail test "%s" for parser "%s" yields match instead of '
                              'expected failure!' % (test_name, parser_name))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
                # write parsing-history log only in case of test-failure
                if is_logging():
                    log_parsing_history(parser, "fail_%s_%s.log" % (parser_name, test_name))
            if cst.error_flag:
                tests.setdefault('__msg__', {})[test_name] = \
                    "\n".join(str(e) for e in cst.collect_errors())
            if verbose:
                print(infostr + ("OK" if len(errata) == errflag else "FAIL"))

    # write test-report
    if report:
        report_dir = "REPORT"
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        with open(os.path.join(report_dir, unit_name + '.md'), 'w', encoding='utf8') as f:
            f.write(get_report(test_unit))

    return errata


def reset_unit(test_unit):
    """
    Resets the tests in ``test_unit`` by removing all results and error
    messages.
    """
    for parser, tests in test_unit.items():
        for key in list(tests.keys()):
            if key not in UNIT_STAGES:
                if key not in RESULT_STAGES:
                    print('Removing unknown component %s from test %s' % (key, parser))
                del tests[key]



def grammar_suite(directory, parser_factory, transformer_factory,
                  fn_patterns=['*test*'],
                  ignore_unknown_filetypes=False,
                  report=True, verbose=True):
    """
    Runs all grammar unit tests in a directory. A file is considered a test
    unit, if it has the word "test" in its name.
    """
    if not isinstance(fn_patterns, collections.abc.Iterable):
        fn_patterns = [fn_patterns]
    all_errors = collections.OrderedDict()
    if verbose:
        print("\nScanning test-directory: " + directory)
    save_cwd = os.getcwd()
    os.chdir(directory)
    if is_logging():
        clear_logs()
    for filename in sorted(os.listdir()):
        if any(fnmatch.fnmatch(filename, pattern) for pattern in fn_patterns):
            try:
                if verbose:
                    print("\nRunning grammar tests from: " + filename)
                errata = grammar_unit(filename, parser_factory,
                                      transformer_factory, report, verbose)
                if errata:
                    all_errors[filename] = errata
            except ValueError as e:
                if not ignore_unknown_filetypes or str(e).find("Unknown") < 0:
                    raise e
    os.chdir(save_cwd)
    error_report = []
    err_N = 0
    if all_errors:
        for filename in all_errors:
            error_report.append('Errors found by unit test "%s":\n' % filename)
            err_N += len(all_errors[filename])
            for error in all_errors[filename]:
                error_report.append('\t' + '\n\t'.join(error.split('\n')))
    if error_report:
        # if verbose:
        #     print("\nFAILURE! %i error%s found!\n" % (err_N, 's' if err_N > 1 else ''))
        return ('Test suite "%s" revealed %s error%s:\n\n'
                % (directory, err_N, 's' if err_N > 1 else '') + '\n'.join(error_report))
    if verbose:
        print("\nSUCCESS! All tests passed :-)\n")
    return ''


def runner(test_classes, namespace):
    """
    Runs all or some selected Python unit tests found in the
    namespace. To run all tests in a module, call
    ``runner("", globals())`` from within that module.

    Unit-Tests are either classes, the name of which starts with
    "Test" and methods, the name of which starts with "test" contained
    in such classes or functions, the name of which starts with "test".

    Args:
        tests: Either a string or a list of strings that contains the
            names of test or test classes. Each test and, in the case
            of a test class, all tests within the test class will be
            run.
        namespace: The namespace for running the test, usually
            ``globals()`` should be used.

    Example:
        class TestSomething()
            def setup(self):
                pass
            def teardown(self):
                pass
            def test_something(self):
                pass

        if __name__ == "__main__":
            from DHParser.testing import runner
            runner("", globals())
    """
    def instantiate(cls_name):
        exec("obj = " + cls_name + "()", namespace)
        obj = namespace["obj"]
        if "setup" in dir(obj):
            obj.setup()
        return obj

    if test_classes:
        if isinstance(test_classes, str):
            test_classes = test_classes.split(" ")
    else:
        # collect all test classes, in case no methods or classes have been passed explicitly
        test_classes = []
        test_functions = []
        for name in namespace.keys():
            if name.lower().startswith('test'):
                if inspect.isclass(namespace[name]):
                    test_classes.append(name)
                elif inspect.isfunction(namespace[name]):
                    test_functions.append(name)


    obj = None
    for test in test_classes:
        try:
            if test.find('.') >= 0:
                cls_name, method_name = test.split('.')
                obj = instantiate(cls_name)
                print("Running " + cls_name + "." + method_name)
                exec('obj.' + method_name + '()')
            else:
                obj = instantiate(test)
                for name in dir(obj):
                    if name.lower().startswith("test"):
                        print("Running " + test + "." + name)
                        exec('obj.' + name + '()')
        finally:
            if "teardown" in dir(obj):
                obj.teardown()

    for test in test_functions:
        exec(test + '()', namespace)

