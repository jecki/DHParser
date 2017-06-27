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
import contextlib
import hashlib
import os
try:
    import regex as re
except ImportError:
    import re
from .typing import List, Tuple


__all__ = ['logging',
           'is_logging',
           'log_dir',
           'logfile_basename',
           # 'supress_warnings',
           # 'warnings',
           'line_col',
           'error_messages',
           'compact_sexpr',
           'escape_re',
           'is_filename',
           'load_if_file',
           'is_python_code',
           'md5',
           'expand_table',
           'smart_list',
           'sane_parser_name']


def log_dir() -> str:
    """Creates a directory for log files (if it does not exist) and
    returns its path.

    WARNING: Any files in the log dir will eventually be overwritten.
    Don't use a directory name that could be the name of a directory
    for other purposes than logging.

    Returns:
        name of the logging directory
    """
    # the try-except clauses in the following are precautions for multiprocessing
    global LOGGING
    try:
        dirname = LOGGING    # raises a name error if LOGGING is not defined
        if not dirname:
            raise NameError  # raise a name error if LOGGING evaluates to False
    except NameError:
        raise NameError("No access to log directory before logging has been turned "
                        "on within the same thread/process.")
    if os.path.exists(dirname) and not os.path.isdir(dirname):
        raise IOError('"' + dirname + '" cannot be used as log directory, '
                                      'because it is not a directory!')
    else:
        try:
            os.mkdir(dirname)
        except FileExistsError:
            pass
    info_file_name = os.path.join(dirname, 'info.txt')
    if not os.path.exists(info_file_name):
        with open(info_file_name, 'w') as f:
            f.write("This directory has been created by DHParser to store log files from\n"
                    "parsing. ANY FILE IN THIS DIRECTORY CAN BE OVERWRITTEN! Therefore,\n"
                    "do not place any files here and do not bother editing files in this\n"
                    "directory as any changes will get lost.\n")
    return dirname


@contextlib.contextmanager
def logging(dirname: str = "LOGS"):
    """Context manager. Log files within this context will be stored in
    directory ``dirname``. Logging is turned off if name is empty.
    
    Args:
        dirname: the name for the log directory or the empty string to
            turn logging of
    """
    global LOGGING
    if dirname == True:  dirname = "LOGS"  # be fail tolerant here...
    try:
        save = LOGGING
    except NameError:
        save = ""
    LOGGING = dirname
    yield
    LOGGING = save


def is_logging() -> bool:
    """-> True, if logging is turned on."""
    global LOGGING
    try:
        return bool(LOGGING)
    except NameError:
        return False


# @contextlib.contextmanager
# def supress_warnings(supress: bool = True):
#     global SUPRESS_WARNINGS
#     try:
#         save = SUPRESS_WARNINGS
#     except NameError:
#         save = False  # global default for warning supression is False
#     SUPRESS_WARNINGS = supress
#     yield
#     SUPRESS_WARNINGS = save
#
#
# def warnings() -> bool:
#     global SUPRESS_WARNINGS
#     try:
#         return not SUPRESS_WARNINGS
#     except NameError:
#         return True


def line_col(text: str, pos: int) -> Tuple[int, int]:
    """Returns the position within a text as (line, column)-tuple.
    """
    assert pos < len(text), str(pos) + " >= " + str(len(text))
    line = text.count("\n", 0, pos) + 1
    column = pos - text.rfind("\n", 0, pos)
    return line, column


def error_messages(source_text, errors) -> List[str]:
    """Returns the sequence or iterator of error objects as an intertor
    of error messages with line and column numbers at the beginning.
    
    Args:
        source_text (str):  The source text on which the errors occurred.
            (Needed in order to determine the line and column numbers.)
        errors (list):  The list of errors as returned by the method 
            ``collect_errors()`` of a Node object     
    Returns:
        a list that contains all error messages in string form. Each
        string starts with "line: [Line-No], column: [Column-No]
    """
    return ["line: %i, column: %i" % line_col(source_text, err.pos) + ", error: %s" % err.msg
            for err in sorted(list(errors))]


def compact_sexpr(s) -> str:
    """Returns S-expression ``s`` as a one liner without unnecessary
    whitespace.

    Example:
        >>> compact_sexpr("(a\n    (b\n        c\n    )\n)\n")
        (a (b c))
    """
    return re.sub('\s(?=\))', '', re.sub('\s+', ' ', s)).strip()


# def quick_report(parsing_result) -> str:
#     """Returns short report (compact s-expression + errors messages)
#     of the parsing results by either a call to a grammar or to a parser
#     directly."""
#     err = ''
#     if isinstance(parsing_result, collections.Collection):
#         result = parsing_result[0]
#         err = ('\nUnmatched sequence: ' + parsing_result[1]) if parsing_result[1] else ''
#     sexpr = compact_sexpr(result.as_sexpr())
#     return sexpr + err


def escape_re(s) -> str:
    """Returns `s` with all regular expression special characters escaped.
    """
    assert isinstance(s, str)
    re_chars = r"\.^$*+?{}[]()#<>=|!"
    for esc_ch in re_chars:
        s = s.replace(esc_ch, '\\' + esc_ch)
    return s


def is_filename(s) -> bool:
    """Tries to guess whether string ``s`` is a file name."""
    return s.find('\n') < 0 and s[:1] != " " and s[-1:] != " " \
           and s.find('*') < 0 and s.find('?') < 0


def logfile_basename(filename_or_text, function_or_class_or_instance) -> str:
    """Generates a reasonable logfile-name (without extension) based on
    the given information.
    """
    if is_filename(filename_or_text):
        return os.path.basename(os.path.splitext(filename_or_text)[0])
    else:
        try:
            s = function_or_class_or_instance.__qualname.__
        except AttributeError:
            s = function_or_class_or_instance.__class__.__name__
        i = s.find('.')
        return s[:i] + '_out' if i >= 0 else s


def load_if_file(text_or_file) -> str:
    """Reads and returns content of a text-file if parameter
    `text_or_file` is a file name (i.e. a single line string),
    otherwise (i.e. if `text_or_file` is a multiline string)
    `text_or_file` is returned.
    """
    if is_filename(text_or_file):
        try:
            with open(text_or_file, encoding="utf-8") as f:
                content = f.read()
            return content
        except FileNotFoundError as error:
            if re.fullmatch(r'[\w/:. \\]+', text_or_file):
                raise FileNotFoundError('Not a valid file: ' + text_or_file + '\nAdd "\\n" '
                                        'to distinguish source data from a file name!')
            else:
                return text_or_file
    else:
        return text_or_file


def is_python_code(text_or_file) -> bool:
    """Checks whether 'text_or_file' is python code or the name of a file that
    contains python code.
    """
    if is_filename(text_or_file):
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


def smart_list(arg) -> list:
    """Returns the argument as list, depending on its type and content.
    
    If the argument is a string, it will be interpreted as a list of
    comma separated values, trying ';', ',', ' ' as possible delimiters
    in this order, e.g.
        >>> smart_list("1; 2, 3; 4")
        ["1", "2, 3", "4"]
        >>> smart_list("2, 3")
        ["2", "3"]
        >>> smart_list("a b cd")
        ["a", "b", "cd"]
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
    # elif isinstance(arg, collections.abc.Sequence):  # python 3.6: collections.abc.Collection
    #     return arg
    elif isinstance(arg, collections.abc.Iterable):
        return list(arg)
    else:
        return [arg]


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
        for k in smart_list(key):
            if k in expanded_table:
                raise KeyError("Key %s used more than once in compact table!" % key)
            expanded_table[k] = value
    return expanded_table

# # commented, because this approach is too error-prone in connection with smart_list
# def as_partial(partial_ellipsis) -> functools.partial:
#     """Transforms ``partial_ellipsis`` into a partial function
#     application, i.e. string "remove_tokens({'(', ')'})" will be
#     transformed into the partial "partial(remove_tokens, {'(', ')'})".
#     Partial ellipsises can be considered as a short hand notation for
#     partials, which look like function, calls but aren't. Plain
#     function names are returned as is. Also, if ``partial_ellipsis``
#     already is a callable, it will be returned as is.
#     """
#     if callable(partial_ellipsis):
#         return partial_ellipsis
#     m = re.match('\s*(\w+)(?:\(([^)]*)\))?\s*$', partial_ellipsis)
#     if m:
#         fname, fargs = m.groups()
#         return eval("functools.partial(%s, %s)" % (fname, fargs)) if fargs else eval(fname)
#     raise SyntaxError(partial_ellipsis + " does not resemble a partial function ellipsis!")


def sane_parser_name(name) -> bool:
    """Checks whether given name is an acceptable parser name. Parser names
    must not be preceeded or succeeded by a double underscore '__'!
    """
    return name and name[:2] != '__' and name[-2:] != '__'


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
        matches = [key for key in namespace.keys() if catch_obj_regex.match(key)]
        if len(matches) == 0:
            raise ValueError("No object matching /%s/ defined in source code." %
                             catch_obj_regex.pattern)
        elif len(matches) > 1:
            raise ValueError("Ambigous matches for %s : %s" %
                             (str(catch_obj_regex), str(matches)))
        return namespace[matches[0]] if matches else None
    else:
        return namespace
