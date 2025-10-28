# configuration.py - default configuration values for DHParser
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
Module "configuration.py" defines the default configuration for DHParser.

The best way to change the configuration or to add custom configurations
for your own project is to place a [DSL-name]config.ini-file in the main-directory
of your DSL-project that is the directory where your parsing and
compilation-scripts reside. This configuration can be overwritten by
a configuration-file with the same name in the current working-directory
if different configurations for different workspaces are needed.

The configuration values can be read and changed while running via the
get_config_value() and set_config_value()-functions. However, the functions
only affect the configuration values for the current thread. Changes will
not be visible to any spawned threads or processes.

In order to change the configuration values for spawned processes or threads,
the presets can also be overwritten before(!) spawning any parsing processes
with:

    access_presets()
    set_preset_value and get_preset_value()
    finalize_presets()

Unless configuration-files are used (see above), the recommended way to use
a different configuration in any custom code using
DHParser is to use the second method, i.e. to overwrite the values for which
this is desired in the CONFIG_PRESET dictionary right after the start of the
program and before any DHParser-function is invoked.
"""

from __future__ import annotations

import sys
from typing import Dict, Any, Iterable, List

__all__ = ('CONFIG_PRESET',
           'ALLOWED_PRESET_VALUES',
           'validate_value',
           'access_presets',
           'is_accessing_presets',
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
           'add_config_values',
           'dump_config_data',
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


access_lock = None  # = threading.Lock()


def get_access_lock():  # -> threading.Lock()
    """Return a global threading.Lock, create it upon first usage."""
    global access_lock
    if access_lock is None:
        import threading
        lock = threading.Lock()
        if access_lock is None:
            access_lock = lock
    return access_lock


def validate_value(key: str, value: Any):
    """Raises a Type- or ValueError, if the values of variable `key` are
    restricted to a certain set or range and the value does not lie within
    this set or range."""
    global ALLOWED_PRESET_VALUES
    allowed = ALLOWED_PRESET_VALUES.get(key, None)
    if allowed:
        if isinstance(allowed, tuple):
            if not isinstance(value, (int, float)):
                raise TypeError(f'Value "{value}" is not an int or float as required '
                                f'for "{key}"!')
            elif not allowed[0] <= value <= allowed[1]:
                raise ValueError(f'Value "{value}" for "{key}" does not lie within the '
                                 f'range from {allowed[0]} to {allowed[1]} (included)!')
        else:
            if not isinstance(value, str) and isinstance(value, Iterable):
                for item in value:
                    if item not in allowed:
                        raise ValueError(f'Item "{item}" for "{key}" is not one of the '
                                         f'allowed values {str(sorted(list(allowed)))[1:-1]}!')
            elif value not in allowed:
                raise ValueError(f'Value "{value}" for "{key}" is not one of '
                                 f'the allowed values {str(sorted(list(allowed)))[1:-1]}!')


def get_forkserver_pid():
    import multiprocessing, os
    process = multiprocessing.current_process()
    if process.daemon or getattr(process, '_inheriting', False):
        forkserver_pid = os.getppid()
    else:
        import concurrent.futures
        with concurrent.futures.ProcessPoolExecutor(1) as ex:
            forkserver_pid = ex.submit(os.getppid).result()
    return forkserver_pid


def os_getpid(mp_method = None):
    import os
    if sys.version_info < (3, 14, 0) \
            or CONFIG_PRESET['multicore_pool'] == 'ProcessPool':
        # TODO chose this path also, if this has not been called inside an InterpreterPool!!!
        import multiprocessing
        if mp_method is None:
            mp_method = multiprocessing.get_start_method()
        if mp_method == "forkserver":
            return get_forkserver_pid()
    return os.getpid()


def get_syncfile_path(mp_method: str) -> str:
    import os
    import tempfile
    syncfile_path = CONFIG_PRESET['syncfile_path']
    if not syncfile_path:
        for getpid in (os.getpid, os.getppid, os_getpid):
            pid = getpid()
            syncfile_path = os.path.join(tempfile.gettempdir(), f'DHParser_{pid}.cfg')
            if os.path.exists(syncfile_path):
                break
    return syncfile_path


def access_presets():
    """
    Allows read and write access to preset values via `get_preset_value()`
    and `set_preset_value()`. Any call to `access_presets()` should be
    matched by a call to `finalize_presets()` to ensure propagation of
    changed preset-values to spawned processes. For an explanation why,
    see: https://docs.python.org/3/library/multiprocessing.html#the-spawn-and-forkserver-start-methods
    """
    global ACCESSING_PRESETS, CONFIG_PRESET
    if ACCESSING_PRESETS:
        raise AssertionError('Presets are already being accessed! '
                             'Calls to access_presets() cannot be nested.')
    ACCESSING_PRESETS = True
    import multiprocessing
    mp_method = multiprocessing.get_start_method()
    if mp_method != 'fork' or CONFIG_PRESET['multicore_pool'] == 'InterpreterPool':
        import os
        import pickle
        syncfile_path = get_syncfile_path(mp_method)
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


def is_accessing_presets() -> bool:
    """Checks if presets are currently open for changes."""
    global ACCESSING_PRESETS
    return ACCESSING_PRESETS


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
        mp_method = multiprocessing.get_start_method()
        if mp_method != 'fork' or CONFIG_PRESET['multicore_pool'] == 'InterpreterPool':
            import atexit
            import os
            import pickle
            syncfile_path = get_syncfile_path(mp_method)
            if fail_on_error:
                    if not os.path.exists(syncfile_path):
                        raise AssertionError(
                            "finalize_presets() can only be called from the main process!")
            with open(syncfile_path, 'wb') as f:
                existing_syncfile = CONFIG_PRESET['syncfile_path']
                CONFIG_PRESET['syncfile_path'] = syncfile_path
                if existing_syncfile != syncfile_path:
                    atexit.register(remove_cfg_tempfile, syncfile_path)
                pickle.dump(CONFIG_PRESET, f)
        PRESETS_CHANGED = False
    ACCESSING_PRESETS = False
    # if THREAD_LOCALS is not None:
    #     THREAD_LOCALS.config = {}  # reset THREAD_LOCALS


RENAMED_KEYS = {
    'ast_serialization': 'AST_serialization',
    'cst_serialization': 'CST_serialization'
}


def set_preset_value(key: str, value: Any, allow_new_key: bool=False):
    global CONFIG_PRESET, ACCESSING_PRESETS, PRESETS_CHANGED
    if not ACCESSING_PRESETS:
        raise AssertionError('Presets must be made accessible with access_presets() first, '
                             'before they can be set!')
    if not allow_new_key:
        oldkey = key
        if key not in CONFIG_PRESET:  key = RENAMED_KEYS.get(key, key)
        if key not in CONFIG_PRESET:
            raise ValueError(
                '"%s" is not a valid config variable. Use "allow_new_key=True" to add  '
                ' new variables or choose one of %s' % (key, list(CONFIG_PRESET.keys())))
        elif oldkey != key:
            print(f'Deprecation Warning: Key {oldkey} has been renamed to {key}!')
    validate_value(key, value)
    if key == 'multicore_pool':
        raise AssertionError('Preset of "multicore_pool" can only be changed with a '
                              'configuration-file, but not at runtime!')
    CONFIG_PRESET[key] = value
    set_config_value(key, value)
    PRESETS_CHANGED = True


def ingest_config_data(config, sources=''):
    """Ingests configuration-data from a Python-STL
    configparser.ConfigParser-object."""
    errors = []
    access_presets()
    for section in config.sections():
        try:
            if section.lower() == "dhparser":
                for variable, value in config[section].items():
                    set_preset_value(f"{variable}", eval(value))
            else:
                for variable, value in config[section].items():
                    set_preset_value(f"{section}.{variable}", eval(value),
                                     allow_new_key=True)
        except ValueError as e:
            errors.append(' '.join(e.args))
    finalize_presets()
    if errors:
        sources = f' files: {sources}'
        raise ValueError(f"\n\nErrors found in configuration{sources}:\n\n"
                         + '\n'.join(errors))


def read_local_config(ini_filename: str) -> List[str]:
    """Reads a local config file(s) and updates the presets
    accordingly. All config-files with the same basename
    (i.e. name without path) as
    "ini_filename" will subsequently be read from these
    directories and be processed in the same order, which
    means config-values in files processed later will
    overwrite config-values from earlier processed files:

    1. script-directory
    2. exact path of "ini_filename"
    3. User's config-file directory, e.g. ~/.config/basename/
    4. current working directory

    This configuration file must be in the .ini-file format
    so that it can be parsed with "configparser" from the
    Python standard library. Any key,value-pair under the
    section "DHParser" will directly be transferred to the
    configuration presets. For other sections, the section
    name will be added as a qualifier to the key:
    "section.key". Thus, only values under the "DHParser"
    section modify the DHParser-configuration while
    configuration parameters unter other sections are
    free to be evaluated by the calling script and cannot
    interfere with DHParser's configuration.

    :param ini_filename: the file path and name of the configuration
        file.
    :returns:  the file paths of the actually read .ini-files
        or the empty string if no .ini-file with the given
        name could be found either at the given path, in
        the current working directory or in the calling
        script's path.
    """
    import configparser
    import os
    # collect config files
    cfg_files = []
    basename = os.path.basename(ini_filename)
    # first, add path in the script-directory
    script_path = os.path.abspath(getattr(sys.modules['__main__'], '__file__', '') or '.')
    cfg_filename = os.path.join(os.path.dirname(script_path), basename)
    if os.path.isfile(cfg_filename): cfg_files.append(cfg_filename)
    # then, add given path
    if ini_filename not in cfg_files and os.path.isfile(ini_filename):
        cfg_files.append(ini_filename)
    # then, add cfg-file from the user's config directory
    appname = os.path.splitext(basename)[0]
    cfg_filename = os.path.join(os.path.expanduser('~'), '.config', appname, 'config.ini')
    if os.path.isfile(cfg_filename):
        if cfg_filename not in cfg_files:
            cfg_files.append(cfg_filename)
    else:
        cfg_filename = os.path.join(os.path.expanduser('~'), '.config', appname, basename)
        if cfg_filename not in cfg_files and os.path.isfile(cfg_filename):
            cfg_files.append(cfg_filename)
    # finally, add cfg-file from the current working directory
    if basename not in cfg_files and os.path.isfile(basename):
        cfg_files.append(basename)

    # Now, read and process all config files in this order
    config = configparser.ConfigParser()
    config.optionxform = lambda optionstr: optionstr
    successfully_read = config.read(cfg_files, encoding='utf-8')
    if successfully_read:
        ingest_config_data(config, ', '.join(cfg_files))
    return successfully_read


def read_config_string(ini_string: str):
    """Reads configuration data in the .ini-file format from
    a string. See :py:func:`read_local_config` for more details."""
    import configparser
    config = configparser.ConfigParser()
    config.optionxform = lambda optionstr: optionstr
    config.read_string(ini_string)
    ingest_config_data(config)


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
        import threading
        THREAD_LOCALS = threading.local()  # TODO: Use ContextVars, here!!!
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
    with get_access_lock():
        cfg = _config_dict()
        try:
            return cfg[key]
        except KeyError:
            access_presets()
            # value = get_preset_value(key, default)
            for k, v in CONFIG_PRESET.items():
                if k not in cfg:
                    cfg[k] = v
            finalize_presets()
            if default is NO_DEFAULT:
                value = cfg[key]
            else:
                value = cfg.get(key, default)
            return value


def get_config_values(key_pattern: str = "*", *additional_patterns) -> Dict:
    """Returns a dictionary of all configuration entries that match
    `key_pattern`."""
    access_presets()
    presets = get_preset_values(key_pattern)
    for pattern in additional_patterns:
        presets.update(get_preset_values(pattern))
    finalize_presets()
    import fnmatch
    with get_access_lock():
        cfg = _config_dict()
        cfg_values = dict()
        for pattern in (key_pattern, *additional_patterns):
            if pattern == "*":
                cfg_values.update(cfg)
            else:
                cfg_values.update({key: value for key, value in cfg.items()
                                   if fnmatch.fnmatchcase(key, key_pattern)})
        presets.update(cfg_values)
        cfg.update(presets)
    return presets


def set_config_value(key: str, value: Any, allow_new_key: bool = False):
    """
    Changes a configuration value thread-safely. The configuration
    value will be set only for the current thread. In order to
    set configuration values for any new thread, add the key and value
    to CONFIG_PRESET, before any thread accessing config-values is started.
    :param key:    the key (an immutable, usually a string)
    :param value:  the value
    """
    with get_access_lock():
        cfg = _config_dict()
        if not allow_new_key:
            oldkey = key
            if key not in CONFIG_PRESET:  key = RENAMED_KEYS.get(key, key)
            if key not in CONFIG_PRESET:
                if key not in cfg:
                    raise ValueError(
                        '"%s" is not a valid config variable. Use "allow_new_key=True" to '
                        'add new variables or choose one of %s' % (key, list(cfg.keys())))
            elif oldkey != key:
                print(f'Deprecation Warning: Key {oldkey} has been renamed to {key}!')
        validate_value(key, value)
        cfg[key] = value


def add_config_values(configuration: dict):
    """
    Adds (or overwrites) new configuration values.
    :param configuration: additional configuration values
    """
    with get_access_lock():
        cfg = _config_dict()
        cfg.update(configuration)


def dump_config_data(*key_patterns, use_headings: bool = True) -> str:
    """Returns the configuration variables the name of which matches one of the
    key_patterns config.ini-string."""
    if key_patterns:
        data = get_config_values(key_patterns[0], *key_patterns[1:])
        if data:
            results = []
            last_prefix = None
            for k, v in data.items():
                i = k.find('.')
                prefix = k[:i + 1]
                name = k[i + 1:] if use_headings else k
                if prefix != last_prefix:
                    results.append('')
                    if use_headings:
                        results.append(f'[{prefix[:-1]}]' if prefix else "[DHParser]")
                    last_prefix = prefix
                results.append(f'{name} = {repr(v)}')
            if not results[0]:  del results[0]
            results.append('')
            return '\n'.join(results)
    return ''


########################################################################
#
# system configuration
#
########################################################################

# Defines which kind of multicore parallelization shall be used:
# Either "ProcessPool" or "InterpreterPool". The latter is only available
# when Python-version is greater or equal 3.14. If "InterpreterPool"
# is specified but the Python version is smaller than 3.14, "ProcessPool"
# will automatically be used as a fallback option.
# Default value: "InterpreterPool"
ALLOWED_PRESET_VALUES['multicore_pool'] = frozenset({'ProcessPool',
                                                     'InterpreterPool'})
CONFIG_PRESET['multicore_pool'] = "InterpreterPool"


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
CONFIG_PRESET['reentry_search_window'] = 50000

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

# Warn about pending infinite loops which would occur if a repeating
# parser like "zero or more" calls another parser that matches but
# does not move the location pointer forward, i.e. { /(?=.)|$/ }.
# Theoretically, this parser would be called at the same place again
# and again forever. In practice, DHParser recognizes this situation
# and breaks the pending infinite loop. Since this situation usually
# is the result of a poorly designed inner parser, a warning can
# be emitted.
# Default value: False
CONFIG_PRESET['infinite_loop_warning'] = False

########################################################################
#
# nodetree configuration
#
########################################################################

# Defines the output format for the serialization of syntax trees.
# Possible values are:
# 'XML'          - output as XML
# 'HTML'         - like XML but enclosed in the body of a minimal
#                  HTML-page.
# 'S-expression' - output as S-expression, i.e. a list-like format
# 'SXML'         - a variant of S-expression differing in how attributes are
#                  rendered, e.g. (@ attr "value") instead of `(attr "value")
# 'tree'         - compact tree output, i.e. children a represented on
#                  indented lines with no opening or closing tags, brackets
#                  etc. 'indented' can be used as a synonym for 'tree'
# 'json'         - output in JSON-format. This is probably the least
#                  readable representation, but useful for serialization, for
#                  example, to return syntax trees from remote procedure calls.
# 'dict.json'    - a different, and often more readable flavor of JSON, where
#                  dicts are used whenever possible. Please be aware that this
#                  goes beyond the JSON-sepcification which does not know
#                  ordered dicts! This could result in the misrepresentation
#                  of data by JSON parsers that are not aware of the order
#                  of entries in dictionaries. (e.g. Python < 3.6)
# 'ndst'         - nodetree-syntax-tree: a JSON-variant following the
#                  unist-Specification (https://github.com/syntax-tree/unist).
# 'xast'         - a JSON-Variant for XML-syntax-trees following the
#                  xast-Specification (https://github.com/syntax-tree/xast).
# Default values: "compact" for concrete syntax trees and "XML" for abstract
#                 syntax trees and "sxpr" (read "S-Expression") for any other
#                 kind of tree.
_serializations = frozenset({'XML', 'HTML', 'json', 'dict.json', 'indented', 'tree',
                             'S-expression', 'sxpr', 'SXML', 'SXML1', 'SXML2',
                             'xast', 'ndst'})
CONFIG_PRESET['CST_serialization'] = ''
CONFIG_PRESET['AST_serialization'] = ''
CONFIG_PRESET['default_serialization'] = 'sxpr'
ALLOWED_PRESET_VALUES['CST_serialization'] = _serializations | {''}
ALLOWED_PRESET_VALUES['AST_serialization'] = _serializations | {''}
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
#           concern only the XMl-serialization and not the
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
# Possible values are {'AST'}, {'CST'} or {'AST', 'CST'}
# Default value: empty set
CONFIG_PRESET['log_syntax_trees'] = frozenset()


########################################################################
#
# ebnf compiler configuration
#
########################################################################

# Carries out static analysis on the parser tree before parsing starts
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

# DHParser.ebnf.EBNFCompiler class adds the EBNF-grammar to the
# docstring of the generated Grammar-class
# Default value: False
CONFIG_PRESET['add_grammar_source_to_parser_docstring'] = False

# Default value for the regular expression by which identifiers for
# parsers that yield anonymous nodes are distinguished from identifiers
# for parsers that yield named nodes. For example, the regular expression
# r'_' catches names with a leading underscore. The default value is a
# regular expression that matches no string whatsoever.
# Default value: r'$.'  # never match.
NEVER_MATCH_PATTERN = r'$.'
CONFIG_PRESET['default_disposable_regexp'] = NEVER_MATCH_PATTERN


# Default value for implicit insignificant whitespace adjacent to literals.
# Possible values are:
# 'none': no implicit adjacent whitespace:   "text" = `text`
# 'right': implicit whitespace to the right: "text" = `text`~
# 'left': implicit whitespace to the left:   "text" = ~`text`
# 'both': implicit whitespace on both sides: "text" = ~`text`~
CONFIG_PRESET['default_literalws'] = "none"


# Default value for the brand of EBNF that DHParser accepts
# 'fixed', 'dhparser' - Allows to use suffix syntax (?, +, *) as well as classic
#       EBNF-syntax ([], {}). The delimiters are fixed before first use to
#       the DHParser-standard and will only be read once from
#       configuration-value "delimiter_set" upon first usage.
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
#       from the configuration-value 'delimiter_set' (see below) each
#       time the grammar object is requested with DHParser.ebnf.get_ebnf_grammar()
#       or DHParser.ebnf.parse_ebnf().
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
# Default value: "dhparser"
CONFIG_PRESET['syntax_variant'] = 'dhparser'
ALLOWED_PRESET_VALUES['syntax_variant'] = frozenset({
    'dhparser',
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

# Switches different kinds of optimization of the EBNF-compiler on.
# Optimaztion is done by substituting compound parsers by SmartRE-parsers
# when this is possible. Theoretically, this is everywhere where
# no recursion occurs. In practice this is done only in (some of the)
# cases where no (non-disposable) symbols are referred.
# Default value: empty frozen set
ALLOWED_PRESET_VALUES['optimizations'] = frozenset({
    'literal',
    'lookahead',
    'alternative',
    'rearrange_alternative',  # this is also implied by 'alternative'
    'sequence'})
CONFIG_PRESET['optimizations'] = frozenset()
    # {'literal', 'lookahead', 'alternative', 'sequence'})


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

# Maximum chunk size when using multiple processes for batch processing
# see: file:///usr/share/doc/python/html/library/concurrent.futures.html#concurrent.futures.Executor.map
# Higher values can lead to more efficient multiprocessing, but can
# also increase the time until a process completes.
# Values must be greater or equal one.
# Default value: 4
CONFIG_PRESET['batch_processing_max_chunk_size'] = 4

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
# 'multitcore' - Full multicore parallel execution will be allowed.
# 'multiprocessing' - DEPRECATED alias for 'multicore'
# 'multithreading' -   A ThreadPoolExecutor will be substituted for any
#         ProcessPoolExecutor.
# 'singlethread' -     A SingleThreadExecutor will be substituted for
#         any ProcessPoolExecutor or ThreadPoolExecutor.
# 'commandline' -      If any of the above is specified on the command
#         line with two leading minus-signs, e.g. '--singlethread'
#
ALLOWED_PRESET_VALUES['debug_parallel_execution'] = frozenset({
    'multicore', 'multiprocessing', 'multithreading', 'singlethread', 'commandline'})
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

# Skips the preprocessor stage when running test. This can be helpful
# a) when running tests on sub-parsers, in case that the preprocessor
# cannot deal with snippets which do not represent full documents or
# b) when you'd like to keep preprocessor matters out of the tests.
# 'test_skip_preprocessor' is best 
# Default value: False
CONFIG_PRESET['test_skip_preprocessor'] = False

########################################################################
#
# deprecation warnings
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

