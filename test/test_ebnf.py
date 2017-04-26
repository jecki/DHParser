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
import os
import sys
sys.path.append(os.path.abspath('../../'))
from DHParser.parsers import full_compilation, Retrieve, WHITESPACE_KEYWORD, nil_scanner
from DHParser.ebnf import EBNFGrammar, EBNFTransform, EBNFCompiler
from DHParser.dsl import compileEBNF, compileDSL


WRITE_LOGS = True


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
        syntax_tree = parser.parse("3 + 4 * 12")
        # parser.log_parsing_history("WSP")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n * 12")
        # parser.log_parsing_history("WSPLF")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n \n * 12")
        assert syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n\n * 12")
        assert syntax_tree.collect_errors()

    def test_whitespace_vertical(self):
        lang = "@ whitespace = vertical\n" + self.mini_language
        parser = compileEBNF(lang)()
        assert parser
        syntax_tree = parser.parse("3 + 4 * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n \n * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n\n * 12")
        assert not syntax_tree.collect_errors()

    def test_whitespace_horizontal(self):
        lang = "@ whitespace = horizontal\n" + self.mini_language
        parser = compileEBNF(lang)()
        assert parser
        syntax_tree = parser.parse("3 + 4 * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n * 12")
        assert syntax_tree.collect_errors()


class TestEBNFParser:
    test_json = {
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
        self.EBNF = EBNFGrammar()

    def test_literal(self):
        snippet = '"literal" '
        result = self.EBNF.parse(snippet, 'literal')
        assert not result.error_flag
        assert str(result) == snippet
        assert result.find(lambda node: str(node) == WHITESPACE_KEYWORD)

        result = self.EBNF.parse(' "literal"', 'literal')
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
        syntax_tree = self.minilang_parser.parse(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert delim == pop
        if WRITE_LOGS:
            syntax_tree.log("test_PopRetrieve_single_line", '.cst')

    def test_multi_line(self):
        teststr = """
            Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ebde

            Absatz ohne ``` codeblock, aber
            das stellt sich erst am Ende herause...

            Mehrzeliger ```code block
            """
        syntax_tree = self.minilang_parser.parse(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="delimiter"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert delim == pop
        if WRITE_LOGS:
            syntax_tree.log("test_PopRetrieve_multi_line", '.cst')

    def test_single_line_complement(self):
        teststr = "Anfang {{{code block }} <- keine Ende-Zeichen ! }}} Ende"
        syntax_tree = self.minilang_parser2.parse(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert len(delim) == len(pop) and delim != pop
        if WRITE_LOGS:
            syntax_tree.log("test_PopRetrieve_single_line", '.cst')

    def test_multi_line_complement(self):
        teststr = """
            Anfang {{{code block {{ <- keine Ende-Zeichen ! }}} Ende

            Absatz ohne {{{ codeblock, aber
            das stellt sich erst am Ende heraus...

            Mehrzeliger }}}code block
            """
        syntax_tree = self.minilang_parser2.parse(teststr)
        assert not syntax_tree.collect_errors()
        delim = str(next(syntax_tree.find(partial(self.opening_delimiter, name="braces"))))
        pop = str(next(syntax_tree.find(self.closing_delimiter)))
        assert len(delim) == len(pop) and delim != pop
        if WRITE_LOGS:
            syntax_tree.log("test_PopRetrieve_multi_line", '.cst')


class TestSemanticValidation:
    def check(self, minilang, bool_filter=lambda x: x):
        grammar = EBNFGrammar()
        st = grammar.parse(minilang)
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
        result, messages, st = full_compilation(ebnf, None, EBNFGrammar(), EBNFTransform,
                                                EBNFCompiler('ErrorPropagationTest'))
        assert messages


class TestSelfHosting:
    def test_self(self):
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
        compiler_name = "EBNF"
        compiler = EBNFCompiler(compiler_name, grammar)
        parser = EBNFGrammar()
        result, errors, syntax_tree = full_compilation(grammar, None, parser,
                                                       EBNFTransform, compiler)
        assert not errors, str(errors)
        # compile the grammar again using the result of the previous
        # compilation as parser
        compileDSL(grammar, nil_scanner, result, EBNFTransform, compiler)



if __name__ == "__main__":
    from run import runner
    runner("", globals())
