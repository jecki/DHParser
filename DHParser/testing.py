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
import concurrent.futures
import copy
import fnmatch
import inspect
import json
import multiprocessing
import os
import sys
from typing import Dict, List, Union, cast

from DHParser.configuration import get_config_value
from DHParser.error import Error, is_error, adjust_error_locations, PARSER_LOOKAHEAD_MATCH_ONLY, \
    PARSER_LOOKAHEAD_FAILURE_ONLY, MANDATORY_CONTINUATION_AT_EOF, AUTORETRIEVED_SYMBOL_NOT_CLEARED
from DHParser.log import is_logging, clear_logs, local_log_dir, log_parsing_history
from DHParser.parse import UnknownParserError, Parser, Lookahead
from DHParser.syntaxtree import Node, RootNode, parse_tree, flatten_sxpr, ZOMBIE_TAG
from DHParser.trace import set_tracer, all_descendants, trace_history
from DHParser.transform import traverse, remove_children
from DHParser.toolkit import load_if_file, re

__all__ = ('unit_from_config',
           'unit_from_json',
           'TEST_READERS',
           'unit_from_file',
           'get_report',
           'grammar_unit',
           'grammar_suite',
           'SymbolsDictType',
           'extract_symbols',
           'create_test_templates',
           'reset_unit',
           'runner',
           'clean_report')


UNIT_STAGES = {'match*', 'match', 'fail', 'ast', 'cst'}
RESULT_STAGES = {'__cst__', '__ast__', '__err__'}

RX_SECTION = re.compile(r'\s*\[(?P<stage>\w+):(?P<symbol>\w+)\]')
RE_VALUE = '(?:"""((?:.|\n)*?)""")|' + "(?:'''((?:.|\n)*?)''')|" + \
           r'(?:"(.*?)")|' + "(?:'(.*?)')|" + r'(.*(?:\n(?:\s*\n)*    .*)*)'
# the following does not work with pypy3, because pypy's re-engine does not
# support local flags, e.g. '(?s: )'
# RE_VALUE = r'(?:"""((?s:.*?))""")|' + "(?:'''((?s:.*?))''')|" + \
#            r'(?:"(.*?)")|' + "(?:'(.*?)')|" + '(.*(?:\n(?:\s*\n)*    .*)*)'
RX_ENTRY = re.compile(r'\s*(\w+\*?)\s*:\s*(?:{value})\s*'.format(value=RE_VALUE))
RX_COMMENT = re.compile(r'\s*[#;].*\n')


def unit_from_config(config_str, filename):
    """ Reads grammar unit tests contained in a file in config file (.ini)
    syntax.

    Args:
        config_str (str): A string containing a config-file with Grammar unit-tests

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

    cfg = config_str.replace('\t', '    ')

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
        # if entry_match is None:
        #     SyntaxError('No entries in section [%s:%s]' % (stage, symbol))
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
            # unit.setdefault(symbol, OD()).setdefault(stage, OD())[testkey] = testcode
            test = unit.setdefault(symbol, OD()).setdefault(stage, OD())
            assert testkey.strip('*') not in test and (testkey.strip('*') + '*') not in test, \
                '"%s": Key %s already exists in %s:%s !' % (filename, testkey, stage, symbol)
            test[testkey] = testcode
            pos = eat_comments(cfg, entry_match.span()[1])
            entry_match = RX_ENTRY.match(cfg, pos)

        section_match = RX_SECTION.match(cfg, pos)

    if pos != len(cfg) and not re.match(r'\s+$', cfg[pos:]):
        raise SyntaxError('in file "%s" in line %i' % (filename, cfg[:pos].count('\n') + 2))

    return unit


def unit_from_json(json_str, filename):
    """
    Reads grammar unit tests from a json string.
    """
    unit = json.loads(json_str)
    for symbol in unit:
        for stage in unit[symbol]:
            if stage not in UNIT_STAGES:
                raise ValueError('in file "%s". Test stage %s not in: %s'
                                 % (filename, stage, str(UNIT_STAGES)))
    return unit


# TODO: add support for yaml, cson, toml


# A dictionary associating file endings with reader functions that
# transfrom strings containing the file's content to a nested dictionary
# structure of test cases.
TEST_READERS = {
    '.ini': unit_from_config,
    '.json': unit_from_json
}


def unit_from_file(filename):
    """
    Reads a grammar unit test from a file. The format of the file is
    determined by the ending of its name.
    """
    try:
        reader = TEST_READERS[os.path.splitext(filename)[1].lower()]
        with open(filename, 'r', encoding='utf8') as f:
            data = f.read()
        test_unit = reader(data, filename)
    except KeyError:
        raise ValueError("Unknown unit test file type: " + filename[filename.rfind('.'):])

    # Check for ambiguous Test names
    errors = []
    for parser_name, tests in test_unit.items():
        # normalize case for test category names
        keys = list(tests.keys())
        for key in keys:
            new_key = key.lower()
            if new_key != key:
                tests[new_key] = tests[keys]
                del tests[keys]

        m_names = set(tests.get('match', dict()).keys())
        f_names = set(tests.get('fail', dict()).keys())
        intersection = list(m_names & f_names)
        intersection.sort()
        if intersection:
            errors.append("Same names %s assigned to match and fail test "
                          "of parser %s." % (str(intersection), parser_name)
                          + " Please, use different names!")
    if errors:
        raise EnvironmentError("Error(s) in Testfile %s :\n" % filename
                               + '\n'.join(errors))

    return test_unit


# def all_match_tests(tests):
#     """Returns all match tests from ``tests``, This includes match tests
#     marked with an asterix for CST-output as well as unmarked match-tests.
#     """
#     return itertools.chain(tests.get('match', dict()).items(),
#                            tests.get('match*', dict()).items())


def get_report(test_unit) -> str:
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
            report.append('### Test-code:\n')
            report.append(indent(test_code))
            error = tests.get('__err__', {}).get(test_name, "")
            if error:
                report.append('\n### Error:\n')
                report.append(error)
            ast = tests.get('__ast__', {}).get(test_name, None)
            cst = tests.get('__cst__', {}).get(test_name, None)
            if cst and (not ast or str(test_name).endswith('*')):
                report.append('\n### CST\n')
                report.append(indent(cst.serialize('cst')))
            if ast:
                report.append('\n### AST\n')
                report.append(indent(ast.serialize('ast')))
        for test_name, test_code in tests.get('fail', dict()).items():
            heading = 'Fail-test "%s"' % test_name
            report.append('\n%s\n%s\n' % (heading, '-' * len(heading)))
            report.append('### Test-code:')
            report.append(indent(test_code))
            messages = tests.get('__msg__', {}).get(test_name, "")
            if messages:
                report.append('\n### Messages:\n')
                report.append(messages)
            error = tests.get('__err__', {}).get(test_name, "")
            if error:
                report.append('\n### Error:\n')
                report.append(error)
    return '\n'.join(report)


POSSIBLE_ARTIFACTS = frozenset((
    PARSER_LOOKAHEAD_MATCH_ONLY,
    PARSER_LOOKAHEAD_FAILURE_ONLY,
    MANDATORY_CONTINUATION_AT_EOF,
    AUTORETRIEVED_SYMBOL_NOT_CLEARED
))


def md_codeblock(code: str) -> str:
    """Formats a piece of code as Markdown inline-code or code-block,
    depending on whether it stretches over several lines or not."""
    if '\n' not in code:
        return '`' + code + '`'
    else:
        # linefeeds = re.match('\s*', code).group(0).count('\n')
        lines = code.strip().split('\n')
        return '\n\n\t' + '\n\t'.join(lines)


def grammar_unit(test_unit, parser_factory, transformer_factory, report='REPORT', verbose=False):
    """
    Unit tests for a grammar-parser and ast transformations.
    """
    output = []

    def write(s):
        nonlocal output
        """Append string `s` to output. The purpose is to defer printing to
        stdout in order to avoid muddled output when several unit tests run
        at the same time."""
        output.append(s)

    def clean_key(k):
        try:
            return k.replace('*', '')
        except AttributeError:
            return k

    def get(tests, category, key) -> str:
        try:
            value = tests[category][key] if key in tests[category] \
                else tests[category][clean_key(key)]
        except KeyError:
            return ''
            # raise AssertionError('%s-test %s for parser %s missing !?'
            #                      % (category, test_name, parser_name))
        return value

    if isinstance(test_unit, str):
        _, unit_name = os.path.split(os.path.splitext(test_unit)[0])
        test_unit = unit_from_file(test_unit)
    else:
        unit_name = 'unit_test_' + str(id(test_unit))
    if verbose:
        write("\nGRAMMAR TEST UNIT: " + unit_name)
    errata = []
    parser = parser_factory()
    transform = transformer_factory()

    def has_lookahead(parser_name: str) -> bool:
        """Returns True if the parser or any of its descendant parsers is a
        Lookahead parser."""
        return parser[parser_name].apply(lambda ctx: isinstance(ctx[-1], Lookahead))
        # lookahead_found = False
        #
        # def find_lookahead(p: Parser):
        #     nonlocal lookahead_found
        #     if not lookahead_found:
        #         lookahead_found = isinstance(p, Lookahead)
        #
        # parser[parser_name].apply(find_lookahead)
        # return lookahead_found

    def lookahead_artifact(syntax_tree: Node):
        """
        Returns True, if the error merely occurred, because the parser
        stopped in front of a sequence that was captured by a lookahead
        operator or if a mandatory lookahead failed at the end of data.
        This is required for testing of parsers that put a lookahead
        operator at the end. See test_testing.TestLookahead.
        """
        if not get_config_value('test_supress_lookahead_failures'):
            return False
        raw_errors = cast(RootNode, syntax_tree).errors_sorted
        is_artifact = ({e.code for e in raw_errors}
                       <= {PARSER_LOOKAHEAD_FAILURE_ONLY,
                           AUTORETRIEVED_SYMBOL_NOT_CLEARED,
                           PARSER_LOOKAHEAD_MATCH_ONLY}
                       or (len(raw_errors) == 1
                           and (raw_errors[-1].code == PARSER_LOOKAHEAD_MATCH_ONLY
                                #  case 2:  mandatory lookahead failure at end of text
                                or raw_errors[-1].code == MANDATORY_CONTINUATION_AT_EOF)))
        if is_artifact:
            # don't remove zombie node with error message at the end
            # but change it's tag_name to indicate that it is an artifact!
            for parent in syntax_tree.select_if(lambda node: any(child.tag_name == ZOMBIE_TAG
                                                                 for child in node.children),
                                                include_root=True, reverse=True):
                zombie = parent.pick_child(ZOMBIE_TAG)
                zombie.tag_name = '__TESTING_ARTIFACT__'
                zombie.result = 'Artifact can be ignored. Be aware, though, that also the ' \
                                'tree structure may not be the same as in a non-testing ' \
                                'environment, when a testing artifact has occurred!'
                # parent.result = tuple(c for c in parent.children if c.tag_name != ZOMBIE_TAG)
                break
        return is_artifact

    for parser_name, tests in test_unit.items():
        if not get_config_value('test_parallelization'):
            print('  Testing parser: ' + parser_name)

        track_history = False
        try:
            if has_lookahead(parser_name):
                set_tracer(all_descendants(parser[parser_name]), trace_history)
                track_history = True
        except UnknownParserError:
            pass

        assert parser_name, "Missing parser name in test %s!" % unit_name
        assert not any(test_type in RESULT_STAGES for test_type in tests), \
            ("Test %s in %s already has results. Use reset_unit() before running again!"
             % (parser_name, unit_name))
        assert set(tests.keys()).issubset(UNIT_STAGES), \
            'Unknown test-types: %s ! Must be one of %s' \
            % (set(tests.keys()) - UNIT_STAGES, UNIT_STAGES)
        if verbose:
            write('  Match-Tests for parser "' + parser_name + '"')
        match_tests = set(tests['match'].keys()) if 'match' in tests else set()
        if 'ast' in tests:
            ast_tests = set(tests['ast'].keys())
            if not {clean_key(k) for k in ast_tests} <= {clean_key(k) for k in match_tests}:
                raise AssertionError('AST-Tests %s for parser %s lack corresponding match-tests!'
                                     % (str(ast_tests - match_tests), parser_name))
        if 'cst' in tests:
            cst_tests = set(tests['cst'].keys())
            if not {clean_key(k) for k in cst_tests} <= {clean_key(k) for k in match_tests}:
                raise AssertionError('CST-Tests %s lack corresponding match-tests!'
                                     % str(cst_tests - match_tests))

        # run match tests

        for test_name, test_code in tests.get('match', dict()).items():
            if not get_config_value('test_parallelization'):
                print('    Test: ' + str(test_name))

            errflag = len(errata)
            try:
                cst = parser(test_code, parser_name)
            except UnknownParserError as upe:
                cst = RootNode()
                cst = cst.new_error(Node(ZOMBIE_TAG, "").with_pos(0), str(upe))
            clean_test_name = str(test_name).replace('*', '')
            # with local_log_dir('./LOGS'):
            #     log_ST(cst, "match_%s_%s.cst" % (parser_name, clean_test_name))
            tests.setdefault('__cst__', {})[test_name] = cst
            errors = []  # type: List[Error]
            if is_error(cst.error_flag) and not lookahead_artifact(cst):
                errors = [e for e in cst.errors_sorted if e.code not in POSSIBLE_ARTIFACTS]
                adjust_error_locations(errors, test_code)
                errata.append('Match test "%s" for parser "%s" failed:'
                              '\nExpr.:  %s\n\n%s\n\n' %
                              (test_name, parser_name, md_codeblock(test_code),
                               '\n'.join(str(m).replace('\n', '\n') for m in errors)))
            if "ast" in tests or report:
                ast = copy.deepcopy(cst)
                old_errors = set(ast.errors)
                traverse(ast, {'*': remove_children({'__TESTING_ARTIFACT__'})})
                transform(ast)
                tests.setdefault('__ast__', {})[test_name] = ast
                ast_errors = [e for e in ast.errors if e not in old_errors]
                ast_errors.sort(key=lambda e: e.pos)
                if is_error(max(e.code for e in ast_errors) if ast_errors else 0):
                    adjust_error_locations(ast_errors, test_code)
                    if errors:
                        if errata:  errata[-1] = errata[-1].rstrip('\n')
                        ast_errors.append('\n')
                        errata.append('\t' + '\n\t'.join(
                            str(msg).replace('\n', '\n\t\t') for msg in ast_errors))
                    # else:  # should not be reported, because AST can be tested independently!!!
                    #     errata.append('Match test "%s" for parser "%s" failed on AST:'
                    #                   '\n\tExpr.:  %s\n\n\t%s\n\n' %
                    #                   (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                    #                    '\n\t'.join(
                    #                        str(m).replace('\n', '\n\t\t') for m in ast_errors)))
            if verbose:
                infostr = '    match-test "' + test_name + '" ... '
                write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if "cst" in tests and len(errata) == errflag:
                compare = parse_tree(get(tests, "cst", test_name))
                if compare:
                    if not compare.equals(cst):
                        errata.append('Concrete syntax tree test "%s" for parser "%s" failed:\n%s' %
                                      (test_name, parser_name, cst.serialize('cst')))
                    if verbose:
                        infostr = '      cst-test "' + test_name + '" ... '
                        write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if "ast" in tests and len(errata) == errflag:
                compare = parse_tree(get(tests, "ast", test_name))
                if compare:
                    traverse(compare, {'*': remove_children({'__TESTING_ARTIFACT__'})})
                    if not compare.equals(ast):
                        errata.append('Abstract syntax tree test "%s" for parser "%s" failed:'
                                      '\n\tExpr.:     %s\n\tExpected:  %s\n\tReceived:  %s'
                                      % (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                                         flatten_sxpr(compare.as_sxpr()),
                                         flatten_sxpr(ast.as_sxpr())))
                    if verbose:
                        infostr = '      ast-test "' + test_name + '" ... '
                        write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if len(errata) > errflag:
                tests.setdefault('__err__', {})[test_name] = errata[-1]
                # write parsing-history log only in case of failure!
                if is_logging() and track_history:
                    with local_log_dir('./LOGS'):
                        log_parsing_history(parser, "match_%s_%s.log" %
                                            (parser_name, clean_test_name))

        if verbose and 'fail' in tests:
            write('  Fail-Tests for parser "' + parser_name + '"')

        # run fail tests

        for test_name, test_code in tests.get('fail', dict()).items():
            errflag = len(errata)
            try:
                cst = parser(test_code, parser_name)
            except UnknownParserError as upe:
                node = Node(ZOMBIE_TAG, "").with_pos(0)
                cst = RootNode(node).new_error(node, str(upe))
                errata.append('Unknown parser "{}" in fail test "{}"!'.format(
                    parser_name, test_name))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
            if not (is_error(cst.error_flag) and not lookahead_artifact(cst)):
                errata.append('Fail test "%s" for parser "%s" yields match instead of '
                              'expected failure!\n%s' % (test_name, parser_name, cst.serialize()))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
                # write parsing-history log only in case of test-failure
                if is_logging() and track_history:
                    with local_log_dir('./LOGS'):
                        log_parsing_history(parser, "fail_%s_%s.log" % (parser_name, test_name))
            if cst.error_flag:
                adjust_error_locations(cst.errors, test_code)
                tests.setdefault('__msg__', {})[test_name] = \
                    "\n".join(str(e) for e in cst.errors_sorted)
            if verbose:
                infostr = '    fail-test  "' + test_name + '" ... '
                write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

    # remove tracers, in case there are any:
    set_tracer(all_descendants(parser.root_parser__), None)

    # write test-report
    if report:
        test_report = get_report(test_unit)
        if test_report:
            try:
                os.mkdir(report)   # is a process-Lock needed, here?
            except FileExistsError:
                pass
            with open(os.path.join(report, unit_name + '.md'), 'w', encoding='utf8') as f:
                f.write(test_report)

    print('\n'.join(output))
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


# def debug_unit(*parameters):
#     """debug unit test in multiprocessing environment."""
#     print("DEBUG_UNIT")
#     try:
#         grammar_unit(*parameters)
#     except Exception as e:
#         print(e)


def grammar_suite(directory, parser_factory, transformer_factory,
                  fn_patterns=('*test*',),
                  ignore_unknown_filetypes=False,
                  report='REPORT', verbose=True):
    """
    Runs all grammar unit tests in a directory. A file is considered a test
    unit, if it has the word "test" in its name.
    """
    assert isinstance(report, str)

    if not isinstance(fn_patterns, collections.abc.Iterable):
        fn_patterns = [fn_patterns]
    all_errors = collections.OrderedDict()
    if verbose:
        print("\nScanning test-directory: " + directory)
    save_cwd = os.getcwd()
    os.chdir(directory)
    if is_logging():
        clear_logs()

    if get_config_value('test_parallelization'):
        with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
            results = []
            for filename in sorted(os.listdir('.')):
                print(filename)
                if any(fnmatch.fnmatch(filename, pattern) for pattern in fn_patterns):
                    parameters = filename, parser_factory, transformer_factory, report, verbose
                    results.append((filename, pool.submit(grammar_unit, *parameters)))
            for filename, err_future in results:
                try:
                    errata = err_future.result()
                    if errata:
                        all_errors[filename] = errata
                except ValueError as e:
                    if not ignore_unknown_filetypes or str(e).find("Unknown") < 0:
                        raise e
    else:
        results = []
        for filename in sorted(os.listdir('.')):
            if any(fnmatch.fnmatch(filename, pattern) for pattern in fn_patterns):
                parameters = filename, parser_factory, transformer_factory, report, verbose
                # print(filename)
                results.append((filename, grammar_unit(*parameters)))
        for filename, errata in results:
            if errata:
                all_errors[filename] = errata

    os.chdir(save_cwd)
    error_report = []
    err_N = 0
    if all_errors:
        for filename in all_errors:
            error_report.append('\n\nErrors found by unit test "%s":\n' % filename)
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


########################################################################
#
# Support for unit-testing of ebnf-grammars
#
########################################################################


RX_DEFINITION_OR_SECTION = re.compile(r'(?:^|\n)[ \t]*(\w+(?=[ \t]*=)|#:.*(?=\n|$|#))')
SymbolsDictType = Dict[str, List[str]]


def extract_symbols(ebnf_text_or_file: str) -> SymbolsDictType:
    r"""
    Extracts all defined symbols from an EBNF-grammar. This can be used to
    prepare grammar-tests. The symbols will be returned as lists of strings
    which are grouped by the sections to which they belong and returned as
    an ordered dictionary, they keys of which are the section names.
    In order to define a section in the ebnf-source, add a comment-line
    starting with "#:", followed by the section name. It is recommended
    to use valid file names as section names. Example:

        #: components

        expression = term  { EXPR_OP~ term}
        term       = factor  { TERM_OP~ factor}
        factor     = [SIGN] ( NUMBER | VARIABLE | group ) { VARIABLE | group }
        group      = "(" expression ")"


        #: leaf_expressions

        EXPR_OP    = /\+/ | /-/
        TERM_OP    = /\*/ | /\//
        SIGN       = /-/

        NUMBER     = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
        VARIABLE   = /[A-Za-z]/~

    If no sections have been defined in the comments, there will be only
    one group with the empty string as a key.

    :param ebnf_text_or_file: Either an ebnf-grammar or the file-name
            of an ebnf-grammar
    :return: Ordered dictionary mapping the section names of the grammar
            to lists of symbols that appear under that section.
    """
    def trim_section_name(name: str) -> str:
        return re.sub(r'[^\w-]', '_', name.replace('#:', '').strip())

    ebnf = load_if_file(ebnf_text_or_file)
    deflist = RX_DEFINITION_OR_SECTION.findall(ebnf)
    if not deflist:
        if ebnf_text_or_file.find('\n') < 0 and ebnf_text_or_file.endswith('.ebnf'):
            deflist = '#: ' + os.path.splitext(ebnf_text_or_file)[0]
        else:
            deflist = '#: ALL'
    symbols = collections.OrderedDict()  # type: SymbolsDictType
    if deflist[0][:2] != '#:':
        curr_section = ''
        symbols[curr_section] = []
    for df in deflist:
        if df[:2] == '#:':
            curr_section = trim_section_name(df)
            if curr_section in symbols:
                raise AssertionError('Section name must not be repeated: ' + curr_section)
            symbols[curr_section] = []
        else:
            symbols[curr_section].append(df)
    return symbols


def create_test_templates(symbols_or_ebnf: Union[str, SymbolsDictType],
                          path: str,
                          fmt: str = '.ini') -> None:
    """
    Creates template files for grammar unit-tests for the given symbols .

    Args:
        symbols_or_ebnf: Either a dictionary that matches section names to
                the grammar's symbols under that section or an EBNF-grammar
                or file name of an EBNF-grammar from which the symbols shall
                be extracted.
        path: the path to the grammar-test directory (usually 'test_grammar').
                If the last element of the path does not exist, the directory
                will be created.
        fmt: the test-file-format. At the moment only '.ini' is supported
    """
    assert fmt == '.ini'
    if isinstance(symbols_or_ebnf, str):
        symbols = extract_symbols(cast(str, symbols_or_ebnf))  # type: SymbolsDictType
    else:
        symbols = cast(Dict, symbols_or_ebnf)
    if not os.path.exists(path):
        os.mkdir(path)
    if os.path.isdir(path):
        save = os.getcwd()
        os.chdir(path)
        keys = reversed(list(symbols.keys()))
        for i, k in enumerate(keys):
            filename = '{num:0>2}_test_{section}'.format(num=i + 1, section=k) + fmt
            if not os.path.exists(filename):
                print('Creating test file template "{name}".'.format(name=filename))
                with open(filename, 'w', encoding='utf-8') as f:
                    for sym in symbols[k]:
                        f.write('\n[match:{sym}]\n\n'.format(sym=sym))
                        f.write('[ast:{sym}]\n\n'.format(sym=sym))
                        f.write('[fail:{sym}]\n\n'.format(sym=sym))
        os.chdir(save)
    else:
        raise ValueError(path + ' is not a directory!')


#######################################################################
#
#  general unit testing support
#
#######################################################################


def run_tests_in_class(cls_name, namespace, methods=()):
    """
    Runs tests in test-class `test` in the given namespace.

    """
    def instantiate(cls, nspace):
        """Instantiates class name `cls` within name-space `nspace` and
        returns the instance."""
        exec("instance = " + cls + "()", nspace)
        instance = nspace["instance"]
        if "setup" in dir(instance):
            instance.setup()
        return instance

    obj = None
    try:
        if methods:
            obj = instantiate(cls_name, namespace)
            for name in methods:
                func = obj.__getattribute__(name)
                if callable(func):
                    print("Running " + cls_name + "." + name)
                    func()
                    # exec('obj.' + name + '()')
        else:
            obj = instantiate(cls_name, namespace)
            for name in dir(obj):
                if name.lower().startswith("test"):
                    func = obj.__getattribute__(name)
                    if callable(func):
                        print("Running " + cls_name + "." + name)
                        func()
    finally:
        if "teardown" in dir(obj):
            obj.teardown()


def run_test_function(func_name, namespace):
    """
    Run the test-function `test` in the given namespace.
    """
    print("Running test-function: " + func_name)
    exec(func_name + '()', namespace)


def runner(tests, namespace):
    """
    Runs all or some selected Python unit tests found in the
    namespace. To run all tests in a module, call
    ``runner("", globals())`` from within that module.

    Unit-Tests are either classes, the name of which starts with
    "Test" and methods, the name of which starts with "test" contained
    in such classes or functions, the name of which starts with "test".

    if `tests` is either the empty string or an empty sequence, runner
    checks sys.argv for specified tests. In case sys.argv[0] (i.e. the
    script's file name) starts with 'test' any argument in sys.argv[1:]
    (i.e. the rest of the command line) that starts with 'test' or
    'Test' is considered the name of a test function or test method
    (of a test-class) that shall be run. Test-Methods are specified in
    the form: class_name.method.name e.g. "TestServer.test_connection".

    Args:
        tests: String or list of strings with the names of tests to
            run. If empty, runner searches by itself all objects the
            of which starts with 'test' and runs it (if its a function)
            or all of its methods that start with "test" if its a class
            plus the "setup" and "teardown" methods if they exist.

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
    test_classes = collections.OrderedDict()
    test_functions = []

    if tests:
        if isinstance(tests, str):
            tests = tests.split(' ')
        assert all(test.lower().startswith('test') for test in tests)
    else:
        tests = []
        if sys.argv[0].lower().startswith('test'):
            tests = [name for name in sys.argv[1:] if name.lower().startswith('test')]
        if not tests:
            tests = [name for name in namespace.keys() if name.lower().startswith('test')]

    for name in tests:
        func_or_class, method = (name.split('.') + [''])[:2]
        if inspect.isclass(namespace[func_or_class]):
            if func_or_class not in test_classes:
                test_classes[func_or_class] = []
            if method:
                test_classes[func_or_class].append(method)
        elif inspect.isfunction(namespace[name]):
            test_functions.append(name)

    for cls_name, methods in test_classes.items():
        run_tests_in_class(cls_name, namespace, methods)

    for test in test_functions:
        run_test_function(test, namespace)


def run_file(fname):
    if fname.lower().startswith('test_') and fname.endswith('.py'):
        print("RUNNING " + fname)
        # print('\nRUNNING UNIT TESTS IN: ' + fname)
        exec('import ' + fname[:-3])
        runner('', eval(fname[:-3]).__dict__)


def run_path(path):
    """Runs all unit tests in `path`"""
    if os.path.isdir(path):
        sys.path.append(path)
        files = os.listdir(path)
        result_futures = []

        if get_config_value('test_parallelization'):
            with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
                for f in files:
                    result_futures.append(pool.submit(run_file, f))
                    # run_file(f)  # for testing!
                for r in result_futures:
                    try:
                        _ = r.result()
                    except AssertionError as failure:
                        print(failure)
        else:
            for f in files:
                run_file(f)

    else:
        path, fname = os.path.split(path)
        sys.path.append(path)
        run_file(fname)
    sys.path.pop()


def clean_report(report_dir='REPORT'):
    """Deletes any test-report-files in the REPORT sub-directory and removes
    the REPORT sub-directory, if it is empty after deleting the files."""
    # TODO: make this thread safe, if possible!!!!
    if os.path.exists(report_dir):
        files = os.listdir(report_dir)
        flag = False
        for file in files:
            if re.match(r'\w*_test_\d+\.md', file):
                os.remove(os.path.join(report_dir, file))
            else:
                flag = True
        if not flag:
            os.rmdir(report_dir)
