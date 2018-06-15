# transform.py - transformation functions for converting the
#                concrete into the abstract syntax tree
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
Module ``transform`` contains the functions for transforming the
concrete syntax tree (CST) into an abstract syntax tree (AST).

As these functions are very generic, they can in principle be
used for any kind of tree transformations, not necessarily only
for CST -> AST transformations.
"""


import collections.abc
import inspect
from functools import partial, reduce, singledispatch

from DHParser.error import Error
from DHParser.syntaxtree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, MockParser, ZOMBIE_NODE
from DHParser.toolkit import expand_table, smart_list, re, typing
from typing import AbstractSet, Any, ByteString, Callable, cast, Container, Dict, \
    Tuple, List, Sequence, Union, Text, GenericMeta

__all__ = ('TransformationDict',
           'TransformationProc',
           'TransformationFunc',
           'ConditionFunc',
           'KeyFunc',
           'transformation_factory',
           'key_parser_name',
           'key_tag_name',
           'traverse',
           'is_named',
           'replace_by_single_child',
           'reduce_single_child',
           'replace_or_reduce',
           'replace_parser',
           'collapse',
           'merge_children',
           'replace_content',
           'replace_content_by',
           'apply_if',
           'apply_unless',
           'traverse_locally',
           'is_anonymous',
           'is_whitespace',
           'is_empty',
           'is_expendable',
           'is_token',
           'is_one_of',
           'has_content',
           'has_parent',
           'lstrip',
           'rstrip',
           'strip',
           'keep_children',
           'keep_children_if',
           'keep_tokens',
           'keep_nodes',
           'keep_content',
           'remove_children_if',
           'remove_nodes',
           'remove_content',
           'remove_first',
           'remove_last',
           'remove_whitespace',
           'remove_empty',
           'remove_anonymous_empty',
           'remove_anonymous_expendables',
           'remove_anonymous_tokens',
           'remove_expendables',
           'remove_brackets',
           'remove_infix_operator',
           'remove_single_child',
           'remove_tokens',
           'flatten',
           'forbid',
           'require',
           'assert_content',
           'error_on',
           'warn_on',
           'assert_has_children')


TransformationProc = Callable[[List[Node]], None]
TransformationDict = Dict[str, Sequence[Callable]]
TransformationFunc = Union[Callable[[Node], Any], partial]
ProcessingTableType = Dict[str, Union[Sequence[Callable], TransformationDict]]
ConditionFunc = Callable  # Callable[[List[Node]], bool]
KeyFunc = Callable[[Node], str]
CriteriaType = Union[int, str, Callable]


def transformation_factory(t1=None, t2=None, t3=None, t4=None, t5=None):
    """Creates factory functions from transformation-functions that
    dispatch on the first parameter after the context parameter.

    Decorating a transformation-function that has more than merely the
    ``context``-parameter with ``transformation_factory`` creates a
    function with the same name, which returns a partial-function that
    takes just the context-parameter.

    Additionally, there is some some syntactic sugar for
    transformation-functions that receive a collection as their second
    parameter and do not have any further parameters. In this case a
    list of parameters passed to the factory function will be converted
    into a collection.

    Main benefit is readability of processing tables.

    Usage::

        @transformation_factory(AbstractSet[str])
        def remove_tokens(context, tokens):
            ...

    or, alternatively::

        @transformation_factory
        def remove_tokens(context, tokens: AbstractSet[str]):
            ...

    Example::

        trans_table = { 'expression': remove_tokens('+', '-') }

    instead of::

        trans_table = { 'expression': partial(remove_tokens, tokens={'+', '-'}) }

    Parameters:
        t1:  type of the second argument of the transformation function,
            only necessary if the transformation functions' parameter list
            does not have type annotations.
    """

    def type_guard(t):
        """Raises an error if type `t` is a generic type or could be mistaken
        for the type of the canonical first parameter "List[Node] of
        transformation functions. Returns `t`."""
        if isinstance(t, GenericMeta):
            raise TypeError("Generic Type %s not permitted\n in transformation_factory "
                            "decorator. Use the equivalent non-generic type instead!"
                            % str(t))
        if issubclass(List[Node], t):
            raise TypeError("Sequence type %s not permitted\nin transformation_factory "
                            "decorator, because it could be mistaken for a base class "
                            "of List[Node]\nwhich is the type of the canonical first "
                            "argument of transformation functions. Try 'tuple' instead!"
                            % str(t))
        return t

    def decorator(f):
        nonlocal t1
        sig = inspect.signature(f)
        params = list(sig.parameters.values())[1:]
        if len(params) == 0:
            return f  # '@transformer' not needed w/o free parameters
        assert t1 or params[0].annotation != params[0].empty, \
            "No type information on second parameter found! Please, use type " \
            "annotation or provide the type information via transformer-decorator."
        f = singledispatch(f)
        p1type = params[0].annotation
        if t1 is None:
            t1 = type_guard(p1type)
        elif issubclass(p1type, type_guard(t1)):
            try:
                if len(params) == 1 and issubclass(p1type, Container) \
                        and not (issubclass(p1type, Text) or issubclass(p1type, ByteString)):
                    def gen_special(*args):
                        c = set(args) if issubclass(p1type, AbstractSet) else \
                            tuple(args) if issubclass(p1type, Sequence) else args
                        d = {params[0].name: c}
                        return partial(f, **d)

                    f.register(type_guard(p1type.__args__[0]), gen_special)
            except AttributeError:
                pass  # Union Type does not allow subclassing, but is not needed here
        else:
            raise TypeError("Annotated type %s is not a subclass of decorated type %s !"
                            % (str(p1type), str(t1)))

        def gen_partial(*args, **kwargs):
            d = {p.name: arg for p, arg in zip(params, args)}
            d.update(kwargs)
            return partial(f, **d)

        for t in (t1, t2, t3, t4, t5):
            if t:
                f.register(type_guard(t), gen_partial)
            else:
                break
        return f

    if isinstance(t1, type(lambda: 1)):
        # Provide for the case that transformation_factory has been
        # written as plain decorator and not as a function call that
        # returns the decorator proper.
        func = t1
        t1 = None
        return decorator(func)
    else:
        return decorator


def key_parser_name(node: Node) -> str:
    return node.parser.name


def key_tag_name(node: Node) -> str:
    return node.tag_name


def traverse(root_node: Node,
             processing_table: ProcessingTableType,
             key_func: KeyFunc=key_tag_name) -> None:
    """
    Traverses the snytax tree starting with the given ``node`` depth
    first and applies the sequences of callback-functions registered
    in the ``processing_table``-dictionary.

    The most important use case is the transformation of a concrete
    syntax tree into an abstract tree (AST). But it is also imaginable
    to employ tree-traversal for the semantic analysis of the AST.

    In order to assign sequences of callback-functions to nodes, a
    dictionary ("processing table") is used. The keys usually represent
    tag names, but any other key function is possible. There exist
    three special keys:

    - '+': always called (before any other processing function)
    - '*': called for those nodes for which no (other) processing
      function appears in the table
    - '~': always called (after any other processing function)

    Args:
        root_node (Node): The root-node of the syntax tree to be traversed
        processing_table (dict): node key -> sequence of functions that
            will be applied to matching nodes in order. This dictionary
            is interpreted as a ``compact_table``. See
            :func:`expand_table` or :func:`EBNFCompiler.EBNFTransTable`
        key_func (function): A mapping key_func(node) -> keystr. The default
            key_func yields node.parser.name.

    Example::

        table = { "term": [replace_by_single_child, flatten],
                  "factor, flowmarker, retrieveop": replace_by_single_child }
        traverse(node, table)

    """
    # Is this optimazation really needed?
    if '__cache__' in processing_table:
        # assume that processing table has already been expanded
        table = processing_table               # type: ProcessingTableType
        cache = cast(TransformationDict, processing_table['__cache__'])  # type: TransformationDict
    else:
        # normalize processing_table entries by turning single values
        # into lists with a single value
        table = {name: cast(Sequence[Callable], smart_list(call))
                 for name, call in list(processing_table.items())}
        table = expand_table(table)
        cache = cast(TransformationDict,
                     table.setdefault('__cache__', cast(TransformationDict, dict())))
        # change processing table in place, so its already expanded and cache filled next time
        processing_table.clear()
        processing_table.update(table)

    # assert '__cache__' in processing_table
    # # Code without optimization
    # table = {name: smart_list(call) for name, call in list(processing_table.items())}
    # table = expand_table(table)
    # cache = {}  # type: Dict[str, List[Callable]]

    def traverse_recursive(context):
        nonlocal cache
        node = context[-1]
        if node.children:
            context.append(ZOMBIE_NODE)
            for child in node.children:
                context[-1] = child
                traverse_recursive(context)  # depth first
            context.pop()

        key = key_func(node)
        try:
            sequence = cache[key]
        except KeyError:
            sequence = table.get('+', []) \
                + table.get(key, table.get('*', [])) \
                + table.get('~', [])
            # '+' always called (before any other processing function)
            # '*' called for those nodes for which no (other) processing function
            #     appears in the table
            # '~' always called (after any other processing function)
            cache[key] = sequence

        for call in sequence:
            call(context)

    traverse_recursive([root_node])
    # assert processing_table['__cache__']


#######################################################################
#
# meta transformations, i.e. transformations that call other
# transformations
#
#######################################################################


@transformation_factory(dict)
def traverse_locally(context: List[Node],
                     processing_table: Dict,            # actually: ProcessingTableType
                     key_func: Callable=key_tag_name):  # actually: KeyFunc
    """Transforms the syntax tree starting from the last node in the context
    according to the given processing table. The purpose of this function is
    to apply certain transformations locally, i.e. only for those nodes that
    have the last node in the context as their parent node.
    """
    traverse(context[-1], processing_table, key_func)


@transformation_factory(collections.abc.Callable)
def apply_if(context: List[Node], transformation: Callable, condition: Callable):
    """Applies a transformation only if a certain condition is met."""
    if condition(context):
        transformation(context)


@transformation_factory(collections.abc.Callable)
def apply_unless(context: List[Node], transformation: Callable, condition: Callable):
    """Applies a transformation if a certain condition is *not* met."""
    if not condition(context):
        transformation(context)


#######################################################################
#
# conditionals that determine whether the context (or the last node in
# the context for that matter) fulfill a specific condition.
# ---------------------------------------------------------------------
#
# The context of a node is understood as a list of all parent nodes
# leading up to and including the node itself. If represented as list,
# the last element of the list is the node itself.
#
#######################################################################


def is_single_child(context: List[Node]) -> bool:
    """Returns ``True`` if the current node does not have any siblings."""
    return len(context[-2].children) == 1


def is_named(context: List[Node]) -> bool:
    """Returns ``True`` if the current node's parser is a named parser."""
    return bool(context[-1].parser.name)


def is_anonymous(context: List[Node]) -> bool:
    """Returns ``True`` if the current node's parser is an anonymous parser."""
    return not context[-1].parser.name


def is_whitespace(context: List[Node]) -> bool:
    """Removes whitespace and comments defined with the
    ``@comment``-directive."""
    return context[-1].parser.ptype == WHITESPACE_PTYPE


def is_empty(context: List[Node]) -> bool:
    """Returns ``True`` if the current node's content is empty."""
    return not context[-1].result


def is_expendable(context: List[Node]) -> bool:
    """Returns ``True`` if the current node either is a node containing
    whitespace or an empty node."""
    return is_empty(context) or is_whitespace(context)


@transformation_factory(collections.abc.Set)
def is_token(context: List[Node], tokens: AbstractSet[str] = frozenset()) -> bool:
    """Checks whether the last node in the context has `ptype == TOKEN_PTYPE`
    and it's content matches one of the given tokens. Leading and trailing
    whitespace-tokens will be ignored. In case an empty set of tokens is passed,
    any token is a match.
    """
    def stripped(nd: Node) -> str:
        """Removes leading and trailing whitespace-nodes from content."""
        # assert node.parser.ptype == TOKEN_PTYPE
        if nd.children:
            i, k = 0, len(nd.children)
            while i < len(nd.children) and nd.children[i].parser.ptype == WHITESPACE_PTYPE:
                i += 1
            while k > 0 and nd.children[k - 1].parser.ptype == WHITESPACE_PTYPE:
                k -= 1
            return "".join(child.content for child in node.children[i:k])
        return nd.content
    node = context[-1]
    return node.parser.ptype == TOKEN_PTYPE and (not tokens or stripped(node) in tokens)


@transformation_factory(collections.abc.Set)
def is_one_of(context: List[Node], tag_name_set: AbstractSet[str]) -> bool:
    """Returns true, if the node's tag_name is one of the given tag names."""
    return context[-1].tag_name in tag_name_set


@transformation_factory
def has_content(context: List[Node], regexp: str) -> bool:
    """
    Checks a node's content against a regular expression.

    In contrast to ``re.match`` the regular expression must match the complete
    string and not just the beginning of the string to succeed!
    """
    if not regexp.endswith('$'):
        regexp += "$"
    return bool(re.match(regexp, context[-1].content))


@transformation_factory(collections.abc.Set)
def has_parent(context: List[Node], tag_name_set: AbstractSet[str]) -> bool:
    """Checks whether a node with one of the given tag names appears somewhere
     in the context before the last node in the context."""
    for i in range(2, len(context)):
        if context[-i].tag_name in tag_name_set:
            return True
    return False


#######################################################################
#
# utility functions (private)
#
#######################################################################


def _replace_by(node: Node, child: Node):
    if not child.parser.name:
        child.parser = MockParser(node.parser.name, child.parser.ptype)
        # parser names must not be overwritten, else: child.parser.name = node.parser.name
    node.parser = child.parser
    # node.errors.extend(child.errors)
    node.result = child.result
    if hasattr(child, '_xml_attr'):
        node.attributes.update(child.attributes)


def _reduce_child(node: Node, child: Node):
    # node.errors.extend(child.errors)
    node.result = child.result
    if hasattr(child, '_xml_attr'):
        node.attributes.update(child.attributes)


# def _pick_child(context: List[Node], criteria: CriteriaType):
#     """Returns the first child that meets the criteria."""
#     if isinstance(criteria, int):
#         try:
#             return context[-1].children[criteria]
#         except IndexError:
#             return None
#     elif isinstance(criteria, str):
#         for child in context[-1].children:
#             if child.tag_name == criteria:
#                 return child
#         return None
#     else:  # assume criteria has type ConditionFunc
#         for child in context[-1].children:
#             context.append(child)
#             evaluation = criteria(context)
#             context.pop()
#             if evaluation:
#                 return child
#         return None


#######################################################################
#
# rearranging transformations
#
# - tree may be rearranged (e.g.flattened)
# - nodes that are not leaves may be dropped
# - order is preserved
# - leave content is preserved (though not necessarily the leaves
#   themselves)
#
#######################################################################


# @transformation_factory(int, str, Callable)
# def replace_by_child(context: List[Node], criteria: CriteriaType=is_single_child):
#     """
#     Replaces a node by the first of its immediate descendants
#     that meets the `criteria`. The criteria can either be the
#     index of the child (counting from zero), or the tag name or
#     a boolean-valued function on the context of the child.
#     If no child matching the criteria is found, the node will
#     not be replaced.
#     With the default value for `criteria` the same semantics is
#     the same that of `replace_by_single_child`.
#     """
#     child = _pick_child(context, criteria)
#     if child:
#         _replace_by(context[-1], child)
#
#
# @transformation_factory(int, str, Callable)
# def content_from_child(context: List[Node], criteria: CriteriaType = is_single_child):
#     """
#     Reduces a node, by transferring the result of the first of its
#     immediate descendants that meets the `criteria` to this node,
#     but keeping this node's parser entry. The criteria can either
#     be the index of the child (counting from zero), or the tag
#     name or a boolean-valued function on the context of the child.
#     If no child matching the criteria is found, the node will
#     not be replaced.
#     With the default value for `criteria` this has the same semantics
#     as `content_from_single_child`.
#     """
#     child = _pick_child(context, criteria)
#     if child:
#         _reduce_child(context[-1], child)


def replace_by_single_child(context: List[Node]):
    """
    Removes single branch node, replacing it by its immediate descendant.
    Replacement only takes place, if the last node in the context has
    exactly one child.
    """
    node = context[-1]
    if len(node.children) == 1:
        _replace_by(node, node.children[0])


def reduce_single_child(context: List[Node]):
    """
    Reduces a single branch node by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    Reduction only takes place if the last node in the context has
    exactly one child.
    """
    node = context[-1]
    if len(node.children) == 1:
        _reduce_child(node, node.children[0])


@transformation_factory(collections.abc.Callable)
def replace_or_reduce(context: List[Node], condition: Callable=is_named):
    """
    Replaces node by a single child, if condition is met on child,
    otherwise (i.e. if the child is anonymous) reduces the child.
    """
    node = context[-1]
    if len(node.children) == 1:
        child = node.children[0]
        if condition(context):
            _replace_by(node, child)
        else:
            _reduce_child(node, child)


@transformation_factory
def replace_parser(context: List[Node], name: str):
    """
    Replaces the parser of a Node with a mock parser with the given
    name.

    Parameters:
        context: the context where the parser shall be replaced
        name: "NAME:PTYPE" of the surrogate. The ptype is optional
    """
    node = context[-1]
    name, ptype = (name.split(':') + [''])[:2]
    node.parser = MockParser(name, ':' + ptype)


@transformation_factory(collections.abc.Callable)
def flatten(context: List[Node], condition: Callable=is_anonymous, recursive: bool=True):
    """
    Flattens all children, that fulfil the given ``condition``
    (default: all unnamed children). Flattening means that wherever a
    node has child nodes, the child nodes are inserted in place of the
    node.

    If the parameter ``recursive`` is ``True`` the same will recursively be
    done with the child-nodes, first. In other words, all leaves of
    this node and its child nodes are collected in-order as direct
    children of this node.

    Applying flatten recursively will result in these kinds of
    structural transformation::

        (1 (+ 2) (+ 3))    ->   (1 + 2 + 3)
        (1 (+ (2 + (3))))  ->   (1 + 2 + 3)
    """
    node = context[-1]
    if node.children:
        new_result = []     # type: List[Node]
        context.append(ZOMBIE_NODE)
        for child in node.children:
            context[-1] = child
            if child.children and condition(context):
                if recursive:
                    flatten(context, condition, recursive)
                new_result.extend(child.children)
            else:
                new_result.append(child)
        context.pop()
        node.result = tuple(new_result)


def collapse(context: List[Node]):
    """
    Collapses all sub-nodes of a node by replacing them with the
    string representation of the node.
    """
    node = context[-1]
    node.result = node.content


# @transformation_factory
# def collect_leaves(context: List[Node], whitespace: str=''):
#     """
#     Collects all leave nodes dropping any intermediary nodes.
#     Optionally adds whitespace between the nodes.
#     """
#     assert context[-1].children
#     node = context[-1]
#     leaves_iterator = node.select(lambda nd: not nd.children, include_root=False)
#     if whitespace:
#         mock_ws_parser = MockParser('', WHITESPACE_PTYPE)
#         result = []
#         for leave in leaves_iterator:
#             result.append(leave)
#             result.append(Node(mock_ws_parser, whitespace, leafhint=True))
#         result.pop()
#         node.result = tuple(result)
#     else:
#         node.result = (nd for nd in leaves_iterator)


@transformation_factory(tuple)
def merge_children(context: List[Node], tag_names: Tuple[str]):
    """
    Joins all children next to each other and with particular tag-names
    into a single child node with a mock-parser with the name of the
    first tag-name in the list.
    """
    node = context[-1]
    result = []
    name, ptype = ('', tag_names[0]) if tag_names[0][:1] == ':' else (tag_names[0], '')
    if node.children:
        i = 0
        L = len(node.children)
        while i < L:
            while i < L and not node.children[i].tag_name in tag_names:
                result.append(node.children[i])
                i += 1
            k = i + 1
            while (k < L and node.children[k].tag_name in tag_names
                   and bool(node.children[i].children) == bool(node.children[k].children)):
                k += 1
            if i < L:
                result.append(Node(MockParser(name, ptype),
                                   reduce(lambda a, b: a + b,
                                          (node.children for node in node.children[i:k]))))
            i = k
        node.result = tuple(result)


@transformation_factory(collections.abc.Callable)
def replace_content(context: List[Node], func: Callable):  # Callable[[Node], ResultType]
    """Replaces the content of the node. ``func`` takes the node's result
    as an argument an returns the mapped result.
    """
    node = context[-1]
    node.result = func(node.result)


@transformation_factory  # (str)
def replace_content_by(context: List[Node], content: str):  # Callable[[Node], ResultType]
    """Replaces the content of the node with the given text content.
    """
    node = context[-1]
    node.result = content


#######################################################################
#
# destructive transformations:
#
# - leaves may be dropped (e.g. if deemed irrelevant)
# - errors of dropped leaves will be lost
# - no promise that order will be preserved
#
#######################################################################


@transformation_factory(collections.abc.Callable)
def lstrip(context: List[Node], condition: Callable = is_expendable):
    """Recursively removes all leading child-nodes that fulfill a given condition."""
    node = context[-1]
    i = 1
    while i > 0 and node.children:
        lstrip(context + [node.children[0]], condition)
        i, L = 0, len(node.children)
        while i < L and condition(context + [node.children[i]]):
            i += 1
        if i > 0:
            node.result = node.children[i:]


@transformation_factory(collections.abc.Callable)
def rstrip(context: List[Node], condition: Callable = is_expendable):
    """Recursively removes all leading nodes that fulfill a given condition."""
    node = context[-1]
    i, L = 0, len(node.children)
    while i < L and node.children:
        rstrip(context + [node.children[-1]], condition)
        L = len(node.children)
        i = L
        while i > 0 and condition(context + [node.children[i-1]]):
            i -= 1
        if i < L:
            node.result = node.children[:i]


@transformation_factory(collections.abc.Callable)
def strip(context: List[Node], condition: Callable = is_expendable):
    """Removes leading and trailing child-nodes that fulfill a given condition."""
    lstrip(context, condition)
    rstrip(context, condition)


@transformation_factory  # (slice)
def keep_children(context: List[Node], section: slice = slice(None)):
    """Keeps only child-nodes which fall into a slice of the result field."""
    node = context[-1]
    if node.children:
        node.result = node.children[section]


@transformation_factory(collections.abc.Callable)
def keep_children_if(context: List[Node], condition: Callable):
    """Removes all children for which `condition()` returns `True`."""
    node = context[-1]
    if node.children:
        node.result = tuple(c for c in node.children if condition(context + [c]))


@transformation_factory(collections.abc.Set)
def keep_tokens(context: List[Node], tokens: AbstractSet[str]=frozenset()):
    """Removes any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    keep_children_if(context, partial(is_token, tokens=tokens))


@transformation_factory(collections.abc.Set)
def keep_nodes(context: List[Node], tag_names: AbstractSet[str]):
    """Removes children by tag name."""
    keep_children_if(context, partial(is_one_of, tag_name_set=tag_names))


@transformation_factory
def keep_content(context: List[Node], regexp: str):
    """Removes children depending on their string value."""
    keep_children_if(context, partial(has_content, regexp=regexp))


@transformation_factory(collections.abc.Callable)
def remove_children_if(context: List[Node], condition: Callable):
    """Removes all children for which `condition()` returns `True`."""
    node = context[-1]
    if node.children:
        node.result = tuple(c for c in node.children if not condition(context + [c]))
    pass

# @transformation_factory(Callable)
# def remove_children(context: List[Node],
#                     condition: Callable = TRUE_CONDITION,
#                     section: slice = slice(None)):
#     """Removes all nodes from a slice of the result field if the function
#     `condition(child_node)` evaluates to `True`."""
#     node = context[-1]
#     if node.children:
#         c = node.children
#         N = len(c)
#         rng = range(*section.indices(N))
#         node.result = tuple(c[i] for i in range(N)
#                             if i not in rng or not condition(context + [c[i]]))
#         # selection = []
#         # for i in range(N):
#         #     context.append(c[i])
#         #     if not i in rng or not condition(context):
#         #         selection.append(c[i])
#         #     context.pop()
#         # if len(selection) != c:
#         #     node.result = tuple(selection)


remove_whitespace = remove_children_if(is_whitespace)
# partial(remove_children_if, condition=is_whitespace)
remove_empty = remove_children_if(is_empty)
remove_anonymous_empty = remove_children_if(lambda ctx: is_empty(ctx) and is_anonymous(ctx))
remove_expendables = remove_children_if(is_expendable)
# partial(remove_children_if, condition=is_expendable)
remove_anonymous_expendables = remove_children_if(lambda ctx: is_anonymous(ctx)
                                                  and is_expendable(ctx))
remove_anonymous_tokens = remove_children_if(lambda ctx: is_token(ctx) and is_anonymous(ctx))
# remove_first = apply_if(keep_children(slice(1, None)), lambda ctx: len(ctx[-1].children) > 1)
# remove_last = apply_if(keep_children(slice(None, -1)), lambda ctx: len(ctx[-1].children) > 1)
# remove_brackets = apply_if(keep_children(slice(1, -1)), lambda ctx: len(ctx[-1].children) >= 2)
remove_infix_operator = keep_children(slice(0, None, 2))
remove_single_child = apply_if(keep_children(slice(0)), lambda ctx: len(ctx[-1].children) == 1)


def remove_first(context: List[Node]):
    """Removes the first non-whitespace child."""
    node = context[-1]
    if node.children:
        for i, child in enumerate(node.children):
            if child.parser.ptype != WHITESPACE_PTYPE:
                break
        else:
            return
        node.result = node.children[:i] + node.children[i+1:]


def remove_last(context: List[Node]):
    """Removes the last non-whitespace child."""
    node = context[-1]
    if node.children:
        for i, child in enumerate(reversed(node.children)):
            if child.parser.ptype != WHITESPACE_PTYPE:
                break
        else:
            return
        i = len(node.children) - i - 1
        node.result = node.children[:i] + node.children[i+1:]


def remove_brackets(context: List[Node]):
    """Removes the first and the last non-whitespace child."""
    remove_first(context)
    remove_last(context)


@transformation_factory(collections.abc.Set)
def remove_tokens(context: List[Node], tokens: AbstractSet[str]=frozenset()):
    """Removes any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    remove_children_if(context, partial(is_token, tokens=tokens))


@transformation_factory(collections.abc.Set)
def remove_nodes(context: List[Node], tag_names: AbstractSet[str]):
    """Removes children by tag name."""
    remove_children_if(context, partial(is_one_of, tag_name_set=tag_names))


@transformation_factory
def remove_content(context: List[Node], regexp: str):
    """Removes children depending on their string value."""
    remove_children_if(context, partial(has_content, regexp=regexp))


########################################################################
#
# AST semantic validation functions (EXPERIMENTAL!!!)
#
########################################################################

@transformation_factory(collections.abc.Callable)
def error_on(context: List[Node], condition: Callable, error_msg: str = ''):
    """
    Checks for `condition`; adds an error message if condition is not met.
    """
    node = context[-1]
    if not condition(context):
        if error_msg:
            node.add_error(error_msg % node.tag_name if error_msg.find("%s") > 0 else error_msg)
        else:
            cond_name = condition.__name__ if hasattr(condition, '__name__') \
                        else condition.__class__.__name__ if hasattr(condition, '__class__') \
                        else '<unknown>'
            node.add_error("transform.error_on: Failed to meet condition " + cond_name)


@transformation_factory(collections.abc.Callable)
def warn_on(context: List[Node], condition: Callable, warning: str = ''):
    """
    Checks for `condition`; adds an warning message if condition is not met.
    """
    node = context[-1]
    if not condition(context):
        if warning:
            node.add_error(warning % node.tag_name if warning.find("%s") > 0 else warning,
                           Error.WARNING)
        else:
            cond_name = condition.__name__ if hasattr(condition, '__name__') \
                        else condition.__class__.__name__ if hasattr(condition, '__class__') \
                        else '<unknown>'
            node.add_error("transform.warn_on: Failed to meet condition " + cond_name,
                           Error.WARNING)


assert_has_children = error_on(lambda nd: nd.children, 'Element "%s" has no children')


@transformation_factory
def assert_content(context: List[Node], regexp: str):
    node = context[-1]
    if not has_content(context, regexp):
        context[0].new_error(node, 'Element "%s" violates %s on %s' %
                             (node.parser.name, str(regexp), node.content))


@transformation_factory(collections.abc.Set)
def require(context: List[Node], child_tags: AbstractSet[str]):
    node = context[-1]
    for child in node.children:
        if child.tag_name not in child_tags:
            context[0].new_error(node, 'Element "%s" is not allowed inside "%s".' %
                                 (child.parser.name, node.parser.name))


@transformation_factory(collections.abc.Set)
def forbid(context: List[Node], child_tags: AbstractSet[str]):
    node = context[-1]
    for child in node.children:
        if child.tag_name in child_tags:
            context[0].new_error(node, 'Element "%s" cannot be nested inside "%s".' %
                                 (child.parser.name, node.parser.name))
