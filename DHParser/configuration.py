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

from typing import Dict, Any

__all__ = ('access_presets',
           'finalize_presets',
           'THREAD_LOCALS',
           'access_thread_locals',
           'get_config_value',
           'set_config_value',
           'XML_SERIALIZATION',
           'SXPRESSION_SERIALIZATION',
           'INDENTED_SERIALIZATION',
           'JSON_SERIALIZATION',
           'SERIALIZATIONS')


########################################################################
#
# multiprocessing-safe preset- and configuration-handling
#
########################################################################


CONFIG_PRESET = dict()  # type: Dict[str, Any]
CONFIG_PRESET['syncfile_path'] = ''
THREAD_LOCALS = None


def get_syncfile_path(pid: int) -> str:
    import os
    import tempfile
    return os.path.join(tempfile.gettempdir(), 'DHParser_%i.cfg' % pid)


def access_presets() -> Dict[str, Any]:
    """
    Returns a dictionary of presets for configuration values.
    If any preset values are changed after calling `access_presets()`,
    `finalize_presets()` should be called to make sure that processes
    spawned after changing the preset values, will be able to read
    the changed values.
    See: https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
    """
    import multiprocessing
    global CONFIG_PRESET
    if not CONFIG_PRESET['syncfile_path'] and multiprocessing.get_start_method() != 'fork':
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
            assert preset['syncfile_path'] == syncfile_path, \
                'Conflicting syncfile paths %s != %s' % (preset['syncfile_path'], syncfile_path)
            CONFIG_PRESET = preset
        except FileNotFoundError:
            pass
        finally:
            if f is not None:
                f.close()
    return CONFIG_PRESET


def remove_cfg_tempfile(filename: str):
    import os
    os.remove(filename)


def finalize_presets():
    """
    Finalizes changes of the presets of the configuration values.
    This method should always be called after changing preset values to
    make sure the changes will be visible to processes spawned later.
    """
    import atexit
    import multiprocessing
    import os
    import pickle
    global CONFIG_PRESET
    if multiprocessing.get_start_method() != 'fork':
        syncfile_path = get_syncfile_path(os.getpid())
        existing_syncfile = CONFIG_PRESET['syncfile_path']
        assert ((not existing_syncfile or existing_syncfile == syncfile_path)
                and (not os.path.exists((get_syncfile_path(os.getppid()))))), \
            "finalize_presets() can only be called from the main process!"
        with open(syncfile_path, 'wb') as f:
            CONFIG_PRESET['syncfile_path'] = syncfile_path
            if existing_syncfile != syncfile_path:
                atexit.register(remove_cfg_tempfile, syncfile_path)
            pickle.dump(CONFIG_PRESET, f)
    # if THREAD_LOCALS is not None:
    #     THREAD_LOCALS.config = {}  # reset THREAD_LOCALS


def access_thread_locals() -> Any:
    """Intitializes (if not done yet) and returns the thread local variable
    store. (Call this function before using THREAD_LOCALS.
    Direct usage of THREAD_LOCALS is DEPRECATED!)
    """
    global THREAD_LOCALS
    if THREAD_LOCALS is None:
        import threading
        THREAD_LOCALS = threading.local()
    return THREAD_LOCALS


def get_config_value(key: str) -> Any:
    """
    Retrieves a configuration value thread-safely.
    :param key:  the key (an immutable, usually a string)
    :return:     the value
    """
    THREAD_LOCALS = access_thread_locals()
    try:
        cfg = THREAD_LOCALS.config
    except AttributeError:
        THREAD_LOCALS.config = dict()
        cfg = THREAD_LOCALS.config
    try:
        return cfg[key]
    except KeyError:
        CONFIG_PRESET = access_presets()
        value = CONFIG_PRESET[key]
        THREAD_LOCALS.config[key] = value
        return value


def set_config_value(key: str, value: Any):
    """
    Changes a configuration value thread-safely. The configuration
    value will be set only for the current thread. In order to
    set configuration values for any new thread, add the key and value
    to CONFIG_PRESET, before any thread accessing config values is started.
    :param key:    the key (an immutable, usually a string)
    :param value:  the value
    """
    THREAD_LOCALS = access_thread_locals()
    try:
        cfg = THREAD_LOCALS.config
    except AttributeError:
        THREAD_LOCALS.config = dict()
        cfg = THREAD_LOCALS.config
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

# Flattens anonymous nodes, by removing the node and adding its children
# to the parent node in place of the removed node. This is a very useful
# optimization that should be turned on except for learning or teaching
# purposes, in which case a concrete syntax tree that more diligently
# reflects the parser structure may be helpful.
# Default value: True
CONFIG_PRESET['flatten_tree'] = True

# Maximum depth of parser's left recursion
# This limit should not be set to high, because the left recursion
# catching algorithm can take exponential time, and, of course,
# because of python's recursion depth limit
# Left recursion handling can be turned off by setting this value to zero
# Default value: 5
CONFIG_PRESET['left_recursion_depth'] = 5

# Maximum allowed number of retries after errors where the parser
# would exit before the complete document has been parsed. Should
# not be set too high, because automatic retry works poorly.
# This value does not affect the @resume-directive.
# Default value: 3
CONFIG_PRESET['max_parser_dropouts'] = 1

# The "search window" for finding a reentry-point after a syntax error was
# encountered during parsing. The value of `reentry_search_window` is the
# maximum number of characters lying ahead of the point of failure, where
# a suitable reentry point will be searched.
# A value smaller or equal than zero means that the complete remaining
# text will be searched.
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


########################################################################
#
# syntaxtree configuration
#
########################################################################

# Defines the output format for the serialization of syntax trees.
# Possible values are:
# 'XML'          - output as XML
# 'S-expression' - output as S-expression, i.e. a list-like format
# 'compact'      - compact tree output, i.e. children a represented on
#                  indented lines with no opening or closing tags, brackets
#                  etc.
# 'smart'        - serialize as S-expression if the S-expression fits on
#                  one line (see 'flatten_sxpr_threshold'), otherwise
#                  serialize as compact tree output
# 'json'         - output in JSON-format. This is probably the least
#                  readable representation, but useful for serialization, for
#                  example, to return syntax trees from remote procedure calls.
# Default values: "compact" for concrete syntax trees and "XML" for abstract
#                 syntax trees and "S-expression" for any other kind of tree.
XML_SERIALIZATION = "XML"
JSON_SERIALIZATION = "json"
INDENTED_SERIALIZATION = "indented"
SXPRESSION_SERIALIZATION = "S-expression"

SERIALIZATIONS = frozenset({XML_SERIALIZATION,
                            JSON_SERIALIZATION,
                            INDENTED_SERIALIZATION,
                            SXPRESSION_SERIALIZATION,})

CONFIG_PRESET['cst_serialization'] = SXPRESSION_SERIALIZATION
CONFIG_PRESET['ast_serialization'] = SXPRESSION_SERIALIZATION
CONFIG_PRESET['default_serialization'] = SXPRESSION_SERIALIZATION

# Defines the maximum line length for flattened S-expressions.
# Below this threshold S-expressions will be returned in flattened
# form by DhParser.syntaxtree.serialize() and other functions
# that use serialize(), like, for example, the reporting functions
# in DHParser.testing.
# Default value: 120
CONFIG_PRESET['flatten_sxpr_threshold'] = 120

# Defines the maximum number of LINES before the "smart" serialization
# will switch from S-expression output to compact output
CONFIG_PRESET['compact_sxpr_threshold'] = 25


########################################################################
#
# general compiler configuration
#
########################################################################

# Defines which syntax tree should be logged during compilation:
# The concrete syntax tree, the abstract syntax tree or both.
# Possible values are {'ast'}, {'cst'} or {'ast', 'cst'}
# Default value: empty set
CONFIG_PRESET['log_syntax_trees'] = set()


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
# Default value: "none"
CONFIG_PRESET['static_analysis'] = "early"

# DHParser.ebnfy.EBNFCompiler class adds the the EBNF-grammar to the
# docstring of the generated Grammar-class
# Default value: False
CONFIG_PRESET['add_grammar_source_to_parser_docstring'] = False

# Default value for the regular expression by which identifiers for
# parsers that yield anonymous nodes are distinguished from identifiers
# for parsers that yield named nodes. For example, the regular expression
# r'_' catches names with a leading underscore. The default value is a
# regular expression that matches no string whatsoever.
# Default value: r'..(?<=^)'  # never match.
CONFIG_PRESET['default_anonymous_regexp'] = r'..(?<=^)'


# Default value for implicit insignificant whitespace adjacent to literals.
# Possible values are:
# 'none': no implicit adjacent whitespace:   "text" = `text`
# 'right': implicit whitespace to the right: "text" = `text`~
# 'left': implicit whitespace to the left:   "text" = ~`text`
# 'both': implicit whitespace on both sides: "text" = ~`text`~
CONFIG_PRESET['default_literalws'] = "none"


# Default value for the brand of EBNF that DHParser accepts
# 'classic'     - relatively closest to the ISO-standard, i.e. uses [] and {}
#       for optional and zero or more elements, respectively. Does not allow
#       the ?, +, * suffixes. Allows the specification of character-ranges
#       within square brackets only with the ordinal unicode numbers,
#       not with the characters itself, i.e. [0x41-0x5A]
# 'regex-like'  - similar to regular expression syntax, allows ?, +, *
#       suffixes for optional, one or more repetitions, zero or more
#       repetitions, but not {} or []. Allows character-ranges within
#       square bracket in any form.
# 'peg-like' - like regex-like, but uses / instead of | for the
#       alternative-parser. Does not allow regular expressions between, i.e.
#       / ... / within the EBNF-code!
# 'strict'      - allows both classic and regex-like syntax to be mixed, but
#       allows character ranges within square brackets with oridinal values,
#       only. Uses | as delimiter for alternatives.
# 'heuristic'   - the most liberal mode, allows about everything. However,
#       because it employs heuristics to distinguish ambiguous cases, it
#       may lead to unexcpeted errors and require the user to resolve the
#       ambiguieties

EBNF_CLASSIC_SYNTAX = "classic"
EBNF_ANY_SYNTAX_STRICT = "strict"
EBNF_ANY_SYNTAX_HEURISTICAL = "heuristic"
EBNF_REGULAR_EXPRESSION_SYNTAX = "regex-like"
EBNF_PARSING_EXPRESSION_GRAMMAR_SYNTAX = "peg-like"

CONFIG_PRESET['syntax_variant'] = EBNF_ANY_SYNTAX_STRICT


########################################################################
#
# compiler server configuration
#
########################################################################

# Maximum allowed source size for reomote procedure calls (including
# parameters) in server.Server. The default value is rather large in
# order to allow transmitting complete source texts as parameter.
# Default value: 4 MB
CONFIG_PRESET['max_rpc_size'] = 4 * 1024 * 1024

# Add a header to JSON-RPC requests of responses.
# see: https://microsoft.github.io/language-server-protocol/specification#header-part
# Default value: True
CONFIG_PRESET['jsonrpc_header'] = True

# Defaut host name or IP-adress for the compiler server. Should usually
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

# Echo server log messages on the terminal.
# Default value: False
CONFIG_PRESET['echo_server_log'] = False


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
CONFIG_PRESET['test_supress_lookahead_failures'] = True
