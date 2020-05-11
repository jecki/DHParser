# ebnf.py - EBNF -> Python-Parser compilation for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.


"""
Module ``ebnf`` provides a self-hosting parser for EBNF-Grammars as
well as an EBNF-compiler that compiles an EBNF-Grammar into a
DHParser based Grammar class that can be executed to parse source text
conforming to this grammar into contrete syntax trees.
"""


from collections import OrderedDict
from functools import partial
import keyword
import os
from typing import Callable, Dict, List, Set, Tuple, Sequence, Union, Optional, Any

from DHParser.compile import CompilerError, Compiler, ResultTuple, compile_source, visitor_name
from DHParser.configuration import access_thread_locals, get_config_value, \
    EBNF_ANY_SYNTAX_HEURISTICAL, EBNF_ANY_SYNTAX_STRICT, EBNF_CLASSIC_SYNTAX, \
    EBNF_REGULAR_EXPRESSION_SYNTAX, EBNF_PARSING_EXPRESSION_GRAMMAR_SYNTAX
from DHParser.error import Error, AMBIGUOUS_ERROR_HANDLING, WARNING, REDECLARED_TOKEN_WARNING,\
    REDEFINED_DIRECTIVE, UNUSED_ERROR_HANDLING_WARNING, INAPPROPRIATE_SYMBOL_FOR_DIRECTIVE, \
    DIRECTIVE_FOR_NONEXISTANT_SYMBOL, UNDEFINED_SYMBOL_IN_TRANSTABLE_WARNING, \
    REORDERING_OF_ALTERNATIVES_REQUIRED, BAD_ORDER_OF_ALTERNATIVES
from DHParser.parse import Parser, Grammar, mixin_comment, mixin_nonempty, Forward, RegExp, \
    Drop, Lookahead, NegativeLookahead, Alternative, Series, Option, ZeroOrMore, OneOrMore, \
    Text, Capture, Retrieve, Pop, optional_last_value, GrammarError, Whitespace, Always, Never, \
    INFINITE, matching_bracket, ParseFunc
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc
from DHParser.syntaxtree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, EMPTY_NODE
from DHParser.toolkit import load_if_file, escape_re, escape_control_characters, md5, \
    sane_parser_name, re, expand_table, unrepr, compile_python_object, DHPARSER_PARENTDIR, \
    RX_NEVER_MATCH
from DHParser.transform import TransformationFunc, traverse, remove_brackets, \
    reduce_single_child, replace_by_single_child, is_empty, remove_children, \
    remove_tokens, flatten, forbid, assert_content, remove_children_if, all_of, not_one_of
from DHParser.versionnumber import __version__


__all__ = ('get_ebnf_preprocessor',
           'get_ebnf_grammar',
           'get_ebnf_transformer',
           'get_ebnf_compiler',
           'parse_ebnf',
           'transform_ebnf',
           'compile_ebnf_ast',
           'EBNFGrammar',
           'EBNFTransform',
           'EBNFCompilerError',
           'EBNFCompiler',
           'grammar_changed',
           'compile_ebnf',
           'PreprocessorFactoryFunc',
           'ParserFactoryFunc',
           'TransformerFactoryFunc',
           'CompilerFactoryFunc')


########################################################################
#
# source code support
#
########################################################################


DHPARSER_IMPORTS = '''
import collections
from functools import partial
import os
import sys

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'{dhparser_parentdir}'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \\
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, AnyChar, \\
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, \\
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \\
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \\
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \\
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \\
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \\
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \\
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \\
    merge_adjacent, collapse, collapse_children_if, transform_content, WHITESPACE_PTYPE, \\
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \\
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \\
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \\
    transform_content, replace_content_with, forbid, assert_content, remove_infix_operator, \\
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \\
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, node_maker, \\
    INDENTED_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \\
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \\
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \\
    positions_of, replace_tag_names, add_attributes, delimit_children, merge_connected, \\
    has_attr, has_parent
'''


########################################################################
#
# EBNF scanning
#
########################################################################


def get_ebnf_preprocessor() -> PreprocessorFunc:
    """
    Returns the preprocessor function for the EBNF compiler.
    As of now, no preprocessing is needed for EBNF-sources. Therefore,
    just a dummy function is returned.
    """
    return nil_preprocessor


########################################################################
#
# EBNF parsing
#
########################################################################


class EBNFGrammar(Grammar):
    r"""Parser for a FlexibleEBNF source file.

    This grammar is tuned for flexibility, that is, it supports as many
    different flavors of EBNF as possible. However, this flexibility
    comes at the cost of some ambiguities. In particular:

       1. the alternative OR-operator / could be mistaken for the start
          of a regular expression and vice versa, and
       2. character ranges [a-z] can be mistaken for optional blocks
          and vice versa

    A strategy to avoid these ambiguities is to do all of the following:

        - replace the free_char-parser by a never matching parser
        - if this is done, it is safe to replace the char_range_heuristics-
          parser by an always matching parser
        - replace the regex_heuristics by an always matching parser

    Ambiguities can also be avoided by NOT using all the syntactic variants
    made possible by this EBNF-grammar within one and the same EBNF-document.

    EBNF-definition of the Grammar::

        @ comment    = /(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/|\(\*(?:.|\n)*?\*\)/
        # comments can be either C-Style: /* ... */
        # or pascal/modula/oberon-style: (* ... *)
        # or python-style: # ... \n, excluding, however, character markers: #x20

        @ whitespace = /\s*/                            # whitespace includes linefeed
        @ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
        @ anonymous  = pure_elem, countable, FOLLOW_UP, SYM_REGEX, ANY_SUFFIX, EOF
        @ drop       = whitespace, EOF                  # do not include these even in the concrete syntax tree
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

        syntax     = ~ { definition | directive } EOF
        definition = symbol §:DEF~ expression :ENDL~ & FOLLOW_UP

        directive  = "@" §symbol "=" (regexp | literals | procedure | symbol !DEF)
                     { "," (regexp | literals | procedure | symbol !DEF) } & FOLLOW_UP
        literals   = { literal }+                       # string chaining, only allowed in directives!
        procedure  = SYM_REGEX "()"                     # procedure name, only allowed in directives!

        FOLLOW_UP  = `@` | symbol | EOF


        #: components

        expression = sequence { :OR~ sequence }
        sequence   = ["§"] ( interleave | lookaround )  # "§" means all following terms mandatory
                     { :AND~ ["§"] ( interleave | lookaround ) }
        interleave = difference { "°" ["§"] difference }
        lookaround = flowmarker § (oneormore | pure_elem)
        difference = term ["-" § (oneormore | pure_elem)]
        term       = oneormore | counted | repetition | option | pure_elem


        #: elements

        countable  = option | oneormore | element
        pure_elem  = element § !ANY_SUFFIX              # element strictly without a suffix
        element    = [retrieveop] symbol !:DEF          # negative lookahead to be sure it's not a definition
                   | literal
                   | plaintext
                   | regexp
                   | char_range
                   | character ~
                   | any_char
                   | whitespace
                   | group


        ANY_SUFFIX = /[?*+]/


        #: flow-operators

        flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
                   | "<-!" | "<-&"                      # '<-' negative lookbehind, '<-&' positive lookbehind
        retrieveop = "::" | ":?" | ":"                  # '::' pop, ':?' optional pop, ':' retrieve


        #: groups

        group      = "(" no_range §expression ")"
        oneormore  = "{" no_range expression "}+" | element "+"
        repetition = "{" no_range §expression "}" | element "*" no_range
        option     = !char_range "[" §expression "]" | element "?"
        counted    = countable range | countable :TIMES~ multiplier | multiplier :TIMES~ §countable

        range      = RNG_BRACE~ multiplier [ :RNG_DELIM~ multiplier ] ::RNG_BRACE~
        no_range   = !multiplier | &multiplier :TIMES
        multiplier = /[1-9]\d*/~


        #: leaf-elements

        symbol     = SYM_REGEX ~                        # e.g. expression, term, parameter_list
        literal    = /"(?:(?<!\\)\\"|[^"])*?"/~         # e.g. "(", '+', 'while'
                   | /'(?:(?<!\\)\\'|[^'])*?'/~         # whitespace following literals will be ignored tacitly.
        plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~         # like literal but does not eat whitespace
                   | /´(?:(?<!\\)\\´|[^´])*?´/~
        regexp     = :RE_LEADIN RE_CORE :RE_LEADOUT ~   # e.g. /\w+/, ~/#.*(?:\n|$)/~
        # regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~     # e.g. /\w+/, ~/#.*(?:\n|$)/~
        char_range = `[` &char_range_heuristics
                         [`^`] (character | free_char) { [`-`] character | free_char } "]"
        character  = :CH_LEADIN HEXCODE
        free_char  = /[^\n\[\]\\]/ | /\\[nrt`´'"(){}\[\]\/\\]/
        any_char   = "."
        whitespace = /~/~                               # insignificant whitespace

        #: delimiters

        EOF = !/./ [:?DEF] [:?OR] [:?AND] [:?ENDL]      # [:?DEF], [:?OR], ... clear stack by eating stored value
                   [:?RNG_DELIM] [:?BRACE_SIGN] [:?CH_LEADIN] [:?TIMES] [:?RE_LEADIN] [:?RE_LEADOUT]

        DEF        = `=` | `:=` | `::=` | `<-`
        OR         = `|` | `/` !regex_heuristics
        AND        = `,` | ``
        ENDL       = `;` | ``

        RNG_BRACE  = :BRACE_SIGN
        BRACE_SIGN = `{` | `(`
        RNG_DELIM  = `,`
        TIMES      = `*`

        RE_LEADIN  = `/` &regex_heuristics | `^/`
        RE_LEADOUT = `/`

        CH_LEADIN  = `0x` | `#x`

        #: heuristics

        char_range_heuristics  = ! ( /[\n\t ]/
                                   | ~ literal_heuristics
                                   | [`::`|`:?`|`:`] SYM_REGEX /\s*\]/ )
        literal_heuristics     = /~?\s*"(?:[\\]\]|[^\]]|[^\\]\[[^"]*)*"/
                               | /~?\s*'(?:[\\]\]|[^\]]|[^\\]\[[^']*)*'/
                               | /~?\s*`(?:[\\]\]|[^\]]|[^\\]\[[^`]*)*`/
                               | /~?\s*´(?:[\\]\]|[^\]]|[^\\]\[[^´]*)*´/
                               | /~?\s*\/(?:[\\]\]|[^\]]|[^\\]\[[^\/]*)*\//
        regex_heuristics       = /[^ ]/ | /[^\/\n*?+\\]*[*?+\\][^\/\n]\//


        #: basic-regexes

        RE_CORE    = /(?:(?<!\\)\\(?:\/)|[^\/])*/       # core of a regular expression, i.e. the dots in /.../
        SYM_REGEX  = /(?!\d)\w+/                        # regular expression for symbols
        HEXCODE    = /[A-Fa-f0-9]{1,8}/
    """
    countable = Forward()
    element = Forward()
    expression = Forward()
    source_hash__ = "3bda01686407a47a9fd0a709bda53ae3"
    anonymous__ = re.compile('pure_elem$|countable$|FOLLOW_UP$|SYM_REGEX$|ANY_SUFFIX$|EOF$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'definition': [(re.compile(r','), 'Delimiter "," not expected in definition!\\nEither this was meant to be a directive and the directive symbol @ is missing\\nor the error is due to inconsistent use of the comma as a delimiter\\nfor the elements of a sequence.')]}
    resume_rules__ = {'definition': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')],
                      'directive': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')]}
    COMMENT__ = r'(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/|\(\*(?:.|\n)*?\*\)'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    HEXCODE = RegExp('[A-Fa-f0-9]{1,8}')
    SYM_REGEX = RegExp('(?!\\d)\\w+')
    RE_CORE = RegExp('(?:(?<!\\\\)\\\\(?:/)|[^/])*')
    regex_heuristics = Alternative(RegExp('[^ ]'), RegExp('[^/\\n*?+\\\\]*[*?+\\\\][^/\\n]/'))
    literal_heuristics = Alternative(RegExp('~?\\s*"(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^"]*)*"'), RegExp("~?\\s*'(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^']*)*'"), RegExp('~?\\s*`(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^`]*)*`'), RegExp('~?\\s*´(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^´]*)*´'), RegExp('~?\\s*/(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^/]*)*/'))
    char_range_heuristics = NegativeLookahead(Alternative(RegExp('[\\n\\t ]'), Series(dwsp__, literal_heuristics), Series(Option(Alternative(Text("::"), Text(":?"), Text(":"))), SYM_REGEX, RegExp('\\s*\\]'))))
    CH_LEADIN = Capture(Alternative(Text("0x"), Text("#x")))
    RE_LEADOUT = Capture(Text("/"))
    RE_LEADIN = Capture(Alternative(Series(Text("/"), Lookahead(regex_heuristics)), Text("^/")))
    TIMES = Capture(Text("*"))
    RNG_DELIM = Capture(Text(","))
    BRACE_SIGN = Capture(Alternative(Text("{"), Text("(")))
    RNG_BRACE = Capture(Retrieve(BRACE_SIGN))
    ENDL = Capture(Alternative(Text(";"), Text("")))
    AND = Capture(Alternative(Text(","), Text("")))
    OR = Capture(Alternative(Text("|"), Series(Text("/"), NegativeLookahead(regex_heuristics))))
    DEF = Capture(Alternative(Text("="), Text(":="), Text("::="), Text("<-")))
    EOF = Drop(Drop(Series(Drop(NegativeLookahead(RegExp('.'))), Drop(Option(Drop(Pop(DEF, match_func=optional_last_value)))), Drop(Option(Drop(Pop(OR, match_func=optional_last_value)))), Drop(Option(Drop(Pop(AND, match_func=optional_last_value)))), Drop(Option(Drop(Pop(ENDL, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RNG_DELIM, match_func=optional_last_value)))), Drop(Option(Drop(Pop(BRACE_SIGN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(CH_LEADIN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(TIMES, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RE_LEADIN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RE_LEADOUT, match_func=optional_last_value)))))))
    whitespace = Series(RegExp('~'), dwsp__)
    any_char = Series(Text("."), dwsp__)
    free_char = Alternative(RegExp('[^\\n\\[\\]\\\\]'), RegExp('\\\\[nrt`´\'"(){}\\[\\]/\\\\]'))
    character = Series(Retrieve(CH_LEADIN), HEXCODE)
    char_range = Series(Text("["), Lookahead(char_range_heuristics), Option(Text("^")), Alternative(character, free_char), ZeroOrMore(Alternative(Series(Option(Text("-")), character), free_char)), Series(Text("]"), dwsp__))
    regexp = Series(Retrieve(RE_LEADIN), RE_CORE, Retrieve(RE_LEADOUT), dwsp__)
    plaintext = Alternative(Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), dwsp__), Series(RegExp('´(?:(?<!\\\\)\\\\´|[^´])*?´'), dwsp__))
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), dwsp__), Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), dwsp__))
    symbol = Series(SYM_REGEX, dwsp__)
    multiplier = Series(RegExp('[1-9]\\d*'), dwsp__)
    no_range = Alternative(NegativeLookahead(multiplier), Series(Lookahead(multiplier), Retrieve(TIMES)))
    range = Series(RNG_BRACE, dwsp__, multiplier, Option(Series(Retrieve(RNG_DELIM), dwsp__, multiplier)), Pop(RNG_BRACE, match_func=matching_bracket), dwsp__)
    counted = Alternative(Series(countable, range), Series(countable, Retrieve(TIMES), dwsp__, multiplier), Series(multiplier, Retrieve(TIMES), dwsp__, countable, mandatory=3))
    option = Alternative(Series(NegativeLookahead(char_range), Series(Text("["), dwsp__), expression, Series(Text("]"), dwsp__), mandatory=2), Series(element, Series(Text("?"), dwsp__)))
    repetition = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}"), dwsp__), mandatory=2), Series(element, Series(Text("*"), dwsp__), no_range))
    oneormore = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}+"), dwsp__)), Series(element, Series(Text("+"), dwsp__)))
    group = Series(Series(Text("("), dwsp__), no_range, expression, Series(Text(")"), dwsp__), mandatory=2)
    retrieveop = Alternative(Series(Text("::"), dwsp__), Series(Text(":?"), dwsp__), Series(Text(":"), dwsp__))
    flowmarker = Alternative(Series(Text("!"), dwsp__), Series(Text("&"), dwsp__), Series(Text("<-!"), dwsp__), Series(Text("<-&"), dwsp__))
    ANY_SUFFIX = RegExp('[?*+]')
    element.set(Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(Retrieve(DEF))), literal, plaintext, regexp, char_range, Series(character, dwsp__), any_char, whitespace, group))
    pure_elem = Series(element, NegativeLookahead(ANY_SUFFIX), mandatory=1)
    countable.set(Alternative(option, oneormore, element))
    term = Alternative(oneormore, counted, repetition, option, pure_elem)
    difference = Series(term, Option(Series(Series(Text("-"), dwsp__), Alternative(oneormore, pure_elem), mandatory=1)))
    lookaround = Series(flowmarker, Alternative(oneormore, pure_elem), mandatory=1)
    interleave = Series(difference, ZeroOrMore(Series(Series(Text("°"), dwsp__), Option(Series(Text("§"), dwsp__)), difference)))
    sequence = Series(Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround), ZeroOrMore(Series(Retrieve(AND), dwsp__, Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround))))
    expression.set(Series(sequence, ZeroOrMore(Series(Retrieve(OR), dwsp__, sequence))))
    FOLLOW_UP = Alternative(Text("@"), symbol, EOF)
    procedure = Series(SYM_REGEX, Series(Text("()"), dwsp__))
    literals = OneOrMore(literal)
    directive = Series(Series(Text("@"), dwsp__), symbol, Series(Text("="), dwsp__), Alternative(regexp, literals, procedure, Series(symbol, NegativeLookahead(DEF))), ZeroOrMore(Series(Series(Text(","), dwsp__), Alternative(regexp, literals, procedure, Series(symbol, NegativeLookahead(DEF))))), Lookahead(FOLLOW_UP), mandatory=1)
    definition = Series(symbol, Retrieve(DEF), dwsp__, expression, Retrieve(ENDL), dwsp__, Lookahead(FOLLOW_UP), mandatory=1, err_msgs=error_messages__["definition"])
    syntax = Series(Option(dwsp__), ZeroOrMore(Alternative(definition, directive)), EOF)
    root__ = syntax

    free_char_parsefunc__ = free_char._parse
    char_range_heuristics_parsefunc__ = char_range_heuristics._parse
    regex_heuristics_parserfunc__ = regex_heuristics._parse

    @property
    def mode(self) -> str:
        def which(p: Parser) -> str:
            if p._parse_proxy.__qualname__ == 'Never._parse':
                return 'never'
            elif p._parse_proxy.__qualname__ == 'Always._parse':
                return 'always'
            else:
                return 'custom'
        signature = (
            which(self.free_char),
            which(self.regex_heuristics),
            which(self.char_range_heuristics)
        )
        if signature == ('custom', 'custom', 'custom'):
            return EBNF_ANY_SYNTAX_HEURISTICAL
        elif signature == ('never', 'always', 'always'):
            return EBNF_ANY_SYNTAX_STRICT  # or EBNF_CLASSIC_SYNTAX
        elif signature == ('custom', 'never', 'always'):
            return EBNF_PARSING_EXPRESSION_GRAMMAR_SYNTAX
        elif signature == ('custom', 'always', 'always'):
            return EBNF_REGULAR_EXPRESSION_SYNTAX
        else:
            return "undefined"

    @mode.setter
    def mode(self, mode: str):
        def set_parsefunc(p: Parser, f: ParseFunc):
            method = f.__get__(p, type(p))  # bind function f to parser p
            # if p._parse == p._parse_proxy:
            p._parse_proxy = method
            # p._parse = method

        always = Always._parse
        never = Never._parse
        if mode == EBNF_ANY_SYNTAX_HEURISTICAL:
            set_parsefunc(self.free_char, self.free_char_parsefunc__)
            set_parsefunc(self.regex_heuristics, self.regex_heuristics_parserfunc__)
            set_parsefunc(self.char_range_heuristics, self.char_range_heuristics_parsefunc__)
        elif mode in (EBNF_ANY_SYNTAX_STRICT, EBNF_CLASSIC_SYNTAX):
            set_parsefunc(self.free_char, never)
            set_parsefunc(self.regex_heuristics, always)
            set_parsefunc(self.char_range_heuristics, always)
        elif mode == EBNF_PARSING_EXPRESSION_GRAMMAR_SYNTAX:
            set_parsefunc(self.free_char, self.free_char_parsefunc__)
            set_parsefunc(self.regex_heuristics, never)
            set_parsefunc(self.char_range_heuristics, always)
        elif  mode == EBNF_REGULAR_EXPRESSION_SYNTAX:
            set_parsefunc(self.free_char, self.free_char_parsefunc__)
            set_parsefunc(self.regex_heuristics, always)
            set_parsefunc(self.char_range_heuristics, always)
        else:
            raise ValueError('Mode must be one of: ' + ', '.join((
                EBNF_ANY_SYNTAX_HEURISTICAL,
                EBNF_ANY_SYNTAX_STRICT,
                EBNF_PARSING_EXPRESSION_GRAMMAR_SYNTAX,
                EBNF_REGULAR_EXPRESSION_SYNTAX,
                EBNF_CLASSIC_SYNTAX
            )))


def grammar_changed(grammar_class, grammar_source: str) -> bool:
    """
    Returns ``True`` if ``grammar_class`` does not reflect the latest
    changes of ``grammar_source``

    Parameters:
        grammar_class:  the parser class representing the grammar
            or the file name of a compiler suite containing the grammar
        grammar_source:  File name or string representation of the
            EBNF code of the grammar

    Returns (bool):
        True, if the source text of the grammar is different from the
        source from which the grammar class was generated
    """
    grammar = load_if_file(grammar_source)
    chksum = md5(grammar, __version__)
    if isinstance(grammar_class, str):
        # grammar_class = load_compiler_suite(grammar_class)[1]
        with open(grammar_class, 'r', encoding='utf8') as f:
            pycode = f.read()
        m = re.search(r'class \w*\(Grammar\)', pycode)
        if m:
            m = re.search('    source_hash__ *= *"([a-z0-9]*)"',
                          pycode[m.span()[1]:])
            return not (m and m.groups() and m.groups()[-1] == chksum)
        else:
            return True
    else:
        return chksum != grammar_class.source_hash__


def get_ebnf_grammar() -> EBNFGrammar:
    """Returns a thread-local EBNF-Grammar-object for parsing EBNF sources."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.ebnf_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.ebnf_grammar_singleton = EBNFGrammar()
        grammar = THREAD_LOCALS.ebnf_grammar_singleton
    grammar.mode = get_config_value('syntax_variant')
    return grammar


def parse_ebnf(ebnf: str) -> Node:
    """Parses and EBNF-source-text and returns the concrete syntax tree
    of the EBNF-code.."""
    return get_ebnf_grammar()(ebnf)


########################################################################
#
# EBNF concrete to abstract syntax tree transformation and validation
#
########################################################################


EBNF_AST_transformation_table = {
    # AST Transformations for EBNF-grammar
    "<":
        [remove_children_if(all_of(not_one_of('regexp'), is_empty))],
    "syntax":
        [],
    "directive":
        [flatten, remove_tokens('@', '=', ',')],
    "procedure":
        [remove_tokens('()'), reduce_single_child],
    "literals":
        [replace_by_single_child],
    "definition":
        [flatten, remove_children('DEF', 'ENDL'),
         remove_tokens('=')],  # remove_tokens('=') is only for backwards-compatibility
    "expression":
        [replace_by_single_child, flatten, remove_children('OR'),
         remove_tokens('|')],  # remove_tokens('|') is only for backwards-compatibility
    "sequence":
        [replace_by_single_child, flatten, remove_children('AND')],
    "interleave":
        [replace_by_single_child, flatten, remove_tokens('°')],
    "lookaround":
        [],
    "difference":
        [remove_tokens('-'), replace_by_single_child],
    "term, pure_elem, element":
        [replace_by_single_child],
    "flowmarker, retrieveop":
        [reduce_single_child],
    "group":
        [remove_brackets],
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets, # remove_tokens('?', '*', '+'),
         forbid('repetition', 'option', 'oneormore'), assert_content(r'(?!§)(?:.|\n)*')],
    "counted":
        [remove_children('TIMES')],
    "range":
        [remove_children('BRACE_SIGN', 'RNG_BRACE', 'RNG_DELIM')],
    "symbol, literal, any_char":
        [reduce_single_child],
    "plaintext":
        [],
    "regexp":
        [remove_children('RE_LEADIN', 'RE_LEADOUT'), reduce_single_child],
    "char_range":
        [flatten, remove_tokens('[', ']')],
    "character":
        [remove_children('CH_LEADIN'), reduce_single_child],
    "free_char":
        [],
    (TOKEN_PTYPE, WHITESPACE_PTYPE, "whitespace"):
        [reduce_single_child],
    "EOF, DEF, OR, AND, ENDL, BRACE_SIGN, RNG_BRACE, RNG_DELIM, TIMES, "
    "RE_LEADIN, RE_CORE, RE_LEADOUT, CH_LEADIN":
        [],
    "*":
        [replace_by_single_child]
}


def EBNFTransform() -> TransformationFunc:
    return partial(traverse, processing_table=EBNF_AST_transformation_table.copy())


def get_ebnf_transformer() -> TransformationFunc:
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.EBNF_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.EBNF_transformer_singleton = EBNFTransform()
        transformer = THREAD_LOCALS.EBNF_transformer_singleton
    return transformer


def transform_ebnf(cst: Node) -> None:
    """Transforms the concrete-syntax-tree of an EBNF-source-code
    into the abstract-syntax-tree. The transformation changes the
    syntax tree in place. No value is returned."""
    get_ebnf_transformer()(cst)


########################################################################
#
# EBNF abstract syntax tree to Python parser compilation
#
########################################################################


PreprocessorFactoryFunc = Callable[[], PreprocessorFunc]
ParserFactoryFunc = Callable[[], Grammar]
TransformerFactoryFunc = Callable[[], TransformationFunc]
CompilerFactoryFunc = Callable[[], Compiler]

PREPROCESSOR_FACTORY = '''

def get_preprocessor() -> PreprocessorFunc:
    return {NAME}Preprocessor
'''


GRAMMAR_FACTORY = '''

def get_grammar() -> {NAME}Grammar:
    """Returns a thread/process-exclusive {NAME}Grammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton = {NAME}Grammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
'''


TRANSFORMER_FACTORY = '''

def Create{NAME}Transformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table={NAME}_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.{NAME}_{ID:08d}_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.{NAME}_{ID:08d}_transformer_singleton = Create{NAME}Transformer()
        transformer = THREAD_LOCALS.{NAME}_{ID:08d}_transformer_singleton
    return transformer
'''


COMPILER_FACTORY = '''

def get_compiler() -> {NAME}Compiler:
    """Returns a thread/process-exclusive {NAME}Compiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.{NAME}_{ID:08d}_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.{NAME}_{ID:08d}_compiler_singleton = {NAME}Compiler()
        compiler = THREAD_LOCALS.{NAME}_{ID:08d}_compiler_singleton
    return compiler
'''


WHITESPACE_TYPES = {'horizontal': r'[\t ]*',  # default: horizontal
                    'linefeed': r'[ \t]*\n?(?!\s*\n)[ \t]*',
                    'vertical': r'\s*'}

DROP_STRINGS  = 'strings'
DROP_WSPC   = 'whitespace'
DROP_REGEXP = 'regexps'
DROP_VALUES = {DROP_STRINGS, DROP_WSPC, DROP_REGEXP}

# Representation of Python code or, rather, something that will be output as Python code
ReprType = Union[str, unrepr]


KNOWN_DIRECTIVES = {
    'comment': r'Regular expression for comments, e.g. /#.*(?:\n|$)/',
    'whitespace': r'Regular expression for whitespace, e.g. /\s*/',
    'literalws': 'Controls implicit whitespace adjacent to literals: left, right, both, none',
    'ignorecase': 'Controls case-sensitivity: on, off',
    '[preprocessor_]tokens': 'List of the names of all preprocessor tokens',
    'anonymous': 'List of symbols that are NOT to appear as tag-names',
    'drop': 'List of tags to be dropped early from syntax tree, '
            'special values: strings, whitespace, regexps',
    '$SYMBOL_filer': 'Function that transforms captured values of the givensymbol on retrieval',
    '$SYMBOL_error': 'Pair of regular epxression an custom error message if regex matches',
    '$SYMBOL_skip': 'List of regexes or functions to find reentry point after an error',
    '$SYMBOL_resume': 'List or regexes or functions to find reentry point for parent parser'
}

class EBNFDirectives:
    """
    A Record that keeps information about compiler directives
    during the compilation process.

    Attributes:
        whitespace:  the regular expression string for (insignificant)
                whitespace

        comment:  the regular expression string for comments

        literalws:  automatic whitespace eating next to literals. Can
                be either 'left', 'right', 'none', 'both'

        tokens:  set of the names of preprocessor tokens

        filter:  mapping of symbols to python match functions that
                will be called on any retrieve / pop - operations on
                these symbols

        error:  mapping of symbols to tuples of match conditions and
                customized error messages. A match condition can be
                either a string or a regular expression. The first
                error message where the search condition matches will
                be displayed. An empty string '' as search condition
                always matches, so in case of multiple error messages,
                this condition should be placed at the end.

        skip:  mapping of symbols to a list of search expressions. A
                search expressions can be either a string ot a regular
                expression. The closest match is the point of reentry
                for the series- or interleave-parser when a mandatory item
                failed to match the following text.

        resume:  mapping of symbols to a list of search expressions. A
                search expressions can be either a string ot a regular
                expression. The closest match is the point of reentry
                for after a parsing error has error occurred. Other
                than the skip field, this configures resuming after
                the failing parser (`parser.Series` or `parser.Interleave`)
                has returned.

        drop:   A set that may contain the elements `DROP_STRINGS` and
                `DROP_WSP', 'DROP_REGEXP' or any name of a symbol
                of an anonymous parser (e.g. '_linefeed') the results
                of which will be dropped during the parsing process,
                already.

        super_ws(property): Cache for the "super whitespace" which
                is a regular expression that merges whitespace and
                comments. This property should only be accessed after
                the `whitespace` and `comment` field have been filled
                with the values parsed from the EBNF source.
    """
    __slots__ = ['whitespace', 'comment', 'literalws', 'tokens', 'filter', 'error', 'skip',
                 'resume', 'drop', '_super_ws']

    def __init__(self):
        self.whitespace = WHITESPACE_TYPES['vertical']  # type: str
        self.comment = ''      # type: str
        self.literalws = {get_config_value('default_literalws')}  # type: Set[str]
        self.tokens = set()    # type: Set[str]
        self.filter = dict()   # type: Dict[str, str]
        self.error = dict()    # type: Dict[str, List[Tuple[ReprType, ReprType]]]
        self.skip = dict()     # type: Dict[str, List[Union[unrepr, str]]]
        self.resume = dict()   # type: Dict[str, List[Union[unrepr, str]]]
        self.drop = set()      # type: Set[str]
        self._super_ws = None  # type: Optional[str]

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        assert hasattr(self, key)
        setattr(self, key, value)

    @property
    def super_ws(self):
        if self._super_ws is None:
            self._super_ws = mixin_comment(self.whitespace, self.comment)
        return self._super_ws

    def keys(self):
        return self.__slots__


class EBNFCompilerError(CompilerError):
    """Error raised by `EBNFCompiler` class. (Not compilation errors
    in the strict sense, see `CompilationError` in module ``dsl.py``)"""
    pass


# def escape_backslash(s: str) -> str:
#     """Replaces backslashes by double backslash and newline by r'\n'."""
#     return s.replace('\\', r'\\').replace('\n', r'\n')


class EBNFCompiler(Compiler):
    """
    Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.

    Instances of this class must be called with the root-node of the
    abstract syntax tree from an EBNF-specification of a formal language.
    The returned value is the Python-source-code of a Grammar class for
    this language that can be used to parse texts in this language.
    See classes `parser.Compiler` and `parser.Grammar` for more information.

    Additionally, class EBNFCompiler provides helper methods to generate
    code-skeletons for a preprocessor, AST-transformation and full
    compilation of the formal language. These method's names start with
    the prefix `gen_`.

    Attributes:
        current_symbols:  During compilation, a list containing the root
                node of the currently compiled definition as first element
                and then the nodes of the symbols that are referred to in
                the currently compiled definition.

        cache_literal_symbols: A cache for all symbols that are defined
                by literals, e.g. head = "<head>". This is used by the
                on_expression()-method.

        rules:  Dictionary that maps rule names to a list of Nodes that
                contain symbol-references in the definition of the rule.
                The first item in the list is the node of the rule-
                definition itself. Example:

                           `alternative = a | b`

                Now `[node.content for node in self.rules['alternative']]`
                yields `['alternative = a | b', 'a', 'b']`

        symbols:  A mapping of symbol names to their first usage (not
                their definition!) in the EBNF source.

        variables:  A set of symbols names that are used with the
                Pop or Retrieve operator. Because the values of these
                symbols need to be captured they are called variables.
                See `test_parser.TestPopRetrieve` for an example.

        recursive:  A set of symbols that are used recursively and
                therefore require a `Forward`-operator.

        definitions:  A dictionary of definitions. Other than `rules`
                this maps the symbols to their compiled definienda.

        required_keywords: A list of keywords (like `comment__` or
                `whitespace__` that need to be defined at the beginning
                of the grammar class because they are referred to later.

        deferred_tasks:  A list of callables that is filled during
                compilatation, but that will be executed only after
                compilation has finished. Typically, it contains
                sementatic checks that require information that
                is only available upon completion of compilation.

        root_symbol: The name of the root symbol.

        drop_flag: This flag is set temporarily when compiling the definition
                of a parser that shall drop its content. If this flag is
                set all contained parser will also drop their content as an
                optimization.

        directives:  A record of all directives and their default values.

        defined_directives:  A dictionary of all directives that have already
                been defined, mapped onto the list of nodes where they have
                been (re-)defined. With the exception of those directives
                contained in EBNFCompiler.REPEATABLE_DIRECTIVES, directives
                must only be defined once.

        consumed_custom_errors:  A set of symbols for which a custom error
                has been defined and(!) consumed during compilation. This
                allows to add a compiler error in those cases where (i) an
                error message has been defined but will never used or (ii)
                an error message is accidently used twice. For examples, see
                `test_ebnf.TestErrorCustomization`.

        consumed_skip_rules: The same as `consumed_custom_errors` only for
                in-series-resume-rules (aka 'skip-rules') for Series-parsers.

        re_flags:  A set of regular expression flags to be added to all
                regular expressions found in the current parsing process

        anonymous_regexp: A regular expression to identify symbols that stand
                for parsers that shall yield anonymous nodes. The pattern of
                the regular expression is configured in configuration.py but
                can also be set by a directive. The default value is a regular
                expression that catches names with a leading underscore.
                See also `parser.Grammar.anonymous__`

        grammar_name:  The name of the grammar to be compiled

        grammar_source:  The source code of the grammar to be compiled.

        grammar_id: a unique id for every compiled grammar. (Required for
                disambiguation of of thread local variables storing
                compiled texts.)
    """
    COMMENT_KEYWORD = "COMMENT__"
    COMMENT_PARSER_KEYWORD = "comment__"
    DROP_COMMENT_PARSER_KEYWORD = "dcomment__"
    COMMENT_RX_KEYWORD = "comment_rx__"
    WHITESPACE_KEYWORD = "WSP_RE__"
    RAW_WS_KEYWORD = "WHITESPACE__"
    RAW_WS_PARSER_KEYWORD = "whitespace__"
    DROP_RAW_WS_PARSER_KEYWORD = "dwhitespace__"
    WHITESPACE_PARSER_KEYWORD = "wsp__"
    DROP_WHITESPACE_PARSER_KEYWORD = "dwsp__"
    RESUME_RULES_KEYWORD = "resume_rules__"
    SKIP_RULES_KEYWORD = 'skip_rules__'
    ERR_MSGS_KEYWORD = 'error_messages__'
    COMMENT_OR_WHITESPACE = {COMMENT_PARSER_KEYWORD, DROP_COMMENT_PARSER_KEYWORD,
                             RAW_WS_PARSER_KEYWORD, DROP_RAW_WS_PARSER_KEYWORD,
                             WHITESPACE_PARSER_KEYWORD, DROP_WHITESPACE_PARSER_KEYWORD}
    RESERVED_SYMBOLS = {COMMENT_KEYWORD, COMMENT_RX_KEYWORD, COMMENT_PARSER_KEYWORD,
                        WHITESPACE_KEYWORD, RAW_WS_KEYWORD, RAW_WS_PARSER_KEYWORD,
                        WHITESPACE_PARSER_KEYWORD, DROP_WHITESPACE_PARSER_KEYWORD,
                        RESUME_RULES_KEYWORD}
    KEYWORD_SUBSTITUTION = {COMMENT_KEYWORD: COMMENT_PARSER_KEYWORD,
                            COMMENT_PARSER_KEYWORD: COMMENT_PARSER_KEYWORD,
                            RAW_WS_KEYWORD: RAW_WS_PARSER_KEYWORD,
                            RAW_WS_PARSER_KEYWORD: RAW_WS_PARSER_KEYWORD,
                            WHITESPACE_KEYWORD: WHITESPACE_PARSER_KEYWORD,
                            WHITESPACE_PARSER_KEYWORD: WHITESPACE_PARSER_KEYWORD,
                            DROP_WHITESPACE_PARSER_KEYWORD: DROP_WHITESPACE_PARSER_KEYWORD}
    AST_ERROR = "Badly structured syntax tree. " \
                "Potentially due to erroneous AST transformation."
    PREFIX_TABLE = {'§': 'Required',
                    '&': 'Lookahead', '!': 'NegativeLookahead',
                    '<-&': 'Lookbehind', '<-!': 'NegativeLookbehind',
                    '::': 'Pop', ':?': 'Pop', ':': 'Retrieve'}
    REPEATABLE_DIRECTIVES = {'tokens'}


    def __init__(self, grammar_name="DSL", grammar_source=""):
        self.grammar_id = 0  # type: int
        super(EBNFCompiler, self).__init__()  # calls the reset()-method
        self.set_grammar_name(grammar_name, grammar_source)


    def reset(self):
        super(EBNFCompiler, self).reset()
        self._result = ''                    # type: str
        self.re_flags = set()                # type: Set[str]
        self.rules = OrderedDict()           # type: OrderedDict[str, List[Node]]
        self.current_symbols = []            # type: List[Node]
        self.cache_literal_symbols = None    # type: Optional[Dict[str, str]]
        self.symbols = {}                    # type: Dict[str, Node]
        self.variables = set()               # type: Set[str]
        self.recursive = set()               # type: Set[str]
        self.definitions = {}                # type: Dict[str, str]
        self.required_keywords = set()       # type: Set[str]
        self.deferred_tasks = []             # type: List[Callable]
        self.root_symbol = ""                # type: str
        self.drop_flag = False               # type: bool
        self.directives = EBNFDirectives()   # type: EBNFDirectives
        self.defined_directives = dict()     # type: Dict[str, List[Node]]
        self.consumed_custom_errors = set()  # type: Set[str]
        self.consumed_skip_rules = set()     # type: Set[str]
        self.anonymous_regexp = re.compile(get_config_value('default_anonymous_regexp'))
        self.grammar_id += 1


    @property
    def result(self) -> str:
        return self._result


    def set_grammar_name(self, grammar_name: str = "", grammar_source: str = ""):
        """
        Changes the grammar name and source.

        The grammar name and the source text are metadata that do not affect the
        compilation process. It is used to name and annotate the output.
        Returns `self`.
        """
        assert grammar_name == "" or re.match(r'\w+\Z', grammar_name)
        if not grammar_name and re.fullmatch(r'[\w/:\\]+', grammar_source):
            grammar_name = os.path.splitext(os.path.basename(grammar_source))[0]
        self.grammar_name = grammar_name or "NameUnknown"
        self.grammar_source = load_if_file(grammar_source)
        return self

    # methods for generating skeleton code for preprocessor, transformer, and compiler

    def gen_preprocessor_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for a preprocessor-function for
        the previously compiled formal language.
        """
        name = self.grammar_name + "Preprocessor"
        return "def %s(text):\n    return text, lambda i: i\n" % name \
               + PREPROCESSOR_FACTORY.format(NAME=self.grammar_name)


    def gen_transformer_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for the AST-transformation for the
        previously compiled formal language.
        """
        if not self.rules:
            raise EBNFCompilerError('Compiler must be run before calling '
                                    '"gen_transformer_Skeleton()"!')
        tt_name = self.grammar_name + '_AST_transformation_table'
        transtable = [tt_name + ' = {',
                      '    # AST Transformations for the ' + self.grammar_name + '-grammar',
                      '    "<": flatten,']
        for name in self.rules:
            transformations = '[]'
            transtable.append('    "' + name + '": %s,' % transformations)
        transtable += ['    "*": replace_by_single_child', '}', '']
        transtable += [TRANSFORMER_FACTORY.format(NAME=self.grammar_name, ID=self.grammar_id)]
        return '\n'.join(transtable)


    def gen_compiler_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for a Compiler-class for the
        previously compiled formal language.
        """
        if not self.rules:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_Compiler_Skeleton()"!')
        compiler = ['class ' + self.grammar_name + 'Compiler(Compiler):',
                    '    """Compiler for the abstract-syntax-tree of a ' +
                    self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self):',
                    '        super(' + self.grammar_name + 'Compiler, self).__init__()',
                    '',
                    '    def reset(self):',
                    '        super().reset()',
                    '        # initialize your variables here, not in the constructor!',
                    '']
        for name in self.rules:
            method_name = visitor_name(name)
            if name == self.root_symbol:
                compiler += ['    def ' + method_name + '(self, node):',
                             '        return self.fallback_compiler(node)', '']
            else:
                compiler += ['    # def ' + method_name + '(self, node):',
                             '    #     return node', '']
        compiler += [COMPILER_FACTORY.format(NAME=self.grammar_name, ID=self.grammar_id)]
        return '\n'.join(compiler)

    def verify_transformation_table(self, transtable):
        """
        Checks for symbols that occur in the transformation-table but have
        never been defined in the grammar. Usually, this kind of
        inconsistency results from an error like a typo in the transformation
        table.
        """
        assert self._dirty_flag
        table_entries = set(expand_table(transtable).keys()) - {'*', '<', '>', '~'}
        symbols = self.rules.keys()
        messages = []
        for entry in table_entries:
            if entry not in symbols and not entry.startswith(":"):
                messages.append(Error(('Symbol "%s" is not defined in grammar %s but appears in '
                                       'the transformation table!') % (entry, self.grammar_name),
                                      0, UNDEFINED_SYMBOL_IN_TRANSTABLE_WARNING))
        return messages

    def verify_compiler(self, compiler):
        """
        Checks for on_XXXX()-methods that occur in the compiler, although XXXX
        has never been defined in the grammar. Usually, this kind of
        inconsistency results from an error like a typo in the compiler-code.
        """
        pass  # TODO: add verification code here


    def check_rx(self, node: Node, rx: str) -> str:
        """
        Checks whether the string `rx` represents a valid regular
        expression. Makes sure that multi-line regular expressions are
        prepended by the multi-line-flag. Returns the regular expression string.
        """
        # TODO: Support atomic grouping: https://stackoverflow.com/questions/13577372/
        #       do-python-regular-expressions-have-an-equivalent-to-rubys-atomic-grouping
        flags = self.re_flags | {'x'} if rx.find('\n') >= 0 else self.re_flags
        if flags:
            rx = "(?%s)%s" % ("".join(flags), rx)
        try:
            re.compile(rx)
        except Exception as re_error:
            self.tree.new_error(node, "malformed regular expression %s: %s" %
                                (repr(rx), str(re_error)))
        return rx


    def extract_regex(self, node: Node) -> str:
        """Extracts regular expression string from regexp-Node."""
        value = node.content
        if node.tag_name in ('literal', 'plaintext'):
            assert value
            assert value[0] + value[-1] in ('""', "''", "``")
            value = escape_re(value[1:-1])
        else:
            assert node.tag_name == "regexp"""
        value = self.check_rx(node, value)
        return value


    def gen_search_rule(self, nd: Node) -> ReprType:
        """Generates a search rule, which can be either a string for simple
        string search or a regular expression from the nodes content. Returns
        an empty string in case the node is neither regexp nor literal.
        """
        if nd.tag_name == 'regexp':
            super_ws = self.directives.super_ws
            nonempty_ws = mixin_nonempty(super_ws)
            search_regex = self.extract_regex(nd)\
                .replace(r'\~!', nonempty_ws).replace(r'\~', super_ws)
            return unrepr("re.compile(r'%s')" % search_regex)
        elif nd.tag_name == 'literal':
            s = nd.content[1:-1]  # remove quotation marks
            return unrepr("re.compile(r'(?=%s)')" % escape_re(s))
        elif nd.tag_name == 'procedure':
            return unrepr(nd.content)
        elif nd.tag_name != 'symbol':
            self.tree.new_error(nd, 'Only regular expressions, string literals and external '
                                'procedures are allowed as search rules, but not: ' + nd.tag_name)
        return ''


    def gen_search_list(self, nodes: Sequence[Node]) -> List[Union[unrepr, str]]:
        search_list = []  # type: List[Union[unrepr, str]]
        for child in nodes:
            rule = self.gen_search_rule(child)
            search_list.append(rule if rule else unrepr(child.content.strip()))
        return search_list

    def referred_symbols(self, symbol: str) -> Set[str]:
        """Returns the set of all symbols that are directly or indirectly
        referred to in the definition of `symbol`."""
        collected = set()  # type: Set[str]

        def gather(sym: str):
            referred = self.rules[sym]
            for nd in referred[1:]:
                s = nd.content
                if s not in collected and s not in EBNFCompiler.RESERVED_SYMBOLS:
                    collected.add(s)
                    gather(s)
        gather(symbol)
        return collected

    def assemble_parser(self, definitions: List[Tuple[str, str]]) -> str:
        """
        Creates the Python code for the parser after compilation of
        the EBNF-Grammar
        """

        def pp_rules(rule_name: str, ruleset: Dict[str, List]) -> Tuple[str, str]:
            """Pretty-print skip- and resume-rule and error-messages dictionaries
            to avoid excessively long lines in the generated python source."""
            assert ruleset
            indent = ",\n" + " " * (len(rule_name) + 8)
            rule_repr = []
            for k, v in ruleset.items():
                if len(v) > 1:
                    delimiter = indent + ' ' * (len(k) + 5)
                    val = '[' + delimiter.join(str(it) for it in v) + ']'
                else:
                    val = v
                rule_repr.append("'{key}': {value}".format(key=k, value=str(val)))
            rule_repr[0] = '{' + rule_repr[0]
            rule_repr[-1] = rule_repr[-1] + '}'
            return rule_name, indent.join(rule_repr)

        def verify_directive_against_symbol(directive: str, related_symbol: str):
            """Adds an error if the symbol that the directive relates to
            does not exist."""
            if related_symbol not in self.rules:
                nd = self.defined_directives[directive][0]
                self.tree.new_error(nd, 'Directive "%s" relates to a symbol that is '
                                    'nowhere defined!' % directive,
                                    DIRECTIVE_FOR_NONEXISTANT_SYMBOL)

        # execute deferred tasks, for example semantic checks that cannot
        # be done before the symbol table is complete

        for task in self.deferred_tasks:
            task()

        # provide for capturing of symbols that are variables, i.e. the
        # value of which will be retrieved at some point during the parsing process

        # The following is needed for cases, where the first retrival-use of a symbol
        # follows its definition

        if self.variables:
            for i in range(len(definitions)):
                if definitions[i][0] in self.variables:
                    definitions[i] = (definitions[i][0], 'Capture(%s)' % definitions[i][1])

        # add special fields for Grammar class

        if DROP_WSPC in self.directives.drop or DROP_STRINGS in self.directives.drop:
            definitions.append((EBNFCompiler.DROP_WHITESPACE_PARSER_KEYWORD,
                                'Drop(Whitespace(%s))' % EBNFCompiler.WHITESPACE_KEYWORD))
        definitions.append((EBNFCompiler.WHITESPACE_PARSER_KEYWORD,
                            'Whitespace(%s)' % EBNFCompiler.WHITESPACE_KEYWORD))
        definitions.append((EBNFCompiler.WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace=" + EBNFCompiler.RAW_WS_KEYWORD
                             + ", comment=" + EBNFCompiler.COMMENT_KEYWORD + ")")))
        if EBNFCompiler.RAW_WS_PARSER_KEYWORD in self.required_keywords:
            definitions.append((EBNFCompiler.RAW_WS_PARSER_KEYWORD,
                                "Whitespace(%s)" % EBNFCompiler.RAW_WS_KEYWORD))
        definitions.append((EBNFCompiler.RAW_WS_KEYWORD,
                            "r'{}'".format(self.directives.whitespace)))
        comment_rx = ("re.compile(%s)" % EBNFCompiler.COMMENT_KEYWORD) \
            if self.directives.comment else "RX_NEVER_MATCH"
        if EBNFCompiler.COMMENT_PARSER_KEYWORD in self.required_keywords:
            definitions.append((EBNFCompiler.COMMENT_PARSER_KEYWORD,
                                "RegExp(%s)" % EBNFCompiler.COMMENT_RX_KEYWORD))
        definitions.append((EBNFCompiler.COMMENT_RX_KEYWORD, comment_rx))
        definitions.append((EBNFCompiler.COMMENT_KEYWORD,
                            "r'{}'".format(self.directives.comment)))

        # prepare and add resume-rules

        resume_rules = dict()  # type: Dict[str, List[ReprType]]
        for symbol, raw_rules in self.directives.resume.items():
            refined_rules = []  # type: List[ReprType]
            verify_directive_against_symbol(symbol + '_resume', symbol)
            for rule in raw_rules:
                if isinstance(rule, unrepr) and rule.s.isidentifier():
                    try:
                        nd = self.rules[rule.s][0].children[1]
                        refined = self.gen_search_rule(nd)
                    except IndexError:
                        nd = self.tree
                        refined = ""
                    except KeyError:
                        # rule represents a procedure name
                        refined = rule
                    if refined:
                        refined_rules.append(refined)
                    else:
                        self.tree.new_error(
                            nd, 'Symbol "%s" cannot be used in resume rule, since it represents '
                            'neither literal nor regexp nor procedure!',
                            INAPPROPRIATE_SYMBOL_FOR_DIRECTIVE)
                else:
                    refined_rules.append(rule)
            resume_rules[symbol] = refined_rules
        if resume_rules:
            definitions.append(pp_rules(self.RESUME_RULES_KEYWORD, resume_rules))

        # prepare and add skip-rules

        skip_rules = dict()  # # type: Dict[str, List[ReprType]]
        for symbol, skip in self.directives.skip.items():
            rules = []  # type: List[ReprType]
            verify_directive_against_symbol(symbol + '_skip', symbol)
            for search in skip:
                if isinstance(search, unrepr) and search.s.isidentifier():
                    try:
                        nd = self.rules[search.s][0].children[1]
                        search = self.gen_search_rule(nd)
                    except IndexError:
                        search = ''
                    except KeyError:
                        # rule represents a procedure name
                        pass
                rules.append(search)
            skip_rules[symbol] = rules
        if skip_rules:
            definitions.append(pp_rules(self.SKIP_RULES_KEYWORD, skip_rules))

        for symbol in self.directives.skip.keys():
            if symbol not in self.consumed_skip_rules:
                # check for indirectly reachable unconsumed mandatory markers
                for s in self.referred_symbols(symbol):
                    if s not in self.directives.skip and s not in self.directives.resume:
                        if self.definitions[s].find('mandatory=') >= 0:
                            self.consumed_skip_rules.add(symbol)
                            break
                else:
                    try:
                        def_node = self.rules[symbol][0]
                        self.tree.new_error(
                            def_node, '"Skip-rules" for symbol "{}" will never be used, beacuse '
                            'the mandatory marker "§" does not appear in its definiendum or has '
                            'already been consumed earlier.'
                            .format(symbol), UNUSED_ERROR_HANDLING_WARNING)
                    except KeyError:
                        pass  # error has already been notified earlier!

        # prepare and add customized error-messages

        error_messages = dict()  # type: Dict[str, List[Tuple[ReprType, ReprType]]]
        for symbol, err_msgs in self.directives.error.items():
            custom_errors = []  # type: List[Tuple[ReprType, ReprType]]
            verify_directive_against_symbol(symbol + '_error', symbol)
            for search, message in err_msgs:
                if isinstance(search, unrepr) and search.s.isidentifier():
                    try:
                        nd = self.rules[search.s][0].children[1]
                        search = self.gen_search_rule(nd)
                    except IndexError:
                        search = ''
                    except KeyError:
                        pass
                custom_errors.append((search, message))
            error_messages[symbol] = custom_errors
        if error_messages:
            definitions.append(pp_rules(self.ERR_MSGS_KEYWORD, error_messages))

        for symbol in self.directives.error.keys():
            if symbol in self.rules and symbol not in self.consumed_custom_errors:
                # try:
                def_node = self.rules[symbol][0]
                self.tree.new_error(
                    def_node, 'Customized error message for symbol "{}" will never be used, '
                    'because the mandatory marker "§" appears nowhere in its definiendum!'
                    .format(symbol), UNUSED_ERROR_HANDLING_WARNING)

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class

        article = 'an ' if self.grammar_name[0:1] in "AaEeIiOoUu" else 'a '
        # what about 'hour', 'universe' etc.?
        show_source = get_config_value('add_grammar_source_to_parser_docstring')
        declarations = ['class ' + self.grammar_name
                        + 'Grammar(Grammar):',
                        'r"""Parser for ' + article + self.grammar_name
                        + ' source file'
                        + ('. Grammar:' if self.grammar_source and show_source else '.')]
        definitions.append(('parser_initialization__', '["upon instantiation"]'))
        definitions.append(('static_analysis_pending__', '[True]'))
        definitions.append(('anonymous__',
                            're.compile(' + repr(self.anonymous_regexp.pattern) + ')'))
        if self.grammar_source:
            definitions.append(('source_hash__',
                                '"%s"' % md5(self.grammar_source, __version__)))
            declarations.append('')
            if show_source:
                declarations += [line for line in self.grammar_source.split('\n')]
            while declarations[-1].strip() == '':
                declarations = declarations[:-1]
        declarations.append('"""')

        # turn definitions into declarations in reverse order

        self.root_symbol = definitions[0][0] if definitions else ""
        definitions.reverse()
        declarations += [symbol + ' = Forward()'
                         for symbol in sorted(list(self.recursive))]
        for symbol, statement in definitions:
            if symbol in self.recursive:
                declarations += [symbol + '.set(' + statement + ')']
            else:
                declarations += [symbol + ' = ' + statement]

        # check for symbols used but never defined

        defined_symbols = set(self.rules.keys()) | self.RESERVED_SYMBOLS
        for symbol in self.symbols:
            if symbol not in defined_symbols:
                self.tree.new_error(self.symbols[symbol],
                                    "Missing definition for symbol '%s'" % symbol)

        # check for unconnected rules

        defined_symbols.difference_update(self.RESERVED_SYMBOLS)

        def remove_connections(symbol):
            """Recursively removes all symbols which appear in the
            definiens of a particular symbol."""
            if symbol in defined_symbols:
                defined_symbols.remove(symbol)
                for related in self.rules[symbol][1:]:
                    remove_connections(str(related))

        remove_connections(self.root_symbol)
        for leftover in defined_symbols:
            self.tree.new_error(self.rules[leftover][0],
                                'Rule "%s" is not connected to parser root "%s" !' %
                                (leftover, self.root_symbol), WARNING)

        # set root_symbol parser and assemble python grammar definition

        if self.root_symbol and 'root__' not in self.rules:
            declarations.append('root__ = ' + self.root_symbol)
        declarations.append('')
        self._result = '\n    '.join(declarations) \
                       + GRAMMAR_FACTORY.format(NAME=self.grammar_name, ID=self.grammar_id)
        return self._result


    # compilation methods ###


    def on_ZOMBIE__(self, node: Node) -> str:
        result = ['Errors in EBNF-source! Fragments found: ']
        result.extend([str(self.compile(child)) for child in node.children])
        return '\n'.join(result)


    def on_syntax(self, node: Node) -> str:
        definitions = []  # type: List[Tuple[str, str]]

        # drop the wrapping sequence node
        if len(node.children) == 1 and node.children[0].anonymous:
            node = node.children[0]

        # compile definitions and directives and collect definitions
        for nd in node.children:
            if nd.tag_name == "definition":
                definitions.append(self.compile(nd))
            else:
                assert nd.tag_name == "directive", nd.as_sxpr()
                self.compile(nd)
        self.definitions.update(definitions)

        grammar_python_src = self.assemble_parser(definitions)
        if get_config_value('static_analysis') == 'early':
            errors = []
            try:
                grammar_class = compile_python_object(
                    DHPARSER_IMPORTS.format(dhparser_parentdir=DHPARSER_PARENTDIR) +
                    grammar_python_src, (self.grammar_name or "DSL") + "Grammar")
                errors = grammar_class().static_analysis_errors__
                grammar_python_src = grammar_python_src.replace(
                    'static_analysis_pending__ = [True]',
                    'static_analysis_pending__ = []  # type: List[bool]', 1)
            except NameError:
                pass  # undefined names in the grammar are already caught and reported
            except GrammarError as ge:
                errors = ge.errors
            for sym, _, err in errors:
                symdef_node = self.rules[sym][0]
                err.pos = self.rules[sym][0].pos
                self.tree.add_error(symdef_node, err)
        return grammar_python_src


    def on_definition(self, node: Node) -> Tuple[str, str]:
        rule = node.children[0].content
        if rule.endswith('_error') or rule.endswith('_skip') \
                or rule.endswith('_resume') or rule.endswith('_filter'):
            self.tree.new_error(node, 'Symbol name "%s" suggests directive, ' % rule +
                                'but directive marker @ is missing...', WARNING)
        if rule in self.rules:
            first = self.rules[rule][0]
            if not id(first) in self.tree.error_nodes:
                self.tree.new_error(first, 'First definition of rule "%s" '
                                    'followed by illegal redefinitions.' % rule)
            self.tree.new_error(node, 'A rule "%s" has already been defined earlier.' % rule)
        elif rule in EBNFCompiler.RESERVED_SYMBOLS:
            self.tree.new_error(node, 'Symbol "%s" is a reserved symbol.' % rule)
        elif not sane_parser_name(rule):
            self.tree.new_error(node, 'Illegal symbol "%s". Symbols must not start or '
                                ' end with a doube underscore "__".' % rule)
        elif rule in self.directives.tokens:
            self.tree.new_error(node, 'Symbol "%s" has already been defined as '
                                'a preprocessor token.' % rule)
        elif keyword.iskeyword(rule):
            self.tree.new_error(node, 'Python keyword "%s" may not be used as a symbol. '
                                % rule + '(This may change in the future.)')
        try:
            self.current_symbols = [node]
            self.rules[rule] = self.current_symbols
            self.drop_flag = rule in self.directives['drop'] and rule not in DROP_VALUES
            defn = self.compile(node.children[1])
            if defn.find("(") < 0:
                # assume it's a synonym, like 'page = REGEX_PAGE_NR'
                defn = 'Synonym(%s)' % defn
            if self.drop_flag:
                defn = 'Drop(%s)' % defn
            # TODO: Recursively drop all contained parsers for optimization
        except TypeError as error:
            from traceback import extract_tb, format_list
            trace = ''.join(format_list((extract_tb(error.__traceback__))))
            errmsg = "%s (TypeError: %s;\n%s)\n%s" \
                     % (EBNFCompiler.AST_ERROR, str(error), trace, node.as_sxpr())
            self.tree.new_error(node, errmsg)
            rule, defn = rule + ':error', '"' + errmsg + '"'
        finally:
            self.drop_flag = False
        return rule, defn

    @staticmethod
    def join_literals(nd):
        assert nd.tag_name == "literals"
        parts = [nd.children[0].content[:-1]]
        for child in nd.children[1:-1]:
            parts.append(child.content[1:-1])
        parts.append(nd.children[-1].content[1:])
        nd.result = "".join(parts)
        nd.tag_name = "literal"


    def on_directive(self, node: Node) -> str:
        for child in node.children:
            if child.tag_name == "literal":
                child.result = escape_control_characters(child.content)
            elif child.tag_name == "literals":
                self.join_literals(child)
                child.result = escape_control_characters(child.content)

        key = node.children[0].content
        assert key not in self.directives.tokens

        if key not in self.REPEATABLE_DIRECTIVES and not key.endswith('_error') \
                and key in self.defined_directives:
            self.tree.new_error(node, 'Directive "%s" has already been defined earlier. '
                                % key + 'Later definition will be ignored!',
                                code=REDEFINED_DIRECTIVE)
            return ""
        self.defined_directives.setdefault(key, []).append(node)

        def check_argnum(n: int = 1):
            if len(node.children) > n + 1:
                self.tree.new_error(node, 'Directive "%s" can have at most %i values.' % (key, n))

        if key in {'comment', 'whitespace'}:
            check_argnum()
            if node.children[1].tag_name == "symbol":
                value = node.children[1].content
                if key == 'whitespace' and value in WHITESPACE_TYPES:
                    value = WHITESPACE_TYPES[value]  # replace whitespace-name by regex
                else:
                    self.tree.new_error(node, 'Value "%s" not allowed for directive "%s".'
                                        % (value, key))
            else:
                value = self.extract_regex(node.children[1])
                if key == 'whitespace' and not re.match(value, ''):
                    self.tree.new_error(node, "Implicit whitespace should always "
                                        "match the empty string, /%s/ does not." % value)
            self.directives[key] = value

        elif key == 'anonymous':
            if node.children[1].tag_name == "regexp":
                check_argnum()
                re_pattern = node.children[1].content
                if re.match(re_pattern, ''):
                    self.tree.new_error(
                        node, "The regular expression r'%s' matches any symbol, "
                        "which is not allowed!" % re_pattern)
                else:
                    self.anonymous_regexp = re.compile(re_pattern)
            else:
                args = node.children[1:]
                assert all(child.tag_name == "symbol" for child in args)
                alist = [child.content for child in args]
                for asym in alist:
                    if asym not in self.symbols:
                        self.symbols[asym] = node
                self.anonymous_regexp = re.compile('$|'.join(alist) + '$')

        elif key == 'drop':
            if len(node.children) <= 1:
                self.tree.new_error(node, 'Directive "@ drop" requires as least one argument!')
            for child in node.children[1:]:
                content = child.content
                if self.anonymous_regexp.match(content):
                    self.directives[key].add(content)
                elif content.lower() in DROP_VALUES:
                    self.directives[key].add(content.lower())
                else:
                    if self.anonymous_regexp == RX_NEVER_MATCH:
                        self.tree.new_error(node, 'Illegal value "%s" for Directive "@ drop"! '
                                            'Should be one of %s or an anonymous parser, where '
                                            'the "@anonymous"-directive must preceed the '
                                            '@drop-directive.' % (content, str(DROP_VALUES)))
                    else:
                        self.tree.new_error(
                            node, 'Illegal value "%s" for Directive "@ drop"! Should be one of '
                            '%s or a string matching r"%s".' % (content, str(DROP_VALUES),
                                                                self.anonymous_regexp.pattern))

        elif key == 'ignorecase':
            check_argnum()
            if node.children[1].content.lower() not in {"off", "false", "no"}:
                self.re_flags.add('i')

        elif key == 'literalws':
            values = {child.content.strip().lower() for child in node.children[1:]}
            if ((values - {'left', 'right', 'both', 'none'})
                    or ('none' in values and len(values) > 1)):
                self.tree.new_error(node, 'Directive "literalws" allows only `left`, `right`, '
                                    '`both` or `none`, not `%s`' % ", ".join(values))
            wsp = {'left', 'right'} if 'both' in values \
                else set() if 'none' in values else values
            self.directives.literalws = wsp

        elif key in {'tokens', 'preprocessor_tokens'}:
            tokens = {child.content.strip() for child in node.children[1:]}
            redeclared = self.directives.tokens & tokens
            if redeclared:
                self.tree.new_error(node, 'Tokens %s have already been declared earlier. '
                                    % str(redeclared) + 'Later declaration will be ignored',
                                    code=REDECLARED_TOKEN_WARNING)
            self.directives.tokens |= tokens - redeclared

        elif key.endswith('_filter'):
            check_argnum()
            symbol = key[:-7]
            if node.children[1].tag_name != "procedure":
                self.tree.new_error(
                    node, 'Filter must be a procedure, denoted as "foo()", not not a %s: %s'
                    % (node.children[1].tag_name, node.children[1].content))
            self.directives.filter[symbol] = node.children[1].content.strip()

        elif key.endswith('_error'):
            check_argnum(2)
            symbol = key[:-6]
            error_msgs = self.directives.error.get(symbol, [])
            if symbol in self.rules:
                self.tree.new_error(node, 'Custom error message for symbol "%s"' % symbol
                                    + ' must be defined before the symbol!')
            if node.children[1 if len(node.children) == 2 else 2].tag_name != 'literal':
                self.tree.new_error(
                    node, 'Directive "%s" requires message string or a a pair ' % key
                    + '(regular expression or search string, message string) as argument!')
            if len(node.children) == 2:
                error_msgs.append(('', unrepr(node.children[1].content)))
            elif len(node.children) == 3:
                rule = self.gen_search_rule(node.children[1])
                error_msgs.append((rule if rule else unrepr(node.children[1].content),
                                   unrepr(node.children[2].content)))
            else:
                self.tree.new_error(node, 'Directive "%s" allows at most two parameters' % key)
            self.directives.error[symbol] = error_msgs

        elif key.endswith('_skip'):
            symbol = key[:-5]
            if symbol in self.rules:
                self.tree.new_error(node, 'Skip list for resuming in series for symbol "{}"'
                                    'must be defined before the symbol!'.format(symbol))
            self.directives.skip[symbol] = self.gen_search_list(node.children[1:])

        elif key.endswith('_resume'):
            symbol = key[:-7]
            self.directives.resume[symbol] = self.gen_search_list(node.children[1:])

        else:
            if any(key.startswith(directive) for directive in ('skip', 'error', 'resume')):
                kl = key.split('_')
                proper_usage = '_'.join(kl[1:] + kl[0:1])
                self.tree.new_error(node, 'Directive "%s" must be used as postfix not prefix to '
                                    'the symbolname. Please, write: "%s"' % (kl[0], proper_usage))
            else:
                self.tree.new_error(node, 'Unknown directive %s ! (Known directives: %s.)' %
                                    (key, ', '.join(k for k in KNOWN_DIRECTIVES.keys())))

        return ""


    def non_terminal(self, node: Node, parser_class: str, custom_args: List[str] = []) -> str:
        """
        Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        arguments = [self.compile(r) for r in node.children] + custom_args
        assert all(isinstance(arg, str) for arg in arguments), str(arguments)
        # remove drop clause for non dropping definitions of forms like "/\w+/~"
        if (parser_class == "Series" and node.tag_name not in self.directives.drop
            and DROP_REGEXP in self.directives.drop and self.context[-2].tag_name == "definition"
            and all((arg.startswith('Drop(RegExp(') or arg.startswith('Drop(Text(')
                     or arg in EBNFCompiler.COMMENT_OR_WHITESPACE) for arg in arguments)):
            arguments = [arg.replace('Drop(', '').replace('))', ')') for arg in arguments]
        if self.drop_flag:
            return 'Drop(' + parser_class + '(' + ', '.join(arguments) + '))'
        else:
            return parser_class + '(' + ', '.join(arguments) + ')'


    def on_expression(self, node) -> str:
        # TODO: Add check for errors like "a" | "ab" (which will always yield a, even for ab)

        # The following algorithm reorders literal alternatives, so that earlier alternatives
        # doe not pre-empt later alternatives, e.g. 'ID' | 'IDREF' will be reordered as
        # 'IDREF' | 'ID'
        # TODO: Add symbols defined as literals, here...

        def move_items(l: List, a: int, b: int):
            """Moves all items in the interval [a:b[ one position forward and moves the
            item at position b to position a."""
            if a > b:
                a, b = b, a
            last = l[b]
            for i in range(b, a, -1):
                l[i] = l[i-1]
            l[a] = last

        def literal_content(nd: Node) -> Optional[str]:
            """Returns the literal content of either a literal-Node, a plaintext-Node
            or a symbol-Node, where the symbol is defined as a literal or plaintext."""
            if nd.tag_name in ('literal', 'plaintext'):
                return nd.content[1:-1]
            elif nd.tag_name == 'symbol':
                if self.cache_literal_symbols is None:
                    self.cache_literal_symbols = dict()
                    for df in self.tree.select_children('definition'):
                        if df.children[1].tag_name in ('literal', 'plaintext'):
                            self.cache_literal_symbols[df.children[0].content] = \
                                df.children[1].content[1:-1]
                return self.cache_literal_symbols.get(nd.content, None)
            return None

        literals = []  # type: List[List[int, str]]
        for i, child in enumerate(node.children):
            content = literal_content(child)
            if content is not None:
                literals.append([i, content])

        move = []          # type: List[Tuple[int, int]]
        snapshots = set()  # type: Set[Tuple[int]]
        start_over = True  # type: bool
        while start_over:
            start_over = False
            for i in range(1, len(literals)):
                later = literals[i][1]
                for k in range(i):
                    earlier = literals[k][1]
                    if later.startswith(earlier):
                        a, b = literals[k][0], literals[i][0]
                        move.append((a, b))
                        literals[i][0] = a
                        for n in range(k, i):
                            literals[n][0] += 1
                        self.tree.new_error(
                            node, 'Alternative "%s" should not preceede "%s" where it occurs '
                            'at the beginning! Reorder to avoid warning.' % (earlier, later),
                            REORDERING_OF_ALTERNATIVES_REQUIRED)
                        start_over = True
                        break
                if start_over:
                    break
            if start_over:
                move_items(literals, k, i)
                snapshot = tuple(item[1] for item in literals)
                if snapshot in snapshots:
                    self.tree.new_error(
                        node, 'Reordering of alternatives "%s" and "%s" required but not possible!'
                              % (earlier, later), BAD_ORDER_OF_ALTERNATIVES)
                    move = []
                    start_over = False
                else:
                    snapshots.add(snapshot)

        if move:
            children = list(node.children)
            for mv in move:
                move_items(children, mv[0], mv[1])
            node.result = tuple(children)

        return self.non_terminal(node, 'Alternative')


    def _error_customization(self, node) -> Tuple[Tuple[Node, ...], List[str]]:
        """Generates the customization arguments (mandatory, error_msgs, skip) for
        `MandatoryNary`-parsers (Series, Interleave, ...)."""
        mandatory_marker = []
        filtered_children = []  # type: List[Node]
        for nd in node.children:
            if nd.tag_name == TOKEN_PTYPE and nd.content == "§":
                mandatory_marker.append(len(filtered_children))
                if len(mandatory_marker) > 1:
                    self.tree.new_error(nd, 'One mandatory marker (§) is sufficient to declare '
                                        'the rest of the elements as mandatory.', WARNING)
            else:
                filtered_children.append(nd)
        custom_args = ['mandatory=%i' % mandatory_marker[0]] if mandatory_marker else []
        # add custom error message if it has been declared for the current definition
        if custom_args:
            current_symbol = next(reversed(self.rules.keys()))
            # add customized error messages, if defined
            if current_symbol in self.directives.error:
                if current_symbol in self.consumed_custom_errors:
                    self.tree.new_error(
                        node, "Cannot apply customized error messages unambiguously, because "
                        "symbol {} contains more than one parser with a mandatory marker '§' "
                        "in its definiens.".format(current_symbol),
                        AMBIGUOUS_ERROR_HANDLING)
                else:
                    # use class field instead or direct representation of error messages!
                    custom_args.append('err_msgs={err_msgs_name}["{symbol}"]'
                                       .format(err_msgs_name=self.ERR_MSGS_KEYWORD,
                                               symbol=current_symbol))
                    self.consumed_custom_errors.add(current_symbol)
            # add skip-rules to resume parsing of a series, if rules have been declared
            if current_symbol in self.directives.skip:
                if current_symbol in self.consumed_skip_rules:
                    self.tree.new_error(
                        node, "Cannot apply 'skip-rules' unambigiously, because symbol "
                        "{} contains more than one parser with a mandatory marker '§' "
                        "in its definiens.".format(current_symbol),
                        AMBIGUOUS_ERROR_HANDLING)
                else:
                    # use class field instead or direct representation of error messages!
                    custom_args.append('skip={skip_rules_name}["{symbol}"]'
                                       .format(skip_rules_name=self.SKIP_RULES_KEYWORD,
                                               symbol=current_symbol))
                    self.consumed_skip_rules.add(current_symbol)
        return tuple(filtered_children), custom_args


    def on_sequence(self, node) -> str:
        filtered_result, custom_args = self._error_customization(node)
        mock_node = Node(node.tag_name, filtered_result)
        return self.non_terminal(mock_node, 'Series', custom_args)


    def on_interleave(self, node) -> str:
        children = []
        repetitions = []
        filtered_result, custom_args = self._error_customization(node)
        for child in filtered_result:
            if child.tag_name == "group":
                assert len(child.children) == 1
                if child.children[0].tag_name == 'repetition':
                    child.tag_name = "option"
                    child.children[0].tag_name = "oneormore"
                elif child.children[0].tag_name == 'option':
                    child = child.children[0]
                else:
                    repetitions.append((1, 1))
                    children.append(child.children[0])
                    continue
            if child.tag_name == "oneormore":
                repetitions.append((1, INFINITE))
                assert len(child.children) == 1
                children.append(child.children[0])
            elif child.tag_name == "repetition":
                repetitions.append((0, INFINITE))
                assert len(child.children) == 1
                children.append(child.children[0])
            elif child.tag_name == "option":
                repetitions.append((0, 1))
                assert len(child.children) == 1
                children.append(child.children[0])
            elif child.tag_name == "counted":
                what, r = self.extract_counted(child)
                repetitions.append(r)
                children.append(what)
            else:
                repetitions.append((1, 1))
                children.append(child)
        custom_args.append('repetitions=' + str(repetitions).replace(str(INFINITE), 'INFINITE'))
        mock_node = Node(node.tag_name, tuple(children))
        return self.non_terminal(mock_node, 'Interleave', custom_args)


    def on_lookaround(self, node: Node) -> str:
        assert node.children
        assert len(node.children) == 2
        assert node.children[0].tag_name == 'flowmarker'
        prefix = node.children[0].content
        # arg_node = node.children[1]
        node.result = node.children[1:]
        assert prefix in {'&', '!', '<-&', '<-!'}

        parser_class = self.PREFIX_TABLE[prefix]
        result = self.non_terminal(node, parser_class)
        if prefix[:2] == '<-':
            def verify(node: Optional[Node]):
                nd = node
                if len(nd.children) >= 1:
                    nd = nd.children[0]
                while nd.tag_name == "symbol":
                    symlist = self.rules.get(nd.content, [])
                    if len(symlist) == 2:
                        nd = symlist[1]
                    else:
                        if len(symlist) == 1:
                            nd = symlist[0].children[1]
                        break
                # content = nd.content
                if nd.tag_name != "regexp":   # outdated: or content[:1] != '/' or content[-1:] != '/'):
                    self.tree.new_error(node, "Lookbehind-parser can only be used with RegExp"
                                              "-parsers, not: " + nd.tag_name)

            if not result.startswith('RegExp('):
                self.deferred_tasks.append(lambda :verify(node))
        return result

    def on_difference(self, node: Node) -> str:
        assert len(node.children) == 2, str(node.as_sxpr())
        left = self.compile(node.children[0])
        right = self.compile(node.children[1])
        return "Series(NegativeLookahead(%s), %s)" % (right, left)

    def on_element(self, node: Node) -> str:
        assert node.children
        assert len(node.children) == 2
        assert node.children[0].tag_name == "retrieveop"
        assert node.children[1].tag_name == "symbol"
        prefix = node.children[0].content  # type: str
        arg = node.children[1].content     # type: str
        node.result = node.children[1:]
        assert prefix in {'::', ':?', ':'}

        if self.anonymous_regexp.match(arg):
            self.tree.new_error(
                node, ('Retrive operator "%s" does not work with anonymous parsers like %s')
                      % (prefix, arg))
            return arg

        custom_args = []           # type: List[str]
        match_func = 'last_value'  # type: str
        if arg in self.directives.filter:
            match_func = self.directives.filter[arg]
        if prefix.endswith('?'):
            match_func = 'optional_' + match_func
        if match_func != 'last_value':
            custom_args = ['match_func=%s' % match_func]

        self.variables.add(arg)
        parser_class = self.PREFIX_TABLE[prefix]
        return self.non_terminal(node, parser_class, custom_args)


    def on_option(self, node) -> str:
        return self.non_terminal(node, 'Option')


    def on_repetition(self, node) -> str:
        return self.non_terminal(node, 'ZeroOrMore')


    def on_oneormore(self, node) -> str:
        return self.non_terminal(node, 'OneOrMore')


    def on_group(self, node) -> str:
        assert len(node.children) == 1, node.as_sxpr()
        return self.compile(node.children[0])


    def extract_range(self, node) -> Tuple[int, int]:
        """Returns the range-value of a range-node as a tuple of two integers.
        """
        assert node.tag_name == "range"
        assert all(child.tag_name == 'multiplier' for child in node.children)
        if len(node.children) == 2:
            r = (int(node.children[0].content), int(node.children[1].content))
            if r[0] > r[1]:
                self.tree.new_error(
                    node, "Upper bound %i of range is greater than lower bound %i!" % r)
                return r[1], r[0]
            return r
        else:
            assert len(node.children) == 1
            return (int(node.children[0].content), int(node.children[0].content))


    def extract_counted(self, node) -> Tuple[Node, Tuple[int, int]]:
        """Returns the content of a counted-node in a normalized form:
        (node, (n, m)) where node is root of the sub-parser that is counted,
        i.e. repeated n or n upto m times.
        """
        assert node.tag_name == 'counted'
        assert len(node.children) == 2
        range = node.get('range', None)
        if range:
            r = self.extract_range(range)
            what = node.children[0]
            assert what.tag_name != 'range'
        else:  # multiplier specified instead of range
            if node.children[0].tag_name == 'multiplier':
                m = int(node.children[0].content)
                what = node.children[1]
            else:
                assert node.children[1].tag_name == 'multiplier'
                m = int(node.children[1].content)
                what = node.children[0]
            if what.tag_name == 'option':
                what = what.children[0]
                r = (0, m)
            elif what.tag_name == 'oneormore':
                what = what.children[0]
                r = (m, INFINITE)
            elif what.tag_name == 'repetition':
                self.tree.new_error(
                    node, 'Counting zero or more repetitions of something does not make sense! '
                    'Its still zero or more repetitions all the same.')
                what = what.children[0]
                r = (0, INFINITE)
            else:
                r = (m, m)
        return what, r


    def on_counted(self, node) -> str:
        what, r = self.extract_counted(node)
        # whatstr = self.compile(what)
        rstr = str(r).replace(str(INFINITE), 'INFINITE')
        mock_node = Node(node.tag_name, (what,))
        return self.non_terminal(mock_node, 'Counted', ['repetitions=' + rstr])


    def on_symbol(self, node: Node) -> str:     # called only for symbols on the right hand side!
        symbol = node.content  # ; assert result == cast(str, node.result)
        if symbol in self.directives.tokens:
            return 'PreprocessorToken("' + symbol + '")'
        else:
            self.current_symbols.append(node)
            if symbol not in self.symbols:
                # remember first use of symbol, so that dangling references or
                # redundant definitions or usages of symbols can be detected later
                self.symbols[symbol] = node
            if symbol in self.rules:
                self.recursive.add(symbol)
            if symbol in EBNFCompiler.KEYWORD_SUBSTITUTION:
                keyword = EBNFCompiler.KEYWORD_SUBSTITUTION[symbol]
                self.required_keywords.add(keyword)
                return keyword
            elif symbol.endswith('__'):
                self.tree.new_error(node, 'Illegal use of reserved symbol name "%s"!' % symbol)
            return symbol


    def TEXT_PARSER(self, text):
        if DROP_STRINGS in self.directives.drop and self.context[-2].tag_name != "definition":
            return 'Drop(Text(' + text + '))'
        return 'Text(' + text + ')'

    def REGEXP_PARSER(self, regexp):
        if DROP_REGEXP in self.directives.drop and self.context[-2].tag_name != "definition":
            return 'Drop(RegExp(' + regexp + '))'
        return 'RegExp(' + regexp + ')'


    def WSPC_PARSER(self, force_drop=False):
        if ((force_drop or DROP_WSPC in self.directives.drop)
                and (self.context[-2].tag_name != "definition"
                     or self.context[-1].tag_name == 'literal')):
            return 'dwsp__'
        return 'wsp__'


    def on_literals(self, node: Node) -> str:
        self.join_literals(node)
        return self.on_literal(node)


    def on_literal(self, node: Node) -> str:
        center = self.TEXT_PARSER(escape_control_characters(node.content))
        force = DROP_STRINGS in self.directives.drop
        left = self.WSPC_PARSER(force) if 'left' in self.directives.literalws else ''
        right = self.WSPC_PARSER(force) if 'right' in self.directives.literalws else ''
        if left or right:
            return 'Series(' + ", ".join(item for item in (left, center, right) if item) + ')'
        return center


    def on_plaintext(self, node: Node) -> str:
        tk = escape_control_characters(node.content)
        rpl = '"' if tk.find('"') < 0 else "'" if tk.find("'") < 0 else ''
        if rpl:
            tk = rpl + tk[1:-1] + rpl
        else:
            tk = rpl + tk.replace('"', '\\"')[1:-1] + rpl
        return self.TEXT_PARSER(tk)


    def on_regexp(self, node: Node) -> str:
        rx = node.content
        name = []   # type: List[str]
        try:
            arg = repr(self.check_rx(node, rx.replace(r'\/', '/')))
        except AttributeError as error:
            from traceback import extract_tb, format_list
            trace = ''.join(format_list(extract_tb(error.__traceback__)))
            errmsg = "%s (AttributeError: %s;\n%s)\n%s" \
                     % (EBNFCompiler.AST_ERROR, str(error), trace, node.as_sxpr())
            self.tree.new_error(node, errmsg)
            return '"' + errmsg + '"'
        return self.REGEXP_PARSER(', '.join([arg] + name))


    def on_char_range(self, node) -> str:
        for child in node.children:
            if child.tag_name == 'character':
                child.result = self.extract_character(child)
            elif child.tag_name == 'free_char':
                child.result = self.extract_free_char(child)
        re_str = re.sub(r"(?<!\\)'", r'\'', node.content)
        re_str = re.sub(r"(?<!\\)]", r'\]', re_str)
        return "RegExp('[%s]')" % re_str


    def extract_character(self, node: Node) -> str:
        hexcode = node.content
        if len(hexcode) > 4:
            assert len(hexcode) <= 8
            code = '\\U' + (8 - len(hexcode)) * '0' + hexcode
        elif len(hexcode) > 2:
            code = '\\u' + (4 - len(hexcode)) * '0' + hexcode
        else:
            code = '\\x' + (2 - len(hexcode)) * '0' + hexcode
        return code


    def on_character(self, node: Node) -> str:
        return "RegExp('%s')" % self.extract_character(node)


    def extract_free_char(self, node: Node) -> str:
        assert len(node.content) == 1
        bytestr = node.content.encode('unicode-escape')
        return bytestr.decode()


    def on_any_char(self, node: Node) -> str:
        return 'AnyChar()'


    def on_whitespace(self, node: Node) -> str:
        return self.WSPC_PARSER()



def get_ebnf_compiler(grammar_name="", grammar_source="") -> EBNFCompiler:
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.ebnf_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except AttributeError:
        compiler = EBNFCompiler(grammar_name, grammar_source)
        compiler.set_grammar_name(grammar_name, grammar_source)
        THREAD_LOCALS.ebnf_compiler_singleton = compiler
        return compiler


def compile_ebnf_ast(ast: Node) -> str:
    """Compiles the abstract-syntax-tree of an EBNF-source-text into
    python code of a class derived from `parse.Grammar` that can
    parse text following the grammar describend with the EBNF-code."""
    return get_ebnf_compiler()(ast)


########################################################################
#
# EBNF compiler
#
########################################################################

def compile_ebnf(ebnf_source: str, branding: str = 'DSL', preserve_AST: bool = False) \
        -> ResultTuple:
    """
    Compiles an `ebnf_source` (file_name or EBNF-string) and returns
    a tuple of the python code of the compiler, a list of warnings or errors
    and the abstract syntax tree of the EBNF-source.
    This function is merely syntactic sugar.
    """
    return compile_source(ebnf_source,
                          get_ebnf_preprocessor(),
                          get_ebnf_grammar(),
                          get_ebnf_transformer(),
                          get_ebnf_compiler(branding, ebnf_source),
                          preserve_AST=preserve_AST)
