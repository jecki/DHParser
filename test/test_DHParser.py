#!/usr/bin/python3

"""test_DHParser.py - tests of global aspects of DHParser 


Author: Eckhart Arnold <arnold@badw.de>

Copyright 2017 Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
sys.path.extend(['../', './'])

from DHParser.toolkit import *
from DHParser.syntaxtree import *
from DHParser.parsers import *
from DHParser.ebnf import *
from DHParser.dsl import *


if __name__ == "__main__":
    from DHParser.testing import runner

    runner("", globals())