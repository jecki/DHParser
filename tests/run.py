#!/usr/bin/env python3

"""Runs the dhparser test-suite with several installed interpreters"""

import concurrent.futures
import doctest
import multiprocessing
import os
import subprocess
import sys
import time
import threading

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, '../'))

lock = threading.Lock()


def run_doctests(module):
    with lock:
        namespace = {}
        print('DOCTEST ' + module)
        exec('import DHParser.' + module, namespace)
        mod = getattr(namespace['DHParser'], module)
        result = doctest.testmod(mod)
        return result.failed


def run_unittests(command):
    # print('>>>>>>>> ', command)
    args = command.split(' ')
    filename = args[1]
    print('\nUNITTEST ' + args[0] + ' ' + filename)
    subprocess.run(args)


if __name__ == "__main__":
    interpreters = [sys.executable + ' ']
    # ['python3 ' if os.system('python3 -V') == 0 else 'python ']
    if os.system('python3.5 -V') == 0:
        interpreters.append('python3.5 ')
    elif os.system('~/.local/bin/python3.5 -V') == 0:
        interpreters.append('~/.local/bin/python3.5 ')
    if os.system('python3.6 -V') == 0:
        interpreters.append('python3.6 ')
    elif os.system('~/.local/bin/python3.6 -V') == 0:
        interpreters.append('~/.local/bin/python3.8 ')
    if os.system('python3.7 -V') == 0:
        interpreters.append('python3.7 ')
    elif os.system('~/.local/bin/python3.7 -V') == 0:
        interpreters.append('~/.local/bin/python3.7 ')
    if os.system('pypy3 -V') == 0:
        interpreters.append('pypy3 ')
    elif os.system('pypy -V') == 0:
        interpreters.append('pypy ')
    print('Interpreters found: ' + ''.join(interpreters))

    cwd = os.getcwd()
    os.chdir(os.path.join(scriptdir, '..'))

    timestamp = time.time()

    run_doctests('toolkit')

    with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
        results = []

        # doctests
        for filename in os.listdir('DHParser'):
            if filename.endswith('.py') and filename not in \
                    ("foreign_typing.py", "shadow_cython.py", "versionnumber.py",
                     "__init__.py"):
                results.append(pool.submit(run_doctests, filename[:-3]))

        # unit tests
        for interpreter in interpreters:
            if os.system(interpreter + '--version') == 0:
                for filename in os.listdir('tests'):
                    if filename.endswith('.py') and (filename.startswith('test_') or
                                                     filename.startswith('notest')):
                        command = interpreter + os.path.join('tests', filename)
                        # run_unittests(command)
                        results.append(pool.submit(run_unittests, command))

        concurrent.futures.wait(results)

    elapsed = time.time() - timestamp
    print('\n Test-Duration: %.2f seconds' % elapsed)

    print('\nPlease note, the following phenomena are not bugs:')
    print('  1. Some doctests fail on Windows, due to different file-separators.')
    print('  2. Some doctests fail with Python 3.5, because in Python 3.5 the order '
          'of entries in a dictionary is undetermined.')

    os.chdir(cwd)
