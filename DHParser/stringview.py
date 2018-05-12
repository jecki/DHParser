# stringview.py - a string class where slices are views not copies as
#                    with the standard Python strings.
#
#    stringview.pxd - declarations for the cython Python to C compiler
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

It is recommended to compile this modules with the Cython-compiler for
speedup. The modules comes with a ``stringview.pxd`` that contains some type
declarations to fully exploit the potential of the Cython-compiler.
"""

import collections

from DHParser.toolkit import typing
from typing import Optional, Union, Iterable, Tuple


__all__ = ('StringView', 'EMPTY_STRING_VIEW')


def first_char(text, begin: int, end: int) -> int:
    """Returns the index of the first non-whitespace character in string
     `text` within the bounds [begin, end].
    """
    while begin < end and text[begin] in ' \n\t':
        begin += 1
    return begin


def last_char(text, begin: int, end: int) -> int:
    """Returns the index of the first non-whitespace character in string
    `text` within the bounds [begin, end].
    """
    while end > begin and text[end-1] in ' \n\t':
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
    return 0 if index < 0 else length if index > length else index


def real_indices(begin: Optional[int],
                 end: Optional[int],
                 length) -> Tuple[int, int]:   # "length: int" fails with cython!?
    """Returns the tuple of real (i.e. positive) indices from the slice
    indices `begin`,  `end`, assuming a string of size `length`.
    """
    cbegin = 0 if begin is None else begin
    cend = length if end is None else end
    return pack_index(cbegin, length), pack_index(cend, length)


class StringView(collections.abc.Sized):
    """
    A rudimentary StringView class, just enough for the use cases
    in parse.py. The difference between a StringView and the python
    builtin strings is that StringView-objects do slicing without
    copying, i.e. slices are just a view on a section of the sliced
    string.
    """
    __slots__ = ['text', 'begin', 'end', 'len', 'fullstring']

    def __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None:
        # assert isinstance(text, str)
        self.text = text  # type: str
        self.begin, self.end = real_indices(begin, end, len(text))
        self.len = max(self.end - self.begin, 0)  # type: int
        if (self.begin == 0 and self.len == len(self.text)):
            self.fullstring = self.text  # type: str
        else:
            self.fullstring = ''

    def __bool__(self):
        return self.end > self.begin  # and bool(self.text)

    def __len__(self):
        return self.len

    def __str__(self):
        # PERFORMANCE WARNING: This creates a copy of the string-slice
        if self.fullstring:  # optimization: avoid slicing/copying
            return self.fullstring
        # since the slice is being copyied now, anyway, the copy might
        # as well be stored in the string view
        # return self.text[self.begin:self.end]  # use this for debugging!
        self.fullstring = self.text[self.begin:self.end]
        return self.fullstring

    def __eq__(self, other):
        # PERFORMANCE WARNING: This creates copies of the strings
        return len(other) == len(self) and str(self) == str(other)

    def __hash__(self):
        # PERFORMANCE WARNING: This creates a copy of the string-slice
        return hash(str(self))

    def __add__(self, other):
        if isinstance(other, str):
            return str(self) + other
        else:
            return StringView(str(self) + str(other))

    def __radd__(self, other):
        if isinstance(other, str):
            return other + str(self)
        else:
            return StringView(str(other) + str(self))

    def __getitem__(self, index):
        # assert isinstance(index, slice), "As of now, StringView only allows slicing."
        # assert index.step is None or index.step == 1, \
        #     "Step sizes other than 1 are not yet supported by StringView"
        try:
            start, stop = real_indices(index.start, index.stop, self.len)
            return StringView(self.text, self.begin + start, self.begin + stop)
        except AttributeError:
            return self.text[self.begin + index]

    def count(self, sub: str, start=None, end=None) -> int:
        """Returns the number of non-overlapping occurrences of substring
        `sub` in StringView S[start:end].  Optional arguments start and end
        are interpreted as in slice notation.
        """
        if self.fullstring:
            return self.fullstring.count(sub, start, end)
        elif start is None and end is None:
            return self.text.count(sub, self.begin, self.end)
        else:
            start, end = real_indices(start, end, self.len)
            return self.text.count(sub, self.begin + start, self.begin + end)

    def find(self, sub: str, start=None, end=None) -> int:
        """Returns the lowest index in S where substring `sub` is found,
        such that `sub` is contained within S[start:end].  Optional
        arguments `start` and `end` are interpreted as in slice notation.
        Returns -1 on failure.
        """
        if self.fullstring:
            return self.fullstring.find(sub, start, end)
        elif start is None and end is None:
            return self.text.find(sub, self.begin, self.end) - self.begin
        else:
            start, end = real_indices(start, end, self.len)
            return self.text.find(sub, self.begin + start, self.begin + end) - self.begin

    def rfind(self, sub: str, start=None, end=None) -> int:
        """Returns the highest index in S where substring `sub` is found,
        such that `sub` is contained within S[start:end].  Optional
        arguments `start` and `end` are interpreted as in slice notation.
        Returns -1 on failure.
        """
        if self.fullstring:
            return self.fullstring.rfind(sub, start, end)
        if start is None and end is None:
            return self.text.rfind(sub, self.begin, self.end) - self.begin
        else:
            start, end = real_indices(start, end, self.len)
            return self.text.rfind(sub, self.begin + start, self.begin + end) - self.begin

    def startswith(self,
                   prefix: Union[str, Tuple[str, ...]],
                   start: int = 0,
                   end: Optional[int] = None) -> bool:
        """Return True if S starts with the specified prefix, False otherwise.
        With optional `start`, test S beginning at that position.
        With optional `end`, stop comparing S at that position.
        prefix can also be a tuple of strings to try.
        """
        start += self.begin
        end = self.end if end is None else self.begin + end
        return self.text.startswith(prefix, start, end)

    def match(self, regex, flags=0):
        """Executes `regex.match` on the StringView object and returns the
        result, which is either a match-object or None. Keep in mind that
        match.end(), match.span() etc. are mapped to the underlying text,
        not the StringView-object!!!
        """
        return regex.match(self.text, pos=self.begin, endpos=self.end)

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
        return absolute_index - self.begin

    def indices(self, absolute_indices: Iterable[int]) -> Tuple[int, ...]:
        """Converts indices for a string watched by a StringView object
        to indices relative to the string view object. See also: `sv_index()`
        """
        return tuple(index - self.begin for index in absolute_indices)

    def search(self, regex):
        """Executes regex.search on the StringView object and returns the
        result, which is either a match-object or None. Keep in mind that
        match.end(), match.span() etc. are mapped to the underlying text,
        not the StringView-object!!!
        """
        return regex.search(self.text, pos=self.begin, endpos=self.end)

    def finditer(self, regex):
        """Executes regex.finditer on the StringView object and returns the
        iterator of match objects. Keep in mind that match.end(), match.span()
        etc. are mapped to the underlying text, not the StringView-object!!!
        """
        return regex.finditer(self.text, pos=self.begin, endpos=self.end)

    def strip(self):
        """Returns a copy of the StringView `self` with leading and trailing
        whitespace removed.
        """
        begin = first_char(self.text, self.begin, self.end) - self.begin
        end = last_char(self.text, self.begin, self.end) - self.begin
        return self if begin == 0 and end == self.len else self[begin:end]

    def lstrip(self):
        """Returns a copy of `self` with leading whitespace removed."""
        begin = first_char(self.text, self.begin, self.end) - self.begin
        return self if begin == 0 else self[begin:]

    def rstrip(self):
        """Returns a copy of `self` with trailing whitespace removed."""
        end = last_char(self.text, self.begin, self.end) - self.begin
        return self if end == self.len else self[:end]

    def split(self, sep=None):
        """Returns a list of the words in `self`, using `sep` as the
        delimiter string.  If `sep` is not specified or is None, any
        whitespace string is a separator and empty strings are
        removed from the result.
        """
        if self.fullstring:
            return self.fullstring.split(sep)
        else:
            pieces = []
            l = len(sep)
            k = 0
            i = self.find(sep, k)
            while i >= 0:
                pieces.append(self.text[self.begin + k: self.begin + i])
                k = i + l
                i = self.find(sep, k)
            pieces.append(self.text[self.begin + k: self.end])
            return pieces

    def replace(self, old, new):
        """Returns a string where `old` is replaced by `new`."""
        return str(self).replace(old, new)


EMPTY_STRING_VIEW = StringView('')
