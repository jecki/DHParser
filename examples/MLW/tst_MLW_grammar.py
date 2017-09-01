#!/usr/bin/python3

"""test_MLW_grammar.py - unit tests for the MLW grammar 

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

import sys

sys.path.extend(['../../', '../', './'])

from DHParser import dsl
from DHParser import testing
from DHParser import toolkit

if not dsl.recompile_grammar('MLW.ebnf', force=True):  # recompiles Grammar only if it has changed
    with open('MLW_ebnf_ERRORS.txt') as f:
        print(f.read())
    sys.exit(1)

from MLWCompiler import get_grammar, get_transformer

with toolkit.logging(True):
    error_report = testing.grammar_suite('grammar_tests', get_grammar, get_transformer,
                                         verbose=True)
assert not error_report, error_report

# class TestMLWGrammar:
#     def test_lemma_position(self):
#         errata = testing.grammar_unit('grammar_tests/test_lemmaposition.ini',  # MLW_TEST_CASES_LEMMA_POSITION,
#                                       get_MLW_grammar,
#                                       get_MLW_transformer)
#         assert not errata, str(errata)
#
#
# if __name__ == "__main__":
#     testing.runner("", globals())
