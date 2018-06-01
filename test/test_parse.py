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

import sys
from functools import partial

sys.path.extend(['../', './'])

from DHParser.toolkit import compile_python_object
from DHParser.log import logging, is_logging, log_ST
from DHParser.error import Error
from DHParser.parse import Retrieve, Grammar, Forward, Token, ZeroOrMore, RE, \
    RegExp, Lookbehind, NegativeLookahead, OneOrMore, Series, Alternative, AllOf, SomeOf, UnknownParserError
from DHParser import compile_source
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.dsl import grammar_provider, DHPARSER_IMPORTS


class TestInfiLoopsAndRecursion:
    def test_direct_left_recursion1(self):
        minilang ="""
            expr = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            """
        snippet = "9 + 8 + 7 + 6 + 5 + 3 * 4"
        parser = grammar_provider(minilang)()
        assert parser
        syntax_tree = parser(snippet)
        assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())
        assert snippet == str(syntax_tree)
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_direct.cst")
            parser.log_parsing_history__("test_LeftRecursion_direct")

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
        assert not syntax_tree.error_flag, syntax_tree.collect_errors()
        assert snippet == str(syntax_tree)

    def test_indirect_left_recursion1(self):
        minilang = """
            Expr    = //~ (Product | Sum | Value)
            Product = Expr { ('*' | '/') Expr }+
            Sum     = Expr { ('+' | '-') Expr }+
            Value   = /[0-9.]+/~ | '(' Expr ')'
            """
        parser = grammar_provider(minilang)()
        assert parser
        snippet = "8 * 4"
        syntax_tree = parser(snippet)
        assert not syntax_tree.error_flag, syntax_tree.collect_errors()
        snippet = "7 + 8 * 4"
        syntax_tree = parser(snippet)
        assert not syntax_tree.error_flag, syntax_tree.collect_errors()
        snippet = "9 + 8 * (4 + 3)"
        syntax_tree = parser(snippet)
        assert not syntax_tree.error_flag, syntax_tree.collect_errors()
        assert snippet == str(syntax_tree)
        if is_logging():
            log_ST(syntax_tree, "test_LeftRecursion_indirect.cst")
            parser.log_parsing_history__("test_LeftRecursion_indirect")

    def test_inifinite_loops(self):
        minilang = """not_forever = { // } \n"""
        snippet = " "
        parser = grammar_provider(minilang)()
        syntax_tree = parser(snippet)
        assert syntax_tree.error_flag


class TestFlowControl:
    def setup(self):
        self.t1 = """
        All work and no play
        makes Jack a dull boy
        END
        """
        self.t2 = "All word and not play makes Jack a dull boy END\n"

    def test_lookbehind(self):
        ws = RegExp('\s*')
        end = RegExp("END")
        doc_end = Lookbehind(RegExp('\\s*?\\n')) + end
        word = RegExp('\w+')
        sequence = OneOrMore(NegativeLookahead(end) + word + ws)
        document = ws + sequence + doc_end + ws

        parser = Grammar(document)
        cst = parser(self.t1)
        assert not cst.error_flag, cst.as_sxpr()
        cst = parser(self.t2)
        assert cst.error_flag, cst.as_sxpr()

    def test_lookbehind_indirect(self):
        class LookbehindTestGrammar(Grammar):
            parser_initialization__ = "upon instantiation"
            ws = RegExp('\\s*')
            end = RegExp('END')
            SUCC_LB = RegExp('\\s*?\\n')
            doc_end = Series(Lookbehind(SUCC_LB), end)
            word = RegExp('\w+')
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
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        node = parser('abc+def', parser.regex)
        assert not node.error_flag
        assert node.parser.name == "regex"
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
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        node = parser('abc+def', parser.regex)
        assert not node.error_flag
        assert node.parser.name == "regex"
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
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        node, rest = parser.regex('Alpha')
        assert node
        assert not node.error_flag
        assert rest == ''
        assert node.parser.name == "regex"
        assert str(node) == 'Alpha'

        mlregex = r"""
        @ ignorecase = False
        regex = /alpha/
        """
        result, messages, syntax_tree = compile_source(mlregex, None, get_ebnf_grammar(),
                        get_ebnf_transformer(), get_ebnf_compiler('MultilineRegexTest'))
        assert result
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
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
        result, messages, syntax_tree = compile_source(tokenlang, None, get_ebnf_grammar(),
                                    get_ebnf_transformer(), get_ebnf_compiler("TokenTest"))
        assert result
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        result = parser(testdoc)
        # parser.log_parsing_history("test.log")
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
        with logging("LOGS"):
            grammar = compile_python_object(DHPARSER_IMPORTS + self.pyparser, '\w+Grammar$')()
            grammar("no_file_name*")
        for record in grammar.history__:
            assert not record.node or record.node.pos >= 0

    def test_select_parsing(self):
        grammar = compile_python_object(DHPARSER_IMPORTS + self.pyparser, '\w+Grammar$')()
        grammar("wort", "WORT")
        grammar("eine Zeile", "textzeile")
        grammar("kein Haupt", "haupt")
        grammar("so ist es richtig", "haupt")

    def test_grammar_subclassing(self):
        class Arithmetic(Grammar):
            '''
            expression =  term  { ("+" | "-") term }
            term       =  factor  { ("*" | "/") factor }
            factor     =  INTEGER | "("  expression  ")"
            INTEGER    =  /\d+/~
            '''
            expression = Forward()
            INTEGER = RE('\\d+')
            factor = INTEGER | Token("(") + expression + Token(")")
            term = factor + ZeroOrMore((Token("*") | Token("/")) + factor)
            expression.set(term + ZeroOrMore((Token("+") | Token("-")) + term))
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
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION

    def test_series_composition(self):
        TA, TB, TC, TD, TE = (Token(b) for b in "ABCDE")
        s1 = Series(TA, TB, TC, mandatory=2)
        s2 = Series(TD, TE)

        combined = Alternative(s1 + s2, RegExp('.*'))
        parser = Grammar(combined)
        st = parser("ABCDE");  assert not st.error_flag
        st = parser("A_CDE");  assert not st.error_flag
        st = parser("AB_DE");  assert st.error_flag
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION
        st = parser("ABC_E");  assert st.error_flag
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION

        combined = Alternative(s2 + s1, RegExp('.*'))
        parser = Grammar(combined)
        st = parser("DEABC");  assert not st.error_flag
        st = parser("_EABC");  assert not st.error_flag
        st = parser("D_ABC");  assert not st.error_flag
        st = parser("DE_BC");  assert not st.error_flag
        st = parser("DEA_C");  assert not st.error_flag
        st = parser("DEAB_");  assert st.error_flag
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION

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
        prefixes = AllOf(Token("A"), Token("B"))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B A').content == 'B A'
        # aternative Form
        prefixes = AllOf(Series(Token("B"), Token("A")))
        assert Grammar(prefixes)('A B').content == 'A B'

    def test_allOf_completeness(self):
        """Test that an error is raised if not  all parsers of an AllOf-List
        match."""
        prefixes = AllOf(Token("A"), Token("B"))
        assert Grammar(prefixes)('B').error_flag

    def test_allOf_redundance(self):
        """Test that one and the same parser may be listed several times
        and must be matched several times accordingly."""
        prefixes = AllOf(Token("A"), Token("B"), Token("A"))
        assert Grammar(prefixes)('A A B').content == 'A A B'
        assert Grammar(prefixes)('A B A').content == 'A B A'
        assert Grammar(prefixes)('B A A').content == 'B A A'
        assert Grammar(prefixes)('A B B').error_flag

    def test_someOf_order(self):
        """Test that parsers of an AllOf-List can match in arbitrary order."""
        prefixes = SomeOf(Token("A"), Token("B"))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B A').content == 'B A'
        # aternative Form
        prefixes = SomeOf(Alternative(Token("B"), Token("A")))
        assert Grammar(prefixes)('A B').content == 'A B'
        assert Grammar(prefixes)('B').content == 'B'

    def test_someOf_redundance(self):
        """Test that one and the same parser may be listed several times
        and must be matched several times accordingly."""
        prefixes = SomeOf(Token("A"), Token("B"), Token("A"))
        assert Grammar(prefixes)('A A B').content == 'A A B'
        assert Grammar(prefixes)('A B A').content == 'A B A'
        assert Grammar(prefixes)('B A A').content == 'B A A'
        assert Grammar(prefixes)('A B B').error_flag


class TestPopRetrieve:
    mini_language = """
        document       = { text | codeblock }
        codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
        delimiter      = delimiter_sign  # never use delimiter between capture and pop except for retrival!
        delimiter_sign = /`+/
        text           = /[^`]+/
        """
    mini_lang2 = """
        @braces_filter=counterpart
        document       = { text | codeblock }
        codeblock      = braces { text | opening_braces | (!:braces closing_braces) } ::braces
        braces         = opening_braces
        opening_braces = /\{+/
        closing_braces = /\}+/
        text           = /[^{}]+/
        """
    mini_lang3 = """
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
        return node.tag_name == name and not isinstance(node.parser, Retrieve)

    @staticmethod
    def closing_delimiter(node):
        return isinstance(node.parser, Retrieve)

    def test_compile_mini_language(self):
        assert self.minilang_parser
        assert self.minilang_parser2
        assert self.minilang_parser3

    def test_stackhandling(self):
        ambigous_opening = "<ABCnormal> normal tag <ABCnormal*>"
        syntax_tree = self.minilang_parser3(ambigous_opening)
        assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())

        ambigous_opening = "<ABCnormal> normal tag <ABCnormal/>"
        syntax_tree = self.minilang_parser3(ambigous_opening)
        assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())

        forgot_closing_tag = "<em> where is the closing tag?"
        syntax_tree = self.minilang_parser3(forgot_closing_tag)
        assert syntax_tree.error_flag, str(syntax_tree.collect_errors())

        proper = "<em> has closing tag <em/>"
        syntax_tree = self.minilang_parser3(proper)
        assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())

        proper = "<em> has closing tag <em*>"
        syntax_tree = self.minilang_parser3(proper)
        assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())

    def test_cache_neutrality(self):
        """Test that packrat-caching does not interfere with the variable-
        changing parsers: Capture and Retrieve."""
        lang = """
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
        assert not st.error_flag, str(st.collect_errors())

    def test_single_line(self):
        teststr = "Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ende"
        syntax_tree = self.minilang_parser(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.select(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.select(self.closing_delimiter)))
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
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.select(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.select(self.closing_delimiter)))
        assert delim == pop
        if is_logging():
            log_ST(syntax_tree, "test_PopRetrieve_multi_line.cst")

    def test_single_line_complement(self):
        teststr = "Anfang {{{code block }} <- keine Ende-Zeichen ! }}} Ende"
        syntax_tree = self.minilang_parser2(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.select(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.select(self.closing_delimiter)))
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
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.select(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.select(self.closing_delimiter)))
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
        assert not cst.error_flag, str(cst.collect_errors())
        cst = self.parser(testcode2)
        assert not cst.error_flag
        cst = self.parser(testcode3)
        assert cst.error_flag


class TestBorderlineCases:
    def test_not_matching(self):
        minilang = """parser = /X/"""
        gr = grammar_provider(minilang)()
        cst = gr('X', 'parser')
        assert not cst.error_flag
        cst = gr(' ', 'parser')
        assert cst.error_flag
        cst = gr('', 'parser')
        assert cst.error_flag

    def test_matching(self):
        minilang = """parser = /.?/"""
        gr = grammar_provider(minilang)()
        cst = gr(' ', 'parser')
        assert not cst.error_flag
        cst = gr('  ', 'parser')
        assert cst.error_flag
        cst = gr('', 'parser')
        assert not cst.error_flag


class TestUnknownParserError:
    def test_unknown_parser_error(self):
        gr = Grammar()
        try:
            gr("", "NonExistantParser")
            assert False, "UnknownParserError expected!"
        except UnknownParserError:
            pass


if __name__ == "__main__":
    from DHParser.testing import runner
    with logging(False):
        runner("", globals())
