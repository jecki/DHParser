#!/usr/bin/env python3

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

from functools import partial
import os
import sys
from typing import cast

scriptdir = os.path.dirname(os.path.abspath(__file__))
i = scriptdir.find('DHParser')
k = len('DHParser-submodule') if scriptdir[i:].startswith('DHParser-submodule') \
    else len('DHParser')
if i >= 0:
    dhparserdir = scriptdir[:i + k]
    if dhparserdir not in sys.path:
        sys.path.append(dhparserdir)
else:
    dhparserdir = ''


from DHParser.compile import compile_source
from DHParser.configuration import access_presets, set_preset_value, finalize_presets
from DHParser.dsl import compileDSL, compile_on_disk, read_template
from DHParser.error import is_error, has_errors, ERROR
from DHParser.ebnf import get_ebnf_grammar, get_ebnf_transformer, get_ebnf_compiler
from DHParser.log import start_logging
from DHParser.toolkit import re, split_path


LOGGING = False
TEST_DIRNAME = 'tests_grammar'


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
    # SERVER_TEMPLATE = read_template('DSLServer.pyi')

    name = os.path.basename(path)
    if not re.match(r'(?!\d)\w+', name):
        print('Project name "%s" is not a valid identifier! Aborting.' % name)
        sys.exit(1)
    if os.path.exists(path) and not os.path.isdir(path):
        print('Cannot create new project, because a file named "%s" already exists!' % path)
        sys.exit(1)
    print('Creating new DHParser-project "%s".' % name)
    if not os.path.exists(path):
        try:
            os.mkdir(path)
        except FileNotFoundError as e:
            print('Path "%s" does not exist. Cannot create directory "%s", there.'
                  % os.path.split(path))
            sys.exit(1)
    curr_dir = os.getcwd()
    os.chdir(path)
    if os.path.exists(TEST_DIRNAME):
        if not os.path.isdir(TEST_DIRNAME):
            print('Cannot overwrite existing file "%s"' % TEST_DIRNAME)
            sys.exit(1)
    else:
        os.mkdir(TEST_DIRNAME)

    create_file(os.path.join(TEST_DIRNAME, '01_test_Regular_Expressions.ini'),
                TEST_WORD_TEMPLATE)
    create_file(os.path.join(TEST_DIRNAME, '02_test_Structure_and_Components.ini'),
                TEST_DOCUMENT_TEMPLATE)
    create_file(name + '.ebnf', EBNF_TEMPLATE.replace('GRAMMAR_NAME', name, 1))
    create_file('README.md', README_TEMPLATE.format(name=name))
    reldhparserdir = os.path.relpath(dhparserdir, os.path.abspath('.'))
    grammar_test_py = GRAMMAR_TEST_TEMPLATE.format(
        name=name, reldhparserdir=str(split_path(reldhparserdir))[1:-1])
    create_file(f'tst_{name}_grammar.py', grammar_test_py)
    create_file('example.dsl', 'Life is but a walking shadow\n')
    os.chmod(f'tst_{name}_grammar.py', 0o755)
    # os.chmod('%sServer.py' % name, 0o755)
    # The following is left to the user as an exercise
    # print('Creating file "%s".' % (name + 'Parser.py'))
    # recompile_grammar(name + '.ebnf', force=True)
    print(f'\nNow generate a DSL-parser from the EBNF-grammar by running\n'
          f'\n    python tst_{name}_gramar.py\n')
    os.chdir(curr_dir)


def selftest(silent: bool=False) -> bool:
    """Run a simple self-test of DHParser.
    """
    if not silent:
        print("DHParser selftest...")
        print("\nSTAGE I:  Trying to compile EBNF-Grammar:\n")
    builtin_ebnf_parser = get_ebnf_grammar()
    docstring = str(builtin_ebnf_parser.__doc__)  # type: str
    i = docstring.find('::')
    if i >= 0:
        docstring = docstring[i + 2::]
    ebnf_src = docstring[docstring.find('@'):]
    ebnf_transformer = get_ebnf_transformer()
    ebnf_compiler = get_ebnf_compiler('EBNF')
    result, errors, _ = compile_source(
        ebnf_src, None,
        builtin_ebnf_parser, ebnf_transformer, ebnf_compiler)
    generated_ebnf_parser = cast(str, result)

    if has_errors(errors, ERROR):
        if not silent:
            print("Selftest FAILED :-(")
            print("\n\n".join(str(err) for err in errors))
        return False
    if not silent:
        print(generated_ebnf_parser)
        print("\n\nSTAGE 2: Selfhosting-test: "
              "Trying to compile EBNF-Grammar with generated parser...\n")
    selfhosted_ebnf_parser = compileDSL(ebnf_src, None, generated_ebnf_parser,
                                        ebnf_transformer, ebnf_compiler)
    # ebnf_compiler.gen_transformer_skeleton()
    if not silent:
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
    stats.sort_stats('time').print_stats(80)
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
    access_presets()
    set_preset_value('syntax_variant', 'heuristic')  # TODO: Bugs in Transformation-Table
    finalize_presets()
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "--selftest":
            if not selftest():
                print("Selftest FAILED :-(\n")
                sys.exit(1)
            print("Selftest SUCCEEDED :-)\n")
        else:
            if sys.argv[1].lower() in ('-ast', '--ast'):
                try:
                    with open(sys.argv[2], 'r', encoding='utf-8') as f:
                        ebnf = f.read()
                    syntax_tree = get_ebnf_grammar()(ebnf)
                    if is_error(syntax_tree.error_flag):
                        print('\n\n'.join(str(err) for err in syntax_tree.errors_sorted))
                        sys.exit(1)
                    get_ebnf_transformer()(syntax_tree)
                    if is_error(syntax_tree.error_flag):
                        print('\n\n'.join(str(err) for err in syntax_tree.errors_sorted))
                        sys.exit(1)
                    print(syntax_tree.as_sxpr(compact=True))
                except IndexError:
                    print("Usage:  dhparser.py -ast FILENAME.ebnf")
                    sys.exit(1)
                except FileNotFoundError:
                    print('File "%s" not found!' % sys.arg[2])
                    sys.exit(1)
                except IOError as e:
                    print('Could not read file "%s": %s' % (sys.argv[2], str(e)))
            elif sys.argv[1].lower() in ('-cpu', '--cpu', '-mem', '--mem'):
                try:
                    func = partial(compile_on_disk, source_file=sys.argv[2])
                    if sys.argv[1].lower() in ('-cpu', '--cpu'):
                        _errors = cpu_profile(func, 1)
                    else:
                        _errors = mem_profile(func)
                    if _errors:
                        print('\n'.join(str(err) for err in _errors))
                        sys.exit(1)
                except IndexError:
                    print("Usage:  dhparser.py -cpu/mem FILENAME.ebnf")
                    sys.exit(1)
                except FileNotFoundError:
                    print('File "%s" not found!' % sys.arg[2])
                    sys.exit(1)
                except IOError as e:
                    print('Could not read file "%s": %s' % (sys.argv[2], str(e)))
            elif os.path.exists(sys.argv[1]) and os.path.isfile(sys.argv[1]):
                _errors = compile_on_disk(sys.argv[1])
                if _errors:
                    print('\n'.join(str(err) for err in _errors))
                    sys.exit(1)
                else:
                    print('%s successfully compiled to %s' %
                          (sys.argv[1], os.path.splitext(sys.argv[1])[0] + 'Parser.py'))
            else:
                create_project(sys.argv[1])
    else:
        print('Usage: \n'
              '    dhparser.py PROJECTNAME  - to create a new project\n'
              '    dhparser.py FILENAME.ebnf  - to produce a python-parser from an EBNF-grammar\n'
              '    dhparser.py --selftest  - to run a self-test\n')
        choice = input('\nWould you now like to ...\n'
                       '  [1] create a new project\n'
                       '  [2] compile an ebnf-grammar\n'
                       '  [3] run a self-test\n'
                       '  [q] to quit\n'
                       'Please chose 1, 2 or 3> ')
        if choice.strip() == '1':
            project_name = input('Please project name or path > ')
            create_project(project_name)
        elif choice.strip() == '2':
            file_path = input('Please enter a file path for compilation > ')
            if os.path.exists(file_path) and os.path.isfile(file_path):
                _errors = compile_on_disk(file_path)
                if _errors:
                    print('\n\n'.join(str(err) for err in _errors))
                    sys.exit(1)
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
