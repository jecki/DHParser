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

from typing import Optional, Union, Iterable, Tuple

try:
    import cython
    cython_optimized = cython.compiled  # type: bool
except ImportError:
    # import DHParser.Shadow as cython
    cython_optimized = False
    import DHParser.shadow_cython as cython


__all__ = ('StringView', 'EMPTY_STRING_VIEW', 'cython_optimized')


def first_char(text, begin: int, end: int, chars) -> int:
    """Returns the index of the first non-whitespace character in string
     `text` within the bounds [begin, end].
    """
    while begin < end and text[begin] in chars:
        begin += 1
    return begin


def last_char(text, begin: int, end: int, chars) -> int:
    """Returns the index of the first non-whitespace character in string
    `text` within the bounds [begin, end].
    """
    while end > begin and text[end - 1] in chars:
        end -= 1
    return end


def pack_index(index: int, length: int) -> int:
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
    # TODO: Test the following code for speedup
    # if index < 0:
    #     index += length
    return 0 if index < 0 else length if index > length else index


def real_indices(begin: Optional[int],
                 end: Optional[int],
                 length) -> Tuple[int, int]:
    """Returns the tuple of real (i.e. positive) indices from the slice
    indices `begin`,  `end`, assuming a string of size `length`.
    """
    cbegin = 0 if begin is None else begin
    cend = length if end is None else end
    return pack_index(cbegin, length), pack_index(cend, length)


class StringView:  # collections.abc.Sized
    """
    A rudimentary StringView class, just enough for the use cases
    in parse.py. The difference between a StringView and the python
    builtin strings is that StringView-objects do slicing without
    copying, i.e. slices are just a view on a section of the sliced
    string.
    """
    __slots__ = ['_text', '_begin', '_end', '_len', '_fullstring']

    def __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None:
        # assert isinstance(text, str)
        self._text = text  # type: str
        self._begin, self._end = real_indices(begin, end, len(text))
        self._len = max(self._end - self._begin, 0)  # type: int
        self._fullstring = ''  # type: str
        # if (self._begin == 0 and self._len == len(self._text)):
        #     self._fullstring = self._text  # type: str
        # else:
        #     self._fullstring = ''

    def __bool__(self) -> bool:
        return self._end > self._begin  # and bool(self.text)

    def __len__(self) -> int:
        return self._len

    def __str__(self) -> str:
        # PERFORMANCE WARNING: This creates a copy of the string-slice
        if self._fullstring:  # optimization: avoid slicing/copying
            return self._fullstring
        # since the slice is being copyied now, anyway, the copy might
        # as well be stored in the string view
        # return self.text[self.begin:self.end]  # use this for debugging!
        self._fullstring = self._text[self._begin:self._end]
        return self._fullstring

    def __repr__(self) -> str:
        return repr(str(self))

    def __eq__(self, other) -> bool:
        # PERFORMANCE WARNING: This creates copies of the strings
        return len(other) == len(self) and str(self) == str(other)

    def __hash__(self) -> int:
        # PERFORMANCE WARNING: This creates a copy of the string-slice
        return hash(str(self))

    def __add__(self, other) -> Union[str, 'StringView']:
        if isinstance(other, str):
            return str(self) + other
        else:
            return StringView(str(self) + str(other))

    def __radd__(self, other) -> Union[str, 'StringView']:
        if isinstance(other, str):
            return other + str(self)
        else:
            return StringView(str(other) + str(self))

    @cython.locals(start=cython.int, stop=cython.int)
    def __getitem__(self, index: Union[slice, int]) -> 'StringView':
        # assert isinstance(index, slice), "As of now, StringView only allows slicing."
        # assert index.step is None or index.step == 1, \
        #     "Step sizes other than 1 are not yet supported by StringView"
        try:
            start, stop = real_indices(index.start, index.stop, self._len)
            return StringView(self._text, self._begin + start, self._begin + stop)
        except AttributeError:
            return StringView(self._text, self._begin + index, self._begin + index + 1)
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
            _start, _end = real_indices(start, end, self._len)
            return self._text.count(sub, self._begin + _start, self._begin + _end)

    @cython.locals(_start=cython.int, _end=cython.int)
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
            return max(self._text.find(sub, self._begin, self._end) - self._begin, -1)
        else:
            _start, _end = real_indices(start, end, self._len)
            return max(self._text.find(sub, self._begin + _start, self._begin + _end)
                       - self._begin, -1)

    @cython.locals(_start=cython.int, _end=cython.int)
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
            return max(self._text.rfind(sub, self._begin, self._end) - self._begin, -1)
        else:
            _start, _end = real_indices(start, end, self._len)
            return max(self._text.rfind(sub, self._begin + _start, self._begin + _end)
                       - self._begin, -1)

    def startswith(self,
                   prefix: str,
                   start: int = 0,
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
                 start: int = 0,
                 end: Optional[int] = None) -> bool:
        """Return True if S ends with the specified suufix, False otherwise.
        With optional `start`, test S beginning at that position.
        With optional `end`, stop comparing S at that position.
        """
        start += self._begin
        end = self._end if end is None else self._begin + end
        return self._text.endswith(suffix, start, end)

    def match(self, regex, flags: int = 0):
        """Executes `regex.match` on the StringView object and returns the
        result, which is either a match-object or None. Keep in mind that
        match.end(), match.span() etc. are mapped to the underlying text,
        not the StringView-object!!!
        """
        return regex.match(self._text, pos=self._begin, endpos=self._end)

    def index(self, absolute_index: int) -> int:
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

    def indices(self, absolute_indices: Iterable[int]) -> Tuple[int, ...]:
        """Converts indices for a string watched by a StringView object
        to indices relative to the string view object. See also: `sv_index()`
        """
        return tuple(index - self._begin for index in absolute_indices)

    def search(self, regex, start: Optional[int] = None, end: Optional[int] = None):
        """Executes regex.search on the StringView object and returns the
        result, which is either a match-object or None. Keep in mind that
        match.end(), match.span() etc. are mapped to the underlying text,
        not the StringView-object!!!
        """
        start = self._begin if start is None else self._begin + start
        end = self._end if end is None else self._begin + end
        return regex.search(self._text, start, end)

    def finditer(self, regex):
        """Executes regex.finditer on the StringView object and returns the
        iterator of match objects. Keep in mind that match.end(), match.span()
        etc. are mapped to the underlying text, not the StringView-object!!!
        """
        return regex.finditer(self._text, pos=self._begin, endpos=self._end)

    @cython.locals(begin=cython.int, end=cython.int)
    def strip(self, chars = ' \n\t'):
        """Returns a copy of the StringView `self` with leading and trailing
        whitespace removed.
        """
        begin = first_char(self._text, self._begin, self._end, chars) - self._begin
        end = last_char(self._text, self._begin, self._end, chars) - self._begin
        return self if begin == 0 and end == self._len else self[begin:end]

    @cython.locals(begin=cython.int)
    def lstrip(self, chars = ' \n\t'):
        """Returns a copy of `self` with leading whitespace removed."""
        begin = first_char(self._text, self._begin, self._end, chars) - self._begin
        return self if begin == 0 else self[begin:]

    @cython.locals(end=cython.int)
    def rstrip(self, chars = ' \n\t'):
        """Returns a copy of `self` with trailing whitespace removed."""
        end = last_char(self._text, self._begin, self._end, chars) - self._begin
        return self if end == self._len else self[:end]

    @cython.locals(length=cython.int, i=cython.int, k=cython.int)
    def split(self, sep=None):
        """Returns a list of the words in `self`, using `sep` as the
        delimiter string.  If `sep` is not specified or is None, any
        whitespace string is a separator and empty strings are
        removed from the result.
        """
        if self._fullstring:
            return self._fullstring.split(sep)
        else:
            pieces = []
            length = len(sep)
            k = 0
            i = self.find(sep, k)
            while i >= 0:
                pieces.append(self._text[self._begin + k: self._begin + i])
                k = i + length
                i = self.find(sep, k)
            pieces.append(self._text[self._begin + k: self._end])
            return pieces

    def replace(self, old, new):
        """Returns a string where `old` is replaced by `new`."""
        return str(self).replace(old, new)


EMPTY_STRING_VIEW = StringView('')
