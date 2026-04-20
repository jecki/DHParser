#!/usr/bin/env python3

"""test_error.py - tests of the error-handling-module of DHParser


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

import os
import sys

scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

from DHParser.dsl import grammar_provider

class TestLateBinding:
    def test_late_binding(self):
        lang = """
            document = allof
            @ allof_error = '{} erwartet, {} gefunden :-('
            @ allof_skip = "D", "E", "F", "G"
            allof = "A" ° "B" ° §"C" ° "D" ° "E" ° "F" ° "G" 
        """
        gr = grammar_provider(lang)()


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())