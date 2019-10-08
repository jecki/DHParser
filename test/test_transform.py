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
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.syntaxtree import Node, parse_sxpr, parse_xml, PLACEHOLDER, \
    tree_sanity_check
from DHParser.transform import traverse, reduce_single_child, remove_whitespace, move_adjacent, \
    traverse_locally, collapse, collapse_children_if, lstrip, rstrip, remove_content, remove_tokens, \
    transformation_factory, has_parent, contains_only_whitespace, is_insignificant_whitespace, \
    merge_adjacent, is_one_of
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
        cst = parse_sxpr('(wortarten (:Token "ajektiv") (:Token "et") (:Token "praeposition"))')
        ast_table = {
            "wortarten": [remove_tokens({"et"})],
            "*": []
        }
        traverse(cst, ast_table)
        cst1 = cst.as_sxpr()
        assert cst1.find('et') < 0
        ast_table = {
            "wortarten": [remove_tokens("et")],
            "*": []
        }
        traverse(cst, ast_table)
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
        context = [Node('A', 'alpha'),
                   Node('B', 'beta'),
                   Node('C', 'gamma')]
        assert has_parent(context, {'A'})
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
        traverse(cst, global_tansformations)
        # whitespace after "facitergula", but not after "bona" should have been removed
        assert str(cst) == "faciterculasim.bona fide"

class TestComplexTransformations:
    def setup(self):
        self.Text = 'Text'  # TOKEN_PTYPE

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
        # print(flatten_sxpr(tree.as_sxpr()))
        collapse_children_if([tree], lambda context: context[-1].tag_name != 'HOCHGESTELLT', self.Text)
        assert tree.as_xml(inline_tags={'Stelle'}) == \
               "<Stelle><Text>p.26</Text><HOCHGESTELLT>b</HOCHGESTELLT><Text>,18</Text></Stelle>"


class TestWhitespaceTransformations:
    def test_move_adjacent(self):
        sentence = parse_sxpr('(SENTENCE (WORD (LETTERS "To") (:Whitespace " ")) '
                              '(WORD (LETTERS "be") (:Whitespace " ")) '
                              '(WORD (LETTERS "or") (:Whitespace " ")) '
                              '(WORD (LETTERS "not") (:Whitespace " ")) '
                              '(WORD (LETTERS "to") (:Whitespace " "))'
                              '(WORD (LETTERS "be") (:Whitespace " ")))')
        transformations = {'WORD': move_adjacent(is_insignificant_whitespace)}
        traverse(sentence, transformations)
        assert tree_sanity_check(sentence)
        assert all(i % 2 == 0 or node.tag_name == ':Whitespace' for i, node in enumerate(sentence))

    def test_move_adjacent2(self):
        sentence = parse_sxpr('(SENTENCE (WORD (LETTERS "To") (:Whitespace " ")) '
                              '(WORD (:Whitespace " ") (LETTERS "be") (:Whitespace " ")) '
                              '(WORD (:Whitespace " ") (LETTERS "or") (:Whitespace " ")) '
                              '(WORD (:Whitespace " ") (LETTERS "not") (:Whitespace "a") (:Whitespace "b")) '
                              '(:Whitespace "c")'
                              '(WORD (:Whitespace "d") (:Whitespace "e") (LETTERS "to") (:Whitespace " "))'
                              '(WORD (:Whitespace " ") (LETTERS "be") (:Whitespace " ")))')
        transformations = {'WORD': move_adjacent(is_insignificant_whitespace)}
        traverse(sentence, transformations)
        assert tree_sanity_check(sentence)
        assert sentence.content.find('abcde') >= 0
        assert all(i % 2 == 0 or node.tag_name == ':Whitespace' for i, node in enumerate(sentence))
        assert all(i % 2 != 0 or (node.tag_name == "WORD" and ":Whitespace" not in node)
                   for i, node in enumerate(sentence))

    def test_move_adjacent2(self):
        sentence = parse_sxpr('(SENTENCE  (:Whitespace " ") (:Whitespace " ")  '
                              '(TEXT (PHRASE "Guten Tag") (:Whitespace " ")))')
        transformations = {'TEXT': move_adjacent(is_insignificant_whitespace)}
        traverse(sentence, transformations)

    def test_merge_adjacent(self):
        sentence = parse_sxpr('(SENTENCE (TEXT "Guten") (L " ") (TEXT "Tag") '
                              ' (T "\n") (TEXT "Hallo") (L " ") (TEXT "Welt")'
                              ' (T "\n") (L " "))')
        transformations = {'SENTENCE': merge_adjacent(is_one_of('TEXT', 'L'), 'TEXT')}
        traverse(sentence, transformations)
        # print(sentence.as_sxpr())
        assert tree_sanity_check(sentence)
        assert sentence['TEXT'].result == "Guten Tag"
        assert sentence[2].result == "Hallo Welt"
        assert sentence[-1].tag_name == 'L'
        assert 'T' in sentence

        # leaf nodes should be left untouched
        sentence = parse_sxpr('(SENTENCE "Hallo Welt")')
        traverse(sentence, transformations)
        assert sentence.content == "Hallo Welt", sentence.content


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())