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

from DHParser.toolkit import is_logging, logging, compile_python_object
from DHParser.syntaxtree import traverse, remove_expendables, \
    replace_by_single_child, reduce_single_child, flatten, TOKEN_PTYPE
from DHParser.parsers import compile_source, Retrieve
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.dsl import parser_factory, DHPARSER_IMPORTS


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


class TestInfiLoopsAndRecursion:
    def test_direct_left_recursion(self):
        minilang = ARITHMETIC_EBNF
        snippet = "5 + 3 * 4"
        parser = parser_factory(minilang)()
        assert parser
        syntax_tree = parser(snippet)
        assert not syntax_tree.collect_errors()
        assert snippet == str(syntax_tree)
        if is_logging():
            syntax_tree.log("test_LeftRecursion_direct.cst")
            # self.minilang_parser1.log_parsing_history("test_LeftRecursion_direct")

    def test_indirect_left_recursion(self):
        pass

    def test_inifinite_loops(self):
        minilang = """not_forever = { // } \n"""
        snippet = " "
        parser = parser_factory(minilang)()
        syntax_tree = parser(snippet)
        assert syntax_tree.error_flag
        # print(syntax_tree.collect_errors())


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
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        node, rest = parser.regex('abc+def')
        assert rest == ''
        assert node.parser.name == "regex"
        assert str(node) == 'abc+def'

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


class TestPopRetrieve:
    mini_language = """
        document       = { text | codeblock }
        codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
        delimiter      = delimiter_sign  # never use delimiter between capture and retrieve!!!
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
        self.minilang_parser = parser_factory(self.mini_language)()
        self.minilang_parser2 = parser_factory(self.mini_lang2)()
        self.minilang_parser3 = parser_factory(self.mini_lang3)()

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


    def test_single_line(self):
        teststr = "Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ende"
        syntax_tree = self.minilang_parser(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert delim == pop
        if is_logging():
            syntax_tree.log("test_PopRetrieve_single_line.cst")

    def test_multi_line(self):
        teststr = """
            Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ebde

            Absatz ohne ``` codeblock, aber
            das stellt sich erst am Ende herause...

            Mehrzeliger ```code block
            """
        syntax_tree = self.minilang_parser(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert delim == pop
        if is_logging():
            syntax_tree.log("test_PopRetrieve_multi_line.cst")

    def test_single_line_complement(self):
        teststr = "Anfang {{{code block }} <- keine Ende-Zeichen ! }}} Ende"
        syntax_tree = self.minilang_parser2(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert len(delim) == len(pop) and delim != pop
        if is_logging():
            syntax_tree.log("test_PopRetrieve_single_line.cst")

    def test_multi_line_complement(self):
        teststr = """
            Anfang {{{code block {{ <- keine Ende-Zeichen ! }}} Ende

            Absatz ohne {{{ codeblock, aber
            das stellt sich erst am Ende heraus...

            Mehrzeliger }}}code block
            """
        syntax_tree = self.minilang_parser2(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert len(delim) == len(pop) and delim != pop
        if is_logging():
            syntax_tree.log("test_PopRetrieve_multi_line.cst")


class TestWhitespaceHandling:
    minilang = """@testing = True
        doc = A B
        A = "A"
        B = "B"
        Rdoc = ar br
        ar = /A/
        br = /B/
        """

    def setup(self):
        self.gr = parser_factory(self.minilang)()

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


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
