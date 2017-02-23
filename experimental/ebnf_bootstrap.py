#!/usr/bin/python3

"""ebnf_bootstrap.py


Copyright 2016  by Eckhart Arnold

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

import difflib
import os
import sys

sys.path.append(os.path.abspath('./'))

from ScratchParserCombinators import *


try:
    stage_0 = compileDSL("EBNF_0.ebnf", EBNFGrammar, EBNFTransTable, EBNFCompiler('EBNF', 'EBNF_0.ebnf'))
    print("STAGE 0:\n")
    print(stage_0)
    stage_1 = compileDSL("EBNF_1.ebnf", stage_0, EBNFTransTable, EBNFCompiler('EBNF', 'EBNF_1.ebnf'))
    print("STAGE 1:\n")
    print(stage_1)
    stage_2 = compileDSL("EBNF_2.ebnf", stage_1, EBNFTransTable, EBNFCompiler('EBNF', 'EBNF_2.ebnf'))
    print("STAGE 2:\n")
    print(stage_2)
    check = compileDSL("EBNF_2.ebnf", stage_2, EBNFTransTable, EBNFCompiler('EBNF', 'EBNF_2.ebnf'))

except GrammarError as error:
    print(error.error_messages)
except CompilationError as error:
    print(error.error_messages)
    print(error.AST)

assert stage_2 == check, "\n".join(difflib.ndiff(stage_2, check))

with open('EBNF_2_parser.py', 'w') as f:
    f.write(stage_2)

print('\nready.')
