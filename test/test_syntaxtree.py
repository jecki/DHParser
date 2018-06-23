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

from DHParser.syntaxtree import Node, RootNode, parse_sxpr, parse_xml, flatten_sxpr, flatten_xml, TOKEN_PTYPE
from DHParser.transform import traverse, reduce_single_child, \
    replace_by_single_child, flatten, remove_expendables
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.dsl import grammar_provider


class TestParseSxpression:
    def test_parse_s_expression(self):
        tree = parse_sxpr('(a (b c))')
        assert flatten_sxpr(tree.as_sxpr()) == '(a (b "c"))', flatten_sxpr(tree.as_sxpr())
        tree = parse_sxpr('(a i\nj\nk)')
        assert flatten_sxpr(tree.as_sxpr()) == '(a "i" "j" "k")', flatten_sxpr(tree.as_sxpr())
        try:
            tree = parse_sxpr('a b c')
            assert False, "parse_sxpr() should raise a ValueError " \
                          "if argument is not a tree!"
        except ValueError:
            pass

class TestParseXML:
    def test_roundtrip(self):
        tree = parse_sxpr('(a (b c) (d (e f) (h i)))')
        xml = tree.as_xml()
        fxml = flatten_xml(xml)
        assert fxml == '<a><b>c</b><d><e>f</e><h>i</h></d></a>'
        tree2 = parse_xml(fxml)
        assert fxml == flatten_xml(tree2.as_xml())

    def test_plaintext_handling(self):
        tree = parse_xml('<a>alpha <b>beta</b> gamma</a>')
        assert flatten_sxpr(tree.as_sxpr()) == \
               '(a (:PlainText "alpha ") (b "beta") (:PlainText " gamma"))'
        tree = parse_xml(' <a>   <b>beta</b>   </a> ')
        assert flatten_xml(tree.as_xml()) == '<a><b>beta</b></a>'


class TestNode:
    """
    Tests for class Node 
    """
    def setup(self):
        self.unique_nodes_sexpr = '(a (b c) (d e) (f (g h)))'
        self.unique_tree = parse_sxpr(self.unique_nodes_sexpr)
        self.recurring_nodes_sexpr = '(a (b x) (c (d e) (b y)))'
        self.recurr_tree = parse_sxpr(self.recurring_nodes_sexpr)

    def test_str(self):
        assert str(self.unique_tree) == "ceh"
        assert str(self.recurr_tree) == "xey"

    def test_select_subnodes(self):
        tags = [node.tag_name
                for node in self.unique_tree.select(lambda nd: True, include_root=True)]
        assert ''.join(tags) == "abdfg", ''.join(tags)

    def test_find(self):
        found = list(self.unique_tree.select(lambda nd: not nd.children and nd.result == "e"))
        assert len(found) == 1
        assert found[0].result == 'e'
        found = list(self.recurr_tree.select(lambda nd: nd.tag_name == 'b'))
        assert len(found) == 2
        assert found[0].result == 'x' and found[1].result == 'y'

    def test_equality1(self):
        assert self.unique_tree == self.unique_tree
        assert self.recurr_tree != self.unique_tree
        assert parse_sxpr('(a (b c))') != parse_sxpr('(a (b d))')
        assert parse_sxpr('(a (b c))') == parse_sxpr('(a (b c))')

    def test_equality2(self):
        ebnf = 'term = term ("*"|"/") factor | factor\nfactor = /[0-9]+/~'
        att  = {"term": [replace_by_single_child, flatten],
                "factor": [remove_expendables, reduce_single_child],
                (TOKEN_PTYPE): [remove_expendables, reduce_single_child],
                "?": [remove_expendables, replace_by_single_child]}
        parser = grammar_provider(ebnf)()
        tree = parser("20 / 4 * 3")
        traverse(tree, att)
        compare_tree = parse_sxpr("(term (term (factor 20) (:Token /) (factor 4)) (:Token *) (factor 3))")
        assert tree == compare_tree, tree.as_sxpr()

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
        assert len(nd1) == 3, "Expected Node.len == 3, got %i" % len(nd1)
        nd2 = Node(None, "456")
        assert len(nd2) == 3, "Expected Node.len == 3, got %i" % len(nd2)
        nd = Node(None, (nd1, nd2))
        assert len(nd) == 6, "Expected Node.len == 6, got %i" % len(nd)
        nd.init_pos(0)
        assert nd.pos == 0, "Expected Node.pos == 0, got %i" % nd.pos
        assert nd1.pos == 0, "Expected Node.pos == 0, got %i" % nd1.pos
        assert nd2.pos == 3, "Expected Node.pos == 3, got %i" % nd2.pos


class TestRootNode:
    def test_error_handling(self):
        tree = parse_sxpr('(A (B D) (C E))')
        tree.init_pos(0)
        root = RootNode()
        root.new_error(tree.children[1], "error C")
        root.new_error(tree.children[0], "error B")
        root.swallow(tree)
        assert root.error_flag
        errors = root.collect_errors()
        assert root.error_flag
        # assert errors == root.collect_errors(True)
        # assert not root.error_flag and not root.collect_errors()
        error_str = "\n".join(str(e) for e in errors)
        assert error_str.find("A") < error_str.find("B")


class TestNodeFind():
    """Test the select-functions of class Node.
    """

    def test_find(self):
        def match_tag_name(node, tag_name):
            return node.tag_name == tag_name
        matchf = lambda node: match_tag_name(node, "X")
        tree = parse_sxpr('(a (b X) (X (c d)) (e (X F)))')
        matches = list(tree.select(matchf))
        assert len(matches) == 2, len(matches)
        assert str(matches[0]) == 'd', str(matches[0])
        assert str(matches[1]) == 'F', str(matches[1])
        assert matches[0] == parse_sxpr('(X (c d))')
        assert matches[1] == parse_sxpr('(X F)')
        # check default: root is included in search:
        matchf2 = lambda node: match_tag_name(node, 'a')
        assert list(tree.select(matchf2, include_root=True))
        assert not list(tree.select(matchf2, include_root=False))

    def test_getitem(self):
        tree = parse_sxpr('(a (b X) (X (c d)) (e (X F)))')
        assert tree[0] == parse_sxpr('(b X)')
        assert tree[2] == parse_sxpr('(e (X F))')
        try:
            node = tree[3]
            assert False, "IndexError expected!"
        except IndexError:
            pass
        matches = list(tree.select_by_tag('X', False))
        assert matches[0] == parse_sxpr('(X (c d))')
        assert matches[1] == parse_sxpr('(X F)')

    def test_contains(self):
        tree = parse_sxpr('(a (b X) (X (c d)) (e (X F)))')
        assert 'a' not in tree
        assert any(tree.select_by_tag('a', True))
        assert not any(tree.select_by_tag('a', False))
        assert 'b' in tree
        assert 'X' in tree
        assert 'e' in tree
        assert 'c' not in tree
        assert any(tree.select_by_tag('c', False))


class TestSerialization:
    def test_sxpr_roundtrip(self):
        pass

    def test_sexpr_attributes(self):
        tree = parse_sxpr('(A "B")')
        tree.attributes['attr'] = "value"
        tree2 = parse_sxpr('(A `(attr "value") "B")')
        assert tree.as_sxpr() ==  tree2.as_sxpr()
        tree.attributes['attr2'] = "value2"
        tree3 = parse_sxpr('(A `(attr "value") `(attr2 "value2") "B")')
        assert tree.as_sxpr() == tree3.as_sxpr()

    def test_sexpr(self):
        tree = parse_sxpr('(A (B "C") (D "E"))')
        s = tree.as_sxpr()
        assert s == '(A\n  (B\n    "C"\n  )\n  (D\n    "E"\n  )\n)', s
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        s = tree.as_sxpr()
        assert s == '(A\n  (B\n    (C\n      "D"\n    )\n    (E\n      "F"\n    )' \
            '\n  )\n  (G\n    "H"\n  )\n)', s
        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        s = tree.as_sxpr()
        assert s == '(A\n  (B\n    (C\n      "D"\n      "X"\n    )' \
            '\n    (E\n      "F"\n    )\n  )\n  (G\n    " H "\n    " Y "\n  )\n)', s

    def test_compact_representation(self):
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        compact = tree.as_sxpr(compact=True)
        assert compact == 'A\n  B\n    C "D"\n    E "F"\n  G "H"', compact
        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        compact = tree.as_sxpr(compact=True)
        assert compact == 'A\n  B\n    C\n      "D"\n      "X"\n    E "F"' \
            '\n  G\n    " H "\n    " Y "', compact

    def test_xml_inlining(self):
        tree = parse_sxpr('(A (B "C") (D "E"))')

        xml = tree.as_xml(inline_tags={'A'})
        assert xml == "<A><B>C</B><D>E</D></A>", xml

        assert tree.as_xml() == "<A>\n  <B>C</B>\n  <D>E</D>\n</A>", xml

        tree.attributes['xml:space'] = 'preserve'
        xml = tree.as_xml()
        assert xml == '<A xml:space="preserve"><B>C</B><D>E</D></A>', xml

        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')

        xml = tree.as_xml(inline_tags={'B'})
        assert xml == "<A>\n  <B><C>D</C><E>F</E></B>\n  <G>H</G>\n</A>", xml
        xml = tree.as_xml(inline_tags={'A'})
        assert xml == "<A><B><C>D</C><E>F</E></B><G>H</G></A>", xml

        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        xml = tree.as_xml()
        assert xml == '<A>\n  <B>\n    <C>\n      D\n      X\n    </C>\n    ' \
            '<E>F</E>\n  </B>\n  <G>\n     H \n     Y \n  </G>\n</A>', xml
        xml = tree.as_xml(inline_tags={'A'})
        assert xml == '<A><B><C>D\nX</C><E>F</E></B><G> H \n Y </G></A>', xml

    # def test_xml2(self):
    #     tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
    #     print(tree.as_xml())
    #     print(tree.as_xml(inline_tags={'A'}))


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
