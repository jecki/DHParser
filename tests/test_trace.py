#!/usr/bin/env python3

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
import re
import sys


scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))

REVEAL = False


from DHParser import grammar_provider, all_descendants, \
    set_tracer, trace_history, log_parsing_history, start_logging, log_dir, \
    set_config_value, resume_notices_on, Error
from DHParser.error import MANDATORY_CONTINUATION, PARSER_STOPPED_BEFORE_END, \
    MANDATORY_CONTINUATION_AT_EOF


def get_history(name, show: bool = REVEAL) -> str:
    history_fname = os.path.join(log_dir() or '', name + "_full_parser.log.html")
    if show:
        import webbrowser, time
        webbrowser.open(history_fname)
        time.sleep(1)
    with open(history_fname, 'r', encoding='utf-8') as f:
        history_file = f.read()
    return history_file


def reveal(grammar, name):
    if REVEAL:
        log_parsing_history(grammar, name)
        get_history(name, show=True)


class TestTrace:
    def setup(self):
        start_logging()

    def teardown(self):
        LOG_DIR = log_dir()
        if os.path.exists(LOG_DIR) and os.path.isdir(LOG_DIR):
            for fname in os.listdir(LOG_DIR):
                os.remove(os.path.join(LOG_DIR, fname))
            os.rmdir(LOG_DIR)

    def test_trace_simple(self):
        lang = """
            @literalws = right
            expr = term { ("+"|"-") term }
            term = factor { ("*"|"/") factor }
            factor = /[0-9]+/~ | "(" expr ")"
            """
        gr = grammar_provider(lang)()
        all_desc = all_descendants(gr.root_parser__)
        set_tracer(all_desc, trace_history)
        st = gr('2*(3+4)')
        assert(str(st)) == '2*(3+4)'
        history = gr.history__
        for record in history:
            if record.status.startswith(record.FAIL):
                # check if the first failed parser yields an excerpt
                assert record.excerpt
                break
        assert len(history) == 24
        log_parsing_history(gr, 'trace_simple')
        history = get_history('trace_simple')
        assert history.count('<tr>') == 25  # same as len(history) + 1 title row

    def test_trace_stopped_early(self):
        lang = """
            @ literalws = right
            expr = term { ("+"|"-") term }
            term = factor { ("*"|"/") factor }
            factor = /[0-9]+/~ | "(" expr ")"
            """
        gr = grammar_provider(lang)()
        all_desc = all_descendants(gr.root_parser__)
        set_tracer(all_desc, trace_history)
        _ = gr('2*(3+4)xxx')
        log_parsing_history(gr, 'trace_stopped_early')
        history = get_history('trace_stopped_early')
        assert history.count('<tr>') == 26

    def test_trace_drop(self):
        lang = r"""
            @ literalws = right
            @ drop = strings, whitespace
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
        all_desc = all_descendants(gr.root_parser__)
        set_tracer(all_desc, trace_history)
        # st = gr('2*(3+4)')
        st = gr('2*(3 + 4*(5 + 6*(7 + 8 + 9*2 - 1/5*1000) + 2) + 5000 + 4000)')
        serialization = st.serialize()
        assert '*' not in serialization   # same for '/', '+', '-'
        log_parsing_history(gr, 'trace_drop')
        history_file = get_history('trace_drop')
        assert "DROP" in history_file
        assert "FAIL" in history_file
        assert "MATCH" in history_file

    def test_trace_resume(self):
        lang = """
        @literalws = right
        document = alpha [beta] gamma "."
          alpha = "ALPHA" abc
            abc = §"a" "b" "c"
          beta = "BETA" (bac | bca)
            bac = "b" "a" §"c"
            bca = "b" "c" §"a"
          gamma = "GAMMA" §(cab | cba)
            cab = "c" "a" §"b"
            cba = "c" "b" §"a"
        """
        gr = grammar_provider(lang)()
        gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)')]
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content, cst.as_sxpr()
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len(cst.errors_sorted) == 1

        # test resume notice
        resume_notices_on(gr)
        cst = gr(content)
        # there should be one error message and one resume notice
        assert len(cst.errors_sorted) == 2
        set_tracer(gr, None)
        assert not gr.history_tracking__


class TestErrorReporting:
    lang = """
    @literalws = right
    document = alpha [beta] gamma "."
      alpha = "ALPHA" abc
        abc = §"a" "b" "c"
      beta = "BETA" (bac | bca)
        bac = "b" "a" §"c"
        bca = "b" "c" §"a"
      gamma = "GAMMA" §(cab | cba)
        cab = "c" "a" §"b"
        cba = "c" "b" §"a"
    """
    gr = grammar_provider(lang)()

    def setup(self):
        start_logging()

    def teardown(self):
        LOG_DIR = log_dir()
        if os.path.exists(LOG_DIR) and os.path.isdir(LOG_DIR):
            for fname in os.listdir(LOG_DIR):
                os.remove(os.path.join(LOG_DIR, fname))
            os.rmdir(LOG_DIR)

    def test_trace_noskip(self):
        lang = """
        document = series | /.*/
        series = "A" "B" §"C" "D"
        """
        gr = grammar_provider(lang)()
        set_tracer(all_descendants(gr.root_parser__), trace_history)
        _ = gr('AB_D')
        for record in gr.history__:
            if record.status.startswith(record.ERROR):
                assert record.excerpt == '_D'
                if record.errors[0].code == PARSER_STOPPED_BEFORE_END:
                    break
        else:
            assert False, "Missing Error!"
        reveal(gr, 'trace_noskip')

    def test_trace_skip_clause(self):
        lang = """
        document = series | /.*/
        @series_skip = /(?=[A-Z])/
        series = "A" "B" §"C" "D"
        """
        gr = grammar_provider(lang)()
        resume_notices_on(gr)
        st = gr('AB_D')
        assert 'Skipping' in str(st.errors_sorted[1])
        for record in gr.history__:
            if record.status.startswith(record.ERROR):
                assert record.excerpt == '_D'
                break
        else:
            assert False, "Missing Error!"
        reveal(gr, 'trace_skip_clause')

    def test_trace_resume(self):
        gr = self.gr;  gr.resume_rules = dict()
        gr.resume_rules__['alpha'] = [re.compile(r'(?=BETA)')]
        resume_notices_on(gr)
        content = 'ALPHA acb BETA bac GAMMA cab .'
        cst = gr(content)
        assert cst.error_flag
        assert cst.content == content
        assert cst.pick('alpha').content.startswith('ALPHA')
        # because of resuming, there should be only one error message
        assert len([err for err in cst.errors_sorted if err.code >= 1000]) == 1
        reveal(gr, 'trace_resume')

    def test_trace_resume_complex_case(self):
        lang = r"""
            @ literalws = right
            @ comment =  /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/  # Kommentare im C++-Stil
            document = block_A block_B
            @ block_A_resume = /(?=x)/
            block_A = "a" §"b" "c"
            block_B = "x" "y" "z"
        """

        def mini_suite(grammar):
            tree = grammar('abc/*x*/xyz')
            assert not tree.errors

            tree = grammar('abDxyz')
            mandatory_cont = (MANDATORY_CONTINUATION, MANDATORY_CONTINUATION_AT_EOF)
            assert len(tree.errors) > 1 and tree.errors[0].code in mandatory_cont
            reveal(grammar, 'trace_resume_complex_1')

            tree = grammar('abD/*x*/xyz')
            assert len(tree.errors) > 1 and tree.errors[0].code in mandatory_cont
            reveal(grammar, 'trace_resume_complex_2')

            tree = grammar('aD /*x*/ c /* a */ /*x*/xyz')
            assert len(tree.errors) > 1 and tree.errors[0].code in mandatory_cont
            reveal(grammar, 'trace_resume_complex_3')

        # test regex-defined resume rule
        grammar = grammar_provider(lang)()
        resume_notices_on(grammar)
        mini_suite(grammar)


if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())
