# parse.py - parser combinators for DHParser
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
Module ``parse`` contains the python classes and functions for
DHParser's packrat-parser. It's central class is the
``Grammar``-class, which is the base class for any concrete
Grammar. Grammar-objects are callable and parsing is done by
calling a Grammar-object with a source text as argument.

The different parsing functions are callable descendants of class
``Parser``. Usually, they are organized in a tree and defined
within the namespace of a grammar-class. See ``ebnf.EBNFGrammar``
for an example.

>>> from DHParser.parse import * 

"""

from bisect import bisect_left
from collections import defaultdict, namedtuple
import copy
from functools import lru_cache
from typing import Callable, cast, List, Tuple, Set, Dict, \
    DefaultDict, Sequence, Union, Optional, Iterator, Hashable

from DHParser.configuration import get_config_value
from DHParser.error import Error, ErrorCode, MANDATORY_CONTINUATION, \
    UNDEFINED_RETRIEVE, PARSER_LOOKAHEAD_FAILURE_ONLY, \
    PARSER_LOOKAHEAD_MATCH_ONLY, PARSER_STOPPED_BEFORE_END, PARSER_NEVER_TOUCHES_DOCUMENT, \
    MALFORMED_ERROR_STRING, MANDATORY_CONTINUATION_AT_EOF, DUPLICATE_PARSERS_IN_ALTERNATIVE, \
    CAPTURE_WITHOUT_PARSERNAME, CAPTURE_DROPPED_CONTENT_WARNING, LOOKAHEAD_WITH_OPTIONAL_PARSER, \
    BADLY_NESTED_OPTIONAL_PARSER, BAD_ORDER_OF_ALTERNATIVES, BAD_MANDATORY_SETUP, \
    OPTIONAL_REDUNDANTLY_NESTED_WARNING, CAPTURE_STACK_NOT_EMPTY, BAD_REPETITION_COUNT, \
    AUTOCAPTURED_SYMBOL_NOT_CLEARED, RECURSION_DEPTH_LIMIT_HIT, CAPTURE_STACK_NOT_EMPTY_WARNING, \
    MANDATORY_CONTINUATION_AT_EOF_NON_ROOT, CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY, \
    AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT, ERROR_WHILE_RECOVERING_FROM_ERROR, \
    ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING, PARSER_STOPPED_ON_RETRY, ERROR, \
    SourceMapFunc, has_errors
from DHParser.log import CallItem, HistoryRecord
from DHParser.preprocess import BEGIN_TOKEN, END_TOKEN, RX_TOKEN_NAME
from DHParser.stringview import StringView, EMPTY_STRING_VIEW
from DHParser.nodetree import ChildrenType, Node, RootNode, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, ZOMBIE_TAG, EMPTY_NODE, EMPTY_PTYPE, ResultType, LEAF_NODE
from DHParser.toolkit import sane_parser_name, escape_ctrl_chars, re, cython, \
    abbreviate_middle, RX_NEVER_MATCH, RxPatternType, linebreaks, line_col


__all__ = ('ParserError',
           'ApplyFunc',
           'FlagFunc',
           'ParseFunc',
           'Parser',
           'AnalysisError',
           'GrammarError',
           'Grammar',
           'Always',
           'Never',
           'AnyChar',
           'PreprocessorToken',
           'Text',
           'DropText',
           'RegExp',
           'update_scanner',
           'RE',
           'TKN',
           'Whitespace',
           'DropRegExp',
           'mixin_comment',
           'mixin_nonempty',
           'CombinedParser',
           'TreeReduction',
           'UnaryParser',
           'NaryParser',
           'Drop',
           'Synonym',
           'Option',
           'ZeroOrMore',
           'OneOrMore',
           'NO_MANDATORY',
           'MandatoryNary',
           'Series',
           'Alternative',
           'longest_match',
           'INFINITE',
           'Counted',
           'Interleave',
           'Required',
           'Lookahead',
           'NegativeLookahead',
           'Lookbehind',
           'NegativeLookbehind',
           'is_context_sensitive',
           'ContextSensitive',
           'Capture',
           'Retrieve',
           'Pop',
           'last_value',
           'optional_last_value',
           'matching_bracket',
           'Capture',
           'Retrieve',
           'Pop',
           'Forward')


########################################################################
#
# ParserError class
#
########################################################################


class ParserError(Exception):
    """
    A ``ParserError`` is thrown for those parser errors that allow the
    controlled re-entrance of the parsing process after the error occurred.
    If a reentry-rule has been configured for the parser where the error
    occurred, the parser guard can resume the parsing process.

    Currently, the only case when a ``ParserError`` is thrown (and not some
    different kind of error like ``UnknownParserError``) is when a `Series`-
    or `Interleave`-parser detects a missing mandatory element.
    """
    def __init__(self,
                 parser: 'Parser',
                 node: Node,
                 node_orig_len: int,
                 rest: StringView,
                 error: Error, *,
                 first_throw: bool):
        assert node is not None
        self.parser = parser  # type: 'Parser'
        self.node = node      # type: Node
        self.node_orig_len = node_orig_len  # type: int
        self.rest = rest      # type: StringView
        self.error = error    # type: Error
        self.first_throw = first_throw   # type: bool
        self.attributes_locked = frozenset({'parser', 'node', 'rest', 'error', 'first_throw'})
        self.callstack_snapshot = []  # type: List[CallItem]  # name, location

    def __setattr__(self, name, value):
        if name == "attributes_locked":
            self.__dict__[name] = value
        elif "attributes_locked" not in self.__dict__ \
                or name not in self.__dict__['attributes_locked']:
            self.__dict__[name] = value
        else:
            raise TypeError('Attribute %s of ParserError-object must not be reassigned!' % name)

    def __str__(self):
        return "%i: %s    %s (%s)" \
               % (self.node.pos, str(self.rest[:25]), repr(self.node), str(self.error))

    def new_PE(self, **kwargs):
        """Returns a new ParserError object with the same attribute values
        as `self`, except those that are reassigned in `**kwargs`.::

            >>> pe = ParserError(Parser(), Node('test', ""), 0, StringView(""), Error("", 0), first_throw=True)
            >>> pe_derived = pe.new_PE(first_throw = False)
            >>> pe.first_throw
            True
            >>> pe_derived.first_throw
            False
        """
        args = {"parser": self.parser,
                "node": self.node,
                "node_orig_len": self.node_orig_len,
                "rest": self.rest,
                "error": self.error,
                "first_throw": self.first_throw}
        assert len(kwargs.keys() - args.keys()) == 0, str(kwargs.keys() - args.keys())
        args.update(kwargs)
        pe = ParserError(**args)
        pe.callstack_snapshot = self.callstack_snapshot
        return pe


PatternMatchType = Union[RxPatternType, str, Callable, 'Parser']
ErrorMessagesType = List[Tuple[PatternMatchType, str]]
ResumeList = Sequence[PatternMatchType]  # list of strings or regular expressions
ReentryPointAlgorithm = Callable[[StringView, int, int], Tuple[int, int]]
# (text, start point, end point) => (reentry point, match length)
# A return value of (-1, x) means that no reentry point before the end of the document was found


# @cython.returns(cython.int)
# must not use: @functools.lru_cache(), because resume-function may contain
# context sensitive parsers!!!
@cython.locals(upper_limit=cython.int, closest_match=cython.int, pos=cython.int)
def reentry_point(rest: StringView,
                  rules: ResumeList,
                  comment_regex,
                  search_window: int = -1) -> Tuple[int, Node]:
    """
    Finds the point where parsing should resume after a ParserError has been caught.
    The algorithm makes sure that this reentry-point does not lie inside a comment.
    The re-entry point is always the point after the end of the match of the regular
    expression defining the re-entry point. (Use look ahead, if you want to define
    the re-entry point by what follows rather than by what text precedes the point.)

    REMARK: The algorithm assumes that any stretch of the document that matches
    `comment_regex` is actually a comment. It is possible to define grammars,
    where the use of comments is restricted to certain areas and that allow to
    use constructs that look like comments (i.e. will be matched by `comment_regex`)
    but are none in other areas. For example::

            my_string = "# This is not a comment"; foo()  # This is a comment
            bar()

    Here the reentry-algorithm would overlook `foo()` and jump directly to `bar()`.
    However, since the reentry-algorithm only needs to be good enough to do its
    work, this seems acceptable.

    :param rest:  The rest of the parsed text or, in other words, the point where
        a ParserError was thrown
    :param rules: A list of strings, regular expressions or search functions.
        The rest of the text is searched for each of these. The closest match
        is the point where parsing will be resumed
    :param comment_regex: A regular expression object that matches comments
    :param search_window: The maximum size of the search window for finding the
        reentry-point. A value smaller than zero means that the complete remaining
        text will be searched. A value of zero effectively turns of resuming after
        error
    :return: A tuple of integer index of the closest reentry point and a Node
        capturing all text from ``rest`` up to this point or ``(-1, None)`` if no
        reentry-point was found.
    """
    upper_limit = len(rest) + 1
    closest_match = upper_limit
    skip_node = None
    comments = None  # type: Optional[Iterator]
    if search_window < 0:
        search_window = len(rest)

    @cython.locals(a=cython.int, b=cython.int)
    def next_comment() -> Tuple[int, int]:
        """Returns the [start, end[ intervall of the next comment in the text.
        The comment-iterator start at the beginning of the `rest` of the
        document and is reset for each search rule.
        """
        nonlocal rest, comments
        if comments:
            try:
                m = next(comments)
                a, b = m.span()
                return rest.index(a), rest.index(b)
            except StopIteration:
                comments = None
        return -1, -2

    @cython.locals(start=cython.int)
    def str_search(s, start: int = 0) -> Tuple[int, int]:
        """Returns the starting position of the next occurrence of `s` in
        the `rest` of the document beginning with `start` and the length
        of the match, which in this case is always the length of `s` itself.
        If there is no match, the returned starting position will be -1.
        """
        nonlocal rest
        return rest.find(s, start, start + search_window), len(s)

    @cython.locals(start=cython.int, end=cython.int)
    def rx_search(rx, start: int = 0) -> Tuple[int, int]:
        """Returns the staring position and the length of the next match of
        the regular expression `rx` in the `rest` of the document, starting
        with `start`.
        If there is no match, the returned starting position will be -1.
        """
        nonlocal rest
        m = rest.search(rx, start, start + search_window)
        if m:
            begin, end = m.span()
            return rest.index(begin), end - begin
        return -1, 0

    def algorithm_search(func: ReentryPointAlgorithm, start: int = 0):
        """Returns the next match as a tuple of position and length that
        the reentry-point-search-function `func` yields.
        """
        nonlocal rest
        return func(rest, start, start + search_window)

    @cython.returns(cython.int)
    @cython.locals(a=cython.int, b=cython.int, k=cython.int, length=cython.int)
    def entry_point(search_func, search_rule) -> int:
        """Returns the next reentry-point outside a comment that `search_func`
        yields. If no reentry point is found, the first position after the
        end of the text ("upper limit") is returned."""
        a, b = next_comment()
        k, length = search_func(search_rule)
        while a < b <= k + length:
            a, b = next_comment()
        # find next as long as start or end point of resume regex are inside a comment
        while (a < k < b) or (a < k + length < b):
            k, length = search_func(search_rule, b)
            while a < b <= k:
                a, b = next_comment()
        return k + length if k >= 0 else upper_limit

    # find the closest match
    for rule in rules:
        comments = rest.finditer(comment_regex)
        if isinstance(rule, Parser):
            parser = cast(Parser, rule)
            grammar = parser.grammar
            save = grammar.history_tracking__
            grammar.history_tracking__ = False
            try:
                _node, _text = parser(rest)
            except ParserError as pe:
                grammar.tree__.new_error(
                    grammar.tree__,
                    f"Error while searching re-entry point with parser {parser}: {pe}",
                    ERROR_WHILE_RECOVERING_FROM_ERROR)
                _node, _text = None, ''
            grammar.history_tracking__ = save
            if _node:
                pos = len(rest) - len(_text)
                if pos < closest_match:
                    closest_match = pos
                    skip_node = _node
        else:
            if callable(rule):
                search_func = algorithm_search
            elif isinstance(rule, str):
                search_func = str_search
            else:
                search_func = rx_search
            pos = entry_point(search_func, rule)
            if pos < closest_match:
                skip_node = None
                closest_match = pos

    # in case no rule matched return -1
    if closest_match == upper_limit:
        closest_match = -1
    if skip_node is None:
        skip_node = Node(ZOMBIE_TAG, rest[:max(closest_match, 0)])
    return closest_match, skip_node


########################################################################
#
# Parser base class
#
########################################################################


ParsingResult = Tuple[Optional[Node], StringView]
MemoizationDict = Dict[int, ParsingResult]

ApplyFunc = Callable[[List['Parser']], Optional[bool]]
# The return value of `True` stops any further application
FlagFunc = Callable[[ApplyFunc, Set[ApplyFunc]], bool]
ParseFunc = Callable[['Parser', StringView], ParsingResult]
ParserContext = List['Parser']


class Parser:
    """
    (Abstract) Base class for Parser combinator parsers. Any parser
    object that is actually used for parsing (i.e. no mock parsers)
    should be derived from this class.

    Since parsers can contain other parsers (see classes UnaryOperator
    and NaryOperator) they form a cyclical directed graph. A root
    parser is a parser from which all other parsers can be reached.
    Usually, there is one root parser which serves as the starting
    point of the parsing process. When speaking of "the root parser"
    it is this root parser object that is meant.

    There are two different types of parsers:

    1. *Named parsers* for which a name is set in field `parser.pname`.
       The results produced by these parsers can later be retrieved in
       the AST by the parser name.

    2. *Disposable parsers* where the name-field just contains the empty
       string. AST-transformation of disposable parsers can be hooked
       only to their class name, and not to the individual parser.

    Parser objects are callable and parsing is done by calling a parser
    object with the text to parse.

    If the parser matches it returns a tuple consisting of a node
    representing the root of the concrete syntax tree resulting from the
    match as well as the substring `text[i:]` where i is the length of
    matched text (which can be zero in the case of parsers like
    `ZeroOrMore` or `Option`). If `i > 0` then the parser has "moved
    forward".

    If the parser does not match it returns `(None, text). **Note** that
    this is not the same as an empty match `("", text)`. Any empty match
    can for example be returned by the `ZeroOrMore`-parser in case the
    contained parser is repeated zero times.

    Attributes and Properties:

        pname:  The parser's name.

        disposable: A property indicating that the parser returns
                anonymous nodes. For performance
                reasons this is implemented as an object variable rather
                than a property. This property should always be equal to
                `self.name[0] == ":"`.

        drop_content: A property (for performance reasons implemented as
                simple field) that, if set, induces the parser not to return
                the parsed content or subtree if it has matched but the
                dummy `EMPTY_NODE`. In effect the parsed content will be
                dropped from the concrete syntax tree already. Only
                anonymous (or pseudo-anonymous) parsers are allowed to
                drop content.

        node_name: The name for the nodes that are created by
                the parser. If the parser is named, this is the same as
                `pname`, otherwise it is the name of the parser's type
                prefixed with a colon ":".

        eq_class: A unique number for the class of functionally
                equivalent parsers that this parser belongs to.
                (This serves the purpose of optimizing memoization,
                by tying memoization dictionaries to the classes
                of functionally equivalent parsers, rather than to
                the individual parsers themselves.)

        visited:  Mapping of places this parser has already been to
                during the current parsing process onto the results the
                parser returned at the respective place. This dictionary
                is used to implement memoizing.

        proxied: The original `_parse()`-method is stored here, if a
                proxy (e.g. a tracing debugger) is installed via the
                `set_proxy()`-method.

        _grammar:  A reference to the Grammar object to which the parser
                is attached.

        _symbol:  The name of the closest named parser to which this
                parser is connected in a grammar. If pname is not the
                empty string, this will become the same as pname, when
                the property `symbol` is read for the first time.
    """

    def __init__(self) -> None:
        # assert isinstance(name, str), str(name)
        self.pname = ''               # type: str
        self.disposable = True        # type: bool
        self.drop_content = False     # type: bool
        self.node_name = self.ptype   # type: str
        self.eq_class = id(self)      # type: int
        # this indirection is required for Cython-compatibility
        self._parse_proxy = self._parse  # type: ParseFunc
        try:
            self._grammar = get_grammar_placeholder()  # type: Grammar
        except NameError:
            pass                      # ensures Cython-compatibility
        self._symbol = ''             # type: str
        self.reset()

    def __deepcopy__(self, memo):
        """Deepcopy method of the parser. Upon instantiation of a Grammar-
        object, parsers will be deep-copied to the Grammar object. If a
        derived parser-class changes the signature of the `__init__`-constructor,
        `__deepcopy__`-method must be replaced (i.e. overridden without
        calling the same method from the superclass) by the derived class.
        """
        duplicate = self.__class__()
        copy_parser_base_attrs(self, duplicate)
        return duplicate

    def __repr__(self):
        return self.pname + self.ptype

    def __str__(self):
        return self.pname + (' = ' if self.pname else '') + repr(self)

    @property
    def ptype(self) -> str:
        """Returns a type name for the parser. By default, this is the name of
        the parser class with an added leading colon ':'. """
        return ':' + self.__class__.__name__

    @property
    def symbol(self) -> str:
        """Returns the symbol with which the parser is associated in a grammar.
        This is the closest parser with a pname that contains this parser."""
        if not self._symbol:
            try:
                self._symbol = self.grammar.associated_symbol__(self).pname
            except AttributeError:
                # return an empty string, if parser is not connected to grammar,
                # but be sure not to save the empty string in self._symbol
                return ''
        return self._symbol

    @property
    def repr(self) -> str:
        """Returns the parser's name if it has a name and self.__repr___() otherwise."""
        return self.pname if self.pname else self.__repr__()

    def gen_memoization_dict(self) -> dict:
        """Create and return an empty memoization dictionary. This allows to customize
        memoization dictionaries. The default is to just return a new plain dictionary."""
        return dict()

    def reset(self):
        """Initializes or resets any parser variables. If overwritten,
        the `reset()`-method of the parent class must be called from the
        `reset()`-method of the derived class."""
        # global _GRAMMAR_PLACEHOLDER
        # grammar = self._grammar
        self.visited: MemoizationDict = self.grammar.get_memoization_dict__(self)

    @cython.locals(location=cython.int, gap=cython.int, i=cython.int)
    def __call__(self: 'Parser', text: StringView) -> ParsingResult:
        """Applies the parser to the given text. This is a wrapper method that adds
        the business intelligence that is common to all parsers. The actual parsing is
        done in the overridden method `_parse()`. This wrapper-method can be thought of
        as a "parser guard", because it guards the parsing process.
        """
        grammar = self._grammar
        location = grammar.document_length__ - text._len  # faster than len(text)?

        try:
            # rollback variable changing operation if parser backtracks to a position
            # before or at the location where the variable changing operation occurred
            if location <= grammar.last_rb__loc__:
                grammar.rollback_to__(location)

            # if location has already been visited by the current parser, return saved result
            visited = self.visited  # using local variable for better performance
            if location in visited:
                # no history recording in case of memoized results!
                return visited[location]

            save_suspend_memoization = grammar.suspend_memoization__
            grammar.suspend_memoization__ = False

            # now, the actual parser call!
            try:
                node, rest = self._parse_proxy(text)
            except ParserError as pe:
                # catching up with parsing after an error occurred
                gap = len(text) - len(pe.rest)
                rules = tuple(grammar.resume_rules__.get(
                    grammar.associated_symbol__(self).pname, []))
                rest = pe.rest[pe.node_orig_len:]
                i, skip_node = reentry_point(rest, rules, grammar.comment_rx__,
                                             grammar.reentry_search_window__)
                if i >= 0 or self == grammar.start_parser__:
                    # either a reentry point was found or the
                    # error has fallen through to the first level
                    assert pe.node._children or (not pe.node.result)
                    # apply reentry-rule or catch error at root-parser
                    if i < 0:  i = 0
                    try:
                        zombie = pe.node.pick_child(ZOMBIE_TAG)  # type: Optional[Node]
                    except (KeyError, ValueError):
                        zombie = None
                    if zombie and not zombie.result:
                        zombie.result = rest[:i]
                        tail = tuple()  # type: ChildrenType
                    else:
                        # nd.attr['err'] = pe.error.message
                        tail = (skip_node,)
                    rest = rest[i:]
                    if pe.first_throw:
                        node = pe.node
                        node.result = node._children + tail
                    else:
                        node = Node(
                            self.node_name,
                            (Node(ZOMBIE_TAG, text[:gap]).with_pos(location), pe.node) + tail) \
                            .with_pos(location)
                # if no re-entry point was found, do any of the following:
                elif pe.first_throw:
                    # just fall through
                    # TODO: Is this case still needed with module "trace"?
                    raise pe.new_PE(first_throw=False)
                elif grammar.tree__.errors[-1].code in \
                        (MANDATORY_CONTINUATION_AT_EOF, MANDATORY_CONTINUATION_AT_EOF_NON_ROOT):
                    # try to create tree as faithful as possible
                    node = Node(self.node_name, pe.node).with_pos(location)
                else:
                    # fall through but skip the gap
                    result = (Node(ZOMBIE_TAG, text[:gap]).with_pos(location), pe.node) if gap \
                        else pe.node  # type: ResultType
                    raise pe.new_PE(node=Node(self.node_name, result).with_pos(location),
                                    node_orig_len=pe.node_orig_len + gap,
                                    rest=text, first_throw=False)

            if node is None:
                if location > grammar.ff_pos__:
                    grammar.ff_pos__ = location
                    grammar.ff_parser__ = self
            elif node is not EMPTY_NODE:
                node._pos = location
            # grammar.suspend_memoization__ = is_context_sensitive(self.parser)
            if not grammar.suspend_memoization__:
                visited[location] = (node, rest)
                grammar.suspend_memoization__ = save_suspend_memoization

        except RecursionError:
            node = Node(ZOMBIE_TAG, str(text[:min(10, max(1, text.find("\n")))]) + " ...")
            node._pos = location
            error = Error("maximum recursion depth of parser reached; potentially due to too many "
                          "errors or left recursion!", location, RECURSION_DEPTH_LIMIT_HIT)
            grammar.tree__.add_error(node, error)
            grammar.most_recent_error__ = ParserError(self, node, node.strlen(), text, error,
                                                      first_throw=False)
            rest = EMPTY_STRING_VIEW

        return node, rest

    def __add__(self, other: 'Parser') -> 'Series':
        """The + operator generates a series-parser that applies two
        parsers in sequence."""
        if isinstance(other, Series):
            return cast('Series', other).__radd__(self)
        return Series(self, other)

    def __or__(self, other: 'Parser') -> 'Alternative':
        """The | operator generates an alternative parser that applies
        the first parser and, if that does not match, the second parser.
        """
        if isinstance(other, Alternative):
            return cast('Alternative', other).__ror__(self)
        return Alternative(self, other)

    def __mul__(self, other: 'Parser') -> 'Interleave':
        """The * operator generates an interleave-parser that applies
        the first parser and the second parser in any possible order
        until both match.
        """
        if isinstance(other, Interleave):
            return cast(Interleave, other).__rmul__(self)
        return Interleave(self, other)

    def _parse(self, text: StringView) -> ParsingResult:
        """Applies the parser to the given `text` and returns a node with
        the results or None as well as the text at the position right behind
        the matching string."""
        raise NotImplementedError

    def is_optional(self) -> Optional[bool]:
        """Returns `True`, if the parser can never fail, i.e. never yields
        `None`, instead of a node. Returns `False`, if the parser can fail.
        Returns `None` if it is not known whether the parser can fail.
        """
        return None

    def set_proxy(self, proxy: Optional[ParseFunc]):
        """Sets a proxy that replaces the _parse()-method. Call `set_proxy`
        with `None` to remove a previously set proxy. Typical use case is
        the installation of a tracing debugger. See module `trace`.
        """
        if proxy is None:
            self._parse_proxy = self._parse
        else:
            if not isinstance(proxy, type(self._parse)):
                # assume that proxy is a function and bind it to self
                proxy = proxy.__get__(self, type(self))
            else:
                # if proxy is a method it must be a method of self
                assert proxy.__self__ == self
            self._parse_proxy = cast(ParseFunc, proxy)

    def name(self, pname: str, disposable: bool = False) -> 'Parser':
        """Sets the parser name to `pname` and returns `self`."""
        self.pname = pname
        self.disposable = disposable
        if disposable:
            self.node_name = (':' + pname) if pname else self.ptype
        else:
            self.node_name = pname if pname else self.ptype
        return self

    @property
    def grammar(self) -> 'Grammar':
        try:
            # if not is_grammar_placeholder(self._grammar):
            #     return self._grammar
            # else:
            #     raise ValueError('Grammar has not yet been set!')
            return self._grammar
        except (AttributeError, NameError):
            raise AttributeError('Parser placeholder does not have a grammar!')

    @grammar.setter
    def grammar(self, grammar: 'Grammar'):
        try:
            if is_grammar_placeholder(self._grammar):
                self._grammar = grammar
                # self._grammar_assigned_notifier()
            elif self._grammar != grammar:
                raise AssertionError("Parser has already been assigned"
                                     "to a different Grammar object!")
        except AttributeError:
            pass  # ignore setting of grammar attribute for placeholder parser
        except NameError:  # Cython: No access to _GRAMMAR_PLACEHOLDER, yet :-(
            self._grammar = grammar

    def sub_parsers(self) -> Tuple['Parser', ...]:
        """Returns the list of sub-parsers if there are any.
        Overridden by Unary, Nary and Forward.
        """
        return tuple()

    def descendants(self) -> Iterator[ParserContext]:
        """Returns an iterator over the contexts of self and all descendant parsers,
        avoiding of circles."""
        visited = set()

        def descendants_(parser: Parser, ctx: ParserContext) -> Iterator[ParserContext]:
            if parser not in visited:
                visited.add(parser)
                ctx = ctx + [parser]
                yield ctx
                for p in parser.sub_parsers():
                    yield from descendants_(p, ctx)

        yield from descendants_(self, [])

    def apply(self, func: ApplyFunc) -> Optional[bool]:
        """
        Applies function `func(parser)` recursively to this parser and all
        descendant parsers as long as `func()` returns `None` or `False`.
        Traversal is pre-order. Stops the further application of `func` and
        returns `True` once `func` has returned `True`.

        If `func` has been applied to all descendant parsers without issuing
        a stop signal by returning `True`, `False` is returned.

        This use of the return value allows to use the `apply`-method both
        to issue tests on all descendant parsers (including self) which may be
        decided already after some parsers have been visited without any need
        to visit further parsers. At the same time `apply` can be used to simply
        apply a procedure to all descendant parsers (including self) without
        worrying about forgetting the return value of procedure, because a
        return value of `None` means "carry on".
        """
        for pctx in self.descendants():
            if func(pctx):
                return True
        return False

    def _signature(self) -> Hashable:
        """This method should be implemented by any non-abstract descendant
        parser class. The implementation must make sure that all instances
        that have the same signature always yield the same parsing result
        for the same piece of text.

        It does not hurt, but only wastes an opportunity for optimization,
        if two functionally equivalent parsers provide different signatures.
        It is a serious mistake, though, if two functionally non-equivalent
        parsers have the same signature.

        By returning `id(self)` this mistake will become impossible, but
        it will turn signature-based memoization-optimization off for
        this parser.
        """
        return id(self)

    def signature(self) -> Hashable:
        """Returns a value that is identical for two different
        parser objects if they are functionally equivalent, i.e.
        yield the same return value for the same call parameters:

        >>> a = Text('[')
        >>> b = Text('[')
        >>> c = Text(']')
        >>> a is b
        False
        >>> a.signature() == b.signature()
        True
        >>> a.signature() == c.signature()
        False

        The purpose of parser-signatures is to optimize better
        memoization in cases of code repetition in the grammar.

        DO NOT OVERRIDE THIS METHOD. In order to implement a
        signature function, the protected method `_signature`
        should be overridden instead.
        """
        return self.pname if self.pname else self._signature()


    def static_error(self, msg: str, code: ErrorCode) -> 'AnalysisError':
        return AnalysisError(self.symbol, self, Error(msg, 0, code))

    def static_analysis(self) -> List['AnalysisError']:
        """Analyses the parser for logical errors after the grammar has been
        instantiated."""
        return []


def copy_parser_base_attrs(src: Parser, duplicate: Parser):
    """Duplicates all attributes of the Parser-class from `src` to `duplicate`."""
    duplicate.pname = src.pname
    duplicate.disposable = src.disposable
    duplicate.drop_content = src.drop_content
    duplicate.node_name = src.node_name
    duplicate.eq_class = src.eq_class


def determine_eq_classes(root: Parser):
    """Sorts the parsers originating in root (imperfectly) into equivalence
    classes and assigns respective the class identifier to the `eq_class`-field
    of each parser."""
    eq_classes: Dict[Hashable, int] = {}

    def assign_eq_class(parser_stack: List[Parser]) -> bool:
        nonlocal eq_classes
        p = parser_stack[-1]
        signature = p.signature()
        p.eq_class = eq_classes.setdefault(signature, id(p))
        return False

    root.apply(assign_eq_class)


def Drop(parser: Parser) -> Parser:
    """Returns the parser with the `parser.drop_content`-property set to `True`."""
    assert parser.disposable, "Parser must be anonymous to be allowed to drop ist content."
    if isinstance(parser, Forward):
        cast(Forward, parser).parser.drop_content = True
    parser.drop_content = True
    return parser


PARSER_PLACEHOLDER = None  # type: Optional[Parser]
# Don't access PARSER_PLACEHOLDER directly, use get_parser_placeholder() instead


def get_parser_placeholder() -> Parser:
    global PARSER_PLACEHOLDER
    if PARSER_PLACEHOLDER is None:
        PARSER_PLACEHOLDER = Parser.__new__(Parser)  # Parser()
        PARSER_PLACEHOLDER.pname = ''
        PARSER_PLACEHOLDER.disposable = False
        PARSER_PLACEHOLDER.drop_content = False
        PARSER_PLACEHOLDER.node_name = ':PLACEHOLDER__'
        PARSER_PLACEHOLDER.eq_class = id(PARSER_PLACEHOLDER)
    return cast(Parser, PARSER_PLACEHOLDER)


def is_parser_placeholder(parser: Optional[Parser]) -> bool:
    """Returns True, if `parser` is `None` or merely a placeholder for a parser."""
    return not parser or parser.ptype == ":Parser"


# functions for analysing the parser tree/graph ###


def has_non_autocaptured_symbols(context: List[Parser]) -> Optional[bool]:
    """Returns True, if the context contains a Capture-Parser that is not
    shielded by a Retrieve-Parser. This is the case for captured symbols
    that are not "auto-captured" by a Retrieve-Parser.
    """
    for parser in context:
        if parser.ptype == ":Retrieve":
            break
        elif parser.ptype == ":Capture":
            p = cast(UnaryParser, parser).parser
            while p.ptype in (":Synonym", ":Forward"):
                p = cast(UnaryParser, p).parser
            if not isinstance(p, Retrieve):
                return True
    return None


########################################################################
#
# Grammar class, central administration of all parser of a grammar
#
########################################################################

def mixin_comment(whitespace: str, comment: str) -> str:
    """
    Returns a regular expression pattern that merges comment and whitespace
    regexps. Thus comments can occur wherever whitespace is allowed
    and will be skipped just as implicit whitespace.

    Note, that because this works on the level of regular expressions,
    nesting comments is not possible. It also makes it much harder to
    use directives inside comments (which isn't recommended, anyway).
    """
    if comment:
        whitespace = '(?:' + whitespace + ')'
        comment = '(?:' + comment + ')'
        return '(?:' + whitespace + '(?:' + comment + whitespace + ')*)'
    return whitespace


def mixin_nonempty(whitespace: str) -> str:
    r"""
    Returns a regular expression pattern that matches only if the regular
    expression pattern `whitespace` matches AND if the match is not empty.

    If `whitespace`  does not match the empty string '', anyway,
    then it will be returned unaltered.

    WARNING: ``mixin_nonempty()`` does not work for regular expressions the matched
    strings of which can be followed by a symbol that can also occur at
    the start of the regular expression.

    In particular, it does not work for fixed size regular expressions,
    that is / / or /   / or /\t/ won't work, but / */ or /\s*/ or /\s+/
    do work. There is no test for this. Fixed-size regular expressions
    run through `mixin_nonempty` will not match at anymore if they are applied
    to the beginning or the middle of a sequence of whitespaces!

    In order to be safe, your whitespace regular expressions should follow
    the rule: "Whitespace cannot be followed by whitespace" or "Either
    grab it all or leave it all".

    :param whitespace: a regular expression pattern
    :return: new regular expression pattern that does not match the empty
        string '' any more.
    """
    if re.match(whitespace, ''):
        return r'(?:(?=(.|\n))' + whitespace + r'(?!\1))'
    return whitespace


# # AnalysisError = Tuple[str, Parser, Error]      # pname, parser, error
# class AnalysisError(NamedTuple):
#     symbol: str
#     parser: Parser
#     error: Error

# collections.namedtuple needed for Cython compatibility
AnalysisError = namedtuple('AnalysisError',
    ['symbol',  # type: str
     'parser',  # type: Parser
     'error'    # type: Error
    ], module=__name__)


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


RESERVED_PARSER_NAMES = ('root__', 'dwsp__', 'wsp__', 'comment__', 'root_parser__', 'ff_parser__')


def reset_parser(ctx):
    return ctx[-1].reset()


class Grammar:
    r"""
    Class Grammar directs the parsing process and stores global state
    information of the parsers, i.e. state information that is shared
    accross parsers.

    Grammars are basically collections of parser objects, which are
    connected to an instance object of class Grammar. There exist two
    ways of connecting parsers to grammar objects: Either by passing
    the root parser object to the constructor of a Grammar object
    ("direct instantiation"), or by assigning the root parser to the
    class variable "root__" of a descendant class of class Grammar.

    Example for direct instantiation of a grammar::

        >>> number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        >>> number_parser = Grammar(number)
        >>> number_parser("3.1416").content
        '3.1416'

    Collecting the parsers that define a grammar in a descendant class of
    class Grammar and assigning the named parsers to class variables
    rather than global variables has several advantages:

    1. It keeps the namespace clean.

    2. The parser names of named parsers do not need to be passed to the
       constructor of the Parser object explicitly, but it suffices to
       assign them to class variables, which results in better
       readability of the Python code.
       See classmethod `Grammar._assign_parser_names__()`

    3. The parsers in the class do not necessarily need to be connected
       to one single root parser, which is helpful for testing and when
       building up a parser gradually from several components.

    As a consequence, though, it is highly recommended that a Grammar
    class should not define any other variables or methods with names
    that are legal parser names. A name ending with a double
    underscore '__' is *not* a legal parser name and can safely be
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
    field `parser.pname` contains the variable name after instantiation
    of the Grammar class. The parser will nevertheless remain anonymous
    with respect to the tag names of the nodes it generates, if its name
    is matched by the `disposable__` regular expression.
    If one and the same parser is assigned to several class variables
    such as, for example, the parser `expression` in the example above,
    which is also assigned to `root__`, the first name sticks.

    Grammar objects are callable. Calling a grammar object with a UTF-8
    encoded document, initiates the parsing of the document with the
    root parser. The return value is the concrete syntax tree. Grammar
    objects can be reused (i.e. called again) after parsing. Thus, it
    is not necessary to instantiate more than one Grammar object per
    thread.

    Grammar classes contain a few special class fields for implicit
    whitespace and comments that should be overwritten, if the defaults
    (no comments, horizontal right aligned whitespace) don't fit:

    Class Attributes:
        root__:  The root parser of the grammar. Theoretically, all parsers of the
                 grammar should be reachable by the root parser. However, for testing
                 of yet incomplete grammars class Grammar does not assume that this
                 is the case.

        resume_rules__: A mapping of parser names to a list of regular expressions
                that act as rules to find the reentry point if a ParserError was
                thrown during the execution of the parser with the respective name.

        skip_rules__: A mapping of parser names to a list of regular expressions
                that act as rules to find the reentry point if a ParserError was
                thrown during the execution of the parser with the respective name.

        error_messages__: A mapping of parser names to a Tuple of regalar expressions
                and error messages. If a mandatory violation error occurs on a
                specific symbol (i.e. parser name) and any of the regular expressions
                matches the error message of the first matching expression is used
                instead of the generic mandatory violation error messages. This
                allows to answer typical kinds of errors (say putting a colon ","
                where a semi-colon ";" is expected) with more informative error
                messages.

        disposable__: A regular expression to identify names of parsers that are
                assigned to class fields but shall nevertheless yield anonymous
                nodes (i.e. nodes the tag name of which starts with a colon ":"
                followed by the parser's class name).

        parser_initialization__:  Before the grammar class (!) has been initialized,
                 which happens upon the first time it is instantiated (see
                 `:func:_assign_parser_names()` for an explanation), this class
                 field contains a value other than "done". A value of "done" indicates
                 that the class has already been initialized.

        static_analysis_pending__: True as long as no static analysis (see the method
                with the same name for more information) has been done to check
                parser tree for correctness. Static analysis
                is done at instantiation and the flag is then set to false, but it
                can also be carried out once the class has been generated
                (by DHParser.ebnf.EBNFCompiler) and then be set to false in the
                definition of the grammar class already.

        static_analysis_errors__: A list of errors and warnings that were found in the
                static analysis

        parser_names__: The list of the names of all named parsers defined in the
                grammar class

        python_src__:  For the purpose of debugging and inspection, this field can
                 take the python src of the concrete grammar class
                 (see `dsl.grammar_provider`).

    Instance Attributes:
        all_parsers__:  A set of all parsers connected to this grammar object

        comment_rx__:  The compiled regular expression for comments. If no
                comments have been defined, it defaults to RX_NEVER_MATCH
                This instance-attribute will only be defined if a class-attribute
                with the same name does not already exist!

        start_parser__:  During parsing, the parser with which the parsing process
                was started (see method `__call__`) or `None` if no parsing process
                is running.

        unconnected_parsers__: A list of parsers that are not connected to the
                root parser. This list of parsers is collected during instantiation.

        resume_parsers__: A list of parsers that appear either in a resume-rule
                or a skip-rule. This is a subset of ``unconnected_parsers__``

        _dirty_flag__:  A flag indicating that the Grammar has been called at
                least once so that the parsing-variables need to be reset
                when it is called again.

        document__:  the text that has most recently been parsed or that is
                currently being parsed.

        document_length__:  the length of the document.

        document_lbreaks__ (property):  list of linebreaks within the document,
                starting with -1 and ending with EOF. This helps to generate line
                and column number for history recording and will only be
                initialized if :attr:`history_tracking__` is true.

        tree__: The root-node of the parsing tree. This variable is available
               for error-reporting already during parsing  via
               ``self.grammar.tree__.add_error``, but it references the full
               parsing tree only after parsing has been finished.

        _reversed__:  the same text in reverse order - needed by the `Lookbehind`-
                parsers.

        variables__:  A mapping for variable names to a stack of their respective
                string values - needed by the :class:`Capture`-, :class:`Retrieve`-
                and :class:`Pop`-parsers.

        rollback__:  A list of tuples (location, rollback-function) that are
                deposited by the :class:`Capture`- and :class:`Pop`-parsers.
                If the parsing process reaches a dead end then all
                rollback-functions up to the point to which it retreats will be
                called and the state of the variable stack restored accordingly.

        last_rb__loc__:  The last, i.e. most advanced location in the text
                where a variable changing operation occurred. If the parser
                backtracks to a location at or before last_rb__loc__ (i.e.
                location < last_rb__loc__) then a rollback of all variable
                changing operations is necessary that occurred after the
                location to which the parser backtracks. This is done by
                calling method :func:`rollback_to__(location)`.

        :ivar ff_pos__: The "farthest fail", i.e. the highest location in the
                document where a parser failed. This gives a good indication
                where and why parsing failed, if the grammar did not match
                a text.

        :ivar ff_parser__: The parser that failed at the "farthest fail"-location
                `ff_pos__`

        suspend_memoization__: A flag that if set suspends memoization of
                results from returning parsers. This flag is needed by the
                left-recursion handling algorithm (see `Parser.__call__`
                and `Forward.__call__`) as well as the context-sensitive
                parsers (see function `Grammar.push_rollback__()`).

        left_recursion__: Turns on left-recursion handling. This prevents the
                recursive descent parser to get caught in an infinite loop
                (resulting in a maximum recursion depth reached error) when
                the grammar definition contains left recursions.

        associated_symbol_cache__: A cache for the associated_symbol__()-method.

        # mirrored class attributes:

        static_analysis_pending__: A pointer to the class attribute of the same name.
                (See the description above.) If the class is instantiated with a
                parser, this pointer will be overwritten with an instance variable
                that serves the same function.

        static_analysis_errors__: A pointer to the class attribute of the same name.
                (See the description above.) If the class is instantiated with a
                parser, this pointer will be overwritten with an instance variable
                that serves the same function.

        # tracing and debugging support

        # These parameters are needed by the debugging functions in module
        # `trace.py`. They should not be manipulated by the users of class
        #  Grammar directly.

        history_tracking__:  A flag indicating that the parsing history is
                being tracked. This flag should not be manipulated by the
                user. Use `trace.set_tracer(grammar, trace.trace_history)` to
                turn (full) history tracking on and
                `trace.set_tracer(grammar, None)` to turn it off. Default is off.

        resume_notices__: A flag indicating that resume messages are generated
                in addition to the error messages, in case the parser was able
                to resume after an error. Use `trace.resume_notices(grammar)` to
                turn resume messages on and `trace.set_tracer(grammar, None)`
                to turn resume messages (as well as history recording) off.
                Default is off.

        call_stack__:  A stack of the tag names and locations of all parsers
                in the call chain to the currently processed parser during
                parsing. The call stack can be thought of as a breadcrumb path.
                This is required for recording the parser history (for debugging)
                and, eventually, i.e. one day in the future, for tracing through
                the parsing process.

        history__:  A list of history records. A history record is appended to
                the list each time a parser either matches, fails or if a
                parser-error occurs. See class `log.HistoryRecord`. History
                records store copies of the current call stack.

        moving_forward__: This flag indicates that the parsing process is currently
                moving forward. It is needed to reduce noise in history recording
                and should not be considered as having a valid value if history
                recording is turned off! (See :func:`Parser.__call__`)

        most_recent_error__: The most recent parser error that has occurred
                or `None`. This can be read by tracers. See module `trace`


        # Configuration parameters.

        # The values of these parameters are copied from the global configuration
        # in the constructor of the Grammar object. (see mpodule `configuration.py`)

        max_parser_dropouts__: Maximum allowed number of retries after errors
                where the parser would exit before the complete document has
                been parsed. Default is 1, as usually the retry-attemts lead
                to a proliferation of senseless error messages.

        reentry_search_window__: The number of following characters that the
                parser considers when searching a reentry point when a syntax error
                has been encountered. Default is 10.000 characters.
    """
    python_src__ = ''  # type: str
    root__ = get_parser_placeholder()   # type: Parser  # TODO: too early initialization of Parser?
    # root__ must be overwritten with the root-parser by grammar subclass
    parser_initialization__ = ["pending"]  # type: List[str]
    resume_rules__ = dict()        # type: Dict[str, ResumeList]
    skip_rules__ = dict()          # type: Dict[str, ResumeList]
    error_messages__ = dict()      # type: Dict[str, Tuple[PatternMatchType, str]]
    disposable__ = RX_NEVER_MATCH  # type: RxPatternType
    # some default values
    COMMENT__ = r''  # type: str  # r'#.*'  or r'#.*(?:\n|$)' if combined with horizontal wspc
    WHITESPACE__ = r'[ \t]*(?:\n[ \t]*)?(?!\n)'  # spaces plus at most a single linefeed
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)  # type: str
    static_analysis_pending__ = [True]  # type: List[bool]
    static_analysis_errors__ = []  # type: List[AnalysisError]
    parser_names__ = []            # type: List[str]

    @classmethod
    def _assign_parser_names__(cls):
        """
        Initializes the `parser.pname` fields of those
        Parser objects that are directly assigned to a class field with
        the field's name, e.g.::

            class Grammar(Grammar):
                ...
                symbol = RE(r'(?!\\d)\\w+')

        After the call of this method symbol.pname == "symbol" holds.
        Parser names starting or ending with a double underscore like
        ``root__`` will be ignored. See :func:`sane_parser_name()`

        This is done only once, upon the first instantiation of the
        grammar class!

        Attention: If there exists more than one reference to the same
        parser, only the first one will be chosen for python versions
        greater or equal 3.6.  For python version <= 3.5 an arbitrarily
        selected reference will be chosen. See PEP 520
        (www.python.org/dev/peps/pep-0520/) for an explanation of why.
        """
        if cls.parser_initialization__[0] != "done" and cls != Grammar:
            cdict = cls.__dict__
            # cls.static_analysis_errors__ = []
            cls.parser_names__ = []
            for entry, parser in cdict.items():
                if isinstance(parser, Parser) and entry not in RESERVED_PARSER_NAMES:
                    anonymous = True if cls.disposable__.match(entry) else False
                    assert anonymous or not parser.drop_content, entry
                    if isinstance(parser, Forward):
                        if not cast(Forward, parser).parser.pname:
                            cast(Forward, parser).parser.name(entry, anonymous)
                            # cast(Forward, parser).parser.pname = entry
                            # cast(Forward, parser).parser.disposable = anonymous
                    else:
                        parser.name(entry, anonymous)
                        # parser.pname = entry
                        # parser.disposable = anonymous
                    cls.parser_names__.append(entry)
            if not is_parser_placeholder(cls.root__):
                determine_eq_classes(cls.root__)
            # if cls != Grammar:
            cls.parser_initialization__ = ["done"]  # (over-)write subclass-variable


    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.root_parser__)
        duplicate.history_tracking__ = self.history_tracking__
        duplicate.resume_notices__ = self.resume_notices__
        duplicate.max_parser_dropouts__ = self.max_parser_dropouts__
        duplicate.reentry_search_window__ = self.reentry_search_window__
        return duplicate


    def _add_parser__(self, context: List[Parser]) -> None:
        """
        Adds the particular copy of the parser object to this
        particular instance of Grammar.
        """
        parser = context[-1]
        if parser not in self.all_parsers__:
            if parser.pname:
                # prevent overwriting instance variables or parsers of a different class
                # assert (parser.pname not in self.__dict__
                #         or isinstance(self.__dict__[parser.pname], parser.__class__)), \
                #     ('Cannot add parser "%s" because a field with the same name '
                #      'already exists in grammar object: %s!'
                #      % (parser.pname, str(self.__dict__[parser.pname])))
                if parser.pname in self.__dict__:
                    assert (isinstance(self.__dict__[parser.pname], Forward)
                            or isinstance(self.__dict__[parser.pname], parser.__class__)), \
                        ('Cannot add parser "%s" because a field with the same name '
                         'already exists in grammar object: %s!'
                         % (parser.pname, str(self.__dict__[parser.pname])))
                else:
                    setattr(self, parser.pname, parser)
            elif isinstance(parser, Forward):
                setattr(self, cast(Forward, parser).parser.pname, parser)
            # # see Parser.name()
            # if parser.disposable:
            #     parser.name = (':' + parser.pname) if parser.pname else parser.ptype
            # else:
            #     parser.name = parser.pname
            # parser.name(parser.pname, parser.disposable)
            self.all_parsers__.add(parser)
            parser.grammar = self


    def __init__(self, root: Parser = None, static_analysis: Optional[bool] = None) -> None:
        """Constructor of class Grammar.

        :param root: If not None, this is going to be the root parser of the grammar.
            This allows to first construct an ensemble of parser objects and then
            link those objects in a grammar-object, rather than adding the parsers
            as fields to a derived class of class Grammar. (See the doc-tests in this
            module for examples.)
        :param static_analysis: If not None, this overrides the config value
            "static_analysis".
        """
        self.all_parsers__ = set()             # type: Set[Parser]
        # add compiled regular expression for comments, if it does not already exist
        if not hasattr(self, 'comment_rx__') or self.comment_rx__ is None:
            if hasattr(self.__class__, 'COMMENT__') and self.__class__.COMMENT__:
                self.comment_rx__ = re.compile(self.__class__.COMMENT__)
            else:
                self.comment_rx__ = RX_NEVER_MATCH
        else:
            assert ((self.__class__.COMMENT__
                     and self.__class__.COMMENT__ == self.comment_rx__.pattern)
                    or (not self.__class__.COMMENT__ and self.comment_rx__ == RX_NEVER_MATCH))
        self.start_parser__ = None               # type: Optional[Parser]
        self._dirty_flag__ = False               # type: bool
        self.left_recursion__ = get_config_value('left_recursion')                # type: bool
        self.history_tracking__ = get_config_value('history_tracking')            # type: bool
        self.resume_notices__ = get_config_value('resume_notices')                # type: bool
        self.max_parser_dropouts__ = get_config_value('max_parser_dropouts')      # type: int
        self.reentry_search_window__ = get_config_value('reentry_search_window')  # type: int
        self.associated_symbol_cache__ = dict()                   # type: Dict[Parser, Parser]
        self._reset__()

        # prepare parsers in the class, first
        self.__class__._assign_parser_names__()

        # then deep-copy the parser tree from class to instance;
        # parsers not connected to the root object will be copied later
        # on demand (see Grammar.__getitem__()).
        # (Usually, all parsers should be connected to the root object. But
        # during testing and development this does not need to be the case.)
        if root:
            determine_eq_classes(root)
            self.root_parser__ = copy.deepcopy(root)
            if not self.root_parser__.pname:
                self.root_parser__.name("root", disposable=False)
                # TODO: Reset name and name after parsing has been finished
                # self.root_parser__.pname = "root"
                # self.root_parser__.disposable = False
            self.static_analysis_pending__ = [True]  # type: List[bool]
            self.static_analysis_errors__ = []       # type: List[AnalysisError]
        else:
            assert self.__class__ == Grammar or not is_parser_placeholder(self.__class__.root__),\
                "Please add `root__` field to definition of class " + self.__class__.__name__
            self.root_parser__ = copy.deepcopy(self.__class__.root__)
            self.static_analysis_pending__ = self.__class__.static_analysis_pending__
            self.static_analysis_errors__ = self.__class__.static_analysis_errors__
        self.static_analysis_caches__ = dict()  # type: Dict[str, Dict]

        self.root_parser__.apply(self._add_parser__)
        root_connected = frozenset(self.all_parsers__)

        assert 'root_parser__' in self.__dict__
        assert self.root_parser__ == self.__dict__['root_parser__']
        self.ff_parser__ = self.root_parser__
        self.root_parser__.apply(lambda ctx: ctx[-1].reset())
        self.unconnected_parsers__: List[Parser] = []
        self.resume_parsers__: List[Parser] = []
        resume_lists = []
        if hasattr(self, 'resume_rules__'):
            resume_lists.extend(self.resume_rules__.values())
        if hasattr(self, 'skip_rules__'):
            resume_lists.extend(self.skip_rules__.values())
        for l in resume_lists:
            for i in range(len(l)):
                if isinstance(l[i], Parser):
                    p = self[l[i].pname]
                    l[i] = p
                    if p not in root_connected:
                        self.unconnected_parsers__.append(p)
                        self.resume_parsers__.append(p)
                        p.apply(self._add_parser__)
        for name in self.__class__.parser_names__:
            parser = self[name]
            if parser not in root_connected:
                self.unconnected_parsers__.append(parser)
                parser.apply(self._add_parser__)

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
                # else:
                    # print(f'\nGrammar warnings in {self.__class__.__name__}!\n')
                    # for ae in analysis_errors:
                    #     print(f'{ae.symbol} -> {ae.parser}: {ae.error}')
                    # print('\n\n')

    def __str__(self):
        return self.__class__.__name__


    def __getitem__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            #  p = getattr(self, key, None)
            parser_template = getattr(self.__class__, key, None)
            if parser_template:
                # add parser to grammar object on the fly...
                parser = copy.deepcopy(parser_template)
                parser.apply(self._add_parser__)
                assert self[key] == parser
                return self[key]
            raise AttributeError(f'Unknown parser "{key}" in grammar {self.__class__.__name__}!')


    def __contains__(self, key):
        return key in self.__dict__ or hasattr(self, key)


    def _reset__(self):
        self.tree__: RootNode = RootNode()
        self.document__: StringView = EMPTY_STRING_VIEW
        self._reversed__: StringView = EMPTY_STRING_VIEW
        self.document_length__: int = 0
        self._document_lbreaks__: List[int] = []
        # variables stored and recalled by Capture and Retrieve parsers
        self.variables__: DefaultDict[str, List[str]] = defaultdict(lambda: [])
        self.rollback__: List[Tuple[int, Callable]] = []
        self.last_rb__loc__: int = -2
        self.suspend_memoization__: bool = False
        # memoization dictionaries, one per parser equivalence class
        self.memoization__: Dict[int, MemoizationDict] = {}
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


    def get_memoization_dict__(self, parser: Parser) -> MemoizationDict:
        """Returns the memoization dictionary for the parser's equivalence class.
        """
        try:
            return self.memoization__.setdefault(parser.eq_class, parser.gen_memoization_dict())
        except AttributeError:  # happens when grammar object is the _GRAMMAR_PLACEHOLDER
            return dict()


    def __call__(self,
                 document: str,
                 start_parser: Union[str, Parser] = "root_parser__",
                 source_mapping: Optional[SourceMapFunc] = None,
                 *, complete_match: bool = True) -> RootNode:
        """
        Parses a document with parser-combinators.

        Args:
            document (str): The source text to be parsed.
            start_parser (str or Parser): The name of the parser with which
                to start. This is useful for testing particular parsers
                (i.e. particular parts of the EBNF-Grammar.)
            complete_match (bool): If True, an error is generated, if
                `start_parser` did not match the entire document.
        Returns:
            Node: The root node to the parse tree.
        """

        @cython.returns(cython.int)
        def tail_pos(predecessors: Union[List[Node], Tuple[Node, ...], None]) -> int:
            """Adds the position after the last node in the list of
            predecessors to the node."""
            if predecessors:
                tail = predecessors[-1].pick(LEAF_NODE, reverse=True, include_root=True)
                return tail.pos + tail.strlen()
            return 0

        def lookahead_failure_only(parser):
            """EXPERIMENTAL!

            Checks if failure to match document was only due to a succeeding
            lookahead parser, which is a common design pattern that can break test
            cases. (Testing for this case allows to modify the error message, so
            that the testing framework knows that the failure is only a
            test-case-artifact and no real failure.
            (See test/test_testing.TestLookahead !))
            """
            def is_lookahead(name: str) -> bool:
                return (name in self and isinstance(self[name], Lookahead)
                        or name[0] == ':' and issubclass(eval(name[1:]), Lookahead))

            last_record = self.history__[-2] if len(self.history__) > 1 \
                else None  # type: Optional[HistoryRecord]
            return last_record and parser != self.root_parser__ \
                and any(h.status == HistoryRecord.MATCH
                        and any(is_lookahead(tn) and location >= len(self.document__)
                                for tn, location in h.call_stack)
                        for h in self.history__[:-1])

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
        self.document__ = StringView(document)
        self.document_length__ = len(self.document__)
        self._document_lbreaks__ = linebreaks(document) if self.history_tracking__ else []
        # done by reset: self.last_rb__loc__ = -1  # rollback location
        result = None  # type: Optional[Node]
        stitches = []  # type: List[Node]
        rest = self.document__
        if not rest:
            try:
                result, _ = parser(rest)
            except ParserError as pe:
                result = pe.node
            if result is None:
                result = Node(ZOMBIE_TAG, '').with_pos(0)
                if lookahead_failure_only(parser):
                    self.tree__.new_error(
                        result, 'Parser "%s" only did not match empty document '
                                'because of lookahead' % str(parser),
                        PARSER_LOOKAHEAD_FAILURE_ONLY)
                else:
                    self.tree__.new_error(
                        result, 'Parser "%s" did not match empty document.' % str(parser),
                        PARSER_STOPPED_BEFORE_END)

        # copy to local variable, so break condition can be triggered manually
        max_parser_dropouts = self.max_parser_dropouts__
        while rest and len(stitches) < max_parser_dropouts:
            try:
                result, rest = parser(rest)
            except ParserError as pe:
                result, rest = pe.node, StringView('')
            if result is EMPTY_NODE:  # don't ever deal out the EMPTY_NODE singleton!
                result = Node(EMPTY_PTYPE, '').with_pos(0)

            if rest and complete_match:
                fwd = rest.find("\n") + 1 or len(rest)
                skip, rest = rest[:fwd], rest[fwd:]
                if result is None or (result.name == ZOMBIE_TAG and len(result) == 0):
                    err_pos = self.ff_pos__
                    associated_symbol = self.associated_symbol__(self.ff_parser__)
                    if associated_symbol != self.ff_parser__:
                        err_pname = associated_symbol.pname + '->' + str(self.ff_parser__)
                    else:
                        err_pname = str(associated_symbol)
                    err_text = self.document__[err_pos:err_pos + 20]
                    if err_pos + 20 < len(self.document__) - 1:  err_text += ' ...'
                    # Check if a Lookahead-Parser did match. Needed for testing, because
                    # in a test case this is not necessarily an error.
                    if lookahead_failure_only(parser):
                        # error_msg = # f'Parser "{parser.name}" stopped before end, because ' \
                        error_msg = f'Parser "{err_pname}" did not match: »{err_text}« ' \
                                    f'- but only because of lookahead.'
                        error_code = PARSER_LOOKAHEAD_FAILURE_ONLY
                    else:
                        # error_msg = f'Parser "{parser.name}" stopped before end, because' \
                        error_msg = f'Parser "{err_pname}" did not match: »{err_text}«'
                        error_code = PARSER_STOPPED_BEFORE_END
                    if self.history_tracking__:
                        error_msg += '\n    Most advanced fail: %s\n    Last match:    %s;' % \
                                     (str(HistoryRecord.most_advanced_fail(self.history__)),
                                      str(HistoryRecord.last_match(self.history__)))
                else:
                    stitches.append(result)
                    for h in reversed(self.history__):
                        if h.node and (h.node.name != EMPTY_NODE.name or h.node.result) \
                                and any('Lookahead' in tag for tag, _ in h.call_stack):
                            break
                    else:
                        h = HistoryRecord([], Node(EMPTY_NODE.name, '').with_pos(0),
                                          StringView(''), (0, 0))
                    if h.status in (h.MATCH, h.DROP) \
                            and (h.node.pos + h.node.strlen() == len(self.document__)):
                        # TODO: this case still needs unit-tests and support in testing.py
                        err_pos = h.node.pos
                        error_msg = "Parser stopped before end, but matched with lookahead."
                        error_code = PARSER_LOOKAHEAD_MATCH_ONLY
                        max_parser_dropouts = -1  # no further retries!
                    else:
                        i = self.ff_pos__ if self.ff_pos__ >= 0 else tail_pos(stitches)
                        err_pos = i
                        fs = self.document__[i:i + 10].replace('\n', '\\n')
                        if i + 10 < len(self.document__) - 1:  fs += '...'
                        root_name = self.associated_symbol__(self.start_parser__).pname
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
                    err_code = PARSER_STOPPED_ON_RETRY
                    err_pos = stitch.pos  # in this case stich.pos is more important than ff_pos
                if error_code in {PARSER_LOOKAHEAD_MATCH_ONLY, PARSER_LOOKAHEAD_FAILURE_ONLY} \
                        or not any(e.pos == err_pos for e in self.tree__.errors):
                    error = Error(error_msg, err_pos, error_code)
                    self.tree__.add_error(stitch, error)
                    if self.history_tracking__:
                        lc = line_col(self.document_lbreaks__, error.pos)
                        self.history__.append(HistoryRecord(
                            [(stitch.name, stitch.pos)], stitch,
                            self.document__[error.pos:], lc, [error]))
            else:
                # if complete_match is False, ignore the rest and leave while loop
                rest = StringView('')

        if stitches:
            if rest:
                stitches.append(Node(ZOMBIE_TAG, rest).with_pos(tail_pos(stitches)))
            result = Node(ZOMBIE_TAG, tuple(stitches)).with_pos(0)

        if any(self.variables__.values()):
                # capture stack not empty will only be reported for root-parsers
                # to avoid false negatives when testing
            error_msg = "Capture-stack not empty after end of parsing: " \
                + ', '.join(f'{v} {len(l)} {"items" if len(l) > 1 else "item"}'
                            for v, l in self.variables__.items() if len(l) >= 1)
            if parser.apply(has_non_autocaptured_symbols):
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

        self.tree__.swallow(result, document, source_mapping)
        if not self.tree__.source:  self.tree__.source = document
        self.start_parser__ = None
        return self.tree__


    def match(self,
              parser: Union[str, Parser],
              string: str,
              source_mapping: Optional[SourceMapFunc] = None):
        """Returns the matched string, if the parser matches the
        beginning of a string or ``None`` if the parser does not match."""
        result = self(string, parser, source_mapping, complete_match=False)
        if has_errors(result.errors):
            return None
        else:
            return str(result)


    def fullmatch(self,
              parser: Union[str, Parser],
              string: str,
              source_mapping: Optional[SourceMapFunc] = None):
        """Returns the matched string, if the parser matches the
        complete string or ``None`` if the parser does not match."""
        result = self(string, parser, source_mapping, complete_match=True)
        if has_errors(result.errors):
            return None
        else:
            return str(result)


    def push_rollback__(self, location, func):
        """
        Adds a rollback function that either removes or re-adds
        values on the variable stack (`self.variables`) that have been
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


    @property
    def document_lbreaks__(self) -> List[int]:
        if not self._document_lbreaks__:
            self._document_lbreaks__ = linebreaks(self.document__)
        return self._document_lbreaks__


    def rollback_to__(self, location):
        """
        Rolls back the variable stacks (`self.variables`) to its
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
        r"""Returns the closest named parser that contains `parser`.
        If `parser` is a named parser itself, `parser` is returned.
        If `parser` is not connected to any symbol in the Grammar,
        an AttributeError is raised.

        >>> word = Series(RegExp(r'\w+'), Whitespace(r'\s*'))
        >>> word.pname = 'word'
        >>> gr = Grammar(word)
        >>> anonymous_re = gr['word'].parsers[0]
        >>> gr.associated_symbol__(anonymous_re).pname
        'word'
        """
        symbol = self.associated_symbol_cache__.get(parser, None)   # type: Optional[Parser]
        if symbol:  return symbol

        def find_symbol_for_parser(context: List[Parser]) -> Optional[bool]:
            nonlocal symbol, parser
            if parser in context[-1].sub_parsers():
                for p in reversed(context):
                    if p.pname:
                        # save the name of the closest containing named parser
                        symbol = p
                        return True  # stop searching
            return False  # continue searching

        if isinstance(parser, Forward) and cast(Forward, parser).parser.pname:
            symbol = cast(Forward, parser).parser
        elif parser.pname:
            symbol = parser
        else:
            self.root_parser__.apply(find_symbol_for_parser)
            for resume_parser in self.unconnected_parsers__:
                resume_parser.apply(find_symbol_for_parser)
            if symbol is None:
                raise AttributeError('Parser %s (%i) is not contained in Grammar!'
                                     % (str(parser), id(parser)))

        self.associated_symbol_cache__[parser] = symbol
        return symbol


    def fill_associated_symbol_cache__(self):
        """Pre-fills the associated symbol cache with an algorithm that
        is more efficient than filling the cache by calling
        ``associated_symbol__()`` on each parser individually.
        """
        symbol = get_parser_placeholder()

        def add_anonymous_descendants(p: Parser):
            nonlocal symbol
            self.associated_symbol_cache__[p] = symbol
            for d in p.sub_parsers():
                if not d.pname and not (isinstance(d, Forward) and cast(Forward, d).parser.pname):
                    add_anonymous_descendants(d)

        for p in self.all_parsers__:
            if isinstance(p, Forward) and cast(Forward, p).parser.pname:
                symbol = cast(Forward, p).parser
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
                sub_list = p.sub_parsers()
                if sub_list:
                    leaf_state[p] = None
                    state = any(leaf_parsers(s) for s in sub_list)  # type: Optional[bool]
                    if not state and any(leaf_state[s] is None for s in sub_list):
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
        # cache = dict()  # type: Dict[Parser, Set[Parser]]
        # for debugging: all_parsers = sorted(list(self.all_parsers__), key=lambda p:p.pname)
        for parser in self.all_parsers__:
            error_list.extend(parser.static_analysis())
            if parser.pname and not has_leaf_parsers(parser):
                error_list.append(AnalysisError(parser.symbol, parser, Error(
                    'Parser %s is entirely cyclical and, therefore, cannot even touch '
                    'the parsed document' % cast('CombinedParser', parser).location_info(),
                    0, PARSER_NEVER_TOUCHES_DOCUMENT)))
        return error_list


def dsl_error_msg(parser: Parser, error_str: str) -> str:
    """
    Returns an error message for errors in the parser configuration,
    e.g. errors that result in infinite loops.

    Args:
        parser (Parser):  The parser where the error was noticed. Note
            that this is not necessarily the parser that caused the
            error but only where the error became apparent.
        error_str (str):  A short string describing the error.
    Returns:
        str: An error message including the call stack if history
        tacking has been turned in the grammar object.
    """
    msg = ["DSL parser specification error:", error_str, 'Caught by parser "%s".' % str(parser)]
    if parser.grammar.history__:
        msg.extend(["\nCall stack:", parser.grammar.history__[-1].stack])
    else:
        msg.extend(["\nEnable history tracking in Grammar object to display call stack."])
    return " ".join(msg)


_GRAMMAR_PLACEHOLDER = None  # type: Optional[Grammar]


def get_grammar_placeholder() -> Grammar:
    global _GRAMMAR_PLACEHOLDER
    if _GRAMMAR_PLACEHOLDER is None:
        _GRAMMAR_PLACEHOLDER = Grammar.__new__(Grammar)
    return cast(Grammar, _GRAMMAR_PLACEHOLDER)


def is_grammar_placeholder(grammar: Optional[Grammar]) -> bool:
    return grammar is None or cast(Grammar, grammar) is _GRAMMAR_PLACEHOLDER


########################################################################
#
# Special parser classes: Always, Never, PreprocessorToken (leaf classes)
#
########################################################################

class Unparameterized(Parser):
    """Unparameterized parsers do not receive any parameters on instantiation.
    As a consequence, different instances of the same unparameterized
    parser are always functionally equivalent."""

    def _signature(self) -> Hashable:
        return self.__class__.__name__,


class Always(Unparameterized):
    """A parser that always matches, but does not capture anything."""
    def _parse(self, text: StringView) -> ParsingResult:
        return EMPTY_NODE, text


class Never(Unparameterized):
    """A parser that never matches."""
    def _parse(self, text: StringView) -> ParsingResult:
        return None, text


class AnyChar(Unparameterized):
    """A parser that returns the next unicode character of the document
    whatever that is. The parser fails only at the very end of the text."""
    def _parse(self, text: StringView) -> ParsingResult:
        if len(text) >= 1:
            return Node(self.node_name, text[:1], True), text[1:]
        else:
            return None, text


class PreprocessorToken(Parser):
    """
    Parses tokens that have been inserted by a preprocessor.

    Preprocessors can generate Tokens with the ``make_token``-function.
    These tokens start and end with magic characters that can only be
    matched by the PreprocessorToken Parser. Such tokens can be used to
    insert BEGIN - END delimiters at the beginning or ending of a
    quoted block, for example.
    """

    def __init__(self, token: str) -> None:
        assert token and token.isupper()
        assert RX_TOKEN_NAME.match(token)
        super(PreprocessorToken, self).__init__()
        self.pname = token
        if token:
            self.disposable = False

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.pname)
        copy_parser_base_attrs(self, duplicate)
        return duplicate

    def _parse(self, text: StringView) -> ParsingResult:
        if text[0:1] == BEGIN_TOKEN:
            end = text.find(END_TOKEN, 1)
            if end < 0:
                node = Node(self.node_name, '')  # type: Node
                self.grammar.tree__.new_error(
                    node,
                    'END_TOKEN delimiter missing from preprocessor token. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[1:]
            elif end == 0:
                node = Node(self.node_name, '')
                self.grammar.tree__.new_error(
                    node,
                    'Preprocessor-token cannot have zero length. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[2:]
            elif text.find(BEGIN_TOKEN, 1, end) >= 0:
                node = Node(self.node_name, text[len(self.pname) + 1:end])
                self.grammar.tree__.new_error(
                    node,
                    'Preprocessor-tokens must not be nested or contain '
                    'BEGIN_TOKEN delimiter as part of their argument. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[end:]
            if text[1:len(self.pname) + 1] == self.pname:
                if self.drop_content:
                    return EMPTY_NODE, text[end + 1:]
                return Node(self.node_name, text[len(self.pname) + 2:end], True), text[end + 1:]
        return None, text


########################################################################
#
# Text and Regular Expression parser classes (leaf classes)
#
########################################################################

class Text(Parser):
    """
    Parses plain text strings. (Could be done by RegExp as well, but is faster.)

    Example::

        >>> while_token = Text("while")
        >>> Grammar(while_token)("while").content
        'while'
    """
    assert TOKEN_PTYPE == ":Text"

    def __init__(self, text: str) -> None:
        super(Text, self).__init__()
        self.text = text
        self.len = len(text)

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.text)
        copy_parser_base_attrs(self, duplicate)
        return duplicate

    def _parse(self, text: StringView) -> ParsingResult:
        self_len = self.len    # use local variables for optimization
        self_text = self.text
        if text[:self_len] == self_text:  # text.startswith(self.text):
            if self.drop_content:
                return EMPTY_NODE, text[self_len:]
            elif self_text or not self.disposable:
                return Node(self.node_name, self_text, True), text[self_len:]
            return EMPTY_NODE, text
        return None, text

    def __repr__(self):
        return '`%s`' % abbreviate_middle(self.text, 80)
        # return ("'%s'" if self.text.find("'") <= 0 else '"%s"') % abbreviate_middle(self.text, 80)

    def _signature(self) -> Hashable:
        return self.__class__.__name__, self.text


class RegExp(Parser):
    r"""
    Regular expression parser.

    The RegExp-parser parses text that matches a regular expression.
    RegExp can also be considered as the "atomic parser", because all
    other parsers delegate part of the parsing job to other parsers,
    but do not match text directly.

    Example::

        >>> word = RegExp(r'\w+')
        >>> Grammar(word)("Haus").content
        'Haus'

    EBNF-Notation:  ``/ ... /``

    EBNF-Example:   ``word = /\w+/``
    """

    def __init__(self, regexp) -> None:
        super(RegExp, self).__init__()
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def __deepcopy__(self, memo):
        # `regex` supports deep copies, but not `re`
        try:
            regexp = copy.deepcopy(self.regexp, memo)
        except TypeError:
            regexp = self.regexp.pattern
        duplicate = self.__class__(regexp)
        copy_parser_base_attrs(self, duplicate)
        return duplicate

    def _parse(self, text: StringView) -> ParsingResult:
        match = text.match(self.regexp)
        if match:
            capture = match.group(0)
            if capture or not self.disposable:
                end = text.index(match.end())
                if self.drop_content:
                    return EMPTY_NODE, text[end:]
                return Node(self.node_name, capture, True), text[end:]
            return EMPTY_NODE, text
        return None, text

    def __repr__(self):
        pattern = self.regexp.pattern
        try:
            if pattern == self._grammar.WSP_RE__:
                return '~'
            elif pattern == self._grammar.COMMENT__:
                return 'comment__'
            elif pattern == self._grammar.WHITESPACE__:
                return 'whitespace__'
        except (AttributeError, NameError):
            pass
        return '/' + escape_ctrl_chars('%s' % abbreviate_middle(pattern, 118))\
            .replace('/', '\\/') + '/'

    def _signature(self) -> Hashable:
        return self.__class__.__name__, self.regexp.pattern


def DropText(text: str) -> Text:
    return cast(Text, Drop(Text(text)))


def DropRegExp(regexp) -> RegExp:
    return cast(RegExp, Drop(RegExp(regexp)))


def withWS(parser_factory, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), parser_factory(), Whitespace(wsR))'.
    """
    parser = parser_factory()
    if wsL and isinstance(wsL, str):
        wsL = Whitespace(wsL)
    if wsR and isinstance(wsR, str):
        wsR = Whitespace(wsR)
    if wsL and wsR:
        combined_parser = Series(wsL, parser, wsR)
    elif wsL:
        combined_parser = Series(wsL, parser)
    elif wsR:
        combined_parser = Series(parser, wsR)
    else:
        combined_parser = parser
    return Drop(combined_parser) if parser.drop_content else combined_parser


def RE(regexp, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), RegExp(regexp), Whitespace(wsR))'"""
    return withWS(lambda: RegExp(regexp), wsL, wsR)


def TKN(token, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), Text(token), Whitespace(wsR))'"""
    return withWS(lambda: Text(token), wsL, wsR)


def DTKN(token, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), DropText(token), Whitespace(wsR))'"""
    return withWS(lambda: Drop(Text(token)), wsL, wsR)


class Whitespace(RegExp):
    """A variant of RegExp that signifies through its class name that it
    is a RegExp-parser for whitespace."""
    assert WHITESPACE_PTYPE == ":Whitespace"

    def __repr__(self):
        return '~'


def update_scanner(grammar: Grammar, leaf_parsers: Dict[str, str]):
    """Updates the "scanner" of a grammar by overwriting the `text` or
    `regex`-fields of some of or all of its leaf parsers with new values.
    This works, of course, only for those parsers that are assigned
    to a symbol in the Grammar class.

    :param grammar: The grammar-object for which the leaf parsers
        shall be updated.
    :param leaf_parsers: A mapping of parser names onto strings that
        are interpreted as plain text (if the parser name refers to
        a `Text`-parser or as regular expressions, if the parser name
        refers to a `RegExp`-parser)

    :raises AttributeError: in case a leaf parser name in the
        dictionary does not exist or does not refer to a `Text`
        or `RegExp`-parser.
    """
    for pname, t in leaf_parsers.items():
        parser = grammar[pname]
        if isinstance(parser, Text):
            assert isinstance(t, str)
            cast(Text, parser).text = t
            cast(Text, parser).len = len(t)
        elif isinstance(parser, RegExp):
            cast(RegExp, parser).regexp = re.compile(t) if isinstance(t, str) else t
        else:
            raise AttributeError('Parser %s is not a Text- oder RegExp-Parser, but %s'
                                 % (pname, type(parser)))


########################################################################
#
# Meta parser classes, i.e. parsers that contain other parsers
# to which they delegate parsing
#
########################################################################


class CombinedParser(Parser):
    """Class CombinedParser is the base class for all parsers that
    call ("combine") other parsers. It contains functions for the
    optimization of return values of such parser
    (i.e. descendants of classes UnaryParser and NaryParser).

    The optimization consists in flattening the tree by eliminating
    anonymous nodes. This is the same as what the function
    DHParser.transform.flatten() does, only at an earlier stage.
    The reasoning is that the earlier the tree is reduced, the less work
    remains to do at all later processing stages. As these typically run
    through all nodes of the syntax tree, this results in a considerable
    speed up.
    """

    def __init__(self):
        super(CombinedParser, self).__init__()
        self._return_value = self._return_value_flatten
        self._return_values = self._return_values_flatten

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    def _return_value_no_optimization(self, node: Optional[Node]) -> Node:
        # assert node is None or isinstance(node, Node)
        if self.drop_content:
            return EMPTY_NODE
        return Node(self.node_name, node or ())  # unoptimized code

    def _return_value_flatten(self, node: Optional[Node]) -> Node:
        """
        Generates a return node if a single node has been returned from
        any descendant parsers. Anonymous empty nodes will be dropped.
        If `self` is an unnamed parser, a non-empty descendant node
        will be passed through. If the descendant node is anonymous,
        it will be dropped and only its result will be kept.
        In all other cases a new node will be
        generated and the descendant node will be its single child.
        """
        # assert node is None or isinstance(node, Node)
        if node is not None:
            if self.disposable:
                if self.drop_content:
                    return EMPTY_NODE
                return node
            if node.name[0] == ':':  # node.anonymous:
                return Node(self.node_name, node._result)
            return Node(self.node_name, node)
        elif self.disposable:
            return EMPTY_NODE  # avoid creation of a node object for anonymous empty nodes
        return Node(self.node_name, '', True)

    @cython.locals(N=cython.int)
    def _return_values_no_tree_reduction(self, results: Sequence[Node]) -> Node:
        # assert isinstance(results, (list, tuple))
        if self.drop_content:
            return EMPTY_NODE
        return Node(self.node_name, tuple(results))  # unoptimized

    @cython.locals(N=cython.int)
    def _return_values_flatten(self, results: Sequence[Node]) -> Node:
        """
        Generates a return node from a tuple of returned nodes from
        descendant parsers. Anonymous empty nodes will be removed from
        the tuple. Anonymous child nodes will be flattened.
        """
        # assert isinstance(results, (list, tuple))
        if self.drop_content:
            return EMPTY_NODE
        N = len(results)
        if N > 1:
            nr = []  # type: List[Node]
            # flatten parse tree
            for child in results:
                c_anonymous = (child.name[0] == ':')  # child.anonymous
                if child._children and c_anonymous:
                    nr.extend(child._children)
                elif child._result or not c_anonymous:
                    nr.append(child)
            if nr or not self.disposable:
                return Node(self.node_name, tuple(nr))
            else:
                return EMPTY_NODE
        elif N == 1:
            return self._return_value(results[0])
        if self.disposable:
            return EMPTY_NODE  # avoid creation of a node object for anonymous empty nodes
        return Node(self.node_name, '', True)

    @cython.locals(N=cython.int)
    def _return_values_merge_treetops(self, results: Sequence[Node]) -> Node:
        """
        Generates a return node from a tuple of returned nodes from
        descendant parsers. Anonymous empty nodes will be removed from
        the tuple. Anonymous child nodes will be flattened. Plus, nodes
        that contain only anonymous leaf-nodes as children will be
        merged, i.e. the content of these nodes will be joined and
        assigned to the parent.
        """
        # assert isinstance(results, (list, tuple))
        if self.drop_content:
            return EMPTY_NODE
        N = len(results)
        if N > 1:
            nr = []  # type: List[Node]
            # flatten and parse tree
            merge = True
            for child in results:
                if child.name[0] == ':':  # child.anonymous:
                    grandchildren = child._children
                    if grandchildren:
                        nr.extend(grandchildren)
                        # merge &= all(not grandchild._children and grandchild.anonymous
                        #               for grandchild in grandchildren)
                        # cython compatibility:
                        for grandchild in grandchildren:
                            if grandchild._children or not grandchild.name[0] == ':':  # grandchild.anonymous:
                                merge = False
                                break
                    elif child._result:
                        nr.append(child)
                else:
                    nr.append(child)
                    merge = False
            if nr:
                if merge:
                    # result = ''.join(nd._result for nd in nr)
                    # cython compatibility:
                    result = ''.join([nd._result for nd in nr])
                    if result or not self.disposable:
                        return Node(self.node_name, result)
                    return EMPTY_NODE
                return Node(self.node_name, tuple(nr))
            return EMPTY_NODE if self.disposable else Node(self.node_name, '', True)
        elif N == 1:
            return self._return_value(results[0])
        if self.disposable:
            return EMPTY_NODE  # avoid creation of a node object for anonymous empty nodes
        return Node(self.node_name, '', True)

    @cython.locals(N=cython.int)
    def _return_values_merge_leaves(self, results: Sequence[Node]) -> Node:
        """
        Generates a return node from a tuple of returned nodes from
        descendant parsers. Anonymous empty nodes will be removed from
        the tuple. Anonymous child nodes will be flattened. Plus, any
        anonymous leaf-nodes adjacent to each other will be merged and,
        in cases where only one anonymous node is left, be reduced to
        its parent.
        """
        # assert isinstance(results, (list, tuple))
        if self.drop_content:
            return EMPTY_NODE
        N = len(results)
        if N > 1:
            nr = []  # type: List[Node]
            # flatten and parse tree
            for child in results:
                if child.name[0] == ':':  # child.anonymous:
                    grandchildren = child._children
                    if grandchildren:
                        nr.extend(grandchildren)
                    elif child._result:
                        nr.append(child)
                else:
                    nr.append(child)
            if nr:
                merged = []
                tail_is_anonymous_leaf = False
                for nd in nr:
                    head_is_anonymous_leaf = not nd._children and nd.name[0] == ':'  # nd.anonymous
                    if tail_is_anonymous_leaf and head_is_anonymous_leaf:
                        merged[-1].result += nd._result
                    else:
                        merged.append(nd)
                    tail_is_anonymous_leaf = head_is_anonymous_leaf
                if len(merged) > 1:
                    return Node(self.node_name, tuple(merged))
                if tail_is_anonymous_leaf:
                    result = merged[0].result
                    if result or not self.disposable:
                        return Node(self.node_name, merged[0].result)
                    return EMPTY_NODE
                return Node(self.node_name, merged[0])
            return EMPTY_NODE if self.disposable else Node(self.node_name, '', True)
        elif N == 1:
            return self._return_value(results[0])
        if self.disposable:
            return EMPTY_NODE  # avoid creation of a node object for anonymous empty nodes
        return Node(self.node_name, '', True)

    def location_info(self) -> str:
        """Returns a description of the location of the parser within the grammar
        for the purpose of transparent error reporting."""
        return '%s%s in definition of "%s" as %s' \
            % (self.pname or '_', self.ptype, self.symbol, str(self))

    NO_TREE_REDUCTION = 0
    FLATTEN = 1  # "flatten" vertically    (A (:Text "data"))  -> (A "data")
    MERGE_TREETOPS = 2  # "merge" horizontally  (A (:Text "hey ") (:RegExp "you")) -> (A "hey you")
    MERGE_LEAVES = 3  #  (A (:Text "hey ") (:RegExp "you") (C "!")) -> (A (:Text "hey you") (C "!"))
    DEFAULT_OPTIMIZATION = FLATTEN


def copy_combined_parser_attrs(src: CombinedParser, duplicate: CombinedParser):
    assert isinstance(src, CombinedParser)
    copy_parser_base_attrs(src, duplicate)
    duplicate._return_value = duplicate.__getattribute__(src._return_value.__name__)
    duplicate._return_values = duplicate.__getattribute__(src._return_values.__name__)


def TreeReduction(root_parser: Parser, level: int = CombinedParser.FLATTEN) -> Parser:
    """
    Applies tree-reduction level to CombinedParsers::

        >>> root = Text('A') + Text('B') | Text('C') + Text('D')
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.NO_TREE_REDUCTION))
        >>> tree = grammar('AB')
        >>> print(tree.as_sxpr())
        (root (:Series (:Text "A") (:Text "B")))
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.FLATTEN))  # default
        >>> tree = grammar('AB')
        >>> print(tree.as_sxpr())
        (root (:Text "A") (:Text "B"))
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.MERGE_TREETOPS))
        >>> tree = grammar('AB')
        >>> print(tree.as_sxpr())
        (root "AB")
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.MERGE_LEAVES))
        >>> tree = grammar('AB')
        >>> print(tree.as_sxpr())
        (root "AB")

        >>> root = Text('A') + Text('B') + (Text('C').name('important') | Text('D'))
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.NO_TREE_REDUCTION))
        >>> tree = grammar('ABC')
        >>> print(tree.as_sxpr())
        (root (:Text "A") (:Text "B") (:Alternative (important "C")))
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.FLATTEN))  # default
        >>> tree = grammar('ABC')
        >>> print(tree.as_sxpr())
        (root (:Text "A") (:Text "B") (important "C"))
        >>> tree = grammar('ABD')
        >>> print(tree.as_sxpr())
        (root (:Text "A") (:Text "B") (:Text "D"))
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.MERGE_TREETOPS))
        >>> tree = grammar('ABC')
        >>> print(tree.as_sxpr())
        (root (:Text "A") (:Text "B") (important "C"))
        >>> tree = grammar('ABD')
        >>> print(tree.as_sxpr())
        (root "ABD")
        >>> grammar = Grammar(TreeReduction(root, CombinedParser.MERGE_LEAVES))
        >>> tree = grammar('ABC')
        >>> print(tree.as_sxpr())
        (root (:Text "AB") (important "C"))
        >>> tree = grammar('ABD')
        >>> print(tree.as_sxpr())
        (root "ABD")
    """
    def apply_func(context: List[Parser]) -> None:
        nonlocal level
        parser = context[-1]
        if isinstance(parser, CombinedParser):
            if level == CombinedParser.NO_TREE_REDUCTION:
                cast(CombinedParser, parser)._return_value = parser._return_value_no_optimization
                cast(CombinedParser, parser)._return_values = parser._return_values_no_tree_reduction
            elif level == CombinedParser.FLATTEN:
                cast(CombinedParser, parser)._return_value = parser._return_value_flatten
                cast(CombinedParser, parser)._return_values = parser._return_values_flatten
            elif level == CombinedParser.MERGE_TREETOPS:
                cast(CombinedParser, parser)._return_value = parser._return_value_flatten
                cast(CombinedParser, parser)._return_values = parser._return_values_merge_treetops
            else:  # level == CombinedParser.SQUEEZE_TIGHT
                cast(CombinedParser, parser)._return_value = parser._return_value_flatten
                cast(CombinedParser, parser)._return_values = parser._return_values_merge_leaves

    assert isinstance(root_parser, Parser)
    assert level in (CombinedParser.NO_TREE_REDUCTION,
                     CombinedParser.FLATTEN,
                     CombinedParser.MERGE_TREETOPS,
                     CombinedParser.MERGE_LEAVES)
    root_parser.apply(apply_func)
    return root_parser


class UnaryParser(CombinedParser):
    """
    Base class of all unary parsers, i.e. parser that contains
    one and only one other parser, like the optional parser for example.

    The UnaryOperator base class supplies __deepcopy__ and apply
    methods for unary parsers. The __deepcopy__ method needs
    to be overwritten, however, if the constructor of a derived class
    has additional parameters.
    """

    def __init__(self, parser: Parser) -> None:
        super(UnaryParser, self).__init__()
        assert isinstance(parser, Parser), str(parser)
        self.parser = parser  # type: Parser

    def __deepcopy__(self, memo):
        parser = copy.deepcopy(self.parser, memo)
        duplicate = self.__class__(parser)
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    def sub_parsers(self) -> Tuple['Parser', ...]:
        return (self.parser,)

    def _signature(self) -> Hashable:
        return self.__class__.__name__, self.parser.signature()


class NaryParser(CombinedParser):
    """
    Base class of all Nary parsers, i.e. parser that
    contains one or more other parsers, like the alternative
    parser for example.

    The NaryOperator base class supplies __deepcopy__ and apply methods
    for n-ary parsers. The __deepcopy__ method needs to be overwritten,
    however, if the constructor of a derived class takes additional
    parameters.
    """

    def __init__(self, *parsers: Parser) -> None:
        super(NaryParser, self).__init__()
        # assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        if len(parsers) == 0:
            raise ValueError('Cannot initialize NaryParser with zero parsers.')
        self.parsers = parsers  # type: Tuple[Parser, ...]

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        duplicate = self.__class__(*parsers)
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    def sub_parsers(self) -> Tuple['Parser', ...]:
        return self.parsers

    def _signature(self) -> Hashable:
        return (self.__class__.__name__,) + tuple(p.signature() for p in self.parsers)


class Option(UnaryParser):
    r"""
    Parser ``Option`` always matches, even if its child-parser
    did not match.

    If the child-parser did not match ``Option`` returns a node
    with no content and does not move forward in the text.

    If the child-parser did match, ``Option`` returns a node
    with the node returned by the child-parser as its single
    child and the text at the position where the child-parser
    left it.

    Examples::

        >>> number = Option(TKN('-')) + RegExp(r'\d+') + Option(RegExp(r'\.\d+'))
        >>> Grammar(number)('3.14159').content
        '3.14159'
        >>> Grammar(number)('3.14159').as_sxpr()
        '(root (:RegExp "3") (:RegExp ".14159"))'
        >>> Grammar(number)('-1').content
        '-1'

    EBNF-Notation: ``[ ... ]``

    EBNF-Example:  ``number = ["-"]  /\d+/  [ /\.\d+/ ]``
    """

    def __init__(self, parser: Parser) -> None:
        super(Option, self).__init__(parser)

    def _parse(self, text: StringView) -> ParsingResult:
        node, text = self.parser(text)
        return self._return_value(node), text

    def is_optional(self) -> Optional[bool]:
        return True

    def __repr__(self):
        return '[' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + ']'

    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        if self.parser.is_optional():
            errors.append(self.static_error(
                "Redundant nesting of optional parser in " + self.location_info(),
                OPTIONAL_REDUNDANTLY_NESTED_WARNING))
        return errors


class ZeroOrMore(Option):
    r"""
    `ZeroOrMore` applies a parser repeatedly as long as this parser
    matches. Like `Option` the `ZeroOrMore` parser always matches. In
    case of zero repetitions, the empty match `((), text)` is returned.

    Examples::

        >>> sentence = ZeroOrMore(RE(r'\w+,?')) + TKN('.')
        >>> Grammar(sentence)('Wo viel der Weisheit, da auch viel des Grämens.').content
        'Wo viel der Weisheit, da auch viel des Grämens.'
        >>> Grammar(sentence)('.').content  # an empty sentence also matches
        '.'
        >>> forever = ZeroOrMore(RegExp(''))
        >>> Grammar(forever)('')  # infinite loops will automatically be broken
        Node('root', '')

    EBNF-Notation: ``{ ... }``

    EBNF-Example:  ``sentence = { /\w+,?/ } "."``
    """

    @cython.locals(n=cython.int, length=cython.int)
    def _parse(self, text: StringView) -> ParsingResult:
        results = ()  # type: Tuple[Node, ...]
        length = text.__len__()
        n = length + 1  # type: int
        while length < n:  # text and length(text) < n:
            n = length
            node, text = self.parser(text)
            length = text.__len__()
            if node is None:
                break
            if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                results += (node,)
            # if length == n:
            #     break  # avoid infinite loop
        nd = self._return_values(results)  # type: Node
        return nd, text

    def __repr__(self):
        return '{' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + '}'


class OneOrMore(UnaryParser):
    r"""
    `OneOrMore` applies a parser repeatedly as long as this parser
    matches. Other than `ZeroOrMore` which always matches, at least
    one match is required by `OneOrMore`.

    Examples::

        >>> sentence = OneOrMore(RE(r'\w+,?')) + TKN('.')
        >>> Grammar(sentence)('Wo viel der Weisheit, da auch viel des Grämens.').content
        'Wo viel der Weisheit, da auch viel des Grämens.'
        >>> str(Grammar(sentence)('.'))  # an empty sentence also matches
        ' <<< Error on "." | Parser "root->/\\\\w+,?/" did not match: ».« >>> '
        >>> forever = OneOrMore(RegExp(''))
        >>> Grammar(forever)('')  # infinite loops will automatically be broken
        Node('root', '')

    EBNF-Notation: ``{ ... }+``

    EBNF-Example:  ``sentence = { /\w+,?/ }+``
    """
    def _parse(self, text: StringView) -> ParsingResult:
        results = ()  # type: Tuple[Node, ...]
        # text_ = text  # type: StringView
        match_flag = False
        length = text.__len__()
        n = length + 1  # type: int
        while length < n:  # text_ and len(text_) < n:
            n = length
            node, text = self.parser(text)
            length = text.__len__()
            if node is None:
                break
            match_flag = True
            if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                results += (node,)
            # if length == n:
            #    break  # avoid infinite loop
        if not match_flag:
            return None, text
        nd = self._return_values(results)  # type: Node
        return nd, text  # text_

    def __repr__(self):
        return '{' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + '}+'

    def static_analysis(self) -> List[AnalysisError]:
        errors = super().static_analysis()
        if self.parser.is_optional():
            errors.append(self.static_error(
                "Use ZeroOrMore instead of nesting OneOrMore with an optional parser in "
                + self.location_info(), BADLY_NESTED_OPTIONAL_PARSER))
        return errors


INFINITE = 2**30


def to_interleave(parser: Parser) -> Parser:
    """Converts a `Counted`-parser into an `Interleave`-parser. Any other
    parser is simply passed through."""
    if isinstance(parser, Counted):
        return Interleave(cast(Counted, parser).parser,
                          repetitions=[cast(Counted, parser).repetitions])
    return parser


class Counted(UnaryParser):
    """Counted applies a parser for a number of repetitions within a given range, i.e.
    the parser must at least match the lower bound number of repetitions and it can
    at most match the upper bound number of repetitions.

    Examples:

    >>> A2_4 = Counted(Text('A'), (2, 4))
    >>> A2_4
    `A`{2,4}
    >>> Grammar(A2_4)('AA').as_sxpr()
    '(root (:Text "A") (:Text "A"))'
    >>> Grammar(A2_4)('AAAAA', complete_match=False).as_sxpr()
    '(root (:Text "A") (:Text "A") (:Text "A") (:Text "A"))'
    >>> Grammar(A2_4)('A', complete_match=False).as_sxpr()
    '(ZOMBIE__ `(err "1:1: Error (1040): Parser did not match!"))'
    >>> moves = OneOrMore(Counted(Text('A'), (1, 3)) + Counted(Text('B'), (1, 3)))
    >>> result = Grammar(moves)('AAABABB')
    >>> result.name, result.content
    ('root', 'AAABABB')
    >>> moves = Counted(Text('A'), (2, 3)) * Counted(Text('B'), (2, 3))
    >>> moves
    `A`{2,3} ° `B`{2,3}
    >>> Grammar(moves)('AAABB').as_sxpr()
    '(root (:Text "A") (:Text "A") (:Text "A") (:Text "B") (:Text "B"))'

    While a Counted-parser could be treated as a special case of Interleave-parser,
    defining a dedicated class makes the purpose clearer and runs slightly faster.
    """
    def __init__(self, parser: Parser, repetitions: Tuple[int, int]) -> None:
        super(Counted, self).__init__(parser)
        self.repetitions = repetitions  # type: Tuple[int, int]

    def __deepcopy__(self, memo):
        parser = copy.deepcopy(self.parser, memo)
        duplicate = self.__class__(parser, self.repetitions)
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    @cython.locals(n=cython.int, length=cython.int)
    def _parse(self, text: StringView):
        results = ()  # Tuple[Node, ...]
        text_ = text
        length = text.__len__()
        for _ in range(self.repetitions[0]):
            node, text = self.parser(text)
            if node is None:
                return None, text_
            results += (node,)
            n = length
            length = text.__len__()
            if length == n:
                break  # avoid infinite loop
        for _ in range(self.repetitions[1] - self.repetitions[0]):
            node, text = self.parser(text)
            if node is None:
                break
            results += (node,)
            n = length
            length = text.__len__()
            if length == n:
                break  # avoid infinite loop
        return self._return_values(results), text

    def is_optional(self) -> Optional[bool]:
        return self.repetitions[0] == 0

    def __repr__(self):
        return self.parser.repr + "{%i,%i}" % self.repetitions

    @cython.locals(a=cython.int, b=cython.int)
    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        a, b = self.repetitions
        if a < 0 or b < 0 or a > b or a > INFINITE or b > INFINITE:
            errors.append(self.static_error(
                'Repetition count [a=%i, b=%i] for parser %s violates requirement '
                '0 <= a <= b <= infinity = 2^30' % (a, b, str(self)),
                BAD_REPETITION_COUNT))
        return errors

    def _signature(self) -> Hashable:
        return self.__class__.__name__, self.parser.signature(), self.repetitions


NO_MANDATORY = 2**30


class MandatoryNary(NaryParser):
    """MandatoryNary is the parent class for N-ary parsers that can be
    configured to fail with a parsing error rather than returning a non-match,
    if all contained parsers from a specific subset of non-mandatory parsers
    have already matched successfully, so that only "mandatory" parsers are
    left for matching. The idea is that once all non-mandatory parsers have
    been consumed it is clear that this parser is a match so that the failure
    to match any of the following mandatory parsers indicates a syntax
    error in the processed document at the location were a mandatory parser
    fails to match.

    For the sake of simplicity, the division between the set of non-mandatory
    parsers and mandatory parsers is realized by an index into the list
    of contained parsers. All parsers from the mandatory-index onward are
    considered mandatory once all parsers up to the index have been consumed.

    In the following example, ``Series`` is a descendant of ``MandatoryNary``::

        >>> fraction = Series(Text('.'), RegExp(r'[0-9]+'), mandatory=1).name('fraction')
        >>> number = (RegExp(r'[0-9]+') + Option(fraction)).name('number')
        >>> num_parser = Grammar(TreeReduction(number, CombinedParser.MERGE_TREETOPS))
        >>> num_parser('25').as_sxpr()
        '(number "25")'
        >>> num_parser('3.1415').as_sxpr()
        '(number (:RegExp "3") (fraction ".1415"))'
        >>> str(num_parser('3.1415'))
        '3.1415'
        >>> str(num_parser('3.'))
        '3. <<< Error on "" | \\'/[0-9]+/\\' expected by parser \\'fraction\\', but »...« found instead! >>> '

    In this example, the first item of the fraction, i.e. the decimal dot,
    is non-mandatory, because only the parser with an index of one or more
    are mandatory (``mandator=1``). In this case this is only the regular
    expression parser capturing the decimal digits after the dot. This means,
    if there is no dot, the fraction parser simply will not match. However,
    if there is a dot, it will fail with an error if the following mandatory
    item, i.e. the decimal digits, are missing.

    :ivar mandatory:  Number of the element starting at which the element
        and all following elements are considered "mandatory". This means
        that rather than returning a non-match an error message is issued.
        The default value is NO_MANDATORY, which means that no elements
        are mandatory. NOTE: The semantics of the mandatory-parameter
        might change depending on the subclass implementing it.
    """
    def __init__(self, *parsers: Parser,
                 mandatory: int = NO_MANDATORY) -> None:
        super(MandatoryNary, self).__init__(*parsers)
        length = len(self.parsers)
        if mandatory < 0:
            mandatory += length
        self.mandatory = mandatory  # type: int

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        duplicate = self.__class__(*parsers, mandatory=self.mandatory)
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    def get_reentry_point(self, text_: StringView) -> Tuple[int, Node]:
        """Returns a tuple of integer index of the closest reentry point and a Node
        capturing all text from ``rest`` up to this point or ``(-1, None)`` if no
        reentry-point was found. If no reentry-point was found or the
        skip-list ist empty, -1 and a zombie-node are returned.
        """
        skip = tuple(self.grammar.skip_rules__.get(self.grammar.associated_symbol__(self).pname,
                                                   tuple()))
        if skip:
            gr = self._grammar
            # print(gr.variables__)
            # location = gr.document_length__ - text_._len
            # if location <= gr.last_rb__loc__ + 1:
            #     gr.rollback_to__(location - 1)
            reloc = reentry_point(text_, skip, gr.comment_rx__, gr.reentry_search_window__)
            return reloc
        return -1, Node(ZOMBIE_TAG, '')

    @cython.locals(location=cython.int)
    def mandatory_violation(self,
                            text_: StringView,
                            failed_on_lookahead: bool,
                            expected: str,
                            reloc: int,
                            err_node: Node) -> Tuple[Error, StringView]:
        """
        Chooses the right error message in case of a mandatory violation and
        returns an error with this message, an error node, to which the error
        is attached, and the text segment where parsing is to continue.

        This is a helper function that abstracts functionality that is
        needed by the Interleave-parser as well as the Series-parser.

        :param text_: the point, where the mandatory violation happend.
                As usual the string view represents the remaining text from
                this point.
        :param failed_on_lookahead: True if the violating parser was a
                Lookahead-Parser.
        :param expected:  the expected (but not found) text at this point.
        :param err_node: A zombie-node that captures the text from the
                position where the error occurred to a suggested
                reentry-position.
        :param reloc: A position value that represents the reentry point for
                parsing after the error occurred.

        :return:   a tuple of an error object and a string view for the
                continuation the parsing process
        """
        grammar = self._grammar
        location = grammar.document_length__ - len(text_)
        err_node._pos = -1  # bad hack to avoid error in case position is re-set
        err_node.with_pos(location)  # for testing artifacts
        found = text_[:10].replace('\n', '\\n') + '...'
        sym = self.grammar.associated_symbol__(self).pname
        err_msgs = self.grammar.error_messages__.get(sym, [])
        for search, message in err_msgs:
            is_func = callable(search)           # search rule is a function: StringView -> bool
            is_str = isinstance(search, str)     # search rule is a simple string
            is_rxs = not is_func and not is_str  # search rule is a regular expression
            if (is_func and cast(Callable, search)(text_)) \
                    or (is_rxs and text_.match(search)) \
                    or (is_str and text_.startswith(cast(str, search))):
                try:
                    msg = message.format(expected, found)
                    break
                except (ValueError, KeyError, IndexError) as e:
                    error = Error("Malformed error format string »{}« leads to »{}«"
                                  .format(message, str(e)),
                                  location, MALFORMED_ERROR_STRING)
                    grammar.tree__.add_error(err_node, error)
        else:
            msg = '%s expected by parser %s, but »%s« found instead!' \
                  % (repr(expected), repr(sym), found)
        if failed_on_lookahead and not text_:
            if grammar.start_parser__ is grammar.root_parser__:
                error_code = MANDATORY_CONTINUATION_AT_EOF
            else:
                error_code = MANDATORY_CONTINUATION_AT_EOF_NON_ROOT
        else:
            error_code = MANDATORY_CONTINUATION
        error = Error(msg, location, error_code,
                      length=max(self.grammar.ff_pos__ - location, 1))
        grammar.tree__.add_error(err_node, error)
        if reloc >= 0:
            # signal error to tracer directly, because this error is not raised!
            grammar.most_recent_error__ = ParserError(
                self, err_node, reloc, text_, error, first_throw=False)
        return error, text_[max(reloc, 0):]

    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        msg = []
        length = len(self.parsers)
        sym = self.grammar.associated_symbol__(self).pname
        # if self.mandatory == NO_MANDATORY and sym in self.grammar.error_messages__:
        #     msg.append('Custom error messages require that parameter "mandatory" is set!')
        # elif self.mandatory == NO_MANDATORY and sym in self.grammar.skip_rules__:
        #     msg.append('Search expressions for skipping text require parameter '
        #                '"mandatory" to be set!')
        if length == 0:
            msg.append('Number of elements %i is below minimum length of 1' % length)
        elif length >= NO_MANDATORY:
            msg.append('Number of elements %i of series exceeds maximum length of %i'
                       % (length, NO_MANDATORY))
        elif not (0 <= self.mandatory < length or self.mandatory == NO_MANDATORY):
            msg.append('Illegal value %i for mandatory-parameter in a parser with %i elements!'
                       % (self.mandatory, length))
        if msg:
            msg.insert(0, 'Illegal configuration of mandatory Nary-parser '
                       + self.location_info())
            errors.append(self.static_error('\n'.join(msg), BAD_MANDATORY_SETUP))
        return errors


@cython.returns(cython.int)
def combined_mandatory(left: Parser, right: Parser) -> int:
    """
    Returns the position of the first mandatory element (if any) when
    parsers `left` and `right` are joined to a sequence.
    """
    left_mandatory, left_length = (left.mandatory, len(left.parsers)) \
        if isinstance(left, Series) else (NO_MANDATORY, 1)
    if left_mandatory != NO_MANDATORY:
        return left_mandatory
    right_mandatory = right.mandatory if isinstance(right, Series) else NO_MANDATORY
    if right_mandatory != NO_MANDATORY:
        return right_mandatory + left_length
    return NO_MANDATORY


class Series(MandatoryNary):
    r"""
    Matches if each of a series of parsers matches exactly in the order of
    the series.

    Example::

        >>> variable_name = RegExp(r'(?!\d)\w') + RE(r'\w*')
        >>> Grammar(variable_name)('variable_1').content
        'variable_1'
        >>> str(Grammar(variable_name)('1_variable'))
        ' <<< Error on "1_variable" | Parser "root->/(?!\\\\d)\\\\w/" did not match: »1_variable« >>> '

    EBNF-Notation: ``... ...``    (sequence of parsers separated by a blank or new line)

    EBNF-Example:  ``series = letter letter_or_digit``
    """
    RX_ARGUMENT = re.compile(r'\s(\S)')

    @cython.locals(pos=cython.int, reloc=cython.int, mandatory=cython.int)
    def _parse(self, text: StringView) -> ParsingResult:
        results = []  # type: List[Node]
        text_ = text  # type: StringView
        error = None  # type: Optional[Error]
        mandatory = self.mandatory  # type: int
        for pos, parser in enumerate(self.parsers):
            node, text_ = parser(text_)
            if node is None:
                if pos < mandatory:
                    return None, text
                else:
                    parser_str = str(parser) if is_context_sensitive(parser) else parser.repr
                    reloc, node = self.get_reentry_point(text_)
                    error, text_ = self.mandatory_violation(
                        text_, isinstance(parser, Lookahead), parser_str, reloc, node)
                    # check if parsing of the series can be resumed somewhere
                    if reloc >= 0:
                        nd, text_ = parser(text_)  # try current parser again
                        if nd is not None:
                            results.append(node)
                            node = nd
                    else:
                        results.append(node)
                        break
            if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                results.append(node)
        # assert len(results) <= len(self.parsers) \
        #        or len(self.parsers) >= len([p for p in results if p.name != ZOMBIE_TAG])
        ret_node = self._return_values(results)  # type: Node
        if error and reloc < 0:  # no worry: reloc is always defined when error is True
            # parser will be moved forward, even if no relocation point has been found
            raise ParserError(self, ret_node.with_pos(self.grammar.document_length__ - len(text_)),
                              len(text) - len(text_),
                              text, error, first_throw=True)
        return ret_node, text_

    def __repr__(self):
        return " ".join([parser.repr for parser in self.parsers[:self.mandatory]]
                        + (['§'] if self.mandatory != NO_MANDATORY else [])
                        + [parser.repr for parser in self.parsers[self.mandatory:]])

    # The following operator definitions add syntactical sugar, so one can write:
    # `RE('\d+') + Optional(RE('\.\d+)` instead of `Series(RE('\d+'), Optional(RE('\.\d+))`

    def __add__(self, other: Parser) -> 'Series':
        if self.pname or other.pname:
            return Series(self, other)
        if not isinstance(self, Series):
            # for some reason cython calls __add__ instead of __radd__,
            # so we have to repeat the __radd__ code here...
            self, other = other, self
            other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
                else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
            return Series(*(other_parsers + cast(NaryParser, self).parsers),
                          mandatory=combined_mandatory(other, self))
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Series(*(self.parsers + other_parsers),
                      mandatory=combined_mandatory(self, other))

    def __radd__(self, other: Parser) -> 'Series':
        if self.pname or other.pname:
            return Series(other, self)
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Series(*(other_parsers + self.parsers),
                      mandatory=combined_mandatory(other, self))

    def __iadd__(self, other: Parser) -> 'Series':
        if self.pname or other.pname:
            return Series(self, other)
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        self.parsers += other_parsers
        self.mandatory = combined_mandatory(self, other)
        return self


def starting_string(parser: Parser) -> str:
    """If parser starts with a fixed string, this will be returned.
    """
    # keep track of already visited parsers to avoid infinite circles
    been_there = parser.grammar.static_analysis_caches__\
        .setdefault('starting_strings', dict())  # type: Dict[Parser, str]

    def find_starting_string(p: Parser) -> str:
        nonlocal been_there
        if isinstance(p, (NegativeLookahead, Lookbehind, NegativeLookbehind)):
            return ""
        if p in been_there:
            return been_there[p]
        else:
            been_there[p] = ""
            if isinstance(p, Text):
                been_there[p] = cast(Text, p).text
            elif isinstance(p, Series) or isinstance(p, Alternative):
                been_there[p] = find_starting_string(cast(NaryParser, p).parsers[0])
            elif isinstance(p, Synonym) or isinstance(p, OneOrMore) \
                    or isinstance(p, Lookahead):
                been_there[p] = find_starting_string(cast(UnaryParser, p).parser)
            elif isinstance(p, Counted):
                counted = cast(Counted, p)  # type: Counted
                if not counted.is_optional():
                    been_there[p] = find_starting_string(counted.parser)
            elif isinstance(p, Interleave):
                interleave = cast(Interleave, p)
                if interleave.repetitions[0][0] >= 1:
                    been_there[p] = find_starting_string(interleave.parsers[0])
            return been_there[p]
    return find_starting_string(parser)


class Alternative(NaryParser):
    r"""
    Matches if one of several alternatives matches. Returns
    the first match.

    This parser represents the EBNF-operator "|" with the qualification
    that both the symmetry and the ambiguity of the EBNF-or-operator
    are broken by selecting the first match.::

        # the order of the sub-expression matters!
        >>> number = RE(r'\d+') | RE(r'\d+') + RE(r'\.') + RE(r'\d+')
        >>> str(Grammar(number)("3.1416"))
        '3 <<< Error on ".1416" | Parser "root" stopped before end, at: ».1416« Terminating parser. >>> '

        # the most selective expression should be put first:
        >>> number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        >>> Grammar(number)("3.1416").content
        '3.1416'

    EBNF-Notation: ``... | ...``

    EBNF-Example:  ``number = /\d+\.\d+/ | /\d+/``
    """
    def _parse(self, text: StringView) -> ParsingResult:
        for parser in self.parsers:
            node, text_ = parser(text)
            if node is not None:
                return self._return_value(node), text_
                # return self._return_value(node if node._result or parser.pname else None), text_
                # return Node(self.name,
                #             node if node._result or parser.pname else ()), text_
        return None, text

    def __repr__(self):
        if self.pname:
            return ' | '.join(parser.repr for parser in self.parsers)
        return '(' + ' | '.join(parser.repr for parser in self.parsers) + ')'

    # The following operator definitions add syntactical sugar, so one can write:
    # `RE('\d+') + RE('\.') + RE('\d+') | RE('\d+')` instead of:
    # `Alternative(Series(RE('\d+'), RE('\.'), RE('\d+')), RE('\d+'))`

    def __or__(self, other: Parser) -> 'Alternative':
        if self.pname or other.pname:
            return Alternative(self, other)
        if not isinstance(self, Alternative):
            # for some reason cython called __or__ instead of __ror__,
            # so we have to repeat the __ror__ code here...
            self, other = other, self
            other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
                else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
            return Alternative(*(other_parsers + cast(NaryParser, self).parsers))
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Alternative(*(self.parsers + other_parsers))

    def __ror__(self, other: Parser) -> 'Alternative':
        if self.pname or other.pname:
            return Alternative(other, self)
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Alternative(*(other_parsers + self.parsers))

    def __ior__(self, other: Parser) -> 'Alternative':
        if self.pname or other.pname:
            return Alternative(self, other)
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        self.parsers += other_parsers
        return self

    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        if len(set(self.parsers)) != len(self.parsers):
            errors.append(self.static_error(
                'Duplicate parsers in ' + self.location_info(),
                DUPLICATE_PARSERS_IN_ALTERNATIVE))
        if not all(not p.is_optional() for p in self.parsers[:-1]):
            i = 0
            for i, p in enumerate(self.parsers):
                if p.is_optional():
                    break
            # no worry: p and i are defined, because self.parsers cannot be empty.
            # See NaryParser.__init__()
            errors.append(self.static_error(
                "Parser-specification Error in " + self.location_info()
                + "\nOnly the very last alternative may be optional! "
                + 'Parser "%s" at position %i out of %i is optional'
                % (p.node_name, i + 1, len(self.parsers)),
                BAD_ORDER_OF_ALTERNATIVES))

        # check for errors like "A" | "AB" where "AB" would never be reached,
        # because a substring at the beginning is already caught by an earlier
        # alternative
        # WARNING: This can become time-consuming!!!
        # EXPERIMENTAL

        def does_preempt(start, parser):
            cst = self.grammar(start, parser, complete_match=False)
            return not cst.errors and cst.strlen() >= 1

        for i in range(2, len(self.parsers)):
            fixed_start = starting_string(self.parsers[i])
            if fixed_start:
                for k in range(i):
                    if does_preempt(fixed_start, self.parsers[k]):
                        errors.append(self.static_error(
                            "Parser-specification Error in " + self.location_info()
                            + "\nAlternative %i will never be reached, because its starting-"
                            'string "%s" is already captured by earlier alternative %i !'
                            % (i + 1, fixed_start, k + 1), BAD_ORDER_OF_ALTERNATIVES))
        return errors


@cython.locals(n=cython.int, i=cython.int)
def longest_match(strings: List[str], text: Union[StringView, str], n: int = 1) -> str:
    """Returns the longest string from a given list of strings that
    matches the beginning of text.
    >>> l = ['a', 'ab', 'ca', 'cd']
    >>> longest_match(l, 'a')
    'a'
    >>> longest_match(l, 'abcdefg')
    'ab'
    >>> longest_match(l, 'ac')
    'a'
    >>> longest_match(l, 'cb')
    ''
    >>> longest_match(l, 'cab')
    'ca'
    """
    if n > len(text):  return ''
    if len(strings) == 1:
        return strings[0] if text.startswith(strings[0]) else ''
    head = str(text[:n])
    if not head:  return ''
    i = bisect_left(strings, head)
    if i >= len(strings) or (i == 0 and not strings[0].startswith(head)):
        return ''
    match = longest_match(strings[i:], text, n + 1)
    if match:  return match
    if head == strings[i]:  return head
    return ''

class TextAlternative(Alternative):
    r"""A faster Alternative-Parser for special cases where all alternatives
    are Text-parsers or sequences beginning with a Text-Parser.

    EXPERIMENTAL!!!
    """

    def __init__(self, *parsers: Parser) -> None:
        super(TextAlternative, self).__init__(*parsers)
        heads: List[str] = []
        for p in parsers:
            while isinstance(p, Synonym):
                p = p.parser
            if isinstance(p, Text):
                heads.append(p.text)
            elif isinstance(p, Series) and isinstance(p.parsers[0], Text):
                heads.append(cast(Text, p.parsers[0]).text)
            else:
                raise ValueError(
                    f'Parser {p} is not a Text-parser and does not start with a Text-parser')
        heads.sort()
        self.heads = heads
        self.indices = {h: parsers.index(p) for h, p in zip(heads, parsers)}
        self.min_head_size = min(len(h) for h in self.heads)

    def _parse(self, text: StringView) -> ParsingResult:
        m = longest_match(self.heads, text, self.min_head_size)
        if m:
            parser = self.parsers[self.indices[m]]
            node, text_ = parser(text)
            if node is not None:
                return self._return_value(node), text_
        return None, text

    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        if len(self.heads) != len(set(self.heads)):
            errors.append(self.static_error(
                'Duplicate text-heads in ' + self.location_info()
                + ' Use of Alternative() instead of TextAlternative() '
                + ' could possibly solve this problem.',
                DUPLICATE_PARSERS_IN_ALTERNATIVE))
        return errors


class Interleave(MandatoryNary):
    r"""Parse elements in arbitrary order.

    Examples::
        >>> prefixes = TKN("A") * TKN("B")
        >>> Grammar(prefixes)('A B').content
        'A B'
        >>> Grammar(prefixes)('B A').content
        'B A'

        >>> prefixes = Interleave(TKN("A"), TKN("B"), repetitions=((0, 1), (0, 1)))
        >>> Grammar(prefixes)('A B').content
        'A B'
        >>> Grammar(prefixes)('B A').content
        'B A'
        >>> Grammar(prefixes)('B').content
        'B'

    EBNF-Notation: ``... ° ...``

    EBNF-Example:  ``float =  { /\d/ }+ ° /\./``
    """

    def __init__(self, *parsers: Parser,
                 mandatory: int = NO_MANDATORY,
                 repetitions: Sequence[Tuple[int, int]] = ()) -> None:
        super(Interleave, self).__init__(*parsers, mandatory=mandatory)
        if len(repetitions) == 0:
            repetitions = [(1, 1)] * len(parsers)
        elif len(parsers) != len(repetitions):
            raise ValueError("Number of repetition-tuples unequal number of sub-parsers!")
        self.repetitions = list(repetitions)  # type: List[Tuple[int, int]]
        self.non_mandatory = frozenset(parsers[i] for i in range(min(mandatory, len(parsers))))
        self.parsers_set = frozenset(self.parsers)

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        duplicate = self.__class__(*parsers, mandatory=self.mandatory,
                                   repetitions=self.repetitions)
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    @cython.locals(i=cython.int, n=cython.int, length=cython.int, reloc=cython.int)
    def _parse(self, text: StringView):
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        counter = [0] * len(self.parsers)
        consumed = set()  # type: Set[Parser]
        error = None  # type: Optional[Error]
        length = text_.__len__()
        while True:
            # there is an order of testing, but no promise about the order of testing, here!
            for i, parser in enumerate(self.parsers):
                if parser not in consumed:
                    node, text__ = parser(text_)
                    if node is not None:
                        if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                            results += (node,)
                            text_ = text__
                        counter[i] += 1
                        if counter[i] >= self.repetitions[i][1]:
                            consumed.add(parser)
                        break
            else:
                for i, parser in enumerate(self.parsers):
                    if counter[i] >= self.repetitions[i][0]:
                        consumed.add(parser)
                if self.non_mandatory <= consumed:
                    if consumed == self.parsers_set:
                        break
                else:
                    return None, text
                reloc, err_node = self.get_reentry_point(text_)
                expected = ' ° '.join([parser.repr for parser in self.parsers])
                error, text_ = self.mandatory_violation(text_, False, expected, reloc, err_node)
                results += (err_node,)
                if reloc < 0:
                    break
            n = length
            length = text_.__len__()
            if length == n:
                break  # avoid infinite loop
        nd = self._return_values(results)  # type: Node
        if error and reloc < 0:  # no worry: reloc is always defined when error is True
            # parser will be moved forward, even if no relocation point has been found
            raise ParserError(self, nd.with_pos(self.grammar.document_length__ - len(text)),
                              len(text) - len(text_),
                              text, error, first_throw=True)
        return nd, text_

    def is_optional(self) -> Optional[bool]:
        return all(r[0] == 0 for r in self.repetitions)

    def __repr__(self):
        def rep(parser: Parser) -> str:
            return '(' + parser.repr + ')' \
                if isinstance(parser, Series) or isinstance(parser, Alternative) else parser.repr

        return ' ° '.join(rep(parser) for parser in self.parsers)

    def _prepare_combined(self, other: Parser) \
            -> Tuple[Tuple[Parser, ...], int, List[Tuple[int, int]]]:
        """Returns the other's parsers and repetitions if `other` is an Interleave-parser,
        otherwise returns ((other,),), [(1, 1])."""
        other = to_interleave(other)
        other_parsers = cast('Interleave', other).parsers if isinstance(other, Interleave) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        other_repetitions = cast('Interleave', other).repetitions \
            if isinstance(other, Interleave) else [(1, 1), ]
        other_mandatory = cast('Interleave', other).mandatory \
            if isinstance(other, Interleave) else NO_MANDATORY
        if other_mandatory == NO_MANDATORY:
            mandatory = self.mandatory
            parsers = self.parsers + other_parsers  # type: Tuple[Parser, ...]
            repetitions = self.repetitions + other_repetitions  # type: List[Tuple[int, int]]
        elif self.mandatory == NO_MANDATORY:
            mandatory = other_mandatory
            parsers = other_parsers + self.parsers
            repetitions = other_repetitions + self.repetitions
        else:
            mandatory = self.mandatory + other_mandatory
            parsers = self.parsers[:self.mandatory] + other_parsers[:other_mandatory] \
                + self.parsers[self.mandatory:] + other_parsers[other_mandatory:]
            repetitions = self.repetitions[:self.mandatory] + other_repetitions[:other_mandatory] \
                + self.repetitions[self.mandatory:] + other_repetitions[other_mandatory:]
        return parsers, mandatory, repetitions

    def __mul__(self, other: Parser) -> 'Interleave':
        if self.pname or other.pname:
            return Interleave(self, other)
        if not isinstance(self, Interleave):
            # for some reason cython called __mul__ instead of __rmul__,
            # so we have to flip self and other...
            self, other = other, self
        parsers, mandatory, repetitions = cast(Interleave, self)._prepare_combined(other)
        return Interleave(*parsers, mandatory=mandatory, repetitions=repetitions)

    def __rmul__(self, other: Parser) -> 'Interleave':
        if self.pname or other.pname:
            return Interleave(other, self)
        parsers, mandatory, repetitions = self._prepare_combined(other)
        return Interleave(*parsers, mandatory=mandatory, repetitions=repetitions)

    def __imul__(self, other: Parser) -> 'Interleave':
        if self.pname or other.pname:
            return Interleave(self, other)
        parsers, mandatory, repetitions = self._prepare_combined(other)
        self.parsers = parsers
        self.mandatory = mandatory
        self.repetitions = repetitions
        return self

    @cython.locals(a=cython.int, b=cython.int)
    def static_analysis(self) -> List['AnalysisError']:
        # assert len(set(parsers)) == len(parsers)  # commented out, because this could make sense
        errors = super().static_analysis()
        if not all(not parser.is_optional() and not isinstance(parser, FlowParser)
                   for parser in self.parsers):
            errors.append(self.static_error(
                "Flow-operators and optional parsers are neither allowed "
                "nor needed in an interleave-parser " + self.location_info(),
                BADLY_NESTED_OPTIONAL_PARSER))
        for parser, (a, b) in zip(self.parsers, self.repetitions):
            if a < 0 or b < 0 or a > b or a > INFINITE or b > INFINITE:
                errors.append(self.static_error(
                    'Repetition count [a=%i, b=%i] for parser %s violates requirement '
                    '0 <= a <= b <= infinity = 2^30' % (a, b, str(parser)),
                    BAD_REPETITION_COUNT))
        return errors

    def _signature(self) -> Hashable:
        return (self.__class__.__name__,) \
               + tuple(p.signature() for p in self.parsers) \
               + tuple(self.repetitions)

########################################################################
#
# Flow control parsers
#
########################################################################

class FlowParser(UnaryParser):
    """
    Base class for all flow parsers like Lookahead and Lookbehind.
    """
    def match(self, bool_value) -> bool:
        """Returns the value. Can be overridden to return the inverted bool."""
        return bool_value


def Required(parser: Parser) -> Parser:
    return Series(parser, mandatory=0)


class Lookahead(FlowParser):
    """
    Matches, if the contained parser would match for the following text,
    but does not consume any text.
    """
    def _parse(self, text: StringView) -> ParsingResult:
        node, _ = self.parser(text)
        if self.match(node is not None):
            return (EMPTY_NODE if self.disposable else Node(self.node_name, '', True)), text
        else:
            return None, text

    def __repr__(self):
        return '&' + self.parser.repr

    def static_analysis(self) -> List[AnalysisError]:
        errors = super().static_analysis()
        if self.parser.is_optional():
            errors.append(AnalysisError(self.pname, self, Error(
                'Lookahead %s does not make sense with optional parser "%s"!'
                % (self.pname, str(self.parser)),
                0, LOOKAHEAD_WITH_OPTIONAL_PARSER)))
        return errors


def _negative_match(grammar, bool_value) -> bool:
    """Match function for Negative Parsers."""
    if bool_value:
        return False
    else:
        # invert the farthest failure, because, due to negation, it's not
        # a failure anymore and should be overwritten by any other failure
        grammar.ff_pos__ = -grammar.ff_pos__
        return True


class NegativeLookahead(Lookahead):
    """
    Matches, if the contained parser would *not* match for the following
    text.
    """
    def __repr__(self):
        return '!' + self.parser.repr

    def match(self, bool_value) -> bool:
        return _negative_match(self.grammar, bool_value)


class Lookbehind(FlowParser):
    """
    Matches, if the contained parser would match backwards. Requires
    the contained parser to be a RegExp, _RE, Text parser.

    EXPERIMENTAL
    """
    def __init__(self, parser: Parser) -> None:
        p = parser
        while isinstance(p, Synonym):
            p = p.parser
        assert isinstance(p, RegExp) or isinstance(p, Text)
        self.regexp = None
        self.text = ''  # type: str
        if isinstance(p, RegExp):
            self.regexp = cast(RegExp, p).regexp
        else:  # p is of type Text
            self.text = cast(Text, p).text
        super(Lookbehind, self).__init__(parser)

    def _parse(self, text: StringView) -> ParsingResult:
        backwards_text = self.grammar.reversed__[text.__len__():]
        if self.regexp is None:  # assert self.text is not None
            does_match = backwards_text[:len(self.text)] == self.text
        else:  # assert self.regexp is not None
            does_match = backwards_text.match(self.regexp)
        if self.match(does_match):
            if self.drop_content:
                return EMPTY_NODE, text
            return Node(self.node_name, '', True), text
        return None, text

    def __repr__(self):
        return '-&' + self.parser.repr


class NegativeLookbehind(Lookbehind):
    """
    Matches, if the contained parser would *not* match backwards. Requires
    the contained parser to be a RegExp-parser.
    """
    def __repr__(self):
        return '-!' + self.parser.repr

    def match(self, bool_value) -> bool:
        return _negative_match(self.grammar, bool_value)


########################################################################
#
# Context-sensitive parsers
#
########################################################################

@lru_cache(maxsize=256)
def is_context_sensitive(parser: Parser) -> bool:
    """Returns True, is ``parser`` is a context-sensitive parser
    or calls a context-sensitive parser."""
    return any(isinstance(pctx[-1], ContextSensitive) for pctx in parser.descendants())
    # for p in parser.descendants():
    #     if isinstance(p, ContextSensitive):
    #         return True
    # return False


class BlackHoleDict(dict):
    """A dictionary that always stays empty. Usae case:
    Disabling memoization."""
    def __setitem__(self, key, value):
        return


class ContextSensitive(UnaryParser):
    """Base class for context-sensitive parsers.

    Context-Sensitive-Parsers are parsers that either manipulate
    (store or change) the values of variables or that read values of
    variables and use them to determine whether the parser matches
    or not.

    While context-sensitive-parsers are quite useful, grammars that
    use them will not be context-free anymore. Plus they breach the
    technology of packrat-parsers. In particular, their results cannot
    simply be memoized by storing them in a dictionary of locations.
    (In other words, the memoization function is not a function of
    parser and location anymore, but would need to be a function
    parser, location and variable (stack-)state.)
    DHParser blocks memoization for context-sensitive-parsers
    (see `Parser.__call__()` and `Forward.__call__()`). As
    a consequence the parsing time cannot be assumed to be strictly
    proportional to the size of the document, anymore. Therefore,
    it is recommended to use context-sensitive-parsers sparingly.
    """

    def gen_memoization_dict(self) -> dict:
        return BlackHoleDict()

    @cython.returns(cython.int)
    @cython.locals(L=cython.int, rb_loc=cython.int)
    def _rollback_location(self, text: StringView, rest: StringView) -> int:
        """
        Determines the rollback location for context-sensitive parsers, i.e.
        parsers that either manipulate (store or change) or use variables.

        Rolling back of variable changes takes place when the parser call sequence
        starts to move forward again. Only those variable changes should be
        rolled back the locations of which have been passed when backtracking.

        The rollback location can also be used to block memoizing. Since
        the result returned by a variable changing parser (or a parser
        that directly or indirectly calls a variable changing parser), should
        never be memoized, memoizing is only triggered, when the location of
        a returning parser is greater than the last rollback location.

        Usually, the rollback location is exactly the location, where the parser
        started parsing. However, the rollback-location must lie before the
        location where the parser stopped, because otherwise variable changes
        would be always be rolled back for parsers that have captured or retrieved
        zero length data. In order to avoid this, the rollback location is
        artificially reduced by one in case the parser did not capture any text
        (either of the two equivalent criteria len(text) == len(rest) or
        node.strlen() == 0) identifies this case. This reduction needs to be
        compensated for, if blocking of memoization is determined by the
        rollback-location as in `Forward.__call__()` where a formula like::

            location <= (grammar.last_rb__loc__ + int(text._len == rest._len)

        determines whether memoization should be blocked.
        """
        L = text._len
        rb_loc = self.grammar.document_length__ - L
        if rest._len == text._len:
            rb_loc -= 1
        return rb_loc

    def _signature(self) -> Hashable:
        return id(self)


class Capture(ContextSensitive):
    """
    Applies the contained parser and, in case of a match, saves the result
    in a variable. A variable is a stack of values associated with the
    contained parser's name. This requires the contained parser to be named.
    """
    def __init__(self, parser: Parser, zero_length_warning: bool = True) -> None:
        super(Capture, self).__init__(parser)
        self.zero_length_warning: bool = zero_length_warning
        self._can_capture_zero_length: Optional[bool] = None

    def __deepcopy__(self, memo):
        symbol = copy.deepcopy(self.parser, memo)
        duplicate = self.__class__(symbol, self.zero_length_warning)
        copy_combined_parser_attrs(self, duplicate)
        duplicate._can_capture_zero_length = self._can_capture_zero_length
        return duplicate

    @property
    def can_capture_zero_length(self) -> bool:
        if self._can_capture_zero_length is None:
            self._can_capture_zero_length = self.parser._parse(StringView(""))[0] is not None
        return cast(bool, self._can_capture_zero_length)

    def _rollback(self):
        return self.grammar.variables__[self.pname].pop()

    def _parse(self, text: StringView) -> ParsingResult:
        node, text_ = self.parser(text)
        if node is not None:
            assert self.pname, """Tried to apply an unnamed capture-parser!"""
            assert not self.parser.drop_content, \
                "Cannot capture content from parsers that drop content!"
            self.grammar.variables__[self.pname].append(node.content)
            self.grammar.push_rollback__(self._rollback_location(text, text_), self._rollback)
            return self._return_value(node), text_
        else:
            return None, text

    def __repr__(self):
        return self.parser.repr

    def static_analysis(self) -> List[AnalysisError]:
        errors = super().static_analysis()
        if not self.pname:
            errors.append(AnalysisError(self.pname, self, Error(
                'Capture only works as named parser! Error in parser: ' + str(self),
                0, CAPTURE_WITHOUT_PARSERNAME
            )))
        if self.parser.apply(lambda plist: plist[-1].drop_content):
            errors.append(AnalysisError(self.pname, self, Error(
                'Captured symbol "%s" contains parsers that drop content, '
                'which can lead to unintended results!' % (self.pname or str(self)),
                0, CAPTURE_DROPPED_CONTENT_WARNING
            )))
        if self.zero_length_warning:
            node, _ = self.parser._parse(StringView(''))
            if node is not None:
                errors.append(AnalysisError(self.pname, self, Error(
                    'Variable "%s" captures zero length strings, which can lead to '
                    'its remaining on the stack after backtracking!' % (self.pname or str(self)),
                    0, ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING
                )))
                self._can_capture_zero_length = True
            else:
                self._can_capture_zero_length = False
        return errors


MatchVariableFunc = Callable[[Union[StringView, str], List[str]], Optional[str]]
# (text, stack) -> value, where:
# text is the following text for be parsed
# stack is a stack of stored variables (for a particular symbol)
# and the return value is the matched text (which can be the empty string) or
# None, if no match occurred

# Match functions, the name of which starts with 'optional_', must never return
# None, but should return the empty string if no match occurs.
# Match functions, the name of which does not start with 'optional_', should
# on the contrary always return `None` if no match occurs!


def last_value(text: Union[StringView, str], stack: List[str]) -> Optional[str]:
    """Matches `text` with the most recent value on the capture stack.
    This is the default case when retrieving captured substrings."""
    try:
        value = stack[-1]
        return value if text.startswith(value) else None
    except IndexError:
        return None


def optional_last_value(text: Union[StringView, str], stack: List[str]) -> Optional[str]:
    """Matches `text` with the most recent value on the capture stack or
    with the empty string, i.e. `optional_match` never returns `None` but
    either the value on the stack or the empty string.

    Use case: Implement shorthand notation for matching tags, i.e.:

        Good Morning, Mrs. <emph>Smith</>!
    """
    # print('SKIP', text.replace('\n', '\\n'))
    value = stack[-1]
    return value if text.startswith(value) else ""


def matching_bracket(text: Union[StringView, str], stack: List[str]) -> Optional[str]:
    """Returns a closing bracket for the opening bracket on the capture stack,
    i.e. if "[" was captured, "]" will be retrieved."""
    value = stack[-1]
    value = value.replace("(", ")").replace("[", "]").replace("{", "}").replace("<", ">")
    return value if text[:len(value)] == value else None


class Retrieve(ContextSensitive):
    """
    Matches if the following text starts with the value of a particular
    variable. As a variable in this context means a stack of values,
    the last value will be compared with the following text. It will not
    be removed from the stack! (This is the difference between the
    `Retrieve` and the `Pop` parser.)
    The constructor parameter `symbol` determines which variable is
    used.

    Attributes:
        symbol: The parser that has stored the value to be retrieved, in
            other words: "the observed parser"
        match_func: a procedure that through which the processing to the
            retrieved symbols is channeled. In the simplest case it merely
            returns the last string stored by the observed parser. This can
            be (mis-)used to execute any kind of semantic action.
    """

    def __init__(self, symbol: Parser, match_func: MatchVariableFunc = None) -> None:
        assert isinstance(symbol, Capture)
        super(Retrieve, self).__init__(symbol)
        self.match = match_func if match_func else last_value

    def __deepcopy__(self, memo):
        symbol = copy.deepcopy(self.parser, memo)
        duplicate = self.__class__(symbol, self.match)
        copy_combined_parser_attrs(self, duplicate)
        return duplicate

    @property
    def symbol_pname(self) -> str:
        """Returns the watched symbol's pname, properly, i.e. even in cases
        where the symbol's parser is shielded by a Forward-parser"""
        return self.parser.pname or cast(Forward, self.parser).parser.pname

    def get_node_name(self) -> str:
        """Returns a name for the retrieved node. If the Retrieve-parser
        has a node-name, this overrides the node-name of the retrieved symbol's
        parser."""
        if self.disposable or not self.node_name:
            return self.parser.pname or cast(Forward, self.parser).parser.pname
            # if self.parser.pname:
            #     return self.parser.name
            # # self.parser is a Forward-Parser, so pick the name of its encapsulated parser
            # return cast(Forward, self.parser).parser.name
        return self.node_name

    def _parse(self, text: StringView) -> ParsingResult:
        # auto-capture on first use if symbol was not captured before
        if len(self.grammar.variables__[self.symbol_pname]) == 0:
            node, text_ = self.parser(text)   # auto-capture value
            if node is None:
                # set last_rb__loc__ to avoid memoizing of retrieved results
                self.grammar.push_rollback__(self._rollback_location(text, text_), lambda: None)
                return None, text_
        node, text_ = self.retrieve_and_match(text)
        # set last_rb__loc__ to avoid memoizing of retrieved results
        self.grammar.push_rollback__(self._rollback_location(text, text_), lambda: None)
        return node, text_

    def __repr__(self):
        return ':' + self.parser.repr

    def retrieve_and_match(self, text: StringView) -> ParsingResult:
        """
        Retrieves variable from stack through the match function passed to
        the class' constructor and tries to match the variable's value with
        the following text. Returns a Node containing the value or `None`
        accordingly.
        """
        # `or self.parser.parser.pname` needed, because Forward-Parsers do not have a pname
        try:
            stack = self.grammar.variables__[self.symbol_pname]
            value = self.match(text, stack)
        except (KeyError, IndexError):
            tn = self.get_node_name()
            if self.match.__name__.startswith('optional_'):
                # returns a None match if parser is optional but there was no value to retrieve
                return None, text
            else:
                node = Node(tn, '', True)  # .with_pos(self.grammar.document_length__ - text.__len__())
                self.grammar.tree__.new_error(
                    node, dsl_error_msg(self, "'%s' undefined or exhausted." % self.symbol_pname),
                    UNDEFINED_RETRIEVE)
                return node, text
        if value is None:
            return None, text
        elif self.drop_content:
            return EMPTY_NODE, text[len(value):]
        return Node(self.get_node_name(), value), text[len(value):]


class Pop(Retrieve):
    """
    Matches if the following text starts with the value of a particular
    variable. As a variable in this context means a stack of values,
    the last value will be compared with the following text. Other
    than the `Retrieve`-parser, the `Pop`-parser removes the value
    from the stack in case of a match.

    The constructor parameter `symbol` determines which variable is
    used.
    """
    def __init__(self, symbol: Parser, match_func: MatchVariableFunc = None) -> None:
        super(Pop, self).__init__(symbol, match_func)

    def reset(self):
        super(Pop, self).reset()
        self.values = []

    # def __deepcopy__(self, memo):
    #     symbol = copy.deepcopy(self.parser, memo)
    #     duplicate = self.__class__(symbol, self.match)
    #     copy_combined_parser_attrs(self, duplicate)
    #     duplicate.values = self.values[:]
    #     return duplicate

    def _rollback(self):
        self.grammar.variables__[self.symbol_pname].append(self.values.pop())

    def _parse(self, text: StringView) -> ParsingResult:
        node, text_ = self.retrieve_and_match(text)
        if node is not None and not id(node) in self.grammar.tree__.error_nodes:
            self.values.append(self.grammar.variables__[self.symbol_pname].pop())
            self.grammar.push_rollback__(self._rollback_location(text, text_), self._rollback)
        else:
            # set last_rb__loc__ to avoid memoizing of retrieved results
            self.grammar.push_rollback__(self._rollback_location(text, text_), lambda: None)
        return node, text_

    def __repr__(self):
        stack = self.grammar.variables__.get(self.symbol_pname, [])
        content = (' "%s"' % stack[-1]) if stack else ''
        prefix = ':?' if self.match.__name__.startswith('optional_') else '::'
        return prefix + self.parser.repr + content


########################################################################
#
# Aliasing parser classes
#
########################################################################


class Synonym(UnaryParser):
    r"""
    Simply calls another parser and encapsulates the result in
    another node if that parser matches.

    This parser is needed to support synonyms in EBNF, e.g.::

        jahr       = JAHRESZAHL
        JAHRESZAHL = /\d\d\d\d/

    Otherwise the first line could not be represented by any parser
    class, in which case it would be unclear whether the parser
    RegExp('\d\d\d\d') carries the name 'JAHRESZAHL' or 'jahr'.
    """
    def __init__(self, parser: Parser) -> None:
        assert not parser.drop_content
        super(Synonym, self).__init__(parser)

    def _parse(self, text: StringView) -> ParsingResult:
        node, text = self.parser(text)
        if node is not None:
            if self.drop_content:
                return EMPTY_NODE, text
            if not self.disposable:
                if node is EMPTY_NODE:
                    return Node(self.node_name, '', True), text
                if node.name[0] == ':':  # node.anonymous:
                    # eliminate anonymous child-node on the fly
                    node.name = self.node_name
                else:
                    return Node(self.node_name, (node,)), text
        return node, text

    def __str__(self):
        return self.pname + (' = ' if self.pname else '') + self.parser.repr

    def __repr__(self):
        return self.pname or self.parser.repr


class Forward(UnaryParser):
    r"""
    Forward allows to declare a parser before it is actually defined.
    Forward declarations are needed for parsers that are recursively
    nested, e.g.::

        class Arithmetic(Grammar):
            '''
            expression =  term  { ("+" | "-") term }
            term       =  factor  { ("*" | "/") factor }
            factor     =  INTEGER | "("  expression  ")"
            INTEGER    =  /\d+/~
            '''
            expression = Forward()
            INTEGER    = RE('\\d+')
            factor     = INTEGER | TKN("(") + expression + TKN(")")
            term       = factor + ZeroOrMore((TKN("*") | TKN("/")) + factor)
            expression.set(term + ZeroOrMore((TKN("+") | TKN("-")) + term))
            root__     = expression

    :ivar recursion_counter:  Mapping of places to how often the parser
            has already been called recursively at this place. This
            is needed to implement left recursion. The number of
            calls becomes irrelevant once a result has been memoized.
    """

    def __init__(self):
        super(Forward, self).__init__(get_parser_placeholder())
        # self.parser = get_parser_placeholder  # type: Parser
        self.cycle_reached = False  # type: bool

    def reset(self):
        super(Forward, self).reset()
        self.recursion_counter = dict()  # type: Dict[int, int]
        assert not self.pname, "Forward-Parsers mustn't have a name!"

    def name(self, pname: str, disposable: bool = False) -> 'Parser':
        """Sets the parser name to `pname` and returns `self`."""
        assert not pname, "Forward-parser mustn't have a name. "\
            'Use pname="" when calling  Forward.name()'
        super().name(pname, disposable)
        return self

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        memo[id(self)] = duplicate
        copy_parser_base_attrs(self, duplicate)
        parser = copy.deepcopy(self.parser, memo)
        duplicate.parser = parser
        duplicate.pname = self.pname        # Forward-Parsers should not have a name!
        duplicate.disposable = self.disposable
        duplicate.node_name = self.node_name  # Forward-Parser should not have a tag name!
        duplicate.drop_content = parser.drop_content
        return duplicate

    @cython.locals(location=cython.int, depth=cython.int, rb_stack_size=cython.int)
    def __call__(self, text: StringView) -> ParsingResult:
        """
        Overrides `Parser.__call__`, because Forward is not an independent parser
        but merely a redirects the call to another parser. Other than parser
        `Synonym`, which might be a meaningful marker for the syntax tree,
        parser Forward should never appear in the syntax tree.

        `Forward.__call__` also takes care of (most of) the left recursion
        handling. In order to do so it (unfortunately) has to duplicate some code
        from `Parser.__call__`.

        The algorithm roughly follows:
        https://medium.com/@gvanrossum_83706/left-recursive-peg-grammars-65dab3c580e1
        See also:
        http://www.vpri.org/pdf/tr2007002_packrat.pdf
        """
        grammar = self.grammar
        if not grammar.left_recursion__:  # TODO: add a static check and flag: self.left_recursive__!
            return self.parser(text)

        location = grammar.document_length__ - text._len
        # rollback variable changing operation if parser backtracks
        # to a position before the variable changing operation occurred
        if location <= grammar.last_rb__loc__:
            grammar.rollback_to__(location)

        # if location has already been visited by the current parser, return saved result
        visited = self.visited  # using local variable for better performance
        if location in visited:
            # no history recording in case of memoized results!
            return visited[location]

        if location in self.recursion_counter:
            depth = self.recursion_counter[location]
            if depth == 0:
                grammar.suspend_memoization__ = True
                result = None, text
            else:
                self.recursion_counter[location] = depth - 1
                result = self.parser(text)
                self.recursion_counter[location] = depth  # allow moving back and forth
        else:
            self.recursion_counter[location] = 0  # fail on the first recursion
            save_suspend_memoization = grammar.suspend_memoization__
            grammar.suspend_memoization__ = False
            history_pointer = len(grammar.history__)

            result = self.parser(text)

            if result[0] is not None:
                # keep calling the (potentially left-)recursive parser and increase
                # the recursion depth by 1 for each call as long as the length of
                # the match increases.
                last_history_state = grammar.history__[history_pointer:len(grammar.history__)]
                depth = 1
                while True:
                    self.recursion_counter[location] = depth
                    grammar.suspend_memoization__ = False
                    rb_stack_size = len(grammar.rollback__)
                    grammar.history__ = grammar.history__[:history_pointer]
                    # reduplication of error messages will be caught by nodetree.RootNode.add_error()
                    # saving and restoring the errors-messages state on each iteration presupposes
                    # that error messages will be recreated every time, which, however, does not
                    # happen because of memoization. (This is a downside of global error-reporting
                    # in contrast to attaching error-messages locally to the node where they
                    # occurred. Big topic...)
                    # don't carry error/resumption-messages over to the next iteration
                    # grammar.most_recent_error__ = None
                    next_result = self.parser(text)

                    # discard next_result if it is not the longest match and return
                    if len(next_result[1]) >= len(result[1]):  # also true, if no match
                        # Since the result of the last parser call (`next_result`) is discarded,
                        # any variables captured by this call should be "rolled back", too.
                        while len(grammar.rollback__) > rb_stack_size:
                            _, rb_func = grammar.rollback__.pop()
                            rb_func()
                            grammar.last_rb__loc__ = grammar.rollback__[-1][0] \
                                if grammar.rollback__ else -2
                        # Finally, overwrite the discarded result in the last history record with
                        # the accepted result, i.e. the longest match.
                        # TODO: Move this to trace.py, somehow... and make it less confusing
                        #       that the result is not the last but the longest match...
                        grammar.history__ = grammar.history__[:history_pointer] + last_history_state
                        # record = grammar.history__[-1]
                        # if record.call_stack[-1] == (self.parser.pname, location):
                        #     record.text = result[1]
                        #     delta = len(text) - len(result[1])
                        #     assert record.node.name != ':None'
                        #     record.node.result = text[:delta]
                        break

                    last_history_state = grammar.history__[history_pointer:len(grammar.history__)]
                    result = next_result
                    depth += 1
            # grammar.suspend_memoization__ = save_suspend_memoization \
            #     or location <= (grammar.last_rb__loc__ + int(text._len == result[1]._len))
            grammar.suspend_memoization__ = save_suspend_memoization  #  = is_context_sensitive(self.parser)
            if not grammar.suspend_memoization__:
                visited[location] = result
        return result

    def set_proxy(self, proxy: Optional[ParseFunc]):
        """`set_proxy` has no effects on Forward-objects!"""
        return

    def __cycle_guard(self, func, alt_return):
        """
        Returns the value of `func()` or `alt_return` if a cycle has
        been reached (which can happen if `func` calls methods of
        child parsers).
        """
        if self.cycle_reached:
            return alt_return
        else:
            self.cycle_reached = True
            ret = func()
            self.cycle_reached = False
            return ret

    def __repr__(self):
        return self.__cycle_guard(lambda: repr(self.parser), '...')

    def __str__(self):
        return self.__cycle_guard(lambda: str(self.parser), '...')

    @property
    def repr(self) -> str:
        """Returns the parser's name if it has a name or repr(self) if not."""
        return self.parser.pname if self.parser.pname else self.__repr__()

    def set(self, parser: Parser):
        """
        Sets the parser to which the calls to this Forward-object
        shall be delegated.
        """
        self.parser = parser
        self.drop_content = parser.drop_content

    def sub_parsers(self) -> Tuple[Parser, ...]:
        """Note: Sub-Parsers are not passed through by Forward-Parser."""
        if is_parser_placeholder(self.parser):
            return tuple()
        return self.parser,

    def _signature(self) -> Hashable:
        # This code should theoretically never be reached, except when debugging
        signature = self.pname or self.parser.pname
        assert signature
        return signature
