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
import copy
import inspect
import regex as re

from DHParser import Node, error_messages
from DHParser.syntaxtree import MockParser
from DHParser.toolkit import compact_sexpr


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
            level = 1;
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


def test_grammar(test_suite, parser_factory, transformer_factory):
    """Unit tests for a grammar-parser and ast transformations.
    """
    errata = []
    parser = parser_factory()
    transform = transformer_factory()
    for parser_name, tests in test_suite.items():
        assert set(tests.keys()).issubset({'match', 'fail', 'ast', 'cst', '__ast__', '__cst__'})

        for test_name, test_code in tests.get('match', dict()).items():
            cst = parser(test_code, parser_name)
            tests.setdefault('__cst__', {})[test_name] = cst
            if cst.error_flag:
                errata.append('Match test "%s" for parser "%s" failed:\n\tExpr.:  %s\n\t%s' %
                              (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                               '\n\t'.join(error_messages(test_code, cst.collect_errors()))))
            elif "cst" in tests and mock_syntax_tree(tests["cst"][test_name]) != cst:
                    errata.append('Concrete syntax tree test "%s" for parser "%s" failed:\n%s' %
                                  (test_name, parser_name, cst.as_sexpr()))
            elif "ast" in tests:
                ast = copy.deepcopy(cst)
                transform(ast)
                tests.setdefault('__ast__', {})[test_name] = ast
                compare = mock_syntax_tree(tests["ast"][test_name])
                if compare != ast:
                    errata.append('Abstract syntax tree test "%s" for parser "%s" failed:'
                                  '\n\tExpr.:     %s\n\tExpected:  %s\n\tReceived:  %s'
                                  % (test_name, parser_name, '\n\t'.join(test_code.split('\n')),
                                     compact_sexpr(compare.as_sexpr()),
                                     compact_sexpr(ast.as_sexpr())))

        for test_name, test_code in tests.get('fail', dict()).items():
            cst = parser(test_code, parser_name)
            if not cst.error_flag:
                errata.append('Fail test "%s" for parser "%s" yields match instead of '
                              'expected failure!' % (test_name, parser_name))
    return errata


def runner(tests, namespace):
    """ Runs all or some selected tests from a test suite. To run all
    tests in a module, call ``runner("", globals())`` from within
    that module.

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
