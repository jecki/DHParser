# configuration.py - default configuration values for DHParser
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
Module "configuration.py" defines the default configuration for DHParser.
The configuration values can be read and changed while running via the
get_config_value() and set_config_value()-functions.

The presets can also be overwritten before(!) spawning any parsing processes by
overwriting the values in the CONFIG_PRESET dictionary.

The recommended way to use a different configuration in any custom code using
DHParser is to use the second method, i.e. to overwrite the values for which
this is desired in the CONFIG_PRESET dictionary right after the start of the
program and before any DHParser-function is invoked.
"""

from __future__ import annotations

import sys
import threading
from typing import Dict, Any

__all__ = ('ALLOWED_PRESET_VALUES',
           'validate_value',
           'access_presets',
           'finalize_presets',
           'get_preset_value',
           'get_preset_values',
           'set_preset_value',
           'read_local_config',
           'NO_DEFAULT',
           'THREAD_LOCALS',
           'access_thread_locals',
           'get_config_value',
           'get_config_values',
           'set_config_value',
           'NEVER_MATCH_PATTERN')


########################################################################
#
# multiprocessing-safe preset- and configuration-handling
#
########################################################################


CONFIG_PRESET = dict()  # type: Dict[str, Any]
CONFIG_PRESET['syncfile_path'] = ''
ACCESSING_PRESETS = False
PRESETS_CHANGED = False
THREAD_LOCALS = None
ALLOWED_PRESET_VALUES = dict()  # Dict[str, Union[Set, Tuple[int, int]]
# dictionary that maps config variables to a set or range of allowed values


access_lock = threading.Lock()


def validate_value(key: str, value: Any):
    """Raises a Type- or ValueError, if the values of variable `key` are
    restricted to a certain set or range and the value does not lie within
    this set or range."""
    global ALLOWED_PRESET_VALUES
    allowed = ALLOWED_PRESET_VALUES.get(key, None)
    if allowed:
        if isinstance(allowed, tuple):
            if not isinstance(value, (int, float)):
                raise TypeError('Value %s is not an int or float as required!' % str(value))
            elif not allowed[0] <= value <= allowed[1]:
                raise ValueError('Value %s lies not within the range from %s to %s (included)!'
                                 % (str(value), str(allowed[0]), str(allowed[1])))
        else:
            if value not in allowed:
                raise ValueError('Value %s is not one of the allowed values: %s'
                                 % (str(value), str(allowed)))


def get_syncfile_path(pid: int) -> str:
    import os
    import tempfile
    return os.path.join(tempfile.gettempdir(), 'DHParser_%i.cfg' % pid)


def access_presets():
    """
    Allows read and write access to preset values via `get_preset_value()`
    and `set_preset_value()`. Any call to `access_presets()` should be
    matched by a call to `finalize_presets()` to ensure propagation of
    changed preset-values to spawned processes. For an explanation why,
    see: https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
    """
    global ACCESSING_PRESETS
    if ACCESSING_PRESETS:
        raise AssertionError('Presets are already being accessed! '
                             'Calls to access_presets() cannot be nested.')
    ACCESSING_PRESETS = True
    import multiprocessing
    global CONFIG_PRESET
    if not CONFIG_PRESET['syncfile_path'] \
            and multiprocessing.get_start_method() != 'fork':
        import os
        import pickle
        syncfile_path = get_syncfile_path(os.getppid())  # assume this is a spawned process
        if not os.path.exists(syncfile_path):
            syncfile_path = get_syncfile_path(os.getpid())  # assume this is the root process
        f = None
        try:
            f = open(syncfile_path, 'rb')
            preset = pickle.load(f)
            assert isinstance(preset, dict)
            if  preset['syncfile_path'] != syncfile_path:
                raise AssertionError('Conflicting syncfile paths %s != %s'
                                     % (preset['syncfile_path'], syncfile_path))
            CONFIG_PRESET = preset
        except FileNotFoundError:
            pass
        finally:
            if f is not None:
                f.close()


def remove_cfg_tempfile(filename: str):
    import os
    os.remove(filename)


def finalize_presets(fail_on_error: bool=False):
    """
    Finalizes changes of the presets of the configuration values.
    This method should always be called after changing preset values to
    make sure the changes will be visible to processes spawned later.
    """
    global ACCESSING_PRESETS, PRESETS_CHANGED, CONFIG_PRESET
    if not ACCESSING_PRESETS:
        raise AssertionError('Presets are not being accessed and therefore cannot be finalized!')
    if PRESETS_CHANGED:
        import multiprocessing
        if multiprocessing.get_start_method() != 'fork':
            import atexit
            import os
            import pickle
            syncfile_path = get_syncfile_path(os.getpid())
            existing_syncfile = CONFIG_PRESET['syncfile_path']
            if fail_on_error:
                assert ((not existing_syncfile or existing_syncfile == syncfile_path)
                        and (not os.path.exists((get_syncfile_path(os.getppid()))))), \
                    "finalize_presets() can only be called from the main process!"
            with open(syncfile_path, 'wb') as f:
                CONFIG_PRESET['syncfile_path'] = syncfile_path
                if existing_syncfile != syncfile_path:
                    atexit.register(remove_cfg_tempfile, syncfile_path)
                pickle.dump(CONFIG_PRESET, f)
        PRESETS_CHANGED = False
    ACCESSING_PRESETS = False
    # if THREAD_LOCALS is not None:
    #     THREAD_LOCALS.config = {}  # reset THREAD_LOCALS


def set_preset_value(key: str, value: Any, allow_new_key: bool=False):
    global CONFIG_PRESET, ACCESSING_PRESETS, PRESETS_CHANGED
    if not ACCESSING_PRESETS:
        raise AssertionError('Presets must be made accessible with access_presets() first, '
                             'before they can be set!')
    if not allow_new_key and key not in CONFIG_PRESET:
        raise ValueError(
            '"%s" is not a valid config variable. Use "allow_new_key=True" to add new variables '
            'or choose one of %s' % (key, list(CONFIG_PRESET.keys())))
    validate_value(key, value)
    CONFIG_PRESET[key] = value
    PRESETS_CHANGED = True


def read_local_config(ini_filename: str) -> str:
    """Reads a local config file and updates the presets
    accordingly. If the file is not found at the given path,
    the same base name will be tried in the current working
    directory, then in the applications config-directory and,
    ultimately, in the calling script's directory.
    This configuration file must be in the .ini-file format
    so that it can be parsed with "configparser" from the
    Python standard library. Any key,value-pair under the
    section "DHParser" will directly be transferred to the
    configuration presets. For other sections, the section
    name will added as a qualifier to the key:
    "section.key". Thus only values under the "DHParser"
    section modify the DHParser-configuration while
    configuration parameters unter other sections are
    free to be evaluated by the calling script and cannot
    interfere with DHParser's configuration.

    :param ini_filename: the file path and name of the configuration
        file.
    :returns:  the file path of the actually read .ini-file
        or the empty string if no .ini-file with the given
        name could be found either at the given path, in
        the current working directory or in the calling
        script's path.
    """
    import configparser
    import os
    config = configparser.RawConfigParser()
    config.optionxform = lambda optionstr: optionstr
    basename = os.path.basename(ini_filename)
    if not os.path.exists(ini_filename):
        # try cfg-file in current working directory next
        ini_filename = basename
    if not os.path.exists(ini_filename):
        # try cfg-file in the applications' config-directory
        # TODO: use a more portable method
        dirname = os.path.splitext(basename)[0]
        cfg_filename = os.path.join(os.path.expanduser('~'), '.config', dirname, 'config.ini')
        if os.path.exists(cfg_filename):
            ini_filename = cfg_filename
        else:
            ini_filename = os.path.join(os.path.expanduser('~'), '.config', dirname, basename)
    if not os.path.exists(ini_filename):
        # try cfg-file in script-directory next
        script_path = os.path.abspath(sys.modules['__main__'].__file__ or '.')
        ini_filename = os.path.join(os.path.dirname(script_path), basename)
    if os.path.exists(ini_filename) and config.read(ini_filename):
        access_presets()
        for section in config.sections():
            if section.lower() == "dhparser":
                for variable, value in config[section].items():
                    set_preset_value(f"{variable}", eval(value))
            else:
                for variable, value in config[section].items():
                    set_preset_value(f"{section}.{variable}", eval(value),
                                     allow_new_key=True)
        finalize_presets()
        return ini_filename
    return ''


class NoDefault:
    pass
NO_DEFAULT = NoDefault()


def get_preset_value(key: str, default: Any = NO_DEFAULT):
    global CONFIG_PRESET, ACCESSING_PRESETS
    if not ACCESSING_PRESETS:
        raise AssertionError('Presets must be made accessible with access_presets() first, '
                             'before they can be read!')
    if default is NO_DEFAULT:
        return CONFIG_PRESET[key]  # may raise a KeyError
    return CONFIG_PRESET.get(key, default)


def get_preset_values(key_pattern: str) -> Dict:
    """Returns a dictionary of all presets that match `key_pattern`."""
    global CONFIG_PRESET, ACCESSING_PRESETS
    if not ACCESSING_PRESETS:
        raise AssertionError('Presets must be made accessible with access_presets() first, '
                             'before they can be read!')
    import fnmatch
    return {key: value for key, value in CONFIG_PRESET.items()
            if fnmatch.fnmatchcase(key, key_pattern)}


def access_thread_locals() -> Any:
    """Intitializes (if not done yet) and returns the thread local variable
    store. (Call this function before using THREAD_LOCALS.
    Direct usage of THREAD_LOCALS is DEPRECATED!)
    """
    global THREAD_LOCALS
    if THREAD_LOCALS is None:
        THREAD_LOCALS = threading.local()
    return THREAD_LOCALS


def _config_dict():
    global THREAD_LOCALS
    THREAD_LOCALS = access_thread_locals()
    try:
        cfg = THREAD_LOCALS.config
    except AttributeError:
        THREAD_LOCALS.config = dict()
        cfg = THREAD_LOCALS.config
    return cfg


def get_config_value(key: str, default: Any = NO_DEFAULT) -> Any:
    """Retrieves a configuration value thread-safely.

    :param key:  the key (an immutable, usually a string)
    :param default: a default value that is returned if no config-value
        exists for the key.
    :return:     the value
    """
    with access_lock:
        cfg = _config_dict()
        try:
            return cfg[key]
        except KeyError:
            access_presets()
            value = get_preset_value(key, default)
            finalize_presets()
            cfg[key] = value
            return value


def get_config_values(key_pattern: str) -> Dict:
    """Returns a dictionary of all configuration entries that match
    `key_pattern`."""
    access_presets()
    presets = get_preset_values(key_pattern)
    finalize_presets()
    import fnmatch
    with access_lock:
        cfg = _config_dict()
        cfg_values = {key: value for key, value in cfg.items()
                      if fnmatch.fnmatchcase(key, key_pattern)}
        presets.update(cfg_values)
        cfg.update(presets)
    return presets


def set_config_value(key: str, value: Any, allow_new_key: bool = False):
    """
    Changes a configuration value thread-safely. The configuration
    value will be set only for the current thread. In order to
    set configuration values for any new thread, add the key and value
    to CONFIG_PRESET, before any thread accessing config values is started.
    :param key:    the key (an immutable, usually a string)
    :param value:  the value
    """
    with access_lock:
        cfg = _config_dict()
        if not allow_new_key and key not in cfg and key not in CONFIG_PRESET:
            raise ValueError(
                '"%s" is not a valid config variable. Use "allow_new_key=True" to '
                'add new variables or choose one of %s' % (key, list(cfg.keys())))
        validate_value(key, value)
        cfg[key] = value


########################################################################
#
# parser configuration
#
########################################################################

# The parser configuration is read when a Grammar-object is instantiated.
# Changes to the configuration value that take place after the
# instantiation of the Grammar-object will not be reflected in the
# Grammar-object. After instantiation, the fields of the Grammar-object
# that reflect the configuration parameters must be manipulated directly
# to change the configuration of a Grammar-object.

# Maximum allowed number of retries after errors where the parser
# would exit before the complete document has been parsed. Should
# not be set too high, because automatic retry works poorly.
# This value does not affect the @resume-directive.
# Default value: 1
CONFIG_PRESET['max_parser_dropouts'] = 1

# The "search window" for finding a reentry-point after a syntax error was
# encountered during parsing. The value of `reentry_search_window` is the
# maximum number of characters lying ahead of the point of failure, where
# a suitable reentry point will be searched. A value smaller than zero
# means that the complete remaining text will be searched. A value of zero
# effectively turns of resuming after error.
# Default value: 10000
CONFIG_PRESET['reentry_search_window'] = 10000

# Turns on tracking of the parsing history. As this slows down parsing,
# it should only be turned on for debugging.
# Default value: False
CONFIG_PRESET['history_tracking'] = False

# Turns on resume notices that add information about where the parsing
# process resumes after an error has been encountered
# Default value: False
CONFIG_PRESET['resume_notices'] = False

# Turns on the left-recursion-handling algorithm. This allows the use
# of left-recursion in grammars, which otherwise would run a recursive
# descent parser into an infinite-loop.
# Default value: True
CONFIG_PRESET['left_recursion'] = True

########################################################################
#
# nodetree configuration
#
########################################################################

# Defines the output format for the serialization of syntax trees.
# Possible values are:
# 'XML'          - output as XML
# 'S-expression' - output as S-expression, i.e. a list-like format
# 'indented'     - compact tree output, i.e. children a represented on
#                  indented lines with no opening or closing tags, brackets
#                  etc.
# 'json'         - output in JSON-format. This is probably the least
#                  readable representation, but useful for serialization, for
#                  example, to return syntax trees from remote procedure calls.
# Default values: "compact" for concrete syntax trees and "XML" for abstract
#                 syntax trees and "S-expression" for any other kind of tree.
_serializations = frozenset({'XML', 'json', 'indented', 'S-expression'})
CONFIG_PRESET['cst_serialization'] = 'S-expression'
CONFIG_PRESET['ast_serialization'] = 'S-expression'
CONFIG_PRESET['default_serialization'] = 'S-expression'
ALLOWED_PRESET_VALUES['cst_serialization'] = _serializations
ALLOWED_PRESET_VALUES['ast_serialization'] = _serializations
ALLOWED_PRESET_VALUES['default_serialization'] = _serializations

# Defines the maximum line length for flattened S-expressions.
# Below this threshold S-expressions will be returned in flattened
# form by DHParser.nodetree.serialize() and other functions
# that use serialize(), like, for example, the reporting functions
# in DHParser.testing.
# Default value: 120
CONFIG_PRESET['flatten_sxpr_threshold'] = 120

# Defines the maximum number of LINES before the "S-expression" serialization
# will switch to a compact output where the closing brackets are placed on
# the same line as the last line of the content.
CONFIG_PRESET['compact_sxpr_threshold'] = 10


# How to treat illegal attribute values when serializing as XML,
# e.g. attr="<". Possible values are:
# 'ignore' - faulty attribute values will be serialized nonetheless
# 'fix'   - attribute values will be corrected, e.g. "<" will be
#           replaced by the respective entity and the like.
# 'lxml'  - attributes values will be corrected and any non-ASCII
#           character will be replaced by a question mark to ensure
#           compatibility with the lxml library.
# 'fail'  - an error will be raised, when an illegal attribute value
#           is encountered while serializing a tree as XML. Illegal
#           attribute values can still be set, though, since they
#           they concern only the XMl-serialization and not the
#           S-expression or JSON serialization.
# Default value = "fail"
CONFIG_PRESET['xml_attribute_error_handling'] = 'fail'
ALLOWED_PRESET_VALUES['xml_attribute_error_handling'] = frozenset({'ignore', 'fix', 'lxml', 'fail'})

########################################################################
#
# general compiler configuration
#
########################################################################

# Defines which syntax tree should be logged during compilation:
# The concrete syntax tree, the abstract syntax tree or both.
# Possible values are {'ast'}, {'cst'} or {'ast', 'cst'}
# Default value: empty set
CONFIG_PRESET['log_syntax_trees'] = frozenset()


########################################################################
#
# ebnf compiler configuration
#
########################################################################

# Carries out static analysis on the the parser tree before parsing starts
# to ensure its correctness. EXPERIMENTAL! Possible values are:
# 'early' - static analysis is carried out by DHParser.ebnf.EBNFCompiler,
#           already. Any errors it revealed will be located in the EBNF
#           source code. This naturally only works for parser that are
#           generated from an EBNF syntax declaration.
# 'late' -  static analysis is carried out when instantiating a Grammar
#           (sub-)class. This works also for parser trees that are
#           handwritten in Python using the parser classes from module
#           `parse`. It slightly slows down instantiation of Grammar
#           classes, though.
# 'none' -  no static analysis at all.
# Default value: "early"
CONFIG_PRESET['static_analysis'] = "early"

# Allows to change the order of the definitions in an EBNF source
# text to minimize the number of forward-declarations in the resulting
# grammar class.
# True  - reordering of definitions is allowed
# False - definitions will not be reordered
# Default value: 'True'
CONFIG_PRESET['reorder_definitions'] = True

# DHParser.ebnf.EBNFCompiler class adds the the EBNF-grammar to the
# docstring of the generated Grammar-class
# Default value: False
CONFIG_PRESET['add_grammar_source_to_parser_docstring'] = False

# Default value for the regular expression by which identifiers for
# parsers that yield anonymous nodes are distinguished from identifiers
# for parsers that yield named nodes. For example, the regular expression
# r'_' catches names with a leading underscore. The default value is a
# regular expression that matches no string whatsoever.
# Default value: r'..(?<=^)'  # never match.
NEVER_MATCH_PATTERN = r'..(?<=^)'
CONFIG_PRESET['default_disposable_regexp'] = NEVER_MATCH_PATTERN


# Default value for implicit insignificant whitespace adjacent to literals.
# Possible values are:
# 'none': no implicit adjacent whitespace:   "text" = `text`
# 'right': implicit whitespace to the right: "text" = `text`~
# 'left': implicit whitespace to the left:   "text" = ~`text`
# 'both': implicit whitespace on both sides: "text" = ~`text`~
CONFIG_PRESET['default_literalws'] = "none"


# Default value for the brand of EBNF that DHParser accepts
# 'fixed'       - Allows to use suffix syntax (?, +, *) as well as classic
#       EBNF-syntax ([], {}). The delimiters are fixed before first use to
#       the DHParser-standard and will not be read from configuration-value
#       "delimiter_set".
# 'classic'     - relatively closest to the ISO-standard, i.e. uses [] and {}
#       for optional and zero or more elements, respectively. Does not allow
#       the ?, +, * suffixes (NOT YET IMPLEMENTED!). Allows the specification
#       of character-ranges within square brackets only with the ordinal
#       unicode numbers, not with the characters itself, i.e. [0x41-0x5A].
#       Delimiters will be configured on first use.
# 'strict'      - allows both classic and regex-like syntax to be mixed, but
#       allows character ranges within square brackets with ordinal values,
#       only. Uses | as delimiter for alternatives.
# 'configurable' - like fixed, but the delimiter constants will be configured
#       from the configuration-value 'delimiter_set' (see below).
# 'heuristic'   - the most liberal mode, allows about everything. However,
#       because it employs heuristics to distinguish ambiguous cases, it
#       may lead to unexpected errors and require the user to resolve the
#       ambiguities
# 'regex-like'  - similar to regular expression syntax, allows ?, +, *
#       suffixes for optional, one or more repetitions, zero or more
#       repetitions, but not {} or []. Allows character-ranges within
#       square bracket in any form.
# 'peg-like' - like regex-like, but uses / instead of | for the
#       alternative-parser. Does not allow regular expressions between, i.e.
#       / ... / within the EBNF-code!
# Default value: "fixed"
CONFIG_PRESET['syntax_variant'] = 'fixed'
ALLOWED_PRESET_VALUES['syntax_variant'] = frozenset({
    'fixed',
    'classic',
    'strict',
    'configurable',
    'heuristic',
    'regex-like',
    'peg-like'})

# Set of delimiters when using the 'configurable'-Grammar
CONFIG_PRESET['delimiter_set'] = {
    'DEF':        '=',
    'OR':         '|',
    'AND':        '',
    'ENDL':       '',
    'RNG_OPEN':   '{',
    'RNG_CLOSE':  '}',
    'RNG_DELIM':  ',',
    'TIMES':      '*',
    'RE_LEADIN':  '/',
    'RE_LEADOUT': '/',
    'RE_CORE': r'(?:(?<!\\)\\(?:/)|[^/])*',
    # RE_LEADOUT:               ^    ^
    'CH_LEADIN':  '0x'
}


########################################################################
#
# compiler command and server configuration
#
########################################################################

# If parser- or compiler-script is called with several input files
# (batch-processing), the files will be processed in parallel via the
# Python multiprocessing module
# Default value: True
CONFIG_PRESET['batch_processing_parallelization'] = True

# Maximum allowed source size for remote procedure calls (including
# parameters) in server.Server. The default value is rather large in
# order to allow transmitting complete source texts as parameter.
# Default value: 4 MB
CONFIG_PRESET['max_rpc_size'] = 4 * 1024 * 1024

# Add a header to JSON-RPC requests of responses.
# see: https://microsoft.github.io/language-server-protocol/specification#header-part
# Default value: True
CONFIG_PRESET['jsonrpc_header'] = True

# Default host name or IP-address for the compiler server. Should usually
# be localhost (127.0.0.1)
# Default value: 127.0.0.1.
CONFIG_PRESET['server_default_host'] = "127.0.0.1"

# Default port number for the compiler server.
# Default value: 8888
CONFIG_PRESET['server_default_port'] = 8888


########################################################################
#
# debugging support configuration
#
########################################################################

# Turn on (costly) debugging functionality for any of the respective
# modules or subsystems.
# Default value: False
CONFIG_PRESET['debug_compiler'] = False

# Makes DHParser.dsl.grammar_provider() write generated Python code to
# the log-file (if logging is on) or to the console (if logging is off)
# Default value: '' (empty string, i.e. no log)
CONFIG_PRESET['compiled_EBNF_log'] = ''

# Defines the kind of threading that `toolkit.instantiate_executor()`
# will allow. Possible values are:
# 'multitprocessing" - Full multiprocessing will be allowed.
# 'multithreading' -   A ThreadPoolExecutor will be substituted for any
#         ProcessPoolExecutor.
# 'singlethread' -     A SingleThreadExecutor will be substituted for
#         any ProcessPoolExecutor or ThreadPoolExecutor.
# 'commandline' -      If any of the above is specified on the command
#         line with two leading minus-signs, e.g. '--singlethread'
#
CONFIG_PRESET['debug_parallel_execution'] = 'commandline'

########################################################################
#
# logging support configuration
#
########################################################################

# Log-directory. An empty string means that writing of log files is
# turned off, no matter what value the other log-configuration
# parameters have. The only exception is "echo logging" to the terminal!
# Default value: '' (all logging is turned off)
CONFIG_PRESET['log_dir'] = ''

# Log server traffic (requests and responses)
# Default value: False
CONFIG_PRESET['log_server'] = False

# Echo server log messages on the terminal. Works only with tcp-server,
# will be ignored by streaming server.
# Default value: False
CONFIG_PRESET['echo_server_log'] = False

# Maximum size (i.e.) number of parsing steps before the parsing ended
# that are logged to the html-parsing-history-file
# Default value: 10000
CONFIG_PRESET['log_size_threshold'] = 10000


########################################################################
#
# testing framework configuration
#
########################################################################

# Allows (coarse-grained) parallelization for running tests via the
# Python multiprocessing module
# Default value: True
CONFIG_PRESET['test_parallelization'] = True

# Employs heuristics to allow lookahead-based parsers to pass unit-test
# in case a reported error may only be due to the fact that the test
# string a) either did include a substring for a lookahead check, the
# was then left over when parsing stopped (which would usually result
# in a "parser stopped before end"-error) or b) did not include a
# substring expected by a lookahead check as this is not part of the
# sequence that the tested parser should return in form of a concrete
# syntax-tree. (This would otherwise result in a 'parser did not match'-
# error.)
# Beware that a) these heuristics can fail, so that certain
# test-failures may fail to be reported and b) the abstract-syntax-trees
# resulting from parsers that contain lookahead checks may have a
# structure that would not occur outside the testing-environment.
# Default value: True
CONFIG_PRESET['test_suppress_lookahead_failures'] = True


########################################################################
#
# decprecation warnings
#
########################################################################

# Determines what happens when functions decorated as deprecated
# are called. Possible values are:
# "warn" - print ar warning, the first time the deprecated function
#          is called
# "fail" - raise a DeprecationWarning, the first time the deprecated
#          function is called
CONFIG_PRESET['deprecation_policy'] = 'warn'
ALLOWED_PRESET_VALUES['deprecation_policy'] = frozenset({'warn', 'fail'})

