#!/usr/bin/python

"""dhparser.py - command line tool for DHParser

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

#  TODO: This is still a stub...

import os
import sys

from DHParser.dsl import compileDSL, compile_on_disk
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.parser import compile_source
from DHParser.toolkit import logging


EBNF_TEMPLATE = r"""-grammar

#######################################################################
#
#  EBNF-Directives
#
#######################################################################

@ testing     = True            # testing supresses error messages for unconnected symbols
@ whitespace  = vertical        # implicit whitespace, includes any number of line feeds
@ literalws   = right           # literals have implicit whitespace on the right hand side 
@ comment     = /#.*/           # comments range from a '#'-character to the end of the line
@ ignorecase  = False           # literals and regular expressions are case-sensitive


#######################################################################
#
#  Structure and Components
#
#######################################################################

document = //~ { WORD } §EOF    # root parser: optional whitespace followed by a sequence of words
                                # until the end of file

#######################################################################
#
#  Regular Expressions
#
#######################################################################

WORD     =  /\w+/~              # a sequence of letters, possibly followed by implicit whitespace
EOF      =  !/./                # no more characters ahead, end of file reached
"""

TEST_WORD_TEMPLATE = r'''[match:WORD]
1  : word
2  : one_word_with_underscores

[fail:WORD]
1  : two words
'''

TEST_DOCUMENT_TEMPLATE = r'''[match:document]
1  : """This is a sequence of words
     extending over several lines"""
     
[fail:document]
1  : """This test should fail, because neither
     comma nor full have been defined anywhere."""
'''

README_TEMPLATE = """# {name}

PLACE A SHORT DESCRIPTION HERE

Author: AUTHOR'S NAME <EMAIL>, AFFILIATION


## License

{name} is open source software under the [MIT License](https://opensource.org/licenses/MIT)

Copyright YEAR AUTHOR'S NAME <EMAIL>, AFFILIATION

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the 
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject
 to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF 
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""


GRAMMAR_TEST_TEMPLATE = r'''#!/usr/bin/python3

"""tst_{name}_grammar.py - runs the unit tests for the {name}-grammar
"""

import sys

import DHParser.dsl
from DHParser import testing
from DHParser import toolkit

if not DHParser.dsl.recompile_grammar('{name}.ebnf', force=False):  # recompiles Grammar only if it has changed
    print('\nErrors while recompiling "{name}.ebnf":\n--------------------------------------\n\n')
    with open('{name}_ebnf_ERRORS.txt') as f:
        print(f.read())
    sys.exit(1)

sys.path.append('./')
# must be appended after module creation, because otherwise an ImportError is raised under Windows
from {name}Compiler import get_grammar, get_transformer

with toolkit.logging(True):
    error_report = testing.grammar_suite('grammar_tests', get_grammar,
                                         get_transformer, report=True, verbose=True)
if error_report:
    print('\n')
    print(error_report)
    sys.exit(1)
else:
    print('\nSUCCESS! All tests passed :-)')
'''


def selftest() -> bool:
    print("DHParser selftest...")
    print("\nSTAGE I:  Trying to compile EBNF-Grammar:\n")
    builtin_ebnf_parser = get_ebnf_grammar()
    ebnf_src = builtin_ebnf_parser.__doc__[builtin_ebnf_parser.__doc__.find('#'):]
    ebnf_transformer = get_ebnf_transformer()
    ebnf_compiler = get_ebnf_compiler('EBNF')
    generated_ebnf_parser, errors, ast = compile_source(ebnf_src, None,
        builtin_ebnf_parser, ebnf_transformer, ebnf_compiler)

    if errors:
        print("Selftest FAILED :-(")
        print("\n\n".join(errors))
        return False
    print(generated_ebnf_parser)
    print("\n\nSTAGE 2: Selfhosting-test: Trying to compile EBNF-Grammar with generated parser...\n")
    selfhosted_ebnf_parser = compileDSL(ebnf_src, None, generated_ebnf_parser,
                                        ebnf_transformer, ebnf_compiler)
    ebnf_compiler.gen_transformer_skeleton()
    print(selfhosted_ebnf_parser)
    print("\n\n Selftest SUCCEEDED :-)\n\n")
    return True


def create_project(path,
                   ebnf_tmpl=EBNF_TEMPLATE,
                   readme_tmpl=README_TEMPLATE,
                   grammar_test_tmpl=GRAMMAR_TEST_TEMPLATE):
    def create_file(name, content):
        if not os.path.exists(name):
            print('Creating file "%s".' % name)
            with open(name, 'w') as f:
                f.write(content)
        else:
            print('"%s" already exists! Not overwritten.' % name)

    if os.path.exists(path) and not os.path.isdir(path):
        print('Cannot create new project, because a file named "%s" alread exists!' % path)
        sys.exit(1)
    name = os.path.basename(path)
    print('Creating new DHParser-project "%s".' % name)
    if not os.path.exists(path):
        os.mkdir(path)
    curr_dir = os.getcwd()
    os.chdir(path)
    if os.path.exists('grammar_tests'):
        if not os.path.isdir('grammar_tests'):
            print('Cannot overwrite existing file "grammar_tests"')
            sys.exit(1)
    else:
        os.mkdir('grammar_tests')

    create_file(os.path.join('grammar_tests', '01_test_word.ini'), TEST_WORD_TEMPLATE)
    create_file(os.path.join('grammar_tests', '02_test_document.ini'), TEST_DOCUMENT_TEMPLATE)
    create_file(name + '.ebnf', '# ' + name + EBNF_TEMPLATE)
    create_file('README.md', README_TEMPLATE.format(name=name))
    create_file('tst_%s_grammar.py' % name, GRAMMAR_TEST_TEMPLATE.format(name=name))
    os.chdir(curr_dir)
    print('ready.')


def cpu_profile(func, repetitions=1):
    import cProfile, pstats
    pr = cProfile.Profile()
    pr.enable()
    for i in range(repetitions):
        success = func()
        if not success:
            break
    pr.disable()
    # after your program ends
    st = pstats.Stats(pr)
    st.strip_dirs()
    st.sort_stats('time').print_stats(40)
    return success


def mem_profile(func, dummy=0):
    import tracemalloc
    tracemalloc.start()
    success = func()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    print("[ Top 20 ]")
    for stat in top_stats[:20]:
        print(stat)
    return success


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1]):
            _errors = compile_on_disk(sys.argv[1],
                                      sys.argv[2] if len(sys.argv) > 2 else "")
            if _errors:
                print('\n\n'.join(_errors))
                sys.exit(1)
        else:
            create_project(sys.argv[1])
    else:
        # run self test
        # selftest('EBNF/EBNF.ebnf')
        with logging(False):
            if not cpu_profile(selftest, 1):
                sys.exit(1)

