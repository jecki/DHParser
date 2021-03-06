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

from DHParser.syntaxtree import parse_sxpr
from DHParser.compile import Compiler


class ZeroTestCompiler(Compiler):
    pass


class SerializingTestCompiler(Compiler):
    def serialize(self, node):
        if node.children:
            content = [self.compile(child) for child in node.children]
            return ' '.join(['(' + node.tag_name] + content) + ')'
        else:
            return '(' + node.tag_name + ' ' + node.content + ')'

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


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
