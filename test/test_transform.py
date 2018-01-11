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

import copy
import sys

sys.path.extend(['../', './'])

from DHParser.syntaxtree import mock_syntax_tree
from DHParser.transform import traverse, reduce_single_child, remove_whitespace, \
    traverse_locally, collapse, lstrip, rstrip


class TestRemoval:
    """Tests removing transformations."""

    def test_lstrip(self):
        cst = mock_syntax_tree('(Token (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        sxpr1 = cst.as_sxpr()
        lstrip([cst])
        assert sxpr1 == cst.as_sxpr()
        cst = mock_syntax_tree('(Token)')
        lstrip([cst])
        assert cst.as_sxpr() == '(Token)'
        cst = mock_syntax_tree('(Token (:Whitespace " ") (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = mock_syntax_tree('(Token (:Whitespace " ") (Deeper (:Whitespace " ")) '
                               '(:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = mock_syntax_tree('(Token (:Re ein) (:Whitespace " ") (:Re test))')
        lstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") >= 0

    def test_rstrip(self):
        cst = mock_syntax_tree('(Token (:Re test) (:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0, cst.as_sxpr()
        sxpr1 = cst.as_sxpr()
        rstrip([cst])
        assert sxpr1 == cst.as_sxpr()
        cst = mock_syntax_tree('(Token)')
        rstrip([cst])
        assert cst.as_sxpr() == '(Token)'
        cst = mock_syntax_tree('(Token  (:Re test) (:Whitespace " ") (:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0
        cst = mock_syntax_tree('(Token  (:Re test) (:Whitespace " ") (Deeper (:Whitespace " ")) '
                               '(:Whitespace " "))')
        rstrip([cst])
        assert cst.as_sxpr().find(":Whitespace") < 0, cst.as_sxpr()


class TestConditionalTransformations:
    """Tests conditional transformations."""

    def test_traverse_locally(self):
        cst = mock_syntax_tree("""
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