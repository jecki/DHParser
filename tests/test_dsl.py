#!/usr/bin/env python3

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

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
LOG_DIR = os.path.abspath(os.path.join(scriptpath, "LOGS"))

from DHParser.parse import Grammar, mixin_comment
from DHParser import Compiler
from DHParser.error import is_error
from DHParser.dsl import compile_on_disk, run_compiler, compileEBNF, grammar_provider, \
    load_compiler_suite, create_parser
from DHParser.toolkit import concurrent_ident, re

ARITHMETIC_EBNF = """
    @ literalws = right
    @ whitespace = linefeed
    formula = [ //~ ] expr
    expr = expr ("+"|"-") term | term
    term = term ("*"|"/") factor | factor
    factor = /[0-9]+/~
    # example:  "5 + 3 * 4"
    """

class TestCompileFunctions:
    def test_compileEBNF(self):
        parser_src = compileEBNF(ARITHMETIC_EBNF)
        assert isinstance(parser_src, str), str(type(parser_src))
        assert parser_src.find('DSLGrammar') >= 0
        parser_src = compileEBNF(ARITHMETIC_EBNF, branding="CustomDSL")
        assert isinstance(parser_src, str), str(type(parser_src))
        assert parser_src.find('CustomDSLGrammar') >= 0
        factory = grammar_provider(ARITHMETIC_EBNF, branding="TestDSL")
        assert callable(factory)
        parser = factory()
        result = parser("5 + 3 * 4")
        assert not is_error(result.error_flag), str(result.errors_sorted)
        result = parser("5A + 4B ** 4C")
        assert is_error(result.error_flag)


class TestCompilerGeneration:
    trivial_lang = r"""
        text = { word | WSPC } "." [/\s/]
        word = /\w+/
        WSPC = /\s+/
        """

    def setup(self):
        self.tmpname = 'tmp_' + concurrent_ident()
        self.tmp = os.path.join('test', self.tmpname) if os.path.isdir('test/') else self.tmpname
        self.trivial_text = u"""Es war ein Koenig in Thule.\n"""
        self.grammar_name = os.path.join(self.tmp, "TestCompilerGeneration.ebnf")
        self.compiler_name = os.path.join(self.tmp, "TestCompilerGenerationParser.py")
        self.text_name = os.path.join(self.tmp, "TestCompilerGeneration_text.txt")
        self.result_name = os.path.join(self.tmp, "TestCompilerGeneration_text.xml")
        if not os.path.exists(self.tmp):
            os.mkdir(self.tmp)
        with open(self.grammar_name, "w") as f:
            f.write(self.trivial_lang)
        with open(self.text_name, "w") as f:
            f.write(self.trivial_text)

    def teardown(self):
        for name in (self.grammar_name, self.compiler_name, self.text_name, self.result_name):
            if os.path.exists(name):
                os.remove(name)
        if os.path.exists(LOG_DIR):
            files = os.listdir(LOG_DIR)
            flag = False
            for file in files:
                if file.startswith('TestCompilerGenerationCompiler') or file == "info.txt":
                    os.remove(os.path.join(LOG_DIR, file))
                else:
                    flag = True
            if not flag:
                os.rmdir(LOG_DIR)
        pycachedir = os.path.join(self.tmp,'__pycache__')
        if os.path.exists(pycachedir):
            for fname in os.listdir(pycachedir):
                os.remove(os.path.join(pycachedir, fname))
            os.rmdir(pycachedir)
        if os.path.exists(self.tmp):
            os.rmdir(self.tmp)


    def test_load_compiler_suite(self):
        src = compileEBNF(self.trivial_lang, "Trivial")
        scanner, parser, transformer, compiler = load_compiler_suite(src)
        scanner = scanner()
        parser = parser()
        transformer = transformer()
        compiler = compiler()
        assert callable(scanner)
        assert isinstance(parser, Grammar)
        assert callable(transformer)
        assert isinstance(compiler, Compiler)

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
        diff = ''.join([a for a, b in zip(compiler_suite_2nd_run, compiler_suite) if a != b])
        # differences should only be ID-Numbers
        assert not diff or diff.isnumeric()
        # test compiling with a generated compiler suite
        # assert is_filename(self.text_name)
        errors = compile_on_disk(self.text_name, compiler_suite=self.compiler_name)
        assert not errors, str(errors)
        assert os.path.exists(self.result_name)
        with open(self.result_name, 'r') as f:
            output = f.read()

        # test compiling in memory
        result = run_compiler(self.trivial_text, self.compiler_name)
        assert output == result.as_xml(), str(result)

        sys.path.append(self.tmp)
        from TestCompilerGenerationParser import compile_src
        result, errors = compile_src(self.trivial_text)

    def test_readme_example(self):
        grammar = r'''@ drop = whitespace, strings
            key_store   = ~ { entry }
            entry       = key "="~ value
            key         = /\w+/~                  # Scannerless parsing: Use regular
            value       = /\"[^"\n]*\"/~          # expressions wherever you like
        '''
        parser = create_parser(grammar)
        text = '''
            title    = "Odysee 2001"
            director = "Stanley Kubrick"
            '''
        result = parser(text)
        assert not result.errors, str(result.errors)


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
