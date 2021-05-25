#!/usr/bin/env python3

"""Runs the dhparser test-suite with several installed interpreters"""

import concurrent.futures
import doctest
import os
import subprocess
import sys
import time
import threading

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(scriptdir, '../'))

from DHParser.configuration import get_config_value
from DHParser.toolkit import instantiate_executor


lock = None  # threading.Lock() initialized in __main__


def run_cmd(parameters: list):
    try:
        subprocess.run(parameters)
        return True
    except FileNotFoundError:
        return False


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
    print('COMPLETED ' + args[0] + ' ' + filename + '\n')


if __name__ == "__main__":
    lock = threading.Lock()
    found = []
    if run_cmd(['pypy3', '-V']):
        found.append('pypy3 ')
    elif run_cmd(['pypy36', '-V']):
        found.append('pypy36 ')
    elif run_cmd(['pypy', '-V']):
        found.append('pypy ')
    if run_cmd(['python', '-V']):
        output = subprocess.run(['python', '-V'], capture_output=True).stdout
        if output.find(b'Python 3') >= 0:
            found.append('python ')
        elif run_cmd(['python3', '-V']):
            found.append('python3')
    elif run_cmd(['python3', '-V']):
        found.append('python3')
    # if run_cmd(['python3.5', '-V']):
    #     found.append('python3.5 ')
    # elif run_cmd(['~/.local/bin/python3.5', '-V']):
    #     found.append('~/.local/bin/python3.5 ')
    if run_cmd(['python3.6', '-V']):
        found.append('python3.6 ')
    elif run_cmd(['~/.local/bin/python3.6', '-V']):
        found.append('~/.local/bin/python3.6 ')
    if run_cmd(['python3.7', '-V']):
        found.append('python3.7 ')
    elif run_cmd(['~/.local/bin/python3.7', '-V']):
        found.append('~/.local/bin/python3.7 ')
    if run_cmd(['python3.9', '-V']):
        found.append('python3.8 ')
    elif run_cmd(['~/.local/bin/python3.8', '-V']):
        found.append('~/.local/bin/python3.8 ')
    print('Interpreters found: ' + ''.join(found))

    arguments = [arg for arg in sys.argv[1:] if arg[:1] != '-']

    if len(arguments) > 1:
        # use interpreters from command line
        interpreters = []
        for interpreter in arguments:
            interpreter = interpreter.strip() + ' '
            if interpreter not in found:
                print('Interpreter ' + arguments[1] + ' not found.')
                sys.exit(1)
            else:
                interpreters.append(interpreter)
    else:
        interpreters = found

    cwd = os.getcwd()
    os.chdir(os.path.join(scriptdir, '..'))

    timestamp = time.time()

    run_doctests('toolkit')

    with instantiate_executor(get_config_value('test_parallelization'),
                              concurrent.futures.ProcessPoolExecutor) as pool:
        results = []

        # doctests
        for filename in os.listdir('DHParser'):
            if filename.endswith('.py') and filename not in \
                    ("foreign_typing.py", "shadow_cython.py", "versionnumber.py",
                     "__init__.py"):
                results.append(pool.submit(run_doctests, filename[:-3]))

        # unit tests
        for interpreter in interpreters:
            if run_cmd([interpreter.strip(), '--version']):
                for filename in os.listdir('tests'):
                    if filename.endswith('.py') and (filename.startswith('test_') or
                                                     filename.startswith('notest')):
                        command = interpreter + os.path.join('tests', filename)
                        results.append(pool.submit(run_unittests, command))

        done, not_done = concurrent.futures.wait(results, timeout=120)
        assert not not_done, str(not_done)

    elapsed = time.time() - timestamp
    print('\n Test-Duration: %.2f seconds' % elapsed)

    print('\nPlease note, the following phenomena are not bugs:')
    print('  1. Some doctests may fail on Windows, due to different file-separators.')
    print('  2. Some doctests may fail with Python 3.5, because in Python 3.5 the order '
          'of entries in a dictionary is undetermined.')
    print('  3. Some tests end with OSError("handle already closed") on pypy3.6, 3.7. '
          'This seems to be a python < 3.9 bug. See: pypy3 scratch/process_pool_doc_examples.py')

    os.chdir(cwd)
