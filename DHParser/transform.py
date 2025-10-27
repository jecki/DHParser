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
#     https://www.apache.org/licenses/LICENSE-2.0
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

from __future__ import annotations

import collections.abc
from functools import partial, singledispatch, reduce
import operator
from typing import AbstractSet, Callable, cast, Container, Dict, \
    Tuple, List, Sequence, Union, Optional

try:
    import cython
except ImportError:
    import DHParser.externallibs.shadow_cython as cython

from DHParser.error import ErrorCode, AST_TRANSFORM_CRASH, ERROR
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, LEAF_PTYPES, PLACEHOLDER, \
    RootNode, parse_sxpr, flatten_sxpr, Path, pp_path
from DHParser.toolkit import issubtype, isgenerictype, expand_table, smart_list, re, \
    deprecation_warning, TypeAlias, ByteString


__all__ = ('TransformationDict',
           'TransformationProc',
           'TransformationTableType',
           'CondFunc',
           'KeyFunc',
           'TransformerFunc',
           'TransformerCallable',
           'TransformerFactory',
           'transformation_factory',
           'key_node_name',
           'Filter',
           'BLOCK_LEAVES',
           'BLOCK_ANONYMOUS_LEAVES',
           'BLOCK_CHILDREN',
           'traverse',
           'transformer',
           'merge_treetops',
           'always',
           'never',
           'neg',
           'any_of',
           'all_of',
           'is_named',
           'update_attr',
           'update_attr_unless',
           'swap_attributes',
           'replace_by_single_child',
           'replace_by_children',
           'reduce_single_child',
           'replace_or_reduce',
           'swap_nested_nodes',
           'change_name',
           # 'change_tag_name',
           'replace_child_names',
           'replace_tag_names',
           'collapse',
           'join_content',
           'pick_longest_content',
           'fix_content',
           'collapse_children_if',
           'transform_result',
           'replace_content_with',
           'add_attributes',
           'del_attributes',
           'normalize_whitespace',
           'fuse_anonymous_leaves',
           'fuse',
           'merge_adjacent',
           'merge_leaves',
           'merge_connected',
           'merge_results',
           'move_fringes',
           'pull_up',
           'left_associative',
           'lean_left',
           'apply_if',
           'apply_unless',
           'apply_ifelse',
           'traverse_locally',
           'is_anonymous',
           'is_anonymous_leaf',
           'contains_only_whitespace',
           'is_empty',
           'is_token',
           'is_one_of',
           'not_one_of',
           'name_matches',
           'has_attr',
           'content_matches',
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
           'remove',
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


TransformationProc: TypeAlias = Callable[[Path], None]
TransformationDict: TypeAlias = Dict[str, Union[Callable, Sequence[Callable]]]
TransformationCache: TypeAlias = Dict[str, Tuple[Sequence[Filter], Sequence[Callable]]]
TransformationTableType: TypeAlias = Dict[str, Union[Sequence[Callable], TransformationDict]]
CondFunc: TypeAlias = Callable[[Path], bool]
KeyFunc: TypeAlias = Callable[[Node], str]
CriteriaType: TypeAlias = Union[int, str, Callable]
TransformerFunc: TypeAlias = Union[Callable[[RootNode], RootNode], partial]
TransformerCallable = TransformerFunc  # Deprecated: Use TransformerFunc!
TransformerFactory: TypeAlias = Callable[[], TransformerFunc]


def transformation_factory(t1=None, t2=None, t3=None, t4=None, t5=None):
    """
    Creates factory functions from transformation-functions that
    dispatch on the first parameter after the path parameter.

    Decorating a transformation-function that has more than merely the
    ``path``-parameter with ``transformation_factory`` creates a
    function with the same name, which returns a partial-function that
    takes just the path-parameter.

    Additionally, there is some syntactic sugar for
    transformation-functions that receive a collection as their second
    parameter and do not have any further parameters. In this case a
    list of parameters passed to the factory function will be converted
    into a single collection-parameter.

    The primary benefit is the readability of the transformation-tables.

    Usage::

        @transformation_factory(AbstractSet[str])
        def remove_tokens(path, tokens):
            ...

    or, alternatively::

        @transformation_factory
        def remove_tokens(path, tokens: AbstractSet[str]):
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

    def real_type(t):
        """get type from string alias, e.g. "Dict" -> typing.Dict."""
        if isinstance(t, str):          # ensure compatibility with python versions
            return eval(t.replace('unicode', 'str'))  # with alternative type handling.
        elif isinstance(t, ByteString):
            return eval(t.replace(b'unicode', b'str'))
        return t

    def type_guard(t):
        """Raises an error if type `t` is a generic type or could be mistaken
        for the type of the canonical first parameter "Path" of
        transformation functions. Returns `t`."""
        # if isinstance(t, GenericMeta):
        #     raise TypeError("Generic Type %s not permitted\n in transformation_factory "
        #                     "decorator. Use the equivalent non-generic type instead!"
        #                     % str(t))
        t = real_type(t)
        if isgenerictype(t):
            raise TypeError("Generic Type %s not permitted\n in transformation_factory "
                            "decorator. Use the equivalent non-generic type instead!"
                            % str(t))
        if issubtype(Path, t):
            raise TypeError("Sequence type %s not permitted\nin transformation_factory "
                            "decorator, because it could be mistaken for a base class "
                            "of Path\nwhich is the type of the canonical first "
                            "argument of transformation functions. Try 'tuple' instead!"
                            % str(t))
        return t

    def decorator(f):
        nonlocal t1
        import inspect
        sig = inspect.signature(f)
        params = list(sig.parameters.values())[1:]
        if len(params) == 0:
            return f  # '@transformer' not needed w/o free parameters
        assert t1 or params[0].annotation != params[0].empty, \
            "No type information on second parameter found! Please, use type " \
            "annotation or provide the type information via transformer-decorator."
        f = singledispatch(f)
        p1type = real_type(params[0].annotation)
        if t1 is None:
            t1 = type_guard(p1type)
        elif issubtype(p1type, type_guard(t1)):
            try:
                if len(params) == 1 and issubtype(p1type, Container) \
                        and not (issubtype(p1type, str) or issubtype(p1type, ByteString)):
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


def traverse(tree: Node,
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

    :param tree: The root-node of the syntax tree to be traversed
    :param transformation_table: A mapping node key -> sequence of functions
            that will be applied to matching nodes in order. This dictionary
            is interpreted as a ``compact_table``. See
            :func:`expand_table` or :func:`EBNFCompiler.EBNFTransTable`
    :param key_func: A mapping key_func(node) -> keystr. The default
            key_func yields node.name.
    :returns: The tree that has been transformed in-place. The returned
            object is the same that has been passed in parameter tree,
            but be aware that this tree has been changed in-place!

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
        # substitute key for insignificant whitespace
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

    def traverse_recursive(path):
        nonlocal cache
        node = path[-1]

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
            path.append(PLACEHOLDER)
            for child in children:
                path[-1] = child
                traverse_recursive(path)  # depth first
            path.pop()

        for call in sequence:
            try:
                call(path)
            except Exception as ae:
                if isinstance(path[0], RootNode) and path[0].docname:
                    raise AssertionError(
                        f'An exepction occured when transforming {pp_path(path, (1, 20))}\n'
                        f'in document "{path[0].docname}"\nwith {str(call)}:\n'
                        f'{ae.__class__.__name__}: {ae}')
                else:
                    raise AssertionError(
                        f'An exception occurred when transforming {pp_path(path, (1, 20))}\n'
                        f'with\n{str(call)}:\n{ae.__class__.__name__}: {ae}')

    for call in table.get('<<<', []):  call([tree])
    traverse_recursive([tree])
    for call in table.get('>>>', []):  call([tree])
    return tree
    # assert transformation_table['__cache__']


def transformer(tree: RootNode,
                transformation_table: TransformationTableType,
                key_func: KeyFunc = key_node_name,
                src_stage: str = '',
                dst_stage: str = '') -> RootNode:
    """
    Same as :func:`traverse`, but expects a node of type RootNode
    to be passed in parameter ``tree`` and retruns this RootNode.
    Furthermore, the names of the source and destination stages
    can be passed optionally in the parameters  ``src_stage`` and
    ``dst_stage``. If these parameters are not empty strings,
    the ``tree.stage`` will be checked against ``src_stage`` before
    transforming the tree and set to ``dst_stage`` after the
    transformation.

    See :func:`traverse` for the first three parameters and the general
    explanation of what ``transform`` does.

    :param src_stage: The name of the source stage or the empty string
        (default) if the source stage shall not be checked.
    :param dst_stage: The name of the destination stage or the empty
        string (default)

    :raises: ValueError, if ``tree.stage != src_stage``
    """
    assert isinstance(tree, RootNode)
    if src_stage and tree.stage and tree.stage.lower() != src_stage.lower():
        raise ValueError(f'Tree in stage "{src_stage}" expected, but "{tree.stage}" found!')
    tree = traverse(tree, transformation_table, key_func=key_func)
    if not isinstance(tree, RootNode):
        tree = RootNode(tree)
    tree.stage = dst_stage
    return tree


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
def traverse_locally(path: Path,
                     transformation_table: dict,  # actually: TransformationTableType
                     key_func: KeyFunc = key_node_name):  # actually: KeyFunc
    """
    Transforms the syntax tree starting from the last node in the path
    according to the given transformation table. The purpose of this function is
    to apply certain transformations locally, i.e. only for those nodes that
    have the last node in the path as their parent node.
    """
    traverse(path[-1], transformation_table, key_func)


def transformation_guard(value) -> None:
    if value is not None:
        raise AssertionError('Transformation of a value instead of None!')


def condition_guard(value) -> bool:
    if value is None:
        raise AssertionError('Condition returned None instead of a bool!')
    return value


def apply_transformations(path: Path, transformation: Union[Callable, Sequence[Callable]]):
    """Applies a single or a sequence of transformations to a path."""
    if callable(transformation):
        transformation_guard(transformation(path))
    else:
        assert isinstance(transformation, tuple)
        for trans in cast(tuple, transformation):
            transformation_guard(trans(path))


@transformation_factory(collections.abc.Callable, tuple)
def apply_if(path: Path,
             transformation: Union[Callable, Tuple[Callable, ...]],
             condition: CondFunc):
    """Applies a transformation only if a certain condition is met."""
    if condition_guard(condition(path)):
        apply_transformations(path, transformation)


@transformation_factory(collections.abc.Callable, tuple)
def apply_ifelse(path: Path,
                 if_transformation: Union[Callable, Tuple[Callable, ...]],
                 else_transformation: Union[Callable, Tuple[Callable, ...]],
                 condition: CondFunc):
    """Applies a one particular transformation if a certain condition is met
    and another transformation otherwise."""
    if condition_guard(condition(path)):
        apply_transformations(path, if_transformation)
    else:
        apply_transformations(path, else_transformation)


@transformation_factory(collections.abc.Callable, tuple)
def apply_unless(path: Path,
                 transformation: Union[Callable, Tuple[Callable, ...]],
                 condition: CondFunc):
    """Applies a transformation if a certain condition is *not* met."""
    if not condition_guard(condition(path)):
        apply_transformations(path, transformation)


## boolean operators


def always(path: Path) -> bool:
    """Always returns True, no matter what the state of the path is."""
    return True


def never(path: Path) -> bool:
    """Always returns True, no matter what the state of the path is."""
    return False

@transformation_factory(collections.abc.Callable)
def neg(path: Path, bool_func: collections.abc.Callable) -> Optional[bool]:
    """Returns the inverted boolean result of ``bool_func(path)``,
    unless the result is None. In that case None is passed through."""
    cond =  bool_func(path)
    if cond is None:  return None
    return not cond


@transformation_factory(collections.abc.Set)
def any_of(path: Path, bool_func_set: AbstractSet[collections.abc.Callable]) -> bool:
    """Returns True, if any of the bool functions in `bool_func_set` evaluate to True
    for the given path."""
    return any(bf(path) for bf in bool_func_set)


@transformation_factory(collections.abc.Set)
def all_of(path: Path, bool_func_set: AbstractSet[collections.abc.Callable]) -> bool:
    """Returns True, if all the bool functions in `bool_func_set` evaluate to True
    for the given path."""
    return all(bf(path) for bf in bool_func_set)


#######################################################################
#
# conditionals that determine whether the path (or the last node in
# the path for that matter) fulfill a specific condition.
# ---------------------------------------------------------------------
#
# The path of a node is understood as a list of all parent nodes
# leading up to and including the node itself. If represented as list,
# the last element of the list is the node itself.
#
#######################################################################

@transformation_factory(collections.abc.Callable)
def three_valued(path: Path, cond_true: CondFunc, cond_false: CondFunc) -> Optional[bool]:
    """Returns True, if ``cond_true`` evaluates to True, 
    Returns False, if ``cond_true`` does not evaluate to True but
    cond_false evaluates to True. Returns None, otherwise.
    
    Note that this means that the first parameter has precedence.
    Expressed as truth-table, this looks like::

        T T -> T
        T F -> T
        F T -> F
        F F -> None
    """
    if cond_true(path):  return True
    elif cond_false(path):  return False
    else: return None


def is_single_child(path: Path) -> bool:
    """Returns ``True`` if the current node does not have any siblings."""
    return len(path[-2]._children) == 1


# TODO: ambiguous: named, tagging...
def is_named(path: Path) -> bool:
    """Returns ``True`` if the current node's parser is a named parser."""
    # return not path[-1].anonymous
    tn = path[-1].name
    return bool(tn) and tn[0] != ':'


def is_anonymous(path: Path) -> bool:
    """Returns ``True`` if the current node is anonymous."""
    # return path[-1].anonymous
    tn = path[-1].name
    return not bool(tn) or tn[0] == ':'


def is_anonymous_leaf(path: Path) -> bool:
    """Returns `True` if path ends in an anonymous leaf-node"""
    # return not path[-1].children and path[-1].anonymous
    node = path[-1]
    if node._children:
        return False
    tn = node.name
    return not tn or tn[0] == ':'


RX_WHITESPACE = re.compile(r'\s*$')


def contains_only_whitespace(path: Path) -> bool:
    r"""Returns ``True`` for nodes that contain only whitespace regardless
    of the name, i.e. nodes the content of which matches the regular
    expression /\s*/, including empty nodes. Note that this is not true
    for anonymous whitespace nodes that contain comments."""
    return bool(RX_WHITESPACE.match(path[-1].content))


def is_empty(path: Path) -> bool:
    """Returns ``True`` if the current node's content is empty."""
    return not path[-1].result


@transformation_factory(collections.abc.Set)
def is_token(path: Path, tokens: AbstractSet[str] = frozenset()) -> bool:
    """
    Checks whether the last node in the path has the name ":Text"
    and it's content matches one of the given tokens. Leading and trailing
    whitespace-tokens will be ignored. In case an empty set of tokens is passed,
    any token is a match.
    """
    node = path[-1]
    return node.name == TOKEN_PTYPE and (not tokens or node.content in tokens)


@transformation_factory(collections.abc.Set)
def is_one_of(path: Path, name_set: AbstractSet[str]) -> bool:
    """Returns true, if the node's name is one of the given tag names."""
    return path[-1].name in name_set


@transformation_factory(str)
def is_a(path: Path, name: str) -> bool:
    """Returns True, if path[-1].name == name."""
    return path[-1].name == name


@transformation_factory(collections.abc.Set)
def not_one_of(path: Path, name_set: AbstractSet[str]) -> bool:
    """Returns true, if the node's name is not one of the given tag names."""
    return path[-1].name not in name_set


@transformation_factory(str)
def not_a(path: Path, name: str) -> bool:
    """Returns False, if path[-1].name != name."""
    return path[-1].name != name


@transformation_factory(str)
def name_matches(path: Path, regexp: str) -> bool:
    """
    Returns true, if the node's name matches the regular
    expression `regexp` completely. For example, ':.*' matches all anonymous nodes.
    """
    if not regexp.endswith('$'):
        regexp = f"(?:{regexp})$"
    return bool(re.match(regexp, path[-1].name))


@transformation_factory
def content_matches(path: Path, regexp: str) -> bool:
    """
    Checks a node's content against a regular expression.

    In contrast to ``re.match`` the regular expression must match the complete
    string and not just the beginning of the string to succeed!
    """
    if not regexp.endswith('$'):
        regexp = f"(?:{regexp})$"
    return bool(re.match(regexp, path[-1].content))


@transformation_factory
def has_content(path: Path, content: str) -> bool:
    """Checks a node's content against a given string. This is faster
    than content_matches for mere string comparisons."""
    return path[-1].content == content


@transformation_factory(str)
def has_attr(path: Path, attr: str="", value: Optional[str] = None) -> bool:
    """
    Returns True, if the node has the attribute ``attr`` and its value
    equals ``value``. If ``value`` is None, True is returned if the attribute
    exists, no matter what its value is.
    """
    if isinstance(path, Node):
        raise ValueError('Function DHParser.transform.has_attr() expects a path, not a node! '
                         'Use method node.has_attr() to check whether a node has attributes '
                         'or has a particular attribute or a particular attribute value?')
    node = path[-1]
    if not attr:
        return node.has_attr()
    if value is None:
        return node.has_attr(attr)
    else:
        return node.get_attr(attr, None) == value


@transformation_factory(collections.abc.Set)
def has_ancestor(path: Path,
                 name_set: AbstractSet[str],
                 generations: int = -1,
                 until: Union[AbstractSet[str], str] = frozenset()) -> bool:
    """
    Checks whether a node with one of the given tag names appears somewhere
    in the path before the last node in the path.

    :param generations: determines how deep `has_ancestor` should dive into
        the ancestry. "1" means only the immediate parents wil be considered,
        "2" means also the grandparents, and so on.
        A value smaller or equal zero means all ancestors will be considered.
    :param until: node-names which, when reached, will stop `has_ancestor`
        from searching further, even if the `generations`-parameter would
        allow a deeper search.
    """
    if until:
        if isinstance(until, str):  until = {until}
        for i in range(len(path) - 1, -1, -1):
            if path[i].name in until:
                break
        trl = path[i:]
    else:
        trl = path
    if generations <= 0:
        return any(nd.name in name_set for nd in trl)
    for i in range(2, min(generations + 2, len(trl) + 1)):
        if trl[-i].name in name_set:
            return True
    return False


@transformation_factory(collections.abc.Set)
def has_parent(path: Path, name_set: AbstractSet[str]) -> bool:
    """Checks whether the immediate predecessor in the path has one of the
    given tags."""
    return has_ancestor(path, name_set, 1)


def has_children(path: Path) -> bool:
    """Checks whether last node in 'path' has children."""
    return bool(path[-1]._children)


@transformation_factory(collections.abc.Set)
def has_descendant(path: Path, name_set: AbstractSet[str],
                   generations: int = -1,
                   until: Union[AbstractSet[str], str] = frozenset()) -> bool:
    """Checks whether a node with one of the given tag names appears somewhere
    among the descendants (children and children's children etc.)
    of the last node in the path.

    :param generations: determines how deep `has_descendant` should dive into
        the descendants. "1" means only the immediate children wil be considered,
        "2" means also the grandchildren, and so on.
        A value smaller or equal zero means all ancestors will be considered.
    :param until: node-names which, when reached, will stop `has_descendant`
        from searching further, even if the `generations`-parameter would
        allow a deeper search.
    """
    assert generations != 0
    if until:
        if isinstance(until, str):  until = {until}
    else:
        until = frozenset()
    if path[-1].name in until:
        for child in path[-1]._children:
            if child.name in name_set:
                return True
        return False
    for child in path[-1]._children:
        if child.name in name_set:
            return True
        if (generations < 0 or generations > 1) \
                and has_descendant(path + [child], name_set, generations - 1, until):
            return True
    return False


@transformation_factory(collections.abc.Set)
def has_child(path: Path, name_set: AbstractSet[str]) -> bool:
    """Checks whether at least one child (i.e. immediate descendant) has one of
    the given tags."""
    return has_descendant(path, name_set, 1)


@transformation_factory(collections.abc.Set)
def has_sibling(path: Path, name_set: AbstractSet[str]):
    """Checks whether the last node in the path has a node with one of the
    given names as sibling."""
    if len(path) >= 2:
        node = path[-1]
        for child in path[-2]._children:
            if child != node and child.name in name_set:
                return True
    return False


#######################################################################
#
# utility functions
#
#######################################################################


def update_attr(dest: Node, src: Union[Node, Tuple[Node, ...]], root: Node):
    """
    Adds all attributes from `src` to `dest` and transfers all errors
    from `src` to `dest`. This is needed, in order to keep the attributes
    if the child node is going to be eliminated.
    """
    if isinstance(src, Node):
        src = (src,)
    for s in src:
        # update attributes
        if s != dest and hasattr(s, '_attributes'):
            for k, v in s.attr.items():
                if k in dest.attr and v != dest.attr[k]:
                    raise ValueError('Conflicting attribute values %s and %s for key %s '
                                     'when merging or reducing %s to %s ! '
                                     'Tree transformation stopped.'
                                     % (v, dest.attr[k], k, str(src), str(dest)))
                dest.attr[k] = v
        # transfer errors
        try:
            cast(RootNode, root).transfer_errors(s, dest)
            # ids = id(s)
            # if ids in root.error_nodes:
            #     root.error_nodes.setdefault(id(dest), []).extend(root.error_nodes[ids])
            #     del root.error_nodes[ids]
        except AttributeError:
            # root was not of type RootNode, probably a doc-test
            pass


def update_attr_unless(dest: Node,
                       src: Union[Node, Tuple[Node, ...]],
                       root: Node,
                       exclude: Optional[CondFunc]):
    """Like :py:func:`update_attr`, but exclude the attributes from those src nodes for which
    `unless` is `True`."""
    if exclude is None:
        update_attr(dest, src, root)
    else:
        if isinstance(src, Node):
            src = (Node,)
        src = tuple(s for s in src if not exclude([s]))
        update_attr(dest, src, root)


def swap_attributes(node: Node, other: Node):
    """
    Exchanges the attributes between node and other. This might be
    needed when re-arranging trees.
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


def _replace_by(node: Node, child: Node, root: Node):
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


def _reduce_child(node: Node, child: Node, root: Node):
    """
    Sets node's results to the child's result, keeping node's name.Example::

    >>> nested = RootNode(parse_sxpr('(i (span `(style "letter-spacing:.25pt") "m."))'))
    >>> _reduce_child(nested, nested[0], nested)
    >>> nested.as_sxpr()
    '(i `(style "letter-spacing:.25pt") "m.")'
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


def replace_by_single_child(path: Path):
    """
    Removes single branch node, replacing it by its immediate descendant.
    Replacement only takes place, if the last node in the path has
    exactly one child. Attributes will be merged. In case one and the same
    attribute is defined for the child as well as the parent, the child's
    attribute value take precedence.
    """
    node = path[-1]
    if len(node._children) == 1:
        _replace_by(node, node._children[0], path[0])


def replace_by_children(path: Path):
    """
    Eliminates the last node in the path by replacing it with its children.
    The attributes of this node will be dropped. In case the last node is
    the root-note (i.e. len(path) == 1), it will only be eliminated, if
    there is but one child.

    WARNING: This should never be followed by move_fringes() in the transformation list!!!
    """
    try:
        parent = path[-2]
    except IndexError:
        replace_by_single_child(path)
        return
    node = path[-1]
    if node._children:
        result = parent._children  # type: Tuple[Node, ...]
        i = result.index(node)
        parent._set_result(result[:i] + node._children + result[i + 1:])


def reduce_single_child(path: Path):
    """
    Reduces a single branch node by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    Reduction only takes place if the last node in the path has
    exactly one child. Attributes will be merged. In case one and the same
    attribute is defined for the child as well as the parent, the parent's
    attribute value take precedence.
    """
    node = path[-1]
    if len(node._children) == 1:
        _reduce_child(node, node._children[0], path[0])


@transformation_factory(collections.abc.Callable)
def replace_or_reduce(path: Path, condition: CondFunc = is_named):
    """
    Replaces node by a single child, if condition is True on child.
    Reduces the child, if condition is not True and not None.
    If the condition is None nothing is changed.
    """
    node = path[-1]
    if len(node._children) == 1:
        child = node._children[0]
        cond = condition(path)
        if cond:
            _replace_by(node, child, path[0])
        elif cond is not None:
            _reduce_child(node, child, path[0])


def swap_nested_nodes(path: Path):
    """Swaps the tag-name and attributes with those of
    a single child. e.g. (A (B "...")) -> (B (A "..."))."""
    node = path[-1]
    if len(node.children) == 1:
        child = node._result[0]
        child.name, node.name = node.name, child.name
        swap_attributes(node, child) 


@transformation_factory(str)
def change_name(path: Path, name: str):
    """
    Changes the tag name of the last node in the path.

    Parameters:
        path: the path where the parser shall be replaced
        name: The new tag name.
    """
    node = path[-1]
    # # ZOMBIE_TAGS will not be changed, so that errors don't get overlooked
    # if node.name != ZOMBIE_TAG:
    node.name = name


# @transformation_factory(str)
# def change_tag_name(path: Path, name: str):
#     deprecation_warning('"DHParser.transform.change_tag_name()" is deprecated. '
#                         'Use "change_name()" instead!')
#     change_name(path, name)


@transformation_factory(dict)
def replace_child_names(path: Path, replacements: Dict[str, str]):
    """
    Replaces the tag names of the children of the last node in the path
    according to the replacement dictionary.

    :param path: The current path (i.e. list of ancestors and current
        node)
    :param replacements: A dictionary of names. Each tag name of a child
        node that exists as a key in the dictionary will be replaced by
        the value for that key.
    """
    # assert ZOMBIE_TAG not in replacements, 'Replacing ZOMBIE_TAGS is not allowed, " \
    #     "because they result from errors that could otherwise be overlooked, subsequently!'
    for child in path[-1]._children:
        original_name = child.name
        child.name = replacements.get(original_name, original_name)


@transformation_factory(dict)
def replace_tag_names(path: Path, replacements: Dict[str, str]):
    deprecation_warning('"DHParser.transform.replace_tag_names()" is deprecated. '
                        'Use "replace_child_names()" instead!')
    replace_child_names(path, replacements)


@transformation_factory(collections.abc.Callable)
def flatten(path: Path, condition: CondFunc = is_anonymous, recursive: bool = True):
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

    node = path[-1]
    if node._children:
        new_result = []     # type: List[Node]
        path.append(PLACEHOLDER)
        for child in node._children:
            path[-1] = child
            if child._children and condition(path):
                if recursive:
                    flatten(path, condition, recursive)
                new_result.extend(child._children)
                update_attr(node, (child,), path[0])
            else:
                new_result.append(child)
        path.pop()
        node._set_result(tuple(new_result))


def collapse(path: Path):
    """
    Collapses all sub-nodes of a node by replacing them with the
    string representation of the node. USE WITH CARE!

    >>> sxpr = '(place (abbreviation "p.") (page "26") (superscript "b") (mark ",") (page "18"))'
    >>> tree = parse_sxpr(sxpr)
    >>> collapse([tree])
    >>> print(flatten_sxpr(tree.as_sxpr()))
    (place "p.26b,18")
    """
    node = path[-1]
    for descendant in node.select_if(Node.has_attr):
        node.attr.update(descendant.attr)
    node.result = node.content


MergeRule = Callable[[Sequence[Node]], Node]


def join_content(package: Sequence[Node]) -> Node:
    return Node('joined', "".join(nd.content for nd in package), True).with_pos(package[0]._pos)


def pick_longest_content(package: Sequence[Node]) -> Node:
    longest = ''
    L = 0
    for nd in package:
        content = nd.content
        ndL = len(content)
        if ndL > L:
            longest = content
            L = ndL
    return Node('joined', longest, True).with_pos(package[0]._pos)


def fix_content(fixed_content: str) -> MergeRule:
    def fix(package: Sequence[Node]) -> Node:
        nonlocal fixed_content
        return Node('joined', fixed_content).with_pos(package[0]._pos)
    return fix


@transformation_factory(collections.abc.Callable)
def collapse_children_if(path: Path,
                         condition: CondFunc,
                         target_name: str,
                         merge_rule: MergeRule = join_content):
    """
    (Recursively) merges the content of all adjacent child nodes that
    fulfill the given `condition` into a single leaf node with the tag-name
    `target_tag`. Nodes that do not fulfil the condition will be preserved.

    >>> sxpr = '(place (abbreviation "p.") (page "26") (superscript "b") (mark ",") (page "18"))'
    >>> tree = parse_sxpr(sxpr)
    >>> collapse_children_if([tree], not_one_of({'superscript', 'subscript'}), 'text')
    >>> print(flatten_sxpr(tree.as_sxpr()))
    (place (text "p.26") (superscript "b") (text ",18"))

    See `test_transform.TestComplexTransformations` for more examples.
    """
    assert isinstance(target_name, str)  # TODO: Delete this when safe

    node = path[-1]
    if not node._children:
        return  # do nothing if it is a leaf node
    package = []  # type: List[Node]
    result = []  # type: List[Node]

    def close_package():
        nonlocal package, target_name, merge_rule
        if package:
            merged_node = merge_rule(package)
            merged_node.name = target_name
            attrs = dict()
            for nd in package:
                if nd.has_attr():
                    attrs.update(nd.attr)
            result.append(merged_node.with_attr(attrs))
            package = []

    for child in node._children:
        if condition(path + [child]):
            if child._children:
                collapse_children_if(path + [child], condition, target_name)
                for c in child._children:
                    if condition(path + [child, c]):
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


def fuse_anonymous_leaves(result: list[Node]) -> list[Node, ...]:
    """Mereges all anonymous leave nodes and returns a list of the
    merge nodes, e.g.::

    >>> tree = parse_sxpr('(p (:t "alpha") (:t "beta") (x "zzz") (:y (:t "uuu")) (:t "gamma"))')
    >>> tree.result = tuple(fuse_anonymous_leaves(list(tree.children)))
    >>> print(tree.as_sxpr())
    (p (:t "alphabeta") (x "zzz") (:y (:t "uuu")) (:t "gamma"))
    """
    i = 0
    L = len(result)
    cuts = []
    while i < L:
        nd = result[i]
        if not nd._children and nd.name[0:1] == ':':  # anonymous leaf node
            k = i + 1
            while k < L and not result[k]._children and result[k].name[0:1] == ':':
                k += 1
            if k - i > 1:
                nd.result = ''.join(r._result for r in result[i:k])
                cuts.append((i + 1, k))
            i = k
        else:
            i += 1
    if cuts:
        for a, b in reversed(cuts):
            del result[a:b]
    return result


def fuse(result: Sequence[Node],
         swallow: Optional[CondFunc] = None) -> Union[str, Tuple[Node, ...]]:
    """Merges the nodes in the given sequence of nodes by either
    merging their content if they are all leaves nodes or their results.

    :param result: The sequence of nodes to merge.
    :param swallow: A function that takes a node as an argument and
        returns True if the node should be added as a whole
        without merging its content.
        See :py:func:`merge_adjacent for an example`.
    :returns: The merges result, either a tuple of nodes or a
        string with the merged content in case all nodes where
        leave-nodes and no node was "swallowed".
    """
    if swallow is not None:
        if not isinstance(result, list):
            result = list(result)
        for i in range(len(result)):
            if swallow([result[i]]):
                result[i] = Node(':Swallowed', result[i])
    if not any(node._children for node in result):
        return ''.join(nd._result for nd in result)
    else:
        new_result = []
        for nd in result:
            if nd._children:
                new_result.extend(nd._children)
            else:
                new_result.append(Node(TOKEN_PTYPE, nd._result).with_pos(nd._pos))
        new_result = fuse_anonymous_leaves(new_result)
        return tuple(new_result)


@transformation_factory(collections.abc.Callable)
def merge_adjacent(path: Path,
                   condition: CondFunc,
                   preferred_name: str = '',
                   *, swallow: Optional[CondFunc] = None):
    """
    Merges adjacent nodes that fulfill the given `condition`. In case,
    some nodes are leaf-nodes, but others are not, the leaf-nodes' content
    will be added as TOKEN_PTYPE-Node to the result of the merged node.

    The merged node's name will be set to the value ``preferred_name``
    unless that value is the empty string. In this case the name of the
    first node of the merge will be chosen. (Note that the assignment
    of the preferred name only happens if a merge actually took place,
    i.e. if there are at least two nodes that have been merged.
    ``merge_adjacent()`` will not rename single nodes.)

    'merge_adjacent' differs from :py:func:`collapse_children_if` in
    two respects:

    1. The merged nodes are not "collapsed" to their string content.
    2. The naming rule for merged nodes is different, in so far as
       the 'preferred_name' passed to `merge_adjacent` is only used
       if it actually occurs among the nodes to be merged.

    This, if 'merge_adjacent' is substituted for 'collapse_children_if'
    in the doc-string example of the latter function, the example yields::

        >>> sxpr = '(place (abbreviation "p.") (page "26") (superscript "b") (mark ",") (page "18"))'
        >>> tree = parse_sxpr(sxpr)
        >>> merge_adjacent([tree], not_one_of({'superscript', 'subscript'}), '')
        >>> print(flatten_sxpr(tree.as_sxpr()))
        (place (abbreviation "p.26") (superscript "b") (mark ",18"))

    The parameter ``swallow`` takes a function that must yield true
    for those nodes that shall be swallowed as a whole, i.e. of which
    the content shall not be merged and which keep their name. This is
    useful if you'd like to keep certain nodes intact like, for
    example, internet links, when merging a sequence of nodes, as seen
    below. Without the swallow-parameter, the link (node named "a") will
    not be retained in the merged node, but merely its attribute is
    copied, which may not be what had been intended::

        >>> tree = parse_sxpr('''(p (t "In ") (a `(href "www.munich.de") "München")
        ...                       (t "steht ") (t "ein ") (t "Hofbräuhaus."))''')
        >>> import copy;  tree_copy = copy.deepcopy(tree)
        >>> merge_adjacent([tree], is_one_of('t', 'a'))
        >>> print(tree.as_sxpr())
        (p (t `(href "www.munich.de") "In Münchensteht ein Hofbräuhaus."))

    To reatain the link-node, merge_adjacent must be instructed to swallow
    nodes with the name "a" as a whole::

        >>> merge_adjacent([tree_copy], is_one_of('t', 'a'), swallow=is_a('a'))
        >>> print(tree_copy.as_sxpr())
        (p (t (:Text "In ") (a `(href "www.munich.de") "München") (:Text "steht ein Hofbräuhaus.")))
    """
    node = path[-1]
    children = node._children
    if children:
        new_result = []
        i = 0
        L = len(children)
        while i < L:
            if condition(path + [children[i]]):
                # initial = () if children[i]._children else ''
                k = i
                i += 1
                while i < L and condition(path + [children[i]]):
                    i += 1
                if i > k:
                    adjacent = children[k:i]
                    head = adjacent[0]
                    if swallow is not None and swallow([head]):
                        head = Node(preferred_name or head.name, '').with_pos(head._pos)
                    elif preferred_name and len(adjacent) > 1:
                        head.name = preferred_name
                    head.result = fuse(adjacent, swallow)
                    update_attr_unless(head, adjacent[1:], path[0], swallow)
                    new_result.append(head)
            else:
                new_result.append(children[i])
                i += 1
        node._set_result(tuple(new_result))


merge_leaves = merge_adjacent(is_anonymous_leaf)


@transformation_factory(collections.abc.Callable)
def merge_connected(path: Path, content: CondFunc, delimiter: CondFunc,
                    content_name: str = '', delimiter_name: str = '',
                    *, swallow: Optional[CondFunc] = None):
    """
    Merges sequences of content and delimiters. Other than `merge_adjacent()`, which
    does not make this distinction, delimiters at the fringe of content blocks are not
    included in the merge. (Note that other than :py:func:`merge_adjacent` the
    content name is always assigned to content nodes, but not to delimiters.)

    :param path: The path, i.e. list of "ancestor" nodes, ranging from the
        root node (`path[0]`) to the current node (`path[-1]`)
    :param content: Condition to identify content nodes. (Path -> bool)
    :param delimiter: Condition to identify delimiter nodes. (Path -> bool)
    :param content_name: tag name for the merged content blocks
    :param delimiter_name: tag name for the merged delimiters at the fringe

    ATTENTION: The condition to identify content nodes and the condition to
    identify delimiter nodes must never come true for one and the same node!!!
    """
    # first, merge all delimiters
    if swallow is None:
        merge_adjacent(path, delimiter, delimiter_name)
    else:
        merge_adjacent(path, lambda p: delimiter(p) and not swallow(p), delimiter_name)
    node = path[-1]
    children = node._children
    if children:
        new_result = []
        i = 0
        L = len(children)
        while i < L:
            if content(path + [children[i]]):
                # initial = () if children[i]._children else ''
                k = i
                i += 1
                while i < L and (content(path + [children[i]]) or delimiter(path + [children[i]])):
                    i += 1
                if delimiter(path + [children[i - 1]]):
                    i -= 1
                if i > k:
                    adjacent = children[k:i]
                    head = adjacent[0]
                    if swallow is not None and swallow([head]):
                        head = Node(content_name, '').with_pos(head._pos)
                    elif content_name:
                        head.name = content_name
                    head.result = fuse(adjacent, swallow)  # reduce(operator.add, (nd.result for nd in adjacent), initial)
                    update_attr_unless(head, adjacent[1:], path[0], swallow)
                    new_result.append(head)
            else:
                new_result.append(children[i])
                i += 1
        node._set_result(tuple(new_result))


def merge_results(dest: Node, src: Tuple[Node, ...], root: Node) -> bool:
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
        # dest.result = reduce(operator.add, (nd._children for nd in src[1:]), src[0]._children)
        result = []
        for nd in src:
            result.extend(nd._children)
        result = fuse_anonymous_leaves(result)
        dest.result = tuple(result)
        update_attr(dest, src, root)
        return True
    elif not any(nd._children for nd in src):
        dest.result = ''.join(nd._result for nd in src)  # reduce(operator.add, (nd.content for nd in src[1:]), src[0].content)
        update_attr(dest, src, root)
        return True
    return False

# TODO: parameterize to move only left or right fringes!
@transformation_factory(collections.abc.Callable)
@cython.locals(a=cython.int, b=cython.int, i=cython.int)
def move_fringes(path: Path, condition: CondFunc, *, side:str = "both", merge: bool = True):
    """
    Moves adjacent nodes on the left and right fringe that fulfill the given condition
    to the parent node. If the `merge`-flag is set, a moved node will be merged with its
    predecessor (or successor, respectively) in the parent node in case it
    also fulfills the given `condition`. Example:

    >>> tree = parse_sxpr('''(paragraph
    ...  (sentence
    ...    (word "Hello ")
    ...    (S " ")
    ...    (word "world,")
    ...    (S " "))
    ...  (sentence
    ...    (word "said")
    ...    (S " ")
    ...    (word "Hal.")))''')
    >>> tree = traverse(tree, {'sentence': move_fringes(is_one_of({'S'}))})
    >>> print(tree.as_sxpr())
    (paragraph
      (sentence
        (word "Hello ")
        (S " ")
        (word "world,"))
      (S " ")
      (sentence
        (word "said")
        (S " ")
        (word "Hal.")))

    In this example the blank at the end of the first sentence has been
    moved BETWEEN the two sentences. This is desirable, because if
    you extract a sentence from the data, most likely you are not interested
    in the trailing blank. Of course, this situation can best be
    avoided by a careful formulation of the grammar in the first place.

    WARNING: This function should never follow replace_by_children() in the transformation list!!!
    """
    assert side in ('left', 'right', 'both'), \
        (f'Parameter side of function move_fringes() must have one of the values '
         f'"left", "right", "both", but not "{side}"!')

    node = path[-1]
    if len(path) <= 1 or not node._children:
        return
    parent = path[-2]

    assert node in parent._children, \
        ("Node %s (%s) is not among its parent's children, any more! "
         "This could be due to a transformation that manipulates the parent's result earlier "
         "in the transformation pipeline, like replace_by_children.") % (node.name, id(node))

    children = node._children

    a, b = 0, len(children)
    while a < b:
        if condition(path + [children[a]]):
            a += 1
        elif condition(path + [children[b - 1]]):
            b -= 1
        else:
            break
    if side == "left":  b = len(children)
    elif side == "right":  a = 0
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
                if merge_results(target, prevN + before, path[0]):
                    before = (target,)
            before = before or prevN

            if len(after) + len(nextN) > 1:
                target = after[0] if after else nextN[-1]
                if merge_results(target, after + nextN, path[0]):
                    after = (target,)
            after = after or nextN

        parent._set_result(parent_children[:a + 1] + before + (node,) + after + parent_children[b:])


def pull_up(path):
    """Moves the last Node in the list one level up in the hierarchy.

    >>> tree = parse_sxpr('(p (t "A") (i (t "1") (X "---") (t "2")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_up(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (i (t "1")) (X (i "---")) (i (t "2")) (t "B"))

    >>> tree = parse_sxpr('(p (t "A") (i (X "---") (t "2")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_up(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (X (i "---")) (i (t "2")) (t "B"))

    >>> tree = parse_sxpr('(p (t "A") (i  (t "1") (X "---")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_up(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (i (t "1")) (X (i "---")) (t "B"))

    >>> tree = parse_sxpr('(p (t "A") (i (X "---")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_up(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (X (i "---")) (t "B"))

    EXPERIMENTAL!!!
    """
    node = path[-1]
    if len(path) <= 2:
        return
    parent = path[-2]
    ur_parent = path[-3]
    i = parent.index(node)
    i2 = ur_parent.index(parent)
    node._set_result(Node(parent.name, node.result).with_pos(node._pos).with_attr(parent.attr))
    children = ur_parent._children
    inlay = []
    if i > 0:
        inlay.append(Node(parent.name, parent[:i]).with_pos(parent._pos).with_attr(parent.attr))
    inlay.append(node)
    if i < len(parent.children) - 1:
        inlay.append(Node(parent.name, parent[i + 1:]).with_pos(parent[i + 1]._pos).with_attr(parent.attr))
    ur_parent._set_result(children[:i2] + tuple(inlay) + children[i2 + 1:])


def left_associative(path: Path):
    """
    Rearranges a flat node with infix operators into a left associative tree.
    """
    node = path[-1]
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
def lean_left(path: Path, operators: AbstractSet[str]):
    """
    Turns a right-leaning tree into a left-leaning tree:

        (op1 a (op2 b c))  ->  (op2 (op1 a b) c)

    If a left-associative operator is parsed with a right-recursive
    parser, `lean_left` can be used to rearrange the tree structure
    so that it properly reflects the order of association.

    This transformation is needed if you want to get the order of
    precedence right, when writing a grammar, say, for arithmetic
    that avoids left-recursion. (DHParser does support left-recursion,
    but left-recursive grammars might not be compatible with
    other PEG-frameworks anymore.)

    ATTENTION: This transformation function moves forward recursively,
    so grouping nodes must not be eliminated during traversal! This
    must be done in a second pass.
    """
    node = path[-1]
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
# - nodes and content may be dropped entirely (if deemed irrelevant)
# - no promise that order will be preserved
#
#######################################################################


@transformation_factory(collections.abc.Callable)
def lstrip(path: Path, condition: CondFunc = contains_only_whitespace):
    """Recursively removes all leading child-nodes that fulfill a given condition."""
    node = path[-1]
    i = 1
    while i > 0 and node._children:
        node_children = node._children
        lstrip(path + [node_children[0]], condition)
        i, L = 0, len(node_children)
        while i < L and condition(path + [node_children[i]]):
            i += 1
        if i > 0:
            node._set_result(node_children[i:])


@transformation_factory(collections.abc.Callable)
def rstrip(path: Path, condition: CondFunc = contains_only_whitespace):
    """Recursively removes all trailing nodes that fulfill a given condition."""
    node = path[-1]
    i, L = 0, len(node._children)
    while i < L and node._children:
        node_children = node._children
        rstrip(path + [node_children[-1]], condition)
        L = len(node_children)
        i = L
        while i > 0 and condition(path + [node_children[i - 1]]):
            i -= 1
        if i < L:
            node._set_result(node_children[:i])


@transformation_factory(collections.abc.Callable)
def strip(path: Path, condition: CondFunc = contains_only_whitespace):
    """Removes leading and trailing child-nodes that fulfill a given condition."""
    lstrip(path, condition)
    rstrip(path, condition)


@transformation_factory  # (slice)
def keep_children(path: Path, section: slice = slice(None)):
    """Keeps only child-nodes which fall into a slice of the result field."""
    node = path[-1]
    if node._children:
        node._set_result(node._children[section])


@transformation_factory(collections.abc.Callable)
def keep_children_if(path: Path, condition: CondFunc):
    """Removes all children for which `condition()` returns `True`."""
    node = path[-1]
    if node._children:
        node._set_result(tuple(c for c in node._children if condition(path + [c])))


@transformation_factory(collections.abc.Set)
def keep_tokens(path: Path, tokens: AbstractSet[str] = frozenset()):
    """Removes any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    keep_children_if(path, partial(is_token, tokens=tokens))


@transformation_factory(collections.abc.Set)
def keep_nodes(path: Path, names: AbstractSet[str]):
    """Removes children by tag name."""
    keep_children_if(path, partial(is_one_of, name_set=names))


@transformation_factory
def keep_content(path: Path, regexp: str):
    """Removes children depending on their string value."""
    keep_children_if(path, partial(content_matches, regexp=regexp))


@transformation_factory(collections.abc.Callable)
def remove_children_if(path: Path, condition: CondFunc):
    """Removes all children for which `condition()` returns `True`."""
    node = path[-1]
    if node._children:
        node._set_result(tuple(c for c in node._children if not condition(path + [c])))


remove_whitespace = remove_children_if(is_one_of(WHITESPACE_PTYPE))
remove_empty = remove_children_if(is_empty)
remove_anonymous_empty = remove_children_if(lambda trl: is_empty(trl) and is_anonymous(trl))
remove_anonymous_tokens = remove_children_if(lambda trl: is_token(trl) and is_anonymous(trl))
remove_infix_operator = keep_children(slice(0, None, 2))
# remove_single_child = apply_if(keep_children(slice(0)), lambda trl: len(trl[-1].children) == 1)


# def remove_first(path: Path):
#     """Removes the first non-whitespace child."""
#     node = path[-1]
#     if node.children:
#         for i, child in enumerate(node.children):
#             if child.name != WHITESPACE_PTYPE:
#                 break
#         else:
#             return
#         node.result = node.children[:i] + node.children[i + 1:]
#
#
# def remove_last(path: Path):
#     """Removes the last non-whitespace child."""
#     node = path[-1]
#     if node.children:
#         for i, child in enumerate(reversed(node.children)):
#             if child.name != WHITESPACE_PTYPE:
#                 break
#         else:
#             return
#         i = len(node.children) - i - 1
#         node.result = node.children[:i] + node.children[i + 1:]


def remove_brackets(path: Path):
    """Removes any leading or trailing sequence of whitespaces, tokens or regexps."""
    children = path[-1]._children
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
        path[-1]._set_result(children[i:k])


@transformation_factory(collections.abc.Set)
def remove_tokens(path: Path, tokens: AbstractSet[str] = frozenset()):
    """Removes any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed."""
    remove_children_if(path, partial(is_token, tokens=tokens))


@transformation_factory(collections.abc.Set)
def remove_children(path: Path, names: AbstractSet[str]):
    """Removes children by tag name."""
    remove_children_if(path, partial(is_one_of, name_set=names))


@transformation_factory
def remove_content(path: Path, regexp: str):
    """Removes children depending on their string value."""
    remove_children_if(path, partial(content_matches, regexp=regexp))


def remove(path: Path):
    """Removes node unconditionally."""
    try:
        parent = path[-2]
    except IndexError:
        return
    node = path[-1]
    parent._set_result(tuple(nd for nd in parent._children if nd != node))


@transformation_factory(collections.abc.Callable)
def remove_if(path: Path, condition: CondFunc):
    """Removes node if condition is `True`"""
    if condition(path):
        remove(path)


#######################################################################
#
# constructive transformations:
#
# nodes may be added (attention: position value )
#
#######################################################################


@transformation_factory(collections.abc.Callable)
def transform_result(path: Path, func: CondFunc):  # Callable[[ResultType], ResultType]
    """
    Replaces the result of the node. ``func`` takes the node's result
    as an argument and returns the mapped result.
    """
    node = path[-1]
    node.result = func(node.result)


@transformation_factory(str)
def replace_content_with(path: Path, content: str):
    """
    Replaces the content of the node with the given text content.
    """
    node = path[-1]
    node.result = content


def normalize_whitespace(path):
    """
    Normalizes Whitespace inside a leaf node, i.e. any sequence of
    whitespaces, tabs and line feeds will be replaced by a single
    whitespace. Empty (i.e. zero-length) Whitespace remains empty,
    however.
    """
    node = path[-1]
    assert not node._children
    if path[-1].name == WHITESPACE_PTYPE:
        if node.result:
            node.result = ' '
    else:
        node.result = re.sub(r'\s+', ' ', node.result)


@transformation_factory
def add_attributes(path: Path, attributes: dict):  # Dict[str, str]
    """
    Adds the attributes in the given dictionary to the XML-attributes
    of the last node in the given path.
    """
    path[-1].attr.update(attributes)


@transformation_factory
def del_attributes(path: Path, attributes: collections.abc.Set = frozenset()):  # Set[str]
    """
    Removes XML-attributes from the last node in the given path.
    If the given set is empty, all attributes will be deleted.
    """
    node = path[-1]
    if node.has_attr():
        if attributes:
            for attr in attributes:
                try:
                    del node.attr[attr]
                except KeyError:
                    pass
        else:
            node.attr = dict()


NodeGenerator = Callable[[], Node]
DynamicResultType = Union[Tuple[NodeGenerator, ...], NodeGenerator, str]


AT_THE_END = 2**32   # VERY, VERY last position in a tuple of child-nodes


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
def positions_of(path: Path, names: AbstractSet[str] = frozenset()) -> Tuple[int, ...]:
    """Returns a (potentially empty) tuple of the positions of the
    children that have one of the given `names`.
    """
    return tuple(i for i, c in enumerate(path[-1]._children) if c.name in names)


@transformation_factory
def delimiter_positions(path: Path):
    """Returns a tuple of positions "between" all children."""
    return tuple(range(1, len(path[-1]._children)))


PositionType = Union[int, tuple, Callable]


def normalize_position_representation(path: Path, position: PositionType) -> Tuple[int, ...]:
    """Converts a position-representation in any of the forms that `PositionType`
    allows into a (possibly empty) tuple of integers."""
    if callable(position):
        position = position(path)
    if isinstance(position, int):
        return (position,)
    elif not position:  # empty tuple or None
        return ()
    else:
        # assert isinstance(position, tuple) and all(isinstance(i, int) for i in position)
        return position


@transformation_factory(int, tuple, collections.abc.Callable)
def insert(path: Path, position: PositionType, node_factory: CondFunc):
    """Inserts a delimiter at a specific position within the children. If
    `position` is `None` nothing will be inserted. Position values greater
    or equal the number of children mean that the delimiter will be appended
    to the tuple of children.

    Example::

        insert(pos_of('paragraph'), node_maker('LF', '\\n'))
    """
    pos_tuple = normalize_position_representation(path, position)
    if not pos_tuple:
        return
    node = path[-1]
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
def delimit_children(path: Path, node_factory: CondFunc):
    """Add a delimiter drawn from the `node_factory` between all children."""
    insert(path, delimiter_positions, node_factory)


########################################################################
#
# AST semantic validation functions (EXPERIMENTAL!!!)
#
########################################################################


# @transformation_factory
@transformation_factory(str)
def add_error(path: Path, error_msg: str, error_code: ErrorCode = ERROR):
    """
    Raises an error unconditionally. This makes sense in case illegal paths are
    encoded in the syntax to provide more accurate error messages.
    """
    node = path[-1]
    assert isinstance(path[0], RootNode)
    root = cast(RootNode, path[0])
    if not error_msg:
        error_msg = "Syntax Error"
    try:
        root.new_error(node, error_msg.format(
             name=node.name, content=node.content, pos=node.pos), error_code)
    except KeyError as key_error:
        root.new_error(
            node, 'Schlüssel %s nicht erlaubt in Format-Zeichenkette: "%s"! '
            'Erlaubt sind "name", "content", "pos"' % (str(key_error), error_msg),
            AST_TRANSFORM_CRASH)


@transformation_factory(collections.abc.Callable)
def error_on(path: Path,
             condition: CondFunc,
             error_msg: str = '',
             error_code: ErrorCode = ERROR):
    """
    Checks for `condition`; adds an error or warning message if condition is not met.
    """
    if condition(path):
        if not error_msg:
            cond_name = condition.__name__ if hasattr(condition, '__name__') \
                else condition.__class__.__name__ if hasattr(condition, '__class__') \
                else '<unknown>'
            error_msg = "transform.error_on: Failed to meet condition " + cond_name
        add_error(path, error_msg, error_code)

#
# @transformation_factory(collections.abc.Callable)
# def warn_on(path: Path, condition: ConditionFunc, warning: str = ''):
#     """
#     Checks for `condition`; adds a warning message if condition is not met.
#     """
#     node = path[-1]
#     if not condition(path):
#         if warning:
#             node.add_error(warning % node.name if warning.find("%s") > 0 else warning,
#                            WARNING)
#         else:
#             cond_name = condition.__name__ if hasattr(condition, '__name__') \
#                         else condition.__class__.__name__ if hasattr(condition, '__class__') \
#                         else '<unknown>'
#             path[0].new_error(node, "transform.warn_on: Failed to meet condition " + cond_name,
#                                  WARNING)


assert_has_children = error_on(lambda nd: nd._children, 'Element "%s" has no children')


@transformation_factory
def assert_content(path: Path, regexp: str):
    node = path[-1]
    if not content_matches(path, regexp):
        cast(RootNode, path[0]).new_error(node, 'Element "%s" violates %s on %s'
                                          % (node.name, str(regexp), node.content))


@transformation_factory(collections.abc.Set)
def require(path: Path, child_tags: AbstractSet[str]):
    node = path[-1]
    for child in node._children:
        if child.name not in child_tags:
            cast(RootNode, path[0]).new_error(node, 'Element "%s" is not allowed inside "%s".'
                                              % (child.name, node.name))


@transformation_factory(collections.abc.Set)
def forbid(path: Path, child_tags: AbstractSet[str]):
    node = path[-1]
    for child in node._children:
        if child.name in child_tags:
            cast(RootNode, path[0]).new_error(node, 'Element "%s" cannot be nested inside "%s".'
                                              % (child.name, node.name))


def peek(path: Path):
    """For debugging: Prints the last node in the path as S-expression."""
    print(path[-1].as_sxpr(compact=True))

