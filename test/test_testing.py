#!/usr/bin/python3

"""test_testing.py - tests of the testing-module of DHParser

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

import os
import re
import sys
from functools import partial

sys.path.extend(['../', './'])

from DHParser.syntaxtree import parse_sxpr, flatten_sxpr, TOKEN_PTYPE
from DHParser.transform import traverse, remove_expendables, \
    replace_by_single_child, reduce_single_child, flatten
from DHParser.dsl import grammar_provider
from DHParser.testing import get_report, grammar_unit, unit_from_configfile, \
    reset_unit

CFG_FILE_1 = '''
# a comment

[match:ParserA]
M1: test
M2: 'test'
M3: "test"
M4: """
    test
        proper multiline indent?
    """

# another comment

[fail:ParserA]
F1: test
'''

CFG_FILE_2 = '''
[match:LB]
1:  """
    """

[fail:LB]
10: """ """

[match:BedeutungsPosition]
M1: """
    BEDEUTUNG
    LAT pannus, faciale, sudarium
    DEU Gesichts-, Schweißtuch {usu liturg.: de re v. p. 32, 63}:"""
'''

CFG_FILE_3 = r'''
[match:paragraph]
1 : Im allgemeinen werden die Bewohner Göttingens eingeteilt in Studenten,
    Professoren, Philister und Vieh; welche vier Stände doch nichts weniger
    als streng geschieden sind. Der Viehstand ist der bedeutendste.

2 : Paragraphs may contain {\em inline blocks} as well as \emph{inline commands}
    and also special \& characters.

[fail:paragraph]
20: Paragraphs are separated by gaps.

    Like this one.

21: \begin{enumerate}

[match:csttest]
M1*: """Trigger CST-output with an asterix!"""
'''


class TestTestfiles:
    def setup(self):
        with open('configfile_test_1.ini', 'w', encoding="utf-8") as f:
            f.write(CFG_FILE_1)
        with open('configfile_test_2.ini', 'w', encoding="utf-8") as f:
            f.write(CFG_FILE_2)
        with open('configfile_test_3.ini', 'w', encoding="utf-8") as f:
            f.write(CFG_FILE_3)

    def teardown(self):
        os.remove('configfile_test_1.ini')
        os.remove('configfile_test_2.ini')
        os.remove('configfile_test_3.ini')

    def test_unit_from_config_file(self):
        unit = unit_from_configfile('configfile_test_1.ini')
        assert list(unit.keys()) == ['ParserA']
        assert list(unit['ParserA'].keys()) == ['match', 'fail'], str(list(unit['ParserA'].keys()))
        assert list(unit['ParserA']['match'].keys()) == ['M1', 'M2', 'M3', 'M4']
        assert list(unit['ParserA']['fail'].keys()) == ['F1']
        testcase = unit['ParserA']['match']['M4']
        lines = testcase.split('\n')
        assert len(lines[2]) - len(lines[2].lstrip()) == 4

        unit = unit_from_configfile('configfile_test_2.ini')
        txt = unit['BedeutungsPosition']['match']['M1']
        txt.split('\n')
        for line in txt:
            assert line.rstrip()[0:1] != ' '

        unit = unit_from_configfile('configfile_test_3.ini')


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
                '1*': "4 * 5",
                2: "20 / 4",
                3: "20 / 4 * 3"
            },
            "ast": {
                '1*': "(term (factor 4) (:Token *) (factor 5))",
                2: "(term (factor 20) (:Token /) (factor 4))",
                3: "(term (term (factor 20) (:Token /) (factor 4)) (:Token *) (factor 3))"
            },
            "fail": {
                4: "4 + 5",
                5: "20 / 4 - 3"
            }
        },
        "no_match_tests_specified": {
            "fail": {
                1: "+ 4 5"
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

    def teardown(self):
        if os.path.exists('REPORT'):
            files = os.listdir('REPORT')
            flag = False
            for file in files:
                if re.match(r'unit_test_\d+\.md', file):
                    os.remove(os.path.join('REPORT', file))
                else:
                    flag = True
            if not flag:
                os.rmdir('REPORT')

    def test_testing_grammar(self):
        parser_fac = grammar_provider(ARITHMETIC_EBNF)
        trans_fac = lambda : ARITHMETIC_EBNFTransform
        # reset_unit(self.cases)
        errata = grammar_unit(self.cases, parser_fac, trans_fac)
        assert not errata, str(errata)
        report = get_report(self.cases)
        assert report.find('### CST') >= 0
        errata = grammar_unit(self.failure_cases, parser_fac, trans_fac)
        # for e in errata:
        #     print(e)
        assert len(errata) == 3, str(errata)

    # def test_get_report(self):
    #     parser_fac = grammar_provider(ARITHMETIC_EBNF)
    #     trans_fac = lambda : ARITHMETIC_EBNFTransform
    #     reset_unit(self.cases)
    #     grammar_unit(self.cases, parser_fac, trans_fac)
    #     report = get_report(self.cases)
    #     assert report.find('### CST') >= 0


class TestSExpr:
    """
    Tests for S-expression handling.
    """
    def test_compact_sexpr(self):
        assert flatten_sxpr("(a\n    (b\n        c\n    )\n)\n") == "(a (b c))"

    def test_mock_syntax_tree(self):
        sexpr = '(a (b c) (d e) (f (g h)))'
        tree = parse_sxpr(sexpr)
        assert flatten_sxpr(tree.as_sxpr().replace('"', '')) == sexpr

        # test different quotation marks
        sexpr = '''(a (b """c""" 'k' "l") (d e) (f (g h)))'''
        sexpr_stripped = '(a (b c k l) (d e) (f (g h)))'
        tree = parse_sxpr(sexpr)
        assert flatten_sxpr(tree.as_sxpr().replace('"', '')) == sexpr_stripped

        sexpr_clean = '(a (b "c" "k" "l") (d "e") (f (g "h")))'
        tree = parse_sxpr(sexpr_clean)
        assert flatten_sxpr(tree.as_sxpr()) == sexpr_clean

        tree = parse_sxpr(sexpr_stripped)
        assert flatten_sxpr(tree.as_sxpr()) == '(a (b "c k l") (d "e") (f (g "h")))'

    def test_mock_syntax_tree_with_classes(self):
        sexpr = '(a:class1 (b:class2 x) (:class3 y) (c z))'
        tree = parse_sxpr(sexpr)
        assert tree.tag_name == 'a'
        assert tree.result[0].tag_name == 'b'
        assert tree.result[1].tag_name == ':class3'
        assert tree.result[2].tag_name == 'c'


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
