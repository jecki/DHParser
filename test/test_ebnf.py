#!/usr/bin/python3

"""test_ebnf.py - tests of the ebnf module of DHParser 
                             

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

from functools import partial
from multiprocessing import Pool
import sys
sys.path.extend(['../', './'])

from DHParser.toolkit import is_logging
from DHParser.parsers import compile_source, Retrieve, WHITESPACE_KEYWORD, nil_scanner
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, EBNFTransform, get_ebnf_compiler
from DHParser.dsl import compileEBNF, compileDSL


class TestDirectives:
    mini_language = """
        expression =  term  { ("+" | "-") term }
        term       =  factor  { ("*" | "/") factor }
        factor     =  constant | "("  expression  ")"
        constant   =  digit { digit } [ //~ ]
        digit      = /0/ | /1/ | /2/ | /3/ | /4/ | /5/ | /6/ | /7/ | /8/ | /9/ 
        """

    def test_whitespace_linefeed(self):
        lang = "@ whitespace = linefeed\n" + self.mini_language
        MinilangParser = compileEBNF(lang)
        parser = MinilangParser()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        # parser.log_parsing_history("WSP")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n * 12")
        # parser.log_parsing_history("WSPLF")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n \n * 12")
        assert syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n\n * 12")
        assert syntax_tree.collect_errors()

    def test_whitespace_vertical(self):
        lang = "@ whitespace = vertical\n" + self.mini_language
        parser = compileEBNF(lang)()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n \n * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n\n * 12")
        assert not syntax_tree.collect_errors()

    def test_whitespace_horizontal(self):
        lang = "@ whitespace = horizontal\n" + self.mini_language
        parser = compileEBNF(lang)()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n * 12")
        assert syntax_tree.collect_errors()


class TestEBNFParser:
    cases = {
        "list_": {
            "match": {
                1: "hund",
                2: "hund, katze,maus",
                3: "hund , katze"
            },
            "fail": {
                1: "123",
                2: '"literal"',
                3: "/regexp/"
            }
        }
    }


    def setup(self):
        self.EBNF = get_ebnf_grammar()

    def test_literal(self):
        snippet = '"literal" '
        result = self.EBNF(snippet, 'literal')
        assert not result.error_flag
        assert str(result) == snippet
        assert result.find(lambda node: str(node) == WHITESPACE_KEYWORD)

        result = self.EBNF(' "literal"', 'literal')
        assert result.error_flag  # literals catch following, but not leading whitespace




class TestPopRetrieve:
    mini_language = """
        document       = { text | codeblock }
        codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
        delimiter      = delimiter_sign  # never use delimiter between capture and retrieve!!!
        delimiter_sign = /`+/
        text           = /[^`]+/ 
        """
    mini_lang2 = """
        @retrieve_counterpart = braces
        document       = { text | codeblock }
        codeblock      = braces { text | opening_braces | (!:braces closing_braces) } ::braces
        braces         = opening_braces
        opening_braces = /\{+/
        closing_braces = /\}+/
        text           = /[^{}]+/
        """

    def setup(self):
        self.minilang_parser = compileEBNF(self.mini_language)()
        self.minilang_parser2 = compileEBNF(self.mini_lang2)()

    @staticmethod
    def opening_delimiter(node, name):
        return node.tag_name == name and not isinstance(node.parser, Retrieve)

    @staticmethod
    def closing_delimiter(node):
        return isinstance(node.parser, Retrieve)

    def test_compile_mini_language(self):
        assert self.minilang_parser
        assert self.minilang_parser2

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


class TestSemanticValidation:
    def check(self, minilang, bool_filter=lambda x: x):
        grammar = get_ebnf_grammar()
        st = grammar(minilang)
        assert not st.collect_errors()
        EBNFTransform(st)
        assert bool_filter(st.collect_errors())

    def test_illegal_nesting(self):
        self.check('impossible = { [ "an optional requirement" ] }')

    def test_illegal_nesting_option_required(self):
        self.check('impossible = [ §"an optional requirement" ]')

    def test_illegal_nesting_oneormore_option(self):
        self.check('impossible = { [ "no use"] }+')

    def test_legal_nesting(self):
        self.check('possible = { [ "+" ] "1" }', lambda x: not x)


class TestCompilerErrors:
    def test_error_propagation(self):
        ebnf = "@ literalws = wrongvalue  # testing error propagation\n"
        result, messages, st = compile_source(ebnf, None, get_ebnf_grammar(),
            get_ebnf_transformer(), get_ebnf_compiler('ErrorPropagationTest'))
        assert messages


class TestSelfHosting:
    grammar = r"""
        # EBNF-Grammar in EBNF

        @ comment    =  /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
        @ whitespace =  /\s*/                            # whitespace includes linefeed
        @ literalws  =  right                            # trailing whitespace of literals will be ignored tacitly

        syntax     =  [~//] { definition | directive } §EOF
        definition =  symbol §"=" expression
        directive  =  "@" §symbol §"=" ( regexp | literal | list_ )

        expression =  term { "|" term }
        term       =  { factor }+
        factor     =  [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
                    | [flowmarker] literal
                    | [flowmarker] regexp
                    | [flowmarker] group
                    | [flowmarker] regexchain
                    | [flowmarker] oneormore
                    | repetition
                    | option

        flowmarker =  "!"  | "&"  | "§" |                # '!' negative lookahead, '&' positive lookahead, '§' required
                      "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
        retrieveop =  "::" | ":"                         # '::' pop, ':' retrieve

        group      =  "(" expression §")"
        regexchain =  ">" expression §"<"                # compiles "expression" into a singular regular expression
        oneormore  =  "{" expression "}+"
        repetition =  "{" expression §"}"
        option     =  "[" expression §"]"

        link       = regexp | symbol | literal           # semantic restriction: symbol must evaluate to a regexp or chain

        symbol     =  /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
        literal    =  /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
                    | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
        regexp     =  /~?\/(?:[^\/]|(?<=\\)\/)*\/~?/~    # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                         # '~' is a whitespace-marker, if present leading or trailing
                                                         # whitespace of a regular expression will be ignored tacitly.
        list_      =  /\w+/~ { "," /\w+/~ }              # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                         # BEGIN_QUOTE, END_QUOTE ; see CommonMark/markdown.py for an exmaple
        EOF =  !/./        
        """

    def test_self(self):
        compiler_name = "EBNF"
        compiler = get_ebnf_compiler(compiler_name, self.grammar)
        parser = get_ebnf_grammar()
        result, errors, syntax_tree = compile_source(self.grammar, None, parser,
                                            get_ebnf_transformer(), compiler)
        assert not errors, str(errors)
        # compile the grammar again using the result of the previous
        # compilation as parser
        compileDSL(self.grammar, nil_scanner, result, get_ebnf_transformer(), compiler)

    def multiprocessing_task(self):
        compiler_name = "EBNF"
        compiler = get_ebnf_compiler(compiler_name, self.grammar)
        parser = get_ebnf_grammar()
        result, errors, syntax_tree = compile_source(self.grammar, None, parser,
                                            get_ebnf_transformer(), compiler)
        return errors

    def test_multiprocessing(self):
        with Pool(processes=2) as pool:
            res = [pool.apply_async(self.multiprocessing_task, ()) for i in range(4)]
            errors = [r.get(timeout=5) for r in res]
        for i, e in enumerate(errors):
            assert not e, ("%i: " % i) + str(e)


if __name__ == "__main__":
    from run import runner
    runner("", globals())
