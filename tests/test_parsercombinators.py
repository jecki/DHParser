#!/usr/bin/python3

"""test_parsercombinators.py - tests of the parsercombinators-module 
                               of DHParser 


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
from DHParser.toolkit import compile_python_object
from DHParser.parsercombinators import full_compilation
from DHParser.EBNFcompiler import EBNFGrammar, EBNF_ASTPipeline, EBNFCompiler
from DHParser.DSLsupport import compileEBNF, DHPARSER_IMPORTS

WRITE_LOGS = True


class TestLeftRecursion:
    mini_language1 = """
        @ whitespace = linefeed
        formula = [ //~ ] expr
        expr = expr ("+"|"-") term | term
        term = term ("*"|"/") factor | factor
        factor = /[0-9]+/~
        # example:  "5 + 3 * 4"
        """

    def setup(self):
        self.minilang_parser1 = compileEBNF(self.mini_language1)()

    def test_compile_mini_language(self):
        assert self.minilang_parser1

    def test_direct_left_recursion(self):
        snippet = "5 + 3 * 4"
        syntax_tree = self.minilang_parser1.parse(snippet)
        assert not syntax_tree.collect_errors()
        assert snippet == str(syntax_tree)
        if WRITE_LOGS:
            syntax_tree.log("test_LeftRecursion_direct", '.cst')
            # self.minilang_parser1.log_parsing_history("test_LeftRecursion_direct")

    def test_indirect_left_recursion(self):
        pass


class TestRegex:
    def test_multilineRegex(self):
        mlregex = r"""
        regex =  /\w+    # one or more alphabetical characters including the underscore
                  [+]    # followed by a plus sign
                  \w*    # possibly followed by more alpha chracters/
        """
        result, messages, syntax_tree = full_compilation(mlregex, EBNFGrammar(), EBNF_ASTPipeline,
                                                         EBNFCompiler('MultilineRegexTest'))
        assert result is not None, messages
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        node, rest = parser.regex('abc+def')
        assert rest == ''
        assert node.parser.name == "regex"
        assert str(node) == 'abc+def'


if __name__ == "__main__":
    from run import run_tests

    run_tests("TestRegex", globals())
