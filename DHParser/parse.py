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
"""


from collections import defaultdict
import copy
from typing import Callable, cast, List, Tuple, Set, Iterator, Dict, \
    DefaultDict, Union, Optional, Any

from DHParser.configuration import get_config_value
from DHParser.error import Error, linebreaks, line_col
from DHParser.log import is_logging, HistoryRecord
from DHParser.preprocess import BEGIN_TOKEN, END_TOKEN, RX_TOKEN_NAME
from DHParser.stringview import StringView, EMPTY_STRING_VIEW
from DHParser.syntaxtree import Node, FrozenNode, RootNode, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, ZOMBIE_TAG, ResultType
from DHParser.toolkit import sane_parser_name, escape_control_characters, re, cython, \
    RX_NEVER_MATCH


__all__ = ('Parser',
           'UnknownParserError',
           'GrammarErrorType',
           'GrammarError',
           'Grammar',
           'EMPTY_NODE',
           'PreprocessorToken',
           'Token',
           'DropToken',
           'RegExp',
           'RE',
           'TKN',
           'Whitespace',
           'DropWhitespace',
           'mixin_comment',
           'MetaParser',
           'UnaryParser',
           'NaryParser',
           'Synonym',
           'Option',
           'ZeroOrMore',
           'OneOrMore',
           'Series',
           'Alternative',
           'AllOf',
           'SomeOf',
           'Unordered',
           'Required',
           'Lookahead',
           'NegativeLookahead',
           'Lookbehind',
           'NegativeLookbehind',
           'last_value',
           'counterpart',
           'accumulate',
           'Capture',
           'Retrieve',
           'Pop',
           'Forward')


########################################################################
#
# Parser base class
#
########################################################################


EMPTY_NODE = FrozenNode(':EMPTY__', '')


class ParserError(Exception):
    """
    A `ParserError` is thrown for those parser errors that allow the
    controlled re-entrance of the parsing process after the error occurred.
    If a reentry-rule has been configured for the parser where the error
    occurred, the parser guard can resume the parsing process.

    Currently, the only case when a `ParserError` is thrown (and not some
    different kind of error like `UnknownParserError`, is when a `Series`-
    detects a missing mandatory element.
    """
    def __init__(self, node: Node, rest: StringView, error: Optional[Error], first_throw: bool):
        self.node = node   # type: Node
        self.rest = rest   # type: StringView
        self.error = error # type: Optional[Error]
        self.first_throw = first_throw  # type: bool

    def __str__(self):
        return "%i: %s    %s" % (self.node.pos, str(self.rest[:25]), repr(self.node))


ResumeList = List[Union[str, Any]]  # list of strings or regular expressiones


def reentry_point(rest: StringView, rules: ResumeList, comment_regex) -> int:
    """
    Finds the point where parsing should resume after a ParserError has been caught.
    The algorithm makes sure that this reentry-point does not lie inside a comment.
    Args:
        rest:  The rest of the parsed text or, in other words, the point where
                a ParserError was thrown.
        rules: A list of strings or regular expressions. The rest of the text is
                searched for each of these. The closest match is the point where
                parsing will be resumed.
        comment_regex: A regular expression object that matches comments.
    Returns:
        The integer index of the closest reentry point or -1 if no reentry-point
        was found.
    """
    upper_limit = len(rest) + 1
    closest_match = upper_limit
    comments = None  # typ: Optional[Iterator]

    def next_comment() -> Tuple[int, int]:
        nonlocal rest, comments
        if comments:
            try:
                m = next(comments)
                a, b = m.span()
                return rest.index(a), rest.index(b)
            except StopIteration:
                comments = None
        return -1, -2

    def str_search(s, start: int = 0) -> Tuple[int, int]:
        nonlocal rest
        return rest.find(s, start), len(rule)

    def rx_search(rx, start: int = 0) -> Tuple[int, int]:
        nonlocal rest
        m = rest.search(rx, start)
        if m:
            start, end = m.span()
            return rest.index(start), end - start
        return -1, 0

    def entry_point(search_func, search_rule) -> int:
        a, b = next_comment()
        k, length = search_func(search_rule)
        while a < b <= k:
            a, b = next_comment()
        while a <= k < b:
            k, length = search_func(search_rule, k + length)
            while a < b <= k:
                a, b = next_comment()
        return k if k >= 0 else upper_limit

    # find closest match
    for rule in rules:
        comments = rest.finditer(comment_regex)
        if isinstance(rule, str):
            pos = entry_point(str_search, rule)
        else:  # rule is a compiled regular expression
            pos = entry_point(rx_search, rule)
        closest_match = min(pos, closest_match)

    # in case no rule matched return -1
    if closest_match == upper_limit:
        closest_match = -1
    return closest_match


ApplyFunc = Callable[['Parser'], None]
FlagFunc = Callable[[ApplyFunc, Set[ApplyFunc]], bool]


class Parser:
    """
    (Abstract) Base class for Parser combinator parsers. Any parser
    object that is actually used for parsing (i.e. no mock parsers)
    should should be derived from this class.

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

    2. *Anonymous parsers* where the name-field just contains the empty
       string. AST-transformation of Anonymous parsers can be hooked
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
        pname:    The parser name or the empty string in case the parser
                remains anonymous.
        tag_name:  The tag_name for the nodes that are created by
                the parser. If the parser is named, this is the same as
                `pname`, otherwise it is the name of the parser's type.
        visited:  Mapping of places this parser has already been to
                during the current parsing process onto the results the
                parser returned at the respective place. This dictionary
                is used to implement memoizing.

        recursion_counter:  Mapping of places to how often the parser
                has already been called recursively at this place. This
                is needed to implement left recursion. The number of
                calls becomes irrelevant once a resault has been memoized.

        cycle_detection:  The apply()-method uses this variable to make
                sure that one and the same function will not be applied
                (recursively) a second time, if it has already been
                applied to this parser.

        _grammar:  A reference to the Grammar object to which the parser
                is attached.
    """

    def __init__(self) -> None:
        # assert isinstance(name, str), str(name)
        self.pname = ''               # type: str
        self.tag_name = self.ptype    # type: str
        self.cycle_detection = set()  # type: Set[ApplyFunc]
        try:
            self._grammar = GRAMMAR_PLACEHOLDER  # type: Grammar
        except NameError:
            pass
        self.reset()

    def __deepcopy__(self, memo):
        """        Deepcopy method of the parser. Upon instantiation of a Grammar-
        object, parsers will be deep-copied to the Grammar object. If a
        derived parser-class changes the signature of the constructor,
        `__deepcopy__`-method must be replaced (i.e. overridden without
        calling the same method from the superclass) by the derived class.
        """
        duplicate = self.__class__()
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    def __repr__(self):
        return self.pname + self.ptype

    def __str__(self):
        return self.pname + (' = ' if self.pname else '') + repr(self)

    @property
    def ptype(self) -> str:
        """Returns a type name for the parser. By default this is the name of
        the parser class with an added leading colon ':'. """
        return ':' + self.__class__.__name__

    @property
    def repr(self) -> str:
        """Returns the parser's name if it has a name and self.__repr___() otherwise."""
        return self.pname if self.pname else self.__repr__()

    def reset(self):
        """Initializes or resets any parser variables. If overwritten,
        the `reset()`-method of the parent class must be called from the
        `reset()`-method of the derived class."""
        self.visited = dict()  # type: Dict[int, Tuple[Optional[Node], StringView]]
        self.recursion_counter = defaultdict(int)  # type: DefaultDict[int, int]

    @cython.locals(location=cython.int, gap=cython.int, i=cython.int)
    def __call__(self: 'Parser', text: StringView) -> Tuple[Optional[Node], StringView]:
        """Applies the parser to the given text. This is a wrapper method that adds
        the business intelligence that is common to all parsers. The actual parsing is
        done in the overridden method `_parse()`. This wrapper-method can be thought of
        as a "parser guard", because it guards the parsing process.
        """
        def get_error_node_id(error_node: Node, root_node: RootNode) -> int:
            if error_node:
                error_node_id = id(error_node)
                while error_node_id not in grammar.tree__.error_nodes and error_node.children:
                    error_node = error_node.result[-1]
                    error_node_id = id(error_node)
            else:
                error_node_id = 0

        grammar = self._grammar
        location = grammar.document_length__ - len(text)

        try:
            # rollback variable changing operation if parser backtracks
            # to a position before the variable changing operation occurred
            if grammar.last_rb__loc__ >= location:
                grammar.rollback_to__(location)

            # if location has already been visited by the current parser, return saved result
            visited = self.visited  # using local variable for better performance
            if location in visited:
                # no history recording in case of memoized results
                return visited[location]

            # break left recursion at the maximum allowed depth
            left_recursion_depth__ = grammar.left_recursion_depth__
            if left_recursion_depth__:
                if self.recursion_counter[location] > left_recursion_depth__:
                    grammar.recursion_locations__.add(location)
                    return None, text
                self.recursion_counter[location] += 1

            # write current step to call stack, if history tracking is configured
            history_tracking__ = grammar.history_tracking__
            if history_tracking__:
                grammar.call_stack__.append(
                    ((self.repr if self.tag_name in (':RegExp', ':Token', ':DropToken')
                      else self.tag_name), location))
                grammar.moving_forward__ = True
                error = None

            # finally, the actual parser call!
            try:
                node, rest = self._parse(text)
            except ParserError as pe:
                # catching up with parsing after an error occurred
                gap = len(text) - len(pe.rest)
                rules = grammar.resume_rules__.get(self.pname, [])
                rest = pe.rest[len(pe.node):]
                i = reentry_point(rest, rules, grammar.comment_rx__)
                if i >= 0 or self == grammar.start_parser__:
                    # apply reentry-rule or catch error at root-parser
                    if i < 0:
                        i = 1
                    nd = Node(ZOMBIE_TAG, rest[:i]).with_pos(location)
                    nd.attr['err'] = pe.error.message
                    rest = rest[i:]
                    assert pe.node.children or (not pe.node.result)
                    if pe.first_throw:
                        node = pe.node
                        node.result = node.children + (nd,)
                    else:
                        node = Node(self.tag_name,
                                    (Node(ZOMBIE_TAG, text[:gap]).with_pos(location), pe.node, nd))
                elif pe.first_throw:
                    raise ParserError(pe.node, pe.rest, pe.error, first_throw=False)
                elif grammar.tree__.errors[-1].code == Error.MANDATORY_CONTINUATION_AT_EOF:
                    node = pe.node
                else:
                    result = (Node(ZOMBIE_TAG, text[:gap]).with_pos(location), pe.node) if gap \
                        else pe.node  # type: ResultType
                    raise ParserError(Node(self.tag_name, result).with_pos(location),
                                      text, pe.error, first_throw=False)
                error = pe.error  # needed for history tracking


            if left_recursion_depth__:
                self.recursion_counter[location] -= 1
                # don't clear recursion_locations__ !!!

            if node is None:
                # retrieve an earlier match result (from left recursion) if it exists
                if location in grammar.recursion_locations__:
                    if location in visited:
                        node, rest = visited[location]
                        if location != grammar.last_recursion_location__:
                            grammar.tree__.add_error(
                                node, Error("Left recursion encountered. "
                                            "Refactor grammar to avoid slow parsing.",
                                            node.pos if node else location,
                                            Error.LEFT_RECURSION_WARNING))
                            error_id = id(node)
                            grammar.last_recursion_location__ = location
                    # don't overwrite any positive match (i.e. node not None) in the cache
                    # and don't add empty entries for parsers returning from left recursive calls!
                elif grammar.memoization__:
                    # otherwise also cache None-results
                    visited[location] = (None, rest)
            else:
                # assert node._pos < 0 or node == EMPTY_NODE
                # if node._pos != EMPTY_NODE:
                node._pos = location
                # assert node._pos >= 0 or node == EMPTY_NODE, \
                #     str("%i < %i" % (grammar.document_length__, location))
                if (grammar.last_rb__loc__ < location
                        and (grammar.memoization__ or location in grammar.recursion_locations__)):
                    # - variable manipulating parsers will not be entered into the cache,
                    #   because caching would interfere with changes of variable state
                    # - in case of left recursion, the first recursive step that
                    #   matches will store its result in the cache
                    # TODO: need a unit-test concerning interference of variable manipulation and left recursion algorithm?
                    visited[location] = (node, rest)

            # Mind that memoized parser calls will not appear in the history record!
            # Does this make sense? Or should it be changed?
            if history_tracking__:
                # don't track returning parsers except in case an error has occurred
                # remaining = len(rest)
                if grammar.moving_forward__:
                    record = HistoryRecord(grammar.call_stack__, node, text,
                                           grammar.line_col__(text))
                    grammar.history__.append(record)
                elif error:
                    # error_nid = id(node)  # type: int
                    # if error_nid in grammar.tree__.error_nodes:
                    record = HistoryRecord(grammar.call_stack__, node, text,
                                           grammar.line_col__(text),
                                           [error])
                    grammar.history__.append(record)
                grammar.moving_forward__ = False
                grammar.call_stack__.pop()

        except RecursionError:
            node = Node(ZOMBIE_TAG, str(text[:min(10, max(1, text.find("\n")))]) + " ...")
            node._pos = location
            grammar.tree__.new_error(node, "maximum recursion depth of parser reached; "
                                           "potentially due to too many errors!")
            rest = EMPTY_STRING_VIEW

        return node, rest

    def __add__(self, other: 'Parser') -> 'Series':
        """The + operator generates a series-parser that applies two
        parsers in sequence."""
        return Series(self, other)

    def __or__(self, other: 'Parser') -> 'Alternative':
        """The | operator generates an alternative parser that applies
        the first parser and, if that does not match, the second parser.
        """
        return Alternative(self, other)


    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        """Applies the parser to the given `text` and returns a node with
        the results or None as well as the text at the position right behind
        the matching string."""
        raise NotImplementedError

    @property
    def grammar(self) -> 'Grammar':
        try:
            if self._grammar != GRAMMAR_PLACEHOLDER:
                return self._grammar
            else:
                raise AssertionError('Grammar has not yet been set!')
        except (AttributeError, NameError):
            raise AttributeError('Parser placeholder does not have a grammar!')

    @grammar.setter
    def grammar(self, grammar: 'Grammar'):
        try:
            if self._grammar == GRAMMAR_PLACEHOLDER:
                self._grammar = grammar
                # self._grammar_assigned_notifier()
            elif self._grammar != grammar:
                  raise AssertionError("Parser has already been assigned"
                                       "to a different Grammar object!")
        except AttributeError:
            pass  # ignore setting of grammar attribute for placeholder parser
        except NameError:  # Cython: No access to GRAMMA_PLACEHOLDER, yet :-(
            self._grammar = grammar

    def _apply(self, func: ApplyFunc, flip: FlagFunc) -> bool:
        """
        Applies function `func(parser)` recursively to this parser and all
        descendant parsers, if any exist.

        In order to break cycles, function `flip` is called, which should
        return `True`, if this parser has already been visited. If not, it
        flips the cycle detection flag and returns `False`.

        This is a protected function and should not called from outside
        class Parser or any of its descendants. The entry point for external
        calls is the method `apply()` without underscore!
        """
        if flip(func, self.cycle_detection):
            return False
        else:
            func(self)
            return True

    def apply(self, func: ApplyFunc):
        """
        Applies function `func(parser)` recursively to this parser and all
        descendant parsers, if any exist. Traversal is pre-order.
        """
        def positive_flip(f: ApplyFunc, flagged: Set[Callable]) -> bool:
            """Returns True, if function `f` has already been applied to this
            parser and sets the flag accordingly. Interprets `f in flagged == True`
            as meaning that `f` has already been applied."""
            if f in flagged:
                return True
            else:
                flagged.add(f)
                return False

        def negative_flip(f: ApplyFunc, flagged: Set[Callable]) -> bool:
            """Returns True, if function `f` has already been applied to this
            parser and sets the flag accordingly. Interprets `f in flagged == False`
            as meaning that `f` has already been applied."""
            if f not in flagged:
                return True
            else:
                flagged.remove(f)
                return False

        if func in self.cycle_detection:
            self._apply(func, negative_flip)
        else:
            self._apply(func, positive_flip)


PARSER_PLACEHOLDER = Parser()


########################################################################
#
# Grammar class, central administration of all parser of a grammar
#
########################################################################

def mixin_comment(whitespace: str, comment: str) -> str:
    """
    Returns a regular expression that merges comment and whitespace
    regexps. Thus comments cann occur whereever whitespace is allowed
    and will be skipped just as implicit whitespace.

    Note, that because this works on the level of regular expressions,
    nesting comments is not possible. It also makes it much harder to
    use directives inside comments (which isn't recommended, anyway).
    """
    if comment:
        return '(?:' + whitespace + '(?:' + comment + whitespace + ')*)'
    return whitespace


class UnknownParserError(KeyError):
    """UnknownParserError is raised if a Grammar object is called with a
    parser that does not exist or if in the course of parsing a parser
    is referred to that does not exist."""


GrammarErrorType = Tuple[str, Parser, Error]      # TODO: replace with a named tuple?


class GrammarError(Exception):
    """GrammarError will be raised if static analysis reveals errors
    in the grammar.
    """
    def __init__(self, static_analysis_result: List[GrammarErrorType]):
        assert static_analysis_result  # must not be empty
        self.errors = static_analysis_result

    def __str__(self):
        if len(self.errors) == 1:
            return str(self.errors[0][2])
        return '\n' + '\n'.join(("%i. " % (i + 1) + str(err_tuple[2]))
                                for i, err_tuple in enumerate(self.errors))


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
    Any parser that is directly assigned to a class variable is a
    'named' parser and its field `parser.pname` contains the variable
    name after instantiation of the Grammar class. All other parsers,
    i.e. parsers that are defined within a `named` parser, remain
    "anonymous parsers" where `parser.pname` is the empty string.
    If one and the same parser is assigned to several class variables
    such as, for example, the parser `expression` in the example above,
    the first name sticks.

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

        resume_rules__: A mapping of parser names to a list of regular expressions or search
                strings that act as rules to find the the reentry point if a ParserError
                was thrown during the execution of the parser with the respective name.

        parser_initializiation__:  Before the parser class (!) has been initialized,
                 which happens upon the first time it is instantiated (see
                 :func:_assign_parser_names()` for an explanation), this class
                 field contains a value other than "done". A value of "done" indicates
                 that the class has already been initialized.

        static_analysis_pending__: True as long as no static analysis (see the method
                with the same name for more information) has been done to check
                parser tree for correctness. Static analysis
                is done at instantiation and the flag is then set to false, but it
                can also be carried out once the class has been generated
                (by DHParser.ebnf.EBNFCompiler) and then be set to false in the
                definition of the grammar class already.

        python__src__:  For the purpose of debugging and inspection, this field can
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

        history_tracking__:  A flag indicating that the parsing history shall
                be tracked

        _dirty_flag__:  A flag indicating that the Grammar has been called at
                least once so that the parsing-variables need to be reset
                when it is called again.

        document__:  the text that has most recently been parsed or that is
                currently being parsed.

        document_length__:  the length of the document.

        document_lbreaks__:  list of linebreaks within the document, starting
                with -1 and ending with EOF. This helps generating line
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
                location <= last_rb__loc__) then a rollback of all variable
                changing operations is necessary that occurred after the
                location to which the parser backtracks. This is done by
                calling method :func:`rollback_to__(location)`.

        call_stack__:  A stack of the tag names and locations of all parsers
                in the call chain to the currently processed parser during
                parsing. The call stack can be thought of as a breadcrumb trail.
                This is required for recording the parser history (for debugging)
                and, eventually, i.e. one day in the future, for tracing through
                the parsing process.

        history__:  A list of parser-call-stacks. A parser-call-stack is
                appended to the list each time a parser either matches, fails
                or if a parser-error occurs.

        moving_forward__: This flag indicates that the parsing process is currently
                moving forward . It is needed to reduce noise in history recording
                and should not be considered as having a valid value if history
                recording is turned off! (See :func:`Parser.__call__`)

        recursion_locations__:  Stores the locations where left recursion was
                detected. Needed to provide minimal memoization for the left
                recursion detection algorithm, but, strictly speaking, superfluous
                if full memoization is enabled. (See :func:`Parser.__call__()`)

        last_recursion_location__:  Last location where left recursion was
                detected. This is used to avoid reduplicating warning messages
                about left recursion.

        memoization__:  Turns full memoization on or off. Turning memoization off
                results in less memory usage and sometimes reduced parsing time.
                In some situations it may drastically increase parsing time, so
                it is safer to leave it on. (Default: on)

        flatten_tree__:  If True (default), anonymous nodes will be flattened
                during parsing already. This greatly reduces the concrete syntax
                tree and simplifies and speeds up abstract syntax tree generation.
                The initial value will be read from the config variable
                'flatten_tree_while_parsing' upon class instantiation.

        left_recursion_depth__: the maximum allowed depth for left-recursion.
                A depth of zero means that no left recursion handling will
                take place. See 'left_recursion_depth' in config.py.

        max_parser_dropouts__: Maximum allowed number of retries after errors
                where the parser would exit before the complete document has
                been parsed. See config.py
    """
    python_src__ = ''  # type: str
    root__ = PARSER_PLACEHOLDER  # type: Parser
    # root__ must be overwritten with the root-parser by grammar subclass
    parser_initialization__ = ["pending"]  # type: List[str]
    resume_rules__ = dict()  # type: Dict[str, ResumeList]
    # some default values
    # COMMENT__ = r''  # type: str  # r'#.*(?:\n|$)'
    # WSP_RE__ = mixin_comment(whitespace=r'[\t ]*', comment=COMMENT__)  # type: str
    static_analysis_pending__ = [True]  # type: List[bool]


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
        if cls.parser_initialization__[0] != "done":
            cdict = cls.__dict__
            for entry, parser in cdict.items():
                if isinstance(parser, Parser) and sane_parser_name(entry):
                    if isinstance(parser, Forward):
                        if not cast(Forward, parser).parser.pname:
                            cast(Forward, parser).parser.pname = entry
                    else:   # if not parser.pname:
                        parser.pname = entry
            cls.parser_initialization__[0] = "done"


    def __init__(self, root: Parser = None) -> None:
        self.all_parsers__ = set()             # type: Set[Parser]
        # add compiled regular expression for comments, if it does not already exist
        if not hasattr(self, 'comment_rx__'):
            self.comment_rx__ = re.compile(self.COMMENT__) \
                if hasattr(self, 'COMMENT__') and self.COMMENT__ else RX_NEVER_MATCH
        else:
            assert ((self.COMMENT__ and self.COMMENT__ == self.comment_rx__.pattern)
                     or (not self.COMMENT__ and self.comment_rx__ == RX_NEVER_MATCH))
        self.start_parser__ = None             # type: Optional[Parser]
        self._dirty_flag__ = False             # type: bool
        self.history_tracking__ = False        # type: bool
        self.memoization__ = True              # type: bool
        self.flatten_tree__ = get_config_value('flatten_tree_while_parsing')    # type: bool
        self.left_recursion_depth__ = get_config_value('left_recursion_depth')  # type: int
        self.max_parser_dropouts__ = get_config_value('max_parser_dropouts')    # type: int
        self._reset__()

        # prepare parsers in the class, first
        self._assign_parser_names__()

        # then deep-copy the parser tree from class to instance;
        # parsers not connected to the root object will be copied later
        # on demand (see Grammar.__getitem__()). Usually, the need to
        # do so only arises during testing.
        self.root_parser__ = copy.deepcopy(root) if root else copy.deepcopy(self.__class__.root__)
        self.root_parser__.apply(self._add_parser__)
        assert 'root_parser__' in self.__dict__
        assert self.root_parser__ == self.__dict__['root_parser__']

        if self.__class__.static_analysis_pending__ \
                and get_config_value('static_analysis') in {'early', 'late'}:
            try:
                result = self.static_analysis()
                if result:
                    raise GrammarError(result)
                self.__class__.static_analysis_pending__.pop()
            except (NameError, AttributeError):
                pass  # don't fail the initialization of PLACEHOLDER


    def __getitem__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            parser_template = getattr(self.__class__, key, None)
            if parser_template:
                # add parser to grammar object on the fly...
                parser = copy.deepcopy(parser_template)
                parser.apply(self._add_parser__)
                assert self[key] == parser
                return self[key]
            raise UnknownParserError('Unknown parser "%s" !' % key)


    def __contains__(self, key):
        return key in self.__dict__ or hasattr(self, key)


    def _reset__(self):
        self.tree__ = RootNode()              # type: RootNode
        self.document__ = EMPTY_STRING_VIEW   # type: StringView
        self._reversed__ = EMPTY_STRING_VIEW  # type: StringView
        self.document_length__ = 0            # type: int
        self.document_lbreaks__ = []          # type: List[int]
        # variables stored and recalled by Capture and Retrieve parsers
        self.variables__ = defaultdict(lambda: [])  # type: DefaultDict[str, List[str]]
        self.rollback__ = []                  # type: List[Tuple[int, Callable]]
        self.last_rb__loc__ = -1              # type: int
        # support for call stack tracing
        self.call_stack__ = []                # type: List[Tuple[str, int]]  # tag_name, location
        # snapshots of call stacks
        self.history__ = []                   # type: List[HistoryRecord]
        # also needed for call stack tracing
        self.moving_forward__ = False         # type: bool
        self.recursion_locations__ = set()    # type: Set[int]
        self.last_recursion_location__ = -1   # type: int


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


    def _add_parser__(self, parser: Parser) -> None:
        """
        Adds the particular copy of the parser object to this
        particular instance of Grammar.
        """
        if parser.pname:
            # prevent overwriting instance variables or parsers of a different class
            assert parser.pname not in self.__dict__ or \
                   isinstance(self.__dict__[parser.pname], parser.__class__), \
                ('Cannot add parser "%s" because a field with the same name '
                 'already exists in grammar object: %s!'
                 % (parser.pname, str(self.__dict__[parser.pname])))
            setattr(self, parser.pname, parser)
        parser.tag_name = parser.pname or parser.ptype
        self.all_parsers__.add(parser)
        parser.grammar = self


    def __call__(self,
                 document: str,
                 start_parser: Union[str, Parser] = "root_parser__",
                 track_history: bool = False) -> RootNode:
        """
        Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
            start_parser (str or Parser): The name of the parser with which
                to start. This is useful for testing particular parsers
                (i.e. particular parts of the EBNF-Grammar.)
            track_history (bool): If true, the parsing history will be
                recorded in self.history__. If logging is turned on (i.e.
                DHParser.log.is_logging() returns true), the parsing history
                will always be recorded, even if `False` is passed to
                the `track_history` parameter.
        Returns:
            Node: The root node to the parse tree.
        """

        def tail_pos(predecessors: Union[List[Node], Tuple[Node, ...], None]) -> int:
            """Adds the position after the last node in the list of
            predecessors to the node."""
            return predecessors[-1].pos + len(predecessors[-1]) if predecessors else 0

        def lookahead_failure_only(parser):
            """EXPERIMENTAL!

            Checks if failure to match document was only due to a succeeding
            lookahead parser, which is a common design pattern that can break test
            cases. (Testing for this case allows to modify the error message, so
            that the testing framework knows that the failure is only a
            test-case-artifact and no real failure.
            (See test/test_testing.TestLookahead !)
            """
            def is_lookahead(tag_name: str) -> bool:
                return (tag_name in self and isinstance(self[tag_name], Lookahead)
                        or tag_name[0] == ':' and issubclass(eval(tag_name[1:]), Lookahead))
            # for h in reversed(self.history__[:-1]):
            #     for tn, pos in h.call_stack:
            #         if is_lookahead(tn) and h.status == HistoryRecord.MATCH:
            #             print(h.call_stack, pos, h.line_col)
            last_record = self.history__[-2] if len(self.history__) > 1 else None  # type: Optional[HistoryRecord]
            return last_record and parser != self.root_parser__ \
                    and any(h.status == HistoryRecord.MATCH
                            and any(is_lookahead(tn) and location >= len(self.document__)
                                    for tn, location in h.call_stack)
                            for h in self.history__[:-1])

        # assert isinstance(document, str), type(document)
        if self._dirty_flag__:
            self._reset__()
            for parser in self.all_parsers__:
                parser.reset()
        else:
            self._dirty_flag__ = True
        self.history_tracking__ = track_history or is_logging()
        # safe tracking state, because history_tracking__ might be set to false, later,
        # but original tracking state is needed for additional error information.
        track_history = self.history_tracking__
        self.document__ = StringView(document)
        self.document_length__ = len(self.document__)
        self.document_lbreaks__ = linebreaks(document) if self.history_tracking__ else []
        self.last_rb__loc__ = -1  # rollback location
        parser = self[start_parser] if isinstance(start_parser, str) else start_parser
        self.start_parser__ = parser.parser if isinstance(parser, Forward) else parser
        assert parser.grammar == self, "Cannot run parsers from a different grammar object!" \
                                       " %s vs. %s" % (str(self), str(parser.grammar))
        result = None  # type: Optional[Node]
        stitches = []  # type: List[Node]
        rest = self.document__
        if not rest:
            result, _ = parser(rest)
            if result is None:
                result = Node(ZOMBIE_TAG, '').with_pos(0)
                if lookahead_failure_only(parser):
                    self.tree__.new_error(
                        result, 'Parser "%s" only did not match empty document '
                                'because of lookahead' % str(parser),
                        Error.PARSER_LOOKAHEAD_FAILURE_ONLY)
                else:
                    self.tree__.new_error(
                        result, 'Parser "%s" did not match empty document.' % str(parser),
                        Error.PARSER_DID_NOT_MATCH)

        # copy to local variable, so break condition can be triggered manually
        max_parser_dropouts = self.max_parser_dropouts__
        while rest and len(stitches) < max_parser_dropouts:
            result, rest = parser(rest)
            if rest:
                fwd = rest.find("\n") + 1 or len(rest)
                skip, rest = rest[:fwd], rest[fwd:]
                if result is None:
                    err_info = '' if not track_history else \
                               '\n    Most advanced: %s\n    Last match:    %s;' % \
                               (str(HistoryRecord.most_advanced_match(self.history__)),
                                str(HistoryRecord.last_match(self.history__)))
                    # Check if a Lookahead-Parser did match. Needed for testing, because
                    # in a test case this is not necessarily an error.
                    if lookahead_failure_only(parser):
                        error_msg = 'Parser "%s" only did not match because of lookahead! ' \
                                    % str(parser) + err_info
                        error_code = Error.PARSER_LOOKAHEAD_FAILURE_ONLY
                    else:
                        error_msg = 'Parser "%s" did not match!' % str(parser) + err_info
                        error_code = Error.PARSER_DID_NOT_MATCH
                else:
                    stitches.append(result)
                    for h in reversed(self.history__):
                        if h.node and h.node.tag_name != EMPTY_NODE.tag_name:
                            break
                    else:
                        h = HistoryRecord([], None, StringView(''), (0, 0))
                    if h.status == h.MATCH and (h.node.pos + len(h.node) == len(self.document__)):
                        # TODO: this case still needs unit-tests and support in testing.py
                        error_msg = "Parser stopped before end, but matched with lookahead."
                        error_code = Error.PARSER_LOOKAHEAD_MATCH_ONLY
                        max_parser_dropouts = -1  # no further retries!
                    else:
                        error_msg = "Parser stopped before end" \
                            + (("! trying to recover"
                                + (" but stopping history recording at this point."
                                   if self.history_tracking__ else "..."))
                                if len(stitches) < self.max_parser_dropouts__
                                else " too often! Terminating parser.")
                        error_code = Error.PARSER_STOPPED_BEFORE_END
                stitches.append(Node(ZOMBIE_TAG, skip).with_pos(tail_pos(stitches)))
                self.tree__.new_error(stitches[-1], error_msg, error_code)
                if self.history_tracking__:
                    # # some parsers may have matched and left history records with nodes != None.
                    # # Because these are not connected to the stitched root node, their pos-
                    # # properties will not be initialized by setting the root node's pos property
                    # # to zero. Therefore, their pos properties need to be initialized here
                    # for record in self.history__:
                    #     if record.node and record.node._pos < 0:
                    #         record.node.with_pos(0)
                    # print(self.call_stack__)
                    # record = HistoryRecord(self.call_stack__.copy(), stitches[-1], rest,
                    #                        self.line_col__(rest))
                    # self.history__.append(record)
                    # stop history tracking when parser returned too early
                    self.history_tracking__ = False
        if stitches:
            if rest:
                stitches.append(Node(ZOMBIE_TAG, rest))
            result = Node(ZOMBIE_TAG, tuple(stitches)).with_pos(0)
        if any(self.variables__.values()):
            error_msg = "Capture-retrieve-stack not empty after end of parsing: " \
                + str(self.variables__)
            error_code = Error.CAPTURE_STACK_NOT_EMPTY
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
        if result:
            self.tree__.swallow(result)
        self.start_parser__ = None
        return self.tree__


    def push_rollback__(self, location, func):
        """
        Adds a rollback function that either removes or re-adds
        values on the variable stack (`self.variables`) that have been
        added (or removed) by Capture or Pop Parsers, the results of
        which have been dismissed.
        """
        self.rollback__.append((location, func))
        self.last_rb__loc__ = location


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
        self.last_rb__loc__ == self.rollback__[-1][0] if self.rollback__ \
            else (len(self.document__) + 1)


    def line_col__(self, text):
        """
        Returns the line and column where text is located in the document.
        Does not check, whether text is actually a substring of the currently
        parsed document.
        """
        return line_col(self.document_lbreaks__, self.document_length__ - len(text))


    def static_analysis(self) -> List[GrammarErrorType]:
        """
        EXPERIMENTAL 

        Checks the parser tree statically for possible errors. At the moment,
        no checks are implemented

        :return: a list of error-tuples consisting of the narrowest containing
            named parser (i.e. the symbol on which the failure occurred),
            the actual parser that failed and an error object.
        """
        error_list = []  # type: List[GrammarErrorType]

        def visit_parser(parser: Parser) -> None:
            nonlocal error_list

        # self.root_parser__.apply(visit_parser)  # disabled, because no use case as of now
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


GRAMMAR_PLACEHOLDER = Grammar()


########################################################################
#
# _Token and Regular Expression parser classes (i.e. leaf classes)
#
########################################################################


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

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.pname)
        # duplicate.pname = self.pname  # will be written by the constructor, anyway
        duplicate.tag_name = self.tag_name
        return duplicate

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        if text[0:1] == BEGIN_TOKEN:
            end = text.find(END_TOKEN, 1)
            if end < 0:
                node = Node(self.tag_name, '')
                self.grammar.tree__.new_error(
                    node,
                    'END_TOKEN delimiter missing from preprocessor token. '
                    '(Most likely due to a preprocessor bug!)')  # type: Node
                return node, text[1:]
            elif end == 0:
                node = Node(self.tag_name, '')
                self.grammar.tree__.new_error(
                    node,
                    'Preprocessor-token cannot have zero length. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[2:]
            elif text.find(BEGIN_TOKEN, 1, end) >= 0:
                node = Node(self.tag_name, text[len(self.pname) + 1:end])
                self.grammar.tree__.new_error(
                    node,
                    'Preprocessor-tokens must not be nested or contain '
                    'BEGIN_TOKEN delimiter as part of their argument. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[end:]
            if text[1:len(self.pname) + 1] == self.pname:
                return Node(self.tag_name, text[len(self.pname) + 2:end]), text[end + 1:]
        return None, text


class Token(Parser):
    """
    Parses plain text strings. (Could be done by RegExp as well, but is faster.)

    Example::

        >>> while_token = Token("while")
        >>> Grammar(while_token)("while").content
        'while'
    """
    assert TOKEN_PTYPE == ":Token"

    def __init__(self, text: str) -> None:
        super(Token, self).__init__()
        self.text = text
        self.len = len(text)

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.text)
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        if text.startswith(self.text):
            if self.text or self.pname:
                return Node(self.tag_name, self.text, True), text[self.len:]
            return EMPTY_NODE, text[0:]
        return None, text

    def __repr__(self):
        return ("'%s'" if self.text.find("'") <= 0 else '"%s"') % self.text


class DropToken(Token):
    """
    Parses play text string, but returns EMPTY_NODE rather than the parsed
    string on a match. Violates the invariant: str(parse(text)) == text !
    """
    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        assert not self.pname, "DropToken must not be used for named parsers!"
        if text.startswith(self.text):
            return EMPTY_NODE, text[self.len:]
            # return Node(self.tag_name, self.text, True), text[self.len:]
        return None, text


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
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        match = text.match(self.regexp)
        if match:
            capture = match.group(0)
            if capture or self.pname:
                end = text.index(match.end())
                return Node(self.tag_name, capture, True), text[end:]
            assert text.index(match.end()) == 0
            return EMPTY_NODE, text[0:]
        return None, text

    def __repr__(self):
        return escape_control_characters('/%s/' % self.regexp.pattern)


def withWS(parser_factory, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), parser_factory(), Whitespace(wsR))'.
    """
    if wsL and isinstance(wsL, str):
        wsL = Whitespace(wsL)
    if wsR and isinstance(wsR, str):
        wsR = Whitespace(wsR)
    if wsL and wsR:
        return Series(wsL, parser_factory(), wsR)
    elif wsL:
        return Series(wsL, parser_factory())
    elif wsR:
        return Series(parser_factory(), wsR)
    else:
        return parser_factory()


def RE(regexp, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), RegExp(regexp), Whitespace(wsR))'"""
    return withWS(lambda: RegExp(regexp), wsL, wsR)


def TKN(token, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), Token(token), Whitespace(wsR))'"""
    return withWS(lambda: Token(token), wsL, wsR)


def DTKN(token, wsL='', wsR=r'\s*'):
    """Syntactic Sugar for 'Series(Whitespace(wsL), DropToken(token), Whitespace(wsR))'"""
    return withWS(lambda: DropToken(token), wsL, wsR)


class Whitespace(RegExp):
    """An variant of RegExp that signifies through its class name that it
    is a RegExp-parser for whitespace."""
    assert WHITESPACE_PTYPE == ":Whitespace"

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        match = text.match(self.regexp)
        if match:
            capture = match.group(0)
            if capture or self.pname:
                end = text.index(match.end())
                return Node(self.tag_name, capture, True), text[end:]
            else:
                # avoid creation of a node object for empty nodes
                return EMPTY_NODE, text
        return None, text

    def __repr__(self):
        return '~'


class DropWhitespace(Whitespace):
    """
    Parses whitespace but never returns it. Instead EMPTY_NODE is returned
    on a match. Violates the invariant: str(parse(text)) == text !
    """

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        assert not self.pname, "DropWhitespace must not be used for named parsers!"
        match = text.match(self.regexp)
        if match:
            # capture = match.group(0)
            end = text.index(match.end())
            return EMPTY_NODE, text[end:]
        return None, text


########################################################################
#
# Meta parser classes, i.e. parsers that contain other parsers
# to which they delegate parsing
#
########################################################################


class MetaParser(Parser):
    """Class Meta-Parser contains functions for the optimization of
    retrun values of parsers that call other parsers (i.e descendants
    of classes UnaryParser and NaryParser).

    The optimization consists in flattening the tree by eliminating
    anonymous nodes. This is the same as what the function
    DHParser.transform.flatten() does, only at an earlier stage.
    The reasoning is that the earlier the tree is reduced, the less work
    reamins to do at all the later processing stages.
    """

    def _return_value(self, node: Optional[Node]) -> Node:
        """
        Generates a return node if a single node has been returned from
        any descendant parsers. Anonymous empty nodes will be dropped.
        If `self` is an unnamed parser, a non-empty descendant node
        will be passed through. If the descendant node is anonymous,
        it will be dropped and only its result will be kept.
        In all other cases or if the optimization is turned off by
        setting `grammar.flatten_tree__` to False, a new node will be
        generated and the descendant node will be its single child.
        """
        assert node is None or isinstance(node, Node)
        if self._grammar.flatten_tree__:
            if node:
                if self.pname:
                    if node.tag_name[0] == ':':  # faster than node.is_anonymous()
                        return Node(self.tag_name, node._result)
                    return Node(self.tag_name, node)
                return node
            elif self.pname:
                return Node(self.tag_name, ())
            return EMPTY_NODE  # avoid creation of a node object for anonymous empty nodes
        return Node(self.tag_name, node or ())  # unoptimized code

    @cython.locals(N=cython.int)
    def _return_values(self, results: Tuple[Node, ...]) -> Node:
        """
        Generates a return node from a tuple of returned nodes from
        descendant parsers. Anonymous empty nodes will be removed from
        the tuple. Anonymous child nodes will be flattened if
        `grammar.flatten_tree__` is True.
        """
        assert isinstance(results, tuple)
        N = len(results)
        if N > 1:
            if self._grammar.flatten_tree__:
                nr = []  # type: List[Node]
                # flatten parse tree
                for child in results:
                    if child.children and child.tag_name[0] == ':':  # faster than c.is_anonymous():
                        nr.extend(child.children)
                    elif child._result or child.tag_name[0] != ':':
                        nr.append(child)
                return Node(self.tag_name, tuple(nr))
            return Node(self.tag_name, results)  # unoptimized code
        elif N == 1:
            return self._return_value(results[0])
        elif self._grammar.flatten_tree__:
            if self.pname:
                return Node(self.tag_name, ())
            return EMPTY_NODE  # avoid creation of a node object for anonymous empty nodes
        return Node(self.tag_name, results)  # unoptimized code


class UnaryParser(MetaParser):
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
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    def _apply(self, func: ApplyFunc, flip: FlagFunc) -> bool:
        if super(UnaryParser, self)._apply(func, flip):
            self.parser._apply(func, flip)
            return True
        return False


class NaryParser(MetaParser):
    """
    Base class of all Nnary parsers, i.e. parser that
    contains one or more other parsers, like the alternative
    parser for example.

    The NnaryOperator base class supplies __deepcopy__ and apply methods
    for unary parsers. The __deepcopy__ method needs to be
    overwritten, however, if the constructor of a derived class has
    additional parameters.
    """

    def __init__(self, *parsers: Parser) -> None:
        super(NaryParser, self).__init__()
        assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        self.parsers = parsers  # type: Tuple[Parser, ...]

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        duplicate = self.__class__(*parsers)
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    def _apply(self, func: ApplyFunc, flip: FlagFunc) -> bool:
        if super(NaryParser, self)._apply(func, flip):
            for parser in self.parsers:
                parser._apply(func, flip)
            return True
        return False


class Option(UnaryParser):
    r"""
    Parser ``Option`` always matches, even if its child-parser
    did not match.

    If the child-parser did not match ``Option`` returns a node
    with no content and does not move forward in the text.

    If the child-parser did match, ``Option`` returns the a node
    with the node returned by the child-parser as its single
    child and the text at the position where the child-parser
    left it.

    Examples::

        >>> number = Option(TKN('-')) + RegExp(r'\d+') + Option(RegExp(r'\.\d+'))
        >>> Grammar(number)('3.14159').content
        '3.14159'
        >>> Grammar(number)('3.14159').as_sxpr()
        '(:Series (:RegExp "3") (:RegExp ".14159"))'
        >>> Grammar(number)('-1').content
        '-1'

    EBNF-Notation: ``[ ... ]``

    EBNF-Example:  ``number = ["-"]  /\d+/  [ /\.\d+/ ]``
    """

    def __init__(self, parser: Parser) -> None:
        super(Option, self).__init__(parser)
        # assert isinstance(parser, Parser)
        assert not isinstance(parser, Option), \
            "Redundant nesting of options: %s(%s)" % (self.ptype, parser.pname)

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, text = self.parser(text)
        return self._return_value(node), text

    def __repr__(self):
        return '[' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + ']'


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
        Node(:EMPTY__, )

    EBNF-Notation: ``{ ... }``

    EBNF-Example:  ``sentence = { /\w+,?/ } "."``
    """

    @cython.locals(n=cython.int)
    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        n = len(text) + 1  # type: int
        while len(text) < n:  # text and len(text) < n:
            n = len(text)
            node, text = self.parser(text)
            if not node:
                break
            if node._result or not node.tag_name.startswith(':'):  # drop anonymous empty nodes
                results += (node,)
            if len(text) == n:
                break  # avoid infinite loop
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
        ' <<< Error on "." | Parser "{/\\w+,?/ ~}+ \'.\' ~" did not match! >>> '
        >>> forever = OneOrMore(RegExp(''))
        >>> Grammar(forever)('')  # infinite loops will automatically be broken
        Node(:EMPTY__, )

    EBNF-Notation: ``{ ... }+``

    EBNF-Example:  ``sentence = { /\w+,?/ }+``
    """

    def __init__(self, parser: Parser) -> None:
        super(OneOrMore, self).__init__(parser)
        assert not isinstance(parser, Option), \
            "Use ZeroOrMore instead of nesting OneOrMore and Option: " \
            "%s(%s)" % (self.ptype, parser.pname)

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        match_flag = False
        n = len(text) + 1  # type: int
        while len(text_) < n:  # text_ and len(text_) < n:
            n = len(text_)
            node, text_ = self.parser(text_)
            if not node:
                break
            match_flag = True
            if node._result or not node.tag_name.startswith(':'):  # drop anonymous empty nodes
                results += (node,)
            if len(text_) == n:
                break  # avoid infinite loop
        if not match_flag:
            return None, text
        nd = self._return_values(results)  # type: Node
        return nd, text_

    def __repr__(self):
        return '{' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + '}+'


MessagesType = List[Tuple[Union[str, Any], str]]
NO_MANDATORY = 1000


def mandatory_violation(grammar: Grammar,
                        text_: StringView,
                        failed_on_lookahead: bool,
                        expected: str,
                        err_msgs: MessagesType,
                        reloc: int) -> Tuple[Error, Node, StringView]:
    """
    Choses the right error message in case of a mandatory violation and
    returns an error with this message, an error node, to which the error
    is attached, and the text segment where parsing is to continue.

    This is a helper function that abstracts functionality that is
    needed by the AllOf- as well as the Series-parser.

    :param grammar: the grammar
    :param text_: the point, where the mandatory violation. As usual the
            string view represents the remaining text from this point.
    :param failed_on_lookahead: True if the violating parser was a
            Lookahead-Parser.
    :param expected:  the expected (but not found) text at this point.
    :param err_msgs:  A list of pairs of regular expressions (or simple
            strings for that matter) and error messages that are chosen
            if the regular expression matches the text where the error
            occurred.
    :param reloc: A position value that represents the reentry point for
            parsing after the error occurred.

    :return:   a tuple of an error object, a zombie node at the position
            where the mandatory violation occured and to which the error
            object is attached and a string view for continuing the
            parsing process
    """
    i = reloc if reloc >= 0 else 0
    location = grammar.document_length__ - len(text_)
    err_node = Node(ZOMBIE_TAG, text_[:i]).with_pos(location)
    found = text_[:10].replace('\n', '\\n ') + '...'
    for search, message in err_msgs:
        rxs = not isinstance(search, str)
        if (rxs and text_.match(search)) or (not rxs and text_.startswith(search)):
            try:
                msg = message.format(expected, found)
                break
            except (ValueError, KeyError, IndexError) as e:
                error = Error("Malformed error format string »{}« leads to »{}«"
                              .format(message, str(e)),
                              location, Error.MALFORMED_ERROR_STRING)
                grammar.tree__.add_error(err_node, error)
    else:
        if grammar.history_tracking__:
            for pname, _ in reversed(grammar.call_stack__):
                if not pname.startswith(':'):
                    break
            msg = '%s expected by parser %s, »%s« found!' % (expected, pname, found)
        else:
            msg = '%s expected, »%s« found!' % (expected, found)
    error = Error(msg, location, Error.MANDATORY_CONTINUATION_AT_EOF
        if (failed_on_lookahead and not text_) else Error.MANDATORY_CONTINUATION)
    grammar.tree__.add_error(err_node, error)
    return error, err_node, text_[i:]


class Series(NaryParser):
    r"""
    Matches if each of a series of parsers matches exactly in the order of
    the series.

    Attributes:
        mandatory (int):  Number of the element statring at which the element
                and all following elements are considered "mandatory". This
                means that rather than returning a non-match an error message
                is isssued. The default value is NO_MANDATORY, which means that
                no elements are mandatory.
        errmsg (str):  An optional error message that overrides the default
               message for mandatory continuation errors. This can be used to
               provide more helpful error messages to the user.

    Example::

        >>> variable_name = RegExp(r'(?!\d)\w') + RE(r'\w*')
        >>> Grammar(variable_name)('variable_1').content
        'variable_1'
        >>> str(Grammar(variable_name)('1_variable'))
        ' <<< Error on "1_variable" | Parser "/(?!\\d)\\w/ /\\w*/ ~" did not match! >>> '

    EBNF-Notation: ``... ...``    (sequence of parsers separated by a blank or new line)

    EBNF-Example:  ``series = letter letter_or_digit``
    """
    RX_ARGUMENT = re.compile(r'\s(\S)')

    def __init__(self, *parsers: Parser,
                 mandatory: int = NO_MANDATORY,
                 err_msgs: MessagesType=[],
                 skip: ResumeList = []) -> None:
        super(Series, self).__init__(*parsers)
        length = len(self.parsers)
        if mandatory < 0:
            mandatory += length

        assert not (mandatory == NO_MANDATORY and err_msgs), \
            'Custom error messages require that parameter "mandatory" is set!'
        assert not (mandatory == NO_MANDATORY and skip), \
            'Search expressions for skipping text require that parameter "mandatory" is set!'

        assert length > 0, \
            'Length of series %i is below minimum length of 1' % length
        assert length < NO_MANDATORY, \
            'Length %i of series exceeds maximum length of %i' % (length, NO_MANDATORY)

        assert 0 <= mandatory < length or mandatory == NO_MANDATORY

        self.mandatory = mandatory  # type: int
        self.err_msgs = err_msgs    # type: MessagesType
        self.skip = skip            # type: ResumeList

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        duplicate = self.__class__(*parsers, mandatory=self.mandatory,
                                   err_msgs=self.err_msgs, skip=self.skip)
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    @cython.locals(pos=cython.int, reloc=cython.int)
    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        error = None  # type: Optional[Error]
        for pos, parser in enumerate(self.parsers):
            node, text_ = parser(text_)
            if not node:
                if pos < self.mandatory:
                    return None, text
                else:
                    reloc = reentry_point(text_, self.skip, self.grammar.comment_rx__) \
                        if self.skip else -1
                    error, node, text_ = mandatory_violation(
                        self.grammar, text_, isinstance(parser, Lookahead), parser.repr,
                        self.err_msgs, reloc)
                    # check if parsing of the series can be resumed somewhere
                    if reloc >= 0:
                        nd, text_ = parser(text_)  # try current parser again
                        if nd:
                            results += (node,)
                            node = nd
                    else:
                        results += (node,)
                        break
            if node._result or not node.tag_name.startswith(':'):  # drop anonymous empty nodes
                results += (node,)
        # assert len(results) <= len(self.parsers) \
        #        or len(self.parsers) >= len([p for p in results if p.tag_name != ZOMBIE_TAG])
        ret_node = self._return_values(results)  # type: Node
        if error and reloc < 0:
            raise ParserError(ret_node.with_pos(self.grammar.document_length__ - len(text)),
                              text, error, first_throw=True)
        return ret_node, text_

    def __repr__(self):
        return " ".join([parser.repr for parser in self.parsers[:self.mandatory]]
                        + (['§'] if self.mandatory != NO_MANDATORY else [])
                        + [parser.repr for parser in self.parsers[self.mandatory:]])

    # The following operator definitions add syntactical sugar, so one can write:
    # `RE('\d+') + Optional(RE('\.\d+)` instead of `Series(RE('\d+'), Optional(RE('\.\d+))`

    @staticmethod
    def combined_mandatory(left: Parser, right: Parser):
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

    def __add__(self, other: Parser) -> 'Series':
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Series(*(self.parsers + other_parsers),
                      mandatory=self.combined_mandatory(self, other))

    def __radd__(self, other: Parser) -> 'Series':
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Series(*(other_parsers + self.parsers),
                      mandatory=self.combined_mandatory(other, self))

    def __iadd__(self, other: Parser) -> 'Series':
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        self.parsers += other_parsers
        self.mandatory = self.combined_mandatory(self, other)
        return self


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
        '3 <<< Error on ".1416" | Parser stopped before end! trying to recover... >>> '

        # the most selective expression should be put first:
        >>> number = RE(r'\d+') + RE(r'\.') + RE(r'\d+') | RE(r'\d+')
        >>> Grammar(number)("3.1416").content
        '3.1416'

    EBNF-Notation: ``... | ...``

    EBNF-Example:  ``sentence = /\d+\.\d+/ | /\d+/``
    """

    def __init__(self, *parsers: Parser) -> None:
        super(Alternative, self).__init__(*parsers)
        assert len(self.parsers) >= 1
        # only the last alternative may be optional. Could this be checked at compile time?
        assert all(not isinstance(p, Option) for p in self.parsers[:-1]), \
            "Parser-specification Error: only the last alternative may be optional!"

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        for parser in self.parsers:
            node, text_ = parser(text)
            if node:
                return self._return_value(node), text_
                # return self._return_value(node if node._result or parser.pname else None), text_
                # return Node(self.tag_name,
                #             node if node._result or parser.pname else ()), text_
        return None, text

    def __repr__(self):
        return '(' + ' | '.join(parser.repr for parser in self.parsers) + ')'

    def reset(self):
        super(Alternative, self).reset()
        return self

    # The following operator definitions add syntactical sugar, so one can write:
    # `RE('\d+') + RE('\.') + RE('\d+') | RE('\d+')` instead of:
    # `Alternative(Series(RE('\d+'), RE('\.'), RE('\d+')), RE('\d+'))`

    def __or__(self, other: Parser) -> 'Alternative':
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Alternative(*(self.parsers + other_parsers))

    def __ror__(self, other: Parser) -> 'Alternative':
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Alternative(*(other_parsers + self.parsers))

    def __ior__(self, other: Parser) -> 'Alternative':
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
            else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        self.parsers += other_parsers
        return self


class AllOf(NaryParser):
    """
    Matches if all elements of a list of parsers match. Each parser must
    match exactly once. Other than in a sequence, the order in which
    the parsers match is arbitrary, however.

    Example::

        >>> prefixes = AllOf(TKN("A"), TKN("B"))
        >>> Grammar(prefixes)('A B').content
        'A B'
        >>> Grammar(prefixes)('B A').content
        'B A'

    EBNF-Notation: ``<... ...>``    (sequence of parsers enclosed by angular brackets)

    EBNF-Example:  ``set = <letter letter_or_digit>``
    """

    def __init__(self, *parsers: Parser,
                 mandatory: int = NO_MANDATORY,
                 err_msgs: MessagesType = [],
                 skip: ResumeList = []) -> None:
        if len(parsers) == 1:
            assert isinstance(parsers[0], Series), \
                "AllOf should be initialized either with a series or with more than one parser!"
            series = cast(Series, parsers[0])  # type: Series
            if mandatory == NO_MANDATORY:
                mandatory = series.mandatory
            if not err_msgs:
                err_msgs = series.err_msgs
            if not skip:
                skip = series.skip

            assert series.mandatory == NO_MANDATORY or mandatory == series.mandatory, \
                "If AllOf is initialized with a series, parameter 'mandatory' must be the same!"
            assert not series.err_msgs or err_msgs == series.err_msgs, \
                "If AllOf is initialized with a series, 'err_msg' must empty or the same!"
            assert not series.skip or skip == series.skip, \
                "If AllOf is initialized with a series, 'skip' must empty or the same!"

            parsers = series.parsers

        super(AllOf, self).__init__(*parsers)
        self.num_parsers = len(self.parsers)  # type: int
        if mandatory < 0:
            mandatory += self.num_parsers

        assert not (mandatory == NO_MANDATORY and err_msgs), \
            'Custom error messages require that parameter "mandatory" is set!'
        assert not (mandatory == NO_MANDATORY and skip), \
            'Search expressions for skipping text require that parameter "mandatory" is set!'
        assert self.num_parsers > 0, \
            'Number of elements %i is below minimum of 1' % self.num_parsers
        assert self.num_parsers < NO_MANDATORY, \
            'Number of elemnts %i of exceeds maximum of %i' % (self.num_parsers, NO_MANDATORY)
        assert 0 <= mandatory < self.num_parsers or mandatory == NO_MANDATORY

        self.mandatory = mandatory  # type: int
        self.err_msgs = err_msgs    # type: MessagesType
        self.skip = skip            # type: ResumeList

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        duplicate = self.__class__(*parsers, mandatory=self.mandatory,
                                   err_msgs=self.err_msgs, skip=self.skip)
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        duplicate.num_parsers = self.num_parsers
        return duplicate

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        parsers = list(self.parsers)  # type: List[Parser]
        error = None  # type: Optional[Error]
        while parsers:
            for i, parser in enumerate(parsers):
                node, text__ = parser(text_)
                if node:
                    if node._result or not node.tag_name.startswith(':'):  # drop anonymous empty nodes
                        results += (node,)
                        text_ = text__
                    del parsers[i]
                    break
            else:
                if self.num_parsers - len(parsers) < self.mandatory:
                    return None, text
                else:
                    reloc = reentry_point(text_, self.skip, self.grammar.comment_rx__) \
                        if self.skip else -1
                    expected = '< ' + ' '.join([parser.repr for parser in parsers]) + ' >'
                    lookahead = any([isinstance(p, Lookahead) for p in parsers])
                    error, err_node, text_ = mandatory_violation(
                        self.grammar, text_, lookahead, expected, self.err_msgs, reloc)
                    results += (err_node,)
                    if reloc < 0:
                        parsers = []
        assert len(results) <= len(self.parsers) \
               or len(self.parsers) >= len([p for p in results if p.tag_name != ZOMBIE_TAG])
        nd = self._return_values(results)  # type: Node
        if error and reloc < 0:
            raise ParserError(nd.with_pos(self.grammar.document_length__ - len(text)),
                              text, error, first_throw=True)
        return nd, text_

    def __repr__(self):
        return '< ' + ' '.join(parser.repr for parser in self.parsers) + ' >'


class SomeOf(NaryParser):
    """
    Matches if at least one element of a list of parsers match. No parser
    must match more than once . Other than in a sequence, the order in which
    the parsers match is arbitrary, however.

    Example::

        >>> prefixes = SomeOf(TKN("A"), TKN("B"))
        >>> Grammar(prefixes)('A B').content
        'A B'
        >>> Grammar(prefixes)('B A').content
        'B A'
        >>> Grammar(prefixes)('B').content
        'B'

    EBNF-Notation: ``<... ...>``    (sequence of parsers enclosed by angular brackets)

    EBNF-Example:  ``set = <letter letter_or_digit>``
    """

    def __init__(self, *parsers: Parser) -> None:
        if len(parsers) == 1:
            assert isinstance(parsers[0], Alternative), \
                "Parser-specification Error: No single arguments other than a Alternative " \
                "allowed as arguments for SomeOf-Parser !"
            alternative = cast(Alternative, parsers[0])
            parsers = alternative.parsers
        super(SomeOf, self).__init__(*parsers)

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        parsers = list(self.parsers)  # type: List[Parser]
        while parsers:
            for i, parser in enumerate(parsers):
                node, text__ = parser(text_)
                if node:
                    if node._result or not node.tag_name.startswith(':'):  # drop anonymous empty nodes
                        results += (node,)
                        text_ = text__
                    del parsers[i]
                    break
            else:
                parsers = []
        assert len(results) <= len(self.parsers)
        if results:
            return self._return_values(results), text_
        else:
            return None, text

    def __repr__(self):
        return '< ' + ' | '.join(parser.repr for parser in self.parsers) + ' >'


def Unordered(parser: NaryParser) -> NaryParser:
    """
    Returns an AllOf- or SomeOf-parser depending on whether `parser`
    is a Series (AllOf) or an Alternative (SomeOf).
    """
    if isinstance(parser, Series):
        return AllOf(parser)
    elif isinstance(parser, Alternative):
        return SomeOf(parser)
    else:
        raise AssertionError("Unordered can take only Series or Alternative as parser.")


########################################################################
#
# Flow control parsers
#
########################################################################

class FlowParser(UnaryParser):
    """
    Base class for all flow parsers like Lookahead and Lookbehind.
    """
    def sign(self, bool_value) -> bool:
        """Returns the value. Can be overriden to return the inverted bool."""
        return bool_value


def Required(parser: Parser) -> Parser:
    return Series(parser, mandatory=0)


# class Required(FlowParser):
#     """OBSOLETE. Use mandatory-parameter of Series-parser instead!
#     """
#     RX_ARGUMENT = re.compile(r'\s(\S)')
#
#     def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
#         node, text_ = self.parser(text)
#         if not node:
#             m = text.search(Required.RX_ARGUMENT)  # re.search(r'\s(\S)', text)
#             i = max(1, text.index(m.regs[1][0])) if m else 1
#             node = Node(self, text[:i])
#             text_ = text[i:]
#             self.grammar.tree__.new_error(node,
#                                           '%s expected; "%s" found!' % (str(self.parser),
#                                           text[:10]), code=Error.MANDATORY_CONTINUATION)
#         return node, text_
#
#     def __repr__(self):
#         return '§' + self.parser.repr


class Lookahead(FlowParser):
    """
    Matches, if the contained parser would match for the following text,
    but does not consume any text.
    """
    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, _ = self.parser(text)
        if self.sign(node is not None):
                # static analysis requires lookahead to be disabled at document end
                # or (self.grammar.static_analysis_pending__ and not text)):
            return Node(self.tag_name, '') if self.pname else EMPTY_NODE, text
        else:
            return None, text

    def __repr__(self):
        return '&' + self.parser.repr


class NegativeLookahead(Lookahead):
    """
    Matches, if the contained parser would *not* match for the following
    text.
    """
    def __repr__(self):
        return '!' + self.parser.repr

    def sign(self, bool_value) -> bool:
        return not bool_value


class Lookbehind(FlowParser):
    """
    Matches, if the contained parser would match backwards. Requires
    the contained parser to be a RegExp, _RE, PlainText or _Token parser.

    EXPERIMENTAL
    """
    def __init__(self, parser: Parser) -> None:
        p = parser
        while isinstance(p, Synonym):
            p = p.parser
        assert isinstance(p, RegExp) or isinstance(p, Token)
        self.regexp = None
        self.text = ''  # type: str
        if isinstance(p, RegExp):
            self.regexp = cast(RegExp, p).regexp
        else:  # p is of type PlainText
            self.text = cast(Token, p).text
        super(Lookbehind, self).__init__(parser)

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        backwards_text = self.grammar.reversed__[len(text):]
        if self.regexp is None:  # assert self.text is not None
            does_match = backwards_text[:len(self.text)] == self.text
        else:  # assert self.regexp is not None
            does_match = backwards_text.match(self.regexp)
        return (Node(self.tag_name, ''), text) if self.sign(does_match) else (None, text)

    def __repr__(self):
        return '-&' + self.parser.repr


class NegativeLookbehind(Lookbehind):
    """
    Matches, if the contained parser would *not* match backwards. Requires
    the contained parser to be a RegExp-parser.
    """
    def __repr__(self):
        return '-!' + self.parser.repr

    def sign(self, bool_value) -> bool:
        return not bool(bool_value)


########################################################################
#
# Capture and Retrieve parsers (for passing variables in the parser)
#
########################################################################


class Capture(UnaryParser):
    """
    Applies the contained parser and, in case of a match, saves the result
    in a variable. A variable is a stack of values associated with the
    contained parser's name. This requires the contained parser to be named.
    """
    def _rollback(self):
        return self.grammar.variables__[self.pname].pop()

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, text_ = self.parser(text)
        if node:
            assert self.pname, """Tried to apply an unnamed capture-parser!"""
            self.grammar.variables__[self.pname].append(node.content)
            location = self.grammar.document_length__ - len(text)
            self.grammar.push_rollback__(location, self._rollback)  # lambda: stack.pop())
            # caching will be blocked by parser guard (see way above),
            # because it would prevent recapturing of rolled back captures
            return self._return_value(node), text_
        else:
            return None, text

    def __repr__(self):
        return self.parser.repr


RetrieveFilter = Callable[[List[str]], str]


def last_value(stack: List[str]) -> str:
    """Returns the last value on the cpature stack. This is the default case
    when retrieving cpatured substrings."""
    return stack[-1]


def counterpart(stack: List[str]) -> str:
    """Returns a closing bracket for the opening bracket on the capture stack,
    i.e. if "[" was captured, "]" will be retrieved."""
    value = stack[-1]
    return value.replace("(", ")").replace("[", "]").replace("{", "}").replace("<", ">")


def accumulate(stack: List[str]) -> str:
    """Returns an accumulation of all values on the stack.
    By the way: I cannot remember any reasonable use case for this!?"""
    return "".join(stack) if len(stack) > 1 else stack[-1]  # provoke IndexError if stack empty


class Retrieve(Parser):
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
        rfilter: a procedure that through which the processing to the
            retrieved symbols is channeled. In the simplest case it merely
            returns the last string stored by the observed parser. This can
            be (mis-)used to execute any kind of semantic action.
    """

    def __init__(self, symbol: Parser, rfilter: RetrieveFilter = None) -> None:
        super(Retrieve, self).__init__()
        self.symbol = symbol
        self.filter = rfilter if rfilter else last_value

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.symbol, self.filter)
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        return duplicate

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        # the following indirection allows the call() method to be called
        # from subclass without triggering the parser guard a second time
        return self.retrieve_and_match(text)

    def __repr__(self):
        return ':' + self.symbol.repr

    def retrieve_and_match(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        """
        Retrieves variable from stack through the filter function passed to
        the class' constructor and tries to match the variable's value with
        the following text. Returns a Node containing the value or `None`
        accordingly.
        """
        try:
            stack = self.grammar.variables__[self.symbol.pname]
            value = self.filter(stack)
        except (KeyError, IndexError):
            node = Node(self.tag_name, '').with_pos(self.grammar.document_length__ - len(text))
            self.grammar.tree__.new_error(
                node, dsl_error_msg(self, "'%s' undefined or exhausted." % self.symbol.pname))
            return node, text
        if text.startswith(value):
            return Node(self.tag_name, value), text[len(value):]
        else:
            return None, text


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
    def __init__(self, symbol: Parser, rfilter: RetrieveFilter = None) -> None:
        super(Pop, self).__init__(symbol, rfilter)

    def reset(self):
        super(Pop, self).reset()
        self.values = []

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.symbol, self.filter)
        duplicate.pname = self.pname
        duplicate.tag_name = self.tag_name
        duplicate.values = self.values[:]
        return duplicate

    def _rollback(self):
        return self.grammar.variables__[self.symbol.pname].append(self.values.pop())

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, txt = self.retrieve_and_match(text)
        if node and not id(node) in self.grammar.tree__.error_nodes:
            self.values.append(self.grammar.variables__[self.symbol.pname].pop())
            location = self.grammar.document_length__ - len(text)
            self.grammar.push_rollback__(location, self._rollback)  # lambda: stack.append(value))
        return node, txt

    def __repr__(self):
        return '::' + self.symbol.repr


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

    def _parse(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, text = self.parser(text)
        if node:
            return Node(self.tag_name, node), text
        return None, text

    def __repr__(self):
        return self.pname or self.parser.repr


class Forward(Parser):
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
    """

    def __init__(self):
        super(Forward, self).__init__()
        self.parser = None
        self.cycle_reached = False

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        # duplicate.pname = self.pname  # Forward-Parsers should never have a name!
        duplicate.tag_name = self.tag_name
        memo[id(self)] = duplicate
        parser = copy.deepcopy(self.parser, memo)
        duplicate.set(parser)
        return duplicate

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        """
        Overrides Parser.__call__, because Forward is not an independent parser
        but merely a redirects the call to another parser. Other then parser
        `Synonym`, which might be a meaningful marker for the syntax tree,
        parser Forward should never appear in the syntax tree.
        """
        return self.parser(text)

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

    def _apply(self, func: ApplyFunc, flip: FlagFunc) -> bool:
        if super(Forward, self)._apply(func, flip):
            self.parser._apply(func, flip)
            return True
        return False
