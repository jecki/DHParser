#!/usr/bin/env python3

"""notest_multiprocessing_spawn.py - runs a few crucial
    tests from the DHParser test-suite to make sure that they
    work with a specific multiprocessing-start-method.


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

scriptpath = os.path.abspath(os.path.dirname(__file__) or '.')
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
sys.path.append(os.path.abspath(os.path.join(scriptpath, '.')))

from DHParser.testing import runner

from test_configuration import *
from test_toolkit import *

if __name__ == '__main__':
    multiprocessing.set_start_method('spawn')
    runner("TestConfigMultiprocessing.test_presets", globals())
    runner("TestLoggingAndLoading.test_logging_multicore", globals())
