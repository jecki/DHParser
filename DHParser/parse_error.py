# parse_error.py - handling of parsing-errors
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
Module parse_error contains defines ParserError which can be
raised by parsers as well as functions for resuming the parsing
process after a (syntax) error occurred.
"""


from __future__ import annotations
from typing import Callable, cast, Union, Optional, Iterator, TYPE_CHECKING

from DHParser.error import Error, ERROR_WHILE_RECOVERING_FROM_ERROR
from DHParser.log import CallItem
from DHParser.stringview import StringView
from DHParser.nodetree import Node, ZOMBIE_TAG
from DHParser.toolkit import TypeAlias, List, Tuple, RxType

try:
    import cython
except (ImportError, NameError):
    import DHParser.externallibs.shadow_cython as cython

if TYPE_CHECKING:
    from DHParser.parse_base import Parser


class ParserError(Exception):
    """
    A "ParserError" is thrown for those parser errors that allow the
    controlled re-entrance of the parsing process after the error occurred.
    If a reentry-rule has been configured for the parser where the error
    occurred, the parser guard can resume the parsing process.

    Currently, the only case when a ParserError is thrown (and not some
    different kind of error like UnknownParserError) is when a :py:class:`Series`
    or :py:class:`Interleave`-parser detects a missing mandatory element.

    :ivar parser:  The parser within which the error has been raised
    :ivar node:  The node within which the error is located
    :ivar node_orig_len:  The original size of that node. The actual size
        of that node may change due to later processing steps and thus not
        be reliable anymore for the description of the error.
    :ivar location:  The location in the document where the parser that caused the
        error started. This is not to be confused with the location where the error
        occurred, because by the time the error occurrs the parser may already have
        read some part of the document.
    :ivar error:  The :py:class:`~error.Error` object that contains, among other things,
        the exact error location.
    :ivar first_throw:  A flag that indicates that the error has not yet been re-raised
    :ivar attributes_locked:  A frozenset of attributes that must not be overwritten
        once the ParrserError-object has been initialized by its constructor
    :ivar callstack_snapshot:  A snapshot of the callstack (if history-recording has
        been turned on) at the point where the error occurred.

    """
    def __init__(self,
                 parser: Parser,
                 node: Node,
                 node_orig_len: int,
                 location: int,
                 error: Error, *,
                 first_throw: bool):
        assert node is not None
        self.parser: Parser = parser
        self.node: Node = node
        self.node_orig_len: int = node_orig_len
        self.location: int = location
        self.error: Error = error
        self.first_throw: bool = first_throw
        self.attributes_locked = frozenset({'parser', 'node', 'location', 'error', 'first_throw'})
        self.callstack_snapshot: List[CallItem] = []  # List[(name, location)]

    def __setattr__(self, name, value):
        if name == "attributes_locked":
            self.__dict__[name] = value
        elif "attributes_locked" not in self.__dict__ \
                or name not in self.__dict__['attributes_locked']:
            self.__dict__[name] = value
        else:
            raise TypeError('Attribute %s of ParserError-object must not be reassigned!' % name)

    def __str__(self):
        snippet = self.parser.grammar.document__[self.location:self.location + 25]
        return "%i: %s    %s (%s)" \
               % (self.node.pos, snippet, repr(self.node), str(self.error))

    def new_PE(self, **kwargs):
        """Returns a new ParserError object with the same attribute values
        as "self", except those that are reassigned in "kwargs"::

            >>> from DHParser.parse_base import Parser
            >>> from DHParser.nodetree import Node
            >>> pe = ParserError(Parser(), Node('test', ""), 0, 0, Error("", 0), first_throw=True)
            >>> pe_derived = pe.new_PE(first_throw = False)
            >>> pe.first_throw
            True
            >>> pe_derived.first_throw
            False
        """
        args = {"parser": self.parser,
                "node": self.node,
                "node_orig_len": self.node_orig_len,
                "location": self.location,
                "error": self.error,
                "first_throw": self.first_throw}
        assert len(kwargs.keys() - args.keys()) == 0, str(kwargs.keys() - args.keys())
        args.update(kwargs)
        pe = ParserError(**args)
        pe.callstack_snapshot = self.callstack_snapshot
        return pe


PatternMatchType: TypeAlias = Union[RxType, str, Callable, 'Parser']
ErrorMessagesType: TypeAlias = List[Tuple[PatternMatchType, str]]
ResumeList: TypeAlias = List[Union[PatternMatchType, 'Parser']]  # list of strings or regular expressions
ReentryPointAlgorithm: TypeAlias = Callable[[StringView, int, int], Tuple[int, int]]
# (text, start point, end point) => (reentry point, match length)
# A return value of (-1, x) means that no reentry point before the end of the document was found


# @cython.returns(cython.int)
# must not use: @functools.lru_cache(), because resume-function may contain
# context-sensitive parsers!!!
@cython.locals(upper_limit=cython.int, closest_match=cython.int, pos=cython.int)
def reentry_point(rest: StringView,
                  rules: ResumeList,
                  comment_regex,
                  search_window: int = -1,
                  skip_node_name: str = "") -> Tuple[int, Node]:
    r"""
    Finds the point where parsing should resume after a ParserError has been caught.
    The algorithm makes sure that this reentry-point does not lie inside a comment.
    The re-entry point is always the point after the end of the match of the regular
    expression defining the re-entry point. (Use lookahead if you want to define
    the re-entry point by what follows rather than by what text precedes the point.)

    REMARK: The algorithm assumes that any stretch of the document that matches
    "comment_regex" is actually a comment. It is possible to define grammars,
    where the use of comments is restricted to certain areas and that allow to
    use constructs that look like comments (i.e. will be matched by "comment_regex")
    but are none in other areas. For example::

        my_string = "# This is not a comment"; foo()  # This is a comment bar()

    Here the reentry-algorithm would overlook "foo()" and jump directly to "bar()".
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
    :param skip_node_name: A name for the skip-node that is used to store that part
        of the document that will be skipped before continuing with the parsing process.
        f"_R{nr}__" will be added to the skip-node name, where "nr" is the nummer
        of the skip-rule, of which there can be more than one for the same parser.
    :return: A tuple of the integer index (counted from the beginning of rest!)
        of the closest reentry point and a Node
        capturing all text from "rest" up to this point or (-1, None) if no
        reentry-point was found.
    """
    from parse_base import Parser

    upper_limit = len(rest) + 1
    closest_match = upper_limit
    skip_node = None
    comments = None  # type: Optional[Iterator]
    if search_window < 0:
        search_window = len(rest)

    @cython.locals(a=cython.int, b=cython.int)
    def next_comment() -> Tuple[int, int]:
        """Returns the [start, end[ intervall of the next comment in the text.
        The comment-iterator starts at the beginning of the "rest" of the
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
        """Returns the starting position of the next occurrence of "s" in
        the "rest" of the document beginning with "start" and the length
        of the match, which in this case is always the length of "s" itself.
        If there is no match, the returned starting position will be -1.
        """
        nonlocal rest
        return rest.find(s, start, start + search_window), len(s)

    @cython.locals(start=cython.int, end=cython.int)
    def rx_search(rx, start: int = 0) -> Tuple[int, int]:
        """Returns the staring position and the length of the next match of
        the regular expression "rx" in the "rest" of the document, starting
        with "start".
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
        the reentry-point-search-function "func" yields.
        """
        nonlocal rest
        return func(rest, start, start + search_window)

    @cython.returns(cython.int)
    @cython.locals(a=cython.int, b=cython.int, k=cython.int, length=cython.int)
    def entry_point(search_func, search_rule) -> int:
        """Returns the next reentry-point outside a comment that "search_func"
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
    nr = 0
    for nr, rule in enumerate(rules, 1):
        comments = rest.finditer(comment_regex)
        if isinstance(rule, Parser):
            parser = cast(Parser, rule)
            grammar = parser.grammar
            save = grammar.history_tracking__
            grammar.history_tracking__ = False
            try:
                location = len(parser.grammar.text__) - len(rest)
                _node, _location = parser(location)
                _text = parser.grammar.document__[_location:]
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
        skip_node = Node(f'{skip_node_name}_R{nr}__', rest[:max(closest_match, 0)])
    return closest_match, skip_node


ARTIFACT_NAMES = ('_skip_', '_resume_', ZOMBIE_TAG)

def artifact(nd: Node) -> bool:
    """Returns True, if node is a skip, resume or ZOMBIE-node."""
    return nd.name[-2:] == '__' and any(nd.name.find(part) >= 0 for part in ARTIFACT_NAMES)
