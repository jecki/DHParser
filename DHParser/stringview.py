# stringview.py - a string class where slices are views not copies as
#                    with the standard Python strings.
#
# stringview.pxd - declarations for the cython Python to C compiler
#                    to speed up handling of StringViews.
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""
StringView provides string-slicing without copying.
Slicing Python-strings always yields copies of a segment of the original
string. See: https://mail.python.org/pipermail/python-dev/2008-May/079699.html
However, this becomes costly (in terms of space and as a consequence also
time) when parsing longer documents. Unfortunately, Python's `memoryview`
does not work for unicode strings. Hence, the StringView class.

It is recommended to compile this module with the Cython-compiler for
speedup. The modules comes with a ``stringview.pxd`` that contains some type
declarations to more fully exploit the benefits of the Cython-compiler.
"""

from __future__ import annotations

from typing import Optional, Union, Iterable, Tuple, List, cast
try:
    from typing import TypeAlias
except ImportError:
    from DHParser.externallibs.typing_extensions import TypeAlias

try:
    import cython
    cython_optimized = cython.compiled  # type: bool
    cint: TypeAlias = cython.int
except NameError:
    cint: TypeAlias = int
except ImportError:
    # import DHParser.Shadow as cython
    cython_optimized = False
    import DHParser.externallibs.shadow_cython as cython
    cint: TypeAlias = int


__all__ = ('StringView', 'real_indices', 'EMPTY_STRING_VIEW', 'TextBuffer')


def first_char(text: str,  begin: cint, end: cint, chars: str) -> cint:
    """Returns the index of the first non-whitespace character in string
     `text` within the bounds [begin, end].
    """
    while begin < end and text[begin] in chars:
        begin += 1
    return begin


def last_char(text: str, begin: cint, end: cint, chars: str) -> cint:
    """Returns the index of the last non-whitespace character in string
    `text` within the bounds [begin, end].
    """
    while end > begin and text[end - 1] in chars:
        end -= 1
    return end


def pack_index(index: cint, length: cint) -> cint:
    """Transforms `index` into a positive index counting from the beginning
    of the string, capping it at the boundaries [0, len].
    Examples:
    >>> pack_index(-1, 5)
    4
    >>> pack_index(6, 5)
    5
    >>> pack_index(-7, 5)
    0
    """
    # assert length >= 0
    index = index if index >= 0 else index + length
    return 0 if index < 0 else length if index > length else index

def fast_real_indices(begin: Optional[int],
                      end: Optional[int],
                      length: cint) -> Tuple[cint, cint]:
    """Returns the tuple of real (i.e. positive) indices from the slice
    indices `begin`,  `end`, assuming a string of size `length`.
    """
    cbegin: cint = 0 if begin is None else begin
    cend: cint = length if end is None else end
    return pack_index(cbegin, length), pack_index(cend, length)


def real_indices(begin: Optional[int],
                 end: Optional[int],
                 length: cint) -> Tuple[cint, cint]:
    """Python callable real-indices function for testing."""
    return fast_real_indices(begin, end, length)


class StringView:  # collections.abc.Sized
    """
    A rudimentary StringView class, just enough for the use cases
    in parse.py. The difference between a StringView and the python
    builtin strings is that StringView-objects do slicing without
    copying, i.e. slices are just a view on a section of the sliced
    string.
    """
    __slots__ = ['_text', '_begin', '_end', '_len', '_fullstring']

    @cython.locals(_begin=cython.int, _end=cython.int, _len=cython.int)
    def __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None:
        # assert isinstance(text, str)
        self._text = text  # type: str
        _begin, _end = fast_real_indices(begin, end, len(text))
        _len = _end - _begin  # type: int
        if _len < 0:
            _len = 0
        self._begin = _begin   # type: int
        self._end = _end       # type: int
        self._len = _len       # type: int
        self._fullstring = ''  # type: str

    def __bool__(self) -> bool:
        return self._len != 0  # self._end > self._begin  # and bool(self.text)

    def __len__(self) -> int:
        return self._len

    def __str__(self) -> str:
        """PERFORMANCE WARNING: This creates a copy of the string-slice!"""
        _fullstring = self._fullstring  # type: str
        if _fullstring or self._len == 0:  # optimization: avoid slicing/copying
            return _fullstring
        # since the slice is being copied now, anyway, the copy might
        # as well be stored in the string view
        # return self.text[self.begin:self.end]  # use this for debugging!
        _fullstring = self._text[self._begin:self._end]
        self._fullstring = _fullstring
        return _fullstring

    def __repr__(self) -> str:
        """PERFORMANCE WARNING: This creates a copy of the string-slice!"""
        return repr(str(self))

    @cython.locals(_len=cython.int)
    def __eq__(self, other) -> bool:
        """PERFORMANCE WARNING: This creates copies of the compared string-slices!"""
        # one string copy could be avoided by using find...
        # return len(other) == self._len and str(self) == str(other)
        _len = self._len
        if len(other) == _len:
            if _len == 0:
                return True
            if isinstance(other, StringView) \
                    and self._text is other._text and self._begin == other._begin:
                return True
            _fullstring = self._fullstring  # type: str
            if _fullstring:
                return _fullstring == str(other)
            _fullstring = self._text[self._begin:self._end]
            self._fullstring = _fullstring
            return _fullstring == str(other)
        return False

    def __hash__(self) -> int:
        """PERFORMANCE WARNING: This creates a copy of the string-slice!"""
        return hash(str(self))

    def __add__(self, other) -> Union[str, StringView]:
        if isinstance(other, str):
            return str(self) + other
        else:
            return StringView(str(self) + str(other))

    def __radd__(self, other) -> Union[str, StringView]:
        if isinstance(other, str):
            return other + str(self)
        else:
            return StringView(str(other) + str(self))

    @cython.locals(start=cython.int, stop=cython.int, _begin=cython.int, _index=cython.int)
    def __getitem__(self, index: Union[slice, int]) -> StringView:
        # assert isinstance(index, slice), "As of now, StringView only allows slicing."
        # assert index.step is None or index.step == 1, \
        #     "Step sizes other than 1 are not yet supported by StringView"
        try:
            start, stop = fast_real_indices(index.start, index.stop, self._len)
            _begin = self._begin
            return StringView(self._text, _begin + start, _begin + stop)
        except AttributeError:
            _index = index
            if _index >= self._len:
                raise IndexError("StringView index %i out of range 0 - %i" % (_index, self._len))
            _begin = self._begin
            return StringView(self._text, self._begin + _index, self._begin + _index + 1)
            # return self._text[self._begin + index] # leads to type errors

    def get_text(self) -> str:
        """Returns the underlying string."""
        return self._text

    @cython.locals(_start=cython.int, _end=cython.int)
    def count(self, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int:
        """Returns the number of non-overlapping occurrences of substring
        `sub` in StringView S[start:end].  Optional arguments start and end
        are interpreted as in slice notation.
        """
        if self._fullstring:
            if cython_optimized:
                return self._fullstring.count(sub, start or 0, self._len if end is None else end)
            else:
                return self._fullstring.count(sub, start, end)
        elif start is None and end is None:
            return self._text.count(sub, self._begin, self._end)
        else:
            _start, _end = fast_real_indices(start, end, self._len)
            return self._text.count(sub, self._begin + _start, self._begin + _end)

    @cython.locals(_start=cython.int, _end=cython.int, _begin=cython.int)
    def find(self, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int:
        """Returns the lowest index in S where substring `sub` is found,
        such that `sub` is contained within S[start:end].  Optional
        arguments `start` and `end` are interpreted as in slice notation.
        Returns -1 on failure.
        """
        if self._fullstring:
            if cython_optimized:
                return self._fullstring.find(sub, start or 0, self._len if end is None else end)
            else:
                return self._fullstring.find(sub, start, end)
        elif start is None and end is None:
            _begin = self._begin  # type: int
            return max(self._text.find(sub, _begin, self._end) - _begin, -1)
        else:
            _begin = self._begin  # type: int
            _start, _end = fast_real_indices(start, end, self._len)
            return max(self._text.find(sub, self._begin + _start, _begin + _end) - _begin, -1)

    @cython.locals(_start=cython.int, _end=cython.int, _begin=cython.int)
    def rfind(self, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int:
        """Returns the highest index in S where substring `sub` is found,
        such that `sub` is contained within S[start:end].  Optional
        arguments `start` and `end` are interpreted as in slice notation.
        Returns -1 on failure.
        """
        if self._fullstring:
            if cython_optimized:
                return self._fullstring.rfind(sub, start or 0, self._len if end is None else end)
            else:
                return self._fullstring.rfind(sub, start, end)
        if start is None and end is None:
            _begin = self._begin  # type: int
            return max(self._text.rfind(sub, _begin, self._end) - _begin, -1)
        else:
            _begin = self._begin  # type: int
            _start, _end = fast_real_indices(start, end, self._len)
            return max(self._text.rfind(sub, _begin + _start, _begin + _end) - _begin, -1)

    def startswith(self,
                   prefix: str,
                   start: cint = 0,
                   end: Optional[int] = None) -> bool:
        """Return True if S starts with the specified prefix, False otherwise.
        With optional `start`, test S beginning at that position.
        With optional `end`, stop comparing S at that position.
        """
        start += self._begin
        end = self._end if end is None else self._begin + end
        return self._text.startswith(prefix, start, end)

    def endswith(self,
                 suffix: str,
                 start: cint = 0,
                 end: Optional[int] = None) -> bool:
        """Return True if S ends with the specified suffix, False otherwise.
        With optional `start`, test S beginning at that position.
        With optional `end`, stop comparing S at that position.
        """
        start += self._begin
        end = self._end if end is None else self._begin + end
        return self._text.endswith(suffix, start, end)

    def match(self, regex, flags: cint = 0):
        """Executes `regex.match` on the StringView object and returns the
        result, which is either a match-object or None. Keep in mind that
        match.end(), match.span() etc. are mapped to the underlying text,
        not the StringView-object!!!
        """
        return regex.match(self._text, pos=self._begin, endpos=self._end)

    def index(self, absolute_index: cint) -> int:
        """Converts an index for a string watched by a StringView object
        to an index relative to the string view object, e.g.::

            >>> import re
            >>> sv = StringView('xxIxx')[2:3]
            >>> match = sv.match(re.compile('I'))
            >>> match.end()
            3
            >>> sv.index(match.end())
            1
        """
        return absolute_index - self._begin

    @cython.locals(_begin=cython.int)
    def indices(self, absolute_indices: Iterable[int]) -> Tuple[int, ...]:
        """Converts indices for a string watched by a StringView object
        to indices relative to the string view object. See also: `sv_index()`
        """
        _begin = self._begin  # type: int
        return tuple(index - _begin for index in absolute_indices)

    @cython.locals(_begin=cython.int)
    def search(self, regex, start: Optional[int] = None, end: Optional[int] = None):
        """Executes regex.search on the StringView object and returns the
        result, which is either a match-object or None. Keep in mind that
        match.end(), match.span() etc. are mapped to the underlying text,
        not the StringView-object!!!
        """
        _begin = self._begin  # type: int
        start = _begin if start is None else max(_begin, min(_begin + start, self._end))
        end = self._end if end is None else max(_begin, min(_begin + end, self._end))
        return regex.search(self._text, start, end)

    def finditer(self, regex):
        """Executes regex.finditer on the StringView object and returns the
        iterator of match objects. Keep in mind that match.end(), match.span()
        etc. are mapped to the underlying text, not the StringView-object!!!
        """
        return regex.finditer(self._text, pos=self._begin, endpos=self._end)

    @cython.locals(begin=cython.int, end=cython.int)
    def strip(self, chars: str = ' \n\r\t') -> StringView:
        """Returns a copy of the StringView `self` with leading and trailing
        whitespace removed.
        """
        begin = first_char(self._text, self._begin, self._end, chars) - self._begin
        end = last_char(self._text, self._begin, self._end, chars) - self._begin
        return self if begin == 0 and end == self._len else self[begin:end]

    @cython.locals(begin=cython.int)
    def lstrip(self, chars=' \n\t') -> StringView:
        """Returns a copy of `self` with leading whitespace removed."""
        begin = first_char(self._text, self._begin, self._end, chars) - self._begin
        return self if begin == 0 else self[begin:]

    @cython.locals(end=cython.int)
    def rstrip(self, chars=' \n\t') -> StringView:
        """Returns a copy of `self` with trailing whitespace removed."""
        end = last_char(self._text, self._begin, self._end, chars) - self._begin
        return self if end == self._len else self[:end]

    @cython.locals(length=cython.int, i=cython.int, k=cython.int)
    def split(self, sep=None): ## -> List[Union[StringView, str]]:
        """Returns a list of the words in `self`, using `sep` as the
        delimiter string.  If `sep` is not specified or is None, any
        whitespace string is a separator and empty strings are
        removed from the result.
        """
        if self._fullstring:
            return self._fullstring.split(sep)
        else:
            pieces = []  # type: List[Union['StringView', str]]
            length = len(sep)
            k = 0
            i = self.find(sep, k)
            # while i >= 0:
            #     pieces.append(self._text[self._begin + k: self._begin + i])
            #     k = i + length
            #     i = self.find(sep, k)
            # pieces.append(self._text[self._begin + k: self._end])
            while i >= 0:
                pieces.append(self[k:i])
                k = i + length
                i = self.find(sep, k)
            pieces.append(self[k:])
            return pieces

    def replace(self, old, new) -> str:
        """Returns a string where `old` is replaced by `new`."""
        return str(self).replace(old, new)


EMPTY_STRING_VIEW = StringView('')


class TextBuffer:
    """TextBuffer class manages a copy of an edited text for a language
    server. The text can be changed  via incremental edits. TextBuffer
    keeps track of the state of the complete text at any point in time.
    It works line oriented and lines of text can be retrieved via
    indexing or slicing.
    """

    def __init__(self, text: Union[str, StringView], version: cint = 0):
        self._text = text       # type: Union[str, StringView]
        self._buffer = []       # type: List[Union[str, StringView]]
        self.version = version if version >= 0 else 0

    def _lazy_init(self):
        self._buffer = [line.strip('\r') for line in self._text.split('\n')]

    def __getitem__(self, index: Union[slice, int]) \
            -> Union[List[Union[str, StringView]], str, StringView]:
        if not self._buffer:
            self._lazy_init()
        return self._buffer.__getitem__(index)

    def __str__(self) -> str:
        if self._text:
            return str(self._text)
        return str(self.snapshot('\n'))

    def __len__(self) -> int:
        if self._text:
            return len(self._text)
        else:
            return sum(len(line) for line in self._buffer) + len(self._buffer) - 1

    @property
    def buffer(self) -> List[Union[str, StringView]]:
        if not self._buffer:
            self._lazy_init()
        return self._buffer

    def lines(self) -> int:
        if not self._buffer:
            self._lazy_init()
        return len(self._buffer)

    def update(self, l1: cint, c1: cint, l2: cint, c2: cint, replacement: Union[str, StringView]):
        """Replaces the text-range from line and column (l1, c1) to
        line and column (l2, c2) with the replacement-string.
        """
        if not self._buffer:
            self._lazy_init()
        lines = [line.strip('\r') for line in replacement.split('\n')]
        head = self._buffer[l1][:c1]
        tail = self._buffer[l2][c2:]
        lines[0] = head + lines[0]
        lines[-1] += tail
        self._buffer[l1:l2 + 1] = lines
        self._text = ''  # invalidate single-string copy
        self.version += 1

    def text_edits(self, edits: Union[list, dict], version: cint = -1):
        """Incorporates the one or more text-edits or change-events into the text.
        A Text-Edit is a dictionary of this form::

            {"range": {"start": {"line": 0, "character": 0 },
                       "end":   {"line": 0, "character": 0 } },
             "newText": "..."}

        In case of a change-event, the key "newText" is replaced by "text".
        """
        def edit(ed: dict):
            """Weaves a single edit into the text-buffer."""
            rng = ed["range"]
            start = rng["start"]
            end = rng["end"]
            try:
                replacement = ed['text']
            except KeyError:
                replacement = ed['newText']
            self.update(start["line"], start["character"],
                        end["line"], end["character"], replacement)

        if isinstance(edits, list):
            for ed in edits:
                edit(ed)
        else:
            edit(cast(dict, edits))
        if version >= 0:
            self.version = version

    def snapshot(self, eol: str = '\n') -> Union[str, StringView]:
        """Returns the current state of the entire text, using the given
        end of line marker (``\\n`` or ``\\r\\n``)"""
        if self._text:
            return self._text
        self._text = eol.join(str(line) for line in self._buffer)
        return self._text
