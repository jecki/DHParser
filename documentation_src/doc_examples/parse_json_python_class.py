#!/usr/bin/env python

"""JSON-parser-example from the DHParser-manual"""

import sys, re

from DHParser.parse import Grammar, Forward, Whitespace, Drop, NegativeLookahead, \
    ZeroOrMore, RegExp, Option, TKN, DTKN, Text

class JSON_Grammar(Grammar):
    # Parser-names must be assigned explicitly by calling the Parser.names()-method
    # for all parsers that contain any of the operators + (Series), | (Alternative)
    # or * (Interlave) on the top-level of their definition.
    # For any other parsers, the name is assigned automatically and early enough
    # by class Grammar. (This has technical reasons.)
    disposable__ = re.compile(r'_\w+')
    _element = Forward()
    _dwsp = Drop(Whitespace(r'\s*'))
    _EOF = NegativeLookahead(RegExp('.'))
    EXP = (Text("E") | Text("e") + Option(Text("+") | Text("-")) + RegExp(r'[0-9]+')).name('EXP')
    DOT = Text(".")
    FRAC = (DOT + RegExp(r'[0-9]+')).name('FRAC')
    NEG = Text("-")
    INT = (Option(NEG) + RegExp(r'[1-9][0-9]+') | RegExp(r'[0-9]')).name('INT')
    HEX = RegExp(r'[0-9a-fA-F][0-9a-fA-F]')
    UNICODE = (DTKN("\\u") + HEX + HEX).name('unicode')
    ESCAPE = RegExp('\\\\[/bnrt\\\\]') | UNICODE
    PLAIN = RegExp('[^"\\\\]+')
    _CHARACTERS = ZeroOrMore(PLAIN | ESCAPE)
    null = TKN("null")
    false = TKN("false")
    true = TKN("true")
    _bool = true | false
    number = (INT + Option(FRAC) + Option(EXP) + _dwsp).name('number')
    string = (Text('"') + _CHARACTERS + Text('"') + _dwsp).name('string')
    array = (DTKN("[") + Option(_element + ZeroOrMore(DTKN(",") + _element)) + DTKN("]")).name('array')
    member = (string + DTKN(":") + _element).name('member')
    json_object = (DTKN("{") + member +  ZeroOrMore(DTKN(",") + member) + DTKN("}")).name('json_object')
    _element.set(json_object | array | string | number | _bool | null)
    json = (_dwsp + _element + _EOF).name('json')
    root__ = json

json_parser = JSON_Grammar()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            json_text = f.read()
    else:
        # just a test
        json_text = '{ "one": 1, "two": 2 }'
    syntax_tree = json_parser(json_text)
    print(syntax_tree.serialize(how='indented'))
