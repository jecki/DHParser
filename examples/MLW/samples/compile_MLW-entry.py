#!/usr/bin/python3

"""compile_MLW-entry.py - simple utility script for compiling a sample 
                          MLW entry

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
sys.path.append(os.path.abspath('../../../'))
import DHParser.toolkit as toolkit
from DHParser.ebnf import grammar_changed
from DHParser.dsl import compile_on_disk

MLW_ebnf = os.path.join('..', 'MLW.ebnf')
MLW_compiler = os.path.join('..', 'MLWCompiler.py')

# print(grammar_changed(MLW_ebnf, MLW_compiler))

if (not os.path.exists(MLW_compiler) or
    grammar_changed(MLW_compiler, MLW_ebnf)):
    print("recompiling parser")
    errors = compile_on_disk(MLW_ebnf)
    if errors:
        print('\n'.join(errors))
        sys.exit(1)

with toolkit.logging():
    errors = compile_on_disk("fascitergula.mlw", MLW_compiler, ".xml")
if errors:
    print('\n'.join(errors))
    sys.exit(1)
