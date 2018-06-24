#!/usr/bin/python3

"""__init__.py - package definition module for DHParser

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

from .compile import *
from .dsl import *
from .ebnf import *
# Flat namespace for the DHParser Package. Is this a good idea...?
from .error import *
from .log import *
from .parse import *
from .preprocess import *
from .stringview import *
from .syntaxtree import *
from .testing import *
from .toolkit import *
from .transform import *
from .versionnumber import __version__

name = "DHParser"
__author__ = "Eckhart Arnold <arnold@badw.de>"
__copyright__ = "http://www.apache.org/licenses/LICENSE-2.0"
# __all__ = ['toolkit', 'stringview', 'error', 'syntaxtree', 'preprocess', 'parse',
# 'transform', 'ebnf', 'dsl', 'testing', 'versionnumber']
