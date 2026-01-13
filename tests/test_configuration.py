#!/usr/bin/env python3

"""test_configuration.py - tests of the configuration-module of DHParser


Author: Eckhart Arnold <arnold@badw.de>

Copyright 2019 Bavarian Academy of Sciences and Humanities

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

import multiprocessing
import os
import shutil
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import access_presets, finalize_presets, \
    set_preset_value, get_preset_value, get_config_value, read_local_config, \
    get_config_values, set_config_value, get_forkserver_pid, CONFIG_PRESET, \
    dump_config_data
from DHParser.testing import unique_name
from DHParser.toolkit import PickMultiCoreExecutor

# spped up tests for Python3.14: CONFIG_PRESET['multicore_pool'] = 'InterpreterPool'


class TestConfigGetAndSet:
    def test_get_forkserver_pid(self):
        _ = get_forkserver_pid()

    def test_get_config_value(self):
        v = get_config_value('default_serialization')
        try:
            v = get_config_value('non_existent')
            assert False, "KeyError expected"
        except KeyError:
            pass
        v = get_config_value('non_existent', 'nothing')
        assert v == 'nothing'
        # check that "nothing" has not mistakenly been added to configuration
        try:
            v = get_config_value('non_existent')
            assert False, "KeyError expected"
        except KeyError:
            pass


class TestDumpConfig:
    def test_dump_config(self):
        set_config_value('test.alpha', 1, allow_new_key=True)
        set_config_value('test.beta', "beta", allow_new_key=True)
        s = dump_config_data('test.*', 'server_default_*', 'batch_processing_*')
        assert s == """[DHParser]
server_default_host = '127.0.0.1'
server_default_port = 8888
batch_processing_parallelization = True
batch_processing_max_chunk_size = 4

[test]
alpha = 1
beta = 'beta'
"""
        t = dump_config_data('test.*', 'server_default_*', 'batch_processing_*',
                             use_headings=False)
        assert t == """server_default_host = '127.0.0.1'
server_default_port = 8888
batch_processing_parallelization = True
batch_processing_max_chunk_size = 4

test.alpha = 1
test.beta = 'beta'
"""



def evaluate_presets():
    # from DHParser.configuration import os_getpid
    access_presets()
    if get_preset_value('test', 'failure') != 'failure' and \
            get_preset_value('test2', 'failure') != 'failure':
        result = True
    else:
        result = False
    finalize_presets()
    return result


class TestConfigMultiprocessing:
    def test_presets(self):
        """Checks whether changes to CONFIG_PRESET before spawning / forking
        new processes will be present in spawned or forked processes
        afterwards."""
        from DHParser.configuration import CONFIG_PRESET, get_syncfile_path
        from _ctypes import Union, Structure, Array
        access_presets()
        set_preset_value('test', 'multiprocessing presets test', allow_new_key=True)
        finalize_presets()
        access_presets()
        set_preset_value('test2', 'multiprocessing presets test2', allow_new_key=True)
        finalize_presets()
        with PickMultiCoreExecutor() as executor:
            result = executor.submit(evaluate_presets)
        assert result

    def test_presets_interpreter_pool(self):
        """Checks whether changes to CONFIG_PRESET before spawning / forking
        new processes will be present in spawned or forked processes
        afterwards."""
        global PYTEST, evaluate_presets
        import DHParser.stringview
        if sys.version_info >= (3, 14, 0) \
                and not getattr(DHParser.stringview, 'cython_optimized', False):
            import concurrent.futures
            # from DHParser.configuration import CONFIG_PRESET, os_getpid
            if __name__ == '__main__':
                import test_configuration
            else:
                os.chdir('..')
                import tests.test_configuration as test_configuration
            evaluate_presets = test_configuration.evaluate_presets
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


TEST_CFG = """
[DHParser]
resume_notices = True
delimiter_set = {
        'DEF':        ':=',
        'OR':         '|',
        'AND':        '',
        'ENDL':       ';',
        'RNG_OPEN':   '{',
        'RNG_CLOSE':  '}',
        'RNG_DELIM':  ',',
        'TIMES':      '*',
        'RE_LEADIN':  '/',
        'RE_LEADOUT': '/',
        'CH_LEADIN':  'ch'
    }

[project_specific]
custom_1 = "test1"
custom_2 = -1
custom_3 = 3.1415
custom_4 = [1, 2, 3]
custom_5 = False
"""

class TestLocalConfig:
    def setup_class(self):
        self.cwd = os.getcwd()
        os.chdir(scriptpath)
        # avoid race-condition
        counter = 10
        while counter > 0:
            try:
                self.dirname = unique_name('test_dhparser_data')
                os.mkdir(self.dirname)
                counter = 0
            except FileExistsError:
                self.dirname = ''
                time.sleep(random.random())
                counter -= 1
        assert self.dirname
        os.mkdir(os.path.join(self.dirname, 'data'))
        access_presets()
        self.save_resume_notices = get_preset_value('resume_notices')
        self.save_delimiter_set = get_preset_value('delimiter_set')
        finalize_presets()

    def teardown_class(self):
        access_presets()
        set_preset_value('resume_notices', self.save_resume_notices)
        set_preset_value('delimiter_set', self.save_delimiter_set)
        finalize_presets()
        set_config_value('resume_notices', self.save_resume_notices)
        set_config_value('delimiter_set', self.save_delimiter_set)
        name = self.dirname
        if os.path.exists(name) and os.path.isdir(name):
            shutil.rmtree(name)
        if os.path.exists(name) and not os.listdir(name):
            os.rmdir(name)

    def test_read_local_config(self):
        ini_path = os.path.join(self.dirname, 'data', 'test.ini')
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.write(TEST_CFG)
        result = read_local_config('wrong_file_name.ini')
        assert not result
        result = read_local_config(ini_path)
        access_presets()
        assert get_preset_value('project_specific.custom_1') == 'test1'
        assert get_preset_value('delimiter_set')['DEF'] == ':='
        finalize_presets()
        test_cfg = TEST_CFG.replace(':=', '=').replace('test1', 'test2')
        old_path = ini_path
        os.remove(old_path)
        ini_path = os.path.join(self.dirname, 'test.ini')
        with open(ini_path, 'w', encoding='utf-8') as f:
            f.write(test_cfg)
        assert not os.path.exists(old_path)
        save = os.getcwd()
        os.chdir(self.dirname)
        result = read_local_config(old_path)
        assert 'test.ini' in result, str(result)
        access_presets()
        assert get_preset_value('project_specific.custom_1') == 'test2'
        assert get_preset_value('delimiter_set')['DEF'] == '='
        finalize_presets()
        os.chdir(save)
        os.remove(ini_path)
        ini_path_1 = os.path.join(self.dirname, 'test.ini')
        with open(ini_path_1, 'w', encoding='utf-8') as f:
            f.write(TEST_CFG)
        ini_path = 'test.ini' if os.getcwd().endswith(scriptpath) \
            else os.path.join(scriptpath, 'test.ini')
        test_cfg = TEST_CFG.replace('3.1415', '2.7183')
        with open(os.path.basename(ini_path), 'w', encoding='utf-8') as f:
            f.write(test_cfg)
        result = read_local_config(ini_path_1)
        assert len(result) >= 2, str(result)
        access_presets()
        assert get_preset_value('project_specific.custom_1') == 'test1'
        assert get_preset_value('delimiter_set')['DEF'] == ':='
        finalize_presets()
        os.remove(ini_path_1)
        os.remove(ini_path)
        custom_cfg = get_config_values('project_specific.*')
        assert list(custom_cfg.values()) == ['test1', -1, 2.7183, [1, 2, 3], False]


if __name__ == "__main__":
    PYTEST = False
    from DHParser.testing import runner
    runner("", globals())
