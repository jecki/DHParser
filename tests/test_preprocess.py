#!/usr/bin/env python3

"""test_preprocess.py - tests of the preprocessor-module of DHParser

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
import platform
import shutil
import subprocess
import sys
import time

scriptpath = os.path.abspath(os.path.dirname(__file__) or '.')
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from functools import partial

from DHParser.configuration import set_config_value
from DHParser.dsl import grammar_provider
from DHParser import compile_source
from DHParser.preprocess import make_token, tokenized_to_original_mapping, source_map, \
    BEGIN_TOKEN, END_TOKEN, TOKEN_DELIMITER, PreprocessorResult, chain_preprocessors, \
    strip_tokens, gen_find_include_func, preprocess_includes, IncludeInfo, make_preprocessor
from DHParser.error import SourceMap, Error
from DHParser.toolkit import normalize_docstring, typing, re
from DHParser.testing import unique_name
from typing import Tuple, Dict, List


class TestMakeToken:
    def test_make_token1(self):
        tk = make_token("INDENTED_BLOCK", " " * 4)
        assert tk[0] == BEGIN_TOKEN
        assert tk[-1] == END_TOKEN
        d = tk.find(TOKEN_DELIMITER)
        assert 0 < d < len(tk) - 1
        assert tk[1:d] == "INDENTED_BLOCK"
        assert tk[d + 1:-1] == " " * 4

    def test_make_token2(self):
        tk = make_token("EMPTY_TOKEN")
        assert tk[0] == BEGIN_TOKEN
        assert tk[-1] == END_TOKEN
        d = tk.find(TOKEN_DELIMITER)
        assert 0 < d < len(tk) - 1
        assert tk[1:d] == "EMPTY_TOKEN"
        assert tk[d + 1:-1] == ""


class TestSourceMapping:
    code = "All persons are mortal AND Socrates is a person YIELDS Socrates is mortal"
    tokenized = code.replace('AND', make_token('CONJUNCTION', 'AND')) \
        .replace('YIELDS', make_token('IMPLICATION', 'YIELDS'))


    def test_tokenized_to_original_mapping(self):
        srcmap = tokenized_to_original_mapping(self.tokenized, self.code)
        positions, offsets = srcmap.positions, srcmap.offsets
        assert len(positions) == len(offsets)
        assert positions[0] == 0
        assert all(positions[i] < positions[i + 1] for i in range(len(positions) - 1))
        assert all(offsets[i] > offsets[i + 1] for i in range(len(offsets) - 2))
        assert offsets[-1] >= offsets[-2]
        assert self.tokenized.find('AND') == self.code.find('AND') + len('CONJUNCTION') + 2

    def test_bondary_cases(self):
        # position at the end of the file
        source = " "
        srcmap = tokenized_to_original_mapping(source, source)
        pos = source_map(1, srcmap)
        # empty file
        source =""
        srcmap = tokenized_to_original_mapping(source, source)
        pos = source_map(0, srcmap)


def tokenize_indentation(src: str) -> Tuple[str, List[Error]]:
    transformed = []
    indent_level = 0
    for line in src.split('\n'):
        indent = len(line) - len(line.lstrip()) if line.strip() else indent_level * 4
        assert indent % 4 == 0
        if indent > indent_level * 4:
            assert indent == (indent_level + 1) * 4, str(indent)  # indent must be 4 spaces
            indent_level += 1
            line = make_token('BEGIN_INDENT') + line
        elif indent <= (indent_level - 1) * 4:
            while indent <= (indent_level - 1) * 4:
                line = make_token('END_INDENT') + line
                indent_level -= 1
            assert indent == (indent_level + 1) * 4  # indent must be 4 spaces
        else:
            assert indent == indent_level * 4
        transformed.append(line)
    while indent_level > 0:
        transformed[-1] += make_token('END_INDENT')
        indent_level -= 1
    tokenized = '\n'.join(transformed)
    # print(prettyprint_tokenized(tokenized))
    return tokenized, []


preprocess_indentation = make_preprocessor(tokenize_indentation)


def preprocess_comments(src: str, src_name: str) -> PreprocessorResult:
    lines = src.split('\n')
    positions, offsets = [0], [0]
    pos = 0
    for i, line in enumerate(lines):
        comment_pos = line.find('#')
        if comment_pos >= 0:
            pos += comment_pos
            lines[i] = line[:comment_pos]
            positions.append(pos - offsets[-1])
            offsets.append(offsets[-1] + len(line) - comment_pos)
        pos += len(lines[i])
    positions.append(pos)
    offsets.append(offsets[-1])
    return PreprocessorResult(src, '\n'.join(lines),
                              partial(source_map, srcmap=SourceMap(src_name,
                                                                   positions,
                                                                   offsets,
                                                                   [src_name] * len(positions),
                                                                   {src_name: src})),
                              [])


class TestTokenParsing:
    ebnf = r"""
        @ tokens     = BEGIN_INDENT, END_INDENT
        @ whitespace = /[ \t]*/ 
        block       = { line | indentBlock }+
        line        = ~/[^\x1b\x1c\x1d\n]*\n/
        indentBlock = BEGIN_INDENT block END_INDENT
        """
    set_config_value('max_parser_dropouts', 3)
    grammar = grammar_provider(ebnf)()
    code = '\n' + normalize_docstring("""
        def func(x, y):
            if x > 0:         # a comment
                if y > 0:
                    print(x)  # another comment
                    print(y)
        """) + '\n'
    tokenized, _ = tokenize_indentation(code)
    srcmap = tokenized_to_original_mapping(tokenized, code)

    def verify_mapping(self, teststr, orig_text, preprocessed_text, mapping):
        mapped_pos = preprocessed_text.find(teststr)
        assert mapped_pos >= 0
        file_name, file_content, original_pos = mapping(mapped_pos)
        # original_pos = source_map(mapped_pos, self.srcmap)
        assert orig_text[original_pos:original_pos + len(teststr)] == teststr, \
            '"%s" (%i) wrongly mapped onto "%s" (%i)' % \
            (teststr, mapped_pos, orig_text[original_pos:original_pos + len(teststr)], original_pos)

    def test_strip_tokens(self):
        assert self.code == strip_tokens(self.tokenized)

    def test_parse_tokenized(self):
        cst = self.grammar(self.tokenized)
        assert not cst.error_flag

    def test_source_mapping_1(self):
        mapping = partial(source_map, srcmap=self.srcmap)
        self.verify_mapping("def func", self.code, self.tokenized, mapping)
        self.verify_mapping("x > 0:", self.code, self.tokenized, mapping)
        self.verify_mapping("if y > 0:", self.code, self.tokenized, mapping)
        self.verify_mapping("print(x)", self.code, self.tokenized, mapping)
        self.verify_mapping("print(y)", self.code, self.tokenized, mapping)

    def test_source_mapping_2(self):
        previous_index = 0
        L = len(self.code)
        for mapped_index in range(len(self.tokenized)):
            _, _, index = source_map(mapped_index, self.srcmap)
            assert previous_index <= index <= L, \
                "%i <= %i <= %i violated" % (previous_index, index, L)
            previous_index = index

    def test_non_token_preprocessor(self):
        _, tokenized, mapping, _ = preprocess_comments(self.code, 'no_uri')
        self.verify_mapping("def func", self.code, tokenized, mapping)
        self.verify_mapping("x > 0:", self.code, tokenized, mapping)
        self.verify_mapping("if y > 0:", self.code, tokenized, mapping)
        self.verify_mapping("print(x)", self.code, tokenized, mapping)
        self.verify_mapping("print(y)", self.code, tokenized, mapping)

    def test_chained_preprocessors(self):
        pchain = chain_preprocessors(preprocess_comments, preprocess_indentation)
        _, tokenized, mapping, _ = pchain(self.code, 'no_uri')
        self.verify_mapping("def func", self.code, tokenized, mapping)
        self.verify_mapping("x > 0:", self.code, tokenized, mapping)
        self.verify_mapping("if y > 0:", self.code, tokenized, mapping)
        self.verify_mapping("print(x)", self.code, tokenized, mapping)
        self.verify_mapping("print(y)", self.code, tokenized, mapping)

    def test_error_position(self):
        orig_src = self.code.replace('#', '\x1b')
        prepr = chain_preprocessors(preprocess_comments, preprocess_indentation)
        self.grammar.max_parser_dropouts__ = 3
        result, messages, syntaxtree = compile_source(orig_src, prepr, self.grammar,
                                                      lambda i: i, lambda i: i)
        for err in messages:
            if self.code[err.orig_pos] == "#":
                break
        else:
            assert False, "wrong error positions"


class TestHelpers:
    def test_generate_find_include_func(self):
        rx = re.compile(r'include\((?P<name>[^)\n]*)\)')
        find = gen_find_include_func(rx)
        info = find('''321include(sub.txt)xyz''', 0)
        assert info == IncludeInfo(3, 16, 'sub.txt')

    def test_generate_find_include_w_comments(self):
        rx = re.compile(r'include\((?P<name>[^)\n]*)\)')
        comment_rx = re.compile(r'#.*(?:\n|$)')
        find = gen_find_include_func(rx, comment_rx)
        test = '''a
        b # include(alpha)
        c include(beta)
        # include(gamma)'''
        info = find(test, 0)
        assert info.file_name == "beta"
        info = find(test, info.begin + info.length)
        assert info.begin < 0


def system(s: str) -> int:
    # return os.system(s)
    return subprocess.call(s, shell=True)


class TestIncludes:
    cwd = os.getcwd()

    def setup(self):
        os.chdir(scriptpath)
        # avoid race-condition
        counter = 10
        while counter > 0:
            try:
                self.dirname = unique_name('test_preprocess_data')
                os.mkdir(self.dirname)
                counter = 0
            except FileExistsError:
                time.sleep(0.5)
                counter -= 1
        os.chdir(os.path.join(scriptpath, self.dirname))

    def teardown(self):
        os.chdir(scriptpath)
        if os.path.exists(self.dirname) and os.path.isdir(self.dirname):
            shutil.rmtree(self.dirname)
        if os.path.exists(self.dirname) and not os.listdir(self.dirname):
            os.rmdir(self.dirname)
        os.chdir(TestIncludes.cwd)

    def create_files(self, files: Dict[str, str]):
        for name, content in files.items():
            with open(name, 'w', encoding='utf-8') as f:
                f.write(content)

    def test_simple_include(self):
        def perform(main, sub):
            self.create_files({'main.txt': main, 'sub.txt': sub})
            find_func = gen_find_include_func(r'include\((?P<name>[^)\n]*)\)')
            _, text, mapping, _ = preprocess_includes(None, 'main.txt', find_func)
            assert text == main.replace('include(sub.txt)', 'abc'), text
            for i in range(len(text)):
                name, offset, k = mapping(i)
                txt = main if name == 'main.txt' else sub
                assert text[i] == txt[k], f'{i},{k}: {text[i]} != {txt[k]} in {name}'

        perform('include(sub.txt)xyz', 'abc')
        perform('012include(sub.txt)xyz', 'abc')
        perform('012xyzinclude(sub.txt)', 'abc')
        perform('01include(sub.txt)2xyz', 'abc')

        perform('012include(sub.txt)xyzinclude(sub.txt)hij', 'abc')
        perform('012include(sub.txt)include(sub.txt)hij', 'abc')
        perform('include(sub.txt)include(sub.txt)hijinclude(sub.txt)', 'abc')
        perform('012include(sub.txt)hilinclude(sub.txt)include(sub.txt)', 'abc')

    def test_complex_include(self):
        def perform(**ensemble):
            self.create_files(ensemble)
            find_func = gen_find_include_func(r'#include\((?P<name>[^)\n]*)\)')
            _, text, mapping, _ = preprocess_includes(None, 'main', find_func)
            substrings = {}
            for k, v in reversed(list(ensemble.items())):
                for name, content in substrings.items():
                    v = v.replace(f'#include({name})', content)
                substrings[k] = v
            assert text == substrings['main']
            for i in range(len(text)):
                name, lbreaks, k = mapping(i)
                txt = ensemble[name]
                assert text[i] == txt[k], f'{i}: {text[i]} != {txt[k]} in {name}'

        perform(main = '#include(sub)xyz', sub='abc')
        perform(main = "ABC#include(sub1)DEF#include(sub2)HIJ",
                sub1 = "UVW#include(sub2)XYZ#include(sub2)",
                sub2 = "123")
        try:
            perform(main="ABC#include(sub1)DEF#include(sub2)HIJ",
                    sub1="UVW#include(sub2)XYZ#include(sub2)",
                    sub2="#include(sub1)")
            assert False, "ValueError expected"
        except ValueError:
            pass


if __name__ == "__main__":
    # tp = TestTokenParsing()
    # tp.setup()
    from DHParser.testing import runner

    runner("", globals())
