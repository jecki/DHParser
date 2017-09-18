"""base.py - various base classes that are used across several other
             the DHParser-modules.

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
import collections
from typing import Hashable, Iterable, Iterator, Optional, Tuple


__all__ = ('ParserBase',
           'WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'MockParser',
           'ZombieParser',
           'ZOMBIE_PARSER',
           'Error',
           'is_error',
           'is_warning',
           'has_errors',
           'only_errors',
           'StringView',
           'EMPTY_STRING_VIEW')


#######################################################################
#
# parser base and mock parsers
#
#######################################################################


class ParserBase:
    """
    ParserBase is the base class for all real and mock parser classes.
    It is defined here, because Node objects require a parser object
    for instantiation.
    """
    def __init__(self, name=''):  # , pbases=frozenset()):
        self.name = name  # type: str
        self._ptype = ':' + self.__class__.__name__  # type: str

    def __repr__(self):
        return self.name + self.ptype

    def __str__(self):
        return self.name + (' = ' if self.name else '') + repr(self)

    @property
    def ptype(self) -> str:
        return self._ptype

    @property
    def repr(self) -> str:
        return self.name if self.name else repr(self)


WHITESPACE_PTYPE = ':Whitespace'
TOKEN_PTYPE = ':Token'


class MockParser(ParserBase):
    """
    MockParser objects can be used to reconstruct syntax trees from a
    serialized form like S-expressions or XML. Mock objects can mimic
    different parser types by assigning them a ptype on initialization.

    Mock objects should not be used for anything other than
    syntax tree (re-)construction. In all other cases where a parser
    object substitute is needed, chose the singleton ZOMBIE_PARSER.
    """
    def __init__(self, name='', ptype=''):  # , pbases=frozenset()):
        assert not ptype or ptype[0] == ':'
        super(MockParser, self).__init__(name)
        self.name = name
        self._ptype = ptype or ':' + self.__class__.__name__


class ZombieParser(MockParser):
    """
    Serves as a substitute for a Parser instance.

    ``ZombieParser`` is the class of the singelton object
    ``ZOMBIE_PARSER``. The  ``ZOMBIE_PARSER`` has a name and can be
    called, but it never matches. It serves as a substitute where only
    these (or one of these properties) is needed, but no real Parser-
    object is instantiated.
    """
    alive = False

    def __init__(self):
        super(ZombieParser, self).__init__("__ZOMBIE__")
        assert not self.__class__.alive, "There can be only one!"
        assert self.__class__ == ZombieParser, "No derivatives, please!"
        self.__class__.alive = True

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

    def __call__(self, text):
        """Better call Saul ;-)"""
        return None, text


ZOMBIE_PARSER = ZombieParser()


#######################################################################
#
# error reporting
#
#######################################################################


class Error:
    __slots__ = ['message', 'level', 'code', 'pos', 'line', 'column']

    WARNING   = 1
    ERROR     = 1000
    HIGHEST   = ERROR

    def __init__(self, message: str, level: int=ERROR, code: Hashable=0):
        self.message = message
        assert level >= 0
        self.level = level or Error.ERROR
        self.code = code
        self.pos = -1
        self.line = -1
        self.column = -1

    def __str__(self):
        prefix = ''
        if self.line > 0:
            prefix = "line: %3i, column: %2i, " % (self.line, self.column)
        return prefix + "%s: %s" % (self.level_str, self.message)

    @property
    def level_str(self):
        return "Warning" if is_warning(self.level) else "Error"


def is_warning(level: int) -> bool:
    return level < Error.ERROR


def is_error(level:  int) -> bool:
    return level >= Error.ERROR


def has_errors(messages: Iterable[Error], level: int=Error.ERROR) -> bool:
    """
    Returns True, if at least one entry in `messages` has at
    least the given error `level`.
    """
    for err_obj in messages:
        if err_obj.level >= level:
            return True
    return False


def only_errors(messages: Iterable[Error], level: int=Error.ERROR) -> Iterator[Error]:
    """
    Returns an Iterator that yields only those messages that have
    at least the given error level.
    """
    return (err for err in messages if err.level >= level)


#######################################################################
#
# string view
#
#######################################################################


class StringView(collections.abc.Sized):
    """"A rudimentary StringView class, just enough for the use cases
    in parser.py.

    Slicing Python-strings always yields copies of a segment of the original
    string. See: https://mail.python.org/pipermail/python-dev/2008-May/079699.html
    However, this becomes costly (in terms of space and as a consequence also
    time) when parsing longer documents. Unfortunately, Python's `memoryview`
    does not work for unicode strings. Hence, the StringView class.
    """

    __slots__ = ['text', 'begin', 'end', 'len', 'fullstring_flag']

    def __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None:
        self.text = text  # type: str
        self.begin = 0  # type: int
        self.end = 0    # type: int
        self.begin, self.end = StringView.real_indices(begin, end, len(text))
        self.len = max(self.end - self.begin, 0)
        self.fullstring_flag = (self.begin == 0 and self.len == len(self.text))

    @staticmethod
    def real_indices(begin, end, len):
        def pack(index, len):
            index = index if index >= 0 else index + len
            return 0 if index < 0 else len if index > len else index
        if begin is None:  begin = 0
        if end is None:  end = len
        return pack(begin, len), pack(end, len)

    def __bool__(self):
        return bool(self.text) and self.end > self.begin

    def __len__(self):
        return self.len

    def __str__(self):
        if self.fullstring_flag:  # optimization: avoid slicing/copying
            return self.text
        return self.text[self.begin:self.end]

    def __getitem__(self, index):
        # assert isinstance(index, slice), "As of now, StringView only allows slicing."
        # assert index.step is None or index.step == 1, \
        #     "Step sizes other than 1 are not yet supported by StringView"
        start, stop = StringView.real_indices(index.start, index.stop, self.len)
        return StringView(self.text, self.begin + start, self.begin + stop)

    def __eq__(self, other):
        return str(self) == str(other)  # PERFORMANCE WARNING: This creates copies of the strings

    def count(self, sub, start=None, end=None) -> int:
        if self.fullstring_flag:
            return self.text.count(sub, start, end)
        elif start is None and end is None:
            return self.text.count(sub, self.begin, self.end)
        else:
            start, end = StringView.real_indices(start, end, self.len)
            return self.text.count(sub, self.begin + start, self.begin + end)

    def find(self, sub, start=None, end=None) -> int:
        if self.fullstring_flag:
            return self.text.find(sub, start, end)
        elif start is None and end is None:
            return self.text.find(sub, self.begin, self.end) - self.begin
        else:
            start, end = StringView.real_indices(start, end, self.len)
            return self.text.find(sub, self.begin + start, self.begin + end) - self.begin

    def rfind(self, sub, start=None, end=None) -> int:
        if self.fullstring_flag:
            return self.text.rfind(sub, start, end)
        if start is None and end is None:
            return self.text.rfind(sub, self.begin, self.end) - self.begin
        else:
            start, end = StringView.real_indices(start, end, self.len)
            return self.text.rfind(sub, self.begin + start, self.begin + end) - self.begin

    def startswith(self, prefix: str, start:int = 0, end:Optional[int] = None) -> bool:
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


EMPTY_STRING_VIEW = StringView('')