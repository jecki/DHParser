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

import sys
from multiprocessing import Pool

sys.path.extend(['../', './'])

from DHParser.toolkit import compile_python_object, re
from DHParser.preprocess import nil_preprocessor
from DHParser import compile_source
from DHParser.error import has_errors
from DHParser.syntaxtree import WHITESPACE_PTYPE
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, EBNFTransform, get_ebnf_compiler
from DHParser.dsl import CompilationError, compileDSL, DHPARSER_IMPORTS, grammar_provider
from DHParser.testing import grammar_unit


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
        MinilangParser = grammar_provider(lang)
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
        parser = grammar_provider(lang)()
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
        parser = grammar_provider(lang)()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser("3 + 4 \n * 12")
        assert syntax_tree.collect_errors()


class TestReservedSymbols:
    def test_comment_usage(self):
        lang = r"""
        @comment = /#.*(?:\n|$)/
        document = text [ COMMENT__ ]
        text = /[^#]+/
        """
        parser = grammar_provider(lang)()

    def test_whitespace(self):
        lang = r"""
        @whitespace = /\s*/
        document = WSP__ { word WSP__ }
        word = /\w+/ 
        """
        parser = grammar_provider(lang)()

    def test_mixin(self):
        lang = r"""
        @comment = /#.*(?:\n|$)/
        @whitespace = /\s*/
        document = WSP__ { word WSP__ }
        word = /\w+/ 
        """
        parser = grammar_provider(lang)()
        result = parser("test # kommentar")
        assert not result.error_flag, str(result.as_sxpr())


class TestEBNFParser:
    cases = {
        "list_": {
            "match": {
                1: "hund",
                2: "hund, katze,maus",
                3: "hund , katze"
            },
            "fail": {
                4: "123",
                5: '"literal"',
                6: "/regexp/"
            }
        }
    }

    def setup(self):
        self.EBNF = get_ebnf_grammar()

    def test_RE(self):
        gr = get_ebnf_grammar()
        m = gr.regexp.main.regexp.match(r'/[\\\\]/ xxx /')
        rs = m.group()
        assert rs.find('x') < 0, rs.group()
        rx = re.compile(rs[1:-1])
        assert rx.match(r'\\')

    def test_literal(self):
        snippet = '"text" '
        result = self.EBNF(snippet, 'literal')
        assert not result.error_flag
        assert str(result) == snippet
        assert result.select(lambda node: node.parser.ptype == WHITESPACE_PTYPE)

        result = self.EBNF('"text" ', 'literal')
        assert not result.error_flag
        result = self.EBNF(' "text"', 'literal')
        assert result.error_flag  # literals catch following, but not leading whitespace

    def test_plaintext(self):
        result = self.EBNF('`plain`', 'plaintext')
        assert not result.error_flag

    def test_list(self):
        grammar_unit(self.cases, get_ebnf_grammar, get_ebnf_transformer)



class TestParserNameOverwriteBug:
    def test_term_bug(self):
        grammar = get_ebnf_grammar()
        st = grammar('impossible = [§"an optional requirement"]')
        # print(st.as_sxpr())
        get_ebnf_transformer()(st)
        # print(st.as_sxpr())
        lang = """series = "A" "B" §"C" "D"
        """
        parser = get_ebnf_grammar()
        st = grammar(lang)
        # print(st.as_sxpr())
        get_ebnf_transformer()(st)
        # print(st.as_sxpr())
        result = get_ebnf_compiler()(st)
        messages = st.collect_errors()
        assert not has_errors(messages), str(messages)


class TestSemanticValidation:
    def check(self, minilang, bool_filter=lambda x: x):
        grammar = get_ebnf_grammar()
        st = grammar(minilang)
        assert not st.collect_errors()
        EBNFTransform()(st)
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

    def test_undefined_symbols(self):
        """Use of undefined symbols should be reported.
        """
        ebnf = """syntax = { intermediary }
                  intermediary = "This symbol is " [ badly_spelled ] "!"
                  bedly_spilled = "wrong" """
        result, messages, st = compile_source(ebnf, None, get_ebnf_grammar(),
            get_ebnf_transformer(), get_ebnf_compiler('UndefinedSymbols'))
        assert messages

    def test_no_error(self):
        """But reserved symbols should not be repoted as undefined.
        """
        ebnf = """nothing =  WSP__ | COMMENT__\n"""
        result, messages, st = compile_source(ebnf, None, get_ebnf_grammar(),
            get_ebnf_transformer(), get_ebnf_compiler('UndefinedSymbols'))
        assert not bool(messages), messages


class TestSelfHosting:
    grammar = r"""
        # EBNF-Grammar in EBNF

        @ comment    =  /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
        @ whitespace =  /\s*/                            # whitespace includes linefeed
        @ literalws  =  right                            # trailing whitespace of literals will be ignored tacitly

        syntax     =  [~//] { definition | directive } §EOF
        definition =  symbol §"=" expression
        directive  =  "@" §symbol "=" ( regexp | literal | list_ )

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
        compileDSL(self.grammar, nil_preprocessor, result, get_ebnf_transformer(), compiler)

    def multiprocessing_task(self):
        compiler_name = "EBNF"
        compiler = get_ebnf_compiler(compiler_name, self.grammar)
        parser = get_ebnf_grammar()
        result, errors, syntax_tree = compile_source(self.grammar, None, parser,
                                            get_ebnf_transformer(), compiler)
        return errors

    def test_multiprocessing(self):
        with Pool() as pool:
            res = [pool.apply_async(self.multiprocessing_task, ()) for i in range(4)]
            errors = [r.get(timeout=10) for r in res]
        for i, e in enumerate(errors):
            assert not e, ("%i: " % i) + str(e)


class TestBoundaryCases:
    def setup(self):
        self.gr = get_ebnf_grammar()
        self.tr = get_ebnf_transformer()
        self.cp = get_ebnf_compiler()

    def test_empty_grammar(self):
        t = self.gr("")
        self.tr(t)
        r = self.cp(t)
        assert r

    def test_single_statement_grammar(self):
        t = self.gr("i = /i/")
        self.tr(t)
        r = self.cp(t)
        assert r

    def test_two_statement_grammar(self):
        t = self.gr("i = k {k}\nk = /k/")
        self.tr(t)
        r = self.cp(t)
        assert r

    def test_unconnected_symbols(self):
        ebnf = """root = /.*/
                  unconnected = /.*/
        """
        result, messages, AST = compile_source(ebnf, nil_preprocessor,
                                               get_ebnf_grammar(),
                                               get_ebnf_transformer(),
                                               get_ebnf_compiler())
        if messages:
            assert not has_errors(messages), "Unconnected rules should result in a warning, " \
                "not an error: " + str(messages)
            grammar_src = result
            grammar = compile_python_object(DHPARSER_IMPORTS + grammar_src,
                                            'get_(?:\w+_)?grammar$')()
        else:
            assert False, "EBNF compiler should warn about unconnected rules."

        assert grammar['root'], "Grammar objects should be subscriptable by parser names!"
        try:
            unconnected = grammar['unconnected']
        except KeyError:
            assert False, "Grammar objects should be able to cope with unconnected parsers!"
        try:
            nonexistant = grammar['nonexistant']
            assert False, "Grammar object shoul raise a KeyError if subscripted by " \
                          "a non-existant parser name!"
        except KeyError:
            pass


class TestSynonymDetection:
    def test_synonym_detection(self):
        ebnf = """a = b
                  b = /b/
        """
        grammar = grammar_provider(ebnf)()
        assert grammar['a'].name == 'a', grammar['a'].name
        assert grammar['b'].name == 'b', grammar['b'].name
        assert grammar('b').as_sxpr().count('b') == 2


class TestFlowControlOperators:
    def setup(self):
        self.t1 = """
        All work and no play 
        makes Jack a dull boy
        END
        """
        self.t2 = "All word and not play makes Jack a dull boy END\n"

    def test_lookbehind_indirect(self):
        lang = r"""
            document = ws sequence doc_end ws         
            sequence = { !end word ws }+
            doc_end  = -&SUCC_LB end        
            ws       = /\s*/
            end      = /END/
            word     = /\w+/
            SUCC_LB  = indirection
            indirection = /\s*?\n/
        """
        parser = grammar_provider(lang)()
        cst = parser(self.t1)
        assert not cst.error_flag, cst.as_sxpr()
        cst = parser(self.t2)
        # this should fail, because 'END' is not preceded by a line feed
        assert cst.error_flag, cst.as_sxpr()

    def test_required_error_reporting(self):
        """Tests whether failures to comply with the required operator '§'
        are correctly reported as such.
        """
        lang1 = "nonsense == /\w+/~  # wrong_equal_sign"
        lang2 = "nonsense = [^{}%]+  # someone forgot the '/'-delimiters for regular expressions"
        try:
            parser_class = grammar_provider(lang1)
            assert False, "Compilation error expected."
        except CompilationError as error:
            pass
        try:
            parser_class = grammar_provider(lang2)
            assert False, "Compilation error expected."
        except CompilationError as error:
            pass


class TestWhitespace:
    def test_whitespace(self):
        tail = r"""
            WORD     =  /\w+/~
            EOF      =  !/./
        """
        lang1 = r'document = "DOC" { WORD } EOF' + tail
        parser = grammar_provider(lang1)()
        cst = parser("DOC Wörter Wörter Wörter")
        assert not cst.error_flag
        cst = parser("DOCWörter Wörter Wörter")
        assert not cst.error_flag

        lang2 = r'document = `DOC` { WORD } EOF' + tail
        parser = grammar_provider(lang2)()
        cst = parser("DOC Wörter Wörter Wörter")
        assert cst.error_flag
        cst = parser("DOCWörter Wörter Wörter")
        assert not cst.error_flag

        lang3 = r'document = `DOC` ~ { WORD } EOF' + tail
        parser = grammar_provider(lang3)()
        cst = parser("DOC Wörter Wörter Wörter")
        assert not cst.error_flag
        cst = parser("DOCWörter Wörter Wörter")
        assert not cst.error_flag


class TestAllSome:
    def test_all(self):
        ebnf = 'prefix = <"A" "B">'
        grammar = grammar_provider(ebnf)()
        assert grammar('B A').content == 'B A'

    def test_some(self):
        ebnf = 'prefix = <"A" | "B">'
        grammar = grammar_provider(ebnf)()
        assert grammar('B A').content == 'B A'
        assert grammar('B').content == 'B'


if __name__ == "__main__":
    from DHParser.testing import runner

    runner("TestTermBug", globals())
