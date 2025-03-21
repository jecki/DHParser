# testing.py - test support for DHParser based grammars and compilers
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
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

from __future__ import annotations

import asyncio
import collections
from collections.abc import Set
import concurrent.futures
import copy
import fnmatch
import json
import os
import random
import sys
import threading
import time
from typing import Dict, List, Union, Deque, Optional, cast

from DHParser import RESUME_NOTICE

if sys.version_info >= (3, 6, 0):
    OrderedDict = dict
else:
    from collections import OrderedDict

from DHParser.configuration import get_config_value, set_config_value
from DHParser.pipeline import extract_data, run_pipeline
from DHParser.error import Error, is_error, PARSER_LOOKAHEAD_MATCH_ONLY, \
    PARSER_LOOKAHEAD_FAILURE_ONLY, MANDATORY_CONTINUATION_AT_EOF, \
    MANDATORY_CONTINUATION_AT_EOF_NON_ROOT, CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY, \
    AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT, PYTHON_ERROR_IN_TEST
from DHParser.log import is_logging, clear_logs, local_log_dir, log_parsing_history
from DHParser.parse import Lookahead, artifact
from DHParser.server import RX_CONTENT_LENGTH, RE_DATA_START, JSONRPC_HEADER_BYTES
from DHParser.nodetree import Node, RootNode, deserialize, flatten_sxpr, ZOMBIE_TAG
from DHParser.trace import set_tracer, trace_history
from DHParser.transform import traverse, remove_children
from DHParser.toolkit import load_if_file, re, instantiate_executor, TypeAlias


__all__ = ('unit_from_config',
           'unit_from_json',
           'TEST_READERS',
           'unit_from_file',
           'get_report',
           'TEST_ARTIFACT',
           'POSSIBLE_ARTIFACTS',
           'grammar_unit',
           'unique_name',
           'grammar_suite',
           'SymbolsDictType',
           'extract_symbols',
           'create_test_templates',
           'reset_unit',
           'runner',
           'clean_report',
           'read_full_content',
           'add_header',
           'stdio',
           'MockStream')


UNIT_STAGES = frozenset({'match*', 'match', 'fail', 'AST', 'CST'})
STARTING_STAGES = frozenset({'match*', 'match', 'fail'})
RESULT_STAGES = frozenset({'__CST__', '__AST__', '__err__'})

RX_SECTION = re.compile(r'\s*\[(?P<stage>\w+(:?\.\w+)*):(?P<symbol>\w+)\]')
RX_METADATA_SECTION = re.compile(r'\s*\[(?P<metadata>\w+)\]')
RE_MULTILINE_DOUBLE_QUOTE = r'(?:""("(?:.|\n)*?")"")'
RE_MULTILINE_SINGLE_QUOTE = r"(?:''('(?:.|\n)*?')'')"
RE_ONELINE_DOUBLE_QUOTE = r'(".*?")'
RE_ONELINE_SINGLE_QUOTE = r"('.*?')"
# Any data as long as it is indented after the first line.
# In practice, S-expressions, XML and nodetree-JSON will be interpreted
RE_MULTILINE_DATA = r"([^\n]*(?:\n     *[^ ][^\n]*|\s*?(?=\n     *[^ ]))*)"
RE_VALUE = '|'.join([RE_MULTILINE_DOUBLE_QUOTE,
                     RE_MULTILINE_SINGLE_QUOTE,
                     RE_ONELINE_DOUBLE_QUOTE,
                     RE_ONELINE_SINGLE_QUOTE,
                     RE_MULTILINE_DATA])
# RE_VALUE = '(?:"""((?:.|\n)*?)""")|' + "(?:'''((?:.|\n)*?)''')|" + \
#            r'(?:"(.*?)")|' + "(?:'(.*?)')|" + r'(.*(?:\n(?:\s*\n)*    .*)*)'
# the following does not work with pypy3, because pypy's re-engine does not
# support local flags, e.g. '(?s: )'
# RE_VALUE = r'(?:"""((?s:.*?))""")|' + "(?:'''((?s:.*?))''')|" + \
#            r'(?:"(.*?)")|' + "(?:'(.*?)')|" + '(.*(?:\n(?:\s*\n)*    .*)*)'
RX_ENTRY = re.compile(r'\s*([\w.]+\*?)\s*[:=]\s*(?:{value})\s*'.format(value=RE_VALUE))
RX_COMMENT = re.compile(r'\s*[#;].*(?:\n|$)')


def normalize_code(testcode: str,
                   full_normalization: bool=False,
                   never_deserialize: bool=False) \
        -> Union[str, Node]:
    """Removes leading and trailing empty lines (if full_normalization is True)
    and leading indentation (always) from multiline text. Furthermore, removes
    quotation marks from strings.

    In case the test-code was not enclosed in single or double quotation marks,
    normalize_code also attemts to deserialize the content as S-expression or XML
    and returns the resulting node-tree, if successful.

    In all other cases the normalized code is returned as string.

    :param testcode: The test-code
    :param full_normalization:  If True, leading or trailing empty lines will be
        ignored.
    :param never_deserialize:  Never return the test-code as deserialized node-tree.
        Thus, strings containing S-expressions or XML will be returned as such.

    :return: The normalized test-code, which can either be:
        a) a string, if the string passed to parameter ``testcode`` contains quotation
            marks (either '  or ") of the same kind in its first and last character,
            or if the string passed can neither be interpreted as an XML nor as an
            S-expression-tree.
        b) a node-tree, if the string passed to parameter ``testcode`` does not begin
            and end with quotation marks AND if the test-code can be interpreted
            as an S-expression or as XML-code.

    Examples::

        >>> code = '''first line
        ...     indented second line'''
        >>> print(normalize_code(code))
        first line
        indented second line
        >>> normalize_code('(a (b X))')
        Node('a', (Node('b', 'X')))
        >>> normalize_code('"(a (b X))"')
        '(a (b X))'

    """
    lines = testcode.split('\n')
    if len(lines) > 1:
        indent = sys.maxsize
        for i in range(1, len(lines)):
            line = lines[i]
            if full_normalization:
                lines[i] = line.rstrip()
            if line:
                indent = min(indent, len(line) - len(line.lstrip()))
        if indent > 0 and indent != sys.maxsize:
            if lines[0].strip() and lines[0][0:1] not in ('', ' ') and indent > 4:
                indent = min(4, max(indent - 4, 4))
            for i in range(1, len(lines)):
                lines[i] = lines[i][indent:]
        if full_normalization:
            for i in range(len(lines)):
                if lines[i]:  break
            for k in range(len(lines) - 1, -1, -1):
                if lines[k]:  break
            lines = lines[i:k + 1]
    if lines[0][:1] in ('"', "'") and lines[-1][-1:] in ('"', "'"):
        # remove string markers
        lines[0] = lines[0][1:]
        lines[-1] = lines[-1][:-1]
    elif not never_deserialize:
        code = '\n'.join(lines)
        try:
            tree = deserialize(code)
            return tree
        except ValueError:
            return code
    return '\n'.join(lines)


def unit_from_config(config_str: str, filename: str, allowed_stages=UNIT_STAGES):
    """ Reads grammar unit tests contained in a file in config file (.ini)
    syntax.

    :param config_str: A string containing a config-file with Grammar unit-tests
    :param filename: The file-name of the config-file containing ``config_str``.
    :param allows_stages: A set of stage names of stages in the processing pipeline
        for which the test-file may contain tests.

    Returns:
        A JSON-like object(i.e. dictionary) representing the unit tests.
    """
    # TODO: issue a warning if the same match:xxx or fail:xxx block appears more than once

    def eat_comments(txt, pos):
        m = RX_COMMENT.match(txt, pos)
        while m:
            pos = m.span()[1]
            m = RX_COMMENT.match(txt, pos)
        return pos

    cfg = config_str.replace('\t', '    ')

    OD = OrderedDict
    unit = OD()

    # read meta-data
    pos = eat_comments(cfg, 0)
    metadata_match = RX_METADATA_SECTION.match(cfg, pos)
    while metadata_match:
        mdsection = metadata_match.groupdict()['metadata']
        if mdsection[-2:] != '__':
            mdsection += '_' if mdsection[-1:] == '_' else '__'
        unit.setdefault(mdsection, OD())
        pos = eat_comments(cfg, metadata_match.span()[1])
        entry_match = RX_ENTRY.match(cfg, pos)
        while entry_match:
            key, value = [group for group in entry_match.groups() if group is not None]
#            value = normalize_code(value, full_normalization=True)
            unit[mdsection][key] = value
            pos = eat_comments(cfg, entry_match.span()[1])
            entry_match = RX_ENTRY.match(cfg, pos)
        metadata_match = RX_METADATA_SECTION.match(cfg, pos)

    # read test-data
    section_match = RX_SECTION.match(cfg, pos)
    first_section_missing = True
    while section_match:
        first_section_missing = False
        d = section_match.groupdict()
        stage = d['stage']
        if stage.upper() == 'AST':  stage = 'AST'
        if stage.upper() == 'CST':  stage = 'CST'
        if stage not in allowed_stages:
            raise KeyError(f'Unknown stage "{stage}" in file "{filename}"! '
                           f"must be one of: {allowed_stages}")
        symbol = d['symbol']
        unit.setdefault(symbol, OD()).setdefault(stage, OD())  # allow empty tests!
        pos = eat_comments(cfg, section_match.span()[1])

        entry_match = RX_ENTRY.match(cfg, pos)
        # if entry_match is None:
        #     SyntaxError('No entries in section [%s:%s]' % (stage, symbol))
        while entry_match:
            testkey, testcode = [group for group in entry_match.groups() if group is not None]
            testcode = normalize_code(testcode,
                full_normalization=stage not in UNIT_STAGES,
                never_deserialize=stage in STARTING_STAGES)
            # test = unit.setdefault(symbol, OD()).setdefault(stage, OD())
            test = unit[symbol][stage]
            if testkey.strip('*') in test or (testkey.strip('*') + '*') in test:
                raise KeyError('"%s": Key %s already exists in %s:%s !'
                               % (filename, testkey, stage, symbol))
            test[testkey] = testcode
            pos = eat_comments(cfg, entry_match.span()[1])
            entry_match = RX_ENTRY.match(cfg, pos)

        section_match = RX_SECTION.match(cfg, pos)

    if pos != len(cfg) and not re.match(r'\s+$', cfg[pos:]):
        err_head = 'N' if first_section_missing else 'Test NAME:STRING or n'
        err_str = err_head + 'ew section [TEST:PARSER] expected, ' \
                  + 'where TEST is "match", "fail" or "AST"; in file ' \
                  + '"%s", line %i: "%s"' \
                  % (filename, cfg[:pos + 1].count('\n') + 1,
                     cfg[pos:cfg.find('\n', pos + 1)].strip('\n'))
        raise SyntaxError(err_str)
    return unit


def unit_from_json(json_str, filename, allowed_stages=UNIT_STAGES):
    """
    Reads grammar unit tests from a json string.
    """
    unit = json.loads(json_str)
    for symbol in unit:
        for stage in unit[symbol]:
            if stage not in allowed_stages:
                raise ValueError('in file "%s". Test stage %s not in: %s'
                                 % (filename, stage, str(allowed_stages)))
    return unit


# TODO: add support for yaml, cson, toml


# A dictionary associating file endings with reader functions that
# transform strings containing the file's content to a nested dictionary
# structure of test cases.
TEST_READERS = {
    '.ini': unit_from_config,
    '.json': unit_from_json
}


def unit_from_file(filename, additional_stages=UNIT_STAGES):
    """
    Reads a grammar unit test from a file. The format of the file is
    determined by the ending of its name.
    """
    allowed_stages = additional_stages | UNIT_STAGES
    if not os.path.exists(filename):  raise FileNotFoundError(filename)
    if not os.path.isfile(filename):  raise ValueError('"%s" is not a file!' % filename)
    try:
        reader = TEST_READERS[os.path.splitext(filename)[1].lower()]
    except KeyError:
        i = filename.rfind('.')
        if i < 0:  i = len(filename)
        raise ValueError('Unknown unit test file type "%s" of file: %s' % (filename[i:], filename))
    with open(filename, 'r', encoding='utf8') as f:
        data = f.read()
    test_unit = reader(data, filename, allowed_stages)

    # Check for ambiguous Test names
    errors = []
    for parser_name, tests in test_unit.items():
        # normalize case for test category names
        # keys = list(tests.keys())
        # for key in keys:
        #     new_key = key.lower()
        #     if new_key != key:
        #         tests[new_key] = tests[key]
        #         del tests[key]

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


def indent(txt):
    lines = txt.split('\n')
    lines[0] = '    ' + lines[0]
    return "\n    ".join(lines)

def get_report(test_unit, serializations: Dict[str, List[str]] = dict()) -> str:
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
    report = []
    srl = { k: v[0] for k, v in serializations.items()}
    save = get_config_value('xml_attribute_error_handling')
    set_config_value('xml_attribute_error_handling', 'fix')
    for parser_name, tests in test_unit.items():
        if parser_name[-2:] == '__':
            heading = parser_name[:-2]
            report.append(f"{heading}\n{'=' * len(heading)}\n\n"
                + '\n'.join(f"{k} = {repr(v)}" for k, v in tests.items()))
            continue
        heading = 'Test of parser: "%s"' % parser_name
        report.append('\n\n%s\n%s' % (heading, '=' * len(heading)))
        for test_name, test_code in tests.get('match', dict()).items():
            heading = '\nMatch-test "%s"' % test_name
            report.append('\n%s\n%s\n' % (heading, '-' * len(heading)))
            report.append('### Test-code:\n')
            report.append(indent(test_code))
            error = tests.get('__err__', {}).get(test_name, "")
            if error:
                report.append('\n### Error:\n')
                report.append(error)
            ast = tests.get('__AST__', {}).get(test_name, None)
            cst = tests.get('__CST__', {}).get(test_name, None)
            if cst and (not ast or str(test_name).endswith('*')):
                report.append('\n### CST\n')
                report.append(indent(cst.serialize(srl.get('CST', 'CST'))))
            if ast:
                report.append('\n### AST\n')
                report.append(indent(ast.serialize(srl.get('AST', 'AST'))))

            compilation_stages = [key for key in tests
                                  if key[:2] + key[-2:] == '____' and key not in
                                  {'__AST__', '__CST__', '__err__', 'match', 'fail'}]
            for stage in compilation_stages:
                if test_name in tests[stage]:
                    result = tests[stage][test_name]
                    report.append(f'\n### {stage.strip("_")}\n')
                    if isinstance(result, Node):
                        result_str = cast(Node, result).serialize(
                            srl.get(stage.strip('_'), srl.get('*', 'default')))
                    else:
                        result_str = str(result)
                    report.append(indent(result_str))

        for test_name, test_code in tests.get('fail', dict()).items():
            heading = '\nFail-test "%s"' % test_name
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
    set_config_value('xml_attribute_error_handling', save)
    return '\n'.join(report)


POSSIBLE_ARTIFACTS = frozenset((
    RESUME_NOTICE,
    PARSER_LOOKAHEAD_MATCH_ONLY,
    PARSER_LOOKAHEAD_FAILURE_ONLY,
    MANDATORY_CONTINUATION_AT_EOF_NON_ROOT,
    CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY,
    AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT
))

TEST_ARTIFACT = "__TEST_ARTIFACT__"


def md_codeblock(code: str) -> str:
    """Formats a piece of code as Markdown inline-code or code-block,
    depending on whether it stretches over several lines or not."""
    if '\n' not in code:
        return '`' + code + '`'
    else:
        # linefeeds = re.match('\s*', code).group(0).count('\n')
        lines = code.strip().split('\n')
        return '\n\n\t' + '\n\t'.join(lines)


def grammar_unit(test_unit, parser_factory, transformer_factory, report='REPORT', verbose=False,
                 junctions=set(), show=set(), serializations: Dict[str, List[str]] = dict()):
    """
    Unit tests for a grammar-parser and ast-transformations.

    :param test_unit: The test-unit in a json-like dictionary format as it is returned by
        :py:func:`~testing.unit_from_file`.
    :param parser_factory: the parser-factory-object, typically an instance of
        :py:class:`~parse.Grammar`.
    :param transformer_factory: A factory-function for the AST-transformation-function.
    :param report: the name of the subdirectory where the test-reports will be saved.
        If the name is the empty string, no reports will be generated.
    :param verbose: If True, more information will be printed to the console during testing.
    :param junctions: A set of :py:class:`~compile.Junction`-objects that define further
        processing stages after the AST-transformation.
    :param show: A set of stage names that shall be shown in the report apart from the AST.
        (The abstract-syntax-tree will always be shown!)
    """
    assert isinstance(report, str)
    assert isinstance(junctions, Set) and all(isinstance(e[0], str) and isinstance(e[2], str)
                                              and callable(e[1]) for e in junctions), \
        f"Value {repr(junctions)} passed to parameter 'junctions' is not a set of compilation-junctions!"
    assert isinstance(show, Set) and all(isinstance(element, str) for element in show), \
        f"Value {repr(show)} passed to parameter 'show' is not a set of strings!"

    output = []

    def write(s):
        """Append string `s` to output. The purpose is to defer printing to
        stdout in order to avoid muddled output when several unit tests run
        at the same time."""
        nonlocal output
        output.append(s)

    def clean_key(k):
        try:
            return k.replace('*', '')
        except AttributeError:
            return k

    def get(tests, category, key) -> Union[Node, str]:
        try:
            try:
                return tests[category][key]
            except KeyError:
                return tests[category][clean_key(key)]
        except KeyError:
            return ""

    if isinstance(test_unit, str):
        _, unit_name = os.path.split(os.path.splitext(test_unit)[0])
        test_unit = unit_from_file(test_unit, UNIT_STAGES | {j[2] for j in junctions})
    else:
        unit_name = 'unit_test_' + str(id(test_unit))
    if verbose:
        write("\nGRAMMAR TEST UNIT: " + unit_name)
    errata = []
    config_history_tracking = get_config_value('history_tracking')
    config_resume_notices = get_config_value('resume_notices')
    parser = parser_factory()
    transform = transformer_factory()

    def has_lookahead(parser_name: str) -> bool:
        """Returns True if the parser or any of its descendant parsers is a
        Lookahead parser."""
        return parser[parser_name].apply(lambda p: isinstance(p, Lookahead))


    def lookahead_artifact(syntax_tree: Node):
        """
        Returns True, if the error merely occurred, because the parser
        stopped in front of a sequence that was captured by a lookahead
        operator or if a mandatory lookahead failed at the end of data.
        This is required for testing of parsers that put a lookahead
        operator at the end. See test_testing.TestLookahead.
        """
        if not get_config_value('test_suppress_lookahead_failures'):
            return False
        raw_errors = cast(RootNode, syntax_tree).errors
        is_artifact = ({e.code for e in raw_errors} <= POSSIBLE_ARTIFACTS
                       or (len(raw_errors) == 1
                           and (raw_errors[-1].code == PARSER_LOOKAHEAD_MATCH_ONLY
                                #  case 2:  mandatory lookahead failure at end of text
                                or raw_errors[-1].code == MANDATORY_CONTINUATION_AT_EOF)))
        if is_artifact:
            # don't remove zombie node with error message at the end
            # but change its name to indicate that it is an artifact!
            for zombie in syntax_tree.select(artifact):
                zombie.name = TEST_ARTIFACT
                zombie.result = 'Artifact can be ignored. Be aware, though, that also the ' \
                                'tree structure may not be the same as in a non-testing ' \
                                'environment, when a testing artifact has occurred!'
        return is_artifact

    def add_errors_to_errata(test_errors: List[Error], stage="?", test_name="?", parser_name="?"):
        nonlocal errata
        test_errors.sort(key=lambda e: e.pos)
        if is_error(max(e.code for e in test_errors) if test_errors else 0):
            if test_errors:
                if errata:  errata[-1] = errata[-1].rstrip('\n')
                errata.append(f'Errors in test "{test_name}" of [{stage}:{parser_name}]\n\t'
                    + '\n\t'.join(str(msg).replace('\n', '\n\t\t') for msg in test_errors))
                # errata.append('\n\n')  # leads to wrong error count!!!

    def flat_string_test(tests, stage, tree, test_name,
                         parser_name, test_code, errata) -> Union[Node, str]:
        compare = get(tests, stage, test_name)
        if compare and isinstance(compare, str):
            content = tree.content
            if content == compare:
                if verbose:  write(f'      {stage}-test "' + test_name + '" ... OK')
                return ""
            else:
                try:
                    return deserialize(compare)
                except ValueError as e:
                    test_code_str = "\n\t".join(test_code.split("\n"))
                    e_str = str(e)
                    if e_str.find('Malformed S-expression') >= 0:
                        errata.append(f'{stage}-test {test_name} for parser {parser_name} '
                                      f'failed because of\n\t{e_str}\n{compare}')
                    else:
                        errata.append(f'{stage}-test {test_name} for parser {parser_name} '
                                      f'failed with: {e_str}:\n'
                                      f'\tExpr.:     {test_code_str}\n'
                                      f'\tExpected:  {compare}\n'
                                      f'\tReceived:  {content}\n')
                    return ""
        return compare or ""

    def log_history(parser_name, test_code, test_name, test_type, track_history):
        nonlocal parser, config_history_tracking
        if not track_history:
            set_tracer(parser[parser_name].descendants(), trace_history)
            try:
                _ = parser(test_code, parser_name)
            except AttributeError:
                pass
            except KeyboardInterrupt as ctrlC:
                with local_log_dir('./LOGS'):
                    log_parsing_history(parser, "interrupted_%s_%s_%s.log" %
                                        (test_type, parser_name, clean_test_name))
                raise ctrlC
            finally:
                set_tracer(parser[parser_name].descendants(), None)
                parser.history_tracking__ = config_history_tracking
        with local_log_dir('./LOGS'):
            tname = test_name.replace('*', '')
            log_parsing_history(parser, f"{test_type}_{parser_name}_{tname}.log")

    saved_config_values = dict()
    for parser_name, tests in test_unit.items():
        if parser_name[-2:] == '__':
            assert parser_name == 'config__', f'Unknown metadata-type: "{parser_name}"'
            for key, value in tests.items():
                saved_config_values[key] = get_config_value(key)
                set_config_value(key, eval(value))
            continue

        track_history = config_history_tracking
        try:
            if has_lookahead(parser_name) or track_history:
                set_tracer(parser[parser_name].descendants(), trace_history)
                track_history = True
        except AttributeError:
            pass

        assert parser_name, "Missing parser name in test %s!" % unit_name
        assert not any(test_type in RESULT_STAGES for test_type in tests), \
            ("Test %s in %s already has results. Use reset_unit() before running again!"
             % (parser_name, unit_name))
        # assert set(tests.keys()).issubset(UNIT_STAGES), \
        #     'Unknown test-types: %s ! Must be one of %s' \
        #     % (set(tests.keys()) - UNIT_STAGES, UNIT_STAGES)
        if verbose:
            write('  Match-Tests for parser "' + parser_name + '"')
        match_tests = set(tests['match'].keys()) if 'match' in tests else set()
        match_test_keys = {clean_key(k) for k in match_tests}

        # normalize AST and CST-names to upper!
        for key in tuple(tests.keys()):
            KEY = key.upper()
            if KEY in ('AST', 'CST') and KEY != key:
                tests[KEY] = tests[key]
                del tests[key]

        transformation_stages = {key for key in tests if key not in {'match', 'fail'}}
        for stage in transformation_stages:
            transformation_tests = set(tests[stage].keys())
            if not {clean_key(k) for k in transformation_tests} <= match_test_keys:
                raise AssertionError(f'{stage}-tests {transformation_tests - match_test_keys}'
                                     ' lack corresponding match-tests.')
        # cst and ast will be treated separately in the following and are thus not
        # needed any more in the list
        for stage in ('CST', 'AST'):
            try:
                transformation_stages.remove(stage)
            except (KeyError, ValueError):
                pass

        # run match tests

        for test_name, test_code in tests.get('match', dict()).items():
            errflag = len(errata)
            err: Optional[Error] = None
            clean_test_name = str(test_name).replace('*', '')
            try:
                cst = parser(test_code, parser_name)
            except AttributeError as upe:
                cst = RootNode()
                cst = cst.new_error(Node(ZOMBIE_TAG, "").with_pos(0), str(upe))
            except KeyboardInterrupt as ctrlC:
                if is_logging() and track_history:
                    with local_log_dir('./LOGS'):
                        log_parsing_history(parser, "interrupted_match_%s_%s.log" %
                                            (parser_name, clean_test_name))
                raise ctrlC

            tests.setdefault('__CST__', {})[test_name] = cst
            # errors = []  # type: List[Error]
            if is_error(cst.error_flag) and not lookahead_artifact(cst):
                errors = [e for e in cst.errors if e.code not in POSSIBLE_ARTIFACTS]
                errata.append('Match test "%s" for parser "%s" failed:'
                              '\n\tExpr.:  %s\n\t%s' %
                              (test_name, parser_name, md_codeblock(test_code),
                               '\n'.join(str(m) for m in errors)))
            if 'AST' in tests or report or transformation_stages or show:
                ast = copy.deepcopy(cst) if 'CST' in tests or str(test_name).find('*') >= 0 \
                      else cst
                old_errors = set(ast.errors)
                traverse(ast, {'*': remove_children({TEST_ARTIFACT})})
                try:
                    transform(ast)
                except AssertionError as e:
                    e.args = ('Test %s of parser %s failed, because:\n%s'
                              % (test_name, parser_name, e.args[0]),)
                    raise e
                tests.setdefault('__AST__', {})[test_name] = ast
                ast_errors = [e for e in ast.errors if e not in old_errors]
                add_errors_to_errata(ast_errors, 'AST', test_name, parser_name)

            # compilation-tests

            if transformation_stages or show:
                if parser_name not in parser:
                    # fail hard when trying a compiliation test with a non-existing
                    # parser (resp. node-type), because otherwise obscure subsequent
                    # errors can occur. (Eventually develop a better solution, that ist...)
                    raise ValueError(
                        f'Unknown parser "{parser_name}" in test(s) '
                        f'{", ".join([repr(t) for t in tests.keys()])} in unit "{unit_name}"!')
                old_errors = set(ast.errors)
                try:
                    targets = run_pipeline(junctions, {'AST': copy.deepcopy(ast)},
                                           transformation_stages | show)
                except Exception as e:  # at least: (ValueError, IndexError)
                    import traceback
                    # raise SyntaxError(f'Compilation-Test {test_name} of parser {parser_name} '
                    #                   f'failed with:\n{str(e)}\n{traceback.format_exc()}')
                    err = Error(f'Python Error in compilation-test {test_name} of parser '
                                f'{parser_name} failed with: {str(e)}\n{traceback.format_exc()}\n'
                                f'Processing of {test_name}:{parser_name} stopped at this point.',
                                pos=0, code=PYTHON_ERROR_IN_TEST, line=1, column=0)
                    add_errors_to_errata([err], '?', test_name, parser_name)
                    targets = dict()
                t_errors: Dict[str, List[Error]] = {}
                for stage in list(transformation_stages) + [t for t in targets if t in show]:
                    try:
                        tests.setdefault(f'__{stage}__', {})[test_name] = targets[stage][0]
                        t_errors[stage] = [e for e in targets[stage][1] if e not in old_errors]
                        for e in t_errors[stage]:
                            old_errors.add(e)
                        add_errors_to_errata(t_errors[stage], stage, test_name, parser_name)
                    except KeyError as ke:
                        # ignore key errors in case they are only consequential errors
                        # of earlier errors
                        if err.code != PYTHON_ERROR_IN_TEST:
                            raise ke
                # keep test-items, so that the order of the items is the same as
                # in which they are processed in the pipeline.
                for t in targets:
                    if t in show:
                        k = f'__{t}__'
                        if k in tests:
                            save = tests[k]
                            del tests[k]
                            tests[k] = save

            if verbose:
                infostr = '    match-test "' + test_name + '" ... '
                write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if 'CST' in tests and len(errata) == errflag:
                compare = flat_string_test(tests, 'CST', cst, test_name,
                                           parser_name, test_code, errata)
                if compare:
                    if not compare.equals(cst):
                        errata.append('Concrete syntax tree test "%s" for parser "%s" failed:\n%s' %
                                      (test_name, parser_name, cst.serialize('CST')))
                    if verbose:
                        infostr = '      CST-test "' + test_name + '" ... '
                        write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if 'AST' in tests and len(errata) == errflag:
                compare = flat_string_test(tests, 'AST', ast, test_name,
                                           parser_name, test_code, errata)
                if compare:
                    traverse(compare, {'*': remove_children({TEST_ARTIFACT})})
                    if not compare.equals(ast):  # no worry: ast is defined if 'AST' in tests
                        ast_str = flatten_sxpr(ast.as_sxpr())
                        compare_str = flatten_sxpr(compare.as_sxpr())
                        templ = 'Abstract syntax tree test "%s" for parser "%s" failed:' \
                                '\n\tExpr.:     %s\n\tExpected:  %s\n\tReceived:  %s'
                        errata.append(templ % (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                                               compare_str, ast_str))
                    if verbose:
                        infostr = '      AST-test "' + test_name + '" ... '
                        write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if len(errata) == errflag and transformation_stages:
                for stage in transformation_stages:
                    try:
                        data = extract_data(targets[stage][0])
                        if isinstance(data, Node):
                            compare = flat_string_test(tests, stage, data, test_name,
                                                       parser_name, test_code, errata)
                            if compare and not compare.equals(data):
                                test_str = flatten_sxpr(data.as_sxpr())
                                compare_str = flatten_sxpr(compare.as_sxpr())
                                test_code_str = "\n\t".join(test_code.split("\n"))
                                errata.append(f'{stage}-test {test_name} for parser {parser_name} failed:\n'
                                              f'\tExpr.:     {test_code_str}\n'
                                              f'\tExpected:  {compare_str}\n'
                                              f'\tReceived:  {test_str}')
                        else:
                            compare = get(tests, stage, test_name).strip('\n')
                            if compare:
                                test_str = str(data)
                                if stage in ('match', 'fail', 'AST', 'CST'):
                                    test_str = normalize_code(test_str, full_normalization=False)
                                else:
                                    test_str = test_str.strip('\n')
                                if not compare == test_str:
                                    test_code_str = "\n\t".join(test_code.split("\n"))
                                    if compare.find('\n') >= 0 and compare.strip() == compare:
                                        compare = '\n' + compare + '\n'
                                    if test_str.find('\n') >= 0 and test_str.strip() == test_str:
                                        test_str = '\n' + test_str + '\n'
                                    errata.append(f'{stage}-test {test_name} for parser {parser_name} failed:\n'
                                                  f'\tExpr.:     {test_code_str}\n'
                                                  f'\tExpected:  {compare}\n'
                                                  f'\tReceived:  {test_str}')
                    except ValueError as e:
                        raise SyntaxError(f'{stage}-test {test_name} of parser {parser_name} '
                                          f'failed with:\n{str(e)}.')
                    if verbose and compare:
                        infostr = ' ' * (max(0, 9 - len(stage))) \
                                  + f'{stage}-test "' + test_name + '" ... '
                        write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

            if len(errata) > errflag or config_history_tracking:
                if len(errata) > errflag:
                    tests.setdefault('__err__', {})[test_name] = errata[-1]
                if is_logging():
                    log_history(parser_name, test_code, clean_test_name, 'match', track_history)

        if verbose and 'fail' in tests:
            write('  Fail-Tests for parser "' + parser_name + '"')

        # run fail tests

        for test_name, test_code in tests.get('fail', dict()).items():
            errflag = len(errata)
            try:
                cst = parser(test_code, parser_name)
            except AttributeError as upe:
                node = Node(ZOMBIE_TAG, "").with_pos(0)
                cst = RootNode(node).new_error(node, str(upe))
                errata.append('Unknown parser "{}" in fail test "{}"!'.format(
                    parser_name, test_name))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
            if 'AST' in tests or report:
                traverse(cst, {'*': remove_children({TEST_ARTIFACT})})
                transform(cst)
            store_fail_log = config_history_tracking
            if not (is_error(cst.error_flag) and not lookahead_artifact(cst)):
                treestr = ''
                errata.append(f'Fail test "{test_name}" for parser "{parser_name}" '
                              f'yields match instead of expected failure!' + treestr)
                tests.setdefault('__err__', {})[test_name] = errata[-1]
                store_fail_log = True
            if is_logging() and store_fail_log:
                log_history(parser_name, test_code, test_name, 'fail', track_history)
            if cst.error_flag:
                tests.setdefault('__msg__', {})[test_name] = \
                    "\n".join(str(e) for e in cst.errors)
            if verbose:
                infostr = '    fail-test  "' + test_name + '" ... '
                write(infostr + ("OK" if len(errata) == errflag else "FAIL"))

        if track_history and not config_history_tracking:
            set_tracer(parser[parser_name].descendants(), None)
            parser.history_tracking__ = False
        parser.resume_notices__ = config_resume_notices

    # write test-report
    if report:
        test_report = get_report(test_unit, serializations)
        if test_report:
            try:
                os.mkdir(report)   # is a process-Lock needed, here?
            except FileExistsError:
                pass
            with open(os.path.join(report, unit_name + '.md'), 'w', encoding='utf8') as f:
                f.write(test_report)
                f.flush()

    # restore changed config values
    for key, value in saved_config_values.items():
        set_config_value(key, value)

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


def unique_name(file_name: str) -> str:
    """Turns the file or dirname into a unique name by adding a time stamp.
    This helps to avoid race conditions when running tests in parallel
    that create and delete files on the disk.
    """
    # return concurrent_ident() + '_' + file_name
    resolution = 1000000
    unique_nr = int(time.time() * resolution) + random.randint(0, resolution)
    name = 'unique_' + str(unique_nr) + '_' + file_name
    time.sleep(1.0 / resolution)
    return name


def grammar_suite(directory, parser_factory, transformer_factory,
                  fn_patterns=('*test*',),
                  ignore_unknown_filetypes=False,
                  report='REPORT', verbose=True,
                  junctions=set(), show=set(),
                  serializations: Dict[str, List[str]] = dict()):
    """
    Runs all grammar unit tests in a directory. A file is considered a test
    unit, if it has the word "test" in its name.
    """
    assert isinstance(report, str)
    assert isinstance(show, set) and all(isinstance(element, str) for element in show), \
        f"Value {repr(show)} passed to parameter 'show' is not a set of strings!"
    assert isinstance(junctions, set) and all(isinstance(e[0], str) and isinstance(e[2], str)
                                              and callable(e[1]) for e in junctions), \
        f"Value {repr(junctions)} passed to parameter 'show' is not a set of compilation-junctions!"

    if not isinstance(fn_patterns, collections.abc.Iterable):
        fn_patterns = [fn_patterns]
    all_errors = OrderedDict()
    if verbose:
        print("\nScanning test-directory: " + directory)
    save_cwd = os.getcwd()
    os.chdir(directory)
    if is_logging():
        clear_logs()

    tests = [fn for fn in sorted(os.listdir('.'))
             if any(fnmatch.fnmatch(fn, pattern) for pattern in fn_patterns)]

    assert tests, f"No pattern from {fn_patterns} matched any test in directory {os.getcwd()}"

    with instantiate_executor(get_config_value('test_parallelization') and len(tests) > 1,
                              concurrent.futures.ProcessPoolExecutor) as pool:
        results = []
        for filename in tests:
            parameters = (filename, parser_factory, transformer_factory,
                          report, verbose, junctions, show, serializations)
            results.append(pool.submit(grammar_unit, *parameters))
        done, not_done = concurrent.futures.wait(results)
        assert not not_done, str(not_done)
        for filename, err_future in zip(tests, results):
            try:
                errata = err_future.result()
                if errata:
                    all_errors[filename] = errata
            except ValueError as e:
                if not ignore_unknown_filetypes or str(e).find("Unknown") < 0:
                    raise e
            except AssertionError as e:
                e.args = ('When processing "%s":\n%s' % (filename, e.args[0]) if e.args else '',)
                raise e
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
        return ('Test suite "%s" revealed %s error%s:\n'
                % (directory, err_N, 's' if err_N > 1 else '') + '\n'.join(error_report))
    if verbose:
        print("\nSUCCESS! All tests passed :-)\n")
    return ''


########################################################################
#
# Support for unit-testing of ebnf-grammars
#
########################################################################


RX_DEFINITION_OR_SECTION = re.compile(r'(?:^|\n)[ \t]*(\w(?:-?\w)*(?=[ \t]*:?:?=)|#:.*(?=\n|$|#))')
SymbolsDictType: TypeAlias = Dict[str, List[str]]

ALL_SYMBOLS = 'ALL_SYMBOLS'


def extract_symbols(ebnf_text_or_file: str) -> SymbolsDictType:
    r"""
    Extracts all defined symbols from an EBNF-grammar. This can be used to
    prepare grammar-tests. The symbols will be returned as lists of strings
    which are grouped by the sections to which they belong and returned as
    an ordered dictionary, the keys of which are the section names.
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
    :return: Ordered dictionary mapping the section names of the
        grammar to lists of symbols that appear under that section.
    """
    def trim_section_name(name: str) -> str:
        return re.sub(r'[^\w-]', '_', name.replace('#:', '').strip())

    ebnf = load_if_file(ebnf_text_or_file)
    deflist = RX_DEFINITION_OR_SECTION.findall(ebnf)
    deflist = [(re.sub(r'(?<=\w)-(?=\w)', '_', dfn) if dfn[:2] != '#:' else dfn)
               for dfn in deflist]
    if not deflist:
        if ebnf_text_or_file.find('\n') < 0 and ebnf_text_or_file.endswith('.ebnf'):
            deflist = ['#: ' + os.path.splitext(ebnf_text_or_file)[0]]
        else:
            deflist = ['#: ALL']
    symbols = OrderedDict()  # type: SymbolsDictType
    if deflist[0][:2] != '#:':
        curr_section = ALL_SYMBOLS
        symbols[curr_section] = []
    for df in deflist:
        if df[:2] == '#:':
            curr_section = trim_section_name(df)
            if curr_section in symbols:
                raise AssertionError('Section name must not be repeated: ' + curr_section)
            symbols[curr_section] = []
        else:
            symbols[curr_section].append(df)  # no worry, curr_section is always defined
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
        path: the path to the grammar-test directory (usually 'tests_grammar').
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
        existing_tests = {fname[3:]: fname for fname in os.listdir() if os.path.isfile(fname)}
        for i, k in enumerate(keys):
            filename = '{num:0>2}_test_{section}'.format(num=i + 1, section=k) + fmt
            if not os.path.exists(filename):
                if filename[3:] in existing_tests:
                    old_name = existing_tests[filename[3:]]
                    print(f'Renaming test file "{old_name}" to "{filename}"')
                    os.rename(old_name, filename)
                    existing_tests[filename[3:]] = filename
                elif k is not ALL_SYMBOLS or not existing_tests:
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
        instance_dir = dir(instance)
        if "setup" in instance_dir:
            setup_method = instance.setup
        elif "setup_method" in instance_dir:
            setup_method = instance.setup_method
        else:
            setup_method = lambda : 0
        if "teardown" in instance_dir:
            teardown_method = instance.teardown
        elif "teardown_method" in instance_dir:
            teardown_method = instance.teardown_method
        else:
            teardown_method = lambda : 0
        setup_class = instance.setup_class if "setup_class" in instance_dir else lambda : 0
        teardown_class = instance.teardown_class if "teardown_class" in instance_dir else lambda : 0

        return instance, setup_method, teardown_method, setup_class, teardown_class

    obj = None
    obj, setup, teardown, setup_class, teardown_class = instantiate(cls_name, namespace)
    setup_class()
    if methods:
        for name in methods:
            func = obj.__getattribute__(name)
            if callable(func):
                print("Running " + cls_name + "." + name)
                setup();  func();  teardown()
    else:
        for name in dir(obj):
            if name.lower().startswith("test"):
                func = obj.__getattribute__(name)
                if callable(func):
                    print("Running " + cls_name + "." + name)
                    setup();  func();  teardown()
    teardown_class()


def run_test_function(func_name, namespace):
    """
    Run the test-function `test` in the given namespace.
    """
    print("Running test-function: " + func_name)
    exec(func_name + '()', namespace)


def runner(tests, namespace, profile=False):
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

    :param tests: String or list of strings with the names of tests
        to run. If empty, runner searches by itself all objects the
        of which starts with 'test' and runs it (if it is a function)
        or all of its methods that start with "test" if it is a class
        plus the "setup" and "teardown" methods if they exist.

    :param namespace: The namespace for running the test, usually
        ``globals()`` should be used.

    :param profile: If True, the tests will be run with the profiler on.
        results will be displayed after the test-results. Profiling will
        also be turned on, if the parameter `--profile` has been provided
        on the command line.

    Example::

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
    test_classes = OrderedDict()
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

    import inspect
    for name in tests:
        func_or_class, method = (name.split('.') + [''])[:2]
        if inspect.isclass(namespace[func_or_class]):
            if func_or_class not in test_classes:
                test_classes[func_or_class] = []
            if method:
                test_classes[func_or_class].append(method)
        elif inspect.isfunction(namespace[name]):
            test_functions.append(name)

    profile = profile or '--profile' in sys.argv
    if profile:
        import cProfile, pstats
        pr = cProfile.Profile()
        pr.enable()

    for cls_name, methods in test_classes.items():
        run_tests_in_class(cls_name, namespace, methods)

    for test in test_functions:
        run_test_function(test, namespace)

    if profile:
        pr.disable()
        st = pstats.Stats(pr)
        st.strip_dirs()
        st.sort_stats('time').print_stats(50)


def run_file(fname):
    f_lower = fname.lower()
    if f_lower.startswith('test_') and f_lower.endswith('.py'):
        print("RUNNING " + fname)
        exec('import ' + fname[:-3])
        runner('', eval(fname[:-3]).__dict__)


def run_path(path):
    """Runs all unit tests in `path`"""
    if os.path.isdir(path):
        sys.path.append(path)
        files = os.listdir(path)
        results = []
        with instantiate_executor(get_config_value('test_parallelization') and len(files) > 1,
                                  concurrent.futures.ProcessPoolExecutor) as pool:
            for f in files:
                f_lower = f.lower()
                if f_lower.startswith('test_') and f_lower.endswith('.py'):
                    results.append(pool.submit(run_file, f))
                # run_file(f)  # for testing!
            concurrent.futures.wait(results)
            for r in results:
                try:
                    _ = r.result()
                except AssertionError as failure:
                    print(failure)

    else:
        path, fname = os.path.split(path)
        sys.path.append(path)
        run_file(fname)
    sys.path.pop()


def clean_report(report_dir='REPORT'):
    """Deletes any test-report-files in the REPORT subdirectory and removes
    the REPORT subdirectory, if it is empty after deleting the files."""
    # TODO: make this thread/process safe, if possible!!!!
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


#######################################################################
#
#  server testing support
#
#######################################################################


async def read_full_content(reader) -> bytes:
    data = b''
    content_length = 0
    while not reader.at_eof():
        data += await reader.read(content_length or -1)
        i = data.find(b'Content-Length:', 0, 512)
        m = RX_CONTENT_LENGTH.match(data, i, i + 100) if i >= 0 else None
        if m:
            content_length = int(m.group(1))
            m2 = re.search(RE_DATA_START, data)
            if m2:
                header_size = m2.end()
                if len(data) < header_size + content_length:
                    content_length = header_size + content_length - len(data)
                else:
                    break
    return data


def add_header(b: bytes) -> bytes:
    return JSONRPC_HEADER_BYTES % len(b) + b


async def stdio(limit=asyncio.streams._DEFAULT_LIMIT, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    reader = asyncio.StreamReader(limit=limit, loop=loop)
    await loop.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(reader, loop=loop), sys.stdin)

    writer_transport, writer_protocol = await loop.connect_write_pipe(
        lambda: asyncio.streams.FlowControlMixin(loop=loop),
        os.fdopen(sys.stdout.fileno(), 'wb'))
    writer = asyncio.streams.StreamWriter(
        writer_transport, writer_protocol, None, loop)

    return reader, writer


class MockStream:
    """Simulates a stream that can be written to from one side and read
    from the other side like a pipe. Usage pattern::

        pipe = MockStream()
        reader = StreamReaderProxy(pipe)
        writer = StreamWriterProxy(pipe)

        async def main(text):
            writer.write((text + '\n').encode())
            await writer.drain()
            data (await reader.read()).decode()
            writer.close()
            return data

        asyncio.run(main('Hello World'))
    """
    def __init__(self, name=''):
        self.name = name or str(id(self))
        self.lock = threading.Lock()
        self.data_waiting = threading.Event()
        self.data_waiting.clear()
        self.data = collections.deque()
        self._closed = False  # type: bool

    def close(self):
        with self.lock:
            self.data_waiting.set()  # wake up any waiting readers
            self._closed = True

    @property
    def closed(self) -> bool:
        countdown = 50
        while self._closed and self.data and countdown > 0:
            self.data_waiting.set()
            time.sleep(0.01)
            countdown -= 1
        return self._closed

    def data_available(self) -> int:
        """Returns the size of the available data."""
        return sum(len(chunk) for chunk in self.data)

    def write(self, data: bytes):
        assert isinstance(data, bytes)
        with self.lock:
            if self._closed:
                raise ValueError("I/O operation on closed file.")
            self.data.append(data)
            # self.data_waiting.set()

    def writelines(self, data: List[bytes]):
        assert all(isinstance(datum, bytes) for datum in data)
        with self.lock:
            if self._closed:
                raise ValueError("I/O operation on closed file.")
            self.data.extend(data)
            # self.data_waiting.set()

    def flush(self):
        with self.lock:
            self.data_waiting.set()

    def _read(self, n=-1) -> Union[List[bytes], Deque[bytes]]:
        with self.lock:
            if n < 0:
                self.data_waiting.clear()
                if len(self.data) == 1:
                    return [self.data.popleft()]
                else:
                    data = self.data
                    # use pop() to clear data, so the data-list object stays in place
                    # which would not be the case when simply assigning an empty list.
                    while self.data:
                        self.data.pop()
                    return data
            elif n > 0:
                size = 0
                data = []
                while size < n and self.data:
                    i = len(self.data[0])
                    if size + i <= n:
                        data.append(self.data.popleft())
                        size += i
                    else:
                        cut = size + i - n
                        data.append(self.data[0][:cut])
                        self.data[0] = self.data[0][cut:]
                        size = n
                if not self.data:
                    self.data_waiting.clear()
                return data
            else:
                return [b'']

    def _readline(self) -> Union[List[bytes], Deque[bytes]]:
        with self.lock:
            data = []
            while self.data:
                i = self.data[0].find(b'\n')
                if i < 0:
                    data.append(self.data.popleft())
                elif i == len(self.data[0]) - 1:
                    data.append(self.data.popleft())
                    break
                else:
                    data.append(self.data[0][:i + 1])
                    self.data[0] = self.data[0][i + 1:]
                    break
            if not self.data:
                self.data_waiting.clear()
            return data

    def read(self, n=-1) -> bytes:
        data = self._read(n)
        if n > 0:
            N = sum(len(chunk) for chunk in data)
            while N < n:
                self.data_waiting.wait()
                more = self._read(n)
                N += sum(len(chunk) for chunk in more)
                data.extend(more)
        return b''.join(data)

    def readline(self) -> bytes:
        data = self._readline()
        while not self._closed and (not data or data[-1][-1] != ord(b'\n')):
            self.data_waiting.wait()
            data.extend(self._readline())
        return b''.join(data)
