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

from typing import Iterable, Iterator, Union, List, Any, Sequence, Tuple

from DHParser.preprocess import SourceMapFunc
from DHParser.stringview import StringView
from DHParser.toolkit import linebreaks, line_col


__all__ = ('ErrorCode',
           'Error',
           'is_fatal',
           'is_error',
           'is_warning',
           'has_errors',
           'only_errors',
           'adjust_error_locations',
           'NO_ERROR',
           'NOTICE',
           'WARNING',
           'ERROR',
           'FATAL',
           'HIGHEST',
           'RESUME_NOTICE',
           'REDECLARED_TOKEN_WARNING',
           'UNUSED_ERROR_HANDLING_WARNING',
           'LEFT_RECURSION_WARNING',
           'UNDEFINED_SYMBOL_IN_TRANSTABLE_WARNING',
           'CANNOT_VERIFY_TRANSTABLE_WARNING',
           'CAPTURE_DROPPED_CONTENT_WARNING',
           'OPTIONAL_REDUNDANTLY_NESTED_WARNING',
           'UNCONNECTED_SYMBOL_WARNING',
           'REORDERING_OF_ALTERNATIVES_REQUIRED',
           'MANDATORY_CONTINUATION',
           'MANDATORY_CONTINUATION_AT_EOF',
           'PARSER_NEVER_TOUCHES_DOCUMENT',
           'PARSER_LOOKAHEAD_FAILURE_ONLY',
           'PARSER_STOPPED_BEFORE_END',
           'PARSER_LOOKAHEAD_MATCH_ONLY',
           'CAPTURE_STACK_NOT_EMPTY',
           'AUTORETRIEVED_SYMBOL_NOT_CLEARED',
           'MALFORMED_ERROR_STRING',
           'AMBIGUOUS_ERROR_HANDLING',
           'REDEFINED_DIRECTIVE',
           'UNDEFINED_RETRIEVE',
           'DIRECTIVE_FOR_NONEXISTANT_SYMBOL',
           'INAPPROPRIATE_SYMBOL_FOR_DIRECTIVE',
           'CAPTURE_WITHOUT_PARSERNAME',
           'LOOKAHEAD_WITH_OPTIONAL_PARSER',
           'BADLY_NESTED_OPTIONAL_PARSER',
           'BAD_MANDATORY_SETUP',
           'DUPLICATE_PARSERS_IN_ALTERNATIVE',
           'BAD_ORDER_OF_ALTERNATIVES',
           'BAD_REPETITION_COUNT',
           'EMPTY_GRAMMAR_ERROR',
           'TREE_PROCESSING_CRASH',
           'COMPILER_CRASH',
           'AST_TRANSFORM_CRASH',
           'RECURSION_DEPTH_LIMIT_HIT')


class ErrorCode(int):
    pass


# error levels

NO_ERROR = ErrorCode(0)
NOTICE   = ErrorCode(1)
WARNING  = ErrorCode(100)
ERROR    = ErrorCode(1000)
FATAL    = ErrorCode(10000)
HIGHEST  = FATAL

# notice codes

RESUME_NOTICE                            = ErrorCode(50)

# warning codes

REDECLARED_TOKEN_WARNING                 = ErrorCode(120)
UNUSED_ERROR_HANDLING_WARNING            = ErrorCode(130)
LEFT_RECURSION_WARNING                   = ErrorCode(140)  # obsolete!

UNDEFINED_SYMBOL_IN_TRANSTABLE_WARNING   = ErrorCode(610)
CANNOT_VERIFY_TRANSTABLE_WARNING         = ErrorCode(620)
CAPTURE_DROPPED_CONTENT_WARNING          = ErrorCode(630)
OPTIONAL_REDUNDANTLY_NESTED_WARNING      = ErrorCode(630)
UNCONNECTED_SYMBOL_WARNING               = ErrorCode(640)

REORDERING_OF_ALTERNATIVES_REQUIRED      = ErrorCode(710)

# error codes

MANDATORY_CONTINUATION                   = ErrorCode(1010)
MANDATORY_CONTINUATION_AT_EOF            = ErrorCode(1015)
PARSER_NEVER_TOUCHES_DOCUMENT            = ErrorCode(1020)
PARSER_LOOKAHEAD_FAILURE_ONLY            = ErrorCode(1030)
PARSER_STOPPED_BEFORE_END                = ErrorCode(1040)
PARSER_LOOKAHEAD_MATCH_ONLY              = ErrorCode(1045)
CAPTURE_STACK_NOT_EMPTY                  = ErrorCode(1050)
AUTORETRIEVED_SYMBOL_NOT_CLEARED         = ErrorCode(1055)
MALFORMED_ERROR_STRING                   = ErrorCode(1060)
AMBIGUOUS_ERROR_HANDLING                 = ErrorCode(1070)
REDEFINED_DIRECTIVE                      = ErrorCode(1080)
UNDEFINED_RETRIEVE                       = ErrorCode(1090)
DIRECTIVE_FOR_NONEXISTANT_SYMBOL         = ErrorCode(1100)
INAPPROPRIATE_SYMBOL_FOR_DIRECTIVE       = ErrorCode(1110)

# EBNF-specific static analysis errors

CAPTURE_WITHOUT_PARSERNAME               = ErrorCode(1510)
LOOKAHEAD_WITH_OPTIONAL_PARSER           = ErrorCode(1520)
BADLY_NESTED_OPTIONAL_PARSER             = ErrorCode(1530)
BAD_MANDATORY_SETUP                      = ErrorCode(1550)
DUPLICATE_PARSERS_IN_ALTERNATIVE         = ErrorCode(1560)
BAD_ORDER_OF_ALTERNATIVES                = ErrorCode(1570)
BAD_REPETITION_COUNT                     = ErrorCode(1580)
EMPTY_GRAMMAR_ERROR                      = ErrorCode(1590)

# fatal errors

TREE_PROCESSING_CRASH                    = ErrorCode(10100)
COMPILER_CRASH                           = ErrorCode(10200)
AST_TRANSFORM_CRASH                      = ErrorCode(10300)
RECURSION_DEPTH_LIMIT_HIT                = ErrorCode(10400)


class Error:
    __slots__ = ['message', 'code', '_pos', 'orig_pos', 'line', 'column',
                 'length', 'end_line', 'end_column', 'related', 'relatedUri']

    def __init__(self, message: str, pos: int, code: ErrorCode = ERROR,
                 orig_pos: int = -1, line: int = -1, column: int = -1,
                 length: int = 1, related: Sequence[Tuple['Error', str]] = []) -> None:
        assert isinstance(code, ErrorCode)
        assert not isinstance(pos, ErrorCode)
        assert code >= 0
        assert pos >= 0
        assert length >= 1
        self.message = message    # type: str
        self._pos = pos           # type: int
        # Add some logic to avoid double assignment of the same error code?
        # Problem: Same code might allowedly be used by two different parsers/compilers
        self.code = code          # type: ErrorCode
        self.orig_pos = orig_pos  # type: int
        self.line = line          # type: int
        self.column = column      # type: int
        # support for Languager Server Protocol Diagnostics
        # see: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#diagnostic
        self.length = length      # type: int
        self.end_line = -1        # type: int
        self.end_column = -1      # type: int
        self.related = tuple(related)   # type: Sequence[Tuple['Error', str]]

    def __str__(self):
        prefix = ''
        if self.line > 0:
            prefix = "%i:%i: " % (max(self.line, 0), max(self.column, 0))
        return prefix + "%s (%i): %s" % (self.severity, self.code, self.message)

    def __repr__(self):
        return 'Error("%s", %s, %i, %i, %i, %i)' \
               % (self.message, repr(self.code), self.pos, self.orig_pos, self.line, self.column)

    @property
    def pos(self) -> int:
        return self._pos

    @pos.setter
    def pos(self, value: int):
        self._pos = value
        # reset line and column values, because they might now not be valid any more
        self.line, self.column = -1, -1
        self.end_line, self.end_column = -1, -1

    @property
    def severity(self):
        """Returns a string representation of the error level, e.g. "warning"."""
        if self.code < WARNING:
            return "Notice"
        elif self.code < ERROR:
            return "Warning"
        elif self.code < FATAL:
            return "Error"
        else:
            return "Fatal"

    def visualize(self, document: str) -> str:
        """Shows the line of the document and the position where the error
        occurred."""
        start = document.rfind('\n', 0, self.pos) + 1
        stop = document.find('\n', self.pos)
        return document[start:stop] + '\n' + ' ' * (self.pos - start) + '^\n'

    def signature(self) -> bytes:
        """Returns a signature to quickly check the equality of errors"""
        return (self.line << 32 | self.column << 16 | self.code).to_bytes(8, 'big')

    def rangeObj(self) -> dict:
        """Returns the range (position plus length) of the error as an LSP-Range-Object.
        https://microsoft.github.io/language-server-protocol/specifications/specification-current/#range
        """
        assert self.line >= 1 and self.column >= 1 and self.end_line >= 1 and self.end_column >= 1
        return {'start': {'line': self.line - 1, 'character': self.column - 1},
                'end': {'line': self.end_line - 1, 'character': self.end_column - 1}}

    def diagnosticObj(self) -> dict:
        """Returns the Error as as Language Server Protocol Diagnostic object.
        https://microsoft.github.io/language-server-protocol/specifications/specification-current/#diagnostic
        """
        def relatedObj(relatedError: Sequence[Tuple['Error', str]]) -> dict:
            err, uri = relatedError
            return {
                'location': {'uri': uri, 'range': err.rangeObj()},
                'message': err.message
            }

        if self.code < WARNING:
            severity = 3
        elif self.code < ERROR:
            severity = 2
        else:
            severity = 1

        diagnostic = {
            'range': self.rangeObj(),
            'severity': severity,
            'code': self.code,
            'source': 'DHParser',
            'message': self.message,
            # 'tags': []
        }
        if self.related:
            diagnostic['relatedInformation'] = [relatedObj(err) for err in self.related]
        return diagnostic

def is_warning(code: int) -> bool:
    """Returns True, if error is merely a warning or a message."""
    return code < ERROR


def is_error(code: int) -> bool:
    """Returns True, if error is a (fatal) error, not just a warning."""
    return code >= ERROR


def is_fatal(code: int) -> bool:
    """Returns True, ir error is fatal. Fatal errors are typically raised
    when a crash (i.e. Python exception) occurs at later stages of the
    processing pipeline (e.g. ast transformation, compiling). """
    return code >= FATAL


# def Warning(message: str, pos, code: ErrorCode = WARNING,
#             orig_pos: int = -1, line: int = -1, column: int = -1) -> Error:
#     """
#     Syntactic sugar for creating Error-objects that contain only a warning.
#     Raises a ValueError if `code` is not within the range for warnings.
#     """
#     if not is_warning(code):
#         raise ValueError("Tried to create a warning with a error code {}. "
#                          "Warning codes must be smaller than {}".format(code, ERROR))
#     return Error(message, pos, code, orig_pos, line, column)


def has_errors(messages: Iterable[Error], level: int = ERROR) -> bool:
    """
    Returns True, if at least one entry in `messages` has at
    least the given error `level`.
    """
    for err_obj in messages:
        if err_obj.code >= level:
            return True
    return False


def only_errors(messages: Iterable[Error], level: int = ERROR) -> Iterator[Error]:
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
        # adjust length in case it exceeds the text size. As this is non-fatal
        # it should be adjusted rather than an error raised to avoid
        # unnecessary special-case treatments in other places
        if err.orig_pos + err.length > len(original_text):
            err.length = len(original_text) - err.orig_pos
        err.end_line, err.end_column = line_col(line_breaks, err.orig_pos + err.length)
