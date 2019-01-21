#!/usr/bin/python

"""Goes through all examples and runs any tst_*.py or recompile_grammar.py
scripts"""

import fnmatch
import os
import platform

if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.realpath(__file__))
    rootdir = scriptdir[:scriptdir.find('DHParser') + 8]

    if platform.system() != "Windows":
        interpreter = 'python3 '
    else:
        interpreter = 'python.exe '

    example_dirs = os.listdir(os.path.join(rootdir, 'examples'))
    run = 0
    failures = 0
    for example in example_dirs:
        example_path = os.path.join(rootdir, 'examples', example)
        if os.path.isdir(example_path):
            save = os.getcwd()
            os.chdir(example_path)
            for name in os.listdir(example_path):
                if os.path.isfile(name) \
                        and (name == "recompile_grammar.py" or fnmatch.fnmatch(name, 'tst_*.py')):
                    print(os.path.join(example_path, name))
                    ret = os.system(interpreter + name)
                    run += 1
                    if ret > 0:
                        failures += 1
            os.chdir(save)
    print()
    print("{} tests run, {} tests failed".format(run, failures))
