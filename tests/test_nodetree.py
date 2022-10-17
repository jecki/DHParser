#!/usr/bin/env python3

"""test_nodetree.py - test of nodetree-module of DHParser

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

from DHParser.configuration import get_config_value, set_config_value
from DHParser.nodetree import Node, RootNode, parse_sxpr, parse_xml, flatten_sxpr, \
    flatten_xml, parse_json, ZOMBIE_TAG, EMPTY_NODE, ANY_NODE, next_path, \
    prev_path, pick_from_path, pp_path, ContentMapping, leaf_paths, NO_PATH, \
    select_path_if, select_path, create_path_match_function, pick_path, \
    LEAF_PATH, TOKEN_PTYPE, insert_node, content_of, strlen_of, gen_chain_ID
from DHParser.preprocess import gen_neutral_srcmap_func
from DHParser.transform import traverse, reduce_single_child, \
    replace_by_single_child, flatten, remove_empty, remove_whitespace
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.error import ERROR
from DHParser.dsl import grammar_provider, create_parser
from DHParser.error import Error
from DHParser.parse import RE, Grammar
from DHParser.toolkit import re


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
        try:
            tree = parse_sxpr('(a (b c)))')
            assert False, "parse_sxpr() should raise a ValueError for too many matching brackets."
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

    def test_parse_s_expression_grinder(self):
        sxpr = '(B (A "abc :-)") (C "1"))'
        s = parse_sxpr(sxpr)
        assert flatten_sxpr(s.as_sxpr()) == sxpr
        sxpr = '(B (A `(tic "abc :-)") "Z") (C "1"))'
        s = parse_sxpr(sxpr)
        assert flatten_sxpr(s.as_sxpr()) == sxpr

    def test_parse_s_expression_malformed(self):
        try:
            s = parse_sxpr('(A (B 1) (C (D (E 2) (F 3)) (G 4) (H (I 5) (J 6)) (K 7)')
            assert False, "ValueError exptected!"
        except ValueError:
            pass

    def test_endlessloop_error(self):
        tree = parse_sxpr(r'(LINEFEED "\\")')
        assert tree

    def test_flatten_sxpr(self):
        tree = parse_sxpr('(a (b "  ") (d (e f) (h i)))')
        sxpr = tree.as_sxpr()
        flat = flatten_sxpr(sxpr)
        assert flat == '(a (b "  ") (d (e "f") (h "i")))'

    def test_sxpression_w_error(self):
        tree = RootNode(Node('u', 'XXX').with_pos(0))
        tree.new_error(tree, 'Fehler, "mein Herr"!', ERROR)
        assert tree.equals(parse_sxpr('(u "XXX")'))
        sxpr = tree.as_sxpr()
        assert sxpr == r'''(u `(err "Error (1000): Fehler, \"mein Herr\"!") "XXX")''', sxpr
        tree2 = parse_sxpr(sxpr)
        assert tree2.as_sxpr() == r'''(u `(err "Error (1000): Fehler, \"mein Herr\"!") "XXX")'''
        # When backparsing s-expression-serialized trees, errors are parsed as attributes
        # but not turned into errors in the error-list of the root-node again:
        assert not tree2.equals(tree)
        assert not tree.has_attr()
        assert tree2.attr['err'] == r'''Error (1000): Fehler, \"mein Herr\"!'''
        assert not tree2.errors

XML_EXAMPLE = '''<?xml version="1.0" encoding="UTF-8"?>
<note date="2018-06-14">
  <to>Tove</to>
  <from>Jani</from>
  <heading>Reminder</heading>
  <body> Don't forget me this weekend! </body>
  <priority level="high"/>
  Some Mixed Content...
</note>'''

XML_EXAMPLE_2 = '''<TEI xmlns:abb="http://www.abbyy.com/FineReader_xml/FineReader10-schema-v1.xml" xmlns:tei="http://www.tei-c.org/ns/1.0" xmlns:mwg="http://mwg-digital.badw.de">
  <teiHeader>
    <!--<fileDesc>
      <titleStmt>
        <title>Die römische Agrargeschichte in ihrer Bedeutung für das Staats- und Privatrecht
          (digitale Edition)</title>
        <author>Max Weber</author>
        <editor>Jürgen Deininger</editor>
        <editor>Bayerische Akademie der Wissenschaften; wissenschaftliche Betreuung: Edith Hanke
          (für die digitale Edition)</editor>
      </titleStmt>
      <editionStmt>
        <edition>
          <date>2021-12-01</date>
        </edition>
      </editionStmt>
      <publicationStmt>
        <p/>
      </publicationStmt>
      <sourceDesc>
        <p/>
      </sourceDesc>
    </fileDesc>
    <encodingDesc>
      <p>TEI-XML, UTF-8</p>
    </encodingDesc>
    <revisionDesc>
      <listChange>
        <change>
          <date>2021-12-01</date>
          <name>BAdW</name>
        </change>
      </listChange>
    </revisionDesc>-->
  </teiHeader>
</TEI>'''

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
        assert flatten_xml(tree.as_xml(string_tags=set())) == \
               '<a><ANONYMOUS_Text__>  </ANONYMOUS_Text__><b>beta</b>' \
               '<ANONYMOUS_Text__>  </ANONYMOUS_Text__></a>'
        assert tree.as_xml(inline_tags={'a'}, string_tags={':Text'}) == '<a>  <b>beta</b>  </a>'
        tree = parse_xml(' <a>\n  <b>beta</b>\n</a> ')
        assert tree.as_xml(inline_tags={'a'}) == '<a><b>beta</b></a>'

    def test_flatten_xml(self):
        tree = parse_xml('<alpha>\n  <beta>gamma</beta>\n</alpha>')
        flat_xml = flatten_xml(tree.as_xml())
        assert flat_xml == '<alpha><beta>gamma</beta></alpha>', flat_xml

    def test_endlessloop_error(self):
        tree = parse_xml(r'<LINEFEED>\\</LINEFEED>')
        assert tree

    def test_tag_name_mismatch(self):
        try:
            _ = parse_xml('<xml><a>xxx</b></xml>', strict_mode=True)
            assert False, "ValueError because of tag-mismatch expected!"
        except ValueError as e:
            assert str(e).find('1:6 - 1:16') >= 0
        # This will still print an error message!
        _ = parse_xml('<xml><a>xxx</b></xml>', strict_mode=False)

    def test_non_empty_empty_tags(self):
        try:
            _ = parse_xml('<xml><a/><a>content</a></xml>', strict_mode=True)
        except ValueError as e:
            assert str(e).find('1:10') >= 0
        try:
            _ = parse_xml('<xml><a>content</a><a/></xml>', strict_mode=True)
        except ValueError as e:
            assert str(e).find('1:20') >= 0
        _ = parse_xml('<xml><a/><a>content</a></xml>', strict_mode=False)
        _ = parse_xml('<xml><a>content</a><a/></xml>', strict_mode=False)

    def test_PI_and_DTD(self):
        """PIs <?...> and DTDs <!...> and the like should politely be overlooked."""
        testdata = """<!DOCTYPE nonsense>
            <?xpacket begin='' id='W5M0MpCehiHzreSzNTczkc9d'?> 
            <?xpacket begin="r" id="Arnold-Mueller2017a"?> 
            <x:xmpmeta xmlns:x="adobe:ns:meta/"> 
            <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"> 
            <rdf:Description xmlns:bibtex="http://jabref.sourceforge.net/bibteXMP/" 
            bibtex:bibtexkey="Arnold-Mueller2017a" 
            bibtex:journal="Informationspraxis" 
            bibtex:title="Wie permanent sind Permalinks?" 
            bibtex:type="Article" 
            bibtex:doi="http://dx.doi.org/10.11588/ip.2016.2.33483" 
            bibtex:year="2017" 
            bibtex:volume="3" 
            bibtex:issue="1" 
            bibtex:url="http://www.eckhartarnold.de/papers/2016_Permalinks/Arnold_Mueller_2016_Permalinks.html"> 
            <bibtex:author>Eckhart Arnold</bibtex:author> 
            </rdf:Description> 
            <!-- comment -->
            </rdf:RDF> 
            </x:xmpmeta> 
            <?xpacket end="r"?> 
            <?xpacket end='r'?>"""
        tree = parse_xml(testdata)
        assert tree.name == 'x:xmpmeta'
        author = tree.pick('bibtex:author')
        assert author and author.content == "Eckhart Arnold"
        description = tree.pick('rdf:Description')
        assert description.has_attr('bibtex:title')

    def test_comments(self):
        tree = parse_xml('<xml><!-- comment --></xml>')
        assert tree.as_sxpr() == '(xml)'
        tree = parse_xml(XML_EXAMPLE_2)
        assert True  # yeah, no endless loop!

    def test_serialize_xml(self):
        root = RootNode(parse_xml(XML_EXAMPLE))
        root.string_tags.update({':Text'})
        root.empty_tags.update({'priority'})
        assert root.as_xml() == XML_EXAMPLE[XML_EXAMPLE.find('\n') + 1:]



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
        tree_copy = parse_json(s)
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
        tree = parse_json(json)
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

    def test_attr_error_reporting_and_fixing(self):
        n = Node('tag', 'content').with_attr(faulty='<&"')
        set_config_value('xml_attribute_error_handling', 'fail')
        try:
            s = n.as_xml()
            assert False, "ValueError expected"
        except ValueError:
            pass
        set_config_value('xml_attribute_error_handling', 'fix')
        assert n.as_xml() == '''<tag faulty='&lt;&amp;"'>content</tag>''', n.as_xml()
        set_config_value('xml_attribute_error_handling', 'ignore')
        assert n.as_xml() == '''<tag faulty='<&"'>content</tag>'''
        n.attr['nonascii'] = 'ἱεραρχικωτάτου'
        set_config_value('xml_attribute_error_handling', 'lxml')
        assert n.as_xml() == '''<tag faulty='&lt;&amp;"' nonascii="??????????????">content</tag>'''


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
        assert root.strlen() == root.children[-1].pos + root.children[-1].strlen()

    def test_deepcopy(self):
        tree = RootNode(parse_sxpr('(a (b c) (d (e f) (h i)))'), "cfi", gen_neutral_srcmap_func("cfi"))
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
        assert tree.equals(parse_sxpr('(a (b c) (d x))'))

        # this also checks for errors equality...
        assert parse_sxpr('(a (b c) (d x))').as_sxpr() != tree.as_sxpr()
        tree_copy = copy.deepcopy(tree)
        assert tree.source == tree_copy.source
        assert tree.source_mapping == tree_copy.source_mapping
        assert tree.lbreaks == tree_copy.lbreaks
        assert tree.errors == tree_copy.errors


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
        tags = [node.name
                for node in self.unique_tree.select_if(lambda nd: True, include_root=True)]
        assert ''.join(tags) == "abdfg", ''.join(tags)
        tags = [node.name
                for node in self.unique_tree.select(ANY_NODE, include_root=True, skip_subtree='f')]
        assert ''.join(tags) == "abdf", ''.join(tags)

    def test_tree_select_path_if(self):
        tree = parse_sxpr(self.unique_nodes_sexpr)
        contexts = []
        for ctx in tree.select_path_if(lambda ctx: ctx[-1].name >= 'd',
                                       include_root=True, reverse=False):
            contexts.append(''.join(nd.name for nd in ctx))
        assert contexts == ['ad', 'af', 'afg']
        contexts = []
        for ctx in tree.select_path_if(lambda ctx: ctx[-1].name >= 'd',
                                       include_root=True, reverse=True):
            contexts.append(''.join(nd.name for nd in ctx))
        assert contexts == ['af', 'afg', 'ad']

    def test_select_path_with_skipping(self):
        tree = parse_sxpr('(a (b c) (d e) (f (g h)))')
        check = []
        contexts = []
        def select_f(ctx):
            nonlocal check
            check.append(''.join(nd.name for nd in ctx))
            return True
        for ctx in tree.select_path(select_f, include_root=True):
            contexts.append(''.join(nd.name for nd in ctx))
        assert check == contexts == ['a', 'ab', 'ad', 'af', 'afg']
        check = []
        contexts = []
        for ctx in tree.select_path(select_f, include_root=True, skip_subtree='f'):
            contexts.append(''.join(nd.name for nd in ctx))
        assert check == contexts == ['a', 'ab', 'ad', 'af']

    def test_tree_select_path(self):
        tree = parse_sxpr('(A (B 1) (C (X 1) (Y 1)) (B 2))')
        l = [str(nd) for nd in tree.select('B')]
        assert ''.join(l) == '12'
        l = [str(ctx[-1]) for ctx in tree.select_path('B')]
        assert ''.join(l) == '12'

    def test_select_children(self):
        tree = parse_sxpr('(A (B 1) (C (X 1) (Y 1)) (B 2))')
        children = list(nd.name for nd in tree.select_children(ANY_NODE))
        assert children == ['B', 'C', 'B']
        B_values = list(nd.content for nd in tree.select_children('B', reverse=True))
        assert B_values == ['2', '1']
        B_indices = tree.indices('B')
        assert B_indices == (0, 2)

    def test_del_children(self):
        tree = parse_sxpr('(A (B 1) (C 2) (D 3) (E 4) (F 5) (G 6))')
        del tree[2:6:2]
        assert tree.as_sxpr() == '(A (B "1") (C "2") (E "4") (G "6"))'

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
            _ = tree[item_w_value_4]
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
        found = list(self.recurr_tree.select_if(lambda nd: nd.name == 'b'))
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
        assert not diff or diff.isnumeric()  # differences should at most be ID-Numbers
        tree_copy = copy.deepcopy(tree)
        transform(tree_copy)
        res3 = compiler(tree_copy)
        diff = ''.join([a for a, b in zip(res2, res3) if a != b])
        assert not diff or diff.isnumeric()  # differences should only be ID-Numbers
        transform(tree)
        res4 = compiler(tree)
        diff = ''.join([a for a, b in zip(res3, res4) if a != b])
        assert not diff or diff.isnumeric()  # differences should only be ID-Numbers

    def test_len_and_pos(self):
        """Test len-property of Node."""
        nd1 = Node(ZOMBIE_TAG, "123")
        assert nd1.strlen() == 3, "Expected Node.len == 3, got %i" % len(nd1)
        nd2 = Node(ZOMBIE_TAG, "456")
        assert nd2.strlen() == 3, "Expected Node.len == 3, got %i" % len(nd2)
        nd = Node(ZOMBIE_TAG, (nd1, nd2))
        assert nd.strlen() == 6, "Expected Node.len == 6, got %i" % len(nd)
        nd.with_pos(0)
        assert nd.pos == 0, "Expected Node.pos == 0, got %i" % nd.pos
        assert nd1.pos == 0, "Expected Node.pos == 0, got %i" % nd1.pos
        assert nd2.pos == 3, "Expected Node.pos == 3, got %i" % nd2.pos

    def test_xml_sanitizer(self):
        node = Node('tag', '<&>')
        assert node.as_xml() == '<tag>&lt;&amp;&gt;</tag>'

    def test_insert_remove(self):
        node = parse_sxpr('(R (A "1") (B "2") (C "3"))')
        B = node.pick('B')
        node.remove(B)
        assert node.as_sxpr() == '(R (A "1") (C "3"))'
        node.insert(0, B)
        assert node.as_sxpr() == '(R (B "2") (A "1") (C "3"))'

    def test_as_etree(self):
        import xml.etree.ElementTree as ET
        # import lxml.etree as ET
        sxpr = '(R (A "1") (S (B `(class "bold") "2")) (C "3"))'
        xml = '<R><A>1</A><S><B class="bold">2</B></S><C>3</C></R>'
        node = parse_sxpr(sxpr)
        et = node.as_etree()
        assert ET.tostring(et, encoding="unicode") == xml, ET.tostring(et, encoding="unicode")
        node = Node.from_etree(et)
        assert node.as_sxpr() == sxpr
        et = ET.XML('<R>mixed <A>1</A>mode <!-- comment --><B class="italic" /></R>')
        node = Node.from_etree(et)
        expected_sxpr = '(R (:Text "mixed ") (A "1") (:Text "mode ") (B `(class "italic")))'
        assert node.as_sxpr() == expected_sxpr
        et = node.as_etree()
        et = ET.XML(ET.tostring(et, encoding="unicode"))
        node = Node.from_etree(et)
        assert node.as_sxpr() == expected_sxpr
        empty_tags = set()
        tree = parse_xml('<a><b>1<c>2<d />3</c></b>4</a>', out_empty_tags=empty_tags)
        etree = tree.as_etree(empty_tags=empty_tags)
        assert ET.tostring(etree).replace(b' /', b'/') == b'<a><b>1<c>2<d/>3</c></b>4</a>'
        tree = Node.from_etree(etree)
        assert flatten_sxpr(tree.as_sxpr()) == \
               '(a (b (:Text "1") (c (:Text "2") (d) (:Text "3"))) (:Text "4"))'

    def test_delete_item(self):
        sxpr = '(root (A "0") (B "1") (C "2") (D "3"))'
        node = parse_sxpr(sxpr)
        try:
            _ = node.index('E')
            assert False, 'ValueError expected'
        except ValueError:
            pass
        assert node[-1].name == "D"
        try:
            del node[4]
            assert False, 'IndexError expected'
        except IndexError:
            pass
        try:
            del node[-5]
            assert False, 'IndexError expected'
        except IndexError:
            pass
        del node[-2]
        assert 'C' not in node
        del node[0]
        assert 'A' not in node
        sxpr = '(root (A "0") (B "1") (C "2") (D "3"))'
        node = parse_sxpr(sxpr)
        del node[1:3]
        assert str(node) == "03"

    def test_setitem(self):
        sxpr = '(root (A "0") (B "1") (C "2") (D "3"))'
        node = parse_sxpr(sxpr)
        assert node['B'].content == '1'
        node['B'] = Node('X', '-1')
        assert flatten_sxpr(node.as_sxpr()) == '(root (A "0") (X "-1") (C "2") (D "3"))'
        node[2] = Node('Y', '-2')
        assert flatten_sxpr(node.as_sxpr()) == '(root (A "0") (X "-1") (Y "-2") (D "3"))'
        subst = [Node('Z', '-7')]
        node[1:3] = subst
        assert flatten_sxpr(node.as_sxpr()) == '(root (A "0") (Z "-7") (D "3"))'


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
        assert result.startswith('3 <<< Error on ".1416" | Parser "root" stopped before end'), \
            str(result)

    def test_get_errors(self):
        # TODO: extend this test to the more complicated case of removed nodes
        number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        result = Grammar(number)("3.1416")
        assert not result.node_errors(result.children[1])
        assert not result.node_errors(result)

        result = Grammar(number)("x.1416")
        assert result.node_errors(result[0])
        assert not result.node_errors(result)

        number = RE(r'\d+') | RE(r'\d+') + RE(r'\.') + RE(r'\d+')
        result = Grammar(number)("3.1416")
        assert not result.node_errors(result)
        assert result.node_errors(result[1])

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
            return node.name == tag_name
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
        s = tree.as_sxpr(compact=False, flatten_threshold=0)
        assert s == '(A\n  (B\n    "C"\n  )\n  (D\n    "E"\n  )\n)', s
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        s = tree.as_sxpr(compact=False, flatten_threshold=0)
        assert s == '(A\n  (B\n    (C\n      "D"\n    )\n    (E\n      "F"\n    )' \
            '\n  )\n  (G\n    "H"\n  )\n)'
        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        s = tree.as_sxpr(compact=False, flatten_threshold=0)
        assert s == '(A\n  (B\n    (C\n      "D"\n      "X"\n    )' \
            '\n    (E\n      "F"\n    )\n  )\n  (G\n    " H "\n    " Y "\n  )\n)', s

    def test_compact_representation(self):
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        compact = tree.as_sxpr(compact=True, flatten_threshold=0)
        assert compact == '(A\n  (B\n    (C "D")\n    (E "F"))\n  (G "H"))'
        tree = parse_sxpr('(A (B (C "D\nX") (E "F")) (G " H \n Y "))')
        compact = tree.as_sxpr(compact=True, flatten_threshold=0)
        assert compact == '(A\n  (B\n    (C\n      "D"\n      "X")\n    (E "F"))' \
            '\n  (G\n    " H "\n    " Y "))'
        tree = parse_sxpr('(A (B (C "D") (E "F")) (G "H"))')
        C = tree['B']['C']
        C.attr['attr'] = 'val'
        threshold = get_config_value('flatten_sxpr_threshold')
        set_config_value('flatten_sxpr_threshold', 20)
        compact = tree.serialize('indented')
        assert compact == 'A\n  B\n    C `attr "val" "D"\n    E "F"\n  G "H"', compact
        tree = parse_xml('<note><priority level="high" /><remark></remark></note>')
        assert tree.serialize(how='indented') == 'note\n  priority `level "high"\n  remark'
        set_config_value('flatten_sxpr_threshold', threshold)

    def test_tree_representation(self):
        tree = parse_sxpr('(alpha `(class "red") `(style "thin") '
                          '    (beta "eins\nzwei\ndrei") '
                          '    (gamma `(class "blue") "vier"))')
        assert tree.as_tree() == ('alpha `class "red" `style "thin"\n'
                                  '  beta\n'
                                  '    "eins"\n'
                                  '    "zwei"\n'
                                  '    "drei"\n'
                                  '  gamma `class "blue" "vier"')

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
        assert tree.as_xml(inline_tags=all_tags, string_tags=all_tags) == "Hallo Welt!"
        # tags with attributes will never be ommitted
        tree.pick_child('T').attr['class'] = "kursiv"
        assert tree.as_xml(inline_tags=all_tags, string_tags=all_tags) == \
               '<T class="kursiv">Hallo</T> Welt!'

    def test_XML_strict_mode(self):
        xml = "<xml><empty/><empty>not_empty!?</empty></xml>"
        # try:
        #     data = parse_xml(xml)
        #     assert False, "ValueError exptected!"
        # except ValueError:
        #     pass
        empty_tags = set()
        data = parse_xml(xml, out_empty_tags=empty_tags, strict_mode=False)
        for e in data.errors:
            print(e)
        # assert data.as_sxpr() == '(xml (empty) (empty "not_empty!?"))'
        assert empty_tags == {'empty'}
        assert data.as_xml().replace('\n', '').replace(' ', '') == \
            "<xml><empty></empty><empty>not_empty!?</empty></xml>"
        try:
            _ = data.as_xml(empty_tags=empty_tags)
            assert False, "ValueError expected"
        except ValueError:
            pass
        assert data.as_xml(empty_tags=empty_tags, strict_mode=False)\
            .replace('\n', '').replace(' ', '') == \
            "<xml><empty/><empty>not_empty!?</empty></xml>"
        data.result = data.result + (Node('empty', ''),)
        assert data.as_xml(empty_tags=empty_tags, strict_mode=False)\
            .replace('\n', '').replace(' ', '') == \
            "<xml><empty/><empty>not_empty!?</empty><empty/></xml>"


class TestSegementExtraction:
    def test_get_path(self):
        tree = parse_sxpr('(A (F (X "a") (Y "b")) (G "c"))')
        nd_X = tree.pick('X')
        ctx = tree.reconstruct_path(nd_X)
        assert [nd.name for nd in ctx] == ['A', 'F', 'X']
        nd_F = tree.pick('F')
        nd_Y = tree.pick('Y')
        ctx = nd_F.reconstruct_path(nd_Y)
        assert [nd.name for nd in ctx] == ['F', 'Y']
        ctx = tree.reconstruct_path(nd_F)
        assert [nd.name for nd in ctx] == ['A', 'F']
        ctx = tree.reconstruct_path(nd_Y)
        assert [nd.name for nd in ctx] == ['A', 'F', 'Y']
        nd_G = tree.pick('G')
        ctx = tree.reconstruct_path(nd_G)
        assert [nd.name for nd in ctx] == ['A', 'G']
        not_there = Node('not_there', '')
        try:
            tree.reconstruct_path(not_there)
            assert False, "ValueError expected!"
        except ValueError:
            pass
        assert tree.reconstruct_path(tree) == [tree]

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


class TestPathNavigation:
    tree = parse_sxpr('(A (B 1) (C (D 2) (E 3)) (F 4))')

    def test_prev_path(self):
        ctx = self.tree.pick_path('D')
        c = prev_path(ctx)
        assert c[-1].name == 'B'
        ctx = self.tree.pick_path('E')
        c = prev_path(ctx)
        assert c[-1].name == 'D'
        ctx = self.tree.pick_path('F')
        c = prev_path(ctx)
        assert c[-1].name == 'C'
        ctx = self.tree.pick_path('C')
        c = prev_path(ctx)
        assert c[-1].name == 'B'

    def test_next_path(self):
        ctx = self.tree.pick_path('D')
        c = next_path(ctx)
        assert c[-1].name == 'E'
        ctx = self.tree.pick_path('E')
        c = next_path(ctx)
        assert c[-1].name == 'F'
        ctx = self.tree.pick_path('C')
        c = next_path(ctx)
        assert c[-1].name == 'F'
        ctx = self.tree.pick_path('B')
        c = next_path(ctx)
        assert c[-1].name == 'C'

    def test_content_mapping(self):
        tree = parse_sxpr('(A (B alpha) (C (D beta) (E gamma)) (F delta))')
        cm = ContentMapping(tree)
        for i in range(len(tree.content)):
            ctx, rel_pos = cm.get_path_and_offset(i)
        i = cm.content.find("delta")
        ctx, rel_pos = cm.get_path_and_offset(i)
        assert ctx[-1].name == 'F' and rel_pos == 0
        i = cm.content.find("lta")
        ctx, rel_pos = cm.get_path_and_offset(i)
        assert ctx[-1].name == 'F' and rel_pos == 2
        i = cm.content.find("a")
        ctx, rel_pos = cm.get_path_and_offset(i)
        assert ctx[-1].name == 'B' and rel_pos == 0
        i = cm.content.rfind("a")
        ctx, rel_pos = cm.get_path_and_offset(i)
        assert ctx[-1].name == 'F' and rel_pos == 4
        i = tree.content.find("mm")
        ctx, rel_pos = cm.get_path_and_offset(i)
        assert ctx[-1].name == 'E' and rel_pos == 2

        select, ignore = {'A', 'B', 'D', 'F'}, {'C'}
        content = content_of(tree, select, ignore)
        assert content == "alphadelta"
        assert strlen_of(tree, select, ignore) == len('alphadelta')
        assert content_of(tree, select, ignore | {'B'}) == "delta"
        assert strlen_of(tree, select, ignore | {'B'}) == len("delta")
        assert content_of(tree, select, ignore | {'A'}) == ""
        assert strlen_of(tree, select, ignore | {'A'}) == 0

        mapping = ContentMapping(tree, leaf_paths(select), ignore)
        mapping.insert_node(content.find('delta'), Node('G', 'omicron'))
        assert flatten_sxpr(tree.as_sxpr()) == \
               '(A (B "alpha") (C (D "beta") (E "gamma")) (G "omicron") (F "delta"))'

    def test_map_index(self):
        tree = parse_xml('<doc>alpha<a><lb/></a><pb/> beta</doc>')
        cm = ContentMapping(tree)
        assert cm.get_path_index(5, left_biased=False) == 3
        assert cm.get_path_index(5, left_biased=True) == 0
        path, i = cm.get_path_and_offset(5, left_biased=False)
        assert path == cm.path_list[3]
        assert i == 0
        path, i = cm.get_path_and_offset(5, left_biased=True)
        assert path == cm.path_list[0]
        assert i == 5


    def test_standalone_select_path_if(self):
        start = self.tree.pick_path('E')
        save = start.copy()
        sequence = []
        for ctx in select_path_if(
                start, lambda c: True, include_root=True, reverse=True):
            sequence.append(''.join(n.name for n in ctx))
        assert sequence == ['ACE', 'ACD', 'AC', 'AB', 'A']
        assert save == start  # path passed should not be changed by select_path

        start = self.tree.pick_path('D')
        sequence = []
        for ctx in select_path_if(
                start, lambda c: True, include_root=True, reverse=False):
            sequence.append(''.join(n.name for n in ctx))
        assert sequence == ['ACD', 'ACE', 'AC', 'AF', 'A']

    def test_standalone_pick_path(self):
        start = self.tree.pick_path('A', include_root=True)
        anfang = pick_path(start, LEAF_PATH, include_root=True)
        ende = pick_path(start, LEAF_PATH, include_root=True, reverse=True)
        assert anfang[-1].name == 'B'
        assert ende[-1].name == 'F'


class TestEvaluation:
    def setup(self):
        self.save = get_config_value('syntax_variant')

    def teardown(self):
        set_config_value('syntax_variant', self.save)

    def test_evaluate(self):
        set_config_value('syntax_variant', 'peg-like')
        parser = create_parser(
            r'''@disposable = Spacing, LPAR, RPAR, EOL, EOF
            @drop = Spacing, LPAR, RPAR, EOL, EOF
            Start   <- Spacing Expr EOL? EOF
            Expr    <- Term ((PLUS / MINUS) Term)*
            Term    <- Factor ((TIMES / DIVIDE) Factor)*
            Factor  <- Sign* (LPAR Expr RPAR
                             / INTEGER )
            Sign    <- NEG / POS
            INTEGER <- Spacing ( '0' / [1-9][0-9]* ) Spacing
            PLUS    <- '+' Spacing
            MINUS   <- '-' Spacing
            TIMES   <- '*' Spacing
            DIVIDE  <- '/' Spacing
            LPAR    <- '(' Spacing
            RPAR    <- ')' Spacing
            NEG     <- '-' Spacing
            POS     <- '+' Spacing
            Spacing <- [ \t\n\f\v\r]*
            EOL     <- '\r\n' / [\n\r]
            EOF     <- !.
            ''')
        tree = parser('2 + 3 * -(7 - 2)')
        from operator import add, sub, mul, truediv as div, neg
        actions = {
            'Start': lambda arg: arg,
            'Expr': lambda *args: args[1](args[0], args[2]) if len(args) == 3 else args[0],
            'Term': lambda *args: args[1](args[0], args[2]) if len(args) == 3 else args[0],
            'Factor': lambda *args: mul(*args) if len(args) > 1 else args[0],
            'Sign': lambda arg: arg,
            'INTEGER': int,
            'PLUS': lambda token: add,
            'MINUS': lambda token: sub,
            'TIMES': lambda token: mul,
            'DIVIDE': lambda token: div,
            'NEG': lambda token: -1,
            'POS': lambda token: 1}
        assert tree.evaluate(actions) == -13


#class TestStrLenPos:



class TestMarkupInsertion:
    testdata_1 = '<document>In Charlot<lb/>tenburg steht ein Schloss.</document>'
    testdata_2 = '''<document>
<app n="g">
<lem>silvae</lem>
<rdg wit="A">silvae, </rdg>
</app> glandiferae</document>'''
    testdata_3 = '''<doc>Am <outer><inner>Anfang</inner> war das Wort</outer>.</doc>'''

    def test_content_of(self):
        tree = parse_xml('<p>This is<fn>footnote</fn> a text</p>')
        assert content_of(tree) == 'This isfootnote a text'
        assert content_of(tree, ignore='fn') == 'This is a text'
        assert content_of(tree, select='fn') == 'footnote'

    def test_ContentMapping_constructor(self):
        tree = parse_xml('<doc><p>In München<footnote><em>München</em> is the '
            'German name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>')
        try:
            cm = ContentMapping(tree, select='footnote')
            assert False, "ValueError expected"
        except ValueError as e:
            pass
        cm = ContentMapping(tree, select=lambda pth: pick_from_path(pth, 'footnote')
                                                     and not pth[-1].children)

    def test_ContentMapping_rebuild_mapping(self):
        tree = parse_xml('<doc><p>In München<footnote><em>München</em> is the '
            'German name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>')
        fm = ContentMapping(tree, select=leaf_paths('footnote'), ignore=NO_PATH)
        i = fm.content.find('München')
        path, offset = fm.get_path_and_offset(i)
        path[-1].result = path[-1].result[:offset] + "Stadt " + path[-1].result[offset:]
        assert tree.as_xml(inline_tags={'doc'}) == ('<doc><p>In München<footnote>'
            '<em>Stadt München</em> is the German name of the city of Munich</footnote> '
            'is a Hofbräuhaus</p></doc>')
        k = fm.get_path_index(i)
        fm.rebuild_mapping_slice(k, k)
        assert fm._pos_list == [0, 13]

    def test_chain_id(self):
        s = set()
        for i in range(200_000):
            cid = gen_chain_ID()
            assert cid not in s
            s.add(cid)
            assert len(cid) <= 4
        assert len(s) == 200_000

    def test_chain_attr_1(self):
        tree = parse_xml("<hard>Please mark up Stadt\n<lb/><location><em>München</em> "
                         "in Bavaria</location> in this sentence.</hard>")
        divisability_map = {'foreign': {'location', ':Text'},
                                        '*': {':Text'}}
        mapping = ContentMapping(tree, divisability=divisability_map,
                                 chain_attr_name = "chain")
        match = re.search(r"Stadt\s+München", mapping.content)
        _ = mapping.markup(match.start(), match.end(), "foreign", {'lang': 'de'})
        xml_str = tree.as_xml(empty_tags={'lb'})
        # print(xml_str)
        chains = {loc.attr['chain'] for loc in tree.select('location')}
        assert len(chains) == 1

    # def test_chain_attr_2(self):
    #     tree = parse_xml("<doc>Please mark up Stadt\n<lb/>"
    #         "<em>München</em><footnote>'Stadt <em>München</em>'"
    #         " is German for 'City of Munich'</footnote> in Bavaria"
    #         " in this sentence.</doc>")
    #     cm = ContentMapping(tree, select=LEAF_PATH, ignore='footnote')
    #     m = re.search(r"München\s+in\s+Bavaria", cm.content)
    #     _ = cm.markup(m.start(), m.end(), 'location', chain_attr_name='chain')
    #     print(tree.as_xml(empty_tags={'lb'}))


    def test_insert_milestone_1(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_1, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        i = tree.content.find("Charlottenburg")
        assert i >= 0
        milestone = Node("ref", "").with_attr(type="subj", target="Charlottenburg_S00231")
        empty_tags.add("ref")
        tm = ContentMapping(tree)
        tm.insert_node(i, milestone)
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document>In <ref type="subj" '
                       'target="Charlottenburg_S00231"/>Charlot<lb/>tenburg steht ein '
                       'Schloss.</document>')

    def test_insert_milestone_2(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_2, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = next(re.finditer(r'silvae,?\s*glandiferae', tree.content))
        milestone = Node("ref", "").with_attr(type="subj", target="silva_glandifera_S01229")
        empty_tags.add("ref")
        tm = ContentMapping(tree)
        tm.insert_node(m.start(), milestone)
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document><app n="g"><lem>silvae</lem><ref type="subj" '
                       'target="silva_glandifera_S01229"/><rdg wit="A">silvae, </rdg></app> '
                       'glandiferae</document>')

    def test_insert_markup_1(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_1, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        i = tree.content.find("Charlottenburg")
        assert i >= 0
        k = i + len("Charlottenburg")
        tm = ContentMapping(tree)
        tm.markup(i, k, "ref", { 'type':"subj", 'target':"Charlottenburg_S00231"})
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document>In <ref type="subj" '
                       'target="Charlottenburg_S00231">Charlot<lb/>tenburg</ref> steht ein '
                       'Schloss.</document>')

    def test_insert_markup_2(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_2, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = next(re.finditer(r'silvae,?\s*glandiferae', tree.content))
        tm = ContentMapping(tree)
        tm.markup(m.start(), m.end(), "ref", {'type': "subj", 'target': "silva_glandifera_S01229"})
        xml = tree.as_xml(inline_tags={"document"}, string_tags={TOKEN_PTYPE},
                          empty_tags=empty_tags)
        assert xml == ('<document><app n="g"><lem>silvae</lem><ref type="subj" '
                       'target="silva_glandifera_S01229"><rdg wit="A">silvae, </rdg></ref></app><ref '
                        'type="subj" target="silva_glandifera_S01229"> glandiferae</ref></document>')

    def test_insert_markup_3(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_3, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = next(re.finditer(r'Anfang war das Wort', tree.content))
        cm = ContentMapping(tree)
        cm.markup(m.start(), m.end(), "a")
        assert tree.as_xml(inline_tags={'doc'}, string_tags={':Text'}) == \
            '<doc>Am <outer><a><inner>Anfang</inner> war das Wort</a></outer>.</doc>'
        empty_tags = set()
        tree = parse_xml(self.testdata_3, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = next(re.finditer(r'Am Anfang war', tree.content))
        cm = ContentMapping(tree)
        cm.markup(m.start(), m.end(), "a")
        assert tree.as_xml(inline_tags={'doc'}, string_tags={':Text'}) == \
            '<doc><a>Am </a><outer><a><inner>Anfang</inner> war</a> das Wort</outer>.</doc>'

    def test_insert_markup_4(self):
        empty_tags = set()
        tree = parse_xml(self.testdata_3, string_tag=TOKEN_PTYPE, out_empty_tags=empty_tags)
        m = next(re.finditer(r'Am Anfang war', tree.content))
        cm = ContentMapping(tree, chain_attr_name='_chain')
        cm.markup(m.start(), m.end(), "a")
        I = tree.pick('a').attr['_chain']
        assert tree.as_xml(inline_tags={'doc'}, string_tags={':Text'}) == \
            f'<doc><a _chain="{I}">Am </a><outer><a _chain="{I}"><inner>Anfang</inner> war</a>'\
            f' das Wort</outer>.</doc>'

    def test_insert_markup_5(self):
        tree = parse_xml('<text><hi rend="i">X</hi>34, 53 ... Q. Aelius Tubero tribunus plebis</text>')
        i = tree.content.find('Q.')
        k = tree.content.find('Tubero') + len('Tubero')
        cm = ContentMapping(tree)
        cm.markup(i, k, "a")
        assert tree.as_xml(inline_tags={'text'}, string_tags={TOKEN_PTYPE}) == \
            '<text><hi rend="i">X</hi>34, 53 ... <a>Q. Aelius Tubero</a> tribunus plebis</text>'

    def test_insert_markup_6(self):
        tree = parse_xml('<doc>wenn wir bei <hi rend="italic">Cicero</hi><note type="footnote" n="29)">'
            '<pb n="225"/>In Verr. acc. 1. 3, 120. </note> die meist nicht erhebli<lb/>chen Zahlen</doc>')
        m = re.search(r'Cicero', tree.content)
        a, b = m.start(), m.end()
        cm = ContentMapping(tree, auto_cleanup=True)
        cm.markup(a, b, 'ref')
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (:Text "wenn wir bei ") '\
            '(hi `(rend "italic") (ref "Cicero")) (note `(type "footnote") `(n "29)") '\
            '(pb `(n "225")) (:Text "In Verr. acc. 1. 3, 120. ")) '\
            '(:Text " die meist nicht erhebli") (lb) (:Text "chen Zahlen"))'

    def test_insert_markup_7(self):
        tree= parse_xml('<doc>Zugleich traf sie für <pb n="219"/>den ager compascuus folgende Bestimmung '
            '(Z. 14, 15 nach <hi rend="italic">Momm</hi><lb/><hi rend="italic">sens</hi>'
            '<note type="comment" n="53"><pb n="219"/>Offenbar</note> nach:</doc>')
        m = re.search(r'Mommsen', tree.content)
        a, b = m.start(), m.end()
        cm = ContentMapping(tree, auto_cleanup=True)
        cm.markup(a, b, 'ref')
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (:Text "Zugleich traf sie für ") '\
            '(pb `(n "219")) (:Text "den ager compascuus folgende Bestimmung '\
            '(Z. 14, 15 nach ") (ref (hi `(rend "italic") "Momm") (lb)) (hi `(rend "italic") '\
            '(ref "sen") (:Text "s")) (note `(type "comment") `(n "53") (pb `(n "219")) '\
            '(:Text "Offenbar")) (:Text " nach:"))'

    def test_insert_markup_8(self):
        tree = parse_xml('<item><pb n="283" ed="A"></pb><hi rend="italic">Beaudouin</hi>. Études'
            '<note type="comment" n="10">Im Titel heißt es: Étude. </note> sur le jus Italicum '
            '(Nouvelle revue historique V, 1881, p. 145ff.). </item>')
        m = re.search('Beaudouin. Études', tree.content)
        a, b = m.start(), m.end()
        cm = ContentMapping(tree, auto_cleanup=True)
        cm.markup(a, b, 'ref')
        assert tree.as_xml(inline_tags={'item'}) == '<item><pb n="283" ed="A"></pb>'\
            '<ref><hi rend="italic">Beaudouin</hi>. Études</ref><note type="comment" n="10">'\
            'Im Titel heißt es: Étude. </note> sur le jus Italicum (Nouvelle revue historique '\
            'V, 1881, p. 145ff.). </item>'

    def test_maskup_borderline_cases(self):
        ### borderline cases
        tree = parse_xml('<doc>Hello, <em>World</em>!</doc>')
        X = copy.deepcopy(tree)
        t = ContentMapping(X)
        _ = t.markup(3, 4, 'b')
        assert X.as_xml(inline_tags={'doc'}) \
            == '<doc>Hel<b>l</b>o, <em>World</em>!</doc>'

        X = copy.deepcopy(tree)
        t = ContentMapping(X)
        _ = t.markup(3, 3, 'b')
        assert X.as_xml(inline_tags={'doc'}, empty_tags={'b'}) \
               == '<doc>Hel<b/>lo, <em>World</em>!</doc>'


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
