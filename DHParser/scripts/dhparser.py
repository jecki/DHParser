#!/usr/bin/python3

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

import os
import sys
from typing import cast

scriptdir = os.path.dirname(os.path.abspath(__file__))
i, k = scriptdir.find('DHParser-submodule'), len('DHParser-submodule')
if i < 0:
    i, k = scriptdir.find('DHParser'), len('DHParser')
if i >= 0:
    dhparserdir = scriptdir[:i + k]
    if dhparserdir not in sys.path:
        sys.path.append(dhparserdir)
else:
    dhparserdir = ''

templatedir = os.path.join(os.path.dirname(scriptdir.rstrip('/')), 'templates')

from DHParser.compile import compile_source
from DHParser.dsl import compileDSL, compile_on_disk  # , recompile_grammar
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.log import start_logging
from DHParser.toolkit import re


LOGGING = False


def read_template(template_name: str) -> str:
    """
    Reads a script-template from a template file named `template_name`
    in the template-directory and returns it as a string.
    """
    with open(os.path.join(templatedir, template_name), 'r', encoding='utf-8') as f:
        return f.read()


def create_project(path: str):
    """Creates the a new DHParser-project in the given `path`.
    """
    def create_file(name, content):
        """Create a file with `name` and write `content` to file."""
        if not os.path.exists(name):
            print('Creating file "%s".' % name)
            with open(name, 'w', encoding='utf-8') as f:
                f.write(content)
        else:
            print('"%s" already exists! Not overwritten.' % name)

    EBNF_TEMPLATE = read_template('example_DSL.ebnf')
    TEST_WORD_TEMPLATE = read_template('example_01_test_Regular_Expressions.ini')
    TEST_DOCUMENT_TEMPLATE = read_template('example_02_test_Structure_and_Components.ini')
    README_TEMPLATE = read_template('readme_template.md')
    GRAMMAR_TEST_TEMPLATE = read_template('tst_DSL_grammar.pyi')
    SERVER_TEMPLATE = read_template('DSLServer.pyi')

    name = os.path.basename(path)
    if not re.match(r'(?!\d)\w+', name):
        print('Project name "%s" is not a valid identifier! Aborting.' % name)
        sys.exit(1)
    if os.path.exists(path) and not os.path.isdir(path):
        print('Cannot create new project, because a file named "%s" already exists!' % path)
        sys.exit(1)
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

    create_file(os.path.join('grammar_tests', '01_test_Regular_Expressions.ini'),
                TEST_WORD_TEMPLATE)
    create_file(os.path.join('grammar_tests', '02_test_Structure_and_Components.ini'),
                TEST_DOCUMENT_TEMPLATE)
    create_file(name + '.ebnf', EBNF_TEMPLATE.replace('GRAMMAR_NAME', name, 1))
    create_file('README.md', README_TEMPLATE.format(name=name))
    reldhparserdir = os.path.relpath(dhparserdir, os.path.abspath('.'))
    create_file('tst_%s_grammar.py' % name, GRAMMAR_TEST_TEMPLATE.format(
        name=name, reldhparserdir=reldhparserdir))
    create_file('%sServer.py' % name, SERVER_TEMPLATE.replace('DSL', name).replace(
        'RELDHPARSERDIR', reldhparserdir))
    create_file('example.dsl', 'Life is but a walking shadow\n')
    os.chmod('tst_%s_grammar.py' % name, 0o755)
    os.chmod('%sServer.py' % name, 0o755)
    # The following is left to the user as an exercise
    # print('Creating file "%s".' % (name + 'Compiler.py'))
    # recompile_grammar(name + '.ebnf', force=True)
    print('\nNow generate a DSL compiler from the EBNF-grammar by running\n'
          '\n    python tst_%s_gramar.py\n' % name)
    os.chdir(curr_dir)


def selftest() -> bool:
    """Run a simple self-test of DHParser.
    """
    print("DHParser selftest...")
    print("\nSTAGE I:  Trying to compile EBNF-Grammar:\n")
    builtin_ebnf_parser = get_ebnf_grammar()
    docstring = str(builtin_ebnf_parser.__doc__)  # type: str
    ebnf_src = docstring[docstring.find('@'):]
    ebnf_transformer = get_ebnf_transformer()
    ebnf_compiler = get_ebnf_compiler('EBNF')
    result, errors, _ = compile_source(
        ebnf_src, None,
        builtin_ebnf_parser, ebnf_transformer, ebnf_compiler)
    generated_ebnf_parser = cast(str, result)

    if errors:
        print("Selftest FAILED :-(")
        print("\n\n".join(str(err) for err in errors))
        return False
    print(generated_ebnf_parser)
    print("\n\nSTAGE 2: Selfhosting-test: "
          "Trying to compile EBNF-Grammar with generated parser...\n")
    selfhosted_ebnf_parser = compileDSL(ebnf_src, None, generated_ebnf_parser,
                                        ebnf_transformer, ebnf_compiler)
    ebnf_compiler.gen_transformer_skeleton()
    print(selfhosted_ebnf_parser)
    return True


def cpu_profile(func, repetitions=1):
    """Profile the function `func`.
    """
    import cProfile
    import pstats
    profile = cProfile.Profile()
    profile.enable()
    success = True
    for _ in range(repetitions):
        success = func()
        if not success:
            break
    profile.disable()
    # after your program ends
    stats = pstats.Stats(profile)
    stats.strip_dirs()
    stats.sort_stats('time').print_stats(40)
    return success


def mem_profile(func):
    """Profile memory usage of `func`.
    """
    import tracemalloc
    tracemalloc.start()
    success = func()
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    print("[ Top 20 ]")
    for stat in top_stats[:20]:
        print(stat)
    return success


def main():
    """Creates a project (if a project name has been passed as command line
    parameter) or runs a quick self-test.
    """
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--selftest":
            if not selftest():
                print("Selftest FAILED :-(\n")
                sys.exit(1)
            print("Selftest SUCCEEDED :-)\n")
        elif os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1]):
            _errors = compile_on_disk(sys.argv[1],
                                      sys.argv[2] if len(sys.argv) > 2 else "")
            if _errors:
                print('\n\n'.join(str(err) for err in _errors))
                sys.exit(1)
        else:
            create_project(sys.argv[1])
    else:
        print('Usage: \n'
              '    dhparser.py DSL_FILENAME [COMPILER]  - to compile a file\n'
              '    dhparser.py PROJECTNAME  - to create a new project\n\n')
        choice = input('Would you now like to ...\n'
                       '  [1] create a new project\n'
                       '  [2] compile an ebnf-grammar or a dsl-file\n'
                       '  [3] run a self-test\n'
                       '  [q] to quit\n'
                       'Please chose 1, 2 or 3> ')
        if choice.strip() == '1':
            project_name = input('Please project name or path > ')
            create_project(project_name)
        elif choice.strip() == '2':
            file_path = input('Please enter a file path for compilation > ')
            if os.path.exists(file_path) and os.path.isfile(file_path):
                compiler_suite = input('Compiler suite or ENTER (for ebnf) > ')
                if not compiler_suite or (os.path.exists(compiler_suite)
                                          and os.path.isfile(compiler_suite)):
                    _errors = compile_on_disk(file_path, compiler_suite)
                    if _errors:
                        print('\n\n'.join(str(err) for err in _errors))
                        sys.exit(1)
                else:
                    print('Compiler suite %s not found! Aborting' % compiler_suite)
            else:
                print('File %s not found! Aborting.' % file_path)
                sys.exit(1)
        elif choice.strip() == '3':
            if LOGGING:
                start_logging(LOGGING)
            if not cpu_profile(selftest, 1):
                print("Selftest FAILED :-(\n")
                sys.exit(1)
            print("Selftest SUCCEEDED :-)\n")
        elif choice.strip().lower() not in {'q', 'quit', 'exit'}:
            print('No valid choice. Goodbye!')


if __name__ == "__main__":
    main()
