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

# Flat namespace for the DHParser Package. Is this a good idea...?

import sys
assert sys.version_info >= (3, 5, 3), "DHParser requires at least Python-Version 3.5.3!"

from .compile import *
from .configuration import *
from .dsl import *
from .ebnf import *
from .error import *
from .log import *
from .parse import *
from .preprocess import *
from .server import *
from .stringview import *
from .syntaxtree import *
from .testing import *
from .toolkit import *
from .trace import *
from .transform import *
from .versionnumber import *

__all__ = (compile.__all__ +
           configuration.__all__ +
           dsl.__all__ +
           ebnf.__all__ +
           error.__all__ +
           log.__all__ +
           parse.__all__ +
           preprocess.__all__ +
           server.__all__ +
           stringview.__all__ +
           syntaxtree.__all__ +
           testing.__all__ +
           toolkit.__all__ +
           trace.__all__ +
           transform.__all__ +
           versionnumber.__all__)

name = "DHParser"
__author__ = "Eckhart Arnold <arnold@badw.de>"
__copyright__ = "http://www.apache.org/licenses/LICENSE-2.0"
# __all__ = ['toolkit', 'stringview', 'error', 'syntaxtree', 'preprocess', 'parse',
# 'transform', 'ebnf', 'dsl', 'testing', 'versionnumber', 'configuration']
