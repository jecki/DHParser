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

import os
import sys
from multiprocessing import Pool

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.toolkit import compile_python_object, re
from DHParser.preprocess import nil_preprocessor
from DHParser import compile_source
from DHParser.error import has_errors, Error
from DHParser.syntaxtree import WHITESPACE_PTYPE
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, EBNFTransform, \
    EBNFDirectives, get_ebnf_compiler, compile_ebnf, DHPARSER_IMPORTS
from DHParser.dsl import CompilationError, compileDSL, grammar_provider
from DHParser.testing import grammar_unit, clean_report


class TestDirectives:
    mini_language = """
        expression =  term  { ("+" | "-") term }
        term       =  factor  { ("*" | "/") factor }
        factor     =  constant | "("  expression  ")"
        constant   =  digit { digit } [ //~ ]
        digit      = /0/ | /1/ | /2/ | /3/ | /4/ | /5/ | /6/ | /7/ | /8/ | /9/ 
        """

    def test_EBNFDirectives_object(self):
        directives = EBNFDirectives()
        assert directives.keys()
        directives.tokens.add('Test')
        assert 'Test' in directives.tokens
        try:
            directives.nonsense = 'nonsense'
            assert False, 'Attribute error expected for illegal directive "nonsense"'
        except AttributeError:
            pass

    def test_whitespace_linefeed(self):
        lang = "@ whitespace = linefeed\n" + self.mini_language
        MinilangParser = grammar_provider(lang)
        parser = MinilangParser()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        # parser.log_parsing_history("WSP")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n * 12")
        # parser.log_parsing_history("WSPLF")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n \n * 12")
        assert syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n\n * 12")
        assert syntax_tree.errors_sorted

    def test_whitespace_vertical(self):
        lang = "@ whitespace = vertical\n" + self.mini_language
        parser = grammar_provider(lang)()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n * 12")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n \n * 12")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n\n * 12")
        assert not syntax_tree.errors_sorted

    def test_whitespace_horizontal(self):
        lang = "@ whitespace = horizontal\n" + self.mini_language
        parser = grammar_provider(lang)()
        assert parser
        syntax_tree = parser("3 + 4 * 12")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n * 12")
        assert syntax_tree.errors_sorted


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
        document = WSP_RE__ { word WSP_RE__ }
        word = /\w+/ 
        """
        parser = grammar_provider(lang)()

    def test_mixin(self):
        lang = r"""
        @comment = /#.*(?:\n|$)/
        @whitespace = /\s*/
        document = WSP_RE__ { word WSP_RE__ }
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
        self.save_dir = os.getcwd()
        os.chdir(scriptpath)
        self.EBNF = get_ebnf_grammar()

    def teardown(self):
        clean_report('REPORT_TestEBNFParser')
        os.chdir(self.save_dir)

    def test_RE(self):
        gr = get_ebnf_grammar()
        m = gr.regexp.parsers[0].regexp.match(r'/[\\\\]/ xxx /')
        rs = m.group()
        assert rs.find('x') < 0, rs.group()
        rx = re.compile(rs[1:-1])
        assert rx.match(r'\\')

    def test_literal(self):
        snippet = '"text" '
        result = self.EBNF(snippet, 'literal')
        assert not result.error_flag
        assert str(result) == snippet.strip()
        assert result.select_if(lambda node: node.parser.ptype == WHITESPACE_PTYPE)

        result = self.EBNF('"text" ', 'literal')
        assert not result.error_flag
        result = self.EBNF(' "text"', 'literal')
        assert result.error_flag  # literals catch following, but not leading whitespace

    def test_plaintext(self):
        result = self.EBNF('`plain`', 'plaintext')
        assert not result.error_flag

    def test_list(self):
        grammar_unit(self.cases, get_ebnf_grammar, get_ebnf_transformer, 'REPORT_TestEBNFParser')



class TestParserNameOverwriteBug:
    def test_term_bug(self):
        grammar = get_ebnf_grammar()
        st = grammar('impossible = [§"an optional requirement"]')
        get_ebnf_transformer()(st)
        lang = """series = "A" "B" §"C" "D"
        """
        parser = get_ebnf_grammar()
        st = grammar(lang)
        get_ebnf_transformer()(st)
        result = get_ebnf_compiler()(st)
        messages = st.errors_sorted
        assert not has_errors(messages), str(messages)

    def test_single_mandatory_bug(self):
        lang = """series = § /B/\n"""
        result, messages, ast = compile_ebnf(lang)
        assert result.find('Required') < 0
        parser = grammar_provider(lang)()
        st = parser('B')
        assert not st.error_flag



class TestSemanticValidation:
    def check(self, minilang, bool_filter=lambda x: x):
        grammar = get_ebnf_grammar()
        st = grammar(minilang)
        assert not st.errors_sorted
        EBNFTransform()(st)
        assert bool_filter(st.errors_sorted)

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
        # save = get_config_value('static_analysis')
        # set_config_value('static_analysis', 'early')

        ebnf = """syntax = { intermediary }
                  intermediary = "This symbol is " [ badly_spelled ] "!"
                  bedly_spilled = "wrong" """
        result, messages, st = compile_source(ebnf, None, get_ebnf_grammar(),
            get_ebnf_transformer(), get_ebnf_compiler('UndefinedSymbols'))
        assert messages

        # set_config_value('static_analysis', save)

    def test_no_error(self):
        """But reserved symbols should not be repoted as undefined.
        """
        ebnf = """nothing =  WSP_RE__ | COMMENT__\n"""
        result, messages, st = compile_source(ebnf, None, get_ebnf_grammar(),
            get_ebnf_transformer(), get_ebnf_compiler('UndefinedSymbols'))
        assert not bool(messages), messages


class TestSelfHosting:
    grammar = r"""
        # EBNF-Grammar in EBNF

        @ comment    = /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
        @ whitespace = /\s*/                            # whitespace includes linefeed
        @ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
        @ drop       = whitespace                       # no whitespace in concrete syntax tree
        
        syntax     = [~//] { definition | directive } §EOF
        definition = symbol §"=" expression
        directive  = "@" §symbol "=" (regexp | literal | symbol) { "," (regexp | literal | symbol) }
        
        expression = term { "|" term }
        term       = { ["§"] factor }+                       # "§" means all following factors mandatory
        factor     = [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
                   | [flowmarker] literal
                   | [flowmarker] plaintext
                   | [flowmarker] regexp
                   | [flowmarker] whitespace
                   | [flowmarker] oneormore
                   | [flowmarker] group
                   | [flowmarker] unordered
                   | repetition
                   | option
        
        flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
                   | "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
        retrieveop = "::" | ":"                         # '::' pop, ':' retrieve
        
        group      = "(" §expression ")"
        unordered  = "<" §expression ">"                # elements of expression in arbitrary order
        oneormore  = "{" expression "}+"
        repetition = "{" §expression "}"
        option     = "[" §expression "]"
        
        symbol     = /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
        literal    = /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
                   | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
        plaintext  = /`(?:[^"]|\\")*?`/~                # like literal but does not eat whitespace
        regexp     = /\/(?:\\(?:\/)|[^\/])*?\//~        # e.g. /\w+/, ~/#.*(?:\n|$)/~
        whitespace = /~/~                               # insignificant whitespace
        
        EOF = !/./
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
                                            r'get_(?:\w+_)?grammar$')()
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
        assert grammar['a'].pname == 'a', grammar['a'].pname
        assert grammar['b'].pname == 'b', grammar['b'].pname
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
        lang1 = r"nonsense == /\w+/~  # wrong_equal_sign "
        lang2 = "nonsense = [^{}%]+  # someone forgot the '/'-delimiters for regular expressions\n"
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


class TestErrorCustomization:
    """
    Customized Errors replace existing errors with alternative
    error codes and messages that are more helptful to the user.
    """
    def test_customized_mandatory_continuation(self):
        lang = """
            document = series | /.*/
            @series_error = "a user defined error message"
            series = "X" | head §"C" "D"
            head = "A" "B"
            """
        parser = grammar_provider(lang)()
        st = parser("X");  assert not st.error_flag
        st = parser("ABCD");  assert not st.error_flag
        st = parser("A_CD");  assert not st.error_flag
        st = parser("AB_D");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "a user defined error message"
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "a user defined error message"

    def test_customized_error_case_sensitive(self):
        lang = """
            document = Series | /.*/
            @Series_error = "a user defined error message"
            Series = "X" | head §"C" "D"
            head = "A" "B"
            """
        parser = grammar_provider(lang)()
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "a user defined error message"

    def test_multiple_error_messages(self):
        lang = r"""
            document = series | /.*/
            @series_error = '_', "the underscore is wrong in this place"
            @series_error = '*', "the asterix is wrong in this place"
            @series_error = /(?<=C)\w/, 'C cannot be followed by {0}'
            @series_error = /\w/, "wrong letter {0} in place of {1}"
            @series_error = "fallback error message"
            series = "X" | head §"C" "D"
            head = "A" "B"
            """
        parser = grammar_provider(lang)()
        st = parser("AB*D");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "the asterix is wrong in this place"
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "the underscore is wrong in this place"
        st = parser("ABiD");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message.startswith('wrong letter')
        st = parser("AB+D");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "fallback error message"
        st = parser("ABCi");  assert st.error_flag
        assert st.errors_sorted[0].code == Error.MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message.startswith('C cannot be followed by')


class TestErrorCustomizationErrors:
    def test_ambiguous_error_customization(self):
        lang = """
            document = series 
            @series_error = "ambiguous error message: does it apply to first or second '§'?"
            series = "A" § "B" "C" | "X" § "Y" "Z" 
            """
        try:
            parser = grammar_provider(lang)()
            assert False, "CompilationError because of ambiguous error message exptected!"
        except CompilationError as compilation_error:
            err = compilation_error.errors[0]
            assert err.code == Error.AMBIGUOUS_ERROR_HANDLING, str(compilation_error)

    def test_unsed_error_customization(self):
        lang = """
            document = series | other
            @other_error = "a user defined error message"
            series = "A" § "B" "C"
            other = "X" | "Y" | "Z"
            """
        result, messages, ast = compile_ebnf(lang)
        assert messages[0].code == Error.UNUSED_ERROR_HANDLING_WARNING

    def test_multiple_resume_definitions(self):
        lang = """
            document = series
            @series_resume = /B/, /C/, /D/, /E/, /F/, /G/
            @series_resume = /X/, /Y/
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        result, messages, ast = compile_ebnf(lang)
        assert messages[0].code == Error.REDEFINED_DIRECTIVE

    def test_multiple_skip_definitions(self):
        lang = """
            document = series
            @series_skip = /B/, /C/, /D/, /E/, /F/, /G/
            @series_skip = /X/, /Y/
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        result, messages, ast = compile_ebnf(lang)
        assert messages[0].code == Error.REDEFINED_DIRECTIVE


class TestCustomizedResumeParsing:
    def setup(self):
        lang = r"""
            @ alpha_resume = 'BETA', GAMMA_STR
            @ beta_resume = GAMMA_RE
            @ bac_resume = /GA\w+/
            document = alpha [beta] gamma "."
            alpha = "ALPHA" abc
                abc = §"a" "b" "c"
              beta = "BETA" (bac | bca)
                bac = "b" "a" §"c"
                bca = "b" "c" §"a"
              gamma = "GAMMA" §(cab | cba)
                cab = "c" "a" §"b"
                cba = "c" "b" §"a"
            GAMMA_RE = /GA\w+/
            GAMMA_STR = "GAMMA"
            """
        self.gr = grammar_provider(lang)()

    def test_several_resume_rules_innermost_rule_matching(self):
        gr = self.gr
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        # print(cst.as_sxpr())
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only on error message
        assert len(cst.errors_sorted) == 1

        content = 'ALPHA acb BETA bad GAMMA cab .'
        cst = gr(content)
        # print(cst.as_sxpr())
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only on error message
        assert len(cst.errors_sorted) == 2

        content = 'ALPHA acb GAMMA cab .'
        cst = gr(content)
        # print(cst.as_sxpr())
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only on error message
        assert len(cst.errors_sorted) == 1


class TestInSeriesResume:
    def setup(self):
        lang = """
            document = series
            @series_skip = /B/, /C/, /D/, /E/, /F/, /G/
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        self.gr = grammar_provider(lang)()

    def test_garbage_in_series(self):
        st = self.gr('ABCDEFG')
        assert not st.error_flag
        st = self.gr('AB XYZ CDEFG')
        errors = st.errors_sorted
        assert len(errors) == 1 and errors[0].code == Error.MANDATORY_CONTINUATION
        st = self.gr('AB XYZ CDE XYZ FG')
        errors = st.errors_sorted
        assert len(errors) == 2 and all(err.code == Error.MANDATORY_CONTINUATION for err in errors)
        st = self.gr('AB XYZ CDE XNZ FG')  # fails to resume parsing
        errors = st.errors_sorted
        assert len(errors) >= 1 and errors[0].code == Error.MANDATORY_CONTINUATION

    def test_series_gap(self):
        st = self.gr('ABDEFG')
        errors = st.errors_sorted
        assert len(errors) == 1 and errors[0].code == Error.MANDATORY_CONTINUATION
        st = self.gr('ABXEFG')  # two missing, one wrong element added
        errors = st.errors_sorted
        assert len(errors) == 2 and all(err.code == Error.MANDATORY_CONTINUATION for err in errors)
        st = self.gr('AB_DE_G')
        errors = st.errors_sorted
        assert len(errors) == 2 and all(err.code == Error.MANDATORY_CONTINUATION for err in errors)

    def test_series_permutation(self):
        st = self.gr('ABEDFG')
        errors = st.errors_sorted
        assert len(errors) >= 1  # cannot really recover from permutation errors


class TestAllOfResume:
    def setup(self):
        lang = """
            document = allof
            @ allof_error = '{} erwartet, {} gefunden :-('
            @ allof_skip = /A/, /B/, /C/, /D/, /E/, /F/, /G/
            allof = < "A" "B" § "C" "D" "E" "F" "G" >
        """
        self.gr = grammar_provider(lang)()

    def test_garbage_added(self):
        st = self.gr('GFCBAED')
        assert not st.error_flag
        st = self.gr('GFCB XYZ AED')
        errors = st.errors_sorted
        assert errors[0].code == Error.MANDATORY_CONTINUATION
        assert str(errors[0]).find(':-(') >= 0


    def test_allof_resume_later(self):
        lang = """
            document = flow "."
            @ flow_resume = '.'
            flow = allof | series
            @ allof_error = '{} erwartet, {} gefunden :-('
            allof = < "A" "B" § "C" "D" "E" "F" "G" >
            series = "E" "X" "Y" "Z"
        """
        gr = grammar_provider(lang)()
        st = gr('GFCBAED.')
        assert not st.error_flag
        st = gr('GFCBAED.')
        assert not st.error_flag
        st = gr('EXYZ.')
        assert not st.error_flag
        st = gr('EDXYZ.')
        assert st.error_flag
        assert len(st.errors_sorted) == 1
        st = gr('FCB_GAED.')
        assert len(st.errors_sorted) == 1


    def test_complex_resume_task(self):
        lang = """
            document = flow { flow } "."
            @ flow_resume = '.'
            flow = allof | series
            @ allof_error = '{} erwartet, {} gefunden :-('
            @ allof_resume = 'E', 'A'
            allof = < "A" "B" § "C" "D" "E" "F" "G" >
            @ series_resume = 'E', 'A'
            series = "E" "X" §"Y" "Z"
        """
        gr = grammar_provider(lang)()
        st = gr('GFCBAED.')
        assert not st.error_flag
        st = gr('GFCBAED.')
        assert not st.error_flag
        st = gr('EXYZ.')
        assert not st.error_flag
        st = gr('EDXYZ.')
        assert st.error_flag
        assert len(st.errors_sorted) == 1
        st = gr('FCB_GAED.')
        assert len(st.errors_sorted) == 2
        st = gr('EXY EXYZ.')
        assert len(st.errors_sorted) == 1


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
