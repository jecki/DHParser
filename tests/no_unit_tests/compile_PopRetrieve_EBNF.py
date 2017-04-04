#!/usr/bin/python3

"""compile_PopRetrieve.py - test of Pop and Retrieve operators 
                             

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
sys.path.append(os.path.abspath('../../'))
from DSLsupport import run_compiler, source_changed

if (not os.path.exists('PopRetrieve_compiler.py') or
    source_changed('PopRetrieve.ebnf', 'PopRetrieve_compiler.py')):
    print("recompiling parser")
    errors = run_compiler("PopRetrieve.ebnf")
    if errors:
        print(errors)
        sys.exit(1)

errors = run_compiler("PopRetrieveTest.txt", 'PopRetrieve_compiler.py')
if errors:
    print(errors)
    sys.exit(1)

errors = run_compiler("PopRetrieveTest2.txt", 'PopRetrieve_compiler.py')
if errors:
    print(errors)
    sys.exit(1)
