#!/usr/bin/python3

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

import os
import sys
from functools import partial

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import get_config_value, set_config_value
from DHParser.toolkit import compile_python_object
from DHParser.log import is_logging, log_ST, log_parsing_history
from DHParser.error import Error, is_error
from DHParser.parse import ParserError, Parser, Grammar, Forward, TKN, ZeroOrMore, RE, \
    RegExp, Lookbehind, NegativeLookahead, OneOrMore, Series, Alternative, AllOf, SomeOf, \
    UnknownParserError, MetaParser, GrammarError, EMPTY_NODE
from DHParser import compile_source
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler, DHPARSER_IMPORTS
from DHParser.dsl import grammar_provider, CompilationError
from DHParser.syntaxtree import Node, parse_sxpr
from DHParser.stringview import StringView


class TestParserError:
    def test_parser_error_str(self):
        pe = ParserError(Node('TAG', 'test').with_pos(0), StringView('Beispiel'), None, True)
        assert str(pe).find('Beispiel') >= 0 and str(pe).find('TAG') >= 0


class TestParserClass:
    def test_apply(self):
        minilang ="""
            expr = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        gr = grammar_provider(minilang)()
        l = []
        def visitor(p: Parser):
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


class TestInfiLoopsAndRecursion:
    def test_direct_left_recursion1(self):
        minilang = """
            expr = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        snippet = "9 + 8 + 7 + 6 + 5 + 3 * 4"
        parser = grammar_provider(minilang)()
        assert parser
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), str(syntax_tree.errors_sorted)
        assert snippet == syntax_tree.content, str(syntax_tree)
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_direct.cst")
            log_parsing_history(parser, "test_LeftRecursion_direct")

    def test_direct_left_recursion2(self):
        minilang = """
            expr = ex
            ex   = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        snippet = "9 + 8 + 7 + 6 + 5 + 3 * 4"
        parser = grammar_provider(minilang)()
        assert parser
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        assert snippet == syntax_tree.content

    def test_indirect_left_recursion1(self):
        minilang = """
            Expr    = //~ (Product | Sum | Value)
            Product = Expr { ('*' | '/') Expr }+
            Sum     = Expr { ('+' | '-') Expr }+
            Value   = /[0-9.]+/~ | '(' §Expr ')'
            """
        parser = grammar_provider(minilang)()
        assert parser
        snippet = "8 * 4"
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        snippet = "7 + 8 * 4"
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        snippet = "9 + 8 * (4 + 3)"
        syntax_tree = parser(snippet)
        assert not is_error(syntax_tree.error_flag), syntax_tree.errors_sorted
        assert snippet == syntax_tree.content
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_indirect.cst")
            log_parsing_history(parser, "test_LeftRecursion_indirect")

    # # BEWARE: EXPERIMENTAL TEST can be long running
    # def test_indirect_left_recursion2(self):
    #     arithmetic_syntax = """
    #         expression     = addition | subtraction
    #         addition       = (expression | term) "+" (expression | term)
    #         subtraction    = (expression | term) "-" (expression | term)
    #         term           = multiplication | division
    #         multiplication = (term | factor) "*" (term | factor)
    #         division       = (term | factor) "/" (term | factor)
    #         factor         = [SIGN] ( NUMBER | VARIABLE | group ) { VARIABLE | group }
    #         group          = "(" expression ")"
    #         SIGN           = /[+-]/
    #         NUMBER         = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
    #         VARIABLE       = /[A-Za-z]/~
    #         """
    #     arithmetic = grammar_provider(arithmetic_syntax)()
    #     arithmetic.left_recursion_depth__ = 2
    #     assert arithmetic
    #     syntax_tree = arithmetic("(a + b) * (a - b)")
    #     assert syntax_tree.errors

    def test_break_inifnite_loop_ZeroOrMore(self):
        forever = ZeroOrMore(RegExp(''))
        result = Grammar(forever)('')  # infinite loops will automatically be broken
        assert repr(result) == "Node(:EMPTY__, )", repr(result)

    def test_break_inifnite_loop_OneOrMore(self):
        forever = OneOrMore(RegExp(''))
        result = Grammar(forever)('')  # infinite loops will automatically be broken
        assert repr(result) == "Node(:EMPTY__, )", str(result)

    # def test_infinite_loops(self):
    #     minilang = """forever = { // } \n"""
    #     try:
    #         parser_class = grammar_provider(minilang)
    #     except CompilationError as error:
    #         assert all(e.code == Error.INFINITE_LOOP for e in error.errors)
    #     save = get_config_value('static_analysis')
    #     set_config_value('static_analysis', 'late')
    #     provider = grammar_provider(minilang)
    #     try:
    #         parser = provider()
    #     except GrammarError as error:
    #         assert error.errors[0][2].code == Error.INFINITE_LOOP
    #     set_config_value('static_analysis', 'none')
    #     parser = provider()
    #     snippet = " "
    #     syntax_tree = parser(snippet)
    #     assert any(e.code == Error.INFINITE_LOOP for e in syntax_tree.errors)
    #     res = parser.static_analysis()
    #     assert res and res[0][2].code == Error.INFINITE_LOOP
    #     minilang = """not_forever = { / / } \n"""
    #     parser = grammar_provider(minilang)()
    #     res = parser.static_analysis()
    #     assert not res
    #     set_config_value('static_analysis', save)


class TestFlowControl:
    def setup(self):
        self.t1 = """
        All work and no play
        makes Jack a dull boy
        END
        """
        self.t2 = "All word and not play makes Jack a dull boy END\n"

    def test_lookbehind(self):
        ws = RegExp(r'\s*')
        end = RegExp("END")
        doc_end = Lookbehind(RegExp('\\s*?\\n')) + end
        word = RegExp(r'\w+')
        sequence = OneOrMore(NegativeLookahead(end) + word + ws)
        document = ws + sequence + doc_end + ws

        parser = Grammar(document)
        cst = parser(self.t1)
        assert not cst.error_flag, cst.as_sxpr()
        cst = parser(self.t2)
        assert cst.error_flag, cst.as_sxpr()

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
        result, messages, syntax_tree = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages, str(messages)
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node = parser('abc+def', parser.regex)
        assert not node.error_flag
        assert node.tag_name == "regex"
        assert str(node) == 'abc+def'

    def test_multilineRegex_wo_Comments(self):
        mlregex = r"""
        regex =  /\w+
                  [+]
                  \w* /
        """
        result, messages, syntax_tree = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages, str(messages)
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node = parser('abc+def', parser.regex)
        assert not node.error_flag
        assert node.tag_name == "regex"
        assert str(node) == 'abc+def'

    def text_ignore_case(self):
        mlregex = r"""
        @ ignorecase = True
        regex = /alpha/
        """
        result, messages, syntax_tree = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node, rest = parser.regex('Alpha')
        assert node
        assert not node.error_flag
        assert rest == ''
        assert node.tag_name == "regex"
        assert str(node) == 'Alpha'

        mlregex = r"""
        @ ignorecase = False
        regex = /alpha/
        """
        result, messages, syntax_tree = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        node, rest = parser.regex('Alpha')
        assert node.error_flag


    def test_token(self):
        tokenlang = r"""
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
        result, messages, syntax_tree = compile_source(
            tokenlang, None, get_ebnf_grammar(), get_ebnf_transformer(),
            get_ebnf_compiler("TokenTest"))
        assert result
        assert not messages, str(messages)
        parser = compile_python_object(DHPARSER_IMPORTS + result, r'\w+Grammar$')()
        result = parser(testdoc)
        # log_parsing_history(parser, "test.log")
        assert not result.error_flag


class TestGrammar:
    def setup(self):
        grammar = r"""@whitespace = horizontal
        haupt        = textzeile LEERZEILE
        textzeile    = { WORT }+
        WORT         = /[^ \t]+/~
        LEERZEILE    = /\n[ \t]*(?=\n)/~
        """
        self.pyparser, messages, syntax_tree = compile_source(grammar, None, get_ebnf_grammar(),
                                                              get_ebnf_transformer(), get_ebnf_compiler("PosTest"))
        assert self.pyparser
        assert not messages

    def test_pos_values_initialized(self):
        # checks whether pos values in the parsing result and in the
        # history record have been initialized
        grammar = compile_python_object(DHPARSER_IMPORTS + self.pyparser, r'\w+Grammar$')()
        grammar("no_file_name*")
        for record in grammar.history__:
            assert not record.node or record.node.pos >= 0

    def test_select_parsing(self):
        grammar = compile_python_object(DHPARSER_IMPORTS + self.pyparser, r'\w+Grammar$')()
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


class TestSeries:
    def test_non_mandatory(self):
        lang = """
        document = series | /.*/
        series = "A" "B" "C" "D"
        """
        parser = grammar_provider(lang)()
        st = parser("ABCD");
        assert not st.error_flag
        st = parser("A_CD");
        assert not st.error_flag
        st = parser("AB_D");
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
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION

    def test_series_composition(self):
        TA, TB, TC, TD, TE = (TKN(b) for b in "ABCDE")
        s1 = Series(TA, TB, TC, mandatory=2)
        s2 = Series(TD, TE)

        combined = Alternative(s1 + s2, RegExp('.*'))
        parser = Grammar(combined)
        st = parser("ABCDE");  assert not st.error_flag
        st = parser("A_CDE");  assert not st.error_flag
        st = parser("AB_DE");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        st = parser("ABC_E");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION

        combined = Alternative(s2 + s1, RegExp('.*'))
        parser = Grammar(combined)
        st = parser("DEABC");  assert not st.error_flag
        st = parser("_EABC");  assert not st.error_flag
        st = parser("D_ABC");  assert not st.error_flag
        st = parser("DE_BC");  assert not st.error_flag
        st = parser("DEA_C");  assert not st.error_flag
        st = parser("DEAB_");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION

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


class TestAllOfSomeOf:
    def test_allOf_order(self):
        """Test that parsers of an AllOf-List can match in arbitrary order."""
        prefixes = AllOf(TKN("A"), TKN("B"))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B A').content == 'B A'
        # aternative Form
        prefixes = AllOf(Series(TKN("B"), TKN("A")))
        assert Grammar(prefixes)('A B').content == 'A B'

    def test_allOf_completeness(self):
        """Test that an error is raised if not  all parsers of an AllOf-List
        match."""
        prefixes = AllOf(TKN("A"), TKN("B"))
        assert Grammar(prefixes)('B').error_flag

    def test_allOf_redundance(self):
        """Test that one and the same parser may be listed several times
        and must be matched several times accordingly."""
        prefixes = AllOf(TKN("A"), TKN("B"), TKN("A"))
        assert Grammar(prefixes)('A A B').content == 'A A B'
        assert Grammar(prefixes)('A B A').content == 'A B A'
        assert Grammar(prefixes)('B A A').content == 'B A A'
        assert Grammar(prefixes)('A B B').error_flag

    def test_someOf_order(self):
        """Test that parsers of an AllOf-List can match in arbitrary order."""
        prefixes = SomeOf(TKN("A"), TKN("B"))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B A').content == 'B A'
        # aternative Form
        prefixes = SomeOf(Alternative(TKN("B"), TKN("A")))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B').content == 'B'

    def test_someOf_redundance(self):
        """Test that one and the same parser may be listed several times
        and must be matched several times accordingly."""
        prefixes = SomeOf(TKN("A"), TKN("B"), TKN("A"))
        assert Grammar(prefixes)('A A B').content == 'A A B'
        assert Grammar(prefixes)('A B A').content == 'A B A'
        assert Grammar(prefixes)('B A A').content == 'B A A'
        assert Grammar(prefixes)('A B B').error_flag


class TestErrorRecovery:
    def test_series_skip(self):
        lang = """
        document = series | /.*/
        @series_skip = /[A-Z]/
        series = "A" "B" §"C" "D"
        """
        parser = grammar_provider(lang)()
        st = parser('AB_D')
        assert len(st.errors) == 1  # no additional "stopped before end"-error!

    def test_AllOf_skip(self):
        lang = """
        document = allof | /.*/
        @allof_skip = /[A-Z]/
        allof = < "A" §"B" "C" "D" >
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
        st = parser('BC_A')
        assert st['allof'].content == "BC_A"


class TestPopRetrieve:
    mini_language = r"""
        document       = { text | codeblock }
        codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
        delimiter      = delimiter_sign  # never use delimiter between capture and pop except for retrival!
        delimiter_sign = /`+/
        text           = /[^`]+/
        """
    mini_lang2 = r"""
        @braces_filter=counterpart
        document       = { text | codeblock }
        codeblock      = braces { text | opening_braces | (!:braces closing_braces) } ::braces
        braces         = opening_braces
        opening_braces = /\{+/
        closing_braces = /\}+/
        text           = /[^{}]+/
        """
    mini_lang3 = r"""
        document       = { text | env }
        env            = (specialtag | opentag) text [closespecial | closetag]
        opentag        = "<" name ">"
        specialtag     = "<" /ABC/ !name ">"
        closetag       = close_slash | close_star
        close_slash    = "<" ::name "/>"
        close_star     = "<" ::name "*>"
        closespecial   = "<" /ABC/~ ">"
        name           = /\w+/~
        text           = /[^<>]+/
        """

    def setup(self):
        self.minilang_parser = grammar_provider(self.mini_language)()
        self.minilang_parser2 = grammar_provider(self.mini_lang2)()
        self.minilang_parser3 = grammar_provider(self.mini_lang3)()

    @staticmethod
    def opening_delimiter(node, name):
        return node.tag_name == name # and not isinstance(node.parser, Retrieve)

    @staticmethod
    def closing_delimiter(node):
        return node.tag_name in {':Pop', ':Retrieve'}
        # return isinstance(node.parser, Retrieve)

    def test_compile_mini_language(self):
        assert self.minilang_parser
        assert self.minilang_parser2
        assert self.minilang_parser3

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

    def test_cache_neutrality(self):
        """Test that packrat-caching does not interfere with the variable-
        changing parsers: Capture and Retrieve."""
        lang = r"""
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

    def test_single_line(self):
        teststr = "Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ende"
        syntax_tree = self.minilang_parser(teststr)
        assert not syntax_tree.errors_sorted
        delim = str(next(syntax_tree.select_if(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.select_if(self.closing_delimiter)))
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
        delim = str(next(syntax_tree.select_if(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.select_if(self.closing_delimiter)))
        assert delim == pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_multi_line.cst")

    def test_single_line_complement(self):
        teststr = "Anfang {{{code block }} <- keine Ende-Zeichen ! }}} Ende"
        syntax_tree = self.minilang_parser2(teststr)
        assert not syntax_tree.errors_sorted
        delim = str(next(syntax_tree.select_if(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.select_if(self.closing_delimiter)))
        assert len(delim) == len(pop) and delim != pop
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
        delim = str(next(syntax_tree.select_if(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.select_if(self.closing_delimiter)))
        assert len(delim) == len(pop) and delim != pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_multi_line.cst")


class TestWhitespaceHandling:
    minilang = """
        doc = A B
        A = "A"
        B = "B"
        Rdoc = ar br
        ar = /A/
        br = /B/
        """

    def setup(self):
        self.gr = grammar_provider(self.minilang)()

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
        assert cst.error_flag and cst.errors_sorted[0].code == Error.PARSER_DID_NOT_MATCH
        cst = gr('', 'parser')
        assert cst.error_flag and cst.errors_sorted[0].code == Error.PARSER_DID_NOT_MATCH

    def test_matching(self):
        minilang = """parser = /.?/"""
        gr = grammar_provider(minilang)()
        cst = gr(' ', 'parser')
        assert not cst.error_flag
        cst = gr('  ', 'parser')
        assert cst.error_flag and cst.errors_sorted[0].code == Error.PARSER_STOPPED_BEFORE_END
        cst = gr('', 'parser')
        assert not cst.error_flag


class TestReentryAfterError:
    def setup(self):
        lang = """
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
        self.gr = grammar_provider(lang)()

    def test_no_resume_rules(self):
        gr = self.gr;  gr.resume_rules = dict()
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')

    def test_no_resume_rules_partial_parsing(self):
        gr = self.gr;  gr.resume_rules = dict()
        content = 'ALPHA acb'
        cst = gr(content, 'alpha')
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')

    def test_simple_resume_rule(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = ['BETA']
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1

    def test_failing_resume_rule(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = ['XXX']
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        # assert cst.pick('alpha').content.startswith('ALPHA')

    def test_severl_reentry_points(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = ['BETA', 'GAMMA']
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1

    def test_several_reentry_points_second_point_matching(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = ['BETA', 'GAMMA']
        content = 'ALPHA acb GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1

    def test_several_resume_rules_innermost_rule_matching(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = ['BETA', 'GAMMA']
        gr.resume_rules__['beta'] = ['GAMMA']
        gr.resume_rules__['bac'] = ['GAMMA']
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1
        # multiple failures
        content = 'ALPHA acb BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # there should be only two error messages
        assert len(cst.errors_sorted) == 2

    def test_skip_comment_on_resume(self):
        lang = r"""
            @ comment =  /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/  # Kommentare im C++-Stil
            document = block_A block_B
            @ block_A_resume = /x/
            block_A = "a" §"b" "c"
            block_B = "x" "y" "z"
        """
        def mini_suite(grammar):
            tree = grammar('abc/*x*/xyz')
            assert not tree.errors
            tree = grammar('abDxyz')
            mandatory_cont = (Error.MANDATORY_CONTINUATION, Error.MANDATORY_CONTINUATION_AT_EOF)
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont
            tree = grammar('abD/*x*/xyz')
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont
            tree = grammar('aD /*x*/ c /* a */ /*x*/xyz')
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont

        # test regex-defined resume rule
        grammar = grammar_provider(lang)()
        mini_suite(grammar)

        # test string-defined resume rule
        alt_lang = lang.replace('@ block_A_resume = /x/',
                                '@ block_A_resume = "x"')
        grammar = grammar_provider(alt_lang)()
        mini_suite(grammar)

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
        assert st.errors_sorted[0].code == Error.MALFORMED_ERROR_STRING
        assert st.errors_sorted[1].code == Error.MANDATORY_CONTINUATION


class TestUnknownParserError:
    def test_unknown_parser_error(self):
        gr = Grammar()
        try:
            gr("", "NonExistantParser")
            assert False, "UnknownParserError expected!"
        except UnknownParserError:
            pass


class TestEarlyTokenWhitespaceDrop:
    def setup(self):
        self.lang = r"""
            @ drop = token, whitespace
            expression = term  { ("+" | "-") term}
            term       = factor  { ("*"|"/") factor}
            factor     = number | variable | "("  expression  ")"
                       | constant | fixed
            variable   = /[a-z]/~
            number     = /\d+/~
            constant   = "A" | "B"
            fixed      = "X"
            """
        self.gr = grammar_provider(self.lang)()

    def test_drop(self):
        cst = self.gr('4 + 3 * 5')
        assert not cst.pick(':Token')
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
    def setup(self):
        self.mp = MetaParser()
        self.mp.grammar = Grammar()  # override placeholder warning
        self.mp.pname = "named"
        self.mp.tag_name = self.mp.pname

    def test_return_value(self):
        save = get_config_value('flatten_tree_while_parsing')
        set_config_value('flatten_tree_while_parsing', True)
        nd = self.mp._return_value(Node('tagged', 'non-empty'))
        assert nd.tag_name == 'named', nd.as_sxpr()
        assert len(nd.children) == 1
        assert nd.children[0].tag_name == 'tagged'
        assert nd.children[0].result == "non-empty"
        nd = self.mp._return_value(Node('tagged', ''))
        assert nd.tag_name == 'named', nd.as_sxpr()
        assert len(nd.children) == 1
        assert nd.children[0].tag_name == 'tagged'
        assert not nd.children[0].result
        nd = self.mp._return_value(Node(':anonymous', 'content'))
        assert nd.tag_name == 'named', nd.as_sxpr()
        assert not nd.children
        assert nd.result == 'content'
        nd = self.mp._return_value(Node(':anonymous', ''))
        assert nd.tag_name == 'named', nd.as_sxpr()
        assert not nd.children
        assert not nd.content
        nd = self.mp._return_value(EMPTY_NODE)
        assert nd.tag_name == 'named' and not nd.children, nd.as_sxpr()
        self.mp.pname = ''
        self.mp.tag_name = ':unnamed'
        nd = self.mp._return_value(Node('tagged', 'non-empty'))
        assert nd.tag_name == 'tagged', nd.as_sxpr()
        assert len(nd.children) == 0
        assert nd.content == 'non-empty'
        nd = self.mp._return_value(Node('tagged', ''))
        assert nd.tag_name == 'tagged', nd.as_sxpr()
        assert len(nd.children) == 0
        assert not nd.content
        nd = self.mp._return_value(Node(':anonymous', 'content'))
        assert nd.tag_name == ':anonymous', nd.as_sxpr()
        assert not nd.children
        assert nd.result == 'content'
        nd = self.mp._return_value(Node('', ''))
        assert nd.tag_name == '', nd.as_sxpr()
        assert not nd.children
        assert not nd.content
        assert self.mp._return_value(None) == EMPTY_NODE
        assert self.mp._return_value(EMPTY_NODE) == EMPTY_NODE
        set_config_value('flatten_tree_while_parsing', save)

    def test_return_values(self):
        self.mp.pname = "named"
        self.mp.tag_name = self.mp.pname
        rv = self.mp._return_values((Node('tag', 'content'), EMPTY_NODE))
        assert rv[-1].tag_name != EMPTY_NODE.tag_name, rv[-1].tag_name

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


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
