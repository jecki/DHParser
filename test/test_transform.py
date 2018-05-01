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
import sys

sys.path.extend(['../', './'])

from DHParser.syntaxtree import Node, parse_sxpr, ZOMBIE_NODE
from DHParser.transform import traverse, reduce_single_child, remove_whitespace, \
    traverse_locally, collapse, lstrip, rstrip, remove_content, remove_tokens, \
    transformation_factory
from DHParser.toolkit import typing
from typing import AbstractSet, List, Sequence, Tuple


class TestRemoval:
    """Tests removing transformations."""

    def test_lstrip(self):
        cst = parse_sxpr('(Token (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        sxpr1 = cst.as_sxpr()
        lstrip([cst])
        assert sxpr1 == cst.as_sxpr()
        cst = parse_sxpr('(Token)')
        lstrip([cst])
        assert cst.as_sxpr() == '(Token)'
        cst = parse_sxpr('(Token (:Whitespace " ") (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = parse_sxpr('(Token (:Whitespace " ") (Deeper (:Whitespace " ")) '
                               '(:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = parse_sxpr('(Token (:Re ein) (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") >= 0

    def test_rstrip(self):
        cst = parse_sxpr('(Token (:Re test) (:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0, cst.as_sxpr()
        sxpr1 = cst.as_sxpr()
        rstrip([cst])
        assert sxpr1 == cst.as_sxpr()
        cst = parse_sxpr('(Token)')
        rstrip([cst])
        assert cst.as_sxpr() == '(Token)'
        cst = parse_sxpr('(Token  (:Re test) (:Whitespace " ") (:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = parse_sxpr('(Token  (:Re test) (:Whitespace " ") (Deeper (:Whitespace " ")) '
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
        transformation([ZOMBIE_NODE])
        assert save == {'a', 'b', 'c'}

    def test_parameter_set_expansion2(self):
        save = None
        @transformation_factory(tuple)
        def parameterized_transformation(context: List[Node], parameters: Tuple[str]):
            nonlocal save
            save = parameters
        transformation = parameterized_transformation('a', 'b', 'c')
        transformation([ZOMBIE_NODE])
        assert save == ('a', 'b', 'c'), str(save)


class TestConditionalTransformations:
    """Tests conditional transformations."""

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



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())