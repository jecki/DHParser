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

from __future__ import annotations

import sys
assert sys.version_info >= (3, 6, 0), "DHParser requires at least Python-Version 3.6!"

from .compile import *
from .configuration import *
from .dsl import *
from .ebnf import *
from .error import *
from .log import *
# from .lsp import *
from .parse import *
from .preprocess import *
# from .server import *
from .stringview import *
from .nodetree import *
# from .testing import *
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
           # lsp.__all__ +
           parse.__all__ +
           preprocess.__all__ +
           # server.__all__ +
           stringview.__all__ +
           nodetree.__all__ +
           # testing.__all__ +
           toolkit.__all__ +
           trace.__all__ +
           transform.__all__ +
           versionnumber.__all__)

name = "DHParser"
__title__ = "DHParser"
__description__ = "Construction-Kit for Domain Specific Languages"
__url__ = 'https://gitlab.lrz.de/badw-it/DHParser'
__uri__ = __url__
__author__ = "Eckhart Arnold"
__email__ = "eckhart.arnold@posteo.de"
__license__ = "http://www.apache.org/licenses/LICENSE-2.0"
__copyright__ = "Copyright (c) 2016-2021 Eckhart Arnold"
# __all__ = ['toolkit', 'stringview', 'error', 'nodetree', 'preprocess', 'parse',
# 'transform', 'ebnf', 'dsl', 'testing', 'versionnumber', 'configuration']
