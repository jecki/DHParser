#!/usr/bin/python3

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

# import sys
# sys.path.append('../')

from DHParser.dsl import grammar_provider
from DHParser.preprocess import make_token, tokenized_to_original_mapping, source_map, \
    BEGIN_TOKEN, END_TOKEN, TOKEN_DELIMITER
from DHParser.toolkit import lstrip_docstring


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
    def setup(self):
        self.code = "All persons are mortal AND Socrates is a person YIELDS Socrates is mortal"
        self.tokenized = self.code.replace('AND', make_token('CONJUNCTION', 'AND')) \
            .replace('YIELDS', make_token('IMPLICATION', 'YIELDS'))

    def test_tokenized_to_original_mapping(self):
        srcmap = tokenized_to_original_mapping(self.tokenized)
        positions, offsets = srcmap.positions, srcmap.offsets
        assert len(positions) == len(offsets)
        assert positions[0] == 0
        assert all(positions[i] < positions[i + 1] for i in range(len(positions) - 1))
        assert all(offsets[i] > offsets[i + 1] for i in range(len(offsets) - 1))
        assert self.tokenized.find('AND') == self.code.find('AND') + len('CONJUNCTION') + 2


class TestTokenParsing:
    def preprocess_indentation(self, src: str) -> str:
        transformed = []
        indent_level = 0
        for line in self.code.split('\n'):
            indent = len(line) - len(line.lstrip()) if line.strip() else indent_level * 4
            assert indent % 4 == 0
            if indent > indent_level * 4:
                assert indent == (indent_level + 1) * 4, str(indent)  # indent must be 4 spaces
                indent_level += 1
                transformed.append(make_token('BEGIN_INDENT'))
            elif indent <= (indent_level - 1) * 4:
                while indent <= (indent_level - 1) * 4:
                    transformed.append(make_token('END_INDENT'))
                    indent_level -= 1
                assert indent == (indent_level + 1) * 4  # indent must be 4 spaces
            else:
                assert indent == indent_level * 4
            transformed.append(line)
        while indent_level > 0:
            transformed.append(make_token('END_INDENT'))
            indent_level -= 1
        tokenized = '\n'.join(transformed)
        # print(pp_tokenized(tokenized))
        return tokenized

    def setup(self):
        self.ebnf = r"""
            @ tokens     = BEGIN_INDENT, END_INDENT
            @ whitespace = /[ \t]*/ 
            block       = { line | indentBlock }+
            line        = ~/[^\x1b\x1c\x1d\n]*\n/
            indentBlock = BEGIN_INDENT block END_INDENT
            """
        self.grammar = grammar_provider(self.ebnf)()
        self.code = lstrip_docstring("""
            def func(x, y):
                if x > 0:
                    if y > 0:
                        print(x)
                        print(y)
            """)
        self.tokenized = self.preprocess_indentation(self.code)
        self.srcmap = tokenized_to_original_mapping(self.tokenized)

    def verify_mapping(self, teststr, orig_text, preprocessed_text):
        mapped_pos = preprocessed_text.find(teststr)
        assert mapped_pos >= 0
        original_pos = source_map(mapped_pos, self.srcmap)
        assert orig_text[original_pos:original_pos + len(teststr)] == teststr, \
            '"%s" (%i) wrongly mapped onto "%s" (%i)' % \
            (teststr, mapped_pos, orig_text[original_pos:original_pos + len(teststr)], original_pos)

    def test_parse_tokenized(self):
        cst = self.grammar(self.tokenized)
        # for e in cst.collect_errors(self.tokenized):
        #     print(e.visualize(self.tokenized) + str(e))
        #     print()
        assert not cst.error_flag

    def test_source_mapping(self):
        self.verify_mapping("def func", self.code, self.tokenized)
        self.verify_mapping("x > 0:", self.code, self.tokenized)
        self.verify_mapping("if y > 0:", self.code, self.tokenized)
        self.verify_mapping("print(x)", self.code, self.tokenized)
        self.verify_mapping("print(y)", self.code, self.tokenized)


if __name__ == "__main__":
    # tp = TestTokenParsing()
    # tp.setup()
    from DHParser.testing import runner

    runner("", globals())
