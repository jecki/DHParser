#!/usr/bin/env python3

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
scriptpath = os.path.abspath(scriptpath)

from DHParser.toolkit import compile_python_object, re, \
    normalize_circular_path
from DHParser.preprocess import nil_preprocessor
from DHParser import compile_source, INFINITE, Interleave
from DHParser.configuration import get_config_value, set_config_value
from DHParser.error import has_errors, MANDATORY_CONTINUATION, PARSER_STOPPED_BEFORE_END, \
    REDEFINED_DIRECTIVE, UNUSED_ERROR_HANDLING_WARNING, AMBIGUOUS_ERROR_HANDLING, \
    REORDERING_OF_ALTERNATIVES_REQUIRED, BAD_ORDER_OF_ALTERNATIVES, UNCONNECTED_SYMBOL_WARNING, \
    PEG_EXPRESSION_IN_DIRECTIVE_WO_BRACKETS, ERROR, WARNING, \
    ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING, canonical_error_strings
from DHParser.nodetree import WHITESPACE_PTYPE, flatten_sxpr
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, EBNFTransform, \
    EBNFDirectives, get_ebnf_compiler, compile_ebnf, DHPARSER_IMPORTS, parse_ebnf, \
    transform_ebnf, HeuristicEBNFGrammar, ConfigurableEBNFGrammar
from DHParser.dsl import CompilationError, compileDSL, create_parser, grammar_provider, raw_compileEBNF
from DHParser.testing import grammar_unit, clean_report, unique_name
from DHParser.trace import set_tracer, trace_history


class TestDirectives:
    mini_language = """
        @ literalws = right
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

    def test_whitespace_comments(self):
        lang = "@whitespace = linefeed\n@comment = /%.*/\n" + self.mini_language
        MinilangParser = grammar_provider(lang)
        parser = MinilangParser()
        assert parser
        syntax_tree = parser("3 + 4 \n \n * 12")
        assert syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n  %comment \n * 12")
        assert not syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n  %comment\n\n * 12")
        assert syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n\n%comment\n * 12")
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

    def test_nocomment(self):
        lang = r"""
            @ whitespace  = /\s*/           # insignificant whitespace, signified by ~
            @ literalws   = none            # literals have no implicit whitespace
            @ comment     = //              # no implicit comments
            @ ignorecase  = False           # literals and regular expressions are case-sensitive
            @ drop        = strings, whitespace
            
            document      = `` "" '' //
        """
        parser = create_parser(lang)
        st = parser('')
        assert not st.errors and str(st) == ''

    def test_drop(self):
        lang = r"""
            @ drop = backticked, whitespace
            @ literalws = right
            doc  = "*" word `*`
            word = /\w+/
        """
        parser = create_parser(lang)
        st = parser('* Hund*')
        assert str(st) == "*Hund"

    def test_drop_error_messages(self):
        lang = r'''
        @disposable = A
        @drop = A, B
        A = { B }
        B = 'x'
        '''
        _, errors, _ = compile_ebnf(lang)
        assert len(errors) == 1
        assert errors[0].message.startswith('''Illegal value "B" for Directive "@ drop"!''')
        assert errors[0].message.endswith('''where the "@disposable"-directive must precede the @drop-directive.''')
        lang = r'''
        @disposable = /[A]/
        @drop = A, B
        A = { B }
        B = 'x'
        '''
        _, errors, _ = compile_ebnf(lang)
        assert errors[0].message.find('or a string matching') >= 0


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

    EBNF = get_ebnf_grammar()

    def setup(self):
        self.save_dir = os.getcwd()
        os.chdir(scriptpath)

    def teardown(self):
        clean_report('REPORT_TestEBNFParser')
        os.chdir(self.save_dir)

    def test_RE(self):
        gr = get_ebnf_grammar()
        m = gr.regexp.parsers[1].regexp.match(r'[\\\\]/ xxx ')
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

    def test_regex_start_end_marker_usable(self):
        """Regular expression begin and end-marker really match only at
        the document start and ending!"""
        lang = '''
        doc = BEGIN !END A !BEGIN !END B !BEGIN END
        A = "A"
        B = "B"
        BEGIN = /^/
        END = /$/
        '''
        parser = create_parser(lang)
        result = parser('AB')
        assert flatten_sxpr(result.as_sxpr()) == '(doc (BEGIN) (A "A") (B "B") (END))'


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
        ebnf = """syntax = { intermediary }
                  intermediary = "This symbol is " [ badly_spelled ] "!"
                  bedly_spilled = "wrong" """
        result, messages, st = compile_source(ebnf, None, get_ebnf_grammar(),
            get_ebnf_transformer(), get_ebnf_compiler('UndefinedSymbols'))
        assert messages

    def test_no_error(self):
        """But reserved symbols should not be reported as undefined.
        """
        ebnf = """nothing =  WSP_RE__ | COMMENT__\n"""
        result, messages, st = compile_source(
            ebnf, None, get_ebnf_grammar(), get_ebnf_transformer(),
            get_ebnf_compiler('UndefinedSymbols'))
        assert not bool(messages), messages

    def test_unconnected_symbols(self):
        ebnf = """
            root = "ROOT" | connected
            connected = "CONNECTED"
            unconnected = "UNCONNECTED (warning expected)"
        """
        result, messages, st = compile_source(
            ebnf, None, get_ebnf_grammar(), get_ebnf_transformer(),
            get_ebnf_compiler('UndefinedSymbols'), preserve_AST=False)
        assert len(messages) == 1
        assert messages[0].code == UNCONNECTED_SYMBOL_WARNING

    def test_unconnected_symbols_corrupted_source(self):
        ebnf = """
            noroot
            root = "ROOT" | connected
            connected = "CONNECTED"
            unconnected = "UNCONNECTED (warning expected)"
        """
        result, messages, st = compile_source(
            ebnf, None, get_ebnf_grammar(), get_ebnf_transformer(),
            get_ebnf_compiler('UndefinedSymbols'), preserve_AST=True)
        assert any(m.code >= ERROR for m in messages)


EBNF = r"""
# EBNF-Grammar in EBNF

@ comment    = /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
@ whitespace = /\s*/                            # whitespace includes linefeed
@ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
@ drop       = whitespace                       # do not include whitespace in concrete syntax tree
@ disposable = pure_elem, element

#: top-level

syntax     = [~//] { definition | directive } §EOF
definition = symbol §"=" expression
directive  = "@" §symbol "="
             (regexp | literal | symbol)
             { "," (regexp | literal | symbol) }

#: components

expression = sequence { "|" sequence }
sequence   = { ["§"] ( interleave | lookaround ) }+  # "§" means all following terms mandatory
interleave = term { "°" ["§"] term }
lookaround = flowmarker (oneormore | pure_elem)
term       = oneormore | repetition | option | pure_elem

#: elements

pure_elem  = element § !/[?*+]/                 # element strictly without a suffix
element    = [retrieveop] symbol !"="           # negative lookahead to be sure it's not a definition
           | literal
           | plaintext
           | regexp
           | whitespace
           | group

#: flow-operators

flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
           | "<-!" | "<-&"                      # '<-' negative lookbehind, '<-&' positive lookbehind
retrieveop = "::" | ":?" | ":"                  # '::' pop, ':?' optional pop, ':' retrieve

#: groups

group      = "(" §expression ")"
oneormore  = "{" expression "}+" | element "+"
repetition = "{" §expression "}" | element "*"
option     = "[" §expression "]" | element "?"

#: leaf-elements

symbol     = /(?!\d)\w+/~                       # e.g. expression, term, parameter_list
literal    = /"(?:(?<!\\)\\"|[^"])*?"/~         # e.g. "(", '+', 'while'
           | /'(?:(?<!\\)\\'|[^'])*?'/~         # whitespace following literals will be ignored tacitly.
plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~         # like literal but does not eat whitespace
regexp     = RE_LEADIN RE_CORE RE_LEADOUT ~      # e.g. /\w+/, ~/#.*(?:\n|$)/~
whitespace = /~/~                               # insignificant whitespace

RE_LEADIN  = `/`
RE_LEADOUT = `/`
RE_CORE    = /(?:(?<!\\)\\(?:\/)|[^\/])*/ 

EOF = !/./
"""


class TestSelfHosting:
    def test_self(self):
        compiler_name = "EBNF"
        compiler = get_ebnf_compiler(compiler_name, EBNF)
        parser = get_ebnf_grammar()
        result, errors, syntax_tree = compile_source(
            EBNF, None, parser, get_ebnf_transformer(), compiler)
        assert not errors, str(errors)
        # compile the grammar again using the result of the previous
        # compilation as parser
        compileDSL(EBNF, nil_preprocessor, result, get_ebnf_transformer(), compiler)

    def multiprocessing_task(self):
        compiler_name = "EBNF"
        compiler = get_ebnf_compiler(compiler_name, EBNF)
        parser = get_ebnf_grammar()
        result, errors, syntax_tree = compile_source(EBNF, None, parser,
                                            get_ebnf_transformer(), compiler)
        return errors

    def test_multiprocessing(self):
        with Pool() as pool:
            res = [pool.apply_async(self.multiprocessing_task, ()) for i in range(4)]
            errors = [r.get(timeout=10) for r in res]
        for i, e in enumerate(errors):
            assert not e, ("%i: " % i) + str(e)


class TestBoundaryCases:
    gr = get_ebnf_grammar()
    tr = get_ebnf_transformer()
    cp = get_ebnf_compiler()

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
            grammar = compile_python_object(
                DHPARSER_IMPORTS + grammar_src, #.format(dhparser_parentdir=repr('.')) + grammar_src,
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
            assert False, "Grammar object should raise an AttributeError if subscripted by " \
                          "a non-existant parser name!"
        except AttributeError:
            pass


class TestSynonymDetection:
    def test_synonym_detection(self):
        ebnf = """a = b
                  b = /b/
        """
        grammar = grammar_provider(ebnf)()
        assert grammar['a'].pname == 'a', grammar['a'].pname
        assert grammar['b'].pname == 'b', grammar['b'].pname
        assert grammar('b').as_sxpr() == '(a (b "b"))'

    def test_synonym_anonymous_elimination(self):
        ebnf = r"""@ disposable = /_\w+$/
                  a = _b
                  _b = /b/
        """
        grammar = grammar_provider(ebnf)()
        assert not grammar['a'].disposable
        assert grammar['_b'].disposable
        assert grammar['a'].pname == 'a', grammar['a'].pname
        assert grammar['_b'].pname == '_b', grammar['_b'].pname
        assert grammar('b').as_sxpr() == '(a "b")', grammar('b').as_sxpr()


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
            doc_end  = <-&SUCC_LB end        
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
        lang2 = "nonsense = [ ^{}%]+  # someone forgot the '/'-delimiters for regular expressions\n"
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
        lang1 = '@literalws=right\ndocument = "DOC" { WORD } EOF' + tail
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


class TestInterleave:
    def test_counted(self):
        ebnf = '@literalws=right\n'\
               'test   = form_1 | form_2 | form_3 | form_4 | "non optional" form_5 | form_6\n' \
               'form_1 = "a"{2,4}\n' \
               'form_2 = "b"{3}\n' \
               'form_3 = "c"*3\n' \
               'form_4 = 2*"d"\n' \
               'form_5 = ["e"]*3\n' \
               'form_6 = 5*{"f"}+'
        grammar = create_parser(ebnf)
        assert grammar.form_6.repetitions == (5, INFINITE)
        assert grammar.form_5.repetitions == (0, 3)
        assert grammar.form_4.repetitions == (2, 2)
        assert grammar.form_3.repetitions == (3, 3)
        assert grammar.form_2.repetitions == (3, 3)
        assert grammar.form_1.repetitions == (2, 4)
        st = grammar('a')
        assert st.errors
        st = grammar('aaaaa')
        assert st.errors
        st = grammar('aaaa')
        assert not st.errors
        st = grammar('bbb')
        assert not st.errors

    def test_illegal_multiplier(self):
        lang = '@literalws=right\ndoc = "a" * 3'
        st = parse_ebnf(lang)
        assert not st.errors
        lang_wrong = 'doc = "a" * 0'
        st = parse_ebnf(lang_wrong)
        assert st.errors

    def test_all(self):
        ebnf = 'prefix = "A" ° "B"'
        grammar = grammar_provider(ebnf)()
        assert len(grammar.prefix.parsers) > 1
        tree = grammar('B A')
        assert tree.content == 'B A'
        assert tree.errors

        ebnf = '@literalws=right\nprefix = "A" ° "B"'
        grammar = grammar_provider(ebnf)()
        assert len(grammar.prefix.parsers) > 1
        assert grammar('B A').error_safe().content == 'B A'
        assert grammar('A B').error_safe().content == 'A B'

    def test_some(self):
        ebnf = '@literalws=right\nprefix = "A"? ° "B"?'
        grammar = grammar_provider(ebnf)()
        assert len(grammar.prefix.parsers) > 1
        assert grammar('B A').error_safe().content == 'B A'
        assert grammar('B').error_safe().content == 'B'
        result = grammar('')
        assert result.content == '' and not result.errors

    def test_interleave_counted(self):
        ebnf = '@literalws=right\nprefix = "A"{1,5} ° "B"{2,3}'
        grammar = create_parser(ebnf)
        assert isinstance(grammar.prefix, Interleave)
        assert grammar.prefix.repetitions == [(1, 5), (2, 3)]
        st = grammar('ABABA')
        assert not st.errors
        st = grammar('BBA')
        assert not st.errors

    def test_grouping_1(self):
        ebnf = '@literalws=right\nprefix = ("A"{1,5}) ° ("B"{2,3})'
        grammar = create_parser(ebnf)
        assert isinstance(grammar.prefix, Interleave)
        assert grammar.prefix.repetitions == [(1, 1), (1, 1)]
        st = grammar('ABABA')
        assert st.errors
        st = grammar('BBA')
        assert not st.errors

    def test_grouping_2(self):
        ebnf = '@literalws=right\nprefix = ("A"{1,5}) ° ("B"{2,3})'
        grammar = create_parser(ebnf)
        assert isinstance(grammar.prefix, Interleave)
        assert grammar.prefix.repetitions == [(1, 1), (1, 1)]
        st = grammar('ABABA')
        assert st.errors
        st = grammar('BBA')
        assert not st.errors


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
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "a user defined error message"
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
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
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
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
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "the asterix is wrong in this place"
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "the underscore is wrong in this place"
        st = parser("ABiD");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message.startswith('wrong letter')
        st = parser("AB+D");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
        assert st.errors_sorted[0].message == "fallback error message"
        st = parser("ABCi");  assert st.error_flag
        assert st.errors_sorted[0].code == MANDATORY_CONTINUATION
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
            assert err.code == AMBIGUOUS_ERROR_HANDLING, str(compilation_error)

    def test_unsed_error_customization(self):
        lang = """
            document = series | other
            @other_error = "a user defined error message"
            series = "A" § "B" "C"
            other = "X" | "Y" | "Z"
            """
        result, messages, ast = compile_ebnf(lang)
        assert messages[0].code == UNUSED_ERROR_HANDLING_WARNING

    def test_indirect_mandatory_marker(self):
        lang = r"""
            @comment = /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/
            document = alles

            @alles_skip = /E|3|$/
            alles = (anfang | "1") (mitte | "2") (ende | "3") [COMMENT__]

            @anfang_resume = /M|2/
            anfang = `A` §"NFANG"

            @mitte_resume = /E|3/
            mitte = `M` §"ITTE"

            ende = "ENDE"
        """
        assert lang.find("@mitte_") >= 0
        result, messages, ast = compile_ebnf(lang)
        assert any(m.code == UNUSED_ERROR_HANDLING_WARNING for m in messages), str(messages)

        l2 = [zeile for zeile in lang.split('\n') if not zeile.lstrip().startswith('@mitte_')]
        lang2 = '\n'.join(l2)
        assert lang2.find('@mitte_') < 0
        result, messages, ast = compile_ebnf(lang2)
        assert not messages, str(messages)

        l3 = [zeile for zeile in l2 if not zeile.lstrip().startswith('mitte')]
        lang3 = '\n'.join(l3).replace('mitte', '(`M` §"ITTE")')
        result, messages, ast = compile_ebnf(lang3)
        assert not messages, str(messages)

        parser = create_parser(lang3)
        cst = parser('ANFANGMITTEENDE')
        assert not cst.errors
        cst = parser('ANFANGMISSEENDE')
        assert cst.errors
        assert 'alles' in cst and 'ZOMBIE__' in cst['alles'] and 'ende' in cst['alles']

    def test_multiple_resume_definitions(self):
        lang = """
            document = series
            @series_resume = /B/, /C/, /D/, /E/, /F/, /G/
            @series_resume = /X/, /Y/
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        result, messages, ast = compile_ebnf(lang)
        assert messages[0].code == REDEFINED_DIRECTIVE

    def test_multiple_skip_definitions(self):
        lang = """
            document = series
            @series_skip = /B/, /C/, /D/, /E/, /F/, /G/
            @series_skip = /X/, /Y/
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        result, messages, ast = compile_ebnf(lang)
        assert messages[0].code == REDEFINED_DIRECTIVE

    def test_erreneous_skip_definitions(self):
        lang = """
            document = series selies
            @selies_error = '', "Error in the series" 
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        result, messages, ast = compile_ebnf(lang)
        assert len(messages) == 2
        lang = lang.replace('series selies', 'series')
        result, messages, ast = compile_ebnf(lang)
        assert len(messages) == 1

    def test_long_error_message(self):
        lang = """
            document = series
            @series_error = 'an error message that spreads\n over ' 
                            'several strings'
            series = "A" § "B" "C"
            """
        provider = grammar_provider(lang)
        parser = provider()
        result = parser('ADX')
        assert "several strings" in str(result.errors), str(result.errors)


class TestVariableCapture:
    tree_grammar = '''@whitespace = horizontal
        @disposable = EOF, LF, SAME_INDENT
        @drop       = strings, whitespace, EOF, LF, SAME_INDENT
        tree     = INDENT node DEDENT /\\\\s*/ EOF
        node     = name [content]
        content  = string | children
        children = &(LF HAS_DEEPER_INDENT)
                   LF INDENT § node { LF SAME_INDENT § node }
                   !(LF HAS_DEEPER_INDENT) DEDENT
        name = /\\\\w+/~
        string   = '"' § /(?:\\\\\\\\"|[^"\\\\n])*/ '"' ~
        INDENT            = / */
        SAME_INDENT       = :INDENT § !/ /
        HAS_DEEPER_INDENT = :INDENT / +/
        DEDENT            = &:?INDENT
        LF       = /\\\\n/
        EOF      = !/./
        '''

    def test_zero_length_capture_warning(self):
        pysrc, errors, _ = compile_ebnf(self.tree_grammar)
        assert errors and errors[0].code == ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING
        alt_tree_grammar = self.tree_grammar.replace('INDENT            = / */',
                                                     'INDENT            = / +/')
        pysrc, errors, _ = compile_ebnf(alt_tree_grammar)
        assert not errors


class TestCustomizedResumeParsing:
    lang = r"""@ literalws = right
        @ alpha_resume = "BETA", "GAMMA"
        @ beta_resume = GAMMA_RE
        @ bac_resume = /(?=GA\w+)/
        document = alpha [beta] gamma "."
        alpha = "ALPHA" abc
            abc = §"a" "b" "c"
        beta = "BETA" (bac | bca)
            bac = "b" "a" §"c"
            bca = "b" "c" §"a"
        gamma = "GAMMA" §(cab | cba)
            cab = "c" "a" §"b"
            cba = "c" "b" §"a"
        GAMMA_RE = /(?=GA\w+)/
        """

    def test_several_resume_rules_innermost_rule_matching(self):
        gr = grammar_provider(self.lang, fail_when=WARNING)()
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1

        content = 'ALPHA acb BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 2

        content = 'ALPHA acb GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only on error message
        assert len(cst.errors_sorted) == 1

    def test_resume_with_customized_whitespace(self):
        grammar_specification = r"""
            @whitespace = /\s*/
            @comment = /(?:\/\*(?:.|\n)*?\*\/)/  # c-style comments
            document = ~ { word }
            # @ word_resume = /(?:(?:\s\~)|(?:\~(?<=\s)))(?=.)|$/
            # @word_resume = /(?=(.|\n))\~(?!\1)(?=.)|$/
            @word_resume = /\~!(?=.)|$/
            # @ word_resume = /\~(?=.)|$/
            word     = !EOF §/\w+/ ~
            EOF      = !/./
        """
        grammar = grammar_provider(grammar_specification)()
        doc0 = """word no*word word"""
        st = grammar(doc0)
        assert st.children and st.children[-1].name == 'word'
        doc1 = """word no*word /* comment */ word"""
        st = grammar(doc1)
        assert st.children and st.children[-1].name == 'word'
        doc2 = """word no*word/* comment */word"""
        st = grammar(doc2)
        assert st.children and st.children[-1].name == 'word'
        doc3 = """word no*word/* comment1 */
                  /* comment2 */word"""
        st = grammar(doc3)
        assert st.children and st.children[-1].name == 'word'


class TestCustomizedResumeParsing_with_Parsers:
    lang = r"""@ literalws = right
        @ alpha_resume = ALPHA_RESUME
        @ beta_resume = GAMMA_RE
        @ bac_resume = /(?=GA\w+)/
        document = alpha [beta] gamma "."
        alpha = "ALPHA" abc
            abc = §"a" "b" "c"
        beta = "BETA" (bac | bca)
            bac = "b" "a" §"c"
            bca = "b" "c" §"a"
        gamma = "GAMMA" §(cab | cba)
            cab = "c" "a" §"b"
            cba = "c" "b" §"a"
        GAMMA_RE = /(?=GA\w+)/
        ALPHA_RESUME = { !`BETA` !`GAMMA` /./ }
        """

    def test_several_resume_rules_innermost_rule_matching(self):
        gr = grammar_provider(self.lang, fail_when=WARNING)()
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1

        content = 'ALPHA acb BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 2

        content = 'ALPHA acb GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1, str(cst.errors_sorted)

    def test_resume_with_expression(self):
        lang = r"""@ literalws = right
            @ alpha_resume =  ({ !`BETA` !`GAMMA` /./ })
            @ beta_resume = GAMMA_RE
            @ bac_resume = /(?=GA\w+)/
            document = alpha [beta] gamma "."
            alpha = "ALPHA" abc
                abc = §"a" "b" "c"
              beta = "BETA" (bac | bca)
                bac = "b" "a" §"c"
                bca = "b" "c" §"a"
              gamma = "GAMMA" §(cab | cba)
                cab = "c" "a" §"b"
                cba = "c" "b" §"a"
            GAMMA_RE = /(?=GA\w+)/
            # ALPHA_RESUME = { !`BETA` !`GAMMA` /./ }
            """
        gr = grammar_provider(lang)()
        # print(gr.python_src__)
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only on error message
        assert len(cst.errors_sorted) == 1

class TestCustomizedResumeParsing_with_autogenerated_Parsers:
    lang = """@ literalws   = right
    @ disposable  = /_\w+/
    @ drop        = _EOF, whitespace, strings
    _document = ~ [ list ] §_EOF
    @list_skip = ({ list | /[^\[\],]*/ })
    list     = "[" [_items] § "]"
    @_items_skip = /(?=,)/, /(?=])/, /$/
    _items   = _item { "," §_item }
    _item    = number | list    
    number   = `0` | /[1-9][0-9]*/
    _EOF     =  !/./
    """

    def test_skip_expression_specification_error(self):
        lang='''
        @doc_skip = `` 'A' | 'B' | 'C'
        doc = 'A' §'B' 'C'
        '''
        pysrc, errors, ast = compile_ebnf(lang, preserve_AST=True)
        i = pysrc.find('root__ =') + 8
        k = pysrc.find('\n', i)
        assert pysrc[i:k].find('_skip_') < 0
        assert len(errors) == 1
        assert len([e for e in errors if e.code == PEG_EXPRESSION_IN_DIRECTIVE_WO_BRACKETS]) > 0

    def test_skip_with_inline_parsers(self):
        parser = create_parser(self.lang)
        result = parser('[1, 2, A, [5, 6; [7, 8]], 8, ]')
        assert all(err.code != PARSER_STOPPED_BEFORE_END for err in result.errors)
        assert len(result.errors) == 3

    def test_interaction_resume_capture(self):
        lang='''
        @ whitespace  = /\s*/
        @ disposable  = EOF
        @ drop        = EOF, whitespace, strings
        
        document = ~ element ~ §EOF
        element  = STag content ETag
        STag     = '<' TagName §'>'
        @ETag_skip = ((`>` | :?TagName) /[^>]*/)
        ETag     = '</' §::TagName '>'
        TagName  = /\w+/
        content  = [CharData] { (element | COMMENT__) [CharData] }
        
        CharData = /(?:(?!\]\]>)[^<&])+/
        EOF      =  !/./
        '''
        pysrc, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert not errors
        i = pysrc.find('root__ =') + 8
        k = pysrc.find('\n', i)
        assert pysrc[i:k].find('_skip_') < 0

        parser = create_parser(lang)
        testdata = """
        <doc>
            <title>Heading</litle>
            A few lines of Text
        </doc>
        """
        set_tracer(parser, trace_history)
        result = parser(testdata)
        assert len(result.errors) == 1  # don't repeat error messages because of recursion!
        assert len(parser.history__) == 33  # don't repeat history because of recursion!


class TestInSeriesResume:
    def setup(self):
        lang = """
            document = series
            @series_skip = /(?=[BCDEFG])/
            series = "A" §"B" "C" "D" "E" "F" "G"
            """
        self.gr = grammar_provider(lang)()

    def test_garbage_in_series(self):
        st = self.gr('ABCDEFG')
        assert not st.error_flag
        st = self.gr('AB XYZ CDEFG')
        errors = st.errors_sorted
        assert len(errors) == 1 and errors[0].code == MANDATORY_CONTINUATION
        st = self.gr('AB XYZ CDE XYZ FG')
        errors = st.errors_sorted
        assert len(errors) == 2 and all(err.code == MANDATORY_CONTINUATION for err in errors)
        st = self.gr('AB XYZ CDE XNZ FG')  # fails to resume parsing
        errors = st.errors_sorted
        assert len(errors) >= 1 and errors[0].code == MANDATORY_CONTINUATION

    def test_series_gap(self):
        st = self.gr('ABDEFG')
        errors = st.errors_sorted
        assert len(errors) == 1 and errors[0].code == MANDATORY_CONTINUATION
        st = self.gr('ABXEFG')  # two missing, one wrong element added
        errors = st.errors_sorted
        assert len(errors) == 2 and all(err.code == MANDATORY_CONTINUATION for err in errors)
        st = self.gr('AB_DE_G')
        errors = st.errors_sorted
        assert len(errors) == 2 and all(err.code == MANDATORY_CONTINUATION for err in errors)

    def test_series_permutation(self):
        st = self.gr('ABEDFG')
        errors = st.errors_sorted
        assert len(errors) >= 1  # cannot really recover from permutation errors


class TestInterleaveResume:
    lang = """
        document = allof
        @ allof_error = '{} erwartet, {} gefunden :-('
        @ allof_skip = "D", "E", "F", "G"
        allof = "A" ° "B" ° §"C" ° "D" ° "E" ° "F" ° "G" 
    """
    gr = grammar_provider(lang)()

    def test_garbage_added(self):
        st = self.gr('BAGFCED')
        assert not st.error_flag
        st = self.gr('BAG FC XYZ ED')
        errors = st.errors_sorted
        assert errors[0].code == MANDATORY_CONTINUATION
        assert str(errors[0]).find(':-(') >= 0

    def test_allof_resume_later(self):
        lang = """
            document = flow "."
            @ flow_resume = "."
            flow = allof | series
            @ allof_error = '{} erwartet, {} gefunden :-('
            allof = "A" ° "B" ° §"C" ° "D" ° "E" ° "F" ° "G"
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
            @ flow_resume = "."
            flow = allof | series
            @ allof_error = '{} erwartet, {} gefunden :-('
            @ allof_resume = "E", "A"
            allof = "A" ° "B" ° §"C" °"D" ° "E" ° "F" ° "G"
            @ series_resume = "E", "A"
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
        assert len(st.errors) == 1
        st = gr('A_BCDEFG.')
        assert len(st.errors) == 1 and st.errors[0].code == PARSER_STOPPED_BEFORE_END
        st = gr('AB_CDEFG.')
        # mandatory continuation error kicks in only, if the parsers before
        # the §-sign have been exhausted!
        assert len(st.errors) == 2 and st.errors_sorted[0].code == MANDATORY_CONTINUATION
        st = gr('EXY EXYZ.')
        assert len(st.errors) == 1

    def test_interleave_groups(self):
        def mini_suite(gr):
            st = gr("AAAB")
            assert not st.errors
            st = gr("BAAA")
            assert not st.errors
            st = gr("B")
            assert not st.errors, str(st.errors)

        lang = """document = { `A` } ° `B`\n"""
        gr = grammar_provider(lang)()
        mini_suite(gr)
        st = gr('AABAA')
        assert not st.errors

        lang = """document = ({ `A` }) ° `B`\n"""
        gr = grammar_provider(lang)()
        mini_suite(gr)
        st = gr('AABAA')
        assert st.errors


ArithmeticEBNF = r"""
@ literalws = right
@ drop = whitespace   # <- there is no alternative syntax for directives!!!

expression ::= term, { ("+" | "-"), term};
term       ::= factor, { ("*" | "/"), factor};
factor     ::= [sign], (NUMBER | VARIABLE | group), { VARIABLE | group };
sign       ::= `+` | `-`;
group      ::= "(", expression, ")";

NUMBER     ::= /(?:0|(?:[1-9]\d*))(?:\.\d+)?/, ~;
VARIABLE   ::= /[A-Za-z]/, ~;
"""


class TestAlternativeEBNFSyntax:
    def setup(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'heuristic')

    def teardown(self):
        set_config_value('syntax_variant', self.save)

    def test_alt_syntax(self):
        code, errors, ast = compile_ebnf(ArithmeticEBNF, preserve_AST=True)
        assert not ast.error_flag, str(ast.errors)
        arithmetic_grammer = compile_python_object(
            DHPARSER_IMPORTS + code)  # .format(dhparser_parentdir=repr(DHPARSER_PARENTDIR)) + code)
        arithmetic_parser = arithmetic_grammer()
        st = arithmetic_parser('2 + 3 * (-4 + 1)')
        assert str(st) == "2+3*(-4+1)"

    # def test_regex_heuristics(self):
    #     gr = get_ebnf_grammar()
    #     assert isinstance(gr, HeuristicEBNFGrammar)
    #     result = gr(r' */', 'regex_heuristics')
    #     print(result.as_sxpr())


class TestConfigurableEBNF:
    def setup(self):
        self.save_variant = get_config_value('syntax_variant')
        self.save_delim = get_config_value('delimiter_set')

    def teardown(self):
        set_config_value('syntax_variant', 'configurable')
        set_config_value('delimiter_set', self.save_delim)
        set_config_value('syntax_variant', self.save_variant)

    def test_alt_syntax_config(self):
        set_config_value('syntax_variant', 'configurable')
        set_config_value('delimiter_set', {
            'DEF': '<-',
            'OR': '/',
            'AND': '',
            'ENDL': '',
            'RNG_OPEN': '{',
            'RNG_CLOSE': '}',
            'RNG_DELIM': ',',
            'TIMES': '*',
            'RE_LEADIN': '<',
            'RE_LEADOUT': '>',
            'RE_CORE': r'(?:(?<!\\)\\(?:>)|[^>])*',
            'CH_LEADIN': '0x'
        })
        parser = create_parser(
            r'''@literalws=none
            @disposable = Spacing, EOL, EOF
            @drop = Spacing, EOL, EOF
            Start   <- Spacing Expr EOL? EOF
            Expr    <- Term ((PLUS / MINUS) Term)*
            Term    <- Factor ((TIMES / DIVIDE) Factor)*
            Factor  <- Sign* (LPAR Expr RPAR
                             / INTEGER )
            Sign    <- NEG / POS
            INTEGER <- ( '0' / <[1-9][0-9]*> ) Spacing
            PLUS    <- '+' Spacing
            MINUS   <- '-' Spacing
            TIMES   <- '*' Spacing
            DIVIDE  <- '/' Spacing
            LPAR    <- '(' Spacing
            RPAR    <- ')' Spacing
            NEG     <- '-' Spacing
            POS     <- '+' Spacing
            Spacing <- <[ \t\n\f\v\r]*>
            EOL     <- '\r\n' / <[\n\r]>
            EOF     <- !<.>
            ''')
        result = parser('3 + 4 * 7')
        assert not result.errors


class TestSyntaxExtensions:
    def setup(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'strict')

    def teardown(self):
        set_config_value('syntax_variant', self.save)

    # def test_difference(self):
    #     lang = """
    #         doc = /[A-Z]/ - /[D-F]/
    #     """
    #     parser = create_parser(lang)
    #     st = parser("A")
    #     assert not st.errors and st.name == "doc" and st.content == "A"
    #     st = parser("E")
    #     assert st.errors and any(e.code == PARSER_STOPPED_BEFORE_END for e in st.errors)
    #
    def test_any_char(self):
        lang = 'doc = "A".'
        parser = create_parser(lang)
        st = parser('A翿')
        assert st.as_sxpr() == '(doc (:Text "A") (:AnyChar "翿"))'

    def test_character(self):
        lang = 'doc = 0xe4'
        parser = create_parser(lang)
        st = parser('ä')
        assert not st.errors
        lang = 'doc = #xe4'
        parser = create_parser(lang)
        st = parser('ä')
        assert not st.errors
        lang = 'doc = 0x37F'
        parser = create_parser(lang)
        st = parser('Ϳ')
        assert not st.errors

    def test_simple_char_range(self):
        set_config_value('syntax_variant', 'strict')
        lang = "Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]"
        parser = create_parser(lang)
        st = parser('賌')
        assert st.as_sxpr() == '(Char "賌")'

    def test_full_char_range(self):
        set_config_value('syntax_variant', 'heuristic')
        lang = """
            Identifier <- IdentStart IdentCont* Spacing
            IdentCont  <- IdentStart / [0-9] 
            IdentStart <- [a-zA-Z_]
            Spacing    <- (´ ´ / ´\t´ / ´\n´)*      
            """
        parser = create_parser(lang)
        st = parser('marke_8')
        assert not st.errors
        st = parser('t3vp ')
        assert not st.errors, str(st.errors)
        st = parser('3tvp ')
        assert st.errors
        set_config_value('syntax_variant', 'strict')


class TestModeSetting:
    def setup(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'heuristic')

    def teardown(self):
        set_config_value('syntax_variant', self.save)

    testdoc = r"""# hey, you

        doc = sequence | re | char | char_range | char_range2 | multiple1 | multiple2 | multiple3 | mutliple4
        sequence = '</' Name S? '>'
        re = /abc*/
        char = #x32  # shell-style comment
        char_range = [#xDFF88-#xEEFF00]   /*
                C-style comment
        */ char_range2 = [-'()+,./:=?;!*#@$_%]
        multiple1 = `a` * 3
        multiple2 = 4 * `b`
        multiple3 = `c`{3}
        multiple4 = `d`{2,5}
        Name = /\w+/
        S    = /\s*/
        """

    def test_setmode_getmode(self):
        gr = get_ebnf_grammar()
        gr.mode = 'strict'
        assert gr.mode == 'strict'
        gr.mode = 'regex-like'
        assert gr.mode == 'regex-like'
        gr.mode = 'peg-like'
        assert gr.mode == 'peg-like'
        gr.mode = 'heuristic'
        assert gr.mode == 'heuristic'

        gr.mode = 'classic'
        assert gr.mode == 'strict'

    def test_heuristic_mode(self):
        gr = get_ebnf_grammar()
        gr.mode = 'strict'
        st = gr(self.testdoc)
        assert st.errors
        gr.mode = 'heuristic'
        st = gr(self.testdoc)
        assert not st.errors, str(st.errors)


class TestAlternativeReordering:
    def setup(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'strict')

    def teardown(self):
        set_config_value('syntax_variant', self.save)

    def test_reordering_alternative_literals(self):
        lang = """
            TokenizedType  ::= 'ID'
                     | 'IDREF'
                     | 'IDREFS'
                     | 'ENTITY'
                     | 'ENTITIES'
                     | 'NMTOKEN'
                     | 'NMTOKENS'
        """
        src, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert src.find("'IDREFS'") < src.find("'IDREF'") < src.find("'ID'")
        assert src.find("'NMTOKENS'") < src.find("'NMTOKEN'")
        assert errors and all(e.code == REORDERING_OF_ALTERNATIVES_REQUIRED for e in errors)

    def test_reordering_alternative_literals_interspersed_with_non_literals(self):
        lang = """
            TokenizedType  ::= /x/ | /y/ | 'ID' | /aaa/
                     | 'IDREF' | /aa/
                     | 'IDREFS'
                     | 'ENTITY'
                     | 'ENTITIES' | /a/ | /h/
                     | 'NMTOKEN'
                     | 'NMTOKENS' | /z/
        """
        src, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert src.find("'IDREFS'") < src.find("'IDREF'") < src.find("'ID'")
        assert src.find("'NMTOKENS'") < src.find("'NMTOKEN'")
        assert src.find("'aaa'") < src.find("'aa'") < src.find("'a'")
        assert errors and all(e.code == REORDERING_OF_ALTERNATIVES_REQUIRED for e in errors)

    def test_reordering_alternative_symbols(self):
        lang = """
            TokenizedType  ::= 'ID'
                     | IDREF
                     | IDREFS
                     | 'ENTITY'
                     | 'ENTITIES'
                     | NMTOKEN
                     | 'NMTOKENS'
            IDREF ::= 'IDREF'
            IDREFS ::= 'IDREFS'
            NMTOKEN ::= 'NMTOKEN'
        """
        src, errors, ast = compile_ebnf(lang, preserve_AST=True)
        i = src.find('TokenizedType')
        k = src.find('\n', i)
        assert src[i:k].find("IDREFS,") < src[i:k].find("IDREF,") < src[i:k].find("'ID'")
        assert src[i:k].find("'NMTOKENS'") < src[i:k].find("NMTOKEN")
        assert errors and all(e.code == REORDERING_OF_ALTERNATIVES_REQUIRED for e in errors)

    def test_reordering_impossible(self):
        lang = """
            type = 'X' | 'ID' | 'XY' | 'ID'
        """
        src, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert any(e.code == BAD_ORDER_OF_ALTERNATIVES for e in errors)


class TestTreeOptimization:
    def test_drop_anonymous(self):
        lang = """
            doc = A B C
            A = `A`
            B = `B`
            C = `C`
        """
        parser = create_parser(lang)
        st = parser('ABC')
        assert str(st) == "ABC"
        parser = create_parser('@ disposable = B\n@ drop = B\n' + lang)
        st = parser('ABC')
        assert str(st) == "AC"

    def test_tree_reduction(self):
        lang = """@reduction = none
           root = 'A' 'B' (important | 'D')
           important = 'C' 
        """
        parser = create_parser(lang)
        st = parser('ABC')
        assert st.as_sxpr() == '(root (:Text "A") (:Text "B") (:Alternative (important "C")))'
        parser = create_parser(lang.replace('none', 'flatten'))
        assert parser('ABC').as_sxpr() == '(root (:Text "A") (:Text "B") (important "C"))'
        parser = create_parser(lang.replace('none', 'merge_treetops'))
        assert parser('ABC').as_sxpr() == '(root (:Text "A") (:Text "B") (important "C"))'
        assert parser('ABD').as_sxpr() == '(root "ABD")'
        parser = create_parser(lang.replace('none', 'merge_leaves'))
        assert parser('ABC').as_sxpr() == '(root (:Text "AB") (important "C"))'
        assert parser('ABD').as_sxpr() == '(root "ABD")'
        parser = create_parser(lang.replace('none', 'merge'))
        assert parser('ABC').as_sxpr() == '(root (:Text "AB") (important "C"))'
        assert parser('ABD').as_sxpr() == '(root "ABD")'


class TestHeuristics:
    """Test of the "heuristic" "syntax_variant" (see DHParser.configuration)
    which flexibly adjusts to the used EBNF-variant."""
    def setup(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'fixed')

    def teardown(self):
        set_config_value('syntax_variant', self.save)

    def test_heuristics(self):
        lang = """
            array = "[" [_element { "," _element }] "]"
            _element = /[0-9]/
        """
        parser = create_parser(lang)
        s = str(parser['array'])
        assert s == "array = `[` [_element {`,` _element}] `]`", s

        set_config_value('syntax_variant', 'strict')
        parser = create_parser(lang + ' ')
        s = str(parser['array'])
        assert s == "array = `[` [_element {`,` _element}] `]`", s

        # set_config_value('syntax_variant', 'heuristic')
        # parser = create_parser(lang + '  ')  # + ' ' cheats the cache
        # s = str(parser['array'])
        # assert s != "array = `[` [_element {`,` _element}] `]`"


class TestRuleOrder:
    """Reordering of rules in order to minimize the number of Forward-Declarations."""

    def test_rule_specification_order_does_not_matter(self):
        normal_order = """
            document = A
            A = B
            B = C
            C = "Hallo Welt"
            """
        # set_config_value('compiled_EBNF_log', 'auto_reorder_test.log')
        parser = create_parser(normal_order)
        assert parser.B.__class__.__name__ != "Forward"

        # Now B, should not be a Forward-Parser
        reverse_order = """
            document = A
            C = "Hallo Welt"
            B = C
            A = B
            """
        parser = create_parser(reverse_order)
        # If order of rule specification did not matter,
        # B should not be a Forward-parser:
        assert parser.B.__class__.__name__ != "Forward"

    def test_recursive_root(self):
        reverse_order = """
            C = "Hallo Welt" [A]
            B = C
            A = B
            """
        # set_config_value('compiled_EBNF_log', 'auto_reorder_test.log')
        parser = create_parser(reverse_order)
        assert parser.B.__class__.__name__ == "Forward"
        assert not parser.B.pname
        assert parser.B.parser.pname == 'B'

    def test_recursive_root_detached_root(self):
        reverse_order = """
            C = "Hallo Welt"
            B = C
            A = B
            """
        # set_config_value('compiled_EBNF_log', 'auto_reorder_test.log')
        parser = create_parser(reverse_order)
        assert parser.B.__class__.__name__ != "Forward"

    def test_resusive_paths(self):
        lang = """
            A = B | C
            B = C [`+` A]
            C = `x` [`-` A] [`*` B]
        """
        ebnf_grammar = get_ebnf_grammar()
        st = ebnf_grammar(lang)
        assert not st.errors, str(st.errors)
        ebnf_transformer = get_ebnf_transformer()
        ebnf_transformer(st)
        ebnf_compiler = get_ebnf_compiler()
        python_src = ebnf_compiler(st)
        pathsA = ebnf_compiler.recursive_paths('A')
        assert pathsA == frozenset({('A', 'B', 'C'), ('A', 'B'),
                                    ('A', 'C', 'B'), ('A', 'C')})
        pathsB = ebnf_compiler.recursive_paths('B')
        assert pathsB == frozenset({('B', 'C', 'A'), ('B', 'A', 'C'),
                                    ('B', 'A'), ('B', 'C')})
        pathsC = ebnf_compiler.recursive_paths('C')
        assert pathsC == frozenset({('C', 'A', 'B'), ('C', 'A'),
                                    ('C', 'B'), ('C', 'B', 'A')})

    def test_order_of_declarations(self):
        """If the order of definitions changes, the following invariants should hold:
        1. The number of Forward declarations is the same
        2. No two Forwardly-declared symbols yield exactly the same set of recursive paths
        3. The union of sets of recursive paths from all farwad-declared symbol
           remains the same.
        4. But: Depending on the order of definitions the symbols which are declared as
           Forward symbols can change within the limits of the previous 3 invariantes.
        """

        def compileEBNF(lang):
            ebnf_grammar = get_ebnf_grammar()
            st = ebnf_grammar(lang)
            assert not st.errors, str(st.errors)
            ebnf_transformer = get_ebnf_transformer()
            ebnf_transformer(st)
            ebnf_compiler = get_ebnf_compiler()
            ebnf_compiler(st)
            return ebnf_compiler

        def all_paths(compiler_obj):
            paths = [normalize_circular_path(compiler_obj.recursive_paths(sym))
                     for sym in compiler_obj.forward]
            for i in range(len(paths)):
                for k in range(i + 1, len(paths)):
                    assert paths[i] ^ paths[k]
            return paths[0].union(*paths[1:])

        lang = """doc = A
            A = B | C
            B = C [`+` A]
            C = `x` [`-` A] [`*` B]
        """
        compiler_obj = compileEBNF(lang)
        A = all_paths(compiler_obj)
        lang = """doc = A
            A = B | C
            C = `x` [`-` A] [`*` B]
            B = C [`+` A]
        """
        compiler_obj = compileEBNF(lang)
        B = all_paths(compiler_obj)
        assert A == B, str(A) + str(B)

        lang = """doc = A
            A = B | C
            B = C [`+` A]
            C = `x` [`-` A]
        """
        compiler_obj = compileEBNF(lang)
        A = all_paths(compiler_obj)
        lang = """doc = A
            A = B | C
            C = `x` [`-` A]
            B = C [`+` A]
        """
        compiler_obj = compileEBNF(lang)
        B = all_paths(compiler_obj)
        assert A == B, str(A) + str(B)

        lang = """doc = A
            A = B | C
            B = C [`+` A]
            C = `x` [`*` B]
        """
        compiler_obj = compileEBNF(lang)
        A = all_paths(compiler_obj)
        lang = """doc = A
            A = B | C
            C = `x` [`*` B]
            B = C [`+` A]
        """
        compiler_obj = compileEBNF(lang)
        B = all_paths(compiler_obj)
        assert A == B, str(A) + str(B)


class TestInclude:
    number_ebnf = '''
    @ disposable = DOT, EXP, FRAC, INT
    NUMBER      = INT [FRAC] [EXP]
    INT         = [NEG] ( /[1-9][0-9]+/ | /[0-9]/ )
    NEG         = `-`
    FRAC        = DOT /[0-9]+/
    DOT         = `.`
    EXP         = (`E`|`e`) [`+`|`-`] /[0-9]+/    
    '''

    arithmetic_ebnf = '''
    @ whitespace  = vertical             
    @ literalws   = right                
    @ comment     = /#.*/                
    @ ignorecase  = False     
    @ reduction   = merge_treetops           
    @ drop        = whitespace, strings    
    
    expression = term  { (add | sub) term}
    term       = factor { (div | mul) factor}
    factor     = [NEG] (number | group)
    group      = "(" expression ")"
    
    add        = "+"
    sub       = "-"
    mul        = "*"
    div        = "/"
    
    number     = NUMBER ~
    
    @ include = "number.ebnf"    
    '''

    def setup(self):
        self.dirname = unique_name('test_ebnf_data')
        os.mkdir(self.dirname)
        self.number_path = os.path.join(self.dirname, "number.ebnf")
        with open(self.number_path, 'w', encoding='utf-8') as f:
            f.write(self.number_ebnf)

    def teardown(self):
        os.remove(self.number_path)
        os.rmdir(self.dirname)

    def test_include(self):
        arithmetic_ebnf = self.arithmetic_ebnf.replace('number.ebnf', self.number_path)
        # print(arithmetic_ebnf)
        src, errors, ast = compile_ebnf(arithmetic_ebnf)
        assert not errors, str(errors)
        # for e in errors:
        #     print(str(e), e.orig_doc)
        # print(canonical_error_strings(errors))
        parser = create_parser(arithmetic_ebnf)
        # print(parser.python_src__)
        tree = parser('2 - (3 * -4.145E+5)')
        assert not tree.errors
        # print(tree.as_sxpr())


class TestCustomParsers:
    arithmetic_ebnf = '''
    @ whitespace  = vertical             
    @ literalws   = right                
    @ comment     = /#.*/                
    @ ignorecase  = False     
    @ reduction   = merge_treetops           
    @ drop        = whitespace, strings    

    expression = term  { (add | sub) term} 
    term       = factor { (div | mul) factor}
    factor     = [NEG] (number | group)
        NEG    = `-`
    group      = "(" expression ")"

    add        = "+"
    sub        = "-"
    mul        = "*"
    div        = "/"

    number     = @Custom(parse_number) ~
    
    EOF        = !/./ '''
    py_parse_number = r'''
def parse_number(s):
    try:
        i = min(k for k in (s.find(' '), s.find('\n'), s.find('('), s.find(')'), 
                            s.find('*'), s.find('/'), len(s))
                if k >= 0)
        if i < 0:  i = len(s)
        float(str(s[:i]))
    except ValueError:
        return None
    return Node('', s[:i])
    '''
    py_parse_number_class = r'''
class ParserNumber(Parser):
    def _parse(self, location):
        s = self.grammar.document__[location:]
        try:
            i = min(k for k in (s.find(' '), s.find('\n'), s.find('('), s.find(')'), 
                                s.find('*'), s.find('/'), len(s))
                    if k >= 0)
            if i < 0:  i = len(s)
            float(str(s[:i]))
        except ValueError:
            return None, location
        return Node(self.node_name, s[:i]), location + i        
    '''
    py_parse_factory_func = r'''
def parse_number(base_as_str: str):
    base = int(base_as_str)
    def parse_number_func(s):
        try:
            i = min(k for k in (s.find(' '), s.find('\n'), s.find('('), s.find(')'), 
                                s.find('*'), s.find('/'), len(s))
                    if k >= 0)
            if i < 0:  i = len(s)
            num_str = str(s[:i])
            int(num_str, base)
        except ValueError:
            return None
        return Node('', num_str)
    return parse_number_func
    '''

    def test_custom_parser_func(self):
        src, errors, ast = compile_ebnf(self.arithmetic_ebnf)
        parser = create_parser(self.arithmetic_ebnf, additional_code=self.py_parse_number)
        tree = parser('2 - (3 * -4.145E+5)')
        assert not tree.errors

    def test_custom_parser_class(self):
        arithmetic_ebnf = self.arithmetic_ebnf.replace('@Custom(parse_number)', '@ParserNumber()')
        # src, errors, ast = compile_ebnf(arithmetic_ebnf)
        parser = create_parser(arithmetic_ebnf, additional_code=self.py_parse_number_class)
        tree = parser('2 - (3 * -4.145E+5)')
        assert not tree.errors

    def test_custom_parser_factory_function(self):
        arithmetic_ebnf = self.arithmetic_ebnf.replace('@Custom(parse_number)', '@parse_number("16")')
        src, errors, ast = compile_ebnf(arithmetic_ebnf)
        parser = create_parser(arithmetic_ebnf, additional_code=self.py_parse_factory_func)
        tree = parser('2A + B3')
        assert not tree.errors

class TestErrors:
    numbers = r"""@whitespace = vertical
    document = { ~ number | error } ~ EOF
    number = /[1-9]\d*/~
    error  = !EOF @Error("Not a valid Number!") /.*?(?=\s|$)/  # skip to next whitespace
    EOF = !/./
    """

    def test_error(self):
        parser = create_parser(self.numbers)
        tree = parser("2 3 4")
        assert not tree.errors
        tree = parser("2 X 3 Y 4")
        assert len(tree.errors) == 2
        assert tree.as_sxpr() == """(document
  (number
    (:RegExp "2")
    (:Whitespace " "))
  (error
    (ZOMBIE__ `(err "1:3: Error (1000): Not a valid Number!"))
    (:RegExp "X"))
  (:Whitespace " ")
  (number
    (:RegExp "3")
    (:Whitespace " "))
  (error
    (ZOMBIE__ `(err "1:7: Error (1000): Not a valid Number!"))
    (:RegExp "Y"))
  (:Whitespace " ")
  (number "4")
  (EOF))"""


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
