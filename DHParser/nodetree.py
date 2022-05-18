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


"""
Module ``nodetree`` encapsulates the functionality for creating and handling
trees of nodes, in particular, syntax-trees. This includes serialization
and deserialization of node-trees, navigating and searching node-trees as well
as annotating node-trees with attributes and error messages.

``nodetree`` can also be seen as a document-tree-library
for handling any kind of XML-data. In contrast to
`Elementtree <https://docs.python.org/3/library/xml.etree.elementtree.html>`_
and `lxml <https://lxml.de/>`_, nodetree maps mixed content to dedicated nodes,
which simplifies the programming of algorithms that run on the data stored
in the (XML-)tree.
"""


import bisect
import copy
import functools
import json
import sys
from typing import Callable, cast, Iterator, Sequence, List, Set, Union, \
    Tuple, Container, Optional, Dict, Any

if sys.version_info >= (3, 6, 0):
    OrderedDict = dict
else:
    from collections import OrderedDict

try:
    import cython
except ImportError:
    import DHParser.externallibs.shadow_cython as cython

from DHParser.configuration import get_config_value, ALLOWED_PRESET_VALUES
from DHParser.error import Error, ErrorCode, ERROR, PARSER_STOPPED_BEFORE_END, \
    add_source_locations, SourceMapFunc, has_errors, only_errors
from DHParser.preprocess import gen_neutral_srcmap_func
from DHParser.stringview import StringView  # , real_indices
from DHParser.toolkit import re, linebreaks, line_col, JSONnull, \
    validate_XML_attribute_value, fix_XML_attribute_value, lxml_XML_attribute_value, \
    deprecation_warning


__all__ = ('WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'REGEXP_PTYPE',
           'EMPTY_PTYPE',
           'LEAF_PTYPES',
           'ZOMBIE_TAG',
           'PLACEHOLDER',
           'TreeContext',
           'ResultType',
           'StrictResultType',
           'ChildrenType',
           'CriteriaType',
           'NodeMatchFunction',
           'ContextMatchFunction',
           'ANY_NODE',
           'NO_NODE',
           'LEAF_NODE',
           'ANY_CONTEXT',
           'NO_CONTEXT',
           'LEAF_CONTEXT',
           'Node',
           'content',
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
           'prev_context',
           'next_context',
           'zoom_into_context',
           'leaf_context',
           'prev_leaf_context',
           'next_leaf_context',
           'PickChildFunction',
           'FIRST_CHILD',
           'LAST_CHILD',
           'select_context_if',
           'select_context',
           'pick_context',
           'foregoing_str',
           'ensuing_str',
           'select_from_context_if',
           'select_from_context',
           'pick_from_context',
           'serialize_context',
           'context_sanity_check',
           'ContextMapping',
           'generate_context_mapping',
           'map_pos_to_context',
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
REGEXP_PTYPE = ':RegExp'
EMPTY_PTYPE = ':EMPTY'
LEAF_PTYPES = {WHITESPACE_PTYPE, TOKEN_PTYPE, REGEXP_PTYPE, EMPTY_PTYPE}

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
# - a function Node -> bool
re_pattern = Any
CriteriaType = Union['Node', str, Container[str], Callable, int, re_pattern]

TreeContext = List['Node']
NodeMatchFunction = Callable[['Node'], bool]
ContextMatchFunction = Callable[[TreeContext], bool]

ANY_NODE = lambda nd: True
NO_NODE = lambda nd: False
LEAF_NODE = lambda nd: not nd._children

ANY_CONTEXT = lambda ctx: True
NO_CONTEXT = lambda ctx: False
LEAF_CONTEXT = lambda ctx: not ctx[-1].children


def create_match_function(criterion: CriteriaType) -> NodeMatchFunction:
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
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda nd: nd.name in cast(Container, criterion)
    elif str(type(criterion)) in ("<class '_regex.Pattern'>", "<class 're.Pattern'>"):
        return lambda nd: criterion.fullmatch(nd.content)
    raise TypeError("Criterion %s of type %s does not represent a legal criteria type"
                    % (repr(criterion), type(criterion)))


def create_context_match_function(criterion: CriteriaType) -> ContextMatchFunction:
    """
    Creates a context-match-function (TreeContext -> bool) for the given
    criterion that returns True, if the last node in the context passed
    to the function matches the criterion.

    See :py:func:`create_match_function()` for a description of the possible
    criteria and their meaning.

    :param criterion: Either a node, the id of a node, a frozen node,
        a name or a container (usually a set) of multiple tag names,
        a regular expression pattern or another match function.

    :returns: a match-function (TreeContext -> bool) for the given criterion.
    """
    if isinstance(criterion, int):
        return lambda ctx: id(ctx[-1]) == criterion
    elif isinstance(criterion, FrozenNode):
        return lambda ctx: ctx[-1].equals(criterion, ignore_attr_order=True)
    elif isinstance(criterion, Node):
        return lambda ctx: ctx[-1] == criterion
        # return lambda ctx[-1]: ctx[-1].equals(criterion)  # may yield wrong results for Node.ictx[-1]ex()
    elif isinstance(criterion, str):
        return lambda ctx: ctx[-1].name == criterion
    elif callable(criterion):
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda ctx: ctx[-1].name in cast(Container, criterion)
    elif str(type(criterion)) in ("<class '_regex.Pattern'>", "<class 're.Pattern'>"):
        return lambda ctx: criterion.fullmatch(ctx[-1].content)
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

ChildrenType = Tuple['Node', ...]
StrictResultType = Union[ChildrenType, StringView, str]
ResultType = Union[StrictResultType, 'Node']


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

    :ivar len: The full length of the node's string result if the
            node is a leaf node or, otherwise, the length of the concatenated
            string result's of its descendants. The figure always represents
            the length before AST-transformation and will never change
            through AST-transformation. READ ONLY!

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
                 result: Union[Tuple['Node', ...], 'Node', StringView, str],
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
            self._result = result        # type: Union[Tuple['Node', ...], StringView, str]
            self._children = tuple()     # type: Tuple['Node', ...]
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

    def strlen(self):
        """Returns the length of the string-content of this node.
        Mind that len(node) returns the number of children of this node!"""
        flag = False
        for child in self.children:
            if not isinstance(child, Node):
                print('>>>', self.name, self.children)
                return "ERROR"
        return (sum(child.strlen() for child in self._children)
                if self._children else len(self._result))

    def __len__(self):
        raise AssertionError(
            "len() on Node-objects would be too mbiguous! Please use either "
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

    @property
    def tag_name(self) -> str:
        deprecation_warning('Property "DHParser.nodetree.Node.tag_name" is deprecated. '
                            'Use "Node.name" instead!')
        return self.name

    @tag_name.setter
    def tag_name(self, name: str):
        deprecation_warning('Property "DHParser.nodetree.Node.tag_name" is deprecated. '
                            'Use "Node.name" instead!')
        self.name = name

    def equals(self, other: 'Node', ignore_attr_order: bool = True) -> bool:
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
        if self.name == other.name and self.compare_attr(other, ignore_attr_order):
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

    def _set_result(self, result: Union[Tuple['Node', ...], 'Node', StringView, str]):
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

    def _init_child_pos(self):
        """Initialize position values of children with potentially
        unassigned positions, i.e. child.pos < 0."""
        children = self._children  # type: Tuple['Node', ...]
        if children:
            offset = self._pos
            prev = children[0]
            if prev._pos < 0:
                prev.with_pos(offset)
            for child in children[1:]:
                if child._pos < 0:
                    offset = offset + prev.strlen()
                    child.with_pos(offset)
                else:
                    offset = child._pos
                prev = child

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
            self._init_child_pos()

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

    def with_pos(self, pos: int) -> 'Node':
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
            raise AssertionError(f"Position value {self._pos} cannot be "
                                 f"reassigned to a different value ({pos})!")
        assert pos >= 0, "Negative value %i not allowed!"
        if self._pos < 0:
            self._pos = pos
            # recursively adjust pos-values of all children
            self._init_child_pos()
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

    def with_attr(self, *attr_dict, **attributes) -> 'Node':
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
        :param attributes: alternatively, a squences of keyword parameters
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

    def compare_attr(self, other: 'Node', ignore_order: bool = True) -> bool:
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

    def __getitem__(self, key: Union[CriteriaType, int, slice]) -> Union['Node', List['Node']]:
        """
        Returns the child node with the given index if ``key`` is
        an integer or all child-nodes with the given tag name. Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")) (b "Y"))')
            >>> tree[0]
            Node('b', 'X')
            >>> tree['X']
            Node('X', (Node('c', 'd')))
            >>> tree['b']
            [Node('b', 'X'), Node('b', 'Y')]

            >>> from DHParser.toolkit import as_list
            >>> as_list(tree['b'])
            [Node('b', 'X'), Node('b', 'Y')]
            >>> as_list(tree['e'])
            [Node('e', (Node('X', 'F')))]

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
            items = [child for child in self._children if mf(child)]
            if items:
                return items if len(items) >= 2 else items[0]
            raise KeyError(str(key))

    def __setitem__(self, 
                    key: Union[CriteriaType, slice, int], 
                    value: Union['Node', Sequence['Node']]):
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

    def __delitem__(self, key: Union[int, slice, CriteriaType]):
        """
        Removes children from the node. Note that integer values passed to
        parameter `key` are always interpreted as index, not as an object id
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

    def get(self, key: Union[int, slice, CriteriaType],
            surrogate: Union['Node', Sequence['Node']]) -> Union['Node', Sequence['Node']]:
        """Returns the child node with the given index if ``key``
        is an integer or the first child node with the given tag name. If no
        child with the given index or name exists, the ``surrogate`` is
        returned instead. This mimics the behaviour of Python's dictionary's
        `get()`-method.

        The type of the return value is always the same type as that of the
        surrogate. If the surrogate is a Node, but there are several items
        matching `key`, then only the first of these will be returned.
        """
        try:
            items = self[key]
            if isinstance(surrogate, Sequence):
                return items if isinstance(items, Sequence) else (items,)
            else:
                return items[0] if isinstance(items, Sequence) else items
        except (KeyError, ValueError, IndexError):
            return surrogate

    def __contains__(self, what: CriteriaType) -> bool:
        """
        Returns true if at least one child that matches the given criterion
        exists. See :py:func:`create_match_function()` for a catalogue of
        possible criteria.

        :param what: a criterion that describes the child-node
        :returns: True, if at least one child fulfills the criterion
        """
        mf = create_match_function(what)
        for child in self._children:
            if mf(child):
                return True
        return False

    def remove(self, node: 'Node'):
        """Removes `node` from the children of the node."""
        if not self.children:
            raise ValueError('Node.remove(x): Called on a node without children')
        i = len(self._children)
        self.result = tuple(nd for nd in self._children if nd != node)
        if len(self.result) >= i:
            raise ValueError('Node.remove(x): x not among children')

    def insert(self, index: int, node: 'Node'):
        """Inserts a node at position `index`"""
        if not self.children and self._result:
            raise ValueError('Node.insert(i, node): Called on a leaf-node')
        result = list(self.children)
        result.insert(index, node)
        self.result = tuple(result)

    def index(self, what: CriteriaType, start: int = 0, stop: int = 2**30) -> int:
        """
        Returns the index of the first child that fulfills the criterion
        `what`. If the parameters start and stop are given, the search is
        restricted to the children with indices from the half-open interval
        [start:end[. If no such child exists a ValueError is raised.

        :param what: the criterion by which the child is identified, the index
            of which shall be returned.
        :param start: the first index to start searching.
        :param stop: the last index that shall be searched
        :returns: the index of the first child that matches `what`.
        :raises: ValueError, if no child matching the criterion `what` was found.
        """
        assert 0 <= start < stop
        if not self.children:
            raise ValueError('Node.index(x): Called on a Node without children')
        mf = create_match_function(what)
        for i, child in enumerate(self._children[start:stop]):
            if mf(child):
                return i + start
        raise ValueError("Node identified by '%s' not among child-nodes." % str(what))

    @cython.locals(i=cython.int)
    def indices(self, what: CriteriaType) -> Tuple[int, ...]:
        """
        Returns the indices of all children that fulfil the criterion `what`.
        """
        mf = create_match_function(what)
        children = self._children
        return tuple(i for i in range(len(children)) if mf(children[i]))

    def select_if(self, match_function: NodeMatchFunction,
                  include_root: bool = False, reverse: bool = False,
                  skip_subtree: NodeMatchFunction = NO_NODE) -> Iterator['Node']:
        """
        Generates an iterator over all nodes in the tree for which
        `match_function()` returns True. See the more general function
        :py:meth:`Node.select()` for a detailed description and examples.
        The tree is traversed pre-order by the iterator.
        """
        if include_root and match_function(self):
            yield self
        child_iterator = reversed(self._children) if reverse else self._children
        for child in child_iterator:
            if match_function(child):
                yield child
            if child._children and not skip_subtree(child):
                yield from child.select_if(match_function, False, reverse, skip_subtree)

    def select(self, criterion: CriteriaType,
               include_root: bool = False, reverse: bool = False,
               skip_subtree: CriteriaType = NO_NODE) -> Iterator['Node']:
        """
        Generates an iterator over all nodes in the tree that fulfill the
        given criterion. See :py:func:`create_match_function()` for a
        catalogue of possible criteria.

        :param criterion: The criterion for selecting nodes.
        :param include_root: If False, only descendant nodes will be checked
            for a match.
        :param reverse: If True, the tree will be walked in reverse
                order, i.e. last children first.
        :param skip_subtree: A criterion to identify subtrees, the returned
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
        """
        return self.select_if(create_match_function(criterion), include_root, reverse,
                              create_match_function(skip_subtree))

    def select_children(self, criterion: CriteriaType, reverse: bool = False) -> Iterator['Node']:
        """Returns an iterator over all direct children of a node that
        fulfil the given `criterion`. See :py:meth:`Node.select()` for a description
        of the parameters.
        """
        match_function = create_match_function(criterion)
        if reverse:
            for child in reversed(tuple(self.select_children(criterion, False))):
                yield child
        else:
            for child in self._children:
                if match_function(child):
                    yield child

    def pick(self, criterion: CriteriaType,
             include_root: bool = False,
             reverse: bool = False,
             skip_subtree: CriteriaType = NO_NODE) -> Optional['Node']:
        """
        Picks the first (or last if run in reverse mode) descendant that
        fulfils the given criterion. See :py:func:`create_match_function()`
        for a catalogue of possible criteria.

        This function is syntactic sugar for `next(node.select(criterion, ...))`.
        However, rather than raising a StopIterationError if no descendant
        with the given tag-name exists, it returns `None`.
        """
        try:
            return next(self.select(criterion, include_root, reverse, skip_subtree))
        except StopIteration:
            return None

    def pick_child(self, criterion: CriteriaType, reverse: bool = False) -> Optional['Node']:
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
            return next(self.select_children(criterion, reverse=reverse))
        except StopIteration:
            return None

    @cython.locals(location=cython.int, end=cython.int)
    def locate(self, location: int) -> Optional['Node']:
        """
        Returns the leaf-Node that covers the given ``location``, where
        location is the actual position within ``self.content`` (not the
        source code position that the pos-attribute represents). If
        the location lies outside the node's string content, `None` is
        returned.
        """
        end = 0
        for nd in self.select_if(lambda nd: not nd._children, include_root=True):
            end += nd.strlen()
            if location < end:
                return nd
        return None

    def find_parent(self, node) -> Optional['Node']:
        """
        Finds and returns the parent of `node` within the tree represented
        by `self`. If the tree does not contain `node`, the value `None`
        is returned.
        """
        for nd in self.select_if(lambda nd: bool(nd._children), include_root=True):
            if node in nd._children:
                return nd
        return None

    # context selection ###

    def select_context_if(self, match_function: ContextMatchFunction,
                          include_root: bool = False,
                          reverse: bool = False,
                          skip_subtree: ContextMatchFunction = NO_CONTEXT) -> Iterator[TreeContext]:
        """
        Like :py:func:`Node.select_if()` but yields the entire context (i.e. list
        of descendants, the last one being the matching node) instead of just
        the matching nodes. NOTE: In contrast to `select_if()`, `match_function`
        receives the complete context as argument, rather than just the last node!
        """
        def recursive(ctx, include_root) -> Iterator[TreeContext]:
            nonlocal match_function, reverse, skip_subtree
            if include_root and match_function(ctx):
                yield ctx
            top = ctx[-1]
            child_iterator = reversed(top._children) if reverse else top._children
            for child in child_iterator:
                child_ctx = ctx + [child]
                if match_function(child_ctx):
                    yield child_ctx
                if child._children and not skip_subtree(child_ctx):
                    yield from recursive(child_ctx, include_root=False)
        yield from recursive([self], include_root)

    def select_context(self, criterion: CriteriaType,
                       include_root: bool = False,
                       reverse: bool = False,
                       skip_subtree: CriteriaType = NO_CONTEXT) -> Iterator[TreeContext]:
        """
        Like :py:meth:`Node.select()` but yields the entire context (i.e. list of
        descendants, the last one being the matching node) instead of just
        the matching nodes.
        """
        return self.select_context_if(create_context_match_function(criterion),
                                      include_root, reverse,
                                      create_context_match_function(skip_subtree))

    def pick_context(self, criterion: CriteriaType,
                     include_root: bool = False,
                     reverse: bool = False,
                     skip_subtree: CriteriaType = NO_CONTEXT) -> TreeContext:
        """
        Like :py:meth:`Node.pick()`, only that the entire context (i.e.
        chain of descendants) relative to `self` is returned.
        """
        try:
            return next(self.select_context(criterion, include_root, reverse, skip_subtree))
        except StopIteration:
            return []

    @cython.locals(location=cython.int, end=cython.int)
    def locate_context(self, location: int) -> TreeContext:
        """
        Like :py:meth:`Node.locate()`, only that the entire context (i.e.
        chain of descendants) relative to `self` is returned.
        """
        end = 0
        for ctx in self.select_context_if(lambda ctx: not ctx[-1]._children, include_root=True):
            end += ctx[-1].strlen()
            if location < end:
                return ctx
        return []

    def _reconstruct_context_recursive(self: 'Node', node: 'Node') -> TreeContext:
        """
        Determines the chain of ancestors of a node that leads up to self. Other than
        the public method `reconstruct_context`, this method returns the chain of ancestors
        in reverse order [node, ... , self] and returns None in case `node` does not exist
        in the tree rooted in self instead of raising a Value Error.
        If `node` equals `self`, any empty context, i.e. list will be returned.
        """
        if node in self._children:
            return [node, self]
        for nd in self._children:
            ctx = nd._reconstruct_context_recursive(node)
            if ctx:
                ctx.append(self)
                return ctx
        return []

    def reconstruct_context(self, node: 'Node') -> TreeContext:
        """
        Determines the chain of ancestors of a node that leads up to self.
        :param node: the descendant node, the ancestry of which shall be determined.
        :return: the list of nodes starting with self and leading to `node`
        :raises: ValueError, in case `node` does not occur in the tree rooted in `self`
        """
        if node == self:
            return [node]
        ctx = self._reconstruct_context_recursive(node)
        if ctx:
            ctx.reverse()
            return ctx
        else:
            raise ValueError('Node "%s" does not occur in the tree %s '
                             % (node.name, flatten_sxpr(self.as_sxpr())))

    # milestone support ### EXPERIMENTAL!!! ###

    # def find_nearest_common_ancestor(self, A: 'Node', B: 'Node') -> 'Node':
    #     """
    #     Finds the nearest common ancestor of the two nodes A and B.
    #     :param A: a node in the tree
    #     :param B: another node in the tree
    #     :return: the nearest common ancestor
    #     :raises: ValueError in case `A` and `B` are not both rooted in `self`
    #     """
    #     ctxA = self.reconstruct_context(A)
    #     ctxB = self.reconstruct_context(B)
    #     for a,b in zip(ctxA, ctxB):
    #         if a != b:
    #             break
    #         common_ancestor = a
    #     return common_ancestor

    def milestone_segment(self, begin: 'Node', end: 'Node') -> 'Node':
        """
        EXPERIMENTAL!!!
        Picks a segment from a tree beginning with start and ending with end.

        :param begin: the opening milestone (will be included in the result)
        :param end: the closing milestone (will be included in the result)
        :return: a tree(-segment) encompassing all nodes from the opening
            milestone up to and including the closing milestone.
        """
        def index(parent: 'Node', nd: 'Node') -> int:
            children = parent._children
            for i in range(len(children)):
                if nd == children[i]:
                    return i
            raise ValueError

        def left_cut(result: Tuple['Node', ...], index: int, subst: 'Node') -> Tuple['Node', ...]:
            return (subst,) + result[index + 1:]

        def right_cut(result: Tuple['Node', ...], index: int, subst: 'Node') -> Tuple['Node', ...]:
            return result[:index] + (subst,)

        def cut(ctx: TreeContext, cut_func: Callable) -> 'Node':
            child = ctx[-1]
            tainted = False
            for i in range(len(ctx) - 1, 0, -1):
                parent = ctx[i - 1]
                k = index(parent, ctx[i])
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
        ctxA = self.reconstruct_context(begin)  # type: TreeContext
        ctxB = self.reconstruct_context(end)    # type: TreeContext
        for a, b in zip(ctxA, ctxB):
            if a != b:
                break
            common_ancestor = a
        left = cut(ctxA[ctxA.index(common_ancestor):], left_cut)    # type: Node
        right = cut(ctxB[ctxB.index(common_ancestor):], right_cut)  # type: Node
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
                txt.append(" `(%s)" % ';  '.join(str(err) for err in root.node_errors(node)))
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

    def as_xml(self, src: str = None,
               indentation: int = 2,
               inline_tags: Set[str] = frozenset(),
               string_tags: Set[str] = frozenset(),
               empty_tags: Set[str] = frozenset(),
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
                    error_msg = f'Empty element "{node.name}" with content: "{node.content}" !?' \
                                f'Use Node.as_xml(..., strict_mode=False) to suppress this error!'
                    if strict_mode:  raise ValueError(error_msg)
                    else:
                        empty_tags = empty_tags.copy()
                        empty_tags.remove(node.name)
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
            if node.name in empty_tags or (node.name in string_tags and not node.has_attr()):
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
              [nd.to_json_obj() for nd in self._children] if self._children else str(self.result)]
        pos = self._pos
        if pos >= 0:
            jo.append(pos)
        if self.has_attr():
            jo.append(self.attr)
        return jo

    @staticmethod
    def from_json_obj(json_obj: Union[Dict, Sequence]) -> 'Node':
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
    def serialize(self: 'Node', how: str = 'default') -> str:
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
            return self.as_xml()
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

    def as_etree(self, ET=None, string_tags: Set[str] = {":Text"}, empty_tags: Set[str] = set()):
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
    def from_etree(et, string_tag: str = ':Text') -> 'Node':
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


def content(segment: Union[Node, Tuple[Node, ...]]) -> str:
    """Returns the string content from a single node or a tuple of Nodes.
    """
    if isinstance(segment, Node):
        return segment.content
    else:
        return ''.join(nd.content for nd in segment)


#######################################################################
#
# Functions related to the Node class
#
#######################################################################


# Query contexts as paths #############################################

### EXPERIMENTAL

def as_path(context: TreeContext) -> str:
    """Returns the context a pseudo filepath of tag-names."""
    tag_list = ['']
    for node in context:
        assert not node.name.find('/'), 'as_path() not allowed for tag-names containing "/"!'
        tag_list.append(node.name)
    if context[-1].children:
        tag_list.append('')
    return '/'.join(tag_list)


def match_path(path: str, glob_pattern: str) -> bool:
    """Matches a context as path against a glob-pattern."""
    from fnmatch import fnmatchcase
    if glob_pattern[0:1] not in ("/", "*"):
        glob_pattern = "*/" + glob_pattern
    return fnmatchcase(path, glob_pattern)



# Navigate contexts ###################################################

@cython.locals(i=cython.int, k=cython.int)
def prev_context(context: TreeContext) -> Optional[TreeContext]:
    """Returns the context of the predecessor of the last node in the
    context. The predecessor is the sibling of the same parent-node
    preceding the node, or, if it already is the first sibling, the parent's
    sibling preceding the parent, or grandparent's sibling and so on.
    In case no predecessor is found, when the first ancestor has been
    reached, `None` is returned.
    """
    assert isinstance(context, list)
    node = context[-1]
    for i in range(len(context) - 2, -1, -1):
        siblings = context[i]._children
        if node is not siblings[0]:
            for k in range(1, len(siblings)):
                if node is siblings[k]:
                    return context[:i + 1] + [siblings[k - 1]]
            raise AssertionError('Structural Error: context[%i] is not the parent of context[%i]'
                                 % (i, i + 1))
        node = context[i]
    return None


@cython.locals(i=cython.int, k=cython.int)
def next_context(context: TreeContext) -> Optional[TreeContext]:
    """Returns the context of the successor of the last node in the
    context. The successor is the sibling of the same parent Node
    succeeding the node, or if it already is the last sibling, the
    parent's sibling succeeding the parent, or grand-parent's sibling and
    so on. In case no successor is found when the first ancestor has been
    reached, `None` is returned.
    """
    assert isinstance(context, list)
    node = context[-1]
    for i in range(len(context) - 2, -1, -1):
        siblings = context[i]._children
        if node is not siblings[-1]:
            for k in range(len(siblings) - 2, -1, -1):
                if node is siblings[k]:
                    return context[:i + 1] + [siblings[k + 1]]
            raise AssertionError('Structural Error: context[%i] is not the parent of context[%i]'
                                 % (i, i + 1))
        node = context[i]
    return None


PickChildFunction = Callable[[Node], Node]
LAST_CHILD = lambda nd: nd.result[-1]
FIRST_CHILD = lambda nd: nd.result[0]


def zoom_into_context(context: Optional[TreeContext],
                      pick_child: PickChildFunction,
                      steps: int) \
                      -> Optional[TreeContext]:
    """Returns the context of a descendant that follows `steps` generations
    up the tree originating in 'context[-1]`. If `steps` < 0 this will be
    as many generations as are needed to reach a leaf-node.
    The function `pick_child` determines which branch to follow during each
    iteration, as long as the top of the context is not yet a leaf node.
    A `context`-parameter value of `None` will simply be passed through.
    """
    if context:
        ctx = context.copy()
        top = ctx[-1]
        while top.children and steps != 0:
            top = pick_child(top)
            ctx.append(top)
            steps -= 1
        return ctx
    return None


leaf_context = functools.partial(zoom_into_context, steps=-1)
next_leaf_context = lambda ctx: leaf_context(next_context(ctx), FIRST_CHILD)
prev_leaf_context = lambda ctx: leaf_context(prev_context(ctx), LAST_CHILD)


def foregoing_str(context: TreeContext, length: int = -1) -> str:
    """Returns `length` characters from the string content preceding
    the context."""
    N = 0
    l = []
    ctx = prev_context(context)
    while ctx and (N < length or length < 0):
        s = ctx[-1].content
        l.append(s)
        N += len(s)
        ctx = prev_context(ctx)
    foregoing = ''.join(reversed(l))
    return foregoing if length < 0 else foregoing[-length:]


def ensuing_str(context: TreeContext, length: int = -1) -> str:
    """Returns `length` characters from the string content succeeding
    the context."""
    N = 0
    l = []
    ctx = next_context(context)
    while ctx and (N < length or length < 0):
        s = ctx[-1].content
        l.append(s)
        N += len(s)
        ctx = next_context(ctx)
    following = ''.join(l)
    return following if length < 0 else following[:length]


def select_context_if(start_context: TreeContext,
                      match_function: ContextMatchFunction,
                      include_root: bool = False,
                      reverse: bool = False,
                      skip_subtree: ContextMatchFunction = NO_CONTEXT) -> Iterator[TreeContext]:
    """
    Creates an Iterator yielding all `contexts` for which the
    `match_function` is true, starting from `context`.
    """

    def recursive(ctx):
        nonlocal match_function, reverse, skip_subtree
        if match_function(ctx):
            yield ctx
        top = ctx[-1]
        child_iterator = reversed(top._children) if reverse else top._children
        for child in child_iterator:
            child_ctx = ctx + [child]
            if not skip_subtree(child_ctx):
                yield from recursive(child_ctx)

    context = start_context.copy()
    while context:
        if include_root:
            yield from recursive(context)
        else:
            include_root = True
        node = context.pop()
        edge, delta = (0, -1) if reverse else (-1, 1)
        while context and node is context[-1]._children[edge]:
            if match_function(context):
                yield context
            node = context.pop()
        if context:
            parent = context[-1]
            i = parent.index(node)
            nearest_sibling = parent._children[i + delta]
            context.append(nearest_sibling)
            # include_root = True

    # context = context.copy()
    # while context:
    #     if match_function(context):
    #         yield context
    #     node = context.pop()
    #
    #     edge, delta = (0, -1) if reverse else (-1, 1)
    #     while context and node is context[-1]._children[edge]:
    #         if match_function(context):
    #             yield context
    #         node = context.pop()
    #     if context:
    #         parent = context[-1]
    #         i = parent.index(node)
    #         nearest_sibling = parent._children[i + delta]
    #         innermost_ctx = nearest_sibling.pick_context(
    #             LEAF_CONTEXT, include_root=True, reverse=reverse)
    #         context.extend(innermost_ctx)


def select_context(start_context: TreeContext,
                   criterion: CriteriaType,
                   include_root: bool = False,
                   reverse: bool = False,
                   skip_subtree: CriteriaType = NO_CONTEXT) -> Iterator[TreeContext]:
    """
    Like `select_context_if()` but yields the entire context (i.e. list of
    descendants, the last one being the matching node) instead of just
    the matching nodes.
    """
    return select_context_if(start_context, create_context_match_function(criterion),
                             include_root, reverse, create_context_match_function(skip_subtree))


def pick_context(start_context: TreeContext,
                 criterion: CriteriaType,
                 include_root: bool = False,
                 reverse: bool = False,
                 skip_subtree: CriteriaType = NO_CONTEXT) -> Optional[TreeContext]:
    """
    Like `Node.pick()`, only that the entire context (i.e. chain of descendants)
    relative to `self` is returned.
    """
    try:
        return next(select_context(
            start_context, criterion, include_root=include_root, reverse=reverse,
            skip_subtree=skip_subtree))
    except StopIteration:
        return None


def select_from_context_if(context: TreeContext,
                           match_function: NodeMatchFunction,
                           reverse: bool=False):
    """Yields all nodes from context for which the match_function is true."""
    if reverse:
        for nd in reversed(context):
            if match_function(nd):
                yield nd
    else:
        for nd in context:
            if match_function(nd):
                yield nd


def select_from_context(context: TreeContext, criterion: CriteriaType, reverse: bool=False):
    """Yields all nodes from context which fulfill the criterion."""
    return select_from_context_if(context, create_match_function(criterion), reverse)


def pick_from_context(context: TreeContext, criterion: CriteriaType, reverse: bool=False) \
        -> Optional[Node]:
    """Picks the first node from the context that fulfils the criterion. Returns `None`
    if the context does not contain any node fulfilling the criterion."""
    try:
        return next(select_from_context(context, criterion, reverse=reverse))
    except StopIteration:
        return None


def serialize_context(context: TreeContext, with_content: int = 0, delimiter: str = ' <- ') \
        -> str:
    """Serializes a context as string.

    :param context: the context to be serialized.
    :param with_content: the number of nodes from the end of the context for
        which the content will be displayed next to the name.
    :param delimiter: The delimiter separating the nodes in the returned string.
    :returns: the string-serialization of the given context.
    """
    if with_content == 0:
        lines = [nd.name for nd in context]
    else:
        n = with_content if with_content > 0 else len(context)
        lines = [nd.name for nd in context[:-n]]
        lines.extend(nd.name + ':' + str(nd.content) for nd in context[-n:])
    return delimiter.join(lines)


def context_sanity_check(context: TreeContext) -> bool:
    """Checks whether the nodes following in the context-list are really
    immediate descendants of each other."""
    return all(context[i] in context[i - 1]._children for i in range(1, len(context)))


# Context-mapping (allowing a "string-view" on syntax-trees) ##########

ContextMapping = Tuple[List[int], List[TreeContext]]  # A mapping of character positions to contexts


def generate_context_mapping(node: Node) -> ContextMapping:
    """
    Generates a context mapping for all leave-nodes of the tree
    originating in `node`. A context mapping is an ordered mapping
    of the first text position of every leaf-node to the context of
    this node.

    Context mappings are a helpful tool when searching substrings in a
    document and then trying to locate them within in the tree.

    :param node: the root of the tree for which a context mapping shall be
        generated.
    :returns: The context mapping for the node.
    """
    pos = 0
    pos_list, ctx_list = [], []
    for ctx in node.select_context_if(LEAF_CONTEXT, include_root=True):
        pos_list.append(pos)
        ctx_list.append(ctx)
        pos += ctx[-1].strlen()
    return pos_list, ctx_list


def map_pos_to_context(i: int, cm: ContextMapping) -> Tuple[TreeContext, int]:
    """Yields the context and relative position for the absolute
    position `i`.

    :param i:   a position in the content of the tree for which the
        context mapping `cm` was generated
    :param cm:  a context mapping
    :returns:    tuple (context, relative position) where relative
        position is the position of i relative to the actual
        position of the last node in the context.
    """
    ctx_index = bisect.bisect_right(cm[0], i) - 1
    return cm[1][ctx_index], i - cm[0][ctx_index]


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
    content equality when picking or selecting nodes or contexts from
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

    def with_pos(self, pos: int) -> 'Node':
        raise NotImplementedError("Position values cannot be assigned to frozen nodes!")

    def to_json_obj(self) -> List:
        raise NotImplementedError("Frozen nodes cannot and be serialized as JSON!")

    @staticmethod
    def from_json_obj(json_obj: Union[Dict, Sequence]) -> 'Node':
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


# #####################################################################
#
# RootNode - manage global properties of trees, like error messages
#
#######################################################################


_EMPTY_SET_SENTINEL = frozenset()  # needed by RootNode.as_xml()


class RootNode(Node):
    """The root node for the node-tree is a special kind of node that keeps
    and manages global properties of the tree as a whole. These are first and
    foremost the list off errors that occurred during tree generation
    (i.e. parsing) or any transformation of the tree. Other properties concern
    the customization of the XML-serialization.

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
        that contain an error at that particular location
    :ivar error_flag: the highest warning or error level of all errors
        that occurred.

    :ivar source:  The source code (after preprocessing)
    :ivar source_mapping:  A source mapping function to map source code
        position to the positions of the non-preprocessed source.
        See module `preprocess`
    :ivar lbreaks: A list of indices of all linebreaks in the source.

    :ivar inline_tags: see `Node.as_xml()` for an explanation.
    :ivar string_tags: see `Node.as_xml()` for an explanation.
    :ivar empty_tags: see `Node.as_xml()` for an explanation.
    """

    def __init__(self, node: Optional[Node] = None,
                 source: Union[str, StringView] = '',
                 source_mapping: Optional[SourceMapFunc] = None):
        super().__init__('__not_yet_ready__', '')
        self.errors: List[Error] = []
        self._error_set: Set[Error] = set()
        self.error_nodes: Dict[int, List[Error]] = dict()   # id(node) -> error list
        self.error_positions: Dict[int, Set[int]] = dict()  # pos -> set of id(node)
        self.error_flag = 0
        # info on source code (to be carried along all stages of tree-processing)
        self.source = source           # type: Union[str, StringView]
        if source_mapping is None:
            self.source_mapping = gen_neutral_srcmap_func(source)
        else:
            self.source_mapping = source_mapping  # type: SourceMapFunc
        self.lbreaks = linebreaks(source)  # List[int]
        # customization for XML-Representation
        self.inline_tags = set()  # type: Set[str]
        self.string_tags = set()    # type: Set[str]
        self.empty_tags = set()   # type: Set[str]
        if node is not None:
            self.swallow(node, source, source_mapping)

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
            duplicate._children = copy.deepcopy(self._children)
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
        duplicate.errors = copy.deepcopy(self.errors)
        duplicate._error_set = {error for error in duplicate.errors}
        duplicate.error_nodes = {map_id.get(i, i): el[:] for i, el in self.error_nodes.items()}
        duplicate.error_positions = {pos: {map_id.get(i, i) for i in s}
                                     for pos, s in self.error_positions.items()}
        duplicate.error_flag = self.error_flag
        duplicate.inline_tags = self.inline_tags
        duplicate.string_tags = self.string_tags
        duplicate.empty_tags = self.empty_tags
        duplicate.name = self.name
        return duplicate

    def swallow(self, node: Optional[Node],
                source: Union[str, StringView] = '',
                source_mapping: Optional[SourceMapFunc] = None) \
            -> 'RootNode':
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
        if source_mapping is None:
            self.source_mapping = gen_neutral_srcmap_func(source)
        else:
            self.source_mapping = source_mapping  # type: SourceMapFunc
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

    # def save_error_state(self) -> tuple:
    #     """Saves the error state. Useful for when backtracking. See
    #     :py:mod:`parse.Forward` """
    #     if self.error_flag:
    #         return (self.errors.copy(),
    #                 {k: v.copy() for k, v in self.error_nodes.items()},
    #                 {k: v.copy() for k, v in self.error_positions.items()},
    #                 self.error_flag)
    #     else:
    #         return ()
    #
    # def restore_error_state(self, error_state: tuple):
    #     """Resotores a previously saved error state."""
    #     if error_state:
    #         self.errors, self.error_nodes, self.error_positions, self.error_flag = error_state
    #         self._error_set = set(self.errors)
    #     else:
    #         self.errors = []
    #         self._error_set = set()
    #         self.error_nodes = dict()
    #         self.error_positions = dict()
    #         self.error_flag = 0

    def add_error(self, node: Optional[Node], error: Error) -> 'RootNode':
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
                  code: ErrorCode = ERROR) -> 'RootNode':
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
        # assert dest._pos <= src._pos, "Cannot reduce %i to %s" % (src._pos, dest._pos)
        # dest._pos < 0 or dest._pos < src._pos
        # or dest._pos < src._pos <= dest._pos + len(dest),
        # "%i %i %i" % (src._pos, dest._pos, len(dest))
        if srcId != destId and srcId in self.error_nodes:
            errorList = self.error_nodes[srcId]
            self.error_nodes.setdefault(destId, []).extend(errorList)
            del self.error_nodes[srcId]
            for nodeSet in self.error_positions.values():
                nodeSet.discard(srcId)
                nodeSet.add(destId)
            # for e in errorList:  # does not work for some reason
            #     nodeSet = self.error_positions[e.pos]
            #     nodeSet.discard(srcId)
            #     nodeSet.add(destId)

    @property
    def errors_sorted(self) -> List[Error]:
        """
        Returns the list of errors, ordered bv their position.
        """
        errors = self.errors[:]
        errors.sort(key=lambda e: e.pos)
        return errors

    def error_safe(self, level: int = ERROR) -> 'RootNode':
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

    def as_xml(self, src: str = None,
               indentation: int = 2,
               inline_tags: Set[str] = _EMPTY_SET_SENTINEL,
               string_tags: Set[str] = _EMPTY_SET_SENTINEL,
               empty_tags: Set[str] = _EMPTY_SET_SENTINEL) -> str:
        return super().as_xml(
            src, indentation,
            inline_tags=self.inline_tags if inline_tags is _EMPTY_SET_SENTINEL else inline_tags,
            string_tags=self.string_tags if string_tags is _EMPTY_SET_SENTINEL else string_tags,
            empty_tags=self.empty_tags if empty_tags is _EMPTY_SET_SENTINEL else empty_tags)

    def customized_XML(self):
        """
        DEPRECATED!!!

        Returns a customized XML representation of the tree.
        See the docstring of `Node.as_xml()` for an explanation of the
        customizations.
        """
        import warnings
        warnings.warn('RootNode.customized_XML is deprecated, use RootNode.as_xml() instead!',
                      DeprecationWarning)
        return self.as_xml(inline_tags=self.inline_tags,
                           string_tags=self.string_tags,
                           empty_tags=self.empty_tags)


#######################################################################
#
# S-expression- and XML-parsers and JSON-reader, ElementTree-converter
#
#######################################################################

RX_SXPR_INNER_PARSER = re.compile(r'[\w:]+')
RX_SXPR_NOTEXT = re.compile(r'(?:(?!\)).)*', re.DOTALL)
RX_SXPR_TEXT = {qtmark: re.compile(qtmark + r'.*?' + qtmark, re.DOTALL)
                for qtmark in ['"""', "'''", '"', "'"]}


def parse_sxpr(sxpr: Union[str, StringView]) -> Node:
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
    return tree


RX_WHITESPACE_TAIL = re.compile(r'\s*$')
RX_XML_ATTRIBUTES = re.compile(r'\s*(?P<attr>[\w:_.-]+)\s*=\s*"(?P<value>.*?)"\s*')
RX_XML_SPECIAL_TAG = re.compile(r'<(?![?!])')
RX_XML_OPENING_TAG = re.compile(r'<\s*(?P<tagname>[\w:_.-]+)\s*')
RX_XML_CLOSING_TAG = re.compile(r'</\s*(?P<tagname>[\w:_.-]+)\s*>')
RX_XML_HEADER = re.compile(r'<(?![?!])')


def parse_xml(xml: Union[str, StringView],
              string_tag: str = TOKEN_PTYPE,
              ignore_pos: bool = False,
              out_empty_tags: Set[str] = set(),
              strict_mode: bool = True) -> Node:
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

    def skip_special_tag(s: StringView) -> StringView:
        """Skip special tags, e.g. <?...>, <!...>, and return the string
        view at the position of the next normal tag."""
        assert s[:2] in ('<!', '<?')
        m = s.search(RX_XML_SPECIAL_TAG)
        i = s.index(m.start()) if m else len(s)
        k = s.rfind(">", end=i)
        return s[k+1:] if k >= 0 else s

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
        res = []  # type: List[Node]
        s, tagname, attrs, solitary = parse_opening_tag(s)
        name, class_name = (tagname.split(":") + [''])[:2]
        if solitary:
            out_empty_tags.add(tagname)
        else:
            if tagname in out_empty_tags:
                error_message = f'"{tagname}" is used as empty as well as non-empty element!' \
                                f' This can cause errors when re-serializing data as XML! ' \
                                f'Use parse_xml(..., strict_mode=False) to suppress this error!'
                if strict_mode:  raise ValueError(error_message)
            while s and not s[:2] == "</":
                s, leaf = parse_leaf_content(s)
                if leaf and (leaf.find('\n') < 0 or not leaf.match(RX_WHITESPACE_TAIL)):
                    res.append(Node(string_tag, leaf))
                if s[:1] == "<":
                    if s[:2] in ("<?", "<!"):
                        s = skip_special_tag(s)
                    elif s[:2] != "</":
                        s, child = parse_full_content(s)
                        res.append(child)
            s, closing_tagname = parse_closing_tag(s)
            if tagname != closing_tagname:
                error_message = f'Tag-name mismatch: <{tagname}>...</{closing_tagname}>!' \
                                f'Use parse_xml(..., strict_mode=False) to suppress this error,' \
                                f' but do not expect sound results if you do!'
                if strict_mode:  raise ValueError(error_message)
                else:  print(error_message)
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
    return tree


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


def parse_json(json_str: str) -> Node:
    """
    Parses a JSON-representation of a node-tree. Other than
    and parse_xml, this function does not convert any json-document into
    a node-tree, but only json-documents that represents a node-tree, e.g.
    a json-document that has been produced by `Node.as_json()`!
    """
    json_obj = json.loads(json_str, object_pairs_hook=lambda pairs: OrderedDict(pairs))
    return Node.from_json_obj(json_obj)


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
