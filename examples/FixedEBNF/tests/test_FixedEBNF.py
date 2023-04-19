#!/usr/bin/env python3

"""test_FixedEBNF.py - tests for the FixedEBNFGrammar

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

import copy
import os
import sys
from functools import partial, lru_cache
from typing import List, Tuple, Optional, Union, Any

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import get_config_value, set_config_value
from DHParser.compile import Compiler
from DHParser.dsl import compileDSL
from DHParser.toolkit import compile_python_object, re
from DHParser.log import is_logging, log_ST, log_parsing_history, start_logging, append_log
from DHParser.error import Error, is_error, add_source_locations, MANDATORY_CONTINUATION, \
    MALFORMED_ERROR_STRING, MANDATORY_CONTINUATION_AT_EOF, RESUME_NOTICE, PARSER_STOPPED_BEFORE_END, \
    PARSER_NEVER_TOUCHES_DOCUMENT, CAPTURE_DROPPED_CONTENT_WARNING, ERROR, \
    MANDATORY_CONTINUATION_AT_EOF_NON_ROOT, INFINITE_LOOP_WARNING, ErrorCode
from DHParser.parse import ParserError, Parser, Grammar, Forward, TKN, ZeroOrMore, RE, \
    RegExp, Lookbehind, NegativeLookahead, OneOrMore, Series, Alternative, ParserFactory, \
    Interleave, CombinedParser, Text, EMPTY_NODE, Capture, Drop, Whitespace, Grammar, \
    GrammarError, Counted, Always, INFINITE, longest_match, extract_error_code
from DHParser import compile_source
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler, \
    parse_ebnf, get_ebnf_preprocessor, DHPARSER_IMPORTS, compile_ebnf
from DHParser.preprocess import gen_neutral_srcmap_func, PreprocessorFunc
from DHParser.nodetree import Node, parse_sxpr
from DHParser.stringview import StringView
from DHParser.trace import set_tracer, trace_history, resume_notices_on
from DHParser.transform import  TransformerFunc

from FixedEBNFParser import get_grammar


@lru_cache()
def grammar_provider(ebnf_src: str,
                     branding="DSL",
                     additional_code: str = '',
                     fail_when: ErrorCode = ERROR) -> ParserFactory:
    """
    Compiles an EBNF-grammar and returns a grammar-parser provider
    function for that grammar.

    Args:
        ebnf_src(str):  Either the file name of an EBNF grammar or
            the EBNF-grammar itself as a string.
        branding (str or bool):  Branding name for the compiler
            suite source code.
        additional_code: Python code added to the generated source. This typically
            contains the source code of semantic actions referred to in the
            generated source, e.g. filter-functions, resume-point-search-functions

    Returns:
        A provider function for a grammar object for texts in the
        language defined by ``ebnf_src``.
    """
    grammar_src = compileDSL(
        ebnf_src, get_ebnf_preprocessor(), get_grammar(), get_ebnf_transformer(),
        get_ebnf_compiler(branding, ebnf_src), fail_when)
    log_name = get_config_value('compiled_EBNF_log')
    if log_name and is_logging():  append_log(log_name, grammar_src)
    imports = DHPARSER_IMPORTS
    parsing_stage = compile_python_object('\n'.join([imports, additional_code, grammar_src]),
                                          r'parsing$')  # r'get_(?:\w+_)?grammar$'
    if callable(parsing_stage.factory):
        parsing_stage.factory.python_src__ = grammar_src
        return parsing_stage.factory
    raise ValueError('Could not compile grammar provider!')


EBNF_with_Errors = r"""# Test code with errors. All places marked by a "€" should yield and error

@ comment    = /#.*(?:\n|$)/
@ whitespace = /\s*/
@ literalws  = right
@ disposable = pure_elem, EOF
@ drop       = whitespace, EOF


# re-entry-rules for resuming after parsing-error
@ definition_resume = /\n\s*(?=@|\w+\w*\s*=)/
@ directive_resume  = /\n\s*(?=@|\w+\w*\s*=)/

# specialized error messages for certain cases

@ definition_error  = /,/, 'Delimiter "," not expected in definition!\nEither this was meant to '
                           'be a directive and the directive symbol @ is missing\nor the error is '
                           'due to inconsistent use of the comma as a delimiter\nfor the elements '
                           'of a sequence.'

#: top-level

syntax     = [~//] { definition | directive } §EOF
definition = symbol §:DEF~ expression :ENDL~
directive  = "@" §symbol "="
             (regexp | literals | symbol)
             { "," (regexp | literals | symbol) }

#: components

expression = sequence { :OR~ sequence }
sequence   = ["§"] ( interleave | lookaround )
             { :AND~ ["§"] ( interleave | lookaround ) }
interleave = difference { "°" ["§"] difference }
lookaround = flowmarker § (oneormore | pure_elem)
difference = term ["-" § (oneormore € pure_elem)]               # <- ERROR
term       = oneormore | repetition | option | pure_elem        # resuming expected her

#: elements

pure_elem  = element § !/[?*+]/
element    = [retrieveop] symbol !DEF
           | literal
           | plaintext
           | regexp
           | whitespace
           | group€                                             # <- ERROR

#: flow-operators

flowmarker = "!"  | "&"                                         # resuming expected her
           | "<-!" | "<-&"
retr€ieveop = "::" | ":?" | ":"

#: groups

group      = "(" §expression ")"
oneormore  = "{" expression "}+" | element "+"
repetition = "{" §expressi€on "}" | element "*"                 # <- ERROR
option     = "[" §expression "]" | element "?"                  # resuming expected here

#: leaf-elements

symbol     = /(?!\d)\w+/~
€literals   = { literal }+                                      # <- ERROR
literal    = /"(?:(?<!\\)\\"|[^"])*?"/~                         # resuming expected her
           | /'(?:(?<!\\)\\'|[^'])*?'/~
plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~
regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~
whitespace = /~/~

#: delimiters

DEF        = `=` | `:=` | `::=`
OR         = `|`
AND        = `,` | ``
ENDL       = `;` | ``

EOF = !/./ [:?DEF] [:?OR] [:?AND] [:?ENDL]
"""


class TestReentryAfterError:
    testlang = """@literalws = right
    document = alpha [beta] gamma "."
      alpha = "ALPHA" abc
        abc = §"a" "b" "c"
      beta = "BETA" (bac | bca)
        bac = "b" "a" §"c"
        bca = "b" "c" §"a"
      gamma = "GAMMA" §(cab | cba)
        cab = "c" "a" §"b"
        cba = "c" "b" §"a"
    """
    gr = grammar_provider(testlang)()

    def test_no_resume_rules(self):
        gr = self.gr;  gr.resume_rules = dict()
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, cst.content
        assert cst.pick('alpha').content.startswith('ALPHA')

    def test_no_resume_rules_partial_parsing(self):
        gr = self.gr;  gr.resume_rules = dict()
        content = 'ALPHA acb'
        cst = gr(content, 'alpha')
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')

    def test_simple_resume_rule(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1

    def test_failing_resume_rule(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=XXX)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, cst.content
        # assert cst.pick('alpha').content.startswith('ALPHA')

    def test_several_reentry_points(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)'), re.compile(r'(?=GAMMA)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1

    def test_several_reentry_points_second_point_matching(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)'), re.compile(r'(?=GAMMA)')]
        content = 'ALPHA acb GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1
        resume_notices_on(gr)
        cst = gr(content)
        assert len(cst.errors) == 2 and any(err.code == RESUME_NOTICE for err in cst.errors)

    def test_several_resume_rules_innermost_rule_matching(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)'), re.compile(r'(?=GAMMA)')]
        gr.resume_rules__['beta'] = [re.compile(r'(?=GAMMA)')]
        gr.resume_rules__['bac'] = [re.compile(r'(?=GAMMA)')]
        content = 'ALPHA abc BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, str(cst.content)
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1
        # multiple failures
        content = 'ALPHA acb BETA bad GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # there should be only two error messages
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 2

    def test_algorithmic_resume(self):
        lang = r"""
            document = block_A block_B
            @ block_A_resume = next_valid_letter()
            @ block_A_skip = next_valid_letter()
            block_A = "a" §"b" "c"
            block_B = "x" "y" "z"
            """
        proc = """
def next_valid_letter(text, start, end):
    L = len(text)
    end = min(L, max(L, end))
    while start < len(text):
        if str(text[start]) in 'abcxyz':
            return start, 0
        start += 1
    return -1, 0
"""
        parser = grammar_provider(lang, additional_code=proc)()
        tree = parser('ab*xyz')
        assert 'block_A' in tree and 'block_B' in tree
        assert tree.pick('ZOMBIE__')


    def test_skip_comment_on_resume(self):
        lang = r"""@literalws = right
            @ comment =  /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/  # Kommentare im C++-Stil
            document = block_A block_B
            @ block_A_resume = /(?=x)/
            block_A = "a" §"b" "c"
            block_B = "x" "y" "z"
        """
        def mini_suite(grammar):
            tree = grammar('abc/*x*/xyz')
            assert not tree.errors
            tree = grammar('abDxyz')
            mandatory_cont = (MANDATORY_CONTINUATION, MANDATORY_CONTINUATION_AT_EOF)
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont
            tree = grammar('abD/*x*/xyz')
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont
            tree = grammar('aD /*x*/ c /* a */ /*x*/xyz')
            assert len(tree.errors) == 1 and tree.errors[0].code in mandatory_cont

        # test regex-defined resume rule
        grammar = grammar_provider(lang)()
        mini_suite(grammar)

    def test_unambiguous_error_location(self):
        lang = r"""
            @ literalws   = right
            @ drop        = whitespace, strings  # drop strings and whitespace early

            @object_resume = /(?<=\})/

            json       = ~ value EOF
            value      = object | string 
            object     = "{" [ member { "," §member } ] "}"
            member     = string §":" value
            string     = `"` CHARACTERS `"` ~

            CHARACTERS = { /[^"\\]+/ }                  
            EOF      =  !/./        # no more characters ahead, end of file reached
            """
        test_case = """{
                "missing member": "abcdef",
            }"""
        gr = grammar_provider(lang)()
        cst = gr(test_case)
        assert any(err.code == MANDATORY_CONTINUATION for err in cst.errors)

    def test_bigfattest(self):
        gr = copy.deepcopy(get_ebnf_grammar())
        resume_notices_on(gr)
        cst = gr(EBNF_with_Errors)
        locations = []
        for error in cst.errors_sorted:
            locations.append((error.line, error.column))
        assert locations == [(36, 37), (37, 1), (47, 19), (51, 1), (53, 5),
                             (57, 1), (59, 27), (60, 1), (65, 1), (66, 1)]

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())

