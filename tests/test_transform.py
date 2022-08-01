#!/usr/bin/python3

"""test_transform.py - test of tramsform-module of DHParser

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2018 Bavarian Academy of Sciences and Humanities

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

import collections.abc
import copy
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.nodetree import Node, RootNode, parse_sxpr, parse_xml, PLACEHOLDER, \
    tree_sanity_check, flatten_sxpr, WHITESPACE_PTYPE
from DHParser.transform import traverse, reduce_single_child, remove_whitespace, move_fringes, \
    traverse_locally, collapse, collapse_children_if, lstrip, rstrip, remove_content, \
    remove_tokens, transformation_factory, has_ancestor, has_parent, contains_only_whitespace, \
    merge_adjacent, is_one_of, not_one_of, swap_attributes, delimit_children, merge_treetops, \
    positions_of, insert, node_maker, apply_if, change_name, add_attributes, add_error, \
    merge_leaves, BLOCK_ANONYMOUS_LEAVES, pick_longest_content, fix_content
from typing import AbstractSet, List, Sequence, Tuple


class TestRemoval:
    """Tests removing transformations."""

    def test_contains_only_whitespace(self):
        assert contains_only_whitespace([Node('test', ' ')])
        assert contains_only_whitespace([Node('test', '')])
        assert contains_only_whitespace([Node('test', '\n')])
        assert not contains_only_whitespace([Node('test', 'Katze')])
        assert not contains_only_whitespace([Node('test', ' tag ')])

    def test_lstrip(self):
        cst = parse_sxpr('(_Token (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        sxpr1 = cst.as_sxpr()
        lstrip([cst])
        assert sxpr1 == cst.as_sxpr()
        cst = parse_sxpr('(_Token)')
        lstrip([cst])
        assert cst.as_sxpr() == '(_Token)'
        cst = parse_sxpr('(_Token (:Whitespace " ") (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = parse_sxpr('(_Token (:Whitespace " ") (Deeper (:Whitespace " ")) '
                               '(:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = parse_sxpr('(_Token (:Re ein) (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") >= 0

    def test_rstrip(self):
        cst = parse_sxpr('(_Token (:Re test) (:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0, cst.as_sxpr()
        sxpr1 = cst.as_sxpr()
        rstrip([cst])
        assert sxpr1 == cst.as_sxpr()
        cst = parse_sxpr('(_Token)')
        rstrip([cst])
        assert cst.as_sxpr() == '(_Token)'
        cst = parse_sxpr('(_Token  (:Re test) (:Whitespace " ") (:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = parse_sxpr('(_Token  (:Re test) (:Whitespace " ") (Deeper (:Whitespace " ")) '
                               '(:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0, cst.as_sxpr()

    def test_remove_content(self):
        cst = parse_sxpr('(BelegLemma (:Series (:RegExp "#") (LAT_WORT (:RegExp "facitergula"))))')
        remove_content([cst], '#')
        assert cst.content == "#facitergula", str(cst.content)
        reduce_single_child([cst])
        remove_content([cst], '#')
        assert cst.content == "facitergula"

    def test_remove_tokens(self):
        cst = parse_sxpr('(wortarten (:Text "ajektiv") (:Text "et") (:Text "praeposition"))')
        ast_table = {
            "wortarten": [remove_tokens({"et"})],
            "*": []
        }
        cst = traverse(cst, ast_table)
        cst1 = cst.as_sxpr()
        assert cst1.find('et') < 0
        ast_table = {
            "wortarten": [remove_tokens("et")],
            "*": []
        }
        cst = traverse(cst, ast_table)
        assert cst1 == cst.as_sxpr()


class TestTransformationFactory:
    def test_mismatching_types(self):
        @transformation_factory(tuple)
        def good_transformation(context: List[Node], parameters: Tuple[str]):
            pass
        try:
            @transformation_factory(tuple)
            def bad_transformation(context: List[Node], parameters: AbstractSet[str]):
                pass
            assert False, "mismatching types not recognized by transform.transformation_factory()"
        except TypeError:
            pass

    def test_forbidden_generic_types_in_decorator(self):
        try:
            @transformation_factory(AbstractSet[str])
            def forbidden_transformation(context: List[Node], parameters: AbstractSet[str]):
                pass
            assert False, "use of generics not recognized in transform.transformation_factory()"
        except TypeError:
            pass

    def test_forbidden_mutable_sequence_types_in_decorator(self):
        try:
            @transformation_factory(collections.abc.Sequence)
            def parameterized_transformation(context: List[Node], parameters: Sequence[str]):
                pass
            _ = parameterized_transformation('a', 'b', 'c')
            assert False, ("use of mutable sequences not recognized in "
                           "transform.transformation_factory()")
        except TypeError:
            pass

    def test_parameter_set_expansion1(self):
        save = None
        @transformation_factory(collections.abc.Set)
        def parameterized_transformation(context: List[Node], parameters: AbstractSet[str]):
            nonlocal save
            save = parameters
        transformation = parameterized_transformation('a', 'b', 'c')
        transformation([PLACEHOLDER])
        assert save == {'a', 'b', 'c'}

    def test_parameter_set_expansion2(self):
        save = None
        @transformation_factory(tuple)
        def parameterized_transformation(context: List[Node], parameters: Tuple[str]):
            nonlocal save
            save = parameters
        transformation = parameterized_transformation('a', 'b', 'c')
        transformation([PLACEHOLDER])
        assert save == ('a', 'b', 'c'), str(save)


class TestConditionalTransformations:
    """Tests conditional transformations."""

    def test_has_parent(self):
        context = [Node('C', 'alpha'),
                   Node('B', 'beta'),
                   Node('A', 'gamma')]
        assert not has_ancestor(context, {'A'}, 1)
        assert has_ancestor(context, {'B'}, 1)
        assert not has_ancestor(context, {'C'}, 1)
        assert has_ancestor(context, {'C'}, 2)

        assert not has_parent(context, {'A'})
        assert has_parent(context, {'B'})
        assert not has_parent(context, {'C'})

    def test_traverse_locally(self):
        cst = parse_sxpr("""
            (Lemma
                (LemmaVariante
                    (LAT_WORT
                        (:RegExp
                            "facitercula"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (Zusatz
                        (DEU_WORT
                            "sim."
                        )
                    )
                )
                (Hinweis
                    (LAT_WORT
                        (:RegExp
                            "bona"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (LAT_WORT
                        (:RegExp
                            "fide"
                        )
                    )
                )
            )""")
        LemmaVariante_transformations = {
            "LAT_WORT": [remove_whitespace, reduce_single_child],
            "Zusatz": [reduce_single_child]
        }
        global_tansformations = {
            "LemmaVariante": [traverse_locally(LemmaVariante_transformations)],
            "Hinweis": [collapse]
        }
        cst = traverse(cst, global_tansformations)
        # whitespace after "facitergula", but not after "bona" should have been removed
        assert str(cst) == "faciterculasim.bona fide"

class TestComplexTransformations:
    Text = 'Text'  # TOKEN_PTYPE

    def test_collapse_children_if_plain(self):
        xml = "<EINZEILER><DEU_WORT>spectat</DEU_WORT><WS> </WS><DEU_WORT>ad</DEU_WORT>" +\
              "<WS> </WS><DEU_WORT>gravitatem</DEU_WORT><TEIL_SATZZEICHEN>,</TEIL_SATZZEICHEN>" +\
              "<WS> </WS><DEU_WORT>momentum</DEU_WORT></EINZEILER>"
        tree = parse_xml(xml)
        assert tree.as_xml(inline_tags={'EINZEILER'}) == xml
        collapse_children_if([tree], lambda l: True, self.Text)
        assert tree.as_xml(inline_tags={'EINZEILER'}) == \
               "<EINZEILER><Text>spectat ad gravitatem, momentum</Text></EINZEILER>"

    def test_collapse_children_if_structured(self):
        xml = """<Stelle>
                   <DEU_WORT>p.</DEU_WORT>
                   <SEITENZAHL>26</SEITENZAHL>
                   <HOCHGESTELLT>b</HOCHGESTELLT>
                   <TEIL_SATZZEICHEN>,</TEIL_SATZZEICHEN>
                   <SEITENZAHL>18</SEITENZAHL>
                 </Stelle>"""
        tree = parse_xml(xml)
        collapse_children_if([tree], lambda context: context[-1].name != 'HOCHGESTELLT',
                             self.Text)
        assert tree.as_xml(inline_tags={'Stelle'}) == \
               "<Stelle><Text>p.26</Text><HOCHGESTELLT>b</HOCHGESTELLT><Text>,18</Text></Stelle>"

    def test_collapse_children_if_with_attributes(self):
        sxpr = '(place (abbreviation `(unabbr "page") "p.") (page `(numbered "arabic") "26") ' \
               '(superscript "b") (mark ",") (page "18"))'
        tree = parse_sxpr(sxpr)
        collapse_children_if([tree], not_one_of({'superscript', 'subscript'}), 'text')
        s = flatten_sxpr(tree.as_sxpr())
        assert s == '(place (text `(unabbr "page") `(numbered "arabic") "p.26") (superscript "b") (text ",18"))'

    def test_collapse_merge_rules(self):
        sxpr = '(Article (TEXT "Hello") (L " ") (L `(spatium "4") "    ") (L " ") (Text "World"))'
        tree = parse_sxpr(sxpr)
        collapse_children_if([tree], is_one_of('L'), 'L', pick_longest_content)
        s = flatten_sxpr(tree.as_sxpr())
        assert s == '(Article (TEXT "Hello") (L `(spatium "4") "    ") (Text "World"))'
        tree = parse_sxpr(sxpr)
        collapse_children_if([tree], is_one_of('L'), 'L', fix_content(" "))
        s = flatten_sxpr(tree.as_sxpr())
        assert s == '(Article (TEXT "Hello") (L `(spatium "4") " ") (Text "World"))'


class TestWhitespaceTransformations:
    def test_move_fringes(self):
        sentence = parse_sxpr('(SENTENCE (WORD (LETTERS "To") (:Whitespace " ")) '
                              '(WORD (LETTERS "be") (:Whitespace " ")) '
                              '(WORD (LETTERS "or") (:Whitespace " ")) '
                              '(WORD (LETTERS "not") (:Whitespace " ")) '
                              '(WORD (LETTERS "to") (:Whitespace " "))'
                              '(WORD (LETTERS "be") (:Whitespace " ")))')
        transformations = {'WORD': move_fringes(lambda ctx: ctx[-1].name == WHITESPACE_PTYPE)}
        sentence = traverse(sentence, transformations)
        assert tree_sanity_check(sentence)
        assert all(i % 2 == 0 or node.name == ':Whitespace' for i, node in enumerate(sentence))

    def test_move_fringes2(self):
        sentence = parse_sxpr('(SENTENCE (WORD (LETTERS "To") (:Whitespace " ")) '
                              '(WORD (:Whitespace " ") (LETTERS "be") (:Whitespace " ")) '
                              '(WORD (:Whitespace " ") (LETTERS "or") (:Whitespace " ")) '
                              '(WORD (:Whitespace " ") (LETTERS "not") (:Whitespace "a") (:Whitespace "b")) '
                              '(:Whitespace "c")'
                              '(WORD (:Whitespace "d") (:Whitespace "e") (LETTERS "to") (:Whitespace " "))'
                              '(WORD (:Whitespace " ") (LETTERS "be") (:Whitespace " ")))')
        transformations = {'WORD': move_fringes(lambda ctx: ctx[-1].name == WHITESPACE_PTYPE)}
        sentence = traverse(sentence, transformations)
        assert tree_sanity_check(sentence)
        assert sentence.content.find('abcde') >= 0
        assert all(i % 2 == 0 or node.name == ':Whitespace' for i, node in enumerate(sentence))
        assert all(i % 2 != 0 or (node.name == "WORD" and ":Whitespace" not in node)
                   for i, node in enumerate(sentence))

    def test_move_fringes3(self):
        sentence = parse_sxpr('(SENTENCE  (:Whitespace " ") (:Whitespace " ")  '
                              '(TEXT (PHRASE "Guten Tag") (:Whitespace " ")))')
        transformations = {'TEXT': move_fringes(lambda ctx: ctx[-1].name == WHITESPACE_PTYPE)}
        sentence = traverse(sentence, transformations)

    def test_merge_adjacent(self):
        sentence = parse_sxpr('(SENTENCE (TEXT "Guten") (L " ") (TEXT "Tag") '
                              ' (T "\n") (TEXT "Hallo") (L " ") (TEXT "Welt")'
                              ' (T "\n") (L " "))')
        transformations = {'SENTENCE': merge_adjacent(is_one_of('TEXT', 'L'), 'TEXT')}
        sentence = traverse(sentence, transformations)
        assert tree_sanity_check(sentence)
        assert sentence.pick_child('TEXT').result == "Guten Tag"
        assert sentence[2].result == "Hallo Welt"
        assert sentence[-1].name == 'L'
        assert 'T' in sentence

        # leaf nodes should be left untouched
        sentence = parse_sxpr('(SENTENCE "Hallo Welt")')
        sentence = traverse(sentence, transformations)
        assert sentence.content == "Hallo Welt", sentence.content

    # def test_merge_adjacent2(self):
    #     expr = parse_sxpr('(Autor (:Whitespace " ") (DEU_GEMISCHT "K. ") (DEU_GEMISCHT "Figala"))')
    #     transformations = {'Autor': merge_adjacent(not_one_of('Anker'), 'TEXT')}
    #     expr = traverse(expr, transformations)
    #     print(expr.as_sxpr())


    def test_merge_adjacent_with_attributes(self):
        tree = parse_sxpr('(A (L " ") (L `(spatium "3+1") " "))')
        merge_adjacent([tree], is_one_of('L'), 'L')
        assert len(tree.children) == 1
        assert tree.children[0].get_attr('spatium', 'FEHLER') == "3+1"

class TestAttributeHandling:
    def test_swap_attributes(self):
        A = Node('A', '')
        B = Node('B', '')
        A.attr['x'] = 'x'
        swap_attributes(A, B)
        assert not A.attr
        assert B.attr['x'] == 'x'
        swap_attributes(A, B)
        assert not B.attr
        assert A.attr['x'] == 'x'
        B.attr['y'] = 'y'
        swap_attributes(A, B)
        assert A.attr['y'] == 'y'
        assert B.attr['x'] == 'x'


class TestConstructiveTransformations:
    def test_add_delimiter(self):
        tree = parse_sxpr('(A (B 1) (B 2) (B 3))').with_pos(0)
        trans_table = {'A': delimit_children(node_maker('c', ','))}
        tree = traverse(tree, trans_table)
        original_result = tree.serialize(how='S-expression')
        assert original_result == '(A (B "1") (c ",") (B "2") (c ",") (B "3"))', original_result

    def test_complex_delimiter(self):
        tree = parse_sxpr('(A (B 1) (B 2) (B 3))').with_pos(0)
        nm = node_maker('d', (node_maker('c', ','), node_maker('l', ' ')))
        n = nm()
        trans_table = {'A': delimit_children(
            node_maker('d', (node_maker('c', ','), node_maker('l', ' '))))}
        tree = traverse(tree, trans_table)
        original_result = tree.serialize()
        assert original_result \
            == '(A (B "1") (d (c ",") (l " ")) (B "2") (d (c ",") (l " ")) (B "3"))', \
            original_result

    def test_insert_nodes(self):
        tree = parse_sxpr('(A (B 1) (B 2) (X 3))').with_pos(0)
        trans_table = {'A': insert(0, node_maker('c', '=>'))}
        tree = traverse(tree, trans_table)
        result1 = tree.serialize()
        assert result1 == '(A (c "=>") (B "1") (B "2") (X "3"))', result1

        trans_table = {'A': insert(4, node_maker('d', '<='))}
        tree = traverse(tree, trans_table)
        result2 = tree.serialize()
        assert result2 == '(A (c "=>") (B "1") (B "2") (X "3") (d "<="))', result2
        trans_table = {'A': insert(-2, node_maker('e', '|'))}
        tree = traverse(tree, trans_table)
        result3 = tree.serialize()
        assert result3 == '(A (c "=>") (B "1") (B "2") (e "|") (X "3") (d "<="))', result3

        tree = parse_sxpr('(A "")').with_pos(0)
        trans_table = {'A': insert(0, node_maker('B', 'b'))}
        tree = traverse(tree, trans_table)
        result4 = tree.serialize()
        assert result4 == '(A (B "b"))'

        tree = parse_sxpr('(A "")').with_pos(0)
        trans_table = {'A': insert(lambda ctx: None, node_maker('B', 'b'))}
        tree = traverse(tree, trans_table)
        result5 = tree.serialize()
        assert result5 == '(A)'

    def test_positions_of(self):
        tree = parse_sxpr('(A (B 1) (C 1) (B 2))').with_pos(0)
        assert positions_of([tree], 'A') == ()
        assert positions_of([tree], 'X') == ()
        assert positions_of([tree], 'C') == (1,)
        assert positions_of([tree], 'B') == (0, 2)

        tree = parse_sxpr('(A (B 1) (C 2) (D 3))').with_pos(0)
        trans_table = {'A': insert(positions_of('D'), node_maker('X', '0'))}
        tree = traverse(tree, trans_table)
        result1 = tree.serialize()
        assert result1 == '(A (B "1") (C "2") (X "0") (D "3"))', result1

        trans_table = {'A': insert(positions_of('Z'), node_maker('X', '0'))}
        tree = traverse(tree, trans_table)
        result2 = tree.serialize()
        assert result2 == '(A (B "1") (C "2") (X "0") (D "3"))', result2


class TestBoolean:
    def test_apply_if(self):
        tree = parse_sxpr('(A (B 1) (C 1) (B 2))').with_pos(0)
        trans_table = { 'B': [apply_if((change_name('X'),
                                        add_attributes({'renamed': 'True'})),
                                       is_one_of('B'))] }
        tree = traverse(tree, trans_table)
        assert flatten_sxpr(tree.as_sxpr()) == '(A (X `(renamed "True") "1") (C "1") (X `(renamed "True") "2"))'

class TestOptimizations:
    model = RootNode(parse_sxpr('''(array
          (number "1")
          (number
            (:RegExp "2")
            (:RegExp ".")
            (:RegExp "0"))
          (string "a string"))''')).with_pos(0)

    def raise_error(self, context):
        raise AssertionError()

    def test_squeeze_tree(self):
        tree = copy.deepcopy(TestOptimizations.model)
        merge_treetops(tree)
        assert tree.as_sxpr() == '''(array (number "1") (number "2.0") (string "a string"))'''

    def test_blocking(self):
        tree = copy.deepcopy(TestOptimizations.model)
        transtable = {
            '<': BLOCK_ANONYMOUS_LEAVES,
            'number': [merge_leaves, reduce_single_child],
            ':RegExp': self.raise_error
        }
        tree = traverse(tree, transtable)
        assert tree.equals(parse_sxpr('(array (number "1") (number "2.0") (string "a string"))'))


class TestErrors:
    def test_add_error(self):
        lang = """
            doc = letters { ws letters }
            letters = /\w+/ | WRONG
            ws = /\s+/
            WRONG = /[^\w\s]+/
        """
        from DHParser.dsl import create_parser
        parser = create_parser(lang)
        ast = parser('abc ??? def')
        trans_table = {'WRONG': add_error('Bad mistake!!!')}
        ast = traverse(ast, trans_table)
        e = ast.errors[0]
        assert e.line > 0 and e.column > 0


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())