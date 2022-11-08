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

The central class of module DHParser's ``error``  is the ``Error``-class.
The easiest way to create an error object is by instantiating
the Error class with an error message and a source position::

    >>> error = Error('Something went wrong', 123)
    >>> print(error)
    Error (1000): Something went wrong

However, in order to report errors, usually at least a line and
column-number

"""

from __future__ import annotations

from collections import namedtuple
import functools
import os
from typing import Iterable, Iterator, Union, List, Sequence, Dict, Callable

from DHParser.stringview import StringView
from DHParser.toolkit import linebreaks, line_col, is_filename, TypeAlias


__all__ = ('SourceMap',
           'SourceLocation',
           'SourceMapFunc',
           'ErrorCode',
           'Error',
           'is_fatal',
           'is_error',
           'is_warning',
           'has_errors',
           'only_errors',
           'add_source_locations',
           'canonical_error_strings',
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
           'ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING',
           'OPTIONAL_REDUNDANTLY_NESTED_WARNING',
           'UNCONNECTED_SYMBOL_WARNING',
           'REORDERING_OF_ALTERNATIVES_REQUIRED',
           'MANDATORY_CONTINUATION',
           'MANDATORY_CONTINUATION_AT_EOF',
           'MANDATORY_CONTINUATION_AT_EOF_NON_ROOT',
           'CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY',
           'AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT',
           'ERROR_WHILE_RECOVERING_FROM_ERROR',
           'PARSER_NEVER_TOUCHES_DOCUMENT',
           'PARSER_NEVER_TOUCHES_DOCUMENT',
           'PARSER_LOOKAHEAD_FAILURE_ONLY',
           'PARSER_STOPPED_BEFORE_END',
           'PARSER_STOPPED_ON_RETRY',
           'PARSER_LOOKAHEAD_MATCH_ONLY',
           'CUSTOM_PARSER_FAILURE',
           'CAPTURE_STACK_NOT_EMPTY',
           'CAPTURE_STACK_NOT_EMPTY_WARNING',
           'AUTOCAPTURED_SYMBOL_NOT_CLEARED',
           'MALFORMED_ERROR_STRING',
           'AMBIGUOUS_ERROR_HANDLING',
           'REDEFINED_DIRECTIVE',
           'UNDEFINED_RETRIEVE',
           'DIRECTIVE_FOR_NONEXISTANT_SYMBOL',
           'INAPPROPRIATE_SYMBOL_FOR_DIRECTIVE',
           'PEG_EXPRESSION_IN_DIRECTIVE_WO_BRACKETS',
           'CAPTURE_WITHOUT_PARSERNAME',
           'LOOKAHEAD_WITH_OPTIONAL_PARSER',
           'BADLY_NESTED_OPTIONAL_PARSER',
           'BAD_MANDATORY_SETUP',
           'DUPLICATE_PARSERS_IN_ALTERNATIVE',
           'BAD_ORDER_OF_ALTERNATIVES',
           'BAD_REPETITION_COUNT',
           'MALFORMED_REGULAR_EXPRESSION',
           'EMPTY_GRAMMAR_ERROR',
           'STRUCTURAL_ERROR_IN_AST',
           'TREE_PROCESSING_CRASH',
           'COMPILER_CRASH',
           'AST_TRANSFORM_CRASH',
           'RECURSION_DEPTH_LIMIT_HIT')


#######################################################################
#
#  source mapping
#
#######################################################################


# class SourceMap(NamedTuple):
#     original_name: str           # nome or path or uri of the original source file
#     positions: List[int]        # a list of locations
#     offsets: List[int]          # the corresponding offsets to be added from these locations onward
#     file_names: List[str]       # list of file_names to which the source locations relate
#     originals_dict: Dict[str, Union[str, StringView]]  # File names => (included) source texts

# SourceMap = NamedTuple('SourceMap',
#     [('original_name', str),
#      ('positions', List[int]),
#      ('offsets', List[int]),
#      ('file_names', List[str]),
#      ('originals_dict', Dict[str, Union[str, StringView]])])
# SourceMap.__module__ = __name__

SourceMap = namedtuple('SourceMap',
    ['original_name',  ## type: str
     'positions',      ## type: List[int]
     'offsets',        ## type: List[int]
     'file_names',     ## type: List[str]
     'originals_dict', ## type: Dict[str, Union[str, StringView]]
    ], module=__name__)

# class SourceLocation(NamedTuple):
#     original_name: str          # the file name (or path or uri) of the source code
#     original_text: Union[str, StringView]  # the source code itself
#     pos: int                  # a position within the code

# SourceLocation = NamedTuple('SourceLocation',
#     [('original_name', str),
#      ('original_text', Union[str, StringView]),
#      ('pos', int)])

SourceLocation = namedtuple('SourceLocation',
    ['original_name',  ## type: str
     'original_text',  ## type: Union[str, StringView]
     'pos',            ## type: int
    ], module=__name__)

SourceMapFunc: TypeAlias = Union[Callable[[int], SourceLocation], functools.partial]


#######################################################################
#
#  error codes
#
#######################################################################


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
CAPTURE_STACK_NOT_EMPTY_WARNING          = ErrorCode(640)
ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING     = ErrorCode(650)
OPTIONAL_REDUNDANTLY_NESTED_WARNING      = ErrorCode(660)
UNCONNECTED_SYMBOL_WARNING               = ErrorCode(670)

REORDERING_OF_ALTERNATIVES_REQUIRED      = ErrorCode(710)

# error codes

MANDATORY_CONTINUATION                   = ErrorCode(1010)
MANDATORY_CONTINUATION_AT_EOF            = ErrorCode(1015)
MANDATORY_CONTINUATION_AT_EOF_NON_ROOT   = ErrorCode(1017)
PARSER_NEVER_TOUCHES_DOCUMENT            = ErrorCode(1020)
PARSER_LOOKAHEAD_FAILURE_ONLY            = ErrorCode(1030)
PARSER_STOPPED_BEFORE_END                = ErrorCode(1040)
PARSER_STOPPED_ON_RETRY                  = ErrorCode(1042)
PARSER_LOOKAHEAD_MATCH_ONLY              = ErrorCode(1045)
CAPTURE_STACK_NOT_EMPTY                  = ErrorCode(1050)
CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY    = ErrorCode(1052)
AUTOCAPTURED_SYMBOL_NOT_CLEARED          = ErrorCode(1055)
AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT = ErrorCode(1057)
MALFORMED_ERROR_STRING                   = ErrorCode(1060)
AMBIGUOUS_ERROR_HANDLING                 = ErrorCode(1070)
REDEFINED_DIRECTIVE                      = ErrorCode(1080)
UNDEFINED_RETRIEVE                       = ErrorCode(1090)
DIRECTIVE_FOR_NONEXISTANT_SYMBOL         = ErrorCode(1100)
INAPPROPRIATE_SYMBOL_FOR_DIRECTIVE       = ErrorCode(1110)
PEG_EXPRESSION_IN_DIRECTIVE_WO_BRACKETS  = ErrorCode(1120)
CUSTOM_PARSER_FAILURE                    = ErrorCode(1130)

ERROR_WHILE_RECOVERING_FROM_ERROR        = ErrorCode(1301)

# EBNF-specific and static analysis errors

CAPTURE_WITHOUT_PARSERNAME               = ErrorCode(1510)
LOOKAHEAD_WITH_OPTIONAL_PARSER           = ErrorCode(1520)
BADLY_NESTED_OPTIONAL_PARSER             = ErrorCode(1530)
BAD_MANDATORY_SETUP                      = ErrorCode(1550)
DUPLICATE_PARSERS_IN_ALTERNATIVE         = ErrorCode(1560)
BAD_ORDER_OF_ALTERNATIVES                = ErrorCode(1570)
BAD_REPETITION_COUNT                     = ErrorCode(1580)
MALFORMED_REGULAR_EXPRESSION             = ErrorCode(1585)
EMPTY_GRAMMAR_ERROR                      = ErrorCode(1590)

# fatal errors

TREE_PROCESSING_CRASH                    = ErrorCode(10100)
COMPILER_CRASH                           = ErrorCode(10200)
AST_TRANSFORM_CRASH                      = ErrorCode(10300)
RECURSION_DEPTH_LIMIT_HIT                = ErrorCode(10400)
STRUCTURAL_ERROR_IN_AST                  = ErrorCode(10500)


#######################################################################
#
#  class Error
#
#######################################################################


class Error:
    """The Error class encapsulates the all information for a single
    error.

    :ivar message:  the error message as text string
    :ivar pos:  the position where the error occurred in the preprocessed text
    :ivar code:  the error-code, which also indicates the severity of the
        error::

               ========= ===========
               code      severity
               ========= ===========
               0         no error
               < 100     notice
               < 1000    warning
               < 10000   error
               >= 10000  fatal error
               ========= ===========

        In cas of a fatal error (error code >= 10000), no further compilation
        stages will be processed, because it is assumed that the syntax tree
        is too distorted for further processing.

    :ivar orig_pos:  the position of the error in the original source file,
        not in the preprocessed document. This is a write-once value!
    :ivar orig_doc:  the name or path or url of the original source file to
        which ``orig_pos`` is related. This is relevant, if the preprocessed
        document has been plugged together from several source files.
    :ivar line:  the line number where the error occurred in the original text.
        Lines are counted from 1 onward.
    :ivar column:  the column where the error occurred in the original text.
        Columns are counted from 1 onward.
    :ivar length:  the length in characters of the faulty passage (default is 1)
    :ivar end_line:  the line number of the position after the last character
        covered by the error in the original source.
    :ivar end_column:  the column number of the position after the last character
        covered by the error in the original source.
    :ivar related: a sequence of related errors.
    """

    __slots__ = ['message', 'code', '_pos', 'line', 'column', 'length',
                 'end_line', 'end_column', 'related', 'orig_pos', 'orig_doc',
                 'relatedUri']

    def __init__(self, message: str, pos: int, code: ErrorCode = ERROR,
                 line: int = -1, column: int = -1, length: int = 1,
                 related: Sequence['Error'] = [],
                 orig_pos: int = -1, orig_doc: str = '') -> None:
        assert isinstance(code, ErrorCode)
        assert not isinstance(pos, ErrorCode)
        assert code >= 0
        assert pos >= 0
        assert length >= 1
        self.message = message    # type: str
        self._pos = pos           # type: int
        # Add some logic to avoid double assignment of the same error code?
        # Problem: Same code might legitimately be used by two different parsers/compilers
        self.code = code          # type: ErrorCode
        self.orig_pos = orig_pos  # type: int
        self.orig_doc = orig_doc  # type: str
        self.line = line          # type: int
        self.column = column      # type: int
        # support for Language Server Protocol Diagnostics
        # see: https://microsoft.github.io/language-server-protocol/specifications/specification-current/#diagnostic
        self.length = length      # type: int
        self.end_line = -1        # type: int
        self.end_column = -1      # type: int
        self.related = tuple(related)   # type: Sequence['Error']

    def __eq__(self, other):
        return self.message == other.message and self.code == other.code \
               and self._pos == other._pos  # and self.length == other.length

    def __hash__(self):
        return hash((self.message, self.code, self._pos))

    def __str__(self):
        if self.orig_doc and self.orig_doc != 'UNKNOWN_FILE':
            prefix = self.orig_doc + ':'
        else:  prefix = ''
        if self.line > 0:
            # prefix += "%i:%i: " % (max(self.line, 0), max(self.column, 0))
            prefix += f"{max(self.line, 0)}:{max(self.column, 0)}: "
        # return prefix + "%s (%i): %s" % (self.severity, self.code, self.message)
        return prefix + f"{self.severity} ({self.code}): {self.message}"

    def __repr__(self):
        return 'Error("%s", %s, %i, %i, %i, %i)' \
               % (self.message, repr(self.code), self.pos, self.orig_pos, self.line, self.column)

    @property
    def pos(self) -> int:
        return self._pos

    @pos.setter
    def pos(self, value: int):
        self._pos = value
        # reset line and column values, because they might now not be valid anymore
        self.orig_pos = -1
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
        """Returns the Error as Language Server Protocol Diagnostic object.
        https://microsoft.github.io/language-server-protocol/specifications/specification-current/#diagnostic
        """
        def relatedObj(relatedError: 'Error') -> dict:
            uri = relatedError.orig_doc
            return {
                'location': {'uri': uri, 'range': relatedError.rangeObj()},
                'message': relatedError.message
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


def is_warning(code: Union[Error, int]) -> bool:
    """Returns True, if error is merely a warning or a message."""
    if isinstance(code, Error):  code = code.code
    return code < ERROR


def is_error(code: Union[Error, int]) -> bool:
    """Returns True, if error is a (fatal) error, not just a warning."""
    if isinstance(code, Error):  code = code.code
    return code >= ERROR


def is_fatal(code: Union[Error, int]) -> bool:
    """Returns True, ir error is fatal. Fatal errors are typically raised
    when a crash (i.e. Python exception) occurs at later stages of the
    processing pipeline (e.g. ast transformation, compiling). """
    if isinstance(code, Error):  code = code.code
    return code >= FATAL


# def Warning(message: str, pos, code: ErrorCode = WARNING,
#             orig_pos: int = -1, line: int = -1, column: int = -1) -> Error:
#     """
#     Syntactic sugar for creating Error-objects that contain only a warning.
#     Raises a ValueError if `code`` is not within the range for warnings.
#     """
#     if not is_warning(code):
#         raise ValueError("Tried to create a warning with a error code {}. "
#                          "Warning codes must be smaller than {}".format(code, ERROR))
#     return Error(message, pos, code, orig_pos, line, column)


def has_errors(messages: Iterable[Error], level: ErrorCode = ERROR) -> bool:
    """
    Returns True, if at least one entry in ``messages`` has at
    least the given error ``level``.
    """
    for err_obj in messages:
        if err_obj.code >= level:
            return True
    return False


def only_errors(messages: Iterable[Error], level: ErrorCode = ERROR) -> Iterator[Error]:
    """
    Returns an Iterator that yields only those messages that have
    at least the given error level.
    """
    return (err for err in messages if err.code >= level)


#######################################################################
#
# support for canonical representation, i.e.
# filename:line:column:severity (code):error string
#
#######################################################################


def add_source_locations(errors: List[Error], source_mapping: SourceMapFunc):
    """Adds (or adjusts) line and column numbers of error messages inplace.

    Args:
        errors:  The list of errors as returned by the method
            ``errors()`` of a Node object
        source_mapping:  A function that maps error positions to their
            positions in the original source file.
    """
    lb_dict = {}
    for err in errors:
        if err.pos < 0:
            raise ValueError(f'Illegal error position: {err.pos} Must be >= 0!')
        if err.orig_pos < 0:  # do not overwrite orig_pos if already set
            err.orig_doc, orig_text, err.orig_pos = source_mapping(err.pos)
            lbreaks = lb_dict.setdefault(orig_text, linebreaks(orig_text))
            err.line, err.column = line_col(lbreaks, err.orig_pos)
            if err.orig_pos + err.length > lbreaks[-1]:
                err.length = lbreaks[-1] - err.orig_pos  # err.length should not exceed text length
            err.end_line, err.end_column = line_col(lbreaks, err.orig_pos + err.length)


def canonical_error_strings(errors: List[Error]) -> List[str]:
    """Returns the list of error strings in canonical form that can be parsed by most
    editors, i.e. "relative filepath : line : column : severity (code) : error string"
    """
    if errors:
        error_strings = []
        for err in errors:
            source_file_name = err.orig_doc
            if source_file_name and is_filename(source_file_name):
                cwd = os.getcwd()
                if source_file_name.startswith(cwd):
                    rel_path = source_file_name[len(cwd):]
                else:
                    rel_path = source_file_name
                err_str = str(err)
                err_str = err_str[err_str.find(':'):]
                error_strings.append(rel_path + err_str)
            else:
                error_strings.append(str(err))
    else:
        error_strings = []
    return error_strings
