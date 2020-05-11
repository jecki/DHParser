# syntaxtree.py - syntax tree classes for DHParser
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
Module ``syntaxtree`` defines the ``Node``-class for syntax trees as well
as an abstract base class for parser-objects. The latter is defined
here, because node-objects refer to parser-objects. All concrete
parser classes are defined in the ``parse`` module.
"""

from collections import OrderedDict
import bisect
import copy
import json
import sys
from typing import Callable, cast, Iterator, Sequence, List, Set, Union, \
    Tuple, Container, Optional, Dict

from DHParser.configuration import SERIALIZATIONS, XML_SERIALIZATION, \
    SXPRESSION_SERIALIZATION, INDENTED_SERIALIZATION, JSON_SERIALIZATION, \
    get_config_value
from DHParser.error import Error, ErrorCode, ERROR, PARSER_STOPPED_BEFORE_END
from DHParser.stringview import StringView  # , real_indices
from DHParser.toolkit import re, cython, linebreaks, line_col

__all__ = ('WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'REGEXP_PTYPE',
           'EMPTY_PTYPE',
           'LEAF_PTYPES',
           'ZOMBIE_TAG',
           'PLACEHOLDER',
           'ResultType',
           'StrictResultType',
           'ChildrenType',
           'CriteriaType',
           'ALL_NODES',
           'LEAF_NODES',
           'BRANCH_NODES',
           'Node',
           'prev_context',
           'next_context',
           'serialize_context',
           'context_sanity_check',
           'FrozenNode',
           'EMPTY_NODE',
           'tree_sanity_check',
           'RootNode',
           'DHParser_JSONEncoder',
           'parse_sxpr',
           'parse_xml',
           'parse_json_syntaxtree',
           'parse_tree',
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
LEAF_PTYPES = {WHITESPACE_PTYPE, TOKEN_PTYPE, REGEXP_PTYPE}

ZOMBIE_TAG = "ZOMBIE__"


#######################################################################
#
# syntaxtree nodes
#
#######################################################################


RX_IS_SXPR = re.compile(r'\s*\(')
RX_IS_XML = re.compile(r'\s*<')
RX_ATTR_NAME = re.compile(r'[\w.:-]')


def flatten_sxpr(sxpr: str, threshold: int = -1) -> str:
    """
    Returns S-expression ``sxpr`` as a one-liner without unnecessary
    whitespace.

    The ``threshold`` value is a maximum number of
    characters allowed in the flattened expression. If this number
    is exceeded the the unflattened S-expression is returned. A
    negative number means that the S-expression will always be
    flattened. Zero or (any postive integer <= 3) essentially means
    that the expression will not be flattened.

    Example:
    >>> flatten_sxpr('(a\\n    (b\\n        c\\n    )\\n)\\n')
    '(a (b c))'
    """
    assert RX_IS_SXPR.match(sxpr)
    if threshold == 0:
        return sxpr
    flat = re.sub(r'\s(?=\))', '', re.sub(r'\s+', ' ', sxpr)).strip()
    if len(flat) > threshold >= 0:
        return sxpr.strip()
    return flat


def flatten_xml(xml: str) -> str:
    """
    Returns an XML-tree as a one liner without unnecessary whitespace,
    i.e. only whitespace within leaf-nodes is preserved.
    A more precise alternative to `flatten_xml` is to use Node.as_xml()
    ans passing a set containing the top level tag to parameter `inline_tags`.
    """
    # works only with regex
    # return re.sub(r'\s+(?=<\w)', '', re.sub(r'(?<=</\w+>)\s+', '', xml))
    assert RX_IS_XML.match(xml)

    def tag_only(m):
        """Return only the tag, drop the whitespace."""
        return m.groupdict()['closing_tag']
    return re.sub(r'\s+(?=<[\w:])', '', re.sub(r'(?P<closing_tag></:?\w+>)\s+', tag_only, xml))


# criteria for finding nodes:
# - node itself (equality)
# - tag_name
# - one of several tag_names
# - a function Node -> bool
CriteriaType = Union['Node', str, Container[str], Callable]
ALL_NODES = lambda nd: True
LEAF_NODES = lambda nd: not nd.children
BRANCH_NODES = lambda nd: nd.children


def create_match_function(criterion: CriteriaType) -> Callable:
    """
    Returns a valid match-function (Node -> bool) for the given criterion.
    Match-functions are used to find an select particular nodes from a
    tree of nodes.
    """
    if isinstance(criterion, Node):
        return lambda nd: nd.equals(criterion)
    elif isinstance(criterion, str):
        return lambda nd: nd.tag_name == criterion
    elif callable(criterion):
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda nd: nd.tag_name in criterion
    raise AssertionError("Criterion %s of type %s does not represent a legal criteria type")


def create_context_match_function(criterion: CriteriaType) -> Callable:
    """
    Returns a valid context-match-function (List[Node] -> bool) for the
    given criterion. Context-match-functions are used to find and select
    particular contexts (lists of ancestors up to and including a particular
    node) from a tree of nodes.
    """
    if isinstance(criterion, Node):
        return lambda ctx: ctx[-1].equals(criterion)
    elif isinstance(criterion, str):
        return lambda ctx: ctx[-1].tag_name == criterion
    elif callable(criterion):
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda ctx: ctx[-1].tag_name in criterion
    raise AssertionError("Criterion %s of type %s does not represent a legal criteria type")


RX_AMP = re.compile(r'&(?!\w+;)')


def clean_anonymous_tag_name(tag_name: str) -> str:
    """Cleans anonymous tag-names for serialization, so that the colon does not
    lead to invalid XML:
    >>> clean_anonymous_tag_name(':Series')
    'ANONYMOUS_Series__'
    """
    if tag_name.startswith(':'):
        return 'ANONYMOUS_%s__' % tag_name[1:]
    return tag_name


class Node:  # (collections.abc.Sized): Base class omitted for cython-compatibility
    """
    Represents a node in the concrete or abstract syntax tree.

    There are three different kinds of nodes:

    1. Branch nodes the have children, but no string content. Other
       than in XML there are no mixed nodes that contain strings as
       well other tags. This constraint simplifies tree-processing
       considerably.

       The conversion to and from XML works by enclosing strings
       in a mixed-content tag with some, freely chosen tag name, and
       dropping the tag name again when serializing to XML. Since
       this is easily done, there is not serious restriction involved
       when not allowing mixed-content nodes. See `Node.as_xml()`
       (parameter `omit_tags`) as `parse_xml`.

    2. Leaf nodes that do not have children but only string content.

    3. The root node which contains further properties that are
       global properties of the parsing tree, such as the error list
       (which cannot be stored locally in the nodes, because nodes
       might be dropped during tree-processsing, but error messages
       should not be forgotten!). Because of that, the root node
       requires a different class (`RootNode`) while leaf-nodes
       as well as branch nodes are both instances of class Node.

    A node always has a tag name (which can be empty, though) and
    a result field, which stores the results of the parsing processs
    and contains either a string or a tuple of child nodes.

    All other properties are either optional or represent different
    views on these two properties. Among these are the 'attr`-field
    that contains a dictionary of xml-attributes, the `children`-filed
    that contains a tuple of child-nodes or an empty tuple if the node
    does not have child nodes, the content-field which contains the string
    content of the node and the `pos`-field which contains the position
    of the node's content in the source code, but may also be left
    uninitialized.

    Examples:
    TODO: Add some examples here!

    Attributes and Properties:
        tag_name (str):  The name of the node, which is either its
            parser's name or, if that is empty, the parser's class name.

            By convention the parser's class name when used as tag name
            is prefixed with a colon ":". A node, the tag name of which
            starts with a colon ":" or the tag name of which is the
            empty string is considered as "anonymous". See
            `Node.anonymous()`-property

        result (str or tuple):  The result of the parser which
            generated this node, which can be either a string or a
            tuple of child nodes.

        children (tuple):  The tuple of child nodes or an empty tuple
            if there are no child nodes. READ ONLY!

        content (str):  Yields the contents of the tree as string. The
            difference to ``str(node)`` is that ``node.content`` does
            not add the error messages to the returned string.

        len (int):  The full length of the node's string result if the
            node is a leaf node or, otherwise, the length of the concatenated
            string result's of its descendants. The figure always represents
            the length before AST-transformation and will never change
            through AST-transformation. READ ONLY!

        pos (int):  the position of the node within the parsed text.

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

        attr (dict): An optional dictionary of XML-attr. This
            dictionary is created lazily upon first usage. The attr
            will only be shown in the XML-Representation, not in the
            S-expression-output.
    """

    __slots__ = '_result', 'children', '_pos', 'tag_name', '_xml_attr'

    def __init__(self, tag_name: str,
                 result: Union[Tuple['Node', ...], 'Node', StringView, str],
                 leafhint: bool = False) -> None:
        """
        Initializes the ``Node``-object with the ``Parser``-Instance
        that generated the node and the parser's result.
        """
        self._pos = -1                   # type: int
        # Assignment to self.result initializes the attr _result and children
        # The following if-clause is merely an optimization, i.e. a fast-path for leaf-Nodes
        if leafhint:
            self._result = result        # type: Union[Tuple['Node', ...], StringView, str]
            self.children = tuple()      # type: Tuple[Node, ...]
        else:
            self._set_result(result)
        self.tag_name = tag_name         # type: str

    def __deepcopy__(self, memo):
        if self.children:
            duplicate = self.__class__(self.tag_name, copy.deepcopy(self.children), False)
        else:
            duplicate = self.__class__(self.tag_name, self.result, True)
        duplicate._pos = self._pos
        if self.has_attr():
            duplicate.attr.update(copy.deepcopy(self._xml_attr))
            # duplicate._xml_attr = copy.deepcopy(self._xml_attr)  # this is not cython compatible
        return duplicate

    def __str__(self):
        return self.content

    def __repr__(self):
        # mpargs = {'name': self.parser.name, 'ptype': self.parser.ptype}
        # name, ptype = (self._tag_name.split(':') + [''])[:2]
        # parg = "MockParser({name}, {ptype})".format(name=name, ptype=ptype)
        rarg = ("'%s'" % str(self)) if not self.children else \
            "(" + ", ".join(child.__repr__() for child in self.children) + ")"
        return "Node('%s', %s)" % (self.tag_name, rarg)

    @property
    def repr(self) -> str:
        """Retrun a full (re-)executable representation of `self` including
        attributes and position value.
        """
        rep = [repr(self)]
        if self.has_attr():
            rep.append('.with_attr(%s)' % repr(dict(self.attr)))
        if self._pos >= 0:
            rep.append('.with_pos(%i)' % self._pos)
        return ''.join(rep)

    def __len__(self):
        return (sum(child.__len__() for child in self.children)
                if self.children else len(self._result))

    def __bool__(self):
        """Returns the bool value of a node, which is always True. The reason
        for this is that a boolean test on a variable that can contain a node
        or None will only yield `False` in case of None.
        """
        return True

    def __hash__(self):
        return hash(self.tag_name)

    def equals(self, other: 'Node', ignore_attr_order: bool = False) -> bool:
        """
        Equality of value: Two nodes are considered as having the same value,
        if their tag name is the same, if their results are equal and
        if their attributes and attribute values are the same and if either
        `ignore_attr_order` is `True` or the attributes also appear in the
        same order.

        Returns True, if the tree originating in node `self` is equal by
        value to the tree originating in node `other`.
        """
        if self.tag_name == other.tag_name and self.compare_attr(other, ignore_attr_order):
            if self.children:
                return (len(self.children) == len(other.children)
                        and all(a.equals(b, ignore_attr_order)
                                for a, b in zip(self.children, other.children)))
            else:
                return self.result == other.result
        return False

    @property
    def anonymous(self) -> bool:
        """Returns True, if the Node is an "anonymous" Node, i.e. a node that
        has not been created by a named parser.

        The tag name of anonymous node is a colon followed by the class name
        of the parser that created the node, i.e. ":Series". It is recommended
        practice to remove (or name) all anonymous nodes during the
        AST-transformation.
        """
        return not self.tag_name or self.tag_name[0] == ':'

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
            self.children = (result,)
            self._result = self.children
        else:
            if isinstance(result, tuple):
                self.children = result
                self._result = result or ''
            else:
                # assert isinstance(result, StringView) \
                #     or isinstance(result, str)
                self.children = tuple()
                self._result = result

    def _init_child_pos(self):
        """Initialize position values of children with potentially
        unassigned positions, i.e. child.pos < 0."""
        children = self.children  # type: Tuple['Node', ...]
        if children:
            offset = self._pos
            prev = children[0]
            if prev._pos < 0:
                prev.with_pos(offset)
            for child in children[1:]:
                if child._pos < 0:
                    offset = offset + prev.__len__()
                    child.with_pos(offset)
                else:
                    offset = child._pos
                prev = child

    @property
    def result(self) -> Union[Tuple['Node', ...], StringView, str]:
        """
        Returns the result from the parser that created the node.
        Error messages are not included in the result. Use `self.content()`
        if the result plus any error messages is needed.
        """
        return self._result

    @result.setter
    def result(self, result: Union[Tuple['Node', ...], 'Node', StringView, str]):
        self._set_result(result)
        # fix position values for children that are added after the parsing process
        if self._pos >= 0:
            self._init_child_pos()

    def _leaf_data(self) -> List[str]:
        """
        Returns string content as list of string fragments
        that are gathered from all child nodes in order.
        """
        if self.children:
            fragments = []
            for child in self.children:
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
        if self.children:
            fragments = []
            for child in self.children:
                fragments.extend(child._leaf_data())
            return ''.join(fragments)
        self._result = str(self._result)
        return self._result
        # unoptimized
        # return "".join(child.content for child in self.children) if self.children \
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
        Initialize position value. Usually, the parser guard
        (`parse.Parser.__call__`) takes care of assigning the
        position in the document to newly created nodes. However,
        when Nodes are created outside the reach of the parser
        guard, their document-position must be assigned manually.
        Position values of the child nodes are assigned recursively, too.
        Returns the node itself for convenience.
        """
        # condition self.pos == pos cannot be assumed when tokens or whitespace
        # are dropped early!
        # assert self._pos < 0 or self.pos == pos, ("pos mismatch %i != %i at Node: %s"
        #                                           % (self._pos, pos, repr(self)))
        if pos != self._pos >= 0:
            raise AssertionError("Position value cannot be reassigned to a different value!")
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
            return attr in self._xml_attr if bool(attr) else bool(self._xml_attr)
        except (AttributeError, TypeError):
            return False

    @property
    def attr(self):
        """
        Returns a dictionary of XML-attr attached to the node.

        Examples:
            >>> node = Node(None, '')
            >>> print('Any attributes present?', node.has_attr())
            Any attributes present? False
            >>> node.attr['id'] = 'identificator'
            >>> node.attr
            OrderedDict([('id', 'identificator')])
            >>> node.attr['id']
            'identificator'
            >>> del node.attr['id']
            >>> node.attr
            OrderedDict()

        NOTE: Use `node.attr_active()` rather than bool(node.attr) to check the
        presence of any attributes. Attribute dictionaries are created lazily
        and node.attr would create a dictionary, even though it may never be
        needed any more.
        """
        try:
            if self._xml_attr is None:          # cython compatibility
                self._xml_attr = OrderedDict()
        except AttributeError:
            self._xml_attr = OrderedDict()
        return self._xml_attr

    @attr.setter
    def attr(self, attr_dict: OrderedDict):
        self._xml_attr = attr_dict

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
        :return: str
        """
        if self.has_attr():
            return self.attr.get(attribute, default)
        return default

    def with_attr(self, *attr_dict, **attributes):
        """
        Adds the attributes which are passed to `with_attr()` either as an
        attribute dictionary or as keyword parameters to the node's attributes
        and returns `self`.

        :param attr_dict:  a dictionary of attribute keys and values
        :param attributes: alternatively, a squences of keyword parameters
        :return: `self`

        Example:
        >>> node = Node('test', '').with_attr(animal = "frog", plant= "tree")
        >>> dict(node.attr)
        {'animal': 'frog', 'plant': 'tree'}
        >>> node.with_attr({'building': 'skyscraper'}).repr
        "Node('test', '').with_attr({'animal': 'frog', 'plant': 'tree', 'building': 'skyscraper'})"
        """
        if attr_dict:
            assert not attributes, "Node.with_attr() can be called either exclusively with " \
                "keyword parameters, or a single non-keyword parameter and no keyword parameters!"
            assert len(attr_dict) == 1, "Node.with_attr() must not be called with more than one " \
                "non-keyword parameter."
            dictionary = attr_dict[0]
            assert isinstance(dictionary, dict), "The non-keyword parameter passed to " \
                "Node.with_attr() must be of type dict, not %s." % str(type(dictionary))
            # assert all(isinstance(a, str) and isinstance(v, str) for a, v in attr_dict.items())
            if dictionary:  # do not update with an empty dictionary
                self.attr.update(dictionary)
        elif attributes:
            # assert all(isinstance(a, str) and isinstance(v, str) for a, v in attributes.items())
            self.attr.update(attributes)
        return self

    def compare_attr(self, other: 'Node', ignore_order: bool = False) -> bool:
        """
        Returns True, if `self` and `other` have the same attributes with the
        same attribute values. If `ignore_order` is False (default), the
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

    def __getitem__(self, key: Union[CriteriaType, int]) -> Union['Node', Sequence['Node']]:
        """
        Returns the child node with the given index if ``key`` is
        an integer or all child-nodes with the given tag name. Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")))')
            >>> flatten_sxpr(tree[0].as_sxpr())
            '(b "X")'
            >>> flatten_sxpr(tree["X"].as_sxpr())
            '(X (c "d"))'

        Args:
            key(str): A criterion (tag name(s), match function, node) or
                an index of the child that shall be returned.
        Returns:
            Node: The node with the given index (always type Node),
                all nodes which have a given tag name (type Node if there
                exists only one or type Tuple[Node] if there are more than
                one).
        Raises:
            KeyError:   if no matching child was found.
            IndexError: if key was an integer index that did not exist
            ValueError: if the __getitem__ has been called on a leaf node.
        """
        if isinstance(key, int):
            return self.children[key]
        else:
            mf = create_match_function(key)
            items = tuple(child for child in self.children if mf(child))
            if items:
                return items if len(items) >= 2 else items[0]
            raise IndexError('index out of range') if isinstance(key, int) \
                else KeyError(str(key))

    def __delitem__(self, key: Union[CriteriaType, int]):
        """
        Removes children from the node.
        :param key:  A criterion (tag name(s), match function, node) or
                an index of the child(ren) that shall be removed.
        """
        if isinstance(key, int):
            if 0 <= key < len(self.children):
                raise IndexError("index %s out of range [0, %i[" % (key, len(self.children)))
            self.result = self.children[:key] + self.children[key + 1:]
        else:
            assert not isinstance(self.result, str)
            mf = create_match_function(key)
            self.result = tuple(child for child in self.children if not mf(child))

    def get(self, key: Union[CriteriaType, int],
            surrogate: Union['Node', Sequence['Node']]) -> Union['Node', Sequence['Node']]:
        """Returns the child node with the given index if ``key``
        is an integer or the first child node with the given tag name. If no
        child with the given index or tag_name exists, the ``surrogate`` is
        returned instead. This mimics the behaviour of Python's dictionary's
        get-method.
        The type of the return value is always the same type as that of the
        surrogate. If the surrogate is a Node, but there are several items
        matching key, then the first of these will be returned.
        """
        try:
            items = self[key]
            if isinstance(surrogate, Sequence):
                return items if isinstance(items, Sequence) else (items,)
            else:
                return items[0] if isinstance(items, Sequence) else items
        except KeyError:
            return surrogate

    def __contains__(self, what: CriteriaType) -> bool:
        """
        Returns true if a child with the given tag name exists.
        Args:
            what: a criterion that describes what (kind of) child node
            shall be looked for among the children of the node. This
            can a node, a tag name or collection of tag names or an
            arbitrary matching function (Node -> bool).
        Returns:
            bool:  True, if at least one child which fulfills the criterion
                exists
        """
        mf = create_match_function(what)
        for child in self.children:
            if mf(child):
                return True
        return False

    @cython.locals(start=cython.int, stop=cython.int, i=cython.int)
    def index(self, what: CriteriaType, start: int = 0, stop: int = sys.maxsize) -> int:
        """
        Returns the first index of the child that fulfills the criterion
        `what`. If the parameters start and stop are given, the search is
        restricted to the children with indices from the half-open interval
        [start:end[. If no such child exists a ValueError is raised.

        :param what: the criterion by which the child is identified, the index
            of which shall be returned.
        :param start: the first index to start searching.
        :param stop: the last index that shall be searched
        :return: the index of the first child with the given tag name.
        :raises: ValueError, if no child matching the criterion `what` was found.
        """
        assert 0 <= start < stop
        mf = create_match_function(what)
        for i, child in enumerate(self.children[start:stop]):
            if mf(child):
                return i + start
        raise ValueError("Node identified by '%s' not among child-nodes." % str(what))

    @cython.locals(i=cython.int)
    def indices(self, what: CriteriaType) -> Tuple[int]:
        """
        Returns the indices of all children that fulfil the criterion `what`.
        """
        mf = create_match_function(what)
        children = self.children
        return tuple(i for i in range(len(children)) if mf(children[i]))

    def select_if(self, match_function: Callable,
                  include_root: bool = False, reverse: bool = False) -> Iterator['Node']:
        """
        Finds nodes in the tree for which `match_function` returns True.
        See see more general function `Node.select()` for a detailed description.

        `select_if` is a generator that yields all nodes for which the
        given `match_function` evaluates to True. The tree is
        traversed pre-order.
        """
        if include_root and match_function(self):
            yield self
        child_iterator = reversed(self.children) if reverse else self.children
        for child in child_iterator:
            if match_function(child):
                yield child
            if child.children:
                yield from child.select_if(match_function, False, reverse)

    def select(self, criterion: CriteriaType,
               include_root: bool = False, reverse: bool = False) -> Iterator['Node']:
        """
        Finds nodes in the tree that fulfill a given criterion. This criterion
        can either be a bool-valued callable a tag_name or a set of tag_names.

        See function `Node.select` for some examples.

        Args:
            criterion: A "criterion" for identifying the nodes to be selected.
                This can either be a tag name (string), a collection of
                tag names or a match function (Node -> bool)
            include_root (bool): If False, only descendant nodes will be
                checked for a match.
            reverse (bool): If True, the tree will be walked in reverse
                order, i.e. last children first.
        Yields:
            Node: All nodes of the tree which fulfill the given criterion

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
        return self.select_if(create_match_function(criterion), include_root, reverse)

    def select_children(self, criterion: CriteriaType, reverse: bool = False) -> Iterator['Node']:
        """Returns an iterator over all direct children of a node that fulfill `criterion`."""
        # if not self.children and self.result:
        #     raise ValueError("Leaf-Node %s does not have any children to iterate over"
        #                      % self.serialize())
        match_function = create_match_function(criterion)
        if reverse:
            for child in reversed(tuple(self.select_children(criterion, False))):
                yield child
        else:
            for child in self.children:
                if match_function(child):
                    yield child

    def pick(self, criterion: CriteriaType,
             include_root: bool = False,
             reverse: bool = False) -> Optional['Node']:
        """
        Picks the first (or last if run in reverse mode) descendant that fulfills
        the given criterion which can be either a match-function or a tag-name or
        a container of tag-names.

        This function is syntactic sugar for
        ``next(node.select(criterion, ...))``. However, rather than
        raising a StopIterationError if no descendant with the given tag-name
        exists, it returns None.
        """
        try:
            return next(self.select(criterion,
                                    include_root=include_root, reverse=reverse))
        except StopIteration:
            return None

    def pick_child(self, criterion: CriteriaType, reverse: bool = False) -> Optional['Node']:
        """
        Picks the first child (or last if run in reverse mode) descendant that fulfills
        the given criterion which can be either a match-function or a tag-name or
        a container of tag-names.

        This function is syntactic sugar for
        ``next(node.select_children(criterion, False))``. However, rather than
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
        Returns the leaf-Node that covers the given `location`, where
        location is the actual position within self.content (not the
        source code position that the pos-attribute represents)
        """
        end = 0
        for nd in self.select_if(lambda nd: not nd.children, include_root=True):
            end = end + len(nd)
            if location < end:
                return nd
        return None

    def find_parent(self, node) -> Optional['Node']:
        """
        Finds and returns the parent of `node` within the tree represented
        by `self`. If the tree does not contain `node`, the value `None`
        is returned.
        """
        for nd in self.select_if(lambda nd: nd.children, include_root=True):
            if node in nd.children:
                return nd
        return None

    # context selection ###

    def select_context_if(self, match_function: Callable,
                          include_root: bool = False,
                          reverse: bool = False,
                          parent_context=[]) -> Iterator[List['Node']]:
        """
        Like `Node.select_if()` but yields the entire context (i.e. list of
        descendants, the last one being the matching node) instead of just
        the matching nodes. NOTE: In contrast to `select_if()`, `match_function`
        receives the complete context as argument, rather than just the last node!
        """
        context = parent_context + [self]
        if include_root and match_function(context):
            yield context
        child_iterator = reversed(self.children) if reverse else self.children
        for child in child_iterator:
            child_context = context + [child]
            if match_function(child_context):
                yield child_context
            if child.children:
                for matched in child.select_context_if(match_function, False, reverse, context):
                    yield matched

    def select_context(self, criterion: CriteriaType,
                       include_root: bool = False,
                       reverse: bool = False) -> Iterator[List['Node']]:
        """
        Like `Node.select()` but yields the entire context (i.e. list of
        descendants, the last one being the matching node) instead of just
        the matching nodes.
        """
        return self.select_context_if(create_context_match_function(criterion),
                                      include_root, reverse)

    def pick_context(self, criterion: CriteriaType,
                     include_root: bool = False,
                     reverse: bool = False) -> Optional[List['Node']]:
        """
        Like `Node.pick()`, only that the entire context (i.e. chain of descendants)
        relative to `self` is returned.
        """
        try:
            return next(self.select_context(criterion,
                                            include_root=include_root, reverse=reverse))
        except StopIteration:
            return None

    @cython.locals(location=cython.int, end=cython.int)
    def locate_context(self, location: int) -> Optional[List['Node']]:
        """
        Like `Node.locate()`,  only that the entire context (i.e. chain of descendants)
        relative to `self` is returned.
        """
        end = 0
        for ctx in self.select_context_if(lambda ctx: not ctx[-1].children, include_root=True):
            end = end + len(ctx[-1])
            if location < end:
                return ctx
        return None

    def _reconstruct_context_recursive(self: 'Node', node: 'Node') -> Optional[List['Node']]:
        """
        Determines the chain of ancestors of a node that leads up to self. Other than
        the public method `reconstuct_context`, this method retruns the chain of ancestors
        in reverse order [node, ... , self] and returns None in case `node` does not exist
        in the tree rooted in self instead of raising a Value Error.
        If `node` equals `self`, `None` will be returned.
        """
        if node in self.children:
            return [node, self]
        for nd in self.children:
            ctx = nd._reconstruct_context_recursive(node)
            if ctx:
                ctx.append(self)
                return ctx
        return None

    def reconstruct_context(self, node: 'Node') -> List['Node']:
        """
        Determines the chain of ancestors of a node that leads up to self.
        :param node: the descendant node, the ancestry of which shall be determined.
        :return: the list of nodes starting with self and leading to `node`
        :raises: ValueError in case `node` does not occur in the tree rooted in `self`
        """
        if node == self:
            return [node]
        ctx = self._reconstruct_context_recursive(node)
        if ctx is None:
            raise ValueError('Node "%s" does not occur in the tree %s '
                             % (node.tag_name, flatten_sxpr(self.as_sxpr())))
        ctx.reverse()
        return ctx


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
            children = parent.children
            for i in range(len(children)):
                if nd == children[i]:
                    return i

        def left_cut(result: Tuple['Node'], index: int, subst: 'Node') -> Tuple['Node', ...]:
            return (subst,) + result[index + 1:]

        def right_cut(result: Tuple['Node'], index: int, subst: 'Node') -> Tuple['Node', ...]:
            return result[:index] + (subst,)

        def cut(ctx: List['Node'], cut_func: Callable) -> 'Node':
            child = ctx[-1]
            tainted = False
            for i in range(len(ctx) - 1, 0, -1):
                parent = ctx[i - 1]
                k = index(parent, ctx[i])
                segment = cut_func(parent.result, k, child)
                if tainted or len(segment) != len(parent.result):
                    parent_copy = Node(parent.tag_name, segment)
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
        ctxA = self.reconstruct_context(begin)
        ctxB = self.reconstruct_context(end)
        for a, b in zip(ctxA, ctxB):
            if a != b:
                break
            common_ancestor = a
        left = cut(ctxA[ctxA.index(common_ancestor):], left_cut)
        right = cut(ctxB[ctxB.index(common_ancestor):], right_cut)
        left_children = left.children
        right_children = right.children
        if left_children == right_children:
            return common_ancestor
        i = 1
        k = len(right_children)
        try:
            k = right_children.index(left_children[1]) - 1
            i = 2
            while left_children[i] == right_children[k + i]:
                i += 1
        except (IndexError, ValueError):
            pass
        new_ca = Node(common_ancestor.tag_name, left_children[:i] + right_children[k + i:])
        if common_ancestor.has_attr():
            new_ca.attr = common_ancestor.attr
        return new_ca

    # serialization ###########################################################

    @cython.locals(i=cython.int, k=cython.int, N=cython.int)
    def _tree_repr(self, tab, open_fn, close_fn, data_fn=lambda i: i,
                   density=0, inline=False, inline_fn=lambda node: False,
                   allow_ommissions=False) -> str:
        """
        Generates a tree representation of this node and its children
        in string from.

        The kind ot tree-representation that is determined by several
        function parameters. This could be an XML-representation or a
        lisp-like S-expression.

        Args:
            tab (str):  The indentation string, e.g. '\t' or '    '
            open_fn:   (Node->str) A function that returns an opening
                string (e.g. an XML-tag_name) for a given node
            close_fn:  (Node->str) A function that returns a closeF
                string (e.g. an XML-tag_name) for a given node.
            data_fn:   (str->str) A function that filters the data string
                before printing, e.g. to add quotation marks

        Returns (str):
            A string that contains a (serialized) tree representation
            of the node and its children.
        """
        head = open_fn(self)
        tail = close_fn(self)

        if not self.result:
            return head.rstrip() + tail.lstrip()

        tail = tail.lstrip(None if density & 2 else '')

        inline = inline or inline_fn(self)
        if inline:
            head = head.rstrip()
            tail = tail.lstrip()
            usetab, sep = '', ''
        else:
            usetab = tab if head else ''    # no indentation if tag is already omitted
            sep = '\n'

        if self.children:
            content = []
            for child in self.children:
                subtree = child._tree_repr(tab, open_fn, close_fn, data_fn,
                                           density, inline, inline_fn)
                if subtree:
                    st = [subtree] if inline else subtree.split('\n')
                    content.append((sep + usetab).join(s for s in st))
            return head + usetab + (sep + usetab).join(content) + tail

        res = self.content
        if not inline and not head and allow_ommissions:
            # strip whitespace for omitted non inline node, e.g. CharData in mixed elements
            res = res.strip()  # WARNING: This changes the data in subtle ways
        if density & 1 and res.find('\n') < 0:
            # except for XML, add a gap between opening statement and content
            gap = ' ' if not inline and head and head.rstrip()[-1:] != '>' else ''
            return head.rstrip() + gap + data_fn(res) + tail.lstrip()
        else:
            lines = [data_fn(s) for s in res.split('\n')]
            N = len(lines)
            i, k = 0, N - 1
            if not inline and allow_ommissions:
                # Strip preceding and succeding whitespace.
                # WARNING: This changes the data in subtle ways
                while i < N and not lines[i]:
                    i += 1
                while k >= 0 and not lines[k]:
                    k -= 1
            lines = [usetab + l for l in lines[i:k + 1]]
            return head + '\n'.join(lines) + tail

    def as_sxpr(self, src: Optional[str] = None,
                indentation: int = 2,
                compact: bool = False,
                flatten_threshold: int = 92) -> str:
        """
        Returns content as S-expression, i.e. in lisp-like form. If this
        method is called on a RootNode-object,

        Args:
            src:  The source text or `None`. In case the source text is
                given the position of the element in the text will be
                reported as position, line, column. In case the empty string is
                given rather than None, only the position value will be
                reported in case it has been initialized, i.e. pos >= 0.
            indentation: The number of whitespaces for indentation
            compact:  If True, a compact representation is returned where
                brackets are omitted and only the indentation indicates the
                tree structure.
            flatten_threshold:  Return the S-expression in flattened form if
                the flattened expression does not exceed the threshold length.
                A negative number means that it will always be flattened.
        """
        left_bracket, right_bracket, density = ('(', ')', 1) if compact else ('(', '\n)', 0)
        lbreaks = linebreaks(src) if src else []  # type: List[int]
        root = cast(RootNode, self) if isinstance(self, RootNode) \
            else None  # type: Optional[RootNode]

        def opening(node: Node) -> str:
            """Returns the opening string for the representation of `node`."""
            txt = [left_bracket, node.tag_name]
            # s += " '(pos %i)" % node.add_pos
            # txt.append(str(id(node)))  # for debugging
            if node.has_attr():
                txt.extend(' `(%s "%s")' % (k, v) for k, v in node.attr.items())
            if src:
                line, col = line_col(lbreaks, node.pos)
                txt.append(' `(pos %i %i %i)' % (node.pos, line, col))
            elif src is not None and node._pos >= 0:
                txt.append(' `(pos %i)' % node.pos)
            # if node.tag_name == ZOMBIE_TAG:
            #     print(node.pos, id(node), id(node) in root.error_nodes, root.get_errors(node))
            if root and id(node) in root.error_nodes and not node.has_attr('err'):
                txt.append(" `(%s)" % ';  '.join(str(err) for err in root.get_errors(node)))
            return "".join(txt) + '\n'

        def closing(node: Node) -> str:
            """Returns the closing string for the representation of `node`."""
            return right_bracket

        def pretty(strg: str) -> str:
            """Encloses `strg` with the right kind of quotation marks."""
            return '"%s"' % strg if strg.find('"') < 0 \
                else "'%s'" % strg if strg.find("'") < 0 \
                else '"%s"' % strg.replace('"', r'\"')

        sxpr = self._tree_repr(' ' * indentation, opening, closing, pretty, density=density)
        return sxpr if compact else flatten_sxpr(sxpr, flatten_threshold)

    def as_xml(self, src: str = None,
               indentation: int = 2,
               inline_tags: Set[str] = set(),
               omit_tags: Set[str] = set(),
               empty_tags: Set[str] = set()) -> str:
        """Returns content as XML-tree.

        :param src: The source text or `None`. In case the source text is given,
                the position will also be reported as line and column.
        :param indentation: The number of whitespaces for indentation
        :param inline_tags:  A set of tag names, the content of which will always be written
                on a single line, unless it contains explicit line feeds ('\n').
        :param omit_tags: A set of tags from which only the content will be printed, but
                neither the opening tag nor its attr nor the closing tag. This
                allows producing a mix of plain text and child tags in the output,
                which otherwise is not supported by the Node object, because it
                requires its content to be either a tuple of children or string content.
        :param empty_tags: A set of tags which shall be rendered as empty elements, e.g.
                "<empty/>" instead of "<empty><empty>".
        :return: The XML-string representing the tree originating in `self`
        """
        root = cast(RootNode, self) if isinstance(self, RootNode) \
            else None  # type: Optional[RootNode]

        def opening(node: Node) -> str:
            """Returns the opening string for the representation of `node`."""
            if node.tag_name in omit_tags and not node.has_attr():
                return ''
            txt = ['<', clean_anonymous_tag_name(node.tag_name)]
            if node.has_attr():
                txt.extend(' %s="%s"' % (k, v) for k, v in node.attr.items())
            if src and not (node.has_attr('line') or node.has_attr('col')):
                txt.append(' line="%i" col="%i"' % line_col(line_breaks, node._pos))
            if src == '' and not (node.has_attr() and '_pos' in node.attr) and node._pos >= 0:
                txt.append(' _pos="%i"' % node._pos)
            if root and id(node) in root.error_nodes and not node.has_attr('err'):
                txt.append(' err="%s"' % ''.join(str(err).replace('"', "'")
                                                 for err in root.get_errors(node)))
            if node.tag_name in empty_tags:
                assert not node.result, ("Node %s with content %s is not an empty element!" %
                                         (node.tag_name, str(node)))
                ending = "/>\n" if not node.tag_name[0] == '?' else "?>\n"
            else:
                ending = ">\n"
            return "".join(txt + [ending])

        def closing(node: Node):
            """Returns the closing string for the representation of `node`."""
            if node.tag_name in empty_tags or (node.tag_name in omit_tags and not node.has_attr()):
                return ''
            return '\n</' + clean_anonymous_tag_name(node.tag_name) + '>'

        def sanitizer(content: str) -> str:
            """Substitute "&", "<", ">" in XML-content by the respective entities."""
            content = RX_AMP.sub('&amp;', content)
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            return content

        def inlining(node: Node):
            """Returns True, if `node`'s tag name is contained in `inline_tags`,
            thereby signalling that the children of this node shall not be
            printed on several lines to avoid unwanted gaps in the output.
            """
            return node.tag_name in inline_tags \
                or (node.has_attr()
                    and node.attr.get('xml:space', 'default') == 'preserve')

        line_breaks = linebreaks(src) if src else []
        return self._tree_repr(' ' * indentation, opening, closing, sanitizer,
                               density=1, inline_fn=inlining, allow_ommissions=bool(omit_tags))

    # JSON serialization ###

    def to_json_obj(self) -> List:
        """Serialize node or tree as JSON-serializable nested list."""
        jo = [self.tag_name,
              [nd.to_json_obj() for nd in self.children] if self.children else str(self.result)]
        pos = self.pos
        if pos >= 0:
            jo.append(pos)
        if self.has_attr():
            jo.append(self.attr)
        return jo

    @staticmethod
    def from_json_obj(json_obj: Union[Dict, Sequence]) -> 'Node':
        """Convert a JSON-object representing a node (or tree) back into a
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
        return json.dumps(self.to_json_obj(), indent=indent, ensure_ascii=ensure_ascii,
                          separators=(', ', ': ') if indent is not None else (',', ':'))

    # serialization meta-method ###

    @cython.locals(vsize=cython.int, i=cython.int, threshold=cython.int)
    def serialize(self: 'Node', how: str = 'default') -> str:
        """
        Serializes the tree starting with `node` either as S-expression, XML, JSON,
        or in compact form. Possible values for `how` are 'S-expression', 'XML',
        'JSON', 'compact' and 'smart' accordingly, or 'AST', 'CST', 'default' in
        which case the value of respective configuration variable determines the
        serialization format. (See module `configuration.py`.)
        """
        def exceeds_compact_threshold(node: Node, threshold: int) -> bool:
            """Returns True, if the S-expression-serialization of the tree
            rooted in `node` would exceed a certain number of lines and
            should therefore be rendered in a more compact form.
            """
            vsize = 0
            for nd in node.select_if(lambda _: True, include_root=True):
                if nd.children:
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

        flatten_threshold = get_config_value('flatten_sxpr_threshold')
        compact_threshold = get_config_value('compact_sxpr_threshold')

        if switch == SXPRESSION_SERIALIZATION.lower():
            return self.as_sxpr(flatten_threshold=get_config_value('flatten_sxpr_threshold'),
                                compact=exceeds_compact_threshold(self, compact_threshold))
        elif switch == XML_SERIALIZATION.lower():
            return self.as_xml()
        elif switch == JSON_SERIALIZATION.lower():
            return self.as_json()
        elif switch == INDENTED_SERIALIZATION.lower():
            sxpr = self.as_sxpr(flatten_threshold=0)
            if sxpr.find('\n') >= 0:
                sxpr = re.sub(r'\n(\s*)\(', r'\n\1', sxpr)
                sxpr = re.sub(r'\n\s*\)(?!")', r'', sxpr)
                # sxpr = re.sub(r'(?<=\n[^`]*)\)[ \t]*\n', r'\n', sxpr)
                s = sxpr.split('\n')
                for i in range(len(s)):
                    if '`' in s[i]:
                        s[i] = s[i].replace('))', ')')
                    elif s[i][-1:] != '"':
                        s[i] = s[i].replace(')', '')
                sxpr = '\n'.join(s)
                sxpr = re.sub(r'^\(', r'', sxpr)
            return sxpr
        else:
            s = how if how == switch else (how + '/' + switch)
            raise ValueError('Unknown serialization "%s". Allowed values are either: %s or : %s'
                             % (s, "ast, cst, default", ", ".join(list(SERIALIZATIONS))))


# Navigate contexts ###################################################


@cython.locals(i=cython.int, k=cython.int)
def prev_context(context: List[Node]) -> Optional[List[Node]]:
    """Returns the context of the predecessor of the last Node in the
    context. The predecessor is the sibling of the same parent Node
    preceding the node, or if it already is the first sibling, the parent's
    sibling preceeding the parent, or grand-parente's sibling and so on.
    In case no predecessor is found when the first ancestor has been
    reached, None is returned.
    """
    assert isinstance(context, list)
    node = context[-1]
    for i in range(len(context) - 2, -1, -1):
        siblings = context[i].children
        if node is not siblings[0]:
            for k in range(1, len(siblings)):
                if node is siblings[k]:
                    return context[:i + 1] + [siblings[k - 1]]
            raise AssertionError('Structural Error: context[%i] is not the parent of context[%i]'
                                 % (i, i+1))
        node = context[i]
    return None


@cython.locals(i=cython.int, k=cython.int)
def next_context(context: List[Node]) -> Optional[List[Node]]:
    """Returns the contexnt of the successor of the last Node in the
    context. The successor is the sibling of the same parent Node
    succeeding the the node, or if it already is the last sibling, the
    parent's sibling succeeding the parent, or grand-parente's sibling and
    so on. In case no successor is found when the first ancestor has been
    reached, None is returned.
    """
    assert isinstance(context, list)
    node = context[-1]
    for i in range(len(context) - 2, -1, -1):
        siblings = context[i].children
        if node is not siblings[-1]:
            for k in range(len(siblings) - 2, -1, -1):
                if node is siblings[k]:
                    return context[:i + 1] + [siblings[k + 1]]
            raise AssertionError('Structural Error: context[%i] is not the parent of context[%i]'
                                 % (i, i+1))
        node = context[i]
    return None


def serialize_context(context: List[Node], with_content: bool = False, delimiter: str = ' <- '):
    l = [nd.tag_name + ((':' + nd.content) if with_content else '') for nd in context]
    return delimiter.join(l)


def context_sanity_check(context: List[Node]) -> bool:
    return all(context[i] in context[i - 1].children for i in range(1, len(context)))



# FrozenNode ##########################################################


ChildrenType = Tuple[Node, ...]
StrictResultType = Union[ChildrenType, StringView, str]
ResultType = Union[ChildrenType, Node, StringView, str]


class FrozenNode(Node):
    """
    FrozenNode is an immutable kind of Node, i.e. it must not be changed
    after initialization. The purpose is mainly to allow certain kinds of
    optimization, like not having to instantiate empty nodes (because they
    are always the same and will be dropped while parsing, anyway) or,
    rather, throw errors if the program tries to treat a node that is
    supposed to be a temporary (frozen) node as if it was a regular node.

    Frozen nodes must only be used temporarily during parsing or
    tree-transformation and should not occur in the product of the
    transformation any more. This can be verified with `tree_sanity_check()`.
    """

    def __init__(self, tag_name: str, result: ResultType, leafhint: bool = True) -> None:
        if isinstance(result, str) or isinstance(result, StringView):
            result = str(result)
        else:
            raise TypeError('FrozenNode only accepts string as result. '
                            '(Only leaf-nodes can be frozen nodes.)')
        super(FrozenNode, self).__init__(tag_name, result, True)

    @property
    def result(self) -> Union[Tuple[Node, ...], StringView, str]:
        return self._result

    @result.setter
    def result(self, result: ResultType):
        raise TypeError('FrozenNode does not allow re-assignment of results.')

    @property
    def attr(self):
        raise NotImplementedError("Attributes cannot be accessed on a frozen node")

    @attr.setter
    def attr(self, attr_dict: OrderedDict):
        raise NotImplementedError("Frozen nodes cannot store attributes")

    def with_pos(self, pos: int) -> 'Node':
        raise NotImplementedError("Position values cannot be assigned to frozen nodes!")

    def to_json_obj(self) -> List:
        raise NotImplementedError("Frozen nodes cannot and should not be serialized!")

    @staticmethod
    def from_json_obj(json_obj: Union[Dict, Sequence]) -> 'Node':
        raise NotImplementedError("Frozen nodes cannot and should not be deserialized!")


PLACEHOLDER = FrozenNode('__PLACEHOLDER__', '')
EMPTY_NODE = FrozenNode(EMPTY_PTYPE, '')


def tree_sanity_check(tree: Node) -> bool:
    """
    Sanity check for syntax trees: One and the same node must never appear
    twice in the syntax tree. Frozen Nodes (EMTPY_NODE, PLACEHOLDER)
    should only exist temporarily and must have been dropped or eliminated
    before any kind of tree generation (i.e. parsing) or transformation
    is finished.
    :param tree: the root of the tree to be checked
    :return: True, if the tree is `sane`, False otherwise.
    """
    node_set = set()  # type: Set[Node]
    for node in tree.select_if(lambda nd: True, include_root=True):
        if node in node_set or isinstance(Node, FrozenNode):
            return False
        node_set.add(node)
    return True


# Tree of nodes #######################################################


class RootNode(Node):
    """The root node for the syntax tree is a special kind of node that keeps
    and manages global properties of the tree as a whole. These are first and
    foremost the list off errors that occurred during tree generation
    (i.e. parsing) or any transformation of the tree. Other properties concern
    the customization of the XML-serialization.

    The root node can be instantiated before the tree is fully parsed. This is
    necessary, because the root node is needed for managing error messages
    during the parsing process, already. In order to connect the root node to
    the tree, when parsing is finished, the swallow()-method must be called.

        errors (list):  A list of all errors that have occurred so far during
                processing (i.e. parsing, AST-transformation, compiling)
                of this tree.

        error_nodes (dict): A mapping of node-ids to a list of errors that
                occurred on the node with the respective id.

        error_positions (dict): A mapping of locations to a set of ids of
                nodes that contain an error at that particular location

        error_flag (int):  the highest warning or error level of all errors
                that occurred.

        inline_tags (set of strings): see `Node.as_xml()` for an explanation.

        omit_tags (set of strings): see `Node.as_xml()` for an explanation.

        empty_tags (set oif strings): see `Node.as_xml()` for an explanation.
    """

    def __init__(self, node: Optional[Node] = None):
        super().__init__('__not_yet_ready__', '')
        self.errors = []               # type: List[Error]
        self.error_nodes = dict()      # type: Dict[int, List[Error]]  # id(node) -> error list
        self.error_positions = dict()  # type: Dict[int, Set[int]]  # pos -> set of id(node)
        self.error_flag = 0
        if node is not None:
            self.swallow(node)
        # customization for XML-Representation
        self.inline_tags = set()  # type: Set[str]
        self.omit_tags = set()    # type: Set[str]
        self.empty_tags = set()   # type: Set[str]

    def clear_errors(self):
        """
        DEPRECATED: Should not be ued any more!
        Removes all error messages. This can be used to keep the error messages
        of different subsequent phases of tree-processing separate.
        """
        raise NotImplementedError
        # self.errors = []               # type: List[Error]
        # self.error_nodes = dict()      # type: Dict[int, List[Error]]  # id(node) -> error list
        # self.error_positions = dict()  # type: Dict[int, Set[int]]  # pos -> set of id(node)
        # self.error_flag = 0

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
        if self.children:
            duplicate.children = copy.deepcopy(self.children)
            duplicate._result = duplicate.children
        else:
            duplicate.children = tuple()
            duplicate._result = self._result
        duplicate._pos = self._pos
        new_node_ids = [id(nd) for nd in duplicate.select_if(lambda n: True, include_root=True)]
        map_id = dict(zip(old_node_ids, new_node_ids))
        if self.has_attr():
            duplicate.attr.update(copy.deepcopy(self._xml_attr))
            # duplicate._xml_attr = copy.deepcopy(self._xml_attr)  # this is blocked by cython
        duplicate.errors = copy.copy(self.errors)
        duplicate.error_nodes = {map_id.get(i, i): el[:] for i, el in self.error_nodes.items()}
        duplicate.error_positions = {pos: {map_id.get(i, i) for i in s}
                                     for pos, s in self.error_positions.items()}
        duplicate.error_flag = self.error_flag
        duplicate.inline_tags = self.inline_tags
        duplicate.omit_tags = self.omit_tags
        duplicate.empty_tags = self.empty_tags
        duplicate.tag_name = self.tag_name
        return duplicate

    def swallow(self, node: Optional[Node]) -> 'RootNode':
        """
        Put `self` in the place of `node` by copying all its data.
        Returns self.

        This is done by the parse.Grammar object after
        parsing has finished, so that the Grammar object always
        returns a syntax tree rooted in a RootNode object.

        It is possible to add errors to a RootNode object, before it
        has actually swallowed the root of the syntax tree.
        """
        if self.tag_name != '__not_yet_ready__':
            raise AssertionError('RootNode.swallow() has already been called!')
        if node is None:
            self.tag_name = ZOMBIE_TAG
            self.with_pos(0)
            self.new_error(self, 'Parser did not match!', PARSER_STOPPED_BEFORE_END)
            return self
        self._result = node._result
        self.children = node.children
        self._pos = node._pos
        self.tag_name = node.tag_name
        if node.has_attr():
            self._xml_attr = node._xml_attr
        # self._content = node._content
        if id(node) in self.error_nodes:
            self.error_nodes[id(self)] = self.error_nodes[id(node)]
        return self

    def add_error(self, node: Optional[Node], error: Error) -> 'RootNode':
        """
        Adds an Error object to the tree, locating it at a specific node.
        """
        if not node:
            # find the first leaf-node from the left that could contain the error
            # judging from its position
            pos_list =[]
            node_list = []
            for nd in self.select_if(lambda nd: not nd.children):
                if nd.pos <= error.pos < nd.pos + len(nd):
                    node = nd
                    break
                pos_list.append(nd.pos)
                node_list.append(nd)
            else:
                node_list.append(nd)
                i = bisect.bisect(pos_list, error.pos)
                node = node_list[i]
        else:
            assert isinstance(node, Node)
            assert isinstance(node, FrozenNode) or node.pos <= error.pos, \
                "%i <= %i <= %i ?" % (node.pos, error.pos, node.pos + max(1, len(node) - 1))
            # assert node.pos == error.pos or isinstance(node, FrozenNode)
        self.error_nodes.setdefault(id(node), []).append(error)
        if node.pos == error.pos:
            self.error_positions.setdefault(error.pos, set()).add(id(node))
        self.errors.append(error)
        self.error_flag = max(self.error_flag, error.code)
        return self

    def new_error(self,
                  node: Node,
                  message: str,
                  code: ErrorCode = ERROR) -> 'RootNode':
        """
        Adds an error to this tree, locating it at a specific node.
        Parameters:
            node(Node):   The node where the error occurred
            message(str): A string with the error message.abs
            code(int):    An error code to identify the kind of error
        """
        error = Error(message, node.pos, code)
        self.add_error(node, error)
        return self

    def get_errors(self, node: Node) -> List[Error]:
        """
        Returns the List of errors that occurred on the node or any child node
        at the position of the node that has already been removed from the tree,
        for example, because it was an anonymous empty child node.
        The position of the node is here understood to cover then range:
        [node.pos, node.pos + len(node)[
        """
        node_id = id(node)           # type: int
        errors = []                  # type: List[Error]
        start_pos = node.pos
        end_pos = node.pos + max(len(node), 1)
        error_node_ids = set()
        for pos in self.error_positions.keys():   # TODO: use bisect here...
            if start_pos <= pos < end_pos:
                error_node_ids.update(self.error_positions[pos])
        for nid in error_node_ids:
            if nid == node_id:
                # add the node's errors
                errors.extend(self.error_nodes[nid])
            elif node.children:
                for _ in node.select_if(lambda n: id(n) == nid):
                    break
                else:
                    # node is not connected to tree any more, but since errors
                    # should not get lost, display its errors on its parent
                    errors.extend(self.error_nodes[nid])
        return errors

    @property
    def errors_sorted(self) -> List[Error]:
        """
        Returns the list of errors, ordered bv their position.
        """
        self.errors.sort(key=lambda e: e.pos)
        return self.errors

    def did_match(self) -> bool:
        """Returns True, if the parser that has generated this tree did
        match, False otherwise. Depending on wether the Grammar-object that
        that generated the syntax tree was called with `complete_match=True`
        or not this requires either the complete document to have been
        matched or only the beginning.

        Note: That if the parser did match, this does not mean that it must
        have matched without errors. It simply means the no
        PARSER_STOPPED_BEFORE_END-error has occurred."""
        return self.tag_name != '__not_yet_ready__' \
            and not any(e.code == PARSER_STOPPED_BEFORE_END for e in self.errors)

    def customized_XML(self):
        """
        Returns a customized XML representation of the tree.
        See the docstring of `Node.as_xml()` for an explanation of the
        customizations.
        """
        return self.as_xml(inline_tags=self.inline_tags,
                           omit_tags=self.omit_tags,
                           empty_tags=self.empty_tags)


#######################################################################
#
# S-expression- and XML-parsers and JSON-reader
#
#######################################################################


def parse_sxpr(sxpr: Union[str, StringView]) -> Node:
    """
    Generates a tree of nodes from an S-expression.

    This can - among other things - be used for deserialization of trees that
    have been serialized with `Node.as_sxpr()` or as a convenient way to
    generate test data.

    Example:
    >>> parse_sxpr("(a (b c))").as_sxpr(flatten_threshold=0)
    '(a\\n  (b\\n    "c"\\n  )\\n)'

    `parse_sxpr()` does not initialize the node's `pos`-values. This can be
    done with `Node.with_pos()`:

    >>> tree = parse_sxpr('(A (B "x") (C "y"))').with_pos(0)
    >>> tree['C'].pos
    1
    """
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
            raise AssertionError(errmsg)

    @cython.locals(pos=cython.int, i=cython.int, k=cython.int, end=cython.int)
    def inner_parser(sxpr: StringView) -> Node:
        if sxpr[0] != '(':
            raise ValueError('"(" expected, not ' + sxpr[:10])
        # assert sxpr[0] == '(', sxpr
        sxpr = sxpr[1:].strip()
        match = sxpr.match(re.compile(r'[\w:]+'))
        if match is None:
            raise AssertionError('Malformed S-expression Node-tagname or identifier expected, '
                                 'not "%s"' % sxpr[:40].replace('\n', ''))
        end = sxpr.index(match.end())
        tagname = sxpr[:end]
        name, class_name = (tagname.split(':') + [''])[:2]
        sxpr = sxpr[end:].strip()
        attributes = OrderedDict()  # type: OrderedDict[str, str]
        pos = -1  # type: int
        # parse attr
        while sxpr[:2] == "`(":
            i = sxpr.find('"')
            k = sxpr.find(')')
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
                    match = sxpr.match(re.compile(qtmark + r'.*?' + qtmark, re.DOTALL))
                    if match:
                        end = sxpr.index(match.end())
                        i = len(qtmark)
                        lines.append(str(sxpr[i:end - i]))
                        sxpr = sxpr[end:].strip()
                        break
                else:
                    match = sxpr.match(re.compile(r'(?:(?!\)).)*', re.DOTALL))
                    end = sxpr.index(match.end())
                    lines.append(str(sxpr[:end]))
                    sxpr = sxpr[end:]
            result = "\n".join(lines)  # # type: Union[Tuple[Node, ...], str]
        node = Node(str(name or ':' + class_name), result)
        node._pos = pos
        if attributes:
            node.attr.update(attributes)
        return node

    xpr = StringView(sxpr).strip() if isinstance(sxpr, str) else sxpr.strip()  # type: StringView
    return inner_parser(xpr)


RX_WHITESPACE_TAIL = re.compile(r'\s*$')


def parse_xml(xml: Union[str, StringView], ignore_pos: bool = False) -> Node:
    """
    Generates a tree of nodes from a (Pseudo-)XML-source.

    If the flag `ignore_pos` is True, '_pos'-attributes will be understood as
    normal XML-attributes. Otherwise '_pos' will be understood as special
    attribute, i.e. its value will be written to `node._pos` and not
    transferred to the `node.attr`-dictionary.
    """

    xml = StringView(str(xml))
    # PlainText = MockParser('', TOKEN_PTYPE)
    # mock_parsers = {TOKEN_PTYPE: PlainText}

    def parse_attributes(s: StringView) -> Tuple[StringView, OrderedDict]:
        """
        Parses a sqeuence of XML-Attributes. Returns the string-slice
        beginning after the end of the attr.
        """
        attributes = OrderedDict()  # type: OrderedDict[str, str]
        eot = s.find('>')
        restart = 0
        for match in s.finditer(re.compile(r'\s*(?P<attr>\w+)\s*=\s*"(?P<value>.*?)"\s*')):
            if s.index(match.start()) >= eot:
                break
            d = match.groupdict()
            attributes[d['attr']] = d['value']
            restart = s.index(match.end())
        return s[restart:], attributes

    def parse_opening_tag(s: StringView) -> Tuple[StringView, str, OrderedDict, bool]:
        """
        Parses an opening tag. Returns the string segment following the
        the opening tag, the tag name, a dictionary of attr and
        a flag indicating whether the tag is actually a solitary tag as
        indicated by a slash at the end, i.e. <br/>.
        """
        match = s.match(re.compile(r'<\s*(?P<tagname>[\w:]+)\s*'))
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
        match = s.match(re.compile(r'</\s*(?P<tagname>[\w:]+)>'))
        assert match
        tagname = match.groupdict()['tagname']
        return s[s.index(match.end()):], tagname

    def parse_leaf_content(s: StringView) -> Tuple[StringView, StringView]:
        """
        Parses a piece of the content of a tag, just until the next opening,
        closing or solitary tag is reached.
        """
        i = 0
        while s[i] != "<" or s[max(0, i - 1)] == "\\":
            i = s.find("<", i)
        return s[i:], s[:i]

    def parse_full_content(s: StringView) -> Tuple[StringView, Node]:
        """
        Parses the full content of a tag, starting right at the beginning
        of the opening tag and ending right after the closing tag.
        """
        res = []  # type: List[Node]
        s, tagname, attrs, solitary = parse_opening_tag(s)
        name, class_name = (tagname.split(":") + [''])[:2]
        if not solitary:
            while s and not s[:2] == "</":
                s, leaf = parse_leaf_content(s)
                if leaf and (leaf.find('\n') < 0 or not leaf.match(RX_WHITESPACE_TAIL)):
                    res.append(Node(TOKEN_PTYPE, leaf))
                if s[:1] == "<" and s[:2] != "</":
                    s, child = parse_full_content(s)
                    res.append(child)
            s, closing_tagname = parse_closing_tag(s)
            assert tagname == closing_tagname, tagname + ' != ' + closing_tagname
        if len(res) == 1 and res[0].tag_name == TOKEN_PTYPE:
            result = res[0].result  # type: Union[Tuple[Node, ...], StringView, str]
        else:
            result = tuple(res)

        node = Node(name or ':' + class_name, result)
        if not ignore_pos and '_pos' in attrs:
            node._pos = int(attrs['_pos'])
            del attrs['_pos']
        if attrs:
            node.attr.update(attrs)
        return s, node

    match_header = xml.search(re.compile(r'<(?!\?)'))
    start = xml.index(match_header.start()) if match_header else 0
    _, tree = parse_full_content(xml[start:])
    assert _.match(RX_WHITESPACE_TAIL), _
    return tree


class DHParser_JSONEncoder(json.JSONEncoder):
    """A JSON-encoder that also encodes syntaxtree.Node- and error.Error-objects
    as valid json objects. Error-objects are encoded as strings. Node-objects
    are encoded using Node.as_json.
    """
    def default(self, obj):
        if isinstance(obj, Node):
            return cast(Node, obj).to_json_obj()
        elif isinstance(obj, Error):
            return str(cast(Error, obj))
        return json.JSONEncoder.default(self, obj)


def parse_json_syntaxtree(json_str: str) -> Node:
    """
    Parses a JSON-representation of a syntax tree. Other than parse_sxpr
    and parse_xml, this function does not convert any json-text into
    a syntax tree, but only json-text that represents a syntax tree, e.g.
    that has been produced by `Node.as_json()`!
    """
    json_obj = json.loads(json_str, object_pairs_hook=lambda pairs: OrderedDict(pairs))
    return Node.from_json_obj(json_obj)


def parse_tree(xml_sxpr_json: str) -> Optional[Node]:
    """
    Parses either XML or S-expressions or a JSON representation of a
    syntax-tree. Which of these is detected automatically.
    """
    if RX_IS_XML.match(xml_sxpr_json):
        return parse_xml(xml_sxpr_json)
    elif RX_IS_SXPR.match(xml_sxpr_json):
        return parse_sxpr(xml_sxpr_json)
    elif re.match(r'\s*', xml_sxpr_json):
        return None
    else:
        try:
            return parse_json_syntaxtree(xml_sxpr_json)
        except json.decoder.JSONDecodeError:
            m = re.match(r'\s*(.*)\n?', xml_sxpr_json)
            snippet = m.group(1) if m else ''
            raise ValueError('Snippet is neither S-expression nor XML: ' + snippet + ' ...')


# if __name__ == "__main__":
#     st = parse_sxpr("(alpha (beta (gamma i\nj\nk) (delta y)) (epsilon z))")
#     print(st.as_sxpr())
#     print(st.as_xml())
