# toolkit.py - utility functions for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
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

# import concurrent.futures  # commented out to save startup time
import functools
import io
import json
import os
import queue
import sys


try:
    if sys.version.find('PyPy') >= 0:
        import re  # regex might not work with PyPy reliably: https://pypi.org/project/regex/
    else:
        import regex as re
except ImportError:
    import re

if sys.version_info >= (3, 12, 0):
    from collections.abc import Iterable, Sequence, Set, MutableSet, Callable, Container, Hashable
    from typing import Any, Type, Union, Optional, TypeAlias, TypeVar, Protocol
    AbstractSet = Set
    FrozenSet = frozenset
    Dict = dict
    List = list
    Tuple = tuple
    ByteString: TypeAlias = Union[bytes, bytearray]
    static = staticmethod
else:
    from typing import Any, Iterable, Sequence, Set, AbstractSet, Union, Dict, List, Tuple, \
        FrozenSet, MutableSet, Optional, Type, Callable, Container, Hashable, ByteString
    try:
        from typing import Protocol
    except ImportError:
        class Protocol:
            pass
    try:
        from typing import TypeAlias
    except ImportError:
        from DHParser.externallibs.typing_extensions import TypeAlias
    if sys.version_info >= (3, 10, 0):
        static = staticmethod
    else:
        static = lambda f: f

try:
    import cython
    cython_optimized = cython.compiled  # type: bool
    if cython_optimized:  # not ?
        import DHParser.externallibs.shadow_cython as cython
except (NameError, ImportError):
    cython_optimized = False
    import DHParser.externallibs.shadow_cython as cython

from DHParser.configuration import access_thread_locals, get_config_value, set_config_value, \
    CONFIG_PRESET, NEVER_MATCH_PATTERN
from DHParser.stringview import StringView


__all__ = ('re',
           'cython_optimized',
           'DHPARSER_FILES',
           'identify_python',
           'identity',
           'CancelQuery',
           'get_annotations',
           # 'gen_id',
           'ThreadLocalSingletonFactory',
           'LazyRE',
           'RX_NEVER_MATCH',
           'RX_ENTITY',
           'RX_NON_ASCII',
           'validate_XML_attribute_value',
           'fix_XML_attribute_value',
           'lxml_XML_attribute_value',
           'RxPatternType',
           'escape_re',
           'escape_ctrl_chars',
           'is_filename',
           'is_html_name',
           'relative_path',
           'split_path',
           'concurrent_ident',
           'unrepr',
           'abbreviate_middle',
           'wrap_str_literal',
           'wrap_str_nicely',
           'printw',
           'escape_formatstr',
           'as_identifier',
           'as_list',
           'as_tuple',
           'first',
           'last',
           'NOPE',
           'INFINITE',
           'matching_brackets',
           'linebreaks',
           'line_col',
           'text_pos',
           'normalize_docstring',
           'issubtype',
           'isgenerictype',
           'DeserializeFunc',
           'cached_load',
           'clear_from_cache',
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
           'pp_json',
           'pp_json_str',
           'sane_parser_name',
           'normalize_circular_path',
           'normalize_circular_paths',
           'DHPARSER_DIR',
           'deprecated',
           'deprecation_warning',
           'SingleThreadExecutor',
           'multiprocessing_broken',
           'MultiCoreManager',
           'PickMultiCoreExecutor',
           'instantiate_executor',
           'cpu_count',
           # Type Aliases
           'Iterable',
           'Sequence',
           'Set',
           'AbstractSet',
           'MutableSet',
           'FrozenSet',
           'Callable',
           'Container',
           'ByteString',
           'Any',
           'Type',
           'Union',
           'Optional',
           'TypeAlias',
           'Protocol',
           'Dict',
           'List',
           'Tuple',
           'static')


#######################################################################
#
# miscellaneous (generic)
#
#######################################################################

DHPARSER_FILES = {'dsl.py', 'log.py', 'parse.py', 'server.py', 'testing.py', 'transform.py',
                  'compile.py', 'ebnf.py', 'lsp.py', 'pipeline.py', 'singledispatch_shim.py',
                  'toolkit.py', 'validate.py', 'configuration.py', 'error.py', 'nodetree.py',
                  'preprocess.py', 'stringview.py', 'trace.py', 'versionnumber.py'}


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


CancelQuery: TypeAlias = Callable[[], bool]  # A type for a cancellation-callback


global_id_counter: int = 0


def gen_id() -> int:
    """Generates a unique id. (Not thread-safe!)"""
    global global_id_counter
    global_id_counter += 1
    return global_id_counter


class ThreadLocalSingletonFactory:
    """
    Generates a singleton-factory that returns one and
    the same instance of `class_or_factory` for one and the
    same thread, but different instances for different threads.

    Note: Parameter uniqueID should be provided if class_or_factory is
    not unique but generic. See source code of
    :py:func:`DHParser.dsl.create_transtable_junction`
    """
    def __init__(self, class_or_factory, name: str = "", *,
                 uniqueID: Union[str, int] = 0,
                 ident=None):
        if ident is not None:
            deprecation_warning('Parameter "ident" of DHParser.toolkit.ThreadLocalSingletonFactory'
                                ' is deprecated and will be ignored.')
        self.class_or_factory = class_or_factory
        # partial functions do not have a __name__ attribute!
        name = name or getattr(class_or_factory, '__name__', '') or class_or_factory.func.__name__
        if not uniqueID:
            if not hasattr(self.__class__, 'lock'):
                import threading
                self.__class__.lock = threading.Lock()
            with self.__class__.lock:
                uniqueID = gen_id()
        self.singleton_name = f"{name}_{str(id(self))}_{str(uniqueID)}_singleton"
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
    r"""
    Tries to guess whether the given string is a file name. It is
    assumed that it is NOT a filename if any of the following
    conditions is true:

    - it starts with a byte-order mark, i.e. '\ufffe' or '\ufeff'
    - it starts or ends with a blank, i.e. " "
    - it contains any of the characters in the set [\*?"<>|]

    For disambiguation of non-filenames it is best to add a
    byteorder-mark to the beginning of the string, because this
    will be stripped by the DHParser's parser, anyway!
    """
    return strg and strg[0:1] not in ('\ufeff', '\ufffe') \
        and strg[0:3] not in ('\xef\xbb\xbf', '\x00\x00\ufeff', '\x00\x00\ufffe') \
        and strg.find('\n') < 0 \
        and strg[:1] != " " and strg[-1:] != " " \
        and all(strg.find(ch) < 0 for ch in '*?"<>|')


def is_html_name(url: str) -> bool:
    """Returns True, if url ends with .htm or .html"""
    return url[-5:].lower() == '.html' or url[-4:].lower() == '.htm'


@cython.locals(i=cython.int, L=cython.int)
def relative_path(from_path: str, to_path: str) -> str:
    """Returns the relative path in order to open a file from
    `to_path` when the script is running in `from_path`. Example::

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
    import multiprocessing, threading
    if sys.version_info >= (3, 8, 0):
        return multiprocessing.current_process().name + '_' + str(threading.get_native_id())
    else:
        return multiprocessing.current_process().name + '_' + str(threading.get_ident())


class unrepr:
    """
    unrepr encapsulates a string representing a python function in such
    a way that the representation of the string yields the function call
    itself rather than a string representing the function call and delimited
    by quotation marks. Example::

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
    if isinstance(item_or_sequence, Iterable) \
            and not isinstance(item_or_sequence, (str, bytes, bytearray)):
        return list(item_or_sequence)
    return [item_or_sequence]


def as_tuple(item_or_sequence) -> Tuple[Any]:
    """Turns an arbitrary sequence or a single item into a tuple. In case of
    a single item, the tuple contains this element as its sole item."""
    if isinstance(item_or_sequence, Iterable) \
            and not isinstance(item_or_sequence, (str, bytes, bytearray)):
        return tuple(item_or_sequence)
    return (item_or_sequence,)


def as_set(item_or_sequence: Hashable) -> MutableSet[Any]:
    """Turns an arbitrary sequence or a single item into a set. In case of
    a single item, the set contains this element as its sole item."""
    if isinstance(item_or_sequence, Iterable) \
            and not isinstance(item_or_sequence, (str, bytes, bytearray)):
        return set(item_or_sequence)
    return {item_or_sequence}


def as_frozenset(item_or_sequence: Hashable) -> FrozenSet[Any]:
    """Turns an arbitrary sequence or a single item into a set. In case of
    a single item, the set contains this element as its sole item."""
    if isinstance(item_or_sequence, Iterable) \
            and not isinstance(item_or_sequence, (str, bytes, bytearray)):
        return frozenset(item_or_sequence)
    return frozenset({item_or_sequence})


def first(item_or_sequence: Union[Sequence, Any]) -> Any:
    """Returns an item or the first item of a sequence of items."""
    if isinstance(item_or_sequence, Sequence) \
            and not isinstance(item_or_sequence, (str, bytes, bytearray)):
        return item_or_sequence[0]
    else:
        return item_or_sequence


def last(item_or_sequence: Union[Sequence, Any]) -> Any:
    """Returns an item or the first item of a sequence of items."""
    if isinstance(item_or_sequence, Sequence) \
            and not isinstance(item_or_sequence, (str, bytes, bytearray)):
        return item_or_sequence[-1]
    else:
        return item_or_sequence


DEPRECATION_WARNINGS_ISSUED: MutableSet[str] = set()


def deprecation_warning(message: str):
    """Issues a deprecation warning. Makes sure that each message is only
    called once."""
    if message not in DEPRECATION_WARNINGS_ISSUED:
        DEPRECATION_WARNINGS_ISSUED.add(message)
        try:
            raise DeprecationWarning(message)
        except DeprecationWarning as e:
            try:
                deprecation_policy = get_config_value('deprecation_policy')
            except AssertionError as e:
                deprecation_policy = 'warn'
                print(e)
            if deprecation_policy == 'warn':
                import traceback
                stacktrace = traceback.format_exc()
                print(stacktrace)
            else:
                raise e


def deprecated(message: str) -> Callable:
    """Decorator that marks a function as deprecated and emits
    a deprecation message on its first use::

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
            deprecation_warning(message or str(f))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def get_annotations(item):
    if sys.version_info >= (3, 14):
        from annotationlib import get_annotations, Format
        return get_annotations(item, format=Format.STRING)
    else:
        return item.__annotations__


#######################################################################
#
# miscellaneous (DHParser-specific)
#
#######################################################################


DHPARSER_DIR = os.path.dirname(os.path.abspath(os.path.realpath(__file__)))
# DHPARSER_PARENTDIR = os.path.dirname(DHPARSER_DIR.rstrip('/').rstrip('\\'))


def sane_parser_name(name) -> bool:
    """
    Checks whether given name is an acceptable parser name. Parser names
    must not be preceded or succeeded by a double underscore '__'!
    """

    return name and name[:2] != '__' and name[-2:] != '__'


def normalize_circular_path(path: Tuple[str, ...]) -> Tuple[str, ...]:
    """Returns a normalized version of a `circular path` represented as
    a tuple.

    A circular (or "recursive") path is a tuple of items, the order of which
    matters, but not the starting point. This can, for example, be a tuple of
    references from one symbol defined in an EBNF source text back to
    (but excluding) itself.

    For example, when defining a grammar for arithmetic, the tuple
    ('expression', 'term', 'factor') if a recursive path, because the
    definition of a factor includes a (bracketed) expression and thus
    refers back to `expression`
    Normalizing is done by "ring-shifting" the tuple so that it starts
    with the alphabetically first symbol in the path::

        >>> normalize_circular_path(('term', 'factor', 'expression'))
        ('expression', 'term', 'factor')
    """
    assert isinstance(path, Tuple)
    first_sym = min(path)
    i = path.index(first_sym)
    return path[i:] + path[:i]


def normalize_circular_paths(path: Union[Tuple[str, ...], AbstractSet[Tuple[str, ...]]]) \
        -> Union[Tuple[str, ...], MutableSet[Tuple[str, ...]], MutableSet]:
    """Like :py:func:`normalize_circular_path`, but normalizes a whole set of
    paths at once.
    """
    if isinstance(path, AbstractSet):
        return {normalize_circular_path(p) for p in path}
    else:
        return normalize_circular_path(path)


#######################################################################
#
#  string manipulation and regular expressions
#
#######################################################################


class LazyRE:
    """
    A lazily-evaluating regular expression. This allows to define as many
    regular expressions on the top-level as you like without wasting
    startup-time.

    >>> rx = LazyRE(r'\\w+')
    >>> rx.match('abc').group(0)
    'abc'
    >>> rx.match('!?')
    """

    def __init__(self, regexp: str, flags = 0):
        self.regexp = regexp
        self.re_flags = flags
        self.rx = None

    def compile_me(self):
        if self.rx is None:
            self.rx = re.compile(self.regexp, self.re_flags)
            self.search = self.rx.search
            self.match = self.rx.match
            self.fullmatch = self.rx.fullmatch
            self.split = self.rx.split
            self.findall = self.rx.findall
            self.finditer = self.rx.finditer
            self.sub = self.rx.sub
            self.subn = self.rx.subn

    @property
    def Pattern(self):
        if self.rx is None:
            self.rx = re.compile(self.regexp)
        return self.rx

    @property
    def pattern(self):
        if self.rx is None:
            self.rx = re.compile(self.regexp)
        return self.rx.pattern

    @property
    def flags(self):
        if self.rx is None:
            self.rx = re.compile(self.regexp)
        return self.rx.flags

    @property
    def groups(self):
        if self.rx is None:
            self.rx = re.compile(self.regexp)
        return self.rx.groups

    @property
    def groupindex(self):
        if self.rx is None:
            self.rx = re.compile(self.regexp)
        return self.rx.groupindex

    def search(self, *args, **kwargs):
        self.compile_me()
        return self.rx.search(*args, **kwargs)

    def match(self, *args, **kwargs):
        self.compile_me()
        return self.rx.match(*args, **kwargs)

    def fullmatch(self, *args, **kwargs):
        self.compile_me()
        return self.rx.fullmatch(*args, **kwargs)

    def split(self, *args, **kwargs):
        self.compile_me()
        return self.rx.split(*args, **kwargs)

    def findall(self, *args, **kwargs):
        self.compile_me()
        return self.rx.findall(*args, **kwargs)

    def finditer(self, *args, **kwargs):
        self.compile_me()
        return self.rx.finditer(*args, **kwargs)

    def sub(self, *args, **kwargs):
        self.compile_me()
        return self.rx.sub(*args, **kwargs)

    def subn(self, *args, **kwargs):
        self.compile_me()
        return self.rx.subn(*args, **kwargs)


RX_NEVER_MATCH = LazyRE(NEVER_MATCH_PATTERN)
try:
    RxPatternType: TypeAlias = re.Pattern
except AttributeError:
    RxPatternType: TypeAlias = Any



@deprecated('find_re() is deprecated. Use re.search() from the Python-Standard-Library, instead!')
def re_find(s, r, pos=0, endpos=9223372036854775807):
    """DEPRECATED! Use re.search() from the Python-Standard-Library!"""
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


@deprecated('escape_re() is deprecated. Use re.escape() from the Python-Standard-Library instead!')
def escape_re(strg: str) -> str:
    """
    Returns the string with all regular expression special characters escaped.
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
    while lines and not lines[-1].strip():  lines.pop()
    if lines:
        if lines[0].strip():
            lines = [lines[0]] + [line[indent:] for line in lines[1:]]
        else:
            lines = [line[indent:] for line in lines[1:]]
        # remove any empty lines at the beginning
        while lines and not lines[0].strip():  del lines[0]
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


def wrap_str_literal(s: Union[str, List[str]], column: int = 80, offset: int = 0) -> str:
    r"""Wraps an excessively long string literal over several lines.
    Example::

        >>> s = '"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"'
        >>> print(wrap_str_literal(s, 25))
        "abcdefghijklmnopqrstuvwx"
        "yzABCDEFGHIJKLMNOPQRSTUVW"
        "XYZ0123456789"
        >>> s = 'r"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"'
        >>> print("Call(" + wrap_str_literal(s, 40, 5) + ")")
        Call(r"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLM"
             r"NOPQRSTUVWXYZ0123456789")
        >>> s = 'fr"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"'
        >>> print("Call(" + wrap_str_literal(s, 40, 5) + ")")
        Call(fr"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLM"
             fr"NOPQRSTUVWXYZ0123456789")
        >>> s = ['r"abcde', 'ABCDE"']
        >>> print(wrap_str_literal(s))
        r"abcde"
        r"ABCDE"
    """
    if isinstance(s, list):
        assert len(s) > 0
        parts = s
        s = '\n'.join(s)
    else:
        parts = None
    if s[0:1].isalpha():
        i = 2 if s[1:2].isalpha() else 1
        r = s[0:i]
        s = s[i:]
        if parts is not None:
            parts[0] = parts[0][i:]
    else:
        r = ''
    q = s[0:1]
    assert len(s) >= 2 and q == s[-1] and q in ('"', "'", "`", "´"), \
        "string literal must be enclosed by quotation marks"
    if parts is None:
        parts = [s[i: i + column] for i in range(0, len(s), column)]
        for i in range(len(parts) - 1):
            p = parts[i]
            k = 1
            while k <= len(p) and p[-k] == '\\':
                k += 1
            k -= 1
            if k > 0:
                parts[i] = p[:-k]
                parts[i + 1] = p[-k:] + parts[i + 1]
    if r:  parts[0] = r + parts[0]
    wrapped = (''.join([q, '\n', ' ' * offset, r, q])).join(parts)
    return wrapped


@cython.locals(wrap_column=cython.int, tolerance=cython.int, a=cython.int, i=cython.int, k=cython.int, m=cython.int)
def wrap_str_nicely(s: str, wrap_column: int = 79, tolerance: int = 24,
                    wrap_chars: str = ")]>, ") -> str:
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


def printw(s: Any, wrap_column: int = 79, tolerance: int = 24,
           wrap_chars: str = ")]>, "):
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
    s = re.sub(r'(?<!})}(?!})', '}}', s)
    return s


RX_IDENTIFIER = LazyRE(r'\w+')
RX_NON_IDENTIFIER = LazyRE(r'\W+')


@cython.locals(i=cython.int, delta=cython.int)
def as_identifier(s: str, replacement: str = "_") -> str:
    r"""Converts a string to an identifier that matches /\w+/ by
    substituting any character not matching /\w/ with the given
    replacement string::

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
INFINITE = 2**30  # a practically infinite value

_RX_CHARSET = LazyRE(r'(?<=\[)(?:(?<!\\)(?:\\\\)*\\\]|[^\]])*(?=\])')
_RX_ESCAPED_ROUND_BRACKET = LazyRE(r'(?<!\\)(?:\\\\)*\\[()]')
_RX_ESCAPED_SQUARE_BRACKET = LazyRE(r'(?<!\\)(?:\\\\)*\\[\[\]]')


def _sub_size(rx: Union[RxPatternType, LazyRE], text: str, fill_char: str = ' ') -> str:
    """Substitutes matches of a regular expression with a fill-string
    of the same size. Example::

        >>> _RX_CHARSET = re.compile(r'(?<=\\[)(?:(?:\\\\)*\\\\]|[^\\]])*(?=\\])')
        >>> _sub_size(_RX_CHARSET, r'([^\\d()]*(?=[\\d\\](]))')
        '([     ]*(?=[     ]))'
    """
    assert len(fill_char) == 1
    a = 0
    chunks = []
    for m in rx.finditer(text):
        start = m.start()
        end = m.end()
        if a < start:
            chunks.append(text[a:start])
        chunks.append(fill_char * (end - start))
        a = end
    if a < len(text): chunks.append(text[a:])
    return ''.join(chunks)


@cython.locals(da=cython.int, db=cython.int, a=cython.int, b=cython.int)
def matching_brackets(text: str,
                      openB: str,
                      closeB: str,
                      unmatched: list = NOPE,
                      is_regex: bool=False) -> List[Tuple[int, int]]:
    """Returns a list of matching bracket positions. Fills an empty list
    passed to parameter `unmatched` with the positions of all
    unmatched brackets. If rx is True, escaped brackets and brackets inside
    charsets will be ignored. In other words, only brackets that are
    control-characters of the regular expression will be considered.
    Examples::

        >>> matching_brackets('(a(b)c)', '(', ')')
        [(2, 4), (0, 6)]
        >>> matching_brackets('(a)b(c)', '(', ')')
        [(0, 2), (4, 6)]
        >>> unmatched = []
        >>> matching_brackets('ab(c', '(', ')', unmatched)
        []
        >>> unmatched
        [2]
        >>> matching_brackets(r'([^\\d()]*(?=[\\d(]))', '(', ')', is_regex=True)
        [(9, 17), (0, 18)]
    """
    assert not unmatched, \
        "Please pass an empty list as unmatched flag, not: " + str(unmatched)
    if is_regex:
        text = _sub_size(_RX_CHARSET, text)
        text = _sub_size(_RX_ESCAPED_ROUND_BRACKET, text)
        text = _sub_size(_RX_ESCAPED_SQUARE_BRACKET, text)
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
RX_ENTITY = LazyRE(r'&(?:_|:|[A-Z]|[a-z]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]'
                   r'|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]|[\u2070-\u218F]'
                   r'|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]'
                   r'|[\U00010000-\U000EFFFF])(?:_|:|-|\.|[A-Z]|[a-z]|[0-9]|\u00B7'
                   r'|[\u0300-\u036F]|[\u203F-\u2040]|[\u00C0-\u00D6]|[\u00D8-\u00F6]'
                   r'|[\u00F8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]'
                   r'|[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]'
                   r'|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF])*;')


def validate_XML_attribute_value(value: Any) -> str:
    """Validates an XML-attribute value and returns the quoted string-value
    if successful. Otherwise, raises a ValueError.
    """
    value = str(value)
    contains_doublequote = value.find('"') >= 0
    if contains_doublequote and value.find("'") >= 0:
        raise ValueError(('Illegal XML-attribute value: %s  (Cannot be quoted, because '
                          'both single and double quotation mark are contained in the '
                          'value. Use entities to avoid this conflict.)') % value)
    if value.find('<') >= 0:
        raise ValueError(f'XML-attribute value "{value}" must not contain "<"! Change '
                         f'config-variable "xml_attribute_error_handling" to "fix" to '
                         f'avoid this error.')
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


RX_NON_ASCII = LazyRE(r'[^\U00000000-\U000000FF]')


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
    """Returns `True` if sub_type is a subtype of `base_type`.
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


RX_FILEPATH = LazyRE(r'[^ \t][^\n\t?*=]+(?<![ \t])')  # r'[\w/:. \\]+'


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
                    '(If "%s" was NOT meant to be a file name then, add a byte-order mark '
                    r'to the beginning of the string "\ufeff" for disambiguation, e.g. '
                    r'source_snippet = "\ufeff" + source_snippet)'
                    % (text_or_file, text_or_file))
            else:
                return text_or_file
    else:
        return text_or_file


DeserializeFunc: TypeAlias = Union[Callable[[str], Any], functools.partial]


def cached_load(file_name: str, deserialize: DeserializeFunc, cachedir: str = "~/.cache") -> Any:
    """
    Loads and deserializes as file into a python-object. The Python-object will
    be pickled and written to "cachedir". If a pickled version already exists,
    the same file will not be deserialized again, but the pickled version will be loaded.
    If cachedir == "", the pickled version will always be preferred, even if the
    original file has been updated. In this case, in order to invalidate the cache,
    the pickled version must be deleted manually.
    Otherwise, and this includes the case cachedir == ".", a hash value is used
    to check whether the original file has been updated, in which case, the
    source-file will be loaded and deserialized anew.

    :param file_name: The name of the file to load.
    :param deserialize: The function to deserialize the content of the file.
    :param cachedir: The directory to cache the pickled version in.
    :returns: The deserialized python object.
    """
    import pickle, typing
    if os.path.sep == "/": cachedir = cachedir.replace('\\', os.path.sep)
    else: cachedir = cachedir.replace('/', os.path.sep)
    if cachedir:
        cachedir = os.path.realpath(os.path.expanduser(cachedir))
        appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        cachedir = os.path.join(cachedir, appname)
        os.makedirs(cachedir, exist_ok=True)
    name = os.path.splitext(os.path.basename(file_name))[0]
    cache_name = os.path.join(cachedir, name + '.pickled')
    source: Optional[str] = None
    if os.path.isfile(cache_name):
        try:
            with open(cache_name, 'rb') as f:
                hash_data, data = pickle.load(f)
            if cachedir:
                with open(file_name, 'r', encoding='utf-8') as f:
                    source = f.read()
                if hash_data == hash(source):
                    return data
            else:
                return data
        except pickle.UnpicklingError as e:
            print(f'{e} encountered while loading data from cache "{cache_name}"!'
                  f'If this error persists, then delete the cache file "{cache_name}" manually.')
    if source is None:
        with open(file_name, 'r', encoding='utf-8') as f:
            source = f.read()
    data = deserialize(typing.cast(str, source))
    with open(cache_name, 'wb') as f:
        pickle.dump((hash(source), data), f)
    return data


def clear_from_cache(file_name: str, cachedir: str = "~/.cache"):
    """Removes the cached version of `file_name` from the cache.
    (See :py:func:`cached_load`)
    """
    if os.path.sep == "/": cachedir = cachedir.replace('\\', os.path.sep)
    else: cachedir = cachedir.replace('/', os.path.sep)
    appname = ""
    if cachedir:
        cachedir = os.path.realpath(os.path.expanduser(cachedir))
        appname = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        cachedir = os.path.join(cachedir, appname)
    name = os.path.splitext(os.path.basename(file_name))[0]
    cache_name = os.path.join(cachedir, name + '.pickled')
    os.remove(cache_name)
    if appname and not os.listdir(cachedir):
        os.rmdir(cachedir)


def is_python_code(text_or_file: str) -> bool:
    """
    Checks whether 'text_or_file' is python code or the name of a file that
    contains python code.
    """
    if is_filename(text_or_file):
        return text_or_file[-3:].lower() == '.py'
    try:
        import ast
        ast.parse(text_or_file)
        return True
    except (SyntaxError, ValueError, OverflowError) as e:
        pass
    return False


def has_fenced_code(text_or_file: str, info_strings=('ebnf', 'test')) -> bool:
    """
    Checks whether `text_or_file` contains fenced code blocks, which are
    marked by one of the given info strings.
    See https://spec.commonmark.org/0.28/#fenced-code-blocks for more
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
        matched_string = re.match(r'\n`+|\n~+', match.group(0)).group(0)
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
    import hashlib
    md5_hash = hashlib.md5()
    for t in txt:
        md5_hash.update(t.encode('utf8'))
    return md5_hash.hexdigest()


def compile_python_object(python_src: str, catch_obj="DSLGrammar") -> Any:
    """
    Compiles the python source code and returns the (first) object
    the name of which is either equal to or matched by ``catch_obj_regex``.
    If catch_obj is the empty string, the namespace dictionary will be returned.
    """
    code = compile(python_src, '<string>', 'exec')
    namespace = {}  # type: Dict[str, Any]
    exec(code, namespace)  # safety risk?
    if catch_obj:
        if isinstance(catch_obj, str):
            try:
                obj = namespace[catch_obj]
                return obj
            except KeyError:
                catch_obj = re.compile(catch_obj)
        matches = [key for key in namespace if catch_obj.fullmatch(key)]
        if len(matches) < 1:
            raise ValueError("No object matching /%s/ defined in source code." %
                             catch_obj.pattern)
        elif len(matches) > 1:
            raise ValueError("Ambiguous matches for %s : %s" %
                             (str(catch_obj), str(matches)))
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
    Returns a list of the indices of all line breaks in the text.
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
def line_col(lbreaks: List[int], pos: cython.int) -> Tuple[cython.int, cython.int]:
    """
    Returns the position within a text as (line, column)-tuple based
    on a list of all line breaks, including -1 and EOF.
    """
    if not lbreaks and pos >= 0:
        return 0, pos
    if pos < 0 or pos > lbreaks[-1]:  # one character behind EOF is still an allowed position!
        raise ValueError('Position %i outside text of length %s !' % (pos, lbreaks[-1]))
    import bisect
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
    in this order, e.g.::

        >>> smart_list('1; 2, 3; 4')
        ['1', '2, 3', '4']
        >>> smart_list('2, 3')
        ['2', '3']
        >>> smart_list('a b cd')
        ['a', 'b', 'cd']

    If the argument is a collection other than a string, it will be
    returned as is, e.g.::

        >>> smart_list((1, 2, 3))
        (1, 2, 3)
        >>> smart_list({1, 2, 3})
        {1, 2, 3}

    If the argument is another iterable than a collection, it will
    be converted into a list, e.g.::

        >>> smart_list(i for i in {1,2,3})
        [1, 2, 3]

    Finally, if none of the above is true, the argument will be
    wrapped in a list and returned, e.g.::

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
ESCAPE = LazyRE(r'[\x00-\x1f\\"\b\f\n\r\t]')
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


def json_dumps(obj: JSON_Type, *, cls=json.JSONEncoder, partially_serialized: bool = False) -> str:
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
            def default(self, o):
                if o is JSONnull or isinstance(o, JSONnull):
                    return None
                return cls.default(self, o)
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


def pp_json(obj: JSON_Type, *, cls=json.JSONEncoder) -> str:
    """Returns json-object as pretty-printed string. Other than the standard-library's
    `json.dumps()`-function `pp_json` allows to include already serialized
    parts (in the form of JSONStr-objects) in the json-object. Example::

        >>> already_serialized = '{"width":640,"height":400"}'
        >>> literal = JSONstr(already_serialized)
        >>> json_obj = {"jsonrpc": "2.0", "method": "report_size", "params": literal, "id": None}
        >>> print(pp_json(json_obj))
        {
          "jsonrpc": "2.0",
          "method": "report_size",
          "params": {"width":640,"height":400"},
          "id": null}

    :param obj: A json-object (or a tree of json-objects) to be serialized
    :param cls: The class of a custom json-encoder derived from `json.JSONEncoder`
    :return: The pretty-printed string-serialized form of the json-object.
    """
    custom_encoder = cls()

    def serialize(obj, indent: str) -> List[str]:
        if isinstance(obj, str):
            if obj.find('\n') >= 0:
                lines = obj.split('\n')
                pretty_str = json_encode_string(lines[0]) + '\n' \
                    + '\n'.join(indent + json_encode_string(line) for line in lines[1:])
                return [pretty_str]
            else:
                return [json_encode_string(obj)]
        elif isinstance(obj, dict):
            if obj:
                if len(obj) == 1:
                    k, v = next(iter(obj.items()))
                    if not isinstance(v, (dict, list, tuple)):
                        r = ['{"' + k + '": ']
                        r.extend(serialize(v, indent + '  '))
                        r.append('}')
                        return r
                r = ['{\n' + indent + '  ']
                for k, v in obj.items():
                    r.append('"' + k + '": ')
                    r.extend(serialize(v, indent + '  '))
                    r.append(',\n' + indent + '  ')
                r[-1] = '}'
                return r
            return ['{}']
        elif isinstance(obj, (list, tuple)):
            if obj:
                r = ['[']
                for item in obj:
                    r.extend(serialize(item, indent + '  '))
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
            return [repr(obj)]
        elif isinstance(obj, JSONstr):
            return [obj.serialized_json]
        elif isinstance(obj, JSONnull) or obj is JSONnull:
            return ['null']
        return serialize(custom_encoder.default(obj), indent)

    return ''.join(serialize(obj, ''))


def pp_json_str(jsons: str) -> str:
    """Pretty-prints and already serialized (but possibly ugly-printed)
    json object in a well-readable form. Syntactic sugar for:
    `pp_json(json.loads(jsons))`."""
    return pp_json(json.loads(jsons))


#######################################################################
#
#  concurrent execution (wrappers for concurrent.futures)
#
#######################################################################

class SingleThreadExecutor:
    r"""SingleThreadExecutor is a replacement for
    concurrent.future.ProcessPoolExecutor and
    concurrent.future.ThreadPoolExecutor that executes any submitted
    task immediately in the submitting thread. This helps to avoid
    writing extra code for the case that multithreading or
    multiprocesssing has been turned off in the configuration. To do
    so is helpful for debugging.

    It is not recommended to use this in asynchronous code or code that
    relies on the submit()- or map()-method of executors to return quickly.
    """

    def submit(self, fn, *args, **kwargs):  # -> concurrent.futures.Future:
        """Run function "fn" with the given args and kwargs synchronously
        without multithreading or multiprocessing."""
        import concurrent.futures
        future = concurrent.futures.Future()
        try:
            result = fn(*args, **kwargs)
            future.set_result(result)
        except BaseException as e:
            future.set_exception(e)
        return future

    # context-manager
    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        return None


@functools.lru_cache(None)
def multiprocessing_broken() -> str:
    """Returns an error message, if, for any reason multiprocessing is not safe
    to be used. For example, multiprocessing does not work with
    PyInstaller (under Windows) or GraalVM.
    """
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        err_msg = "Multiprocessing turned off for PyInstaller-bundled script."
        print(err_msg)
        return err_msg
    return ""


class InterpreterEventShim:
    def __init__(self):
        from concurrent.interpreters import create_queue
        self.queue = create_queue()

    def is_set(self):
        return self.queue.qsize() > 0

    def set(self):
        if self.queue.qsize() == 0:
            self.queue.put_nowait(1)

    def clear(self):
        while self.queue.qsize() > 0:
            _ = self.queue.get_nowait()
            self.queue.task_done()

    def wait(self, timeout=None):
        if self.is_set():
            return True
        import queue
        try:
            _ = self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return False
        self.queue.task_done()
        if not self.is_set():
            self.set()
        return True


class ManagerShim:
    def __enter__(self):
        return self

    def __exit__(self, *exc_details):
        pass

    def start(self):
        pass

    def shutdown(self):
        pass


class ThreadingManagerShim(ManagerShim):
    def Event(self):
        import threading
        return threading.Event()

    def Queue(self):
        import queue
        return queue.Queue()


class InterpreterManagerShim(ManagerShim):
    def Event(self):
        return InterpreterEventShim()

    def Queue(self):
        from concurrent.interpreters import create_queue
        return create_queue()


def eval_debug_parallel_execution() -> str:
    mode = get_config_value('debug_parallel_execution')  # type: str
    if mode == "commandline":
        options = [arg for arg in sys.argv if arg[:2] == '--']
        if '--singlethread' in options:
            return "singlethread"
        elif '--multithreading' in options:
            return "multithreading"
        else:
            return "multicore"
    elif mode == "singlethread":
        return "singlethread"
    elif mode == "multithreading" or (mode in ('multicore', 'multiprocessing')
                                      and multiprocessing_broken()):
        return "multithreading"
    else:
        assert mode in ('multicore', 'multiprocessing')
        if mode == "multiprocessing":
            print('Value "multiprocessing" for config-variable "debug_parallel_execution"'
                  ' is deprecated. Please, use "multicore", instead!')
        return "multicore"


def MultiCoreManager():
    mode = eval_debug_parallel_execution()
    if mode == 'multicore':
        if sys.version_info >= (3, 14, 0) \
                and CONFIG_PRESET['multicore_pool'] == 'InterpreterPool':
            return InterpreterManagerShim()
        else:
            import multiprocessing
            return multiprocessing.Manager()
    else:
        return ThreadingManagerShim()



# def unpickle_result(result):
#     import pickle
#     try:
#         return pickle.loads(result)
#     except (TypeError, pickle.UnpicklingError):
#         return result
#
#
# class FutureWrapper:
#     def __init__(self, future):
#         self.future = future
#
#     def cancel(self):
#         return self.future.cancel()
#
#     def cancelled(self):
#         return self.future.cancelled()
#
#     def running(self):
#         return self.future.running()
#
#     def done(self):
#         return self.future.done()
#
#     def result(self, timeout=None):
#         result = self.future.result(timeout)
#         return unpickle_result(result)
#
#     def execption(self, timeout=None):
#         return self.future.exception(timeout)
#
#     def add_done_callback(self, fn):
#         pass # TODO: Wrap fn
#
#
# def pickled_return(f):
#     import pickle  # , functools
#     # @functools.wraps(f)
#     def wrapper(*args, **kwargs):
#         result = f(*args, **kwargs)
#         return pickle.dumps(result)
#     return wrapper
#
#
# class InterpreterPoolWrapper:
#     def __init__(self, interpreter_pool_executor):
#         assert sys.version_info >= (3, 14, 0)
#         from concurrent.futures import InterpreterPoolExecutor
#         assert isinstance(interpreter_pool_executor, InterpreterPoolExecutor)
#         self.pool = interpreter_pool_executor
#
#     def __enter__(self):
#         return self.pool.__enter__()
#
#     def __exit__(self, *exc_details):
#         return self.pool.__exit__(*exc_details)
#
#     def submit(self, fn, *args, ** kwargs):
#         # fn = pickeld_return(fn)  # apply decorator
#         future = self.pool.submit(fn, *args, **kwargs)
#         return future
#         return FutureWrapper(future)
#
#     def map(self, fn, *iterables, timeout=None, chunksize=1, buffersize=None):
#         # fn = pickled_return(fn)
#         results = self.pool.map(fn, *iterables,
#                                 timeout=timeout, chunksize=chunksize, buffersize=buffersize)
#         return (unpickle_result(r) for r in results)
#
#     def shutdown(self, wait=True, *, cancel_futures=False):
#         self.pool.shutdown(wait, cancel_futures=cancel_futures)


class PickMultiCoreExecutorShim:
    def __call__(self):  # -> Type[concurrent.futures.Executor]:
        """Returns an instance of the most lightweight
        concurrent.futures.Executor that can make use of all available cpu
        cores. For Python versions >= 3.14 this is an instance of
        concurrent.futures.InterpreterPoolExecutor. For older Python-versions
        an instance of concurrent.futures.ProcessPoolExecutor is returned.
        """
        mode = eval_debug_parallel_execution()  # type: str
        if mode == "commandline":
            options = [arg for arg in sys.argv if arg[:2] == '--']
            if '--singlethread' in options:
                raise AssertionError("--singlethread forbids using a multi-core-executor")
            elif '--multithreading' in options:
                raise AssertionError("--multithreating forbids using a multi-core-executor")
        elif multiprocessing_broken():
                raise AssertionError("multi-core-executor does not work with PyInstaller")
        else:
            assert mode in ('multicore', 'multiprocessing')
        import concurrent.futures
        if sys.version_info >= (3, 14, 0) \
                and CONFIG_PRESET['multicore_pool'] == 'InterpreterPool':
            return concurrent.futures.InterpreterPoolExecutor()
        else:
            return concurrent.futures.ProcessPoolExecutor()


PickMultiCoreExecutor = PickMultiCoreExecutorShim()


def instantiate_executor(allow_parallel: bool,
                         preferred_executor = PickMultiCoreExecutor,  # : Type[concurrent.futures.Executor],
                         *args, **kwargs):  # -> concurrent.futures.Executor:
    """Instantiates an Executor of a particular type.

    If `allow_parallel` is False, a SingleThreadExecutor will be instantiated,
    regardless of the preferred_executor and any configuration values.

    Parallel execution can still be blocked by the configuration variable
    'debug_parallel_execution'. (The default
    is to allow full multiprocessing unless a command-line switch was used to
    trigger a different behavior.) Otherwise, a surrogate executor will be returned.

    :param allow_parallel: If false, a SingeThreadExecutor-object will be returned.
        If true, it depends on the config value of 'debug_parallel_executor'
        (see comments in config.py for a detailed explanation)
    :param preferred_executor: the preferred executor class that is used if the
        parameter allaw_parallel is true and 'debug_parallel_executor' does not
        forbid the use of this kind of executor. The inofficial default value
        is MultiCoreExecutor, which yields a ProcessPoolExecutor for Python
        versions <= 3.13 and a wrapped InterpreterPoolExecutor for Python
        versions 3.14 and above.
    :returns: and executor-object, either an instance of concurrent.futures.Executor
        or SingleThreadExecutor (see above).
    """
    if allow_parallel:
        import concurrent.futures
        mode = get_config_value('debug_parallel_execution')  # type: str
        if mode == "commandline":
            options = [arg for arg in sys.argv if arg[:2] == '--']
            if '--singlethread' in options:  mode = 'singlethread'
            elif '--multithreading' in options:  mode = 'multithreading'
            else:  mode = 'multicore'
        if mode == "singlethread":
            return SingleThreadExecutor()
        elif mode == "multithreading" or multiprocessing_broken():
            if not issubclass(preferred_executor, concurrent.futures.ThreadPoolExecutor):
                return concurrent.futures.ThreadPoolExecutor(*args, **kwargs)
        else:
            assert mode in ("multicore", "multiprocessing"), \
                f'Config variable "debug_parallel_execution" has illegal value "{mode}"'
            if mode == "multiprocessing":
                print('Value "multiprocessing" for config-variable "debug_parallel_execution"'
                      ' is deprecated. Please, use "multicore", instead!')
        return preferred_executor(*args, **kwargs)
    return SingleThreadExecutor()


def cpu_count() -> int:
    """Returns the number of cpus that are accessible to the current process
    or 1 if the cpu count cannot be determined."""
    try:
        return len(os.sched_getaffinity(0)) or 1
    except AttributeError:
        return os.cpu_count() or 1

#######################################################################
#
# initialization
#
#######################################################################


try:
    if sys.stdout.encoding.lower() != "utf-8":  # and  platform.system() == "Windows":
        # make sure that `print()` does not raise an error on
        # non-ASCII characters:
        # sys.stdout = cast(io.TextIOWrapper, codecs.getwriter("utf-8")(cast(
        #     io.BytesIO, cast(io.TextIOWrapper, sys.stdout).detach())))
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), sys.stdout.encoding, 'replace')
except AttributeError:
    # somebody has already taken care of this !?
    pass
