#!/usr/bin/env python3

"""recompile_grammar.py - recompiles any .ebnf files in the current 
                          directory if necessary

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

sys.path.extend([os.path.join('..', '..'), '..', '.'])
flag = os.path.exists('LyrikParser.py')

from DHParser.dsl import recompile_grammar

if not recompile_grammar('Lyrik.ebnf', force=True):
    with open('Lyrik_ebnf_ERRORS.txt') as f:
        print(f.read())
    sys.exit(1)

# Not needed if DHParser was installed on the system. Just a little
# service for those who have merely checked out the git repository,
# in particular for those reading the Tutorial in the Introduction

if not flag:
    with open('LyrikParser.py', 'r') as f:
        script = f.read()
    i = script.find('import sys') + 10
    script = script[:i] + "\nsys.path.extend([os.path.join('..', '..'), '..', '.'])\n" + script [i:]
    with open('LyrikParser.py', 'w') as f:
        f.write(script)
