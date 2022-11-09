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
several of the other DHParser-Modules Helper functions that are not
needed in more than one module are best placed within that module and
not in the toolkit-module. An acceptable exception to this rule are
functions that are very generic.
"""

from __future__ import annotations

import ast
import bisect
import collections.abc
import concurrent.futures
import functools
import hashlib
import io
import json
import multiprocessing
import os
import sys
import threading
import traceback

assert sys.version_info >= (3, 5, 3), "DHParser requires at least Python-Version 3.5.3!"

try:
    if sys.version.find('PyPy') >= 0:
        import re  # regex might not work with PyPy reliably: https://pypi.org/project/regex/
    else:
        import regex as re
except ImportError:
    import re

try:
    import dataclasses
except ImportError:
    from DHParser.externallibs import dataclasses36 as dataclasses

import typing
from typing import Any, Iterable, Sequence, Set, AbstractSet, Union, Dict, List, Tuple, \
    Optional, Type, Callable
try:
    from typing import Protocol
except ImportError:
    class Protocol:
        pass
try:
    from typing import TypeAlias
except ImportError:
    from DHParser.externallibs.typing_extensions import TypeAlias

try:
    import cython
    cython_optimized = cython.compiled  # type: bool
    if cython_optimized:  # not ?
        import DHParser.externallibs.shadow_cython as cython
    cint = cython.int
except NameError:
    cint = int
except ImportError:
    cython_optimized = False
    import DHParser.externallibs.shadow_cython as cython

from DHParser.configuration import access_thread_locals, get_config_value, set_config_value, \
    NEVER_MATCH_PATTERN
from DHParser.stringview import StringView


__all__ = ('typing',
           're',
           'dataclasses',
           'Protocol',
           'TypeAlias',
           'cython_optimized',
           'identify_python',
           'identity',
           # 'gen_id',
           'ThreadLocalSingletonFactory',
           'RX_NEVER_MATCH',
           'RX_ENTITY',
           'RX_NON_ASCII',
           'validate_XML_attribute_value',
           'fix_XML_attribute_value',
           'lxml_XML_attribute_value',
           'RxPatternType',
           're_find',
           'escape_re',
           'escape_ctrl_chars',
           'is_filename',
           'is_html_name',
           'relative_path',
           'split_path',
           'concurrent_ident',
           'unrepr',
           'abbreviate_middle',
           'wrap_str_nicely',
           'printw',
           'escape_formatstr',
           'as_identifier',
           'as_list',
           'as_tuple',
           'first',
           'last',
           'NOPE',
           'matching_brackets',
           'linebreaks',
           'line_col',
           'text_pos',
           'normalize_docstring',
           'issubtype',
           'isgenerictype',
           'load_if_file',
           'is_python_code',
           'md5',
           'expand_table',
           'compile_python_object',
           'smart_list',
           'JSON_Type',
           'JSON_Dict',
           'JSONstr',
           'JSONnull',
           'json_encode_string',
           'json_dumps',
           'json_rpc',
           'sane_parser_name',
           'normalize_circular_path',
           'DHPARSER_DIR',
           'deprecated',
           'deprecation_warning')


#######################################################################
#
# miscellaneous (generic)
#
#######################################################################

def identify_python() -> str:
    """Returns a reasonable identification string for the python interpreter,
    e.g. "cpython 3.8.6"."""
    return "%s %i.%i.%i" % (sys.implementation.name, *sys.version_info[:3])


def identity(x):
    """Canonical identity function. The purpose of defining identity()
    here is to allow it to serve as a default value and to be
    able to check whether a function parameter has been assigned
    another than the default value or not."""
    return x



global_id_counter: int = 0


# def gen_id() -> str:
#     """Generates a unique id. (Not thread-safe!)"""
#     global global_id_counter
#     global_id_counter += 1
#     return str(global_id_counter)


class ThreadLocalSingletonFactory:
    """
    Generates a singleton-factory that returns one and
    the same instance of `class_or_factory` for one and the
    same thread, but different instances for different threads.
    """
    def __init__(self, class_or_factory, name: str = "", *, ident: str = ""):
        self.class_or_factory = class_or_factory
        self.singleton_name = "{NAME}_{ID}_singleton".format(
            NAME=name or class_or_factory.__name__, ID=str(id(self)))
        THREAD_LOCALS = access_thread_locals()
        assert not hasattr(THREAD_LOCALS, self.singleton_name), self.singleton_name

    def __call__(self):
        THREAD_LOCALS = access_thread_locals()
        try:
            singleton = getattr(THREAD_LOCALS, self.singleton_name)
        except AttributeError:
            setattr(THREAD_LOCALS, self.singleton_name, self.class_or_factory())
            singleton = getattr(THREAD_LOCALS, self.singleton_name)
        return singleton


@functools.lru_cache()
def is_filename(strg: str) -> bool:
    """
    Tries to guess whether string ``strg`` is a file name.
    """
    return strg.find('\n') < 0 and strg[:1] != " " and strg[-1:] != " " \
        and all(strg.find(ch) < 0 for ch in '*?"<>|')
    #   and strg.select_if('*') < 0 and strg.select_if('?') < 0


def is_html_name(url: str) -> bool:
    """Returns True, if url ends with .htm or .html"""
    return url[-5:].lower() == '.html' or url[-4:].lower() == '.htm'


@cython.locals(i=cython.int, L=cython.int)
def relative_path(from_path: str, to_path: str) -> str:
    """Returns the relative path in order to open a file from
    `to_path` when the script is running in `from_path`. Example:

        >>> relative_path('project/common/dir_A', 'project/dir_B').replace(chr(92), '/')
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


def split_path(path: str) -> Tuple[str, ...]:
    """Splits a filesystem path into its components. Other than
    os.path.split() it does not only split of the last part::

        >>> split_path('a/b/c')
        ('a', 'b', 'c')
        >>> os.path.split('a/b/c')  # for comparison.
        ('a/b', 'c')
    """
    split = os.path.split(path)
    while split[0]:
        split = os.path.split(split[0]) + split[1:]
    return split[1:]


def concurrent_ident() -> str:
    """
    Returns an identificator for the current process and thread
    """
    return multiprocessing.current_process().name + '_' + str(threading.get_ident())


class unrepr:
    """
    unrepr encapsulates a string representing a python function in such
    a way that the representation of the string yields the function call
    itself rather than a string representing the function call and delimited
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


def as_list(item_or_sequence) -> List[Any]:
    """Turns an arbitrary sequence or a single item into a list. In case of
    a single item, the list contains this element as its sole item."""
    if isinstance(item_or_sequence, Iterable):
        return list(item_or_sequence)
    return [item_or_sequence]


def as_tuple(item_or_sequence) -> List[Any]:
    """Turns an arbitrary sequence or a single item into a tuple. In case of
    a single item, the tuple contains this element as its sole item."""
    if isinstance(item_or_sequence, Iterable):
        return tuple(item_or_sequence)
    return (item_or_sequence,)


def first(item_or_sequence: Union[Sequence, Any]) -> Any:
    """Returns an item or the first item of a sequence of items."""
    if isinstance(item_or_sequence, Sequence):
        return item_or_sequence[0]
    else:
        return item_or_sequence


def last(item_or_sequence: Union[Sequence, Any]) -> Any:
    """Returns an item or the first item of a sequence of items."""
    if isinstance(item_or_sequence, Sequence):
        return item_or_sequence[-1]
    else:
        return item_or_sequence


DEPRECATION_WARNINGS_ISSUED: Set[str] = set()


def deprecation_warning(message: str):
    """Issues a deprecation warning. Makes sure that each message is only
    called once."""
    if message not in DEPRECATION_WARNINGS_ISSUED:
        DEPRECATION_WARNINGS_ISSUED.add(message)
        try:
            raise DeprecationWarning(message)
        except DeprecationWarning as e:
            if get_config_value('deprecation_policy') == 'warn':
                stacktrace = traceback.format_exc()
                print(stacktrace)
            else:
                raise e


def deprecated(message: str) -> Callable:
    """Marks a function as deprecated and emits a deprecation
    message on its first use::

        >>> @deprecated('This function is deprecated!')
        ... def bad():
        ...     pass
        >>> save = get_config_value('deprecation_policy')
        >>> set_config_value('deprecation_policy', 'fail')
        >>> try: bad()
        ... except DeprecationWarning as w:  print(w)
        This function is deprecated!
        >>> set_config_value('deprecation_policy', save)

    """
    assert isinstance(message, str)
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            deprecation_warning(message)
            return f(*args, **kwargs)
        return wrapper
    return decorator


#######################################################################
#
# miscellaneous (DHParser-specific)
#
#######################################################################


DHPARSER_DIR = os.path.dirname(os.path.abspath(__file__))
# DHPARSER_PARENTDIR = os.path.dirname(DHPARSER_DIR.rstrip('/').rstrip('\\'))


def sane_parser_name(name) -> bool:
    """
    Checks whether given name is an acceptable parser name. Parser names
    must not be preceded or succeeded by a double underscore '__'!
    """

    return name and name[:2] != '__' and name[-2:] != '__'


def normalize_circular_path(path: Union[Tuple[str, ...], AbstractSet[Tuple[str, ...]]]) \
        -> Union[Tuple[str, ...], Set[Tuple[str, ...]]]:
    """Returns a normalized version of a `circular path` represented as
    a tuple or - if called with a set of paths instead of a single path
    - a set of normalized paths.

    A circular (or "recursive") path is a tuple of items, the order of which
    matters, but not the starting point. This can, for example, be a tuple of
    references from one symbol defined in an EBNF source text back to
    (but excluding) itself.

    For example, when defining a grammar for arithmetic, the tuple
    ('expression', 'term', 'factor') if a recursive path, because the
    definition of a factor includes a (bracketed) expression and thus
    refers back to `expression`
    Normalizing is done by "ring-shifting" the tuple so that it starts
    with the alphabetically first symbol in the path.

    >>> normalize_circular_path(('term', 'factor', 'expression'))
    ('expression', 'term', 'factor')
    """
    if isinstance(path, AbstractSet):
        return {normalize_circular_path(p) for p in path}
    else:
        assert isinstance(path, Tuple)
        first_sym = min(path)
        i = path.index(first_sym)
        return path[i:] + path[:i]



#######################################################################
#
#  string manipulation and regular expressions
#
#######################################################################


RX_NEVER_MATCH = re.compile(NEVER_MATCH_PATTERN)
RxPatternType = Any


def re_find(s, r, pos=0, endpos=9223372036854775807):
    """
    Returns the match of the first occurrence of the regular expression
    `r` in string (or byte-sequence) `s`. This is essentially a wrapper
    for `re.finditer()` to avoid a try-catch StopIteration block.
    If `r` cannot be found, `None` will be returned.
    """
    if isinstance(r, (str, bytes)):
        if (pos, endpos) != (0, 9223372036854775807):
            r = re.compile(r)
        else:
            try:
                m = next(re.finditer(r, s))
                return m
            except StopIteration:
                return None
    if r:
        try:
            m = next(r.finditer(s, pos, endpos))
            return m
        except StopIteration:
            return None


def escape_re(strg: str) -> str:
    """
    Returns the string with all regular expression special characters escaped.
    TODO: Remove this function in favor of re.escape()
    """

    # assert isinstance(strg, str)
    # re_chars = r"\.^$*+?{}[]()#<>=|!"
    # for esc_ch in re_chars:
    #     strg = strg.replace(esc_ch, '\\' + esc_ch)
    # return strg
    return re.escape(strg)


def escape_ctrl_chars(strg: str) -> str:
    r"""
    Replace all control characters (e.g. `\n` `\t`) in a string
    by their back-slashed representation and replaces backslash by
    double backslash.
    """
    s = repr(strg.replace('\\', r'\\')).replace('\\\\', '\\')[1:-1]
    if s[:2] == r"\'" and s[-2:] == r"\'":
        return ''.join(["'", s[2:-2], "'"])
    elif s[:2] == r'\"' and s[-2:] == r'\"':
        return ''.join(['"', s[2:-2], '"'])
    return s


def normalize_docstring(docstring: str) -> str:
    """
    Strips leading indentation as well as leading
    and trailing empty lines from a docstring.
    """
    lines = docstring.replace('\t', '    ').split('\n')
    # determine indentation
    indent = 255  # highest integer value
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:  # ignore empty lines
            indent = min(indent, len(line) - len(stripped))
    if indent >= 255:  indent = 0
    # remove trailing empty lines
    while lines and not lines[-1].strip(): lines.pop()
    if lines:
        if lines[0].strip():
            lines = [lines[0]] + [line[indent:] for line in lines[1:]]
        else:
            lines = [line[indent:] for line in lines[1:]]
        # remove any empty lines at the beginning
        while lines and not lines[0].strip(): del lines[0]
        return '\n'.join(lines)
    return ''


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


@cython.locals(wrap_column=cython.int, tolerance=cython.int, a=cython.int, i=cython.int, k=cython.int, m=cython.int)
def wrap_str_nicely(s: str, wrap_column: int=79, tolerance: int=24,
                    wrap_chars: str=")]>, ") -> str:
    r"""Line-wraps a single-line output string at 'wrap_column'. Tries to
    find a suitable point for wrapping, i.e. after any of the wrap_characters.

    If the strings spans multiple lines, the existing linebreaks will be kept
    and no rewrapping takes place. In order to enforce rewrapping of multiline
    strings, use: ``wrap_str_nicely(repr(s)[1:-1])``. (repr() replaces
    linebreaks by the \\n-marker. The slicing [1:-1] removes the opening
    and closing angular quotation marks that repr adds.

    Examples::

        >>> s = ('(X (l ",.") (A (O "123") (P (:Text "4") (em "56"))) '
        ...      '(em (m "!?")) (B (Q (em "78") (:Text "9")) (R "abc")) '
        ...      '(n "+-"))')
        >>> print(wrap_str_nicely(s))
        (X (l ",.") (A (O "123") (P (:Text "4") (em "56"))) (em (m "!?"))
         (B (Q (em "78") (:Text "9")) (R "abc")) (n "+-"))
        >>> s = ('(X (s) (A (u) (C "One,")) (em (A (C " ") (D "two, ")))'
        ...      '(B (E "three, ") (F "four!") (t))))')
        >>> print(wrap_str_nicely(s))
        (X (s) (A (u) (C "One,")) (em (A (C " ") (D "two, ")))(B (E "three, ")
         (F "four!") (t))))
        >>> s = ("[Node('word', 'This'), Node('word', 'is'), "
        ...      "Node('word', 'Buckingham'), Node('word', 'Palace')]")
        >>> print(wrap_str_nicely(s))
        [Node('word', 'This'), Node('word', 'is'), Node('word', 'Buckingham'),
         Node('word', 'Palace')]
        >>> s = ("Node('phrase', (Node('word', 'Buckingham'), "
        ...      "Node('blank', ' '), Node('word', 'Palace')))")
        >>> print(wrap_str_nicely(s))
        Node('phrase', (Node('word', 'Buckingham'), Node('blank', ' '),
         Node('word', 'Palace')))
        >>> s = ('<hard>Please mark up <foreign lang="de">Stadt\n<lb/></foreign>'
        ...      '<location><foreign lang="de"><em>München</em></foreign> '
        ...      'in Bavaria</location> in this sentence.</hard>')
        >>> print(wrap_str_nicely(s))
        <hard>Please mark up <foreign lang="de">Stadt
        <lb/></foreign><location><foreign lang="de"><em>München</em></foreign> in Bavaria</location> in this sentence.</hard>
        >>> print(wrap_str_nicely(repr(s)[1:-1]))  # repr to ignore the linebreaks
        <hard>Please mark up <foreign lang="de">Stadt\n<lb/></foreign><location>
        <foreign lang="de"><em>München</em></foreign> in Bavaria</location>
         in this sentence.</hard>
    """
    assert 2 <= tolerance
    assert wrap_column > tolerance
    if len(s) <= wrap_column or s.rfind('\n') >= 0:  return s
    parts = []
    a = 0
    i = wrap_column
    while i < len(s):
        for ch in wrap_chars:
            m = i
            while s[m] == ch:  m -= 1
            if i - m > tolerance // 2:
                continue
            k = s.rfind(ch, a, m)
            probe = s[k + 1]
            while k < i and s[k + 1] in wrap_chars and s[k + 1] != ' ':  k += 1
            if i - k <= tolerance:
                parts.append(s[a:k + 1])
                a = k + 1
                i = k + 1 + wrap_column
                break
        else:
            parts.append(s[a:i])
            a = i
            i += wrap_column
    if a < len(s) - 1:  parts.append(s[a:])
    return '\n'.join(parts)


def printw(s: Any, wrap_column: int=79, tolerance: int=24,
           wrap_chars: str=")]>, "):
    """Prints the string or other object nicely wrapped.
    See :py:func:`wrap_str_nicely`."""
    if isinstance(s, (list, tuple, dict)) and wrap_chars == ")]>, ":
        wrap_chars = ",)]> "
        s = repr(s)
    elif not isinstance(s, str):
        s = repr(s)
    print(wrap_str_nicely(s, wrap_column, tolerance, wrap_chars))


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


NOPE = []  # a list that is empty and is supposed to remain empty


@cython.locals(da=cython.int, db=cython.int, a=cython.int, b=cython.int)
def matching_brackets(text: str,
                      openB: str,
                      closeB: str,
                      unmatched: list = NOPE) -> List[Tuple[int, int]]:
    """Returns a list of matching bracket positions. Fills an empty list
    passed to parameter `unmatched` with the positions of all
    unmatched brackets.

    >>> matching_brackets('(a(b)c)', '(', ')')
    [(2, 4), (0, 6)]
    >>> matching_brackets('(a)b(c)', '(', ')')
    [(0, 2), (4, 6)]
    >>> unmatched = []
    >>> matching_brackets('ab(c', '(', ')', unmatched)
    []
    >>> unmatched
    [2]
    """
    assert not unmatched, \
        "Please pass an empty list as unmatched flag, not: " + str(unmatched)
    stack, matches = [], []
    da = len(openB)
    db = len(closeB)
    a = text.find(openB)
    b = text.find(closeB)
    while a >= 0 and b >= 0:
        while 0 <= a < b:
            stack.append(a)
            a = text.find(openB, a + da)
        while 0 <= b < a:
            try:
                matches.append((stack.pop(), b))
            except IndexError:
                if unmatched is not NOPE:  unmatched.append(b)
            b = text.find(closeB, b + db)
    while b >= 0:
        try:
            matches.append((stack.pop(), b))
        except IndexError:
            if unmatched is not NOPE:  unmatched.append(b)
        b = text.find(closeB, b + db)
    if unmatched is not NOPE:
        if stack:
            unmatched.extend(stack)
        elif a >= 0:
            unmatched.append(a)
    return matches


# see definition of EntityRef in: XML-grammar: XML-grammar, see https://www.w3.org/TR/xml/
RX_ENTITY = re.compile(r'&(?:_|:|[A-Z]|[a-z]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]'
                       r'|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]|[\u2070-\u218F]'
                       r'|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]'
                       r'|[\U00010000-\U000EFFFF])(?:_|:|-|\.|[A-Z]|[a-z]|[0-9]|\u00B7'
                       r'|[\u0300-\u036F]|[\u203F-\u2040]|[\u00C0-\u00D6]|[\u00D8-\u00F6]'
                       r'|[\u00F8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]'
                       r'|[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]'
                       r'|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF])*;')


def validate_XML_attribute_value(value: Any) -> str:
    """Validates an XML-attribute value and returns the quoted string-value
    if successful. Otherwise raises a ValueError.
    """
    value = str(value)
    contains_doublequote = value.find('"') >= 0
    if contains_doublequote and value.find("'") >= 0:
        raise ValueError(('Illegal XML-attribute value: %s  (Cannot be quoted, because '
                          'both single and double quotation mark are contained in the '
                          'value. Use enttites to avoid this conflict.)') % value)
    if value.find('<') >= 0:
        raise ValueError('XML-attribute value  %s  must not contain "<"!' % value)
    i = value.find('&')
    while i >= 0:
        if not RX_ENTITY.match(value, i):
            raise ValueError('Ampersand.sign "&" not allowed in XML-attribute value '
                             'unless it is the beginning of an entity: ' + value)
        i = value.find('&', i + 1)
    return ("'%s'" % value) if contains_doublequote else '"%s"' % value


def fix_XML_attribute_value(value: Any) -> str:
    """Returns the quoted XML-attribute value. In case the values
    contains illegal characters, like '<', these will be replaced by
    XML-entities."""
    value = str(value)
    value = value.replace('<', '&lt;')
    # value = value.replace('>', '&gt;')
    i = value.find('&')
    while i >= 0:
        if not RX_ENTITY.match(value, i):
            value = value[:i] + '&amp;' + value[i + 1:]
        i = value.find('&', i + 1)
    if value.find('"') >= 0:
        if value.find("'") >= 0:
            value = value.replace("'", "&apos;")
        value = "'%s'" % value
    else:
        value = '"%s"' % value
    return value


RX_NON_ASCII = re.compile(r'[^\U00000000-\U000000FF]')


def lxml_XML_attribute_value(value: Any) -> str:
    """Makes sure that the attribute value works with the lxml-library,
    at the cost of replacing all characters with a code > 256 by
    a quesiton mark.

    :param value: the original attribute value
    :return: the quoted and lxml-compatible attribute value.
    """
    value = str(value)
    value = RX_NON_ASCII.sub('?', value)
    return fix_XML_attribute_value(value)


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
        def fix(t: Any) -> Any:
            return {'Dict': dict, 'Tuple': tuple, 'List': list}.get(t, t)
        try:
            if isinstance(t, (str, bytes)):  t = eval(t)
            ot = t.__origin__
            if ot is Union:
                try:
                    return tuple((fix(a.__origin__) if a.__origin__ is not None else fix(a))
                                 for a in t.__args__)
                except AttributeError:
                    try:
                        return tuple((fix(a.__origin__) if a.__origin__ is not None else fix(a))
                                     for a in t.__union_args__)
                    except AttributeError:
                        return t.__args__
        except AttributeError:
            if t == 'unicode':  # work-around for cython bug
                return str,
            return fix(t),
        return (fix(ot),) if ot is not None else (fix(t),)
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
                raise FileNotFoundError(
                    'File not found or not a valid filepath or URL: "%s".\n' 
                    '(If "%s" was not meant to be a file name then, please, add '
                    'an empty line to distinguish source data from a file name.)'
                    % (text_or_file, text_or_file))
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
    assert isinstance(text, (StringView, str)), \
        "Type %s of `text` is not a string type!" % str(type(text))
    lbr = [-1]
    i = text.find('\n', 0)
    while i >= 0:
        lbr.append(i)
        i = text.find('\n', i + 1)
    lbr.append(len(text))
    return lbr


@cython.locals(line=cython.int, column=cython.int)
def line_col(lbreaks: List[int], pos: cint) -> Tuple[cint, cint]:
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
    Example::

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
# JSON RPC support
#
#######################################################################


JSON_Type: TypeAlias = Union[Dict, Sequence, str, int, float, None]
JSON_Dict: TypeAlias = Dict[str, JSON_Type]


class JSONstr:
    """
    JSONStr is a special type that encapsulates already serialized
    json-chunks in json object-trees. ``json_dumps`` will insert the content
    of a JSONStr-object literally, rather than serializing it as other
    objects.
    """
    __slots__ = ['serialized_json']

    def __repr__(self):
        return self.serialized_json

    def __init__(self, serialized_json: str):
        assert isinstance(serialized_json, str)
        self.serialized_json = serialized_json


class JSONnull:
    """JSONnull is a special type that is serialized as ``null`` by ``json_dumps``.
    This can be used whenever it is inconvenient to use ``None`` as the null-value.
    """
    __slots__ = []

    def __repr__(self):
        return 'null'


# the following string-escaping tables and procedures have been
# copy-pasted and slightly adapted from the std-library
ESCAPE = re.compile(r'[\x00-\x1f\\"\b\f\n\r\t]')
ESCAPE_DCT = {'\\': '\\\\', '"': '\\"', '\x08': '\\b', '\x0c': '\\f', '\n': '\\n', '\r': '\\r',
              '\t': '\\t', '\x00': '\\u0000', '\x01': '\\u0001', '\x02': '\\u0002',
              '\x03': '\\u0003', '\x04': '\\u0004', '\x05': '\\u0005', '\x06': '\\u0006',
              '\x07': '\\u0007', '\x0b': '\\u000b', '\x0e': '\\u000e', '\x0f': '\\u000f',
              '\x10': '\\u0010', '\x11': '\\u0011', '\x12': '\\u0012', '\x13': '\\u0013',
              '\x14': '\\u0014', '\x15': '\\u0015', '\x16': '\\u0016', '\x17': '\\u0017',
              '\x18': '\\u0018', '\x19': '\\u0019', '\x1a': '\\u001a', '\x1b': '\\u001b',
              '\x1c': '\\u001c', '\x1d': '\\u001d', '\x1e': '\\u001e', '\x1f': '\\u001f'}


def json_encode_string(s: str) -> str:
    return '"' + ESCAPE.sub(lambda m: ESCAPE_DCT[m.group(0)], s) + '"'


def json_dumps(obj: JSON_Type, *, cls=json.JSONEncoder, partially_serialized: bool=False) -> str:
    """Returns json-object as string. Other than the standard-library's
    `json.dumps()`-function `json_dumps` allows to include alrady serialzed
    parts (in the form of JSONStr-objects) in the json-object. Example::
        
        >>> already_serialized = '{"width":640,"height":400"}'
        >>> literal = JSONstr(already_serialized)
        >>> json_obj = {"jsonrpc": "2.0", "method": "report_size", "params": literal, "id": None}
        >>> json_dumps(json_obj, partially_serialized=True)
        '{"jsonrpc":"2.0","method":"report_size","params":{"width":640,"height":400"},"id":null}'

    :param obj: A json-object (or a tree of json-objects) to be serialized
    :param cls: The class of a custom json-encoder berived from ``json.JSONEncoder``
    :param partially_serialized: If True, :py:class:`JSONStr`-objects within the json tree
        will be encoded (by inserting their content). If False, :py:class:`JSONStr`-objects
        will raise a TypeError, but encoding will be faster.
    :return: The string-serialized form of the json-object.
    """

    # def serialize(obj) -> Iterator[str]:
    #     if isinstance(obj, str):
    #         yield json_encode_string(obj)
    #     elif isinstance(obj, dict):
    #         buf = '{'
    #         for k, v in obj.items():
    #             yield buf + '"' + k + '":'
    #             yield from serialize(v)
    #             buf = ','
    #         yield '}'
    #     elif isinstance(obj, (list, tuple)):
    #         buf = '['
    #         for item in obj:
    #             yield buf
    #             yield from serialize(item)
    #             buf = ','
    #         yield ']'
    #     elif obj is True:
    #         yield 'true'
    #     elif obj is False:
    #         yield 'false'
    #     elif isinstance(obj, int):
    #         # NOTE: test for int must follow test for bool, because True and False
    #         #       are treated as instances of int as well by Python
    #         yield str(obj)
    #     elif isinstance(obj, float):
    #         yield str(obj)
    #     elif obj is None:
    #         yield 'null'
    #     elif isinstance(obj, JSONStr):
    #         yield obj.serialized_json
    #     else:
    #         yield from serialize(custom_encoder.default(obj))

    def serialize(obj) -> List[str]:
        if isinstance(obj, str):
            return [json_encode_string(obj)]
        elif isinstance(obj, dict):
            if obj:
                r = ['{']
                for k, v in obj.items():
                    r.append('"' + k + '":')
                    r.extend(serialize(v))
                    r.append(',')
                r[-1] = '}'
                return r
            return ['{}']
        elif isinstance(obj, (list, tuple)):
            if obj:
                r = ['[']
                for item in obj:
                    r.extend(serialize(item))
                    r.append(',')
                r[-1] = ']'
                return r
            return ['[]']
        elif obj is True:
            return ['true']
        elif obj is False:
            return ['false']
        elif obj is None:
            return ['null']
        elif isinstance(obj, (int, float)):
            # NOTE: test for int must follow test for bool, because True and False
            #       are treated as instances of int as well by Python
            return[repr(obj)]
        elif isinstance(obj, JSONstr):
            return [obj.serialized_json]
        elif obj is JSONnull or isinstance(obj, JSONnull):
            return ['null']
        return serialize(custom_encoder.default(obj))

    if partially_serialized:
        custom_encoder = cls()
        return ''.join(serialize(obj))
    else:
        class MyEncoder(json.JSONEncoder):
            def default(self, obj):
                if obj is JSONnull or isinstance(obj, JSONnull):
                    return None
                return cls.default(self, obj)
        return json.dumps(obj, cls=MyEncoder, indent=None, separators=(',', ':'))


def json_rpc(method: str,
             params: JSON_Type = [],
             ID: Optional[int] = None,
             partially_serialized: bool = True) -> str:
    """Generates a JSON-RPC-call string for `method` with parameters `params`.
    
    :param method: The name of the rpc-function that shall be called
    :param params: A json-object representing the parameters of the call
    :param ID: An ID for the json-rpc-call or `None` 
    :param partially_serialized: If True, the `params`-object may contain
        already serialized parts in form of `JSONStr`-objects.
        If False, any `JSONStr`-objects will lead to a TypeError.
    :return: The string-serialized form of the json-object.
    """
    rpc = {"jsonrpc": "2.0", "method": method, "params": params}
    if ID is not None:
        rpc['id'] = ID
    return json_dumps(rpc, partially_serialized=partially_serialized)


#######################################################################
#
#  concurrent execution (wrappers for concurrent.futures)
#
#######################################################################

class SingleThreadExecutor(concurrent.futures.Executor):
    """SingleThreadExecutor is a replacement for
    concurrent.future.ProcessPoolExecutor and
    concurrent.future.ThreadPoolExecutor that executes any submitted
    task immediately in the submitting thread. This helps to avoid
    writing extra code for the case that multithreading or
    multiprocesssing has been turned off in the configuration. To do
    so is helpful for debugging.

    It is not recommended to use this in asynchronous code or code that
    relies on the submit() or map()-method of executors to return quickly.
    """
    def submit(self, fn, *args, **kwargs):
        future = concurrent.futures.Future()
        try:
            result = fn(*args, **kwargs)
            future.set_result(result)
        except BaseException as e:
            future.set_exception(e)
        return future


def instantiate_executor(allow_parallel: bool,
                         preferred_executor: Type[concurrent.futures.Executor],
                         *args, **kwargs) -> concurrent.futures.Executor:
    """Instantiates an Executor of a particular type, if the value of the
    configuration variable 'debug_parallel_execution' allows to do so.
    Otherwise a surrogate executor will be returned.
    If 'allow_parallel` is False, a SingleThreadExecutor will be instantiated,
    regardless of the preferred_executor and any configuration values.
    """
    if allow_parallel:
        mode = get_config_value('debug_parallel_execution')  # type: str
        if mode == "commandline":
            options = [arg for arg in sys.argv if arg[:2] == '--']  # type: List[str]
            if '--singlethread' in options:  mode = 'singlethread'
            elif '--multithreading' in options:  mode = 'multithreading'
            else:  mode = 'multiprocessing'
        if mode == "singlethread":
            return SingleThreadExecutor()
        elif mode == "multithreading":
            if issubclass(preferred_executor, concurrent.futures.ProcessPoolExecutor):
                return concurrent.futures.ThreadPoolExecutor(*args, **kwargs)
        else:
            assert mode == "multiprocessing", \
                'Config variable "debug_parallel_execution" as illegal value "%s"' % mode
        return preferred_executor(*args, **kwargs)
    return SingleThreadExecutor()


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
