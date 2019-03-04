#!/usr/bin/python3

"""rename_project.py - rename a dhparser project properly

Copyright 2019  by Eckhart Arnold (arnold@badw.de)
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
import re
import shutil
import sys


def save_project(path: str) -> bool:
    """Copies the old project to another directory."""
    if os.path.exists(path + '_save'):
        return False
    shutil.copytree(path, path + '_save')
    return True


def check_projectdir(path: str) -> bool:
    """Verifies that `path` if a valid DHParser project directory."""
    name = os.path.basename(path)

    def check(*args):
        for filename in args:
            filepath = os.path.join(path, filename)
            if not (os.path.exists(filepath) and os.path.isfile(filepath)):
                print('Could not find ' + filepath)
                return False
        return True

    return check(name + '.ebnf', name + 'Compiler.py', "tst_%s_grammar.py" % name)


def rename_projectdir(path: str, new: str) -> bool:
    """
    Renames the dhparser project in `path`. This implies renaming
    the directory itself, the test and compile script and the data types
    and variables that contain the project's name as part of their name.
    """
    name = os.path.basename(path)
    save = os.getcwd()
    os.chdir(path)
    os.rename(name + '.ebnf', new + '.ebnf')
    os.rename(name + 'Compiler.py', new + 'Compiler.py')
    os.rename('tst_%s_grammar.py' % name, 'tst_%s_grammar.py' % new)
    for fname in (new + 'Compiler.py', 'tst_%s_grammar.py' % new):
        with open(fname, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(content.replace(name, new))
    os.chdir('..')
    os.rename(name, new)
    os.chdir(save)


if __name__ == "__main__":
    if len(sys.argv) == 3:
        projectdir = sys.argv[1]
        new_name = sys.argv[2]
        if not os.path.isdir(projectdir):
            print(projectdir + " is not a directory!")
            sys.exit(1)
        elif check_projectdir(projectdir):
            m = re.match('\w+', new_name)
            if m and len(m.group(0)) == len(new_name):
                if save_project(projectdir):
                    rename_projectdir(projectdir, new_name)
                else:
                    print('Could not save old project to '
                          + os.path.basename(projectdir) + '_saved!')
                    sys.exit(1)
            else:
                print(new_name + " is not a valid project name!")
                sys.exit(1)
        else:
            print(projectdir + " does not seem to be a DHParser-project directory!")
            sys.exit(1)
    else:
        print('Usage: python rename_project.py PROJECT_DIRECTORY NEW_NAME')
