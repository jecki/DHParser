#!/usr/bin/python3

"""test_error.py - tests of the error-handling-module of DHParser


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

import sys

sys.path.extend(['../', './'])

try:
    import regex as re
except ImportError:
    import re

from DHParser.error import linebreaks, line_col, Error
from DHParser.dsl import grammar_provider,  CompilationError


class TestErrorSupport:
    def mini_suite(self, s, lbreaks, offset):
        l, c = line_col(lbreaks, 0)
        assert (l, c) == (1, 1), str((l, c))
        l, c = line_col(lbreaks, 0 + offset)
        assert (l, c) == (1 + offset, 1), str((l, c))
        l, c = line_col(lbreaks, 1 + offset)
        assert (l, c) == (1 + offset, 2), str((l, c))
        l, c = line_col(lbreaks, 9 + offset)
        assert (l, c) == (1 + offset, 10), str((l, c))
        l, c = line_col(lbreaks, 10 + offset)
        assert (l, c) == (2 + offset, 1), str((l, c))
        l, c = line_col(lbreaks, 18 + offset)
        assert (l, c) == (2 + offset, 9), str((l, c))
        l, c = line_col(lbreaks, 19 + offset)
        assert (l, c) == (2 + offset, 10), str((l, c))
        try:
            l, c = line_col(lbreaks, -1)
            assert False, "ValueError expected for negative position."
        except ValueError:
            pass
        try:
            l, c = line_col(lbreaks, len(s) + 1)
            assert False, "ValueError expected for postion > pos(EOF)+1."
        except ValueError:
            pass

    def test_line_col(self):
        s = "123456789\n123456789"
        self.mini_suite(s, linebreaks(s), 0)
        s = "\n123456789\n123456789"
        self.mini_suite(s, linebreaks(s), 1)
        s = "123456789\n123456789\n"
        self.mini_suite(s, linebreaks(s), 0)
        s = "\n123456789\n123456789\n"
        self.mini_suite(s, linebreaks(s), 1)


class TestCuratedErrors:
    """
    Cureted Errors replace existing errors with alternative
    error codes and messages that are more helptful to the user.
    """
    def test_user_error_declaration(self):
        lang = """
            document = series | /.*/
            series = "X" | head §"C" "D"
            head = "A" "B"
            @series_error = "a user defined error message"
            """
        try:
            parser = grammar_provider(lang)()
            assert False, "Error definition after symbol definition should fail!"
        except CompilationError as e:
            pass

    def test_curated_mandatory_continuation(self):
        lang = """
            document = series | /.*/
            @series_error = "a user defined error message"
            series = "X" | head §"C" "D"
            head = "A" "B"
            """
        # from DHParser.dsl import compileDSL
        # from DHParser.preprocess import nil_preprocessor
        # from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
        # grammar_src = compileDSL(lang, nil_preprocessor, get_ebnf_grammar(),
        #                          get_ebnf_transformer(), get_ebnf_compiler("test", lang))
        # print(grammar_src)
        parser = grammar_provider(lang)()
        st = parser("X");  assert not st.error_flag
        st = parser("ABCD");  assert not st.error_flag
        st = parser("A_CD");  assert not st.error_flag
        st = parser("AB_D");  assert st.error_flag
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION
        assert st.collect_errors()[0].message == "a user defined error message"
        # transitivity of mandatory-operator
        st = parser("ABC_");  assert st.error_flag
        assert st.collect_errors()[0].code == Error.MANDATORY_CONTINUATION
        assert st.collect_errors()[0].message == "a user defined error message"


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
