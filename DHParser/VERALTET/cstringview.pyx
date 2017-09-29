"""cstringview.pyx - a cython-version of the stringview class for speedup
                     slicing strings without copying

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


cdef inline int pack_index(int index, int len):
    index = index if index >= 0 else index + len
    return 0 if index < 0 else len if index > len else index


cdef real_indices(begin, end, int len):
    cdef int begin_i = 0 if begin is None else begin
    cdef int end_i = len if end is None else end
    return pack_index(begin_i, len), pack_index(end_i, len)


class StringView(collections.abc.Sized):
    """"
    A rudimentary StringView class, just enough for the use cases
    in parser.py. The difference between a StringView and the python
    builtin strings is that StringView-objects do slicing without
    copying, i.e. slices are just a view on a section of the sliced
    string.
    """

    __slots__ = ['text', 'begin', 'end', 'len', 'fullstring_flag']

    def __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None:
        self.text = text
        self.begin, self.end = real_indices(begin, end, len(text))
        self.len = max(self.end - self.begin, 0)
        self.fullstring_flag = (self.begin == 0 and self.len == len(self.text))

    def __bool__(self):
        return self.end > self.begin  # and bool(self.text)

    def __len__(self):
        return self.len

    def __str__(self):
        if self.fullstring_flag:  # optimization: avoid slicing/copying
            return self.text
        # since the slice is being copyied now, anyway, the copy might
        # as well be stored in the string view
        self.text = self.text[self.begin:self.end]
        self.begin = 0
        self.len = len(self.text)
        self.end = self.len
        self.fullstring_flag = True
        return self.text

    def __eq__(self, other):
        return len(other) == len(self) and str(self) == str(other)  # PERFORMANCE WARNING: This creates copies of the strings

    def __hash__(self):
        return hash(str(self))  # PERFORMANCE WARNING: This creates a copy of the string-slice

    def __add__(self, other):
        if isinstance(other, str):
            return (str(self) + other)
        else:
            return StringView(str(self) + str(other))

    def __radd__(self, other):
        if isinstance(other, str):
            return (other + str(self))
        else:
            return StringView(str(other) + str(self))

    def __getitem__(self, index):
        # assert isinstance(index, slice), "As of now, StringView only allows slicing."
        # assert index.step is None or index.step == 1, \
        #     "Step sizes other than 1 are not yet supported by StringView"
        start, stop = real_indices(index.start, index.stop, self.len)
        return StringView(self.text, self.begin + start, self.begin + stop)

    def count(self, sub, start=None, end=None) -> int:
        if self.fullstring_flag:
            return self.text.count(sub, start, end)
        elif start is None and end is None:
            return self.text.count(sub, self.begin, self.end)
        else:
            start, end = real_indices(start, end, self.len)
            return self.text.count(sub, self.begin + start, self.begin + end)

    def find(self, sub, start=None, end=None) -> int:
        if self.fullstring_flag:
            return self.text.find(sub, start, end)
        elif start is None and end is None:
            return self.text.find(sub, self.begin, self.end) - self.begin
        else:
            start, end = real_indices(start, end, self.len)
            return self.text.find(sub, self.begin + start, self.begin + end) - self.begin

    def rfind(self, sub, start=None, end=None) -> int:
        if self.fullstring_flag:
            return self.text.rfind(sub, start, end)
        if start is None and end is None:
            return self.text.rfind(sub, self.begin, self.end) - self.begin
        else:
            start, end = real_indices(start, end, self.len)
            return self.text.rfind(sub, self.begin + start, self.begin + end) - self.begin

    def startswith(self, prefix: str, start: int = 0, end: Optional[int] = None) -> bool:
        start += self.begin
        end = self.end if end is None else self.begin + end
        return self.text.startswith(prefix, start, end)

    def match(self, regex):
        return regex.match(self.text, pos=self.begin, endpos=self.end)

    def index(self, absolute_index: int) -> int:
        """
        Converts an index for a string watched by a StringView object
        to an index relative to the string view object, e.g.:
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
        return regex.search(self.text, pos=self.begin, endpos=self.end)

    def strip(self):
        cdef int begin, end
        if self.fullstring_flag:
            return self.text.strip()
        else:
            begin = self.begin
            end = self.end
            while begin < end and self.text[begin] in ' \n\t':
                begin += 1
            while end > begin and self.text[end] in ' \n\t':
                end -= 1
            return self.text[begin:end]
        # return str(self).strip()  # PERFORMANCE WARNING: This creates a copy of the string

    def split(self, sep=None):
        cdef int i, k, l
        if self.fullstring_flag:
            return self.text.split(sep)
        else:
            pieces = []
            l = len(sep)
            k = 0
            i = self.find(sep, k)
            while i >= 0:
                pieces.append(self.text[self.begin + k : self.begin + i])
                k = i + l
                i = self.find(sep, k)
            pieces.append(self.text[self.begin + k : self.end])
            return pieces
        # return str(self).split(sep, maxsplit)  # PERFORMANCE WARNING: This creates a copy of the string


EMPTY_STRING_VIEW = StringView('')
