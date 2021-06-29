#!/usr/bin/env python

"""JSON-parser-example from the DHParser-manual"""

from DHParser.dsl import create_parser

json_grammar = r"""
    @literalws  = right
    @drop       = whitespace, strings
    @disposable = /_\w+/

    json        = ~ _element _EOF
    _element    = object | array | string | number | _bool | null
    object      = "{" member { "," §member } §"}"
    member      = string §":" _element
    array       = "[" [ _element { "," _element } ] §"]"
    string      = `"` §_CHARACTERS `"` ~
    number      = INT [ FRAC ] [ EXP ] ~
    _bool       = true | false
    true        = `true` ~
    false       = `false` ~
    null        = "null"

    _CHARACTERS = { PLAIN | ESCAPE }
    PLAIN       = /[^"\\]+/
    ESCAPE      = /\\[\/bnrt\\]/ | UNICODE
    UNICODE     = "\u" HEX HEX
    HEX         = /[0-9a-fA-F][0-9a-fA-F]/

    INT         = [NEG] ( /[1-9][0-9]+/ | /[0-9]/ )
    NEG         = `-`
    FRAC        = DOT /[0-9]+/
    DOT         = `.`
    EXP         = (`E`|`e`) [`+`|`-`] /[0-9]+/

    _EOF        =  !/./
    """

json_parser = create_parser(json_grammar, 'JSON')

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            json_text = f.read()
    else:
        # just a test
        json_text = '{ "one": 1, "two": 2 }'
    syntax_tree = json_parser(json_text)
    print(syntax_tree.serialize(how='indented'))
