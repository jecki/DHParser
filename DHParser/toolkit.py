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

import hashlib
import io
import multiprocessing
import os
import parser
import threading

try:
    import regex as re
except ImportError:
    import re
import sys
import typing
from typing import Any, Iterable, Sequence, Set, Union, Dict

try:
    import cython
    cython_optimized = cython.compiled  # type: bool
    if cython_optimized:
        import DHParser.shadow_cython as cython
except ImportError:
    cython_optimized = False
    import DHParser.shadow_cython as cython


__all__ = ('typing',
           'cython',
           'cython_optimized',
           'NEVER_MATCH_PATTERN',
           'RX_NEVER_MATCH',
           're_find',
           'escape_re',
           'escape_control_characters',
           'is_filename',
           'concurrent_ident',
           'unrepr',
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
    """
    Replace all control characters (e.g. \n \t) in a string by their backslashed representation.
    """

    return repr(strg).replace('\\\\', '\\')[1:-1]


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


#######################################################################
#
# type system support
#
#######################################################################


def issubtype(sub_type, base_type):
    def origin(t):
        try:
            ot = t.__origin__
        except AttributeError:
            if t == 'unicode':  # work-around for cython bug
                return str
            return t
        return ot if ot is not None else t
    return issubclass(origin(sub_type), origin(base_type))


def isgenerictype(t):
    return str(t).endswith(']')


#######################################################################
#
# loading and compiling
#
#######################################################################

RX_FILEPATH = re.compile(r'[^ \t][^\n\t?*]+(?<![ \t])')  # r'[\w/:. \\]+'


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
        # TODO: parser module will be deprecated from Python 3.9 onwards
        #       ast.parse(text_or_file, 'file.py', 'exec')?
        parser.suite(text_or_file)
        # compile(text_or_file, '<string>', 'exec')
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


def compile_python_object(python_src, catch_obj_regex=""):
    """
    Compiles the python source code and returns the (first) object
    the name of which is matched by ``catch_obj_regex``. If catch_obj
    is the empty string, the namespace dictionary will be returned.
    """

    if isinstance(catch_obj_regex, str):
        catch_obj_regex = re.compile(catch_obj_regex)
    code = compile(python_src, '<string>', 'exec')
    namespace = {}
    exec(code, namespace)  # safety risk?
    if catch_obj_regex:
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
