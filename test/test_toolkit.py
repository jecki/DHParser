#!/usr/bin/python3

"""test_toolkit.py - tests of the toolkit-module of DHParser


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

import concurrent.futures
import os
import sys
try:
    import regex as re
except ImportError:
    import re

sys.path.extend(['../', './'])

from DHParser.toolkit import load_if_file, logging, log_dir, is_logging, linebreaks, line_col


class TestErrorSupport:
    def mini_suite(self, s, data, offset):
        l, c = line_col(data, 0)
        assert (l, c) == (1, 1), str((l, c))
        l, c = line_col(data, 0 + offset)
        assert (l, c) == (1 + offset, 1), str((l, c))
        l, c = line_col(data, 1 + offset)
        assert (l, c) == (1 + offset, 2), str((l, c))
        l, c = line_col(data, 9 + offset)
        assert (l, c) == (1 + offset, 10), str((l, c))
        l, c = line_col(data, 10 + offset)
        assert (l, c) == (2 + offset, 1), str((l, c))
        l, c = line_col(data, 18 + offset)
        assert (l, c) == (2 + offset, 9), str((l, c))
        l, c = line_col(data, 19 + offset)
        assert (l, c) == (2 + offset, 10), str((l, c))
        try:
            l, c = line_col(data, -1)
            assert False, "ValueError expected for negative position."
        except ValueError:
            pass
        try:
            l, c = line_col(data, len(s) + 1)
            assert False, "ValueError expected for postion > pos(EOF)+1."
        except ValueError:
            pass

    def test_line_col(self):
        s = "123456789\n123456789"
        self.mini_suite(s, s, 0)
        s = "\n123456789\n123456789"
        self.mini_suite(s, s, 1)
        s = "123456789\n123456789\n"
        self.mini_suite(s, s, 0)
        s = "\n123456789\n123456789\n"
        self.mini_suite(s, s, 1)

    def test_line_col_bisect(self):
        s = "123456789\n123456789"
        self.mini_suite(s, linebreaks(s), 0)
        s = "\n123456789\n123456789"
        self.mini_suite(s, linebreaks(s), 1)
        s = "123456789\n123456789\n"
        self.mini_suite(s, linebreaks(s), 0)
        s = "\n123456789\n123456789\n"
        self.mini_suite(s, linebreaks(s), 1)


class TestLoggingAndLoading:
    filename = "tmp/test.py" if os.path.isdir('tmp') else "test/tmp/test.py"
    code1 = "x = 46"
    code2 = "def f():\n    return 46"

    def setup(self):
        with open(self.filename, 'w') as f:
            f.write(self.code2)

    def teardown(self):
        os.remove(self.filename)
        if os.path.exists("TESTLOGS"):
            os.remove("TESTLOGS/info.txt")
            os.rmdir("TESTLOGS")

    def test_load_if_file(self):
        # an error should be raised if file expected but not found
        error_raised = False
        try:
            load_if_file('this_is_code_and_not_a_file')
        except FileNotFoundError:
            error_raised = True
        assert error_raised

        # multiline text will never be mistaken for a file
        assert load_if_file('this_is_code_and_not_a_file\n')

        # neither will text that does not look like a file name
        s = "this is code * and not a file"
        assert s == load_if_file(s)

        # not a file and not mistaken for a file
        assert self.code1 == load_if_file(self.code1)

        # not a file and not mistaken for a file either
        assert self.code2 == load_if_file(self.code2)

        # file correctly loaded
        assert self.code2 == load_if_file(self.filename)

    def test_logging(self):
        try:
            log_dir()
            assert False, "Name error should be raised when log_dir() is called outside " \
                          "a logging context."
        except NameError:
            pass
        with logging("TESTLOGS"):
            assert not os.path.exists("TESTSLOGS"), \
                "Log dir should not be created before first use!"
            dirname = log_dir()
            assert dirname == "TESTLOGS"
            assert is_logging(), "is_logging() should return True, if logging is on"
            with logging(False):
                assert not is_logging(), \
                    "is_logging() should return False, if innermost logging context " \
                    "has logging turned off."
            assert is_logging(), "is_logging() should return True after logging off " \
                                 "context has been left"
            assert os.path.exists("TESTLOGS/info.txt"), "an 'info.txt' file should be " \
                "created within a newly created log dir"
        # cleanup
        os.remove("TESTLOGS/info.txt")
        os.rmdir("TESTLOGS")

    def logging_task(self):
        with logging("TESTLOGS"):
            log_dir()
            assert is_logging(), "Logging should be on inside logging context"
        assert not is_logging(), "Logging should be off outside logging context"
        return os.path.exists("TESTLOGS/info.txt")

    def test_logging_multiprocessing(self):
        with concurrent.futures.ProcessPoolExecutor() as ex:
            f1 = ex.submit(self.logging_task)
            f2 = ex.submit(self.logging_task)
            f3 = ex.submit(self.logging_task)
            f4 = ex.submit(self.logging_task)
        assert f1.result()
        assert f2.result()
        assert f3.result()
        assert f4.result()


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())