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
several of the the other DHParser-Modules or that are just very generic
so that they are best defined in a toolkit-module.
"""

import codecs
import hashlib
import io
import parser

try:
    import regex as re
except ImportError:
    import re
import sys

try:
    import typing
except ImportError:
    import DHParser.foreign_typing as typing
    sys.modules['typing'] = typing  # make it possible to import from typing

from typing import Any, Iterable, Sequence, Set, Union, Dict, cast

__all__ = ('escape_re',
           'escape_control_characters',
           'is_filename',
           'lstrip_docstring',
           'load_if_file',
           'is_python_code',
           'md5',
           'expand_table',
           'compile_python_object',
           'smart_list',
           'sane_parser_name')


#######################################################################
#
# miscellaneous (generic)
#
#######################################################################


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
    """Tries to guess whether string ``s`` is a file name."""
    return strg.find('\n') < 0 and strg[:1] != " " and strg[-1:] != " " \
        and all(strg.find(ch) < 0 for ch in '*?"<>|')
    #   and strg.select('*') < 0 and strg.select('?') < 0


#######################################################################
#
# loading and compiling
#
#######################################################################


def load_if_file(text_or_file) -> str:
    """Reads and returns content of a text-file if parameter
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
            if re.fullmatch(r'[\w/:. \\]+', text_or_file):
                raise FileNotFoundError('Not a valid file: ' + text_or_file + '!\n(Add "\\n" '
                                        'to distinguish source data from a file name.)')
            else:
                return text_or_file
    else:
        return text_or_file


def is_python_code(text_or_file: str) -> bool:
    """Checks whether 'text_or_file' is python code or the name of a file that
    contains python code.
    """
    if is_filename(text_or_file):
        return text_or_file[-3:].lower() == '.py'
    try:
        parser.suite(text_or_file)
        # compile(text_or_file, '<string>', 'exec')
        return True
    except (SyntaxError, ValueError, OverflowError):
        pass
    return False


def has_fenced_code(text_or_file: str, info_strings=('ebnf', 'test')) -> bool:
    """Checks whether `text_or_file` contains fenced code blocks, which are
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
    fence_tmpl = '\n(?:(?:``[`]*[ ]*(?:%s)(?=[ .\-:\n])[^`\n]*\n)' + \
                 '|(?:~~[~]*[ ]*(?:%s)(?=[ .\-:\n])[\n]*\n))'
    label_re = '|'.join('(?:%s)' % matched_string for matched_string in info_strings)
    rx_fence = re.compile(fence_tmpl % (label_re, label_re), flags=re.IGNORECASE)

    for match in rx_fence.finditer(markdown):
        matched_string = re.match('(?:\n`+)|(?:\n~+)', match.group(0)).group(0)
        if markdown.find(matched_string, match.end()) >= 0:
            return True
        else:
            break
    return False


def md5(*txt):
    """Returns the md5-checksum for `txt`. This can be used to test if
    some piece of text, for example a grammar source file, has changed.
    """
    md5_hash = hashlib.md5()
    for t in txt:
        md5_hash.update(t.encode('utf8'))
    return md5_hash.hexdigest()


def compile_python_object(python_src, catch_obj_regex=""):
    """Compiles the python source code and returns the (first) object
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
    """Returns the argument as list, depending on its type and content.

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
    """Expands a table by separating keywords that are tuples or strings
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
    """Checks whether given name is an acceptable parser name. Parser names
    must not be preceded or succeeded by a double underscore '__'!
    """
    return name and name[:2] != '__' and name[-2:] != '__'


#######################################################################
#
# initialization
#
#######################################################################


try:
    if sys.stdout.encoding.upper() != "UTF-8":
        # make sure that `print()` does not raise an error on
        # non-ASCII characters:
        sys.stdout = cast(io.TextIOWrapper, codecs.getwriter("utf-8")(cast(
            io.BytesIO, cast(io.TextIOWrapper, sys.stdout).detach())))
except AttributeError:
    # somebody has already taken care of this !?
    pass
