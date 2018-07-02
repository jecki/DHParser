#!/usr/bin/python

if __name__ == "__main__":
    import os

    # if os.getcwd().endswith('test'):
    #     os.chdir('..')
    # print("Running nosetests:")
    # os.system("nosetests test")

    interpreter = 'python '
    # interpreter = r'C:\Users\di68kap\AppData\Local\Programs\Python\Python37-32\python.exe '

    os.system(interpreter + '--version')

    assert os.getcwd().endswith('test')
    files = os.listdir()
    for filename in files:
        if filename.startswith('test_'):
            print('\nTEST ' + filename)
            os.system(interpreter + filename)
