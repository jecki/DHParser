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
from DHParser.dsl import compile_on_disk, is_outdated

#
# if (not os.path.exists('PopRetrieveCompiler.py') or
#     is_outdated('PopRetrieveCompiler.py', 'PopRetrieve.ebnf')):
#     print("recompiling PopRetrieve parser")
#     errors = compile_on_disk("PopRetrieve.ebnf")
#     if errors:
#         print('\n\n'.join(errors))
#         sys.exit(1)


# from PopRetrieve_compiler import compile_PopRetrieve
#
# print("PopRetrieveTest 1")
# result, errors, ast = compile_PopRetrieve("PopRetrieveTest.txt")
# if errors:
#     print(errors)
#     sys.exit(1)
# else:
#     print(result)
#
# print("PopRetrieveTest 2")
# result, errors, ast = compile_PopRetrieve("PopRetrieveTest2.txt")
# if errors:
#     print(errors)
#     sys.exit(1)
# else:
#     print(result)


# print("PopRetrieveTest 1")
# errors = compile_on_disk("PopRetrieveTest.txt", 'PopRetrieveCompiler.py')
# if errors:
#     print(errors)
#     sys.exit(1)
#
# print("PopRetrieveTest 2")
# errors = compile_on_disk("PopRetrieveTest2.txt", 'PopRetrieveCompiler.py')
# if errors:
#     print(errors)
#     sys.exit(1)
#
#
#
# if (not os.path.exists('PopRetrieveComplementCompiler.py') or
#         is_outdated('PopRetrieveComplementCompiler.py', 'PopRetrieveComplement.ebnf')):
#     print("recompiling PopRetrieveComplement parser")
#     errors = compile_on_disk("PopRetrieveComplement.ebnf")
#     if errors:
#         print('\n\n'.join(errors))
#         sys.exit(1)
#
#
# from PopRetrieveComplementCompiler import compile_src
#
# print("PopRetrieveComplement Test 1")
# result, errors, ast = compile_src("PopRetrieveComplementTest.txt")
# if errors:
#     print(errors)
#     sys.exit(1)
# else:
#     print(result)
#
# print("PopRetrieveComplement Test 2")
# result, errors, ast = compile_src("PopRetrieveComplementTest2.txt")
# if errors:
#     print(errors)
#     sys.exit(1)
# else:
#     print(result)



if (not os.path.exists('PopRetrieveConfusionCompiler.py') or
        is_outdated('PopRetrieveConfusionCompiler.py', 'PopRetrieveConfusion.ebnf')):
    print("recompiling PopRetrieveConfusion parser")
    errors = compile_on_disk("PopRetrieveConfusion.ebnf")
    if errors:
        print('\n\n'.join(errors))
        sys.exit(1)

from PopRetrieveConfusionCompiler import compile_src

print("PopRetrieveConfusion Test 1")
result, errors, ast = compile_src("PopRetrieveConfusion.txt")
print(ast.as_sxpr())
if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print(result)
