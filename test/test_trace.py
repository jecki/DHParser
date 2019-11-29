#!/usr/bin/python3

"""test_trace.py - unit tests for the trace-module of DHParser

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

from DHParser import grammar_provider, with_all_descendants, with_unnamed_descendants, \
    set_tracer, trace_history, log_parsing_history, start_logging


class TestTrace:
    def setup(self):
        minilang = """
            expr = term { ("+"|"-") term }
            term = factor { ("*"|"/") factor }
            factor = /[0-9]+/~ | "(" expr ")"
            """
        self.gr = grammar_provider(minilang)()

    # def tear_down(self):
    #    os.remove('trace.log')

    def test_trace(self):
        all_desc = with_all_descendants(self.gr.root_parser__)
        set_tracer(all_desc, trace_history)
        st = self.gr('2*(3+4)')
        start_logging()
        log_parsing_history(self.gr, 'trace.log')



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
