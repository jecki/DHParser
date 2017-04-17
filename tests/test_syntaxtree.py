#!/usr/bin/python3

"""test_syntaxtree.py - test of syntaxtree-module of DHParser 
                             

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2017 Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import re
import sys
sys.path.append(os.path.abspath('../../'))
from DHParser.toolkit import compact_sexpr
from DHParser.syntaxtree import Node, traverse


class DummyParser:
    def __init__(self, name=''):
        self.name = name

    def __str__(self):
        return self.name or self.__class__.__name__

    def __call__(self, text):
        return None, text


def from_sexpr(s):
    """Generates a tree of nodes from an S-expression.
    
    Example: 
    >>> from_sexpr("(a (b c))").as_sexpr()
    (a 
        (b 
            c 
        )
    )
    """
    def next_block(s):
        s = s.strip()
        while s[0] != ')':
            assert s[0] == '(', s
            level = 1;  i = 1
            while level > 0:
                if s[i] == '(':
                    level += 1
                elif s[i] == ')':
                    level -= 1
                i += 1
            yield s[:i]
            s = s[i:].strip()

    s = s.strip()
    assert s[0] == '(', s
    s = s[1:].strip()
    m = re.match('\w+', s)
    name = s[:m.end()]
    s = s[m.end():].strip()
    if s[0] == '(':
        result = tuple(from_sexpr(block) for block in next_block(s))
    else:
        m = re.match('\w+', s)
        result = s[:m.end()]
        s = s[m.end():].strip()
        assert s[0] == ')', s
    return Node(DummyParser(name), result)


class TestSExpr:
    """
    Tests for S-expression handling.
    """
    def test_compact_sexpr(self):
        assert compact_sexpr("(a\n    (b\n        c\n    )\n)\n") == "(a (b c))"

    def test_selftest_from_sexpr(self):
        sexpr = '(a (b c) (d e) (f (g h)))'
        tree = from_sexpr(sexpr)
        assert compact_sexpr(tree.as_sexpr(prettyprint=False)) == sexpr


class TestNode:
    """
    Tests for class Node 
    """
    def setup(self):
        self.unique_nodes_sexpr = '(a (b c) (d e) (f (g h)))'
        self.unique_tree = from_sexpr(self.unique_nodes_sexpr)
        self.recurring_nodes_sexpr = '(a (b x) (c (d e) (b y)))'
        self.recurr_tree = from_sexpr(self.recurring_nodes_sexpr)

    def test_str(self):
        assert str(self.unique_tree) == "ceh"
        assert str(self.recurr_tree) == "xey"

    def test_find(self):
        found = list(self.unique_tree.find(lambda nd: not nd.children and nd.result == "e"))
        assert len(found) == 1
        assert found[0].result == 'e'
        found = list(self.recurr_tree.find(lambda nd: nd.tag_name == 'b'))
        assert len(found) == 2
        assert found[0].result == 'x' and found[1].result == 'y'


class TestErrorHandling:
    def test_error_flag_propagation(self):
        tree = from_sexpr('(a (b c) (d (e (f (g h)))))')

        def find_h(node):
            if node.result == "h":
                node.add_error("an error deep inside the syntax tree")

        assert not tree.error_flag
        traverse(tree, {"*": find_h})
        assert tree.error_flag



if __name__ == "__main__":
    from run import run_tests

    run_tests("TestErrorHandling", globals())
