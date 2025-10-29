#!/usr/bin/env python
# A mini-DSL for a key value store

import re

from DHParser.dsl import create_parser, grammar_changed
from DHParser.parse import *

# specify the grammar of your DSL in EBNF-notation
grammar = r'''@ drop = whitespace, strings
key_store   = ~ { entry }
entry       = key "="~ value          # ~ means: insignificant whitespace 
key         = /[\w]+/~                  # Scanner-less parsing: Use regular
value       = /\"[^"\n]*\"/~          # expressions wherever you like'''

class KeyValueGrammar(Grammar):
    r"""Parser for a KeyValue document.

    Instantiate this class and then call the instance with the
    source code as argument in order to use the parser, e.g.:
        parser = KeyValue()
        syntax_tree = parser(source_code)
    """
    source_hash__ = "d6d82738894cbdaa5b14ba8f4254e666"
    disposable__ = re.compile('$.')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'[ \t]*(?:\n[ \t]*(?![ \t]*\n))?'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    value = Series(RegExp('\\"[^"\\n]*\\"'), dwsp__)
    key = Series(RegExp('[\\w]+'), dwsp__)
    entry = Series(key, Drop(Text("=")), dwsp__, value)
    key_store = Series(dwsp__, ZeroOrMore(entry))
    root__ = key_store

if grammar_changed(KeyValueGrammar, grammar):
    parser = create_parser(grammar, branding="KeyValue")
    raise AssertionError(
        "Grammar changed! Please, update your source code with:\n\n" \
        + parser.python_src__)

if __name__ == "__main__":
    parser = KeyValueGrammar()
    example = '''
        title    = "Odysee 2001"
        director = "Stanley Kubrick"'''
    print(parser(example).as_xml())

