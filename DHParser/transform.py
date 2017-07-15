"""transformation.py - transformation functions for converting the
                       concrete into the abstract syntax tree

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import inspect
from functools import partial, reduce, singledispatch

from DHParser.syntaxtree import WHITESPACE_PTYPE, TOKEN_PTYPE, MockParser, Node

try:
    import regex as re
except ImportError:
    import re
try:
    from typing import AbstractSet, Any, ByteString, Callable, cast, Container, Dict, \
        Iterator, List, NamedTuple, Sequence, Union, Text, Tuple
except ImportError:
    from .typing34 import AbstractSet, Any, ByteString, Callable, cast, Container, Dict, \
        Iterator, List, NamedTuple, Sequence, Union, Text, Tuple

from DHParser.toolkit import expand_table, smart_list

__all__ = ('transformation_factory',
           'key_parser_name',
           'key_tag_name',
           'traverse',
           'replace_by_single_child',
           'reduce_single_child',
           'replace_parser',
           'collapse',
           'join',
           'replace_content',
           'apply_if',
           'is_whitespace',
           'is_empty',
           'is_expendable',
           'is_token',
           'has_name',
           'has_content',
           'remove_parser',
           'remove_content',
           'remove_first',
           'remove_last',
           'remove_whitespace',
           'remove_empty',
           'remove_expendables',
           'remove_brackets',
           'remove_tokens',
           'flatten',
           'forbid',
           'require',
           'assert_content')


def transformation_factory(t=None):
    """Creates factory functions from transformation-functions that
    dispatch on the first parameter after the node parameter.

    Decorating a transformation-function that has more than merely the
    ``node``-parameter with ``transformation_factory`` creates a
    function with the same name, which returns a partial-function that
    takes just the node-parameter.

    Additionally, there is some some syntactic sugar for
    transformation-functions that receive a collection as their second
    parameter and do not have any further parameters. In this case a
    list of parameters passed to the factory function will be converted
    into a collection.

    Main benefit is readability of processing tables.

    Usage:
        @transformation_factory(AbtractSet[str])
        def remove_tokens(node, tokens):
            ...
      or, alternatively:
        @transformation_factory
        def remove_tokens(node, tokens: AbstractSet[str]):
            ...

    Example:
        trans_table = { 'expression': remove_tokens('+', '-') }
      instead of:
        trans_table = { 'expression': partial(remove_tokens, tokens={'+', '-'}) }
    """

    def decorator(f):
        sig = inspect.signature(f)
        params = list(sig.parameters.values())[1:]
        if len(params) == 0:
            return f  # '@transformer' not needed w/o free parameters
        assert t or params[0].annotation != params[0].empty, \
            "No type information on second parameter found! Please, use type " \
            "annotation or provide the type information via transfomer-decorator."
        p1type = t or params[0].annotation
        f = singledispatch(f)
        if len(params) == 1 and issubclass(p1type, Container) and not issubclass(p1type, Text) \
                and not issubclass(p1type, ByteString):
            def gen_special(*args):
                c = set(args) if issubclass(p1type, AbstractSet) else \
                    list(args) if issubclass(p1type, Sequence) else args
                d = {params[0].name: c}
                return partial(f, **d)

            f.register(p1type.__args__[0], gen_special)

        def gen_partial(*args, **kwargs):
            d = {p.name: arg for p, arg in zip(params, args)}
            d.update(kwargs)
            return partial(f, **d)

        f.register(p1type, gen_partial)
        return f

    if isinstance(t, type(lambda: 1)):
        # Provide for the case that transformation_factory has been
        # written as plain decorator and not as a function call that
        # returns the decorator proper.
        func = t;
        t = None
        return decorator(func)
    else:
        return decorator


def key_parser_name(node) -> str:
    return node.parser.name


def key_tag_name(node) -> str:
    return node.tag_name


def traverse(root_node, processing_table, key_func=key_tag_name) -> None:
    """Traverses the snytax tree starting with the given ``node`` depth
    first and applies the sequences of callback-functions registered
    in the ``calltable``-dictionary.

    The most important use case is the transformation of a concrete
    syntax tree into an abstract tree (AST). But it is also imaginable
    to employ tree-traversal for the semantic analysis of the AST.

    In order to assign sequences of callback-functions to nodes, a
    dictionary ("processing table") is used. The keys usually represent
    tag names, but any other key function is possible. There exist
    three special keys:
        '+': always called (before any other processing function)
        '*': called for those nodes for which no (other) processing
             function appears in the table
        '~': always called (after any other processing function)

    Args:
        root_node (Node): The root-node of the syntax tree to be traversed
        processing_table (dict): node key -> sequence of functions that
            will be applied to matching nodes in order. This dictionary
            is interpreted as a ``compact_table``. See
            ``toolkit.expand_table`` or ``EBNFCompiler.EBNFTransTable``
        key_func (function): A mapping key_func(node) -> keystr. The default
            key_func yields node.parser.name.

    Example:
        table = { "term": [replace_by_single_child, flatten],
            "factor, flowmarker, retrieveop": replace_by_single_child }
        traverse(node, table)
    """
    # commented, because this approach is too error prone!
    # def funclist(call):
    #     return [as_partial(func) for func in smart_list(call)]

    # normalize processing_table entries by turning single values into lists
    # with a single value
    table = {name: smart_list(call) for name, call in list(processing_table.items())}
    table = expand_table(table)
    cache = {}  # type: Dict[str, List[Callable]]

    def traverse_recursive(node):
        if node.children:
            for child in node.result:
                traverse_recursive(child)  # depth first
                node.error_flag |= child.error_flag  # propagate error flag

        key = key_func(node)
        sequence = cache.get(key, None)
        if sequence is None:
            sequence = table.get('+', []) + \
                       table.get(key, table.get('*', [])) + \
                       table.get('~', [])
            # '+' always called (before any other processing function)
            # '*' called for those nodes for which no (other) processing function
            #     appears in the table
            # '~' always called (after any other processing function)
            cache[key] = sequence

        for call in sequence:
            call(node)

    traverse_recursive(root_node)


# ------------------------------------------------
#
# rearranging transformations:
#     - tree may be rearranged (e.g.flattened)
#     - nodes that are not leaves may be dropped
#     - order is preserved
#     - leave content is preserved (though not necessarily the leaves themselves)
#
# ------------------------------------------------


def replace_by_single_child(node):
    """Remove single branch node, replacing it by its immediate descendant.
    (In case the descendant's name is empty (i.e. anonymous) the
    name of this node's parser is kept.)
    """
    if node.children and len(node.result) == 1:
        if not node.result[0].parser.name:
            node.result[0].parser.name = node.parser.name
        node.parser = node.result[0].parser
        node._errors.extend(node.result[0].errors)
        node.result = node.result[0].result


def reduce_single_child(node):
    """Reduce a single branch node, by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    """
    if node.children and len(node.result) == 1:
        node._errors.extend(node.result[0].errors)
        node.result = node.result[0].result


@transformation_factory
def replace_parser(node, name: str):
    """Replaces the parser of a Node with a mock parser with the given
    name.

    Parameters:
        name(str): "NAME:PTYPE" of the surogate. The ptype is optional
        node(Node): The node where the parser shall be replaced
    """
    name, ptype = (name.split(':') + [''])[:2]
    node.parser = MockParser(name, ptype)


@transformation_factory(Callable)
def flatten(node, condition=lambda node: not node.parser.name, recursive=True):
    """Flattens all children, that fulfil the given `condition`
    (default: all unnamed children). Flattening means that wherever a
    node has child nodes, the child nodes are inserted in place of the
    node.
     If the parameter `recursive` is `True` the same will recursively be
    done with the child-nodes, first. In other words, all leaves of
    this node and its child nodes are collected in-order as direct
    children of this node.
     Applying flatten recursively will result in these kinds of
    structural transformation:
        (1 (+ 2) (+ 3)     ->   (1 + 2 + 3)
        (1 (+ (2 + (3))))  ->   (1 + 2 + 3)
    """
    if node.children:
        new_result = []
        for child in node.children:
            if child.children and condition(child):
                if recursive:
                    flatten(child, condition, recursive)
                new_result.extend(child.children)
            else:
                new_result.append(child)
        node.result = tuple(new_result)


def collapse(node):
    """Collapses all sub-nodes by replacing the node's result with it's
    string representation.
    """
    node.result = str(node)


@transformation_factory
def join(node, tag_names: List[str]):
    """Joins all children next to each other and with particular tag-
    names into a single child node with mock parser 'parser_name'.
    """
    result = []
    name, ptype = (tag_names[0].split(':') + [''])[:2]
    if node.children:
        i = 0;
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
                                   reduce(lambda a, b: a + b, (node.result for node in node.children[i:k]))))
            i = k
        node.result = tuple(result)


# ------------------------------------------------
#
# destructive transformations:
#     - tree may be rearranged (flattened),
#     - order is preserved
#     - but (irrelevant) leaves may be dropped
#     - errors of dropped leaves will be lost
#
# ------------------------------------------------


@transformation_factory
def replace_content(node, func: Callable):  # Callable[[Node], ResultType]
    """Replaces the content of the node. ``func`` takes the node
    as an argument an returns the mapped result.
    """
    node.result = func(node.result)


def is_whitespace(node):
    """Removes whitespace and comments defined with the
    ``@comment``-directive."""
    return node.parser.ptype == WHITESPACE_PTYPE


def is_empty(node):
    return not node.result


def is_expendable(node):
    return is_empty(node) or is_whitespace(node)


def is_token(node, tokens: AbstractSet[str] = frozenset()) -> bool:
    return node.parser.ptype == TOKEN_PTYPE and (not tokens or node.result in tokens)


@transformation_factory
def has_name(node, tag_names: AbstractSet[str]) -> bool:
    """Checks if node has any of a given set of `tag names`.
    See property `Node.tagname`."""
    return node.tag_name in tag_names


@transformation_factory
def has_content(node, contents: AbstractSet[str]) -> bool:
    """Checks if the node's content (i.e. `str(node)`) matches any of
    a given set of strings."""
    return str(node) in contents


@transformation_factory
def apply_if(node, transformation: Callable, condition: Callable):
    """Applies a transformation only if a certain condition is met.
    """
    if condition(node):
        transformation(node)


@transformation_factory
def keep_children(node, section: slice = slice(None, None, None), condition=lambda node: True):
    """Keeps only the nodes which fall into a slice of the result field
    and for which the function `condition(child_node)` evaluates to
    `True`."""
    if node.children:
        node.result = tuple(c for c in node.children[section] if condition(c))


@transformation_factory(Callable)
def remove_children_if(node, condition):
    """Removes all nodes from a slice of the result field if the function
    ``condition(child_node)`` evaluates to ``True``."""
    if node.children:
        node.result = tuple(c for c in node.children if not condition(c))


remove_whitespace = remove_children_if(is_whitespace)  # partial(remove_children_if, condition=is_whitespace)
remove_empty = remove_children_if(is_empty)
remove_expendables = remove_children_if(is_expendable)  # partial(remove_children_if, condition=is_expendable)
remove_brackets = keep_children(slice(1, -1))


@transformation_factory(Callable)
def remove_first(node, condition=lambda node: True):
    """Removes the first child if the condition is met.
    Otherwise does nothing."""
    if node.children:
        if condition(node.children[0]):
            node.result = node.result[1:]


@transformation_factory(Callable)
def remove_last(node, condition=lambda node: True):
    """Removes the last child if the condition is met.
    Otherwise does nothing."""
    if node.children:
        if condition(node.children[-1]):
            node.result = node.result[:-1]


@transformation_factory
def remove_tokens(node, tokens: AbstractSet[str] = frozenset()):
    """Reomoves any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    remove_children_if(node, partial(is_token, tokens=tokens))


@transformation_factory
def remove_parser(node, tag_names: AbstractSet[str]):
    """Removes children by 'tag name'."""
    remove_children_if(node, partial(has_name, tag_names=tag_names))


@transformation_factory
def remove_content(node, contents: AbstractSet[str]):
    """Removes children depending on their string value."""
    remove_children_if(node, partial(has_content, contents=contents))


########################################################################
#
# AST semantic validation functions
# EXPERIMENTAL!
#
########################################################################


@transformation_factory
def require(node, child_tags: AbstractSet[str]):
    for child in node.children:
        if child.tag_name not in child_tags:
            node.add_error('Element "%s" is not allowed inside "%s".' %
                           (child.parser.name, node.parser.name))


@transformation_factory
def forbid(node, child_tags: AbstractSet[str]):
    for child in node.children:
        if child.tag_name in child_tags:
            node.add_error('Element "%s" cannot be nested inside "%s".' %
                           (child.parser.name, node.parser.name))


@transformation_factory
def assert_content(node, regex: str):
    content = str(node)
    if not re.match(regex, content):
        node.add_error('Element "%s" violates %s on %s' %
                       (node.parser.name, str(regex), content))
