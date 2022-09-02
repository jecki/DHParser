#!/usr/bin/env python3

"""test_compile.py - unit tests for the compile-module of DHParser

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

import copy
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.nodetree import parse_sxpr, Node
from DHParser.compile import Compiler


class ZeroTestCompiler(Compiler):
    pass


class SerializingTestCompiler(Compiler):
    def serialize(self, node):
        if node.children:
            content = [self.compile(child) for child in node.children]
            return ' '.join(['(' + node.name] + content) + ')'
        else:
            return '(' + node.name + ' ' + node.content + ')'

    def on_A(self, node):
        return self.serialize(node)

    def on_B(self, node):
        return self.serialize(node)

    def on_C(self, node):
        return self.serialize(node)

    def on_D(self, node):
        return self.serialize(node)

    def on_E(self, node):
        return self.serialize(node)

    def on_F(self, node):
        return self.serialize(node)


class AttrTestCompiler(Compiler):
    def attr_tic(self, node, value):
        if node.children:
            node.result = node.children + (Node('tic', f' tic: {value}'),)
        else:
            node.result = node.content + f' tic: {value}'
        del node.attr['tic']


class WildcardTestCompiler(Compiler):
    def on_a(self, node):
        node = self.fallback_compiler(node)
        node.name = 'A'
        return node

    def wildcard(self, node):
        node = self.fallback_compiler(node)
        node.name = "x"
        return node


class TestCompilerClass:
    original = parse_sxpr('(A (B "1") (C (D (E "2") (F "3"))))')

    def test_zero_compiler(self):
        """Tests the fallback-method and boilerplate of the compiler."""
        tree = copy.deepcopy(self.original)
        compiler = ZeroTestCompiler()
        tree = compiler.compile(tree)
        assert tree.equals(self.original), tree.as_sxpr()

    def test_non_Node_return_type(self):
        """Tests a compiler that returns strings, not Nodes."""
        tree = copy.deepcopy(self.original)
        compiler = SerializingTestCompiler()
        s = compiler.compile(tree)
        assert s == "(A (B 1) (C (D (E 2) (F 3))))"

    def test_fallback_failure1(self):
        """Tests failure when leaf-node is mistakenly handled by fallback."""
        tree = copy.deepcopy(self.original)
        compiler = SerializingTestCompiler()
        compiler.on_F = compiler.fallback_compiler
        try:
            s = compiler.compile(tree)
            assert False, "TypeError expected"
        except TypeError:
            pass

    def test_fallback_failure2(self):
        """Tests failure when branch-node is mistakenly handled by fallback."""
        tree = copy.deepcopy(self.original)
        compiler = SerializingTestCompiler()
        compiler.on_D = compiler.fallback_compiler
        try:
            s = compiler.compile(tree)
            assert False, "TypeError expected"
        except TypeError as e:
            assert "DHParser.compile.Compiler.fallback_compiler()" in str(e), \
                "Incorrect Error Message: " + str(e)
            pass

    def test_attribute_visitory(self):
        attr_tree = parse_sxpr('(A (B `(tic "ticced :-)") "1") '
                               '(C `(tic "ticced :-(") (D (E "2") (F "3"))))')
        compiler = AttrTestCompiler()
        s = compiler.compile(attr_tree)
        assert str(s) == '1 tic: ticced :-)23 tic: ticced :-('

    def test_wildcard(self):
        tree = parse_sxpr('(a (b (a (c 1) (d 2)) (e 3)) (f 4))')
        comp = WildcardTestCompiler()
        tree = comp(tree)
        assert tree.as_sxpr() == '(A (x (A (x "1") (x "2")) (x "3")) (x "4"))'


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
