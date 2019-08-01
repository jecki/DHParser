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
import json
import sys
sys.path.extend(['../', './'])

from DHParser.syntaxtree import Node, RootNode, parse_sxpr, parse_xml, flatten_sxpr, \
    flatten_xml, parse_json_syntaxtree, ZOMBIE_TAG
from DHParser.transform import traverse, reduce_single_child, \
    replace_by_single_child, flatten, remove_empty, remove_whitespace
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.dsl import grammar_provider
from DHParser.error import Error
from DHParser.parse import RE, Grammar


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
               '(a (:Token "alpha ") (b "beta") (:Token " gamma"))'
        tree = parse_xml(' <a>  <b>beta</b>  </a> ')
        assert flatten_xml(tree.as_xml()) == '<a><:Token>  </:Token><b>beta</b><:Token>  </:Token></a>'
        assert tree.as_xml(inline_tags={'a'}, omit_tags={':Token'}) == '<a>  <b>beta</b>  </a>'
        tree = parse_xml(' <a>\n  <b>beta</b>\n</a> ')
        assert tree.as_xml(inline_tags={'a'}) == '<a><b>beta</b></a>'

    def test_flatten_xml(self):
        tree = parse_xml('<alpha>\n  <beta>gamma</beta>\n</alpha>')
        flat_xml = flatten_xml(tree.as_xml())
        assert flat_xml == '<alpha><beta>gamma</beta></alpha>', flat_xml


class TestParseJSON:
    def setup(self):
        self.tree = parse_sxpr('(a (b ä) (d (e ö) (h über)))').with_pos(0)
        d = self.tree.pick('d')
        d.attr['name'] = "James Bond"
        d.attr['id'] = '007'

    def test_json_obj_roundtrip(self):
        json_obj_tree = self.tree.to_json_obj()
        # print(json.dumps(json_obj_tree, ensure_ascii=False, indent=2))
        tree_copy = Node.from_json_obj(json_obj_tree)
        assert tree_copy.equals(self.tree), tree_copy.as_sxpr()

    def test_json_rountrip(self):
        s = self.tree.as_json(indent=None, ensure_ascii=True)
        tree_copy = Node.from_json_obj(json.loads(s))
        assert tree_copy.equals(self.tree)
        s = self.tree.as_json(indent=2, ensure_ascii=False)
        tree_copy = Node.from_json_obj(json.loads(s))

    def test_attr_serialization_and_parsing(self):
        n = Node('employee', 'James Bond').with_pos(46)
        n.attr['branch'] = 'Secret Service'
        n.attr['id'] = '007'
        # json
        json = n.as_json()
        tree = parse_json_syntaxtree(json)
        # print()

        # XML
        xml = n.as_xml()
        assert xml.find('_pos') < 0
        xml = n.as_xml('')
        assert xml.find('_pos') >= 0
        tree = parse_xml(xml)
        assert tree.pos == 46
        assert not '_pos' in tree.attr
        tree = parse_xml(xml, ignore_pos=True)
        assert '_pos' in tree.attr
        assert tree._pos < 0

        # S-Expression
        sxpr = n.as_sxpr()
        assert sxpr.find('pos') < 0
        sxpr = n.as_sxpr('')
        assert sxpr.find('pos') >= 0
        tree = parse_sxpr(sxpr)
        assert tree.pos == 46
        assert not 'pos' in tree.attr


class TestNode:
    """
    Tests for class Node 
    """
    def setup(self):
        self.unique_nodes_sexpr = '(a (b c) (d e) (f (g h)))'
        self.unique_tree = parse_sxpr(self.unique_nodes_sexpr)
        self.recurring_nodes_sexpr = '(a (b x) (c (d e) (b y)))'
        self.recurr_tree = parse_sxpr(self.recurring_nodes_sexpr)

    def test_content_property(self):
        tree = RootNode(parse_sxpr('(a (b c) (d e))'))
        content = tree.content
        b = tree.pick('b')
        d = tree.pick('d')
        b.result = "recently "
        d.result = "changed"
        assert content != tree.content
        assert content == 'ce'
        assert tree.content == 'recently changed'

    def test_pos_value_of_later_added_nodes(self):
        nd = Node('Test', '').with_pos(0)
        assert nd.pos == 0
        nd.result = (Node('A', 'aaa'), Node('B', 'bbb'))
        assert nd.children[0].pos == 0 and nd.children[1].pos == 3

    def test_deepcopy(self):
        tree = RootNode(parse_sxpr('(a (b c) (d (e f) (h i)))'))
        tree.with_pos(0)
        tree_copy = copy.deepcopy(tree)

        assert tree.equals(tree_copy)
        assert tree.as_sxpr() == parse_sxpr('(a (b c) (d (e f) (h i)))').as_sxpr()
        assert tree_copy.as_sxpr() == parse_sxpr('(a (b c) (d (e f) (h i)))').as_sxpr()

        tree.add_error(tree, Error('Test Error', 0))
        assert not tree_copy.errors
        assert tree.as_sxpr() != parse_sxpr('(a (b c) (d (e f) (h i)))').as_sxpr()
        assert tree_copy.as_sxpr() == parse_sxpr('(a (b c) (d (e f) (h i)))').as_sxpr()

        tree['d'].result = "x"
        assert not tree.equals(tree_copy)
        assert tree_copy.equals(parse_sxpr('(a (b c) (d (e f) (h i)))'))
        #print(tree.as_sxpr())
        #print(tree.attr)
        assert tree.equals(parse_sxpr('(a (b c) (d x))'))

        # this also checks for errors equality...
        assert parse_sxpr('(a (b c) (d x))').as_sxpr() != tree.as_sxpr()

    def test_str(self):
        assert str(self.unique_tree) == "ceh"
        assert str(self.recurr_tree) == "xey"

    def test_select_subnodes(self):
        tags = [node.tag_name
                for node in self.unique_tree.select_if(lambda nd: True, include_root=True)]
        assert ''.join(tags) == "abdfg", ''.join(tags)

    def test_find(self):
        found = list(self.unique_tree.select_if(lambda nd: not nd.children and nd.result == "e"))
        assert len(found) == 1
        assert found[0].result == 'e'
        found = list(self.recurr_tree.select_if(lambda nd: nd.tag_name == 'b'))
        assert len(found) == 2
        assert found[0].result == 'x' and found[1].result == 'y'

    def test_equality1(self):
        assert self.unique_tree.equals(self.unique_tree)
        assert not self.recurr_tree.equals(self.unique_tree)
        assert not parse_sxpr('(a (b c))').equals(parse_sxpr('(a (b d))'))
        assert parse_sxpr('(a (b c))').equals(parse_sxpr('(a (b c))'))

    def test_equality2(self):
        ebnf = 'term = term ("*"|"/") factor | factor\nfactor = /[0-9]+/~'
        att  = {"term": [remove_empty, remove_whitespace, replace_by_single_child, flatten],
                "factor": [remove_empty, remove_whitespace, reduce_single_child],
                "*": [remove_empty, remove_whitespace, replace_by_single_child]}
        parser = grammar_provider(ebnf)()
        tree = parser("20 / 4 * 3")
        traverse(tree, att)
        compare_tree = parse_sxpr("(term (term (factor 20) (:Token /) (factor 4)) (:Token *) (factor 3))")
        assert tree.equals(compare_tree), tree.as_sxpr()

    def test_copy(self):
        cpy = copy.deepcopy(self.unique_tree)
        assert cpy.equals(self.unique_tree)
        assert cpy.result[0].result != "epsilon" # just to make sure...
        cpy.result[0].result = "epsilon"
        assert not cpy.equals(self.unique_tree)

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
        diff = ''.join([a for a, b in zip(res1, res2) if a != b])
        assert diff.isnumeric()  # differences should only be ID-Numbers
        tree_copy = copy.deepcopy(tree)
        transform(tree_copy)
        res3 = compiler(tree_copy)
        diff = ''.join([a for a, b in zip(res2, res3) if a != b])
        assert diff.isnumeric()  # differences should only be ID-Numbers
        transform(tree)
        res4 = compiler(tree)
        diff = ''.join([a for a, b in zip(res3, res4) if a != b])
        assert diff.isnumeric()  # differences should only be ID-Numbers

    def test_len_and_pos(self):
        """Test len-property of Node."""
        nd1 = Node(ZOMBIE_TAG, "123")
        assert len(nd1) == 3, "Expected Node.len == 3, got %i" % len(nd1)
        nd2 = Node(ZOMBIE_TAG, "456")
        assert len(nd2) == 3, "Expected Node.len == 3, got %i" % len(nd2)
        nd = Node(ZOMBIE_TAG, (nd1, nd2))
        assert len(nd) == 6, "Expected Node.len == 6, got %i" % len(nd)
        nd.with_pos(0)
        assert nd.pos == 0, "Expected Node.pos == 0, got %i" % nd.pos
        assert nd1.pos == 0, "Expected Node.pos == 0, got %i" % nd1.pos
        assert nd2.pos == 3, "Expected Node.pos == 3, got %i" % nd2.pos

    def test_xml_sanitizer(self):
        node = Node('tag', '<&>')
        assert node.as_xml() == '<tag>&lt;&amp;&gt;</tag>'


class TestRootNode:
    def test_error_handling(self):
        tree = parse_sxpr('(A (B D) (C E))')
        tree.with_pos(0)
        root = RootNode()
        root.new_error(tree.children[1], "error C")
        root.new_error(tree.children[0], "error B")
        root.swallow(tree)
        assert root.error_flag
        errors = root.errors_sorted
        assert root.error_flag
        # assert errors == root.errors(True)
        # assert not root.error_flag and not root.errors()
        error_str = "\n".join(str(e) for e in errors)
        assert error_str.find("A") < error_str.find("B")

    def test_error_reporting(self):
        number = RE(r'\d+') | RE(r'\d+') + RE(r'\.') + RE(r'\d+')
        result = str(Grammar(number)("3.1416"))
        assert result == '3 <<< Error on ".141" | Parser stopped before end! trying to recover... >>> ', \
            str(result)


class TestNodeFind:
    """Test the item-access-functions of class Node.
    """

    def test_find(self):
        def match_tag_name(node, tag_name):
            return node.tag_name == tag_name
        matchf = lambda node: match_tag_name(node, "X")
        tree = parse_sxpr('(a (b X) (X (c d)) (e (X F)))')
        matches = list(tree.select_if(matchf))
        assert len(matches) == 2, len(matches)
        assert str(matches[0]) == 'd', str(matches[0])
        assert str(matches[1]) == 'F', str(matches[1])
        assert matches[0].equals(parse_sxpr('(X (c d))'))
        assert matches[1].equals(parse_sxpr('(X F)'))
        # check default: root is included in search:
        matchf2 = lambda node: match_tag_name(node, 'a')
        assert list(tree.select_if(matchf2, include_root=True))
        assert not list(tree.select_if(matchf2, include_root=False))

    def test_getitem(self):
        tree = parse_sxpr('(a (b X) (X (c d)) (e (X F)))')
        assert tree[0].equals(parse_sxpr('(b X)'))
        assert tree[2].equals(parse_sxpr('(e (X F))'))
        assert tree[-1].equals(parse_sxpr('(e (X F))'))
        try:
            node = tree[3]
            assert False, "IndexError expected!"
        except IndexError:
            pass
        matches = list(tree.select('X', False))
        assert matches[0].equals(parse_sxpr('(X (c d))'))
        assert matches[1].equals(parse_sxpr('(X F)'))

    def test_contains(self):
        tree = parse_sxpr('(a (b X) (X (c d)) (e (X F)))')
        assert 'a' not in tree
        assert any(tree.select('a', True))
        assert not any(tree.select('a', False))
        assert 'b' in tree
        assert 'X' in tree
        assert 'e' in tree
        assert 'c' not in tree
        assert any(tree.select('c', False))

    def test_index(self):
        tree = parse_sxpr('(a (b 0) (c 1) (d 2))')
        assert tree.index('d') == 2
        assert tree.index('b') == 0
        assert tree.index('c') == 1
        try:
            i = tree.index('x')
            raise AssertionError('ValueError expected!')
        except ValueError:
            pass


class TestSerialization:
    def test_sxpr_roundtrip(self):
        sxpr = ('(BelegText (Anker "interdico_1") (BelegLemma "inter.|ticente") (TEXT ", (") '
                '(Anker "interdico_2") (BelegLemma "inter.|titente") (L " ") (Zusatz "var. l.") '
                '(TEXT ") Deo."))')
        tree = parse_sxpr(sxpr)
        assert flatten_sxpr(tree.as_sxpr()) == sxpr


    def test_sexpr_attributes(self):
        tree = parse_sxpr('(A "B")')
        tree.attr['attr'] = "value"
        tree2 = parse_sxpr('(A `(attr "value") "B")')
        assert tree.as_sxpr() ==  tree2.as_sxpr()
        tree.attr['attr2'] = "value2"
        tree3 = parse_sxpr('(A `(attr "value") `(attr2 "value2") "B")')
        assert tree.as_sxpr() == tree3.as_sxpr()

    def test_sexpr(self):
        tree = parse_sxpr('(A (B "C") (D "E"))')
        s = tree.as_sxpr(flatten_threshold=0)
        assert s == '(A\n  (B\n    "C"\n  )\n  (D\n    "E"\n  )\n)', s
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        s = tree.as_sxpr(flatten_threshold=0)
        assert s == '(A\n  (B\n    (C\n      "D"\n    )\n    (E\n      "F"\n    )' \
            '\n  )\n  (G\n    "H"\n  )\n)', s
        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        s = tree.as_sxpr(flatten_threshold=0)
        assert s == '(A\n  (B\n    (C\n      "D"\n      "X"\n    )' \
            '\n    (E\n      "F"\n    )\n  )\n  (G\n    " H "\n    " Y "\n  )\n)', s

    def test_compact_representation(self):
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        compact = tree.as_sxpr(compact=True, )
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

        tree.attr['xml:space'] = 'preserve'
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
