"""testing.py - test support for DHParser based grammars and compilers

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""
import collections
import configparser
import copy
import inspect
import json
import os
try:
    import regex as re
except ImportError:
    import re

from DHParser import Node, error_messages
from DHParser.toolkit import compact_sexpr, is_logging
from DHParser.syntaxtree import MockParser
from DHParser.ebnf import grammar_changed
from DHParser.dsl import compile_on_disk


def mock_syntax_tree(sexpr):
    """Generates a tree of nodes from an S-expression.

    Example: 
    >>> mock_syntax_tree("(a (b c))").as_sexpr()
    (a 
        (b 
            "c" 
        )
    )
    """
    def next_block(s):
        s = s.strip()
        while s[0] != ')':
            if s[0] != '(': raise ValueError('"(" expected, not ' + s[:10])
            # assert s[0] == '(', s
            level = 1
            i = 1
            while level > 0:
                if s[i] == '(':
                    level += 1
                elif s[i] == ')':
                    level -= 1
                i += 1
            yield s[:i]
            s = s[i:].strip()

    sexpr = sexpr.strip()
    if sexpr[0] != '(': raise ValueError('"(" expected, not ' + sexpr[:10])
    # assert sexpr[0] == '(', sexpr
    sexpr = sexpr[1:].strip()
    m = re.match('[\w:]+', sexpr)
    name, class_name = (sexpr[:m.end()].split(':') + [''])[:2]
    sexpr = sexpr[m.end():].strip()
    if sexpr[0] == '(':
        result = tuple(mock_syntax_tree(block) for block in next_block(sexpr))
    else:
        lines = []
        while sexpr and sexpr[0] != ')':
            for qm in ['"""', "'''", '"', "'"]:
                m = re.match(qm + r'.*?' + qm, sexpr)
                if m:
                    i = len(qm)
                    lines.append(sexpr[i:m.end() - i])
                    sexpr = sexpr[m.end():].strip()
                    break
            else:
                m = re.match(r'(?:(?!\)).)*', sexpr)
                lines.append(sexpr[:m.end()])
                sexpr = sexpr[m.end():]
        result = "\n".join(lines)
    return Node(MockParser(name, ':' + class_name), result)


def recompile_grammar(ebnf_filename, force=False) -> bool:
    """Recompiles an ebnf-grammar if necessary, that is if either no
    corresponding 'XXXXCompiler.py'-file exists or if that file is
    outdated.
    
    Parameters:
        ebnf_filename(str):  The filename of the ebnf-source of the 
            grammar. In case this is a directory and not a file all
            files within this directory ending with .ebnf will be 
            compiled.
        force(bool):  If False (default), the grammar will only be
            recompiled if it has been changed.
    """
    if os.path.isdir(ebnf_filename):
        success = True
        for entry in os.listdir(ebnf_filename):
            if entry.lower().endswith('.ebnf') and os.path.isfile(entry):
                success = success and recompile_grammar(entry, force)
        return success

    base, ext = os.path.splitext(ebnf_filename)
    compiler_name = base + 'Compiler.py'
    errors = []
    if (not os.path.exists(compiler_name) or force or
        grammar_changed(compiler_name, ebnf_filename)):
        # print("recompiling parser for: " + ebnf_filename)
        errors = compile_on_disk(ebnf_filename)
        if errors:
            # print("Errors while compiling: " + ebnf_filename + '!')
            with open(base + '_errors.txt', 'w') as f:
                for e in errors:
                    f.write(e)
                    f.write('\n')
            return False

    if not errors and os.path.exists(base + '_errors.txt'):
        os.remove(base + '_errors.txt')
    return True


UNIT_STAGES = {'match', 'fail', 'ast', 'cst', '__ast__', '__cst__'}


def unit_from_configfile(config_filename):
    """Reads a grammar unit test from a config file.
    """
    cfg = configparser.ConfigParser()
    cfg.read(config_filename)
    OD = collections.OrderedDict
    unit = OD()
    for section in cfg.sections():
        symbol, stage = section.split(':')
        if stage not in UNIT_STAGES:
            if symbol in UNIT_STAGES:
                symbol, stage = stage, symbol
            else:
                raise ValueError('Test stage %s not in: ' % (stage, str(UNIT_STAGES)))
        for testkey, testcode in cfg[section].items():
            if testcode[:3] + testcode[-3:] in {"''''''", '""""""'}:
                testcode = testcode[3:-3]
            elif testcode[:1] + testcode[-1:] in {"''", '""'}:
                testcode = testcode[1:-1]
            unit.setdefault(symbol, OD()).setdefault(stage, OD())[testkey] = testcode
    # print(json.dumps(unit, sort_keys=True, indent=4))
    return unit


def unit_from_json(json_filename):
    """Reads a grammar unit test from a json file.
    """
    with open(json_filename, 'r') as f:
        unit = json.load(f)
    for symbol in unit:
        for stage in unit[symbol]:
            if stage not in UNIT_STAGES:
                raise ValueError('Test stage %s not in: ' % (stage, str(UNIT_STAGES)))
    return unit

# TODO: add support for yaml, cson, toml


def unit_from_file(filename):
    """Reads a grammar unit test from a file. The format of the file is
    determined by the ending of its name.
    """
    if filename.endswith(".json"):
        return unit_from_json(filename)
    elif filename.endswith(".ini"):
        return unit_from_configfile(filename)
    else:
        raise ValueError("Unknown unit test file type: " + filename[filename.rfind('.'):])


def get_report(test_unit):
    """Returns a text-report of the results of a grammar unit test.
    """
    report = []
    for parser_name, tests in test_unit.items():
        heading = 'Test of parser: "%s"' % parser_name
        report.append('\n\n%s\n%s\n' % (heading, '=' * len(heading)))
        for test_name, test_code in tests.get('match', dict()).items():
            heading = 'Match-test "%s"' % test_name
            report.append('\n%s\n%s\n' % (heading, '-' * len(heading)))
            report.append('### Test-code:')
            report.append(test_code)
            error = tests.get('__err__', {}).get(test_name, "")
            if error:
                report.append('\n### Error:')
                report.append(error)
            ast = tests.get('__ast__', {}).get(test_name, None)
            cst = tests.get('__cst__', {}).get(test_name, None)
            if cst and (not ast or cst == ast):
                report.append('\n### CST')
                report.append(cst.as_sexpr())
            elif ast:
                report.append('\n### AST')
                report.append(ast.as_sexpr())
    return '\n'.join(report)


def grammar_unit(test_unit, parser_factory, transformer_factory, report=True, verbose=False):
    """Unit tests for a grammar-parser and ast transformations.
    """
    if isinstance(test_unit, str):
        unit_dir, unit_name = os.path.split(os.path.splitext(test_unit)[0])
        test_unit = unit_from_file(test_unit)
    else:
        unit_dir = ""
        unit_name = str(id(test_unit))
    if verbose:
        print("\nUnit: " + unit_name)
    errata = []
    parser = parser_factory()
    transform = transformer_factory()
    for parser_name, tests in test_unit.items():
        assert set(tests.keys()).issubset(UNIT_STAGES)
        if verbose:
            print('  Match-Tests for parser "' + parser_name + '"')
        for test_name, test_code in tests.get('match', dict()).items():
            if verbose:
                infostr = '    match-test "' + test_name + '" ... '
                errflag = len(errata)
            cst = parser(test_code, parser_name)
            if is_logging():
                cst.log("match_%s_%s.cst" % (parser_name, test_name))
                parser.log_parsing_history("match_%s_%s.log" % (parser_name, test_name))
            tests.setdefault('__cst__', {})[test_name] = cst
            if "ast" in tests or report:
                ast = copy.deepcopy(cst)
                transform(ast)
                tests.setdefault('__ast__', {})[test_name] = ast
                if is_logging():
                    ast.log("match_%s_%s.ast" % (parser_name, test_name))
            if cst.error_flag:
                errata.append('Match test "%s" for parser "%s" failed:\n\tExpr.:  %s\n\n\t%s' %
                              (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                               '\n\t'.join(m.replace('\n', '\n\t\t') for m in
                                           error_messages(test_code, cst.collect_errors()))))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
            elif "cst" in tests and mock_syntax_tree(tests["cst"][test_name]) != cst:
                    errata.append('Concrete syntax tree test "%s" for parser "%s" failed:\n%s' %
                                  (test_name, parser_name, cst.as_sexpr()))
            elif "ast" in tests:
                compare = mock_syntax_tree(tests["ast"][test_name])
                if compare != ast:
                    errata.append('Abstract syntax tree test "%s" for parser "%s" failed:'
                                  '\n\tExpr.:     %s\n\tExpected:  %s\n\tReceived:  %s'
                                  % (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                                     compact_sexpr(compare.as_sexpr()),
                                     compact_sexpr(ast.as_sexpr())))
                    tests.setdefault('__err__', {})[test_name] = errata[-1]
            if verbose:
                print(infostr + ("OK" if len(errata) == errflag else "FAIL"))

        if verbose and 'fail' in tests:
            print('  Fail-Tests for parser "' + parser_name + '"')
        for test_name, test_code in tests.get('fail', dict()).items():
            if verbose:
                infostr = '    fail-test  "' + test_name + '" ... '
                errflag = len(errata)
            cst = parser(test_code, parser_name)
            if is_logging():
                cst.log("fail_%s_%s.cst" % (parser_name, test_name))
                parser.log_parsing_history("fail_%s_%s.log" % (parser_name, test_name))
            if not cst.error_flag:
                errata.append('Fail test "%s" for parser "%s" yields match instead of '
                              'expected failure!' % (test_name, parser_name))
                tests.setdefault('__err__', {})[test_name] = errata[-1]
            if verbose:
                print(infostr + "OK" if len(errata) == errflag else "FAIL")

    # write test-report
    if report:
        report_dir = os.path.join(unit_dir, "REPORT")
        if not os.path.exists(report_dir):
            os.mkdir(report_dir)
        with open(os.path.join(report_dir, unit_name + '.report'), 'w') as f:
            f.write(get_report(test_unit))

    return errata


def grammar_suite(directory, parser_factory, transformer_factory, ignore_unknown_filetypes=False,
                  report=True, verbose=False):
    """Runs all grammar unit tests in a directory. A file is considered a test
    unit, if it has the word "test" in its name.
    """
    all_errors = collections.OrderedDict()
    if verbose:
        print("\nScanning test-directory: " + directory)
    for filename in sorted(os.listdir(directory)):
        if filename.lower().find("test") >= 0:
            try:
                if verbose:
                    print("\nRunning grammar tests from: " + filename)
                errata = grammar_unit(os.path.join(directory, filename),
                                      parser_factory, transformer_factory, report, verbose)
                if errata:
                    all_errors[filename] = errata
            except ValueError as e:
                if not ignore_unknown_filetypes or str(e).find("Unknown") < 0:
                    raise e
    error_report = []
    if all_errors:
        for filename in all_errors:
            error_report.append('Errors found by unit test "%s":' % filename)
            for error in all_errors[filename]:
                error_report.append('\t' + '\n\t'.join(error.split('\n')))
    if error_report:
        return ('Test suite "%s" revealed some errors:\n\n' % directory) + '\n'.join(error_report)
    return ''


def runner(tests, namespace):
    """ Runs all or some selected Python unit tests found in the 
    namespace. To run all tests in a module, call 
    ``runner("", globals())`` from within that module.

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

    if tests:
        if isinstance(tests, str):
            tests = tests.split(" ")
    else:
        # collect all test classes, in case no methods or classes have been passed explicitly
        tests = []
        for name in namespace.keys():
            if name.lower().startswith('test') and inspect.isclass(namespace[name]):
                tests.append(name)

    obj = None
    for test in tests:
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
