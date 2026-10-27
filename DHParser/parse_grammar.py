# parse_grammar.py - grammar class, i.e. hub object for parser hierarchy
#
# Copyright 2026  by Eckhart Arnold (arnold@badw.de)
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
Module parse_grammar defines the class :py:class:`Grammar` which
serves as a hub object for the hierarchy (or, rather, directed graph)
of connected parser classes. It is also the entry and exit point for
the parsing process. Parser objects are never call directly, but only
through the Grammar object to which they belong.
"""


from __future__ import annotations

import functools
from collections import defaultdict
import copy
from typing import Callable, cast, DefaultDict, Union, Optional, \
    NamedTuple

from DHParser.configuration import get_config_value, NEVER_MATCH_PATTERN
from DHParser.error import Error, PARSER_LOOKAHEAD_FAILURE_ONLY, \
    PARSER_LOOKAHEAD_MATCH_ONLY, PARSER_STOPPED_BEFORE_END, PARSER_NEVER_TOUCHES_DOCUMENT, \
    CAPTURE_STACK_NOT_EMPTY, AUTOCAPTURED_SYMBOL_NOT_CLEARED, \
    CAPTURE_STACK_NOT_EMPTY_WARNING, CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY, \
    AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT, PARSER_STOPPED_ON_RETRY, ERROR, CANCELED, \
    PARSER_STOPPED_BEFORE_END_WARNING, has_errors, is_error
from DHParser.log import CallItem, HistoryRecord
from DHParser.parse_base import Parser, get_parser_placeholder, is_parser_placeholder, \
    has_non_autocaptured_symbols, LeafParser, ParserTrail, PARSER_PLACEHOLDER
from DHParser.parse_error import ParserError, ResumeList, PatternMatchType
from DHParser.preprocess import SourceMapFunc
from DHParser.stringview import StringView, EMPTY_STRING_VIEW
from DHParser.nodetree import Node, RootNode, ZOMBIE_TAG, EMPTY_NODE, \
    EMPTY_PTYPE, LEAF_NODE
from DHParser.toolkit import sane_parser_name, re, RxPatternType, linebreaks, line_col, \
    TypeAlias, List, Tuple, Any, MutableSet, Set, FrozenSet, Dict, INFINITE, LazyRE, \
    CancelQuery, deprecated, RxType

try:
    import cython
except (ImportError, NameError):
    import DHParser.externallibs.shadow_cython as cython


RX_NEVER_MATCH = LazyRE(NEVER_MATCH_PATTERN)


def mixin_comment(whitespace: str, comment: str, always_match: bool = True) -> str:
    r"""
    Returns a regular expression pattern that merges comment and whitespace
    regexps. Thus comments can occur wherever whitespace is allowed
    and will be skipped just as implicit whitespace.

    Note that because this works on the level of regular expressions,
    nesting comments is not possible. It also makes it much harder to
    use directives inside comments (which isn't recommended, anyway).

    Examples::

        >>> import re
        >>> combined = mixin_comment(r"\s+", r"#.*")
        >>> print(combined)
        (?:(?:\s+)?(?:(?:#.*)(?:\s+)?)*)
        >>> rx = re.compile(combined)
        >>> rx.match('   # comment').group(0)
        '   # comment'
        >>> combined = mixin_comment(r"\s+", r"#.*", always_match=False)
        >>> print(combined)
        (?:(?:\s+)(?:(?:#.*)(?:\s+))*)
        >>> rx = re.compile(combined)
        >>> rx.match('   # comment').group(0)
        '   # '
    """
    if re.match(whitespace, ""):
        whitespace = f'(?:{whitespace})'
    else:
        whitespace = '(?:' + whitespace + (')?' if always_match else ')')

    if comment and comment != NEVER_MATCH_PATTERN:
        comment = '(?:' + comment + ')'
        return '(?:' + whitespace + '(?:' + comment + whitespace + ')*)'
    return whitespace


def mixin_nonempty(whitespace: str) -> str:
    r"""
    Returns a regular expression pattern that matches only if the regular
    expression pattern "whitespace" matches AND if the match is not empty.

    If "whitespace"  does not match the empty string '', anyway,
    then it will be returned unaltered.

    WARNING: "mixin_nonempty()" does not work for regular expressions the matched
    strings of which can be followed by a symbol that can also occur at
    the start of the regular expression.

    In particular, it does not work for fixed size regular expressions,
    that is / / or /   / or /\t/ won't work, but / */ or /\s*/ or /\s+/
    do work. There is no test for this. Fixed-size regular expressions
    run through "mixin_nonempty" will not match at anymore if they are applied
    to the beginning or the middle of a sequence of whitespaces!

    In order to be safe, your whitespace regular expressions should follow
    the rule: "Whitespace cannot be followed by whitespace" or "Either
    grab it all or leave it all".

    :param whitespace: a regular expression pattern
    :return: new regular expression pattern that does not match the empty
        string '', anymore.
    """
    if re.match(whitespace, ''):
        return r'(?:(?=(.|\n))' + whitespace + r'(?!\1))'
    return whitespace


class AnalysisError(NamedTuple):
    symbol: str
    parser: Parser
    error: Error
    __module__ = __name__  # required for cython compatibility


class GrammarError(Exception):
    """GrammarError will be raised if static analysis reveals errors
    in the grammar.
    """
    def __init__(self, static_analysis_result: List[AnalysisError]):
        assert static_analysis_result  # must not be empty
        self.errors = static_analysis_result

    def __str__(self):
        if len(self.errors) == 1:
            return str(self.errors[0][2])
        return '\n' + '\n'.join(("%i. " % (i + 1) + str(err_tuple[2]))
                                for i, err_tuple in enumerate(self.errors))


class UninitializedError(Exception):
    """An error that results from unintialized objects. This can be
    a consequence of some broken boot-strapping-process."""
    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return f'UninitializedError: {self.msg}'


class CancelError(Exception):
    "An error that is raised, if parsing has been canceled by a cancel_query."
    def __init__(self, location):
        self.location = location

    def __str__(self):
        return f'CancelError: {self.location}'


CANCEL_QUERY_INTERVAL = 10


def cancel_proxy(self: Parser, location: cython.int) -> Tuple[Optional[Node], cython.int]:
    grammar = self.grammar
    grammar.cancel_interval__ -= 1
    if grammar.cancel_interval__ < 0:
        grammar.cancel_interval__ = CANCEL_QUERY_INTERVAL
        if grammar.cancel_query__ and grammar.cancel_query__():
            raise CancelError(location)
    return self._parse(location)


RESERVED_PARSER_NAMES = ('root__', 'dwsp__', 'wsp__', 'comment__', 'root_parser__', 'ff_parser__')


def reset_parser(parser):
    return parser.reset()


def is_disposable(name: str, disposables: Union[Set[str], RxType]) -> bool:
    if name[0:1] == ':':
        return True
    elif isinstance(disposables, (Set, frozenset)):
        return name in disposables
    elif isinstance(disposables, (RxPatternType, LazyRE)):
        return bool(disposables.match(name))
    else:
        assert isinstance(disposables, str), type(disposables)
        return bool(re.match(disposables, name))


class Grammar:
    r"""
    Class Grammar directs the parsing process and stores global state
    information of the parsers, i.e. state information that is shared
    across parsers.

    Grammars are basically collections of parser objects, which are
    connected to an instance object of class Grammar. There exist two
    ways of connecting parsers to grammar objects: Either by passing
    the root parser object to the constructor of a Grammar object
    ("direct instantiation"), or by assigning the root parser to the
    class variable "root\__" of a descendant class of class Grammar.

    Example for direct instantiation of a grammar::

        >>> from DHParser.parse_combinators import RE
        >>> number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        >>> number_parser = Grammar(number)
        >>> number_parser("3.1416").content
        '3.1416'

    Collecting the parsers that define a grammar in a descendant class of
    class Grammar and assigning the named parsers to class variables
    rather than to global variables has several advantages:

    1. It keeps the namespace clean.

    2. The parser names of named parsers do not need to be passed to the
       constructor of the Parser object explicitly, but it suffices to
       assign them to class variables, which results in better
       readability of the Python code.
       See classmethod :py:meth:`Grammar._assign_parser_names__`

    3. The parsers in the class do not necessarily need to be connected
       to one single root parser, which is helpful for testing and when
       building up a parser gradually from several components.

    As a consequence, though, it is highly recommended that a Grammar
    class should not define any other variables or methods with names
    that are legal parser names. A name ending with a double
    underscore "__" is *not* a legal parser name and can safely be
    used.

    Example::

        class Arithmetic(Grammar):
            # special fields for implicit whitespace and comment configuration
            COMMENT__ = r'#.*(?:\n|$)'  # Python style comments
            wspR__ = mixin_comment(whitespace=r'[\t ]*', comment=COMMENT__)

            # parsers
            expression = Forward()
            INTEGER = RE('\\d+')
            factor = INTEGER | TKN("(") + expression + TKN(")")
            term = factor + ZeroOrMore((TKN("*") | TKN("/")) + factor)
            expression.set(term + ZeroOrMore((TKN("+") | TKN("-")) + term))
            root__ = expression

    Upon instantiation the parser objects are deep-copied to the
    Grammar object and assigned to object variables of the same name.
    For any parser that is directly assigned to a class variable the
    field "parser.pname" contains the variable name after instantiation
    of the Grammar class. The parser will nevertheless remain anonymous
    with respect to the tag names of the nodes it generates, if its name
    is included in the "disposable\__" set or, if "disposable\__"
    has been defined by a regular expression, matched by that regular expression.
    If one and the same parser is assigned to several class variables
    such as, for example, the parser "expression" in the example above,
    which is also assigned to "root\__", the first name sticks.

    Grammar objects are callable. Calling a grammar object with a UTF-8
    encoded document initiates the parsing of the document with the
    root parser. The return value is the concrete syntax tree. Grammar
    objects can be reused (i.e. called again) after parsing. Thus, it
    is not necessary to instantiate more than one Grammar object per
    thread.

    Grammar classes contain a few special class fields for implicit
    whitespace and comments that should be overwritten if the defaults
    (no comments, horizontal right aligned whitespace) don't fit:

    Class Attributes:

    :cvar root\__:  The root parser of the grammar. Theoretically, all parsers of the
                 grammar should be reachable by the root parser. However, for testing
                 of yet incomplete grammars, class Grammar does not assume that this
                 is the case.

    :cvar resume_rules\__: A mapping of parser names to a list of regular expressions
                that act as rules to find the reentry point if a ParserError was
                thrown during the execution of the parser with the respective name.

    :cvar skip_rules\__: A mapping of parser names to a list of regular expressions
                that act as rules to find the reentry point if a ParserError was
                thrown during the execution of the parser with the respective name.

    :cvar error_messages\__: A mapping of parser names to a Tuple of regular expressions
                and error messages. If a mandatory violation error occurs on a
                specific symbol (i.e. parser name) and any of the regular expressions
                matches, the error message of the first matching expression is used
                instead of the generic mandatory violation error messages. This
                allows answering typical kinds of errors (say putting a colon ","
                where a semicolon ";" is expected) with more informative error
                messages.

    :cvar disposable\__: A set of parser-names or a regular expression to
                identify names of parsers that are assigned to class fields
                but shall nevertheless yield anonymous nodes (i.e. nodes the
                tag name of which starts with a colon ":"
                followed by the parser's class name).

    :cvar parser_initialization\__:  Before the grammar class (!) has been initialized,
                 which happens upon the first time it is instantiated (see
                 :py:meth:`_assign_parser_names__` for an explanation), this class
                 field contains a value other than "done". A value of "done" indicates
                 that the class has already been initialized.

    :cvar static_analysis_pending\__: True as long as no static analysis (see the method
                with the same name for more information) has been done to check
                parser tree for correctness. Static analysis
                is done at instantiation and the flag is then set to false, but it
                can also be carried out once the class has been generated
                (by DHParser.ebnf.EBNFCompiler) and then be set to false in the
                definition of the grammar class already.

    :cvar static_analysis_errors\__: A list of errors and warnings that were found in the
                static analysis

    :cvar parser_names\__: The list of the names of all named parsers defined in the
                grammar class

    :cvar python_src\__:  For the purpose of debugging and inspection, this field can
                 take the python src of the concrete grammar class
                 (see :py:func:`dsl.grammar_provider`).


    Instance Attributes:

    :ivar all_parsers\__:  A set of all parsers connected to this grammar object

    :ivar comment_rx\__:  The compiled regular expression for comments. If no
                comments have been defined, it defaults to RX_NEVER_MATCH
                This instance-attribute will only be defined if a class-attribute
                with the same name does not already exist!

    :ivar start_parser\__:  During parsing, the parser with which the parsing process
                was started (see method "__call__") or "None" if no parsing process
                is running.

    :ivar unconnected_parsers\__: A set of parsers that are not connected to the
                root parser. The set of parsers is collected during instantiation.

    :ivar resume_parsers\__: A set of parsers that appear either in a resume-rule
                or a skip-rule. This set is a subset of "unconnected_parsers\__"

    :ivar _dirty_flag\__:  A flag indicating that the Grammar has been called at
                least once so that the parsing-variables need to be reset
                when it is called again.

    :ivar text\__: The text that is currently been parsed or that has mose recently
               been parsed.

    :ivar document\__:  A string view on the text that has most recently been parsed
                or that is currently being parsed.

    :ivar document_length\__:  the length of the document.

    :ivar document_lbreaks\__: (property) list of linebreaks within the document,
                starting with -1 and ending with EOF. This helps to generate line
                and column number for history recording and will only be
                initialized if :attr:`history_tracking__` is true.

    :ivar tree\__: The root-node of the parsing tree. This variable is available
               for error-reporting already during parsing  via
               "self.grammar.tree\__.add_error", but it references the full
               parsing tree only after parsing has been finished.

    :ivar _reversed\__:  the same text in reverse order - needed by the "Lookbehind"-
                parsers.

    :ivar variables\__:  A mapping for variable names to a stack of their respective
                string values - needed by the :py:class:`Capture`-, :py:class:`Retrieve`-
                and :py:class:`Pop`-parsers.

    :ivar rollback\__:  A list of tuples (location, rollback-function) that are
                deposited by the :py:class:`Capture`- and :py:class:`Pop`-parsers.
                If the parsing process reaches a dead end then all
                rollback-functions up to the point to which it retreats will be
                called and the state of the variable stack restored accordingly.

    :ivar last_rb__loc\__:  The last, i.e. most advanced location in the text
                where a variable changing operation occurred. If the parser
                backtracks to a location at or before "last_rb__loc__" (i.e.
                location < last_rb__loc__) then a rollback of all variable
                changing operations is necessary that occurred after the
                location to which the parser backtracks. This is done by
                calling method :py:meth:`rollback_to__` (location).

    :ivar ff_pos\__: The "farthest fail", i.e. the highest location in the
                document where a parser failed. This gives a good indication
                where and why parsing failed, if the grammar did not match
                a text.

    :ivar ff_parser\__: The parser that failed at the "farthest fail"-location
                "ff_pos\__"

    :ivar suspend_memoization\__: A flag that if set suspends memoization of
                results from returning parsers. This flag is needed by the
                left-recursion handling algorithm (see :py:meth:`Parser.__call__`
                and :py:meth:`Forward.__call__`) as well as the context-sensitive
                parsers (see function :py:meth:`Grammar.push_rollback__`).

    :ivar associated_symbol_cache\__: A cache for the :py:meth:`associated_symbol__` -method.

    :ivar memo\__: A temporary memo for the deepcopy-calls inside the constructor.
                Before the first deepcopy-call, this memo is filled with the negative
                id's of all the classes' parser-objects that have directly been assigned
                to a class variable, mapped to the class variable's name (= the symbol
                of the parser) and zero mapped to the Grammar-object under constrcution.
                This allows assigning the object variables to the duplicated parser objects
                as well as assigning the grammar object to all parsers very early in the
                construction phase. Before the constructor returns, memo\__ will be set to
                None and it will never be used anymore, afterwards.


    Mirrored class attributes:

    :ivar static_analysis_pending\__: A pointer to the class attribute of the same name.
                (See the description above.) If the class is instantiated with a
                parser, this pointer will be overwritten with an instance variable
                that serves the same function.

    :ivar static_analysis_errors\__: A pointer to the class attribute of the same name.
                (See the description above.) If the class is instantiated with a
                parser, this pointer will be overwritten with an instance variable
                that serves the same function.


    Tracing and debugging support:

    The following parameters are needed by the debugging functions in module
    "trace.py". They should not be manipulated by the users of class
    Grammar directly.

    :ivar history_tracking\__:  A flag indicating that the parsing history is
                being tracked. This flag should not be manipulated by the
                user. Use :py:func:`trace.set_tracer` (grammar, trace.trace_history) to
                turn (full) history tracking on and
                :py:func:`trace.set_tracer` (grammar, None) to turn it off.
                Default is off.

    :ivar resume_notices\__: A flag indicating that resume messages are generated
                in addition to the error messages, in case the parser was able
                to resume after an error. Use :py:func:`trace.resume_notices` (grammar)
                to turn resume messages on and :py:func:`trace.set_tracer` (grammar, None)
                to turn resume messages (as well as history recording) off.
                Default is off.

    :ivar call_stack\__:  A stack of the tag names and locations of all parsers
                in the call chain to the currently processed parser during
                parsing. The call stack can be thought of as a breadcrumb path.
                This is required for recording the parser history (for debugging)
                and, eventually, i.e. one day in the future, for tracing through
                the parsing process.

    :ivar history\__:  A list of history records. A history record is appended to
                the list each time a parser either matches, fails or if a
                parser-error occurs. See class :py:class:`log.HistoryRecord`. History
                records store copies of the current call stack.

    :ivar moving_forward\__: This flag indicates that the parsing process is currently
                moving forward. It is needed to reduce noise in history recording
                and should not be considered as having a valid value if history
                recording is turned off! (See :py:meth:`Parser.__call__`)

    :ivar most_recent_error\__: The most recent parser error that has occurred
                or "None". This can be read by tracers. See module :py:mod:`trace`


    Configuration parameters:

    The values of these parameters are copied from the global configuration
    in the constructor of the Grammar object. (see mpodule :py:mod:`configuration`)

    :ivar max_parser_dropouts\__: Maximum allowed number of retries after errors
                where the parser would exit before the complete document has
                been parsed. Default is 1, as usually the retry-attemts lead
                to a proliferation of senseless error messages.

    :ivar reentry_search_window\__: The number of following characters that the
                parser considers when searching a reentry point when a syntax error
                has been encountered. Default is 10.000 characters.
    """
    python_src__ = ''  # type: str
    root__: Parser = get_parser_placeholder()
    # root__ must be overwritten with the root-parser by grammar subclass
    parser_initialization__: List[str] = ["pending"]
    resume_rules__: Dict[str, ResumeList] = dict()
    skip_rules__: Dict[str, ResumeList] = dict()
    error_messages__: Dict[str, Tuple[PatternMatchType, str]] = dict()
    disposable__: Union[FrozenSet[str], RxType] = frozenset()
    # some default values
    COMMENT__ = r''  # type: str  # r'#.*'  or r'#.*(?:\n|$)' if combined with horizontal wspc
    WHITESPACE__ = r'[ \t]*(?:\n[ \t]*)?(?!\n)'  # spaces plus at most a single linefeed
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)  # type: str
    static_analysis_pending__ = [True]  # type: List[bool]
    static_analysis_errors__ = []  # type: List[AnalysisError]
    parser_names__ = []            # type: List[str]
    early_tree_reduction__ = 1     # type: int  # 1 == CombinedParser.FLATTEN

    @classmethod
    def _propagate_drop__(cls, p: Parser):
        """propagates the drop_content flag to all unnamed children."""
        assert p.drop_content
        from DHParser.parse_combinators import ForwardBase
        p._grammar = cls  # only required for LateBindingUnary, but faster then isinstance-check for every p
        for c in p.sub_parsers:
            if (not isinstance(c, ForwardBase)
                    and (not c.pname or isinstance(p, ForwardBase))):
                c.drop_content = True
                cls._propagate_drop__(c)

    @classmethod
    def ensure_drop_propagation__(cls, p: Parser):
        """propagates the drop_content flag to all unnamed children."""
        if p.drop_content:
            cls._propagate_drop__(p)
        else:
            from DHParser.parse_combinators import ForwardBase, LateBindingUnary
            try:
                p._grammar = cls   # only required for LateBindingUnary
                for c in p.sub_parsers:
                    if (not isinstance(c, ForwardBase)
                            and (not c.pname or isinstance(p, ForwardBase))):
                        cls.ensure_drop_propagation__(c)
            except UninitializedError as e:
                if not isinstance(p, LateBindingUnary):
                    raise e

    @classmethod
    def _assign_parser_names__(cls):
        r"""
        Initializes the "parser.pname" fields of those
        Parser objects that are directly assigned to a class field with
        the field's name, e.g.::

            class Grammar(Grammar):
                ...
                symbol = RE(r'(?!\\d)\\w+')

        After the call of this method symbol.pname == "symbol" holds.
        Parser names starting or ending with a double underscore like
        "root\__" will be ignored. See :py:func:`sane_parser_name`

        This is done only once, upon the first instantiation of the
        grammar class!

        Attention: If there exists more than one reference to the same
        parser, only the first one will be chosen. See also PEP 520
        (www.python.org/dev/peps/pep-0520/).
        """
        if cls.parser_initialization__[0] != "done" and cls != Grammar:
            from DHParser.parse_combinators import ForwardBase
            cdict = cls.__dict__
            # cls.static_analysis_errors__ = []
            cls.parser_names__ = []
            for entry, parser in cdict.items():
                if isinstance(parser, Parser) and entry not in RESERVED_PARSER_NAMES:
                    anonymous = ":" if is_disposable(entry, cls.disposable__) else ""
                    assert anonymous or not parser.drop_content, entry
                    if isinstance(parser, ForwardBase):
                        if not cast(ForwardBase, parser).parser.pname:
                            cast(ForwardBase, parser).parser.name(anonymous + entry)
                    else:
                        parser.name(anonymous + entry)
                    cls.parser_names__.append(entry)
            for entry in cls.parser_names__:
                parser = cdict[entry]
                cls.ensure_drop_propagation__(parser)
            cls.parser_initialization__ = ["done"]  # (over-)write subclass-variable


    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        duplicate.history_tracking__ = self.history_tracking__
        duplicate.resume_notices__ = self.resume_notices__
        duplicate.max_parser_dropouts__ = self.max_parser_dropouts__
        duplicate.reentry_search_window__ = self.reentry_search_window__
        return duplicate


    def _add_parser__(self, parser: Parser) -> None:
        """
        Adds the particular copy of the parser object to this
        particular instance of Grammar.
        """
        assert parser is not PARSER_PLACEHOLDER
        if parser not in self.all_parsers__:
            from DHParser.parse_combinators import ForwardBase
            if parser.pname:
                # prevent overwriting instance variables or parsers of a different class
                registered = self.__dict__.get(parser.pname, None)
                if registered:
                    # assert (isinstance(self.__dict__[parser.pname], ForwardBase)
                    #         or self.__dict__.get(parser.pname, parser) is parser), \
                    assert (registered is parser
                            or (isinstance(registered, ForwardBase) and registered.parser is parser)), \
                        (f'Cannot add parser "{parser}" because a field with '
                         ' the same name already exists in grammar object: '
                         f'{type(registered)} {registered}')
                else:
                    setattr(self, parser.pname, parser)
            elif isinstance(parser, ForwardBase):
                registered = self.__dict__.get(parser.parser.pname, None)
                if registered and not registered is parser.parser:
                    assert registered is parser, \
                        (f'Cannot add forward-parser "{parser}" because a field with '
                         ' the same name already exists in grammar object: '
                         f'{type(registered)} {registered}')
                else:  # set forward parser or overwrite forwarded parser with forward parser
                    setattr(self, parser.parser.pname, parser)
            self.all_parsers__.add(parser)
            # parser.grammar = self  # happens earlier when deep-copying all parser objects


    def __init__(self, root: Optional[Parser] = None, static_analysis: Optional[bool] = None) -> None:
        """Constructor of class Grammar.

        :param root: If not None, this is going to be the root parser of the grammar.
            This allows constructing an ensemble of parser objects, first, and then
            linking those objects in a grammar-object, rather than adding the parsers
            as fields to a derived class of class Grammar. (See the doc-tests in this
            module for examples.)
        :param static_analysis: If not None, this overrides the config value
            "static_analysis".
        """
        global PARSER_PLACEHOLDER, RESERVED_PARSER_NAMES
        assert root is None or self.__class__ is Grammar, \
            "External root-parsers cannot be passed to derived classes of Grammar!"
        from DHParser.parse_combinators import ForwardBase, TreeReduction
        self.all_parsers__: MutableSet[Parser] = set()
        # add compiled regular expression for comments if it does not already exist
        if not hasattr(self, 'comment_rx__') or self.comment_rx__ is None:
            if hasattr(self.__class__, 'COMMENT__') and self.__class__.COMMENT__:
                self.comment_rx__: RxType = re.compile(self.__class__.COMMENT__)
            else:
                self.comment_rx__ = RX_NEVER_MATCH
        else:
            assert ((self.__class__.COMMENT__
                     and self.__class__.COMMENT__ == self.comment_rx__.pattern)
                    or (not self.__class__.COMMENT__ and
                        self.comment_rx__.pattern == RX_NEVER_MATCH.pattern))
        self.start_parser__: Optional[Parser] = None
        self._dirty_flag__: bool = False
        self.history_tracking__: bool = get_config_value('history_tracking')
        self.resume_notices__: bool = get_config_value('resume_notices')
        self.max_parser_dropouts__: int = get_config_value('max_parser_dropouts')
        self.reentry_search_window__: int = get_config_value('reentry_search_window')
        self.associated_symbol_cache__: Dict[Parser, Parser] = dict()
        self.cancel_query__: Optional[CancelQuery] = None
        self.cancel_query_last__: Optional[CancelQuery] = None
        self.cancel_interval__: int = CANCEL_QUERY_INTERVAL
        self._reset__()

        # Bootsrapping phase 1: assign names to the parsers
        # Prepare parsers in the class, first, by setting the name of those parsers
        # that are assigned to a class variable to the name of that class variable.
        # Also, LateBindingUnary-parser will be bound at this stage.
        self.__class__._assign_parser_names__()

        # Bottstrapping phase 2: deepcopy the parsers defined in the context of the
        # Grammar-class to the Grammar instance.

        # 2.1. Prepare a deepcopy-memo and inject the grammar-object into that memo.
        self.memo__: Optional[Dict[int, Any]] = {0: self}
        # Then inject all named parsers (i.e. parser directly assigned to a class variable)
        # into the deepcopy-memo.
        for name in self.__class__.parser_names__:
            obj = self.__class__.__dict__[name]
            self.memo__[-id(obj)] = name  # src object -> symbol name
        # 2.2. Then, deepcopy all named parsers (i.e. parsers assigned to a class variable)
        # to the Grammar-instance and doing so, connect them to the Grammar-instance
        for name in self.__class__.parser_names__:
            setattr(self, name, copy.deepcopy(self.__class__.__dict__[name], self.memo__))
        # 2.3 Now, initialize additional top-level parser references like 'root__'
        if PARSER_PLACEHOLDER is None:  # can happen in doc-test examples...
            PARSER_PLACEHOLDER = get_parser_placeholder()
        for name in RESERVED_PARSER_NAMES:
            p = self.__class__.__dict__.get(name, None)
            if isinstance(p, Parser):
                if p is PARSER_PLACEHOLDER:
                    setattr(self, name, p)
                else:
                    setattr(self, name, copy.deepcopy(p, self.memo__))

        # 2.5. Set self.root_parser__
        if root:
            # deepcopy the root-parser tree to the Grammar instance, if in case the non-derived
            # Grammar class was initialized with a root-parser defined outside the class
            self.root_parser__ = copy.deepcopy(root, self.memo__)
            if not self.root_parser__.pname and not isinstance(root, ForwardBase):
                self.root_parser__.name("root")
            self.root_parser__.disposable = False
            self.static_analysis_pending__ = [True]  # type: List[bool]
            self.static_analysis_errors__ = []       # type: List[AnalysisError]
        else:
            assert self.__class__ == Grammar or not is_parser_placeholder(self.__class__.root__),\
                "Please add `root__` field to definition of class " + self.__class__.__name__
            # assign the 'root_parser__' field to the root-parser of the grammar
            self.root_parser__ = self.root__
            # # practically the entire root-parser tree will have been copied already, but this
            # # does not harm, because with self.memo__ copying the root-parser-tree will be
            # # short-circuited, anyway. (So the following command is not very costly.)
            # self.root_parser__ = copy.deepcopy(self.__class__.root__, self.memo__)
            self.static_analysis_pending__ = self.__class__.static_analysis_pending__
            self.static_analysis_errors__ = self.__class__.static_analysis_errors__
        self.static_analysis_caches__ = dict()  # type: Dict[str, Dict]

        # At the end of phase two, only parsers inside the skip and resume list
        # are not yet initialized. This will happen en passent in the next phase

        # Phase 3: Add any parser whatsoever connected to this Grammar instance
        #          to the self.all_parsers__ set. Add those parser which are
        #          not connected to the root-parser to the
        #          self.unconnected_parsers__ - field

        # Start by adding the parsers connected to the root parser.
        if self.root_parser__ is not PARSER_PLACEHOLDER:
            self.root_parser__.apply(self._add_parser__, self)
            assert self.root_parser__ is self.__dict__['root_parser__']
        root_connected = frozenset(self.all_parsers__)

        # Now, make sure that the parsers occurring in a @skip- or @resume-directive
        # will also be copyied and initialized with the grammar-object and added
        # to the all_parsers__ set.
        self.ff_parser__ = self.root_parser__
        self.unconnected_parsers__: MutableSet[Parser] = set()
        self.resume_parsers__: MutableSet[Parser] = set()
        resume_lists: List[ResumeList] = []
        if hasattr(self, 'resume_rules__'):
            resume_lists.extend(self.resume_rules__.values())
        if hasattr(self, 'skip_rules__'):
            resume_lists.extend(self.skip_rules__.values())
        for l in resume_lists:
            for i in range(len(l)):
                if isinstance(l[i], Parser):
                    p = self[cast(Parser, l[i]).pname]  # deep-copy and initialize, if necessary.
                    l[i] = p
                    if p not in root_connected:
                        self.unconnected_parsers__.add(p)
                        self.resume_parsers__.add(p)
        # Add remaining parsers
        for name in self.__class__.parser_names__:
            parser = self[name]
            if parser not in root_connected:  self.unconnected_parsers__.add(parser)

        # # DEBUGGING code:
        # if self.__class__.__name__ == 'DSLGrammar':
        #     print('***')
        #     for p in self.all_parsers__:
        #         if p.pname == 'term':
        #             print('term = ', id(p))
        #         elif p.effective_pname() == 'term':
        #             print(type(p), id(p), id(p.parser))

        self.memo__ = None  # the deepcopy memo is not needed any more after this point.

        # Phase 4: Reset/Initialize all parsers
        for p in self.all_parsers__:  reset_parser(p)

        if not root:  TreeReduction(self.all_parsers__, self.early_tree_reduction__)

        # Phase 5: Do some static error checking, if the error checking flag
        #          has been set on the class and error checking for this class
        #          has not already taken place.
        if (self.static_analysis_pending__
            and (static_analysis
                 or (static_analysis is None
                     and get_config_value('static_analysis') in {'early', 'late'}))):
            analysis_errors = self.static_analysis__()
            # clears any stored errors without overwriting the pointer
            while self.static_analysis_errors__:
                self.static_analysis_errors__.pop()
            self.static_analysis_errors__.extend(analysis_errors)
            self.static_analysis_pending__.pop()
            # raise a GrammarError even if result only contains warnings.
            # It is up to the caller to decide whether to ignore warnings
            # # has_errors = any(is_error(tpl[-1].code) for tpl in result)
            # # if has_errors
            if has_errors([ae.error for ae in analysis_errors], ERROR):
                raise GrammarError(analysis_errors)


    def __str__(self):
        return self.__class__.__name__


    def __getitem__(self, key):
        try:
            parser = self.__dict__[key]
            if parser not in self.all_parsers__:
                parser.apply(self._add_parser__, self)
            return parser
        except KeyError:
            parser_template = getattr(self.__class__, key, None)
            if parser_template:
                # TODO: Can this code ever be reached?
                from DHParser.parse_combinators import ForwardBase
                if key != parser_template.pname or (parser_template.parser.pname
                        if isinstance(parser_template, ForwardBase) else ''):
                    raise AttributeError(
                        f'Illegal parser-name "{key}" for grammar {self.__class__.__name__}!')
                # add parser to grammar-object on the fly...
                parser = copy.deepcopy(parser_template, self.memo__)
                parser.apply(self._add_parser__, self)
                assert self[key] == parser
                return self[key]
            raise AttributeError(f'Unknown parser "{key}" in grammar {self.__class__.__name__}!')


    def __contains__(self, key):
        return key in self.__dict__ or hasattr(self, key)


    def _reset__(self):
        self.tree__: RootNode = RootNode()
        self.text__: str = ''
        self.document__: StringView = EMPTY_STRING_VIEW
        self._reversed__: StringView = EMPTY_STRING_VIEW
        self.document_length__: int = 0
        self._document_lbreaks__: List[int] = []
        # variables stored and recalled by Capture and Retrieve parsers
        self.variables__: DefaultDict[str, List[str]] = defaultdict(lambda: [])
        self.rollback__: List[Tuple[int, Callable]] = []
        self.last_rb__loc__: int = -2
        self.suspend_memoization__: Union[bool, int] = False
        self.use_memo__: int = -1  # True
        # support for call stack tracing
        self.call_stack__: List[CallItem] = []  # name, location
        # snapshots of call stacks
        self.history__: List[HistoryRecord] = []
        # also needed for call stack tracing
        self.moving_forward__: bool = False
        self.most_recent_error__: Optional[ParserError] = None
        # farthest fail error reporting
        self.ff_pos__: int = -1
        try:
            self.ff_parser__: Parser = self.root_parser__
        except AttributeError:
            self.ff_parser__: Parser = get_parser_placeholder()

    @property
    def reversed__(self) -> StringView:
        """
        Returns a reversed version of the currently parsed document. As
        about the only case where this is needed is the Lookbehind-parser,
        this is done lazily.
        """
        if not self._reversed__:
            self._reversed__ = StringView(self.document__.get_text()[::-1])
        return self._reversed__


    def __call__(self,
                 document: str,
                 start_parser: Union[str, Parser] = "root_parser__",
                 source_mapping: Optional[SourceMapFunc] = None,
                 *, complete_match: Union[bool, str] = "WSP_RE__") -> RootNode:
        """
        Parses a document with parser-combinators.

        :param document: The source text to be parsed.
        :param start_parser: The name of the parser (or the parser-object itself)
            with which to start. This is useful for testing particular parsers
            (i.e. particular parts of the EBNF-Grammar.)
        :param complete_match: If True, an error is generated, if
            "start_parser" did not match the entire document. If complete_match
            is a string (default) it suffices that the remaining text after the
            match consists of whitespace. The string is interpreted as the name
            of an attribute of self that contains a regular expression string
            defining the ensuing whitespace. If False, no error is generated
            even if not the complete text has been matched.
        :return: The root node of the parse-tree alias "concrete-syntax-tree".
        """
        assert source_mapping is None or callable(source_mapping), source_mapping

        @cython.returns(cython.int)
        def tail_pos(predecessors: Union[List[Node], Tuple[Node, ...], None]) -> int:
            """Adds the position after the last node in the list of
            predecessors to the node."""
            if predecessors:
                tail = predecessors[-1].pick(LEAF_NODE, reverse=True, include_root=True)
                if tail is not None:
                    return tail.pos + tail.strlen()
            return 0

        def lookahead_failure_only(parser) ->bool:
            """EXPERIMENTAL!

            Checks if failure to match document was only due to a succeeding
            lookahead parser, which is a common design pattern that can break test
            cases. (Testing for this case allows to modify the error message, so
            that the testing framework knows that the failure is only a
            test-case-artifact and no real failure.
            (See test/test_testing.TestLookahead !))
            """
            from DHParser.parse_combinators import Lookahead, RegExp, SmartRE

            def is_lookahead(name: str) -> bool:
                custom_parser_class = None

                def find_parser_class(parser, name) -> bool:
                    nonlocal custom_parser_class
                    if parser.__class__.__name__ == name:
                        custom_parser_class = parser.__class__
                        return True
                    return False

                try:
                    return ((name in self
                             and (isinstance(self[name], Lookahead)
                                  or (isinstance(self[name], RegExp)
                                      and self[name].regexp.pattern[0:3] in ('(?=', '(?!'))
                                  or (isinstance(self[name], SmartRE)
                                      and self[name].pattern[0:3] in ('(?=', '(?!'))))
                            or (name[0] == ':' and issubclass(eval(name[1:]), Lookahead)))
                except NameError:
                    #  eval(name[1:]) failed, because custom parsers are not visible from here
                    nonlocal parser
                    parser.apply(functools.partial(find_parser_class, name=name[1:]))
                    if custom_parser_class is not None:
                        return issubclass(custom_parser_class, Lookahead)
                    return False

            last_record = self.history__[-2] if len(self.history__) > 1 else None
            if last_record and parser != self.root_parser__:
                for i, h in enumerate(self.history__[:-1]):
                    if h.status == HistoryRecord.MATCH \
                            and h.node.strlen() == self.document_length__:
                        # the last clause is faster than, but does the same as:
                        # h.node.content == self.text__
                        break
                else:
                    return False
                for h in self.history__[i:-1]:
                    if h.status == HistoryRecord.MATCH:
                        if any(is_lookahead(tn) and location >= len(self.document__)
                               for tn, location in h.call_stack):
                            return True
                return False
            else:
                return False

        # assert isinstance(document, str), type(document)
        parser = self[start_parser] if isinstance(start_parser, str) else start_parser
        assert parser.grammar == self, "Cannot run parsers from a different grammar object!" \
                                       " %s vs. %s" % (str(self), str(parser.grammar))

        if self._dirty_flag__:
            self._reset__()
            parser.apply(reset_parser)
            for p in self.resume_parsers__:  p.apply(reset_parser)
        else:
            self._dirty_flag__ = True

        self.start_parser__ = parser
        assert isinstance(document, str)
        # eliminate BOM (byte order mark) https://en.wikipedia.org/wiki/Byte_order_mark
        if document[0:1] in ('\ufeff', '\uffef'):
            self.text__ = document[1:]
        elif document[0:3] in ('\xef\xbb\xbf', '\x00\x00\ufeff', '\x00\x00\ufffe'):
            self.text__ = document[3:]
        else:
            self.text__ = document
        self.text__ = document[1:] if document[0:1] in ('\ufeff', '\uffef') else document
        self.document__ = StringView(self.text__)
        self.document_length__ = len(self.document__)
        self._document_lbreaks__ = linebreaks(self.text__) if self.history_tracking__ else []
        # done by reset: self.last_rb__loc__ = -2  # rollback location
        self.set_cancel_query__()
        result = None  # type: Optional[Node]
        stitches = []  # type: List[Node]
        L = len(self.document__)
        if L >= INFINITE:
            raise ValueError(f"Document of size {L} exceeds maximum size of {INFINITE - 1} !")
        if L == 0:
            try:
                result, _ = parser(0)
            except ParserError as pe:
                result = pe.node
            if result is None:
                result = Node(ZOMBIE_TAG, '').with_pos(0)
                if lookahead_failure_only(parser):
                    self.tree__.new_error(
                        result, 'Parser %s only did not match empty document '
                                'because of lookahead' % str(parser),
                        PARSER_LOOKAHEAD_FAILURE_ONLY)
                else:
                    self.tree__.new_error(
                        result, 'Parser %s did not match empty document.' % str(parser),
                        PARSER_STOPPED_BEFORE_END)

        # copy to local variable, so break condition can be triggered manually
        max_parser_dropouts = self.max_parser_dropouts__
        location = 0
        while location < L and len(stitches) < max_parser_dropouts:
            try:
                result, location = parser(location)
            except ParserError as pe:
                result, location = pe.node, L
                for k in self.variables__:  del self.variables__[k]
            except CancelError as ce:
                result = Node(EMPTY_NODE.name, '').with_pos(0)
                self.tree__.new_error(
                    result, f'Parsing was canceled at position: {ce.location} of {L}!', CANCELED)
                location = L
                for k in self.variables__:  del self.variables__[k]
            if result is EMPTY_NODE:  # don't ever deal out the EMPTY_NODE singleton!
                result = Node(EMPTY_PTYPE, '').with_pos(0)

            ## begin of error-handling

            # form here on, it is only error handling in case the parser has failed,
            # e.g. because of an incomplete match.

            # Not very elegant code, but there are many special cases to consider, e.g.
            # in order to allow proper error-reporting when testing sub-parsers with
            # lookaheads etc.

            if location < L and (complete_match is True
                    or (complete_match is not False and
                        re.fullmatch(getattr(self, complete_match),
                                     self.text__[location:]) is None)):
                rest = self.document__[location:]
                fwd = rest.find("\n") + 1 or len(rest)
                skip, location = rest[:fwd], location + fwd
                if result is None or (result.name == ZOMBIE_TAG and len(result) == 0):
                    err_pos = self.ff_pos__
                    associated_symbol = self.associated_symbol__(self.ff_parser__)
                    if associated_symbol is not self.ff_parser__:
                        err_pname = associated_symbol.pname + '->' + str(self.ff_parser__)
                    else:
                        err_pname = str(associated_symbol)
                    err_text = self.document__[err_pos:err_pos + 20]
                    if err_pos + 20 < len(self.document__) - 1:  err_text += ' ...'
                    # Check if a Lookahead-Parser did match. Needed for testing, because
                    # in a test case this is not necessarily an error.
                    if lookahead_failure_only(parser):
                        # error_msg = # f'Parser "{parser.name}" stopped before end, because ' \
                        error_msg = f'Parser {err_pname} did not match: »{err_text}« ' \
                                    f'- but only because of lookahead.'
                        error_code = PARSER_LOOKAHEAD_FAILURE_ONLY
                    else:
                        # error_msg = f'Parser "{parser.name}" stopped before end, because' \
                        error_msg = f'Parser {err_pname} did not match: »{err_text}«'
                        error_code = PARSER_STOPPED_BEFORE_END
                    if self.history_tracking__:
                        error_msg += '\n    Most advanced fail: %s\n    Last match:    %s;' % \
                                     (str(HistoryRecord.most_advanced_fail(self.history__)),
                                      str(HistoryRecord.last_match(self.history__)))
                else:
                    stitches.append(result)
                    error_msg = ""
                    for h in reversed(self.history__):
                        if h.node and (h.node.name != EMPTY_NODE.name or h.node.result
                                       or h.call_stack[-1][0].endswith(':SmartRE_Lookahead')):
                            for tag, _ in h.call_stack:
                                if tag in (':Lookahead', ':NegativeLookahead'):
                                    if h.node.pos + h.node.strlen() == len(self.document__):
                                        error_msg = "Parser stopped before end, " \
                                                  "but matched with lookahead."
                                    break
                                elif tag.endswith(':SmartRE_Lookahead'):
                                    if h.node.pos >= self.ff_pos__:
                                        error_msg = "Parser stopped before end, " \
                                                  "but might have matched with lookahead."
                                    break
                            else:
                                continue
                            break
                    else:
                        h = HistoryRecord([], Node(EMPTY_NODE.name, '').with_pos(0),
                                          StringView(''), (0, 0))
                    if h.status in (h.MATCH, h.DROP) and error_msg:
                        # TODO: this case still needs unit-tests and support in testing.py
                        err_pos = h.node.pos
                        error_code = PARSER_LOOKAHEAD_MATCH_ONLY
                        max_parser_dropouts = -1  # no further retries!
                    else:
                        i = self.ff_pos__ if self.ff_pos__ >= 0 else tail_pos(stitches)
                        err_pos = i
                        fs = self.document__[i:i + 10].replace('\n', '\\n')
                        if i + 10 < len(self.document__) - 1:  fs += '...'
                        root_name = self.start_parser__.symbol
                        error_msg = f'Parser "{root_name}" ' \
                            f"stopped before end, at: »{fs}«" + \
                            (("Trying to recover" +
                              (" but stopping history recording at this point."
                               if self.history_tracking__ else "..."))
                             if len(stitches) < self.max_parser_dropouts__
                             else " too often!" if self.max_parser_dropouts__ > 1 else " " +
                             "Terminating parser.")
                        error_code = PARSER_STOPPED_BEFORE_END
                stitch = Node(ZOMBIE_TAG, skip).with_pos(tail_pos(stitches))
                stitches.append(stitch)
                if stitch.pos > 0:
                    if self.ff_pos__ > err_pos:
                        l, c = line_col(linebreaks(self.document__), self.ff_pos__)
                        error_msg = f'Farthest Fail at {l}:{c}, ' + error_msg
                    err_pos = max(err_pos, stitch.pos)
                if len(stitches) > 2:
                    error_msg = f'Error after {len(stitches) - 2}. reentry: ' + error_msg
                    error_code = PARSER_STOPPED_ON_RETRY
                    err_pos = stitch.pos  # in this case stich.pos is more important than ff_pos
                if error_code in {PARSER_LOOKAHEAD_MATCH_ONLY,
                                  PARSER_LOOKAHEAD_FAILURE_ONLY,
                                  PARSER_STOPPED_BEFORE_END} \
                        or not any(e.pos == err_pos for e in self.tree__.errors if is_error(e)):
                    error = Error(error_msg, err_pos, error_code)
                    self.tree__.add_error(stitch, error)
                    if self.history_tracking__:
                        lc = line_col(self.document_lbreaks__, error.pos)
                        self.history__.append(HistoryRecord(
                            [(stitch.name, stitch.pos)], stitch,
                            self.document__[error.pos:], lc, [error]))
            else:
                # if complete_match is not True, ignore the rest and leave while loop
                if location < L and not isinstance(complete_match, bool):
                    # match was complete except for trailing whitespace
                    if result is None: result = Node(EMPTY_PTYPE, '').with_pos(0)
                    self.tree__.add_error(result, Error(
                        f'Parser "{parser.effective_pname()}" '
                        f'stopped before end, because of trailing whitespace.',
                        location, PARSER_STOPPED_BEFORE_END_WARNING))
                location = L
        if stitches:
            if location < L:
                stitches.append(Node(ZOMBIE_TAG, self.document__[location:])\
                                .with_pos(tail_pos(stitches)))
            result = Node(ZOMBIE_TAG, tuple(stitches)).with_pos(0)
        if any(self.variables__.values()):
            # capture stack not empty will only be reported for root-parsers
            # to avoid false negatives when testing
            error_msg = "Capture-stack not empty after end of parsing: " \
                + ', '.join(f'{v} {len(l)} {"items" if len(l) > 1 else "item"}'
                            for v, l in self.variables__.items() if len(l) >= 1)
            if parser.apply_to_trail(has_non_autocaptured_symbols):
                from DHParser.parse_combinators import Capture
                if all(cast(Capture, self[v]).can_capture_zero_length
                       for v, l in self.variables__.items() if len(l) >= 1):
                    error_code = CAPTURE_STACK_NOT_EMPTY_WARNING
                elif parser is self.root_parser__:
                    error_code = CAPTURE_STACK_NOT_EMPTY
                else:
                    error_code = CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY
            else:
                error_code = AUTOCAPTURED_SYMBOL_NOT_CLEARED if parser is self.root_parser__ \
                             else AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT
            if result:
                if result.children:
                    # add another child node at the end to ensure that the position
                    # of the error will be the end of the text. Otherwise, the error
                    # message above ("...after end of parsing") would appear illogical.
                    error_node = Node(ZOMBIE_TAG, '').with_pos(tail_pos(result.children))
                    self.tree__.new_error(error_node, error_msg, error_code)
                    result.result = result.children + (error_node,)
                else:
                    self.tree__.new_error(result, error_msg, error_code)

        ## end of error-handling

        self.tree__.swallow(result, self.text__, source_mapping)
        self.tree__.stage = 'CST'
        # if not self.tree__.source:  self.tree__.source = document
        self.start_parser__ = None
        return self.tree__


    def match__(self,
                parser: Union[str, Parser],
                string: str,
                source_mapping: Optional[SourceMapFunc] = None) -> Optional[str]:
        """Returns the matched string, if the parser matches the
        beginning of a string or "None" if the parser does not match."""
        result = self(string, parser, source_mapping, complete_match=False)
        if has_errors(result.errors):
            return None
        else:
            return str(result)

    @deprecated("Grammar.match() is deprecated, use Grammar.match__() or match(grammar, ...) instead!")
    def match(self,
              parser: Union[str, Parser],
              string: str,
              source_mapping: Optional[SourceMapFunc] = None) -> Optional[str]:
        return self.match__(parser, string, source_mapping)


    def fullmatch__(self,
                    parser: Union[str, Parser],
                    string: str,
                    source_mapping: Optional[SourceMapFunc] = None) -> Optional[str]:
        """Returns the matched string, if the parser matches the
        complete string or "None" if the parser does not match."""
        result = self(string, parser, source_mapping, complete_match=True)
        if has_errors(result.errors):
            return None
        else:
            return str(result)

    @deprecated("Grammar.fullmatch() is deprecated, use Grammar.fullmatch__() or fullmatch(grammar, ...) instead!")
    def fullmatch(self,
                  parser: Union[str, Parser],
                  string: str,
                  source_mapping: Optional[SourceMapFunc] = None) -> Optional[str]:
        return self.fullmatch__(parser, string, source_mapping)


    def set_cancel_query__(self):
        if self.cancel_query__ != self.cancel_query_last__:
            for p in self.all_parsers__:
                if isinstance(p, LeafParser):
                    if self.cancel_query__ is None:
                        p.set_proxy(None)
                    elif p._parse_proxy == p._parse:
                        p.set_proxy(cancel_proxy)
                    else:
                        assert p._parse_proxy.__name__ in ("cancel_proxy", "trace_history"), \
                            f"DHParser-Error: Currently, cancel_query cannot be used in " \
                            f"combination with {p._parse_proxy.__name__}."
            self.cancel_query_last__ = self.cancel_query__
        self.cancel_interval__ = CANCEL_QUERY_INTERVAL


    @property
    def document_lbreaks__(self) -> List[int]:
        if not self._document_lbreaks__:
            self._document_lbreaks__ = linebreaks(self.document__)
        return self._document_lbreaks__


    def push_rollback__(self, location, func):
        """
        Adds a rollback function that either removes or re-adds
        values on the variable stack ("self.variables") that have been
        added (or removed) by Capture or Pop Parsers, the results of
        which have been dismissed.
        """
        self.rollback__.append((location, func))
        self.last_rb__loc__ = location
        # memoization must be suspended to allow recapturing of variables
        self.suspend_memoization__ = True
        # memoization will be turned back on again in Parser.__call__ after
        # the parser that called push_rollback__() has returned.
        # print("PUSH", self.document__[location:location+10].replace('\n', '\\n'), dict(self.variables__))


    def rollback_to__(self, location):
        """
        Rolls back the variable stacks ("self.variables") to its
        state at an earlier location in the parsed document.
        """
        while self.rollback__ and self.rollback__[-1][0] >= location:
            _, rollback_func = self.rollback__.pop()
            # assert not loc > self.last_rb__loc__, \
            #     "Rollback confusion: line %i, col %i < line %i, col %i" % \
            #     (*line_col(self.document__, len(self.document__) - loc),
            #      *line_col(self.document__, len(self.document__) - self.last_rb__loc__))
            rollback_func()
        self.last_rb__loc__ = self.rollback__[-1][0] if self.rollback__ \
            else -2  # (self.document__.__len__() + 1)
        # print("POP", self.document__[location:location + 10].replace('\n', '\\n'), dict(self.variables__))

    def as_ebnf__(self) -> str:
        """
        Serializes the Grammar object as a grammar-description in the
        Extended Backus-Naur-Form. Does not serialize directives and
        may contain abbreviations with three dots " ... " for very long
        expressions.
        """
        ebnf = ['# This grammar does not include any of the DHParser-specific ',
                '# directives and may contain abbreviations ("...")!', '']
        for entry, parser in self.__dict__.items():
            if isinstance(parser, Parser) and sane_parser_name(entry):
                ebnf.append(str(parser))
        ebnf.append('')
        return '\n'.join(ebnf)


    def associated_symbol__(self, parser: Parser) -> Parser:
        r"""Returns the closest named parser that contains "parser".
        If "parser" is a named parser itself, "parser" is returned.
        If "parser" is not connected to any symbol in the Grammar,
        an AttributeError is raised. Example::

            >>> from DHParser.parse_combinators import Series, Whitespace, RegExp
            >>> word = Series(RegExp(r'\w+'), Whitespace(r'\s*'))
            >>> word.pname = 'word'
            >>> gr = Grammar(word)
            >>> anonymous_re = gr['word'].parsers[0]
            >>> gr.associated_symbol__(anonymous_re).pname
            'word'
        """
        from DHParser.parse_combinators import ForwardBase
        symbol = self.associated_symbol_cache__.get(parser, None)   # type: Optional[Parser]
        if symbol:  return symbol

        def find_symbol_for_parser(ptrail: ParserTrail) -> Optional[bool]:
            nonlocal symbol, parser
            if parser in ptrail[-1].sub_parsers:
                for p in reversed(ptrail):
                    if p.pname:
                        # save the name of the closest containing named parser
                        symbol = p
                        return True  # stop searching
            return False  # continue searching

        if isinstance(parser, ForwardBase) and cast(ForwardBase, parser).parser.pname:
            symbol = cast(ForwardBase, parser).parser
        elif parser.pname:
            symbol = parser
        else:
            if not self.root_parser__.apply_to_trail(find_symbol_for_parser):
                for resume_parser in self.unconnected_parsers__:
                    if resume_parser.apply_to_trail(find_symbol_for_parser):
                        break
            if symbol is None:
                raise AttributeError('Parser %s (%i) is not contained in Grammar!'
                                     % (str(parser), id(parser)))

        self.associated_symbol_cache__[parser] = symbol
        return symbol


    def fill_associated_symbol_cache__(self):
        """Pre-fills the associated symbol cache with an algorithm that
        is more efficient than filling the cache by calling
        "associated_symbol__()" on each parser individually.
        """
        from DHParser.parse_combinators import ForwardBase
        symbol = get_parser_placeholder()

        def add_anonymous_descendants(p: Parser):
            nonlocal symbol
            self.associated_symbol_cache__[p] = symbol
            for d in p.sub_parsers:
                if not d.effective_pname():
                    add_anonymous_descendants(d)

        for p in self.all_parsers__:
            if isinstance(p, ForwardBase) and cast(ForwardBase, p).parser.pname:
                symbol = cast(ForwardBase, p).parser
                self.associated_symbol_cache__[p] = symbol
                add_anonymous_descendants(symbol)
            elif p.pname:
                symbol = p
                add_anonymous_descendants(symbol)


    def static_analysis__(self) -> List[AnalysisError]:
        """
        Checks the parser tree statically for possible errors.

        This function is called by the constructor of class Grammar and does
        not need to (and should not) be called externally.

        :return: a list of error-tuples consisting of the narrowest containing
            named parser (i.e. the symbol on which the failure occurred),
            the actual parser that failed and an error object.
        """
        error_list = []  # type: List[AnalysisError]
        leaf_state = dict()  # type: Dict[Parser, Optional[bool]]

        def has_leaf_parsers(prsr: Parser) -> bool:
            def leaf_parsers(p: Parser) -> Optional[bool]:
                if p in leaf_state:
                    return leaf_state[p]
                if p.sub_parsers:
                    leaf_state[p] = None
                    state = any(leaf_parsers(s) for s in p.sub_parsers)  # type: Optional[bool]
                    if not state and any(leaf_state[s] is None for s in p.sub_parsers):
                        state = None
                else:
                    state = True
                leaf_state[p] = state
                return state

            # remove parsers with unknown state (None) from cache
            state_unknown = [p for p, s in leaf_state.items() if s is None]
            for p in state_unknown:
                del leaf_state[p]

            result = leaf_parsers(prsr) or False  # type: bool
            leaf_state[prsr] = result
            return result

        self.fill_associated_symbol_cache__()
        # cache = dict()  # type: Dict[Parser, MutableSet[Parser]]
        # for debugging: all_parsers = sorted(list(self.all_parsers__), key=lambda p:p.pname)
        for parser in self.all_parsers__:
            error_list.extend(parser.static_analysis())
            assert self.document__ is EMPTY_STRING_VIEW
            if parser.pname and not has_leaf_parsers(parser):
                from DHParser.parse_combinators import CombinedParser
                error_list.append(AnalysisError(parser.symbol, parser, Error(
                    'Parser %s is entirely cyclical and, therefore, cannot even touch '
                    'the parsed document' % cast('CombinedParser', parser).location_info(),
                    0, PARSER_NEVER_TOUCHES_DOCUMENT)))
        return error_list


def match(grammar: Grammar,
          parser: Union[str, Parser],
          string: str,
          source_mapping: Optional[SourceMapFunc] = None) -> Optional[str]:
    """See :py:func:`Grammar.match__`"""
    return grammar.match__(parser, string, source_mapping)


def fullmatch(grammar: Grammar,
              parser: Union[str, Parser],
              string: str,
              source_mapping: Optional[SourceMapFunc] = None) -> Optional[str]:
    """See :py:func:`Grammar.fullmatch__`"""
    return grammar.fullmatch__(parser, string, source_mapping)


ParserCallable: TypeAlias = Union[Grammar, Callable[[str], RootNode], functools.partial]
ParserFactory: TypeAlias = Union[Callable[[], ParserCallable], functools.partial]


def dsl_error_msg(parser: Parser, error_str: str) -> str:
    """
    Returns an error message for errors in the parser configuration,
    e.g. errors that result in infinite loops.

    :param parser:  The parser where the error was noticed. Note
            that this is not necessarily the parser that caused the
            error but only where the error became apparent.
    :param  error_str:  A short string describing the error.
    :return: An error message string including the call stack if
        history tracking has been enabled in the grammar object.
    """
    msg = ["DSL parser specification:", error_str, 'Caught by parser "%s".' % str(parser)]
    if parser.grammar.history__:
        msg.extend(["\nCall stack:", parser.grammar.history__[-1].stack])
    else:
        msg.extend(["\nEnable history tracking in Grammar object to display call stack."])
    return " ".join(msg)


def dsl_error(parser, node, error_str, error_code):
    parser.grammar.tree__.new_error(node, dsl_error_msg(parser, error_str), error_code)

