"""stringview.py - a stringview class: slicing strings without copying
    (This module merely passes through the Python or Cython version of
    string views. The real implementations are to be found in the
    pstringview.py and cstringview.pyx modules, respectively.)

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

StringView provides string-slicing without copying.
Slicing Python-strings always yields copies of a segment of the original
string. See: https://mail.python.org/pipermail/python-dev/2008-May/079699.html
However, this becomes costly (in terms of space and as a consequence also
time) when parsing longer documents. Unfortunately, Python's `memoryview`
does not work for unicode strings. Hence, the StringView class.
"""
import collections
from typing import Optional, Iterable, Tuple

__all__ = ('StringView', 'EMPTY_STRING_VIEW')

try:
    import pyximport; pyximport.install()
    from DHParser.cstringview import StringView, EMPTY_STRING_VIEW
except ImportError:
    from DHParser.pstringview import StringView, EMPTY_STRING_VIEW

