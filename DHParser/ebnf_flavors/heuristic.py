"""heuristic.py - A heursitic EBNF grammar that captures several different
                  flavors like classic EBNF, PEG and variants

Copyright 2024  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.

The EBNF-parser defined in the HeuristicEBNFGrammar-class is slower than
the standard ConfigurableEBNF-parser from DHParser.ebenf, but it is more
versatile and does not need any configuration of its delimiter-set, but
can "learn" a number of different delimiter sets right from the grammar,
e.g. whether "::=" or ":=" or "=" is used for definitions, whether there
is a trailing ";" or not, and the like.

HeuristicEBNFGrammar can be used as a last resort in all those cases where
no more specialized grammar exists or where the particular EBNF-flavor
used could not be detected beforehand by probing.
"""

from __future__ import annotations

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import os
import sys
from typing import Optional

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, os.path.pardir, os.path.pardir))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser.configuration import ALLOWED_PRESET_VALUES
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, mixin_comment, \
    last_value, matching_bracket, optional_last_value, SmartRE, Always, Never, ParseFunc
from DHParser.toolkit import Tuple, List, INFINITE

__all__ = ('HeuristicEBNFGrammar')


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class HeuristicEBNFGrammar(Grammar):
    r"""Parser for an EBNF source file that heuristically detects the
    used syntactical variant of EBNF on the fly.

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
        literal    = /"(?:(?<!\\)\\"|[^"])*?"/~         # e.g. "(", '+', 'while'
                   | /'(?:(?<!\\)\\'|[^'])*?'/~         # whitespace following literals will be ignored tacitly.
                   | /’(?:(?<!\\)\\’|[^’])*?’/~
        plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~         # like literal but does not eat whitespace
                   | /´(?:(?<!\\)\\´|[^´])*?´/~
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

        CH_LEADIN  = `0x` | `#x` | `\x` | `\u` | `\U`

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
    """
    countable = Forward()
    element = Forward()
    expression = Forward()
    source_hash__ = "f28102ebed9fa2a532524a8a7fc322a7"
    disposable__ = re.compile(
        '(?:MOD_SEP$|ANY_SUFFIX$|no_range$|component$|EOF$|pure_elem$|countable$|MOD_SYM$|is_mdef$|FOLLOW_UP$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'definition': [(re.compile(r','),
                                        'Delimiter "," not expected in definition!\\nEither this was meant to be a directive and the directive symbol @ is missing\\nor the error is due to inconsistent use of the comma as a delimiter\\nfor the elements of a sequence.')]}
    COMMENT__ = r'(?!#x[A-Fa-f0-9])#.*(?:\n|$)|/\*(?:.|\n)*?\*/|\(\*(?:.|\n)*?\*\)'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    RAISE_EXPR_WO_BRACKETS = Text("")
    HEXCODE = RegExp('(?:[A-Fa-f1-9]|0(?!x)){1,8}')
    SYM_REGEX = RegExp('(?!\\d)\\w(?:-?\\w)*')
    RE_CORE = RegExp('(?:(?<!\\\\)\\\\(?:/)|[^/])*')
    regex_heuristics = SmartRE(
        f'(?! +`[^`]*` +/| +´[^´]*´ +/| +\'[^\']*\' +/| +"[^"]*" +/| +\\w+ +/)([^/\\n*?+\\\\]*[*?+\\\\][^/\\n]*/|[^\\w]+/|[^ ])',
        '!/ +`[^`]*` +\\//|/ +´[^´]*´ +\\//|/ +\'[^\']*\' +\\//|/ +"[^"]*" +\\//|/ +\\w+ +\\// /[^\\/\\n*?+\\\\]*[*?+\\\\][^\\/\\n]*\\//|/[^\\w]+\\//|/[^ ]/')
    literal_heuristics = SmartRE(
        f'((?:~?\\s*"(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^"]*)*")|(?:~?\\s*\'(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^\']*)*\')|(?:~?\\s*`(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^`]*)*`)|(?:~?\\s*´(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^´]*)*´)|(?:~?\\s*/(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^/]*)*/))',
        '/~?\\s*"(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^"]*)*"/|/~?\\s*\'(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^\']*)*\'/|/~?\\s*`(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^`]*)*`/|/~?\\s*´(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^´]*)*´/|/~?\\s*\\/(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^\\/]*)*\\//')
    more_than_one_blank = RegExp('[^ \\]]*[ ][^ \\]]*[ ]')
    STRICT_SYM_REGEX = RegExp('(?!\\d)\\w+')
    CH_LEADIN = Capture(
        SmartRE(f'(?P<:Text>0x|%x|U\\+|u\\+|\\#x|\\\\x|\\\\u|\\\\U)', '`0x`|`%x`|`U+`|`u+`|`#x`|`\\x`|`\\u`|`\\U`'),
        zero_length_warning=False)
    MOD_SYM = Drop(Text("->"))
    character = Series(Retrieve(CH_LEADIN), HEXCODE)
    RE_LEADOUT = Capture(Text("/"), zero_length_warning=True)
    RE_LEADIN = Capture(Alternative(Series(Text("/"), Lookahead(regex_heuristics)), Text("^/")),
                        zero_length_warning=True)
    TIMES = Capture(Text("*"), zero_length_warning=False)
    RNG_DELIM = Capture(Text(","), zero_length_warning=False)
    BRACE_SIGN = Capture(SmartRE(f'(?P<:Text>\\{{|\\()', '`{`|`(`'), zero_length_warning=False)
    RNG_BRACE = Capture(Retrieve(BRACE_SIGN), zero_length_warning=True)
    ENDL = Capture(SmartRE(f'(?P<:Text>;|)', '`;`|``'), zero_length_warning=False)
    AND = Capture(SmartRE(f'(?P<:Text>,|)', '`,`|``'), zero_length_warning=False)
    OR = Capture(Alternative(Text("|"), Series(Text("/"), NegativeLookahead(regex_heuristics))),
                 zero_length_warning=True)
    _DEF = SmartRE(f'(?P<:Text>=|:=|::=|<\\-)|(:\\n)|(?P<:Text>:\\ )', '`=`|`:=`|`::=`|`<-`|/:\\n/|`: `')
    DEF = Capture(Synonym(_DEF), zero_length_warning=False)
    EOF = Drop(Series(SmartRE(f'(?!.)', '!/./'), Option(Pop(ENDL, match_func=optional_last_value)),
                      Option(Pop(DEF, match_func=optional_last_value)), Option(Pop(OR, match_func=optional_last_value)),
                      Option(Pop(AND, match_func=optional_last_value)),
                      Option(Pop(RNG_DELIM, match_func=optional_last_value)),
                      Option(Pop(BRACE_SIGN, match_func=optional_last_value)),
                      Option(Pop(CH_LEADIN, match_func=optional_last_value)),
                      Option(Pop(TIMES, match_func=optional_last_value)),
                      Option(Pop(RE_LEADIN, match_func=optional_last_value)),
                      Option(Pop(RE_LEADOUT, match_func=optional_last_value))))
    name = Synonym(SYM_REGEX)
    placeholder = Series(Series(Text("$"), dwsp__), name, NegativeLookahead(Text("(")), dwsp__)
    multiplier = SmartRE(f'(\\d+)(?:{WSP_RE__})', '/\\d+/ ~')
    whitespace = SmartRE(f'(~)(?:{WSP_RE__})', '/~/ ~')
    any_char = Series(Text("."), dwsp__)
    free_char = SmartRE(f'([^\\n\\[\\]\\\\]|\\\\[nrtfv`´\'"(){{}}\\[\\]/\\\\])',
                        '/[^\\n\\[\\]\\\\]/|/\\\\[nrtfv`´\'"(){}\\[\\]\\/\\\\]/')
    range_desc = Series(Alternative(character, free_char),
                        Option(Series(Option(Text("-")), Alternative(character, free_char))))
    char_range_heuristics = Series(NegativeLookahead(
        Alternative(RegExp('[\\n]'), more_than_one_blank, Series(dwsp__, literal_heuristics),
                    Series(dwsp__, Option(SmartRE(f'(?P<:Text>::|:\\?|:)', '`::`|`:?`|`:`')), STRICT_SYM_REGEX,
                           RegExp('\\s*\\]')))), Lookahead(Series(OneOrMore(range_desc), Text("]"))))
    range_chain = Series(Text("["), Option(Text("^")), OneOrMore(range_desc), Text("]"))
    char_ranges = Series(RE_LEADIN, range_chain, ZeroOrMore(Series(Text("|"), range_chain)), RE_LEADOUT, dwsp__)
    char_range = Series(Text("["), Lookahead(char_range_heuristics), Option(Text("^")), OneOrMore(range_desc),
                        Series(Text("]"), dwsp__))
    regexp = Series(Retrieve(RE_LEADIN), RE_CORE, Retrieve(RE_LEADOUT), dwsp__)
    plaintext = SmartRE(
        f'(?:(`(?:(?<!\\\\)(?:\\\\\\\\)*\\\\`|[^`])*?`)(?:{WSP_RE__}))|(?:(´(?:(?<!\\\\)(?:\\\\\\\\)*\\\\´|[^´])*?´)(?:{WSP_RE__}))',
        '/`(?:(?<!\\\\)(?:\\\\\\\\)*\\\\`|[^`])*?`/ ~|/´(?:(?<!\\\\)(?:\\\\\\\\)*\\\\´|[^´])*?´/ ~')
    literal = SmartRE(
        f'(?:("(?:(?<!\\\\)(?:\\\\\\\\)*\\\\"|[^"])*?")(?:{WSP_RE__}))|(?:(\'(?:(?<!\\\\)(?:\\\\\\\\)*\\\\\'|[^\'])*?\')(?:{WSP_RE__}))|(?:(’(?:(?<!\\\\)(?:\\\\\\\\)*\\\\’|[^’])*?’)(?:{WSP_RE__}))',
        '/"(?:(?<!\\\\)(?:\\\\\\\\)*\\\\"|[^"])*?"/ ~|/\'(?:(?<!\\\\)(?:\\\\\\\\)*\\\\\'|[^\'])*?\'/ ~|/’(?:(?<!\\\\)(?:\\\\\\\\)*\\\\’|[^’])*?’/ ~')
    symbol = Series(SYM_REGEX, dwsp__)
    argument = Alternative(literal, Series(name, dwsp__))
    parser = Series(Series(Text("@"), dwsp__), name, Series(Text("("), dwsp__), Option(argument),
                    Series(Text(")"), dwsp__))
    no_range = Drop(Alternative(NegativeLookahead(multiplier), Series(Lookahead(multiplier), Retrieve(TIMES))))
    macro = Series(Series(Text("$"), dwsp__), name, Series(Text("("), dwsp__), no_range, expression,
                   ZeroOrMore(Series(Series(Text(","), dwsp__), no_range, expression)), Series(Text(")"), dwsp__))
    range = Series(RNG_BRACE, dwsp__, multiplier, Option(Series(Retrieve(RNG_DELIM), dwsp__, multiplier)),
                   Pop(RNG_BRACE, match_func=matching_bracket), dwsp__)
    counted = Alternative(Series(countable, range), Series(countable, Retrieve(TIMES), dwsp__, multiplier),
                          Series(multiplier, Retrieve(TIMES), dwsp__, countable, mandatory=3))
    option = Alternative(
        Series(NegativeLookahead(char_range), Series(Text("["), dwsp__), expression, Series(Text("]"), dwsp__),
               mandatory=2), Series(element, Series(Text("?"), dwsp__)))
    repetition = Alternative(
        Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}"), dwsp__), mandatory=2),
        Series(element, Series(Text("*"), dwsp__), no_range))
    oneormore = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}+"), dwsp__)),
                            Series(element, Series(Text("+"), dwsp__)))
    group = Series(Series(Text("("), dwsp__), no_range, expression, Series(Text(")"), dwsp__), mandatory=2)
    retrieveop = SmartRE(f'(?P<:Text>::)(?:{WSP_RE__})|(?P<:Text>:\\?)(?:{WSP_RE__})|(?P<:Text>:)(?:{WSP_RE__})',
                         '"::"|":?"|":"')
    flowmarker = SmartRE(
        f'(?P<:Text>!)(?:{WSP_RE__})|(?P<:Text>\\&)(?:{WSP_RE__})|(?P<:Text><\\-!)(?:{WSP_RE__})|(?P<:Text><\\-\\&)(?:{WSP_RE__})',
        '"!"|"&"|"<-!"|"<-&"')
    ANY_SUFFIX = RegExp('[?*+]')
    is_mdef = Series(Series(Text("$"), dwsp__), name, Option(
        Series(Series(Text("("), dwsp__), placeholder, ZeroOrMore(Series(Series(Text(","), dwsp__), placeholder)),
               Series(Text(")"), dwsp__))), dwsp__, Retrieve(DEF))
    pure_elem = Series(element, NegativeLookahead(ANY_SUFFIX), mandatory=1)
    MOD_SEP = RegExp(' *: *')
    hide = SmartRE(
        f'(?P<:Text>HIDE)(?:{WSP_RE__})|(?P<:Text>Hide)(?:{WSP_RE__})|(?P<:Text>hide)(?:{WSP_RE__})|(?P<:Text>DISPOSE)(?:{WSP_RE__})|(?P<:Text>Dispose)(?:{WSP_RE__})|(?P<:Text>dispose)(?:{WSP_RE__})',
        '"HIDE"|"Hide"|"hide"|"DISPOSE"|"Dispose"|"dispose"')
    drop = SmartRE(
        f'(?P<:Text>DROP)(?:{WSP_RE__})|(?P<:Text>Drop)(?:{WSP_RE__})|(?P<:Text>drop)(?:{WSP_RE__})|(?P<:Text>SKIP)(?:{WSP_RE__})|(?P<:Text>Skip)(?:{WSP_RE__})|(?P<:Text>skip)(?:{WSP_RE__})',
        '"DROP"|"Drop"|"drop"|"SKIP"|"Skip"|"skip"')
    part = Series(Alternative(oneormore, pure_elem), Option(Series(MOD_SYM, dwsp__, drop)))
    term = Series(Alternative(oneormore, counted, repetition, option, pure_elem), Option(Series(MOD_SYM, dwsp__, drop)))
    difference = Series(term,
                        Option(Series(NegativeLookahead(Text("->")), Series(Text("-"), dwsp__), part, mandatory=2)))
    lookaround = Series(flowmarker, part, mandatory=1)
    interleave = Series(difference,
                        ZeroOrMore(Series(Series(Text("°"), dwsp__), Option(Series(Text("§"), dwsp__)), difference)))
    sequence = Series(Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround), ZeroOrMore(
        Series(NegativeLookahead(Text("@")), NegativeLookahead(Series(symbol, Retrieve(DEF))), Retrieve(AND), dwsp__,
               Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround))))
    modifier = Series(Alternative(drop, Option(hide)), MOD_SEP)
    FOLLOW_UP = Alternative(Text("@"), Text("$"), modifier, symbol, EOF)
    is_def = Alternative(Series(Option(Series(MOD_SEP, symbol)), Retrieve(DEF)), Series(MOD_SEP, is_mdef))
    macrobody = Synonym(expression)
    definition = Series(Option(modifier), symbol, Retrieve(DEF), dwsp__, Option(Series(Retrieve(OR), dwsp__)),
                        expression, Option(Series(MOD_SYM, dwsp__, hide)), Retrieve(ENDL), dwsp__, Lookahead(FOLLOW_UP),
                        mandatory=2)
    procedure = Series(SYM_REGEX, Series(Text("()"), dwsp__))
    literals = OneOrMore(literal)
    macrodef = Series(Option(modifier), Series(Text("$"), dwsp__), name, dwsp__, Option(
        Series(Series(Text("("), dwsp__), placeholder, ZeroOrMore(Series(Series(Text(","), dwsp__), placeholder)),
               Series(Text(")"), dwsp__), mandatory=1)), Retrieve(DEF), dwsp__, Option(Series(OR, dwsp__)), macrobody,
                      Option(Series(MOD_SYM, dwsp__, hide)), Retrieve(ENDL), dwsp__, Lookahead(FOLLOW_UP))
    _is_def = Alternative(Series(Option(Series(MOD_SEP, symbol)), _DEF), Series(MOD_SEP, is_mdef))
    component = Alternative(regexp, literals, procedure,
                            Series(symbol, NegativeLookahead(_DEF), NegativeLookahead(_is_def)),
                            Series(Lookahead(Text("$")), NegativeLookahead(is_mdef), placeholder,
                                   NegativeLookahead(is_def), mandatory=2),
                            Series(Series(Text("("), dwsp__), expression, Series(Text(")"), dwsp__)),
                            Series(RAISE_EXPR_WO_BRACKETS, expression))
    directive = Series(Series(Text("@"), dwsp__), symbol, Series(Text("="), dwsp__), component,
                       ZeroOrMore(Series(Series(Text(","), dwsp__), component)), Lookahead(FOLLOW_UP), mandatory=1)
    element.set(
        Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(is_def)), literal, plaintext, char_ranges,
                    regexp, char_range, Series(character, dwsp__), any_char, whitespace, group,
                    Series(macro, NegativeLookahead(is_def)), Series(placeholder, NegativeLookahead(is_def)), parser))
    countable.set(Alternative(option, oneormore, element))
    expression.set(Series(sequence, ZeroOrMore(Series(Retrieve(OR), dwsp__, sequence))))
    syntax = Series(dwsp__, ZeroOrMore(Alternative(definition, directive, macrodef)), EOF)
    resume_rules__ = {'definition': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')],
                      'directive': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')]}
    root__ = syntax

    def __init__(self, root: Optional[Parser] = None, static_analysis: Optional[bool] = None) -> None:
        Grammar.__init__(self, root, static_analysis)
        self.free_char_parsefunc__ = self.free_char._parse
        self.char_range_heuristics_parsefunc__ = self.char_range_heuristics._parse
        self.regex_heuristics_parserfunc__ = self.regex_heuristics._parse
        self.mode__ = 'fixed'

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
            return 'heuristic'
        elif signature == ('never', 'always', 'always'):
            return 'strict'  # or 'classic'
        elif signature == ('custom', 'never', 'always'):
            return 'peg-like'
        elif signature == ('custom', 'always', 'always'):
            return 'regex-like'
        else:
            return "undefined"

    @mode.setter
    def mode(self, mode: str):
        if mode == self.mode:
            return

        def set_parsefunc(p: Parser, f: ParseFunc):
            method = f.__get__(p, type(p))  # bind function f to parser p
            p._parse_proxy = method

        always = Always._parse
        never = Never._parse

        if mode == 'heuristic':
            set_parsefunc(self.free_char, self.free_char_parsefunc__)
            set_parsefunc(self.regex_heuristics, self.regex_heuristics_parserfunc__)
            set_parsefunc(self.char_range_heuristics, self.char_range_heuristics_parsefunc__)
        elif mode in ('strict', 'classic'):
            set_parsefunc(self.free_char, never)
            set_parsefunc(self.regex_heuristics, always)
            set_parsefunc(self.char_range_heuristics, always)
        elif mode == 'peg-like':
            set_parsefunc(self.free_char, self.free_char_parsefunc__)
            set_parsefunc(self.regex_heuristics, never)
            set_parsefunc(self.char_range_heuristics, always)
        elif mode == 'regex-like':
            set_parsefunc(self.free_char, self.free_char_parsefunc__)
            set_parsefunc(self.regex_heuristics, always)
            set_parsefunc(self.char_range_heuristics, always)
        else:
            raise ValueError('Mode must be one of: ' + ', '.join(
                ALLOWED_PRESET_VALUES['syntax_variant']))


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

