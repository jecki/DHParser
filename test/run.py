#!/usr/bin/python

if __name__ == "__main__":
    import os

    if os.getcwd().endswith('test'):
        os.chdir('..')
    print("Running nosetests:")
    os.system("nosetests")
