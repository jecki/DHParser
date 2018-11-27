#!/usr/bin/python

"""Runs the dhparser test-suite with several installed interpreters"""

import concurrent.futures
import multiprocessing
import os
import platform
import time


def run_tests(command):
    testtype = 'DOCTEST' if command.find('doctest') >= 0 else 'UNITTEST'
    filename = command[command.rfind(' ') + 1:]
    print('\n' + testtype + ' ' + filename)
    os.system(command)


if __name__ == "__main__":
    scriptdir = os.path.dirname(os.path.realpath(__file__))

    # if os.getcwd().endswith('test'):
    #     os.chdir('..')
    # print("Running nosetests:")
    # os.system("nosetests test")
    if platform.system() != "Windows":
        interpreters = ['pypy3 ', 'python3 ']
    else:
        interpreters = ['python.exe ']

    cwd = os.getcwd()
    os.chdir(scriptdir + '/..')

    timestamp = time.time()

    with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
        for interpreter in interpreters:
            os.system(interpreter + '--version')

            # doctests
            commands = [interpreter + ' -m doctest ' + os.path.join('DHParser', filename)
                        for filename in os.listdir('DHParser') if filename.endswith('.py')
                        and filename not in ["foreign_typing.py", "stringview.py", "__init__.py"]]

            # unit tests
            commands += [interpreter + os.path.join('test', filename)
                         for filename in os.listdir('test') if filename.startswith('test_')]

            pool.map(run_tests, commands)

    elapsed = time.time() - timestamp
    print('\n Test-Duration: %.2f seconds' % elapsed)

    os.chdir(cwd)
