# error.py - error handling for DHParser
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
Module ``error`` defines class Error and a few helpful functions that are
needed for error reporting of DHParser. Usually, what is of interest are
the string representations of the error objects. For example::

    from DHParser import compile_source, has_errors

    result, errors, ast = compile_source(source, preprocessor, grammar,
                                         transformer, compiler)
    if errors:
        for error in errors:
            print(error)

        if has_errors(errors):
            print("There have been fatal errors!")
            sys.exit(1)
        else:
            print("There have been warnings, but no errors.")
"""


import bisect

from DHParser.preprocess import SourceMapFunc
from DHParser.stringview import StringView
from DHParser.toolkit import typing
from typing import Iterable, Iterator, Union, Tuple, List, NewType

__all__ = ('ErrorCode',
           'Error',
           'is_error',
           'is_warning',
           'has_errors',
           'only_errors',
           'linebreaks',
           'line_col',
           'adjust_error_locations')


class ErrorCode(int):
    pass


class Error:
    __slots__ = ['message', 'level', 'code', '_pos', 'orig_pos', 'line', 'column', '_node_keep']

    # error levels

    NO_ERROR  = ErrorCode(0)
    MESSAGE   = ErrorCode(1)
    WARNING   = ErrorCode(10)
    ERROR     = ErrorCode(1000)
    HIGHEST   = ERROR

    # warning codes

    REDEFINED_DIRECTIVE_WARNING = ErrorCode(101)
    REDECLARED_TOKEN_WARNING = ErrorCode(102)

    UNDEFINED_SYMBOL_IN_TRANSFORMATION_TABLE = ErrorCode(601)

    # error codes

    MANDATORY_CONTINUATION = ErrorCode(1001)

    def __init__(self, message: str, pos, code: ErrorCode = ERROR,
                 orig_pos: int = -1, line: int = -1, column: int = -1) -> None:
        assert isinstance(code, ErrorCode)
        assert not isinstance(pos, ErrorCode)
        assert pos >= 0
        assert code >= 0
        self.message = message
        self._pos = pos
        self.code = code
        self.orig_pos = orig_pos
        self.line = line
        self.column = column

    def __str__(self):
        prefix = ''
        if self.line > 0:
            prefix = "%i:%i: " % (max(self.line, 0), max(self.column, 0))
        return prefix + "%s: %s" % (self.severity, self.message)

    def __repr__(self):
        return 'Error("%s", %s, %i, %i, %i, %i)' \
               % (self.message, repr(self.code), self.pos, self.orig_pos, self.line, self.column)

    @property
    def pos(self):
        return self._pos

    @property
    def severity(self):
        """Returns a string representation of the error level, e.g. "warning"."""
        return "Warning" if is_warning(self.code) else "Error"

    def visualize(self, document: str) -> str:
        """Shows the line of the document and the position where the error
        occurred."""
        start = document.rfind('\n', 0, self.pos) + 1
        stop = document.find('\n', self.pos)
        return document[start:stop] + '\n' + ' ' * (self.pos - start) + '^\n'


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
    return (err for err in messages if err.code >= level)


#######################################################################
#
# Setting of line, column and position properties of error messages.
#
#######################################################################


def linebreaks(text: Union[StringView, str]) -> List[int]:
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


def line_col(lbreaks: List[int], pos: int) -> Tuple[int, int]:
    """
    Returns the position within a text as (line, column)-tuple based
    on a list of all line breaks, including -1 and EOF.
    """
    if not lbreaks and pos >= 0:
        return 0, pos
    if pos < 0 or pos > lbreaks[-1]:  # one character behind EOF is still an allowed position!
        raise ValueError('Position %i outside text of length %s !' % (pos, lbreaks[-1]))
    line = bisect.bisect_left(lbreaks, pos)
    column = pos - lbreaks[line - 1]
    return line, column


# def line_col(text: Union[StringView, str], pos: int) -> Tuple[int, int]:
#     """
#     Returns the position within a text as (line, column)-tuple.
#     """
#     if pos < 0 or add_pos > len(text):  # one character behind EOF is still an allowed position!
#         raise ValueError('Position %i outside text of length %s !' % (pos, len(text)))
#     line = text.count("\n", 0, pos) + 1
#     column = pos - text.rfind("\n", 0, add_pos)
#     return line, column


def adjust_error_locations(errors: List[Error],
                           original_text: Union[StringView, str],
                           source_mapping: SourceMapFunc=lambda i: i) -> List[Error]:
    """Adds (or adjusts) line and column numbers of error messages in place.

    Args:
        errors:  The list of errors as returned by the method
            ``collect_errors()`` of a Node object
        original_text:  The source text on which the errors occurred.
            (Needed in order to determine the line and column numbers.)
        source_mapping:  A function that maps error positions to their
            positions in the original source file.

    Returns:
        The list of errors. (Returning the list of errors is just syntactical
        sugar. Be aware that the line, col and orig_pos attributes have been
        changed in place.)
    """
    line_breaks = linebreaks(original_text)
    for err in errors:
        assert err.pos >= 0
        err.orig_pos = source_mapping(err.pos)
        err.line, err.column = line_col(line_breaks, err.orig_pos)
    return errors
