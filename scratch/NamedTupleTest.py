# see: https://stackoverflow.com/questions/33796490/why-cant-i-pickle-a-typing-namedtuple-while-i-can-pickle-a-collections-namedtup

from collections import namedtuple
from typing import NamedTuple

PersonTyping = NamedTuple('PersonTyping', [('firstname',str),('lastname',str)])
PersonCollections = namedtuple('PersonCollections', ['firstname','lastname'])

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