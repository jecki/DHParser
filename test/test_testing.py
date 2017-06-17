#!/usr/bin/python3

"""test_parsers.py - tests of the parsers-module of DHParser 

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

import sys
from functools import partial

sys.path.extend(['../', './'])

from DHParser.toolkit import compact_sexpr
from DHParser.syntaxtree import traverse, remove_expendables, \
    replace_by_single_child, reduce_single_child, flatten, TOKEN_PTYPE
from DHParser.dsl import parser_factory
from DHParser.testing import grammar_unit, mock_syntax_tree

ARITHMETIC_EBNF = """
    @ whitespace = linefeed
    formula = [ //~ ] expr
    expr = expr ("+"|"-") term | term
    term = term ("*"|"/") factor | factor
    factor = /[0-9]+/~
    # example:  "5 + 3 * 4"
    """


ARITHMETIC_EBNF_transformation_table = {
    # AST Transformations for the DSL-grammar
    "formula": [remove_expendables],
    "term, expr": [replace_by_single_child, flatten],
    "factor": [remove_expendables, reduce_single_child],
    (TOKEN_PTYPE): [remove_expendables, reduce_single_child],
    "*": [remove_expendables, replace_by_single_child]
}


ARITHMETIC_EBNFTransform = partial(traverse, processing_table=ARITHMETIC_EBNF_transformation_table)


class TestGrammarTest:
    cases = {
        "factor": {
            "match": {
                1: "0",
                2: "314",
            },
            "fail": {
                3: "21F",
                4: "G123"
            }
        },
        "term": {
            "match": {
                1: "4 * 5",
                2: "20 / 4",
                3: "20 / 4 * 3"
            },
            "ast": {
                1: "(term (factor 4) (:Token *) (factor 5))",
                2: "(term (factor 20) (:Token /) (factor 4))",
                3: "(term (term (factor 20) (:Token /) (factor 4)) (:Token *) (factor 3))"
            },
            "fail": {
                4: "4 + 5",
                5: "20 / 4 - 3"
            }
        }
    }

    failure_cases = {
        "term": {
            "match": {
                1: "4 + 5",     # error: this should fail
                2: "20 / 4",
                3: "20 / 4 * 3"
            },
            "ast": {
                1: "(term (factor 4) (:Token *) (factor 5))",
                2: "(term (factor 20) (:Token /) (factor 4))",
                3: "(term (term (factor 19) (:Token /) (factor 4)) (:Token *) (factor 3))"  # error 19 != 20
            },
            "fail": {
                4: "4 * 5",     # error: this should match
                5: "20 / 4 - 3"
            }
        }
    }

    def test_testing_grammar(self):
        parser_fac = parser_factory(ARITHMETIC_EBNF)
        trans_fac = lambda : ARITHMETIC_EBNFTransform
        errata = grammar_unit(self.cases, parser_fac, trans_fac)
        assert not errata, str(errata)
        errata = grammar_unit(self.failure_cases, parser_fac, trans_fac)
        # for e in errata:
        #     print(e)
        assert len(errata) == 3


class TestSExpr:
    """
    Tests for S-expression handling.
    """
    def test_compact_sexpr(self):
        assert compact_sexpr("(a\n    (b\n        c\n    )\n)\n") == "(a (b c))"

    def test_mock_syntax_tree(self):
        sexpr = '(a (b c) (d e) (f (g h)))'
        tree = mock_syntax_tree(sexpr)
        assert compact_sexpr(tree.as_sexpr().replace('"', '')) == sexpr

        # test different quotation marks
        sexpr = '''(a (b """c""" 'k' "l") (d e) (f (g h)))'''
        sexpr_stripped = '(a (b c k l) (d e) (f (g h)))'
        tree = mock_syntax_tree(sexpr)
        assert compact_sexpr(tree.as_sexpr().replace('"', '')) == sexpr_stripped

        sexpr_clean = '(a (b "c" "k" "l") (d "e") (f (g "h")))'
        tree = mock_syntax_tree(sexpr_clean)
        assert compact_sexpr(tree.as_sexpr()) == sexpr_clean

        tree = mock_syntax_tree(sexpr_stripped)
        assert compact_sexpr(tree.as_sexpr()) == '(a (b "c k l") (d "e") (f (g "h")))'

    def test_mock_syntax_tree_with_classes(self):
        sexpr = '(a:class1 (b:class2 x) (:class3 y) (c z))'
        tree = mock_syntax_tree(sexpr)
        assert tree.tag_name == 'a'
        assert tree.result[0].tag_name == 'b'
        assert tree.result[1].tag_name == ':class3'
        assert tree.result[2].tag_name == 'c'


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
