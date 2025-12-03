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
    normalize_circular_paths, INFINITE
from DHParser.preprocess import nil_preprocessor
from DHParser.compile import compile_source
from DHParser.configuration import get_config_value, set_config_value
# from DHParser.ebnf_flavors.heuristic import HeuristicEBNFGrammar
from DHParser.error import has_errors, MANDATORY_CONTINUATION, PARSER_STOPPED_BEFORE_END, \
    REDEFINED_DIRECTIVE, UNUSED_ERROR_HANDLING_WARNING, AMBIGUOUS_ERROR_HANDLING, \
    REORDERING_OF_ALTERNATIVES_REQUIRED, BAD_ORDER_OF_ALTERNATIVES, UNCONNECTED_SYMBOL_WARNING, \
    PEG_EXPRESSION_IN_DIRECTIVE_WO_BRACKETS, ERROR, WARNING, UNDEFINED_MACRO, \
    UNKNOWN_MACRO_ARGUMENT, UNUSED_MACRO_ARGUMENTS_WARNING, \
    ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING, SYMBOL_NAME_IS_PYTHON_KEYWORD
from DHParser.nodetree import WHITESPACE_PTYPE, flatten_sxpr, parse_sxpr, RootNode, Node, ANY_PATH, \
    pp_path
from DHParser.parse import Interleave
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, EBNFTransform, \
    EBNFDirectives, get_ebnf_compiler, compile_ebnf, DHPARSER_IMPORTS, \
    WHITESPACE_TYPES, parse_ebnf, transform_ebnf, EBNF_AST_Serialization_Table, \
    ebnf_from_ast
from DHParser.dsl import CompilationError, compileDSL, create_parser, grammar_provider
from DHParser.testing import grammar_unit, clean_report, unique_name
from DHParser.trace import set_tracer, trace_history


class TestDirectives:
    mini_language = """
        @ literalws = right
        expression =  term  { ("+" | "-") term }
        term       =  factor  { ("*" | "/") factor }
        factor     =  constant | "("  expression  ")"
        constant   =  digit { digit } [ ~ ]
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

    def test_EBNF_doubleDirectives(self):
        lang = """
        @
        """

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
        assert not syntax_tree.pick('comment__')
        assert syntax_tree.pick(':Whitespace')
        syntax_tree = parser("3 + 4 \n  %comment\n\n * 12")
        assert syntax_tree.errors_sorted
        syntax_tree = parser("3 + 4 \n\n%comment\n * 12")
        assert syntax_tree.errors_sorted

    def test_whitespace_keep_comments(self):
        lang = """@whitespace = linefeed
                  @comment = /%.*/
                  @drop = no_comments
               """ + self.mini_language
        MinilangParser = grammar_provider(lang)
        parser = MinilangParser()
        assert parser
        syntax_tree = parser("3 + 4 \n  %comment \n * 12")
        assert syntax_tree.pick('comment__')
        assert not syntax_tree.pick(':Whitespace')

    def test_whitespace_keep_comments_alt(self):
        lang = """@whitespace = linefeed
                  @comment_keep = /%.*/
               """ + self.mini_language
        MinilangParser = grammar_provider(lang)
        parser = MinilangParser()
        assert parser
        syntax_tree = parser("3 + 4 \n  %comment \n * 12")
        assert syntax_tree.pick('comment__')
        assert not syntax_tree.pick(':Whitespace')

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

            document      = ` ` " " ' ' / /
        """
        parser = create_parser(lang)
        st = parser('    ')
        assert not st.errors and str(st) == '  '

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

    # def test_dont_drop_alternatives(self):
    #     lang = r"""
    #         @ drop = strings, whitespace
    #         @ literalws = right
    #         doc  = a b c d
    #         a    = "A"
    #         b    = "1" | "2"
    #         c    = a "+" b
    #         d    = a ("*"|"/") b
    #     """
    #     parser = create_parser(lang)
    #     st = parser('A2A+1A*2')
    #     assert str(st) == "A2A1A2"

    def test_dont_drop_sequence(self):
        lang = r"""
            @ drop = strings, backticked, whitespace
            @ literalws = right
            doc  = a b
            a    = "A"
            b    = `1` `2`
        """
        parser = create_parser(lang)
        st = parser('A12')
        assert str(st) == "A"

    def test_no_drop_clause_for_non_dropping_defs(self):
        save = get_config_value('optimizations')
        set_config_value('optimizations', frozenset())
        lang = r"""@drop = regexps
        CMDNAME    = /\\@?(?:(?![\d_])\w)+/~
        """
        parser = create_parser(lang)
        set_config_value('optimizations', save)
        assert parser.python_src__.find('CMDNAME = Series(RegExp(') >= 0


    def test_drop_error_messages(self):
        lang = r'''
        @disposable = A
        @drop = A, B
        A = { B }
        B = 'x'
        '''
        _, errors, _ = compile_ebnf(lang)
        # error does not exist any more, due to directives-reordering in DHParser Version 1.4 and above
        # assert len(errors) == 1
        # assert errors[0].message.startswith('''Illegal value "B" for Directive "@ drop"!''')
        # assert errors[0].message.endswith('''where the "@disposable"-directive must precede the @drop-directive.''')
        lang = r'''
        @disposable = /[A]/
        @drop = A, B
        A = { B }
        B = 'x'
        '''
        _, errors, _ = compile_ebnf(lang)
        assert errors[0].message.find('or a string matching') >= 0

    def test_disposable_bug(self):
        lang = r'''@disposable = /_\w+/
        doc=_text
        _text = /.*/'''
        parser=create_parser(lang)
        assert parser.python_src__.find(r'(?:_\\w+)|(?:_\\w+)') < 0


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


class TestModifiers:
    def test_no_modifiers(self):
        lang = r"""
        @reduction = merge
        list = string [WS] { SEP [WS] string [WS] }
        string = QUOT /[^"]*/ QUOT
        SEP = `,`
        WS = /\s+/
        QUOT = `"`
        """
        parser = create_parser(lang)
        cst = parser('"alpha", "beta"')
        assert cst.equals(parse_sxpr(
            """(list
              (string
                (QUOT '"')
                (:RegExp "alpha")
                (QUOT '"'))
              (SEP ",")
              (WS " ")
              (string
                (QUOT '"')
                (:RegExp "beta")
                (QUOT '"')))"""))

    def test_hide(self):
        lang = r"""
        @reduction = merge
        list = string [WS] { SEP [WS] string [WS] }
        string = QUOT /[^"]*/ QUOT
        SEP = `,` -> hide
        WS = /\s+/ -> hide
        QUOT = `"` -> hide
        """
        parser = create_parser(lang)
        cst = parser('"alpha", "beta"')
        assert cst.as_sxpr() == '''(list (string '"alpha"') (:Text ", ") (string '"beta"'))'''

    def test_drop(self):
        lang = r"""
        @reduction = merge
        list = string [WS] { SEP [WS] string [WS] }
        string = QUOT /[^"]*/ QUOT
        SEP = `,` -> drop
        WS = /\s+/ -> drop
        QUOT = `"` -> hide
        """
        parser = create_parser(lang)
        cst = parser('"alpha", "beta"')
        assert cst.as_sxpr() == '''(list (string '"alpha"') (string '"beta"'))'''

        lang = r"""
        @reduction = none
        list = string [WS] { SEP [WS] string [WS] }
        string = (QUOT -> drop) /[^"]*/ QUOT
        SEP = `,` -> drop
        WS = /\s+/ -> drop
        QUOT = `"`
        """
        parser = create_parser(lang)
        cst = parser('"alpha", "beta"')
        assert cst.equals(parse_sxpr(
            """(list
              (string
                (:RegExp "alpha")
                (QUOT '"'))
              (:ZeroOrMore
                (:Series
                  (string
                    (:RegExp "beta")
                    (QUOT '"')))))"""))

        lang = r"""
        @reduction = none
        list = string [WS] { SEP [WS] string [WS] }
        string = ((`'` | QUOT) -> drop) /[^"]*/ (`'` | QUOT)
        SEP = (`,` -> drop)
        WS = /\s+/ -> drop
        QUOT = `"`
        """
        parser = create_parser(lang)
        a = parser.python_src__.find('SEP =')
        b = parser.python_src__.find('\n', a)
        assert parser.python_src__[a:b].find('Synonym(') >= 0
        a = parser.python_src__.find('string =')
        b = parser.python_src__.find('\n', a)
        assert parser.python_src__[a:b].find('Synonym(') < 0
        cst = parser('"alpha", "beta"')
        assert cst.equals(parse_sxpr(
            """(list
              (string
                (:RegExp "alpha")
                (:Alternative
                  (QUOT '"')))
              (:ZeroOrMore
                (:Series
                  (SEP)
                  (string
                    (:RegExp "beta")
                    (:Alternative
                      (QUOT '"'))))))"""))

    def test_prefix_modifiers(self):
        lang = r"""
        @reduction = merge
        list = string [WS] { SEP [WS] string [WS] }
        string = QUOT /[^"]*/ QUOT
        DROP:SEP = `,`
        DROP:WS = /\s+/
        HIDE:QUOT = `"`
        """
        parser = create_parser(lang)
        cst = parser('"alpha", "beta"')
        assert cst.as_sxpr() == '''(list (string '"alpha"') (string '"beta"'))'''

        lang = r"""
        @reduction = merge
        list = string [WS] { SEP [WS] string [WS] }
        string = QUOT /[^"]*/ QUOT
        DROP:SEP = `,`
        DROP:WS = /\s+/
        :QUOT = `"`  # abbreviated HIDE modifier
        """
        parser = create_parser(lang)
        cst = parser('"alpha", "beta"')
        assert cst.as_sxpr() == '''(list (string '"alpha"') (string '"beta"'))'''

    def test_macro_modifiers_drop(self):
        lang = r'''
        @reduction = merge
        @disposable = $phrase
        @drop = $phrase
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = /[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }
        '''
        parser = create_parser(lang)
        a = parser.python_src__.find('doc =')
        b = parser.python_src__.find('\n', a)
        line = parser.python_src__[a:b]
        assert line.find('.name(') < 0
        assert line[20:].startswith('Drop(Series')

        lang = r'''
        @reduction = merge
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = (/[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }) -> DROP
        '''
        parser = create_parser(lang)
        a = parser.python_src__.find('doc =')
        b = parser.python_src__.find('\n', a)
        assert line == parser.python_src__[a:b]

        lang = '''
        @reduction = merge
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        DROP:$phrase($separator) = /[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }
        '''
        parser = create_parser(lang)
        a = parser.python_src__.find('doc =')
        b = parser.python_src__.find('\n', a)
        assert line == parser.python_src__[a:b]

    def test_macro_modifiers_hide(self):
        lang = r'''
        @reduction = merge
        @disposable = $phrase
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = /[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }
        '''
        parser = create_parser(lang)
        a = parser.python_src__.find('doc =')
        b = parser.python_src__.find('\n', a)
        line = parser.python_src__[a:b]
        assert line.find('.name(') < 0

        lang = r'''
        @reduction = merge
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = (/[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }) -> HIDE
        '''
        parser = create_parser(lang)
        a = parser.python_src__.find('doc =')
        b = parser.python_src__.find('\n', a)
        assert line == parser.python_src__[a:b]

        lang = r'''@reduction = merge
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        HIDE:$phrase($separator) = /[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }
        '''
        parser = create_parser(lang)
        a = parser.python_src__.find('doc =')
        b = parser.python_src__.find('\n', a)
        assert line == parser.python_src__[a:b]

    def test_drop_bug(self):
        lang = r'''EOF      =  !/./ -> DROP'''
        parser = create_parser(lang)
        assert parser.python_src__.rfind("NegativeLookahead(Drop(RegExp('.')))") >= 0


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

    def setup_class(self):
        self.save_dir = os.getcwd()
        os.chdir(scriptpath)

    def teardown_class(self):
        clean_report('REPORT_TestEBNFParser')
        os.chdir(self.save_dir)

    def test_RE(self):
        gr = get_ebnf_grammar()
        m = gr.regexp.parsers[1].regexp.match(r'[\\\\]/ xxx ')
        rs = m.group()
        assert rs.find('x') < 0, rs.group()
        rx = re.compile(rs[1:-1])
        assert rx.match(r'\\')

    def test_SmartRE(self):
        ebnf = r"name = /(?P<first_name>\w+)\s+(?P<last_name>\w+)/"
        gr = create_parser(ebnf, 'SmartRETest')
        result = gr('Arthur Schopenhauer')
        assert result.as_sxpr() == '(name (first_name "Arthur") (last_name "Schopenhauer"))'

        ebnf = r"name = /(?P<first_name>\w+)(\s+)(?P<last_name>\w+)/"
        gr = create_parser(ebnf, 'SmartRETest')
        result = gr('Arthur Schopenhauer')
        assert result.as_sxpr() == '(name (first_name "Arthur") (:RegExp " ") (last_name "Schopenhauer"))'

        ebnf = (r"""@disposable = name
                name = /(?P<:first_name>\w*)\s*(?P<:last_name>\w*)/""")
        gr = create_parser(ebnf, 'SmartRETest')
        result = gr('Nietzsche')
        assert result.as_sxpr() == '(:first_name "Nietzsche")'
        result = gr('')
        assert result.as_sxpr() == '(:EMPTY)'
        result = gr('$$$')
        assert result.errors

        ebnf = r"keyword = /(?P<Text__>hide)(?P<Whitespace__>\s*)/"
        gr = create_parser(ebnf, "SmartRETest")
        assert gr("hide").as_sxpr() == '(keyword (Text__ "hide") (Whitespace__))'

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


class TestEBNFErrors:
    def test_Python_keywords(self):
        ebnf = '''and = /.*/\n'''
        try:
            parser = create_parser(ebnf)
            assert False, "CompilationError expected"
        except SyntaxError:
            assert False, "SyntaxError should have been avoided."
        except CompilationError as ce:
            assert any(err.code == SYMBOL_NAME_IS_PYTHON_KEYWORD
                       for err in ce.errors)

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
        ebnf = """nothing =  COMMENT__ | WSP_RE__\n"""
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
@ hide       = pure_elem, element

#: top-level

syntax     = ~ { definition | directive } §EOF
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
                DHPARSER_IMPORTS + grammar_src,
                'parsing').factory()
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
    def setup_class(self):
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

    def test_predefined_whitespace(self):
        rx = re.compile(WHITESPACE_TYPES['linefeed'])
        assert rx.match('').group(0) == ''
        assert rx.match('\n').group(0) == '\n'
        assert rx.match('\n\n').group(0) == ''
        assert rx.match('A').group(0) == ''
        assert rx.match('\n   ').group(0) == '\n   '
        assert rx.match('   \n').group(0) == '   \n'
        assert rx.match('\n   \n').group(0) == ''
        assert rx.match('   \n   \n').group(0) == '   '

        rx = re.compile(WHITESPACE_TYPES['linestart'])
        assert rx.match('').group(0) == ''
        assert rx.match('\n').group(0) == '\n'
        assert rx.match('\n\n').group(0) == ''
        assert rx.match('A').group(0) == ''
        assert rx.match('\n   ').group(0) == '\n'
        assert rx.match('   \n').group(0) == '   \n'
        assert rx.match('\n   \n').group(0) == ''
        assert rx.match('   \n   \n').group(0) == '   '


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
        result, errors, _ = compile_ebnf(lang)
        assert not errors
        lang_wrong = 'doc = "a" * 0'
        result, errors, _ = compile_ebnf(lang_wrong)
        assert errors

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
        assert 'alles' in cst and 'alles_skip_R1__' in cst['alles'] and 'ende' in cst['alles']

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

    # def test_indirect_error_handling(self):
    #     lang = """
    #         document = series
    #         @series_error = 'error'
    #         series = "A" B "C"
    #         B = "B" § "b"
    #         """
    #     provider = grammar_provider(lang)
    #     parser = provider()
    #     result = parser('ABC')
    #     print(result.errors)
    #     # result, messages, ast = compile_ebnf(lang)
    #     # assert not messages, "No warning expected, but: " + str(messages)
    #
    # def test_indirect_ambiguity(self):
    #     lang = """
    #         document = series
    #         @series_error = 'error'
    #         series = "A" B § "C"
    #         B = "B" § "b"
    #         """
    #     result, messages, ast = compile_ebnf(lang)
    #     assert messages, '"Ambigous error message"-warning expected!'


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
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only on error message
        assert len(cst.errors_sorted) == 1


class TestCustomizedResumeParsing_with_autogenerated_Parsers:
    lang = r"""@ literalws   = right
    @ disposable  = /_\w+/
    @ drop        = _EOF, whitespace, strings
    _document = ~ [ list ] §_EOF
    @list_skip = ({ list | /[^\[\],]+/ })
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
        lang=r'''
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
        for e in result.errors: print(e)
        assert len([e for e in result.errors if e.code > ERROR]) == 1  # don't repeat error messages because of recursion!
        assert len(parser.history__) in (24, 25),  len(parser.history__)  # don't repeat history because of recursion!
        # possible differences in length above are due to optimizations turned on (25) or off (24)!


class TestInSeriesResume:
    def setup_class(self):
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
    def setup_class(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'heuristic')

    def teardown_class(self):
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


class TestConfigurableEBNF:
    def setup_class(self):
        self.save_variant = get_config_value('syntax_variant')
        self.save_delim = get_config_value('delimiter_set')

    def teardown_class(self):
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
    def setup_method(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'strict')

    def teardown_method(self):
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

    def test_simple_char_range(self): # TODO: test with alternative-optimization
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

    def test_minus_identifiers(self):
        set_config_value('syntax_variant', 'heuristic')
        lang = """
            identifier  <- ident-start ident-cont* spacing
            ident-cont  <- ident-start / [0-9]
            ident-start <- [a-zA-Z_]
            spacing     <- (` ` / ´\t´ / ´\n´)*
        """
        parser = create_parser(lang)
        assert parser.python_src__.find('ident-cond') < 0

    def test_yet_another_variant(self):
        set_config_value('syntax_variant', 'heuristic')
        lang = """STRING
        : [a-z]+
        ;"""
        parser = create_parser(lang)

    def test_placeholder(self):
        set_config_value('syntax_variant', 'heuristic')
        lang = """ @reduction = merge
        @disposable = $phrase
        @drop = $phrase
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = /[^.,;]*/ { !$separator /[.,;]/ /[^,.;]/ }
        """
        parser = create_parser(lang)



class TestModeSetting:
    def setup_method(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'heuristic')

    def teardown_method(self):
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
    def setup_class(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'strict')

    def teardown_class(self):
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
        save = get_config_value('optimizations')
        set_config_value('optimizations', frozenset())
        src, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert src.find("'IDREFS'") < src.find("'IDREF'") < src.find("'ID'")
        assert src.find("'NMTOKENS'") < src.find("'NMTOKEN'")
        assert errors and all(e.code == REORDERING_OF_ALTERNATIVES_REQUIRED for e in errors)
        set_config_value('optimizations', save)

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
        save = get_config_value('optimizations')
        set_config_value('optimizations', frozenset())
        src, errors, ast = compile_ebnf(lang, preserve_AST=True)
        assert src.find("'IDREFS'") < src.find("'IDREF'") < src.find("'ID'")
        assert src.find("'NMTOKENS'") < src.find("'NMTOKEN'")
        assert src.find("'aaa'") < src.find("'aa'") < src.find("'a'")
        assert errors and all(e.code == REORDERING_OF_ALTERNATIVES_REQUIRED for e in errors)
        set_config_value('optimizations', save)

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
    def setup_method(self):
        self.save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'fixed')

    def teardown_method(self):
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
            paths = [normalize_circular_paths(compiler_obj.recursive_paths(sym))
                     for sym in compiler_obj.forward]
            for i in range(len(paths)):
                for k in range(i + 1, len(paths)):
                    assert paths[i] ^ paths[k]
            return paths and paths[0].union(*paths[1:])

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
    sub        = "-"
    mul        = "*"
    div        = "/"

    number     = NUMBER ~

    @ include = "number.ebnf"
    '''

    def setup_class(self):
        self.dirname = unique_name('test_ebnf_data')
        os.mkdir(self.dirname)
        self.number_path = os.path.join(self.dirname, "number.ebnf")
        with open(self.number_path, 'w', encoding='utf-8') as f:
            f.write(self.number_ebnf)

    def teardown_class(self):
        os.remove(self.number_path)
        os.rmdir(self.dirname)

    def test_include(self):
        arithmetic_ebnf = self.arithmetic_ebnf.replace('number.ebnf', self.number_path)
        src, errors, ast = compile_ebnf(arithmetic_ebnf)
        assert not errors, str(errors)
        parser = create_parser(arithmetic_ebnf)
        tree = parser('2 - (3 * -4.145E+5)')
        assert not tree.errors


class TestCustomParsers:
    arithmetic_ebnf = r'''
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

    number_rx  = /\d+/~
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
    py_parse_referring_class = r'''
class ParserNumber(LateBindingUnary):
    def _parse(self, location):
        assert self.parser is not PARSER_PLACEHOLDER
        parser = self.parser
        result, location_ = parser(location)
        return result, location_
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

    def test_custom_parser_referring_class(self):
        arithmetic_ebnf = self.arithmetic_ebnf.replace('@Custom(parse_number)', '@ParserNumber("number_rx")')
        parser = create_parser(arithmetic_ebnf, additional_code=self.py_parse_referring_class)
        tree = parser('2 * (12 - 3)')
        assert not tree.errors

class TestErrors:
    numbers = r"""@whitespace = vertical
    document = { ~ number | error } ~ EOF
    number = /[1-9]\d*/~
    error  = !EOF @Error("»{1}« is not a valid Number!") /.*?(?=\s|$)/  # skip to next whitespace
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
    (ZOMBIE__ `(err "1:3: Error (1000): »X 3 Y 4...« is not a valid Number!"))
    (:RegExp "X"))
  (:Whitespace " ")
  (number
    (:RegExp "3")
    (:Whitespace " "))
  (error
    (ZOMBIE__ `(err "1:7: Error (1000): »Y 4...« is not a valid Number!"))
    (:RegExp "Y"))
  (:Whitespace " ")
  (number "4")
  (EOF))"""

    def test_missing_at(self):
        try:
            parser = create_parser(self.numbers.replace('@Error', 'Error'))
            assert False, "CompilationError expected"
        except CompilationError as ce:
            assert str(ce).find('"@" should be added')


class TestNameConflicts:
    def test_symbol_shadows_parser_name(self):
        gr = r'''
        doc = Text | Literal
        Literal = `abc`
        Text = /\w+/
        '''
        # should run without causig an exception
        p = create_parser(gr)
        assert p.python_src__.find('parse_namespace__.Text("abc")') >= 0


class TestMacros:
    def test_simple_macros(self):
        lang = '''@reduction = merge
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = /[^.,;]+/ { !$separator /[.,;]/ /[^,.;]/+ }
        '''
        parser = create_parser(lang)
        tree = parser('1; 2, 3; 4')
        assert not tree.errors
        assert flatten_sxpr(tree.as_sxpr()) == \
               '(doc (phrase "1; 2") (:Text ", ") (phrase "3; 4"))', tree.as_sxpr()

        lang = "@disposable = $phrase\n" + lang
        parser = create_parser(lang)
        tree = parser('1; 2, 3; 4')
        assert not tree.errors
        assert tree.as_sxpr() == '(doc "1; 2, 3; 4")'

        lang = "@drop = $phrase\n" + lang
        parser = create_parser(lang)
        tree = parser('1; 2, 3; 4')
        assert not tree.errors
        assert tree.as_sxpr() == '(doc ", ")'

    def test_boundary_case(self):
        lang = """doc = $macro("x")
        $macro($arg) = $arg
        """
        parser = create_parser(lang)
        tree = parser('x')
        assert not tree.errors

    def test_macro_errors(self):
        import sys
        lang = '''@reduction = merge
        doc = ~ $undefined(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = /[^.,;]+/ { !$separator /[.,;]/ /[^,.;]/+ }
        '''
        src, errors, ast = compile_ebnf(lang)
        assert errors[0].code == UNDEFINED_MACRO

        lang = '''@reduction = merge
        doc = ~ $phrase(`,`) { `,`~ $phrase(`,`) }
        $phrase($separator) = /[^.,;]+/ { !$unknown /[.,;]/ /[^,.;]/+ }
        '''
        src, errors, ast = compile_ebnf(lang)
        assert len(errors) == 2
        codes = {e.code for e in errors}
        assert UNKNOWN_MACRO_ARGUMENT in codes
        assert UNUSED_MACRO_ARGUMENTS_WARNING in codes
        # TODO: UNUSED MACRO ARGUMENTS should be warned about as well!
        # TODO: Test WRONG_NUMBER_OF_ARGUMENTS

    def test_nested_macros(self):
        lang = '''@reduction = merge
        doc = ~ $phrase_list(`,`)
        $phrase_list($sep) = $phrase($sep) { $sep~ $phrase($sep) }
        $phrase($separator) = /[^.,;]+/ { !$separator /[.,;]/ /[^,.;]/+ }
        '''
        parser = create_parser(lang)
        tree = parser('1; 2, 3; 4')
        assert not tree.errors
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (phrase_list (phrase "1; 2") (:Text ", ") (phrase "3; 4")))'

        lang = "@disposable = $phrase_list\n" + lang
        parser = create_parser(lang)
        tree = parser('1; 2, 3; 4')
        assert not tree.errors
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (phrase "1; 2") (:Text ", ") (phrase "3; 4"))'

    def test_macrosyms(self):
        lang = '''@reduction = merge
        @disposable = $phrase_list, $chars, _neutral_chars
        doc = ~ $phrase_list(`,`)
        $phrase_list($sep) = $phrase($sep) { $sep~ $phrase($sep) }
        $phrase($separator) = _neutral_chars $chars
        $chars = { !$separator /[.,;]/ _neutral_chars }
        _neutral_chars = /[^.,;]+/
        '''
        parser = create_parser(lang)
        tree = parser('1; 2, 3; 4')
        assert not tree.errors
        assert flatten_sxpr(tree.as_sxpr()) == '(doc (phrase "1; 2") (:Text ", ") (phrase "3; 4"))'

    def test_macro_complex_case(self):
        lang = r'''@ whitespace  = /[ \t]*/
        @ reduction   = merge
        @ disposable  = WS, EOF, LINE, S
        @ drop        = WS, EOF, backticked
        document = main [WS] §EOF
        $one_sec($level_sign, $sub_level) = [WS] $level_sign !`#` heading [blocks] { $sub_level }
        $sec_seq($sec) = { [WS] $sec }+
        main = $one_sec(`#`, sections)
        sections = $sec_seq(section)
        section = $one_sec(`##`, subsections)
        subsections = $sec_seq(subsection)
        subsection = $one_sec(`###`, subsubsections)
        subsubsections = $sec_seq(subsubsection)
        subsubsection = $one_sec(`####`, NEVER_MATCH)
        heading = LINE
        blocks = [WS] block { PARSEP block }
        block  = !is_heading line { lf !is_heading line }
          line = LINE
          lf   = S
        is_heading = /##?#?#?#?#?(?!#)/
        LINE      = /[ \t]*[^\n]+/
        WS        = /(?:[ \t]*\n)+/  # empty lines
        S         = !PARSEP /\s+/
        PARSEP    = /[ \t]*\n[ \t]*\n\s*/
        NEVER_MATCH = /..(?<=^)/
        EOF       =  !/./
        '''
        parser = create_parser(lang)
        doc = """
        # Title
        ## Section 1
        ### SubSection 1.1
        Text
        ## SubSection 1.2
        ### Section 2
        """
        tree = parser(doc)


class TestIgnoreCase:
    def test_ignore_case(self):
        lang = """@ignorecase = True
           doc = "ABC" | /DEF/
        """
        parser = create_parser(lang)
        assert not parser('Abc').errors
        assert parser("Abc").content == "Abc"
        assert not parser('abc').errors
        assert parser("abc").content == "abc"
        assert not parser('ABC').errors
        assert parser("ABC").content == "ABC"

        assert not parser("Def").errors
        assert parser("Def").content == "Def"
        assert not parser('def').errors
        assert parser("def").content == "def"
        assert not parser('DEF').errors
        assert parser("DEF").content == "DEF"

        lang2 = lang.replace('True', 'False')
        parser = create_parser(lang2)
        assert parser("Abc").errors
        assert parser("abc").errors
        assert not parser("ABC").errors
        assert parser("ABC").content == "ABC"

        assert parser("Def").errors
        assert parser("def").errors
        assert not parser("DEF").errors
        assert parser("DEF").content == "DEF"


class TestRegexRendering:
    def test_multiline_regex(self):
        lang = r"""LATIN = /[\x41-\x5A]|[\x61-\x7A]|[\xC0-\xD6]|[\xD8-\xF6]|[\u00F8-\u02AF]|[\u0363-\u036F]
            |[\u1D00-\u1D25]|[\u1D62-\u1D65]|[\u1D6B-\u1D77]|[\u1D79-\u1D9A]|\u1DCA
            |[\u1DD3-\u1DF4]|[\u1E00-\u1EFF]|\u2071|\u207F|[\u2090-\u209C]|\u2184|[\u249C-\u24E9]
            |[\u271D-\u271F]|\u2C2E|\u2C5E|[\u2C60-\u2C7C]|[\u2C7E-\u2C7F]|[\uA722-\uA76F]
            |[\uA771-\uA787]|[\uA78B-\uA7BF]|[\uA7C2-\uA7C6]|\uA7F7|[\uA7FA-\uA7FF]
            |[\uAB30-\uAB5A]|[\uAB60-\uAB64]|[\uAB66-\uAB67]|[\uFB00-\uFB06]|[\uFF21-\uFF3A]
            |[\uFF41-\uFF5A]|[\U0001F110-\U0001F12C]|[\U0001F130-\U0001F149]
            |[\U0001F150-\U0001F169]|[\U0001F170-\U0001F18A]|\U0001F1A5|[\U0001F520-\U0001F521]
            |\U0001F524|[\U0001F546-\U0001F547]|[\U000E0041-\U000E005A]|[\U000E0061-\U000E007A]/
        """
        parser = create_parser(lang)
        expected = r"""LATIN = RegExp('(?x)[\\x41-\\x5A]|[\\x61-\\x7A]|[\\xC0-\\xD6]|[\\xD8-\\xF6]|[\\u00F8-\\u02AF]|[\\u0363-\\u036F]\n'
                   '|[\\u1D00-\\u1D25]|[\\u1D62-\\u1D65]|[\\u1D6B-\\u1D77]|[\\u1D79-\\u1D9A]|\\u1DCA\n'
                   '|[\\u1DD3-\\u1DF4]|[\\u1E00-\\u1EFF]|\\u2071|\\u207F|[\\u2090-\\u209C]|\\u2184|[\\u249C-\\u24E9]\n'
                   '|[\\u271D-\\u271F]|\\u2C2E|\\u2C5E|[\\u2C60-\\u2C7C]|[\\u2C7E-\\u2C7F]|[\\uA722-\\uA76F]\n'
                   '|[\\uA771-\\uA787]|[\\uA78B-\\uA7BF]|[\\uA7C2-\\uA7C6]|\\uA7F7|[\\uA7FA-\\uA7FF]\n'
                   '|[\\uAB30-\\uAB5A]|[\\uAB60-\\uAB64]|[\\uAB66-\\uAB67]|[\\uFB00-\\uFB06]|[\\uFF21-\\uFF3A]\n'
                   '|[\\uFF41-\\uFF5A]|[\\U0001F110-\\U0001F12C]|[\\U0001F130-\\U0001F149]\n'
                   '|[\\U0001F150-\\U0001F169]|[\\U0001F170-\\U0001F18A]|\\U0001F1A5|[\\U0001F520-\\U0001F521]\n'
                   '|\\U0001F524|[\\U0001F546-\\U0001F547]|[\\U000E0041-\\U000E005A]|[\\U000E0061-\\U000E007A]')"""
        assert parser.python_src__.find(expected) >= 0
        lang = r"""
        literal = /(?:(?:(?:[\t ]*)?(?:(?:(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/))(?:[\t ]*)?)*))(?:,)(?:(?:(?:[\t ]*)?(?:(?:(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/))(?:[\t ]*)?)*))/
        """
        parser = create_parser(lang)
        expected = r"""    literal = RegExp('(?:(?:(?:[\\t ]*)?(?:(?:(?://.*)|(?:/\\*(?:.|\\n)*?\\*/))(?:[\\t ]*)?)*))(?:,)('
       '?:(?:(?:[\\t ]*)?(?:(?:(?://.*)|(?:/\\*(?:.|\\n)*?\\*/))(?:[\\t ]*)?)*))')"""
        assert parser.python_src__.find(expected) >= 0
        lang = r"""
        literal = /(?:(?:(?:[\t ]*)?(?:(?:(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/))(?:[\t ]*)?)*))(?P<TEXT>,)(?:(?:(?:[\t ]*)?(?:(?:(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/))(?:[\t ]*)?)*))/
        """
        parser = create_parser(lang)
        expected = r"""    literal = SmartRE('(?:(?:(?:[\\t ]*)?(?:(?:(?://.*)|(?:/\\*(?:.|\\n)*?\\*/))(?:[\\t ]*)?)*))(?P<TE'
        'XT>,)(?:(?:(?:[\\t ]*)?(?:(?:(?://.*)|(?:/\\*(?:.|\\n)*?\\*/))(?:[\\t ]*)?)*))')"""
        assert parser.python_src__.find(expected) >= 0


class TestStringLiterals:
    def test_string_literals(self):
        lang = r'''secret = "\'"
        '''
        p = create_parser(lang)
        root = p(r"\'")
        assert not root.errors
        assert root.strlen() == 2

    def test_plaintext_literals(self):
        lang = r'''secret = `\'`
        '''
        p = create_parser(lang)
        root = p(r"\'")
        assert not root.errors
        assert root.strlen() == 2


class TestOptimizations:
    def setup_method(self):
        self.save_optimizations = get_config_value('optimizations')

    def teardown_method(self):
        set_config_value('optimizations', self.save_optimizations)

    def test_literal_optimization(self):
        save = get_config_value('optimizations')

        from DHParser.dsl import grammar_provider
        lang = '''
               @literalws = both  # both needed, because single sided literals would be stell slower when optimized
               doc = "AAA" '''

        set_config_value('optimizations', frozenset())
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') < 0
        tree = parser("AAA  ")
        assert tree.as_sxpr() == '(doc (:Text "AAA") (:Whitespace "  "))'

        set_config_value('optimizations', frozenset({'literal'}))
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser("AAA  ")
        assert tree.as_sxpr() == '(doc (:Text "AAA") (:Whitespace "  "))'

        set_config_value('optimizations', save)

    def test_repeated_groups(self):
        save = get_config_value('optimizations')
        set_config_value('optimizations', frozenset({'literal'}))
        lang = '''
               @literalws = both
               doc = "AAA" '''
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        # print(parser.python_src__)
        # TODO: This is a stub

        set_config_value('optimizations', save)

    def test_plaintext(self):
        save = get_config_value('optimizations')
        set_config_value('optimizations', frozenset({'alternative'}))
        from DHParser.dsl import grammar_provider
        lang = '''@reduction = merge
        EXP = (`E`|`e`) [`+`|`-`] /[0-9]+/ '''
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser('E+18')
        assert tree.as_sxpr() == '(EXP "E+18")'
        set_config_value('optimizations', save)

    def test_char_ranges(self):
        set_config_value('optimizations', frozenset({'alternative'}))
        save_syn = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'strict')
        lang = """Char ::= #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]
        """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        st = parser('賌')
        assert st.as_sxpr() == '(Char "賌")', st.as_sxpr()
        set_config_value('syntax_variant', save_syn)

    def test_macros(self):
        set_config_value('optimizations', frozenset({'alternative'}))
        lang = r'''@disposable = $close
        keyword = "Open" | $close | /\w+/
        $close = "Close" '''
        parser = create_parser(lang)
        assert parser.python_src__.rfind('SmartRE(') >= 0, parser.python_src__
        assert parser('Close').as_sxpr() == '(keyword "Close")'

        lang = '@drop = $close\n' + lang
        parser = create_parser(lang)
        assert parser.python_src__.rfind('SmartRE') >= 0, parser.python_src__
        assert parser('Close').as_sxpr() == '(keyword)'

    def test_option(self):
        set_config_value('optimizations', frozenset({'alternative'}))
        lang = r'''lang = keyword /.*/
        keyword = "Open" | [/\w+/]'''
        parser = create_parser(lang)
        assert parser.python_src__.rfind('SmartRE(') >= 0, parser.python_src__
        tree = parser('#*?')
        assert not tree.errors
        assert tree.as_sxpr() == '(lang (keyword) (:RegExp "#*?"))'

    def test_complex_regexes(self):
        set_config_value('optimizations', frozenset({'alternative'}))
        lang = r'''
            lang = "abcdefg" | /[^\d()]*(?=[\d(])/'''
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser('abcdefg')
        assert not tree.errors

    def test_complex_regexes_2(self):
        set_config_value('optimizations', frozenset({'alternative'}))
        lang = r'''
        literal    = /"(?:(?<!\\)\\"|[^"])*?"/
                   | /'(?:(?<!\\)\\'|[^'])*?'/
                   | /’(?:(?<!\\)\\’|[^’])*?’/
        plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/
                   | /´(?:(?<!\\)\\´|[^´])*?´/
        '''
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser(r'"\""')
        assert not tree.errors
        assert tree.as_sxpr() == r'''(literal '"\""')'''

    def test_ignore_case(self):
        set_config_value('optimizations', frozenset({'alternative'}))
        lang = r'''@ignorecase = True
        voidElement     = '<' ( 'area' | 'base' | 'br' | 'col' | 'embed' | 'hr'
                       | 'img' | 'input' | 'link' | 'meta' | 'param'
                       | 'source' | 'track' | 'wbr' ) '>'
        '''
        parser = create_parser(lang)
        assert parser.python_src__.find("SmartRE(f'(?i)(?P<:IgnoreCase>") >= 0
        tree = parser('<BR>')
        assert tree.as_sxpr() == '(voidElement (:IgnoreCase "<") (:IgnoreCase "BR") (:IgnoreCase ">"))'

    def test_sequence(self):
        set_config_value('optimizations', frozenset({'sequence'}))
        lang = '''@reduction = merge
        doc = "a" "b" "c" /d/'''
        parser = create_parser(lang)
        assert parser.python_src__.find("SmartRE(f'(?P<:Text>abc)(d)',") >= 0
        assert parser('abcd').as_sxpr() == '(doc "abcd")'

        lang = '''@reduction = merge
        doc = ("a"|"b") ("c"|"d")'''
        parser = create_parser(lang)
        assert parser.python_src__.find("SmartRE(f'(?P<:Text>(?:a|b)(?:c|d))',") >= 0
        assert parser('ad').as_sxpr() == '(doc "ad")'

        lang = '''@reduction = merge
        doc = ("a"|"b") ("c"|"d") ("ef"|/gh/|"ij")'''
        parser = create_parser(lang)
        assert parser.python_src__.find("SmartRE(f'(?P<:Text>(?:a|b)(?:c|d))(?:(?P<:Text>ef)|(gh)|(?P<:Text>ij))',") >= 0
        assert parser('bcgh').as_sxpr() == '(doc "bcgh")'

    def test_complex_sequence(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang = r"""@ whitespace  = /\s*/
        @ literalws   = none
        @ comment     = //
        @ ignorecase  = False
        @ reduction   = merge_treetops
        @ drop        = strings, whitespace

        SDDecl = ~ 'standalone' ~ '=' ~ (("'" (`yes` | `no`) "'") | ('"' (`yes` | `no`) '"'))"""
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser('''standalone="yes"''')
        # for e in tree.errors:  print(e)
        assert not tree.errors
        assert tree.as_sxpr() == '(SDDecl "yes")'

    def test_sequence2(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang='''
        doc = `` 'A' | 'B' | 'C'
        '''
        parser = create_parser(lang)
        assert parser.python_src__.find("SmartRE(f'(?P<:Text>)(?P<:Text>A)|(?P<:Text>B|C)',") >= 0
        lang = "@reduction = merge_treetops" + lang
        parser = create_parser(lang)
        assert parser.python_src__.find("SmartRE(f'(?P<:Text>A|B|C)',")

    def test_sequence3(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        numbers = r"""@whitespace = vertical
        document = { ~ number | error } ~ EOF
        number = /[1-9]\d*/~
        error  = !EOF @Error("»{1}« is not a valid Number!") /.*?(?=\s|$)/  # skip to next whitespace
        EOF = !/./
        """
        parser = create_parser(numbers)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser("2 3 4")
        assert not tree.errors
        tree = parser("2 X 3 Y 4")
        assert len(tree.errors) == 2
        # print(tree.as_sxpr())
        nd = tree.pick(':RegExp', reverse=True)
        assert nd.content != "4"  # :RegExp was not reduced!!!
        # print(tree.as_sxpr())

    def test_sequence4(self):
        set_config_value('optimizations', frozenset({'alternative', 'sequence'}))
        lang = """@whitespace = linefeed
            @ literalws = right
            expression =  term  { ("+" | "-") term }
            term       =  factor  { ("*" | "/") factor }
            factor     =  constant | "("  expression  ")"
            constant   =  digit { digit } [ ~ ]
            digit      = /0/ | /1/ | /2/ | /3/ | /4/ | /5/ | /6/ | /7/ | /8/ | /9/
            """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0

    def test_sequence5(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative', 'literal'}))
        lang = r"""
        @reduction = merge
        list = string [WS] { SEP [WS] string [WS] }
        string = QUOT /[^"]*/ QUOT
        SEP = `,` -> drop
        WS = /\s+/ -> drop
        QUOT = `"` -> hide
        """
        parser = create_parser(lang)

    def test_any_char(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang = '''doc = "A".'''
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0, str(get_config_value('optimizations'))
        st = parser('A翿')
        assert st.as_sxpr() == '(doc (:Text "A") (:AnyChar "翿"))'

    def test_drop(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative', 'literal'}))
        # set_config_value('optimizations', frozenset())
        lang = r"""
        @reduction = none
        list = string [WS] { SEP [WS] string [WS] }
        string = ((`'` | QUOT) -> drop) /[^"]*/ (`'` | QUOT)
        SEP = (`,` -> drop)
        WS = /\s+/ -> drop
        QUOT = `"`
        """
        parser = create_parser(lang)

    def test_macro_complex_case(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang = r'''@ whitespace  = /[ \t]*/
        @ reduction   = merge
        @ disposable  = WS, EOF, LINE, S
        @ drop        = WS, EOF, backticked
        document = main [WS] §EOF
        $one_sec($level_sign, $sub_level) = [WS] $level_sign !`#` heading [blocks] { $sub_level }
        $sec_seq($sec) = { [WS] $sec }+
        main = $one_sec(`#`, sections)
        sections = $sec_seq(section)
        section = $one_sec(`##`, subsections)
        subsections = $sec_seq(subsection)
        subsection = $one_sec(`###`, subsubsections)
        subsubsections = $sec_seq(subsubsection)
        subsubsection = $one_sec(`####`, NEVER_MATCH)
        heading = LINE
        blocks = [WS] block { PARSEP block }
        block  = !is_heading line { lf !is_heading line }
          line = LINE
          lf   = S
        is_heading = /##?#?#?#?#?(?!#)/
        LINE      = /[ \t]*[^\n]+/
        WS        = /(?:[ \t]*\n)+/  # empty lines
        S         = !PARSEP /\s+/
        PARSEP    = /[ \t]*\n[ \t]*\n\s*/
        NEVER_MATCH = /..(?<=^)/
        EOF       =  !/./
        '''
        parser = create_parser(lang)

    def test_braces(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang = r"""
        free_char = /[^\n\[\]\\]/ | /\\[nrtfv`´'"(){}\[\]\/\\]/"""
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0

    def test_braces2(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang = r"""
        tag = "begin{" | "end{" """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0

    def test_expression_of_sequences(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        lang = r"""@ whitespace  = /\s*/
        @ literalws   = none
        @ comment     = //
        @ ignorecase  = True
        @ reduction   = merge_treetops
        @ drop        = strings, whitespace
        SystemLiteral   = '"' /[^"]*/ '"' | "'" /[^']*/ "'" """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0

    def test_char_range(self):
        set_config_value('optimizations', frozenset({'sequence', 'alternative'}))
        save = get_config_value('syntax_variant')
        set_config_value('syntax_variant', 'heuristic')
        lang = r"""
        Char <- [nrt´"\[\]\\] / !´\\´
        """
        parser = create_parser(lang)
        set_config_value('syntax_variant', save)

    def test_keepdata(self):
        set_config_value('optimizations', frozenset({'alternative', 'sequence'}))
        lang = r"""@ literalws  = right
        @ whitespace = /[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?/    # insignificant whitespace, including at most one linefeed
        @ comment    = /%.*/                                # note: trailing linefeed is not part of the comment proper
        @ reduction  = merge_treetops
        @ disposable = /_\w+/
        @ drop       = strings, backticked, whitespace, regexps
        CMDNAME = /\\@?(?:(?![\d_])\w)+/~ """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser(r'\abc')
        assert tree.as_sxpr() == r'(CMDNAME "\abc")'

    def test_keepdata_plain(self):
        set_config_value('optimizations', frozenset())
        lang = r"""@ literalws  = right
        @ whitespace = /[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?/    # insignificant whitespace, including at most one linefeed
        @ comment    = /%.*/                                # note: trailing linefeed is not part of the comment proper
        @ reduction  = merge_treetops
        @ disposable = /_\w+/
        @ drop       = strings, backticked, whitespace, regexps
        CMDNAME = /\\@?(?:(?![\d_])\w)+/~ """
        parser = create_parser(lang)
        tree = parser(r'\abc')
        assert tree.as_sxpr() == r'(CMDNAME "\abc")'

    def test_option(self):
        set_config_value('optimizations', frozenset({'alternative', 'sequence'}))
        lang = """@ literalws = right
        EtymologieSprache = "theod." ["inf."] ["vet."] """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser("theod. vet.")
        assert not tree.errors
        assert tree.as_sxpr() == '(EtymologieSprache (:Text "theod.") (:Whitespace " ") (:Text "vet."))'

    def test_regex(self):
        set_config_value('optimizations', frozenset({'alternative', 'sequence'}))
        lang = r"""@ literalws = right
        ROEM_NORMAL = ~/(?!D[.|])(?![M][^\w])(?=[MDCLXVI])M*(C+[MD]|D?C*)(X+[CL]|L?X*)(I+[XV]|V?I*)(?=1|[^\w]|_)\.?/~ """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        tree = parser("II.")
        assert tree.as_sxpr() == '(ROEM_NORMAL "II.")'

    def test_lookahead(self):
        from DHParser.trace import set_tracer, trace_history
        from DHParser.error import PARSER_LOOKAHEAD_MATCH_ONLY
        set_config_value('optimizations', frozenset({'alternative', 'sequence', 'lookahead'}))
        # set_config_value('optimizations', frozenset())
        lang = """@literalws = left
        doc = "Hallo" & "?" """
        parser = create_parser(lang)
        assert parser.python_src__.find('SmartRE(') >= 0
        set_tracer(parser["doc"].descendants(), trace_history)
        tree = parser("Hallo?")
        assert any(e.code == PARSER_LOOKAHEAD_MATCH_ONLY for e in tree.errors)

    def test_lookahead2(self):
        from DHParser.trace import set_tracer, trace_history
        from DHParser.error import PARSER_LOOKAHEAD_MATCH_ONLY
        set_config_value('optimizations', frozenset({'alternative', 'sequence', 'lookahead'}))
        # set_config_value('optimizations', frozenset())
        lang = """@literalws = left
        doc = greeting & (~ "?")
        greeting = "Hallo" """
        parser = create_parser(lang)
        # print(parser.python_src__)
        assert parser.python_src__.find('SmartRE(') >= 0
        set_tracer(parser["doc"].descendants(), trace_history)
        tree = parser("Hallo?")
        assert any(e.code == PARSER_LOOKAHEAD_MATCH_ONLY for e in tree.errors)

    def test_comments(self):
        lang = r"""@ optimizations = all
        @ whitespace  = /\s*/           # implicit whitespace, includes linefeeds
        @ literalws   = right           # literals have implicit whitespace on the right hand side
        @ comment_keep = /(?:\/\/.*)\n?|(?:\/\*(?:.|\n)*?\*\/) *\n?/   # /* ... */ or // to EOL
        @ ignorecase  = False           # literals and regular expressions are case-sensitive
        @ reduction   = merge_treetops  # anonymous nodes are being reduced where possible
        @ drop        = whitespace, strings

        document = `hallo` ~
        word     = /\w+/
        """
        parser = create_parser(lang)
        tree = parser('hallo /* Kommentar */ ')
        assert not tree.errors
        assert tree.as_sxpr() == '(document (:Text "hallo") (comment__ " /* Kommentar */ "))'


FlexibleEBNF = r'''
@ optimizations = all
@ comment    = /(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/|\(\*(?:.|\n)*?\*\)/
    # comments can be either C-Style: /* ... */
    # or pascal/modula/oberon-style: (* ... *)
    # or python-style: # ... \n, excluding, however, character markers: #x20
@ whitespace = /\s*/                            # whitespace includes linefeed
@ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
@ hide       = is_mdef, component, pure_elem, countable, no_range, FOLLOW_UP,
               MOD_SYM, MOD_SEP, ANY_SUFFIX, EOF
@ drop       = whitespace, MOD_SYM, EOF, no_range        # do not include these even in the concrete syntax tree
@ RNG_BRACE_filter = matching_bracket()         # filter or transform content of RNG_BRACE on retrieve

# re-entry-rules for resuming after parsing-error

@ definition_resume = /\n\s*(?=@|\w+\w*\s*=)/
@ directive_resume  = /\n\s*(?=@|\w+\w*\s*=)/

# specialized error messages for certain cases

@ definition_error  = /,/, 'Delimiter "," not expected in definition!\nEither this was meant to '
                           'be a directive and the directive symbol @ is missing\nor the error is '
                           'due to inconsistent use of the comma as a delimiter\nfor the elements '
                           'of a sequence.'


#: top-level

syntax     = ~ { definition | directive | macrodef } EOF
definition = [modifier] symbol §:DEF~ [ :OR~ ] expression [ MOD_SYM~ hide ]
             :ENDL~ & FOLLOW_UP  # [:OR~] to support v. Rossum's syntax
  modifier = (drop | [hide]) MOD_SEP   # node LF after modifier allowed!
  is_def   = [ MOD_SEP symbol ] :DEF | MOD_SEP is_mdef
  _is_def  = [ MOD_SEP symbol ] _DEF | MOD_SEP is_mdef
  MOD_SEP  = / *: */

directive  = "@" §symbol "=" component { "," component } & FOLLOW_UP
  # component  = (regexp | literals | procedure | symbol !DEF)
  component  = regexp | literals | procedure | symbol !_DEF !_is_def
             | &`$` !is_mdef § placeholder !is_def
             | "(" expression ")"  | RAISE_EXPR_WO_BRACKETS expression
  literals   = { literal }+                       # string chaining, only allowed in directives!
  procedure  = SYM_REGEX "()"                     # procedure name, only allowed in directives!

macrodef   =  [modifier] "$" name~ ["(" §placeholder { "," placeholder }  ")"]
             :DEF~ [ OR~ ] macrobody [ MOD_SYM~ hide ] :ENDL~ & FOLLOW_UP
  macrobody  = expression
  is_mdef    = "$" name ["(" placeholder { "," placeholder }  ")"] ~:DEF

FOLLOW_UP  = `@` | `$` | modifier | symbol | EOF


#: components

expression = sequence { :OR~ sequence }
sequence   = ["§"] ( interleave | lookaround )  # "§" means all following terms mandatory
             { !`@` !(symbol :DEF) :AND~ ["§"] ( interleave | lookaround ) }
interleave = difference { "°" ["§"] difference }
lookaround = flowmarker § part
difference = term [!`->` "-" § part]
term       = (oneormore | counted | repetition | option | pure_elem) [ MOD_SYM~ drop ]
part       = (oneormore | pure_elem) [ MOD_SYM~ drop ]


#: tree-reduction-markers aka "AST-hints"

drop       = "DROP" | "Drop" | "drop" | "SKIP" | "Skip" | "skip"
hide       = "HIDE" | "Hide" | "hide" | "DISPOSE" | "Dispose" | "dispose"


#: elements


countable  = option | oneormore | element
pure_elem  = element § !ANY_SUFFIX              # element strictly without a suffix
element    = [retrieveop] symbol !is_def        # negative lookahead to be sure it's not a definition
           | literal
           | plaintext
           | char_ranges
           | regexp
           | char_range
           | character ~
           | any_char
           | whitespace
           | group
           | macro !is_def
           | placeholder !is_def
           | parser                             # a user-defined parser


ANY_SUFFIX = /[?*+]/


#: flow-operators

flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
           | "<-!" | "<-&"                      # '<-!' negative lookbehind, '<-&' positive lookbehind
retrieveop = "::" | ":?" | ":"                  # '::' pop, ':?' optional pop, ':' retrieve


#: groups

group      = "(" no_range §expression ")"
oneormore  = "{" no_range expression "}+" | element "+"
repetition = "{" no_range §expression "}" | element "*" no_range
option     = !char_range "[" §expression "]" | element "?"
counted    = countable range | countable :TIMES~ multiplier | multiplier :TIMES~ §countable

range      = RNG_BRACE~ multiplier [ :RNG_DELIM~ multiplier ] ::RNG_BRACE~
no_range   = !multiplier | &multiplier :TIMES
multiplier = /\d+/~


#: leaf-elements

parser     = "@" name "(" [argument] ")"        # a user defined parser
  argument = literal | name~

symbol     = SYM_REGEX ~                        # e.g. expression, term, parameter_list
literal    = /"(?:(?<!\\)(?:\\\\)*\\"|[^"])*?"/~  # e.g. "(", '+', 'while'
           | /'(?:(?<!\\)(?:\\\\)*\\'|[^'])*?'/~  # whitespace following literals will be ignored tacitly.
           | /’(?:(?<!\\)(?:\\\\)*\\’|[^’])*?’/~
plaintext  = /`(?:(?<!\\)(?:\\\\)*\\`|[^`])*?`/~  # like literal but does not eat whitespace
           | /´(?:(?<!\\)(?:\\\\)*\\´|[^´])*?´/~
regexp     = :RE_LEADIN RE_CORE :RE_LEADOUT ~   # e.g. /\w+/, ~/#.*(?:\n|$)/~
# regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~     # e.g. /\w+/, ~/#.*(?:\n|$)/~

char_range = `[` &char_range_heuristics [`^`] { range_desc }+ "]"
char_ranges = RE_LEADIN range_chain { `|` range_chain } RE_LEADOUT ~
  range_chain = `[` [`^`] { range_desc }+ `]`
  range_desc = (character | free_char) [ [`-`] (character | free_char) ]

character  = :CH_LEADIN HEXCODE
free_char  = /[^\n\[\]\\]/ | /\\[nrtfv`´'"(){}\[\]\/\\]/
any_char   = "."
whitespace = /~/~                               # insignificant whitespace


#: macros

macro       = "$" name "(" no_range expression { "," no_range expression } ")"
placeholder = "$" name !`(` ~

name        = SYM_REGEX


#: delimiters

EOF = !/./ [:?ENDL] [:?DEF] [:?OR] [:?AND]      # [:?DEF], [:?OR], ... clear stack by eating stored value
           [:?RNG_DELIM] [:?BRACE_SIGN] [:?CH_LEADIN] [:?TIMES] [:?RE_LEADIN] [:?RE_LEADOUT]

DEF        = _DEF
_DEF       = `=` | `:=` | `::=` | `<-` | /:\n/ | `: `  # with `: `, retrieve markers mustn't be followed by a blank!
OR         = `|` | `/` !regex_heuristics
AND        =  `,` | ``
ENDL       = `;` | ``

RNG_BRACE  = :BRACE_SIGN
BRACE_SIGN = `{` | `(`
RNG_DELIM  = `,`
TIMES      = `*`

RE_LEADIN  = `/` &regex_heuristics | `^/`
RE_LEADOUT = `/`

CH_LEADIN  = `0x` | `%x` | `U+` | `u+` | `#x` | `\x` | `\u` | `\U`

MOD_SYM   = `->`

#: heuristics

char_range_heuristics  = ! ( /[\n]/ | more_than_one_blank
                           | ~ literal_heuristics
                           | ~ [`::`|`:?`|`:`] STRICT_SYM_REGEX /\s*\]/ )
                         & ({ range_desc }+ `]`)
  STRICT_SYM_REGEX     = /(?!\d)\w+/
more_than_one_blank    = /[^ \]]*[ ][^ \]]*[ ]/
literal_heuristics     = /~?\s*"(?:[\\]\]|[^\]]|[^\\]\[[^"]*)*"/
                       | /~?\s*'(?:[\\]\]|[^\]]|[^\\]\[[^']*)*'/
                       | /~?\s*`(?:[\\]\]|[^\]]|[^\\]\[[^`]*)*`/
                       | /~?\s*´(?:[\\]\]|[^\]]|[^\\]\[[^´]*)*´/
                       | /~?\s*\/(?:[\\]\]|[^\]]|[^\\]\[[^\/]*)*\//
regex_heuristics       = ! ( / +`[^`]*` +\//
                           | / +´[^´]*´ +\//
                           | / +'[^']*' +\//
                           | / +"[^"]*" +\//
                           | / +\w+ +\// )
                         ( /[^\/\n*?+\\]*[*?+\\][^\/\n]*\//
                         | /[^\w]+\//
                         | /[^ ]/ )

#: basic-regexes

RE_CORE    = /(?:(?<!\\)\\(?:\/)|[^\/])*/       # core of a regular expression, i.e. the dots in /.../
SYM_REGEX  = /(?!\d)\w(?:-?\w)*/                # regular expression for symbols
HEXCODE    = /(?:[A-Fa-f1-9]|0(?!x)){1,8}/


#: error-markers

RAISE_EXPR_WO_BRACKETS = ``
'''


class TestSerialization:
    def test_serialization_simple(self):
        gr = r"""document = { paragraph }
            paragraph = word { ws word }
            HIDE:word = /\w+/
            ws = / +/ -> DROP"""
        cst = parse_ebnf(gr)
        ast = transform_ebnf(cst)
        ebnf = ast.evaluate_path(EBNF_AST_Serialization_Table, path=[ast])
        assert ebnf == r"""document = { paragraph }
paragraph = word { ws word }
HIDE:word = /\w+/
ws = / +/ -> DROP"""
        cst2 = parse_ebnf(ebnf)
        ast2 = transform_ebnf(cst2)
        assert ast2.equals(ast)

    def test_counted(self):
        gr = r'''documnt = x y z
            x = "a"*3
            y = 44*"b"
            z = "cde"{4,21}
        '''
        cst = parse_ebnf(gr)
        ast = transform_ebnf(cst)
        ebnf = (ast.evaluate_path(EBNF_AST_Serialization_Table, path=[ast]))
        ast2 = transform_ebnf(parse_ebnf(ebnf))
        assert ast2.equals(ast)

    def test_directives(self):
        gr = r'''    @ comment    = /(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/|\(\*(?:.|\n)*?\*\)/
            @ whitespace = /\s*/
            @ literalws  = right
            @ disposable = component, pure_elem, countable, FOLLOW_UP, SYM_REGEX, ANY_SUFFIX, EOF
            @ drop       = whitespace, EOF
            @ RNG_BRACE_filter = matching_bracket()
            @ definition_resume = /\n\s*(?=@|\w+\w*\s*=)/
            @ directive_resume  = /\n\s*(?=@|\w+\w*\s*=)/    
            @ definition_error  = /,/, 'Delimiter "," not expected in definition!\nEither this was meant to '
                                       'be a directive and the directive symbol @ is missing\nor the error is '
                                       'due to inconsistent use of the comma as a delimiter\nfor the elements '
                                       'of a sequence.'
            syntax     = ~ { definition | directive } EOF
            definition = "a" § "b"
            directive = "c" § "d"'''
        cst = parse_ebnf(gr)
        ast = transform_ebnf(cst)
        ebnf = ast.evaluate_path(EBNF_AST_Serialization_Table, path=[ast])
        ast2 = transform_ebnf(parse_ebnf(ebnf))
        assert ast2.equals(ast)

    def test_ebnf(self):
        cst = parse_ebnf(FlexibleEBNF)
        ast = transform_ebnf(cst)
        ebnf = ast.evaluate_path(EBNF_AST_Serialization_Table, path=[ast])
        cst2 = parse_ebnf(ebnf)
        ast2 = transform_ebnf(cst2)
        assert ast2.equals(ast)
        iso_ebnf = ebnf_from_ast(ast2, 'ISO')
        cst3 = parse_ebnf(iso_ebnf, "classic")
        assert not cst3.errors
        ast3 = transform_ebnf(cst3)
        assert ast3.equals(ast2)

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
