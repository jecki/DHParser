#!/usr/bin/python3

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

from DHParser.dsl import recompile_grammar

recompile_grammar('.')

# import os
#
# from DHParser.ebnf import grammar_changed
# from DHParser.dsl import compile_on_disk
#
#
# def compile(name):
#     base, ext = os.path.splitext(name)
#     compiler_name = base + '_compiler.py'
#     if (not os.path.exists(compiler_name) or
#         grammar_changed(compiler_name, name)):
#         print("recompiling parser for: " + name)
#         errors = compile_on_disk(name)
#         if errors:
#             print("Errors while compiling: " + name + '!')
#             with open(base + '_errors.txt', 'w') as f:
#                 for e in errors:
#                     f.write(e)
#                     f.write('\n')
#
# for entry in os.listdir():
#     if entry.lower().endswith('.ebnf') and os.path.isfile(entry):
#         compile(entry)
