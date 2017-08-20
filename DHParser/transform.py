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

__all__ = ('TransformationDict',
           'TransformationProc',
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
           'apply_if',
           'is_anonymous',
           'is_whitespace',
           'is_empty',
           'is_expendable',
           'is_token',
           'is_one_of',
           'has_content',
           'remove_children_if',
           'remove_parser',
           'remove_content',
           'remove_first',
           'remove_last',
           'remove_whitespace',
           'remove_empty',
           'remove_expendables',
           'remove_brackets',
           'remove_infix_operator',
           'remove_single_child',
           'remove_tokens',
           'keep_children',
           'flatten',
           'forbid',
           'require',
           'assert_content',
           'assert_condition',
           'assert_has_children',
           'TRUE_CONDITION')


TransformationProc = Callable[[List[Node]], None]
TransformationDict = Dict
ConditionFunc = Callable  # Callable[[List[Node]], bool]
KeyFunc = Callable[[Node], str]


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
        def remove_tokens(context, tokens):
            ...
      or, alternatively:
        @transformation_factory
        def remove_tokens(context, tokens: AbstractSet[str]):
            ...

    Example:
        trans_table = { 'expression': remove_tokens('+', '-') }
      instead of:
        trans_table = { 'expression': partial(remove_tokens, tokens={'+', '-'}) }

    Parameters:
        t:  type of the second argument of the transformation function,
            only necessary if the transformation functions' parameter list
            does not have type annotations.
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
        func = t
        t = None
        return decorator(func)
    else:
        return decorator


def key_parser_name(node: Node) -> str:
    return node.parser.name


def key_tag_name(node: Node) -> str:
    return node.tag_name


def traverse(root_node: Node,
             processing_table: Dict[str, List[Callable]],
             key_func: KeyFunc=key_tag_name) -> None:
    """
    Traverses the snytax tree starting with the given ``node`` depth
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
            is interpreted as a `compact_table`. See
            `toolkit.expand_table` or ``EBNFCompiler.EBNFTransTable`
        key_func (function): A mapping key_func(node) -> keystr. The default
            key_func yields node.parser.name.

    Example:
        table = { "term": [replace_by_single_child, flatten],
            "factor, flowmarker, retrieveop": replace_by_single_child }
        traverse(node, table)
    """
    # Is this optimazation really needed?
    if '__cache__' in processing_table:
        # assume that processing table has already been expanded
        table = processing_table
        cache = processing_table['__cache__']
    else:
        # normalize processing_table entries by turning single values into lists
        # with a single value
        table = {name: smart_list(call) for name, call in list(processing_table.items())}
        table = expand_table(table)
        cache = table.setdefault('__cache__', {})  # type: Dict[str, List[Callable]]
        # change processing table in place, so that table expansion does not get lost
        # between calls
        processing_table.clear();
        processing_table.update(table)

    # assert '__cache__' in processing_table
    # # Code without optimization
    # table = {name: smart_list(call) for name, call in list(processing_table.items())}
    # table = expand_table(table)
    # cache = {}  # type: Dict[str, List[Callable]]

    def traverse_recursive(context):
        node = context[-1]
        if node.children:
            for child in node.result:
                context.append(child)
                traverse_recursive(context)  # depth first
                node.error_flag = node.error_flag or child.error_flag  # propagate error flag
                context.pop()

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
            call(context)

    traverse_recursive([root_node])
    # assert processing_table['__cache__']



# ------------------------------------------------
#
# rearranging transformations:
#     - tree may be rearranged (e.g.flattened)
#     - nodes that are not leaves may be dropped
#     - order is preserved
#     - leave content is preserved (though not necessarily the leaves themselves)
#
# ------------------------------------------------


def TRUE_CONDITION(context: List[Node]) -> bool:
    return True


def replace_child(node: Node):
    assert len(node.children) == 1
    if not node.children[0].parser.name:
        node.children[0].parser.name = node.parser.name
    node.parser = node.children[0].parser
    node._errors.extend(node.children[0]._errors)
    node.result = node.result[0].result


def reduce_child(node: Node):
    assert len(node.children) == 1
    node._errors.extend(node.children[0]._errors)
    node.result = node.result[0].result


@transformation_factory(Callable)
def replace_by_single_child(context: List[Node], condition: Callable=TRUE_CONDITION):
    """
    Remove single branch node, replacing it by its immediate descendant
    if and only if the condision on the descendant is true.
    (In case the descendant's name is empty (i.e. anonymous) the
    name of this node's parser is kept.)
    """
    node = context[-1]
    if len(node.children) == 1:
        context.append(node.children[0])
        if  condition(context):
            replace_child(node)
        context.pop()


@transformation_factory(Callable)
def reduce_single_child(context: List[Node], condition: Callable=TRUE_CONDITION):
    """
    Reduce a single branch node, by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    If the condition evaluates to false on the descendant, it will not
    be reduced.
    """
    node = context[-1]
    if len(node.children) == 1:
        context.append(node.children[0])
        if condition(context):
            reduce_child(node)
        context.pop()


def is_named(context: List[Node]) -> bool:
    return context[-1].parser.name


def is_anonymous(context: List[Node]) -> bool:
    return not context[-1].parser.name


@transformation_factory(Callable)
def replace_or_reduce(context: List[Node], condition: Callable=is_named):
    """
    Replaces node by a single child, if condition is met on child,
    otherwise (i.e. if the child is anonymous) reduces the child.
    """
    node = context[-1]
    if len(node.children) == 1:
        context.append(node.children[0])
        if condition(context):
            replace_child(node)
        else:
            reduce_child(node)
        context.pop()


@transformation_factory
def replace_parser(context: List[Node], name: str):
    """
    Replaces the parser of a Node with a mock parser with the given
    name.

    Parameters:
        name(str): "NAME:PTYPE" of the surogate. The ptype is optional
        node(Node): The node where the parser shall be replaced
    """
    node = context[-1]
    name, ptype = (name.split(':') + [''])[:2]
    node.parser = MockParser(name, ptype)


@transformation_factory(Callable)
def flatten(context: List[Node], condition: Callable=is_anonymous, recursive: bool=True):
    """
    Flattens all children, that fulfil the given `condition`
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
    node = context[-1]
    if node.children:
        new_result = []
        for child in node.children:
            context.append(child)
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
    node.result = str(node)


@transformation_factory
def merge_children(context: List[Node], tag_names: List[str]):
    """
    Joins all children next to each other and with particular tag-
    names into a single child node with a mock-parser with the name of
    the first tag-name in the list.
    """
    node = context
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
def replace_content(context: List[Node], func: Callable):  # Callable[[Node], ResultType]
    """Replaces the content of the node. ``func`` takes the node
    as an argument an returns the mapped result.
    """
    node = context[-1]
    node.result = func(node.result)


def is_whitespace(context: List[Node]) -> bool:
    """Removes whitespace and comments defined with the
    ``@comment``-directive."""
    return context[-1].parser.ptype == WHITESPACE_PTYPE


def is_empty(context: List[Node]) -> bool:
    return not context[-1].result


def is_expendable(context: List[Node]) -> bool:
    return is_empty(context) or is_whitespace(context)


def is_token(context: List[Node], tokens: AbstractSet[str] = frozenset()) -> bool:
    node = context[-1]
    return node.parser.ptype == TOKEN_PTYPE and (not tokens or node.result in tokens)


def is_one_of(context: List[Node], tag_name_set: AbstractSet[str]) -> bool:
    """Returns true, if the node's tag_name is on of the
    given tag names."""
    return context[-1].tag_name in tag_name_set


def has_content(context: List[Node], regexp: str) -> bool:
    """Checks a node's content against a regular expression."""
    return bool(re.match(regexp, str(context[-1])))


@transformation_factory(Callable)
def apply_if(context: List[Node], transformation: Callable, condition: Callable):
    """Applies a transformation only if a certain condition is met."""
    node = context[-1]
    if condition(node):
        transformation(context)


@transformation_factory(slice)
def keep_children(context: List[Node], section: slice = slice(None)):
    """Keeps only child-nodes which fall into a slice of the result field."""
    node = context[-1]
    if node.children:
        node.result = node.children[section]


@transformation_factory(Callable)
def remove_children_if(context: List[Node], condition: Callable, section: slice = slice(None)):
    """Removes all nodes from a slice of the result field if the function
    `condition(child_node)` evaluates to `True`."""
    node = context[-1]
    if node.children:
        c = node.children
        N = len(c)
        rng = range(*section.indices(N))
        node.result = tuple(c[i] for i in range(N)
                            if not i in rng or not condition(context + [c[i]]))
        # selection = []
        # for i in range(N):
        #     context.append(c[i])
        #     if not i in rng or not condition(context):
        #         selection.append(c[i])
        #     context.pop()
        # if len(selection) != c:
        #     node.result = tuple(selection)


remove_whitespace = remove_children_if(is_whitespace)  # partial(remove_children_if, condition=is_whitespace)
remove_empty = remove_children_if(is_empty)
remove_expendables = remove_children_if(is_expendable)  # partial(remove_children_if, condition=is_expendable)
remove_first = apply_if(keep_children(slice(1, None)), lambda nd: len(nd.children) > 1)
remove_last = apply_if(keep_children(slice(None, -1)), lambda nd: len(nd.children) > 1)
remove_brackets = apply_if(keep_children(slice(1, -1)), lambda nd: len(nd.children) >= 2)
remove_infix_operator = keep_children(slice(0, None, 2))
remove_single_child = apply_if(keep_children(slice(0)), lambda nd: len(nd.children) == 1)


@transformation_factory
def remove_tokens(context: List[Node], tokens: AbstractSet[str] = frozenset()):
    """Reomoves any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    remove_children_if(context, partial(is_token, tokens=tokens))


@transformation_factory
def remove_parser(context: List[Node], tag_names: AbstractSet[str]):
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

@transformation_factory(Callable)
def assert_condition(context: List[Node], condition: Callable, error_msg: str = '') -> bool:
    """Checks for `condition`; adds an error message if condition is not met."""
    node = context[-1]
    if not condition(context):
        if error_msg:
            node.add_error(error_msg % node.tag_name if error_msg.find("%s") > 0 else error_msg)
        else:
            cond_name = condition.__name__ if hasattr(condition, '__name__') \
                        else condition.__class__.__name__ if hasattr(condition, '__class__') \
                        else '<unknown>'
            node.add_error("transform.assert_condition: Failed to meet condition " + cond_name)


assert_has_children = assert_condition(lambda nd: nd.children, 'Element "%s" has no children')


@transformation_factory
def assert_content(context: List[Node], regexp: str):
    node = context[-1]
    if not has_content(context, regexp):
        node.add_error('Element "%s" violates %s on %s' %
                       (node.parser.name, str(regexp), str(node)))


@transformation_factory
def require(context: List[Node], child_tags: AbstractSet[str]):
    node = context[-1]
    for child in node.children:
        if child.tag_name not in child_tags:
            node.add_error('Element "%s" is not allowed inside "%s".' %
                           (child.parser.name, node.parser.name))


@transformation_factory
def forbid(context: List[Node], child_tags: AbstractSet[str]):
    node = context[-1]
    for child in node.children:
        if child.tag_name in child_tags:
            node.add_error('Element "%s" cannot be nested inside "%s".' %
                           (child.parser.name, node.parser.name))
