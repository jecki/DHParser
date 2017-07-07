#!/usr/bin/python3

"""LatexParser.py - Parser for LaTeX documents


Copyright 2016  by Eckhart Arnold

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Module latex_parser defines a parser for LaTeX files based on parser
combinators (see module parser_combinators).
"""

import os
import sys

sys.path.append(os.path.abspath('../'))


from ParserCombinators import Alternative, Forward, Optional, RegExp, \
    Sequence, Token, Required, ZeroOrMore, parse


doc = Forward()
configDoc = Forward()

text = RegExp("text", r'(?:[^\\\{\}%\n]|\n(?!\n))+')
configText = RegExp("configText", r'[^\\\{\}\[\]%]+')

group = Sequence("group", Token('{'), doc, Required(Token('}')))
config = Sequence("config", Token('['), doc, Required(Token(']')))
comment = RegExp("comment", r'( *%.*\n)+')
gap = RegExp("gap", r'\n\n+')

commandToken = RegExp("commandToken", r'\\\\?(?!(end\W)|(begin\W))[^\\\{\}\[\]%\s]*')  # r'\\\\?(?!end )[^\\\{\}\[\]%\s]*'

commandConfig = Sequence("commandConfig", Optional(None, comment), config)
commandGroup = Sequence("commandGroup", Optional(None, comment), group)

command = Sequence("command",
                   commandToken,
                   Optional("head", commandConfig),
                   ZeroOrMore("tail", commandGroup))

anonymousEnv = Sequence("anonymousEnv", Token('{'), doc, Required(Token('}')))

envBegin = Sequence("envBegin",
                    RegExp("head", r'\\begin\{\w+\}'),
                    ZeroOrMore("tail", commandGroup))
envEnd = RegExp("envEnd", r'\\end\{\w+\}')
environment = Sequence("environment", envBegin, doc, Required(envEnd))

configDoc.set(ZeroOrMore("configDoc", Alternative(None, command, group, configText)))
doc.set(ZeroOrMore("doc", Alternative(None, environment, anonymousEnv, command, comment, text, gap)))


if __name__ == "__main__":
    def test(file_name):
        print(file_name)
        with open(file_name) as f:
            latex_file = f.read()
        result = parse(latex_file, doc)
        assert str(result) == latex_file or result.collect_errors()
        return result


    assert str(doc) == str(doc)
    print(doc)

    result = test('testdata/testdoc1.tex')
    # result = test('testdata/testdoc2.tex')
    # result = test('testdata/testerror.tex')
    print(result.as_sxpr())
    print(result.collect_errors())
