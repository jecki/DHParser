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
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.configuration import access_presets, finalize_presets


def evaluate_presets(flag):
    CONFIG_PRESET = access_presets()
    if CONFIG_PRESET.get('test', 'failure') != 'failure' and \
            CONFIG_PRESET.get('test2', 'failure') != 'failure':
        flag.value = 1
    else:
        flag.value = 0


class TestConfigMultiprocessing:

    def test_presets(self):
        """Checks whether changes to CONFIG_PRESET before spawning / forking
        new processes will be present in spawned or forked processes
        afterwards."""
        CONFIG_PRESET = access_presets()
        CONFIG_PRESET['test'] = 'multiprocessing presets test'
        finalize_presets()
        CONFIG_PRESET = access_presets()
        CONFIG_PRESET['test2'] = 'multiprocessing presets test2'
        finalize_presets()
        flag = multiprocessing.Value('b', 0)
        p = multiprocessing.Process(target=evaluate_presets, args=(flag,))
        p.start()
        p.join()
        assert flag.value == 1



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
