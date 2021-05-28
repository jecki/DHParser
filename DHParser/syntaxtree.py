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
Module ``syntaxtree`` encapsulates the functionality for creating
and handling syntax-trees. This includes serialization and
deserialization of syntax-trees, navigating and serching syntax-trees
as well as annotating sytanx trees with attributes and error messages.


The Node-class
--------------

Syntax trees are composed of Node-objects which are linked
unidirectionally from parent to chilren. Nodes can contain either
child-nodes, in which case they are informally called "branch-nodes" or
test-strings, in which case they informally called "leaf nodes", but
not both at the same time. (There are no mixed nodes as in XML!)

In order to test whether a Node is leaf-node one can check for the
absence of children::

    >>> node = Node('word', 'Palace')
    >>> assert not node.children

The data of a node can be queried by reading the result-property::

    >>> node.result
    'Palace'

The `result` is always a string or a tuple of Nodes, even if the
node-object has been initialized with a single node::

    >>> parent = Node('phrase', node)
    >>> parent.result
    (Node('word', 'Palace'),)

The `result`-property can be assigned to, in order to changae the data
of a node::

    >>> parent.result = (Node('word', 'Buckingham'), Node('blank', ' '), node)

More conveniently than printing the result-propery, nodes can be
serialized as S-expressions (well-known from the computer languages
"lisp" and "scheme")::

    >>> print(parent.as_sxpr())
    (phrase (word "Buckingham") (blank " ") (word "Palace"))

It is also possible to serialize nodes as XML-snippet::

    >>> print(parent.as_xml())
    <phrase>
      <word>Buckingham</word>
      <blank> </blank>
      <word>Palace</word>
    </phrase>

Content-equality of Nodes must be tested with the `equals()`-method.
The equality operator `==` tests merely for the identity of the
node-object, not for the euqality of the content of two different
node-objects::

    >>> n1 = Node('dollars', '1')
    >>> n2 = Node('dollars', '1')
    >>> n1.equals(n2)
    True
    >>> n1 == n2
    False

An empty node is always a leaf-node, that is, if initialized with an
empty tuple, the node's result will actually be the empty string::

    >>> empty = Node('void', ())
    >>> empty.result
    ''
    >>> assert empty.equals(Node('void', ''))

Next to the `result`-property, a node's content can be queried with
either its `children`-property or its `content`-property. The former
yields the tuple of child-nodes. The latter yields the string-content
of the node, which in the case of a "branch-node" is the (recursively
generated) concatenated string-content of all of its children::

    >>> node.content
    'Palace'
    >>> node.children
    ()
    >>> parent.content
    'Buckingham Palace'
    >>> parent.children
    (Node('word', 'Buckingham'), Node('blank', ' '), Node('word', 'Palace'))

Both the `content`-property and the `children`-propery are
read-only-properties. In order to change the data of a node, its
`result`-property must be assigned to (as shown above).

Just like HTML- oder XML-tags, nodes can be annotated with attributes.
Attributes are stored in an ordered dictionary that maps string
identifiers, i.e. the attribute name, to the string-content of the
attribute. This dictionary can be accessed via the `attr`-property::

    >>> node.attr['price'] = 'very high'
    >>> print(node.as_xml())
    <word price="very high">Palace</word>

When serializing as S-expressions attributes are shown as a nested list
marked with a "tick"::

    >>> print(node.as_sxpr())
    (word `(price "very high") "Palace")

Attributes can be queried via the `has_attr()` and `get_attr()`-methods.
This is to be preferred over accessing the `attr`-property for querying,
because the attribute dictionary is created lazily on the first
access of the `attr`-property::

    >>> node.has_attr('price')
    True
    >>> node.get_attr('price', '')
    'very high'
    >>> parent.get_attr('price', 'unknown')
    'unknown'

If called with no parameters or an empty string as attribute name,
`has_attr()` returns True, if at least one attribute is present::

    >>> parent.has_attr()
    False

Attributes can be deleted like dictionary entries::

    >>> del node.attr['price']
    >>> node.has_attr('price')
    False

Node-objects contain a special "write once, read afterwards"-property
named `pos` that is meant to capture the source code position of the
content represented by the Node. Usually, the `pos` values are
initialized with the corresponding source code location by the parser.

The main purpose of keeping source-code locations in the node-objects
is to equip the messages of errors that are detected in later
processing stages with source code locations. In later processing
stages the tree may already have been reshaped and its string-content
may have been changed, say, by normalising whitespace or dropping
delimiters.

Before the `pos`-field can be read, it must have been initialized with
the `with_pos`-method, which recursively initializes the `pos`-field of
the child nodes according to the offset of the string values from the
main field::

    >>> import copy; essentials = copy.deepcopy(parent)
    >>> print(essentials.with_pos(0).as_xml(src=essentials.content))
    <phrase line="1" col="1">
      <word line="1" col="1">Buckingham</word>
      <blank line="1" col="11"> </blank>
      <word line="1" col="12">Palace</word>
    </phrase>
    >>> essentials[-1].pos, essentials.content.find('Palace')
    (11, 11)
    >>> essentials.result = tuple(child for child in essentials.children if child.tag_name != 'blank')
    >>> print(essentials.as_xml(src=essentials.content))
    <phrase line="1" col="1">
      <word line="1" col="1">Buckingham</word>
      <word line="1" col="12">Palace</word>
    </phrase>
    >>> essentials[-1].pos, essentials.content.find('Palace')
    (11, 10)


Serializing and de-serializing syntax-trees
-------------------------------------------

Syntax trees can be serialized as S-expressions, XML, JSON and indented
text. Module 'syntaxtree' also contains two simple parsers
(`parse_sxpr()`, `parse_xml()`) to convert XML-snippets and
S-expressions into trees composed of Node-objects. There is also a
function to parse JSON (`parse_json_syntaxtree()`), but in contrast
to the former two functions it can only deserialize previously
JSON-serialized trees and not any kind of JSON-file. There is no
function to deserialize indented text.

In order to make parameterizing serialization easier, the Node-class
also defines a generic `serialize()`-method next to the more specialized
`as_sxpr()`-, `as_json()`- and `as_xml()`-methods::

    >>> s = '(sentence (word "This") (blank " ") (word "is") (blank " ") (phrase (word "Buckingham") (blank " ") (word "Palace")))'
    >>> sentence = parse_sxpr(s)
    >>> print(sentence.serialize(how='indented'))
    sentence
      word "This"
      blank " "
      word "is"
      blank " "
      phrase
        word "Buckingham"
        blank " "
        word "Palace"
    >>> sxpr = sentence.serialize(how='sxpr')
    >>> round_trip = parse_sxpr(sxpr)
    >>> assert sentence.equals(round_trip)


Navigating and searching nodes and tree-contexts
------------------------------------------------

Transforming syntax trees is usually done by traversing the complete
tree and applying specific transformation functions on each node.
Modules "transform" and "compile" provide high-level interfaces and
scaffolding classes for the traversal and transformation of
syntax-trees.

Module `syntaxtree` does not provide any functions for transforming
trees, but it provides low-evel functions for navigating trees.
These functions cover three different purposes:

1. Downtree-navigation within the subtree spanned by a prticular node.
2. Uptree- and horizontal navigation to the neigborhood ("siblinings")
   ancestry of a given node.
3. Navigation by looking at the string-representation of the tree.


Navigating "downtree" within a tree spanned by a node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are a number of useful functions to help navigating a tree and finding
particular nodes within in a tree::

    >>> list(sentence.select('word'))
    [Node('word', 'This'), Node('word', 'is'), Node('word', 'Buckingham'), Node('word', 'Palace')]
    >>> list(sentence.select(lambda node: node.content == ' '))
    [Node('blank', ' '), Node('blank', ' '), Node('blank', ' ')]

The pick functions always picks the first node fulfilling the criterion::

    >>> sentence.pick('word')
    Node('word', 'This')

Or, reversing the direction::

    >>> last_match = sentence.pick('word', reverse=True)
    >>> last_match
    Node('word', 'Palace')

While nodes contain references to their children, a node does not contain
a references to its parent. As a last resort (because it is slow) the
node's parent can be found by the `find_parent`-function which must be
executed ony ancestor of the node::

    >>> sentence.find_parent(last_match)
    Node('phrase', (Node('word', 'Buckingham'), Node('blank', ' '), Node('word', 'Palace')))

Sometimes, one only wants to select or pick particular children of a node.
Apart from accessing these via `node.children`, there is a tuple-like
access to the immediate children via indices and slices::

    >>> sentence[0]
    Node('word', 'This')
    >>> sentence[-1]
    Node('phrase', (Node('word', 'Buckingham'), Node('blank', ' '), Node('word', 'Palace')))
    >>> sentence[0:3]
    (Node('word', 'This'), Node('blank', ' '), Node('word', 'is'))
    >>> sentence.index('blank')
    1
    >>> sentence.indices('word')
    (0, 2)

as well as a dictionary-like access, with the difference that a "key" may
occur several times::

    >>> sentence['word']
    (Node('word', 'This'), Node('word', 'is'))
    >>> sentence['phrase']
    Node('phrase', (Node('word', 'Buckingham'), Node('blank', ' '), Node('word', 'Palace')))

Be aware that always all matching values will be returned and that the return
type can accordingly be either a tuple of Nodes or a single Node! An IndexError
is raised in case the "key" does not exist or an index is out of range.

It is also possible to delete children conveniently with Python's `del`-operator::

    >>> s_copy = copy.deepcopy(sentence)
    >>> del s_copy['blank'];  print(s_copy)
    ThisisBuckingham Palace
    >>> del s_copy[2][0:2]; print(s_copy.serialize())
    (sentence (word "This") (word "is") (phrase (word "Palace")))

One can also use the `Node.pick_child()` or `Node.select_children()`-method in
order to select children with an arbitrary condition::

    >>> tuple(sentence.select_children(lambda nd: nd.content.find('s') >= 0))
    (Node('word', 'This'), Node('word', 'is'))
    >>> sentence.pick_child(lambda nd: nd.content.find('i') >= 0, reverse=True)
    Node('phrase', (Node('word', 'Buckingham'), Node('blank', ' '), Node('word', 'Palace')))

Often, one is neither interested in selecting form the children of a node, nor
from the entire subtree, but from a certain "depth-range" of a tree-structure.
Say, you would like to pick all word's from the sentence that are not inside
a phrase and assume at the same time that words may occur in nested structures::

    >>> nested = copy.deepcopy(sentence)
    >>> i = nested.index(lambda nd: nd.content == 'is')
    >>> nested[i].result = Node('word', nested[i].result)
    >>> nested[i].tag_name = 'italic'
    >>> nested[0:i + 1]
    (Node('word', 'This'), Node('blank', ' '), Node('italic', (Node('word', 'is'))))

No, in order to select all words on the level of the sentence, but excluding
any sub-phrases, it would not be helpful to use methods based on the selection
of children (i.e. immediate descendents), because the word nested in an
'italic'-Node would be missed. For this purpose the various selection()-methods
of class node have a `skip_subtree`-parameter which can be used to block subtrees
from the iterator based on a criteria (which can be a function, a tag name or
set of tag names and the like)::

    >>> tuple(nested.select('word', skip_subtree='phrase'))
    (Node('word', 'This'), Node('word', 'is'))


Navigating "uptree" within the neighborhood and lineage of a node
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

It is much more elegant to keep track of a node's ancestry by using a
"tree-context" which is a simple List of ancestors starting with the
root-node and including the node itself as its last item. For most
search methods such as select, there exists a pendant that returns
this context instead of just the node itself::

    >>> last_context = sentence.pick_context('word', reverse=True)
    >>> last_context[-1] == last_match
    True
    >>> last_context[0] == sentence
    True
    >>> serialize_context(last_context)
    'sentence <- phrase <- word'

One can also think of a tree-context as a breadcrumb-trail that
"points" to a particular part of text by marking the path from the root
to the node, the content of which contains this text. This node does
not need to be a leaf node, but can be any branching on the way from
the root to the leaves of the tree. When analysing or
transforming a tree-structured text, it is often helpful to "zoom" in
and out of a particular part of text (pointed to by a context) or to
move forward and backward from a particular location (again represented
by a context).

The ``next_context()`` and ``prev_context()``-functions allow to move
one step forward or backward from a given context::

    >>> pointer = prev_context(last_context)
    >>> serialize_context(pointer, with_content=-1)
    'sentence:This is Buckingham Palace <- phrase:Buckingham Palace <- blank: '

``prev_context()`` and ``next_context()`` automatically zoom out by one step,
if they move past the first or last child of the last but one node in the list::

    >>> pointer = prev_context(pointer)
    >>> serialize_context(pointer, with_content=-1)
    'sentence:This is Buckingham Palace <- phrase:Buckingham Palace <- word:Buckingham'
    >>> serialize_context(prev_context(pointer), with_content=-1)
    'sentence:This is Buckingham Palace <- blank: '

Thus::

    >>> next_context(prev_context(pointer)) == pointer
    False
    >>> pointer = prev_context(pointer)
    >>> serialize_context(next_context(pointer), with_content=-1)
    'sentence:This is Buckingham Palace <- phrase:Buckingham Palace'

The reason for this beaviour is that ``prev_context()`` and
``next_context()`` try to move to the context which contains the string
content preeceding or succeeding that of the given context. Therefore,
these functions move to the next sibling on the same branch, rather
traversing the complete tree like the ``select()`` and ``select_context()``-
methods of the Node-class. However, when moving past the first or last
sibling, it is not clear what the next node on the same level should
be. To keep it easy, the function "zooms out" and returns the next
sibling of the parent.

It is, of course, possible to zoom back into a context::

    >>> serialize_context(zoom_into_context(next_context(pointer), FIRST_CHILD, steps=1), with_content=-1)
    'sentence:This is Buckingham Palace <- phrase:Buckingham Palace <- word:Buckingham'

Often it is preferable to move through the leaf-nodes and their
contexts right away. Functions like ``next_leaf_context()`` and
``prev_leaf_context()`` provide syntactic sugar for this case::

    >>> pointer = next_leaf_context(pointer)
    >>> serialize_context(pointer, with_content=-1)
    'sentence:This is Buckingham Palace <- phrase:Buckingham Palace <- word:Buckingham'

It is also possible to inspect just the string content surrounding a
context, rather than its structural environment::

    >>> ensuing_str(pointer)
    ' Palace'
    >>> assert foregoing_str(pointer, length=1) == ' ', "Blank expected!"

It is also possible to systematically iterate through the contexts
forward or backward - just like the `node.select_context()`-method,
but starting from an arbitraty context, instead of the one end or
the other end of the tree rooted in `node`::

    >>> t = parse_sxpr('(A (B 1) (C (D (E 2) (F 3))) (G 4) (H (I 5) (J 6)) (K 7))')
    >>> pointer = t.pick_context('G')
    >>> [serialize_context(ctx, with_content=1) for ctx in select_context(pointer, ALL_CONTEXTS)]
    ['A <- G:4', 'A <- H <- I:5', 'A <- H <- J:6', 'A <- H:56', 'A <- K:7', 'A:1234567']
    >>> [serialize_context(ctx, with_content=1) for ctx in select_context(pointer, ALL_CONTEXTS, reverse=True)]
    ['A <- G:4', 'A <- C <- D <- F:3', 'A <- C <- D <- E:2', 'A <- C <- D:23', 'A <- C:23', 'A <- B:1', 'A:1234567']

Another important difference, besides the starting point is then the
`select()`-generators of the `syntaxtree`-module traverse the tree
post-order (or "depth first"), while the respective methods ot the
Node-class traverse the tree pre-order. See the difference::

    >>> l = [serialize_context(ctx, with_content=1) for ctx in t.select_context(ALL_CONTEXTS, include_root=True)]
    >>> l[l.index('A <- G:4'):]
    ['A <- G:4', 'A <- H:56', 'A <- H <- I:5', 'A <- H <- J:6', 'A <- K:7']
    >>> l = [serialize_context(ctx, with_content=1) for ctx in t.select_context(ALL_CONTEXTS, include_root=True, reverse=True)]
    >>> l[l.index('A <- G:4'):]
    ['A <- G:4', 'A <- C:23', 'A <- C <- D:23', 'A <- C <- D <- F:3', 'A <- C <- D <- E:2', 'A <- B:1']


Navigating a tree via its flat-string-representation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes it may be more convenient to search for a specific feature in
the string-content of a text, rather than in the structured tree. For
example, finding matching brackets in tree-strcutured text can be quite
cumbersome if brackets are not "tagged" individually. For theses cases
it is possible to generate a context mapping that maps text position to
the contexts of the leaf-nodes to which they belong. The context-mapping
can be thought of as a "string-view" on the tree::

    >>> flat_text = sentence.content
    >>> ctx_mapping = generate_context_mapping(sentence)
    >>> leaf_positions, contexts = ctx_mapping
    >>> {k: v for k, v in zip(leaf_positions, (ctx[-1].as_sxpr() for ctx in contexts))}
    {0: '(word "This")', 4: '(blank " ")', 5: '(word "is")', 7: '(blank " ")', 8: '(word "Buckingham")', 18: '(blank " ")', 19: '(word "Palace")'}

Now let's find all letters that are followed by a whitespace character::

    >>> import re; locations = [m.start() for m in re.finditer(r'\w ', flat_text)]
    >>> targets = [map_pos_to_context(loc, ctx_mapping) for loc in locations]

The target returned by `map_pos_to_context()` is a tuple of the target
context and the relative position of the location that falls within this
context::

    >>> [(serialize_context(ctx), relative_pos) for ctx, relative_pos in targets]
    [('sentence <- word', 3), ('sentence <- word', 1), ('sentence <- phrase <- word', 9)]

Now, the structured text can be manipulated at the precise locations
where string search yielded a match. Let's turn our text into a little
riddle by replacing the letters of the leaf-nodes before the match
locations with three dots::

    >>> for ctx, pos in targets: ctx[-1].result = '...' + ctx[-1].content[pos:]
    >>> str(sentence)
    '...s ...s ...m Palace'

The positions resemble the text positions of the text represented by the tree at the
very moment when the context mapping is generated, not the source positions captured
by the `pos`-propery of the node-objects! This also means that the mapping becomes
outdated the very moment, the tree is being restructured.


Adding Error Messages
---------------------

Although errors are typically located at a particualr point or range of the source
code, DHParser treats them as global properties of the syntax tree (albeit with a
location), rather than attaching them to particular nodes. This has two advantages:

1. When restructuring the tree and removing or adding nodes during the
   abtract-syntax-tree-transformation and possibly further tree-transformation,
   error messages do not accidently get lost.

2. It is not necessary to add another slot to the Node class for keeping an
   error list which most of the time would remain empty, anyway.

In order to track errors and other global properties, Module `syntaxtree` provides
the `RootNode`-class. The root-object of a syntax-tree produced by parsing
is of type `RootNode`. If a root node needs to be created manually, it is necessary
to create a `Node`-object and either pass it to `RootNode` as parameter on
instantiation or, later, to the :py:meth:`swallow()`-method of the RootNode-object::

    >>> document = RootNode(sentence, str(sentence))

The second parameter is normally the source code. In this example we simply use the
string representation of the syntax-tree originating in `sentence`. Before any
errors can be added the source-position fields of the nodes of the tree must have
be been initialized. Usually, this is done by the parser. Since the syntax-tree
in this example does not stem from a parsing-process, we have to do it manually:

    >>> _ = document.with_pos(0)

Now, let's mark all "word"-nodes that contain non-letter characters with an
error-message. There should be plenty of them, because, earlier, we have replaced
some of the words partially with "..."::

    >>> import re
    >>> len([document.new_error(node, "word contains illegal characters") \
             for node in document.select('word') if re.fullmatch(r'\w*', node.content) is None])
    3
    >>> for error in document.errors_sorted:  print(error)
    1:1: Error (1000): word contains illegal characters
    1:6: Error (1000): word contains illegal characters
    1:11: Error (1000): word contains illegal characters

The format of the string representation of Error-objects resembles that of
compilers and is understood by many Text-Editors which mark the errors in
the source code.


A Mini-API for attribute-handling
---------------------------------

One important use case of attributes is to add or remove css-classes to the
"class"-attribute. The "class"-attribute understood as containg a set of
whitespace delimited strings. Module "syntaxtree" provides a few functions
to simplify class-handling::

    >>> paragraph = Node('p', 'veni vidi vici')
    >>> add_class(paragraph, 'smallprint')
    >>> paragraph.attr['class']
    'smallprint'

Although the class-attribute is filled with a sequence of strings, it should
behave like a set of strings. For example, one and the same class name should
not appear twice in the class attribute::

    >>> add_class(paragraph, 'smallprint justified')
    >>> paragraph.attr['class']
    'smallprint justified'

Plus, the order of the class strings does not matter, when checking for
elements::

    >>> has_class(paragraph, 'justified smallprint')
    True
    >>> remove_class(paragraph, 'smallprint')
    >>> has_class(paragraph, 'smallprint')
    False
    >>> has_class(paragraph, 'justified smallprint')
    False
    >>> has_class(paragraph, 'justified')
    True

The same logic of treating blank separated sequences of strings as sets can also
be applied to other attributes:

    >>> car = Node('car', 'Porsche')
    >>> add_token_to_attr(car, "Linda Peter", 'owner')
    >>> car.attr['owner']
    'Linda Peter'

Or, more generally, to strings containing whitespace-separated substrings:

    >>> add_token('Linda Paula', 'Peter Paula')
    'Linda Paula Peter'
"""

from collections import OrderedDict
import bisect
import copy
import functools
import json
import sys
from typing import Callable, cast, Iterator, Sequence, List, Set, Union, \
    Tuple, Container, Optional, Dict, Any

from DHParser.configuration import get_config_value, ALLOWED_PRESET_VALUES
from DHParser.error import Error, ErrorCode, ERROR, PARSER_STOPPED_BEFORE_END, \
    add_source_locations
from DHParser.preprocess import SourceMapFunc, SourceLocation, gen_neutral_srcmap_func
from DHParser.stringview import StringView  # , real_indices
from DHParser.toolkit import re, cython, linebreaks, line_col, JSONnull, \
    validate_XML_attribute_value, fix_XML_attribute_value, lxml_XML_attribute_value, \
    identity, Protocol


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
           'ALL_NODES',
           'NO_NODES',
           'LEAF_NODES',
           'ALL_CONTEXTS',
           'NO_CONTEXTS',
           'LEAF_CONTEXTS',
           'Node',
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
# support functions
#
#######################################################################


# support functions for searching an navigating trees #################


# criteria for finding nodes:
# - node itself (equality)
# - tag_name
# - one of several tag_names
# - a function Node -> bool
re_pattern = Any
CriteriaType = Union['Node', str, Container[str], Callable, int, re_pattern]

TreeContext = List['Node']
NodeMatchFunction = Callable[['Node'], bool]
ContextMatchFunction = Callable[[TreeContext], bool]

ALL_NODES = lambda nd: True
NO_NODES = lambda nd: False
LEAF_NODES = lambda nd: not nd._children

ALL_CONTEXTS = lambda ctx: True
NO_CONTEXTS = lambda ctx: False
LEAF_CONTEXTS = lambda ctx: not ctx[-1].children


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
    match function       match function returns `True`
    ==================== ===================================================

    :param criterion: Either a node, the id of a node, a frozen node,
        a tag_name or a container (usually a set) of multiple tag names,
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
        return lambda nd: nd.tag_name == criterion
    elif callable(criterion):
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda nd: nd.tag_name in cast(Container, criterion)
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
        a tag_name or a container (usually a set) of multiple tag names,
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
        return lambda ctx: ctx[-1].tag_name == criterion
    elif callable(criterion):
        return cast(Callable, criterion)
    elif isinstance(criterion, Container):
        return lambda ctx: ctx[-1].tag_name in cast(Container, criterion)
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
    is exceeded the the unflattened S-expression is returned. A
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
    flat = re.sub(r'\s(?=\))', '', re.sub(r'(?<!")\s+', ' ', sxpr).replace('\n', '')).strip()
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
    :returns: the XML-conform tag_name
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

    :ivar tag_name: The name of the node, which is either its
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

    :ivar attr: An optional dictionary of XML-attr. This
            dictionary is created lazily upon first usage. The attr
            will only be shown in the XML-Representation, not in the
            S-expression-output.
    """

    __slots__ = '_result', '_children', '_pos', 'tag_name', '_xml_attr'

    def __init__(self, tag_name: str,
                 result: Union[Tuple['Node', ...], 'Node', StringView, str],
                 leafhint: bool = False) -> None:
        """
        Initializes the ``Node``-object with a tag name and the result of a
        parsing operation. The result of a parsing operation can either be
        one or more child-nodes, in which case the Node is informally
        considered to be a "branch-node", or a text-string, in which case
        the node is informally considered to be a "leaf-node".

        :param tag_name: a tag_name for the node. If the node has been created
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
            self._children = tuple()     # type: Tuple[Node, ...]
        else:
            self._set_result(result)
        self.tag_name = tag_name         # type: str

    def __deepcopy__(self, memo):
        if self._children:
            duplicate = self.__class__(self.tag_name, copy.deepcopy(self._children), False)
        else:
            duplicate = self.__class__(self.tag_name, self.result, True)
        duplicate._pos = self._pos
        if self.has_attr():
            duplicate.attr.update(self._xml_attr)
            # duplicate.attr.update(copy.deepcopy(self._xml_attr))
            # duplicate._xml_attr = copy.deepcopy(self._xml_attr)  # this is not cython compatible
        return duplicate

    def __str__(self):
        return self.content

    def __repr__(self):
        # mpargs = {'name': self.parser.name, 'ptype': self.parser.ptype}
        # name, ptype = (self._tag_name.split(':') + [''])[:2]
        # parg = "MockParser({name}, {ptype})".format(name=name, ptype=ptype)
        rarg = ("'%s'" % str(self)) if not self._children else \
            "(" + ", ".join(child.__repr__() for child in self._children) + ")"
        return "Node('%s', %s)" % (self.tag_name, rarg)

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

    def __len__(self):
        return (sum(child.__len__() for child in self._children)
                if self._children else len(self._result))

    def __bool__(self):
        """Returns the bool value of a node, which is always True. The reason
        for this is that a boolean test on a variable that can contain a node
        or None will only yield `False` in case of None.
        """
        return True

    # def __hash__(self):
    #     return hash(self.tag_name)  # very bad idea!

    def equals(self, other: 'Node', ignore_attr_order: bool = True) -> bool:
        """
        Equality of value: Two nodes are considered as having the same value,
        if their tag name is the same, if their results are equal and
        if their attributes and attribute values are the same and if either
        `ignore_attr_order` is `True` or the attributes also appear in the
        same order.

        :param other: The node to which `self` shall be compared.
        :returns: True, if the tree originating in node `self` is equal by
            value to the tree originating in node `other`.
        """
        if self.tag_name == other.tag_name and self.compare_attr(other, ignore_attr_order):
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
        of the parser that created the node, i.e. ":Series". It is recommended
        practice to remove (or name) all anonymous nodes during the
        AST-transformation.
        """
        tn = self.tag_name
        return not tn or tn[0] == ':'  # self.tag_name.find(':') >= 0

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
                    offset = offset + prev.__len__()
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
            return attr in self._xml_attr if attr else bool(self._xml_attr)
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
            OrderedDict([('id', 'identificator')])
            >>> node.attr['id']
            'identificator'
            >>> del node.attr['id']
            >>> node.attr
            OrderedDict()

        NOTE: Use :py:meth:`Node.has_attr()` rather than `bool(node.attr)`
        to probe the presence of attributes. Attribute dictionaries are
        created lazily and `node.attr` would create a dictionary, even
        though it may never be needed, any more.
        """
        try:
            if self._xml_attr is None:          # cython compatibility
                self._xml_attr = OrderedDict()  # type: Dict[str, str]
        except AttributeError:
            self._xml_attr = OrderedDict()
        return self._xml_attr

    @attr.setter
    def attr(self, attr_dict: Dict[str, str]):
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
            assert isinstance(dictionary, dict), "The non-keyword parameter passed to " \
                "Node.with_attr() must be of type dict, not %s." % str(type(dictionary))
            # assert all(isinstance(a, str) and isinstance(v, str) for a, v in attr_dict.items())
            if dictionary:  # do not update with an empty dictionary
                self.attr.update(dictionary)
        elif attributes:
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

    def __getitem__(self, key: Union[CriteriaType, int, slice]) -> Union['Node', Sequence['Node']]:
        """
        Returns the child node with the given index if ``key`` is
        an integer or all child-nodes with the given tag name. Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")))')
            >>> flatten_sxpr(tree[0].as_sxpr())
            '(b "X")'
            >>> flatten_sxpr(tree["X"].as_sxpr())
            '(X (c "d"))'

        :param key(str): A criterion (tag name(s), match function, node) or
            an index of the child that shall be returned.
        :returns: The node with the given index (always type Node) or a
            tuple of all nodes which have a given tag name, if `key` was a
            tag-name and there is more than one child-node with this tag-name
        :raises:
            KeyError:   if no matching child was found.
            IndexError: if key was an integer index that did not exist
            ValueError: if the __getitem__ has been called on a leaf node.
        """
        if isinstance(key, (int, slice)):
            return self._children[key]
        else:
            mf = create_match_function(key)
            items = tuple(child for child in self._children if mf(child))
            if items:
                return items if len(items) >= 2 else items[0]
            raise IndexError('index out of range') if isinstance(key, int) else KeyError(str(key))

    def __delitem__(self, key: Union[int, slice, CriteriaType]):
        """
        Removes children from the node. Note that integer values passed to
        parameter `key` are always interpreted as index, not as an object id
        as comparison criterion.

        :param key: An integer index of slice of child-nodes to be deleted
            or a criterion for selecting child-nodes for deletion.
        """
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
            assert not isinstance(self.result, str)
            mf = create_match_function(key)
            self.result = tuple(child for child in self._children if not mf(child))

    def get(self, key: Union[int, slice, CriteriaType],
            surrogate: Union['Node', Sequence['Node']]) -> Union['Node', Sequence['Node']]:
        """Returns the child node with the given index if ``key``
        is an integer or the first child node with the given tag name. If no
        child with the given index or tag_name exists, the ``surrogate`` is
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
        except KeyError:
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
        if not self.children and self.content:
            raise ValueError('Node.insert(i, node): Called on a leaf-node')
        result = list(self.children)
        result.insert(index, node)
        self.result = tuple(result)

    @cython.locals(start=cython.int, stop=cython.int, i=cython.int)
    def index(self, what: CriteriaType, start: int = 0, stop: int = sys.maxsize) -> int:
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
                  skip_subtree: NodeMatchFunction = NO_NODES) -> Iterator['Node']:
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
               skip_subtree: CriteriaType = NO_NODES) -> Iterator['Node']:
        """
        Generates an iterator over all nodes in the tree that fulfill the
        given criterion. See :py:func:`create_match_function()` for a
        catalogue of possible criteria.

        :param criterion: The criterion for selecting nodes.
        :param include_root: If False, only descendant nodes will be checked
            for a match.
        :param reverse: If True, the tree will be walked in reverse
                order, i.e. last children first.
        :param skip_subtree: A criterion to identify sub-trees, the returned
                iterator shall not dive into.
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
             skip_subtree: CriteriaType = NO_NODES) -> Optional['Node']:
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
        Returns the leaf-Node that covers the given `location`, where
        location is the actual position within self.content (not the
        source code position that the pos-attribute represents). If
        the location lies out side the node's string content, `None` is
        returned.
        """
        end = 0
        for nd in self.select_if(lambda nd: not nd._children, include_root=True):
            end += len(nd)
            if location < end:
                return nd
        return None

    def find_parent(self, node) -> Optional['Node']:
        """
        Finds and returns the parent of `node` within the tree represented
        by `self`. If the tree does not contain `node`, the value `None`
        is returned.
        """
        for nd in self.select_if(lambda nd: nd._children, include_root=True):
            if node in nd._children:
                return nd
        return None

    # context selection ###

    def select_context_if(self, match_function: ContextMatchFunction,
                          include_root: bool = False,
                          reverse: bool = False,
                          skip_subtree: ContextMatchFunction = NO_CONTEXTS) -> Iterator[TreeContext]:
        """
        Like :py:func:`Node.select_if()` but yields the entire context (i.e. list
        of descendants, the last one being the matching node) instead of just
        the matching nodes. NOTE: In contrast to `select_if()`, `match_function`
        receives the complete context as argument, rather than just the last node!
        """
        def recursive(ctx, include_root):
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
                       skip_subtree: CriteriaType = NO_CONTEXTS) -> Iterator[TreeContext]:
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
                     skip_subtree: CriteriaType = NO_CONTEXTS) -> TreeContext:
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
            end += len(ctx[-1])
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
                             % (node.tag_name, flatten_sxpr(self.as_sxpr())))

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

        def left_cut(result: Tuple['Node'], index: int, subst: 'Node') -> Tuple['Node', ...]:
            return (subst,) + result[index + 1:]

        def right_cut(result: Tuple['Node'], index: int, subst: 'Node') -> Tuple['Node', ...]:
            return result[:index] + (subst,)

        def cut(ctx: TreeContext, cut_func: Callable) -> 'Node':
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
        new_ca = Node(common_ancestor.tag_name, left_children[:i] + right_children[k + i:])
        if common_ancestor.has_attr():
            new_ca.attr = common_ancestor.attr
        return new_ca

    # serialization ###########################################################

    @cython.locals(i=cython.int, k=cython.int, N=cython.int)
    def _tree_repr(self, tab, open_fn, close_fn, data_fn=lambda i: i,
                   density=0, inline=False, inline_fn=lambda node: False,
                   allow_ommissions=False) -> List[str]:
        """
        Generates a tree representation of this node and its children
        in string from.

        The kind ot tree-representation that is determined by several
        function parameters. This could be an XML-representation or a
        lisp-like S-expression.

        :param tab:  The indentation string, e.g. '\t' or '    '
        :param open_fn: A function (Node -> str) that returns an
            opening string (e.g. an XML-tag_name) for a given node
        :param close_fn:  A function (Node -> str) that returns a closing
            string (e.g. an XML-tag_name) for a given node.
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
                                           density, inline, inline_fn)
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
        if not inline and not head and allow_ommissions:
            # strip whitespace for omitted non inline node, e.g. CharData in mixed elements
            res = res.strip()  # WARNING: This changes the data in subtle ways
        if density & 1 and res.find('\n') < 0:
            # except for XML, add a gap between opening statement and content
            gap = ' ' if not inline and head and head[-1:] != '>' else ''
            return [''.join((head, gap, data_fn(res), tail))]
        else:
            lines = [data_fn(s) for s in res.split('\n')]
            N = len(lines)
            i, k = 0, N - 1
            if not inline and allow_ommissions:
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
                compact: bool = False,
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
            brackets are omitted and only the indentation indicates the
            tree structure.
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
            txt = [left_bracket, node.tag_name]
            # s += " '(pos %i)" % node.add_pos
            # txt.append(str(id(node)))  # for debugging
            if node.has_attr():
                txt.extend(' `(%s "%s")' % (k, v) for k, v in node.attr.items())
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
        return sxpr if compact else flatten_sxpr(sxpr, flatten_threshold)

    def as_xml(self, src: str = None,
               indentation: int = 2,
               inline_tags: Set[str] = set(),
               omit_tags: Set[str] = set(),
               empty_tags: Set[str] = set()) -> str:
        """Serializes the tree of nodes as XML.

        :param src: The source text or `None`. In case the source text is
                given, the position will also be reported as line and column.
        :param indentation: The number of whitespaces for indentation
        :param inline_tags:  A set of tag names, the content of which will always be
                written on a single line, unless it contains explicit line feeds (`\\n`).
        :param omit_tags: A set of tags from which only the content will be printed, but
                neither the opening tag nor its attr nor the closing tag. This
                allows producing a mix of plain text and child tags in the output,
                which otherwise is not supported by the Node object, because it
                requires its content to be either a tuple of children or string content.
        :param empty_tags: A set of tags which shall be rendered as empty elements, e.g.
                "<empty/>" instead of "<empty><empty>".
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
            nonlocal attr_filter
            if node.tag_name in omit_tags and not node.has_attr():
                return ''
            txt = ['<', xml_tag_name(node.tag_name)]
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
            if node.tag_name in empty_tags:
                assert not node.result, ("Node %s with content %s is not an empty element!" %
                                         (node.tag_name, str(node)))
                ending = "/>" if not node.tag_name[0] == '?' else "?>"
            else:
                ending = ">"
            return "".join(txt + [ending])

        def closing(node: Node):
            """Returns the closing string for the representation of `node`."""
            if node.tag_name in empty_tags or (node.tag_name in omit_tags and not node.has_attr()):
                return ''
            return '</' + xml_tag_name(node.tag_name) + '>'

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
            return node.tag_name in inline_tags \
                or (node.has_attr()
                    and node.attr.get('xml:space', 'default') == 'preserve')

        line_breaks = linebreaks(src) if src else []
        return '\n'.join(self._tree_repr(
            ' ' * indentation, opening, closing, sanitizer, density=1, inline_fn=inlining,
            allow_ommissions=bool(omit_tags)))

    # JSON serialization ###

    def to_json_obj(self) -> list:
        """Converts the tree into a JSON-serializable nested list."""
        jo = [self.tag_name,
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
        """Serializes the tree originating in `self` as JSON-string."""
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
                if nd._children:
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
        elif switch == 'indented':
            sxpr = self.as_sxpr(flatten_threshold=0)
            if sxpr.find('\n') >= 0:
                sxpr = re.sub(r'\n(\s*)\(', r'\n\1', sxpr)
                sxpr = re.sub(r'\n\s*\)(?!")', r'', sxpr)
                # sxpr = re.sub(r'(?<=\n[^`]*)\)[ \t]*\n', r'\n', sxpr)
                sl = sxpr.split('\n')
                for i in range(len(sl)):
                    if '`' in sl[i]:
                        sl[i] = sl[i].replace('))', ')')
                    elif sl[i][-1:] != '"':
                        sl[i] = sl[i].replace(')', '')
                sxpr = '\n'.join(sl)
                sxpr = re.sub(r'^\(', r'', sxpr)
            sxpr = re.sub(r'\n\s*"(?=.*?(?:$|\n\s*\w))', r' "', sxpr)
            return sxpr
        else:
            s = how if how == switch else (how + '/' + switch)
            raise ValueError('Unknown serialization "%s". Allowed values are either: %s or : %s'
                             % (s, "ast, cst, default",
                                ", ".join(ALLOWED_PRESET_VALUES['default_serialization'])))

    # Export and import as Element-Tree ###

    def as_etree(self, text_tags: Set[str] = {":Text"}):
        """Returns the tree as standard-library XML-ElementTree."""
        import xml.etree.ElementTree as ET
        attributes = self.attr if self.has_attr() else {}
        tag_name = xml_tag_name(self.tag_name) if self.tag_name[:1] == ':' else self.tag_name
        if self.children:
            element = ET.Element(tag_name, attrib=attributes)
            element.extend([child.as_etree() for child in self.children])
        else:
            element = ET.Element(tag_name, attrib=attributes)
            element.text = self.content
        return element

    @staticmethod
    def from_etree(et, text_tag: str = ':Text') -> 'Node':
        """Converts a standard-library XML-ElementTree to a tree of nodes."""
        sub_elements = et.findall('*')
        if sub_elements:
            children = [Node(text_tag, et.text)] if et.text else []
            for el in sub_elements:
                children.append(Node.from_etree(el))
                if el.tail:
                    children.append(Node(text_tag, el.tail))
            node = Node(restore_tag_name(et.tag), tuple(children))
        else:
            node = Node(restore_tag_name(et.tag), et.text or '').with_attr(et.attrib)
        return node


#######################################################################
#
# Functions related to the Node class
#
#######################################################################


# Navigate contexts ###################################################

@cython.locals(i=cython.int, k=cython.int)
def prev_context(context: TreeContext) -> Optional[TreeContext]:
    """Returns the context of the predecessor of the last node in the
    context. The predecessor is the sibling of the same parent-node
    preceding the node, or, if it already is the first sibling, the parent's
    sibling preceding the parent, or grand-parent's sibling and so on.
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
    succeeding the the node, or if it already is the last sibling, the
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


def select_context_if(context: TreeContext,
                      match_function: ContextMatchFunction,
                      reverse: bool = False) -> Iterator[TreeContext]:
    """
    Creates an Iterator yielding all `contexts` for which the
    `match_function` is true, starting from `context`.
    """
    context = context.copy()
    while context:
        if match_function(context):
            yield context
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
            innermost_ctx = nearest_sibling.pick_context(
                LEAF_CONTEXTS, include_root=True, reverse=reverse)
            context.extend(innermost_ctx)


def select_context(context: TreeContext,
                   criterion: CriteriaType,
                   reverse: bool = False) -> Iterator[TreeContext]:
    """
    Like `select_context_if()` but yields the entire context (i.e. list of
    descendants, the last one being the matching node) instead of just
    the matching nodes.
    """
    return select_context_if(context, create_context_match_function(criterion), reverse)


def pick_context(context: TreeContext,
                 criterion: CriteriaType,
                 reverse: bool = False) -> Optional[TreeContext]:
    """
    Like `Node.pick()`, only that the entire context (i.e. chain of descendants)
    relative to `self` is returned.
    """
    try:
        return next(select_context(context, criterion, reverse=reverse))
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

    :param context: the context to serialized.
    :param with_content: the number of nodes from the end of the context for
        which the content will be displayed next to the tag_name.
    :param delimiter: The delimiter separating the nodes in the returned string.
    :returns: the string-serialization of the given context.
    """
    if with_content == 0:
        lines = [nd.tag_name for nd in context]
    else:
        n = with_content if with_content > 0 else len(context)
        lines = [nd.tag_name for nd in context[:-n]]
        lines.extend(nd.tag_name + ':' + str(nd.content) for nd in context[-n:])
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
    for ctx in node.select_context_if(LEAF_CONTEXTS, include_root=True):
        pos_list.append(pos)
        ctx_list.append(ctx)
        pos += len(ctx[-1])
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
    transformation any more. This can be verified with
    :py:func:`tree_sanity_check()`. Or, as comparison criterion for
    content equality when picking or selecting nodes or contexts from
    a tree (see :py:func:`create_match_function()`).
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
        try:
            return self._xml_attr
        except AttributeError:
            return OrderedDict()  # assignments will be void!

    @attr.setter
    def attr(self, attr_dict: OrderedDict):
        if self.has_attr():
            raise AssertionError("Frozen nodes' attributes can only be set once")
        else:
            self._xml_attr = attr_dict

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
    Sanity check for syntax trees: One and the same node must never appear
    twice in the syntax tree. Frozen Nodes (EMTPY_NODE, PLACEHOLDER)
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


class RootNode(Node):
    """The root node for the syntax tree is a special kind of node that keeps
    and manages global properties of the tree as a whole. These are first and
    foremost the list off errors that occurred during tree generation
    (i.e. parsing) or any transformation of the tree. Other properties concern
    the customization of the XML-serialization.

    Although errors are local properties that occur on a specific point or
    chunk of source code, instead of attaching the errors to the nodes on
    which they have occurred, the list of errors in managed globally by the
    root-node object. Otherwise it would be hard to keep track of the
    errors when during the transformation of trees node are replaced or
    dropped that might also contain error messages.

    The root node can be instantiated before the tree is fully parsed. This is
    necessary, because the root node is needed for managing error messages
    during the parsing process, already. In order to connect the root node to
    the tree, when parsing is finished, the swallow()-method must be called.

    :ivar errors:  A list of all errors that have occurred so far during
        processing (i.e. parsing, AST-transformation, compiling) of this tree.
    :ivar errors_sorted: (read-only property) The list of errors orderd by
        their position.
    :ivar error_nodes: A mapping of node-ids to a list of errors that
        occurred on the node with the respective id.
    :ivar error_positions: A mapping of locations to a set of ids of nodes
        that contain an error at that particular location
    :ivar error_flag: the highest warning or error level of all errors
        that occurred.

    :ivar source:  The source code (after preprocessing)
    :ivar source_mapping:  A source mapping function to map source code
        position to positions of the non-preprocessed source.
        See module `preprocess`
    :ivar lbreaks: A list of indices of all linebreaks in the source.

    :ivar inline_tags: see `Node.as_xml()` for an explanation.
    :ivar omit_tags: see `Node.as_xml()` for an explanation.
    :ivar empty_tags: see `Node.as_xml()` for an explanation.
    """

    def __init__(self, node: Optional[Node] = None,
                 source: Union[str, StringView] = '',
                 source_mapping: Optional[SourceMapFunc] = None):
        super().__init__('__not_yet_ready__', '')
        self.errors = []               # type: List[Error]
        self.error_nodes = dict()      # type: Dict[int, List[Error]]  # id(node) -> error list
        self.error_positions = dict()  # type: Dict[int, Set[int]]  # pos -> set of id(node)
        self.error_flag = 0
        # info on source code (to be carried along all stages of tree-processing)
        self.source = source           # type: str
        if source_mapping is None:
            self.source_mapping = gen_neutral_srcmap_func(source)
        else:
            self.source_mapping = source_mapping  # type: SourceMapFunc
        self.lbreaks = linebreaks(source)  # List[int]
        # customization for XML-Representation
        self.inline_tags = set()  # type: Set[str]
        self.omit_tags = set()    # type: Set[str]
        self.empty_tags = set()   # type: Set[str]
        if node is not None:
            self.swallow(node, source, source_mapping)

    # def clear_errors(self):
    #     """
    #     DEPRECATED: Should not be ued any more!
    #     Removes all error messages. This can be used to keep the error messages
    #     of different subsequent phases of tree-processing separate.
    #     """
    #     raise NotImplementedError
    #     # self.errors = []               # type: List[Error]
    #     # self.error_nodes = dict()      # type: Dict[int, List[Error]]  # id(node) -> error list
    #     # self.error_positions = dict()  # type: Dict[int, Set[int]]  # pos -> set of id(node)
    #     # self.error_flag = 0

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
            duplicate.attr.update(self._xml_attr)
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

    def swallow(self, node: Optional[Node],
                source: Union[str, StringView] = '',
                source_mapping: Optional[SourceMapFunc] = None) \
            -> 'RootNode':
        """
        Put `self` in the place of `node` by copying all its data.
        Returns self.

        This is done by the parse.Grammar object after
        parsing has finished, so that the Grammar object always
        returns a syntax tree rooted in a RootNode object.

        It is possible to add errors to a RootNode object, before it
        has actually swallowed the root of the syntax tree.
        """
        if source and source != self.source:
            self.source = source
            self.lbreaks = linebreaks(source)
        if source_mapping is None:
            self.source_mapping = gen_neutral_srcmap_func(source)
        else:
            self.source_mapping = source_mapping  # type: SourceMapFunc
        if self.tag_name != '__not_yet_ready__':
            raise AssertionError('RootNode.swallow() has already been called!')
        if node is None:
            self.tag_name = ZOMBIE_TAG
            self.with_pos(0)
            self.new_error(self, 'Parser did not match!', PARSER_STOPPED_BEFORE_END)
            return self
        self._result = node._result
        self._children = node._children
        self._pos = node._pos
        self.tag_name = node.tag_name
        if node.has_attr():
            self._xml_attr = node._xml_attr
        # self._content = node._content
        if id(node) in self.error_nodes:
            self.error_nodes[id(self)] = self.error_nodes[id(node)]
        if self.source:
            add_source_locations(self.errors, self.source_mapping)
        return self

    def add_error(self, node: Optional[Node], error: Error) -> 'RootNode':
        """
        Adds an Error object to the tree, locating it at a specific node.
        """
        assert isinstance(error, Error)
        if not node:
            # find the first leaf-node from the left that could contain the error
            # judging from its position
            pos_list = []
            node_list = []
            nd = None
            for nd in self.select_if(lambda nd: not nd._children):
                assert nd.pos >= 0
                if nd.pos <= error.pos < nd.pos + len(nd):
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
                "%i <= %i <= %i ?" % (node.pos, error.pos, node.pos + max(1, len(node) - 1))
            assert node.pos >= 0, "Errors cannot be assigned to nodes without position!"
        self.error_nodes.setdefault(id(node), []).append(error)
        if node.pos == error.pos:
            self.error_positions.setdefault(error.pos, set()).add(id(node))
        if self.source:
            add_source_locations([error], self.source_mapping)
        self.errors.append(error)
        self.error_flag = max(self.error_flag, error.code)
        return self

    def new_error(self,
                  node: Node,
                  message: str,
                  code: ErrorCode = ERROR) -> 'RootNode':
        """
        Adds an error to this tree, locating it at a specific node.

        :param node:    the node where the error occurred
        :param message: a string with the error message.abs
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
        [node.pos, node.pos + len(node)[
        """
        node_id = id(node)           # type: int
        errors = []                  # type: List[Error]
        start_pos = node.pos
        end_pos = node.pos + max(len(node), 1)
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
                    # node is not connected to tree any more, but since errors
                    # should not get lost, display its errors on its parent
                    errors.extend(self.error_nodes[nid])
        return errors

    def transfer_errors(self, src: Node, dest: Node):
        """
        Transfers errors to a different node. While errors never get lost
        during AST-transformation, because they are kept by the RootNode,
        the nodes they are connected to may be dropped in the course of the
        transformation. This function allows to attach errors from a node that
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
        self.errors.sort(key=lambda e: e.pos)
        return self.errors

    def did_match(self) -> bool:
        """
        Returns True, if the parser that has generated this tree did
        match, False otherwise. Depending on wether the Grammar-object that
        that generated the syntax tree was called with `complete_match=True`
        or not this requires either the complete document to have been
        matched or only the beginning.

        Note: If the parser did match, this does not mean that it must
        have matched without errors. It simply means the no
        PARSER_STOPPED_BEFORE_END-error has occurred.
        """
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
# S-expression- and XML-parsers and JSON-reader, ElementTree-converter
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
    remaining = sxpr  # type: StringView

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
        for match in s.finditer(re.compile(r'\s*(?P<attr>[\w:_.-]+)\s*=\s*"(?P<value>.*?)"\s*')):
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
        m = s.search(re.compile(r'<(?![?!])'))
        i = s.index(m.start()) if m else len(s)
        k = s.rfind(">", end=i)
        return s[k+1:] if k >= 0 else s

    def parse_opening_tag(s: StringView) -> Tuple[StringView, str, OrderedDict, bool]:
        """
        Parses an opening tag. Returns the string segment following the
        the opening tag, the tag name, a dictionary of attr and
        a flag indicating whether the tag is actually a solitary tag as
        indicated by a slash at the end, i.e. <br/>.
        """
        match = s.match(re.compile(r'<\s*(?P<tagname>[\w:_.-]+)\s*'))
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
        match = s.match(re.compile(r'</\s*(?P<tagname>[\w:_.-]+)\s*>'))
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
        if not solitary:
            while s and not s[:2] == "</":
                s, leaf = parse_leaf_content(s)
                if leaf and (leaf.find('\n') < 0 or not leaf.match(RX_WHITESPACE_TAIL)):
                    res.append(Node(TOKEN_PTYPE, leaf))
                if s[:1] == "<":
                    if s[:2] in ("<?", "<!"):
                        s = skip_special_tag(s)
                    elif s[:2] != "</":
                        s, child = parse_full_content(s)
                        res.append(child)
            s, closing_tagname = parse_closing_tag(s)
            assert tagname == closing_tagname, tagname + ' != ' + closing_tagname
        if len(res) == 1 and res[0].tag_name == TOKEN_PTYPE:
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

    match_header = xml.search(re.compile(r'<(?![?!])'))
    start = xml.index(match_header.start()) if match_header else 0
    _, tree = parse_full_content(xml[start:])
    return tree


class DHParser_JSONEncoder(json.JSONEncoder):
    """A JSON-encoder that also encodes syntaxtree.Node- as valid json objects.
    Node-objects are encoded using Node.as_json.
    """
    def default(self, obj):
        if isinstance(obj, Node):
            return cast(Node, obj).to_json_obj()
        elif obj is JSONnull or isinstance(obj, JSONnull):
            return None
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
