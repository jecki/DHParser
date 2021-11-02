#!/usr/bin/env python3

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

import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

try:
    import regex as re
except ImportError:
    import re

from DHParser.dsl import create_parser
from DHParser.error import Error, ERROR, add_source_locations
from DHParser.preprocess import gen_neutral_srcmap_func
from DHParser.toolkit import linebreaks, line_col


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
            assert False, "ValueError expected for negative position, not %i, %i." % (l, c)
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

    def test_boundary_cases(self):
        err = Error('Error-Test', 1, ERROR)
        source_mapping = gen_neutral_srcmap_func(' ')
        add_source_locations([err], source_mapping)

        err = Error('Error-Test', 2, ERROR)
        try:
            add_source_locations([err], source_mapping)
            assert False, "Error-location outside text. ValueError was expected but not raised"
        except ValueError:
            pass


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
