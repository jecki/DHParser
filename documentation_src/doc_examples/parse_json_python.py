#!/usr/bin/env python

"""JSON-parser-example from the DHParser-manual"""

import sys, re

from DHParser.parse import Grammar, Forward, Whitespace, Drop, NegativeLookahead, \
    ZeroOrMore, RegExp, Option, TKN, DTKN, Text

_element = Forward().name('_element', disposable=True)
_dwsp = Drop(Whitespace(r'\s*'))
_EOF = NegativeLookahead(RegExp('.'))
EXP = (Text("E") | Text("e") + Option(Text("+") | Text("-")) + RegExp(r'[0-9]+')).name('EXP')
DOT = Text(".").name('DOT')
FRAC = (DOT + RegExp(r'[0-9]+')).name('FRAC')
NEG = Text("-").name('NEG')
INT = (Option(NEG) + RegExp(r'[1-9][0-9]+') | RegExp(r'[0-9]')).name('INT')
HEX = RegExp(r'[0-9a-fA-F][0-9a-fA-F]').name('HEX')
UNICODE = (DTKN("\\u") + HEX + HEX).name('unicode')
ESCAPE = (RegExp('\\\\[/bnrt\\\\]') | UNICODE).name('ESCAPE')
PLAIN = RegExp('[^"\\\\]+').name('PLAIN')
_CHARACTERS = ZeroOrMore(PLAIN | ESCAPE)
null = TKN("null").name('null')
false = TKN("false").name('false')
true = TKN("true").name('true')
_bool = true | false
number = (INT + Option(FRAC) + Option(EXP) + _dwsp).name('number')
string = (Text('"') + _CHARACTERS + Text('"') + _dwsp).name('string')
array = (DTKN("[") + Option(_element + ZeroOrMore(DTKN(",") + _element)) + DTKN("]")).name('array')
member = (string + DTKN(":") + _element).name('member')
json_object = (DTKN("{") + member +  ZeroOrMore(DTKN(",") + member) + DTKN("}")).name('json_object')
_element.set(json_object | array | string | number | _bool | null)
json = (_dwsp + _element + _EOF).name('json')

json_parser = Grammar(json)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            json_text = f.read()
    else:
        # just a test
        json_text = '{ "one": 1, "two": 2 }'
    syntax_tree = json_parser(json_text)
    print(syntax_tree.serialize(how='indented'))
