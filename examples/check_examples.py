#!/usr/bin/env python3

"""Goes through all examples and runs any tst_*.py or recompile_grammar.py
scripts"""

import fnmatch
import platform
import os
import sys


if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    rootdir = scriptdir[:-8]

    if platform.system() != "Windows":
        interpreter = 'python3 '
    else:
        interpreter = 'python.exe '

    example_dirs = os.listdir(os.path.join(rootdir, 'examples'))

    run = 0
    failures = 0

    def check(ret):
        global run, failures
        run += 1
        if ret > 0:
            failures += 1
            print("********** FAILURE **********")

    for example in example_dirs:
        example_path = os.path.join(rootdir, 'examples', example)
        if os.path.isdir(example_path):
            save = os.getcwd()
            os.chdir(example_path)
            ebnf = []
            for name in os.listdir(example_path):
                if name.lower().endswith('.ebnf'):
                    ebnf.append(name)
            for name in os.listdir(example_path):
                if os.path.isfile(name) \
                        and (name == "recompile_grammar.py" or fnmatch.fnmatch(name, 'tst_*.py')):
                    print(os.path.join(example_path, name))
                    for grammar in ebnf:
                        call = interpreter + name + ' ' + grammar
                        print("CALL: ", call)
                        check(os.system(call))
                    call = interpreter + name
                    print("CALL: ", call)
                    check(os.system(call))
            os.chdir(save)

    save = os.getcwd()
    os.chdir(os.path.join(scriptdir, 'Introduction'))
    python = sys.executable + ' '
    check(os.system(python + ' LyrikParser.py Lyrisches_Intermezzo_IV.txt'))
    check(os.system(python + ' LyrikParser_example.py Lyrisches_Intermezzo_IV.txt'))

    os.chdir(save)
    print()
    print("{} tests run, {} tests failed".format(run, failures))
