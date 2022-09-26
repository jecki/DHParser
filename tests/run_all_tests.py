#!/usr/bin/env python3

"""Runs the dhparser test-suite with several installed interpreters"""

import concurrent.futures
import multiprocessing
import os
import subprocess
import sys
import time
import threading

scriptdir = os.path.dirname(os.path.realpath(__file__))
doc_paths = [os.path.join('documentation_src'),
             os.path.join('documentation_src', 'manuals')]
# sys.path.append(os.path.join(scriptdir, '../'))

from DHParser.configuration import get_config_value
from DHParser.toolkit import instantiate_executor


lock = None
interpreters = ['python ']


def run_cmd(parameters: list):
    try:
        subprocess.run(parameters)
        return True
    except FileNotFoundError:
        return False


#TODO: No doctest-errors reported on Windows!?
def run_doctests_rst(rst_path):
    global lock
    import doctest
    # with lock:
    print('DOCTEST ' + rst_path)
    try:
        result = doctest.testfile(os.path.join('..', rst_path))
        return result.failed
    except Exception as e:
        print("**********************************************************************")
        print(f"Exception while procesing {rst_path}", e)
        print("**********************************************************************")


def run_doctests(module):
    global lock
    import doctest
    # with lock:
    namespace = {}
    print('DOCTEST ' + module)
    # exec('import DHParser.' + module, namespace)
    exec('from DHParser import ' + module, namespace)
    mod = namespace[module]
    result = doctest.testmod(mod)
    return result.failed


def run_unittests(command):
    args = command.split(' ')
    filename = args[1]
    print('\nUNITTEST ' + args[0] + ' ' + filename)
    subprocess.run(args)
    print('COMPLETED ' + args[0] + ' ' + filename + '\n')


def gather_interpreters():
    global interpreters
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
    # if run_cmd(['python3.6', '-V']):
    #     found.append('python3.6 ')
    # elif run_cmd(['~/.local/bin/python3.6', '-V']):
    #     found.append('~/.local/bin/python3.6 ')
    if run_cmd(['python3.7', '-V']):
        found.append('python3.7 ')
    elif run_cmd(['~/.local/bin/python3.7', '-V']):
        found.append('~/.local/bin/python3.7 ')
    if run_cmd(['python3.8', '-V']):
        found.append('python3.8 ')
    elif run_cmd(['~/.local/bin/python3.8', '-V']):
        found.append('~/.local/bin/python3.8 ')
    if run_cmd(['python3.9', '-V']):
        found.append('python3.9 ')
    elif run_cmd(['~/.local/bin/python3.9', '-V']):
        found.append('~/.local/bin/python3.9 ')
    if run_cmd(['python3.10', '-V']):
        found.append('python3.10 ')
    elif run_cmd(['~/.local/bin/python3.10', '-V']):
        found.append('~/.local/bin/python3.10 ')
    if run_cmd(['python3.11', '-V']):
        found.append('python3.11 ')
    elif run_cmd(['~/.local/bin/python3.11', '-V']):
        found.append('~/.local/bin/python3.11 ')
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


def run_tests(doctests=True, unittests=True):
    global lock
    if lock is None:
        lock = multiprocessing.Lock()

    cwd = os.getcwd()
    os.chdir(os.path.join(scriptdir, '..'))

    done, not_done = [], []
    with instantiate_executor(get_config_value('test_parallelization'),
                              concurrent.futures.ProcessPoolExecutor) as pool:
        results = []

        if doctests:
            # documentation doctests
            sys.path.append('documentation_src')
            for doc_path in doc_paths:
                for filename in os.listdir(doc_path):
                    if filename.endswith('.rst'):
                        filepath = os.path.join(doc_path, filename)
                        results.append((filepath, pool.submit(run_doctests_rst, filepath)))

            # module doctests
            for filename in os.listdir('DHParser'):
                if filename.endswith('.py') and filename not in \
                        ("foreign_typing.py", "shadow_cython.py", "versionnumber.py",
                         "__init__.py"):
                    results.append((filename[:-3], pool.submit(run_doctests, filename[:-3])))

        if unittests:
            # unit tests
            for interpreter in interpreters:
                if run_cmd([interpreter.strip(), '--version']):
                    for filename in os.listdir('tests'):
                        if filename.endswith('.py') and (filename.startswith('test_') or
                                                         filename.startswith('notest')):
                            command = interpreter + os.path.join('tests', filename)
                            results.append((command, pool.submit(run_unittests, command)))
        done, not_done = concurrent.futures.wait([r[1] for r in results], timeout=180)

    os.chdir(cwd)
    for test, result in results:
        r_exception = result.exception()
        if r_exception:
            print(f'"{test}" failed with exception: {repr(r_exception)}')
            _ = result.result()  # raise the exception
        r_code = result.result()
        if r_code != 0 and r_code is not None:
            print(f'"{test}" failed with result: {r_code}')
    assert not not_done, str(not_done)


if __name__ == "__main__":
    gather_interpreters()

    timestamp = time.time()

    run_tests(doctests=True, unittests=True)

    elapsed = time.time() - timestamp
    print('\n Test-Duration: %.2f seconds' % elapsed)

    print('\nPlease note, the following phenomena are not bugs:')
    print('  1. Some doctests may fail on Windows, due to different file-separators.')
    print('  2. Some tests end with OSError("handle already closed") on pypy3.6, 3.7. '
          'This seems to be a python < 3.9 bug. See: pypy3 scratch/process_pool_doc_examples.py')
    print('  3. Occasionally, notest_server_tcp.TestServer.test_long_running_task() will '
          'raise the "AssertionError: [0.02, 0.001, 0.02, 0.001]" as a false negative.')

