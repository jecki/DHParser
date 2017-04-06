#!/usr/bin/python3

"""compile_MLW.py - simple utility script for compiling MLW.ebnf

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
import logs
from DSLsupport import run_compiler, source_changed

MLW_ebnf = os.path.join('..', 'MLW.ebnf')
MLW_compiler = os.path.join('..', 'MLW_compiler.py')

# print(source_changed(MLW_ebnf, MLW_compiler))

logs.logging_off()

if (not os.path.exists(MLW_compiler) or
    source_changed(MLW_ebnf, MLW_compiler)):
    print("recompiling parser")
    errors = run_compiler(MLW_ebnf)
    if errors:
        print(errors)
        sys.exit(1)

logs.logging_on()

errors = run_compiler("fascitergula.mlw", MLW_compiler, ".xml")
if errors:
    print(errors)
    sys.exit(1)
