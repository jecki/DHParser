# toolkit.py - utility functions for DHParser
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
Module ``toolkit`` contains utility functions that are needed across
several of the the other DHParser-Modules Helper functions that are not
needed in more than one module are best placed within that module and
not in the toolkit-module. An acceptable exception from this rule are
functions that are very generic.
"""

import ast
import bisect
import functools
import hashlib
import io
import multiprocessing
import os
import sys
import threading

assert sys.version_info >= (3, 5, 3), "DHParser requires at least Python-Version 3.5.3!"

try:
    import regex as re
except ImportError:
    import re

import typing
from typing import Any, Iterable, Sequence, Set, Union, Dict, List, Tuple

try:
    import cython
    cython_optimized = cython.compiled  # type: bool
    if cython_optimized:  # not ?
        import DHParser.shadow_cython as cython
except ImportError:
    cython_optimized = False
    import DHParser.shadow_cython as cython

from DHParser.stringview import StringView


__all__ = ('typing',
           'cython',
           'cython_optimized',
           'NEVER_MATCH_PATTERN',
           'RX_NEVER_MATCH',
           'RxPatternType',
           're_find',
           'escape_re',
           'escape_control_characters',
           'is_filename',
           'relative_path',
           'concurrent_ident',
           'unrepr',
           'abbreviate_middle',
           'escape_formatstr',
           'as_identifier',
           'as_list',
           'first',
           'last',
           'linebreaks',
           'line_col',
           'text_pos',
           'lstrip_docstring',
           'issubtype',
           'isgenerictype',
           'load_if_file',
           'is_python_code',
           'md5',
           'expand_table',
           'compile_python_object',
           'smart_list',
           'sane_parser_name',
           'DHPARSER_DIR',
           'DHPARSER_PARENTDIR')


#######################################################################
#
# (Thread-safe) global variables and configuration
#
#######################################################################


DHPARSER_DIR = os.path.dirname(os.path.abspath(__file__))
DHPARSER_PARENTDIR = os.path.dirname(DHPARSER_DIR.rstrip('/'))


# global_id_counter = multiprocessing.Value('Q', 0)
#
#
# def gen_id() -> int:
#     """Generates a unique id."""
#     global global_id_counter
#     with global_id_counter.get_lock():
#         next_id = global_id_counter.value + 1
#         global_id_counter.value = next_id
#     return next_id


#######################################################################
#
# miscellaneous (generic)
#
#######################################################################


NEVER_MATCH_PATTERN = r'..(?<=^)'
RX_NEVER_MATCH = re.compile(NEVER_MATCH_PATTERN)


RxPatternType = Any


def re_find(s, r, pos=0, endpos=9223372036854775807):
    """
    Returns the match of the first occurrence of the regular expression
    `r` in string (or byte-sequence) `s`. This is essentially a wrapper
    for `re.finditer()` to avoid a try-catch StopIteration block.
    If `r` cannot be found, `None` will be returned.
    """
    rx = None
    if isinstance(r, str) or isinstance(r, bytes):
        if (pos, endpos) != (0, 9223372036854775807):
            rx = re.compile(r)
        else:
            try:
                m = next(re.finditer(r, s))
                return m
            except StopIteration:
                return None
    else:
        rx = r
    if rx:
        try:
            m = next(rx.finditer(s, pos, endpos))
            return m
        except StopIteration:
            return None


def escape_re(strg: str) -> str:
    """
    Returns the string with all regular expression special characters escaped.
    """

    # assert isinstance(strg, str)
    re_chars = r"\.^$*+?{}[]()#<>=|!"
    for esc_ch in re_chars:
        strg = strg.replace(esc_ch, '\\' + esc_ch)
    return strg


def escape_control_characters(strg: str) -> str:
    r"""
    Replace all control characters (e.g. `\n` `\t`) in a string
    by their backslashed representation and replaces backslash by
    double backslash.
    """
    s = repr(strg.replace('\\', r'\\')).replace('\\\\', '\\')[1:-1]
    if s.startswith(r"\'") and s.endswith((r"\'")):
        return ''.join(["'", s[2:-2], "'"])
    elif s.startswith(r'\"') and s.endswith((r'\"')):
        return ''.join(['"', s[2:-2], '"'])
    return s


def lstrip_docstring(docstring: str) -> str:
    """
    Strips leading whitespace from a docstring.
    """

    lines = docstring.replace('\t', '    ').split('\n')
    indent = 255  # highest integer value
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:  # ignore empty lines
            indent = min(indent, len(line) - len(stripped))
    if indent >= 255:
        indent = 0
    return '\n'.join([lines[0]] + [line[indent:] for line in lines[1:]])


def is_filename(strg: str) -> bool:
    """
    Tries to guess whether string ``strg`` is a file name.
    """
    return strg.find('\n') < 0 and strg[:1] != " " and strg[-1:] != " " \
        and all(strg.find(ch) < 0 for ch in '*?"<>|')
    #   and strg.select_if('*') < 0 and strg.select_if('?') < 0


@cython.locals(i=cython.int, L=cython.int)
def relative_path(from_path: str, to_path: str) -> str:
    """Returns the relative path in order to open a file from
    `to_path` when the script is running in `from_path`. Example:

        >>> relative_path('project/common/dir_A', 'project/dir_B')
        '../../dir_B'
    """
    from_path = os.path.normpath(os.path.abspath(from_path)).replace('\\', '/')
    to_path = os.path.normpath(os.path.abspath(to_path)).replace('\\', '/')
    if from_path and from_path[-1] != '/':
        from_path += '/'
    if to_path and to_path[-1] != '/':
        to_path += '/'
    i = 0
    L = min(len(from_path), len(to_path))
    while i < L and from_path[i] == to_path[i]:
        i += 1
    return os.path.normpath(from_path[i:].count('/') * '../' + to_path[i:])


def concurrent_ident() -> str:
    """
    Returns an identificator for the current process and thread
    """
    return multiprocessing.current_process().name + '_' + str(threading.get_ident())


class unrepr:
    """
    unrepr encapsulates a string representing a python function in such
    a way that the representation of the string yields the function call
    itself rather then a string representing the function call and delimited
    by quotation marks.

    Example:
        >>> "re.compile(r'abc+')"
        "re.compile(r'abc+')"
        >>> unrepr("re.compile(r'abc+')")
        re.compile(r'abc+')
    """
    def __init__(self, s: str):
        self.s = s  # type: str

    def __eq__(self, other: object) -> bool:
        if isinstance(other, unrepr):
            return self.s == other.s
        elif isinstance(other, str):
            return self.s == other
        else:
            raise TypeError('unrepr objects can only be compared with '
                            'other unrepr objects or strings!')

    def __str__(self) -> str:
        return self.s

    def __repr__(self) -> str:
        return self.s

@cython.locals(max_length=cython.int, length=cython.int, a=cython.int, b=cython.int)
def abbreviate_middle(s: str, max_length: int) -> str:
    """Shortens string `s` by replacing the middle part with an ellipsis
    sign ` ... ` if the size of the string exceeds `max_length`."""
    assert max_length > 6
    length = len(s)  # type: int
    if length > max_length:
        a = max_length // 2 - 2  # type: int
        b = max_length // 2 - 3  # type: int
        s = s[:a] + ' ... ' + s[-b:] if length > 40 else s
    return s


def escape_formatstr(s: str) -> str:
    """Replaces single curly braces by double curly-braces in string `s`,
    so that they are not misinterpreted as place-holder by "".format().
    """
    s = re.sub(r'(?<!\{)\{(?!\{)', '{{', s)
    s = re.sub(r'(?<!\})\}(?!\})', '}}', s)
    return s


RX_IDENTIFIER = re.compile(r'\w+')
RX_NON_IDENTIFIER = re.compile(r'[^\w]+')


@cython.locals(i=cython.int, delta=cython.int)
def as_identifier(s: str, replacement: str = "_") -> str:
    r"""Converts a string to an identifier that matches /\w+/ by
    substituting any character not matching /\w/ with the given
    replacement string:

    >>> as_identifier('EBNF-m')
    'EBNF_m'
    """
    ident = []
    i = 0
    while i < len(s):
        m = RX_IDENTIFIER.match(s, i)
        if m:
            ident.append(m.group(0))
            rng = m.span(0)
            i += rng[1] - rng[0]
        m = RX_NON_IDENTIFIER.match(s, i)
        if m:
            rng = m.span(0)
            delta = rng[1] - rng[0]
            ident.append(replacement * delta)
            i += delta  # rng[1] - rng[0]
    return ''.join(ident)


def as_list(item_or_sequence) -> List[Any]:
    """Turns an arbitrary sequence or a single item into a list. In case of
    a single item, the list contains this element as its sole item."""
    if isinstance(item_or_sequence, Iterable):
        return list(item_or_sequence)
    return [item_or_sequence]


def first(item_or_sequence: Union[Sequence, Any]) -> Any:
    """Returns an item or a the first item of a sequence of items."""
    if isinstance(item_or_sequence, Sequence):
        return item_or_sequence[0]
    else:
        return item_or_sequence


def last(item_or_sequence: Union[Sequence, Any]) -> Any:
    """Returns an item or a the first item of a sequence of items."""
    if isinstance(item_or_sequence, Sequence):
        return item_or_sequence[-1]
    else:
        return item_or_sequence


#######################################################################
#
# type system support
#
#######################################################################


def issubtype(sub_type, base_type) -> bool:
    """Returns `True` if sub_type is a sub_type of `base_type`.
    WARNING: Implementation is somewhat "hackish" and might break
    with new Python-versions.
    """
    def origin(t) -> tuple:
        try:
            ot = t.__origin__
            if ot is Union:
                try:
                    return tuple((a.__origin__ if a.__origin__ is not None else a)
                                 for a in t.__args__)
                except AttributeError:
                    try:
                        return tuple((a.__origin__ if a.__origin__ is not None else a)
                                     for a in t.__union_args__)
                    except AttributeError:
                        return t.__args__
        except AttributeError:
            if t == 'unicode':  # work-around for cython bug
                return (str,)
            return (t,)
        return (ot,) if ot is not None else (t,)
    true_st = origin(sub_type)
    true_bt = origin(base_type)[0]
    return any(issubclass(st, true_bt) for st in true_st)


def isgenerictype(t):
    """Returns `True` if `t` is a generic type.
    WARNING: This is very "hackish". Caller must make sure that `t`
    actually is a type!"""
    return str(t).endswith(']')


#######################################################################
#
# loading and compiling
#
#######################################################################

RX_FILEPATH = re.compile(r'[^ \t][^\n\t?*=]+(?<![ \t])')  # r'[\w/:. \\]+'


def load_if_file(text_or_file) -> str:
    """
    Reads and returns content of a text-file if parameter
    `text_or_file` is a file name (i.e. a single line string),
    otherwise (i.e. if `text_or_file` is a multi-line string)
    `text_or_file` is returned.
    """

    if is_filename(text_or_file):
        try:
            with open(text_or_file, encoding="utf-8") as f:
                content = f.read()
            return content
        except FileNotFoundError:
            if RX_FILEPATH.fullmatch(text_or_file):
                raise FileNotFoundError('File not found or not a valid filepath or URL: "'
                                        + text_or_file + '". \n(Add an empty line to '
                                        'distinguish source data from a file name.)')
            else:
                return text_or_file
    else:
        return text_or_file


def is_python_code(text_or_file: str) -> bool:
    """
    Checks whether 'text_or_file' is python code or the name of a file that
    contains python code.
    """
    if is_filename(text_or_file):
        return text_or_file[-3:].lower() == '.py'
    try:
        ast.parse(text_or_file)
        return True
    except (SyntaxError, ValueError, OverflowError):
        pass
    return False


def has_fenced_code(text_or_file: str, info_strings=('ebnf', 'test')) -> bool:
    """
    Checks whether `text_or_file` contains fenced code blocks, which are
    marked by one of the given info strings.
    See http://spec.commonmark.org/0.28/#fenced-code-blocks for more
    information on fenced code blocks in common mark documents.
    """
    if is_filename(text_or_file):
        with open(text_or_file, 'r', encoding='utf-8') as f:
            markdown = f.read()
    else:
        markdown = text_or_file

    if markdown.find('\n~~~') < 0 and markdown.find('\n```') < 0:
        return False

    if isinstance(info_strings, str):
        info_strings = (info_strings,)
    fence_tmpl = r'\n(?:(?:``[`]*[ ]*(?:%s)(?=[ .\-:\n])[^`\n]*\n)' + \
                 r'|(?:~~[~]*[ ]*(?:%s)(?=[ .\-:\n])[\n]*\n))'
    label_re = '|'.join('(?:%s)' % matched_string for matched_string in info_strings)
    rx_fence = re.compile(fence_tmpl % (label_re, label_re), flags=re.IGNORECASE)

    for match in rx_fence.finditer(markdown):
        matched_string = re.match(r'(?:\n`+)|(?:\n~+)', match.group(0)).group(0)
        if markdown.find(matched_string, match.end()) >= 0:
            return True
        else:
            break
    return False


def md5(*txt):
    """
    Returns the md5-checksum for `txt`. This can be used to test if
    some piece of text, for example a grammar source file, has changed.
    """

    md5_hash = hashlib.md5()
    for t in txt:
        md5_hash.update(t.encode('utf8'))
    return md5_hash.hexdigest()


def compile_python_object(python_src: str, catch_obj_regex="DSL") -> Any:
    """
    Compiles the python source code and returns the (first) object
    the name of which is matched by ``catch_obj_regex``. If catch_obj
    is the empty string, the namespace dictionary will be returned.
    """

    if isinstance(catch_obj_regex, str):
        catch_obj_regex = re.compile(catch_obj_regex)
    code = compile(python_src, '<string>', 'exec')
    namespace = {}  # type: Dict[str, Any]
    exec(code, namespace)  # safety risk?
    if catch_obj_regex.pattern:
        matches = [key for key in namespace if catch_obj_regex.match(key)]
        if len(matches) < 1:
            raise ValueError("No object matching /%s/ defined in source code." %
                             catch_obj_regex.pattern)
        elif len(matches) > 1:
            raise ValueError("Ambiguous matches for %s : %s" %
                             (str(catch_obj_regex), str(matches)))
        return namespace[matches[0]] if matches else None
    else:
        return namespace


#######################################################################
#
# text services
#
#######################################################################


@cython.locals(i=cython.int)
@functools.lru_cache()
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


@cython.locals(line=cython.int, column=cython.int, pos=cython.int)
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


@cython.returns(cython.int)
@cython.locals(line=cython.int, column=cython.int, i=cython.int)
def text_pos(text: Union[StringView, str],
             line: int, column: int,
             lbreaks: List[int] = []) -> int:
    """
    Returns the text-position for a given line and column or -1 if the line
    and column exceed the size of the text.
    """
    if lbreaks:
        try:
            return lbreaks[line] + column - 1
        except IndexError:
            return -1
    else:
        i = 0
        while line > 0 and i >= 0:
            i = text.find('\n', i + 1)
            line -= 1
        return i + column - 1


#######################################################################
#
# smart lists and multi-keyword tables
#
#######################################################################


# def smart_list(arg: Union[str, Iterable[T]]) -> Union[Sequence[str], Sequence[T]]:
def smart_list(arg: Union[str, Iterable, Any]) -> Union[Sequence, Set]:
    """
    Returns the argument as list, depending on its type and content.

    If the argument is a string, it will be interpreted as a list of
    comma separated values, trying ';', ',', ' ' as possible delimiters
    in this order, e.g.
    >>> smart_list('1; 2, 3; 4')
    ['1', '2, 3', '4']
    >>> smart_list('2, 3')
    ['2', '3']
    >>> smart_list('a b cd')
    ['a', 'b', 'cd']

    If the argument is a collection other than a string, it will be
    returned as is, e.g.
    >>> smart_list((1, 2, 3))
    (1, 2, 3)
    >>> smart_list({1, 2, 3})
    {1, 2, 3}

    If the argument is another iterable than a collection, it will
    be converted into a list, e.g.
    >>> smart_list(i for i in {1,2,3})
    [1, 2, 3]

    Finally, if none of the above is true, the argument will be
    wrapped in a list and returned, e.g.
    >>> smart_list(125)
    [125]
    """

    if isinstance(arg, str):
        for delimiter in (';', ','):
            lst = arg.split(delimiter)
            if len(lst) > 1:
                return [s.strip() for s in lst]
        return [s.strip() for s in arg.strip().split(' ')]
    elif isinstance(arg, Sequence) or isinstance(arg, Set):
        return arg
    elif isinstance(arg, Iterable):
        return list(arg)
    else:
        return [arg]


def expand_table(compact_table: Dict) -> Dict:
    """
    Expands a table by separating keywords that are tuples or strings
    containing comma separated words into single keyword entries with
    the same values. Returns the expanded table.
    Example:
    >>> expand_table({"a, b": 1, ('d','e','f'):5, "c":3})
    {'a': 1, 'b': 1, 'd': 5, 'e': 5, 'f': 5, 'c': 3}
    """

    expanded_table = {}  # type: Dict
    keys = list(compact_table.keys())
    for key in keys:
        value = compact_table[key]
        for k in smart_list(key):
            if k in expanded_table:
                raise KeyError('Key "%s" used more than once in compact table!' % key)
            expanded_table[k] = value
    return expanded_table


#######################################################################
#
# miscellaneous (DHParser-specific)
#
#######################################################################


def sane_parser_name(name) -> bool:
    """
    Checks whether given name is an acceptable parser name. Parser names
    must not be preceded or succeeded by a double underscore '__'!
    """

    return name and name[:2] != '__' and name[-2:] != '__'


#######################################################################
#
# initialization
#
#######################################################################


try:
    if sys.stdout.encoding.upper() != "UTF-8":  # and  platform.system() == "Windows":
        # make sure that `print()` does not raise an error on
        # non-ASCII characters:
        # sys.stdout = cast(io.TextIOWrapper, codecs.getwriter("utf-8")(cast(
        #     io.BytesIO, cast(io.TextIOWrapper, sys.stdout).detach())))
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), sys.stdout.encoding, 'replace')
except AttributeError:
    # somebody has already taken care of this !?
    pass
