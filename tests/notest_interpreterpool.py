#!/usr/bin/env python3

"""notest_interpreterpool.py - additional tests that require
        interpreterppols

Author: Eckhart Arnold <arnold@badw.de>

Copyright 2025 Bavarian Academy of Sciences and Humanities

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
import sys
import os

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
sys.path.append(scriptpath)

from DHParser.log import log_dir, start_logging, is_logging, suspend_logging, resume_logging
from DHParser.configuration import CONFIG_PRESET
CONFIG_PRESET['multicore_pool'] = 'InterpreterPool'


def logging_task():
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


class TestLoggingAndLoading:  # addition to test_toolkit
    def setup_class(self):
        self.LOGDIR = os.path.abspath(os.path.join(scriptpath, "TESTLOGS" + str(os.getpid())))

    def teardown_class(self):
        if os.path.exists(self.LOGDIR):
            # for fname in os.listdir(self.LOGDIR):
            #     os.remove(os.path.join(self.LOGDIR, fname))
            os.remove(os.path.join(self.LOGDIR, "info.txt"))
            os.rmdir(self.LOGDIR)

    def test_logging_interpreterpool(self):
        if sys.version_info >= (3, 14, 0):
            from notest_interpreterpool import logging_task
            start_logging(self.LOGDIR)
            with concurrent.futures.InterpreterPoolExecutor() as ex:
                f1 = ex.submit(logging_task)
                f2 = ex.submit(logging_task)
                f3 = ex.submit(logging_task)
                f4 = ex.submit(logging_task)
            assert f1.result()
            assert f2.result()
            assert f3.result()
            assert f4.result()


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
