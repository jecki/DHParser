import sys, os

print(os.path.abspath(__file__))

sys.path.append('../')

from DHParser import configuration

print(configuration.scriptpath)
