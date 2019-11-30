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
    set_tracer, trace_history, log_parsing_history, start_logging, set_config_value


class TestTrace:
    def setup(self):
        start_logging()

    def test_trace_simple(self):
        lang = """
            expr = term { ("+"|"-") term }
            term = factor { ("*"|"/") factor }
            factor = /[0-9]+/~ | "(" expr ")"
            """
        gr = grammar_provider(lang)()
        all_desc = with_all_descendants(gr.root_parser__)
        set_tracer(all_desc, trace_history)
        st = gr('2*(3+4)')
        log_parsing_history(gr, 'trace_simple')
        print(st.serialize())

    def test_trace_drop(self):
        lang = r"""
            @ drop = token, whitespace
            expression = term  { ("+" | "-") term}
            term       = factor  { ("*"|"/") factor}
            factor     = number | variable | "("  expression  ")"
                       | constant | fixed
            variable   = /[a-z]/~
            number     = /\d+/~
            constant   = "A" | "B"
            fixed      = "X"
            """
        set_config_value('compiled_EBNF_log', 'test_trace_parser.py')
        gr = grammar_provider(lang)()
        all_desc = with_all_descendants(gr.root_parser__)
        set_tracer(all_desc, trace_history)
        # st = gr('2*(3+4)')
        st = gr('2*(3 + 4*(5 + 6*(7 + 8 + 9*2 - 1/5*1000) + 2) + 5000 + 4000)')
        log_parsing_history(gr, 'trace_drop')
        print(st.serialize())



if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
