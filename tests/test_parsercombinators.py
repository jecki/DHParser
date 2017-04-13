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
from DHParser.DSLsupport import compileEBNF

WRITE_LOGS = True


class TestLeftRecursion:
    mini_language1 = """
        @ whitespace = linefeed
        formula = expr "." 
        expr = expr ("+"|"-") term | term
        term = term ("*"|"/") factor | factor
        factor = /[0-9]+/
        # example:  "5 + 3 * 4"
        """

    def setup(self):
        self.minilang_parser1 = compileEBNF(self.mini_language1)()

    def test_compile_mini_language(self):
        assert self.minilang_parser1

    def test_direct_left_recursion(self):
        syntax_tree = self.minilang_parser1.parse("5 + 3 * 4")
        assert not syntax_tree.collect_errors()
        if WRITE_LOGS:
            syntax_tree.log("test_LeftRecursion_direct", '.cst')
            self.minilang_parser1.log_parsing_history("test_LeftRecursion_direct")


    def test_indirect_left_recursion(self):
        pass


if __name__ == "__main__":
    from run import run_tests
    run_tests("TestLeftRecursion", globals())