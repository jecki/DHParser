#!/usr/bin/env python3

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
import collections.abc
import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.toolkit import has_fenced_code, load_if_file, re, \
    lstrip_docstring, issubtype, typing, concurrent_ident
from DHParser.log import log_dir, start_logging, is_logging, suspend_logging, resume_logging


class TestLoggingAndLoading:
    def setup(self):
        self.tmpname = 'tmp_' + concurrent_ident()
        self.filename = os.path.join("test", self.tmpname, "test.py") if os.path.isdir('test') \
            else os.path.join(self.tmpname, "test.py")
        self.dirname = os.path.dirname(self.filename)
        self.code1 = "x = 46\n"
        self.code2 = "def f():\n    return 46"
        if not os.path.exists(self.dirname):
            os.mkdir(self.dirname)
        with open(self.filename, 'w') as f:
            f.write(self.code2)
        self.LOGDIR = os.path.abspath(os.path.join(scriptpath, "TESTLOGS" + str(os.getpid())))

    def teardown(self):
        os.remove(self.filename)
        pycachedir = os.path.join(self.dirname,'__pycache__')
        if os.path.exists(pycachedir):
            for fname in os.listdir(pycachedir):
                os.remove(os.path.join(pycachedir, fname))
            os.rmdir(pycachedir)
        os.rmdir(self.dirname)
        if os.path.exists(self.LOGDIR):
            # for fname in os.listdir(self.LOGDIR):
            #     os.remove(os.path.join(self.LOGDIR, fname))
            os.remove(os.path.join(self.LOGDIR, "info.txt"))
            os.rmdir(self.LOGDIR)

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

    def test_has_fenced_code(self):
        code1="has fenced code block\n~~~ ebnf\nstart = 'start'\n~~~\n"
        code2="no fenced code block ~~~ ebnf\nstart = 'start'\n~~~\n"
        code3="\n~~~ ebnd\nstart = 'start'\n~~"
        assert has_fenced_code(code1)
        assert not has_fenced_code(code2)
        assert not has_fenced_code(code3)


    def test_logging(self):
        # try:
        #     log_dir()
        #     assert False, "AttributeError should be raised when log_dir() is called outside " \
        #                   "a logging context."
        # except AttributeError:
        #     pass
        res = log_dir()
        if res:
            suspend_logging()
        start_logging(self.LOGDIR)
        assert not os.path.exists(self.LOGDIR), \
            "Log dir should be created lazily!"
        dirname = log_dir()
        # print(type(dirname), dirname)
        assert dirname == self.LOGDIR
        assert is_logging(), "is_logging() should return True, if logging is on"
        save_log_dir = suspend_logging()
        assert not is_logging(), \
            "is_logging() should return False, if innermost logging context " \
            "has logging turned off."
        resume_logging(save_log_dir)
        assert is_logging(), "is_logging() should return True after logging off " \
                             "context has been left"
        info_path = os.path.join(self.LOGDIR, 'info.txt')
        assert os.path.exists(info_path), "an 'info.txt' file should be " \
            "created within a newly created log dir"
        # cleanup
        os.remove(info_path)
        os.rmdir(self.LOGDIR)

    def logging_task(self):
        log_dir()
        assert is_logging(), "Logging should be on inside logging context"
        save_log_dir = suspend_logging()
        assert not is_logging(), "Logging should be off outside logging context"
        resume_logging(save_log_dir)
        # TODO: Some race condition occurs here, but which and why???
        #       Maybe: Some other thread has created logdir but not yet info.txt
        #       Solution: Just return True, cause log_dir() does not guarantee
        #                 existence of 'info.txt', anyway...
        return True

    def test_logging_multiprocessing(self):
        start_logging(self.LOGDIR)
        with concurrent.futures.ProcessPoolExecutor() as ex:
            f1 = ex.submit(self.logging_task)
            f2 = ex.submit(self.logging_task)
            f3 = ex.submit(self.logging_task)
            f4 = ex.submit(self.logging_task)
        assert f1.result()
        assert f2.result()
        assert f3.result()
        assert f4.result()


class TestStringHelpers:
    def test_lstrip_docstring(self):
        str1 = """line
        
            indented line
        line
        """
        assert lstrip_docstring(str1) == 'line\n\n    indented line\nline\n'
        str2 = """
            line
            line
                indented line
                    indented indented line"""
        assert lstrip_docstring(str2) == '\nline\nline\n    indented line\n        indented ' \
                                         'indented line'


class TestTypeSystemSupport:
    def test_issubtype(self):
        assert issubtype(typing.List, collections.abc.Sequence)
        assert issubtype(typing.Tuple, type(tuple()))
        assert issubtype(typing.Callable, collections.abc.Callable)
        assert issubtype(typing.Tuple[typing.Callable], tuple)


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
