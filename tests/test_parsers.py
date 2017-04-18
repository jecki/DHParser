#!/usr/bin/python3

"""test_parsers.py - tests of the parsercombinators-module 
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
from DHParser.parsers import full_compilation
from DHParser.ebnf import EBNFGrammar, EBNF_ASTPipeline, EBNFCompiler
from DHParser.dsl import compileEBNF, DHPARSER_IMPORTS

WRITE_LOGS = True


class TestInfiLoopsAndRecursion:
    def test_direct_left_recursion(self):
        minilang = """
            @ whitespace = linefeed
            formula = [ //~ ] expr
            expr = expr ("+"|"-") term | term
            term = term ("*"|"/") factor | factor
            factor = /[0-9]+/~
            # example:  "5 + 3 * 4"
            """
        snippet = "5 + 3 * 4"
        parser = compileEBNF(minilang)()
        assert parser
        syntax_tree = parser.parse(snippet)
        assert not syntax_tree.collect_errors()
        assert snippet == str(syntax_tree)
        if WRITE_LOGS:
            syntax_tree.log("test_LeftRecursion_direct", '.cst')
            # self.minilang_parser1.log_parsing_history("test_LeftRecursion_direct")

    def test_indirect_left_recursion(self):
        pass

    def test_inifinite_loops(self):
        minilang = """not_forever = { // } \n"""
        snippet = " "
        parser = compileEBNF(minilang)()
        syntax_tree = parser.parse(snippet)
        assert syntax_tree.error_flag
        # print(syntax_tree.collect_errors())


class TestRegex:
    def test_multilineRegex(self):
        mlregex = r"""
        regex =  /\w+    # one or more alphabetical characters including the underscore
                  [+]    # followed by a plus sign
                  \w*    # possibly followed by more alpha chracters/
        """
        result, messages, syntax_tree = full_compilation(mlregex, None,
                                                         EBNFGrammar(), EBNF_ASTPipeline,
                                                         EBNFCompiler('MultilineRegexTest'))
        assert result
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        node, rest = parser.regex('abc+def')
        assert rest == ''
        assert node.parser.name == "regex"
        assert str(node) == 'abc+def'

    def test_token(self):
        tokenlang = r"""
            @whitespace = linefeed
            lang        = "" begin_token {/\w+/ ""} end_token
            begin_token = "\begin{document}"
            end_token   = "\end{document}"
            """
        testdoc = r"""
            \begin{document}
            test
            \end{document}
            """
        result, messages, syntax_tree = full_compilation(tokenlang, None,
                                                         EBNFGrammar(), EBNF_ASTPipeline, EBNFCompiler("TokenTest"))
        assert result
        assert not messages
        parser = compile_python_object(DHPARSER_IMPORTS + result, '\w+Grammar$')()
        result = parser.parse(testdoc)
        # parser.log_parsing_history("test.log")
        assert not result.error_flag


if __name__ == "__main__":
    from run import run_tests

    run_tests("", globals())
