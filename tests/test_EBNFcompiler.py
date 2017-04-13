#!/usr/bin/python3

"""test_EBNFcompiler.py - tests of the EBNFcompiler-module of DHParser 
                             

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
sys.path.append(os.path.abspath('../../'))
from DHParser.DSLsupport import compileEBNF


WRITE_LOGS = True


class TestDirectives:
    mini_language = """
        expression =  term  { ("+" | "-") term }
        term       =  factor  { ("*" | "/") factor }
        factor     =  constant | "("  expression  ")"
        constant   =  digit { digit } [ //~ ]
        digit      = /0/ | /1/ | /2/ | /3/ | /4/ | /5/ | /6/ | /7/ | /8/ | /9/ 
        """

    def test_whitespace_linefeed(self):
        lang = "@ whitespace = linefeed\n" + self.mini_language
        MinilangParser = compileEBNF(lang)
        parser = MinilangParser()
        assert parser
        syntax_tree = parser.parse("3 + 4 * 12")
        parser.log_parsing_history("WSP")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n * 12")
        parser.log_parsing_history("WSPLF")
        assert not syntax_tree.collect_errors()

    def test_whitespace_standard(self):
        lang = "@ whitespace = standard\n" + self.mini_language
        parser = compileEBNF(lang)()
        assert parser
        syntax_tree = parser.parse("3 + 4 * 12")
        assert not syntax_tree.collect_errors()
        syntax_tree = parser.parse("3 + 4 \n * 12")
        assert syntax_tree.collect_errors()

class TestPopRetrieve:
    mini_language = """
        document       = { text | codeblock }
        codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
        delimiter      = delimiter_sign
        delimiter_sign = /`+/
        text           = /[^`]+/ 
        """

    def setup(self):
        self.minilang_parser = compileEBNF(self.mini_language)()

    def test_compile_mini_language(self):
        assert self.minilang_parser

    def test_single_line(self):
        teststr = "Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ende"
        syntax_tree = self.minilang_parser.parse(teststr)
        assert not syntax_tree.collect_errors()
        if WRITE_LOGS:
            syntax_tree.log("test_PopRetrieve_single_line", '.cst')
            # self.minilang_parser.log_parsing_history("test_PopRetrieve_single_line")

    def test_multi_line(self):
        teststr = """
            Anfang ```code block `` <- keine Ende-Zeichen ! ``` Ebde

            Absatz ohne ``` codeblock, aber
            das stellt sich erst am Ende herause...

            Mehrzeliger ```code block
            """
        syntax_tree = self.minilang_parser.parse(teststr)
        assert not syntax_tree.collect_errors()
        if WRITE_LOGS:
            syntax_tree.log("test_PopRetrieve_multi_line", '.cst')
            # self.minilang_parser.log_parsing_history("test_PopRetrieve_multi_line")


if __name__ == "__main__":
    from run import run_tests
    run_tests("TestDirectives TestPopRetrieve", globals())
