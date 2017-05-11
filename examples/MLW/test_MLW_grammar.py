#!/usr/bin/python3

"""test_MLW_grammar.py - test code for the MLW grammar 

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
import DHParser.testing
from DHParser import parsers
# from DHParser.dsl import load_compiler_suite
from MLW_compiler import get_MLW_grammar, get_MLW_transformer


MLW_TEST_CASES_LEMMA_POSITION = {

"lemma": {
    "match": {
        1: "facitergula",
        2: "facitergul|a",
        3: "fasc|itergula"
    },
    "fail": {
        9: "duo vocabula"
    }
},

"HauptLemma" : {
    "match": {
        1: "facitergula",
        2: "*fascitergula",
        3: "* fasciterugl|a"
    }
},

"LemmaVarianten": {
    "match": {
        1: """
           fasc-itergula
           fac-iet-ergula
           fac-ist-ergula
           fa-rcu-tergula
           """,
        2: " fasc-itergula",
        3: " fasc-itergula fac-iet-ergula ZUSATZ sim.",
    },
    "fail": {
        9: "* fascitergula"
    }
}

}




class TestMLWGrammar:
    def test_lemma_position(self):
        errata = DHParser.testing.test_grammar(MLW_TEST_CASES_LEMMA_POSITION,
                                               get_MLW_grammar,
                                               get_MLW_transformer)
        assert not errata, str(errata)

