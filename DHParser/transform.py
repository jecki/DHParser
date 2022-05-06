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
from functools import partial, singledispatch, reduce
import inspect
import operator
from typing import AbstractSet, ByteString, Callable, cast, Container, Dict, \
    Tuple, List, Sequence, Union, Text

try:
    import cython
except ImportError:
    import DHParser.externallibs.shadow_cython as cython

from DHParser.error import ErrorCode, AST_TRANSFORM_CRASH, ERROR
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, LEAF_PTYPES, PLACEHOLDER, \
    RootNode, parse_sxpr, flatten_sxpr, TreeContext
from DHParser.toolkit import issubtype, isgenerictype, expand_table, smart_list, re, \
    deprecation_warning


__all__ = ('TransformationDict',
           'TransformationProc',
           'TransformationTableType',
           'ConditionFunc',
           'KeyFunc',
           'TransformerCallable',
           'transformation_factory',
           'key_node_name',
           'Filter',
           'BLOCK_LEAVES',
           'BLOCK_ANONYMOUS_LEAVES',
           'BLOCK_CHILDREN',
           'traverse',
           'merge_treetops',
           'always',
           'never',
           'neg',
           'any_of',
           'all_of',
           'is_named',
           'update_attr',
           'swap_attributes',
           'replace_by_single_child',
           'replace_by_children',
           'reduce_single_child',
           'replace_or_reduce',
           'change_name',
           'change_tag_name',
           'replace_child_names',
           'replace_tag_names',
           'collapse',
           'join_content',
           'pick_longest_content',
           'fix_content',
           'collapse_children_if',
           'transform_content',
           'replace_content_with',
           'add_attributes',
           'normalize_whitespace',
           'merge_adjacent',
           'merge_leaves',
           'merge_connected',
           'merge_results',
           'move_fringes',
           'left_associative',
           'lean_left',
           'apply_if',
           'apply_unless',
           'apply_ifelse',
           'traverse_locally',
           'is_anonymous',
           'is_anonymous_leaf',
           'contains_only_whitespace',
           # 'is_any_kind_of_whitespace',
           'is_empty',
           'is_token',
           'is_one_of',
           'not_one_of',
           'matches_re',
           'has_attr',
           'attr_equals',
           'has_content',
           'has_ancestor',
           'has_parent',
           'has_descendant',
           'has_child',
           'has_children',
           'has_sibling',
           'lstrip',
           'rstrip',
           'strip',
           'keep_children',
           'keep_children_if',
           'keep_tokens',
           'keep_nodes',
           'keep_content',
           'remove_children_if',
           'remove_children',
           'remove_content',
           # 'remove_first',
           # 'remove_last',
           'remove_whitespace',
           'remove_empty',
           'remove_anonymous_empty',
           'remove_anonymous_tokens',
           'remove_brackets',
           'remove_infix_operator',
           'remove_tokens',
           'remove_if',
           'flatten',
           'forbid',
           'require',
           'assert_content',
           'AT_THE_END',
           'node_maker',
           'delimit_children',
           'positions_of',
           'PositionType',
           'normalize_position_representation',
           'insert',
           'add_error',
           'error_on',
           'assert_has_children',
           'peek')


class Filter:
    def __call__(self, children: Tuple[Node, ...]) -> Tuple[Node, ...]:
        raise NotImplementedError


TransformationProc = Callable[[TreeContext], None]
TransformationDict = Dict[str, Union[Callable, Sequence[Callable]]]
TransformationCache = Dict[str, Tuple[Sequence[Filter], Sequence[Callable]]]
TransformationTableType = Dict[str, Union[Sequence[Callable], TransformationDict]]
ConditionFunc = Callable  # Callable[[TreeContext], bool]
KeyFunc = Callable[[Node], str]
CriteriaType = Union[int, str, Callable]
TransformerCallable = Union[Callable[[RootNode], RootNode], partial]


def transformation_factory(t1=None, t2=None, t3=None, t4=None, t5=None):
    """
    Creates factory functions from transformation-functions that
    dispatch on the first parameter after the context parameter.

    Decorating a transformation-function that has more than merely the
    ``context``-parameter with ``transformation_factory`` creates a
    function with the same name, which returns a partial-function that
    takes just the context-parameter.

    Additionally, there is some syntactic sugar for
    transformation-functions that receive a collection as their second
    parameter and do not have any further parameters. In this case a
    list of parameters passed to the factory function will be converted
    into a single collection-parameter.

    The primary benefit is the readability of the transformation-tables.

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
        for the type of the canonical first parameter "TreeContext of
        transformation functions. Returns `t`."""
        # if isinstance(t, GenericMeta):
        #     raise TypeError("Generic Type %s not permitted\n in transformation_factory "
        #                     "decorator. Use the equivalent non-generic type instead!"
        #                     % str(t))
        if isinstance(t, str):          # ensure compatibility with python versions
            t = eval(t.replace('unicode', 'str'))  # with alternative type handling.
        if isgenerictype(t):
            raise TypeError("Generic Type %s not permitted\n in transformation_factory "
                            "decorator. Use the equivalent non-generic type instead!"
                            % str(t))
        if issubtype(TreeContext, t):
            raise TypeError("Sequence type %s not permitted\nin transformation_factory "
                            "decorator, because it could be mistaken for a base class "
                            "of TreeContext\nwhich is the type of the canonical first "
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
        elif issubtype(p1type, type_guard(t1)):
            try:
                if len(params) == 1 and issubtype(p1type, Container) \
                        and not (issubtype(p1type, Text) or issubtype(p1type, ByteString)):
                    def gen_special(*args):
                        c = set(args) if issubtype(p1type, AbstractSet) else \
                            tuple(args) if issubtype(p1type, Sequence) else args
                        d = {params[0].name: c}
                        return partial(f, **d)
                    assert p1type.__args__ is not None, "Please use more specific container " \
                        "type, e.g. %s[Callable] instead of %s, in signature of function " \
                        "%s !" % (str(p1type), str(p1type), f.__name__)
                    for alt_t in p1type.__args__:
                        f.register(type_guard(alt_t), gen_special)
                    # f.register(type_guard(p1type.__args__[0]), gen_special)
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


def key_node_name(node: Node) -> str:
    """
    Returns the tag name of the node as key for selecting transformations
    from the transformation table in function `traverse`.
    """
    return node.name


class BlockChildren(Filter):
    def __call__(self, children: Tuple[Node, ...]) -> Tuple[Node, ...]:
        return ()


class BlockLeaves(Filter):
    def __call__(self, children: Tuple[Node, ...]) -> Tuple[Node, ...]:
        return tuple(child for child in children if child._children)


class BlockAnonymousLeaves(Filter):
    def __call__(self, children: Tuple[Node, ...]) -> Tuple[Node, ...]:
        try:
            return tuple(child for child in children
                         if child._children or not child.name[0] == ':')
        except IndexError:
            return tuple(child for child in children
                         if child._children or not child.anonymous)


BLOCK_CHILDREN = BlockChildren()
BLOCK_LEAVES = BlockLeaves()
BLOCK_ANONYMOUS_LEAVES = BlockAnonymousLeaves()


def traverse(root_node: Node,
             transformation_table: TransformationTableType,
             key_func: KeyFunc = key_node_name) -> Node:
    """
    Traverses the syntax tree starting with the given ``node`` depth
    first and applies the sequences of callback-functions registered
    in the ``transformation_table``-dictionary.

    The most important use case is the transformation of a concrete
    syntax tree into an abstract tree (AST). But it is also imaginable
    to employ tree-traversal for the semantic analysis of the AST.

    In order to assign sequences of callback-functions to nodes, a
    dictionary ("processing table") is used. The keys usually represent
    tag names, but any other key function is possible. There exist
    three special keys:

    - '<': always called (before any other processing function)
    - '*': called for those nodes for which no (other) processing
      function appears in the table
    - '>': always called (after any other processing function)

    Args:
        root_node (Node): The root-node of the syntax tree to be traversed
        transformation_table (dict): node key -> sequence of functions that
            will be applied to matching nodes in order. This dictionary
            is interpreted as a ``compact_table``. See
            :func:`expand_table` or :func:`EBNFCompiler.EBNFTransTable`
        key_func (function): A mapping key_func(node) -> keystr. The default
            key_func yields node.name.

    Example::

        table = { "term": [replace_by_single_child, flatten],
                  "factor, flowmarker, retrieveop": replace_by_single_child }
        traverse(node, table)

    """

    # Is this optimization really needed?
    if '__cache__' in transformation_table:
        # assume that processing table has already been expanded
        table = transformation_table               # type: TransformationTableType
        cache = cast(TransformationDict, transformation_table['__cache__'])  # type: TransformationDict
    else:
        # normalize transformation_table entries by turning single values
        # into lists with a single value
        table = {name: cast(Sequence[Callable], smart_list(call))
                 for name, call in list(transformation_table.items())}
        table = expand_table(table)
        # substitute key for insiginificant whitespace
        assert '+' not in table, 'Symbol "+" in processing table is obsolete, use "<" instead'
        if '~' in table:
            if ':Whitespace' in table:
                raise AssertionError(
                    '"~" is a synonym for ":Whitespace" in the processing table. '
                    'To avoid confusion, choose either of the two, but do not use '
                    'both at the same time!')
            whitespace_transformation = table['~']
            del table['~']
            table[':Whitespace'] = whitespace_transformation
        # cache expanded table
        cache = cast(TransformationDict,
                     table.setdefault('__cache__', cast(TransformationDict, dict())))
        # change processing table in place, so its already expanded and cache filled next time
        transformation_table.clear()
        transformation_table.update(table)

    def split_filter(callables: Sequence[Callable]) -> Tuple[List[Filter], List[Callable]]:
        i = 0
        filter = []
        for callable in callables:
            if isinstance(callable, Filter):
                filter.append(callable)
                i += 1
            else:  break
        callables = list(callables[i:])
        assert not any(isinstance(callable, Filter) for callable in callables)
        return filter, callables

    def traverse_recursive(context):
        nonlocal cache
        node = context[-1]

        key = key_func(node)
        try:
            filters, sequence = cache[key]
        except KeyError:
            filters, pre = split_filter(table.get('<', []))
            assert BLOCK_CHILDREN not in filters
            more_filters, main = split_filter(table.get(key, table.get('*', [])))
            post = table.get('>', [])
            assert not any(isinstance(callable, Filter) for callable in post)
            sequence = pre + main + post
            all_filters = filters + more_filters
            if BLOCK_CHILDREN in all_filters:
                all_filters = [BLOCK_CHILDREN]
            cache[key] = (all_filters, sequence)

        children = node._children
        for filter in filters:
            children = filter(children)
        if children:
            context.append(PLACEHOLDER)
            for child in children:
                context[-1] = child
                traverse_recursive(context)  # depth first
            context.pop()

        for call in sequence:
            try:
                call(context)
            except Exception as ae:
                raise AssertionError('An exception occurred when transforming "%s" with %s:\n%s'
                                     % (key, str(call), ae.__class__.__name__ + ': ' + str(ae)))

    traverse_recursive([root_node])
    return root_node
    # assert transformation_table['__cache__']


#######################################################################
#
# specialized full tree transformations
#
#######################################################################

def merge_treetops(node: Node):
    """Recursively traverses the tree and "merges" nodes that contain
    only anonymous child nodes that are leaves. "mergeing" here means the
    node's result will be replaced by the merged content of the children.
    """
    if node._children:
        crunch = True
        for child in node._children:
            if child._children:
                merge_treetops(child)
                crunch = False
            elif not child.anonymous:
                crunch = False
        if crunch:
            node.result = node.content


#######################################################################
#
# meta transformations, i.e. transformations that call other
# transformations
#
#######################################################################


@transformation_factory(dict)
def traverse_locally(context: TreeContext,
                     transformation_table: Dict,  # actually: TransformationTableType
                     key_func: Callable = key_node_name):  # actually: KeyFunc
    """
    Transforms the syntax tree starting from the last node in the context
    according to the given transformation table. The purpose of this function is
    to apply certain transformations locally, i.e. only for those nodes that
    have the last node in the context as their parent node.
    """
    traverse(context[-1], transformation_table, key_func)


def transformation_guard(value) -> None:
    if value is not None:
        raise AssertionError('Transformation a value instead of None!')


def condition_guard(value) -> bool:
    if value is None:
        raise AssertionError('Condition returned None instead of a bool!')
    return value


def apply_transformations(context: TreeContext, transformation: Union[Callable, Sequence[Callable]]):
    """Applies a single or a sequence of transformations to a context."""
    if callable(transformation):
        transformation_guard(transformation(context))
    else:
        assert isinstance(transformation, tuple)
        for trans in cast(tuple, transformation):
            transformation_guard(trans(context))


@transformation_factory(collections.abc.Callable, tuple)
def apply_if(context: TreeContext, 
             transformation: Union[Callable, Tuple[Callable, ...]], 
             condition: Callable):
    """Applies a transformation only if a certain condition is met."""
    if condition_guard(condition(context)):
        apply_transformations(context, transformation)


@transformation_factory(collections.abc.Callable, tuple)
def apply_ifelse(context: TreeContext,
                 if_transformation: Union[Callable, Tuple[Callable, ...]],
                 else_transformation: Union[Callable, Tuple[Callable, ...]],
                 condition: Callable):
    """Applies a one particular transformation if a certain condition is met
    and another transformation otherwise."""
    if condition_guard(condition(context)):
        apply_transformations(context, if_transformation)
    else:
        apply_transformations(context, else_transformation)


@transformation_factory(collections.abc.Callable, tuple)
def apply_unless(context: TreeContext, 
                 transformation: Union[Callable, Tuple[Callable, ...]], 
                 condition: Callable):
    """Applies a transformation if a certain condition is *not* met."""
    if not condition_guard(condition(context)):
        apply_transformations(context, transformation)


## boolean operators


def always(context: TreeContext) -> bool:
    """Always returns True, no matter what the state of the context is."""
    return True


def never(context: TreeContext) -> bool:
    """Always returns True, no matter what the state of the context is."""
    return False

@transformation_factory(collections.abc.Callable)
def neg(context: TreeContext, bool_func: collections.abc.Callable) -> bool:
    """Returns the inverted boolean result of `bool_func(context)`"""
    return not bool_func(context)


@transformation_factory(collections.abc.Set)
def any_of(context: TreeContext, bool_func_set: AbstractSet[collections.abc.Callable]) -> bool:
    """Returns True, if any of the bool functions in `bool_func_set` evaluate to True
    for the given context."""
    return any(bf(context) for bf in bool_func_set)


@transformation_factory(collections.abc.Set)
def all_of(context: TreeContext, bool_func_set: AbstractSet[collections.abc.Callable]) -> bool:
    """Returns True, if all of the bool functions in `bool_func_set` evaluate to True
    for the given context."""
    return all(bf(context) for bf in bool_func_set)


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


def is_single_child(context: TreeContext) -> bool:
    """Returns ``True`` if the current node does not have any siblings."""
    return len(context[-2]._children) == 1


# TODO: ambiguous: named, tagging...
def is_named(context: TreeContext) -> bool:
    """Returns ``True`` if the current node's parser is a named parser."""
    # return not context[-1].anonymous
    tn = context[-1].name
    return bool(tn) and tn[0] != ':'


def is_anonymous(context: TreeContext) -> bool:
    """Returns ``True`` if the current node is anonymous."""
    # return context[-1].anonymous
    tn = context[-1].name
    return not tn or tn[0] == ':'


def is_anonymous_leaf(context: TreeContext) -> bool:
    """Returns `True` if context ends in an anonymous leaf-node"""
    # return not context[-1].children and context[-1].anonymous
    node = context[-1]
    if node._children:
        return False
    tn = node.name
    return not tn or tn[0] == ':'


RX_WHITESPACE = re.compile(r'\s*$')


def contains_only_whitespace(context: TreeContext) -> bool:
    r"""Returns ``True`` for nodes that contain only whitespace regardless
    of the name, i.e. nodes the content of which matches the regular
    expression /\s*/, including empty nodes. Note, that this is not true
    for anonymous whitespace nodes that contain comments."""
    return bool(RX_WHITESPACE.match(context[-1].content))


def is_empty(context: TreeContext) -> bool:
    """Returns ``True`` if the current node's content is empty."""
    return not context[-1].result


@transformation_factory(collections.abc.Set)
def is_token(context: TreeContext, tokens: AbstractSet[str] = frozenset()) -> bool:
    """
    Checks whether the last node in the context has the name ":Text"
    and it's content matches one of the given tokens. Leading and trailing
    whitespace-tokens will be ignored. In case an empty set of tokens is passed,
    any token is a match.
    """
    node = context[-1]
    return node.name == TOKEN_PTYPE and (not tokens or node.content in tokens)


@transformation_factory(collections.abc.Set)
def is_one_of(context: TreeContext, name_set: AbstractSet[str]) -> bool:
    """Returns true, if the node's name is one of the given tag names."""
    return context[-1].name in name_set


@transformation_factory(collections.abc.Set)
def not_one_of(context: TreeContext, name_set: AbstractSet[str]) -> bool:
    """Returns true, if the node's name is not one of the given tag names."""
    return context[-1].name not in name_set


@transformation_factory(collections.abc.Set)
def matches_re(context: TreeContext, patterns: AbstractSet[str]) -> bool:
    """
    Returns true, if the node's name matches one of the regular
    expressions in `patterns`. For example, ':.*' matches all anonymous nodes.
    """
    tn = context[-1].name
    for pattern in patterns:
        if re.match(pattern, tn):
            return True
    return False


@transformation_factory(str)
def has_attr(context: TreeContext, attr: str) -> bool:
    """
    Returns true, if the node has the attribute `attr`, no matter
    what its value is.
    """
    node = context[-1]
    return node.has_attr(attr)


@transformation_factory(str)
def attr_equals(context: TreeContext, attr: str, value: str) -> bool:
    """
    Returns true, if the node has the attribute `attr` and its value equals
    `value`.
    """
    node = context[-1]
    return node.has_attr(attr) and node.attr[attr] == value


@transformation_factory
def has_content(context: TreeContext, regexp: str) -> bool:
    """
    Checks a node's content against a regular expression.

    In contrast to ``re.match`` the regular expression must match the complete
    string and not just the beginning of the string to succeed!
    """
    if not regexp.endswith('$'):
        regexp += "$"
    return bool(re.match(regexp, context[-1].content))


@transformation_factory(collections.abc.Set)
def has_ancestor(context: TreeContext,
                 name_set: AbstractSet[str],
                 generations: int = -1,
                 until: Union[AbstractSet[str], str] = frozenset()) -> bool:
    """
    Checks whether a node with one of the given tag names appears somewhere
    in the context before the last node in the context.

    :param generations: determines how deep `has_ancestor` should dive into
        the ancestry. "1" means only the immediate parents wil be considered,
        "2" means also the grandparents, ans so on.
        A value smaller or equal zero means all ancestors will be considered.
    :param until: node-names which, when reached, will stop `has_ancestor`
        from searching further, even if the `generations`-parameter would
        allow a deeper search.
    """
    if until:
        if isinstance(until, str):  until = {until}
        for i in range(len(context) - 1, -1, -1):
            if context[i].name in until:
                break
        ctx = context[i:]
    else:
        ctx = context
    if generations <= 0:
        return any(nd.name in name_set for nd in ctx)
    for i in range(2, min(generations + 2, len(ctx) + 1)):
        if ctx[-i].name in name_set:
            return True
    return False


@transformation_factory(collections.abc.Set)
def has_parent(context: TreeContext, name_set: AbstractSet[str]) -> bool:
    """Checks whether the immediate predecessor in the context has one of the
    given tags."""
    return has_ancestor(context, name_set, 1)


def has_children(context: TreeContext) -> bool:
    """Checks whether last node in context has children."""
    return bool(context[-1]._children)


@transformation_factory(collections.abc.Set)
def has_descendant(context: TreeContext, name_set: AbstractSet[str],
                   generations: int = -1,
                   until: Union[AbstractSet[str], str] = frozenset()) -> bool:
    assert generations != 0
    if until:
        if isinstance(until, str):  until = {until}
    else:
        until = frozenset()
    if context[-1].name in until:
        for child in context[-1]._children:
            if child.name in name_set:
                return True
        return False
    for child in context[-1]._children:
        if child.name in name_set:
            return True
        if (generations < 0 or generations > 1) \
                and has_descendant(context + [child], name_set, generations - 1, until):
            return True
    return False


@transformation_factory(collections.abc.Set)
def has_child(context: TreeContext, name_set: AbstractSet[str]) -> bool:
    """Checks whether at least one child (i.e. immediate descendant) has one of
    the given tags."""
    return has_descendant(context, name_set, 1)


@transformation_factory(collections.abc.Set)
def has_sibling(context: TreeContext, name_set: AbstractSet[str]):
    if len(context) >= 2:
        node = context[-1]
        for child in context[-2]._children:
            if child != node and child.name in name_set:
                return True
    return False


#######################################################################
#
# utility functions
#
#######################################################################


def update_attr(dest: Node, src: Union[Node, Tuple[Node, ...]], root: RootNode):
    """
    Adds all attributes from `src` to `dest` and transfers all errors
    from `src` to `dest`. This is needed, in order to keep the attributes
    if the child node is going to be eliminated.
    """
    if isinstance(src, Node):
        src = (Node,)
    for s in src:
        # update attributes
        if s != dest and hasattr(s, '_attributes'):
            for k, v in s.attr.items():
                if k in dest.attr and v != dest.attr[k]:
                    raise ValueError('Conflicting attribute values %s and %s for key %s '
                                     'when reducing %s to %s ! Tree transformation stopped.'
                                     % (v, dest.attr[k], k, str(src), str(dest)))
                dest.attr[k] = v
        # transfer errors
        try:
            root.transfer_errors(s, dest)
            # ids = id(s)
            # if ids in root.error_nodes:
            #     root.error_nodes.setdefault(id(dest), []).extend(root.error_nodes[ids])
            #     del root.error_nodes[ids]
        except AttributeError:
            # root was not of type RootNode, probably a doc-test
            pass


def swap_attributes(node: Node, other: Node):
    """
    Exchanges the attributes between node and other. This might be
    needed when re-aranging trees.
    """
    NA = node.has_attr()
    OA = other.has_attr()
    if NA or OA:
        save = node._attributes if NA else None
        if OA:
            node._attributes = other._attributes
        elif NA:
            node._attributes = None
        if NA:
            other._attributes = save
        elif OA:
            other._attributes = None


def _replace_by(node: Node, child: Node, root: RootNode):
    """
    Replaces node's contents by child's content including the tag name.
    """
    # if node.anonymous or not child.anonymous:
    #     node.name = child.name
    nd_tn = node.name
    ch_tn = child.name
    if not nd_tn or nd_tn[0] == ':' or (ch_tn and ch_tn[0] != ':'):
        node.name = ch_tn
    node._set_result(child._result)
    update_attr(node, (child,), root)


def _reduce_child(node: Node, child: Node, root: RootNode):
    """
    Sets node's results to the child's result, keeping node's name.
    """
    node._set_result(child._result)
    update_attr(node, (child,), root)
    # update_attr(child, (node,), root)
    # if child.has_attr():
    #     node._attributes = child._attributes


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


def replace_by_single_child(context: TreeContext):
    """
    Removes single branch node, replacing it by its immediate descendant.
    Replacement only takes place, if the last node in the context has
    exactly one child. Attributes will be merged. In case one and the same
    attribute is defined for the child as well as the parent, the child's
    attribute value take precedence.
    """
    node = context[-1]
    if len(node._children) == 1:
        _replace_by(node, node._children[0], cast(RootNode, context[0]))


def replace_by_children(context: TreeContext):
    """
    Eliminates the last node in the context by replacing it with its children.
    The attributes of this node will be dropped. In case the last node is
    the root-note (i.e. len(context) == 1), it will only be eliminated, if
    there is but one child.

    WARNING: This should never be followed by move_fringes() in the transformation list!!!
    """
    try:
        parent = context[-2]
    except IndexError:
        replace_by_single_child(context)
        return
    node = context[-1]
    if node._children:
        result = parent._children  # type: Tuple[Node, ...]
        i = result.index(node)
        parent._set_result(result[:i] + node._children + result[i + 1:])


def reduce_single_child(context: TreeContext):
    """
    Reduces a single branch node by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    Reduction only takes place if the last node in the context has
    exactly one child. Attributes will be merged. In case one and the same
    attribute is defined for the child as well as the parent, the parent's
    attribute value take precedence.
    """
    node = context[-1]
    if len(node._children) == 1:
        _reduce_child(node, node._children[0], cast(RootNode, context[0]))


@transformation_factory(collections.abc.Callable)
def replace_or_reduce(context: TreeContext, condition: Callable = is_named):
    """
    Replaces node by a single child, if condition is met on child,
    otherwise (i.e. if the child is anonymous) reduces the child.
    """
    node = context[-1]
    if len(node._children) == 1:
        child = node._children[0]
        if condition(context):
            _replace_by(node, child, cast(RootNode, context[0]))
        else:
            _reduce_child(node, child, cast(RootNode, context[0]))


@transformation_factory(str)
def change_name(context: TreeContext, name: str, restriction: Callable = always):
    """
    Changes the tag name of the last node in the context.

    Parameters:
        restriction: A function of the context that returns False in cases
                where the tag name shall not be exchanged
        context: the context where the parser shall be replaced
        name: The new tag name.
    """
    if restriction(context):
        node = context[-1]
        # ZOMBIE_TAGS will not be changed, so that errors don't get overlooked
        # if node.name != ZOMBIE_TAG:
        node.name = name


@transformation_factory(str)
def change_tag_name(context: TreeContext, name: str, restriction: Callable = always):
    deprecation_warning('"DHParser.transform.change_tag_name()" is deprecated. '
                        'Use "change_name()" instead!')
    change_name(context, name, restriction)


@transformation_factory(dict)
def replace_child_names(context: TreeContext, replacements: Dict[str, str]):
    """
    Replaces the tag names of the children of the last node in the context
    according to the replacement dictionary.

    :param context: The current context (i.e. list of ancestors and current
        node)
    :param replacements: A dictionary of name. Each tag name of a child
        node that exists as a key in the dictionary will be replaces by
        the value for that key.
    """
    # assert ZOMBIE_TAG not in replacements, 'Replacing ZOMBIE_TAGS is not allowed, " \
    #     "because they result from errors that could otherwise be overlooked, subsequently!'
    for child in context[-1]._children:
        original_name = child.name
        child.name = replacements.get(original_name, original_name)


@transformation_factory(dict)
def replace_tag_names(context: TreeContext, replacements: Dict[str, str]):
    deprecation_warning('"DHParser.transform.replace_tag_names()" is deprecated. '
                        'Use "replace_child_names()" instead!')
    replace_child_names(context, replacements)


@transformation_factory(collections.abc.Callable)
def flatten(context: TreeContext, condition: Callable = is_anonymous, recursive: bool = True):
    """
    Flattens all children, that fulfill the given ``condition``
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
    if node._children:
        new_result = []     # type: List[Node]
        context.append(PLACEHOLDER)
        for child in node._children:
            context[-1] = child
            if child._children and condition(context):
                if recursive:
                    flatten(context, condition, recursive)
                new_result.extend(child._children)
                update_attr(node, (child,), cast(RootNode, context[0]))
            else:
                new_result.append(child)
        context.pop()
        node._set_result(tuple(new_result))


def collapse(context: TreeContext):
    """
    Collapses all sub-nodes of a node by replacing them with the
    string representation of the node. USE WITH CARE!

    >>> sxpr = '(place (abbreviation "p.") (page "26") (superscript "b") (mark ",") (page "18"))'
    >>> tree = parse_sxpr(sxpr)
    >>> collapse([tree])
    >>> print(flatten_sxpr(tree.as_sxpr()))
    (place "p.26b,18")
    """
    node = context[-1]
    for descendant in node.select_if(lambda nd: nd.has_attr()):
        node.attr.update(descendant.attr)
    node.result = node.content


MergeRule = Callable[[Sequence[Node]], Node]


def join_content(package: Sequence[Node]) -> Node:
    return Node('joined', "".join(nd.content for nd in package), True)


def pick_longest_content(package: Sequence[Node]) -> Node:
    longest = ''
    L = 0
    for nd in package:
        content = nd.content
        ndL = len(content)
        if ndL > L:
            longest = content
            L = ndL
    return Node('joined', longest, True)


def fix_content(fixed_content: str) -> MergeRule:
    def fix(package: Sequence[Node]) -> Node:
        nonlocal fixed_content
        return Node('joined', fixed_content)
    return fix


@transformation_factory(collections.abc.Callable)
def collapse_children_if(context: TreeContext,
                         condition: Callable,
                         target_tag: str,
                         merge_rule: MergeRule = join_content):
    """
    (Recursively) merges the content of all adjacent child nodes that
    fulfill the given `condition` into a single leaf node with the tag-name
    `taget_tag`. Nodes that do not fulfil the condition will be preserved.

    >>> sxpr = '(place (abbreviation "p.") (page "26") (superscript "b") (mark ",") (page "18"))'
    >>> tree = parse_sxpr(sxpr)
    >>> collapse_children_if([tree], not_one_of({'superscript', 'subscript'}), 'text')
    >>> print(flatten_sxpr(tree.as_sxpr()))
    (place (text "p.26") (superscript "b") (text ",18"))

    See `test_transform.TestComplexTransformations` for more examples.
    """
    assert isinstance(target_tag, str)  # TODO: Delete this when safe

    node = context[-1]
    if not node._children:
        return  # do nothing if its a leaf node
    package = []  # type: List[Node]
    result = []  # type: List[Node]

    def close_package():
        nonlocal package, target_tag, merge_rule
        if package:
            merged_node = merge_rule(package)
            merged_node.name = target_tag
            attrs = dict()
            for nd in package:
                if nd.has_attr():
                    attrs.update(nd.attr)
            result.append(merged_node.with_attr(attrs))
            package = []

    for child in node._children:
        if condition([child]):
            if child._children:
                collapse_children_if([child], condition, target_tag)
                for c in child._children:
                    if condition([c]):
                        package.append(c)
                    else:
                        close_package()
                        result.append(c)
                close_package()
            else:
                package.append(child)
        else:
            close_package()
            result.append(child)
    close_package()
    node.result = tuple(result)


@transformation_factory(collections.abc.Callable)
def transform_content(context: TreeContext, func: Callable):  # Callable[[ResultType], ResultType]
    """
    Replaces the content of the node. ``func`` takes the node's result
    as an argument an returns the mapped result.
    """
    node = context[-1]
    node.result = func(node.result)


@transformation_factory  # (str)
def replace_content_with(context: TreeContext, content: str):  # Callable[[Node], ResultType]
    """
    Replaces the content of the node with the given text content.
    """
    node = context[-1]
    node.result = content


@transformation_factory
def add_attributes(context: TreeContext, attributes: dict):  # Dict[str, str]
    """
    Adds the attributes in the dictionary to the XML-Attributes of the last node
    in the given context.
    """
    context[-1].attr.update(attributes)


def normalize_whitespace(context):
    """
    Normalizes Whitespace inside a leaf node, i.e. any sequence of
    whitespaces, tabs and line feeds will be replaced by a single
    whitespace. Empty (i.e. zero-length) Whitespace remains empty,
    however.
    """
    node = context[-1]
    assert not node._children
    if context[-1].name == WHITESPACE_PTYPE:
        if node.result:
            node.result = ' '
    else:
        node.result = re.sub(r'\s+', ' ', node.result)


@transformation_factory(collections.abc.Callable)
def merge_adjacent(context: TreeContext, condition: Callable, name: str = ''):
    """
    Merges adjacent nodes that fulfill the given `condition`. It is
    is assumed that `condition` is never true for leaf-nodes and non-leaf-nodes
    alike. Otherwise a type-error might ensue.
    """
    node = context[-1]
    children = node._children
    if children:
        new_result = []
        i = 0
        L = len(children)
        while i < L:
            if condition([children[i]]):
                initial = () if children[i]._children else ''
                k = i
                i += 1
                while i < L and condition([children[i]]):
                    i += 1
                if i > k:
                    adjacent = children[k:i]
                    head = adjacent[0]
                    names = {nd.name for nd in adjacent}
                    head.result = reduce(operator.add, (nd.result for nd in adjacent), initial)
                    update_attr(head, adjacent[1:], cast(RootNode, context[0]))
                    if name in names:
                        head.name = name
                    new_result.append(head)
            else:
                new_result.append(children[i])
                i += 1
        node._set_result(tuple(new_result))


merge_leaves = merge_adjacent(is_anonymous_leaf)


@transformation_factory(collections.abc.Callable)
def merge_connected(context: TreeContext, content: Callable, delimiter: Callable,
                    content_name: str = '', delimiter_name: str = ''):
    """
    Merges sequences of content and delimiters. Other than `merge_adjacent()`, which
    does not make this distinction, delimiters at the fringe of content blocks are not
    included in the merge.

    :param context: The context, i.e. list of "ancestor" nodes, ranging from the
        root node (`context[0]`) to the current node (`context[-1]`)
    :param content: Condition to identify content nodes. (TreeContext -> bool)
    :param delimiter: Condition to identify delimiter nodes. (TreeContext -> bool)
    :param content_name: tag name for the merged content blocks
    :param delimiter_name: tag name for the merged delimiters at the fringe

    ATTENTION: The condition to identify content nodes and the condition to
    identify delimiter nodes must never come true for one and the same node!!!
    """
    # first, merge all delimiters
    merge_adjacent(context, delimiter, delimiter_name)
    node = context[-1]
    children = node._children
    if children:
        new_result = []
        i = 0
        L = len(children)
        while i < L:
            if content([children[i]]):
                initial = () if children[i]._children else ''
                k = i
                i += 1
                while i < L and (content([children[i]]) or delimiter([children[i]])):
                    i += 1
                if delimiter([children[i - 1]]):
                    i -= 1
                if i > k:
                    adjacent = children[k:i]
                    head = adjacent[0]
                    names = {nd.name for nd in adjacent}
                    head.result = reduce(operator.add, (nd.result for nd in adjacent), initial)
                    update_attr(head, adjacent[1:], cast(RootNode, context[0]))
                    if content_name in names:
                        head.name = content_name
                    new_result.append(head)
            else:
                new_result.append(children[i])
                i += 1
        node._set_result(tuple(new_result))


def merge_results(dest: Node, src: Tuple[Node, ...], root: RootNode) -> bool:
    """
    Merges the results of nodes `src` and writes them to the result
    of `dest` type-safely, if all src nodes are leaf-nodes (in which case
    their result-strings are concatenated) or none are leaf-nodes (in which
    case the tuples of children are concatenated).
    Returns `True` in case of a successful merge, `False` if some source nodes
    were leaf-nodes and some weren't and the merge could thus not be done.

    Example:
        >>> head, tail = Node('head', '123'), Node('tail', '456')
        >>> merge_results(head, (head, tail), head)  # merge head and tail (in that order) into head
        True
        >>> str(head)
        '123456'
    """
    if all(nd._children for nd in src):
        dest.result = reduce(operator.add, (nd._children for nd in src[1:]), src[0]._children)
        update_attr(dest, src, root)
        return True
    elif all(not nd._children for nd in src):
        dest.result = reduce(operator.add, (nd.content for nd in src[1:]), src[0].content)
        update_attr(dest, src, root)
        return True
    return False


@transformation_factory(collections.abc.Callable)
@cython.locals(a=cython.int, b=cython.int, i=cython.int)
def move_fringes(context: TreeContext, condition: Callable, merge: bool = True):
    """
    Moves adjacent nodes on the left and right fringe that fulfill the given condition
    to the parent node. If the `merge`-flag is set, a moved node will be merged with its
    predecessor (or successor, respectively) in the parent node in case it
    also fulfills the given `condition`.

    WARNING: This function should never follow replace_by_children() in the transformation list!!!
    """
    node = context[-1]
    if len(context) <= 1 or not node._children:
        return
    parent = context[-2]

    assert node in parent._children, \
        ("Node %s (%s) is not among its parent's children, any more! "
         "This could be due to a transformation that manipulates the parent's result earlier "
         "in the transformation pipeline, like replace_by_children.") % (node.name, id(node))

    children = node._children

    a, b = 0, len(children)
    while a < b:
        if condition([children[a]]):
            a += 1
        elif condition([children[b - 1]]):
            b -= 1
        else:
            break
    before = children[:a]
    after = children[b:]
    children = children[a:b]

    if before or after:
        node._set_result(children)
        parent_children = parent._children
        for i, child in enumerate(parent_children):
            if id(child) == id(node):
                break

        a = i - 1
        b = i + 1

        # merge adjacent nodes that fulfil the condition
        if merge:
            while a >= 0 and condition([parent_children[a]]):
                a -= 1
            prevN = parent_children[a + 1:i]

            N = len(parent_children)
            while b < N and condition([parent_children[b]]):
                b += 1
            nextN = parent_children[i + 1:b]

            if len(before) + len(prevN) > 1:
                target = before[-1] if before else prevN[0]
                if merge_results(target, prevN + before, cast(RootNode, context[0])):
                    before = (target,)
            before = before or prevN

            if len(after) + len(nextN) > 1:
                target = after[0] if after else nextN[-1]
                if merge_results(target, after + nextN, cast(RootNode, context[0])):
                    after = (target,)
            after = after or nextN

        parent._set_result(parent_children[:a + 1] + before + (node,) + after + parent_children[b:])


def left_associative(context: TreeContext):
    """
    Rearranges a flat node with infix operators into a left associative tree.
    """
    node = context[-1]
    if len(node._children) >= 3:
        assert (len(node._children) + 1) % 2 == 0
        rest = list(node._children)
        left, rest = rest[0], rest[1:]
        while rest:
            infix, right, rest = rest[0], rest[1], rest[2:]
            assert not infix._children
            assert infix.name[0:1] != ":"
            left = Node(infix.name, (left, right))
        node.result = (left,)


@transformation_factory(collections.abc.Set)
def lean_left(context: TreeContext, operators: AbstractSet[str]):
    """
    Turns a right leaning tree into a left leaning tree:

        (op1 a (op2 b c))  ->  (op2 (op1 a b) c)

    If a left-associative operator is parsed with a right-recursive
    parser, `lean_left` can be used to rearrange the tree structure
    so that it properly reflects the order of association.

    ATTENTION: This transformation function moves forward recursively,
    so grouping nodes must not be eliminated during traversal! This
    must be done in a second pass.
    """
    node = context[-1]
    assert node._children and len(node._children) == 2
    assert node.name in operators
    right = node._children[1]
    if right.name in operators:
        assert right._children and len(right._children) == 2
        a, b, c = node._children[0], right._children[0], right._children[1]
        op1 = node.name
        op2 = right.name
        right.result = (a, b)
        right.name = op1
        node.result = (right, c)
        node.name = op2
        swap_attributes(node, right)
        # continue recursively on the left branch
        lean_left([right], operators)


#######################################################################
#
# destructive transformations:
#
# - leaves may be dropped (e.g. if deemed irrelevant)
# - errors of dropped leaves may be be lost
# - no promise that order will be preserved
#
#######################################################################


@transformation_factory(collections.abc.Callable)
def lstrip(context: TreeContext, condition: Callable = contains_only_whitespace):
    """Recursively removes all leading child-nodes that fulfill a given condition."""
    node = context[-1]
    i = 1
    while i > 0 and node._children:
        node_children = node._children
        lstrip(context + [node_children[0]], condition)
        i, L = 0, len(node_children)
        while i < L and condition(context + [node_children[i]]):
            i += 1
        if i > 0:
            node._set_result(node_children[i:])


@transformation_factory(collections.abc.Callable)
def rstrip(context: TreeContext, condition: Callable = contains_only_whitespace):
    """Recursively removes all leading nodes that fulfill a given condition."""
    node = context[-1]
    i, L = 0, len(node._children)
    while i < L and node._children:
        node_children = node._children
        rstrip(context + [node_children[-1]], condition)
        L = len(node_children)
        i = L
        while i > 0 and condition(context + [node_children[i - 1]]):
            i -= 1
        if i < L:
            node._set_result(node_children[:i])


@transformation_factory(collections.abc.Callable)
def strip(context: TreeContext, condition: Callable = contains_only_whitespace):
    """Removes leading and trailing child-nodes that fulfill a given condition."""
    lstrip(context, condition)
    rstrip(context, condition)


@transformation_factory  # (slice)
def keep_children(context: TreeContext, section: slice = slice(None)):
    """Keeps only child-nodes which fall into a slice of the result field."""
    node = context[-1]
    if node._children:
        node._set_result(node._children[section])


@transformation_factory(collections.abc.Callable)
def keep_children_if(context: TreeContext, condition: Callable):
    """Removes all children for which `condition()` returns `True`."""
    node = context[-1]
    if node._children:
        node._set_result(tuple(c for c in node._children if condition(context + [c])))


@transformation_factory(collections.abc.Set)
def keep_tokens(context: TreeContext, tokens: AbstractSet[str] = frozenset()):
    """Removes any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    keep_children_if(context, partial(is_token, tokens=tokens))


@transformation_factory(collections.abc.Set)
def keep_nodes(context: TreeContext, names: AbstractSet[str]):
    """Removes children by tag name."""
    keep_children_if(context, partial(is_one_of, name_set=names))


@transformation_factory
def keep_content(context: TreeContext, regexp: str):
    """Removes children depending on their string value."""
    keep_children_if(context, partial(has_content, regexp=regexp))


@transformation_factory(collections.abc.Callable)
def remove_children_if(context: TreeContext, condition: Callable):
    """Removes all children for which `condition()` returns `True`."""
    node = context[-1]
    if node._children:
        node._set_result(tuple(c for c in node._children if not condition(context + [c])))
    pass


remove_whitespace = remove_children_if(is_one_of(WHITESPACE_PTYPE))
remove_empty = remove_children_if(is_empty)
remove_anonymous_empty = remove_children_if(lambda ctx: is_empty(ctx) and is_anonymous(ctx))
remove_anonymous_tokens = remove_children_if(lambda ctx: is_token(ctx) and is_anonymous(ctx))
remove_infix_operator = keep_children(slice(0, None, 2))
# remove_single_child = apply_if(keep_children(slice(0)), lambda ctx: len(ctx[-1].children) == 1)


# def remove_first(context: TreeContext):
#     """Removes the first non-whitespace child."""
#     node = context[-1]
#     if node.children:
#         for i, child in enumerate(node.children):
#             if child.name != WHITESPACE_PTYPE:
#                 break
#         else:
#             return
#         node.result = node.children[:i] + node.children[i + 1:]
#
#
# def remove_last(context: TreeContext):
#     """Removes the last non-whitespace child."""
#     node = context[-1]
#     if node.children:
#         for i, child in enumerate(reversed(node.children)):
#             if child.name != WHITESPACE_PTYPE:
#                 break
#         else:
#             return
#         i = len(node.children) - i - 1
#         node.result = node.children[:i] + node.children[i + 1:]


def remove_brackets(context: TreeContext):
    """Removes any leading or trailing sequence of whitespaces, tokens or regexps."""
    children = context[-1]._children
    if children:
        disposables = LEAF_PTYPES
        i = 0
        while (i < len(children)
               and (children[i].name in disposables
                    or (children[i].name == ':Series'
                        and all(c.name in disposables for c in children[i]._children)))):
            i += 1
        k = len(children)
        while (k > 0
               and (children[k - 1].name in disposables
                    or (children[k - 1].name == ':Series'
                        and all(c.name in disposables for c in children[k - 1]._children)))):
            k -= 1
        context[-1]._set_result(children[i:k])


@transformation_factory(collections.abc.Set)
def remove_tokens(context: TreeContext, tokens: AbstractSet[str] = frozenset()):
    """Removes any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    remove_children_if(context, partial(is_token, tokens=tokens))


@transformation_factory(collections.abc.Set)
def remove_children(context: TreeContext, names: AbstractSet[str]):
    """Removes children by tag name."""
    remove_children_if(context, partial(is_one_of, name_set=names))


@transformation_factory
def remove_content(context: TreeContext, regexp: str):
    """Removes children depending on their string value."""
    remove_children_if(context, partial(has_content, regexp=regexp))


@transformation_factory(collections.abc.Callable)
def remove_if(context: TreeContext, condition: Callable):
    """Removes node if condition is `True`"""
    if condition(context):
        try:
            parent = context[-2]
        except IndexError:
            return
        node = context[-1]
        parent._set_result(tuple(nd for nd in parent._children if nd != node))


#######################################################################
#
# constructive transformations:
#
# nodes may be added (attention: position value )
#
#######################################################################

NodeGenerator = Callable[[], Node]
DynamicResultType = Union[Tuple[NodeGenerator, ...], NodeGenerator, str]


AT_THE_END = 2**32   # VERY VERY last position in a tuple of childe nodes


def node_maker(name: str,
               result: DynamicResultType,
               attributes: dict = {}) -> Callable:
    """
    Returns a parameter-free function that upon calling returns a freshly
    instantiated node with the given result, where `result` can again
    contain recursively nested node-factory functions which will be
    evaluated before instantiating the node.

    Example:
        >>> factory = node_maker('d', (node_maker('c', ','), node_maker('l', ' ')))
        >>> node = factory()
        >>> node.serialize()
        '(d (c ",") (l " "))'
    """
    def dynamic_result(result: DynamicResultType) -> Union[Tuple[Node, ...], Node, str]:
        if isinstance(result, str):
            return result
        elif isinstance(result, tuple):
            return tuple(node_generator() for node_generator in result)
        else:
            assert isinstance(result, Callable)
            return result()

    def create_leaf() -> Node:
        assert isinstance(result, str)
        return Node(name, result, True).with_attr(attributes)

    def create_branch() -> Node:
        return Node(name, dynamic_result(result)).with_attr(attributes)

    if isinstance(result, str):
        return create_leaf
    else:
        return create_branch


@transformation_factory(collections.abc.Set)
def positions_of(context: TreeContext, names: AbstractSet[str] = frozenset()) -> Tuple[int, ...]:
    """Returns a (potentially empty) tuple of the positions of the
    children that have one of the given `names`.
    """
    return tuple(i for i, c in enumerate(context[-1]._children) if c.name in names)


@transformation_factory
def delimiter_positions(context: TreeContext):
    """Returns a tuple of positions "between" all children."""
    return tuple(range(1, len(context[-1]._children)))


PositionType = Union[int, tuple, Callable]


def normalize_position_representation(context: TreeContext, position: PositionType) -> Tuple[int, ...]:
    """Converts a position-representation in any of the forms that `PositionType`
    allows into a (possibly empty) tuple of integers."""
    if callable(position):
        position = position(context)
    if isinstance(position, int):
        return (position,)
    elif not position:  # empty tuple or None
        return ()
    else:
        # assert isinstance(position, tuple) and all(isinstance(i, int) for i in position)
        return position


@transformation_factory(int, tuple, collections.abc.Callable)
def insert(context: TreeContext, position: PositionType, node_factory: Callable):
    """Inserts a delimiter at a specific position within the children. If
    `position` is `None` nothing will be inserted. Position values greater
    or equal the number of children mean that the delimiter will be appended
    to the tuple of children.

    Example::

        insert(pos_of('paragraph'), node_maker('LF', '\\n'))
    """
    pos_tuple = normalize_position_representation(context, position)
    if not pos_tuple:
        return
    node = context[-1]
    children = list(node._children)
    assert children or not node.result, "Cannot add nodes to a leaf-node!"
    L = len(children)
    pos_tuple = sorted(tuple((p if p >= 0 else (p + L)) for p in pos_tuple), reverse=True)
    for n in pos_tuple:
        n = min(L, n)
        text_pos = (children[n - 1].pos + children[n - 1].strlen()) if n > 0 else node.pos
        children.insert(n, node_factory().with_pos(text_pos))
    node.result = tuple(children)


@transformation_factory(collections.abc.Callable)
def delimit_children(context: TreeContext, node_factory: Callable):
    """Add a delimiter drawn from the `node_factory` between all children."""
    insert(context, delimiter_positions, node_factory)


########################################################################
#
# AST semantic validation functions (EXPERIMENTAL!!!)
#
########################################################################


# @transformation_factory
@transformation_factory(str)
def add_error(context: TreeContext, error_msg: str, error_code: ErrorCode = ERROR):
    """
    Raises an error unconditionally. This makes sense in case illegal paths are
    encoded in the syntax to provide more accurate error messages.
    """
    node = context[-1]
    if not error_msg:
        error_msg = "Syntax Error"
    try:
        cast(RootNode, context[0]).new_error(node, error_msg.format(
             name=node.name, content=node.content, pos=node.pos), error_code)
    except KeyError as key_error:
        cast(RootNode, context[0].new_error(
            node, 'Schlüssel %s nicht erlaubt in Format-Zeichenkette: "%s"! '
            'Erlaubt sind "name", "content", "pos"' % (str(key_error), error_msg),
            AST_TRANSFORM_CRASH))


@transformation_factory(collections.abc.Callable)
def error_on(context: TreeContext,
             condition: Callable,
             error_msg: str = '',
             error_code: ErrorCode = ERROR):
    """
    Checks for `condition`; adds an error or warning message if condition is not met.
    """
    if condition(context):
        if not error_msg:
            cond_name = condition.__name__ if hasattr(condition, '__name__') \
                else condition.__class__.__name__ if hasattr(condition, '__class__') \
                else '<unknown>'
            error_msg = "transform.error_on: Failed to meet condition " + cond_name
        add_error(context, error_msg, error_code)

#
# @transformation_factory(collections.abc.Callable)
# def warn_on(context: TreeContext, condition: Callable, warning: str = ''):
#     """
#     Checks for `condition`; adds an warning message if condition is not met.
#     """
#     node = context[-1]
#     if not condition(context):
#         if warning:
#             node.add_error(warning % node.name if warning.find("%s") > 0 else warning,
#                            WARNING)
#         else:
#             cond_name = condition.__name__ if hasattr(condition, '__name__') \
#                         else condition.__class__.__name__ if hasattr(condition, '__class__') \
#                         else '<unknown>'
#             context[0].new_error(node, "transform.warn_on: Failed to meet condition " + cond_name,
#                                  WARNING)


assert_has_children = error_on(lambda nd: nd._children, 'Element "%s" has no children')


@transformation_factory
def assert_content(context: TreeContext, regexp: str):
    node = context[-1]
    if not has_content(context, regexp):
        cast(RootNode, context[0]).new_error(node, 'Element "%s" violates %s on %s'
                                             % (node.name, str(regexp), node.content))


@transformation_factory(collections.abc.Set)
def require(context: TreeContext, child_tags: AbstractSet[str]):
    node = context[-1]
    for child in node._children:
        if child.name not in child_tags:
            cast(RootNode, context[0]).new_error(node, 'Element "%s" is not allowed inside "%s".'
                                                 % (child.name, node.name))


@transformation_factory(collections.abc.Set)
def forbid(context: TreeContext, child_tags: AbstractSet[str]):
    node = context[-1]
    for child in node._children:
        if child.name in child_tags:
            cast(RootNode, context[0]).new_error(node, 'Element "%s" cannot be nested inside "%s".'
                                                 % (child.name, node.name))


def peek(context: TreeContext):
    """For debugging: Prints the last node in the context as S-expression."""
    print(context[-1].as_sxpr(compact=True))
