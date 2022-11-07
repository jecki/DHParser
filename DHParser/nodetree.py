# nodetree.py - node-tree classes for DHParser
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


"""Module ``nodetree`` encapsulates the functionality for creating and handling
trees of nodes, in particular, syntax-trees. This includes serialization
and deserialization of node-trees, navigating and searching node-trees as well
as annotating node-trees with attributes and error messages.

``nodetree`` can also be seen as a document-tree-library
for handling any kind of XML-data. In contrast to
`Elementtree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_
and `lxml <https://lxml.de/>`_, nodetree maps mixed content to dedicated nodes,
which simplifies the programming of algorithms that run on the data stored
in the (XML-)tree."""

from __future__ import annotations

import bisect
import copy
import functools
import json
import random
import sys
from typing import Callable, cast, Iterator, Sequence, List, Set, AbstractSet, \
    Union, Tuple, Container, Optional, Dict, Any

if sys.version_info >= (3, 6, 0):
    OrderedDict = dict
else:
    from collections import OrderedDict

from DHParser.configuration import get_config_value, ALLOWED_PRESET_VALUES
from DHParser.error import Error, ErrorCode, ERROR, PARSER_STOPPED_BEFORE_END, \
    add_source_locations, SourceMapFunc, has_errors, only_errors
from DHParser.preprocess import gen_neutral_srcmap_func
from DHParser.stringview import StringView  # , real_indices
from DHParser.toolkit import re, linebreaks, line_col, JSONnull, \
    validate_XML_attribute_value, fix_XML_attribute_value, lxml_XML_attribute_value, \
    abbreviate_middle, TypeAlias

try:
    import cython
    cint: TypeAlias = cython.int
except NameError:
    cint: TypeAlias = int
except ImportError:
    import DHParser.externallibs.shadow_cython as cython
    cint: TypeAlias = int


__all__ = ('WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'MIXED_MODE_TEXT_PTYPE',
           'REGEXP_PTYPE',
           'EMPTY_PTYPE',
           'LEAF_PTYPES',
           'ZOMBIE_TAG',
           'PLACEHOLDER',
           'Path',
           'ResultType',
           'StrictResultType',
           'ChildrenType',
           'NodeMatchFunction',
           'PathMatchFunction',
           'NodeSelector',
           'PathSelector',
           'ANY_NODE',
           'NO_NODE',
           'LEAF_NODE',
           'ANY_PATH',
           'NO_PATH',
           'LEAF_PATH',
           'Node',
           'content_of',
           'strlen_of',
           'validate_token_sequence',
           'has_token',
           'add_token',
           'remove_token',
           'eq_tokens',
           'has_token_on_attr',
           'add_token_to_attr',
           'remove_token_from_attr',
           'has_class',
           'add_class',
           'remove_class',
           'prev_path',
           'next_path',
           'zoom_into_path',
           'leaf_path',
           'prev_leaf_path',
           'next_leaf_path',
           'PickChildFunction',
           'FIRST_CHILD',
           'LAST_CHILD',
           'select_path_if',
           'select_path',
           'pick_path',
           'foregoing_str',
           'ensuing_str',
           'select_from_path_if',
           'select_from_path',
           'pick_from_path',
           'find_common_ancestor',
           'pp_path',
           'path_sanity_check',
           'insert_node',
           'split',
           'deep_split',
           'can_split',
           'leaf_paths',
           'reset_chain_ID',
           'ContentMapping',
           'FrozenNode',
           'EMPTY_NODE',
           'tree_sanity_check',
           'RootNode',
           'DHParser_JSONEncoder',
           'parse_sxpr',
           'parse_xml',
           'parse_json',
           'deserialize',
           'flatten_sxpr',
           'flatten_xml')


#######################################################################
#
# parser-related definitions
#
#######################################################################


WHITESPACE_PTYPE = ':Whitespace'
TOKEN_PTYPE = ':Text'
# Node name for plain text in XML-elements that contain both children and plain text
MIXED_MODE_TEXT_PTYPE = ':Text'
REGEXP_PTYPE = ':RegExp'
EMPTY_PTYPE = ':EMPTY'
LEAF_PTYPES = frozenset({WHITESPACE_PTYPE, TOKEN_PTYPE, MIXED_MODE_TEXT_PTYPE,
                         REGEXP_PTYPE, EMPTY_PTYPE})

ZOMBIE_TAG = "ZOMBIE__"


#######################################################################
#
# support functions
#
#######################################################################


# support functions for searching and navigating trees #################


# criteria for finding nodes:
# - node itself (equality)
# - name
# - one of several names
# - a function Node -> bool  or  Path -> bool, respectively
re_pattern: TypeAlias = Any
NodeSelector: TypeAlias = Union['Node', str, Container[str], Callable, int, re_pattern]
PathSelector: TypeAlias = Union['Node', str, Container[str], Callable, int, re_pattern]

Path: TypeAlias = List['Node']
NodeMatchFunction: TypeAlias = Callable[['Node'], bool]
PathMatchFunction: TypeAlias = Callable[[Path], bool]

def affirm(whatever) -> bool:
    return True

def deny(whatever) -> bool:
    return False

ANY_NODE = affirm
NO_NODE = deny
ANY_PATH = affirm
NO_PATH = deny


def LEAF_NODE(nd: Node) -> bool:
    return not nd._children


def LEAF_PATH(path: Path) -> bool:
    return not path[-1].children


def create_match_function(criterion: NodeSelector) -> NodeMatchFunction:
    """
    Creates a node-match-function (Node -> bool) for the given criterion
    that returns True, if the node passed to the function matches the
    criterion.

    ==================== ===================================================
         criterion                         type of match
    ==================== ===================================================
    id (int)             object identity
    Node                 object identity
    FrozenNode           equality of tag name, string content and attributes
    tag name (str)       equality of tag name only
    multiple tag names   equality of tag name with one of the given names
    pattern (re.Pattern) full match of content with pattern
    match function       function returns `True`
    ==================== ===================================================

    :param criterion: Either a node, the id of a node, a frozen node,
        a name or a container (usually a set) of multiple tag names,
        a regular expression pattern or another match function.

    :returns: a match-function (Node -> bool) for the given criterion.
    """
    if isinstance(criterion, int):
        return lambda nd: id(nd) == criterion
    elif isinstance(criterion, FrozenNode):
        return lambda nd: nd.equals(criterion, ignore_attr_order=True)
    elif isinstance(criterion, Node):
        return lambda nd: nd == criterion
        # return lambda nd: nd.equals(criterion)  # may yield wrong results for Node.index()
    elif isinstance(criterion, str):
        return lambda nd: nd.name == criterion
    elif callable(criterion):
        annotations = criterion.__annotations__.items()
        if len(annotations) > 2:
            raise ValueError(f'Signature of callable criterion must be f(nd: Node) -> bool, '
                             f'not {list(annotations)}')
        for name, typ in annotations:
            if typ is not Node and typ != 'Node' and name != 'return':
                raise ValueError(f'First argument of callable criterion '
                                 f'{criterion} must have type Node, not {typ}!')
            break  # only read the first argument
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda nd: nd.name in cast(Container, criterion)
    elif str(type(criterion)) in ("<class '_regex.Pattern'>", "<class 're.Pattern'>"):
        return lambda nd: criterion.fullmatch(nd.content)
    raise TypeError("Criterion %s of type %s does not represent a legal criteria type"
                    % (repr(criterion), type(criterion)))


def create_path_match_function(criterion: PathSelector) -> PathMatchFunction:
    """
    Creates a path-match-function (Path -> bool) for the given
    criterion that returns True, if the last node in the path passed
    to the function matches the criterion.

    See :py:func:`create_match_function()` for a description of the possible
    criteria and their meaning.

    :param criterion: Either a node, the id of a node, a frozen node,
        a name or a container (usually a set) of multiple tag names,
        a regular expression pattern or another match function.

    :returns: a match-function (Prail -> bool) for the given criterion.
    """
    if isinstance(criterion, int):
        return lambda trl: id(trl[-1]) == criterion
    elif isinstance(criterion, FrozenNode):
        return lambda trl: trl[-1].equals(criterion, ignore_attr_order=True)
    elif isinstance(criterion, Node):
        return lambda trl: trl[-1] == criterion
        # return lambda trl[-1]: trl[-1].equals(criterion)  # may yield wrong results
    elif isinstance(criterion, str):
        return lambda trl: trl[-1].name == criterion
    elif callable(criterion):
        is_node_match_func = False
        for _, typ in criterion.__annotations__.items():
            if typ is Node or typ == 'Node':
                is_node_match_func = True
            break
        if is_node_match_func:
            return lambda path: criterion(path[-1])
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda trl: trl[-1].name in cast(Container, criterion)
    elif str(type(criterion)) in ("<class '_regex.Pattern'>", "<class 're.Pattern'>"):
        return lambda trl: criterion.fullmatch(trl[-1].content)
    raise TypeError("Criterion %s of type %s does not represent a legal criteria type"
                    % (repr(criterion), type(criterion)))


# support functions for tree-serialization ############################


RX_IS_SXPR = re.compile(r'\s*\(')
RX_IS_XML = re.compile(r'\s*<')
RX_ATTR_NAME = re.compile(r'[\w.:-]')

def flatten_sxpr(sxpr: str, threshold: int = -1) -> str:
    """
    Returns S-expression ``sxpr`` as a one-liner without unnecessary
    whitespace.

    The ``threshold`` value is a maximum number of
    characters allowed in the flattened expression. If this number
    is exceeded the unflattened S-expression is returned. A
    negative number means that the S-expression will always be
    flattened. Zero or (any postive integer <= 3) essentially means
    that the expression will not be flattened. Example::

        >>> flatten_sxpr('(a\\n    (b\\n        c\\n    )\\n)\\n')
        '(a (b c))'

    :param sxpr: and S-expression in string form
    :param threshold: maximum allowed string-length of the flattened
        S-exrpession. A value < 0 means that it may be arbitrarily long.

    :return: Either flattened S-expression or, if the threshold has been
        overstepped, the original S-expression without leading or
        trailing whitespace.
    """
    assert RX_IS_SXPR.match(sxpr)
    if threshold == 0:
        return sxpr
    flat = re.sub(r'\s(?=\))', '', re.sub(r'\n\s*', ' ', sxpr)).strip()
    l = flat.split('"')
    if len(l) > 1:
        for i in range(0, len(l), 2):
            l[i] = re.sub(r'  +', ' ', l[i])
        flat = '"'.join(l)
    else:
        flat =  re.sub(r'  +', ' ', flat)
    if len(flat) > threshold > 0:
        return sxpr.strip()
    return flat


def flatten_xml(xml: str) -> str:
    """
    Returns an XML-tree as a one liner without unnecessary whitespace,
    i.e. only whitespace within leaf-nodes is preserved.

    A more precise alternative to `flatten_xml` is to use Node.as_xml()
    and passing a set containing the top level tag to parameter `inline_tags`.

    :param xml: the XML-Text to be "flattened"
    :returns: the flattened XML-Text
    """
    # works only with regex
    # return re.sub(r'\s+(?=<\w)', '', re.sub(r'(?<=</\w+>)\s+', '', xml))
    assert RX_IS_XML.match(xml)

    def tag_only(m):
        """Return only the tag, drop the whitespace."""
        return m.groupdict()['closing_tag']
    return re.sub(r'\s+(?=<[\w:])', '', re.sub(r'(?P<closing_tag></:?\w+>)\s+', tag_only, xml))


RX_AMPERSAND = re.compile(r'&(?!\w+;)')


def xml_tag_name(tag_name: str) -> str:
    """Cleans anonymous tag-names for serialization, so that the colon does not
    lead to invalid XML::

        >>> xml_tag_name(':Series')
        'ANONYMOUS_Series__'

    :param tag_name: the original tag name
    :returns: the XML-conform name
    """
    if tag_name[:1] == ':':
        return 'ANONYMOUS_%s__' % tag_name[1:]
    return tag_name


def restore_tag_name(tag_name: str) -> str:
    """Reverts the function :py:func:`xml_tag_name`::

    >>> restore_tag_name('ANONYMOUS_Series__')
    ':Series'
    """
    if tag_name[-2:] == "__" and tag_name[:10] == "ANONYMOUS_":
        return ':' + tag_name[10:-2]
    return tag_name


#######################################################################
#
# Node class
#
#######################################################################

ChildrenType: TypeAlias = Tuple['Node', ...]
StrictResultType: TypeAlias = Union[ChildrenType, StringView, str]
ResultType: TypeAlias = Union[StrictResultType, 'Node']


class Node:  # (collections.abc.Sized): Base class omitted for cython-compatibility
    """
    Represents a node in a tree data structure. This can, for example, be
    the concrete or abstract syntax tree that is produced by a recursive
    descent parser.

    There are three different kinds of nodes:

    1. Branch nodes that have children, but no string content. Other
       than in XML there are no mixed-content nodes that contain strings as
       well other tags. This constraint simplifies tree-processing
       considerably.

       The conversion to and from XML works by enclosing strings
       in a mixed-content tag with some, freely chosen tag name, and
       dropping the tag name again when serializing to XML. Since
       this is easily done, there is no serious restriction involved
       when not allowing mixed-content nodes. See `Node.as_xml()`
       (parameter `string_tags`) as `parse_xml`.

    2. Leaf nodes that do not have children but only string content.

    3. The root node which contains further properties that are
       global properties of the parsing tree, such as the error list
       (which cannot be stored locally in the nodes, because nodes
       might be dropped during tree-processing, but error messages
       should not be forgotten!). Because of that, the root node
       requires a different class (`RootNode`) while leaf-nodes
       as well as branch nodes are both instances of class Node.

    A node always has a tag name (which can be empty, though) and
    a result field, which stores the results of the parsing process
    and contains either a string or a tuple of child nodes.

    All other properties are either optional or represent different
    views on these two properties. Among these are the 'attr`-field
    that contains a dictionary of xml-attributes, the `children`-filed
    that contains a tuple of child-nodes or an empty tuple if the node
    does not have child nodes, the content-field which contains the string
    content of the node and the `pos`-field which contains the position
    of the node's content in the source code, but may also be left
    uninitialized.

    :ivar name: The name of the node, which is either its
            parser's name or, if that is empty, the parser's class name.

            By convention the parser's class name when used as tag name
            is prefixed with a colon ":". A node, the tag name of which
            starts with a colon ":" or the tag name of which is the
            empty string is considered as "anonymous". See
            `Node.anonymous()`-property

    :ivar result: The result of the parser which generated this node,
            which can be either a string or a tuple of child nodes.

    :ivar children: The tuple of child nodes or an empty tuple
            if there are no child nodes. READ ONLY!

    :ivar content: Yields the contents of the tree as string. The
            difference to ``str(node)`` is that ``node.content`` does
            not add the error messages to the returned string. READ ONLY!

    :ivar pos: the position of the node within the parsed text.

            The default value of ``pos`` is -1 meaning invalid by default.
            Setting pos to a value >= 0 will trigger the assignment
            of position values of all child nodes relative to this value.

            The pos field is WRITE ONCE, i.e. once assigned it cannot be
            reassigned. The assignment of the pos values happens either
            during the parsing process or, when later added to a tree,
            the pos-values of which have already been initialized.

            Thus, pos-values always retain their position in the source
            text. If in any tree-processing stage after parsing, nodes
            are added or deleted, the pos values will not represent
            the position within in the string value of the tree.

            Retaining the original source positions is crucial for
            correctly locating errors which might only be detected at
            later stages of the tree-transformation within the source text.

    :ivar attr: An optional dictionary of attributes attached to the node.
            This dictionary is created lazily upon first usage.
    """

    __slots__ = '_result', '_children', '_pos', 'name', '_attributes'

    def __init__(self, name: str,
                 result: Union[Tuple[Node, ...], Node, StringView, str],
                 leafhint: bool = False) -> None:
        """
        Initializes the ``Node``-object with a tag name and the result of a
        parsing operation. The result of a parsing operation can either be
        one or more child-nodes, in which case the Node is informally
        considered to be a "branch-node", or a text-string, in which case
        the node is informally considered to be a "leaf-node".

        :param name: a name for the node. If the node has been created
            by a parser, this is either the parser's name, e.g. "phrase",
            or if the parser wasn't named the parser's type, i.e. name of the
            parser's class, preceded by a colon, e.g. ":Series"
        :param result: the result of the parsing operation that generated the
            node or, more generally, the data that the node contains.
        :param leafhint: default: False. Can be set to true to indicate that
            `result` is a string type. This is an optimization to circumvent
             type-checking the `result`-parameter.
        """
        self._pos = -1                   # type: int
        # Assignment to self.result initializes the attr _result and children
        # The following if-clause is merely an optimization, i.e. a fast-path for leaf-Nodes
        if leafhint:
            self._result = result        # type: Union[Tuple[Node, ...], StringView, str]
            self._children = tuple()     # type: Tuple[Node, ...]
        else:
            self._set_result(result)
        self.name = name         # type: str

    def __deepcopy__(self, memo):
        if self._children:
            duplicate = self.__class__(self.name, copy.deepcopy(self._children), False)
        else:
            duplicate = self.__class__(self.name, self.result, True)
        duplicate._pos = self._pos
        if self.has_attr():
            duplicate.attr.update(self._attributes)
            # duplicate.attr.update(copy.deepcopy(self._attributes))
            # duplicate._attributes = copy.deepcopy(self._attributes)  # this is not cython compatible
        return duplicate

    def __str__(self):
        return self.content

    def __repr__(self):
        rarg = ("'%s'" % str(self)) if not self._children else \
            "(" + ", ".join(child.__repr__() for child in self._children) + ")"
        return "Node('%s', %s)" % (self.name, rarg)

    @property
    def repr(self) -> str:
        """Return a full (re-)executable representation of `self` including
        attributes and position value.
        """
        rep = [repr(self)]
        if self.has_attr():
            rep.append('.with_attr(%s)' % repr(dict(self.attr)))
        if self._pos >= 0:
            rep.append('.with_pos(%i)' % self._pos)
        return ''.join(rep)

    def strlen(self) -> int:
        """Returns the length of the string-content of this node.
        Mind that len(node) returns the number of children of this node!"""
        if self._children:
            return sum(child.strlen() for child in self._children)
        else:
            return len(self._result)

    def __len__(self):
        raise AssertionError(
            "len() on Node-objects would be too ambiguous! Please use either "
            "node.strlen() to query the string-length of the contained text, "
            "or len(node.children) to query the number of child nodes.")

    def __bool__(self):
        """Returns the bool value of a node, which is always True. The reason
        for this is that a boolean test on a variable that can contain a node
        or None will only yield `False` in case of None.
        """
        return True

    # def __hash__(self):
    #     return hash(self.name)  # very bad idea!

    # @property
    # def tag_name(self) -> str:
    #     deprecation_warning('Property "DHParser.nodetree.Node.tag_name" is deprecated. '
    #                         'Use "Node.name" instead!')
    #     return self.name
    #
    # @tag_name.setter
    # def tag_name(self, name: str):
    #     deprecation_warning('Property "DHParser.nodetree.Node.tag_name" is deprecated. '
    #                         'Use "Node.name" instead!')
    #     self.name = name

    def equals(self, other: Node, ignore_attr_order: bool = True) -> bool:
        """
        Equality of value: Two nodes are considered as having the same value,
        if their tag name is the same, if their results are equal and
        if their attributes and attribute values are the same and if either
        `ignore_attr_order` is `True` or the attributes also appear in the
        same order.

        :param other: The node to which `self` shall be compared.
        :param ignore_attr_order: If True (default), two sets of attributes
            are considered as equal if their attribute-names and
            attribute-values are the same, no matter in which order the
            attributes have been added.
        :returns: True, if the tree originating in node `self` is equal by
            value to the tree originating in node `other`.
        """
        if self.name == other.name and self.has_equal_attr(other, ignore_attr_order):
            if self._children:
                return (len(self._children) == len(other._children)
                        and all(a.equals(b, ignore_attr_order)
                                for a, b in zip(self._children, other._children)))
            else:
                return self.result == other.result
        return False

    @property
    def anonymous(self) -> bool:
        """Returns True, if the Node is an "anonymous" Node, i.e. a node that
        has not been created by a named parser.

        The tag name of anonymous node contains a colon followed by the class name
        of the parser that created the node, i.e. ":Series". It is the recommended
        practice to remove (or name) all anonymous nodes during the
        AST-transformation.
        """
        tn = self.name
        return not tn or tn[0] == ':'  # self.name.find(':') >= 0

    # node content ###

    def _set_result(self, result: Union[Tuple[Node, ...], Node, StringView, str]):
        """
        Sets the result of a node without assigning the position.
        An assignment to the `result`-property is to be preferred,
        and `_set_result()` should only be used for optimization
        when it is really necessary!
        :param result:  the new result of the note
        """
        if isinstance(result, Node):
            self._children = (result,)
            self._result = self._children
        else:
            if isinstance(result, tuple):
                self._children = result
                self._result = result or ''
            else:
                # assert isinstance(result, StringView) \
                #     or isinstance(result, str)
                self._children = tuple()
                self._result = result

    # def _init_child_pos(self):
    #     """Initialize position values of children with potentially
    #     unassigned positions, i.e. child.pos < 0."""
    #     children = self._children  # type: Tuple[Node, ...]
    #     if children:
    #         offset = self._pos
    #         prev = children[0]
    #         if prev._pos < 0:
    #             prev.with_pos(offset)
    #         for child in children[1:]:
    #             if child._pos < 0:
    #                 offset = offset + prev.strlen()
    #                 child.with_pos(offset)
    #             else:
    #                 offset = child._pos
    #             prev = child

    @property
    def result(self) -> StrictResultType:
        """
        Returns the result from the parser that created the node.
        """
        return self._result

    @result.setter
    def result(self, result: ResultType):
        self._set_result(result)
        # fix position values for children that are added after the parsing process
        if self._pos >= 0:
            # self._init_child_pos()
            pos = self._pos
            self._pos = -1
            self.with_pos(pos)

    @property
    def children(self) -> ChildrenType:
        """Returns the tuple of child-nodes or an empty tuple if the node does
        node have any child-nodes but only string content."""
        return self._children

    def _leaf_data(self) -> List[str]:
        """
        Returns string content as list of string fragments
        that are gathered from all child nodes in order.
        """
        if self._children:
            fragments = []
            for child in self._children:
                fragments.extend(child._leaf_data())
            return fragments
        self._result = str(self._result)
        return [self._result]

    @property
    def content(self) -> str:
        """
        Returns content as string. If the node has child-nodes, the
        string content of the child-nodes is recursively read and then
        concatenated.
        """
        if self._children:
            fragments = []
            for child in self._children:
                fragments.extend(child._leaf_data())
            return ''.join(fragments)
        self._result = str(self._result)
        return self._result

        # unoptimized
        # return "".join(child.content for child in self._children) if self._children \
        #     else str(self._result)

    # node position ###

    @property
    def pos(self) -> int:
        """Returns the position of the Node's content in the source text."""
        if self._pos < 0:
            raise AssertionError("Position value not initialized! Use Node.with_pos()")
        return self._pos

    def with_pos(self, pos: cint) -> Node:
        """
        Initializes the node's position value. Usually, the parser takes
        care of assigning the positions in the document to the nodes of
        the parse-tree. However, when Nodes are created outside the reach
        of the parser guard, their document-position must be assigned
        manually. Position values of the child nodes are assigned
        recursively, too. Example::

            >>> node = Node('test', 'position').with_pos(10)
            >>> node.pos
            10

            >>> tree = parse_sxpr('(a (b (c "0") (d (e "1")(f "2"))) (g "3"))')
            >>> _ = tree.with_pos(0)
            >>> [(nd.name, nd.pos) for nd in tree.select(ANY_NODE, include_root=True)]
            [('a', 0), ('b', 0), ('c', 0), ('d', 1), ('e', 1), ('f', 2), ('g', 3)]

        :param pos: The position assigned to be assigned to the node.
            Value must be >= 0.
        :returns: the node itself (for convenience).
        :raises: AssertionError if position has already been assigned or
            if parameter `pos` has a value < 0.
        """
        # condition self.pos == pos cannot be assumed when tokens or whitespace
        # are dropped early!
        # assert self._pos < 0 or self.pos == pos, ("pos mismatch %i != %i at Node: %s"
        #                                           % (self._pos, pos, repr(self)))
        if pos != self._pos >= 0:
            raise AssertionError(f"Position value {self._pos} of node {self.name} cannot be "
                                 f"reassigned to a different value ({pos})!")
        assert pos >= 0, "Negative value %i not allowed!"
        if self._pos < 0:
            self._pos = pos
            for nd in self.select(ANY_NODE, include_root=False):
                if nd._pos < 0:
                    if nd._children:
                        nd._pos = pos
                    else:
                        nd._pos = pos
                        pos += len(nd._result)
                else:
                    pos = nd._pos + nd.strlen()
            # recursively adjust pos-values of all children
            # self._init_child_pos()
        return self

    # (XML-)attributes ###

    def has_attr(self, attr: str = '') -> bool:
        """
        Returns `True`, if the node has the attribute `attr` or,
        in case `attr` is the empty string, any attributes at all;
        `False` otherwise.

        This function does not create an attribute dictionary, therefore
        it should be preferred to querying node.attr when testing for the
        existence of any attributes.
        """
        try:
            return attr in self._attributes if attr else bool(self._attributes)
        except (AttributeError, TypeError):
            return False

    @property
    def attr(self):
        """
        Returns a dictionary of XML-attributes attached to the node.

        Examples::

            >>> node = Node('', '')
            >>> print('Any attributes present?', node.has_attr())
            Any attributes present? False
            >>> node.attr['id'] = 'identificator'
            >>> node.attr
            {'id': 'identificator'}
            >>> node.attr['id']
            'identificator'
            >>> del node.attr['id']
            >>> node.attr
            {}

        NOTE: Use :py:meth:`Node.has_attr()` rather than `bool(node.attr)`
        to probe the presence of attributes. Attribute dictionaries are
        created lazily and `node.attr` would create a dictionary, even
        though it may never be needed, anymore.
        """
        try:
            if self._attributes is None:          # cython compatibility
                self._attributes = OrderedDict()  # type: Dict[str, Any]
        except AttributeError:
            self._attributes = OrderedDict()
        return self._attributes

    @attr.setter
    def attr(self, attr_dict: Dict[str, str]):
        self._attributes = attr_dict

    def get_attr(self, attribute: str, default: str) -> str:
        """
        Returns the value of 'attribute' if attribute exists. If not, the
        default value is returned. This function has the same semantics
        as `node.attr.get(attribute, default)`, but with the advantage then
        other than `node.attr.get` it does not automatically create an
        attribute dictionary on (first) access.

        :param attribute: The attribute, the value of which shall be looked up
        :param default: A default value that is returned, in case attribute
            does not exist.
        :returns: the attribute's value or, if unassigned, the default value.
        """
        if self.has_attr():
            return self.attr.get(attribute, default)
        return default

    def with_attr(self, *attr_dict, **attributes) -> Node:
        """
        Adds the attributes which are passed to `with_attr()` either as an
        attribute dictionary or as keyword parameters to the node's attributes
        and returns `self`. Example::

            >>> node = Node('test', '').with_attr(animal = "frog", plant= "tree")
            >>> dict(node.attr)
            {'animal': 'frog', 'plant': 'tree'}
            >>> node.with_attr({'building': 'skyscraper'}).repr
            "Node('test', '').with_attr({'animal': 'frog', 'plant': 'tree', 'building': 'skyscraper'})"

        :param attr_dict:  a dictionary of attribute keys and values
        :param attributes: alternatively, a sequences of keyword parameters
        :return: `self`
        """
        if attr_dict:
            assert not attributes, "Node.with_attr() can be called either exclusively with " \
                "keyword parameters, or a single non-keyword parameter and no keyword parameters!"
            assert len(attr_dict) == 1, "Node.with_attr() must not be called with more than one " \
                "non-keyword parameter."
            dictionary = attr_dict[0]
            # # commented out, because otherwise lxml-conversion fails
            # assert isinstance(dictionary, dict), "The non-keyword parameter passed to " \
            #     "Node.with_attr() must be of type dict, not %s." % str(type(dictionary))
            # assert all(isinstance(a, str) and isinstance(v, str) for a, v in attr_dict.items())
            if dictionary:  # do not update with an empty dictionary
                self.attr.update(dictionary)
        if attributes:
            # assert all(isinstance(a, str) and isinstance(v, str) for a, v in attributes.items())
            self.attr.update(attributes)
        return self

    def has_equal_attr(self, other: Node, ignore_order: bool = True) -> bool:
        """
        Returns True, if `self` and `other` have the same attributes with
        the same attribute values. If `ignore_order` is False, the
        attributes must also appear in the same order.
        """
        if self.has_attr():
            if other.has_attr():
                if ignore_order:
                    return set(self.attr.items()) == set(other.attr.items())
                return self.attr == other.attr
            return len(self.attr) == 0
            # self has empty dictionary and other has no attributes
        elif other.has_attr():
            return len(other.attr) == 0
            # other has empty attribute dictionary and self as no attributes
        return True  # neither self nor other have any attributes

    # tree traversal and node selection #######################################

    def __getitem__(self, key: Union[NodeSelector, int, slice]) \
            -> Union[Node, Tuple[Node, ...]]:
        """
        Returns the child node with the given index if ``key`` is
        an integer or all child-nodes with the given tag name. Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")) (b "Y"))')
            >>> tree[0]
            Node('b', 'X')
            >>> tree['X']
            Node('X', (Node('c', 'd')))
            >>> tree['b']
            (Node('b', 'X'), Node('b', 'Y'))

            >>> from DHParser.toolkit import as_list, as_tuple
            >>> as_tuple(tree['b'])
            (Node('b', 'X'), Node('b', 'Y'))
            >>> as_tuple(tree['e'])
            (Node('e', (Node('X', 'F'))),)

        :param key(str): A tag-name (string) or an index or a slice of the 
            child or children that shall be returned.
        :returns: The node with the given index (always type Node) or a
            list of all nodes which have a given tag name, if `key` was a
            tag-name and there is more than one child-node with this tag-name
        :raises:
            KeyError:   if no matching child was found.
            IndexError: if key was an integer index that did not exist
            ValueError: if the __getitem__ has been called on a leaf node.
        """
        if not self._children and self._result:
            raise ValueError('Item access is not possible on a leaf-node!')
        if isinstance(key, (int, slice)):
            return self._children[key]
        else:
            mf = create_match_function(key)
            items = tuple(child for child in self._children if mf(child))
            if items:
                return items if len(items) >= 2 else items[0]
            raise KeyError(str(key))

    def __setitem__(self,
                    key: Union[NodeSelector, slice, int],
                    value: Union[Node, Sequence[Node]]):
        """
        Changes one or more children of a branch-node.
        :raises:
            KeyError:   if no matching child was found.
            IndexError: if key was an integer index that did not exist
            ValueError: if the __getitem__ has been called on a leaf node.
        """
        if not self._children:
            raise ValueError('Setting items is not possible on a leaf-node!')
        lchildren = list(self._children)
        if isinstance(key, int):
            if not isinstance(value, Node):
                raise ValueError('Only nodes can be assigned to a single item!')
            lchildren[key] = value
        elif isinstance(key, slice):
            if not isinstance(value, Sequence):
                value = [value]
            lchildren.__setitem__(key, value)
        else:
            mf = create_match_function(key)
            indices = [i for i in range(len(lchildren)) if mf(lchildren[i])]
            if isinstance(value, Sequence):
                if len(indices) != len(value):
                    raise ValueError(f'Cannot assign {len(value)} values to {len(indices)} items!')
                for k, i in enumerate(indices):
                    lchildren[i] = value[k]
            else:
                if indices:
                    for i in indices:
                        lchildren[i] = value
                else:
                    raise KeyError(f'No item matching "{str(key)}" found!')
        self.result = tuple(lchildren)

    def __delitem__(self, key: Union[int, slice, NodeSelector]):
        """
        Removes children from the node. Note that integer values passed to
        parameter ``key`` are always interpreted as index, not as an object id
        as comparison criterion.

        :param key: An integer index of slice of child-nodes to be deleted
            or a tag name (string) for selecting child-nodes for deletion.
        :raises:
            KeyError:   if no matching child was found.
            IndexError: if key was an integer index that did not exist
            ValueError: if the __getitem__ has been called on a leaf node.
        """
        if not self._children and self.result:
            raise ValueError('Item deletion is not possible on a leaf-node!')
        if isinstance(key, int):
            L = len(self._children)
            k = L + key if key < 0 else key
            if 0 <= k < L:
                self.result = self._children[:k] + self._children[k + 1:]
            else:
                raise IndexError("index %s out of range [0, %i[" % (key, len(self._children)))
        elif isinstance(key, slice):
            children = list(self.children)
            for i in range(*key.indices(len(children))):
                children[i] = None
            self.result = tuple(child for child in children if child is not None)
        else:
            mf = create_match_function(key)
            before = self._result
            after = tuple(child for child in self._children if not mf(child))
            if len(before) == len(after):
                raise KeyError(f'No child-node matching {str(key)} found!')
            self.result = after

    def get(self, key: Union[int, slice, NodeSelector],
            surrogate: Union[Node, Sequence[Node]]) -> Union[Node, Sequence[Node]]:
        """Returns the child node with the given index if ``key``
        is an integer or the first child node with the given tag name. If no
        child with the given index or name exists, the ``surrogate`` is
        returned instead. This mimics the behaviour of Python's dictionary's
        ``get()``-method.

        The type of the return value is always the same type as that of the
        surrogate. If the surrogate is a Node, but there are several items
        matching ``key``, then only the first of these will be returned.
        """
        try:
            items = self[key]
            if isinstance(surrogate, Sequence):
                return items if isinstance(items, Sequence) else (items,)
            else:
                return items[0] if isinstance(items, Sequence) else items
        except (KeyError, ValueError, IndexError):
            return surrogate

    def __contains__(self, selector: NodeSelector) -> bool:
        """
        Returns true if at least one child that matches the given criterion
        exists. See :py:func:`create_match_function()` for a catalogue of
        possible criteria.

        :param selector: a criterion that describes the child-node
        :returns: True, if at least one child fulfills the criterion
        """
        mf = create_match_function(selector)
        for child in self._children:
            if mf(child):
                return True
        return False

    def remove(self, node: Node):
        """Removes `node` from the children of the node."""
        if not self.children:
            raise ValueError('Node.remove(x): Called on a node without children')
        i = len(self._children)
        self.result = tuple(nd for nd in self._children if nd != node)
        if len(self.result) >= i:
            raise ValueError('Node.remove(x): x not among children')

    def insert(self, index: int, node: Node):
        """Inserts a node at position `index`"""
        if not self.children and self._result:
            raise ValueError('Node.insert(i, node): Called on a leaf-node')
        result = list(self.children)
        result.insert(index, node)
        self.result = tuple(result)

    def index(self, selector: NodeSelector, start: int = 0, stop: int = 2 ** 30) -> int:
        """
        Returns the index of the first child that fulfills the criterion
        `what`. If the parameters start and stop are given, the search is
        restricted to the children with indices from the half-open interval
        [start:end[. If no such child exists a ValueError is raised.

        :param selector: the criterion by which the child is identified, the index
            of which shall be returned.
        :param start: the first index to start searching.
        :param stop: the last index that shall be searched
        :returns: the index of the first child that matches `what`.
        :raises: ValueError, if no child matching the criterion `what` was found.
        """
        assert 0 <= start < stop
        if not self.children:
            raise ValueError('Node.index(x): Called on a Node without children')
        mf = create_match_function(selector)
        for i, child in enumerate(self._children[start:stop]):
            if mf(child):
                return i + start
        raise ValueError("Node identified by '%s' not among child-nodes."
                         % abbreviate_middle(repr(selector), 60))

    @cython.locals(i=cython.int)
    def indices(self, selector: NodeSelector) -> Tuple[int, ...]:
        """
        Returns the indices of all children that fulfil the criterion `what`.
        """
        mf = create_match_function(selector)
        children = self._children
        return tuple(i for i in range(len(children)) if mf(children[i]))

    def select_if(self, match_func: NodeMatchFunction,
                  include_root: bool = False, reverse: bool = False,
                  skip_func: NodeMatchFunction = NO_NODE) -> Iterator[Node]:
        """
        Generates an iterator over all nodes in the tree for which
        `match_function()` returns True. See the more general function
        :py:meth:`Node.select()` for a detailed description and examples.
        The tree is traversed pre-order by the iterator.
        """
        def recursive(nd: Node) -> Iterator[Node]:
            nonlocal match_func, reverse, skip_func
            child_iterator = reversed(nd._children) if reverse else nd._children
            for child in child_iterator:
                if match_func(child):
                    yield child
                if child._children and not skip_func(child):
                    yield from recursive(child)

        if include_root:
            if match_func(self):  yield self
            if not skip_func(self):
                yield from recursive(self)
        else:
            yield from recursive(self)

    def select(self, criteria: NodeSelector,
               include_root: bool = False, reverse: bool = False,
               skip_subtree: NodeSelector = NO_NODE) -> Iterator[Node]:
        """
        Generates an iterator over all nodes in the tree that fulfill the
        given criterion. See :py:func:`create_match_function()` for a
        catalogue of possible criteria.

        :param criteria: The criteria for selecting nodes.
        :param include_root: If False, only descendant nodes will be checked
            for a match.
        :param reverse: If True, the tree will be walked in reverse
                order, i.e. last children first.
        :param skip_subtree: A criterion to identify subtrees that the returned
                iterator shall not dive into. Note that the root-node of the
                subtree will still be yielded by the iterator.
        :returns: An iterator over all descendant nodes which fulfill the
           given criterion. Traversal is pre-order.

        Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")))')
            >>> list(flatten_sxpr(item.as_sxpr()) for item in tree.select("X", False))
            ['(X (c "d"))', '(X "F")']
            >>> list(flatten_sxpr(item.as_sxpr()) for item in tree.select({"X", "b"}, False))
            ['(b "X")', '(X (c "d"))', '(X "F")']
            >>> any(tree.select('a', False))
            False
            >>> list(flatten_sxpr(item.as_sxpr()) for item in tree.select('a', True))
            ['(a (b "X") (X (c "d")) (e (X "F")))']
            >>> flatten_sxpr(next(tree.select("X", False)).as_sxpr())
            '(X (c "d"))'
            >>> tree = parse_sxpr('(a (b (c "") (d (e "")(f ""))) (g ""))')
            >>> [nd.name for nd in tree.select(ANY_NODE)]
            ['b', 'c', 'd', 'e', 'f', 'g']
        """
        return self.select_if(create_match_function(criteria), include_root, reverse,
                              create_match_function(skip_subtree))

    def select_children(self, criteria: NodeSelector, reverse: bool = False) \
            -> Iterator[Node]:
        """Returns an iterator over all direct children of a node that
        fulfil the given `criterion`. See :py:meth:`Node.select()` for a description
        of the parameters.
        """
        match_function = create_match_function(criteria)
        if reverse:
            for child in reversed(tuple(self.select_children(criteria, False))):
                yield child
        else:
            for child in self._children:
                if match_function(child):
                    yield child

    def pick(self, criteria: NodeSelector,
             include_root: bool = False,
             reverse: bool = False,
             skip_subtree: NodeSelector = NO_NODE) -> Optional[Node]:
        """
        Picks the first (or last if run in reverse mode) descendant that
        fulfils the given criterion. See :py:func:`create_match_function()`
        for a catalogue of possible criteria.

        This function is syntactic sugar for `next(node.select(criterion, ...))`.
        However, rather than raising a StopIterationError if no descendant
        with the given tag-name exists, it returns `None`.
        """
        try:
            return next(self.select(criteria, include_root, reverse, skip_subtree))
        except StopIteration:
            return None

    def pick_child(self, criteria: NodeSelector, reverse: bool = False) \
            -> Optional[Node]:
        """
        Picks the first child (or last if run in reverse mode) descendant
        that fulfils the given criterion. See :py:func:`create_match_function()`
        for a catalogue of possible criteria.

        This function is syntactic sugar for
        `next(node.select_children(criterion, False))`. However, rather than
        raising a StopIterationError if no descendant with the given tag-name
        exists, it returns None.
        """
        try:
            return next(self.select_children(criteria, reverse=reverse))
        except StopIteration:
            return None

    @cython.locals(end=cython.int)
    def locate(self, location: cint) -> Optional[Node]:
        """
        Returns the leaf-Node that covers the given ``location``, where
        location is the actual position within ``self.content`` (not the
        source code position that the pos-attribute represents). If
        the location lies outside the node's string content, `None` is
        returned.

        See also :py:class:`ContentMapping` for a more
        general approach to locating string positions within the tree.
        """
        end = 0
        for nd in self.select_if(lambda nd: not nd._children, include_root=True):
            end += nd.strlen()
            if location < end:
                return nd
        return None

    def find_parent(self, node) -> Optional[Node]:
        """
        Finds and returns the parent of `node` within the tree represented
        by `self`. If the tree does not contain `node`, the value `None`
        is returned.
        """
        for nd in self.select_if(lambda nd: bool(nd._children), include_root=True):
            if node in nd._children:
                return nd
        return None

    # path selection ###

    def select_path_if(self, match_func: PathMatchFunction,
                       include_root: bool = False,
                       reverse: bool = False,
                       skip_func: PathMatchFunction = NO_PATH) -> Iterator[Path]:
        """
        Like :py:func:`Node.select_if()` but yields the entire path (i.e. list
        of descendants, the last one being the matching node) instead of just
        the matching nodes. NOTE: In contrast to `select_if()`, `match_function`
        receives the complete path as argument, rather than just the last node!
        """
        def recursive(trl) -> Iterator[Path]:
            nonlocal match_func, reverse, skip_func
            top = trl[-1]
            child_iterator = reversed(top._children) if reverse else top._children
            for child in child_iterator:
                child_trl = trl + [child]
                if match_func(child_trl):
                    yield child_trl
                if child._children and not skip_func(child_trl):
                    yield from recursive(child_trl)

        trl = [self]
        if include_root:
            if match_func(trl):  yield trl
            if not skip_func(trl):
                yield from recursive(trl)
        else:
            yield from recursive(trl)

    def select_path(self, criteria: PathSelector,
                    include_root: bool = False,
                    reverse: bool = False,
                    skip_subtree: PathSelector = NO_PATH) -> Iterator[Path]:
        """
        Like :py:meth:`Node.select()` but yields the entire path (i.e. list of
        descendants, the last one being the matching node) instead of just
        the matching nodes.
        """
        return self.select_path_if(create_path_match_function(criteria),
                                   include_root, reverse,
                                   create_path_match_function(skip_subtree))

    def pick_path(self, criteria: PathSelector,
                  include_root: bool = False,
                  reverse: bool = False,
                  skip_subtree: PathSelector = NO_PATH) -> Path:
        """
        Like :py:meth:`Node.pick()`, only that the entire path (i.e.
        chain of descendants) relative to `self` is returned.
        """
        try:
            return next(self.select_path(criteria, include_root, reverse, skip_subtree))
        except StopIteration:
            return []

    @cython.locals(end=cython.int)
    def locate_path(self, location: cint) -> Path:
        """
        Like :py:meth:`Node.locate()`, only that the entire path (i.e.
        chain of descendants) relative to `self` is returned.
        """
        end = 0
        for trl in self.select_path_if(lambda trl: not trl[-1]._children, include_root=True):
            end += trl[-1].strlen()
            if location < end:
                return trl
        return []

    def _reconstruct_path_recursive(self, node: Node) -> Path:
        """
        Determines the chain of ancestors of a node that leads up to self. Other than
        the public method `reconstruct_path`, this method returns the chain of ancestors
        in reverse order [node, ... , self] and returns None in case `node` does not exist
        in the tree rooted in self instead of raising a Value Error.
        If `node` equals `self`, any empty path, i.e. list will be returned.
        """
        if node in self._children:
            return [node, self]
        for nd in self._children:
            trl = nd._reconstruct_path_recursive(node)
            if trl:
                trl.append(self)
                return trl
        return []

    def reconstruct_path(self, node: Node) -> Path:
        """
        Determines the chain of ancestors of a node that leads up to self.
        :param node: the descendant node, the ancestry of which shall be determined.
        :return: the list of nodes starting with self and leading to `node`
        :raises: ValueError, in case `node` does not occur in the tree rooted in `self`
        """
        if node == self:
            return [node]
        trl = self._reconstruct_path_recursive(node)
        if trl:
            trl.reverse()
            return trl
        else:
            raise ValueError('Node "%s" does not occur in the tree %s '
                             % (node.name, flatten_sxpr(self.as_sxpr())))

    # milestone support ### EXPERIMENTAL!!! ###

    # def find_nearest_common_ancestor(self, A: Node, B: Node) -> Node:
    #     """
    #     Finds the nearest common ancestor of the two nodes A and B.
    #     :param A: a node in the tree
    #     :param B: another node in the tree
    #     :return: the nearest common ancestor
    #     :raises: ValueError in case `A` and `B` are not both rooted in `self`
    #     """
    #     trlA = self.reconstruct_path(A)
    #     trlB = self.reconstruct_path(B)
    #     for a,b in zip(trlA, trlB):
    #         if a != b:
    #             break
    #         common_ancestor = a
    #     return common_ancestor

    def milestone_segment(self, begin: Union[Path, Node], end: Union[Path, Node]) -> Node:
        """
        EXPERIMENTAL!!!
        Picks a segment from a tree beginning with start and ending with end.

        :param begin: the opening milestone (will be included in the result)
        :param end: the closing milestone (will be included in the result)
        :return: a tree(-segment) encompassing all nodes from the opening
            milestone up to and including the closing milestone.
        """
        def index(parent: Node, nd: Node) -> int:
            children = parent._children
            for i in range(len(children)):
                if nd == children[i]:
                    return i
            raise ValueError

        def left_cut(result: Tuple[Node, ...], index: int, subst: Node) -> Tuple[Node, ...]:
            return (subst,) + result[index + 1:]

        def right_cut(result: Tuple[Node, ...], index: int, subst: Node) -> Tuple[Node, ...]:
            return result[:index] + (subst,)

        def cut(trl: Path, cut_func: Callable) -> Node:
            child = trl[-1]
            tainted = False
            for i in range(len(trl) - 1, 0, -1):
                parent = trl[i - 1]
                k = index(parent, trl[i])
                segment = cut_func(parent.result, k, child)
                if tainted or len(segment) != len(parent.result):
                    parent_copy = Node(parent.name, segment)
                    if parent.has_attr():
                        parent_copy.attr = parent.attr
                    child = parent_copy
                    tainted = True
                else:
                    child = parent
            return child

        if begin.pos > end.pos:
            begin, end = end, begin
        common_ancestor = self  # type: Node
        trlA = self.reconstruct_path(begin) if isinstance(begin, Node) else begin
        trlB = self.reconstruct_path(end) if isinstance(end, Node) else end
        for a, b in zip(trlA, trlB):
            if a != b:
                break
            common_ancestor = a
        left = cut(trlA[trlA.index(common_ancestor):], left_cut)    # type: Node
        right = cut(trlB[trlB.index(common_ancestor):], right_cut)  # type: Node
        left_children = left._children    # type: Tuple[Node, ...]
        right_children = right._children  # type: Tuple[Node, ...]
        if left_children == right_children:
            return common_ancestor
        i = 1  # type: int
        k = len(right_children)  # type: int
        try:
            k = right_children.index(left_children[1]) - 1
            i = 2
            while left_children[i] == right_children[k + i]:
                i += 1
        except (IndexError, ValueError):
            pass
        new_ca = Node(common_ancestor.name, left_children[:i] + right_children[k + i:])
        if common_ancestor.has_attr():
            new_ca.attr = common_ancestor.attr
        return new_ca

    # evaluation ##############################################################

    def evaluate(self, actions: Dict[str, Callable]) -> Any:
        """Simple tree evaluation: For each node the action associated with
        the node's tag-name is called with either the tuple of the evaluated
        children or, in case of a leaf-node, the result-string as parameters::

            >>> tree = parse_sxpr('(plus (number 3) (mul (number 5) (number 4)))')
            >>> from operator import add, mul
            >>> actions = {'plus': add, 'mul': mul, 'number': int}
            >>> tree.evaluate(actions)
            23

        :param actions: A dictionary that maps node-names to action functions.
        :return: the result of the evaluation
        """
        args = tuple(child.evaluate(actions) for child in self._children) if self._children \
               else (self._result,)
        try:
            return actions[self.name](*args)
        except KeyError:
            return self.content
        except TypeError as e:
            raise AssertionError(f'Evaluation function for tag "{self.name}" cannot handle '
                                 f'arguments: {args}. Error raised: {e}')

    # serialization ###########################################################

    @cython.locals(i=cython.int, k=cython.int, N=cython.int)
    def _tree_repr(self, tab, open_fn, close_fn, data_fn=lambda i: i,
                   density=0, inline=False, inline_fn=lambda node: False,
                   allow_omissions=False) -> List[str]:
        """
        Generates a tree representation of this node and its children
        in string from.

        The kind ot tree-representation that is determined by several
        function parameters. This could be an XML-representation or a
        lisp-like S-expression.

        :param tab:  The indentation string, e.g. '\t' or '    '
        :param open_fn: A function (Node -> str) that returns an
            opening string (e.g. an XML-name) for a given node
        :param close_fn:  A function (Node -> str) that returns a closing
            string (e.g. an XML-name) for a given node.
        :param data_fn:  A function (str -> str) that filters the data
            string before printing, e.g. to add quotation marks

        :returns:  A list of strings that, if concatenated, yield a
            serialized tree representation of the node and its children.
        """
        head = open_fn(self)
        tail = close_fn(self)

        if not self.result:
            return [head + tail]

        inline = inline or inline_fn(self)
        if inline:
            usetab, sep = '', ''
            hlf, tlf = '', ''
        else:
            usetab = tab if head else ''    # no indentation if tag is already omitted
            sep = '\n'
            hlf = '\n'
            tlf = '\n' if density == 0 or (tail[0:1] == '<') else ''

        if self._children:
            content = [head]
            # first_child = self._children[0]
            for child in self._children:
                subtree = child._tree_repr(tab, open_fn, close_fn, data_fn,
                                           density, inline, inline_fn, allow_omissions)
                if subtree:
                    if inline:
                        content[-1] += '\n'.join(subtree)
                    else:
                        if sep:
                            for item in subtree:
                                content.append(usetab + item)
                        else:
                            content[-1] += ''.join(subtree)
            if tlf:
                content.append(tail)
            else:
                content[-1] += tail
            return content

        res = self.content
        if not inline and not head and allow_omissions:
            # strip whitespace for omitted non-inline node, e.g. CharData in mixed elements
            res = res.strip()  # WARNING: This changes the data in subtle ways
        if density & 1 and res.find('\n') < 0:
            # except for XML, add a gap between opening statement and content
            if not inline and head and (head[-1:] != '>' and head != '<!--'):
                gap = ' '
            else:  gap = ''
            return [''.join((head, gap, data_fn(res), tail))]
        else:
            lines = [data_fn(s) for s in res.split('\n')]
            N = len(lines)
            i, k = 0, N - 1
            if not inline and allow_omissions:
                # Strip preceding and succeeding whitespace.
                # WARNING: This changes the data in subtle ways
                while i < N and not lines[i]:
                    i += 1
                while k >= 0 and not lines[k]:
                    k -= 1
            content = [head, usetab] if hlf else [head + usetab]
            for line in lines[i:k]:
                content[-1] += line
                content.append(usetab)
            content[-1] += lines[k]
            if tlf:
                content.append(tail)
            else:
                content[-1] += tail
            return content

    def as_sxpr(self, src: Optional[str] = None,
                indentation: int = 2,
                compact: bool = True,
                flatten_threshold: int = 92) -> str:
        """
        Serializes the tree as S-expression, i.e. in lisp-like form. If this
        method is called on a RootNode-object, error strings will be displayed
        as pseudo-attributes of the nodes where the error is located.

        :param src:  The source text or `None`. In case the source text is
            given the position of the element in the text will be
            reported as position, line, column. In case the empty string is
            given rather than None, only the position value will be
            reported in case it has been initialized, i.e. pos >= 0.
        :param indentation: The number of whitespaces for indentation
        :param compact:  If True, a compact representation is returned where
            closing brackets remain on the same line as the last element.
        :param flatten_threshold:  Return the S-expression in flattened form if
            the flattened expression does not exceed the threshold length.
            A negative number means that it will always be flattened.
        :returns: A string containing the S-expression serialization of the tree.
        """
        left_bracket, right_bracket, density = ('(', ')', 1) if compact else ('(', ')', 0)
        lbreaks = linebreaks(src) if src else []  # type: List[int]
        root = cast(RootNode, self) if isinstance(self, RootNode) \
            else None  # type: Optional[RootNode]

        def opening(node: Node) -> str:
            """Returns the opening string for the representation of `node`."""
            txt = [left_bracket, node.name]
            # s += " '(pos %i)" % node.add_pos
            # txt.append(str(id(node)))  # for debugging
            if node.has_attr():
                txt.extend(' `(%s "%s")' % (k, str(v)) for k, v in node.attr.items())
            if node._pos >= 0:
                if src:
                    line, col = line_col(lbreaks, node.pos)
                    txt.append(' `(pos %i %i %i)' % (node.pos, line, col))
                elif src is not None:
                    txt.append(' `(pos %i)' % node.pos)
            if root and id(node) in root.error_nodes and not node.has_attr('err'):
                err_str = ';  '.join(str(err) for err in root.node_errors(node))
                err_str = err_str.replace('"', r'\"')
                txt.append(f' `(err "{err_str}")')
            return "".join(txt)

        def closing(node: Node) -> str:
            """Returns the closing string for the representation of `node`."""
            return right_bracket

        def pretty(strg: str) -> str:
            """Encloses `strg` with the right kind of quotation marks."""
            return '"%s"' % strg if strg.find('"') < 0 \
                else "'%s'" % strg if strg.find("'") < 0 \
                else '"%s"' % strg.replace('"', r'\"')

        sxpr = '\n'.join(self._tree_repr(' ' * indentation, opening, closing, pretty, density=density))
        return flatten_sxpr(sxpr, flatten_threshold)

    def as_xml(self, src: Optional[str] = None,
               indentation: int = 2,
               inline_tags: AbstractSet[str] = frozenset(),
               string_tags: AbstractSet[str] = frozenset({MIXED_MODE_TEXT_PTYPE}),
               empty_tags: AbstractSet[str] = frozenset(),
               strict_mode: bool = True) -> str:
        """Serializes the tree of nodes as XML.

        :param src: The source text or `None`. In case the source text is
                given, the position will also be reported as line and column.
        :param indentation: The number of whitespaces for indentation
        :param inline_tags:  A set of tag names, the content of which will always be
                written on a single line, unless it contains explicit line feeds (`\\n`).
        :param string_tags: A set of tags from which only the content will be printed, but
                neither the opening tag nor its attr nor the closing tag. This
                allows producing a mix of plain text and child tags in the output,
                which otherwise is not supported by the Node object, because it
                requires its content to be either a tuple of children or string content.
        :param empty_tags: A set of tags which shall be rendered as empty elements, e.g.
                "<empty/>" instead of "<empty><empty>".
        :param strict_mode: If True, violation of stylistic or interoperability rules
                raises a ValueError.
        :returns: The XML-string representing the tree originating in `self`
        """
        root = cast(RootNode, self) if isinstance(self, RootNode) \
            else None  # type: Optional[RootNode]

        def attr_err_ignore(value: str) -> str:
            return ("'%s'" % value) if value.find('"') >= 0 else '"%s"' % value

        attr_err_handling = get_config_value('xml_attribute_error_handling')
        if attr_err_handling == 'fail':
            attr_filter = validate_XML_attribute_value
        elif attr_err_handling == 'fix':
            attr_filter = fix_XML_attribute_value
        elif attr_err_handling == 'lxml':
            attr_filter = lxml_XML_attribute_value
        else:
            assert attr_err_handling == 'ignore', 'Illegal value for configuration ' +\
                'variable "xml_attribute_error_handling": ' + attr_err_handling
            attr_filter = attr_err_ignore

        def opening(node: Node) -> str:
            """Returns the opening string for the representation of `node`."""
            nonlocal attr_filter, empty_tags
            if node.name in string_tags and not node.has_attr():
                return ''
            txt = ['<', xml_tag_name(node.name)]
            if node.has_attr():
                txt.extend(' %s=%s' % (k, attr_filter(str(v))) for k, v in node.attr.items())
            if src and not (node.has_attr('line') or node.has_attr('col')):
                txt.append(' line="%i" col="%i"' % line_col(line_breaks, node._pos))
            if src == '' and not (node.has_attr() and '_pos' in node.attr) and node._pos >= 0:
                txt.append(' _pos="%i"' % node._pos)
            if root and id(node) in root.error_nodes and not node.has_attr('err'):
                # txt.append(' err="%s"' % (
                #     ''.join(str(err).replace('"', "'").replace('&', '&amp;').replace('<', '&lt;')
                #             for err in root.node_errors(node))))
                txt.append(' err=' + attr_filter(''.join(str(err) for err in root.node_errors(node))))
            if node.name in empty_tags:
                if node.name[0:1] != '?' and node.result:
                    if strict_mode:
                        raise ValueError(
                            f'Empty element "{node.name}" with content: '
                            f'"{abbreviate_middle(str(node.result), 40)}" !? '
                            f'Use Node.as_xml(..., strict_mode=False) to suppress this error!')
                if node.name[0] == '?':  ending = '?>'
                elif node.result:  ending = '>'
                else:  ending = '/>'
            elif node.name == '!--':
                ending = ""
            else:
                ending = ">"
            return "".join(txt + [ending])

        def closing(node: Node):
            """Returns the closing string for the representation of `node`."""
            if (node.name in empty_tags and not node.result) \
                    or (node.name in string_tags and not node.has_attr()):
                return ''
            elif node.name == '!--':
                return '-->'
            return '</' + xml_tag_name(node.name) + '>'

        def sanitizer(content: str) -> str:
            """Substitute "&", "<", ">" in XML-content by the respective entities."""
            content = RX_AMPERSAND.sub('&amp;', content)
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            return content

        def inlining(node: Node):
            """Returns True, if `node`'s tag name is contained in `inline_tags`,
            thereby signalling that the children of this node shall not be
            printed on several lines to avoid unwanted gaps in the output.
            """
            return node.name in inline_tags \
                   or (node.has_attr() and node.attr.get('xml:space', 'default') == 'preserve')
                    # or (node.name in string_tags and not node.children)

        line_breaks = linebreaks(src) if src else []
        return '\n'.join(self._tree_repr(
            ' ' * indentation, opening, closing, sanitizer, density=1, inline_fn=inlining,
            allow_omissions=bool(string_tags)))

    def as_tree(self) -> str:
        """Serialize as a simple indented text-tree."""
        sxpr = self.as_sxpr(flatten_threshold=0, compact=True)
        lines = sxpr.split('\n')
        for i, line in enumerate(lines):
            # Admittedly, the following transformations are sloppy
            # and my lead to wrong output, when there are strings
            # that contain ") `(" and the like....
            line = re.sub(r'^(\s*)\(', r'\1', line)
            line = re.sub(r'\)+$', r'', line)
            line = line.replace(') `(', ' `')
            line = line.replace('`(', '`')
            line = line.replace('") "', '" "')
            lines[i] = line
        return '\n'.join(lines)

    # JSON serialization ###

    def to_json_obj(self) -> list:
        """Converts the tree into a JSON-serializable nested list. Nodes
        are serialized as JSON-lists with either two or three elements:

        1. name (always a string),
        2. content (either a string or a list of JSON-serialized Nodes)
        3. optional: a dictionary that maps attribute names to attribute values,
           both of which are strings.

        Example::

            >>> Node('root', 'content').with_attr(importance="high").to_json_obj()
            ['root', 'content', {'importance': 'high'}]
        """
        jo = [self.name,
              [nd.to_json_obj() for nd in self._children]
              if self._children else str(self.result)]
        pos = self._pos
        if pos >= 0:
            jo.append(pos)
        if self.has_attr():
            jo.append(self.attr)
        return jo

    @staticmethod
    def from_json_obj(json_obj: Union[Dict, Sequence]) -> Node:
        """Converts a JSON-object representing a node (or tree) back into a
        Node object. Raises a ValueError, if `json_obj` does not represent
        a node."""
        assert isinstance(json_obj, Sequence)
        assert 2 <= len(json_obj) <= 4, str(json_obj)
        if isinstance(json_obj[1], str):
            result = json_obj[1]  # type: Union[Tuple[Node, ...], StringView, str]
        else:
            result = tuple(Node.from_json_obj(item) for item in json_obj[1])
        node = Node(json_obj[0], result)
        for extra in json_obj[2:]:
            if isinstance(extra, dict):
                node.attr.update(extra)
            else:
                assert isinstance(extra, int)
                node._pos = extra
        return node

    def as_json(self, indent: Optional[int] = 2, ensure_ascii=False) -> str:
        """Serializes the tree originating in `self` as JSON-string. Nodes
        are serialized as JSON-lists with either two or three elements:

        1. name (always a string),
        2. content (either a string or a list of JSON-serialized Nodes)
        3. optional: a dictionary that maps attribute names to attribute values,
           both of which are strings.

        Example::

            >>> Node('root', 'content').with_attr(importance="high").as_json(indent=0)
            '["root","content",{"importance":"high"}]'
        """
        if not indent or indent <= 0:  indent = None
        return json.dumps(self.to_json_obj(), indent=indent, ensure_ascii=ensure_ascii,
                          separators=(', ', ': ') if indent is not None else (',', ':'))

    # serialization meta-method ###

    @cython.locals(vsize=cython.int, i=cython.int, threshold=cython.int)
    def serialize(self, how: str = 'default') -> str:
        """
        Serializes the tree originating in the node `self` either as
        S-expression, XML, JSON, or in compact form. Possible values for
        `how` are 'S-expression', 'XML', 'JSON', 'indented' accordingly, or
        'AST', 'CST', 'default', in which case the value of respective
        configuration variable determines the serialization format.
        (See module :py:mod:`DHParser.configuration`.)
        """
        def exceeds_compact_threshold(node: Node, threshold: int) -> bool:
            """Returns True, if the S-expression-serialization of the tree
            rooted in `node` would exceed a certain number of lines and
            should therefore be rendered in a more compact form.
            """
            vsize = 0
            for nd in node.select_if(lambda _: True, include_root=True):
                vsize += 1
                if vsize > threshold:
                    return True
            return False

        switch = how.lower()

        if switch == 'ast':
            switch = get_config_value('ast_serialization').lower()
        elif switch == 'cst':
            switch = get_config_value('cst_serialization').lower()
        elif switch == 'default':
            switch = get_config_value('default_serialization').lower()

        # flatten_threshold = get_config_value('flatten_sxpr_threshold')
        compact_threshold = get_config_value('compact_sxpr_threshold')

        if switch in ('S-expression', 'S-Expression', 's-expression', 'sxpr'):
            return self.as_sxpr(flatten_threshold=get_config_value('flatten_sxpr_threshold'),
                                compact=exceeds_compact_threshold(self, compact_threshold))
        elif switch == 'xml':
            return self.as_xml(strict_mode=False)
        elif switch == 'json':
            return self.as_json()
        elif switch in ('indented', 'tree'):
            return self.as_tree()
        else:
            s = how if how == switch else (how + '/' + switch)
            raise ValueError('Unknown serialization "%s". Allowed values are either: %s or : %s'
                             % (s, "ast, cst, default",
                                ", ".join(ALLOWED_PRESET_VALUES['default_serialization'])))

    # Export and import as Element-Tree ###

    def as_etree(self, ET=None, string_tags: AbstractSet[str] = frozenset({MIXED_MODE_TEXT_PTYPE}),
                 empty_tags: AbstractSet[str] = frozenset()):
        """Returns the tree as standard-library- or lxml-ElementTree.

        :param ET: The ElementTree-library to be used. If None, the STL ElemtentTree
            will be used.
        :param string_tags: A set of tags the content of which will be written without
            tag-name into the mixed content of the parent.
        :param empty_tags: A set of tags that will be considered empty tags like "<br/>".
            No Node with any of these tags must contain any content.

        :returns: The tree of Nodes as an ElementTree
        """
        if ET is None:
            import xml.etree.ElementTree as ET
        # import lxml.etree as ET
        attributes = {k: str(v) for k, v in self.attr.items()} if self.has_attr() else {}
        tag_name = xml_tag_name(self.name) if self.name[:1] == ':' else self.name
        if self.children:
            element = ET.Element(tag_name, attrib=attributes)
            # element.extend([child.as_etree(text_tags, empty_tags) for child in self.children])
            children = self.children
            i = 0;  L = len(children);  text = []
            while i < L and children[i].name in string_tags:
                assert not children[i].children
                text.append(children[i].content)
                i += 1
            if text:  element.text = ''.join(text)
            last_element = None
            while i < L:
                while i < L and children[i].name not in string_tags:
                    last_element = children[i].as_etree(ET, string_tags, empty_tags)
                    element.append(last_element)
                    i += 1
                text = []
                while i < L and children[i].name in string_tags:
                    assert not children[i].children
                    text.append(children[i].content)
                    i += 1
                if text and last_element is not None:  last_element.tail = ''.join(text)
        else:
            element = ET.Element(tag_name, attrib=attributes)
            if tag_name in empty_tags:
                assert not self.content
                # element.text = None
            else:
                element.text = self.content
        return element

    @staticmethod
    def from_etree(et, string_tag: str = MIXED_MODE_TEXT_PTYPE) -> Node:
        """Converts a standard-library- or lxml-ElementTree to a tree of nodes.

        :param et:  the root element-object of the ElementTree
        :param string_tag: A tag-name that will be used for the strings
            occurring in mixed content.
        :returns: a tree of nodes.
        """
        sub_elements = et.findall('*')
        if sub_elements:
            children = [Node(string_tag, et.text)] if et.text else []
            for el in sub_elements:
                children.append(Node.from_etree(el, string_tag))
                if el.tail:
                    children.append(Node(string_tag, el.tail))
            node = Node(restore_tag_name(et.tag), tuple(children))
        else:
            node = Node(restore_tag_name(et.tag), et.text or '').with_attr(et.attrib)
        return node


def content_of(segment: Union[Node, Tuple[Node, ...], StringView, str],
               select: PathSelector = LEAF_PATH,
               ignore: PathSelector = NO_PATH) -> str:
    """Returns the string content from a single node or a tuple of Nodes.
    """
    if isinstance(segment, (StringView, str)):
        return str(segment)
    if ignore is NO_PATH and (select is LEAF_PATH or select is ANY_PATH):
        if isinstance(segment, Node):
            return segment.content
        else:
            return ''.join(nd.content for nd in segment)
    if isinstance(segment, Node):  segment = (segment,)
    match_func = create_path_match_function(select)
    skip_func = create_path_match_function(ignore)
    content_list = []
    for root in segment:
        for tr in root.select_path_if(match_func, include_root=True, skip_func=skip_func):
            nd = tr[-1]
            if nd._children or skip_func(tr):  continue
            content_list.append(nd._result)
    return ''.join(content_list)


def _strlen_of(segment: Union[Node, Tuple[Node, ...]],
              match_func: PathMatchFunction = LEAF_PATH,
              skip_func: PathMatchFunction = NO_PATH) -> int:
    if skip_func is NO_PATH and (match_func is LEAF_PATH or match_func is ANY_PATH):
        if isinstance(segment, Node):
            return segment.strlen()
        else:
            return sum(nd.strlen() for nd in segment)
    if isinstance(segment, Node):  segment = (segment,)
    length = 0
    for root in segment:
        for tr in root.select_path_if(match_func, include_root=True, skip_func=skip_func):
            nd = tr[-1]
            if nd._children or skip_func(tr):  continue
            length += len(nd._result)
    return length


def strlen_of(segment: Union[Node, Tuple[Node, ...], StringView, str],
              select: PathSelector = LEAF_PATH,
              ignore: PathSelector = NO_PATH) -> int:
    """Returns the string size from a single node or a tuple of Nodes."""
    if isinstance(segment, (StringView, str)):
        return len(segment)
    match_func = create_path_match_function(select)
    skip_func = create_path_match_function(ignore)
    return _strlen_of(segment, match_func, skip_func)


#######################################################################
#
# Functions related to the Node class
#
#######################################################################


# path strings ########################################################

### EXPERIMENTAL

def path_str(path: Path) -> str:
    """Returns the path a pseudo filepath of tag-names."""
    tag_list = ['']
    for node in path:
        assert not node.name.find('/'), 'path_str() not allowed for tag-names containing "/"!'
        tag_list.append(node.name)
    if path[-1].children:
        tag_list.append('')
    return '/'.join(tag_list)


def match_path_str(path_str: str, glob_pattern: str) -> bool:
    """Matches a path_str against a glob-pattern."""
    from fnmatch import fnmatchcase
    if glob_pattern[0:1] not in ("/", "*"):
        glob_pattern = "*/" + glob_pattern
    return fnmatchcase(path_str, glob_pattern)



# Navigate paths #####################################################

@cython.locals(i=cython.int, k=cython.int)
def prev_path(path: Path) -> Optional[Path]:
    """Returns the path of the predecessor of the last node in the
    path. The predecessor is the sibling of the same parent-node
    preceding the node, or, if it already is the first sibling, the parent's
    sibling preceding the parent, or grandparent's sibling and so on.
    In case no predecessor is found, when the first ancestor has been
    reached, `None` is returned.
    """
    assert isinstance(path, list)
    node = path[-1]
    for i in range(len(path) - 2, -1, -1):
        siblings = path[i]._children
        if node is not siblings[0]:
            for k in range(1, len(siblings)):
                if node is siblings[k]:
                    return path[:i + 1] + [siblings[k - 1]]
            raise AssertionError('Structural Error: path[%i] is not the parent of path[%i]'
                                 % (i, i + 1))
        node = path[i]
    return None


@cython.locals(i=cython.int, k=cython.int)
def next_path(path: Path) -> Optional[Path]:
    """Returns the path of the successor of the last node in the
    path. The successor is the sibling of the same parent Node
    succeeding the node, or if it already is the last sibling, the
    parent's sibling succeeding the parent, or grand parent's sibling and
    so on. In case no successor is found when the first ancestor has been
    reached, `None` is returned.
    """
    assert isinstance(path, list)
    node = path[-1]
    for i in range(len(path) - 2, -1, -1):
        siblings = path[i]._children
        if node is not siblings[-1]:
            for k in range(len(siblings) - 2, -1, -1):
                if node is siblings[k]:
                    return path[:i + 1] + [siblings[k + 1]]
            raise AssertionError('Structural Error: path[%i] is not the parent of path[%i]'
                                 % (i, i + 1))
        node = path[i]
    return None


PickChildFunction: TypeAlias = Callable[[Node], Node]
LAST_CHILD = lambda nd: nd.result[-1]
FIRST_CHILD = lambda nd: nd.result[0]


def zoom_into_path(path: Optional[Path],
                   pick_child: PickChildFunction,
                   steps: int) \
                      -> Optional[Path]:
    """Returns the path of a descendant that follows `steps` generations
    up the tree originating in 'path[-1]`. If `steps` < 0 this will be
    as many generations as are needed to reach a leaf-node.
    The function `pick_child` determines which branch to follow during each
    iteration, as long as the top of the path is not yet a leaf node.
    A `path`-parameter value of `None` will simply be passed through.
    """
    if path:
        trl = path.copy()
        top = trl[-1]
        while top.children and steps != 0:
            top = pick_child(top)
            trl.append(top)
            steps -= 1
        return trl
    return None


leaf_path = functools.partial(zoom_into_path, steps=-1)
next_leaf_path = lambda trl: leaf_path(next_path(trl), FIRST_CHILD)
prev_leaf_path = lambda trl: leaf_path(prev_path(trl), LAST_CHILD)


def foregoing_str(path: Path, length: int = -1) -> str:
    """Returns `length` characters from the string content preceding
    the path."""
    N = 0
    l = []
    trl = prev_path(path)
    while trl and (N < length or length < 0):
        s = trl[-1].content
        l.append(s)
        N += len(s)
        trl = prev_path(trl)
    foregoing = ''.join(reversed(l))
    return foregoing if length < 0 else foregoing[-length:]


def ensuing_str(path: Path, length: int = -1) -> str:
    """Returns `length` characters from the string content succeeding
    the path."""
    N = 0
    l = []
    trl = next_path(path)
    while trl and (N < length or length < 0):
        s = trl[-1].content
        l.append(s)
        N += len(s)
        trl = next_path(trl)
    following = ''.join(l)
    return following if length < 0 else following[:length]


def select_path_if(start_path: Path,
                   match_func: PathMatchFunction,
                   include_root: bool = False,
                   reverse: bool = False,
                   skip_func: PathMatchFunction = NO_PATH) -> Iterator[Path]:
    """
    Creates an Iterator yielding all `paths` for which the
    `match_function` is true, starting from `path`.
    """

    def recursive(trl):
        nonlocal match_func, reverse, skip_func
        if match_func(trl):
            yield trl
        top = trl[-1]
        child_iterator = reversed(top._children) if reverse else top._children
        for child in child_iterator:
            child_trl = trl + [child]
            if not skip_func(child_trl):
                yield from recursive(child_trl)

    path = start_path.copy()
    while path:
        if include_root:
            yield from recursive(path)
        else:
            include_root = True
        node = path.pop()
        edge, delta = (0, -1) if reverse else (-1, 1)
        while path and node is path[-1]._children[edge]:
            if match_func(path):
                yield path
            node = path.pop()
        if path:
            parent = path[-1]
            i = parent.index(node)
            nearest_sibling = parent._children[i + delta]
            path.append(nearest_sibling)
            # include_root = True


def select_path(start_path: Path,
                criteria: PathSelector,
                include_root: bool = False,
                reverse: bool = False,
                skip_subtree: PathSelector = NO_PATH) -> Iterator[Path]:
    """
    Like `select_path_if()` but yields the entire path (i.e. list of
    descendants, the last one being the matching node) instead of just
    the matching nodes.
    """
    return select_path_if(start_path, create_path_match_function(criteria),
                          include_root, reverse, create_path_match_function(skip_subtree))


def pick_path(start_path: Path,
              criteria: PathSelector,
              include_root: bool = False,
              reverse: bool = False,
              skip_subtree: PathSelector = NO_PATH) -> Optional[Path]:
    """
    Like ``Node.pick()``, only that the entire path (i.e. chain of descendants)
    relative to `self` is returned.
    """
    try:
        return next(select_path(
            start_path, criteria, include_root=include_root, reverse=reverse,
            skip_subtree=skip_subtree))
    except StopIteration:
        return None


def select_from_path_if(path: Path,
                        match_func: NodeMatchFunction,
                        reverse: bool=False) -> Iterator[Node]:
    """Yields all nodes from path for which the match_function is true."""
    if reverse:
        for nd in reversed(path):
            if match_func(nd):
                yield nd
    else:
        for nd in path:
            if match_func(nd):
                yield nd


def select_from_path(path: Path, criteria: NodeSelector, reverse: bool=False) \
        -> Iterator[Node]:
    """Yields all nodes from path which fulfill the criterion."""
    return select_from_path_if(path, create_match_function(criteria), reverse)


def pick_from_path(path: Path, criterion: NodeSelector, reverse: bool=False) \
        -> Optional[Node]:
    """Picks the first node from the path that fulfils the criterion. Returns `None`
    if the path does not contain any node fulfilling the criterion."""
    try:
        return next(select_from_path(path, criterion, reverse=reverse))
    except StopIteration:
        return None


def find_common_ancestor(path_A: Path, path_B: Path) -> Tuple[Optional[Node], int]:
    """Returns the last common ancestor of path_A, path_B and its index
    in the path. If there is no common ancestor (None, undefined integer)
    is returned.
    """
    common_ancestor = None
    i = 0
    last_a = [path_A[0]]
    last_b = [path_B[0]]
    for i, (a, b) in enumerate(zip(path_A, path_B)):
        if a != b or a not in last_a or b not in last_b:  break
        common_ancestor = a
        last_a = a
        last_b = b
    else:
        i += 1
    i -= 1
    return common_ancestor, i


def pp_path(path: Path, with_content: int = 0, delimiter: str = ' <- ') \
        -> str:
    """Serializes a path as string.

    :param path: the path to be serialized.
    :param with_content: the number of nodes from the end of the path for
        which the content will be displayed next to the name.
    :param delimiter: The delimiter separating the nodes in the returned string.
    :returns: the string-serialization of the given path.
    """
    if with_content == 0:
        steps = [nd.name for nd in path]
    else:
        n = with_content if with_content > 0 else len(path)
        steps = [nd.name for nd in path[:-n]]
        steps.extend(f'{nd.name} "{nd.content}"' for nd in path[-n:])
    return delimiter.join(steps)


def path_sanity_check(path: Path) -> bool:
    """Checks whether the nodes following in the path-list are really
    immediate descendants of each other."""
    return all(path[i] in path[i - 1]._children for i in range(1, len(path)))


# splitting and insertion of nodes ####################################


def insert_node(leaf_path: Path, rel_pos: int, node: Node,
                divisable_leaves: Container = LEAF_PTYPES) -> Node:
    """Inserts a node at a specific position into the last or
    eventually second but last node in the path. The path must be
    a "leaf"-path, i.e. a path that ends in a leaf. Returns the
    parent of the newly inserted node."""
    assert leaf_path
    leaf = leaf_path[-1]
    leaf_len = leaf.strlen()
    assert not leaf.children
    assert rel_pos <= leaf_len
    if len(leaf_path) >= 2:
        parent = leaf_path[-2]
        i = parent.index(leaf)
        if rel_pos == 0:
            parent.insert(i, node)
            return parent
        if rel_pos == leaf_len:
            parent.insert(i + 1, node)
            return parent
        if leaf.name in divisable_leaves:
            content = leaf.content
            parent.result = parent.result[:i] + \
                            (Node(leaf.name, content[:rel_pos]), node,
                             Node(leaf.name, content[rel_pos:])) + \
                            parent.result[i + 1:]
            return parent
    if rel_pos == 0:
        leaf.result = (node, Node(leaf.name, leaf.content))
    elif rel_pos == leaf_len:
        leaf.result = (Node(leaf.name, leaf.content), node)
    else:
        content = leaf.content
        leaf.result = (Node(leaf.name, content[:rel_pos]), node,
                       Node(leaf.name, content[rel_pos:]))
    return leaf


chain_id = 4231
chain_step = 4231
chain_len = 3
chain_modulo = 23 ** chain_len
chain_letters = "ABCDEFGHKLMNPQRSTUVWXYZ"


def reset_chain_ID(chain_length: int = 3):
    """For testing and debugging, reset the chain_id counter to ensure
    deterministic results.

    :param chain_length: The staring length of the letter-chain used
        as ID value
    """
    global chain_id, chain_step, chain_len, chain_modulo
    assert chain_length >= 3
    multiplier = 23 ** (chain_length - 3)
    chain_id = 4231 * multiplier
    chain_step = 4231 * multiplier
    chain_len = chain_length
    chain_modulo = 23 ** chain_len


def gen_chain_ID() -> str:
    """Generate a unique chain-ID for marking splitted nodes or tags,
    for that matter.

    Chain-IDs in different threads or processes can be identical. It is assumed
    that one tree is not processed by several threads at the same time."""
    global chain_id, chain_step, chain_len, chain_modulo
    chain_id = (chain_id + chain_step) % chain_modulo
    if chain_id == chain_step:
        chain_step = chain_step * 23 - 1
        chain_id = chain_step
        chain_len += 1
        chain_modulo *= 23
    c = chain_id
    cid = []
    while c > 0:
        cid.append(chain_letters[c % 23])
        c = c // 23
    while len(cid) < chain_len:
        cid.append('A')
    return ''.join(cid)


@cython.locals(k=cython.int)
def split(node: Node, parent: Node, i: cint, left_biased: bool = True,
          chain_attr: Optional[dict] = None) -> int:
    """Splits a node at the given index (in case of a branch-node) or
    string-position (in case of a leaf-node). Returns the index of the
    right part within the parent node after the split. (This means
    that with ``node.insert(index, nd)`` nd will be inserted (exactly at
    the split location.)

    Non-anonymous node that have been split will be marked by updateing
    their attribute-dictionary with the chain_attr-dictionary if given.

    Examples::

        >>> test_tree = parse_sxpr('(X (A "Hello, ") (B "Peter") (C " Smith"))').with_pos(0)
        >>> X = copy.deepcopy(test_tree)

        # test edge cases first
        >>> split(X['B'], X, 0)
        1
        >>> print(X.as_sxpr())
        (X (A "Hello, ") (B "Peter") (C " Smith"))
        >>> split(X['B'], X, X['B'].strlen())
        2
        >>> print(X.as_sxpr())
        (X (A "Hello, ") (B "Peter") (C " Smith"))

        # standard case
        >>> split(X['B'], X, 2)
        2
        >>> print(X.as_sxpr())
        (X (A "Hello, ") (B "Pe") (B "ter") (C " Smith"))
        >>> print(X.pick('B', reverse=True).pos)
        9

        # use split() as preparation for adding markup
        >>> X = copy.deepcopy(test_tree)
        >>> a = split(X['A'], X, 6)
        >>> a
        1
        >>> b = split(X['C'], X, 1)
        >>> b
        4
        >>> print(X.as_sxpr())
        (X (A "Hello,") (A " ") (B "Peter") (C " ") (C "Smith"))
        >>> markup = Node('em', X[a:b]).with_pos(X[a].pos)
        >>> X.result = X[:a] + (markup,) + X[b:]
        >>> print(X.as_sxpr())
        (X (A "Hello,") (em (A " ") (B "Peter") (C " ")) (C "Smith"))

        # a more complex case: add markup to a nested tree
        >>> X = parse_sxpr('(X (A "Hello, ") (B "Peter") (bold (C " Smith")))').with_pos(0)
        >>> a = split(X['A'], X, 6)
        >>> b0 = split(X['bold']['C'], X['bold'], 1)
        >>> b0
        1
        >>> print(X.as_sxpr())
        (X (A "Hello,") (A " ") (B "Peter") (bold (C " ") (C "Smith")))
        >>> b = split(X['bold'], X, b0)
        >>> b
        4
        >>> print(X.as_sxpr())
        (X (A "Hello,") (A " ") (B "Peter") (bold (C " ")) (bold (C "Smith")))
        >>> markup = Node('em', X[a:b]).with_pos(X[a].pos)
        >>> X.result = X[:a] + (markup,) + X[b:]
        >>> print(X.as_sxpr())
        (X (A "Hello,") (em (A " ") (B "Peter") (bold (C " "))) (bold (C "Smith")))

        # use left_bias hint for potentially ambiguous cases:
        >>> X = parse_sxpr('(X (A ""))')
        >>> split(X['A'], X, X['A'].strlen())
        0
        >>> split(X['A'], X, X['A'].strlen(), left_biased=False)
        1
    """
    assert i >= 0
    k = parent.index(node) + 1
    if left_biased:
        if i == 0:  return k - 1
        if i == len(node._result):  return k
    else:
        if i == len(node._result):  return k
        if i == 0:  return k - 1
    right = Node(node.name, node._result[i:])
    if node.has_attr():  right.with_attr(node.attr)
    if  right._children:  right._pos = right._result[0]._pos
    elif node._pos >= 0:  right._pos = node._pos + i
    node.result = node._result[:i]
    # if chain_attr and not node.anonymous:
    if chain_attr and not node.anonymous:
        node.attr.update(chain_attr)
        right.attr.update(chain_attr)
    parent.result = parent._result[:k] + (right,) + parent.result[k:]
    return k


@cython.locals(L=cython.int)
def deep_split(path: Path, i: cint, left_biased: bool=True,
               greedy: bool=True,
               match_func: PathMatchFunction = ANY_PATH,
               skip_func: PathMatchFunction = NO_PATH,
               chain_attr_name: str = '') -> int:
    """Split all nodes from the end of the path up to the i-th element,
    but excluding the first node in the path. Returns the index of the
    split-location in the first node of the path.

    Exapmles::

        >>> from DHParser.toolkit import printw
        >>> tree = parse_sxpr('(X (s "") (A (u "") (C "One, ") (D "two, ")) '
        ...                   '(B (E "three, ") (F "four!") (t "")))')
        >>> X = copy.deepcopy(tree)
        >>> C = X.pick_path('C')
        >>> a = deep_split(C, 0)
        >>> a
        1
        >>> F = X.pick_path('F', reverse=True)
        >>> b = deep_split(F, F[-1].strlen(), left_biased=False)
        >>> b
        3
        >>> printw(X.as_sxpr())
        (X (s) (A (u) (C "One, ") (D "two, ")) (B (E "three, ") (F "four!") (t)))
        >>> a = deep_split(C, 0, greedy=False)
        >>> a
        2
        >>> b = deep_split(F, F[-1].strlen(), left_biased=False, greedy=False)
        >>> b
        4
        >>> printw(X.as_sxpr(flatten_threshold=-1))
        (X (s) (A (u)) (A (C "One, ") (D "two, ")) (B (E "three, ") (F "four!"))
         (B (t)))

        >>> X = copy.deepcopy(tree).with_pos(0)
        >>> C = X.pick_path('C')
        >>> a = deep_split(C, 4)
        >>> E = X.pick_path('E')
        >>> b = deep_split(E, 0, left_biased=False)
        >>> a, b
        (2, 3)
        >>> printw(X.as_sxpr(flatten_threshold=-1))
        (X (s) (A (u) (C "One,")) (A (C " ") (D "two, ")) (B (E "three, ") (F "four!")
         (t)))
        >>> X.result = X[:a] + (Node('em', X[a:b]).with_pos(X[a].pos),) + X[b:]
        >>> printw(X.as_sxpr(flatten_threshold=-1))
        (X (s) (A (u) (C "One,")) (em (A (C " ") (D "two, "))) (B (E "three, ")
         (F "four!") (t)))

        # edge cases
        >>> Y = parse_sxpr('(Y "123")')
        >>> deep_split([Y], 1)
        1
        >>> print(Y.as_sxpr())
        (Y "123")
    """
    # match_func = create_path_match_function(select)
    # skip_func = create_path_match_function(ignore)
    parent = path[-1]
    last_index = len(path)
    chain_attr = {}
    for idx in range(2, last_index + 1):
        node = parent
        parent = path[-idx]
        if chain_attr_name:  chain_attr = {chain_attr_name: gen_chain_ID()}
        i = split(node, parent, i, left_biased, chain_attr)
        if greedy and idx < last_index:
            if left_biased:
                if i > 0 and _strlen_of(parent.children[:i], match_func, skip_func) == 0:  i = 0
            else:
                L = len(parent.children)
                if i < L and _strlen_of(parent.children[i:], match_func, skip_func) == 0:  i = L
    return i


@cython.locals(L=cython.int)   # k=cython.int does not work!!!
def can_split(t: Path, i: cint, left_biased: bool = True, greedy: bool = True,
              match_func: PathMatchFunction = ANY_PATH,
              skip_func: PathMatchFunction = NO_PATH,
              divisable: AbstractSet[str] = LEAF_PTYPES) -> int:
    """Returns the negative index of the first node in the path, from which
    on all nodes can be split or do not need to be split, because the
    split-index lies to the left or right of the node.

    Examples::

        >>> tree = parse_sxpr('(doc (p (:Text "ABC")))')
        >>> can_split([tree, tree[0], tree[0][0]], 1)
        -1
        >>> can_split([tree, tree[0], tree[0][0]], 0)
        -2
        >>> can_split([tree, tree[0], tree[0][0]], 3)
        -2
        >>> # anonymous nodes, like ":Text" are always divisable
        >>> can_split([tree, tree[0], tree[0][0]], 1, divisable=set())
        -1
        >>> # However, non anonymous nodes aren't ...
        >>> tree = parse_sxpr('(doc (p (Text "ABC")))')
        >>> can_split([tree, tree[0], tree[0][0]], 1, divisable=set())
        0
        >>> # ... unless explicitly mentioned
        >>> tree = parse_sxpr('(doc (p (Text "ABC")))')
        >>> can_split([tree, tree[0], tree[0][0]], 1, divisable={'Text'})
        -1
        >>> tree = parse_sxpr('(X (Z "!?") (A (B "123") (C "456")))')
        >>> can_split(tree.pick_path('B'), 0)
        -2

        # edge cases
        >>> can_split([parse_sxpr('(p "123")')], 1)
        0
        >>> can_split([parse_sxpr('(:Text "123")')], 1)
        0
    """
    if len(t) <= 1:  return 0

    # make a shallow copy of the path's nodes, first.
    t2 = [copy.copy(nd) for nd in t]
    for k in range(1, len(t2)):
        t2[k - 1].result = tuple((t2[k] if nd == t[k] else nd) for nd in t2[k - 1].result)
    t = t2

    k = 0
    for k in range(len(t) - 1):
        node = t[-k - 1]
        if i != 0 and i != len(node._result) and not (node.anonymous or node.name in divisable):
            break
        parent = t[-k - 2]
        i = split(node, parent, i, left_biased)
        if greedy:
            if left_biased:
                if i > 0 and _strlen_of(parent.children[:i], match_func, skip_func) == 0:  i = 0
            else:
                L = len(parent.children)
                if i < L and _strlen_of(parent.children[i:], match_func, skip_func) == 0:  i = L
    else:
        # node = t[0]
        k += 1
    return -k


def markup_leaf(node: Node, start: int, end: int, name: str, *attr_dict, **attributes):
    """Adds markup to a leaf node, incidentally turning the leaf node into a branch node."""
    assert not node._children
    seg_1 = Node(TOKEN_PTYPE, node._result[:start])
    seg_1._pos = node._pos
    seg_2 = Node(name, node._result[start:end]).with_attr(*attr_dict, **attributes)
    seg_2._pos = node._pos + start if node._pos >= 0 else -1
    seg_3 = Node(TOKEN_PTYPE, node._result[end:])
    seg_3._pos = node._pos + end if node._pos >= 0 else -1
    node.result = tuple(nd for nd in (seg_1, seg_2, seg_3) if nd._result)


#######################################################################
#
# ContentMapping: A "string-view" on node-trees
#
#######################################################################

@cython.locals(k=cython.int)
def markup_right(path: Path, i: cint, name: str, attr_dict: Dict[str, Any],
                 greedy: bool = True,
                 match_func: PathMatchFunction = ANY_PATH,
                 skip_func: PathMatchFunction = NO_PATH,
                 divisable: AbstractSet[str] = LEAF_PTYPES,
                 chain_attr_name: str = ''):
    """Markup the content from string position i within the last node of
    the path up to the very end of the content of the first node of the
    path.

    This is a helper function for :py:math:`ContentMapping.markup`.

    Examples::

        >>> tree = parse_sxpr('(X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))')
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> all_tags = {'A', 'B', 'C', 'D', 'E', 'F', 'X'}
        >>> markup_right(C_path, 2, 'em', dict(), divisable=all_tags)
        >>> print(X.as_sxpr())
        (X (A (C "12")) (em (A (C "3") (D "456")) (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> markup_right(C_path, 2, 'em', dict(), divisable=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (C "12") (em (C "3") (D "456"))) (em (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_right(D_path, 2, 'em', dict(), divisable=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "45") (em (D "6"))) (em (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_right(D_path, 2, 'em', dict(), divisable=all_tags - {'A', 'D'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D (:Text "45") (em "6"))) (em (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_right(E_path, 1, 'em', dict(), divisable=all_tags - {'E'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E (:Text "7") (em "89")) (em (F "abc"))) (em (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_right(E_path, 1, 'em', dict(), divisable=all_tags - {'B'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "7") (em (E "89") (F "abc"))) (em (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_right(E_path, 1, 'em', dict(), divisable=all_tags)
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "7")) (em (B (E "89") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> G_path = X.pick_path('G')
        >>> markup_right(E_path, 3, 'em', dict(), divisable=all_tags)
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))

        # edge cases
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 1, 'em', dict(), divisable={'A'})
        >>> print(X.as_sxpr())
        (A (:Text "1") (em "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 1, 'em', dict(), divisable=set())
        >>> print(X.as_sxpr())
        (A (:Text "1") (em "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 0, 'em', dict(), divisable={'A'})
        >>> print(X.as_sxpr())
        (A (em "123"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 3, 'em', dict(), divisable={'A'})
        >>> print(X.as_sxpr())
        (A "123")
    """
    assert path
    k = max(can_split(path, i, True, greedy, match_func, skip_func, divisable) - 1, -len(path))
    # k is parent-index of first node to split
    i = deep_split(path[k:], i, True, greedy, match_func, skip_func, chain_attr_name)

    if chain_attr_name and chain_attr_name not in attr_dict:
        attr_dict[chain_attr_name] = gen_chain_ID()

    nd = Node(name, path[k]._result[i:]).with_attr(attr_dict)
    if nd._children:
        nd._pos = path[k]._result[i]._pos
        path[k].result = path[k]._result[:i] + (nd,)
    elif nd._result:
        nd._pos = path[k]._pos + i if path[k]._pos >= 0 else -1
        text_node = Node(TOKEN_PTYPE, path[k]._result[:i])
        text_node._pos = path[k]._pos
        path[k].result = (text_node, nd) if text_node._result else (nd,)

    k -= 1
    while abs(k) <= len(path):
        i = path[k].index(path[k + 1]) + 1
        if i < len(path[k]._result):
            nd = Node(name, path[k]._result[i:]).with_attr(attr_dict)
            nd._pos = path[k]._result[i]._pos
            path[k].result = path[k]._result[:i] + (nd,)
        k -= 1

    assert not any(nd.name == ':Text' and nd.children for nd in path)


@cython.locals(k=cython.int)
def markup_left(path: Path, i: cint, name: str, attr_dict: Dict[str, Any],
                greedy: bool = True,
                match_func: PathMatchFunction = ANY_PATH,
                skip_func: PathMatchFunction = NO_PATH,
                divisable: AbstractSet[str] = LEAF_PTYPES,
                chain_attr_name: str = ''):
    """Markup the content from string position i within the last node of
    the path up to the very end of the content of the first node of the
    path.

    This is a helper function for :py:math:`ContentMapping.markup`.

    Examples::

        >>> tree = parse_sxpr('(X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))')
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> all_tags = {'A', 'B', 'C', 'D', 'E', 'F', 'X'}
        >>> markup_left(C_path, 2, 'em', dict(), divisable=all_tags)
        >>> print(X.as_sxpr())
        (X (em (A (C "12"))) (A (C "3") (D "456")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> markup_left(C_path, 2, 'em', dict(), divisable=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (em (C "12")) (C "3") (D "456")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> markup_left(C_path, 0, 'em', dict(), divisable=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_left(D_path, 2, 'em', dict(), divisable=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (em (C "123") (D "45")) (D "6")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_left(D_path, 2, 'em', dict(), divisable=all_tags - {'A', 'D'})
        >>> print(X.as_sxpr())
        (X (A (em (C "123")) (D (em "45") (:Text "6"))) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_left(E_path, 1, 'em', dict(), divisable=all_tags - {'E'})
        >>> print(X.as_sxpr())
        (X (em (A (C "123") (D "456"))) (B (E (em "7") (:Text "89")) (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_left(E_path, 1, 'em', dict(), divisable=all_tags - {'B'})
        >>> print(X.as_sxpr())
        (X (em (A (C "123") (D "456"))) (B (em (E "7")) (E "89") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_left(E_path, 1, 'em', dict(), divisable=all_tags)
        >>> print(X.as_sxpr())
        (X (em (A (C "123") (D "456")) (B (E "7"))) (B (E "89") (F "abc")) (G "def"))

        # edge cases
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 1, 'em', dict(), divisable={'A'})
        >>> print(X.as_sxpr())
        (A (em "1") (:Text "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 1, 'em', dict(), divisable=set())
        >>> print(X.as_sxpr())
        (A (em "1") (:Text "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 3, 'em', dict(), divisable={'A'})
        >>> print(X.as_sxpr())
        (A (em "123"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 0, 'em', dict(), divisable={'A'})
        >>> print(X.as_sxpr())
        (A "123")
    """
    assert path
    k = max(can_split(path, i, False, greedy, match_func, skip_func, divisable) - 1, -len(path))
    i = deep_split(path[k:], i, False, greedy, match_func, skip_func, chain_attr_name)

    if chain_attr_name and chain_attr_name not in attr_dict:
        attr_dict[chain_attr_name] = gen_chain_ID()

    nd = Node(name, path[k]._result[:i]).with_attr(attr_dict)
    nd._pos = path[k]._pos
    if nd._children:
        path[k].result = (nd,) + path[k]._result[i:]
    elif nd._result:
        text_node = Node(TOKEN_PTYPE, path[k]._result[i:])
        text_node._pos = path[k]._pos + i if path[k]._pos >= 0 else -1
        path[k].result = (nd, text_node) if text_node._result else (nd,)

    k -= 1
    while abs(k) <= len(path):
        i = path[k].index(path[k + 1])
        if i > 0:
            nd = Node(name, path[k]._result[:i]).with_attr(attr_dict)
            nd._pos = path[k]._pos
            path[k].result = (nd,) + path[k]._result[i:]
        k -= 1

    assert not any(nd.name == ':Text' and nd.children for nd in path)


def _breed_leaf_selector(select: PathSelector,
                                ignore: PathSelector) -> Tuple[Callable, Callable]:
    select_func = create_path_match_function(select)
    ignore_func = create_path_match_function(ignore)

    def general_match_func(path: Path) -> bool:
        if path[-1]._children:
            if select_func(path):
                raise ValueError(f'Selector "{select}" should yield only leaf-paths! But '
                    f'the last element "{path[-1].name}" of path "{pp_path(path)}" has '
                    f'children: {", ".join(child.name for child in path[-1].children)}! '
                    f'Use leaf_path({select}) to circumvent this error.')
            return False
        return select_func(path) and not ignore_func(path)

    if select == LEAF_PATH and ignore == NO_PATH:
        match_func = LEAF_PATH
    else:
        match_func = general_match_func

    return match_func, ignore_func


def leaf_paths(criterion: PathSelector) -> PathMatchFunction:
    """Creates a path-match function that matches only and all leaf path
    for those paths that the criterion matches. Warning: This may be
    slower than a custom algorithm that matches only leaf-poth right
    from the start. Example::

        >>> xml = '''<doc><p>In München<footnote><em>München</em> is the German
        ... name of the city of Munich</footnote> is a Hofbräuhaus</p></doc>'''
        >>> tree = parse_xml(xml)
        >>> for path in tree.select_path(leaf_paths('footnote')):
        ...    pp_path(path, 1)
        'doc <- p <- footnote <- em "München"'
        'doc <- p <- footnote <- :Text " is the German\\nname of the city of Munich"'

    Compare this with the result without the leaf_paths-filter::

        >>> for path in tree.select_path('footnote'):
        ...    pp_path(path, 1)
        'doc <- p <- footnote "München is the German\\nname of the city of Munich"'
    """

    match_func = create_path_match_function(criterion)

    def leaf_match_func(path: Path) -> bool:
        if path[-1]._children:  return False
        for i in range(len(path), 0, -1):
            if match_func(path[:i]):
                return True
        return False

    return leaf_match_func


class ContentMapping:
    """
    ContentMapping represents a path-mapping of the string-content of all or a
    specific selection of the leave-nodes of a tree. A content-mapping is an ordered
    mapping of the first text position of every (selected) leaf-node to the
    path of this node.

    Path-mappings allow to search the flat document with regular expressions or
    simple text search and then changing the tree at the appropriate places,
    for example by adding markup (i.e. nodes) in these places.

    The ContentMapping class provides methods for adding markup-nodes.
    In cases where the new markup-nodes cut across the existing tree-hierarchy,
    the markup-method takes care of splitting up either the newly created or
    some of the existing nodes to fit in the markup.

    Public properties:

    :ivar path_list: A list of paths covering the selected leaves of the tree from
        left to right.
    :ivar pos_list: The list of positions of the paths in ``path_list``

    Location-related instance variables:

    :ivar origin: The orogin of the tree for which a path mapping shall be
        generated. This can be a branch of another tree and therefore does not
        need to be a RootNode-object.
    :ivar select_func: Only leaf-paths for which this is true will be considered when
        generating the content-mapping. This function integrates both the select-
        and ignore-criteria passed to the constructor of the class. Note that the
        select-criterion must only accept leaf-paths. Otherwise a ValueError will
        be raised.
    :ivar ignore_func: The ignore function derives from the ignore-parameter of
        the ``__init__()``-construcotr of class ContentMapping.
    :ivar content: The string content of the selected parts of the tree.

    Markup-related instance variables:

    :ivar greedy: If True, the algorithm for adding markup minimizes the number
        of required cuts by switching child and parent nodes if the markup fills
        up a node completely as well as including empty nodes in the markup.
        In any the case string content of the added markup remains the same, but
        it might cover more tags than strictly necessary.
    :ivar chain_attr: An attribute that will receive one and the same identifier as
        value for all nodes belonging to the chain of on split-up node.
    :ivar auto_cleanup: Update the content mapping after the markup has been finished.
        Should always be true, if it is intended to reuse the same content mapping
        for further markups in the same range or other purposes.
    :param divisability: A dictionary that contains the information which tags
        (or nodes as identified by their name) are "harder" than other tags. Each
        key-tag in the dictionary is harder than (i.e. is  allowed to split up) up
        all tags in the associated value (which is a set of node, or for that matter,
        tag-names). Tag or node-names associated to the wildcard key ``*`` can be split
        by any tag.

        If the markup-method reaches nodes that cannot be split, it will split
        the markup-node instead to cover the string to be marked up, completely.
    """

    def __init__(self, origin: Node,
                 select: PathSelector = LEAF_PATH,
                 ignore: PathSelector = NO_PATH,
                 greedy: bool = True,
                 divisability: Union[Dict[str, Container], Container, str] = LEAF_PTYPES,
                 chain_attr_name: str = '',
                 auto_cleanup: bool = True):
        self.origin: Node = origin
        select_func, ignore_func = _breed_leaf_selector(select, ignore)
        self.select_func: PathMatchFunction = select_func
        self.ignore_func: PathMatchFunction = ignore_func
        self.greedy: bool = greedy
        if isinstance(divisability, Dict):
            if '*' not in divisability:  divisability['*'] = set()
            self.divisability: Dict[str, Container] = divisability
        elif isinstance(divisability, str):
            for delimiter in (';', ',', ' '):
                lst = divisability.split(delimiter)
                if len(lst) > 1:
                    self.divisability = {'*': {s.strip() for s in lst}}
                    break
            else:
                raise ValueError(f'String value "{divisability}" of parameter "divisability" '
                                 f'does not look like a list node-names!')
        else:
            self.divisability = {'*': divisability}
        self.chain_attr_name: str = chain_attr_name
        self.auto_cleanup = auto_cleanup

        content, pos_list, path_list = self._generate_mapping(origin)
        self.content: str = content
        self._pos_list: List[int] = pos_list
        self._path_list: List[Path] = path_list

    def _generate_mapping(self, origin, stump: Path = []) \
            -> Tuple[str, List[int], List[Path]]:
        """Generates the string content, list of positions and list of paths
        for the given origin taking into account ``self.select_func`` and
        ``self.ignore_func`` as constraints."""
        pos = 0
        content_list = []
        path_list = []
        pos_list = []
        select_func = (lambda pth: self.select_func(stump + pth)) if stump else self.select_func
        if self.ignore_func([origin]):
            return '', [], []
        for trl in origin.select_path_if(
                select_func, include_root=True, skip_func=self.ignore_func):
            #  if self.ignore_func(trl):  continue
            pos_list.append(pos)
            path_list.append(trl)
            content_list.append(trl[-1].content)
            pos += trl[-1].strlen()
        return ''.join(content_list), pos_list, path_list

    def __str__(self):
        """Pretty-prints the content mapping. The format is:
        Test-Position -> List of node-names, the last node as S-expression without
        outer brackets. Example::

            >>> tree = parse_sxpr('(a (b "123") (c (d "45") (e "67")))')
            >>> cm = ContentMapping(tree)
            >>> print(cm)
            0 -> a, b "123"
            3 -> a, c, d "45"
            5 -> a, c, e "67"
        """
        assert len(self.pos_list) == len(self.path_list)
        lines = []
        for i in range(len(self.pos_list)):
            position = self.pos_list[i]
            path = [nd.name for nd in self.path_list[i][:-1]]
            last = self._path_list[i][-1]
            path.append(flatten_sxpr(last.as_sxpr())[1:-1])
            s = ', '.join(s for s in path)
            lines.append(f'{position} -> {s}')
        return '\n'.join(lines)

    @property
    def path_list(self) -> List[Path]:
        return self._path_list

    @property
    def pos_list(self) -> List[int]:
        return self._pos_list

    @cython.locals(path_index=cython.int, last=cython.int)
    def get_path_index(self, pos: cint, left_biased: bool = False) -> int:
        """Yields the index for the path in given context-mapping that contains
        the position ``pos``.

        :param pos:   a position in the content of the tree for which the
            path mapping ``cm`` was generated
        :param left_biased: yields the location after the end of the previous
            path rather than the location at the very beginning of the
            next path. Default value is "False".
        :returns:   the integer index of the path in self.path_list that
            covers the given position ``pos``
        :raises:    IndexError if not 0 <= position < length of document

        Example::

            >>> tree = parse_sxpr('(a (b "123") (c (d "45") (e "67")))')
            >>> cm = ContentMapping(tree)
            >>> i = cm.get_path_index(4)
            >>> path = cm.path_list[i]
            >>> print(pp_path(path, 1, ', '))
            a, c, d "45"
        """
        errmsg = lambda i: f'Illegal position value {i}. ' \
                           f'Must be 0 <= position < length of text!'
        if pos < 0:  raise IndexError(errmsg(pos))
        try:
            path_index = bisect.bisect_right(self._pos_list, pos) - 1
            if left_biased:
                while path_index > 0 and pos - self._pos_list[path_index] == 0:
                    path_index -= 1
            else:
                last = len(self._pos_list) - 1
                pivot = self._pos_list[path_index]
                while path_index < last and self._pos_list[path_index + 1] == pivot:
                    path_index += 1
        except IndexError:
            raise IndexError(errmsg(pos))
        return path_index

    def get_path_and_offset(self, pos: int, left_biased: bool = False) -> Tuple[Path, int]:
        """Yields the path and relative position for the absolute
        position ``pos``. See :py:meth:`ContentMappin.get_path_index` for the description
        of the parameters.

        :returns:   tuple (path, offset) where the offset is the position of
            ``pos`` relative to the actual position of the last node in the path.
        :raises:    IndexError if not 0 <= position < length of document
        """
        path_index = self.get_path_index(pos, left_biased)
        return self._path_list[path_index], pos - self._pos_list[path_index]

    @cython.locals(a=cython.int, b=cython.int, index_a=cython.int, index_b=cython.int)
    def iterate_paths(self, start_pos: cint, end_pos: cint, left_biased: bool = False) \
            -> Iterator[Path]:
        """Yields all paths from position ``start_pos`` up to and including
        position ``end_pos``. Example::

            >>> tree = parse_sxpr('(a (b "123") (c (d "456") (e "789")) (f "ABC"))')
            >>> cm = ContentMapping(tree)
            >>> [[nd.name for nd in p] for p in cm.iterate_paths(1, 12)]
            [['a', 'b'], ['a', 'c', 'd'], ['a', 'c', 'e'], ['a', 'f']]
        """
        index_a = self.get_path_index(start_pos, left_biased)
        index_b = self.get_path_index(end_pos, left_biased)
        for i in range(index_a, index_b + 1):
            yield self._path_list[i]

    @cython.locals(i=cython.int, start_pos=cython.int, end_pos=cython.int, offset=cython.int)
    def rebuild_mapping_slice(self, first_index: cint, last_index: cint):
        """Reconstructs a particular section of the context mapping after the
        underlying tree has been restructured. Ohter than
        :py:meth:`ContentMappin.rebuild_mapping`, the section that needs repairing
        if here defined by the path indices and not the string positions.

        :param first_index: The index (not the position within the string-content!)
            of the first path that has been affected by restruturing of the tree.
            Use :py:meth:`ContentMapping.get_path_index` to determine the path-index
            if only the position is known.
        :param last_index: The index (not the position within the string-content!)
            of the last path that has been affected by restruturing of the tree.
            Use :py:meth:`ContentMapping.get_path_index` to determine the path-index
            if only the position is known.

        Examples::

            >>> tree = parse_sxpr('(a (b (c "123") (d "456")) (e (f (g "789") (h "ABC")) (i "DEF")))')
            >>> cm = ContentMapping(tree)
            >>> print(cm)
            0 -> a, b, c "123"
            3 -> a, b, d "456"
            6 -> a, e, f, g "789"
            9 -> a, e, f, h "ABC"
            12 -> a, e, i "DEF"
            >>> b = tree.pick('b')
            >>> b.result = (b[0], Node('x', 'xyz'), b[1])
            >>> cm.rebuild_mapping_slice(0, 1)
            >>> print(cm)
            0 -> a, b, c "123"
            3 -> a, b, x "xyz"
            6 -> a, b, d "456"
            9 -> a, e, f, g "789"
            12 -> a, e, f, h "ABC"
            15 -> a, e, i "DEF"
            >>> cm.auto_cleanup = False
            >>> common_ancestor = cm.markup(10, 16, 'Y')
            >>> print(common_ancestor.as_sxpr())
            (e (f (g (:Text "7") (Y "89")) (Y (h "ABC"))) (i (Y "D") (:Text "EF")))
            >>> print(cm)
            0 -> a, b, c "123"
            3 -> a, b, x "xyz"
            6 -> a, b, d "456"
            9 -> a, e, f, g (:Text "7") (Y "89")
            12 -> a, e, f, h "ABC"
            15 -> a, e, i (Y "D") (:Text "EF")
            >>> a = cm.get_path_index(10)
            >>> b = cm.get_path_index(16, left_biased=True)
            >>> a, b
            (3, 5)
            >>> cm.rebuild_mapping_slice(3, 5)
            >>> print(cm)
            0 -> a, b, c "123"
            3 -> a, b, x "xyz"
            6 -> a, b, d "456"
            9 -> a, e, f, g, :Text "7"
            10 -> a, e, f, g, Y "89"
            12 -> a, e, f, Y, h "ABC"
            15 -> a, e, i, Y "D"
            16 -> a, e, i, :Text "EF"

            >>> tree = parse_sxpr('(a (b (c "123") (d "456")) (e (f (g "789") (h "ABC")) (i "DEF")))')
            >>> cm = ContentMapping(tree, auto_cleanup=False)
            >>> common_ancestor = cm.markup(0, 6, 'Y')
            >>> print(common_ancestor.as_sxpr())
            (b (Y (c "123") (d "456")))
            >>> a = cm.get_path_index(0)
            >>> b = cm.get_path_index(6, left_biased=True)
            >>> a, b
            (0, 1)
            >>> cm.rebuild_mapping_slice(a, b)
            >>> print(cm)
            0 -> a, b, Y, c "123"
            3 -> a, b, Y, d "456"
            6 -> a, e, f, g "789"
            9 -> a, e, f, h "ABC"
            12 -> a, e, i "DEF"
        """
        start_path = self._path_list[first_index]
        end_path = self._path_list[last_index]
        common_ancestor, i = find_common_ancestor(start_path, end_path)
        assert common_ancestor
        while first_index > 0 and self._path_list[first_index - 1][i:i + 1] == [common_ancestor]:
            first_index -= 1
        last = len(self._path_list) - 1
        while last_index < last and self._path_list[last_index + 1][i:i + 1] == [common_ancestor]:
            last_index += 1

        stump = start_path[:i]
        content, offsets, paths = self._generate_mapping(common_ancestor, stump)
        assert offsets[0] == 0
        start_pos = self._pos_list[first_index]
        end_pos = self._pos_list[last_index] + self._path_list[last_index][-1].strlen()
        offsets = [offset + start_pos for offset in offsets]
        if stump:  paths = [stump + path for path in paths]

        off_head = self._pos_list[:first_index]
        followup_offset = offsets[-1] + paths[-1][-1].strlen()
        if last_index < len(self._pos_list) - 1 and followup_offset != self._pos_list[last_index + 1]:
            shift = followup_offset - self._pos_list[last_index + 1]
            off_tail = [offset + shift for offset in self._pos_list[last_index + 1:]]
        else:
            off_tail = self._pos_list[last_index + 1:]

        path_head = self._path_list[:first_index]
        path_tail = self._path_list[last_index + 1:]

        self.content = ''.join([self.content[:start_pos], content, self.content[end_pos:]])

        self._pos_list.clear()
        self._pos_list.extend(off_head)
        self._pos_list.extend(offsets)
        self._pos_list.extend(off_tail)

        self._path_list.clear()
        self._path_list.extend(path_head)
        self._path_list.extend(paths)
        self._path_list.extend(path_tail)

    def rebuild_mapping(self, start_pos: int, end_pos: int):
        """Reconstructs a particular section of the context mapping after the
        underlying tree has been restructured.

        :param start_pos: The string position of the beginning of the text-area
            that has been affected by earlier changes.
        :param end_pos: The string position of the ending of the text-area
            that has been affected by earlier changes."""
        first_index = self.get_path_index(start_pos)
        last_index = self.get_path_index(end_pos)
        self.rebuild_mapping_slice(first_index, last_index)

    def insert_node(self, pos: int, node: Node) -> Node:
        """Inserts a node at a specific position into the last or
        eventually second but last node in the path from the context mapping
        that covers this position. Returns the parent of the newly inserted
        node."""
        index = self.get_path_index(pos)
        path = self._path_list[index]
        rel_pos = pos - self._pos_list[index]
        parent = insert_node(path, rel_pos, node)
        self.rebuild_mapping_slice(index, index)
        return parent


    @cython.locals(i=cython.int, k=cython.int, q=cython.int, r=cython.int, t=cython.int, u=cython.int, L=cython.int)
    def markup(self, start_pos: cint, end_pos: cint, name: str,
               *attr_dict, **attributes) -> Node:
        """ Marks the span [start_pos, end_pos[ up by adding one or more Node's
        with ``name``, eventually cutting through ``divisable`` nodes. Returns the
        nearest common ancestor of ``start_pos`` and ``end_pos``.

        :param cm:  A context mapping of the document (or a part therof) where the
            markup shall be inserted. See :py:func:`generate_content_mapping`
        :param start_pos:  The string-position of the first character to be marked
            up. Note that this is the position in the string-content of the tree
            over which the content mapping has been generated and not the position
            in the XML or any other serialization of the tree!
        :param end_pos:  The string-position of the last character to be included
            in the markup. Be aware that other than in slicing of Python lists
            or strings where the beginning and ending define an half-open intervall,
            the character indexed by end_pos is included in the markup, i.e.
            [start_pos, end_pos] define a closed intervall for markup.
            Also note that ``end_pos`` is the position in the string-content of the tree
            over which the content mapping has been generated and not the position
            in the XML or any other serialization of the tree!
        :param name:  The name, or "tag-name" in XML-terminology, of the element
            (or tag) to be added.
        :param attr_dict: A dictionary of attributes that will
            be added to the newly created tag.
        :param attributes: Alternatively, the attributes can also be passed as a
            list of named parameters.

        :returns: The nearest (from the top of the tree) node within which the
            entire markup lies.

        Examples::

            >>> from DHParser.toolkit import printw
            >>> tree = parse_sxpr('(X (l ",.") (A (O "123") (P "456")) (m "!?") '
            ...                   ' (B (Q "789") (R "abc")) (n "+-"))')
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(2, 8, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (em (O "123") (P "456"))) (m "!?") (B (Q "789") (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(2, 10, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (em (A (O "123") (P "456")) (m "!?")) (B (Q "789") (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X, divisability={'A'})
            >>> _ = t.markup(5, 10, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123")) (em (A (P "456")) (m "!?")) (B (Q "789") (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(2, 13, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (em (A (O "123") (P "456")) (m "!?")) (B (em (Q "789")) (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(5, 16, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123") (em (P "456"))) (em (m "!?") (B (Q "789") (R "abc")))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(5, 13, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123") (em (P "456"))) (em (m "!?")) (B (em (Q "789"))
             (R "abc")) (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(6, 12, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123") (P (:Text "4") (em "56"))) (em (m "!?"))
             (B (Q (em "78") (:Text "9")) (R "abc")) (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.markup(1, 17, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l (:Text ",") (em ".")) (em (A (O "123") (P "456")) (m "!?") (B (Q "789")
             (R "abc"))) (n (em "+") (:Text "-")))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X, divisability={'em': {'l', 'n'}})
            >>> _ = t.markup(1, 17, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",") (em (l ".") (A (O "123") (P "456")) (m "!?") (B (Q "789") (R "abc"))
             (n "+")) (n "-"))
        """
        assert not attr_dict or (len(attr_dict) == 1 and isinstance(attr_dict[0], Dict)), \
            f'{attr_dict} is not a valid attribute-dictionary!'
        assert end_pos >= start_pos
        attr_dict = attr_dict[0] if attr_dict else {}
        attr_dict.update(attributes)
        if start_pos == end_pos:
            milestone = Node(name, '').with_attr(attr_dict)
            common_ancestor = self.insert_node(start_pos, milestone)
            return common_ancestor

        path_A, pos_A = self.get_path_and_offset(start_pos)
        path_B, pos_B = self.get_path_and_offset(end_pos, left_biased=True)
        assert path_A
        assert path_B
        common_ancestor, i = find_common_ancestor(path_A, path_B)
        assert common_ancestor
        assert not common_ancestor.pick(lambda nd: nd.name == ':Text' and nd.children, include_root=True), common_ancestor.as_sxpr()

        if self.chain_attr_name and self.chain_attr_name not in attr_dict:
            attr_dict[self.chain_attr_name] = gen_chain_ID()

        divisable = self.divisability.get(name, self.divisability.get('*', frozenset()))

        if not common_ancestor._children:
            attr_dict.pop(self.chain_attr_name, None)
            markup_leaf(common_ancestor, pos_A, pos_B, name, attr_dict)
            if i != 0 and (common_ancestor.name in divisable or common_ancestor.anonymous):
                ur_ancestor = path_A[i - 1]
                t = ur_ancestor.index(common_ancestor)
                ur_ancestor.result = ur_ancestor[:t] + common_ancestor.children + ur_ancestor[t + 1:]
                common_ancestor = ur_ancestor
            assert not (common_ancestor.name == ':Text' and common_ancestor.children)
            if self.auto_cleanup:
                self.rebuild_mapping_slice(self.get_path_index(start_pos),
                                           self.get_path_index(end_pos, left_biased=True))
            return common_ancestor

        stump_A = path_A[i:]
        stump_B = path_B[i:]

        q = can_split(
            stump_A, pos_A, False, self.greedy, self.select_func, self.ignore_func, divisable)
        r = can_split(
            stump_B, pos_B, True, self.greedy, self.select_func, self.ignore_func, divisable)

        i = -1
        k = -1
        if q < abs(q) == len(stump_A) - 1:
            i = deep_split(stump_A, pos_A, False, self.greedy, self.select_func,
                           self.ignore_func, self.chain_attr_name)
        if r < abs(r) == len(stump_B) - 1:
            k = deep_split(stump_B, pos_B, True, self.greedy, self.select_func,
                           self.ignore_func, self.chain_attr_name)

        if i >= 0 and k >= 0:
            attr_dict.pop(self.chain_attr_name, None)
            nd = Node(name, common_ancestor[i:k]).with_attr(attr_dict)
            nd._pos = common_ancestor[i]._pos
            common_ancestor.result = common_ancestor[:i] + (nd,) + common_ancestor[k:]
        elif i >= 0:
            t = common_ancestor.index(stump_B[1])
            nd = Node(name, common_ancestor[i:t]).with_attr(attr_dict)
            nd._pos = common_ancestor[i]._pos
            markup_left(stump_B[1:], pos_B, name, attr_dict,
                        self.greedy, self.select_func, self.ignore_func,
                        divisable, self.chain_attr_name)
            common_ancestor.result = common_ancestor[:i] + (nd,) + common_ancestor[t:]
        elif k >= 0:
            t = common_ancestor.index(stump_A[1])
            nd = Node(name, common_ancestor[t + 1:k]).with_attr(attr_dict)
            nd._pos = common_ancestor[t + 1]._pos
            markup_right(stump_A[1:], pos_A, name, attr_dict,
                         self.greedy, self.select_func, self.ignore_func,
                         divisable, self.chain_attr_name)
            common_ancestor.result = common_ancestor[:t + 1] + (nd,) + common_ancestor[k:]
        else:
            t = common_ancestor.index(stump_A[1])
            u = common_ancestor.index(stump_B[1])
            markup_right(stump_A[1:], pos_A, name, attr_dict,
                         self.greedy, self.select_func, self.ignore_func,
                         divisable, self.chain_attr_name)
            markup_left(stump_B[1:], pos_B, name, attr_dict,
                        self.greedy, self.select_func, self.ignore_func,
                        divisable, self.chain_attr_name)
            if u - t > 1:
                nd = Node(name, common_ancestor[t + 1:u]).with_attr(attr_dict)
                nd._pos = common_ancestor[t + 1]._pos
                common_ancestor.result = common_ancestor[:t + 1] + (nd,) + common_ancestor[u:]

        if self.auto_cleanup:
            self.rebuild_mapping_slice(self.get_path_index(start_pos),
                                       self.get_path_index(end_pos, left_biased=True))
        assert not common_ancestor.pick(lambda nd: nd.name == ':Text' and nd.children, include_root=True), common_ancestor.as_sxpr()
        return common_ancestor


class LocalContentMapping(ContentMapping):
    """A context-mapping (see :py:class:`ContentMapping`) that does not span
    the complete tree, but a section between two paths.

    EXPERIMENTAL AND UNTESTED!!!
    """

    def __init__(self, start_path: Path, end_path: Path,
                 select: PathSelector = LEAF_PATH,
                 ignore: PathSelector = NO_PATH,
                 greedy: bool = True,
                 divisability: Union[Dict[str, Container], Container, str] = LEAF_PTYPES,
                 chain_attr_name: str = '',
                 auto_cleanup: bool = True):
        ancestor, index = find_common_ancestor(start_path, end_path)
        super().__init__(self, ancestor, select, ignore, greedy, divisability,
                         chain_attr_name, auto_cleanup)
        self.stump: Path = start_path[:index]
        start_path_tail = start_path[index:]
        end_path_tail = end_path[index:]
        for i in range(len(self._path_list)):
            if self._path_list[i] == start_path_tail:
                self.first_index = i
                break
        else:
            self.first_index = 0
        for k in range(i, len(self._path_list)):
            if self._path_list[k] == end_path_tail:
                self.last_index = k
                break
        else:
            self.last_index = len(self._path_list) - 1
        self.pos_offset: int = strlen_of(tuple(path[-1] for path in self._path_list[:i]))
        pathL, posL = self._gen_local_path_and_pos_list(i, k)
        self.local_path_list: List[Path] = pathL
        self.local_pos_list: List[int] = posL

    def _gen_local_path_and_pos_list(self, i: cint, k: cint):
        return ([(self.stump + path) for path in self._path_list[i:k + 1]],
                [pos - self.pos_offset for pos in self._pos_list[i:k + 1]])

    @ContentMapping.path_list.getter
    def _(self) -> List[Path]:
        return self.local_path_list

    @ContentMapping.pos_list.getter
    def _(self) -> List[int]:
        return self.local_pos_list

    def get_path_index(self, pos: int, left_biased: bool = False) -> int:
        return super().get_path_index(self, pos + self.pos_offset, left_biased) - self.first_index

    def get_path_and_offset(self, pos: int, left_biased: bool = False) -> Tuple[Path, int]:
        pth, off = super().get_path_and_offset(pos + self.pos_offset, left_biased)
        return pth, off - self.pos_offset

    def iterate_paths(self, start_pos: int, end_pos: int, left_biased: bool = False) \
            -> Iterator[Path]:
        yield from super().iterate_paths(
            self, start_pos + self.pos_offset, end_pos + self.pos_offset, left_biased)

    def rebuild_mapping_slice(self, first_index: int, last_index: int):
        super().rebuild_mapping_slice(first_index + self.first_index,
                                      last_index + self.first_index)
        self.local_path_list, self.local_pos_list = self._gen_local_path_and_pos_list()

    def rebuild_mapping(self, start_pos: int, end_pos: int):
        super().rebuild_mapping(start_pos + self.pos_offset, end_pos + self.pos_offset)

    def insert_node(self, pos: int, node: Node) -> Node:
        return super().insert_node(pos + self.pos_offset, node)

    def markup(self, start_pos: int, end_pos: int, name: str,
               *attr_dict, **attributes) -> Node:
        return super().markup(start_pos + self.pos_offset, end_pos + self.pos_offset, name,
                              *attr_dict, **attributes)


# Attribute handling ##################################################


def validate_token_sequence(token_sequence: str) -> bool:
    """Returns True, if `token_sequence` is properly formed.

    Token sequences are strings or words which are separated by
    single blanks with no leading or trailing blank.
    """
    return token_sequence[:1] != ' ' and token_sequence[-1:] != ' ' \
        and token_sequence.find('  ') < 0


def has_token(token_sequence: str, tokens: str) -> bool:
    """Returns true, if `token` is contained in the blank-spearated
    token sequence. If `token` itself is a blank-separated sequence of
    tokens, True is returned if all tokens are contained in
    `token_sequence`::

        >>> has_token('bold italic', 'italic')
        True
        >>> has_token('bold italic', 'normal')
        False
        >>> has_token('bold italic', 'italic bold')
        True
        >>> has_token('bold italic', 'bold normal')
        False
    """
    # assert validate_token_sequence(token_sequence)
    # assert validate_token_sequence(token)
    return not tokens or set(tokens.split(' ')) <= set(token_sequence.split(' '))


def add_token(token_sequence: str, tokens: str) -> str:
    """Adds the tokens from 'tokens' that are not already contained in
    `token_sequence` to the end of `token_sequence`::

        >>> add_token('', 'italic')
        'italic'
        >>> add_token('bold italic', 'large')
        'bold italic large'
        >>> add_token('bold italic', 'bold')
        'bold italic'
        >>> add_token('red thin', 'stroked red')
        'red thin stroked'
    """
    for tk in tokens.split(' '):
        if tk and token_sequence.find(tk) < 0:
            token_sequence += ' ' + tk
    return token_sequence.lstrip()


def remove_token(token_sequence, tokens: str) -> str:
    """
    Removes all `tokens` from  `token_sequence`::

        >>> remove_token('red thin stroked', 'thin')
        'red stroked'
        >>> remove_token('red thin stroked', 'blue')
        'red thin stroked'
        >>> remove_token('red thin stroked', 'blue stroked')
        'red thin'
    """
    for tk in tokens.split(' '):
        token_sequence = token_sequence.replace(tk, '').strip().replace('  ', ' ')
    return token_sequence


def eq_tokens(token_sequence1: str, token_sequence2: str) -> bool:
    """Returns True if bothe token sequences contain the same tokens,
    no matter in what order::

        >>> eq_tokens('red thin stroked', 'stroked red thin')
        True
        >>> eq_tokens('red thin', 'thin blue')
        False
    """
    return set(token_sequence1.split(' ')) - {''} == set(token_sequence2.split(' ')) - {''}


def has_token_on_attr(node: Node, tokens: str, attribute: str):
    """Returns True, if 'attribute' of 'node' contains all 'tokens'."""
    return has_token(node.get_attr(attribute, ''), tokens)


def add_token_to_attr(node: Node, tokens: str, attribute: str):
    """Adds all `tokens` to `attribute` of `node`."""
    if tokens:
        node.attr[attribute] = add_token(node.get_attr(attribute, ''), tokens)


def remove_token_from_attr(node: Node, tokens: str, attribute: str):
    """Removes all `tokens` from `attribute` of `node`."""
    node.attr[attribute] = remove_token(node.get_attr(attribute, ''), tokens)


has_class = functools.partial(has_token_on_attr, attribute='class')
add_class = functools.partial(add_token_to_attr, attribute='class')
remove_class = functools.partial(remove_token_from_attr, attribute='class')


#######################################################################
#
# FrozenNode - an immutable Node
#
#######################################################################


class FrozenNode(Node):
    """
    FrozenNode is an immutable kind of Node, i.e. it must not be changed
    after initialization. The purpose is mainly to allow certain kinds of
    optimizations, like not having to instantiate empty nodes (because they
    are always the same and will be dropped while parsing, anyway) and
    to be able to trigger errors if the program tries to treat such
    temporary nodes as a regular ones. (See :py:mod:`DHParser.parse`)

    Frozen nodes must only be used temporarily during parsing or
    tree-transformation and should not occur in the product of the
    transformation anymore. This can be verified with
    :py:func:`tree_sanity_check()`. Or, as comparison criterion for
    content equality when picking or selecting nodes or paths from
    a tree (see :py:func:`create_match_function()`).
    """

    def __init__(self, name: str, result: ResultType, leafhint: bool = True) -> None:
        if isinstance(result, str) or isinstance(result, StringView):
            result = str(result)
        else:
            raise TypeError('FrozenNode only accepts string as result. '
                            '(Only leaf-nodes can be frozen nodes.)')
        super(FrozenNode, self).__init__(name, result, True)

    @property
    def result(self) -> Union[Tuple[Node, ...], StringView, str]:
        return self._result

    @result.setter
    def result(self, result: ResultType):
        raise TypeError('FrozenNode does not allow re-assignment of results.')

    @property
    def attr(self):
        try:
            return self._attributes
        except AttributeError:
            return OrderedDict()  # assignments will be void!

    @attr.setter
    def attr(self, attr_dict: Dict[str, Any]):
        if self.has_attr():
            raise AssertionError("Frozen nodes' attributes can only be set once")
        else:
            self._attributes = attr_dict

    @property
    def pos(self):
        return -1

    def with_pos(self, pos: cint) -> Node:
        raise NotImplementedError("Position values cannot be assigned to frozen nodes!")

    def to_json_obj(self) -> List:
        raise NotImplementedError("Frozen nodes cannot and be serialized as JSON!")

    @staticmethod
    def from_json_obj(json_obj: Union[Dict, Sequence]) -> Node:
        raise NotImplementedError("Frozen nodes cannot be deserialized from JSON!")


PLACEHOLDER = FrozenNode('__PLACEHOLDER__', '')
EMPTY_NODE = FrozenNode(EMPTY_PTYPE, '')


def tree_sanity_check(tree: Node) -> bool:
    """
    Sanity check for node-trees: One and the same node must never appear
    twice in the node-tree. Frozen Nodes (EMTPY_NODE, PLACEHOLDER)
    should only exist temporarily and must have been dropped or eliminated
    before any kind of tree generation (i.e. parsing) or transformation
    is finished.
    :param tree: the root of the tree to be checked
    :returns: `True`, if the tree is "sane", `False` otherwise.
    """
    node_set = set()  # type: Set[Node]
    for node in tree.select_if(lambda nd: True, include_root=True):
        if not isinstance(node, Node) or node in node_set or isinstance(node, FrozenNode):
            return False
        node_set.add(node)
    return True


#######################################################################
#
# RootNode - manage global properties of trees, like error messages
#
#######################################################################

_EMPTY_SET_SENTINEL = frozenset()  # needed by RootNode.as_xml()


def default_divisable() -> AbstractSet[str]:
    return LEAF_PTYPES


class RootNode(Node):
    """The root node for the node-tree is a special kind of node that keeps
    and manages global properties of the tree as a whole. These are first and
    foremost the list off errors that occurred during tree generation
    (i.e. parsing) or any transformation of the tree.

    Other properties concern the customization of the XML-serialization and
    meta-data about the procesed document and processing stage.

    Although errors are local properties that occur on a specific point or
    chunk of source code, instead of attaching the errors to the nodes on
    which they have occurred, the list of errors in managed globally by the
    root-node object. Otherwise, it would be hard to keep track of the
    errors when during the transformation of trees node are replaced or
    dropped that might also contain error messages.

    The root node can be instantiated before the tree is fully parsed. This is
    necessary, because the root node is needed for managing error messages
    during the parsing process, already. In order to connect the root node to
    the tree, when parsing is finished, the swallow()-method must be called.

    :ivar errors:  A list of all errors that have occurred so far during
        processing (i.e. parsing, AST-transformation, compiling) of this tree.
        The errors are ordered by the time of their being added to the list.
    :ivar errors_sorted: (read-only property) The list of errors ordered by
        their position.
    :ivar error_nodes: A mapping of node-ids to a list of errors that
        occurred on the node with the respective id.
    :ivar error_positions: A mapping of locations to a set of ids of nodes
        that contain an error at that particular location.
    :ivar error_flag: the highest warning or error level of all errors
        that occurred.

    :ivar source:  The source code (after preprocessing)
    :ivar source_mapping:  A source mapping function to map source code
        positions to the positions of the non-preprocessed source.
        See module `preprocess`
    :ivar lbreaks: A list of indices of all linebreaks in the source.

    :ivar inline_tags: see `Node.as_xml()` for an explanation.
    :ivar string_tags: see `Node.as_xml()` for an explanation.
    :ivar empty_tags: see `Node.as_xml()` for an explanation.

    :ivar docname: a name for the document
    :ivar stage: a name for the current processing stage
    :ivar serialization_type: The kind of serialization for the
        current processing stage. Can be one of 'XML', 'json',
        'indented', 'S-expression' or 'default'. (The latter picks
        the default serialization from the configuration.)

    :ivar data: Compiled data. If the data still is a tree this
        simnply contains a reference to self.
    """

    def __init__(self, node: Optional[Node] = None,
                 source: Union[str, StringView] = '',
                 source_mapping: Optional[SourceMapFunc] = None):
        super().__init__('__not_yet_ready__', '')
        self.errors: List[Error] = []
        self._error_set: Set[Error] = set()
        self.error_nodes: Dict[int, List[Error]] = dict()   # id(node) -> error list
        self.error_positions: Dict[int, Set[int]] = dict()  # pos -> set of id(node)
        self.error_flag: ErrorCode = ErrorCode(0)
        self.source: Union[str, StringView] = source
        self.lbreaks: List[int] = linebreaks(source)

        # customization for XML-Representation
        self.inline_tags: AbstractSet[str] = set()
        self.string_tags: AbstractSet[str] = {TOKEN_PTYPE}
        self.empty_tags: AbstractSet[str] = set()

        # meta-data
        self.docname: str = ''
        self.stage: str = ''
        self.serialization_type: str = 'default'

        if node is not None:
            self.swallow(node, source, source_mapping)
        else:
            self.source_mapping: SourceMapFunc = gen_neutral_srcmap_func(source) \
                if source_mapping is None else source_mapping

        # Data resembling the compiled tree. Default is the tree itself.
        self.data = self

    def __str__(self):
        errors = self.errors_sorted
        if errors:
            e_pos = errors[0].pos
            content = self.content
            return content[:e_pos] + ' <<< Error on "%s" | %s >>> ' % \
                (content[e_pos - self.pos:], '; '.join(e.message for e in errors))
        return self.content

    def __deepcopy__(self, memodict={}):
        old_node_ids = [id(nd) for nd in self.select_if(lambda n: True, include_root=True)]
        duplicate = self.__class__(None)
        if self._children:
            duplicate._children = copy.deepcopy(self._children, memodict)
            duplicate._result = duplicate._children
        else:
            duplicate._children = tuple()
            duplicate._result = self._result
        duplicate._pos = self._pos
        new_node_ids = [id(nd) for nd in duplicate.select_if(lambda n: True, include_root=True)]
        map_id = dict(zip(old_node_ids, new_node_ids))
        if self.has_attr():
            duplicate.attr.update(self._attributes)
            # duplicate._attributes = copy.deepcopy(self._attributes)  # this is blocked by cython
        duplicate.errors = copy.deepcopy(self.errors, memodict)
        duplicate._error_set = {error for error in duplicate.errors}
        duplicate.error_nodes = {map_id.get(i, i): el[:] for i, el in self.error_nodes.items()}
        duplicate.error_positions = {pos: {map_id.get(i, i) for i in s}
                                     for pos, s in self.error_positions.items()}
        duplicate.source = self.source
        duplicate.source_mapping = self.source_mapping
        duplicate.lbreaks = copy.deepcopy(self.lbreaks, memodict)
        duplicate.error_flag = self.error_flag

        duplicate.inline_tags = self.inline_tags
        duplicate.string_tags = self.string_tags
        duplicate.empty_tags = self.empty_tags

        duplicate.docname = self.docname
        duplicate.stage = self.stage
        duplicate.serialization_type = self.serialization_type

        if self.data != self:
            duplicate.data = copy.deepcopy(self.data)

        duplicate.name = self.name
        return duplicate

    def swallow(self, node: Optional[Node],
                source: Union[str, StringView] = '',
                source_mapping: Optional[SourceMapFunc] = None) \
            -> RootNode:
        """
        Put `self` in the place of `node` by copying all its data.
        Returns self.

        This is done by the parse.Grammar object after
        parsing has finished, so that the Grammar object always
        returns a node-tree rooted in a RootNode object.

        It is possible to add errors to a RootNode object, before it
        has actually swallowed the root of the node-tree.
        """
        if source and source != self.source:
            self.source = source
            self.lbreaks = linebreaks(source)
        self.source_mapping: SourceMapFunc = gen_neutral_srcmap_func(source) \
            if source_mapping is None else source_mapping
        if self.name != '__not_yet_ready__':
            raise AssertionError('RootNode.swallow() has already been called!')
        if node is None:
            self.name = ZOMBIE_TAG
            self.with_pos(0)
            self.new_error(self, 'Parser did not match!', PARSER_STOPPED_BEFORE_END)
            return self
        self._result = node._result
        self._children = node._children
        self._pos = node._pos
        self.name = node.name
        if node.has_attr():
            self._attributes = node._attributes
        # self._content = node._content
        if id(node) in self.error_nodes:
            self.error_nodes[id(self)] = self.error_nodes[id(node)]
        if self.source:
            add_source_locations(self.errors, self.source_mapping)
        return self

    def continue_with_data(self, data: Any):
        """Drops the swallowed tree in favor of the (non-tree) data resulting
        from the compilation of the tree. The data can then be retrieved from
        the field ``self.data``, which before the tree has been dropped contains
        a reference to the tree itself.
        """
        if data != self:
            self.data = data
            self.result = "TREE HAS BEEN DESTROYED!"

    def add_error(self, node: Optional[Node], error: Error) -> RootNode:
        """
        Adds an Error object to the tree, locating it at a specific node.
        """
        assert isinstance(error, Error)
        if error in self._error_set:  return self  # prevent duplication of errors
        if not node:
            # find the first leaf-node from the left that could contain the error
            # judging from its position
            pos_list = []
            node_list = []
            nd = None
            for nd in self.select_if(lambda nd: not nd._children):
                assert nd.pos >= 0
                if nd.pos <= error.pos < nd.pos + nd.strlen():
                    node = nd
                    break
                pos_list.append(nd.pos)
                node_list.append(nd)
            else:
                if nd is None:
                    node = self
                else:
                    node_list.append(nd)
                    i = bisect.bisect(pos_list, error.pos)
                    node = node_list[i]
        else:
            assert isinstance(node, Node)
            assert isinstance(node, FrozenNode) or node.pos <= error.pos, \
                "Wrong error position when processing error: %s\n" % str(error) + \
                "%i <= %i <= %i ?" % (node.pos, error.pos, node.pos + max(1, node.strlen() - 1))
            assert node.pos >= 0, "Errors cannot be assigned to nodes without position!"
        self.error_nodes.setdefault(id(node), []).append(error)
        if node.pos == error.pos:
            self.error_positions.setdefault(error.pos, set()).add(id(node))
        if self.source:
            add_source_locations([error], self.source_mapping)
        self.errors.append(error)
        self._error_set.add(error)
        self.error_flag = max(self.error_flag, error.code)
        return self

    def new_error(self,
                  node: Node,
                  message: str,
                  code: ErrorCode = ERROR) -> RootNode:
        """
        Adds an error to this tree, locating it at a specific node.

        :param node:    the node where the error occurred
        :param message: a string with the error message
        :param code:    an error code to identify the type of the error
        """
        error = Error(message, node.pos, code)
        self.add_error(node, error)
        return self

    def node_errors(self, node: Node) -> List[Error]:
        """
        Returns the List of errors that occurred on the node or any child node
        at the position of the node that has already been removed from the tree,
        for example, because it was an anonymous empty child node.
        The position of the node is here understood to cover the range:
        [node.pos, node.pos + node.strlen()[
        """
        node_id = id(node)           # type: int
        errors = []                  # type: List[Error]
        start_pos = node.pos
        end_pos = node.pos + max(node.strlen(), 1)
        error_node_ids = set()
        for pos, ids in self.error_positions.items():   # TODO: use bisect here...
            if start_pos <= pos < end_pos:
                error_node_ids.update(ids)
        for nid in error_node_ids:
            if nid == node_id:
                # add the node's errors
                errors.extend(self.error_nodes[nid])
            elif node._children:
                for _ in node.select_if(lambda n: id(n) == nid):
                    break
                else:
                    # node is not connected to tree anymore, but since errors
                    # should not get lost, display its errors on its parent
                    errors.extend(self.error_nodes[nid])
        return errors

    def transfer_errors(self, src: Node, dest: Node):
        """
        Transfers errors to a different node. While errors never get lost
        during AST-transformation, because they are kept by the RootNode,
        the nodes they are connected to may be dropped in the course of the
        transformation. This function allows attaching errors from a node that
        will be dropped to a different node.
        """
        srcId = id(src)
        destId = id(dest)
        if srcId != destId and srcId in self.error_nodes:
            errorList = self.error_nodes[srcId]
            self.error_nodes.setdefault(destId, []).extend(errorList)
            del self.error_nodes[srcId]
            for nodeSet in self.error_positions.values():
                nodeSet.discard(srcId)
                nodeSet.add(destId)

    @property
    def errors_sorted(self) -> List[Error]:
        """
        Returns the list of errors, ordered bv their position.
        """
        errors = self.errors[:]
        errors.sort(key=lambda e: e.pos)
        return errors

    def error_safe(self, level: ErrorCode = ERROR) -> RootNode:
        """
        Asserts that the given tree does not contain any errors with a
        code equal or higher than the given level.
        Returns the tree if this is the case, raises an `AssertionError`
        otherwise.
        """
        if has_errors(self.errors, level):
            raise AssertionError('\n'.join(['Tree-sanity-check failed, because of:'] +
                                           [str(e) for e in only_errors(self.errors, level)]))
        return self

    def did_match(self) -> bool:
        """
        Returns True, if the parser that has generated this tree did
        match, False otherwise. Depending on wether the Grammar-object that
        that generated the node-tree was called with `complete_match=True`
        or not this requires either the complete document to have been
        matched or only the beginning.

        Note: If the parser did match, this does not mean that it must
        have matched without errors. It simply means the no
        PARSER_STOPPED_BEFORE_END-error has occurred.
        """
        return self.name != '__not_yet_ready__' \
            and not any(e.code == PARSER_STOPPED_BEFORE_END for e in self.errors)

    def as_xml(self, src: Optional[str] = None,
               indentation: int = 2,
               inline_tags: AbstractSet[str] = _EMPTY_SET_SENTINEL,
               string_tags: AbstractSet[str] = _EMPTY_SET_SENTINEL,
               empty_tags: AbstractSet[str] = _EMPTY_SET_SENTINEL,
               strict_mode: bool=True) -> str:
        return super().as_xml(
            src, indentation,
            inline_tags=self.inline_tags if inline_tags is _EMPTY_SET_SENTINEL else inline_tags,
            string_tags=self.string_tags if string_tags is _EMPTY_SET_SENTINEL else string_tags,
            empty_tags=self.empty_tags if empty_tags is _EMPTY_SET_SENTINEL else empty_tags,
            strict_mode=strict_mode)

    def serialize(self, how: str = '') -> str:
        if not how:
            how = self.serialization_type or 'default'
        return super().serialize(how)



#######################################################################
#
# S-expression- and XML-parsers and JSON-reader, ElementTree-converter
#
#######################################################################

RX_SXPR_INNER_PARSER = re.compile(r'[\w:]+')
RX_SXPR_NOTEXT = re.compile(r'(?:(?!\)).)*', re.DOTALL)
RX_SXPR_TEXT = {qtmark: re.compile(qtmark + r'.*?' + qtmark, re.DOTALL)
                for qtmark in ['"""', "'''", '"', "'"]}


def parse_sxpr(sxpr: Union[str, StringView]) -> RootNode:
    """
    Generates a tree of nodes from an S-expression.

    This can - among other things - be used for deserialization of trees that
    have been serialized with `Node.as_sxpr()` or as a convenient way to
    generate test data.

    Example:
    >>> parse_sxpr("(a (b c))").as_sxpr(flatten_threshold=0)
    '(a\\n  (b "c"))'

    `parse_sxpr()` does not initialize the node's `pos`-values. This can be
    done with `Node.with_pos()`:

    >>> tree = parse_sxpr('(A (B "x") (C "y"))').with_pos(0)
    >>> tree['C'].pos
    1
    """
    remaining = sxpr  # type: Union[str, StringView]

    @cython.locals(level=cython.int, k=cython.int)
    def next_block(s: StringView) -> Iterator[StringView]:
        """Generator that yields all characters until the next closing bracket
        that does not match an opening bracket matched earlier within the same
        package.
        """
        s = s.strip()
        try:
            while s[0] != ')':
                if s[0] != '(':
                    raise ValueError('"(" expected, not ' + s[:10])
                # assert s[0] == '(', s
                level = 1
                k = 1
                while level > 0:
                    if s[k] in ("'", '"'):
                        k = s.find(str(s[k]), k + 1)
                    if k < 0:
                        raise IndexError()
                    if s[k] == '(':
                        level += 1
                    elif s[k] == ')':
                        level -= 1
                    k += 1
                yield s[:k]
                s = s[k:].strip()
        except IndexError:
            errmsg = ('Malformed S-expression. Unprocessed part: "%s"' % s) if s \
                else 'Malformed S-expression. Closing bracket(s) ")" missing.'
            raise ValueError(errmsg)
        nonlocal remaining
        remaining = s


    @cython.locals(pos=cython.int, i=cython.int, k=cython.int, end=cython.int)
    def inner_parser(sxpr: StringView) -> Node:
        if sxpr[0] != '(':
            raise ValueError('"(" expected, not ' + sxpr[:10])
        # assert sxpr[0] == '(', sxpr
        sxpr = sxpr[1:].strip()
        match = sxpr.match(RX_SXPR_INNER_PARSER)
        if match is None:
            raise AssertionError('Malformed S-expression Node-tagname or identifier expected, '
                                 'not "%s"' % sxpr[:40].replace('\n', ''))
        end = sxpr.index(match.end())
        tagname = sxpr[:end]
        name, class_name = (tagname.split(':') + [''])[:2]
        sxpr = sxpr[end:].strip()
        attributes = OrderedDict()  # type: Dict[str, Any]
        pos = -1  # type: int
        # parse attr
        while sxpr[:2] == "`(":
            i = sxpr.find('"')
            k = sxpr.find(')')
            if k > i:
                k = sxpr.find(')', sxpr.find('"', i + 1))
            if i < 0:
                i = k + 1
            if k < 0:
                raise ValueError('Unbalanced parantheses in S-Expression: ' + str(sxpr))
            # read very special attribute pos
            if sxpr[2:5] == "pos" and 0 < k < i:
                pos = int(str(sxpr[5:k].strip(' \'"').split(' ')[0]))
            # ignore very special attribute err
            elif sxpr[2:5] == "err" and 0 <= sxpr.find('`', 5) < k:
                m = sxpr.find('(', 5)
                while 0 <= m < k:
                    m = sxpr.find('(', k)
                    k = max(k, sxpr.find(')', max(m, 0)))
            # read attr
            else:
                attr = str(sxpr[2:i].strip())
                if not RX_ATTR_NAME.match(attr):
                    raise ValueError('Illegal attribute name: ' + attr)
                value = sxpr[i:k].strip()[1:-1]
                attributes[attr] = str(value)
            sxpr = sxpr[k + 1:].strip()
        if sxpr[0] == '(':
            result = tuple(inner_parser(block)
                           for block in next_block(sxpr))  # type: Union[Tuple[Node, ...], str]
        else:
            lines = []
            while sxpr and sxpr[0:1] != ')':
                # parse content
                for qtmark in ['"""', "'''", '"', "'"]:
                    match = sxpr.match(RX_SXPR_TEXT[qtmark])
                    if match:
                        end = sxpr.index(match.end())
                        i = len(qtmark)
                        lines.append(str(sxpr[i:end - i]))
                        sxpr = sxpr[end:].strip()
                        break
                else:
                    match = sxpr.match(RX_SXPR_NOTEXT)
                    end = sxpr.index(match.end())
                    lines.append(str(sxpr[:end]))
                    sxpr = sxpr[end:]
            result = "\n".join(lines)  # # type: Union[Tuple[Node, ...], str]
            nonlocal remaining
            remaining = sxpr
        node = Node(str(name or ':' + class_name), result)
        node._pos = pos
        if attributes:
            node.attr.update(attributes)
        return node

    xpr = StringView(sxpr).strip() if isinstance(sxpr, str) else sxpr.strip()  # type: StringView
    tree = inner_parser(xpr)
    if remaining != ')':
        raise ValueError('Malformed S-expression. Superfluous characters: ' + remaining[1:])
    return RootNode(tree)


RX_WHITESPACE_TAIL = re.compile(r'\s*$')
RX_XML_ATTRIBUTES = re.compile(r'\s*(?P<attr>[\w:_.-]+)\s*=\s*"(?P<value>.*?)"\s*')
RX_XML_SPECIAL_TAG = re.compile(r'<(?![?!])')
RX_XML_OPENING_TAG = re.compile(r'<\s*(?P<tagname>[\w:_.-]+)\s*')
RX_XML_CLOSING_TAG = re.compile(r'</\s*(?P<tagname>[\w:_.-]+)\s*>')
RX_XML_HEADER = re.compile(r'<(?![?!])')


EMPTY_TAGS_SENTINEL = set()


def parse_xml(xml: Union[str, StringView],
              string_tag: str = TOKEN_PTYPE,
              ignore_pos: bool = False,
              out_empty_tags: Set[str] = EMPTY_TAGS_SENTINEL,
              strict_mode: bool = True) -> RootNode:
    """
    Generates a tree of nodes from a (Pseudo-)XML-source.

    :param xml: The XML-string to be parsed into a tree of Nodes
    :param string_tag: A tag-name that will be used for
        strings inside mixed-content-tags.
    :param ignore_pos: if True, '_pos'-attributes will be understood as
        normal XML-attributes. Otherwise, '_pos' will be understood as a
        special attribute, the value of which will be written to `node._pos`
        and not transferred to the `node.attr`-dictionary.
    :param out_empty_tags: A set that is filled with the names of those
        tags that are empty tags, e.g. "<br/>"
    :param strict_mode: If True, errors are raised if XML
        contains stylistic or interoperability errors, like using one
        and the same tag-name for empty and non-empty tags, for example.
    """

    xml = StringView(str(xml))
    non_empty_tags: Set[str] = set()
    dual_use_notified: Set[str] = set()

    if out_empty_tags is EMPTY_TAGS_SENTINEL:
        out_empty_tags = set()

    def get_pos_str(substring: StringView) -> str:
        """Returns line:column indicating where substring is located within
        the whole xml-string."""
        nonlocal xml
        pos = len(xml) - len(substring)
        l, c = line_col(linebreaks(xml), pos)
        return f'{l}:{c}'

    def parse_attributes(s: StringView) -> Tuple[StringView, Dict[str, Any]]:
        """
        Parses a sequence of XML-Attributes. Returns the string-slice
        beginning after the end of the attr.
        """
        attributes = OrderedDict()  # type: Dict[str, Any]
        eot = s.find('>')
        restart = 0
        for match in s.finditer(RX_XML_ATTRIBUTES):
            if s.index(match.start()) >= eot:
                break
            d = match.groupdict()
            attributes[d['attr']] = d['value']
            restart = s.index(match.end())
        return s[restart:], attributes

    def skip_comment(s: StringView) -> StringView:
        assert s[:4] == "<!--"
        i = s.find('-->')
        if i < 0:
            if strict_mode:
                raise ValueError(get_pos_str(s) + " comment is never closed!")
            else:
                return s[4:]
        else:
            return s[i + 3:]

    def skip_special_tag(s: StringView) -> StringView:
        """Skip special tags, e.g. <?...>, <!...>, and return the string
        view at the position of the next normal tag."""
        assert s[:2] in ('<!', '<?')
        assert s[:4] != '<!--'
        m = s.search(RX_XML_SPECIAL_TAG)
        i = s.index(m.start()) if m else len(s)
        k = s.rfind(">", end=i)
        return s[k+1:] if k >= 0 else s[2:]

    def parse_opening_tag(s: StringView) -> Tuple[StringView, str, OrderedDict, bool]:
        """
        Parses an opening tag. Returns the string segment following
        the opening tag, the tag name, a dictionary of attr and
        a flag indicating whether the tag is actually a solitary tag as
        indicated by a slash at the end, i.e. <br/>.
        """
        match = s.match(RX_XML_OPENING_TAG)
        assert match
        tagname = match.groupdict()['tagname']
        section = s[s.index(match.end()):]
        s, attributes = parse_attributes(section)
        i = s.find('>')
        assert i >= 0
        return s[i + 1:], tagname, attributes, s[i - 1] == "/"

    def parse_closing_tag(s: StringView) -> Tuple[StringView, str]:
        """
        Parses a closing tag and returns the string segment, just after
        the closing tag.
        """
        match = s.match(RX_XML_CLOSING_TAG)
        assert match, 'XML-closing-tag expected, but found: ' + s[:20]
        tagname = match.groupdict()['tagname']
        return s[s.index(match.end()):], tagname

    def parse_leaf_content(s: StringView) -> Tuple[StringView, StringView]:
        """
        Parses a piece of the content of a tag, just until the next opening,
        closing or solitary tag is reached.
        """
        i = 0
        while s[i] != "<":  # or s[max(0, i - 1)] == "\\":
            i = s.find("<", i + 1)
            assert i > 0
        return s[i:], s[:i]

    def parse_full_content(s: StringView) -> Tuple[StringView, Node]:
        """
        Parses the full content of a tag, starting right at the beginning
        of the opening tag and ending right after the closing tag.
        """
        nonlocal non_empty_tags, dual_use_notified
        res = []  # type: List[Node]
        substring = s
        s, tagname, attrs, solitary = parse_opening_tag(s)
        name, class_name = (tagname.split(":") + [''])[:2]
        if solitary:
            if tagname in non_empty_tags:
                if strict_mode and tagname not in dual_use_notified:
                    print(get_pos_str(substring) +
                        f' "{tagname}" is used as empty as well as non-empty element!'
                        f' This can cause errors when re-serializing data as XML!')
                    dual_use_notified.add(tagname)
                    # raise ValueError(get_pos_str(substring) +
                    #     f' "{tagname}" is used as empty as well as non-empty element!'
                    #     f' This can cause errors when re-serializing data as XML!'
                    #     f' Use parse_xml(..., strict_mode=False) to suppress this error!')
                non_empty_tags.remove(tagname)
            out_empty_tags.add(tagname)
        else:
            if tagname in out_empty_tags:
                if strict_mode and tagname not in dual_use_notified:
                    print(get_pos_str(substring) +
                        f' "{tagname}" is used as empty as well as non-empty element!'
                        f' This can cause errors when re-serializing data as XML!')
                    dual_use_notified.add(tagname)
                    # raise ValueError(get_pos_str(substring) +
                    #     f' "{tagname}" is used as empty as well as non-empty element!'
                    #     f' This can cause errors when re-serializing data as XML!'
                    #     f' Use parse_xml(..., strict_mode=False) to suppress this error!')
            else:
                non_empty_tags.add(tagname)
            while s and not s[:2] == "</":
                s, leaf = parse_leaf_content(s)
                if leaf and (leaf.find('\n') < 0 or not leaf.match(RX_WHITESPACE_TAIL)):
                    res.append(Node(string_tag, leaf))
                if s[:1] == "<":
                    if s[:4] == '<!--':
                        s = skip_comment(s)
                    elif s[:2] in ("<?", "<!"):
                        s = skip_special_tag(s)
                    elif s[:2] != "</":
                        s, child = parse_full_content(s)
                        res.append(child)
            s, closing_tagname = parse_closing_tag(s)
            if tagname != closing_tagname:
                if strict_mode:
                    raise ValueError(
                        f'{get_pos_str(substring)} - {get_pos_str(s)}'
                        f' Tag-name mismatch: <{tagname}>...</{closing_tagname}>!'
                        f' Use parse_xml(..., strict_mode=False) to suppress this error,'
                        f' but do not expect sound results if you do!')
                else:
                    print(f'{get_pos_str(substring)} - {get_pos_str(s)}'
                          f' Tag-name mismatch: <{tagname}>...</{closing_tagname}>!')
        if len(res) == 1 and res[0].name == string_tag:
            result = res[0].result  # type: Union[Tuple[Node, ...], StringView, str]
        else:
            result = tuple(res)

        if name and not class_name:  name = restore_tag_name(name)
        if class_name:  class_name = ':' + class_name
        node = Node(name + class_name, result)
        if not ignore_pos and '_pos' in attrs:
            node._pos = int(attrs['_pos'])
            del attrs['_pos']
        if attrs:
            node.attr.update(attrs)
        return s, node

    match_header = xml.search(RX_XML_HEADER)
    start = xml.index(match_header.start()) if match_header else 0
    _, tree = parse_full_content(xml[start:])
    return RootNode(tree)


class DHParser_JSONEncoder(json.JSONEncoder):
    """A JSON-encoder that also encodes ``nodetree.Node`` as valid json objects.
    Node-objects are encoded using Node.as_json.
    """
    def default(self, obj):
        if isinstance(obj, Node):
            return cast(Node, obj).to_json_obj()
        elif obj is JSONnull or isinstance(obj, JSONnull):
            return None
        return json.JSONEncoder.default(self, obj)


def parse_json(json_str: str) -> RootNode:
    """
    Parses a JSON-representation of a node-tree. Other than
    and parse_xml, this function does not convert any json-document into
    a node-tree, but only json-documents that represents a node-tree, e.g.
    a json-document that has been produced by `Node.as_json()`!
    """
    json_obj = json.loads(json_str, object_pairs_hook=lambda pairs: OrderedDict(pairs))
    return RootNode(Node.from_json_obj(json_obj))


def deserialize(xml_sxpr_or_json: str) -> Optional[Node]:
    """
    Parses either XML or S-expressions or a JSON representation of a
    syntax-tree. Which of these is detected automatically.
    """
    if RX_IS_XML.match(xml_sxpr_or_json):
        return parse_xml(xml_sxpr_or_json)
    elif RX_IS_SXPR.match(xml_sxpr_or_json):
        return parse_sxpr(xml_sxpr_or_json)
    elif re.match(r'\s*', xml_sxpr_or_json):
        return None
    else:
        try:
            return parse_json(xml_sxpr_or_json)
        except json.decoder.JSONDecodeError:
            m = re.match(r'\s*(.*)\n?', xml_sxpr_or_json)
            snippet = m.group(1) if m else ''
            raise ValueError('Snippet is neither S-expression nor XML: ' + snippet + ' ...')


# if __name__ == "__main__":
#     st = parse_sxpr("(alpha (beta (gamma i\nj\nk) (delta y)) (epsilon z))")
#     print(st.as_sxpr())
#     print(st.as_xml())
