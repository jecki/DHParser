#!/usr/bin/python3

"""Runs the dhparser test-suite with several installed interpreters"""

import concurrent.futures
import doctest
import multiprocessing
import os
import platform
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


# def run_unittests(command):
#     args = command.split(' ')
#     filename = args[1]
#     print('\nUNITTEST ' + filename)
#     subprocess.run(args)


if __name__ == "__main__":
    if platform.system() != "Windows":
        interpreters = ['python3 ', 'pypy3 ']
    else:
        interpreters = ['python.exe ']

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
            os.system(interpreter + '--version')
            # for filename in os.listdir('test'):
            #     if filename.startswith('test_'):
            #         command = interpreter + os.path.join('test', filename)
            #         results.append(pool.submit(run_unittests, command))
            os.system(' '.join([interpreter, '-c',
                                '''"import sys; '''
                                '''sys.path.extend(['DHParser']);''' 
                                '''import testing; testing.run_path('%s')"''' %
                                scriptdir.replace('\\', '\\\\'),
                            os.path.join(os.getcwd(), 'test')]))

        concurrent.futures.wait(results)

    elapsed = time.time() - timestamp
    print('\n Test-Duration: %.2f seconds' % elapsed)

    os.chdir(cwd)
