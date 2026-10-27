# parse_base.py - base class for all parser combinators
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
Module parse_base defines class Parser which is the root class
for all parser classes. Most notably, the memoization is handled
by the base class. Furthermore. base class for leaf-parsers and
non-memoizing parsers are defined.
"""


from __future__ import annotations

from inspect import isclass
from typing import Callable, cast, Union, Optional, TYPE_CHECKING

from DHParser.configuration import get_config_value
from DHParser.error import Error, ErrorCode, MANDATORY_CONTINUATION_AT_EOF, \
    RECURSION_DEPTH_LIMIT_HIT, MANDATORY_CONTINUATION_AT_EOF_NON_ROOT
from DHParser.nodetree import Node, ZOMBIE_TAG, EMPTY_NODE, ChildrenType, ResultType
from DHParser.parse_error import ParserError, reentry_point, artifact
from DHParser.toolkit import TypeAlias, List, Tuple, Any, MutableSet, Set, FrozenSet, \
    Dict, INFINITE

try:
    import cython
except (ImportError, NameError):
    import DHParser.externallibs.shadow_cython as cython


if TYPE_CHECKING:
    from DHParser.parse_grammar import Grammar, AnalysisError
    from DHParser.parse_combinators import Series, Alternative, Interleave



########################################################################
#
# Parser base class
#
########################################################################


class BlackHoleDict(dict):
    """A dictionary that always stays empty. Use case:
    Disabling memoization (for whatever reason)."""
    def __setitem__(self, key, value):
        return
    def __getitem__(self, key):
        raise AssertionError(f'BlackHoleDict cannot be read from. Key: {key}')
    def __contains__(self, key):
        raise AssertionError(f'BlackHoleDict cannot be queried. Key: {key}')


BLACKHOLE_SINGLETON = BlackHoleDict()


def NOCALL(*args, **kwargs):
    assert False, f'illegal method-call on PLACEHOLDER-object!'


_GRAMMAR_PLACEHOLDER: Optional['Grammar'] = None


def get_grammar_placeholder() -> 'Grammar':
    global _GRAMMAR_PLACEHOLDER
    if _GRAMMAR_PLACEHOLDER is None:
        _GRAMMAR_PLACEHOLDER = Grammar.__new__(Grammar)
        if not cython.compiled:
            _GRAMMAR_PLACEHOLDER.__call__ = NOCALL
        _GRAMMAR_PLACEHOLDER.COMMENT__ = 'Grammar placeholder'
    return _GRAMMAR_PLACEHOLDER


def is_grammar_placeholder(grammar: Optional[Union['Grammar', type]]) -> bool:
    from DHParser.parse_grammar import Grammar
    x = Grammar
    return grammar is None \
        or cast(Grammar, grammar) is _GRAMMAR_PLACEHOLDER \
        or isclass(grammar) and issubclass(cast(type, grammar), Grammar)


ParsingResult: TypeAlias = Tuple[Optional[Node], int]
MemoizationDict: TypeAlias = Dict[int, ParsingResult]

ApplyFunc: TypeAlias = Callable[['Parser'], Optional[bool]]
ParserTrail: TypeAlias = Tuple['Parser', ...]
ApplyToTrailFunc: TypeAlias = Callable[[ParserTrail], Optional[bool]]
# The return value of "True" stops any further application
FlagFunc: TypeAlias = Callable[[ApplyFunc, MutableSet[ApplyFunc]], bool]
ParseFunc: TypeAlias = Callable[['Parser', int], ParsingResult]
BoundParseFunc: TypeAlias = Callable[[int], ParsingResult]


class Parser:
    r"""
    (Abstract) Base class for Parser combinator parsers. Any parser
    object that is actually used for parsing (i.e. no mock parsers)
    should be derived from this class.

    Since parsers can contain other parsers (see classes UnaryOperator
    and NaryOperator) they form a cyclical directed graph. A root
    parser is a parser from which all other parsers can be reached.
    Usually, there is one root parser, which serves as the starting
    point of the parsing process. When speaking of "the root parser"
    it is this root parser object that is meant.

    There are two different types of parsers:

    1. *Named parsers* for which a name is set in field "parser.pname".
       The results produced by these parsers can later be retrieved in
       the AST by the parser name.

    2. *Disposable parsers* where the name-field just contains the empty
       string. AST-transformation of disposable parsers can be hooked
       only to their class name, and not to the individual parser.

    Parser objects are callable and parsing is done by calling a parser
    object with the text to parse.

    If the parser matches, it returns a tuple consisting of a node
    representing the root of the concrete syntax tree resulting from the
    match as well as the substring text[i:] where i is the length of
    matched text (which can be zero in the case of parsers like
    :py:class:`ZeroOrMore` or :py:class:`Option`). If i > 0 then the
    parser has "moved forward".

    If the parser does not match, it returns (None, text). **Note** that
    this is not the same as an empty match ("", text). Any empty match
    can, for example, be returned by the :py:class:`ZeroOrMore`-parser in case
    the contained parser is repeated zero times.

    :ivar pname:  The parser's name. Hint: Forward-parsers do not have a
                pname, even though they are always associated with a symbol.
                Be sure, to test for Forward-parsers where needed and then pick
                cast(ForwardBase, parser).parser.pname !

    :ivar disposable: A property indicating that the parser returns
                anonymous nodes. For performance
                reasons this is implemented as an object variable rather
                than a property. This property should always be equal to
                ``self.name[0] == ":"``.

    :ivar drop_content: A property (for performance reasons implemented as
                simple field) that, if set, induces the parser not to return
                the parsed content or subtree if it has matched but the
                dummy EMPTY_NODE`. In effect the parsed content will be
                dropped from the concrete syntax tree already. Only
                anonymous (or pseudo-anonymous) parsers are allowed to
                drop content.

    :ivar node_name: The name for the nodes that are created by
                the parser. If the parser is named, this is the same as
                "pname", otherwise it is the name of the parser's type
                prefixed with a colon ":".

    :ivar visited:  Mapping of places this parser has already been to
                during the current parsing process onto the results the
                parser returned at the respective place. This dictionary
                is used to implement memoizing.

    :ivar \_parse_proxy: Usually, just a reference to "self._parse", but can
                be overwritten to run th call to the "_parse"-method
                through a proxy like, for example, a tracing debugger.
                See :py:mod:`~DHParser.trace`

    :ivar \_sub_parsers: Set of parsers that are directly referred to by
                this parser, e.g. parser "a" defined by the EBNF-expression
                "a = b (b | c)" has the sub-parser-set {b, c}.

                Notes: 1.the set is empty for parsers that derive neither
                from :py:class:`UnaryParser` nor from :py:class:`NaryParser`
                2. unary parsers have exactly one sub-parser 3. n-ary parsers
                have one or more sub_parsers. For n-ary-parsers
                len(p.sub_parser) can be lower than len(p.parsers), in case
                one and the same parser is referred to more than once
                in the contained parser's list.

    :ivar _grammar:  A reference to the Grammar object to which the parser
                is attached.

    :ivar _symbol: The closest named parser to which this
                parser is connected in a grammar. If the parser itself is
                named, this is the same as self. _symbol is private and
                should be accessed only via the symbol-property which
                will initialize its value on first use.

    :ivar _descendants_cache: A cache of all descendant parsers that can be
                reached from this parser.

    :ivar _desc_trails_cache:  A cache of the trails (i.e. list of parsers)
                from this parser to all other parsers that can be reached from
                this parser.
    """

    def __init__(self) -> None:
        # assert isinstance(name, str), str(name)
        self.pname: str = ''
        self.ptype: str = ':' + self.__class__.__name__
        self.node_name: str = self.ptype
        self.disposable: bool = True
        self.drop_content: bool = False
        self._sub_parsers: FrozenSet[Parser] = frozenset()
        # this indirection is required for Cython-compatibility
        self._parse_proxy: BoundParseFunc = self._parse
        try:
            self._grammar: Grammar = get_grammar_placeholder()
        except NameError:
            pass                        # ensures Cython-compatibility
        self._symbol = ''               # type: str
        self._descendants_cache: Optional[Set[Parser]] = None
        self._anon_desc_cache: Optional[Set[Parser]] = None
        self._desc_trails_cache: Optional[Set[ParserTrail]] = None
        self.reset()

    def __deepcopy__(self, memo):
        r"""Deepcopy method of the parser. Upon instantiation of a Grammar-object,
        parsers will be deep-copied to the Grammar object. If a
        derived parser-class changes the signature of the "__init__"-constructor,
        "__deepcopy__"-method must be replaced (i.e. overridden without
        calling the same method from the superclass) by the derived class.
        """
        duplicate = self.__class__()
        copy_parser_base_attrs(self, duplicate, memo)
        return duplicate

    def __repr__(self):
        return self.pname + self.ptype

    def __str__(self):
        return self.pname + (' = ' if self.pname else '') + repr(self)

    # @property
    # def ptype(self) -> str:
    #     """Returns a type name for the parser. By default, this is the name of
    #     the parser class with an added leading colon ':'. """
    #     return ':' + self.__class__.__name__

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
        """Returns the parser's name if it has a name and "self.__repr__()" otherwise."""
        return self.pname if self.pname else self.__repr__()

    def reset(self):
        """Initializes or resets any parser variables. If overwritten,
        the "reset()"-method of the parent class must be called from the
        "reset()"-method of the derived class."""
        # global _GRAMMAR_PLACEHOLDER
        # grammar = self._grammar
        self.visited: MemoizationDict = dict()

    @cython.locals(next_location=cython.int, location=cython.int, gap=cython.int, i=cython.int)
    def _handle_parsing_error(self, pe: ParserError, location: cython.int) -> ParsingResult:
        grammar = self._grammar
        gap = pe.location - location
        cut = grammar.document__[location:location + gap]
        rules = tuple(grammar.resume_rules__.get(self.symbol, []))
        next_location = pe.location + pe.node_orig_len
        rest = grammar.document__[next_location:]
        i, skip_node = reentry_point(
            rest, rules, grammar.comment_rx__, grammar.reentry_search_window__,
            f'{pe.parser.symbol}_resume')
        if i >= 0 or self == grammar.start_parser__:
            # either a reentry point was found or the
            # error has fallen through to the first level
            assert pe.node._children or (not pe.node.result)
            # apply reentry-rule or catch error at root-parser
            if i < 0:  i = 0
            zombie = pe.node.pick_child(artifact)  # type: Optional[Node]
            if zombie and not zombie.result:
                zombie.result = rest[:i]
                zombie.name = skip_node.name
                tail = tuple()  # type: ChildrenType
            else:
                # nd.attr['err'] = pe.error.message
                tail = (skip_node,)
            next_location += i
            if pe.first_throw:
                node = pe.node
                node.result = node._children + tail
            else:
                node = (Node(self.node_name, (Node(ZOMBIE_TAG, cut), pe.node) + tail)
                        .with_pos(location))
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
            result = (Node(ZOMBIE_TAG, cut), pe.node) if gap else pe.node  # type: ResultType
            raise pe.new_PE(node=Node(self.node_name, result).with_pos(location),
                            node_orig_len=pe.node_orig_len + gap,
                            location=location, first_throw=False)
        return node, next_location

    def _handle_recursion_error(self, location: int) -> ParsingResult:
        grammar = self._grammar
        text = grammar.document__[location:]
        node = Node(ZOMBIE_TAG, str(text[:min(10, max(1, text.find("\n")))]) + " ...")
        node._pos = location
        msg = ("Maximum recursion depth of parser reached; potentially due to too many "
               "errors or left recursion!")
        if get_config_value('left_recursion').lower() == 'none':
            msg += " (Setting config value 'left_recursion' to 'full' may help.)"
        error = Error(msg, location, RECURSION_DEPTH_LIMIT_HIT)
        grammar.tree__.add_error(node, error)
        grammar.most_recent_error__ = ParserError(self, node, node.strlen(), location, error,
                                                  first_throw=False)
        next_location = len(grammar.document__)
        return node, next_location

    @cython.locals(next_location=cython.int, gap=cython.int, i=cython.int, save_suspend_memoization=cython.bint)
    def __call__(self: Parser, location: cython.int) -> ParsingResult:
        """Applies the parser to the given text. This is a wrapper method that adds
        the business intelligence that is common to all parsers. The actual parsing is
        done in the overridden method "_parse()". This wrapper-method can be thought of
        as a "parser guard", because it guards the parsing process.
        """
        grammar = self._grammar

        try:
            # roll-back variable-changing operation if the parser backtracks to a position
            # before or at the location where the variable-changing operation occurred
            if location <= grammar.last_rb__loc__:
                grammar.rollback_to__(location)

            # if location has already been visited by the current parser, return saved result
            visited = self.visited  # using local variable for better performance
            if location in visited and grammar.use_memo__:
                if grammar.history_tracking__  and self._parse_proxy.__name__ == 'trace_history' \
                        and self._parse_proxy.__module__ == 'DHParser.trace':
                    return self._parse_proxy(-location or -INFINITE)  # a negative location signals a memo-hit
                return visited[location]

            save_suspend_memoization = grammar.suspend_memoization__
            grammar.suspend_memoization__ = False

            # now, the actual parser call!
            try:
                node, next_location = self._parse_proxy(location)
            except ParserError as pe:
                # catching up with parsing after an error occurred
                node, next_location = self._handle_parsing_error(pe, location)

            if node is None:
                if location > grammar.ff_pos__:
                    grammar.ff_pos__ = location
                    grammar.ff_parser__ = self
            elif node is not EMPTY_NODE:
                node._pos = location

            if not grammar.suspend_memoization__:
                visited[location] = (node, next_location)
                grammar.suspend_memoization__ = save_suspend_memoization

        except RecursionError:
            node, next_location = self._handle_recursion_error(location)
        return node, next_location

    def __add__(self, other: Parser) -> 'Series':
        """The + operator generates a series-parser that applies two
        parsers in sequence."""
        from DHParser.parse_combinators import Series
        if isinstance(other, Series):
            return cast('Series', other).__radd__(self)
        return Series(self, other)

    def __or__(self, other: Parser) -> 'Alternative':
        """The | operator generates an alternative parser that applies
        the first parser and, if that does not match, the second parser.
        """
        from DHParser.parse_combinators import Alternative
        if isinstance(other, Alternative):
            return cast('Alternative', other).__ror__(self)
        return Alternative(self, other)

    def __mul__(self, other: Parser) -> 'Interleave':
        """The * operator generates an interleave-parser that applies
        the first parser and the second parser in any possible order
        until both match.
        """
        from DHParser.parse_combinators import Interleave
        if isinstance(other, Interleave):
            return other.__rmul__(self)
        return Interleave(self, other)

    def _parse(self, location: cython.int) -> ParsingResult:
        """Applies the parser at the given location and returns a node with
        the results or None as well as the text at the position right behind
        the matching string."""
        raise NotImplementedError(f"{type(self)}._parse() not implemented and "
            f"{self.effective_pname() or self}._parse() not overwritten by "
            "Parser.set_proxy() or trace.set_tracer()!")

    def is_optional(self) -> Optional[bool]:
        """Returns "True", if the parser can never fail, i.e. never yields
        "None" instead of a node. Returns "False", if the parser can fail.
        Returns "None" if it is not known whether the parser can fail.
        """
        return None

    def set_proxy(self, proxy: Optional[ParseFunc]):
        """Sets a proxy that replaces the _parse()-method. Call "set_proxy"
        with "None" to remove a previously set proxy. Typical use case is
        the installation of a tracing debugger. See module "trace".
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
            if self._parse_proxy != self._parse and proxy != self._parse\
                    and proxy != self._parse_proxy:
                # in the following `encode('utf-8')` is silly but needed, because
                # MS Windows might otherwise crash with an encoding-error :-(
                raise AssertionError((f"A new parsing proxy can only be set if the old"
                    f'parsing proxy has been cleared with "parser.set_proxy(None)", first! '
                    f'Parser "{self}" still has proxy: "{self._parse_proxy}" which cannot '
                    f'be overwritten with "{proxy}".').encode('utf-8'))
            self._parse_proxy = cast(ParseFunc, proxy)

    def name(self, pname: str="", disposable: Optional[bool] = None) -> Parser:  # -> Self for Python 3.11 and above...
        """Sets the parser name to "pname" and returns "self". If
        `disposable` is True, the nodes produced by the parser will also be
        marked as disposable, i.e. they can be eliminated bur their content
        will be retained. The same can be achieved by prefixing the panme-string
        with a colon ":" or with "HIDE:". Another possible prefix is "DROP:"
        in which case the nodes will be dropped entirely, including their
        content. (This is useful to keep delimiters out of the syntax-tree.)
        """
        assert pname, "Tried to assigned empty name!"
        assert self.pname == "" or self.pname == pname, f'Parser name cannot be reassigned! "{self.pname}" -> "{pname}"'

        if pname[0:1] == ":":
            self.disposable = True
            if disposable is False:  self.disposable = False
            self.pname = pname[1:]
            self.node_name = pname
        elif pname[0:5] == "HIDE:":
            assert disposable or disposable is None
            self.disposable = True
            self.pname = pname[5:]
            self.node_name = pname[4:]
        elif pname[0:5] == "DROP:":
            assert disposable or disposable is None
            self.disposable = True
            self.pname = pname[5:]
            self.node_name = pname[4:]
            Drop(self)
        else:
            if pname[0:1] == "$":
                pname = pname[1:]
            else:  # self.pname will not be set for macros!
                self.pname = pname
            self.disposable = False
            if disposable is True:
                self.disposable = True
                self.node_name = ':' + pname
            else:
                self.node_name = pname
        return self

    def effective_pname(self) -> str:
        """Returns the parser's pname. In the case of a Forward-parser,
        returns parser.parser.pname."""
        return self.pname

    @property
    def grammar(self) -> 'Grammar':
        try:
            # if not is_grammar_placeholder(self._grammar):
            #     return self._grammar
            # else:
            #     raise ValueError('Grammar has not yet been set!')
            assert not is_grammar_placeholder(self._grammar)
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

    @property
    def sub_parsers(self) -> FrozenSet[Parser]:
        return self._sub_parsers

    @sub_parsers.setter
    def sub_parsers(self, f: FrozenSet[Parser]):
        self._sub_parsers = f

    def descendants(self, grammar = _GRAMMAR_PLACEHOLDER) -> Set[Parser]:
        """Returns a set of self and all descendant parsers,
        avoiding circles."""
        if self._descendants_cache is None:
            # Caches descendants, avoiding cycles; updates grammar if needed
            if self._desc_trails_cache:
                self._descendants_cache = set(pt[-1] for pt in self._desc_trails_cache)
            else:
                if  is_grammar_placeholder(grammar):   grammar = self._grammar
                visited = set()

                def collect(parser: Parser):
                    nonlocal visited
                    if parser not in visited:
                        visited.add(parser)
                        for p in parser.sub_parsers:
                            collect(p)
                collect(self)
                self._descendants_cache = frozenset(visited)  # tuple(p for p in collect(self))
        return self._descendants_cache

    def descendant_trails(self) -> Set[ParserTrail]:
        """Returns a set of the trails of self and all descendant
        parsers, avoiding circles. NOTE: The algorithm is rather sloppy, and
        the returned set is not really comprehensive but sufficient to trace
        anonymous parsers to their nearest named ancestor."""
        if self._desc_trails_cache is None:
            visited: MutableSet[Parser] = set()
            trails: MutableSet[Tuple[Parser, ...]] = set()

            def collect_trails(parser: Parser, ptrl: List[Parser]):
                nonlocal visited, trails
                if parser not in visited:
                    visited.add(parser)
                    ptrl.append(parser)
                    trails.add(tuple(ptrl))
                    for p in parser.sub_parsers:
                        collect_trails(p, ptrl)
                    ptrl.pop()

            collect_trails(self, [])
            self._desc_trails_cache = frozenset(trails)
        return self._desc_trails_cache

    def apply(self, func: ApplyFunc, grammar = _GRAMMAR_PLACEHOLDER) -> Optional[bool]:
        """
        Applies function "func(parser)" recursively to this parser and all
        descendant parsers as long as "func()" returns "None" or "False".
        Traversal is pre-order. Stops the further application of "func" and
        returns "True" once "func" has returned "True".


        If "func" has been applied to all descendant parsers without issuing
        a stop signal by returning "True", "False" is returned.

        if apply is called for the first time on the parser, the parser will be
        conntected to "grammar"
        This use of the return value allows to use the "apply"-method both
        to issue tests on all descendant parsers (including self) which may be
        decided already after some parsers have been visited without any need
        to visit further parsers. At the same time "apply" can be used to simply
        apply a procedure to all descendant parsers (including self) without
        worrying about forgetting the return value of procedure, because a
        return value of "None" means "carry on".
        """
        for parser in self.descendants(grammar):
            if func(parser):
                return True
        return False

    def apply_to_trail(self, func: ApplyToTrailFunc) -> Optional[bool]:
        """
        Same as :py:meth:`Parser.apply`, only that the applied function
        receives the complete "trail", i.e. list of parsers that lead
        from self to the visited parser as argument.
        """
        for pctx in self.descendant_trails():
            if func(pctx):
                return True
        return False

    def static_error(self, msg: str, code: ErrorCode) -> 'AnalysisError':
        from DHParser.parse_grammar import AnalysisError
        return AnalysisError(self.symbol, self, Error(msg, 0, code))

    def static_analysis(self) -> List['AnalysisError']:
        """Analyses the parser for logical errors after the grammar has been
        instantiated."""
        return []


# Auxiliary functions for Parser class ###


def assign(name: str, parser: Parser) -> Parser:
    r"""Assigns a name to the given parser. This does the same
    as the :py:meth:`Parser.name`-method. Example::

        >>> from DHParser.parse_combinators import RegExp
        >>> doc = assign("doc", RegExp(r"\w+"))
        >>> print(doc.pname)
        doc
    """
    return parser.name(name)


def copy_parser_base_attrs(src: Parser, duplicate: Parser, memo: Dict[int, Any]):
    """Duplicates all attributes of the Parser-class from "src" to "duplicate".
    Also, if the parser has directly been assigned to a field in the grammar-class, it
    will be added early to the grammar! This is a hack, tn order to make
    LateBindingUnary.resolve_parser_name() work!"""
    grammar = memo[0]
    duplicate.grammar = grammar
    name = memo.get(-id(src), '')
    if name:  setattr(grammar, name, duplicate)
    duplicate.pname = src.pname
    duplicate.disposable = src.disposable
    duplicate.drop_content = src.drop_content
    duplicate.node_name = src.node_name


def Drop(parser: Parser) -> Parser:
    """Returns the parser with the "parser.drop_content" property set to "True".
    Parser must be anonymous and disposable. Use "DropFrom" instead
    when this requirement ist not met."""
    assert parser.disposable, "Parser must be anonymous to be allowed to drop its content."
    from DHParser.parse_combinators import ForwardBase
    if isinstance(parser, ForwardBase):
        cast(ForwardBase, parser).parser.drop_content = True
    parser.drop_content = True
    return parser


def DropFrom(parser: Parser) -> Parser:
    """Encapsulates the parser in an anonymous Synonym-Parser and sets the
    drop_content-flag of the latter. This leaves the drop-flag of the
    parser itself untouched. This is needed, if you want to drop the
    result from a named-parser in one particular context where it is
    referred to, only."""
    from DHParser.parse_combinators import Synonym
    wrapper = Synonym(parser)
    wrapper.drop_content = True
    wrapper.disposable = True
    return wrapper


PARSER_PLACEHOLDER = None  # type: Optional[Parser]
# Don't access PARSER_PLACEHOLDER directly, use get_parser_placeholder() instead


def get_parser_placeholder() -> Parser:
    global PARSER_PLACEHOLDER
    if PARSER_PLACEHOLDER is None:
        PARSER_PLACEHOLDER = Parser.__new__(Parser)  # Parser()
        PARSER_PLACEHOLDER.pname = ''
        PARSER_PLACEHOLDER.ptype = ':Parser'
        PARSER_PLACEHOLDER.disposable = False
        PARSER_PLACEHOLDER.drop_content = False
        PARSER_PLACEHOLDER.node_name = ':PLACEHOLDER__'
        PARSER_PLACEHOLDER.sub_parsers = frozenset()
        if not cython.compiled:
            PARSER_PLACEHOLDER.__deepcopy__ = NOCALL
            PARSER_PLACEHOLDER.apply = NOCALL
    return cast(Parser, PARSER_PLACEHOLDER)


def is_parser_placeholder(parser: Optional[Parser]) -> bool:
    """Returns True, if "parser" is "None" or merely a placeholder for a parser."""
    return parser is None or parser.ptype == ":Parser"


# functions for analysing the parser tree/graph ###


def has_non_autocaptured_symbols(ptrail: ParserTrail) -> Optional[bool]:
    """Returns True, if the parser-path contains a Capture-Parser that is not
    shielded by a Retrieve-Parser. This is the case for captured symbols
    that are not "auto-captured" by a Retrieve-Parser.
    """
    from DHParser.parse_combinators import UnaryParser, Retrieve
    for parser in ptrail:
        if parser.ptype == ":Retrieve":
            break
        elif parser.ptype == ":Capture":
            p = cast(UnaryParser, parser).parser
            while p.ptype in (":Synonym", ":Forward"):
                p = cast(UnaryParser, p).parser
            if not isinstance(p, Retrieve):
                return True
    return None



#######################################################################
#
# Special parser (base) classes
#
#######################################################################


class LeafParser(Parser):
    """Base-Class for leaf-parsers. A leaf-parser is a parser that does
    not call any other parsers."""

    def __call__(self: Parser, location: cython.int) -> ParsingResult:
        """Applies the parser to the given text. This is a wrapper method that adds
        the business intelligence that is common to all parsers. The actual parsing is
        done in the overridden method "_parse()". This wrapper-method can be thought of
        as a "parser guard", because it guards the parsing process.
        """
        grammar = self._grammar

        try:
            # rollback variable changing operation if the parser backtracks to a position
            # before or at the location where the variable-changing operation occurred
            if location <= grammar.last_rb__loc__:
                grammar.rollback_to__(location)

            # if the location has already been visited by, return the saved result
            visited = self.visited  # using local variable for better performance
            if location in visited:
                # Sorry, no history recording in case of memoized results!
                return visited[location]

            # now, the actual parser call!
            try:
                node, next_location = self._parse_proxy(location)
            except ParserError as pe:
                # catching up with parsing after an error occurred
                node, next_location = self._handle_parsing_error(pe, location)

            if node is None:
                if location > grammar.ff_pos__:
                    grammar.ff_pos__ = location
                    grammar.ff_parser__ = self
            elif node is not EMPTY_NODE:
                node._pos = location

            visited[location] = (node, next_location)
        except RecursionError:
            node, next_location = self._handle_recursion_error(location)
        return node, next_location


class NoMemoizationParser(LeafParser):
    """Base class for parsers that should not memoize"""

    def __init__(self) -> None:
        super().__init__()
        global BLACKHOLE_SINGLETON
        self.visited: MemoizationDict = BLACKHOLE_SINGLETON

    def reset(self):
        # no need to initialize self.visited, it's always the BLACKHOLE_SINGLETON
        pass

    @cython.locals(next_location=cython.int, gap=cython.int, i=cython.int, save_suspend_memoization=cython.bint)
    def __call__(self: Parser, location: cython.int) -> ParsingResult:
        """Like Parser.__call__, but without memoization"""
        grammar = self._grammar

        try:
            # rollback variable changing operation if parser backtracks to a position
            # before or at the location where the variable changing operation occurred
            if location <= grammar.last_rb__loc__:
                grammar.rollback_to__(location)

            # now, the actual parser call!
            try:
                node, next_location = self._parse_proxy(location)
            except ParserError as pe:
                # catching up with parsing after an error occurred
                node, next_location = self._handle_parsing_error(pe, location)

            if node is None:
                if location > grammar.ff_pos__:
                    grammar.ff_pos__ = location
                    grammar.ff_parser__ = self
            elif node is not EMPTY_NODE:
                node._pos = location

        except RecursionError:
            node, next_location = self._handle_recursion_error(location)

        return node, next_location


class Unparameterized(NoMemoizationParser):
    """Unparameterized parsers do not receive any parameters on instantiation.
    As a consequence, different instances of the same unparameterized
    parser are always functionally equivalent."""
    pass


class Always(Unparameterized):
    """A parser that always matches, but does not capture anything."""
    def _parse(self, location: cython.int) -> ParsingResult:
        if self.node_name[0:1] == ':':
            return EMPTY_NODE, location
        else:
            return Node(self.node_name, ''), location

    def is_optional(self) -> Optional[bool]:
        return True  # parser can never fail, like an optional parser


class Never(Unparameterized):
    """A parser that never matches."""
    def _parse(self, location: cython.int) -> ParsingResult:
        return None, location


class AnyChar(Unparameterized):
    """A parser that returns the next Unicode character of the document
    whatever that is. The parser fails only at the very end of the text."""
    @cython.locals(location_=cython.int, L=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        text = self._grammar.document__._text
        L = len(text)
        if location < L:
            location_ = location + 1
            return Node(self.node_name, text[location:location_], True), location_
        else:
            return None, location