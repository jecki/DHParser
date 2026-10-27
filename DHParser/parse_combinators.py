# parse_combinators.py - base class for all parser combinators
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
Module parse_combinators provides classes for all kinds of parsers and
parser combinators, e.g. Series, Alternative, OneOrMore. It furthermore
defines look a head and look behind parsers as well as content capturing
parsers. (The latter break with the paradigm of conext free grammars and
are not compatible with other parsing expression grammar suites. Use with
care!) Finally, it defines Forward parsers allow for cycles
(i.e. forward-references) in the grammar. Class :py:class:`Forward` also
contains functionality for handling left left-recursion via a variant of
the squirrel-parser algorithm.
"""


from __future__ import annotations

import functools
from collections import defaultdict
import copy
from functools import lru_cache
from inspect import isclass
from itertools import chain
from typing import Callable, cast, Collection, DefaultDict, Sequence, Union, Optional, \
    NamedTuple, Iterator

from DHParser.configuration import get_config_value, NEVER_MATCH_PATTERN
from DHParser.error import Error, ErrorCode, MANDATORY_CONTINUATION, \
    UNDEFINED_RETRIEVE, PARSER_LOOKAHEAD_FAILURE_ONLY, CUSTOM_PARSER_FAILURE, \
    PARSER_LOOKAHEAD_MATCH_ONLY, PARSER_STOPPED_BEFORE_END, PARSER_NEVER_TOUCHES_DOCUMENT, \
    MALFORMED_ERROR_STRING, MANDATORY_CONTINUATION_AT_EOF, DUPLICATE_PARSERS_IN_ALTERNATIVE, \
    CAPTURE_WITHOUT_PARSERNAME, CAPTURE_DROPPED_CONTENT_WARNING, LOOKAHEAD_WITH_OPTIONAL_PARSER, \
    BADLY_NESTED_OPTIONAL_PARSER, BAD_ORDER_OF_ALTERNATIVES, BAD_MANDATORY_SETUP, \
    OPTIONAL_REDUNDANTLY_NESTED_WARNING, CAPTURE_STACK_NOT_EMPTY, BAD_REPETITION_COUNT, \
    AUTOCAPTURED_SYMBOL_NOT_CLEARED, RECURSION_DEPTH_LIMIT_HIT, CAPTURE_STACK_NOT_EMPTY_WARNING, \
    MANDATORY_CONTINUATION_AT_EOF_NON_ROOT, CAPTURE_STACK_NOT_EMPTY_NON_ROOT_ONLY, \
    AUTOCAPTURED_SYMBOL_NOT_CLEARED_NON_ROOT, ERROR_WHILE_RECOVERING_FROM_ERROR, \
    ZERO_LENGTH_CAPTURE_POSSIBLE_WARNING, PARSER_STOPPED_ON_RETRY, ERROR, CANCELED, \
    INFINITE_LOOP_WARNING, REDUNDANT_PARSER_WARNING, PARSER_STOPPED_BEFORE_END_WARNING, \
    has_errors, is_error
from DHParser.log import CallItem, HistoryRecord
from DHParser.parse_base import Parser, LeafParser, copy_parser_base_attrs, ParsingResult, \
    NoMemoizationParser, Drop, get_parser_placeholder, is_parser_placeholder, \
    is_grammar_placeholder, ParseFunc
from DHParser.parse_error import ParserError
from DHParser.parse_grammar import Grammar, AnalysisError, dsl_error, is_disposable, \
    UninitializedError
from DHParser.preprocess import BEGIN_TOKEN, END_TOKEN, RX_TOKEN_NAME, SourceMapFunc
from DHParser.stringview import StringView, EMPTY_STRING_VIEW
from DHParser.nodetree import Node, RootNode, FrozenNode, WHITESPACE_PTYPE, \
    KEEP_COMMENTS_PTYPE, TOKEN_PTYPE, MIXED_CONTENT_TEXT_PTYPE, ZOMBIE_TAG, EMPTY_NODE, \
    EMPTY_PTYPE, LEAF_NODE, ChildrenType, ResultType
from DHParser.toolkit import sane_parser_name, escape_ctrl_chars, re, matching_brackets, \
    abbreviate_middle, RxPatternType, linebreaks, line_col, TypeAlias, List, Tuple, Any, \
    MutableSet, Set, FrozenSet, Dict, INFINITE, LazyRE, CancelQuery, deprecated, RxType

try:
    import cython
except (ImportError, NameError):
    import DHParser.externallibs.shadow_cython as cython


class PreprocessorToken(LeafParser):
    """
    Parses tokens that have been inserted by a preprocessor.

    Preprocessors can generate Tokens with the "make_token"-function.
    These tokens start and end with magic characters that can only be
    matched by the PreprocessorToken Parser. Such tokens can be used to
    insert BEGIN - END delimiters at the beginning or ending of a
    quoted block, for example.
    """

    def __init__(self, token: str) -> None:
        assert token and token.isupper()
        assert RX_TOKEN_NAME.match(token)
        super().__init__()
        self.pname = token
        if token:
            self.disposable = False

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.pname)
        copy_parser_base_attrs(self, duplicate, memo)
        return duplicate

    @cython.locals(end=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        text = self._grammar.document__[location:]
        if text[0:1] == BEGIN_TOKEN:
            end = text.find(END_TOKEN, 1)
            if end < 0:
                node = Node(self.node_name, '')  # type: Node
                self.grammar.tree__.new_error(
                    node,
                    'END_TOKEN delimiter missing from preprocessor token. '
                    '(Most likely due to a preprocessor bug!)')
                return node, location + 1
            elif end == 0:
                node = Node(self.node_name, '')
                self.grammar.tree__.new_error(
                    node,
                    'Preprocessor-token cannot have zero length. '
                    '(Most likely due to a preprocessor bug!)')
                return node, location + 2
            elif text.find(BEGIN_TOKEN, 1, end) >= 0:
                node = Node(self.node_name, text[len(self.pname) + 1:end])
                self.grammar.tree__.new_error(
                    node,
                    'Preprocessor-tokens must not be nested or contain '
                    'BEGIN_TOKEN delimiter as part of their argument. '
                    '(Most likely due to a preprocessor bug!)')
                return node, location + end
            if text[1:len(self.pname) + 1] == self.pname:
                if self.drop_content:
                    return EMPTY_NODE, location + end + 1
                return Node(self.node_name, text[len(self.pname) + 2:end], True), location + end + 1
        return None, location


def extract_error_code(err_msg: str, err_code: ErrorCode = ERROR) -> Tuple[str, ErrorCode]:
    """Extracts the error-code-prefix from an error message.

    Example::

        >>> msg = '2010:Big mistake!'
        >>> print(extract_error_code(msg))
        ('Big mistake!', 2010)
        >>> msg = "Syntax error at: {1}"
        >>> print(extract_error_code(msg))
        ('Syntax error at: {1}', 1000)
    """
    i = err_msg.find(':')
    if i >= 0:
        err_code_str = err_msg[:i]
        try:
            # if error code has been specified in the string...
            err_code = ErrorCode(err_code_str)
            # ... override tehe err_code parameter
            err_msg = err_msg[i + 1:]
        except ValueError:
            pass
            # # This code does not work, because ErrorCode names
            # # defined on a higher level
            # # are not reachable from within the parse-module
            # if re.match(r'[A-Z_]+', err_code_str):
            #     # assume err_code_str is not a number but
            #     # the name of an ErrorCode-constant
            #     try:
            #         err_code = ErrorCode(globals()[err_code_str])
            #     except (KeyError, ValueError):
            #         pass
    return err_msg, err_code


class ERR(LeafParser):
    """ERR is a pseudo-parser does not consume any text, but adds an error
    message at the current location."""

    def __init__(self, err_msg: str, err_code: ErrorCode = ERROR) -> None:
        super().__init__()
        self.err_msg, self.err_code = extract_error_code(err_msg, err_code)

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.err_msg, self.err_code)
        copy_parser_base_attrs(self, duplicate, memo)
        return duplicate

    def _parse(self, location: cython.int) -> ParsingResult:
        node = Node(ZOMBIE_TAG, '').with_pos(location)
        before = '...' + self._grammar.document__[location - 10:location].replace('\n', '\\n')
        after = self._grammar.document__[location:location + 10].replace('\n', '\\n') + '...'
        message = self.err_msg.format(before, after)
        self._grammar.tree__.new_error(node, message, self.err_code)
        return node, location

    def __repr__(self):
        return f'ERR("{self.err_msg}", {self.err_code})'


########################################################################
#
# Text and Regular Expression parser classes (leaf classes)
#
########################################################################


class Text(NoMemoizationParser):
    """
    Parses plain text strings. (Could be done by RegExp as well, but is faster.)

    Example::

        >>> while_token = Text("while")
        >>> Grammar(while_token)("while").content
        'while'
    """
    assert TOKEN_PTYPE == ":Text"

    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text
        self.len = len(text)

    def __deepcopy__(self, memo):
        duplicate = self.__class__(self.text)
        copy_parser_base_attrs(self, duplicate, memo)
        return duplicate

    @cython.locals(location_=cython.int)
    @cython.returns((object, cython.int))
    def _parse(self, location: cython.int) -> ParsingResult:
        location_ = location + self.len
        self_text = self.text
        if self._grammar.text__[location:location_] == self_text:
            if self.drop_content:
                return EMPTY_NODE, location_
            return Node(self.node_name, self_text, True), location_
            # elif self_text or not self.disposable:
            #     return Node(self.node_name, self_text, True), location_
            # return EMPTY_NODE, location
        return None, location

    def __repr__(self):
        return '`%s`' % abbreviate_middle(self.text, 80)
        # return ("'%s'" if self.text.find("'") <= 0 else '"%s"') % abbreviate_middle(self.text, 80)

    def is_optional(self) -> Optional[bool]:
        return not self.text


class IgnoreCase(Text):
    """
    Parses plain text strings, ignoring the case,
    e.g. "head" == "HEAD" == "Head".
    (Could be done by RegExp as well, but is faster.)

    Example::

        >>> tag = IgnoreCase("head")
        >>> Grammar(tag)("HEAD").content
        'HEAD'
        >>> Grammar(tag)("Head").content
        'Head'
    """

    def __init__(self, text: str) -> None:
        super().__init__(text.lower())
        self.len = len(text)

    @cython.locals(location_=cython.int)
    @cython.returns((object, cython.int))
    def _parse(self, location: cython.int) -> ParsingResult:
        location_ = location + self.len
        comp_text = self._grammar.text__[location:location_]
        if comp_text.lower() == self.text:
            if self.drop_content:
                return EMPTY_NODE, location_
            elif self.text or not self.disposable:
                return Node(self.node_name, comp_text, True), location_
            return EMPTY_NODE, location
        return None, location


class LazyPattern:
    def __init__(self, obj, pattern: str):
        self.pattern = pattern
        self.obj = obj
        self.expired = False

    def match(self, *args, **kwargs):
        assert not self.expired, str(self.obj)
        obj = self.obj
        if hasattr(obj, "lazy_initialization"):
            obj.lazy_initialization(self.pattern)
        else:
            obj.regexp = re.compile(self.pattern)
        self.expired = True
        return obj.regexp.match(*args, **kwargs)

    def __deepcopy__(self, memo):
        raise TypeError


class RegExp(LeafParser):
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
        super().__init__()
        self.regexp = LazyPattern(self, regexp) if isinstance(regexp, str) else regexp

    def __deepcopy__(self, memo):
        # `regex` supports deep copies, but not `re`
        try:
            regexp = copy.deepcopy(self.regexp, memo)
        except TypeError:
            regexp = self.regexp.pattern
        duplicate = self.__class__(regexp)
        copy_parser_base_attrs(self, duplicate, memo)
        return duplicate

    def _parse(self, location: cython.int) -> ParsingResult:
        try:
            match = self.regexp.match(self._grammar.text__, location)
        except KeyboardInterrupt:
            raise KeyboardInterrupt(f'Stopped while processing regular expression:  {self.regexp}'
                f'  at pos {location}:  {self._grammar.text__[location:location + 40]}  ...')
        if match:
            capture = match.group(0)
            if capture or not self.disposable:
                end = match.end()
                if self.drop_content:
                    return EMPTY_NODE, end
                return Node(self.node_name, capture, True), end
            return EMPTY_NODE, location
        return None, location

    def __repr__(self):
        pattern = self.regexp.pattern
        try:
            if pattern == self._grammar.WSP_RE__:
                return '~'
            elif pattern and pattern == self._grammar.COMMENT__:
                return 'comment__'
            elif pattern and pattern == self._grammar.WHITESPACE__:
                return 'whitespace__'
        except (AttributeError, NameError):
            pass
        return '/' + escape_ctrl_chars('%s' % abbreviate_middle(pattern, 118))\
            .replace('/', '\\/') + '/'

    def is_optional(self) -> Optional[bool]:
        if not self.regexp.pattern:
            return True
        return super().is_optional()

    def is_lookahead(self) -> bool:
        """Just a heuristic for the simplemost cases!"""
        return self.regexp.pattern[0:3] in ('(?=', '(?!')



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
    r"""A variant of RegExp that it meant to be used for insignificant whitespace.
    In contrast to RegExp, Whitespace always returns a match. If the defining
    regular expression did not match, an empty match is returned.

    :ivar keep_comments: A boolean indicating whether whitespace
        that contains comments should be kept, even if the self.drop_content
        flag is True. If keep_comments and drop_flag are both true,
        a stretch of whitespace containing a comment will be renamed
        to "comment\__" and whitespace that does not contain any comments
        will be dropped.

    Class Whitespace uses only a very simple (and fast algorithm) to preserve
    comments if needed. Keep in mind the following caveats:

    Caveat 1: If there is a comment, the returned node will contain any leading
        or trailing whitespace as well, not just the comment.

    Caveat 2: If there are several comments, possibly interspersed with whitespace,
        there will still only one flat node named "comment\__" be produced that
        contains all whitespace and all comments in the sequence.

    Example::

        >>> ws = Whitespace(mixin_comment(r'\s+', r'#.*'))
        >>> Grammar(ws)("   # comment").as_sxpr()
        '(root "   # comment")'
        >>> dws = Drop(Whitespace(mixin_comment(r'\s+', r'#.*')))
        >>> Grammar(dws)("   # comment").as_sxpr()
        '(:EMPTY)'
        >>> dws = Drop(Whitespace(mixin_comment(r'\s+', r'#.*'), keep_comments=True))
        >>> Grammar(Synonym(dws))("   # comment").as_sxpr()
        '(root (comment__ "   # comment"))'
        >>> Grammar(Synonym(dws))("   ").as_sxpr()
        '(root)'
        >>> Grammar(dws)("   # comment").as_sxpr()
        '(root "   # comment")'
        >>> Grammar(dws)("   ").as_sxpr()
        '(:EMPTY)'
    """
    assert WHITESPACE_PTYPE == ":Whitespace"

    def __init__(self, regexp, keep_comments: bool = False) -> None:
        super().__init__(regexp)
        self.keep_comments = keep_comments

    def __deepcopy__(self, memo):
        # `regex` supports deep copies, but not `re`
        try:
            regexp = copy.deepcopy(self.regexp, memo)
        except TypeError:
            regexp = self.regexp.pattern
        duplicate = self.__class__(regexp, self.keep_comments)
        copy_parser_base_attrs(self, duplicate, memo)
        return duplicate

    def _parse(self, location: cython.int) -> ParsingResult:
        """For the sake of performance, the _parse-method of class RegExp has
        been repeated, here, rather than being called. Only the last line
        has been changed to retrun an empty match instead of a non-match,
        when the regular expression did not match."""
        try:
            match = self.regexp.match(self._grammar.text__, location)
        except KeyboardInterrupt:
            raise KeyboardInterrupt(f'Stopped while processing Whitespace-RE:  {self.regexp}'
                f'  at pos {location}:  {self._grammar.text__[location:location + 40]}  ...')
        if match:
            capture = match.group(0)
            if capture or not self.disposable:
                end = match.end()
                if self.keep_comments and capture.lstrip():  # there is not only whitesspace, thus a comment...
                    name = "comment__" if self.node_name[0:1] == ":" else self.node_name
                    return Node(name, capture, True), end
                elif self.drop_content:
                    return EMPTY_NODE, end
                return Node(self.node_name, capture, True), end
        return EMPTY_NODE, location

    def is_optional(self) -> Optional[bool]:
        return True  # parser can never fail, like an optional parser

    def __repr__(self):
        return '~'


# TODO: Add character-range-parser?


def update_scanner(grammar: Grammar, leaf_parsers: Dict[str, str]):
    """Updates the "scanner" of a grammar by overwriting the "text" or
    "regex"-fields of some of or all of its leaf parsers with new values.
    This works only for those parsers that are assigned
    to a symbol in the Grammar class.

    :param grammar: The grammar-object for which the leaf parsers
        shall be updated.
    :param leaf_parsers: A mapping of parser names onto strings that
        are interpreted as plain text (if the parser name refers to
        a :py:class:`Text`-parser or as regular expressions, if the parser name
        refers to a :py:class:`RegExp`-parser)

    :raises AttributeError: in case a leaf parser name in the
        dictionary does not exist or does not refer to a :py:class:`Text`
        or :py:class:`RegExp`-parser.
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


MERGED_PTYPE = MIXED_CONTENT_TEXT_PTYPE


class CombinedParser(Parser):
    """Class CombinedParser is the base class for all parsers that
    call ("combine") other parsers. It contains functions for the
    optimization of return values of such parsers
    (i.e. descendants of classes UnaryParser and NaryParser).

    One optimization consists in flattening the tree by eliminating
    anonymous nodes. This is the same as what the function
    DHParser.transform.flatten() does, only at an earlier stage.
    The reasoning is that the earlier the tree is reduced, the less work
    remains to do at all later processing stages. As these typically run
    through all nodes of the syntax tree, this saves memory and presumably
    also time.

    Regarding the latter, however, performing flattening or
    merging during the parsing stage also means that it will be performed
    on all those tree-structures that are discarded later in the parsing
    process, as well.

    Doing flatteining or merging during AST-transformation will ensure
    that it is performed only on those nodes that made it into the
    concrete-syntax-tree. Mergeing, in particular, might become costly
    because of potentially many string-concatenations. But then again,
    the usual depth-first-traversal during AST-transformation will take
    longer, because of the much more verbose tree. (Experiments suggest
    that not much is to be gained by postponing flattening and
    merging to the AST-transformation stage.)

    Another optimization consists in returning the singleton EMPTY_NODE
    for dropped contents, rather than creating a new empty node every
    time empty content is returned. This optimization should always work.
    """

    def __init__(self):
        super().__init__()
        self._return_value = self._return_value_flatten
        self._return_values = self._return_values_flatten

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    def _return_value_no_optimization(self, node: Optional[Node]) -> Node:
        # assert node is None or isinstance(node, Node)
        if self.drop_content:
            return EMPTY_NODE
        if node is None or (node.name[0] == ":" and not node._result):
            if self.disposable:
                return EMPTY_NODE
            return Node(self.node_name, ())
        return Node(self.node_name, node)  # unoptimized code

    def _return_value_flatten(self, node: Optional[Node]) -> Node:
        """
        Generates a return node if a single node has been returned from
        any descendant parsers. Anonymous empty nodes will be dropped.
        If "self" is an unnamed parser, a non-empty descendant node
        will be passed through. If the descendant node is anonymous,
        it will be dropped and only its result will be kept.
        In all other cases a new node will be
        generated, and the descendant node will be its single child.
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

    def _return_values_no_tree_reduction(self, results: Tuple[Node]) -> Node:
        # assert isinstance(results, (list, tuple))
        if self.drop_content or (self.disposable and not results):
            return EMPTY_NODE
        return Node(self.node_name, results)  # unoptimized

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

    @cython.locals(N=cython.int, merge=cython.bint)
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
            # flatten the parse tree
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
                            if grandchild._children or grandchild.name[0] != ':':  # grandchild.anonymous:
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

    @cython.locals(N=cython.int, head_is_anonymous_leaf=cython.bint, tail_is_anonymous_leaf=cython.bint)
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
            # flatten the parse tree
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
                bunch = []
                for nd in nr:
                    head_is_anonymous_leaf = not nd._children and nd.name[0] == ':'  # nd.anonymous
                    if tail_is_anonymous_leaf:
                        if head_is_anonymous_leaf:
                            bunch.append(tail._result)
                            tail: Node = nd
                        else:
                            if bunch:
                                bunch.append(tail._result)
                                new = Node(MERGED_PTYPE, ''.join(bunch), True)
                                new._pos = pos
                                merged.append(new)
                                bunch = []
                            else:
                                merged.append(tail)
                            merged.append(nd)
                    elif head_is_anonymous_leaf:
                        tail = nd
                        pos = tail._pos
                    else:
                        merged.append(nd)
                    tail_is_anonymous_leaf = head_is_anonymous_leaf
                if tail_is_anonymous_leaf:
                    if bunch:
                        bunch.append(tail._result)
                        new = Node(MERGED_PTYPE, ''.join(bunch), True)
                        new._pos = pos
                        merged.append(new)
                    else:
                        merged.append(tail)
                    if len(merged) > 1:
                        return Node(self.node_name, tuple(merged))
                    else:
                        result = merged[0].result
                        if result or not self.disposable:
                            return Node(self.node_name, result)
                        return EMPTY_NODE
                if len(merged) > 1:
                    return Node(self.node_name, tuple(merged))
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

# duplicate this definitions on toplevel for forward-compatibility

NO_TREE_REDUCTION = 0
FLATTEN = 1  # "flatten" vertically    (A (:Text "data"))  -> (A "data")
MERGE_TREETOPS = 2  # "merge" horizontally  (A (:Text "hey ") (:RegExp "you")) -> (A "hey you")
MERGE_LEAVES = 3  #  (A (:Text "hey ") (:RegExp "you") (C "!")) -> (A (:Text "hey you") (C "!"))


def copy_combined_parser_attrs(src: CombinedParser,
                               duplicate: CombinedParser,
                               memo: Dict[int, Any]):
    assert isinstance(src, CombinedParser)
    copy_parser_base_attrs(src, duplicate, memo)
    duplicate._return_value = duplicate.__getattribute__(src._return_value.__name__)
    duplicate._return_values = duplicate.__getattribute__(src._return_values.__name__)


def TreeReduction(root_or_parserlist: Union[Parser, Collection[Parser]],
                  level: int = CombinedParser.FLATTEN) -> Parser:
    """
    Applies tree-reduction level to CombinedParsers either in the collection
    or parsers passed in the first arg or in the graph of interconnected
    parsers originating in the single "roo" parser passed as first argument.
    Returns the root-parser or, if a collection has been passed, the
    PARSER_PLACEHOLDER

    Examples, how tree-reduction works::

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

        >>> root = Series(Text('A'), Text('B'), Text('C').name('important') | Text('D'))
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
    def apply_func(parser: Parser) -> None:
        nonlocal level
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
            else:  # level == CombinedParser.MERGE_LEAVES
                cast(CombinedParser, parser)._return_value = parser._return_value_flatten
                cast(CombinedParser, parser)._return_values = parser._return_values_merge_leaves

    if isinstance(root_or_parserlist, Parser):
        root_parser = root_or_parserlist
        assert isinstance(root_parser, Parser)
        assert level in (CombinedParser.NO_TREE_REDUCTION,
                         CombinedParser.FLATTEN,
                         CombinedParser.MERGE_TREETOPS,
                         CombinedParser.MERGE_LEAVES)
        root_parser.apply(apply_func)
        return root_parser
    else:
        if level != CombinedParser.FLATTEN:
            for p in root_or_parserlist:
                apply_func(p)
        return get_parser_placeholder()


KEEP_COMMENTS_NAME = KEEP_COMMENTS_PTYPE[1:] + '__'
RX_NAMED_GROUPS = LazyRE(r'\(\?P<(:?\w+)>')


def _with_pos(nd: Node, pos: int) -> Node:
    """A faster replacement for Node.with_pos()"""
    nd._pos = pos
    return nd


class SmartRE(CombinedParser):
    r"""
    Regular expression parser that returns a tree with a node for every
    captured group (named as the group or as the number of the group,
    in case it  is not a named group). The space between groups is dropped.

    Example::

        >>> name = SmartRE(r'(?P<christian_name>\w+)\s+(?P<family_name>\w+)').name("name")
        >>> Grammar(name)("Arthur Schopenhauer").as_sxpr()
        '(name (christian_name "Arthur") (family_name "Schopenhauer"))'
        >>> name = SmartRE(r'(?P<christian_name>\w+)(\s+)(?P<family_name>\w+)').name("name")
        >>> Grammar(name)("Arthur Schopenhauer").as_sxpr()
        '(name (christian_name "Arthur") (:RegExp " ") (family_name "Schopenhauer"))'

    EBNF-Notation:  ``/ ... /``

    EBNF-Example:   ``name = /(?P<first_name>\w+)\s+(?P<last_name>\w+)/``
    """
    def __init__(self, pattern,
                 repr_str: str = '') -> None:
        super().__init__()
        self.repr_str = repr_str
        self.groups: Optional[List[Tuple[str, bool]]] = None
        if isinstance(pattern, str):
            self.pattern = pattern
            self.regexp = LazyPattern(self, pattern)
        else:
            self.pattern = pattern.pattern
            self.regexp = pattern
        self.is_lookahead_: Optional[bool] = None

    @cython.locals(i=cython.int)
    def lazy_initialization(self, pattern: str):
        group_names = RX_NAMED_GROUPS.findall(pattern)
        # assert group_names, f"Named group(s) missing in SmartRE: {pattern}"
        names = dict()
        for i, name in enumerate(group_names):
            if name[0:1] == ":":
                alias = name[1:] + '_' * (i + len(group_names) + 4)
            else:
                alias = name + '_' * (i + 2)
            names[alias] = name
            pattern = pattern.replace(f'(?P<{name}>', f'(?P<{alias}>', 1)
        regexp = re.compile(pattern)
        realname = {index: names[alias] for alias, index in regexp.groupindex.items()}
        self.groups = []
        disposables = self.grammar.disposable__
        for i in range(1, regexp.groups + 1):
            name = realname.get(i, ":RegExp")
            self.groups.append((name, is_disposable(name, disposables)))
        pattern = RX_NAMED_GROUPS.sub('(', pattern)
        self.regexp = re.compile(pattern)

        if self.is_lookahead() and self.node_name[:1] == ":":
            self.node_name = ":SmartRE_Lookahead"

    def __deepcopy__(self, memo):
        # `regex` supports deep copies, but not `re`
        try:
            regexp = copy.deepcopy(self.regexp, memo)
        except TypeError:
            regexp = self.pattern
        duplicate = self.__class__(regexp, self.repr_str)
        duplicate.pattern = self.pattern
        duplicate.groups = copy.deepcopy(self.groups, memo)
        duplicate.is_lookahead_ = self.is_lookahead_
        copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    @cython.locals(i=cython.int, disposable=cython.bint)
    def _parse(self, location: cython.int) -> ParsingResult:
        try:
            match = self.regexp.match(self._grammar.text__, location)
        except KeyboardInterrupt as e:
            raise KeyboardInterrupt(f'Stopped while processing regular expression:  {self.regexp}'
                f'  at pos {location}:  {self._grammar.text__[location:location + 40]}  ...') \
                from e
        if match:
            values = match.groups()
            end = match.end()
            if not self.disposable or any((content and len(content)) for content in values):
                if self.drop_content:
                    return EMPTY_NODE, end
                assert self.groups is not None
                results = tuple(_with_pos(Node(name, content), match.start(i))
                                for i, ((name, disposable), content) in enumerate(zip(self.groups, values), start=1)
                                if content is not None
                                   and (((not disposable or content)
                                         and name != KEEP_COMMENTS_PTYPE)
                                        or content.strip()))
                return self._return_values(results), end
            return EMPTY_NODE, end
        return None, location

    def __repr__(self):
        if self.repr_str:
            return self.repr_str
        pattern = self.pattern
        try:
            pattern = pattern.replace(self._grammar.WSP_RE__, '~')
            if self._grammar.COMMENT__:
                pattern = pattern.replace(self._grammar.COMMENT__, 'comment__')
            if self._grammar.WHITESPACE__:
                pattern = pattern.replace(self._grammar.WHITESPACE__, 'whitespace__')
            pattern = pattern.replace('(?:', '(') # .replace('(?P', '(')
            i = len(pattern)
            l = i - 1
            while l < i:
                i = len(pattern)
                pattern = pattern.replace('\\\\', '\\')
                l = len(pattern)
        except (AttributeError, NameError):
            pass
        return '/' + abbreviate_middle(pattern, 118) + '/'

    def is_optional(self) -> Optional[bool]:
        if not self.regexp.pattern:
            return True
        return super().is_optional()

    def is_lookahead(self) -> bool:
        r"""
        Just a heuristic test - not perfect::

            >>> print(SmartRE(r'(?:alpha(?=x))').is_lookahead())
            True
            >>> print(SmartRE(r'(?!alpha)').is_lookahead())
            True
            >>> print(SmartRE(r'(?P<x>\w+)(?=\d)\d+').is_lookahead())
            False
            >>> print(SmartRE(r'(?=(?::)(?:\s*))').is_lookahead())
            True
        """
        if self.is_lookahead_ is not None:
            return self.is_lookahead_
        pattern = RX_NAMED_GROUPS.sub('(', self.regexp.pattern).replace('(?:', '(')
        if pattern.lstrip('(')[0:2] in ('?=', '?!'):
            return True
        mb = None
        i = pattern.rfind('(?=')
        if i > 0:
            mb = matching_brackets(pattern, '(', ')', )
            mb.reverse()
            rs_pattern = pattern.rstrip(')')
            for a, b in mb:
                if a == i:
                    if len(rs_pattern) <= b:
                        self.is_lookahead_ = True
                        return True
        i = pattern.rfind('(?!')
        if i > 0:
            if mb is None:
                mb = matching_brackets(pattern, '(', ')', )
                mb.reverse()
            rs_pattern = pattern.rstrip(')')
            for a, b in mb:
                if a == i:
                    if len(rs_pattern) <= b:
                        self.is_lookahead_ = True
                        return True
        return False



CustomParseFunc: TypeAlias = Callable[[StringView], Optional[Node]]


class CustomParser(CombinedParser):
    """
    A wrapper for a simple custom parser function defined by the user::

        >>> def parse_magic_number(rest: StringView) -> Node:
        ...     return Node('', rest[:4]) if rest.startswith('1234') else EMPTY_NODE
        >>> parser = Grammar(CustomParser(parse_magic_number))
        >>> result = parser('1234')
        >>> print(result.as_sxpr())
        (root "1234")
        >>> result = parser('abcd')
        >>> for e in result.errors:  print(e)
        1:1: Error (1040): Parser "root" stopped before end, at: »abcd« Terminating parser.
    """

    def __init__(self, parse_func: CustomParseFunc) -> None:
        super().__init__()
        assert callable(parse_func), f"Not a CustomParseFunc: {parse_func}"
        self.parse_func: CustomParseFunc = parse_func

    def __deepcopy__(self, memo):
        parse_func = copy.deepcopy(self.parse_func, memo)
        duplicate = self.__class__(parse_func)
        copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    def _parse(self, location: cython.int) -> ParsingResult:
        try:
            node = self.parse_func(self._grammar.document__[location:])
        except Exception as e:
            node = Node(self.node_name, '').with_pos(location)
            self.grammar.tree__.new_error(node, f"Custom parser {self.parse_func} crashed: {e}",
                                          CUSTOM_PARSER_FAILURE)
        if node is None:
            return None, location
        if node is EMPTY_NODE:
            return EMPTY_NODE, location + node.strlen()
        else:
            if node.name and not node.name[0:1] == ':':
                save_name = node.name
            else:
                save_name = self.node_name
            node.name = ":"
            node = self._return_value(node)
            if node is not EMPTY_NODE and node is not None:
                node.name = save_name
            return node, location + node.strlen()

    def __repr__(self):
        pf = self.parse_func
        pfname = getattr(pf, '__name__',
                         getattr(getattr(pf, '__class__', None), '__name__',
                                 str(pf)))
        return f'Custom({pfname})'


def Custom(custom_parser: Union[Parser, CustomParseFunc, str]) -> Parser:
    if isinstance(custom_parser, Parser):
        return cast(Parser, custom_parser)
    elif callable(custom_parser):
        return CustomParser(custom_parser)
    elif isinstance(custom_parser, str):
        custom_parser = globals().get(custom_parser, custom_parser)
        if callable(custom_parser):
            return CustomParser(cast(CustomParseFunc, custom_parser))
        else:
            raise AssertionError(f"Not a CustomParseFunc: {custom_parser}")
    else:
        raise ValueError(f'Illegal parameter {custom_parser} of type {type(custom_parser)}')


########################################################################
#
# One-ary parsers
#
########################################################################


class UnaryParser(CombinedParser):
    """
    Base class of all unary parsers, i.e. parser that contains
    one and only one other parser, like the optional parser for example.

    The UnaryOperator base class supplies "__deepcopy__()" and
    methods for unary parsers. The "__deepcopy__()"-method needs
    to be overwritten, however, if the constructor of a derived class
    has additional parameters.
    """

    def __init__(self, parser: Parser) -> None:
        super().__init__()
        # assert isinstance(parser, Parser), str(parser)
        self.parser = parser  # type: Parser
        self.sub_parsers = frozenset({parser})

    def __deepcopy__(self, memo):
        parser = copy.deepcopy(self.parser, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(parser)
            copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate


class LateBindingUnary(UnaryParser):
    """Superclass for late-binding unary parsers. LateBindingUnary only stores
    the name of a parser upon object creation. This name is resolved at the time
    when the late-binding-parser-object is connected to the grammar.

    EXPERIMENTAL !!!

    A possible use case is a custom parser derived from LateBindingUnary that
    calls another parser without having to worry about whether the called
    parser has already been defined earlier in the Grammar-class.

    LateBindingUnary is not to be confused with :py:class:`Forward` and should
    not be abused for recursive parser calls either!"""

    def __init__(self, parser_name: Union[str, Parser]) -> None:
        assert parser_name
        if isinstance(parser_name, Parser):
            parser = parser_name
            assert parser.effective_pname(), \
                f'LateBindingUnary must bet initialized with named parser, not {parser}!'
            super().__init__(parser)
            self.parser_name = parser.effective_pname()
            self.sub_parsers = frozenset({parser})
        else:
            self.parser_name = parser_name
            super().__init__(get_parser_placeholder())
            self._sub_parsers = frozenset()

    def __deepcopy__(self, memo):
        if is_parser_placeholder(self.parser):
            duplicate = self.__class__(self.parser_name)
            copy_combined_parser_attrs(self, duplicate, memo)
        else:
            _ = copy.deepcopy(self.parser, memo)
            try:
                duplicate = memo[id(self)]
            except KeyError:
                duplicate = self.__class__(self.parser_name)
                duplicate.sub_parsers = frozenset({duplicate.parser})
                copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    def _resolve_parser_name(self) -> Parser:
        assert self.parser
        if is_parser_placeholder(self.parser):
            if is_grammar_placeholder(self._grammar) and not isclass(self._grammar):
                raise UninitializedError(
                    f'Grammar hast not yet been set in LateBindingUnary "{self}"')
            # self.parser = getattr(self.grammar, self.parser_name)
            self.parser = self._grammar.__dict__[self.parser_name]
            assert isinstance(self.parser, Parser), f'"{self.parser_name}" is not a parser!'
        return self.parser

    def effective_pname(self) -> str:
        return self.parser_name if is_parser_placeholder(self.parser) else self.parser.effective_pname()

    @property
    def sub_parsers(self) -> FrozenSet[Parser]:
        if not self._sub_parsers:
            parser = self._resolve_parser_name()
            if is_parser_placeholder(parser):
                self._sub_parsers = frozenset()
            else:
                self._sub_parsers = frozenset({self._resolve_parser_name()})
        return self._sub_parsers

    @sub_parsers.setter
    def sub_parsers(self, f: FrozenSet[Parser]):
        """Sets sub‑parsers unless placeholder is present"""
        if len(f) == 1 and is_parser_placeholder(list(f)[0]):
            self._sub_parsers = frozenset()
        else:
            self._sub_parsers = f


class Option(UnaryParser):
    r"""
    Parser "Option" always matches, even if its child-parser
    did not match.

    If the child-parser did not match "Option" returns a node
    with no content and does not move forward in the text.

    If the child-parser did match, "Option" returns a node
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

    # def __init__(self, parser: Parser) -> None:
    #     super().__init__(parser)

    def _parse(self, location: cython.int) -> ParsingResult:
        node, location = self.parser(location)
        return self._return_value(node), location

    def is_optional(self) -> Optional[bool]:
        return True

    def __repr__(self):
        return '[' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + ']'

    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        if self.parser.is_optional():
            errors.append(self.static_error(
                "Redundant nesting of optional or empty parser in " + self.location_info(),
                OPTIONAL_REDUNDANTLY_NESTED_WARNING))
        return errors


def infinite_loop_warning(parser, node, location):
    assert isinstance(parser, UnaryParser) or isinstance(parser, NaryParser)
    if location < parser._grammar.document_length__ \
            and get_config_value('infinite_loop_warning'):
        if node is EMPTY_NODE:  node = Node(EMPTY_PTYPE, '').with_pos(location)
        dsl_error(parser, node,
                  f'Repeating parser did not make any progress! Was inner parser '
                  f'of "{parser.symbol}" really intended to capture empty text?',
                  INFINITE_LOOP_WARNING)


class ZeroOrMore(Option):
    r"""
    "ZeroOrMore" applies a parser repeatedly as long as this parser
    matches. Like :py:class:`Option` the "ZeroOrMore" parser always matches. In
    case of zero repetitions, the empty match "((), text)" is returned.

    Examples::

        >>> sentence = ZeroOrMore(RE(r'\w+,?')) + TKN('.')
        >>> Grammar(sentence)('Wo viel der Weisheit, da auch viel des Grämens.').content
        'Wo viel der Weisheit, da auch viel des Grämens.'
        >>> Grammar(sentence)('.').content  # an empty sentence also matches
        '.'
        >>> forever = ZeroOrMore(RegExp('(?=.)|$'))
        >>> Grammar(forever)('')  # infinite loops will automatically be broken
        Node('root', '')

    Except for the end of file a warning will be emitted, if an infinite-loop
    is detected.

    EBNF-Notation: ``{ ... }``

    EBNF-Example:  ``sentence = { /\w+,?/ } "."``
    """

    @cython.locals(n=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        results: Tuple[Node, ...] = ()
        n = location - 1
        while True:  # location > n:
            n = location
            node, location = self.parser(location)
            if node is None:
                break
            if node._result or node.name[0] != ':': # drop anonymous empty nodes
                results += (node,)
            if location <= n:
                infinite_loop_warning(self, node, location)
                break
        nd = self._return_values(results)  # type: Node
        return nd, location

    def __repr__(self):
        return '{' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.pname else self.parser.repr) + '}'

    # def static_analysis(self) -> List[AnalysisError]:
    #     errors = super().static_analysis()
    #     if self.parser.is_optional():
    #         errors.append(self.static_error(
    #             "Optional or empty parsers should not be nested inside repeating parsers: "
    #             + self.location_info(), BADLY_NESTED_OPTIONAL_PARSER))
    #     return errors


class OneOrMore(UnaryParser):
    r"""
    "OneOrMore" applies a parser repeatedly as long as this parser
    matches. Other than :py:class:`ZeroOrMore` which always matches, at least
    one match is required by "OneOrMore".

    Examples::

        >>> sentence = OneOrMore(RE(r'\w+,?')) + TKN('.')
        >>> Grammar(sentence)('Wo viel der Weisheit, da auch viel des Grämens.').content
        'Wo viel der Weisheit, da auch viel des Grämens.'
        >>> str(Grammar(sentence)('.'))  # an empty sentence also matches
        ' <<< Error on "." | Parser root->/\\\\w+,?/ did not match: ».« >>> '
        >>> forever = OneOrMore(RegExp('(?=.)|$'))
        >>> Grammar(forever)('')  # infinite loops will automatically be broken
        Node('root', '')

    Except for the end of file a warning will be emitted, if an infinite-loop
    is detected.

    EBNF-Notation: ``{ ... }+``

    EBNF-Example:  ``sentence = { /\w+,?/ }+``
    """
    @cython.locals(n=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        results: Tuple[Node, ...] = ()
        # text_ = text  # type: StringView
        match_flag: bool = False
        n = location - 1
        while True:
            n = location
            node, location = self.parser(location)
            if node is None:
                break
            match_flag = True
            if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                results += (node,)
            if location <= n:
                infinite_loop_warning(self, node, location)
                break
        if not match_flag:
            return None, location
        nd = self._return_values(results)  # type: Node
        return nd, location  # text_

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


def to_interleave(parser: Parser) -> Parser:
    """Converts a :py:class:`Counted`-parser into an :py:class:`Interleave`-parser. Any other
    parser is simply passed through."""
    if isinstance(parser, Counted):
        return Interleave(cast(Counted, parser).parser,
                          repetitions=[cast(Counted, parser).repetitions])
    return parser


class Counted(UnaryParser):
    """Counted applies a parser for a number of repetitions within a given range, i.e.
    the parser must at least match the lower bound number of repetitions, and it can
    at most match the upper bound number of repetitions.

    Examples::

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
        super().__init__(parser)
        assert repetitions[0] <= repetitions[1]
        self.repetitions = repetitions  # type: Tuple[int, int]

    def __deepcopy__(self, memo):
        parser = copy.deepcopy(self.parser, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(parser, self.repetitions)
            copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    @cython.locals(location_=cython.int)
    def _parse(self, location: cython.int):
        results: Tuple[Node, ...] = ()
        location_ = location
        for _ in range(self.repetitions[0]):
            node, location = self.parser(location)
            if node is None:
                return None, location_
            if node._result or node.name[0] != ':':
                results += (node,)
            if location_ >= location:
                infinite_loop_warning(self, node, location)
                break  # avoid infinite loop
            location_ = location
        for _ in range(self.repetitions[1] - self.repetitions[0]):
            node, location = self.parser(location)
            if node is None:
                break
            if node._result or node.name[0] != ':':
                results += (node,)
            if location_ >= location:
                infinite_loop_warning(self, node, location)
                break  # avoid infinite loop
            location_ = location
        return self._return_values(results), location

    def is_optional(self) -> Optional[bool]:
        if self.repetitions[0] == 0:
            return True
        else:
            return None

    def __repr__(self):
        return self.parser.repr + "{%i,%i}" % self.repetitions

    @cython.locals(a=cython.int, b=cython.int)
    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        a, b = self.repetitions
        if a < 0 or b < 0 or a > b or a > INFINITE or b > INFINITE:
            errors.append(self.static_error(
                'Repetition count [a=%i, b=%i] for parser %s violates requirement '
                '0 <= a <= b <= infinity (%i)' % (a, b, str(self), INFINITE),
                BAD_REPETITION_COUNT))
        if self.repetitions == (1, 1):
            errors.append(self.static_error(
                "Repetition count from 1 to 1 renders Counted-parser redundant: "
                + self.location_info(), REDUNDANT_PARSER_WARNING))
        if self.parser.is_optional() and self.repetitions != (1, 1):
            errors.append(self.static_error(
                "Optional parsers should not be nested inside repeating parsers: "
                + self.location_info(), BADLY_NESTED_OPTIONAL_PARSER))
        return errors


########################################################################
#
# N-ary parsers
#
########################################################################


class NaryParser(CombinedParser):
    """
    Base class of all Nary parsers, i.e. parser that
    contains one or more other parsers, like the alternative
    parser for example.

    The NaryOperator base class supplies "__deepcopy__()" and methods
    for n-ary parsers. The "__deepcopy__()"-method needs to be overwritten,
    however, if the constructor of a derived class takes additional
    parameters.
    """

    def __init__(self, *parsers: Parser) -> None:
        super().__init__()
        # assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        if len(parsers) == 0:
            raise ValueError('Cannot initialize NaryParser with zero parsers.')
        # assert all(isinstance(p, Parser) for p in parsers)
        self.parsers = parsers  # type: Tuple[Parser, ...]
        self.sub_parsers = frozenset(parsers)

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(*parsers)
            copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate


def starting_string(parser: Parser) -> str:
    """If the parser starts with a fixed string, this will be returned.
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

    @cython.locals(location_=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        for parser in self.parsers:
            node, location_ = parser(location)
            if node is not None:
                return self._return_value(node), location_
        return None, location

    def __repr__(self):
        if self.pname:
            return ' | '.join(parser.repr for parser in self.parsers)
        return '(' + ' | '.join(parser.repr for parser in self.parsers) + ')'

    # The following operator definitions add syntactical sugar, so one can write:
    # ``RE('\d+') + RE('\.') + RE('\d+') | RE('\d+')`` instead of:
    # ``Alternative(Series(RE('\d+'), RE('\.'), RE('\d+')), RE('\d+'))``

    def __or__(self, other: Parser) -> 'Alternative':
        return Alternative(self, other)

    def __ror__(self, other: Parser) -> 'Alternative':
        return Alternative(other, self)

    def __ior__(self, other: Parser) -> 'Alternative':
        return Alternative(self, other)

    def is_optional(self) -> Optional[bool]:
        if (self.parsers and self.parsers[-1].is_optional()) \
                or any(p.is_optional() for p in self.parsers):
            return True
        return super().is_optional()

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

        def does_preempt(start, parser) -> bool:
            if isinstance(parser, ForwardBase):
                if self in parser.descendants():
                    # In case of recursive parsers, the test is not reliable!
                    return False
            cst = self.grammar(start, parser, complete_match=False)
            self.grammar._reset__()
            return not cst.errors and cst.strlen() >= 1

        for i in range(2, len(self.parsers)):
            fixed_start = starting_string(self.parsers[i])
            if fixed_start:
                for k in range(i):
                    if (not isinstance(self.parsers[k], ForwardBase)  # TODO: find a more fine-grained check for recursive parsers
                            and does_preempt(fixed_start, self.parsers[k])):
                        errors.append(self.static_error(
                            "Parser-specification Error in " + self.location_info()
                            + "\nAlternative %i will never be reached, because its starting-"
                            'string "%s" is already captured by earlier alternative %i !'
                            % (i + 1, fixed_start, k + 1), BAD_ORDER_OF_ALTERNATIVES))
        return errors


@cython.locals(n=cython.int, i=cython.int)
def longest_match(strings: List[str], text: Union[StringView, str], n: int = 1) -> str:
    """Returns the longest string from a given list of strings that
    matches the beginning of text. Examples::

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
    import bisect
    i = bisect.bisect_left(strings, head)
    if i >= len(strings) or (i == 0 and not strings[0].startswith(head)):
        return ''
    match = longest_match(strings[i:], text, n + 1)
    if match:  return match
    if head == strings[i]:  return head
    return ''


NO_MANDATORY = 2**30


class ErrorCatchingNary(NaryParser):
    r"""ErrorCatchingNary is the parent class for N-ary parsers that can be
    configured to fail with a parsing error in case of a non-match,
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

    In the following example, "Series" is a descendant of "ErrorCatchingNary"::

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
        '3. <<< Error on "" | /[0-9]+/ expected by parser \'fraction\', but END OF FILE found instead! >>> '

    In this example, the first item of the fraction, i.e. the decimal dot,
    is non-mandatory, because only the parser with an index of one or more
    are mandatory ("mandator=1"). In this case this is only the regular
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
        super().__init__(*parsers)
        length = len(self.parsers)
        if mandatory < 0:
            mandatory += length
        self.mandatory = mandatory  # type: int

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(*parsers, mandatory=self.mandatory)
            copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    def get_reentry_point(self, location: cython.int) -> Tuple[int, Node]:
        """Returns a tuple of integer index of the closest reentry point and a Node
        capturing all text from "rest" up to this point or "(-1, None)" if no
        reentry-point was found. If no reentry-point was found or the
        skip-list ist empty, -1 and a zombie-node are returned.
        """
        text_ = self.grammar.document__[location:]
        skip = tuple(self.grammar.skip_rules__.get(self.symbol, []))
        if skip:
            gr = self._grammar
            reloc, zombie = reentry_point(text_, skip, gr.comment_rx__, gr.reentry_search_window__,
                                          f'{self.symbol}_skip')
            return reloc, zombie
        return -1, Node(ZOMBIE_TAG, '')

    def mandatory_violation(self,
                            location: cython.int,
                            failed_on_lookahead: bool,
                            expected: str,
                            reloc: int,
                            err_node: Node) -> Tuple[Error, int]:
        """
        Chooses the right error message in case of a mandatory violation and
        returns an error with this message, an error node, to which the error
        is attached, and the text segment where parsing is to continue.

        This is a helper function that abstracts functionality that is
        needed by the Interleave-parser as well as the Series-parser.

        :param location: the point, where the mandatory violation happened.
                As usual, the string view represents the remaining text from
                this point.
        :param failed_on_lookahead: True if the violating parser was a
                Lookahead-Parser.
        :param expected:  the expected (but not found) text at this point.
                position where the error occurred to a suggested
                reentry-position.
        :param reloc: A position offset that represents the reentry point for
                parsing after the error occurred.
        :param err_node: The node to which the mandatory violation error shall
                be attached. Usually, this is the skip-node so that the error
                will be located exactly where the violation occurred.

        :return:   a tuple of an error object and a location for the
                continuation the parsing process
        """
        grammar = self._grammar
        text_ = self.grammar.document__[location:]

        err_node._pos = -1  # bad hack to avoid error in case position is re-set
        err_node.with_pos(location)  # for testing artifacts
        error_code = MANDATORY_CONTINUATION
        L = len(text_)
        if L > 10:
            found = '»' + text_[:10].replace('\n', '\\n') + '...' + '«'
        elif L > 0:
            found = '»' + text_[:10].replace('\n', '\\n') + '«'
        else:
            found = "END OF FILE"
        sym = self.symbol
        err_msgs = self.grammar.error_messages__.get(sym, [])
        for search, message in err_msgs:
            is_func = callable(search)           # search rule is a function: StringView -> bool
            is_str = isinstance(search, str)     # search rule is a simple string
            is_rxs = not is_func and not is_str  # search rule is a regular expression
            if (is_func and cast(Callable, search)(text_)) \
                    or (is_rxs and text_.match(search)) \
                    or (is_str and text_.startswith(cast(str, search))):
                try:
                    msg, error_code = extract_error_code(
                        message.format(expected, found), MANDATORY_CONTINUATION)
                    break
                except (ValueError, KeyError, IndexError) as e:
                    error = Error("Malformed error format string »{}« leads to »{}«"
                                  .format(message, str(e)),
                                  location, MALFORMED_ERROR_STRING)
                    grammar.tree__.add_error(err_node, error)
        else:
            repr_expected = repr(expected)[1:-1]
            if len(repr_expected) > 2 and (repr_expected[0] + repr_expected[-1]) in ('""', "''"):
                repr_expected = repr_expected[1:-1]
            msg = f'{repr_expected} expected by parser {repr(sym)}, but {found} found instead!'
        if failed_on_lookahead and not text_:
            if grammar.start_parser__ is grammar.root_parser__:
                error_code = MANDATORY_CONTINUATION_AT_EOF
            else:
                error_code = MANDATORY_CONTINUATION_AT_EOF_NON_ROOT
        error = Error(msg, location, error_code,
                      length=max(self.grammar.ff_pos__ - location, 1))
        grammar.tree__.add_error(err_node, error)
        if reloc >= 0:
            # signal error to tracer directly, because this error is not raised!
            grammar.most_recent_error__ = ParserError(
                self, err_node, reloc, location, error, first_throw=False)
        return error, location + max(reloc, 0)

    def static_analysis(self) -> List['AnalysisError']:
        errors = super().static_analysis()
        msg = []
        length = len(self.parsers)
        # sym = self.symbol
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


class Series(ErrorCatchingNary):
    r"""
    Matches if each of a series of parsers matches exactly in the order of
    the series.

    Example::

        >>> variable_name = RegExp(r'(?!\d)\w') + RE(r'\w*')
        >>> Grammar(variable_name)('variable_1').content
        'variable_1'
        >>> str(Grammar(variable_name)('1_variable'))
        ' <<< Error on "1_variable" | Parser root->/(?!\\\\d)\\\\w/ did not match: »1_variable« >>> '

    EBNF-Notation: ``... ...``    (sequence of parsers separated by a blank or new line)

    EBNF-Example:  ``series = letter letter_or_digit``
    """
    # RX_ARGUMENT = re.compile(r'\s(\S)')

    def __init__(self, *parsers: Parser,
                 mandatory: int = NO_MANDATORY) -> None:
        super().__init__(*parsers, mandatory=mandatory)
        if mandatory >= len(self.parsers):
            self._parse_proxy = self._quick_parse

    def set_proxy(self, proxy: Optional[ParseFunc]):
        if self.mandatory >= len(self.parsers) and proxy is None:
            self._parse_proxy = self._quick_parse
        else:
            if self._parse_proxy == self._quick_parse:
                self._parse_proxy = self._parse  # to avoid assertion error in the super()-call
            super(Series, self).set_proxy(proxy)

    @cython.locals(location_=cython.int)
    def _quick_parse(self, location: cython.int) -> ParsingResult:
        """faster Series-parsing-method if mandatory marker is not used."""
        results = []  # type: List[Node]
        location_ = location
        for parser in self.parsers:
            node, location_ = parser(location_)
            if node is None:
                return None, location
            if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                results.append(node)
        return self._return_values(tuple(results)), location_

    @cython.locals(location_=cython.int, pos=cython.int, reloc=cython.int, mandatory=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        results = []  # type: List[Node]
        location_ = location
        error = None  # type: Optional[Error]
        mandatory = self.mandatory  # type: int
        for pos, parser in enumerate(self.parsers):
            node, location_ = parser(location_)
            if node is None:
                if pos < mandatory:
                    return None, location
                else:
                    parser_str = str(parser) if is_context_sensitive(parser) else parser.repr
                    qq = parser_str[0] + parser_str[-1]
                    if parser.node_name[0] == ":" and qq in ('""', "''", "``"):
                        parser_str = f'»{parser_str[1:-1]}«'
                    reloc, node = self.get_reentry_point(location_)
                    lookahead = isinstance(parser, Lookahead) \
                                or (isinstance(parser, SmartRE) and parser.pattern[0:3] in ("(?=", "(?!"))
                    error, location_ = self.mandatory_violation(
                        location_, lookahead, parser_str, reloc, node)
                    # check if parsing of the series can be resumed somewhere
                    if reloc >= 0:
                        nd, location_ = parser(location_)  # try current parser again
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
        ret_node = self._return_values(tuple(results))  # type: Node
        if error and reloc < 0:  # no worry: reloc is always defined when error is True
            # parser will be moved forward, even if no relocation point has been found
            raise ParserError(self, ret_node.with_pos(location_),
                              location_ - location,
                              location, error, first_throw=True)
        return ret_node, location_

    def __repr__(self):
        L = len(self.parsers)
        if L == 2 or L == 3 and isinstance(self.parsers[2], Whitespace):
            if isinstance(self.parsers[1], Whitespace) and isinstance(self.parsers[0], Text):
                return f'"{cast(Text, self.parsers[0]).text}"'
            if isinstance(self.parsers[0], Whitespace) and isinstance(self.parsers[1], Text):
                return f'"{cast(Text, self.parsers[1]).text}"'
        return " ".join([parser.repr for parser in self.parsers[:self.mandatory]]
                        + (['§'] if self.mandatory != NO_MANDATORY else [])
                        + [parser.repr for parser in self.parsers[self.mandatory:]])

    # The following operator definitions add syntactical sugar, so one can write:
    # ``RE('\d+') + Optional(RE('\.\d+)`` instead of ``Series(RE('\d+'), Optional(RE('\.\d+))``

    def __add__(self, other: Parser) -> 'Series':
        return Series(self, other)

    def __radd__(self, other: Parser) -> 'Series':
        return Series(other, self)

    def __iadd__(self, other: Parser) -> 'Series':
        return Series(self, other)

    def is_optional(self) -> Optional[bool]:
        if all(p.is_optional() for p in self.parsers):
            return True
        return super().is_optional()


class Interleave(ErrorCatchingNary):
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
        super().__init__(*parsers, mandatory=mandatory)
        assert all(0 <= r[0] <= r[1] for r in repetitions)
        if len(repetitions) == 0:
            repetitions = [(1, 1)] * len(parsers)
        elif len(parsers) != len(repetitions):
            raise ValueError("Number of repetition-tuples unequal number of sub-parsers!")
        self.repetitions = list(repetitions)  # type: List[Tuple[int, int]]
        self.non_mandatory = frozenset(parsers[i] for i in range(min(mandatory, len(parsers))))
        self.parsers_set = frozenset(self.parsers)

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(*parsers,
                                       mandatory=self.mandatory,
                                       repetitions=self.repetitions)
            copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    @cython.locals(location_=cython.int, location__=cython.int, i=cython.int, reloc=cython.int)
    def _parse(self, location: cython.int):
        results = ()  # type: Tuple[Node, ...]
        location_ = location  # type: int
        counter = [0] * len(self.parsers)
        consumed = set()  # type: MutableSet[Parser]
        error = None  # type: Optional[Error]
        while True:
            # there is an order of testing, but no promise about the order of testing, here!
            for i, parser in enumerate(self.parsers):
                if parser not in consumed:
                    node, location__ = parser(location_)
                    if node is not None:
                        if node._result or not node.name[0] == ':':  # node.anonymous:  # drop anonymous empty nodes
                            results += (node,)
                            # location_ = location__
                        counter[i] += 1
                        if counter[i] >= self.repetitions[i][1]:
                            consumed.add(parser)
                        break
            else:
                for i, parser in enumerate(self.parsers):
                    if counter[i] >= self.repetitions[i][0]:
                        consumed.add(parser)
                if self.non_mandatory <= consumed:
                    if len(consumed) == len(self.parsers_set):  # faster than: comsumed == self.parsers_set
                        break
                else:
                    return None, location
                reloc, err_node = self.get_reentry_point(location_)
                expected = ' ° '.join([parser.repr for parser in self.parsers])
                error, location__ = self.mandatory_violation(location_, False, expected, reloc, err_node)
                results += (err_node,)
                if reloc < 0:
                    break
            if location__ <= location_:
                infinite_loop_warning(self, node, location)
                break  # infinite loop protection
            location_ = location__
        nd = self._return_values(results)  # type: Node
        if error and reloc < 0:  # no worry: reloc is always defined when error is True
            # parser will be moved forward, even if no relocation point has been found
            raise ParserError(self, nd.with_pos(location),
                              location_ - location,
                              location, error, first_throw=True)
        return nd, location_

    def is_optional(self) -> Optional[bool]:
        return all(r[0] == 0 for r in self.repetitions)

    def __repr__(self):
        def rep(parser: Parser) -> str:
            return '(' + parser.repr + ')' \
                if isinstance(parser, Series) or isinstance(parser, Alternative) else parser.repr

        return ' ° '.join(rep(parser) for parser in self.parsers)

    def __mul__(self, other: Parser) -> 'Interleave':
        return Interleave(self, other)

    def __rmul__(self, other: Parser) -> 'Interleave':
        return Interleave(other, self)

    def __imul__(self, other: Parser) -> 'Interleave':
        return Interleave(self, other)

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
    def _parse(self, location: cython.int) -> ParsingResult:
        node, _ = self.parser(location)
        if self.match(node is not None):
            return (EMPTY_NODE if self.disposable else Node(self.node_name, '', True)), location
        else:
            return None, location

    def __repr__(self):
        return '&' + self.parser.repr

    def static_analysis(self) -> List[AnalysisError]:
        errors = super().static_analysis()
        # Whitespaces are excluded in the following, because they are also used as
        # placeholders for macros in which case the error message would be confusing
        if self.parser.is_optional() and not isinstance(self.parser, Whitespace):
            errors.append(AnalysisError(self.pname, self, Error(
                "Lookahead %s does not make sense with optional parser %s!"
                % (self.node_name, str(self.parser)),
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
        return _negative_match(self._grammar, bool_value)


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
        self.regexp = None
        self.text = ''  # type: str
        if isinstance(p, RegExp):
            self.regexp = LazyPattern(self, cast(RegExp, p).regexp.pattern)
        else:  # p is of type Text
            assert isinstance(p, Text)
            self.text = cast(Text, p).text
        super().__init__(parser)

    @cython.locals(start=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        start = self._grammar.document_length__ - location
        backwards_text = self._grammar.reversed__[start:]
        if self.regexp is None:  # assert self.text is not None
            does_match = backwards_text[:len(self.text)] == self.text
        else:  # assert self.regexp is not None
            does_match = backwards_text.match(self.regexp)
        if self.match(does_match):
            if self.drop_content:
                return EMPTY_NODE, location
            return Node(self.node_name, '', True), location
        return None, location

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
        return _negative_match(self._grammar, bool_value)


########################################################################
#
# Context-sensitive parsers
#
########################################################################

@lru_cache(maxsize=256)
def is_context_sensitive(parser: Parser) -> bool:
    """Returns True, is "parser" is a context-sensitive parser
    or calls a context-sensitive parser."""
    return any(isinstance(p, ContextSensitive) for p in parser.descendants())


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
    (see :py:meth:`Parser.__call__` and :py:meth:`Forward.__call__`). As
    a consequence the parsing time cannot be assumed to be strictly
    proportional to the size of the document, anymore. Therefore,
    it is recommended to use context-sensitive-parsers sparingly.
    """

    __call__ = NoMemoizationParser.__call__

    def _rollback_location(self, location: cython.int, location_: cython.int) -> cython.int:
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
        rollback-location as in :py:meth:`Forward.__call__` where a formula like::

            location = (grammar.last_rb__loc__ + int(text._len == rest._len)

        determines whether memoization should be blocked.
        """
        return location if location != location_ else location-1


class Capture(ContextSensitive):
    """
    Applies the contained parser and, in case of a match, saves the result
    in a variable. A variable is a stack of values associated with the
    contained parser's name. This requires the contained parser to be named.
    """
    def __init__(self, parser: Parser, zero_length_warning: bool = True) -> None:
        super().__init__(parser)
        self.zero_length_warning: bool = zero_length_warning
        self._can_capture_zero_length: Optional[bool] = None

    def __deepcopy__(self, memo):
        symbol = copy.deepcopy(self.parser, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(symbol, self.zero_length_warning)
            copy_combined_parser_attrs(self, duplicate, memo)
            duplicate._can_capture_zero_length = self._can_capture_zero_length
        return duplicate

    @property
    def can_capture_zero_length(self) -> bool:
        if self._can_capture_zero_length is None:
            self._can_capture_zero_length = self.parser._parse(0)[0] is not None
        return cast(bool, self._can_capture_zero_length)

    def _rollback(self):
        return self._grammar.variables__[self.pname].pop()

    @cython.locals(location_=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        node, location_ = self.parser(location)
        if node is not None:
            assert self.pname, """Tried to apply an unnamed capture-parser!"""
            assert not self.parser.drop_content, \
                "Cannot capture content from parsers that drop content!"
            self._grammar.variables__[self.pname].append(node.content)
            self._grammar.push_rollback__(self._rollback_location(location, location_), self._rollback)
            return self._return_value(node), location_
        else:
            return None, location

    def __repr__(self):
        return self.parser.repr

    def static_analysis(self) -> List[AnalysisError]:
        errors = super().static_analysis()
        if not self.pname:
            errors.append(AnalysisError(self.pname, self, Error(
                'Capture only works as named parser! Error in parser: ' + str(self),
                0, CAPTURE_WITHOUT_PARSERNAME
            )))
        if self.parser.apply(lambda p: p.drop_content):
            errors.append(AnalysisError(self.pname, self, Error(
                'Captured symbol "%s" contains parsers that drop content, '
                'which can lead to unintended results!' % (self.pname or str(self)),
                0, CAPTURE_DROPPED_CONTENT_WARNING
            )))
        if self.zero_length_warning:
            node, _ = self.parser._parse(0)
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


MatchVariableFunc: TypeAlias = Callable[[Union[StringView, str], List[str]], Optional[str]]
# (text, stack) -> value, where:
# text is the following text for be parsed
# stack is a stack of stored variables (for a particular symbol)
# and the return value is the matched text (which can be the empty string) or
# None, if no match occurred

# Match functions, the name of which starts with 'optional_', must never return
# None, but should return the empty string if no match occurs.
# Match functions, the name of which does not start with 'optional_', should
# on the contrary always return "None" if no match occurs!


def last_value(text: Union[StringView, str], stack: List[str]) -> Optional[str]:
    """Matches "text" with the most recent value on the capture stack.
    This is the default case when retrieving captured substrings."""
    try:
        value = stack[-1]
        return value if text.startswith(value) else None
    except IndexError:
        return None


def optional_last_value(text: Union[StringView, str], stack: List[str]) -> Optional[str]:
    """Matches "text" with the most recent value on the capture stack or
    with the empty string, i.e. "optional_match" never returns "None" but
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
    "Retrieve" and the :py:class:`Pop` parser.)
    The constructor parameter "symbol" determines which variable is
    used.

    :ivar parser: The name of the parser that has stored the value
        to be retrieved, in other words: "the observed parser".
        (class Retrieve reuses the instance variable "parser" of its
        superclass Unary with a slightly different semantics.)
    :ivar match: a procedure through which the processing of the
        retrieved symbols is channeled. In the simple most case, it merely
        returns the last string stored by the observed parser. This can
        be (mis-)used to execute any kind of semantic action.
    """

    def __init__(self, symbol: Parser, match_func: Optional[MatchVariableFunc] = None) -> None:
        assert isinstance(symbol, Capture)
        super().__init__(symbol)
        self.match = match_func if match_func else last_value

    def __deepcopy__(self, memo):
        symbol = copy.deepcopy(self.parser, memo)
        try:
            duplicate = memo[id(self)]
        except KeyError:
            duplicate = self.__class__(symbol, self.match)
            copy_combined_parser_attrs(self, duplicate, memo)
        return duplicate

    @property
    def symbol_pname(self) -> str:
        """Returns the watched symbol's pname, properly, i.e. even in cases
        where the symbol's parser is shielded by a Forward-parser"""
        return self.parser.effective_pname()

    def get_node_name(self) -> str:
        """Returns a name for the retrieved node. If the Retrieve-parser
        has a node-name, this overrides the node-name of the retrieved symbol's
        parser."""
        if self.disposable or not self.node_name:
            return self.parser.effective_pname()
            # if self.parser.pname:
            #     return self.parser.name
            # # self.parser is a Forward-Parser, so pick the name of its encapsulated parser
            # return cast(ForwardBase, self.parser).parser.name
        return self.node_name

    @cython.locals(location_=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        # auto-capture on first use if symbol was not captured before
        if len(self._grammar.variables__[self.symbol_pname]) == 0:
            node, location_ = self.parser(location)   # auto-capture value
            if node is None:
                # set last_rb__loc__ to avoid memoizing of retrieved results
                self._grammar.push_rollback__(
                    self._rollback_location(location, location_), lambda: None)
                return None, location_
        node, location_ = self.retrieve_and_match(location)
        # set last_rb__loc__ to avoid memoizing of retrieved results
        self._grammar.push_rollback__(
            self._rollback_location(location, location_), lambda: None)
        return node, location_

    def __repr__(self):
        return ':' + self.parser.repr

    def retrieve_and_match(self, location: cython.int) -> ParsingResult:
        """
        Retrieves variable from stack through the match function passed to
        the class' constructor and tries to match the variable's value with
        the following text. Returns a Node containing the value or "None"
        accordingly.
        """
        # "or self.parser.parser.pname" needed, because Forward-Parsers do not have a pname
        text = self._grammar.document__[location:]
        try:
            stack = self._grammar.variables__[self.symbol_pname]
            value = self.match(text, stack)
        except (KeyError, IndexError):
            tn = self.get_node_name()
            if self.match.__name__.startswith('optional_'):
                # returns a None match if parser is optional but there was no value to retrieve
                return None, location
            else:
                node = Node(tn, '', True).with_pos(location)
                dsl_error(self, node, "'{self.symbol_pname}' undefined or exhausted.",
                          UNDEFINED_RETRIEVE)
                return node, location
        if value is None:
            return None, location
        elif self.drop_content:
            return EMPTY_NODE, location + len(value)
        return Node(self.get_node_name(), value), location + len(value)


class Pop(Retrieve):
    """
    Matches if the following text starts with the value of a particular
    variable. As a variable in this context means a stack of values,
    the last value will be compared with the following text. Other
    than the :py:class:`Retrieve`-parser, the "Pop"-parser removes the value
    from the stack in case of a match.

    The constructor parameter "symbol" determines which variable is
    used.
    """
    def __init__(self, symbol: Parser, match_func: Optional[MatchVariableFunc] = None) -> None:
        super().__init__(symbol, match_func)

    def reset(self):
        super(Pop, self).reset()
        self.values = []

    # def __deepcopy__(self, memo):
    #     symbol = copy.deepcopy(self.parser, memo)
    #     try:
    #         duplicate = memo[id(self)]
    #     except KeyError:
    #         duplicate = self.__class__(symbol, self.match)
    #         copy_combined_parser_attrs(self, duplicate, memo)
    #         duplicate.values = self.values[:]
    #     return duplicate

    def _rollback(self):
        self._grammar.variables__[self.symbol_pname].append(self.values.pop())

    @cython.locals(location_=cython.int)
    def _parse(self, location: cython.int) -> ParsingResult:
        node, location_ = self.retrieve_and_match(location)
        if node is not None and not id(node) in self._grammar.tree__.error_nodes:
            self.values.append(self._grammar.variables__[self.symbol_pname].pop())
            self._grammar.push_rollback__(self._rollback_location(location, location_), self._rollback)
        else:
            # set last_rb__loc__ to avoid memoizing of retrieved results
            self._grammar.push_rollback__(self._rollback_location(location, location_), lambda: None)
        return node, location_

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

    Otherwise, the first line could not be represented by any parser
    class, in which case it would be unclear whether the parser
    RegExp('\d\d\d\d') carries the name 'JAHRESZAHL' or 'jahr'.
    """
    def __init__(self, parser: Parser) -> None:
        super().__init__(parser)

    def _parse(self, location: cython.int) -> ParsingResult:
        node, location = self.parser(location)
        if node is not None:
            if self.drop_content:
                return EMPTY_NODE, location
            if not self.disposable:
                if node is EMPTY_NODE:
                    return Node(self.node_name, '', True), location
                if node.name[0] == ':':  # node.anonymous:
                    # eliminate anonymous child-node on the fly
                    # node.name = self.node_name   # Big mistake: this can spoil the memo-cache
                    return Node(self.node_name, node._result), location
                else:
                    return Node(self.node_name, (node,)), location
        return node, location

    def __str__(self):
        return self.pname + (' = ' if self.pname else '') + self.parser.repr

    def __repr__(self):
        return self.pname or self.parser.repr


class ForwardBase(UnaryParser):
    """Base class for forward parsers that implement (differen kinds of)
    left recursion handling. This base clase does not implement any kind of
    left recursion handling but simply forwards the parser call. In case of
    left-recursive grammars this leads to an infinite loop the will be
    stopped by the Python interpreter with a RecursionError.

    :ivar cycle_reached: Flag for the private function __cycle_guard() that
        allows to call a functions that runs recursively through the sub-parsers
        without getting caught in an infinite loop.
    """

    def __init__(self):
        super().__init__(get_parser_placeholder())
        self.cycle_reached: bool = False
        self.sub_parsers = frozenset()

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        memo[id(self)] = duplicate  # prevent infinite recursion during next deepcopy() call
        copy_parser_base_attrs(self, duplicate, memo)
        parser = copy.deepcopy(self.parser, memo)
        duplicate.parser = parser
        duplicate.sub_parsers = frozenset({parser})
        return duplicate

    def __call__(self, location: cython.int) -> ParsingResult:
        # This will lead to an infinite loop in case of left-recursion
        # and raise a RecursionError
        return self.parser(location)

    def set_proxy(self, proxy: Optional[ParseFunc]):
        """"set_proxy" has no effects on Forward-objects!"""
        return

    def __cycle_guard(self, func, alt_return):
        """
        Returns the value of "func()" or "alt_return" if a cycle has
        been reached (which can happen if "func" calls methods of
        child parsers).
        """
        if self.cycle_reached:
            return alt_return
        else:
            self.cycle_reached = True
            ret = func()
            self.cycle_reached = False
            return ret

    def effective_pname(self) -> str:
        """Returns the parser's pname. In the case of a Forward-parser,
        returns parser.parser.pname."""
        return self.parser.pname or self.pname

    def __repr__(self):
        return self.__cycle_guard(lambda: repr(self.parser), '...')

    def __str__(self):
        return self.__cycle_guard(lambda: str(self.parser), '...')

    @property
    def repr(self) -> str:
        """Returns the parser's name if it has a name or "repr(self)" if not."""
        return self.parser.pname if self.parser.pname else self.__repr__()

    def set(self, parser: Parser):
        """Sets the parser to which the calls to this Forward-object
        shall be delegated.
        """
        assert not isinstance(parser, ForwardBase)
        self.parser = parser
        self.sub_parsers = frozenset({parser})
        if self.pname and not parser.pname:  parser.name(self.pname, self.disposable)
        if not parser.drop_content:  parser.disposable = self.disposable
        self.drop_content = parser.drop_content
        self.pname = ""


FWTracerMemo: TypeAlias = Callable[['ForwardBase', int, ParsingResult], None]
FWTracerInit: TypeAlias = Callable[['ForwardBase', int], Any]
FWTracerLoop: TypeAlias = Callable[[Any], None]
FWTracerDone: TypeAlias = Callable[[Any, ParsingResult], None]


def nil_tracer(*args, **kwargs) -> None:
    return None


SEED = (FrozenNode(':SEED', ''), 0)


class Forward(ForwardBase):
    r"""
    Forward allows declaring a parser before it is actually defined.
    Forward declarations are needed for parsers that are recursively
    nested, e.g.::

        >>> class Arithmetic(Grammar):
        ...     r'''
        ...     expression =  term  { ("+" | "-") term }
        ...     term       =  factor  { ("*" | "/") factor }
        ...     factor     =  INTEGER | "("  expression  ")"
        ...     INTEGER    =  /\d+/~
        ...     '''
        ...     expression = Forward()
        ...     INTEGER    = RE('\\d+')
        ...     factor     = INTEGER | TKN("(") + expression + TKN(")")
        ...     term       = factor + ZeroOrMore((TKN("*") | TKN("/")) + factor)
        ...     expression.set(term + ZeroOrMore((TKN("+") | TKN("-")) + term))
        ...     root__     = expression

    :ivar seed:  Mapping of location to a List of ParsingResults that were
        returned in the course of the iterative expansion (grow-phase) of the
        left-recursive cycle. The first element is always the SEED-sentinel.
    :ivar versions: Mapping of location to a List of ParsingResults. It will be
        filled with the list at self.seed[location] in case backtracking
        through earlier (shorter) matches than the longest match might be needed
        due to an "overspill" (parsing too far because of greedily picking the
        longest match).
    :ivar farthest: Keeps track of the farthest location reached by this parser.
        This is needed for checking if an overspill has occured.

    The Forward parser class contains an algorithm to handle left-recursive
    grammars. See it's __call__()-method. The algorithm handles direct and indirect
    left-recursion, but not interwoven left-recursion!
    """

    def __init__(self):
        super().__init__()
        # self.parser = get_parser_placeholder  # type: Parser
        self.set_fwtracer(nil_tracer, nil_tracer, nil_tracer, nil_tracer)

    def reset(self):
        super(Forward, self).reset()
        assert not self.pname, "Forward-Parsers mustn't have a name!"
        self.seed: Dict[int, List[ParsingResult]] = dict()  # aka recursion counter
        self.versions: Dict[int, List[ParsingResult]] = dict()
        self.iteration = dict()
        self.farthest = -1

    @cython.locals(ldepth=cython.int, rb_stack_size=cython.int)
    def __call__(self, location: cython.int) -> ParsingResult:
        """
        Overrides :py:meth:`Parser.__call__`, because Forward is not an independent parser
        but merely redirects the call to another parser. Other than parser
        :py:class:`Synonym`, which might be a meaningful marker for the syntax tree,
        parser Forward should never appear in the syntax tree.

        :py:meth:`Forward.__call__` also takes care of (most of) the left recursion
        handling. In order to do so, it (unfortunately) has to duplicate some code
        from :py:meth:`Parser.__call__`.

        The algorithm for avoiding infinite loops in left-recursive grammars roughly follows:
        https://medium.com/@gvanrossum_83706/left-recursive-peg-grammars-65dab3c580e1
        See also:
        https://tinlizzie.org/VPRIPapers/tr2007002_packrat.pdf
        """
        grammar = self._grammar
        history_tracking = grammar.history_tracking__
        visited = self.visited  # using local variable for better performance

        # roll back variable-changing operation if the parser backtracks
        # to a position before the variable-changing operation occurred
        if location <= grammar.last_rb__loc__:
            grammar.rollback_to__(location)

        if not grammar.use_memo__ and (versions := self.versions.get(location, None)):
            # rotate versions
            last = versions.pop()
            versions.insert(0, last)
            if last[0] is SEED:
                grammar.use_memo__ = location or -1
                # assert len(versions) > 1
                return versions[-1][0] if len(versions) > 1 else (None, location)  # len(version) > 1 implies verions[-1][0] is SEED
                # TODO: Do I need to worry about grammar.ff_pos__, here?
            else:
                return last[0]  # versions[0][0]
        elif location in visited:
            # Sorry, no history recording in case of memoized results!
            # if history_tracking:  self.tracer_memo(self, location, visited[location])
            return visited[location]

        # check if a seed has been planted for the seed and grow algorithm

        sapling, iter = self.seed.get(location, [(None, -1)])[-1]
        if sapling and iter == self.iteration[location]:  # TODO: Could the requirement iter == self.iteration[location] lead to infinite recursion?
            grammar.suspend_memoization__ = id(self)
            if history_tracking:  self.tracer_memo(self, location, sapling)
            return (None, location) if sapling is SEED else sapling

        save_suspend_memoization = grammar.suspend_memoization__
        grammar.suspend_memoization__ = False
        save_ff_pos = grammar.ff_pos__
        grammar.ff_pos__ = min(location, save_ff_pos)
        save_use_memo = grammar.use_memo__
        grammar.use_memo__ = -1
        rb_stack_size = len(grammar.rollback__)

        self.seed[location] = [(SEED, 0)]  # fail on the first recursion
        result: ParsingResult = None, location

        while grammar.ff_pos__ < grammar.document_length__:
            iteration = 0
            self.iteration[location] = 0
            next_result: ParsingResult = self._parse_proxy(location)  # self.parser(location)
            if grammar.use_memo__ or next_result[0] is not None:
                if location in visited:
                    result = visited[location]
                if history_tracking: tracing_data = self.tracer_init(self, location)

                while next_result[1] > result[1] and location in self.seed:
                    result = next_result
                    if grammar.ff_pos__ >= grammar.document_length__:
                        break
                    grammar.suspend_memoization__ = False
                    rb_stack_size = len(grammar.rollback__)
                    iteration += 1
                    self.iteration[location] = iteration
                    self.seed[location].append((result, iteration))
                    next_result = self._parse_proxy(location)  # self.parser(location)
                    if history_tracking: self.tracer_loop(tracing_data)
                if history_tracking: self.tracer_done(tracing_data, result)

                # Since the result of the last parser call ("next_result") is discarded,
                # any variables captured by this call should be "rolled back", too.
                while len(grammar.rollback__) > rb_stack_size:
                    _, rb_func = grammar.rollback__.pop()
                    rb_func()
                    grammar.last_rb__loc__ = grammar.rollback__[-1][0] \
                        if grammar.rollback__ else -2

                if result[0] is None:
                    if next_result[0] is None:
                        if grammar.use_memo__ <= location < self.farthest \
                                and any(loc >= location and len(saps) > 1 for loc, saps in self.seed.items()):
                            grammar.use_memo__ = 0
                            grammar.ff_pos__ = save_ff_pos
                            continue  # TODO:  Could this lead to an infinite loop?
                    else:
                        # make sure that a parser that treats the water
                        # ("der auf der Stelle tritt") matches nevertheless,
                        # see test_parse.TestInfiniLoopRecursion.test_parser_that_treads_the_water()
                        result = next_result

            versions = self.seed.get(location, None)
            if versions is not None and len(versions) > 1:
                self.versions[location] = versions
                if location > self.farthest:  self.farthest = location

            while versions:
                r, iter = versions[-1]
                if iter != self.iteration[location]:
                    break
                versions.pop()

            if versions is not None and (not versions or versions[-1][0] is SEED):
                del self.seed[location]
            break

        # both checks in the following are necessary:
        # 1. id(self)-check in order not to interfere with interwoven recursive parser calls
        # 2. isinstance check for referenced parsers that are not in fact recursive
        if grammar.suspend_memoization__ == id(self) or isinstance(grammar.suspend_memoization__, bool):
            grammar.suspend_memoization__ = save_suspend_memoization  #  = is_context_sensitive(self.parser)
        if location in visited and result[1] < visited[location][1]:
            result = visited[location]
        elif not grammar.suspend_memoization__:
            visited[location] = result
        grammar.ff_pos__ = max(grammar.ff_pos__, save_ff_pos)
        grammar.use_memo__ = save_use_memo
        self.iteration[location] = -1
        return result

    def _parse(self, location: cython.int) -> ParsingResult:
        return self.parser(location)

    def set_proxy(self, proxy: Optional[ParseFunc]):
        super(Forward, self).set_proxy(proxy)
        # if proxy is None:
        #     self.set_fwtracer(nil_tracer, nil_tracer, nil_tracer, nil_tracer)

    def set_fwtracer(self, memo: FWTracerMemo, init: FWTracerInit, loop: FWTracerLoop, done: FWTracerDone):
        """Adds a seed-and-grow loop-tracer. The tracer can be disabled by calling either
        "set_fwtracer(nil_tracer, nil_tracer, nil_tracer)" or "set_proxy(None)"
        """
        assert memo is not nil_tracer(), "Use nil_memo_tracer not nil_memo as first argumen!"
        self.tracer_memo: FWTracerMemo = memo
        self.tracer_init: FWTracerInit = init
        self.tracer_loop: FWTracerLoop = loop
        self.tracer_done: FWTracerDone = done


###############################################################################
#
# Older, simpler and more limited versions of the left-recursion agorithm
#
###############################################################################


class SimpleForwardRecursive(ForwardBase):
    r"""This is the "old" (DHParser version < 2.0) version of the Forward
    parser class. The left-recursion algorithm handles direct and indirect
    left-recursion but fails on interwoven and monotonic left-recursion!

    :ivar recursion_counter:  Mapping of places to how often the parser
        has already been called recursively at this place. This
        is needed to implement left recursion. The number of
        calls becomes irrelevant once a result has been memoized.
    """

    def reset(self):
        super().reset()
        self.recursion_counter: Dict[int, int] = dict()
        assert not self.pname, f"Forward-Parsers mustn't have a name! ({self.pname})"

    @cython.locals(ldepth=cython.int, rb_stack_size=cython.int)
    def __call__(self, location: cython.int) -> ParsingResult:
        """
        Overrides :py:meth:`Parser.__call__`, because Forward is not an independent parser
        but merely redirects the call to another parser. Other than parser
        :py:class:`Synonym`, which might be a meaningful marker for the syntax tree,
        parser Forward should never appear in the syntax tree.

        :py:meth:`Forward.__call__` also takes care of (most of) the left recursion
        handling. In order to do so it (unfortunately) has to duplicate some code
        from :py:meth:`Parser.__call__`.

        The algorithm for avoiding infinite loops in left-recursive grammars roughly follows:
        https://medium.com/@gvanrossum_83706/left-recursive-peg-grammars-65dab3c580e1
        See also:
        https://tinlizzie.org/VPRIPapers/tr2007002_packrat.pdf
        """
        grammar = self._grammar

        # rollback variable-changing operation if the parser backtracks
        # to a position before the variable-changing operation occurred
        if location <= grammar.last_rb__loc__:
            grammar.rollback_to__(location)

        # if the location has already been visited by the current parser, return the saved result
        visited = self.visited  # using local variable for better performance
        if location in visited:
            # Sorry, no history recording in case of memoized results!
            return visited[location]

        if location in self.recursion_counter:
            depth = self.recursion_counter[location]
            if depth == 0:
                grammar.suspend_memoization__ = id(self)
                result = None, location
            else:
                self.recursion_counter[location] = depth - 1
                result = self.parser(location)
                self.recursion_counter[location] = depth  # allow moving back and forth
        else:
            self.recursion_counter[location] = 0  # fail on the first recursion
            save_suspend_memoization = grammar.suspend_memoization__
            grammar.suspend_memoization__ = False
            history_tracking = grammar.history_tracking__
            history_pointer = len(grammar.history__) if history_tracking else 0

            result = self.parser(location)

            if result[0] is not None:
                # keep calling the (potentially left-)recursive parser and increase
                # the recursion depth by 1 for each call as long as the length of
                # the match increases.
                last_history_state = grammar.history__[history_pointer:len(grammar.history__)] \
                    if history_tracking else []
                depth = 1
                while True:
                    self.recursion_counter[location] = depth
                    grammar.suspend_memoization__ = False
                    rb_stack_size = len(grammar.rollback__)
                    if history_tracking:
                        grammar.history__ = grammar.history__[:history_pointer]
                    # reduplication of error messages will be caught by nodetree.RootNode.add_error()
                    # saving and restoring the errors-messages state on each iteration presupposes
                    # that error messages will be recreated every time, which, however, does not
                    # happen because of memoization. (This is a downside of global error-reporting
                    # in contrast to attaching error-messages locally to the node where they
                    # occurred. Big topic...)
                    # don't carry error/resumption-messages over to the next iteration
                    # grammar.most_recent_error__ = None
                    next_result = self.parser(location)

                    # discard next_result if it is not the longest match and return
                    if next_result[1] <= result[1]:  # also true, if no match
                        # Since the result of the last parser call ("next_result") is discarded,
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
                        if history_tracking:
                            grammar.history__ = grammar.history__[:history_pointer] + last_history_state
                        # record = grammar.history__[-1]
                        # if record.call_stack[-1] == (self.parser.pname, location):
                        #     record.text = result[1]
                        #     delta = len(text) - len(result[1])
                        #     assert record.node.name != ':None'
                        #     record.node.result = text[:delta]
                        break

                    if history_tracking:
                        last_history_state = grammar.history__[history_pointer:len(grammar.history__)]
                    result = next_result
                    depth += 1
            # grammar.suspend_memoization__ = save_suspend_memoization \
            #     or location <= (grammar.last_rb__loc__ + int(text._len == result[1]._len))
            # both checks in the following are necessary:
            # 1. id(self)-check in order not to interfere with interwoven recursive parser calls
            # 2. isinstance check for referenced parsers that are not in fact recursive
            if grammar.suspend_memoization__ == id(self) or isinstance(grammar.suspend_memoization__, bool):
                grammar.suspend_memoization__ = save_suspend_memoization  #  = is_context_sensitive(self.parser)
        if not grammar.suspend_memoization__:
            visited[location] = result
        return result


class SimpleForwardIterative(ForwardBase):
    r"""This is a more straight-forward quasi-iterative version of the "old"
    Forward parser class. The left-recursion algorithm handles direct and
    indirect left-recursion but fails on interwoven and monotonic left-recursion!

    This version of the parser class is experimental has hardly been tested!!!

    :ivar recursion_counter:  Mapping of places to how often the parser
            has already been called recursively at this place. This
            is needed to implement left recursion. The number of
            calls becomes irrelevant once a result has been memoized.
    """

    def reset(self):
        super(UnaryParser, self).reset()
        self.recursion_counter: Dict[int, int] = dict()
        assert not self.pname, "Forward-Parsers mustn't have a name!"

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        memo[id(self)] = duplicate  # prevent infinite recursion during next deepcopy() call
        copy_parser_base_attrs(self, duplicate, memo)
        parser = copy.deepcopy(self.parser, memo)
        duplicate.parser = parser
        duplicate.sub_parsers = frozenset({parser})
        return duplicate

    @cython.locals(ldepth=cython.int, rb_stack_size=cython.int)
    def __call__(self, location: cython.int) -> ParsingResult:
        """
        Overrides :py:meth:`Parser.__call__`, because Forward is not an independent parser
        but merely redirects the call to another parser. Other than parser
        :py:class:`Synonym`, which might be a meaningful marker for the syntax tree,
        parser Forward should never appear in the syntax tree.

        :py:meth:`Forward.__call__` also takes care of (most of) the left recursion
        handling. In order to do so it (unfortunately) has to duplicate some code
        from :py:meth:`Parser.__call__`.

        The algorithm for avoiding infinite loops in left-recursive grammars roughly follows:
        https://medium.com/@gvanrossum_83706/left-recursive-peg-grammars-65dab3c580e1
        See also:
        https://tinlizzie.org/VPRIPapers/tr2007002_packrat.pdf
        """
        grammar = self._grammar

        # roll back variable-changing operation if the parser backtracks
        # to a position before the variable-changing operation occurred
        if location <= grammar.last_rb__loc__:
            grammar.rollback_to__(location)

        # if the location has already been visited by the current parser, return the saved result
        visited = self.visited  # using local variable for better performance
        if location in visited:
            # Sorry, no history recording in case of memoized results!
            if self.recursion_counter[location]:
                grammar.suspend_memoization__ = id(self)
            return visited[location]

        if location in self.recursion_counter:
            grammar.suspend_memoization__ = id(self)
            return None, location

        self.recursion_counter[location] = True  # fail on the first recursion
        save_suspend_memoization = grammar.suspend_memoization__
        grammar.suspend_memoization__ = False
        history_tracking = grammar.history_tracking__
        history_pointer = len(grammar.history__) if history_tracking else 0
        rb_stack_size = len(grammar.rollback__)
        last_history_state = []

        result = None, location
        next_result = self.parser(location)

        while next_result[1] > result[1]:
            result = next_result
            grammar.suspend_memoization__ = False
            rb_stack_size = len(grammar.rollback__)
            if history_tracking:
                last_history_state.extend(grammar.history__[history_pointer:len(grammar.history__)])
                grammar.history__ = grammar.history__[:history_pointer]
            visited[location] = result
            next_result = self.parser(location)

        if result[0] is None:
            if next_result[0] is not None:
                # make sure that a parser that treats the water ("der auf der Stelle tritt") matches nevertheless
                result = next_result
        elif history_tracking:
            grammar.history__ = grammar.history__[:history_pointer] + last_history_state

        self.recursion_counter[location] = False
        # Since the result of the last parser call ("next_result") is discarded,
        # any variables captured by this call should be "rolled back", too.
        while len(grammar.rollback__) > rb_stack_size:
            _, rb_func = grammar.rollback__.pop()
            rb_func()
            grammar.last_rb__loc__ = grammar.rollback__[-1][0] \
                if grammar.rollback__ else -2

        # both checks in the following are necessary:
        # 1. id(self)-check in order not to interfere with interwoven recursive parser calls
        # 2. isinstance check for referenced parsers that are not in fact recursive
        if grammar.suspend_memoization__ == id(self) or isinstance(grammar.suspend_memoization__, bool):
            grammar.suspend_memoization__ = save_suspend_memoization  #  = is_context_sensitive(self.parser)
        # if location in visited and result[1] < visited[location][1]:
        #     result = visited[location]
        if not grammar.suspend_memoization__:
            visited[location] = result
        return result
