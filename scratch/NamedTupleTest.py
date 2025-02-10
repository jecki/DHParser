# see: https://stackoverflow.com/questions/33796490/why-cant-i-pickle-a-typing-namedtuple-while-i-can-pickle-a-collections-namedtup

# compile with:

# cython3 --embed -o NamedTupleTest.c NamedTupleTest.py
# $ gcc -Os -I /usr/include/python3.13 -o NamedTupleTest NamedTupleTest.c -lpython3.13 -lpthread -lm -lutil -ldl


from collections import namedtuple
from typing import NamedTuple

PersonTyping = NamedTuple('PersonTyping', [('firstname',str),('lastname',str)])
PersonCollections = namedtuple('PersonCollections', ['firstname','lastname'], module=__name__)

pt = PersonTyping("John","Smith")
pc = PersonCollections("John","Smith")


import pickle
import traceback

try:
    with open('personTyping.pkl', 'wb') as f:
        pickle.dump(pt, f)
except:
    traceback.print_exc()
try:
    with open('personCollections.pkl', 'wb') as f:
        pickle.dump(pc, f)
except:
    traceback.print_exc()
    

