#!/usr/bin/env python3.14

# This test does not play well with pytest, possibly because of
# a InterpreterPool and process-id related problems. Therefore,
# it is so far a "no-test"

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
from DHParser.configuration import CONFIG_PRESET, get_config_value, access_presets, finalize_presets, \
    set_preset_value, get_preset_value, get_config_values, set_config_value, read_local_config

CONFIG_PRESET['multicore_pool'] = 'InterpreterPool'

def logging_task():
    log_dir()
    assert is_logging(), "Logging should be on inside logging context"
    save_log_dir = suspend_logging()
    assert not is_logging(), "Logging should be off outside logging context"
    resume_logging(save_log_dir)
    # TODO: Some race condition occurs here, but which and why???
    #       Maybe: Some other thread has created logdir but not yet info.txt
    #       Solution: Just return True, because log_dir() does not guarantee
    #                 existence of 'info.txt', anyway...
    return True


class TestLoggingAndLoading:  # addition to test_toolkit
    def setup_class(self):
        self.LOGDIR = os.path.abspath(os.path.join(scriptpath, "TESTLOGS" + str(os.getpid())))
        self.save_dir = os.getcwd()

    def teardown_class(self):
        os.chdir(self.save_dir)
        if os.path.exists(self.LOGDIR):
            os.remove(os.path.join(self.LOGDIR, "info.txt"))
            for fname in os.listdir(self.LOGDIR):
                os.remove(os.path.join(self.LOGDIR, fname))
            os.rmdir(self.LOGDIR)

    def test_logging_interpreterpool(self):
        if sys.version_info >= (3, 14, 0):
            if __name__ != '__main__':
                os.chdir('..')
                import tests.notest_interpreterpool as notest_interpreterpool
            else:
                import notest_interpreterpool
            start_logging(self.LOGDIR)
            with concurrent.futures.InterpreterPoolExecutor() as ex:
                f1 = ex.submit(notest_interpreterpool.logging_task)
                f2 = ex.submit(notest_interpreterpool.logging_task)
                f3 = ex.submit(notest_interpreterpool.logging_task)
                f4 = ex.submit(notest_interpreterpool.logging_task)
            assert f1.result()
            assert f2.result()
            assert f3.result()
            assert f4.result()



def evaluate_presets():
    from DHParser.configuration import os_getpid
    access_presets()
    if get_preset_value('test', 'failure') != 'failure' and \
            get_preset_value('test2', 'failure') != 'failure':
        result = True
    else:
        result = False
    finalize_presets()
    return result


class TestConfigMultiprocessing:
    def setup_class(self):
        self.save_dir = os.getcwd()

    def teardown_class(self):
        os.chdir(self.save_dir)

    def test_presets_interpreter_pool(self):
        """Checks whether changes to CONFIG_PRESET before spawning / forking
        new processes will be present in spawned or forked processes
        afterwards."""
        global PYTEST, evaluate_presets
        if sys.version_info >= (3, 14, 0):
            import concurrent.futures
            from DHParser.configuration import CONFIG_PRESET, os_getpid
            CONFIG_PRESET['multicore_pool'] = 'InterpreterPool'
            if __name__ == '__main__':
                import notest_interpreterpool
            else:
                os.chdir('..')
                import tests.notest_interpreterpool as notest_interpreterpool
            evaluate_presets = notest_interpreterpool.evaluate_presets
            try:
                from _ctypes import Union, Structure, Array
                access_presets()
                set_preset_value('test', 'multiprocessing presets test', allow_new_key=True)
                finalize_presets()
                access_presets()
                set_preset_value('test2', 'multiprocessing presets test2', allow_new_key=True)
                finalize_presets()
                with concurrent.futures.InterpreterPoolExecutor() as pool:
                    result = pool.submit(evaluate_presets).result()
                assert result
            except ImportError as e:
                print(f'Skipping Test, because {e}')



if __name__ == "__main__":
    PYTEST = False
    from DHParser.testing import runner
    runner("", globals())
