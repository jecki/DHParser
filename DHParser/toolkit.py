#!/usr/bin/python3

"""toolkit.py - utility functions for DHParser

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


Module ``toolkit`` contains utility functions and cross-sectional
functionality like logging support that is needed across several 
of the the other DHParser-Modules.

For logging functionality, the global variable LOGGING is defined which
contains the name of a directory where log files shall be placed. By
setting its value to the empty string "" logging can be turned off.

To read the directory name function ``LOGS_DIR()`` should be called
rather than reading the variable LOGGING. ``LOGS_DIR()`` makes sure
the directory exists and raises an error if a file with the same name
already exists.
"""

import collections
import hashlib
import os
try:
    import regex as re
except ImportError:
    import re


__all__ = ['logging_on',
           'logging_off',
           'IS_LOGGING',
           'LOGS_DIR',
           'line_col',
           'error_messages',
           'escape_re',
           'load_if_file',
           'is_python_code',
           'md5',
           'expand_table',
           'sequence',
           'sane_parser_name']


LOGGING: str = "LOGS"  # LOGGING = "" turns logging off!


def logging_on(log_subdir="LOGS"):
    "Turns logging of syntax trees and parser history on."
    global LOGGING
    LOGGING = log_subdir


def logging_off():
    "Turns logging of syntax trees and parser history off."
    global LOGGING
    LOGGING = ""


def IS_LOGGING():
    """-> True, if logging is turned on."""
    return bool(LOGGING)


def LOGS_DIR() -> str:
    """Returns a path of a directory where log files will be stored.
    
    The default name of the logging directory is taken from the LOGGING
    variabe (default value 'LOGS'). The directory will be created if it
    does not exist. If the directory name does not contain a leading
    slash '/' it will be created as a subdirectory of the current
    directory Any files in the logging directory can be overwritten!
    
    Raises:
        AssertionError if logging has been turned off 
    Returns:
        name of the logging directory
    """
    global LOGGING
    if not LOGGING:
        raise AssertionError("Cannot use LOGS_DIR() if logging is turned off!")
    dirname = LOGGING
    if os.path.exists(LOGGING):
        if not os.path.isdir(LOGGING):
            raise IOError('"' + LOGGING + '" cannot be used as log directory, '
                                          'because it is not a directory!')
    else:
        os.mkdir(LOGGING)
    info_file_name = os.path.join(LOGGING, 'info.txt')
    if not os.path.exists(info_file_name):
        with open(info_file_name, 'w') as f:
            f.write("This directory has been created by DHParser to store log files from\n"
                    "parsing. ANY FILE IN THIS DIRECTORY CAN BE OVERWRITTEN! Therefore,\n"
                    "do not place any files here or edit existing files in this directory\n"
                    "manually.\n")
    return dirname


def line_col(text, pos):
    """Returns the position within a text as (line, column)-tuple.
    """
    assert pos < len(text), str(pos) + " >= " + str(len(text))
    line = text.count("\n", 0, pos) + 1
    column = pos - text.rfind("\n", 0, pos)
    return line, column


def error_messages(text, errors):
    """
    Converts the list of ``errors`` collected from the root node of the
    parse tree of `text` into a human readable (and IDE or editor
    parsable text) with line an column numbers. Error messages are
    separated by an empty line.
    """
    return "\n\n".join("line: %i, column: %i, error: %s" %
                       (*line_col(text, err.pos), err.msg)
                       for err in sorted(list(errors)))


def compact_sexpr(s):
    """Returns S-expression ``s`` as a one liner without unnecessary
    whitespace.

    Example:
        >>> compact_sexpr("(a\n    (b\n        c\n    )\n)\n")
        (a (b c))
    """
    return re.sub('\s(?=\))', '', re.sub('\s+', ' ', s)).strip()


def escape_re(s):
    """Returns `s` with all regular expression special characters escaped.
    """
    assert isinstance(s, str)
    re_chars = r"\.^$*+?{}[]()#<>=|!"
    for esc_ch in re_chars:
        s = s.replace(esc_ch, '\\' + esc_ch)
    return s


def load_if_file(text_or_file):
    """Reads and returns content of a file if parameter `text_or_file` is a
    file name (i.e. a single line string), otherwise (i.e. if `text_or_file` is
    a multiline string) `text_or_file` is returned.
    """
    if text_or_file and text_or_file.find('\n') < 0:
        with open(text_or_file, encoding="utf-8") as f:
            content = f.read()
        return content
    else:
        return text_or_file


def is_python_code(text_or_file):
    """Checks whether 'text_or_file' is python code or the name of a file that
    contains python code.
    """
    if text_or_file.find('\n') < 0:
        return text_or_file[-3:].lower() == '.py'
    try:
        compile(text_or_file, '<string>', 'exec')
        return True
    except (SyntaxError, ValueError, OverflowError):
        pass
    return False


def md5(*txt):
    """Returns the md5-checksum for `txt`. This can be used to test if
    some piece of text, for example a grammar source file, has changed.
    """
    md5_hash = hashlib.md5()
    for t in txt:
        md5_hash.update(t.encode('utf8'))
    return md5_hash.hexdigest()


def expand_table(compact_table):
    """Expands a table by separating keywords that are tuples or strings
    containing comma separated words into single keyword entries with
    the same values. Returns the expanded table.
    Example:
    >>> expand_table({"a, b": 1, "b": 1, ('d','e','f'):5, "c":3})
    {'a': 1, 'b': 1, 'c': 3, 'd': 5, 'e': 5, 'f': 5}
    """
    expanded_table = {}
    keys = list(compact_table.keys())
    for key in keys:
        value = compact_table[key]
        if isinstance(key, str):
            parts = (s.strip() for s in key.split(','))
        else:
            assert isinstance(key, collections.abc.Iterable)
            parts = key
        for p in parts:
            expanded_table[p] = value
    return expanded_table


def sequence(arg):
    """Returns the argument if it is a sequence, otherwise returns a
    list containing the argument as sole item."""
    return arg if isinstance(arg, collections.abc.Sequence) else [arg]


def sane_parser_name(name):
    """Checks whether given name is an acceptable parser name. Parser names
    must not be preceeded or succeeded by a double underscore '__'!
    """
    return name and name[:2] != '__' and name[-2:] != '__'


def compile_python_object(python_src, catch_obj_regex):
    """Compiles the python source code and returns the object the name of which
    ends is matched by ``catch_obj_regex``.
    """
    if isinstance(catch_obj_regex, str):
        catch_obj_regex = re.compile(catch_obj_regex)
    code = compile(python_src, '<string>', 'exec')
    namespace = {}
    exec(code, namespace)  # safety risk?
    matches = [key for key in namespace.keys() if catch_obj_regex.match(key)]
    if len(matches) > 1:
        raise AssertionError("Ambigous matches for %s : %s" %
                             (str(catch_obj_regex), str(matches)))
    return namespace[matches[0]] if matches else None

