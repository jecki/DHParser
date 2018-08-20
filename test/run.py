#!/usr/bin/python

"""Runs the dhparser test-suite with several installed interpreters"""

if __name__ == "__main__":
    import os
    import platform

    scriptdir = os.path.dirname(os.path.realpath(__file__))

    # if os.getcwd().endswith('test'):
    #     os.chdir('..')
    # print("Running nosetests:")
    # os.system("nosetests test")
    if platform.system() != "Windows":
        interpreters = ['python ', 'pypy3 ', 'python37 ']
    else:
        interpreters = [r'C:\Users\di68kap\AppData\Local\Programs\Python\Python37-32\python.exe ']

    cwd = os.getcwd()

    for interpreter in interpreters:
        os.system(interpreter + '--version')

        # unit tests

        os.chdir(scriptdir)

        assert os.getcwd().endswith('test')
        files = os.listdir()
        for filename in files:
            if filename.startswith('test_'):
                print('\nUNITTEST ' + filename)
                os.system(interpreter + filename)

        # doctests

        os.chdir('..')
        files = os.listdir('DHParser')
        for filename in files:
            if filename.endswith('.py') and filename \
                    not in ["foreign_typing.py", "stringview.py", "__init__.py"]:
                filepath = os.path.join('DHParser', filename)
                print('\nDOCTESTS in ' + filepath)
                os.system(interpreter + ' -m doctest ' + filepath)

    os.chdir(cwd)
