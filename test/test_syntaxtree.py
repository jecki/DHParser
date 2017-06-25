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

import copy
import sys
sys.path.extend(['../', './'])

from DHParser.syntaxtree import Node, traverse, reduce_single_child, \
    replace_by_single_child, flatten, remove_expendables, TOKEN_PTYPE
from DHParser.testing import mock_syntax_tree
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.dsl import parser_factory


class TestNode:
    """
    Tests for class Node 
    """
    def setup(self):
        self.unique_nodes_sexpr = '(a (b c) (d e) (f (g h)))'
        self.unique_tree = mock_syntax_tree(self.unique_nodes_sexpr)
        self.recurring_nodes_sexpr = '(a (b x) (c (d e) (b y)))'
        self.recurr_tree = mock_syntax_tree(self.recurring_nodes_sexpr)

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

    def test_equality1(self):
        assert self.unique_tree == self.unique_tree
        assert self.recurr_tree != self.unique_tree
        assert mock_syntax_tree('(a (b c))') != mock_syntax_tree('(a (b d))')
        assert mock_syntax_tree('(a (b c))') == mock_syntax_tree('(a (b c))')

    def test_equality2(self):
        ebnf = 'term = term ("*"|"/") factor | factor\nfactor = /[0-9]+/~'
        att  = {"term": [replace_by_single_child, flatten],
                "factor": [remove_expendables, reduce_single_child],
                (TOKEN_PTYPE): [remove_expendables, reduce_single_child],
                "?": [remove_expendables, replace_by_single_child]}
        parser = parser_factory(ebnf)()
        tree = parser("20 / 4 * 3")
        traverse(tree, att)
        compare_tree = mock_syntax_tree("(term (term (factor 20) (:Token /) (factor 4)) (:Token *) (factor 3))")
        assert tree == compare_tree

    def test_copy(self):
        cpy = copy.deepcopy(self.unique_tree)
        assert cpy == self.unique_tree
        assert cpy.result[0].result != "epsilon" # just to make sure...
        cpy.result[0].result = "epsilon"
        assert cpy != self.unique_tree

    def test_copy2(self):
        # test if Node.__deepcopy__ goes sufficiently deep for ast-
        # transformation and compiling to perform correctly after copy
        ebnf = 'term = term ("*"|"/") factor | factor\nfactor = /[0-9]+/~'
        parser = get_ebnf_grammar()
        transform = get_ebnf_transformer()
        compiler = get_ebnf_compiler()
        tree = parser(ebnf)
        tree_copy = copy.deepcopy(tree)
        transform(tree_copy)
        res1 = compiler(tree_copy)
        t2 = copy.deepcopy(tree_copy)
        res2 = compiler(t2)
        assert res1 == res2
        tree_copy = copy.deepcopy(tree)
        transform(tree_copy)
        res3 = compiler(tree_copy)
        assert res3 == res2
        transform(tree)
        res4 = compiler(tree)
        assert res4 == res3

    def test_len_and_pos(self):
        """Test len-property of Node."""
        nd1 = Node(None, "123")
        assert nd1.len == 3, "Expected Node.len == 3, got %i" % nd1.len
        nd2 = Node(None, "456")
        assert nd2.len == 3, "Expected Node.len == 3, got %i" % nd1.len
        nd = Node(None, (nd1, nd2))
        assert nd.len == 6, "Expected Node.len == 6, got %i" % nd.len
        nd.pos = 0
        assert nd.pos == 0, "Expected Node.pos == 0, got %i" % nd.pos
        assert nd1.pos == 0, "Expected Node.pos == 0, got %i" % nd1.pos
        assert nd2.pos == 3, "Expected Node.pos == 3, got %i" % nd2.pos


class TestErrorHandling:
    def test_error_flag_propagation(self):
        tree = mock_syntax_tree('(a (b c) (d (e (f (g h)))))')

        def find_h(node):
            if node.result == "h":
                node.add_error("an error deep inside the syntax tree")

        assert not tree.error_flag
        traverse(tree, {"*": find_h})
        assert tree.error_flag


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
