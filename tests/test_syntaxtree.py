#!/usr/bin/env python3

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
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import get_config_value, set_config_value, INDENTED_SERIALIZATION, \
    SXPRESSION_SERIALIZATION
from DHParser.syntaxtree import Node, RootNode, parse_sxpr, parse_xml, flatten_sxpr, \
    flatten_xml, parse_json_syntaxtree, ZOMBIE_TAG, EMPTY_NODE, ALL_NODES, next_context, \
    prev_context, serialize_context
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

    def test_parse_s_expression_w_attributes(self):
        s = '(A `(attr "1") (B "X"))'
        assert flatten_sxpr(parse_sxpr(s).as_sxpr()) == '(A `(attr "1") (B "X"))'
        s = """(BedeutungsPosition `(unterbedeutungstiefe "0")
                 (Bedeutung
                   (Beleg
                     (Quellenangabe (Quelle (Autor "LIUTPR.") (L " ") (Werk "leg.")) (L " ")
                       (BelegStelle (Stellenangabe (Stelle "21")) (L " ")
                         (BelegText (TEXT "...")))))))"""
        tree = parse_sxpr(s)
        assert str(tree) == "LIUTPR. leg. 21 ..."
        assert tree.attr['unterbedeutungstiefe'] == '0'


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
        assert flatten_sxpr(tree.as_sxpr()) == '(a (:Text "alpha ") (b "beta") (:Text " gamma"))'
        tree = parse_xml(' <a>  <b>beta</b>  </a> ')
        assert flatten_xml(tree.as_xml()) == \
               '<a><ANONYMOUS_Text__>  </ANONYMOUS_Text__><b>beta</b>' \
               '<ANONYMOUS_Text__>  </ANONYMOUS_Text__></a>'
        assert tree.as_xml(inline_tags={'a'}, omit_tags={':Text'}) == '<a>  <b>beta</b>  </a>'
        tree = parse_xml(' <a>\n  <b>beta</b>\n</a> ')
        assert tree.as_xml(inline_tags={'a'}) == '<a><b>beta</b></a>'

    def test_flatten_xml(self):
        tree = parse_xml('<alpha>\n  <beta>gamma</beta>\n</alpha>')
        flat_xml = flatten_xml(tree.as_xml())
        assert flat_xml == '<alpha><beta>gamma</beta></alpha>', flat_xml


class TestParseJSON:
    tree = parse_sxpr('(a (b ä) (d (e ö) (h über)))').with_pos(0)
    d = tree.pick('d')
    d.attr['name'] = "James Bond"
    d.attr['id'] = '007'

    def test_json_obj_roundtrip(self):
        json_obj_tree = self.tree.to_json_obj()
        tree_copy = Node.from_json_obj(json_obj_tree)
        # print(json_obj_tree)
        # print(json.dumps(json_obj_tree, ensure_ascii=False))
        # print(json.loads(json.dumps(json_obj_tree, ensure_ascii=False)))        
        assert tree_copy.equals(self.tree), '\n' + tree_copy.as_sxpr() + '\n' + self.tree.as_sxpr()

    def test_json_roundtrip(self):
        s = self.tree.as_json(indent=None, ensure_ascii=True)
        tree_copy = Node.from_json_obj(json.loads(s))
        assert tree_copy.equals(self.tree, ignore_attr_order = sys.version_info < (3, 6))
        s = self.tree.as_json(indent=2, ensure_ascii=False)
        tree_copy = Node.from_json_obj(json.loads(s))
        assert tree_copy.equals(self.tree, ignore_attr_order = sys.version_info < (3, 6))
        s = self.tree.as_json(indent=None, ensure_ascii=False)
        tree_copy = parse_json_syntaxtree(s)
        # print(s)
        # print(self.tree.as_sxpr())
        # print(tree_copy.as_sxpr())
        assert tree_copy.equals(self.tree)

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

    def test_with_pos(self):
        nd = Node('A', '123')
        nd._pos = 0
        n1 = Node('B', '')
        n2 = Node('C', '456')
        root = Node('root', (nd, n1, n2))
        root.with_pos(0)
        assert len(root) == root.children[-1].pos + len(root.children[-1])

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

    def test_repr(self):
        assert repr(Node('test1', 'content1')) == "Node('test1', 'content1')"
        assert repr(Node('test2', (Node('child1', 'content1'), Node('child2', 'content2')))) \
            == "Node('test2', (Node('child1', 'content1'), Node('child2', 'content2')))"

        test3 = Node('test', '').with_attr(attr='value')
        assert repr(test3) == "Node('test', '')"
        assert test3.repr == "Node('test', '').with_attr({'attr': 'value'})"

        test4 = Node('test', '').with_pos(0).with_attr(attr='value')
        assert repr(test4) == "Node('test', '')"
        assert test4.repr == "Node('test', '').with_attr({'attr': 'value'}).with_pos(0)"

    def test_select_subnodes(self):
        tags = [node.tag_name
                for node in self.unique_tree.select_if(lambda nd: True, include_root=True)]
        assert ''.join(tags) == "abdfg", ''.join(tags)

    def test_select_context(self):
        tree = parse_sxpr(self.unique_nodes_sexpr)
        contexts = []
        for ctx in tree.select_context_if(lambda ctx: ctx[-1].tag_name >= 'd',
                                          include_root=True, reverse=False):
            contexts.append(''.join(nd.tag_name for nd in ctx))
        assert contexts == ['ad', 'af', 'afg']
        contexts = []
        for ctx in tree.select_context_if(lambda ctx: ctx[-1].tag_name >= 'd',
                                          include_root=True, reverse=True):
            contexts.append(''.join(nd.tag_name for nd in ctx))
        assert contexts == ['af', 'afg', 'ad']

    def test_select_children(self):
        tree = parse_sxpr('(A (B 1) (C (X 1) (Y 1)) (B 2))')
        children = list(nd.tag_name for nd in tree.select_children(ALL_NODES))
        assert children == ['B', 'C', 'B']
        B_values = list(nd.content for nd in tree.select_children('B', reverse=True))
        assert B_values == ['2', '1']
        B_indices = tree.indices('B')
        assert B_indices == (0, 2)

    def test_single_child_selection(self):
        tree = parse_sxpr('(A (B 1) (C 1) (B 2))')
        assert 'B' in tree
        assert 'X' not in tree
        assert tree.pick_child('B').equals(Node('B', '1'))
        item_w_value_2 = lambda nd: nd.content == '2'
        assert item_w_value_2 in tree
        item_w_value_4 = lambda nd: nd.content == '4'
        assert item_w_value_4 not in tree
        assert tree[item_w_value_2].equals(Node('B', '2'))
        try:
            tree[item_w_value_4]
            assert False
        except KeyError:
            pass
        assert tree.get('B', EMPTY_NODE).equals(Node('B', '1'))
        assert tree.get(item_w_value_2, EMPTY_NODE).equals(Node('B', '2'))
        assert tree.get(item_w_value_4, EMPTY_NODE).equals(EMPTY_NODE)
        assert tree.index('C') == 1
        try:
            tree.index('X')
            assert False
        except ValueError:
            pass

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
        ebnf = '@literalws = right\nterm = term ("*"|"/") factor | factor\nfactor = /[0-9]+/~'
        att  = {"term": [remove_empty, remove_whitespace, replace_by_single_child, flatten],
                "factor": [remove_empty, remove_whitespace, reduce_single_child],
                "*": [remove_empty, remove_whitespace, replace_by_single_child]}
        parser = grammar_provider(ebnf)()
        tree = parser("20 / 4 * 3")
        traverse(tree, att)
        compare_tree = parse_sxpr("(term (term (factor 20) (:Text /) (factor 4)) (:Text *) (factor 3))")
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
        # right
        number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        result = str(Grammar(number)("3.1416"))
        assert result == "3.1416"
        # wrong
        number = RE(r'\d+') | RE(r'\d+') + RE(r'\.') + RE(r'\d+')
        result = str(Grammar(number)("3.1416"))
        assert result.startswith('3 <<< Error on ".1416" | Parser stopped before end!'), \
            str(result)

    def test_get_errors(self):
        # TODO: extend this test to the more compilcated case of removed nodes
        number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        result = Grammar(number)("3.1416")
        assert not result.get_errors(result.children[1])
        assert not result.get_errors(result)

        result = Grammar(number)("x.1416")
        assert result.get_errors(result[0])
        assert not result.get_errors(result)

        number = RE(r'\d+') | RE(r'\d+') + RE(r'\.') + RE(r'\d+')
        result = Grammar(number)("3.1416")
        assert not result.get_errors(result)
        assert result.get_errors(result[1])

    def test_copy_errors(self):
        tree = RootNode(parse_sxpr('(A (B "1") (C "2"))').with_pos(0))
        tree.add_error(tree['C'], Error('error', 1))
        tree.add_error(None, Error('unspecific error', 2))
        save = tree.as_sxpr()
        tree_copy = copy.deepcopy(tree)
        compare = tree_copy.as_sxpr()
        assert compare == save  # is the error message still included?

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
        compact = tree.as_sxpr(compact=True)
        assert compact == '(A\n  (B\n    (C "D")\n    (E "F"))\n  (G "H"))'
        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        compact = tree.as_sxpr(compact=True)
        assert compact == '(A\n  (B\n    (C\n      "D"\n      "X")\n    (E "F"))' \
            '\n  (G\n    " H "\n    " Y "))'
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        C = tree['B']['C']
        C.attr['attr'] = 'val'
        threshold = get_config_value('flatten_sxpr_threshold')
        set_config_value('flatten_sxpr_threshold', 20)
        compact = tree.serialize('indented')
        assert compact == 'A\n  B\n    C `(attr "val")\n      "D"\n    E\n      "F"\n  G\n    "H"'
        tree = parse_xml('<note><priority level="high" /><remark></remark></note>')
        assert tree.serialize(how=INDENTED_SERIALIZATION) == 'note\n  priority `(level "high")\n  remark'
        set_config_value('flatten_sxpr_threshold', threshold)

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

    def test_xml_tag_omission(self):
        tree = parse_sxpr('(XML (T "Hallo") (L " ") (T "Welt!"))')
        all_tags = {'XML', 'T', 'L'}
        assert tree.as_xml(inline_tags=all_tags, omit_tags=all_tags) == "Hallo Welt!"
        # tags with attributes will never be ommitted
        tree.pick_child('T').attr['class'] = "kursiv"
        assert tree.as_xml(inline_tags=all_tags, omit_tags=all_tags) == \
               '<T class="kursiv">Hallo</T> Welt!'


class TestSegementExtraction:
    def test_get_context(self):
        tree = parse_sxpr('(A (F (X "a") (Y "b")) (G "c"))')
        nd_X = tree.pick('X')
        ctx = tree.reconstruct_context(nd_X)
        assert [nd.tag_name for nd in ctx] == ['A', 'F', 'X']
        nd_F = tree.pick('F')
        nd_Y = tree.pick('Y')
        ctx = nd_F.reconstruct_context(nd_Y)
        assert [nd.tag_name for nd in ctx] == ['F', 'Y']
        ctx = tree.reconstruct_context(nd_F)
        assert [nd.tag_name for nd in ctx] == ['A', 'F']
        ctx = tree.reconstruct_context(nd_Y)
        assert [nd.tag_name for nd in ctx] == ['A', 'F', 'Y']
        nd_G = tree.pick('G')
        ctx = tree.reconstruct_context(nd_G)
        assert [nd.tag_name for nd in ctx] == ['A', 'G']
        not_there = Node('not_there', '')
        try:
            tree.reconstruct_context(not_there)
            assert False, "ValueError expected!"
        except ValueError:
            pass
        assert tree.reconstruct_context(tree) == [tree]

    def test_milestone_segment(self):
        tree = parse_sxpr('(root (left (A "a") (B "b") (C "c")) (middle "-") (right (X "x") (Y "y") (Z "z")))').with_pos(0)
        left = tree.pick('left')
        right = tree.pick('right')
        middle = tree.pick('middle')
        B = tree.pick('B')
        Y = tree.pick('Y')
        segment = tree.milestone_segment(B, Y)
        assert segment.content == "bc-xy"
        assert left != segment.pick('left')
        assert right != segment.pick('right')
        assert B == segment.pick('B')
        assert Y == segment.pick('Y')
        assert middle == segment.pick('middle')
        A = tree.pick('A')
        Z = tree.pick('Z')
        segment = tree.milestone_segment(A, Z)
        assert segment == tree
        assert segment.content == "abc-xyz"
        segment = tree.milestone_segment(A, middle)
        assert segment.equals(parse_sxpr('(root (left (A "a") (B "b") (C "c")) (middle "-"))'))
        assert segment.content == "abc-"
        assert segment != tree
        assert A == segment.pick('A')
        assert middle == segment.pick('middle')
        root = tree.milestone_segment(tree, tree)
        assert root == tree
        assert tree.milestone_segment(B, B) == B
        C = tree.pick('C')
        segment = tree.milestone_segment(B, C)
        assert segment.equals(parse_sxpr('(left (B "b") (C "c"))'))


class TestPositionAssignment:
    def test_position_assignment(self):
        tree = parse_sxpr('(A (B (C "D") (E "FF")) (G "HHH"))')
        # assignment of position values
        tree.with_pos(0)
        assert (tree.pos, tree['B'].pos, tree['B']['C'].pos,
                tree['B']['E'].pos, tree['G'].pos) == (0, 0, 0, 1, 3)
        # assignment of unassigned position values
        tree['G'].result = parse_sxpr('(_ (N "OOOO") (P "Q"))').children
        assert (tree['G']['N'].pos, tree['G']['P'].pos) == (3, 7)
        # no reassignment of position values
        # (because pos-values should always reflect source position)
        tree['G'].result = parse_sxpr('(_ (N "OOOO") (P "Q"))').with_pos(1).children
        assert (tree['G']['N'].pos, tree['G']['P'].pos) == (1, 5)


class TestContextNavigation:
    tree = parse_sxpr('(A (B 1) (C (D 2) (E 3)) (F 4))')

    def test_prev_context(self):
        ctx = self.tree.pick_context('D')
        c = prev_context(ctx)
        assert c[-1].tag_name == 'B'
        ctx = self.tree.pick_context('E')
        c = prev_context(ctx)
        assert c[-1].tag_name == 'D'
        ctx = self.tree.pick_context('F')
        c = prev_context(ctx)
        assert c[-1].tag_name == 'C'
        ctx = self.tree.pick_context('C')
        c = prev_context(ctx)
        assert c[-1].tag_name == 'B'

    def test_next_context(self):
        ctx = self.tree.pick_context('D')
        c = next_context(ctx)
        assert c[-1].tag_name == 'E'
        ctx = self.tree.pick_context('E')
        c = next_context(ctx)
        assert c[-1].tag_name == 'F'
        ctx = self.tree.pick_context('C')
        c = next_context(ctx)
        assert c[-1].tag_name == 'F'
        ctx = self.tree.pick_context('B')
        c = next_context(ctx)
        assert c[-1].tag_name == 'C'

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
