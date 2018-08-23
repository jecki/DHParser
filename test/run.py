#!/usr/bin/python

"""Runs the dhparser test-suite with several installed interpreters"""

import concurrent.futures
import os
import platform
import time



def run_tests(testtype, command):
    filename = command[command.rfind(' ')+1:]
    print('\n' + testtype + ' ' + filename)
    os.system(command)


def run_unittests(command):
    run_tests('UNITTESTS', command)


def run_doctests(command):
    print(os.getcwd())
    run_tests('DOCTESTS', command)


if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.realpath(__file__))

    # if os.getcwd().endswith('test'):
    #     os.chdir('..')
    # print("Running nosetests:")
    # os.system("nosetests test")
    if platform.system() != "Windows":
        interpreters = ['python ', 'pypy3 ', 'python37 ']
    else:
        interpreters = ['python.exe ']

    cwd = os.getcwd()
    os.chdir(scriptdir + '/..')

    timestamp = time.time()

    with concurrent.futures.ProcessPoolExecutor(4) as pool:
        for interpreter in interpreters:
            os.system(interpreter + '--version')

            # unit tests

            commands = [interpreter + os.path.join('test', filename)
                        for filename in os.listdir('test') if filename.startswith('test_')]
            pool.map(run_unittests, commands)

            # doctests

            commands = [interpreter + ' -m doctest ' + os.path.join('DHParser', filename)
                        for filename in os.listdir('DHParser') if filename.endswith('.py')
                        and filename not in ["foreign_typing.py", "stringview.py", "__init__.py"]]
            pool.map(run_doctests, commands)

    elapsed = time.time() - timestamp
    print('\n Test-Duration: %.2f seconds' % elapsed)

    os.chdir(cwd)
