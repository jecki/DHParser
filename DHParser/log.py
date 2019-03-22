# logging.py - logging and debugging for DHParser
#
# Copyright 2018  by Eckhart Arnold (arnold@badw.de)
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
Module ``log`` contains logging and debugging support for the
parsing process.

For logging functionality, the global variable LOGGING is defined which
contains the name of a directory where log files shall be placed. By
setting its value to the empty string "" logging can be turned off.

To read the directory name function ``LOGS_DIR()`` should be called
rather than reading the variable LOGGING. ``LOGS_DIR()`` makes sure
the directory exists and raises an error if a file with the same name
already exists.

For debugging of the parsing process, the parsing history can be
logged and written to an html-File.

For ease of use module ``log`` defines a context-manager ``logging``
to which either ``False`` (turn off logging), a log directory name or
``True`` for the default logging directory is passed as argument.
The other components of DHParser check whether logging is on and
write log files in the the logging directory accordingly. Usually,
this will be concrete and abstract syntax trees as well as the full
and abreviated parsing history.

Example::

    from DHParser import compile_source, logging

    with logging("LOGS"):
        result, errors, ast = compile_source(source, preprocessor, grammar,
                                             transformer, compiler)
"""

import collections
import contextlib
import html
import os
from typing import List, Tuple, Union, Optional

from DHParser.error import Error
from DHParser.stringview import StringView
from DHParser.syntaxtree import Node, ZOMBIE_TAG
from DHParser.toolkit import is_filename, escape_control_characters, GLOBALS

__all__ = ('log_dir',
           'logging',
           'is_logging',
           'logfile_basename',
           'clear_logs',
           'HistoryRecord',
           'log_ST',
           'log_parsing_history')


#######################################################################
#
# logging context manager and logfile support
#
#######################################################################


def log_dir() -> Union[str, bool]:
    """Creates a directory for log files (if it does not exist) and
    returns its path.

    WARNING: Any files in the log dir will eventually be overwritten.
    Don't use a directory name that could be the name of a directory
    for other purposes than logging.

    ATTENTION: The log-dir is sotred thread locally, which means the log-dir
    as well as the information whether logging is turned on or off will not
    automatically be transferred to any subprocesses. This needs to be done
    explicitly. (See `testing.grammar_suite()` for an example, how this can
    be done.

    Returns:
        name of the logging directory (str) or False (bool) if logging has
        not been switched on with the logging-contextmanager (see below), yet.
    """
    # the try-except clauses in the following are precautions for multithreading
    try:
        dirname = GLOBALS.LOGGING  # raises a name error if LOGGING is not defined
        if not dirname:
            raise AttributeError  # raise a name error if LOGGING evaluates to False
    except AttributeError:
        return False
        # raise AttributeError("No access to log directory before logging has been "
        #                      "turned on within the same thread/process.")
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
        with open(info_file_name, 'w', encoding="utf-8") as f:
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
    if dirname and not isinstance(dirname, str):
        dirname = "LOGS"  # be fail tolerant here...
    try:
        save = GLOBALS.LOGGING
    except AttributeError:
        save = ""
    GLOBALS.LOGGING = dirname or ""
    # if dirname and not os.path.exists(dirname):
    #     os.mkdir(dirname)
    yield
    GLOBALS.LOGGING = save


def is_logging() -> bool:
    """-> True, if logging is turned on."""
    try:
        return bool(GLOBALS.LOGGING)
    except AttributeError:
        return False


def logfile_basename(filename_or_text, function_or_class_or_instance) -> str:
    """Generates a reasonable logfile-name (without extension) based on
    the given information.
    """
    if is_filename(filename_or_text):
        return os.path.basename(os.path.splitext(filename_or_text)[0])
    else:
        try:
            name = function_or_class_or_instance.__qualname.__
        except AttributeError:
            name = function_or_class_or_instance.__class__.__name__
        i = name.find('.')
        return name[:i] + '_out' if i >= 0 else name


def clear_logs(logfile_types=frozenset(['.cst', '.ast', '.log'])):
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


#######################################################################
#
# parsing history
#
#######################################################################


class HistoryRecord:
    """
    Stores debugging information about one completed step in the
    parsing history.

    A parsing step is "completed" when the last one of a nested
    sequence of parser-calls returns. The call stack including
    the last parser call will be frozen in the ``HistoryRecord``-
    object. In addition a reference to the generated leaf node
    (if any) will be stored and the result status of the last
    parser call, which ist either MATCH, FAIL (i.e. no match)
    or ERROR.
    """
    __slots__ = ('call_stack', 'node', 'text', 'line_col', 'errors')

    MATCH = "MATCH"
    ERROR = "ERROR"
    FAIL = "FAIL"
    Snapshot = collections.namedtuple('Snapshot', ['line', 'column', 'stack', 'status', 'text'])

    COLGROUP = '<colgroup>\n<col style="width:2%"/><col style="width:2%"/><col ' \
               'style="width:75%"/><col style="width:6%"/><col style="width:15%"/>\n</colgroup>'
    HEADINGS = ('<tr><th>L</th><th>C</th><th>parser call sequence</th>'
                '<th>success</th><th>text matched or failed</th></tr>')
    HTML_LEAD_IN = (
        '<!DOCTYPE html>\n'
        '<html>\n<head>\n<meta charset="utf-8"/>\n<style>\n'
        'td,th {font-family:monospace; '
        'border-right: thin solid grey; border-bottom: thin solid grey}\n'
        'td.line, td.column {color:darkgrey}\n'  # 'td.stack {}\n'
        'td.status {font-weight:bold}\n'
        'td.text {color:darkblue}\n'
        'table {border-spacing: 0px; border: thin solid darkgrey; width:100%}\n'
        'span {color:grey;}\nspan.match {color:darkgreen}\n'
        'span.fail {color:darkgrey}\nspan.error {color:red}\n'
        'span.matchstack {font-weight:bold;color:darkred}'
        '\n</style>\n</head>\n<body>\n')
    HTML_LEAD_OUT = '\n</body>\n</html>\n'

    def __init__(self, call_stack: List[str],
                 node: Optional[Node],
                 text: StringView,
                 line_col: Tuple[int, int],
                 errors: List[Error] = []) -> None:
        # copy call stack, dropping uninformative Forward-Parsers
        self.call_stack = [tn for tn in call_stack if tn != ":Forward"]  # type: List[str]
        self.node = node                # type: Optional[Node]
        self.text = text                # type: StringView
        self.line_col = line_col        # type: Tuple[int, int]
        self.errors = errors            # type: List[Error]

    def __str__(self):
        return '%4i, %2i:  %s;  %s;  "%s"' % self.as_tuple()

    def as_tuple(self) -> 'Snapshot':
        """
        Returns history record formatted as a snapshot tuple.
        """
        return self.Snapshot(self.line_col[0], self.line_col[1],
                             self.stack, self.status, self.excerpt)

    def as_csv_line(self) -> str:
        """
        Returns history record formatted as a csv table row.
        """
        return '"{}", "{}", "{}", "{}", "{}"'.format(*self.as_tuple())

    def as_html_tr(self) -> str:
        """
        Returns history record formatted as an html table row.
        """
        stack = html.escape(self.stack).replace(
            '-&gt;', '<span>&shy;-&gt;</span>')
        status = html.escape(self.status)
        excerpt = html.escape(self.excerpt)
        if status == self.MATCH:
            status = '<span class="match">' + status + '</span>'
            i = stack.rfind('-&gt;')
            chr = stack[i + 12:i + 13]
            while not chr.isidentifier() and i >= 0:
                i = stack.rfind('-&gt;', 0, i)
                chr = stack[i + 12:i + 13]
            if i >= 0:
                i += 12
                k = stack.find('<', i)
                if k < 0:
                    stack = stack[:i] + '<span class="matchstack">' + stack[i:]
                else:
                    stack = stack[:i] + '<span class="matchstack">' + stack[i:k] \
                        + '</span>' + stack[k:]
        elif status == self.FAIL:
            status = '<span class="fail">' + status + '</span>'
        else:
            stack += '<br/>\n' + status
            status = '<span class="error">ERROR</span>'
        tpl = self.Snapshot(str(self.line_col[0]), str(self.line_col[1]), stack, status, excerpt)
        # return ''.join(['<tr>'] + [('<td>%s</td>' % item) for item in tpl] + ['</tr>'])
        return ''.join(['<tr>'] + [('<td class="%s">%s</td>' % (cls, item))
                                   for cls, item in zip(tpl._fields, tpl)] + ['</tr>'])

    def err_msg(self) -> str:
        return self.ERROR + ": " + "; ".join(str(e) for e in (self.errors))

    @property
    def stack(self) -> str:
        return "->".join(self.call_stack)

    @property
    def status(self) -> str:
        return self.FAIL if self.node is None or self.node.tag_name == ZOMBIE_TAG else \
            ('"%s"' % self.err_msg()) if self.errors else self.MATCH

    @property
    def excerpt(self):
        length = len(self.node) if self.node else len(self.text)
        excerpt = str(self.node)[:min(length, 20)] if self.node else str(self.text[:20])
        excerpt = escape_control_characters(excerpt)
        if length > 20:
            excerpt += '...'
        return excerpt

    # @property
    # def extent(self) -> slice:
    #     return (slice(-self.remaining - len(self.node), -self.remaining) if self.node
    #             else slice(-self.remaining, None))

    @property
    def remaining(self) -> int:
        return len(self.text) - (len(self.node) if self.node else 0)

    @staticmethod
    def last_match(history: List['HistoryRecord']) -> Union['HistoryRecord', None]:
        """
        Returns the last match from the parsing-history.
        Args:
            history:  the parsing-history as a list of HistoryRecord objects

        Returns:
            the history record of the last match or none if either history is
            empty or no parser could match
        """
        for record in reversed(history):
            if record.status == HistoryRecord.MATCH:
                return record
        return None

    @staticmethod
    def most_advanced_match(history: List['HistoryRecord']) -> Union['HistoryRecord', None]:
        """
        Returns the closest-to-the-end-match from the parsing-history.
        Args:
            history:  the parsing-history as a list of HistoryRecord objects

        Returns:
            the history record of the closest-to-the-end-match or none if either history is
            empty or no parser could match
        """
        remaining = -1
        result = None
        for record in history:
            if (record.status == HistoryRecord.MATCH
                    and (record.remaining < remaining or remaining < 0)):
                result = record
                remaining = record.remaining
        return result


#######################################################################
#
#  context specific log functions, i.e. logging of syntax trees,
#  grammar history and the like
#
#######################################################################


def log_ST(syntax_tree, log_file_name):
    """
    Writes an S-expression-representation of the `syntax_tree` to a file,
    if logging is turned on.
    """
    if is_logging():
        path = os.path.join(log_dir(), log_file_name)
        if os.path.exists(path):
            print('WARNING: Log-file "%s" already exists and will be overwritten!' % path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(syntax_tree.as_sxpr())


LOG_SIZE_THRESHOLD = 10000    # maximum number of history records to log
LOG_TAIL_THRESHOLD = 500      # maximum number of history recors for "tail log"


def log_parsing_history(grammar, log_file_name: str = '', html: bool = True) -> None:
    """
    Writes a log of the parsing history of the most recently parsed document.

    Parameters:
        grammar (Grammar):  The Grammar object from which the parsing history
            shall be logged.
        log_file_name (str):  The (base-)name of the log file to be written.
            If no name is given (default), then the class name of the grammar
            object will be used.
        html (bool):  If true (default), the log will be output as html-Table,
            otherwise as plain test. (Browsers might take a few seconds or
            minutes to display the table for long histories.)
    """
    def write_log(history, log_name):
        htm = '.html' if html else ''
        path = os.path.join(log_dir(), log_name + "_parser.log" + htm)
        if os.path.exists(path):
            os.remove(path)
            print('WARNING: Log-file "%s" already existed and was deleted.' % path)
        if history:
            with open(path, "w", encoding="utf-8") as f:
                if html:
                    f.write(HistoryRecord.HTML_LEAD_IN + '\n')
                    f.write("\n".join(history))
                    f.write('\n</table>\n' + HistoryRecord.HTML_LEAD_OUT)
                else:
                    f.write("\n".join(history))

    def append_line(log, line):
        """Appends a line to a list of HTML table rows. Starts a new
        table every 100 rows to allow browser to speed up rendering.
        Does this really work...?"""
        log.append(line)
        if html and len(log) % 50 == 0:
            log.append('\n'.join(['</table>\n<table>', HistoryRecord.COLGROUP]))

    if not is_logging():
        raise AssertionError("Cannot log history when logging is turned off!")

    if not log_file_name:
        name = grammar.__class__.__name__
        log_file_name = name[:-7] if name.lower().endswith('grammar') else name
    elif log_file_name.lower().endswith('.log'):
        log_file_name = log_file_name[:-4]

    full_history = ['<h1>Full parsing history of "%s"</h1>' % log_file_name]  # type: List[str]

    if len(grammar.history__) > LOG_SIZE_THRESHOLD:
        warning = ('Sorry, man, %iK history records is just too many! '
                   'Only looking at the last %iK records.'
                   % (len(grammar.history__) // 1000, LOG_SIZE_THRESHOLD // 1000))
        html_warning = '<p><strong>' + warning + '</strong></p>'
        full_history.append(html_warning)

    lead_in = '\n'. join(['<table>', HistoryRecord.COLGROUP, HistoryRecord.HEADINGS])
    full_history.append(lead_in)

    for record in grammar.history__[-LOG_SIZE_THRESHOLD:]:
        line = record.as_html_tr() if html else str(record)
        append_line(full_history, line)

    write_log(full_history, log_file_name + '_full')
    if len(full_history) > LOG_TAIL_THRESHOLD + 10:
        heading = '<h1>Last 500 records of parsing history of "%s"</h1>' % log_file_name + lead_in
        write_log([heading] + full_history[-LOG_TAIL_THRESHOLD:], log_file_name + '_full.tail')
