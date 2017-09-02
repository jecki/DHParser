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

import codecs
import collections
import contextlib
import hashlib
import os

try:
    import regex as re
except ImportError:
    import re
import sys

try:
    from typing import Any, List, Tuple, Iterable, Sequence, Union, Optional, TypeVar
except ImportError:
    from .typing34 import Any, List, Tuple, Iterable, Sequence, Union, Optional, TypeVar

__all__ = ('logging',
           'is_logging',
           'log_dir',
           'logfile_basename',
           'StringView',
           'sv_match',
           'sv_index',
           'sv_search',
           # 'supress_warnings',
           # 'warnings',
           # 'repr_call',
           'line_col',
           'error_messages',
           'escape_re',
           'is_filename',
           'load_if_file',
           'is_python_code',
           'md5',
           'expand_table',
           'smart_list',
           'sane_parser_name')


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
        dirname = LOGGING  # raises a name error if LOGGING is not defined
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
def logging(dirname="LOGS"):
    """Context manager. Log files within this context will be stored in
    directory ``dirname``. Logging is turned off if name is empty.
    
    Args:
        dirname: the name for the log directory or the empty string to
            turn logging of
    """
    global LOGGING
    if dirname and not isinstance(dirname, str):  dirname = "LOGS"  # be fail tolerant here...
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


def clear_logs(logfile_types={'.cst', '.ast', '.log'}):
    """Removes all logs from the log-directory and removes the
    log-directory if it is empty.
    """
    log_dirname = log_dir()
    files = os.listdir(log_dirname)
    only_log_files = True
    for file in files:
        path = os.path.join(log_dirname, file)
        if os.path.splitext(file)[1] in logfile_types or file == 'info.txt':
            os.remove(path)
        else:
            only_log_files = False
    if only_log_files:
        os.rmdir(log_dirname)


class StringView(collections.abc.Sized):
    """"A rudimentary StringView class, just enough for the use cases
    in parswer.py.

    Slicing Python-strings always yields copies of a segment of the original
    string. See: https://mail.python.org/pipermail/python-dev/2008-May/079699.html
    However, this becomes costly (in terms of space and as a consequence also
    time) when parsing longer documents. Unfortunately, Python's `memoryview`
    does not work for unicode strings. Hence, the StringView class.
    """

    __slots__ = ['text', 'begin', 'end', 'len']

    def __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None:
        self.text = text  # type: str
        self.begin = 0  # type: int
        self.end = 0    # type: int
        self.begin, self.end = StringView.real_indices(begin, end, len(text))
        self.len = max(self.end - self.begin, 0)

    @staticmethod
    def real_indices(begin, end, len):
        def pack(index, len):
            index = index if index >= 0 else index + len
            return 0 if index < 0 else len if index > len else index
        if begin is None:  begin = 0
        if end is None:  end = len
        return pack(begin, len), pack(end, len)

    def __bool__(self):
        return bool(self.text) and self.end > self.begin

    def __len__(self):
        return self.len

    def __str__(self):
        return self.text[self.begin:self.end]

    def __getitem__(self, index):
        # assert isinstance(index, slice), "As of now, StringView only allows slicing."
        # assert index.step is None or index.step == 1, \
        #     "Step sizes other than 1 are not yet supported by StringView"
        start, stop = StringView.real_indices(index.start, index.stop, self.len)
        return StringView(self.text, self.begin + start, self.begin + stop)

    def __eq__(self, other):
        return str(self) == str(other)  # PERFORMANCE WARNING: This creates copies of the strings

    def find(self, sub, start=None, end=None) -> int:
        if start is None and end is None:
            return self.text.find(sub, self.begin, self.end) - self.begin
        else:
            start, end = StringView.real_indices(start, end, self.len)
            return self.text.find(sub, self.begin + start, self.begin + end) - self.begin

    def startswith(self, prefix: str, start:int = 0, end:Optional[int] = None) -> bool:
        start += self.begin
        end = self.end if end is None else self.begin + end
        return self.text.startswith(prefix, start, end)



def sv_match(regex, sv: StringView):
    return regex.match(sv.text, pos=sv.begin, endpos=sv.end)


def sv_index(absolute_index: int, sv: StringView) -> int:
    """
    Converts the an index into string watched by a StringView object
    to an index relativ to the string view object, e.g.:
    >>> sv = StringView('xxIxx')[2:3]
    >>> match = sv_match(re.compile('I'), sv)
    >>> match.end()
    3
    >>> sv_index(match.end(), sv)
    1
    """
    return absolute_index - sv.begin


def sv_indices(absolute_indices: Iterable[int], sv: StringView) -> Tuple[int, ...]:
    """Converts the an index into string watched by a StringView object
    to an index relativ to the string view object. See also: `sv_index()`
    """
    return tuple(index - sv.begin for index in absolute_indices)


def sv_search(regex, sv: StringView):
    return regex.search(sv.text, pos=sv.begin, endpos=sv.end)



EMPTY_STRING_VIEW = StringView('')


# def repr_call(f, parameter_list) -> str:
#     """Turns a list of items into a string resembling the parameter
#     list of a function call by omitting default values at the end:
#     >>> def f(a, b=1):    print(a, b)
#     >>> repr_call(f, (5,1))
#     'f(5)'
#     >>> repr_call(f, (5,2))
#     'f(5, 2)'
#     """
#     i = 0
#     defaults = f.__defaults__ if f.__defaults__ is not None else []
#     for parameter, default in zip(reversed(parameter_list), reversed(defaults)):
#         if parameter != default:
#             break
#         i -= 1
#     if i < 0:
#         parameter_list = parameter_list[:i]
#     name = f.__self__.__class__.__name__ if f.__name__ == '__init__' else f.__name__
#     return "%s(%s)" % (name, ", ".merge_children(repr(item) for item in parameter_list))


def line_col(text: str, pos: int) -> Tuple[int, int]:
    """Returns the position within a text as (line, column)-tuple.
    """
    assert pos <= len(text), str(pos) + " > " + str(len(text))  # can point one character after EOF
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
    return ["line: %3i, column: %2i" % line_col(source_text, err.pos) + ", error: %s" % err.msg
            for err in sorted(list(errors))]


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


# def smart_list(arg: Union[str, Iterable[T]]) -> Union[Sequence[str], Sequence[T]]:
def smart_list(arg: Union[str, Iterable, Any]) -> Sequence:
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
    elif isinstance(arg, Sequence):
        return arg
    elif isinstance(arg, Iterable):
        return list(arg)
    else:
        return [arg]


def expand_table(compact_table):
    """Expands a table by separating keywords that are tuples or strings
    containing comma separated words into single keyword entries with
    the same values. Returns the expanded table.
    Example:
    >>> expand_table({"a, b": 1, ('d','e','f'):5, "c":3})
    {'a': 1, 'b': 1, 'd': 5, 'e': 5, 'f': 5, 'c': 3}
    """
    expanded_table = {}
    keys = list(compact_table.keys())
    for key in keys:
        value = compact_table[key]
        for k in smart_list(key):
            if k in expanded_table:
                raise KeyError('Key "%s" used more than once in compact table!' % key)
            expanded_table[k] = value
    return expanded_table


def sane_parser_name(name) -> bool:
    """Checks whether given name is an acceptable parser name. Parser names
    must not be preceded or succeeded by a double underscore '__'!
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
            raise ValueError("Ambiguous matches for %s : %s" %
                             (str(catch_obj_regex), str(matches)))
        return namespace[matches[0]] if matches else None
    else:
        return namespace


def identity(anything: Any) -> Any:
    return anything


try:
    if sys.stdout.encoding.upper() != "UTF-8":
        # make sure that `print()` does not raise an error on 
        # non-ASCII characters:
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
except AttributeError:
    # somebody has already taken care of this !?
    pass
