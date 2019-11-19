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
from typing import Iterable, Iterator, Union, Dict, Tuple, List

from DHParser.preprocess import SourceMapFunc
from DHParser.stringview import StringView


__all__ = ('ErrorCode',
           'Error',
           'is_fatal',
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
    __slots__ = ['message', 'code', '_pos', 'orig_pos', 'line', 'column']

    # error levels

    NO_ERROR = ErrorCode(0)
    NOTICE   = ErrorCode(1)
    WARNING  = ErrorCode(100)
    ERROR    = ErrorCode(1000)
    FATAL    = ErrorCode(10000)
    HIGHEST  = FATAL

    # warning codes

    REDECLARED_TOKEN_WARNING                 = ErrorCode(120)
    UNUSED_ERROR_HANDLING_WARNING            = ErrorCode(130)
    LEFT_RECURSION_WARNING                   = ErrorCode(140)

    UNDEFINED_SYMBOL_IN_TRANSTABLE_WARNING   = ErrorCode(610)

    # error codes

    MANDATORY_CONTINUATION                   = ErrorCode(1010)
    MANDATORY_CONTINUATION_AT_EOF            = ErrorCode(1015)
    PARSER_DID_NOT_MATCH                     = ErrorCode(1020)
    PARSER_LOOKAHEAD_FAILURE_ONLY            = ErrorCode(1030)
    PARSER_STOPPED_BEFORE_END                = ErrorCode(1040)
    PARSER_LOOKAHEAD_MATCH_ONLY              = ErrorCode(1045)
    CAPTURE_STACK_NOT_EMPTY                  = ErrorCode(1050)
    MALFORMED_ERROR_STRING                   = ErrorCode(1060)
    AMBIGUOUS_ERROR_HANDLING                 = ErrorCode(1070)
    REDEFINED_DIRECTIVE                      = ErrorCode(1080)

    # fatal errors

    TREE_PROCESSING_CRASH                    = ErrorCode(10100)
    COMPILER_CRASH                           = ErrorCode(10200)
    AST_TRANSFORM_CRASH                      = ErrorCode(10300)

    def __init__(self, message: str, pos, code: ErrorCode = ERROR,
                 orig_pos: int = -1, line: int = -1, column: int = -1) -> None:
        assert isinstance(code, ErrorCode)
        assert not isinstance(pos, ErrorCode)
        assert code >= 0
        self.message = message    # type: str
        self._pos = pos           # type: int
        # TODO: Add some logic to avoid double assignment of the same error code?
        #       Problem: Same code might allowedly be used by two different parsers/compilers
        self.code = code          # type: ErrorCode
        self.orig_pos = orig_pos  # type: int
        self.line = line          # type: int
        self.column = column      # type: int

    def __str__(self):
        prefix = ''
        if self.line > 0:
            prefix = "%i:%i: " % (max(self.line, 0), max(self.column, 0))
        return prefix + "%s (%i): %s" % (self.severity, self.code, self.message)

    def __repr__(self):
        return 'Error("%s", %s, %i, %i, %i, %i)' \
               % (self.message, repr(self.code), self.pos, self.orig_pos, self.line, self.column)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value: int):
        self._pos = value
        # reset line and column values, because they might now not be valid any more
        self.line, self.column = -1, -1

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
    """Returns True, if error is merely a warning or a message."""
    return code < Error.ERROR


def is_error(code: int) -> bool:
    """Returns True, if error is a (fatal) error, not just a warning."""
    return code >= Error.ERROR


def is_fatal(code: int) -> bool:
    """Returns True, ir error is fatal. Fatal errors are typically raised
    when a crash (i.e. Python exception) occurs at later stages of the
    processing pipline (e.g. ast transformation, compiling). """
    return code >= Error.FATAL


# def Warning(message: str, pos, code: ErrorCode = Error.WARNING,
#             orig_pos: int = -1, line: int = -1, column: int = -1) -> Error:
#     """
#     Syntactic sugar for creating Error-objects that contain only a warning.
#     Raises a ValueError if `code` is not within the range for warnings.
#     """
#     if not is_warning(code):
#         raise ValueError("Tried to create a warning with a error code {}. "
#                          "Warning codes must be smaller than {}".format(code, Error.ERROR))
#     return Error(message, pos, code, orig_pos, line, column)


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
                           source_mapping: SourceMapFunc = lambda i: i):
    """Adds (or adjusts) line and column numbers of error messages inplace.

    Args:
        errors:  The list of errors as returned by the method
            ``errors()`` of a Node object
        original_text:  The source text on which the errors occurred.
            (Needed in order to determine the line and column numbers.)
        source_mapping:  A function that maps error positions to their
            positions in the original source file.
    """
    line_breaks = linebreaks(original_text)
    for err in errors:
        assert err.pos >= 0
        err.orig_pos = source_mapping(err.pos)
        err.line, err.column = line_col(line_breaks, err.orig_pos)
