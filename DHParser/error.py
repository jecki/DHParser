"""error.py - error handling for DHParser

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

import bisect
import functools

from DHParser.stringview import StringView
from DHParser.toolkit import typing
from typing import Hashable, Iterable, Iterator, Union, Tuple, List


__all__ = ('Error',
           'is_error',
           'is_warning',
           'has_errors',
           'only_errors',
           'linebreaks',
           'line_col')


class Error:
    __slots__ = ['message', 'level', 'code', 'pos', 'line', 'column']

    # error levels

    WARNING   = 1
    ERROR     = 1000
    HIGHEST   = ERROR

    # warning codes

    REDEFINED_DIRECTIVE_WARNING = 101

    # error codes

    MANDATORY_CONTINUATION = 1001

    def __init__(self, message: str, code: int = ERROR,
                 pos: int = -1, line: int = -1, column: int = -1) -> None:
        self.message = message
        assert code >= 0
        self.code = code
        self.pos = pos
        self.line = line
        self.column = column

    def __str__(self):
        prefix = ''
        if self.line > 0:
            prefix = "line: %3i, column: %2i, " % (self.line, self.column)
        return prefix + "%s: %s" % (self.level_str, self.message)

    def __repr__(self):
        return 'Error("%s", %i, %s, %i, %i, %i)' \
               % (self.message, self.level, repr(self.code), self.pos, self.line, self.column)

    @property
    def level_str(self):
        """Returns a string representation of the error level, e.g. "warning".
        """
        return "Warning" if is_warning(self.code) else "Error"


def is_warning(code: int) -> bool:
    """Returns True, if error is merely a warning."""
    return code < Error.ERROR


def is_error(code: int) -> bool:
    """Returns True, if error is an error, not just a warning."""
    return code >= Error.ERROR


def has_errors(messages: Iterable[Error], level: int = Error.ERROR) -> bool:
    """
    Returns True, if at least one entry in `messages` has at
    least the given error `level`.
    """
    for err_obj in messages:
        if err_obj.code >= level:
            return True
    return False


def only_errors(messages: Iterable[Error], level: int = Error.ERROR) -> Iterator[Error]:
    """
    Returns an Iterator that yields only those messages that have
    at least the given error level.
    """
    return (err for err in messages if err.level >= level)


def linebreaks(text: Union[StringView, str]):
    """
    Returns a list of indices all line breaks in the text.
    """
    lbr = [-1]
    i = text.find('\n', 0)
    while i >= 0:
        lbr.append(i)
        i = text.find('\n', i + 1)
    lbr.append(len(text))
    return lbr


@functools.singledispatch
def line_col(text: Union[StringView, str], pos: int) -> Tuple[int, int]:
    """
    Returns the position within a text as (line, column)-tuple.
    """
    if pos < 0 or pos > len(text):  # one character behind EOF is still an allowed position!
        raise ValueError('Position %i outside text of length %s !' % (pos, len(text)))
    line = text.count("\n", 0, pos) + 1
    column = pos - text.rfind("\n", 0, pos)
    return line, column


@line_col.register(list)
def _line_col(lbreaks: List[int], pos: int) -> Tuple[int, int]:
    """
    Returns the position within a text as (line, column)-tuple based
    on a list of all line breaks, including -1 and EOF.
    """
    if pos < 0 or pos > lbreaks[-1]:  # one character behind EOF is still an allowed position!
        raise ValueError('Position %i outside text of length %s !' % (pos, lbreaks[-1]))
    line = bisect.bisect_left(lbreaks, pos)
    column = pos - lbreaks[line - 1]
    return line, column


# def error_messages(source_text:str, errors: List[Error]) -> List[str]:
#     """Adds line, column information for error messages, if the position
#     is given.
#
#     Args:
#         source_text (str):  The source text on which the errors occurred.
#             (Needed in order to determine the line and column numbers.)
#         errors (list):  The list of errors as returned by the method
#             ``collect_errors()`` of a Node object
#     Returns:
#         The same list of error messages, which now contain line and
#         column numbers.
#     """
#     for err in errors:
#         if err.pos >= 0 and err.line <= 0:
#             err.line, err.column = line_col(source_text, err.pos)
#     return errors
