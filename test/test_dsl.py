#!/usr/bin/python3

"""test_dsl.py - tests of the dsl-module of DHParser 


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
sys.path.extend(['../', './'])

from DHParser.dsl import compile_on_disk, run_compiler, compileDSL, compileEBNF


ARITHMETIC_EBNF = """
    @ whitespace = linefeed
    formula = [ //~ ] expr
    expr = expr ("+"|"-") term | term
    term = term ("*"|"/") factor | factor
    factor = /[0-9]+/~
    # example:  "5 + 3 * 4"
    """

class TestCompileFunctions:
    def test_compileEBNF(self):
        parser_src = compileEBNF(ARITHMETIC_EBNF, source_only=True)
        print(parser_src)

class TestCompilerGeneration:
    trivial_lang = """
        text = { word | WSPC } "."
        word = /\w+/
        WSPC = /\s+/
        """
    tmp = 'tmp/' if os.path.isdir('tmp') else ('test/tmp/')
    trivial_text = """Es war ein König in Thule."""
    grammar_name = tmp + "TestCompilerGeneration.ebnf"
    compiler_name = tmp + "TestCompilerGeneration_compiler.py"
    text_name = tmp + "TestCompilerGeneration_text.txt"
    result_name = tmp + "TestCompilerGeneration_text.xml"

    def setup(self):
        with open(self.grammar_name, "w") as f:
            f.write(self.trivial_lang)
        with open(self.text_name, "w") as f:
            f.write(self.trivial_text)

    def teardown(self):
        for name in (self.grammar_name, self.compiler_name, self.text_name, self.result_name):
            if os.path.exists(name):
                os.remove(name)
        pass

    def test_compiling_functions(self):
        # test if cutting and reassembling of compiler suite works:
        errors = compile_on_disk(self.grammar_name)
        assert not errors
        with open(self.compiler_name, 'r') as f:
            compiler_suite = f.read()
        errors = compile_on_disk(self.grammar_name)
        assert not errors
        with open(self.compiler_name, 'r') as f:
            compiler_suite_2nd_run = f.read()
        assert compiler_suite == compiler_suite_2nd_run

        # test compiling with a generated compiler suite
        errors = compile_on_disk(self.text_name, self.compiler_name)
        assert not errors, str(errors)
        assert os.path.exists(self.result_name)
        with open(self.result_name, 'r') as f:
            output = f.read()

        # test compiling in memory
        result = run_compiler(self.trivial_text, self.compiler_name)
        assert output == result.as_xml(), str(result)

        sys.path.append(self.tmp)
        from TestCompilerGeneration_compiler import compile_TestCompilerGeneration
        result, errors, ast = compile_TestCompilerGeneration(self.trivial_text)


if __name__ == "__main__":
    from run import runner
    runner("TestCompileFunctions", globals())