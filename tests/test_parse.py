#!/usr/bin/env python3

"""test_parse.py - tests of the parsers-module of DHParser

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
import os
import sys
from functools import partial
from typing import List, Tuple

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import get_config_value, set_config_value
from DHParser.toolkit import compile_python_object, re
from DHParser.log import is_logging, log_ST, log_parsing_history, start_logging
from DHParser.error import Error, is_error, add_source_locations, MANDATORY_CONTINUATION, \
    MALFORMED_ERROR_STRING, MANDATORY_CONTINUATION_AT_EOF, RESUME_NOTICE, PARSER_STOPPED_BEFORE_END, \
    PARSER_NEVER_TOUCHES_DOCUMENT, CAPTURE_DROPPED_CONTENT_WARNING, \
    MANDATORY_CONTINUATION_AT_EOF_NON_ROOT, ErrorCode
from DHParser.parse import ParserError, Parser, Grammar, Forward, TKN, ZeroOrMore, RE, \
    RegExp, Lookbehind, NegativeLookahead, OneOrMore, Series, Alternative, \
    Interleave, CombinedParser, Text, EMPTY_NODE, Capture, Drop, Whitespace, \
    GrammarError, Counted, Always, INFINITE, longest_match, extract_error_code
from DHParser import compile_source
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler, \
    parse_ebnf, DHPARSER_IMPORTS, compile_ebnf
from DHParser.dsl import grammar_provider, create_parser
from DHParser.preprocess import gen_neutral_srcmap_func
from DHParser.nodetree import Node, parse_sxpr
from DHParser.stringview import StringView
from DHParser.trace import set_tracer, trace_history, resume_notices_on



class TestWhitespace:
    # TODO: add test cases here
    def test_whitespace_comment_mangling(self):
        pass

    def test_non_empty_derivation(self):
        pass


class TestParserError:
    def test_parser_error_str(self):
        parser = Parser()
        parser.grammar = Grammar()
        parser.grammar.document__ = StringView('Beispiel')
        pe = ParserError(parser, Node('TAG', 'test').with_pos(0), len('test'),
                         0, None, first_throw=True)
        assert str(pe).find('Beispiel') >= 0 and str(pe).find('TAG') >= 0

    def test_false_lookahead_only_message(self):
        """PARSER_LOOKAHEAD_*_ONLY errors must not be reported if there
        no lookahead parser in the history!"""
        lang = """
        word = letters { letters | `-` letters }
        letters = /[A-Za-z]+/
        """
        gr = grammar_provider(lang)()
        set_tracer(gr, trace_history)
        st = gr('hard-time')
        assert not st.errors
        st = gr('hard-')
        assert st.errors and not any(e.code == 1045 for e in st.errors)


class TestParserClass:
    def test_apply(self):
        minilang ="""
            expr = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        gr = grammar_provider(minilang)()
        l = []
        def visitor(context: List[Parser]):
            p = context[-1]
            l.append(p.pname + p.ptype)
        gr.root__.apply(visitor)
        s1 = ", ".join(l)
        l = []
        gr.root__.apply(visitor)
        s2 = ", ".join(l)
        l = []
        gr.root__.apply(visitor)
        s3 = ", ".join(l)
        assert s1 == s2 == s3

    def test_symbol(self):
        class MyGrammar(Grammar):
            wrong = Text('wrong')
            word = OneOrMore(wrong) + Whitespace(r'\s*') + OneOrMore(RegExp(r'\w+'))
            root__ = word
        gr = MyGrammar()
        regex = gr['word'].parsers[-1].parser
        result = gr.associated_symbol__(regex).symbol
        assert result == 'word', result


class TestInfiLoopsAndRecursion:
    def setup(self):
        pass
        # set_config_value('history_tracking', True)
        # set_config_value('resume_notices', True)
        # start_logging('LOGS')

    def test_very_simple(self):
        minilang = """
            term = term (`*`|`/`) factor | factor
            factor = /[0-9]+/
            """
        grammar_factory = grammar_provider(minilang)
        parser = grammar_factory()
        snippet = "5*4*3*2"
        # set_tracer(parser, trace_history)
        st = parser(snippet)
        if is_logging():
            log_ST(st, 'test_LeftRecursion_very_simple.cst')
            log_parsing_history(parser, 'test_LeftRecursion_very_simple')
        assert not is_error(st.error_flag), str(st.errors)
        st = parser("1*2*3*4*5*6*7*8*9")
        # if is_logging():
        #     log_ST(st, 'test_LeftRecursion_very_simple_2.cst')
        #     log_parsing_history(parser, 'test_LeftRecursion_very_simple_2')
        assert not is_error(st.error_flag)

    def test_direct_left_recursion1(self):
        minilang = """@literalws = right
            expr = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        snippet = "9 + 8 + 7 + 6 + 5 + 3 * 4"
        parser = grammar_provider(minilang)()
        assert parser
        syntax_tree = parser(snippet)
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_direct1.cst")
            log_parsing_history(parser, "test_LeftRecursion_direct1")
        assert not is_error(syntax_tree.error_flag), str(syntax_tree.errors_sorted)
        assert snippet == syntax_tree.content, str(syntax_tree)

    def test_direct_left_recursion2(self):
        minilang = """@literalws = right
            expr = ex
            ex   = expr ("+"|"-") term | term
            term = tr
            tr   = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        snippet = "9 + 8 + 7 + 6 + 5 + 3 * 4"
        parser = grammar_provider(minilang)()
        assert parser
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        assert snippet == syntax_tree.content
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_direct2.cst")
            log_parsing_history(parser, "test_LeftRecursion_direct2")

    def test_indirect_left_recursion1(self):
        minilang = """@literalws = right
            Expr    = //~ (Product | Sum | Value)
            Product = Expr { ('*' | '/') Expr }+
            Sum     = Expr { ('+' | '-') Expr }+
            Value   = /[0-9.]+/~ | '(' §Expr ')'
            """
        parser = grammar_provider(minilang)()
        snippet = "8 * 4"
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        snippet = "7 + 8 * 4"
        syntax_tree = parser(snippet)
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_indirect1.cst")
            log_parsing_history(parser, "test_LeftRecursion_indirect1")
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        snippet = "9 + 8 * (4 + 3)"
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        assert snippet == syntax_tree.content
        snippet = "9 + 8 * (4 - 3 / (5 - 1))"
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        assert snippet == syntax_tree.content
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_indirect1.cst")
            log_parsing_history(parser, "test_LeftRecursion_indirect1")

    # BEWARE: EXPERIMENTAL TEST can be long running
    def test_indirect_left_recursion2(self):
        arithmetic_syntax = r"""@literalws = right
            expression     = addition | subtraction  # | term
            addition       = (expression | term) "+" (expression | term)
            subtraction    = (expression | term) "-" (expression | term)
            term           = multiplication | division  # | factor
            multiplication = (term | factor) "*" (term | factor)
            division       = (term | factor) "/" (term | factor)
            factor         = [SIGN] ( NUMBER | VARIABLE | group ) { VARIABLE | group }
            group          = "(" expression ")"
            SIGN           = /[+-]/
            NUMBER         = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
            VARIABLE       = /[A-Za-z]/~
            """
        arithmetic = grammar_provider(arithmetic_syntax)()
        assert arithmetic
        syntax_tree = arithmetic("(a + b) * (a - b)")
        assert syntax_tree.errors
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_indirect2.cst")
            log_parsing_history(arithmetic, "test_LeftRecursion_indirect2")

    def test_indirect_left_recursion3(self):
        arithmetic_syntax = r"""@literalws = right
            expression     = addition | subtraction | term
            addition       = (expression | term) "+" (expression | term)
            subtraction    = (expression | term) "-" (expression | term)
            term           = multiplication | division | factor
            multiplication = (term | factor) "*" (term | factor)
            division       = (term | factor) "/" (term | factor)
            factor         = [SIGN] ( NUMBER | VARIABLE | group ) { VARIABLE | group }
            group          = "(" expression ")"
            SIGN           = /[+-]/
            NUMBER         = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
            VARIABLE       = /[A-Za-z]/~
            """
        arithmetic = grammar_provider(arithmetic_syntax)()
        assert arithmetic
        syntax_tree = arithmetic("(a + b) * (a - b)")
        assert not syntax_tree.errors
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_indirect3.cst")
            log_parsing_history(arithmetic, "test_LeftRecursion_indirect3")


    def test_break_inifnite_loop_ZeroOrMore(self):
        forever = ZeroOrMore(RegExp(''))
        result = Grammar(forever)('')  # infinite loops will automatically be broken
        assert repr(result) == "Node('root', '')", repr(result)

    def test_break_inifnite_loop_OneOrMore(self):
        forever = OneOrMore(RegExp(''))
        result = Grammar(forever)('')  # infinite loops will automatically be broken
        assert repr(result) == "Node('root', '')", repr(result)

    def test_break_infinite_loop_Counted(self):
        forever = Counted(Always(), (0, INFINITE))
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)
        forever = Counted(Always(), (5, INFINITE))
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)
        forever = Counted(Always(), (INFINITE, INFINITE))
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)
        forever = Counted(Always(), (1000, INFINITE - 1))
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)

    def test_break_infinite_loop_Interleave(self):
        forever = Interleave(Always(), repetitions=[(0, INFINITE)])
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)
        forever = Interleave(Always(), Always(),
                             repetitions=[(5, INFINITE), (INFINITE, INFINITE)])
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)
        forever = Interleave(Always(), repetitions=[(1000, INFINITE - 1)])
        result = Grammar(forever)('')  # if this takes very long, something is wrong
        assert repr(result) == "Node('root', '')", repr(result)

    # def test_infinite_loops(self):
    #     minilang = """forever = { // } \n"""
    #     try:
    #         parser_class = grammar_provider(minilang)
    #     except CompilationError as error:
    #         assert all(e.code == INFINITE_LOOP for e in error.errors)
    #     save = get_config_value('static_analysis')
    #     set_config_value('static_analysis', 'late')
    #     provider = grammar_provider(minilang)
    #     try:
    #         parser = provider()
    #     except GrammarError as error:
    #         assert error.errors[0][2].code == INFINITE_LOOP
    #     set_config_value('static_analysis', 'none')
    #     parser = provider()
    #     snippet = " "
    #     syntax_tree = parser(snippet)
    #     assert any(e.code == INFINITE_LOOP for e in syntax_tree.errors)
    #     res = parser.static_analysis__()
    #     assert res and res[0][2].code == INFINITE_LOOP
    #     minilang = """not_forever = { / / } \n"""
    #     parser = grammar_provider(minilang)()
    #     res = parser.static_analysis__()
    #     assert not res
    #     set_config_value('static_analysis', save)


# class TestStaticAnalysis:
#     def test_alternative(self):
#         lang = 'doc = "A" | "AB"'
#         parser = create_parser(lang)


class TestFlowControl:
    t1 = """
         All work and no play
         makes Jack a dull boy
         END
         """
    t2 = "All word and not play makes Jack a dull boy END\n"

    def test_lookbehind(self):
        ws = RegExp(r'\s*');  ws.pname = "ws"
        end = RegExp("END");  end.pname = "end"
        doc_end = Lookbehind(RegExp('\\s*?\\n')) + end
        word = RegExp(r'\w+');  word.pname = "word"
        sequence = OneOrMore(NegativeLookahead(end) + word + ws)
        document = ws + sequence + doc_end + ws
        parser = Grammar(document)
        cst = parser(self.t1)
        assert not cst.error_flag, cst.as_sxpr()
        cst = parser(self.t2)
        assert cst.error_flag, cst.as_sxpr()

        cst = parser(self.t2, parser['ws'], complete_match=False)
        assert cst.did_match() and cst.strlen() == 0 and not cst.errors
        cst = parser(self.t2, parser['word'], complete_match=False)
        assert cst.did_match() and cst.content == "All" and not cst.errors
        cst = parser(self.t2, parser['end'], complete_match=False)
        assert not cst.did_match()


    def test_lookbehind_indirect(self):
        class LookbehindTestGrammar(Grammar):
            parser_initialization__ = ["upon instantiation"]
            ws = RegExp(r'\s*')
            end = RegExp('END')
            SUCC_LB = RegExp('\\s*?\\n')
            doc_end = Series(Lookbehind(SUCC_LB), end)
            word = RegExp(r'\w+')
            sequence = OneOrMore(Series(NegativeLookahead(end), word, ws))
            document = Series(ws, sequence, doc_end, ws)
            root__ = document

        parser = LookbehindTestGrammar()
        cst = parser(self.t1)
        assert not cst.error_flag, cst.as_sxpr()
        cst = parser(self.t2)
        assert cst.error_flag, cst.as_sxpr()


class TestRegex:
    def test_multilineRegex(self):
        mlregex = r"""
        regex =  /\w+    # one or more alphabetical characters including the underscore
                  [+]    # followed by a plus sign
                  \w*    # possibly followed by more alpha chracters/
        """
        result, messages, _ = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages, str(messages)
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node = parser('abc+def', parser.regex)
        assert not node.error_flag
        assert node.name == "regex"
        assert str(node) == 'abc+def'

    def test_multilineRegex_wo_Comments(self):
        mlregex = r"""
        regex =  /\w+
                  [+]
                  \w* /
        """
        result, messages, _ = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages, str(messages)
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node = parser('abc+def', parser.regex)
        assert not node.error_flag
        assert node.name == "regex"
        assert str(node) == 'abc+def'

    def test_ignore_case(self):
        mlregex = r"""
        @ ignorecase = True
        regex = /alpha/
        """
        result, messages, _ = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages
        grammar = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node = grammar('Alpha', grammar.regex)
        assert node
        assert node.strlen() == 5
        assert node.name == "regex"
        assert str(node) == 'Alpha'

        mlregex = r"""
        @ ignorecase = False
        regex = /alpha/
        """
        result, messages, _ = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages
        grammar = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node = grammar('Alpha', 'regex')
        assert node.error_flag and node.errors[0].code == 1040

    def test_token(self):
        tokenlang = r"""@literalws = right
            @whitespace = linefeed
            lang        = "" begin_token {/\w+/ ""} end_token
            begin_token = "\begin{document}"
            end_token   = "\end{document}"
            """
        testdoc = r"""
            \begin{document}
            test
            \end{document}
            """
        result, messages, _ = compile_source(
            tokenlang, None, get_ebnf_grammar(), get_ebnf_transformer(),
            get_ebnf_compiler("TokenTest"))
        assert result
        assert not messages, str(messages)
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        result = parser(testdoc)
        # log_parsing_history(parser, "test.log")
        assert not result.error_flag, str(result.errors_sorted)


class TestGrammar:
    grammar = r"""@whitespace = horizontal
    haupt        = textzeile LEERZEILE
    textzeile    = { WORT }+
    WORT         = /[^ \t]+/~
    LEERZEILE    = /\n[ \t]*(?=\n)/~
    """
    pyparser, messages, _ = compile_source(grammar, None, get_ebnf_grammar(),
                                           get_ebnf_transformer(), get_ebnf_compiler("PosTest"))
    assert pyparser, str(messages)
    assert not messages, str(messages)

    def test_pos_values_initialized(self):
        # checks whether pos values in the parsing result and in the
        # history record have been initialized
        grammar = compile_python_object(DHPARSER_IMPORTS + self.pyparser, r'\w+Grammar$')()
                                        # .format(dhparser_parentdir=repr('.')) + self.pyparser, r'\w+Grammar$')()
        grammar("no_file_name*")
        for record in grammar.history__:
            assert not record.node or record.node.pos >= 0

    def test_select_parsing(self):
        grammar = compile_python_object(
            DHPARSER_IMPORTS + self.pyparser,
            r'\w+Grammar$')()
        grammar("wort", "WORT")
        grammar("eine Zeile", "textzeile")
        grammar("kein Haupt", "haupt")
        grammar("so ist es richtig", "haupt")

    def test_grammar_subclassing(self):
        class Arithmetic(Grammar):
            r'''
            expression =  term  { ("+" | "-") term }
            term       =  factor  { ("*" | "/") factor }
            factor     =  INTEGER | "("  expression  ")"
            INTEGER    =  /\d+/~
            '''
            expression = Forward()
            INTEGER = RE('\\d+')
            factor = INTEGER | TKN("(") + expression + TKN(")")
            term = factor + ZeroOrMore((TKN("*") | TKN("/")) + factor)
            expression.set(term + ZeroOrMore((TKN("+") | TKN("-")) + term))
            root__ = expression

        grammar = Arithmetic()
        CST = grammar('3+4')
        assert not CST.error_flag, CST.as_sxpr()

    def test_incomplete_matching(self):
        """Tests whether the flag `complete_match` works as expected when
        calling a grammar object in order to parse a document."""
        gr = grammar_provider('word = ~/\\w+/\n')()
        st = gr('eins')
        assert not st.errors
        st = gr('eins zwei')
        assert st.errors[0].code == PARSER_STOPPED_BEFORE_END
        st = gr('eins zwei', complete_match=False)
        assert not st.errors

    def test_synonym(self):
        lang = r"""
            doc  = { word | number }
            word = /\w+/ S
            number = [VZ] /\d+/ S 
            S    = ~        # let S by a synonym for anonymous whitespace
            VZ   = "-"
        """
        gr = grammar_provider(lang)()
        st = gr('eins 1 zwei2drei 3')
        # set_config_value('compiled_EBNF_log', 'grammar.log')
        gr = grammar_provider("@drop = whitespace, strings" + lang)()
        st = gr('eins 1 zwei2drei 3')
        st = gr('-3')
        assert str(gr['S']) == "S = ~", str(gr['S'])

    def test_match_and_fullmatch(self):
        lang = r"""
            word = /[A-Za-z]+/
            number = /[0-9]+/
        """
        gr = create_parser(lang)
        assert gr.match('word', 'hallo123') == "hallo"
        assert gr.match('word', '') is None
        assert gr.match('word', '123') is None
        assert gr.match('word', 'hallo') == "hallo"

        assert gr.fullmatch('word', 'hallo123') is None
        assert gr.fullmatch('word', '') is None
        assert gr.fullmatch('word', '123') is None
        assert gr.fullmatch('word', 'hallo') == 'hallo'

        assert gr.match('number', 'hallo123') is None
        assert gr.match('number', '') is None
        assert gr.match('number', '123') == "123"
        assert gr.match('number', 'hallo') is None


class TestSeries:
    def test_non_mandatory(self):
        lang = """
        document = series | /.*/
        series = "A" "B" "C" "D"
        """
        parser = grammar_provider(lang)()
        st = parser("ABCD")
        assert not st.error_flag
        st = parser("A_CD")
        assert not st.error_flag
        st = parser("AB_D")
        assert not st.error_flag

    def test_mandatory(self):
        """Test for the §-operator. The Series-parser should raise an
        error for any non-match that occurs after the mandatory-operator.
        """
        lang = """
        document = series | /.*/
        series = "A" "B" §"C" "D"
        """
        parser = grammar_provider(lang)()
        st = parser("ABCD");  assert not st.error_flag
        st = parser("A_CD");  assert not st.error_flag
        st = parser("AB_D");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        assert str(st.errors_sorted[0]).find("series") >= 0
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION

    def test_series_composition(self):
        TA, TB, TC, TD, TE = (TKN(b) for b in "ABCDE")
        s1 = Series(TA, TB, TC, mandatory=2)
        s2 = Series(TD, TE)

        combined = Alternative(s1 + s2, RegExp('.*'))
        parser = Grammar(combined)
        st = parser("ABCDE");  assert not st.error_flag
        st = parser("A_CDE");  assert not st.error_flag
        st = parser("AB_DE");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        st = parser("ABC_E");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION

        combined = Alternative(s2 + s1, RegExp('.*'))
        parser = Grammar(combined)
        st = parser("DEABC");  assert not st.error_flag
        st = parser("_EABC");  assert not st.error_flag
        st = parser("D_ABC");  assert not st.error_flag
        st = parser("DE_BC");  assert not st.error_flag
        st = parser("DEA_C");  assert not st.error_flag
        st = parser("DEAB_");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION

    # def test_boundary_cases(self):
    #     lang = """
    #     document = series | §!single | /.*/
    #     series = "A" "B" §"C" "D"
    #     single = "E"
    #     """
    #     parser_class = grammar_provider(lang)
    #     parser = parser_class()
    #     print(parser.python_src__)
    #     print(parser_class.python_src__)

    def test_ebnf_serialization(self):
        ebnf_grammar = get_ebnf_grammar()
        # TODO: Add test here
        ebnf = ebnf_grammar.as_ebnf__()
        # print(ebnf)


class TestAllOfSomeOf:
    def test_allOf_order(self):
        """Test that parsers of an AllOf-List can match in arbitrary order."""
        prefixes = Interleave(TKN("A"), TKN("B"))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B A').content == 'B A'

    def test_allOf_completeness(self):
        """Test that an error is raised if not  all parsers of an AllOf-List
        match."""
        prefixes = Interleave(TKN("A"), TKN("B"))
        assert Grammar(prefixes)('B').error_flag

    def test_allOf_redundance(self):
        """Test that one and the same parser may be listed several times
        and must be matched several times accordingly."""
        prefixes = Interleave(TKN("A"), TKN("B"), TKN("A"))
        assert Grammar(prefixes)('A A B').content == 'A A B'
        assert Grammar(prefixes)('A B A').content == 'A B A'
        assert Grammar(prefixes)('B A A').content == 'B A A'
        assert Grammar(prefixes)('A B B').error_flag

    def test_someOf_order(self):
        """Test that parsers of an AllOf-List can match in arbitrary order."""
        prefixes = Interleave(TKN("A"), TKN("B"))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B A').content == 'B A'
        st = Grammar(prefixes)('B')
        assert st.error_flag
        prefixes = Interleave(TKN("B"), TKN("A"), repetitions=((0, 1), (0, 1)))
        assert Grammar(prefixes)('A B').content == 'A B'
        st = Grammar(prefixes)('B')
        assert not st.error_flag
        assert st.content == 'B'

    def test_someOf_redundance(self):
        """Test that one and the same parser may be listed several times
        and must be matched several times accordingly."""
        prefixes = Interleave(TKN("A"), TKN("B"), TKN("A"))
        assert Grammar(prefixes)('A A B').content == 'A A B'
        assert Grammar(prefixes)('A B A').content == 'A B A'
        assert Grammar(prefixes)('B A A').content == 'B A A'
        assert Grammar(prefixes)('A B B').error_flag


class TestInterleave:
    def test_interleave_most_simple(self):
        letterset = Interleave(Text("A"), Text("B"), Text("C"))
        gr = Grammar(letterset)
        st = gr('ABC')
        assert not st.errors, str(st.errors)
        assert st.content == "ABC"
        st = gr('BCA')
        assert not st.errors
        assert st.content == "BCA"
        st = gr('BCBA')
        assert st.errors
        st = gr('AB')
        assert st.errors

    def test_interleave(self):
        letterset = Interleave(Text("A"), Text("B"), Text("C"),
                               repetitions=[(1, 1000), (0, 1), (1, 1)])
        gr = Grammar(letterset)
        st = gr('AABC')
        assert not st.errors
        st = gr('BACAAA')
        assert not st.errors
        st = gr('ABCC')
        assert st.errors
        st = gr('AAACAAA')
        assert not st.errors
        st = gr('AAABAAA')
        assert st.errors


class TestErrorRecovery:
    def test_series_skip(self):
        lang = """
        document = series | /.*/
        @series_skip = /(?=[A-Z])/
        series = "A" "B" §"C" "D"
        """
        parser = grammar_provider(lang)()
        st = parser('AB_D')
        assert len(st.errors) == 1  # no additional "stopped before end"-error!
        resume_notices_on(parser)
        st = parser('AB_D')
        assert len(st.errors) == 2 and any(err.code == RESUME_NOTICE for err in st.errors)
        assert 'Skipping' in str(st.errors_sorted[1])

    def test_series_skip2(self):
        grammar = r"""
        @whitespace = vertical
        @literalws = right
        @document_skip = /\s+|(?=$)/
        document = { sentence § sentence_continuation }+ EOF
            sentence_continuation = &(sentence | EOF)
        @sentence_skip = /\s+|(?=\.|$)/
        sentence = { word § word_continuation }+ "."
            word_continuation = &(word | `.` | EOF)
        word = /[A-Za-z]+/~
        EOF = !/./ 
        """
        data = "Time is out of joint. Oh cursed spite that I was ever born to set it right."
        parser = grammar_provider(grammar)()
        st = parser(data)
        assert not st.errors, str(st.errors)
        data2 = data.replace('cursed', 'cur?ed')
        st = parser(data2)
        assert len(st.errors) == 1
        zombie = st.pick('ZOMBIE__')
        assert zombie.content == '?ed ', zombie.content

    def test_irrelevance_of_error_definition_order(self):
        lang = """
        document = series | /.*/
        series = "A" "B" §"C" "D"
        @series_skip = /(?=[A-Z])/
        @series_error = '', "Unerwartetes Zeichen"
        """
        parser = grammar_provider(lang)()
        st = parser('AB_D')
        assert len(st.errors) == 1  # no additional "stopped before end"-error!
        assert st.errors[0].message == "Unerwartetes Zeichen"
        resume_notices_on(parser)
        st = parser('AB_D')
        assert len(st.errors) == 2 and any(err.code == RESUME_NOTICE for err in st.errors)
        assert 'Skipping' in str(st.errors_sorted[1])

    def test_Interleave_skip(self):
        lang = """
        document = allof | /.*/
        @allof_skip = /[A-Z]/
        allof = "A" ° §"B" ° "C" ° "D"
        """
        parser = grammar_provider(lang)()
        st = parser('CADB')
        assert 'allof' in st and st['allof'].content == "CADB"
        st = parser('_BCD')
        assert st.equals(parse_sxpr('(document "_BCD")'))
        st = parser('_ABC')
        assert st.equals(parse_sxpr('(document "_ABC")'))
        st = parser('A_CD')
        assert st['allof'].content == "A_CD"
        st = parser('AB_D')
        assert st['allof'].content == "AB_D"
        st = parser('A__D')
        assert st['allof'].content == "A__D"
        st = parser('CA_D')
        assert st['allof'].content == "CA_D"
        st = parser('A_CB')
        assert st['allof'].content == "A_CB"
        st = parser('BC_A')
        assert 'allof' not in st


class TestPopRetrieve:
    mini_language = r"""
        document       = { text | codeblock }
        codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
        delimiter      = delimiter_sign  # never use delimiter between capture and pop except for retrieval!
        delimiter_sign = /`+/
        text           = /[^`]+/
        """
    mini_lang2 = r"""
        @braces_filter = matching_bracket()
        document       = { text | codeblock }
        codeblock      = braces { text | opening_braces | (!:braces closing_braces) } ::braces
        braces         = opening_braces
        opening_braces = /\{+/
        closing_braces = /\}+/
        text           = /[^{}]+/
        """
    mini_lang3 = r"""@literalws = right
        document       = { text | env }
        env            = (specialtag | opentag) text [ closespecial | closetag ]
        opentag        = "<" name ">"
        specialtag     = "<" /ABC/ !name ">"
        closetag       = close_slash | close_star
        close_slash    = "<" ::name "/>"
        close_star     = "<" ::name "*>"
        closespecial   = "<" /ABC/~ ">"
        name           = /\w+/~
        text           = /[^<>]+/
        """
    mini_lang4 = r"""@literalws = right
        document       = { text | env }
        env            = opentag document closetag
        opentag        = "<" name ">"
        closetag       = "</" :?name ">"
        name           = /\w+/~
        text           = /[^<>]+/        
    """

    def setup(self):
        self.minilang_parser = grammar_provider(self.mini_language)()
        self.minilang_parser2 = grammar_provider(self.mini_lang2)()
        self.minilang_parser3 = grammar_provider(self.mini_lang3)()
        self.minilang_parser4 = grammar_provider(self.mini_lang4)()

    @staticmethod
    def has_tag_name(node, name):
        return node.name == name # and not isinstance(node.parser, Retrieve)

    def test_capture_assertions(self):
        try:
            gr = Grammar(Capture(Drop(Whitespace(r'\s*'))))
            assert any(ae.error.code == CAPTURE_DROPPED_CONTENT_WARNING
                       for ae in gr.static_analysis_errors__), \
                "Dropped content warning expected"
        except GrammarError as ge:
            assert ge.errors and ge.errors[0][-1].code == CAPTURE_DROPPED_CONTENT_WARNING, \
                "Capture-dropped-content-Warning expected"
        try:
            _ = Grammar(Capture(Series(Text(' '), Drop(Whitespace(r'\s*')))))
            assert any(ae.error.code == CAPTURE_DROPPED_CONTENT_WARNING
                       for ae in gr.static_analysis_errors__), \
                "Dropped content warning expected"
        except GrammarError as ge:
            assert ge.errors and ge.errors[0][-1].code == CAPTURE_DROPPED_CONTENT_WARNING, \
                "Capture-dropped-content-Warning expected"
        cp = Capture(RegExp(r'\w+'))
        cp.pname = "capture"
        _ = Grammar(cp)

    def test_compile_mini_language(self):
        assert self.minilang_parser
        assert self.minilang_parser2
        assert self.minilang_parser3
        assert self.minilang_parser4

    def test_stackhandling(self):
        ambigous_opening = "<ABCnormal> normal tag <ABCnormal*>"
        syntax_tree = self.minilang_parser3(ambigous_opening)
        assert not syntax_tree.error_flag, str(syntax_tree.errors_sorted)

        ambigous_opening = "<ABCnormal> normal tag <ABCnormal/>"
        syntax_tree = self.minilang_parser3(ambigous_opening)
        assert not syntax_tree.error_flag, str(syntax_tree.errors_sorted)

        forgot_closing_tag = "<em> where is the closing tag?"
        syntax_tree = self.minilang_parser3(forgot_closing_tag)
        assert syntax_tree.error_flag, str(syntax_tree.errors_sorted)

        proper = "<em> has closing tag <em/>"
        syntax_tree = self.minilang_parser3(proper)
        assert not syntax_tree.error_flag, str(syntax_tree.errors_sorted)

        proper = "<em> has closing tag <em*>"
        syntax_tree = self.minilang_parser3(proper)
        assert not syntax_tree.error_flag, str(syntax_tree.errors_sorted)

    def test_optional_match(self):
        test1 = '<info>Hey, you</info>'
        st = self.minilang_parser4(test1)
        assert not st.error_flag, str(st.errors_sorted)
        test12 = '<info>Hey, <emph>you</emph></info>'
        st = self.minilang_parser4(test1)
        assert not st.error_flag
        test2 = '<info>Hey, you</>'
        # set_config_value('history_tracking', True)
        # set_tracer(self.minilang_parser4, trace_history)
        # start_logging('LOGS')
        st = self.minilang_parser4(test2)
        # log_parsing_history(self.minilang_parser4, "optional_match")
        assert not st.error_flag
        test3 = '<info>Hey, <emph>you</></>'
        st = self.minilang_parser4(test3)
        assert not st.error_flag
        test4 = '<info>Hey, <emph>you</></info>'
        st = self.minilang_parser4(test4)
        assert not st.error_flag, str(st.errors_sorted)

    def test_rollback_behaviour_of_optional_match(self):
        test1 = '<info>Hey, you</info*>'
        st = self.minilang_parser4(test1)
        assert not self.minilang_parser4.variables__['name']
        assert st.error_flag
        test2 = '<info>Hey, you</*>'
        st = self.minilang_parser4(test2)
        assert not self.minilang_parser4.variables__['name']
        assert st.error_flag

    def test_cache_neutrality_1(self):
        """Test that packrat-caching does not interfere with the variable-
        changing parsers: Capture and Retrieve."""
        lang = r"""@literalws = right
            text = opening closing
            opening = (unmarked_package | marked_package)
            closing = ::variable
            unmarked_package = package "."
            marked_package = package "*" "."
            package = "(" variable ")"
            variable = /\w+/~
            """
        case = "(secret)*. secret"
        gr = grammar_provider(lang)()
        st = gr(case)
        assert not st.error_flag, str(st.errors_sorted)

    def test_cache_neutrality_2(self):
        lang = r'''document = variantA | variantB
            variantA  = delimiter `X` ::delimiter `!` 
            variantB  = `A` delimiter ::delimiter `!` 
            delimiter = `A` | `X`
        '''
        gr = grammar_provider(lang)()
        case = 'AXA!'
        # st = gr(case)
        # assert not st.errors
        case = 'AXX!'
        # set_config_value('history_tracking', True)
        # start_logging('LOGS')
        # set_tracer(gr, trace_history)
        st = gr(case)
        # log_parsing_history(gr, 'test_cache_neutrality_2')
        assert not st.errors
        assert str(st) == "AXX!"

    def test_cache_neutrality_3(selfself):
        lang = r'''document = variantA | variantB
            variantA  = delimiter `X` [`---`] check ::delimiter `!` 
            variantB  = `A` delimiter [`---`] check ::delimiter `!`
            check = :delimiter 
            delimiter = `A` | `X`
        '''
        gr = grammar_provider(lang)()
        case = 'AX---XX!'
        # set_config_value('history_tracking', True)
        # start_logging('LOGS')
        # set_tracer(gr, trace_history)
        st = gr(case)
        # log_parsing_history(gr, 'test_cache_neutrality_3')
        assert not st.errors, str(st.errors)
        case = 'AXXX!'
        st = gr(case)
        assert not st.errors

    def test_single_line(self):
        teststr = "Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ende"
        syntax_tree = self.minilang_parser(teststr)
        assert not syntax_tree.errors_sorted, \
            ''.join(str(error) for error in syntax_tree.errors_sorted)
        matchf = partial(self.has_tag_name, name="delimiter")
        delim = str(next(syntax_tree.select_if(matchf)))
        pop = str(next(syntax_tree.select_if(matchf, reverse=True)))
        assert delim == pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_single_line.cst")

    def test_multi_line(self):
        teststr = """
            Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ebde

            Absatz ohne ``` codeblock, aber
            das stellt sich erst am Ende herause...

            Mehrzeliger ```code block
            """
        syntax_tree = self.minilang_parser(teststr)
        assert not syntax_tree.errors_sorted
        matchf = partial(self.has_tag_name, name="delimiter")
        delim = str(next(syntax_tree.select_if(matchf)))
        pop = str(next(syntax_tree.select_if(matchf, reverse=True)))
        assert delim == pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_multi_line.cst")

    def test_single_line_complement(self):
        teststr = "Anfang {{{code block }} <- keine Ende-Zeichen ! }}} Ende"
        syntax_tree = self.minilang_parser2(teststr)
        assert not syntax_tree.errors_sorted
        matchf = partial(self.has_tag_name, name="braces")
        delim = str(next(syntax_tree.select_if(matchf)))
        pop = str(next(syntax_tree.select_if(matchf, reverse=True)))
        assert len(delim) == len(pop)
        assert delim != pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_single_line.cst")

    def test_multi_line_complement(self):
        teststr = """
            Anfang {{{code block {{ <- keine Ende-Zeichen ! }}} Ende

            Absatz ohne {{{ codeblock, aber
            das stellt sich erst am Ende heraus...

            Mehrzeliger }}}code block
            """
        syntax_tree = self.minilang_parser2(teststr)
        assert not syntax_tree.errors_sorted
        matchf = partial(self.has_tag_name, name="braces")
        delim = str(next(syntax_tree.select_if(matchf)))
        pop = str(next(syntax_tree.select_if(matchf, reverse=True)))
        assert len(delim) == len(pop) and delim != pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_multi_line.cst")

    def test_autoretrieve(self):
        lang = r"""@literalws = right
            document   = { definition } § EOF
            definition = symbol :defsign value
            symbol     = /\w+/~                      
            defsign    = "=" | ":="
            value      = /\d+/~
            EOF        = !/./ [ :?defsign ]   # eat up captured defsigns
        """
        parser = grammar_provider(lang)()
        st = parser("X := 1")
        assert not st.error_flag, str(st.errors)
        st1 = st
        st = parser("")
        assert not st.error_flag

        lines = [line for line in lang.split('\n') if line.strip()]
        eof_line = lines.pop()
        lines.insert(2, eof_line)
        lang = '\n'.join(lines)
        parser = grammar_provider(lang)()
        st = parser("X := 1")
        assert not st.errors, str(st.errors)
        assert st.equals(st1)

        del lines[2]
        lines.insert(3, eof_line)
        lang = '\n'.join(lines)
        parser = grammar_provider(lang)()
        st = parser("X := 1")
        assert not st.errors
        assert st.equals(st1)

        # and, finally...
        lang_variant = r"""@literalws = right
            document   = { definition } § EOF
            symbol     = /\w+/~                      
            defsign    = "=" | ":="
            value      = /\d+/~
            EOF        = !/./ :?defsign   # eat up captured defsign, only if it has been retrieved
            definition = symbol :defsign value
        """
        parser = grammar_provider(lang_variant)()
        st = parser("X := 1")
        assert not st.errors, str(st.errors)
        assert st.equals(st1)
        st = parser('')
        # for e in st.errors: print(e)
        assert "'EOF = !/./ :?defsign' expected" in str(st.errors), st.as_sxpr()


class TestWhitespaceHandling:
    minilang = """@literalws = right
        doc = A B
        A = "A"
        B = "B"
        Rdoc = ar br
        ar = /A/
        br = /B/
        """
    gr = grammar_provider(minilang)()

    def test_token_whitespace(self):
        st = self.gr("AB", 'doc')
        assert not st.error_flag
        st = self.gr("A B", 'doc')
        assert not st.error_flag

    def test_regexp_whitespace(self):
        st = self.gr("AB", 'Rdoc')
        assert not st.error_flag
        st = self.gr("A B", 'Rdoc')
        assert st.error_flag


class TestErrorReporting:
    grammar = """
        root      = series alpha | anything
        series    = subseries &alpha
        subseries = alpha §beta
        alpha     = /[a-z]+/
        beta      = /[A-Z]+/
        anything  = /.*/
        """

    def setup(self):
        self.parser = grammar_provider(self.grammar)()

    def test_error_propagation(self):
        testcode1 = "halloB"
        testcode2 = "XYZ"
        testcode3 = "hallo "
        cst = self.parser(testcode1)
        assert not cst.error_flag, str(cst.errors_sorted)
        cst = self.parser(testcode2)
        assert not cst.error_flag
        cst = self.parser(testcode3)
        assert cst.error_flag


class TestBorderlineCases:
    def test_not_matching(self):
        minilang = """parser = /X/\n"""
        gr = grammar_provider(minilang)()
        cst = gr('X', 'parser')
        assert not cst.error_flag
        cst = gr(' ', 'parser')
        assert cst.error_flag and cst.errors_sorted[0].code == PARSER_STOPPED_BEFORE_END
        cst = gr('', 'parser')
        assert cst.error_flag and cst.errors_sorted[0].code == PARSER_STOPPED_BEFORE_END

    def test_matching(self):
        minilang = """parser = /.?/"""
        gr = grammar_provider(minilang)()
        cst = gr(' ', 'parser')
        assert not cst.error_flag
        cst = gr('  ', 'parser')
        assert cst.error_flag and cst.errors_sorted[0].code == PARSER_STOPPED_BEFORE_END
        cst = gr('', 'parser')
        assert not cst.error_flag


EBNF_with_Errors = r"""# Test code with errors. All places marked by a "$" should yield and error

@ comment    = /#.*(?:\n|$)/
@ whitespace = /\s*/
@ literalws  = right
@ disposable = pure_elem, EOF
@ drop       = whitespace, EOF


# re-entry-rules for resuming after parsing-error
@ definition_resume = /\n\s*(?=@|\w+\w*\s*=)/
@ directive_resume  = /\n\s*(?=@|\w+\w*\s*=)/

# specialized error messages for certain cases

@ definition_error  = /,/, 'Delimiter "," not expected in definition!\nEither this was meant to '
                           'be a directive and the directive symbol @ is missing\nor the error is '
                           'due to inconsistent use of the comma as a delimiter\nfor the elements '
                           'of a sequence.'

#: top-level

syntax     = [~//] { definition | directive } §EOF
definition = symbol §:DEF~ expression :ENDL~
directive  = "@" §symbol "="
             (regexp | literals | symbol)
             { "," (regexp | literals | symbol) }

#: components

expression = sequence { :OR~ sequence }
sequence   = ["§"] ( interleave | lookaround )
             { :AND~ ["§"] ( interleave | lookaround ) }
interleave = difference { "°" ["§"] difference }
lookaround = flowmarker § (oneormore | pure_elem)
difference = term ["-" § (oneormore $ pure_elem)]               # <- ERROR
term       = oneormore | repetition | option | pure_elem        # resuming expected her

#: elements

pure_elem  = element § !/[?*+]/
element    = [retrieveop] symbol !DEF
           | literal
           | plaintext
           | regexp
           | whitespace
           | group$                                             # <- ERROR

#: flow-operators

flowmarker = "!"  | "&"                                         # resuming expected her
           | "<-!" | "<-&"
retr$ieveop = "::" | ":?" | ":"

#: groups

group      = "(" §expression ")"
oneormore  = "{" expression "}+" | element "+"
repetition = "{" §expressi$on "}" | element "*"                 # <- ERROR
option     = "[" §expression "]" | element "?"                  # resuming expected here

#: leaf-elements

symbol     = /(?!\d)\w+/~
$literals   = { literal }+                                      # <- ERROR
literal    = /"(?:(?<!\\)\\"|[^"])*?"/~                         # resuming expected her
           | /'(?:(?<!\\)\\'|[^'])*?'/~
plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~
regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~
whitespace = /~/~

#: delimiters

DEF        = `=` | `:=` | `::=`
OR         = `|`
AND        = `,` | ``
ENDL       = `;` | ``

EOF = !/./ [:?DEF] [:?OR] [:?AND] [:?ENDL]
"""

class TestReentryAfterError:
    testlang = """@literalws = right
    document = alpha [beta] gamma "."
      alpha = "ALPHA" abc
        abc = §"a" "b" "c"
      beta = "BETA" (bac | bca)
        bac = "b" "a" §"c"
        bca = "b" "c" §"a"
      gamma = "GAMMA" §(cab | cba)
        cab = "c" "a" §"b"
        cba = "c" "b" §"a"
    """
    gr = grammar_provider(testlang)()

    def test_no_resume_rules(self):
        gr = self.gr;  gr.resume_rules = dict()
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, cst.content
        assert cst.pick('alpha').content.startswith('ALPHA')

    def test_no_resume_rules_partial_parsing(self):
        gr = self.gr;  gr.resume_rules = dict()
        content = 'ALPHA acb'
        cst = gr(content, 'alpha')
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')

    def test_simple_resume_rule(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1

    def test_failing_resume_rule(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=XXX)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, cst.content
        # assert cst.pick('alpha').content.startswith('ALPHA')

    def test_several_reentry_points(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)'), re.compile(r'(?=GAMMA)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1

    def test_several_reentry_points_second_point_matching(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)'), re.compile(r'(?=GAMMA)')]
        content = 'ALPHA acb GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1
        resume_notices_on(gr)
        cst = gr(content)
        assert len(cst.errors) == 2 and any(err.code == RESUME_NOTICE for err in cst.errors)

    def test_several_resume_rules_innermost_rule_matching(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)'), re.compile(r'(?=GAMMA)')]
        gr.resume_rules__['beta'] = [re.compile(r'(?=GAMMA)')]
        gr.resume_rules__['bac'] = [re.compile(r'(?=GAMMA)')]
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1
        # multiple failures
        content = 'ALPHA acb BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # there should be only two error messages
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 2

    def test_algorithmic_resume(self):
        lang = r"""
            document = block_A block_B
            @ block_A_resume = next_valid_letter()
            @ block_A_skip = next_valid_letter()
            block_A = "a" §"b" "c"
            block_B = "x" "y" "z"
            """
        proc = """
def next_valid_letter(text, start, end):
    L = len(text)
    end = min(L, max(L, end))
    while start < len(text):
        if str(text[start]) in 'abcxyz':
            return start, 0
        start += 1
    return -1, 0
"""
        parser = create_parser(lang, additional_code=proc)
        tree = parser('ab*xyz')
        assert 'block_A' in tree and 'block_B' in tree
        assert tree.pick('ZOMBIE__')


    def test_skip_comment_on_resume(self):
        lang = r"""@literalws = right
            @ comment =  /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/  # Kommentare im C++-Stil
            document = block_A block_B
            @ block_A_resume = /(?=x)/
            block_A = "a" §"b" "c"
            block_B = "x" "y" "z"
        """
        def mini_suite(grammar):
            tree = grammar('abc/*x*/xyz')
            assert not tree.errors
            tree = grammar('abDxyz')
            mandatory_cont = (MANDATORY_CONTINUATION, MANDATORY_CONTINUATION_AT_EOF)
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont
            tree = grammar('abD/*x*/xyz')
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont
            tree = grammar('aD /*x*/ c /* a */ /*x*/xyz')
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont

        # test regex-defined resume rule
        grammar = grammar_provider(lang)()
        mini_suite(grammar)

    def test_unambiguous_error_location(self):
        lang = r"""
            @ literalws   = right
            @ drop        = whitespace, strings  # drop strings and whitespace early
           
            @object_resume = /(?<=\})/
           
            json       = ~ value EOF
            value      = object | string 
            object     = "{" [ member { "," §member } ] "}"
            member     = string §":" value
            string     = `"` CHARACTERS `"` ~

            CHARACTERS = { /[^"\\]+/ }                  
            EOF      =  !/./        # no more characters ahead, end of file reached
            """
        test_case = """{
                "missing member": "abcdef",
            }"""
        gr = grammar_provider(lang)()
        cst = gr(test_case)
        assert any(err.code == MANDATORY_CONTINUATION for err in cst.errors)

    def test_bigfattest(self):
        gr = copy.deepcopy(get_ebnf_grammar())
        resume_notices_on(gr)
        cst = gr(EBNF_with_Errors)
        locations = []
        for error in cst.errors_sorted:
            locations.append((error.line, error.column))
        assert locations == [(36, 37), (37, 1), (47, 19), (51, 1), (53, 5),
                             (57, 1), (59, 27), (60, 1), (65, 1), (66, 1)]



class TestConfiguredErrorMessages:
    def test_configured_error_message(self):
        lang = """
            document = series | /.*/
            @series_error = "a badly configured error message {5}"
            series = /X/ | head §"C" "D"
            head = "A" "B"
            """
        parser = grammar_provider(lang)()
        st = parser("AB_D");  assert st.error_flag
        assert st.errors_sorted[0].code == MALFORMED_ERROR_STRING
        assert st.errors_sorted[1].code == MANDATORY_CONTINUATION


class TestUnknownParserError:
    def test_unknown_parser_error(self):
        gr = Grammar()
        try:
            gr("", "NonExistantParser")
            assert False, "UnknownParserError expected!"
        except AttributeError:
            pass


class TestEarlyTokenWhitespaceDrop:
    lang = r"""
        @ drop = strings, whitespace
        expression = term  { ("+" | "-") term}
        term       = factor  { ("*"|"/") factor}
        factor     = number | variable | "("  expression  ")"
                   | constant | fixed
        variable   = /[a-z]/~
        number     = /\d+/~
        constant   = "A" | "B"
        fixed      = "X"
        """
    gr = grammar_provider(lang)()

    def test_drop(self):
        cst = self.gr('4 + 3 * 5')
        assert not cst.pick(':Text')
        assert not cst.pick(':Whitespace')
        cst = self.gr('A + B')
        try:
            _ = next(cst.select_if(lambda node: node.content == 'A'))
            assert False, "Tokens in compound expressions should be dropped!"
        except StopIteration:
            pass
        cst = self.gr('X * y')
        assert next(cst.select_if(lambda node: node.content == 'X'))


class TestMetaParser:
    mp = CombinedParser()
    mp.grammar = Grammar()  # override placeholder warning
    mp.pname = "named"
    mp.disposable = False
    mp.node_name = mp.pname

    def test_return_value(self):
        nd = self.mp._return_value(Node('tagged', 'non-empty'))
        assert nd.name == 'named', nd.as_sxpr()
        assert len(nd.children) == 1
        assert nd.children[0].name == 'tagged'
        assert nd.children[0].result == "non-empty"
        nd = self.mp._return_value(Node('tagged', ''))
        assert nd.name == 'named', nd.as_sxpr()
        assert len(nd.children) == 1
        assert nd.children[0].name == 'tagged'
        assert not nd.children[0].result
        nd = self.mp._return_value(Node(':anonymous', 'content'))
        assert nd.name == 'named', nd.as_sxpr()
        assert not nd.children
        assert nd.result == 'content'
        nd = self.mp._return_value(Node(':anonymous', ''))
        assert nd.name == 'named', nd.as_sxpr()
        assert not nd.children
        assert not nd.content
        nd = self.mp._return_value(EMPTY_NODE)
        assert nd.name == 'named' and not nd.children, nd.as_sxpr()
        self.mp.pname = ''
        self.mp.disposable = True
        self.mp.node_name = ':unnamed'
        nd = self.mp._return_value(Node('tagged', 'non-empty'))
        assert nd.name == 'tagged', nd.as_sxpr()
        assert len(nd.children) == 0
        assert nd.content == 'non-empty'
        nd = self.mp._return_value(Node('tagged', ''))
        assert nd.name == 'tagged', nd.as_sxpr()
        assert len(nd.children) == 0
        assert not nd.content
        nd = self.mp._return_value(Node(':anonymous', 'content'))
        assert nd.name == ':anonymous', nd.as_sxpr()
        assert not nd.children
        assert nd.result == 'content'
        nd = self.mp._return_value(Node('', ''))
        assert nd.name == '', nd.as_sxpr()
        assert not nd.children
        assert not nd.content
        assert self.mp._return_value(None) == EMPTY_NODE
        assert self.mp._return_value(EMPTY_NODE) == EMPTY_NODE

    def test_return_values(self):
        self.mp.pname = "named"
        self.mp.node_name = self.mp.pname
        rv = self.mp._return_values((Node('tag', 'content'), EMPTY_NODE))
        assert rv[-1].name != EMPTY_NODE.name, rv[-1].name

    def test_in_context(self):
        minilang = r"""
            term       = factor  { (DIV|MUL) factor}
            factor     = NUMBER | VARIABLE
            MUL        = "*" | &factor
            DIV        = "/"
            NUMBER     = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
            VARIABLE   = /[A-Za-z]/~
            """
        gr = grammar_provider(minilang)()
        cst = gr("2x")
        assert bool(cst.pick('MUL')), "Named empty nodes should not be dropped!!!"


class TestParserCombining:
    def test_series(self):
        parser = RegExp(r'\d+') + RegExp(r'\.')
        assert isinstance(parser, Series)
        parser += RegExp(r'\d+')
        assert isinstance(parser, Series)
        assert len(parser.parsers) == 3
        parser = Text(">") + parser
        assert isinstance(parser, Series)
        assert len(parser.parsers) == 4
        parser = parser + Text("<")
        assert isinstance(parser, Series)
        assert len(parser.parsers) == 5

    def test_alternative(self):
        parser = RegExp(r'\d+') | RegExp(r'\.')
        assert isinstance(parser, Alternative)
        parser |= RegExp(r'\d+')
        assert isinstance(parser, Alternative)
        assert len(parser.parsers) == 3
        parser = Text(">") | parser
        assert isinstance(parser, Alternative)
        assert len(parser.parsers) == 4
        parser = parser | Text("<")
        assert isinstance(parser, Alternative)
        assert len(parser.parsers) == 5

    def test_interleave(self):
        parser = RegExp(r'\d+') * RegExp(r'\.')
        assert isinstance(parser, Interleave)
        parser *= RegExp(r'\d+')
        assert isinstance(parser, Interleave)
        assert len(parser.parsers) == 3
        parser = Text(">") * parser
        assert isinstance(parser, Interleave)
        assert len(parser.parsers) == 4
        parser = parser * Text("<")
        assert isinstance(parser, Interleave)
        assert len(parser.parsers) == 5

    def test_mixed_combinations(self):
        parser = RegExp(r'\d+') +  RegExp(r'\.') + RegExp(r'\d+') | RegExp(r'\d+')
        assert isinstance(parser, Alternative)
        assert len(parser.parsers) == 2
        assert isinstance(parser.parsers[0], Series)
        assert len(parser.parsers[0].parsers) == 3
        assert isinstance(parser.parsers[1], RegExp)


class TestStaticAnalysis:
    def setup(self):
        self.static_analysis = get_config_value('static_analysis')
        set_config_value('static_analysis', 'early')

    def teardown(self):
        set_config_value('static_analysis', self.static_analysis)

    def test_cannot_capture_dropped_content(self):
        p = Capture(Drop(Whitespace(" ")))
        try:
            gr = Grammar(p)
            assert any(ae.error.code == CAPTURE_DROPPED_CONTENT_WARNING
                       for ae in gr.static_analysis_errors__), \
                "Dropped content warning expected"
        except GrammarError as ge:
            assert ge.errors and ge.errors[0][-1].code == CAPTURE_DROPPED_CONTENT_WARNING, \
                "Capture-dropped-content-Warning expected"

    def test_cyclical_ebnf_error(self):
        doc = Text('proper');  doc.pname = "doc"
        grammar = Grammar(doc)
        # grammar.static_analysis__()
        lang = "doc = 'proper'  # this works!"
        lang1 = "doc = { doc }  # this parser never reaches a leaf parser."
        lang2 = """doc = word | sentence  # a more convoluted example
                word = [sentence] doc 
                sentence = { word }+ | sentence"""
        code, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert not ast.errors
        code, errors, ast = compile_ebnf(lang1, preserve_AST=True)
        assert any(e.code == PARSER_NEVER_TOUCHES_DOCUMENT for e in errors)
        code, errors, ast = compile_ebnf(lang2, preserve_AST=True)
        assert any(e.code == PARSER_NEVER_TOUCHES_DOCUMENT for e in errors)


class TestMemoization:
    def test_memoization(self):
        words = r'''@literalws = right
        list = word { ',' word } §EOF
        word = wordA | wordB | wordC
        wordA = `"` /[Aa]\w+/ '"'
        wordB = `"` /[Bb]\w+/ '"'
        wordC = `"` /[Cc]\w+/ '"'
        EOF = /$/'''
        grammar = create_parser(words, 'words')

        p1 = grammar.wordC.parsers[0]
        p2 = grammar.wordB.parsers[0]
        p3 = grammar.wordA.parsers[0]

        ps1 = grammar.wordC.parsers[-1]
        ps2 = grammar.wordB.parsers[-1]
        ps3 = grammar.wordA.parsers[-1]

        p4 = ps1.parsers[0]
        p5 = ps1.parsers[0]
        p6 = ps1.parsers[0]

        assert (p.eq_class == p1.eq_class for p in (p2, p3, p4, p5, p6))
        assert (p.eq_class == ps1.eq_class for p in (ps2, ps3))

        cst = grammar('"camma", "beta", "alpha"')


class TestStringAlternative:
    def test_longest_match(self):
        l = ['a', 'ab', 'ca', 'cd']
        assert longest_match(l, '0abdd') == ''
        assert longest_match(l, 'axcde') == 'a'
        assert longest_match(l, 'cab') == 'ca'
        assert longest_match(l, 'b') == ''
        assert longest_match(l, 'x') == ''
        assert longest_match(l, 'a') == 'a'
        assert longest_match(l, 'ab') == 'ab'
        assert longest_match(l, 'ca') == 'ca'
        assert longest_match(l, 'cd') == 'cd'
        assert longest_match(l, 'cb') == ''
        assert longest_match(l, 'cdc') == 'cd'
        assert longest_match(l, 'c') == ''
        l = ['a', 'ab', 'abc', 'abcd']
        assert longest_match(l, 'abxyz') == 'ab'
        assert longest_match(l, 'abcdxyz') == 'abcd'
        assert longest_match(l, 'abcxyz') == 'abc'
        assert longest_match(l, 'axyz') == 'a'
        assert longest_match(l, 'axyz') == 'a'
        assert longest_match(l, 'ax') == 'a'
        assert longest_match(l, '') == ''
        assert longest_match([], 'a') == ''
        assert longest_match([], '') == ''
        l = ['abc', 'xy']
        assert longest_match(l, 'xyzt', 2) == 'xy'
        assert longest_match(l, 'abcdefg', 1) == 'abc'
        assert longest_match(l, 'abcdefg', 2) == 'abc'
        assert longest_match(l, 'ax12345', 2) == ''
        assert longest_match(l, 'a', 2) == ''


class TestErrorLocations:
    def test_error_locations_bug(self):
        miniXML = '''
        @ disposable  = EOF
        @ drop        = EOF, whitespace, strings
        document = ~ element ~ §EOF
        element  = STag §content ETag
        STag     = '<' TagName §'>'
        @ETag_skip = /[^<>]*/
        ETag     = '</' § ::TagName '>'
        TagName  = /\\w+/
        content  = [CharData] { (element | COMMENT__) [CharData] }
        CharData = /(?:(?!\\]\\]>)[^<&])+/
        EOF      =  !/./
        '''
        testdoc = '''
        <doc>
            <title>Heading <wrong></title>
        </doc>'''
        parseXML = create_parser(miniXML)
        _ = parseXML(testdoc)

    def test_error_resumption(self):
        miniXML = '''
        @ whitespace  = /\s*/
        @ disposable  = EOF
        @ drop        = EOF, whitespace, strings

        document = ~ element ~ §EOF
        @element_resume = (:?TagName)
        element  = STag §content ETag
        @STag_skip = (/[^<>]*>/)
        STag     = '<' TagName §'>'
        @ETag_skip = (/[^<>]*/)
        ETag     = '</' ::TagName §'>'
        TagName  = /\w+/
        content  = [CharData] { (element | COMMENT__) [CharData] }

        CharData = /(?:(?!\]\]>)[^<&])+/
        EOF      =  !/./        # no more characters ahead, end of file reached
        '''
        testdoc = '''
        <doc>
            <title>Heading <wrong></title>
        </doc>'''
        parseXML = create_parser(miniXML)
        resume_notices_on(parseXML)
        result = parseXML(testdoc)
        assert len(result.errors) == 2

    def test_error_resumption_2(self):
        miniXML = '''
        @ whitespace  = /\s*/
        @ disposable  = EOF
        @ drop        = EOF, whitespace, strings

        document = ~ element ~ §EOF
        @element_resume = /[^<>]*/
        element  = STag §content ETag
        @STag_skip = (/[^<>]*>/)
        STag     = '<' TagName §'>'
        @ETag_skip = (/[^<>]*/)
        ETag     = '</' ::TagName §'>'
        TagName  = /\w+/
        content  = [CharData] { (element | COMMENT__) [CharData] }

        CharData = /(?:(?!\]\]>)[^<&])+/
        EOF      =  !/./        # no more characters ahead, end of file reached
        '''
        testdoc = '''
        <doc>
            <title>Heading <wrong></title>
        </doc>'''
        parseXML = create_parser(miniXML)
        resume_notices_on(parseXML)
        result = parseXML(testdoc)
        # for e in result.errors:  print(e)
        assert len(result.errors) == 2

    def test_error_location(self):
        grammar = r'''
            @ string_error  = /\\/, 'Illegal escape sequence »{1}«'
            @ string_error  = '', 'Illegal character "{1}" in string.'
            @ string_resume = /("\s*)/
            string          = `"` §characters `"` ~
            characters      = { plain | escape }
            plain           = /[^"\\]+/
            escape          = /\[\/bnrt\\]/'''
        json_string = create_parser(grammar, 'json_string')
        tree = json_string('"al\\pha"')
        assert len(tree.errors) == 1


class TestStructurePreservationOnLookahead:
    def test_structure_preservation_on_lookahead(self):
        bib_grammar = r'''@literalws = right
        @whitespace = horizontal
        biliography = author ":" work { /\s*/ author ":" work } EOF 
        author = name § { ~ name}+ &`:`
        work = word § { ~ word} &(/\n/ | EOF)
        name = word
        word = /\w+/
        EOF = !/./
        '''
        document = "Bertrand Russel: Principia Mathematica"
        gr = create_parser(bib_grammar)
        bib = gr(document)
        assert bib['author'].content == "Bertrand Russel"
        assert bib['work'].content == "Principia Mathematica"
        author = gr('Bertrand Russell', 'author')
        assert author.name == "author" and author.content == "Bertrand Russell"
        assert author.errors[0].code == MANDATORY_CONTINUATION_AT_EOF_NON_ROOT


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())

