# log.py - logging and debugging for DHParser
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

    from DHParser import compile_source, logging, set_config_value

    start_logging("LOGS")
    set_config_value('log_syntax_trees', {'cst', 'ast'})
    set_config_value('history_tracking', True)
    set_config_value('resume_notices', True)
    result, errors, ast = compile_source(source, preprocessor, grammar,
                                         transformer, compiler)
"""

import collections
import contextlib
import html
import os
from typing import List, Tuple, Union, Optional

from DHParser.configuration import access_presets, finalize_presets, get_config_value, \
    set_config_value
from DHParser.error import Error
from DHParser.stringview import StringView
from DHParser.syntaxtree import Node, FrozenNode, ZOMBIE_TAG, EMPTY_PTYPE
from DHParser.toolkit import escape_control_characters, abbreviate_middle

__all__ = ('CallItem',
           'start_logging',
           'suspend_logging',
           'resume_logging',
           'log_dir',
           'local_log_dir',
           'is_logging',
           'create_log',
           'append_log',
           'clear_logs',
           'NONE_TAG',
           'NONE_NODE',
           'freeze_callstack',
           'HistoryRecord',
           'log_ST',
           'log_parsing_history')


CallItem = Tuple[str, int]      # call stack item: (tag_name, location)


#######################################################################
#
# basic logging functionality
#
#######################################################################

def start_logging(dirname: str = "LOGS"):
    """Turns logging on an sets the log-directory to `dirname`.
    The log-directory, if it does not already exist, will be created
    lazily, i.e. only when logging actually starts."""
    CFG = access_presets()
    log_dir = os.path.abspath(dirname) if dirname else ''
    if log_dir != CFG['log_dir']:
        CFG['log_dir'] = log_dir
        set_config_value('log_dir', log_dir)
        finalize_presets()


def suspend_logging() -> str:
    """Suspends logging in the current thread. Returns the log-dir
    for resuming logging later."""
    save = get_config_value('log_dir')
    set_config_value('log_dir', '')
    return save


def resume_logging(log_dir: str = ''):
    """Resumes logging in the current thread with the given log-dir."""
    if not 'log_dir':
        CFG = access_presets()
        log_dir = CFG['log_dir']
    set_config_value('log_dir', log_dir)


def log_dir(path: str = "") -> str:
    """Creates a directory for log files (if it does not exist) and
    returns its path.

    WARNING: Any files in the log dir will eventually be overwritten.
    Don't use a directory name that could be the name of a directory
    for other purposes than logging.

    ATTENTION: The log-dir is stored thread locally, which means the log-dir
    as well as the information whether logging is turned on or off will not
    automatically be transferred to any subprocesses. This needs to be done
    explicitly. (See `testing.grammar_suite()` for an example, how this can
    be done.

    Parameters:
        path:   The directory path. If empty, the configured value will be
            used: `configuration.get_config_value('log_dir')`.

    Returns:
        str - name of the logging directory or '' if logging is turned off.
    """
    dirname = path if path else get_config_value('log_dir')
    if not dirname:
        return ''
    dirname = os.path.normpath(dirname)
    # `try ... except` rather than `if os.path.exists(...)` for thread-safety
    try:
        os.mkdir(dirname)
        info_file_name = os.path.join(dirname, 'info.txt')
        if not os.path.exists(info_file_name):
            with open(info_file_name, 'w', encoding="utf-8") as f:
                f.write("This directory has been created by DHParser to store log files from\n"
                        "parsing. ANY FILE IN THIS DIRECTORY CAN BE OVERWRITTEN! Therefore,\n"
                        "do not place any files here and do not bother editing files in this\n"
                        "directory as any changes will get lost.\n")
    except FileExistsError:
        if not os.path.isdir(dirname):
            raise IOError('"' + dirname + '" cannot be used as log directory, '
                                          'because it is not a directory!')
    set_config_value('log_dir', dirname)
    return dirname


@contextlib.contextmanager
def local_log_dir(path: str = './LOGS'):
    """Context manager for temporarily switching to a different log-directory."""
    assert path, "Pathname cannot be empty"
    saved_log_dir = get_config_value('log_dir')
    log_dir(path)
    try:
        yield
    finally:
        set_config_value('log_dir', saved_log_dir)


def is_logging(thread_local_query: bool = True) -> bool:
    """-> True, if logging is turned on."""
    if thread_local_query:
        return bool(get_config_value('log_dir'))
    else:
        CFG = access_presets()
        return bool(CFG['log_dir'])


def create_log(log_name: str) -> str:
    """
    Creates a new log file. If log_name is not just a file name but a path with
    at least one directoy (which can be './') the file is not created in the
    configured log directory but at the given path. If a file with the same
    name already exists, it will be overwritten.

    :param log_name: The file name of the log file to be created
    :return: the file name of the log file or an empty string if the log-file
        has not been created (e.g. because logging is still turned off and
        no log-directory set).
    """
    ldir, file_name = os.path.split(log_name)
    if not ldir:
        ldir = log_dir()
    if ldir:
        with open(os.path.join(ldir, file_name), 'w', encoding='utf-8') as f:
            f.write('LOG-FILE: ' + log_name + '\n\n')
        return log_name
    return ''


def append_log(log_name: str, *strings, echo: bool = False) -> None:
    """Appends one or more strings to the log-file with the name `log_name`,
    if logging is turned on and log_name is not the empty string, or
    `log_name` contains path information.

    :param log_name: The name of the log file. The file must already exist.
        (See: `create_log()` above).
    :param strings: One or more strings that will be written to the log-file.
        No delimiters will be added, i.e. all delimiters like blanks or
        linefeeds need to be added explicitly to the list of strings, before
        calling `append_log()`.
    :param echo: If True, the log message will be echoed on the terminal. This
        will also happen if logging is turned off.
    """
    ldir, _ = os.path.split(log_name)
    if not ldir:
        ldir = log_dir()
    if ldir and log_name:
        log_path = os.path.join(ldir, log_name)
        if not os.path.exists(log_path):
            assert create_log(log_path), 'Could not create log file: "{}"'.format(log_path)
        with open(log_path, 'a', encoding='utf-8') as f:
            for text in strings:
                f.write(text)
    if echo:
        print(''.join(strings))


def clear_logs(logfile_types=frozenset(['.cst', '.ast', '.log'])):
    """
    Removes all logs from the log-directory and removes the
    log-directory if it is empty.
    """
    log_dirname = log_dir()
    if log_dirname and os.path.exists(log_dirname) and os.path.isdir(log_dirname):
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


NONE_TAG = ":None"
NONE_NODE = FrozenNode(NONE_TAG, '')


def freeze_callstack(call_stack: List[CallItem]) -> Tuple[CallItem, ...]:
    """Returns a frozen copy of the call stack."""
    return tuple((tn, pos) for tn, pos in call_stack if tn != ":Forward")


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
    __slots__ = ('call_stack', 'node', 'text', 'pos', 'line_col', 'errors')

    MATCH = "MATCH"
    DROP = "DROP"
    ERROR = "ERROR"
    FAIL = "FAIL"
    Snapshot_Fields = ('line', 'column', 'stack', 'status', 'text')
    Snapshot = collections.namedtuple('Snapshot', ('line', 'column', 'stack', 'status', 'text'))

    COLGROUP = '<colgroup>\n<col style="width:2%"/><col style="width:2%"/><col ' \
               'style="width:65%"/><col style="width:6%"/><col style="width:25%"/>\n</colgroup>'
    HEADINGS = ('<tr><th>L</th><th>C</th><th>parser call sequence</th>'
                '<th>success</th><th>text matched or failed</th></tr>')
    HTML_LEAD_IN = (
        '<!DOCTYPE html>\n'
        '<html>\n<head>\n<meta charset="utf-8"/>\n<style>\n'
        'table {border-spacing: 0px; border: thin solid grey; width:100%}\n'
        'td,th {font-family:monospace; '
        'border-right: thin solid grey; border-bottom: thin solid grey}\n'
        'td.line, td.column {color:grey}\n'
        '.text{color:blue}\n'
        '.failtext {font-weight:normal; color:grey}\n'
        '.errortext {font-weight:normal; color:darkred}\n'
        '.unmatched {font-weight:normal; color:lightgrey}\n'
        '.fail {font-weight:bold; color:darkgrey}\n'
        '.error {font-weight:bold; color:red}\n'
        '.match {font-weight:bold; color:green}\n'
        '.drop {font-weight:bold; color:darkslategrey}\n'
        '.matchstack {font-weight:bold;color:darkred}\n'
        'span {color:darkgrey}\n'
        '</style>\n</head>\n<body>\n')
    HTML_LEAD_OUT = '\n</body>\n</html>\n'

    def __init__(self, call_stack: Union[List[CallItem], Tuple[CallItem, ...]],
                 node: Optional[Node],
                 text: StringView,
                 line_col: Tuple[int, int],
                 errors: List[Error] = []) -> None:
        # copy call stack, dropping uninformative Forward-Parsers
        # self.call_stack = call_stack    # type: Tuple[CallItem,...]
        if isinstance(call_stack, tuple):
            self.call_stack = call_stack  # type: Tuple[CallItem,...]
        else:
            self.call_stack = freeze_callstack(call_stack)
        self.node = NONE_NODE if node is None else node  # type: Node
        self.text = text                                 # type: StringView
        self.line_col = line_col                         # type: Tuple[int, int]
        assert all(isinstance(err, Error) for err in errors)
        self.errors = errors                             # type: List[Error]

    def __str__(self):
        return '%4i, %2i:  %s;  %s;  "%s"' % self.as_tuple()

    def __repr__(self):
        return 'HistoryRecord(%s, %s, %s, %s, %s)' % \
               (repr(self.call_stack), repr(self.node), repr(self.text),
                repr(self.line_col), repr(self.errors))

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
        if excerpt.startswith(' '):
            stripped = excerpt.lstrip()
            excerpt = "&nbsp;" * (len(excerpt) - len(stripped)) + stripped
        classes = list(HistoryRecord.Snapshot_Fields)
        idx = {field_name: i for i, field_name in enumerate(classes)}
        classes[idx['status']] = 'error' if status.startswith('ERROR') else status.lower()
        if status in (self.MATCH, self.DROP):
            n = max(40 - len(excerpt), 0)
            dots = '...' if len(self.text) > n else ''
            excerpt = excerpt + '<span class="unmatched">' + self.text[:n] + dots + '</span>'
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
            else:
                stack = '<span class="matchstack">{}</span>'.format(stack)
        elif status == self.FAIL:
            classes[idx['text']] = 'failtext'
        else:  # ERROR
            stack += '<br/>\n"%s"' % self.err_msg()
            classes[idx['text']] = 'errortext'
        tpl = self.Snapshot(str(self.line_col[0]), str(self.line_col[1]),
                            stack, status, excerpt)  # type: Tuple[str, str, str, str, str]
        return ''.join(['<tr>'] + [('<td class="%s">%s</td>' % (cls, item))
                                   for cls, item in zip(classes, tpl)] + ['</tr>\n'])

    def err_msg(self) -> str:
        return self.ERROR + ": " + "; ".join(str(e) for e in self.errors)

    @property
    def stack(self) -> str:
        # return "->".join(tag_name for tag_name, _ in self.call_stack)
        short_stack = []
        anonymous_tail = True
        for tag_name, _ in reversed(self.call_stack):
            if tag_name.startswith(':'):
                if anonymous_tail:
                    short_stack.append(tag_name)
            else:
                short_stack.append(tag_name)
                anonymous_tail = False
        return "->".join(reversed(short_stack))

    @property
    def status(self) -> str:
        if self.errors:
            return self.ERROR + ": " + ', '.join(str(e.code) for e in self.errors)
        elif self.node.tag_name in (NONE_TAG, ZOMBIE_TAG):
            return self.FAIL
        elif self.node.tag_name == EMPTY_PTYPE:
            return self.DROP
        else:
            return self.MATCH
        # return self.FAIL if self.node is None or self.node.tag_name == ZOMBIE_TAG else \
        #     ('"%s"' % self.err_msg()) if self.errors else self.MATCH

    @property
    def excerpt(self):
        if self.node.tag_name not in (NONE_TAG, ZOMBIE_TAG) and not self.errors:
            excerpt = abbreviate_middle(str(self.node), 40)
        else:
            s = self.text
            excerpt = s[:36] + ' ...' if len(s) > 36 else s
        excerpt = escape_control_characters(str(excerpt))
        return excerpt

    # @property
    # def extent(self) -> slice:
    #     return (slice(-self.remaining - len(self.node), -self.remaining) if self.node
    #             else slice(-self.remaining, None))

    @property
    def remaining(self) -> int:
        return len(self.text) - len(self.node)

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


def log_ST(syntax_tree, log_file_name) -> bool:
    """
    Writes an S-expression-representation of the `syntax_tree` to a file,
    if logging is turned on. Returns True, if logging was turned on and
    log could be written. Returns False, if logging was turned off.
    Raises a FileSystem error if writing the log failed for some reason.
    """
    if is_logging():
        path = os.path.join(log_dir(), log_file_name)
        # if os.path.exists(path):
        #     print('WARNING: Log-file "%s" already exists and will be overwritten!' % path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(syntax_tree.serialize())
        return True
    return False


LOG_SIZE_THRESHOLD = 10000    # maximum number of history records to log
LOG_TAIL_THRESHOLD = 500      # maximum number of history recors for "tail log"


def log_parsing_history(grammar, log_file_name: str = '', html: bool = True) -> bool:
    """
    Writes a log of the parsing history of the most recently parsed document, if
    logging is turned on. Returns True, if that was the case and writing the
    history was successful.

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
    def write_log(history: List[str], log_name: str) -> None:
        htm = '.html' if html else ''
        path = os.path.join(log_dir(), log_name + "_parser.log" + htm)
        if os.path.exists(path):
            os.remove(path)
            # print('WARNING: Log-file "%s" already existed and was deleted.' % path)
        if history:
            with open(path, "w", encoding="utf-8") as f:
                if html:
                    f.write(HistoryRecord.HTML_LEAD_IN + '\n')
                    f.writelines(history)
                    f.write('\n</table>\n' + HistoryRecord.HTML_LEAD_OUT)
                else:
                    f.write("\n".join(history))

    def append_line(log: List[str], line: str) -> None:
        """Appends a line to a list of HTML table rows. Starts a new
        table every 100 rows to allow browser to speed up rendering.
        Does this really work...?"""
        log.append(line)
        if html and len(log) % 50 == 0:
            log.append('\n'.join(['</table>\n<table>', HistoryRecord.COLGROUP]))

    if not is_logging():
        return False

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
        line = record.as_html_tr() if html else (str(record) + '\n')
        append_line(full_history, line)

    write_log(full_history, log_file_name + '_full')
    if len(full_history) > LOG_TAIL_THRESHOLD + 10:
        heading = '<h1>Last 500 records of parsing history of "%s"</h1>' % log_file_name + lead_in
        write_log([heading] + full_history[-LOG_TAIL_THRESHOLD:], log_file_name + '_full.tail')
    return True
