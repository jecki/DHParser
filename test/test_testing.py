#!/usr/bin/env python3

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
import sys
from functools import partial

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.syntaxtree import parse_sxpr, flatten_sxpr, TOKEN_PTYPE
from DHParser.transform import traverse, remove_whitespace, remove_empty, \
    replace_by_single_child, reduce_single_child, flatten
from DHParser.dsl import grammar_provider
from DHParser.error import Error, PARSER_LOOKAHEAD_FAILURE_ONLY, PARSER_LOOKAHEAD_MATCH_ONLY, \
    MANDATORY_CONTINUATION_AT_EOF
from DHParser.testing import get_report, grammar_unit, unit_from_file, \
    clean_report
from DHParser.trace import set_tracer, trace_history


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
        self.save_dir = os.getcwd()
        os.chdir(scriptpath)
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
        os.chdir(self.save_dir)

    def test_unit_from_config_file(self):
        unit = unit_from_file('configfile_test_1.ini')
        assert list(unit.keys()) == ['ParserA']
        assert list(unit['ParserA'].keys()) == ['match', 'fail'], str(list(unit['ParserA'].keys()))
        assert list(unit['ParserA']['match'].keys()) == ['M1', 'M2', 'M3', 'M4']
        assert list(unit['ParserA']['fail'].keys()) == ['F1']
        testcase = unit['ParserA']['match']['M4']
        lines = testcase.split('\n')
        assert len(lines[2]) - len(lines[2].lstrip()) == 4

        unit = unit_from_file('configfile_test_2.ini')
        txt = unit['BedeutungsPosition']['match']['M1']
        txt.split('\n')
        for line in txt:
            assert line.rstrip()[0:1] != ' '

        unit = unit_from_file('configfile_test_3.ini')


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
    "formula": [remove_empty, remove_whitespace],
    "term, expr": [remove_empty, remove_whitespace, replace_by_single_child, flatten],
    "factor": [remove_empty, remove_whitespace, reduce_single_child],
    (TOKEN_PTYPE): [remove_empty, remove_whitespace, reduce_single_child],
    "*": [remove_empty, remove_whitespace, replace_by_single_child]
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
                '1*': "(term (factor 4) (:Text *) (factor 5))",
                2: "(term (factor 20) (:Text /) (factor 4))",
                3: "(term (term (factor 20) (:Text /) (factor 4)) (:Text *) (factor 3))"
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
                1: "(term (factor 4) (:Text *) (factor 5))",
                2: "(term (factor 20) (:Text /) (factor 4))",
                3: "(term (term (factor 19) (:Text /) (factor 4)) (:Text *) (factor 3))"  # error 19 != 20
            },
            "fail": {
                4: "4 * 5",     # error: this should match
                5: "20 / 4 - 3"
            }
        }
    }

    def setup(self):
        self.save_dir = os.getcwd()
        os.chdir(scriptpath)

    def teardown(self):
        clean_report('REPORT_TestGrammarTest')
        os.chdir(self.save_dir)

    def test_testing_grammar(self):
        parser_fac = grammar_provider(ARITHMETIC_EBNF)
        trans_fac = lambda : ARITHMETIC_EBNFTransform
        # reset_unit(self.cases)
        errata = grammar_unit(self.cases, parser_fac, trans_fac, 'REPORT_TestGrammarTest')
        assert errata, "Unknown parser, but no error message!?"
        report = get_report(self.cases)
        assert report.find('### CST') >= 0
        errata = grammar_unit(self.failure_cases, parser_fac, trans_fac, 'REPORT_TestGrammarTest')
        assert len(errata) == 3, str(errata)

    def test_fail_failtest(self):
        """Failure test should not pass if it failed because the parser is unknown."""
        fcases = {}
        fcases['berm'] = {}
        fcases['berm']['fail'] = self.failure_cases['term']['fail']
        errata = grammar_unit(fcases,
                              grammar_provider(ARITHMETIC_EBNF),
                              lambda : ARITHMETIC_EBNFTransform,
                              'REPORT_TestGrammarTest')
        assert errata


class TestLookahead:
    """
    Testing of Expressions with trailing Lookahead-Parser.
    """
    EBNF = r"""
        document = { category | entry } { LF }
        category = { LF } sequence_of_letters { /:/ sequence_of_letters } /:/ §&(LF sequence_of_letters) 
        entry = { LF } sequence_of_letters !/:/
        sequence_of_letters = /[A-Za-z0-9 ]+/
        LF = / *\n/
    """

    cases = {
        "category": {
            "match": {
                1: """Mountains: big:
                          K2""",  # case 1: matches only with lookahead (but should not fail in a test)
                2: """Rivers:""", # case 2: lookahaead failure occurs at end of file and is mandatory. (should not fail as a test)
                3: """Mountains: big:"""  # same here
            },
            "fail": {
                6: """Mountains: big: """
            }
        }
    }

    fail_cases = {
        "category": {
            "match": {
                1: """Mountains: b""",  # stop sign ":" is missing
                2: """Rivers: 
                         # not allowed""",
                2: """Mountains:        
                          K2
                      Rivers:"""  # lookahead only covers K2
            },
            "fail": {
                1: """Mountains: big:
                          K2"""
            }
        }
    }

    grammar_fac = grammar_provider(EBNF)
    trans_fac = lambda: partial(traverse, processing_table={"*": [flatten, remove_empty]})

    def setup(self):
        self.save_dir = os.getcwd()
        os.chdir(scriptpath)

    def teardown(self):
        clean_report('REPORT_TestLookahead')
        os.chdir(self.save_dir)

    def test_selftest(self):
        doc = """
            Mountains: big:
                Mount Everest
                K2
            Mountains: medium:
                Denali
                Alpomayo
            Rivers:
                Nile   
            """
        grammar = TestLookahead.grammar_fac()
        cst = grammar(doc)
        assert not cst.error_flag

    def test_unit_lookahead(self):
        gr = TestLookahead.grammar_fac()
        set_tracer(gr, trace_history)
        # Case 1: Lookahead string is part of the test case; parser fails but for the lookahead
        result = gr(self.cases['category']['match'][1], 'category')
        assert any(e.code in (PARSER_LOOKAHEAD_FAILURE_ONLY,
                              PARSER_LOOKAHEAD_MATCH_ONLY)
                   for e in result.errors), str(result.errors)
        # Case 2: Lookahead string is not part of the test case; parser matches but for the mandatory continuation
        result = gr(self.cases['category']['match'][2], 'category')
        assert any(e.code == MANDATORY_CONTINUATION_AT_EOF for e in result.errors)
        errata = grammar_unit(self.cases, TestLookahead.grammar_fac, TestLookahead.trans_fac,
                              'REPORT_TestLookahead')
        assert not errata, str(errata)
        errata = grammar_unit(self.fail_cases, TestLookahead.grammar_fac, TestLookahead.trans_fac,
                              'REPORT_TestLookahead')
        assert errata


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
