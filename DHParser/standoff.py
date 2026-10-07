# standoff.py - standoff markup functions for DHParser
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


"""Module ``standoff`` provides some of the functionality of standoff
markup:

1. Content Mappings (:py:class:`ContentMapping`) relate the flat
    string-content of a document-tree to its structure. This allows using
    the string-content for searching in the document and then switching
    to the tree-structure to manipulate it.

    A (very experimental!) special case of content mappings are
    serialization mappings that map positions within a serialized version
    of the syntax-tree (XML, S-Expression or SXML) to locations within
    the tree (Node, Node-position within the serialization, offset and
    a flag indicating whether the position falls into the opening-tag,
    cosing-tag or content of the Node.)

2. A general markup function (:py:meth:`ContenMapping.markup`)that allows
    adding markup anywhere, even if it cuts across existing markup by
    suitably cutting either the new or the existing markup regions in two
    several parts.
"""

from __future__ import annotations

import copy
from enum import IntEnum
from typing import Container, Tuple, Optional, List, Dict, Any, Iterator, \
    Iterable, NamedTuple, Union, Sequence, cast, TypeAlias

from DHParser.nodetree import Node, Path, PathMatchFunction, PathSelector, \
    NodeMatchFunction, NodeSelector, flatten_sxpr, raw_strlen_of, strlen_of, \
    create_match_function, create_path_match_function, path_str, \
    find_common_ancestor, pp_path, RawMappingType, \
    ANY_PATH, NO_PATH, LEAF_PATH, DIVISIBLES, TOKEN_PTYPE
from DHParser.preprocess import SourceMap
from DHParser.toolkit import deprecated, deprecation_warning

try:
    import cython
except ImportError:
    import DHParser.externallibs.shadow_cython as cython


__all__ = ('Range',
           'never_empty',
           'never_invalid',
           'is_sorted_and_merged',
           'sort_and_merge',
           'range_union',
           'range_difference',
           'range_intersection',
           'insert_node',
           'split',  # deprecated!
           'split_node',
           # 'deep_split',
           # 'full_split',
           # 'can_split',
           # 'leaf_paths',
           'reset_chain_ID',
           'split_tree_if',
           'split_tree',
           'sourcemapped_path',
           'content_regions',
           'sourcemapped_selection',
           'DEFAULT_START_INDEX_SENTINEL',
           'LocationInfo',
           'NodeLocation',
           'ContentMapping',
           'SerPart',
           'SerLocation',
           'SerializationMapping')


#######################################################################
#
# ranges - range algebra for half-open [...[ intervals
#          (adapted from examples/re/runranges.py)
#
#######################################################################


Range: TypeAlias = Tuple[int, int]
# represents the half-open interval r[0] <= n < r[1]


def never_empty(rr: Sequence[Range]) -> bool:
    """Returns True if the sequence of ranges is not empty and
    no range in the seuqence has zero length."""
    if len(rr) <= 0: return False
    for r in rr:
        if r[0] >= r[1]: return False
    return True


def never_invalid(rr: Sequence[Range]) -> bool:
    """Returns True if the sequence of ranges is not empty and
    no range in the sequence is invalid, i.e. the end of the range
    lies before the start."""
    if len(rr) <= 0: return False
    for r in rr:
        if r[0] > r[1]: return False
    return True


def is_sorted_and_merged(rr: Sequence[Range]) -> bool:
    """Checks if a sequence of ranges is sorted in order
    and adjacent ranges merged where possible."""
    for i in range(1, len(rr)):
        if rr[i][0] < rr[i - 1][1]: return False
    return True


@cython.locals(a=cython.int, b=cython.int)
def sort_and_merge(R: List[Range]):
    """Sorts a sequence of ranges in order and merges all adjacent ranges."""
    Rlen = len(R)
    R.sort(key=lambda r: r[0])
    a = 0
    b = 1
    while b < Rlen:
        if R[b][0] <= R[a][1]:
            if R[a][1] <= R[b][1]:
                # high(R[a]) := high(R[b])
                R[a] = (R[a][0], R[b][1])
        else:
            a += 1
            if a != b: R[a] = R[b]
        b += 1
    del R[a + 1:]
    # assert is_sorted_and_merged(R)


def range_union(A: Sequence[Range], B: Sequence[Range]) -> List[Range]:
    """Returns the (sorted and merged) union of two sequences of ranges."""
    R = [r for r in A]
    R.extend(B)
    sort_and_merge(R)
    return R


def range_difference(A: Sequence[Range], B: Sequence[Range]) \
        -> List[Range]:
    """Returns the (sorted and merged) difference of two sequences of ranges: A - B.
    Unless A or B is empty, no range in A must be empty and both A and B must
    be sorted and merged. Otherwise, no reliable result can be guaranteed.
    """
    if not A:  return []
    if not B:  return list(A)
    # assert never_empty(A) and never_invalid(B)
    # assert is_sorted_and_merged(A) and is_sorted_and_merged(B)

    result = []
    lenB = len(B)
    lenA = len(A)
    i = 1
    k = 0
    M = A[0]
    S = B[0]

    def nextA() -> bool:
        nonlocal i, A, M, lenA
        if i < lenA:
            M = A[i]
            i += 1
            return False
        return True

    def nextB():
        nonlocal k, B, S, lenB
        k += 1
        if k < lenB:
            S = B[k]

    while k < lenB:
        if S[0] < M[1] and M[0] < S[1]:
            if M[0] < S[0]:
                result.append((M[0], S[0]))
                if S[1] < M[1]:
                    M = (S[1], M[1])  # need to create a new object, here!
                    nextB()
                elif nextA():
                    return result
            elif S[1] < M[1]:# need to create a new object, here!
                M = (S[1], M[1])
                nextB()
            elif nextA():
                return result
        elif M[1] <= S[0]:
            result.append(M)
            if nextA():
                return result
        else:
            assert S[1] <= M[0]
            nextB()
    result.append(M)
    while i < lenA:
        result.append(A[i])
        i += 1
    # assert is_sorted_and_merged(result)
    return result


def range_intersection(A: Sequence[Range], B: Sequence[Range]) \
        -> List[Range]:
    """Returns the (sorted and merged) intersection of two sequences of ranges.
    Unless A or B is empty, no range in A must be empty and both A and B must
    be sorted and merged. Otherwise, no reliable result can be guaranteed."""
    C = range_difference(A, B)
    return range_difference(A, C)


#######################################################################
#
# Content Mappings - splitting and insertion of new nodes into a tree
#
#######################################################################

def insert_node(leaf_path: Path, rel_pos: int, node: Node,
                divisible_leaves: Container = DIVISIBLES) -> Node:
    """Inserts a node at a specific position into the last or
    eventually second but last node in the path. The path must be
    a "leaf"-path, i.e., a path that ends in a leaf. Returns the
    parent of the newly inserted node.

    This is a convenient function for inserting milestones into
    a tree-strcutured document.

    Examples::

        >>> from DHParser.nodetree import Node, parse_sxpr
        >>> tree = parse_sxpr('(A "Guten Morgen!")')
        >>> _ = insert_node([tree], 6, Node('M', ''), divisible_leaves={'A'})
        >>> print(tree.as_sxpr())
        (A (A "Guten ") (M) (A "Morgen!"))
        >>> tree = parse_sxpr('(A (B "Guten") (S " ") (C "Morgen"))')
        >>> path = [tree, tree['S']]
        >>> _ = insert_node(path, 0, Node('M', ''), divisible_leaves={'B', 'S', 'C'})
        >>> print(tree.as_sxpr())
        (A (B "Guten") (M) (S " ") (C "Morgen"))
        >>> del tree['M']
        >>> _ = insert_node(path, 1, Node('M', ''), divisible_leaves={'B', 'S', 'C'})
        >>> print(tree.as_sxpr())
        (A (B "Guten") (S " ") (M) (C "Morgen"))
        >>> del tree['M']
        >>> path = [tree, tree['B']]
        >>> _ = insert_node(path, 2, Node('Hicks!', ''), divisible_leaves={'B', 'S', 'C'})
        >>> print(tree.as_sxpr())
        (A (B "Gu") (Hicks!) (B "ten") (S " ") (C "Morgen"))
        >>> tree = parse_sxpr('(A (B "Guten") (S " ") (C "Morgen"))')
        >>> path = [tree['B']]  # same tree, but 'path' is confined to the leaf node!
        >>> _ = insert_node(path, 2, Node('Hicks!', ''), divisible_leaves={'B', 'S', 'C'})
        >>> print(tree.as_sxpr())
        (A (B (B "Gu") (Hicks!) (B "ten")) (S " ") (C "Morgen"))
    """

    def split_leaf(leaf, node) -> Tuple[Node, Node, Node]:
        content = leaf.content
        if leaf._pos >= 0:
            node._pos = leaf._pos + rel_pos
            pred = Node(leaf.name, content[:rel_pos]).with_pos(leaf._pos)
            succ = Node(leaf.name, content[rel_pos:]).with_pos(node._pos + node.strlen())
        else:
            pred = Node(leaf.name, content[:rel_pos])
            succ = Node(leaf.name, content[rel_pos:])
        return (pred, node, succ)

    assert leaf_path
    leaf = leaf_path[-1]
    leaf_len = leaf.strlen()
    assert not leaf.children
    if rel_pos > leaf_len:
        raise ValueError(f'Relative position {rel_pos} > '
                         f'length of leaf element in the path {leaf_len} !')

    if len(leaf_path) >= 2:
        parent = leaf_path[-2]
        i = parent.index(leaf)
        if rel_pos == 0:
            parent.insert(i, node)
            return parent
        if rel_pos == leaf_len:
            parent.insert(i + 1, node)
            return parent
        if leaf.name not in divisible_leaves:
            raise ValueError(f'Node "{leaf.name}" is not divisible!')
        parent.result = parent.children[:i] + split_leaf(leaf, node) + parent.children[i + 1:]
        return parent
    else:
        if rel_pos == 0:
            node._pos = leaf._pos
            leaf.result = (node, Node(leaf.name, leaf.content))
        elif rel_pos == leaf_len:
            if leaf._pos >= 0:  node._pos = leaf._pos + leaf_len
            leaf.result = (Node(leaf.name, leaf.content), node)
        else:
            if leaf.name not in divisible_leaves:
                raise ValueError(f'Node "{leaf.name}" is not divisible!')
            leaf.result = split_leaf(leaf, node)
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
    """Generate a unique chain-ID for marking split nodes or tags,
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


@deprecated('Function "split()" has been renamed to "split_node()".')
def split(*args, **kwargs):
    return split_node(*args, **kwargs)


@cython.locals(k=cython.int)
def split_node(node: Node, parent: Node, i: cython.int, left_biased: bool = True,
               chain_attr: Optional[dict] = None) -> int:
    """Splits a node at the given index (in case of a branch-node) or
    string-position (in case of a leaf-node). Returns the index of the
    right part within the parent node after the split. (This means
    that with ``node.insert(index, nd)`` nd will be inserted exactly at
    the split location.)

    Non-anonymous nodes that have been split will be marked by updating
    their attribute-dictionary with the chain_attr-dictionary if given.

    :param node: the node to be split
    :param parent: the node's parent
    :param i: the index either of the child or of the character before
        which the node will be split.
    :param left_biased: if True, yields the location after the end of
        the previous path rather than the location at the very beginning
        of the next path. The default value is "True".
    :param chain_attr: a dictionary with a single key and value resembling
        an attribute and value that will be added to the attributes-dictionary
        of both nodes after the split if the node is named node.

    :returns: the index of the split within the children's tuple of the
        parent node.

    Examples::

        >>> from DHParser.nodetree import Node, parse_sxpr
        >>> test_tree = parse_sxpr('(X (A "Hello, ") (B "Peter") (C " Smith"))').with_pos(0)
        >>> X = copy.deepcopy(test_tree)

        # test edge cases first
        >>> split_node(X['B'], X, 0)
        1
        >>> print(X.as_sxpr())
        (X (A "Hello, ") (B "Peter") (C " Smith"))
        >>> split_node(X['B'], X, X['B'].strlen())
        2
        >>> print(X.as_sxpr())
        (X (A "Hello, ") (B "Peter") (C " Smith"))

        # standard case
        >>> split_node(X['B'], X, 2)
        2
        >>> print(X.as_sxpr())
        (X (A "Hello, ") (B "Pe") (B "ter") (C " Smith"))
        >>> print(X.pick('B', reverse=True).pos)
        9

        # use split() as preparation for adding markup
        >>> X = copy.deepcopy(test_tree)
        >>> a = split_node(X['A'], X, 6)
        >>> a
        1
        >>> b = split_node(X['C'], X, 1)
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
        >>> a = split_node(X['A'], X, 6)
        >>> b0 = split_node(X['bold']['C'], X['bold'], 1)
        >>> b0
        1
        >>> print(X.as_sxpr())
        (X (A "Hello,") (A " ") (B "Peter") (bold (C " ") (C "Smith")))
        >>> b = split_node(X['bold'], X, b0)
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
        >>> split_node(X['A'], X, X['A'].strlen())
        0
        >>> split_node(X['A'], X, X['A'].strlen(), left_biased=False)
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
    if right._children:
        right._pos = right.children[0]._pos
    elif node._pos >= 0:
        right._pos = node._pos + i
    node.result = node._result[:i]
    # if chain_attr and not node.anonymous:
    if chain_attr and not node.anonymous:
        node.attr.update(chain_attr)
        right.attr.update(chain_attr)
    parent.result = parent.children[:k] + (right,) + parent.children[k:]
    return k


@cython.locals(L=cython.int)
def deep_split(path: Path, i: cython.int,
               left_biased: bool = True,
               greedy: bool = True,
               match_func: PathMatchFunction = ANY_PATH,
               skip_func: PathMatchFunction = NO_PATH,
               chain_attr_name: str = '') -> int:
    """Splits a tree along the path where i is the offset (or relative
    index) of the split in the last node of the path.
    Returns the index of the split-location in the first node of the path.

    Examples::

        >>> from DHParser.nodetree import Node, parse_sxpr
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
        i = split_node(node, parent, i, left_biased, chain_attr)
        if greedy and idx < last_index:
            if left_biased:
                if i > 0 and raw_strlen_of(parent.children[:i], match_func, skip_func) == 0:
                    i = 0
            else:
                L = len(parent.children)
                if i < L and raw_strlen_of(parent.children[i:], match_func, skip_func) == 0:
                    i = L
    return i


def full_split(path: Path, i: cython.int,
               left_biased: bool = True,
               greedy: bool = True,
               match_func: PathMatchFunction = ANY_PATH,
               skip_func: PathMatchFunction = NO_PATH,
               chain_attr_name: str = '') -> Tuple[Node, Node]:
    """Like :py:func:`deep_split`, but splits the first node in the path
    and returns two trees, one to the left of the split, one to the right.
    As an edge case, either tree can be an empty node.
    Note that the type RootNode will only be preserved for the first
    returned Node. The second Node will always be an ordinary node.
    Also, no attributes will be transferred to the second Node from the
    root of the path, nor will its pos-value be initialized.
    (Instantiate a new RootNode-object and use :py:meth:`RootNode.swallow`
    to turn it into a RootNode-object.)
    """
    i = deep_split(path, i, left_biased, greedy, match_func, skip_func, chain_attr_name)
    root = path[0]
    tail = Node(root.name, root.result[i:])
    root.result = root.result[:i]
    return root, tail


@cython.locals(L=cython.int)  # k=cython.int does not work!!!
def can_split(t: Path, i: cython.int, left_biased: bool = True, greedy: bool = True,
              match_func: PathMatchFunction = ANY_PATH,
              skip_func: PathMatchFunction = NO_PATH,
              divisible: Container[str] = DIVISIBLES) -> int:
    """Returns the negative index of the first node in the path, from which
    on all nodes can be split or do not need to be split, because the
    split-index lies to the left or right of the node.

    Examples::

        >>> from DHParser.nodetree import Node, parse_sxpr
        >>> tree = parse_sxpr('(doc (p (:Text "ABC")))')
        >>> can_split([tree, tree[0], tree[0][0]], 1)
        -1
        >>> can_split([tree, tree[0], tree[0][0]], 0)
        -2
        >>> can_split([tree, tree[0], tree[0][0]], 3)
        -2
        >>> # anonymous nodes, like ":Text" are always divisible
        >>> can_split([tree, tree[0], tree[0][0]], 1, divisible=set())
        -1
        >>> # However, non-anonymous nodes aren't ...
        >>> tree = parse_sxpr('(doc (p (Text "ABC")))')
        >>> can_split([tree, tree[0], tree[0][0]], 1, divisible=set())
        0
        >>> # ... unless explicitly mentioned
        >>> tree = parse_sxpr('(doc (p (Text "ABC")))')
        >>> can_split([tree, tree[0], tree[0][0]], 1, divisible={'Text'})
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
        t2[k - 1].result = tuple((t2[k] if nd == t[k] else nd) for nd in t2[k - 1].children)
    t = t2

    k = 0
    for k in range(len(t) - 1):
        node = t[-k - 1]
        if i != 0 and i != len(node._result) and not (node.anonymous or node.name in divisible):
            break
        parent = t[-k - 2]
        i = split_node(node, parent, i, left_biased)
        if greedy:
            if left_biased:
                if i > 0 and raw_strlen_of(parent.children[:i], match_func, skip_func) == 0:
                    i = 0
            else:
                L = len(parent.children)
                if i < L and raw_strlen_of(parent.children[i:], match_func, skip_func) == 0:
                    i = L
    else:
        # node = t[0]
        k += 1
    return -k


def markup_leaf(node: Node, start: int, end: int, name: str, attr_dict: Optional[Dict] = None):
    """Adds markup to a leaf node, incidentally turning the leaf node into a branch node."""
    assert not node._children
    if attr_dict is None:  attr_dict = {}
    seg_1 = Node(TOKEN_PTYPE, node._result[:start])
    seg_1._pos = node._pos
    seg_2 = Node(name, node._result[start:end]).with_attr(attr_dict)
    seg_2._pos = node._pos + start if node._pos >= 0 else -1
    seg_3 = Node(TOKEN_PTYPE, node._result[end:])
    seg_3._pos = node._pos + end if node._pos >= 0 else -1
    node.result = tuple(nd for nd in (seg_1, seg_2, seg_3) if nd._result)


## tree splitting (EXPERIMENTAL) ######################################


def split_tree_if(tree: Node, milestone: PathMatchFunction,
                  skip_func: PathMatchFunction = NO_PATH) -> Tuple[Node, ...]:
    """Splits the entire tree into several trees at every Path for which
    the milestone-function yields True. The last node in the path for which
    the milestone-function yields True will be removed from the tree.
    Thus, split_if() resembles the split-method of the Python-string-object.

    EXPERIMENTAL!
    """
    result = []
    tail = tree
    msp = tree.pick_path_if(milestone, include_root=True, reverse=False, skip_func=skip_func)
    while msp:
        if len(msp) < 2:
            return tuple()
        i = msp[-2].index(msp[-1])
        del msp[-2][i]
        head, tail = full_split(msp[:-1], i)
        result.append(head)
        if tail.result:
            msp = tail.pick_path_if(milestone, include_root=True, reverse=False,
                                    skip_func=skip_func)
        else:
            msp = []
    result.append(tail)
    return tuple(result)


def split_tree(tree: Node, milestone: PathSelector,
               skip_subtree: PathSelector = NO_PATH) -> Tuple[Node, ...]:
    """Splits the entire tree into several trees at every Path for which
    the milestone-selector yields True. The last node in the path for which
    the milestone-selector yields True will be removed from the tree.
    Thus, split_if() resembles the split-method of the Python-string-object.

    EXPERIMENTAL!

    :param milestone: The criterion for a milestone-path
    :param skip_subtree: The criterion for subtrees (identified by their path)
        within which no milestones will be searched. (Default: all subtrees
        will be searched).
    """
    return split_tree_if(tree, create_path_match_function(milestone),
                         create_path_match_function(skip_subtree))


#######################################################################
#
# ContentMapping: A "string-view" on node-trees
#
#######################################################################

@cython.locals(k=cython.int)
def markup_right(path: Path, i: cython.int, name: str, attr_dict: Dict[str, Any],
                 greedy: bool = True,
                 match_func: PathMatchFunction = ANY_PATH,
                 skip_func: PathMatchFunction = NO_PATH,
                 divisible: Container[str] = DIVISIBLES,
                 chain_attr_name: str = ''):
    """Mark up the content from string position i within the last node of
    the path up to the very end of the content of the first node of the
    path.

    This is a helper function for :py:math:`ContentMapping.markup`.

    Examples::

        >>> from DHParser.nodetree import Node, parse_sxpr
        >>> tree = parse_sxpr('(X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))')
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> all_tags = {'A', 'B', 'C', 'D', 'E', 'F', 'X'}
        >>> markup_right(C_path, 2, 'em', dict(), divisible=all_tags)
        >>> print(X.as_sxpr())
        (X (A (C "12")) (em (A (C "3") (D "456")) (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> markup_right(C_path, 2, 'em', dict(), divisible=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (C "12") (em (C "3") (D "456"))) (em (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_right(D_path, 2, 'em', dict(), divisible=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "45") (em (D "6"))) (em (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_right(D_path, 2, 'em', dict(), divisible=all_tags - {'A', 'D'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D (:Text "45") (em "6"))) (em (B (E "789") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_right(E_path, 1, 'em', dict(), divisible=all_tags - {'E'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E (:Text "7") (em "89")) (em (F "abc"))) (em (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_right(E_path, 1, 'em', dict(), divisible=all_tags - {'B'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "7") (em (E "89") (F "abc"))) (em (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_right(E_path, 1, 'em', dict(), divisible=all_tags)
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "7")) (em (B (E "89") (F "abc")) (G "def")))
        >>> X = copy.deepcopy(tree)
        >>> G_path = X.pick_path('G')
        >>> markup_right(E_path, 3, 'em', dict(), divisible=all_tags)
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))

        # edge cases
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 1, 'em', dict(), divisible={'A'})
        >>> print(X.as_sxpr())
        (A (:Text "1") (em "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 1, 'em', dict(), divisible=set())
        >>> print(X.as_sxpr())
        (A (:Text "1") (em "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 0, 'em', dict(), divisible={'A'})
        >>> print(X.as_sxpr())
        (A (em "123"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_right([X], 3, 'em', dict(), divisible={'A'})
        >>> print(X.as_sxpr())
        (A "123")
    """
    assert path
    k = max(can_split(path, i, True, greedy, match_func, skip_func, divisible) - 1, -len(path))
    # k is parent-index of first node to split
    i = deep_split(path[k:], i, True, greedy, match_func, skip_func, chain_attr_name)

    if chain_attr_name and chain_attr_name not in attr_dict:
        attr_dict[chain_attr_name] = gen_chain_ID()

    nd = Node(name, path[k]._result[i:]).with_attr(attr_dict)
    if nd._children:
        nd._pos = path[k].children[i]._pos
        path[k].result = path[k].children[:i] + (nd,)
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
            nd._pos = path[k].children[i]._pos
            path[k].result = path[k].children[:i] + (nd,)
        k -= 1

    assert not any(nd.name == ':Text' and nd.children for nd in path)


@cython.locals(k=cython.int)
def markup_left(path: Path, i: cython.int, name: str, attr_dict: Dict[str, Any],
                greedy: bool = True,
                match_func: PathMatchFunction = ANY_PATH,
                skip_func: PathMatchFunction = NO_PATH,
                divisible: Container[str] = DIVISIBLES,
                chain_attr_name: str = ''):
    """Mark up the content from string position i within the last node of
    the path up to the very end of the content of the first node of the
    path.

    This is a helper function for :py:math:`ContentMapping.markup`.

    Examples::

        >>> from DHParser.nodetree import Node, parse_sxpr
        >>> tree = parse_sxpr('(X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))')
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> all_tags = {'A', 'B', 'C', 'D', 'E', 'F', 'X'}
        >>> markup_left(C_path, 2, 'em', dict(), divisible=all_tags)
        >>> print(X.as_sxpr())
        (X (em (A (C "12"))) (A (C "3") (D "456")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> markup_left(C_path, 2, 'em', dict(), divisible=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (em (C "12")) (C "3") (D "456")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> C_path = X.pick_path('C')
        >>> markup_left(C_path, 0, 'em', dict(), divisible=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (C "123") (D "456")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_left(D_path, 2, 'em', dict(), divisible=all_tags - {'A'})
        >>> print(X.as_sxpr())
        (X (A (em (C "123") (D "45")) (D "6")) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> D_path = X.pick_path('D')
        >>> markup_left(D_path, 2, 'em', dict(), divisible=all_tags - {'A', 'D'})
        >>> print(X.as_sxpr())
        (X (A (em (C "123")) (D (em "45") (:Text "6"))) (B (E "789") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_left(E_path, 1, 'em', dict(), divisible=all_tags - {'E'})
        >>> print(X.as_sxpr())
        (X (em (A (C "123") (D "456"))) (B (E (em "7") (:Text "89")) (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_left(E_path, 1, 'em', dict(), divisible=all_tags - {'B'})
        >>> print(X.as_sxpr())
        (X (em (A (C "123") (D "456"))) (B (em (E "7")) (E "89") (F "abc")) (G "def"))
        >>> X = copy.deepcopy(tree)
        >>> E_path = X.pick_path('E')
        >>> markup_left(E_path, 1, 'em', dict(), divisible=all_tags)
        >>> print(X.as_sxpr())
        (X (em (A (C "123") (D "456")) (B (E "7"))) (B (E "89") (F "abc")) (G "def"))

        # edge cases
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 1, 'em', dict(), divisible={'A'})
        >>> print(X.as_sxpr())
        (A (em "1") (:Text "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 1, 'em', dict(), divisible=set())
        >>> print(X.as_sxpr())
        (A (em "1") (:Text "23"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 3, 'em', dict(), divisible={'A'})
        >>> print(X.as_sxpr())
        (A (em "123"))
        >>> X = parse_sxpr('(A "123")')
        >>> markup_left([X], 0, 'em', dict(), divisible={'A'})
        >>> print(X.as_sxpr())
        (A "123")
    """
    assert path
    k = max(can_split(path, i, False, greedy, match_func, skip_func, divisible) - 1, -len(path))
    i = deep_split(path[k:], i, False, greedy, match_func, skip_func, chain_attr_name)

    if chain_attr_name and chain_attr_name not in attr_dict:
        attr_dict[chain_attr_name] = gen_chain_ID()

    nd = Node(name, path[k]._result[:i]).with_attr(attr_dict)
    nd._pos = path[k]._pos
    if nd._children:
        path[k].result = (nd,) + path[k].children[i:]
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
            path[k].result = (nd,) + path[k].children[i:]
        k -= 1

    assert not any(nd.name == ':Text' and nd.children for nd in path)


# def _breed_leaf_selector(select: PathSelector,
#                          ignore: PathSelector) -> Tuple[Callable, Callable]:
#     select_func = create_path_match_function(select)
#     ignore_func = create_path_match_function(ignore)
#
#     def general_match_func(path: Path) -> bool:
#         if path[-1]._children:
#             if select_func(path):
#                 raise ValueError(f'Selector "{select}" should yield only leaf-paths! But '
#                     f'the last element "{path[-1].name}" of path "{pp_path(path)}" has '
#                     f'children: {", ".join(child.name for child in path[-1].children)}! '
#                     f'Use leaf_path({select}) to circumvent this error.')
#             return False
#         return select_func(path) and not ignore_func(path)
#
#     if select == LEAF_PATH and ignore == NO_PATH:
#         match_func = LEAF_PATH
#     else:
#         match_func = general_match_func
#
#     return select_func, ignore_func  # match_func, ignore_func


def leaf_paths(criterion: PathSelector) -> PathMatchFunction:
    """Creates a path-match function that matches only and all leaf paths
    for those paths that the criterion matches.

        >>> from DHParser.nodetree import parse_xml
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

    def leaf_match_func(path: Path) -> bool:
        nonlocal cache_idx, cache_nd, match_func
        if path[-1]._children:  return False
        if cache_idx < len(path) and path[cache_idx] is cache_nd:
            return True
        for i in range(len(path), 0, -1):
            if match_func(path[:i]):
                cache_idx = i - 1
                cache_nd = path[cache_idx]
                return True
        return False

    if criterion is leaf_match_func:  return criterion
    match_func = create_path_match_function(criterion)
    cache_idx = 0
    cache_nd = None
    return leaf_match_func


def sourcemapped_path(origin: Node,
                      match_func: PathMatchFunction,
                      ignore_func: PathMatchFunction = NO_PATH) \
        -> Iterator[Tuple[Path, cython.int]]:
    """
    Similar to :py:func:`Node.select_path_if` but yields the path and the
    number of characters skipped since the last matched path was returned.
    Also, other than skip_func from select_path_if, ignore_func does not
    (still) yield the root-node if the ignored elements!
    """
    gap = 0

    def recursive(path) -> Iterator[Tuple[Path, int]]:
        nonlocal match_func, ignore_func, gap
        for child in path[-1].children:
            child_path = path + [child]
            if match_func(child_path):
                yield child_path, gap
                gap = 0
            elif child._children:
                if ignore_func(child_path):
                    gap += child.strlen()
                else:
                    yield from recursive(child_path)
            else:
                gap += child.strlen()

    path: List[Node] = [origin]
    if match_func(path):  yield path, 0
    if not ignore_func(path):
        yield from recursive(path)


@cython.locals(a=cython.int, b=cython.int, gap=cython.int)
def content_regions(origin: Node,
                    select: PathSelector,
                    ignore: PathSelector = NO_PATH) -> List[Range]:
    """Returns the minimal sequence of position-ranges in form of
    closed intervals (within the string content of the tree rooted in
    "origin") that covers all selected paths."""
    # select_func, ignore_func = _breed_leaf_selector(select, ignore)
    select_func = leaf_paths(select)
    ignore_func = create_path_match_function(ignore)
    a = 0
    ranges = []
    for path, gap in sourcemapped_path(origin, select_func, ignore_func):
        a += gap
        b = a + path[-1].strlen()
        if b >= a:
            if ranges and a <= ranges[-1][1]:
                ranges[-1] = (ranges[-1][0], b)
            else:
                ranges.append((a, b))
            a = b
    # assert is_sorted_and_merged(ranges)
    return ranges


@cython.locals(pos=cython.int, offset=cython.int, gap=cython.int)
def sourcemapped_selection(origin: Node,
                           select: PathSelector,
                           ignore: PathSelector = NO_PATH,
                           stump: Path = []) \
        -> Tuple[str, List[int], List[Path], SourceMap]:
    """Generates the string content, list of positions and list of paths
    as well as a source mapping for the given origin taking into account
    select and ignore as constraints.

    Note that ignore is not a strict equivalent to the skip_subtree or
    skip_func parameter from the Node.select...() methods. skip_subtree
    and skip_func still return the root of the subtree to be skipped
    and only  leave out its branches. ingnore also holds back the
    root of the subtree to be skipped!
    """
    # select_f, ignore_f = _breed_leaf_selector(select, ignore)
    select_f = leaf_paths(select)
    ignore_f = create_path_match_function(ignore)
    if ignore_f([origin]):
        return '', [], [], SourceMap('selection', [0, 1], [0, 0],
                                     ['selection'], {'selection': ''})
    pos = 0
    offset = 0
    content_list = []
    path_list = []
    pos_list = []
    offsets = [0]
    positions = [0]
    if stump:  select_f = lambda pth: select_f(stump + pth)
    for path, gap in sourcemapped_path(origin, select_f, ignore_f):
        if gap > 0:
            offset += gap
            if pos == positions[-1]:
                offsets[-1] = offset
            else:
                offsets.append(offset)
                positions.append(pos)
        pos_list.append(pos)
        path_list.append(path)
        content_list.append(path[-1].content)
        pos += path[-1].strlen()
    content = ''.join(content_list)
    offsets.append(offsets[-1] if len(offsets) > 0 else 0)
    positions.append(len(content) + 1)
    source_map = SourceMap('selection', positions, offsets,
                           ['selection'], {'selection': content})
    source_map.validate()  # TODO: Remove this when sufficiently tested!
    return content, pos_list, path_list, source_map


class ContentLocation(NamedTuple):
    """DEPRECATED: A location within in a context mapping"""
    path: Path
    offset: int
    __module__ = __name__  # required for cython/pickle compatibility


class LocationInfo(NamedTuple):
    """A location within in a context mapping"""
    path_index: int
    path: Path
    offset: int
    __module__ = __name__  # required for cython/pickle compatibility


class NodeLocation(NamedTuple):
    "Location (possibly void) of a node within the context mapping."
    node: Optional[Node]
    path_index: int
    __moddule__ = __name__  # required for cython/pickle compatibility


DEFAULT_START_INDEX_SENTINEL = -2 ** 30


class ContentMapping:
    """
    ContentMapping represents a path-mapping of the string-content of all or a
    specific selection of the leave-nodes of a tree. A content-mapping is an ordered
    mapping of the first text position of every (selected) leaf-node to the
    path of this node.

    Path-mappings allow searching the flat document with regular expressions or
    simple text search and then changing the tree at the appropriate places,
    for example, by adding markup (i.e., nodes) in these places.

    The ContentMapping class provides methods for adding markup-nodes.
    In cases where the new markup-nodes cut across the existing tree-hierarchy,
    the markup-method takes care of splitting up either the newly created or
    some of the existing nodes to fit in the markup.

    Caveat: Content mappings always use their own position values counting from 0
    for the left-most character. The Node.pos value will be both ignored and left
    untouched by the ContentMapping object. It is not even required that Node.pos has
    been initialized. Use :py:meth:`ContentMapping.get_node_pos` to determine
    a node's position within the content mapping and do not assume this to be
    the same as Node.pos.

    Public properties:

    :ivar path_list: A list of paths covering the selected leaves of the tree from
        left to right.
    :ivar pos_list: The list of positions of the paths in ``path_list``

    Location-related instance variables:

    :ivar origin: The origin of the tree for which a path mapping shall be
        generated. This can be a branch of another tree and therefore does not
        need to be a RootNode-object.
    :ivar select_func: Only leaf-paths for which this is true will be considered when
        generating the content-mapping. Note that the
        select-criterion must only accept leaf-paths. Otherwise, a ValueError will
        be raised. (Other than that, select_func is similar to the match_func
        parameter of Node.select_path_if)
    :ivar ignore_func: No leaf-path for which this is true will be considered when
        generating the content-mapping. (This is similar to the skip_func parameter
        of Node.select_path_if)
        Caveat: ignore is not a strict equivalent to the skip_subtree or
        skip_func parameter from the Node.select...() methods. skip_subtree
        and skip_func still return the root of the subtree to be skipped
        and only  leave out its branches. ingnore also holds back the
        root of the subtree to be skipped!
    :ivar content: The string content of the selected parts of the tree.
    :ivar sourcemap: A :py:class:`preprocess.SourceMap` instance that
        maps positions in the content

    Markup-related instance variables:

    :ivar greedy: If True, the algorithm for adding markup minimizes the number
        of required cuts by switching child and parent nodes if the markup fills
        up a node completely as well as including empty nodes in the markup.
        In any case, the string content of the added markup remains the same, but
        it might cover more tags than strictly necessary.
    :ivar chain_attr_name: An attribute that will receive one and the same identifier as
        value for all nodes belonging to the chain of a split-up node.
    :ivar auto_cleanup: Update the content mapping after the markup has been finished.
        Should always be true if it is intended to reuse the same content mapping
        for further markups in the same range or other purposes.
    :param divisibility: A dictionary that contains the information which tags
        (or nodes as identified by their name) are "harder" than other tags. Each
        key-tag in the dictionary is harder than (i.e., is allowed to split up) up
        all tags in the associated value (which is a set of nodes, or for that matter,
        tag-names). Tag or node-names associated with the wildcard key ``*`` can be split
        by any tag.

        If the markup-method reaches nodes that cannot be split, it will split
        the markup-node instead to cover the string to be marked up, completely.
    """

    def __init__(self, origin: Node,
                 select: PathSelector = LEAF_PATH,
                 ignore: PathSelector = NO_PATH,
                 greedy: bool = True,
                 divisibility: Union[Dict[str, Container], Container, str] = DIVISIBLES,
                 chain_attr_name: str = '',
                 auto_cleanup: bool = True,
                 sourcemap: bool = True):
        assert isinstance(origin, Node), f"origin must be a Node, not {type(origin)}, {origin}"
        self.origin: Node = origin
        # select_func, ignore_func = _breed_leaf_selector(select, ignore)
        select_func = leaf_paths(select)
        ignore_func = create_path_match_function(ignore)
        self.select_func: PathMatchFunction = select_func
        self.ignore_func: PathMatchFunction = ignore_func
        self.greedy: bool = greedy
        if isinstance(divisibility, Dict):
            if '*' not in divisibility:  divisibility['*'] = set()
            self.divisibility: Dict[str, Container] = divisibility
        elif isinstance(divisibility, str):
            for delimiter in (';', ',', ' '):
                lst = divisibility.split(delimiter)
                if len(lst) > 1:
                    self.divisibility = {'*': {s.strip() for s in lst}}
                    break
            else:
                raise ValueError(f'String value "{divisibility}" of parameter "divisability" '
                                 f'does not look like a list node-names!')
        else:
            self.divisibility = {'*': divisibility}
        self.chain_attr_name: str = chain_attr_name
        self.auto_cleanup = auto_cleanup

        if sourcemap:
            content, pos_list, path_list, sm = sourcemapped_selection(
                origin, select, ignore)
            self._sourcemap: Optional[SourceMap] = sm
        else:
            content, pos_list, path_list = self._generate_mapping(origin)
            self._sourcemap = None

        self.content: str = content
        self._pos_list: List[int] = pos_list
        self._path_list: List[Path] = path_list
        self._path_str_cache: Dict[int, str] = dict()
        self._fullcm: Optional[ContentMapping] = None  # needed for markup with excluded regions
        self._fullcm_offset = 0

    def _generate_mapping(self, origin, stump: Path = []) \
            -> Tuple[str, List[int], List[Path]]:
        """Generates the string content, list of positions and list of paths
        for the given origin taking into account ``self.select_func`` and
        ``self.ignore_func`` as constraints."""
        if self.ignore_func([origin]):
            return '', [], []
        pos = 0
        content_list = []
        path_list = []
        pos_list = []
        select_func = (lambda pth: self.select_func(stump + pth)) if stump else self.select_func
        for path in origin.select_path_if(
                select_func, include_root=True, skip_func=self.ignore_func):
            pos_list.append(pos)
            path_list.append(path)
            content_list.append(path[-1].content)
            pos += path[-1].strlen()
        return ''.join(content_list), pos_list, path_list

    def __str__(self):
        """Pretty-prints the content mapping. The format is:
        Test-Position -> List of node-names, the last node as S-expression without
        outer brackets. Example::

            >>> from DHParser.nodetree import parse_sxpr
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
    def sourcemap(self) -> SourceMap:
        if self._sourcemap is None:
            _, _, _, sm = sourcemapped_selection(
                self.origin, self.select_func, self.ignore_func)
            self._sourcemap = sm
        return self._sourcemap

    def flush_markup_cache(self):
        """Use this to clean up once after several markup-calls with
        parameter use_cache=True"""
        self._fullcm = None

    @property
    def path_list(self) -> List[Path]:
        return self._path_list

    @property
    def pos_list(self) -> List[int]:
        return self._pos_list

    def path(self, path_index: int) -> Path:
        try:
            return self._path_list[path_index]
        except IndexError:
            raise IndexError(f"path_index {path_index} is out of range "
                             f" [0, {len(self._path_list) - 1}]! Use cm.path(cm.get_path_index(position)) "
                             "to determine the path that for a particular position in the text!")

    def pos(self, path_index: int) -> int:
        """Returns the position of the first character of the leaf-node
        at the given path index. If the path index surpasses the
        highest possible path index exactly by one, the position right
        after the last character of the content mapping will be returned!
        (This helps to avoid boundary checking for some algorithms.)
        """
        try:
            return self._pos_list[path_index]
        except IndexError as e:
            return self._pos_list[path_index - 1] + self._path_list[path_index - 1][-1].strlen()

    def path_str(self, path_index: int) -> str:
        return self._path_str_cache.setdefault(path_index, path_str(self._path_list[path_index]))

    def node_names(self, path_index: int) -> Iterator[str]:
        return (nd.name for nd in self._path_list[path_index])

    @deprecated('Use "node_names()" instead.')
    def path_names(self, path_index: int) -> Iterator[str]:
        return self.node_names(path_index)

    @cython.locals(path_index=cython.int, last=cython.int)
    def get_path_index(self, pos: cython.int, left_biased: bool = False) -> int:
        """Yields the index for the path in given context-mapping that contains
        the position ``pos``.

        :param pos:   a position in the content of the tree for which the
            path mapping ``cm`` was generated
        :param left_biased: yields the location after the end of the previous
            path rather than the location at the very beginning of the
            next path. The default value is "False".
        :returns:   the integer index of the path in self.path_list that
            covers the given position ``pos``
        :raises:    IndexError if not 0 <= position < length of the document

        Example::

            >>> from DHParser.nodetree import parse_sxpr
            >>> tree = parse_sxpr('(a (b "012") (c (d "34") (e "56")))')
            >>> cm = ContentMapping(tree)
            >>> i = cm.get_path_index(4)
            >>> path = cm.path_list[i]
            >>> print(pp_path(path, 1, ', '))
            a, c, d "34"
        """
        errmsg = lambda i: f'Illegal position value {i}. ' \
                           f'Must be 0 <= position < length of text!'
        if pos < 0:  raise IndexError(errmsg(pos))
        import bisect
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

    def get_path(self, pos: int, left_biased: bool = False) -> Path:
        """Returns the path for a given position in the string content.
        :param pos: the position in the string-content for which the path and
            offset should be determined.
        :param left_biased: yields the location after the end of the previous
            path rather than the location at the very beginning of the
            next path. The default value is "False".
        :returns: The path for the given position
        """
        path_index = self.get_path_index(pos, left_biased)
        return self._path_list[path_index]

    def get_path_and_offset(self, pos: int, left_biased: bool = False,
                            index_out: Optional[List[int]] = None) -> Tuple[Path, int]:
        """Returns the path and relative position within the leaf-node of
        the path for a given position.

        :param pos: the position in the string-content for which the path and
            offset should be determined.
        :param left_biased: yields the location after the end of the previous
            path rather than the location at the very beginning of the
            next path. The default value is "False".
        :param index_out: DEPRECATED the index of the path in the content
            mapping's path-list will be appended to index_out.

        :returns:  tuple (path, offset) where the offset is the position
            of ``pos`` relative to the actual position of the last node in the path.
        :raises:    IndexError if not 0 <= position < length of the document
        """
        path_index = self.get_path_index(pos, left_biased)
        if index_out is not None:
            deprecation_warning('index_out parameter of ContentMapping.get_path_and_offset() '
                                'is deprecated and should not be used anymore! Use '
                                'ContentMapping.get_location() instead.')
            index_out.append(path_index)
        return (self._path_list[path_index], pos - self._pos_list[path_index])

    def get_location(self, pos: int, left_biased: bool = False) -> LocationInfo:
        """Returns the path-index, the path and the relative position within
        the leaf-node of the path for a given position.

        :param pos: the position in the string-content for which the path and
            offset should be determined.
        :param left_biased: yields the location after the end of the previous
            path rather than the location at the very beginning of the
            next path. The default value is "False".

        :returns:  LocationInfo, i.e., the tuple (path-index, path, offset) where
            the offset is the position of ``pos`` relative to the actual position
            of the last node in the path.
        :raises:  IndexError if not 0 <= position < length of the document
        """
        path_index = self.get_path_index(pos, left_biased)
        return LocationInfo(
            path_index, self._path_list[path_index], pos - self._pos_list[path_index])

    def get_node_index(self, node: Optional[Node], reverse: bool = False,
                       start_idx: int = 0, end_idx: int = -1) -> int:
        """Returns the index in the path_list of the first or last
        (if 'reverse' is True) path that contains 'node' or -1 if 'node'
        is None or the node cannot be found. Note: If 'node' is a leaf
        node, the first and the last index are the same. Otherwise, it
        occurs (if at all) more often than once if it or any of its
        children has more than one child.

        :param node: The node for which a path-index shall be found.
            If None is passed, -1 for "invalid index" is returned
        :param reverse: If true, search starts from the end.
        :param start_idx: An optional starting path index for the search.
        :param end_idx: An optional ending path index for the search.

        Examples::
            >>> from DHParser.nodetree import parse_sxpr
            >>> tree = parse_sxpr('(A (B (x "1") (y "2")) (C (z "3")))')
            >>> cm = ContentMapping(tree)
            >>> B = tree.pick('B')
            >>> cm.get_node_index(B)
            0
            >>> cm.get_node_index(B, reverse=True)
            1
            >>> cm.get_node_index(tree.pick('y'))
            1
            >>> cm.get_node_index(tree.pick('z'))
            2
            >>> cm.get_node_index(tree.pick('A', include_root=True), reverse=True)
            2
        """
        if node is None:
            return -1
        if end_idx <= 0:  end_idx = len(self._path_list)
        if reverse:
            while node.children:
                node = node.children[-1]
            for i in range(end_idx - 1, start_idx - 1, -1):
                if self._path_list[i][-1] == node:
                    return i
        else:
            while node.children:
                node = node.children[0]
            for i in range(end_idx):
                if self._path_list[i][-1] == node:
                    return i
        return -1

    def get_node_position(self, node: Node, reverse: bool = False) -> int:
        """Returns the string-position of the first or last + 1 (if 'reverse'
        is True) character of the node within the mapping. If 'node' is None
        or not contained in any path of the mapping, -1 will be returned.

        Note that this is the position within the context mapping and not
        a position derived from node.pos! (Content mappings always use their own
        positions and start counting from 0 for the left-most character.)

        Examples::

            >>> from DHParser.nodetree import parse_sxpr
            >>> tree = parse_sxpr('(A (B (x "1") (y "2")) (C (z "3")))')
            >>> cm = ContentMapping(tree)
            >>> B = tree.pick('B')
            >>> cm.get_node_position(B)
            0
            >>> cm.get_node_position(B, reverse=True)
            2
            >>> cm.get_node_position(tree.pick('y'))
            1
            >>> z = tree.pick('z')
            >>> cm.get_node_position(z)
            2
            >>> cm.get_node_position(z, reverse=True)
            3
            >>> cm.get_node_position(tree.pick('A', include_root=True), reverse=True)
            3
        """
        i = self.get_node_index(node, reverse)
        if i >= 0:
            if reverse:
                return self._pos_list[i] + self._path_list[i][-1].strlen()
            else:
                return self._pos_list[i]
        return -1

    @cython.locals(a=cython.int, b=cython.int, index_a=cython.int, index_b=cython.int)
    def iterate_paths(self, start_pos: cython.int, end_pos: cython.int, left_biased: bool = False) \
            -> Iterator[Path]:
        """Yields all paths from position ``start_pos`` up to and including
        position ``end_pos``. Example::

            >>> from DHParser.nodetree import parse_sxpr
            >>> tree = parse_sxpr('(a (b "123") (c (d "456") (e "789")) (f "ABC"))')
            >>> cm = ContentMapping(tree)
            >>> [[nd.name for nd in p] for p in cm.iterate_paths(1, 12)]
            [['a', 'b'], ['a', 'c', 'd'], ['a', 'c', 'e'], ['a', 'f']]
        """
        index_a = self.get_path_index(start_pos, left_biased)
        index_b = self.get_path_index(end_pos, left_biased)
        if index_b >= index_a:
            for i in range(index_a, index_b + 1):
                yield self._path_list[i]
        else:
            for i in range(index_a, index_b - 1, -1):
                yield self._path_list[i]

    def select_if(self, match_func: NodeMatchFunction,
                  start_from: int = DEFAULT_START_INDEX_SENTINEL,
                  reverse: bool = False) -> Iterator[NodeLocation]:
        """Yields the node and its path-index for all nodes that are matched
        by the match function. Searching starts from the path with the index
        ``start_from``. Searching within a path starts from the end
        of the path, and only the last matching node in every path is returned.
        Only the path-index from the first path that contains a matching node
        is returned. Subsequent pathes that contain the same node are skipped.

        Note that one and the same node can occur in more than one path, so
        there is no 1:1 relation between nodes and paths. In particular, the
        node location for one and the same node can differ depending on
        whether you iterate from the start or from the end (revers=True) of
        the content mapping.

        Examples::

            >>> from DHParser.nodetree import parse_sxpr
            >>> tree = parse_sxpr('(A (B (x "1") (y "2")) (B "!") (C (z "3")))')
            >>> cm = ContentMapping(tree)
            >>> for p in cm._path_list:  print(pp_path(p, 1))
            A <- B <- x "1"
            A <- B <- y "2"
            A <- B "!"
            A <- C <- z "3"
            >>> mf = create_match_function("B")
            >>> print([(i, nd.as_sxpr()) for nd, i in cm.select_if(mf)])
            [(0, '(B (x "1") (y "2"))'), (2, '(B "!")')]
            >>> print([(i, nd.as_sxpr()) for nd, i in cm.select_if(mf, reverse=True)])
            [(2, '(B "!")'), (1, '(B (x "1") (y "2"))')]
            >>> i = cm.get_node_index(tree.pick("B", reverse=True))
            >>> print([(i, nd.as_sxpr()) for nd, i in cm.select_if(mf, start_from=i)])
            [(2, '(B "!")')]
            >>> i = cm.get_node_index(tree.pick("y"))
            >>> print([(i, nd.as_sxpr()) for nd, i in cm.select_if(mf, start_from=i, reverse=True)])
            [(1, '(B (x "1") (y "2"))')]
        """
        node = None
        L = len(self._path_list)
        if start_from <= DEFAULT_START_INDEX_SENTINEL:
            start_from = L - 1 if reverse else 0
        assert start_from >= 0, "Cannot select from empty ContentMapping" if L == 0 \
            else f"start_from value {start_from} is below zero!"
        path_indices = range(start_from, -1, -1) if reverse else range(start_from, L)
        k = -1  # unnecessary, except to suppress a pyright message in the next if-statement
        for i in path_indices:
            path = self._path_list[i]
            try:
                if node and self._path_list[i][k] == node:
                    continue
            except IndexError:
                pass  # cause: k >= len(self._path_list[i])
            for k in range(len(path) - 1, -1, -1):
                node = path[k]
                if match_func(node):
                    yield NodeLocation(node, i)
                    break
            else:
                node = None

    def pick_if(self, match_func: NodeMatchFunction,
                start_from: int = DEFAULT_START_INDEX_SENTINEL,
                reverse: bool = False) -> Union[NodeLocation, Tuple[None, int]]:
        return next(self.select_if(match_func, start_from, reverse), (None, -1))

    def select(self, criterion: NodeSelector,
               start_from: int = DEFAULT_START_INDEX_SENTINEL,
               reverse: bool = False) -> Iterator[NodeLocation]:
        """See :py:meth:`ContentMapping.select_if`

        Example::

            >>> from DHParser.nodetree import parse_sxpr
            >>> tree = parse_sxpr('(A (B (x "1") (y "2")) (B "!") (C (z "3")))')
            >>> cm = ContentMapping(tree)
            >>> print([(i, nd.as_sxpr()) for nd, i in cm.select("y")])
            [(1, '(y "2")')]
        """
        yield from self.select_if(create_match_function(criterion), start_from, reverse)

    def pick(self, criterion: NodeSelector,
             start_from: int = DEFAULT_START_INDEX_SENTINEL,
             reverse: bool = False) -> Union[NodeLocation, Tuple[None, int]]:
        return next(self.select(criterion, start_from, reverse), (None, -1))

    @cython.locals(i=cython.int, start_pos=cython.int, end_pos=cython.int, offset=cython.int)
    def rebuild_mapping_slice(self, first_index: cython.int, last_index: cython.int):
        """Reconstructs a particular section of the context mapping after the
        underlying tree has been restructured. Other than
        :py:meth:`ContentMappin.rebuild_mapping`, the section that needs repairing
        is defined by the path indices and not the string positions.

        :param first_index: The index (not the position within the string-content!)
            of the first path that has been affected by restruturing of the tree.
            Use :py:meth:`ContentMapping.get_path_index` to determine the path-index
            if only the position is known.
        :param last_index: The index (not the position within the string-content!)
            of the last path that has been affected by restruturing of the tree.
            Use :py:meth:`ContentMapping.get_path_index` to determine the path-index
            if only the position is known.

        Examples::

            >>> from DHParser.nodetree import parse_sxpr
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
            >>> common_ancestor, _ = cm.add_markup(10, 16, 'Y')
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
            >>> common_ancestor, _ = cm.add_markup(0, 6, 'Y')
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

        # BEWARE: the paths self._path_list are already messed up from first_index to last_index
        #         from common_ancestor downwards (after markup)!

        stump = start_path[:i]
        content, offsets, paths = self._generate_mapping(common_ancestor, stump)
        assert offsets[0] == 0
        start_pos = self._pos_list[first_index]
        end_pos = self._pos_list[last_index] + paths[-1][-1].strlen()
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

        self.content = ''.join([self.content[:start_pos], content, self.content[end_pos + 1:]])

        self._pos_list.clear()
        self._pos_list.extend(off_head)
        self._pos_list.extend(offsets)
        self._pos_list.extend(off_tail)

        self._path_list.clear()
        self._path_list.extend(path_head)
        self._path_list.extend(paths)
        self._path_list.extend(path_tail)

        self._path_str_cache = dict()  # clear path-string-cache

    def rebuild_mapping(self, start_pos: int = -1, end_pos: int = -1):
        """Reconstructs parts of the content mapping. This will be
        necessary after the underlying tree has been restructured by
        other methods than the methods (markup, insert_node)
        of ContentMapping or if auto_cleanup was set to False.

        :param start_pos: The string position of the beginning of the text-area
            that has been affected by earlier changes. Any value <= 0 is assumend
            to refer to the beginning of the text.
        :param end_pos: The string position of the ending of the text-area
            that has been affected by earlier changes. A value < 0 means the
            last position in the text."""
        first_index = self.get_path_index(start_pos) if start_pos >= 0 else 0
        last_index = self.get_path_index(end_pos) if end_pos >= 0 else (len(self._path_list) - 1)
        self.rebuild_mapping_slice(first_index, last_index)

    def insert_node(self, pos: int, node: Node, left_biased: bool = False) -> NodeLocation:
        """Inserts a node at a specific position into the last or
        eventually second but last node in the path from the context mapping
        that covers this position. Returns the parent of the newly inserted
        node."""
        index = self.get_path_index(pos, left_biased)
        path = self._path_list[index]
        rel_pos = pos - self._pos_list[index]
        try:
            divisables = self.divisibility[node.name]
        except KeyError:
            divisables = self.divisibility['*']
        parent = insert_node(path, rel_pos, node, divisables)
        if self.auto_cleanup:
            i1 = self.get_path_index(pos, left_biased=True)
            i2 = self.get_path_index(pos + node.strlen(), left_biased=False)
            self.rebuild_mapping_slice(i1, i2)
        return NodeLocation(parent, index)

    @cython.locals(i=cython.int, k=cython.int, q=cython.int, r=cython.int, t=cython.int, u=cython.int, L=cython.int)
    def add_markup(self, start_pos: cython.int, end_pos: cython.int, tag_name: str,
                   attributes: Optional[Dict] = None, **additional_attrs) -> NodeLocation:
        """Marks the span [start_pos, end_pos[ up by adding one or more Node's
        with ``name``, eventually cutting through ``divisible`` nodes. Returns the
        nearest common ancestor of ``start_pos`` and ``end_pos``.

        Use of this method is discouraged. Instead, the use of the more general method
        :pa:meth:`markup` is recommended for which this special case method merely
        is a building block - just like the various top-level markup-methods.

        :param start_pos:  The string-position of the first character to be marked
            up. Note that this is the position in the string-content of the tree
            over which the content mapping has been generated and not the position
            in the XML or any other serialization of the tree!
        :param end_pos:  The string-position after the last character to be included
            in the markup. Similar to the slicing of Python lists
            or strings, the beginning and ending define a half-open intervall,
            [start_pos, ent_pos[. The character indexed by end_pos is not included
            in the markup. Also, keep in mind that ``end_pos`` is the position in
            the string-content of the tree over which the content mapping has been
            generated and not the positionvin the XML or any other serialization
            of the tree!
        :param tag_name:  The name of the element (or tag) to be added.
        :param attributes: A dictionary of attributes that will
            be added to the newly created tag.
        :param additional_attrs: Alternatively, the attributes can also be passed as a
            list of named parameters.

        :returns: The nearest (from the top of the tree) node, e.g. "ancestor", within
            which the entire markup lies as well as the first path-index of that
            ancestor.

        Examples::

            >>> from DHParser.nodetree import parse_sxpr
            >>> from DHParser.toolkit import printw
            >>> tree = parse_sxpr('(X (l ",.") (A (O "123") (P "456")) (m "!?") '
            ...                   ' (B (Q "789") (R "abc")) (n "+-"))')
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(2, 8, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (em (O "123") (P "456"))) (m "!?") (B (Q "789") (R "abc"))
             (n "+-"))
            >>> Y = copy.deepcopy(X)
            >>> t = ContentMapping(Y, divisibility={'bf': {':Text', 'em', 'A', 'P'}})
            >>> _ = t.add_markup(0, 7, 'bf')
            >>> printw(Y.as_sxpr(flatten_threshold=-1))
            (X (bf (l ",.") (A (em (O "123") (P "45")))) (A (em (P "6"))) (m "!?")
             (B (Q "789") (R "abc")) (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(2, 10, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (em (A (O "123") (P "456")) (m "!?")) (B (Q "789") (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X, divisibility={'A'})
            >>> _ = t.add_markup(5, 10, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123")) (em (A (P "456")) (m "!?")) (B (Q "789") (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(2, 13, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (em (A (O "123") (P "456")) (m "!?")) (B (em (Q "789")) (R "abc"))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(5, 16, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123") (em (P "456"))) (em (m "!?") (B (Q "789") (R "abc")))
             (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(5, 13, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123") (em (P "456"))) (em (m "!?")) (B (em (Q "789"))
             (R "abc")) (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(6, 12, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",.") (A (O "123") (P (:Text "4") (em "56"))) (em (m "!?"))
             (B (Q (em "78") (:Text "9")) (R "abc")) (n "+-"))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X)
            >>> _ = t.add_markup(1, 17, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l (:Text ",") (em ".")) (em (A (O "123") (P "456")) (m "!?") (B (Q "789")
             (R "abc"))) (n (em "+") (:Text "-")))
            >>> X = copy.deepcopy(tree)
            >>> t = ContentMapping(X, divisibility={'em': {'l', 'n'}})
            >>> _ = t.add_markup(1, 17, 'em')
            >>> printw(X.as_sxpr(flatten_threshold=-1))
            (X (l ",") (em (l ".") (A (O "123") (P "456")) (m "!?") (B (Q "789") (R "abc"))
             (n "+")) (n "-"))
        """
        assert end_pos >= start_pos
        if attributes is None:  attributes = {}
        attributes.update(additional_attrs)
        if start_pos == end_pos:
            milestone = Node(tag_name, '').with_attr(attributes)
            common_ancestor, path_index = self.insert_node(start_pos, milestone)
            return NodeLocation(common_ancestor, path_index)

        bag = []
        path_index, path_A, pos_A = self.get_location(start_pos)
        path_B, pos_B = self.get_path_and_offset(end_pos, left_biased=True)
        assert path_A
        assert path_B
        common_ancestor, i = find_common_ancestor(path_A, path_B)
        assert common_ancestor
        assert not common_ancestor.pick_if(lambda nd: nd.name == ':Text' and bool(nd.children),
                                           include_root=True), common_ancestor.as_sxpr()

        if self.chain_attr_name and self.chain_attr_name not in attributes:
            attributes[self.chain_attr_name] = gen_chain_ID()

        divisible = self.divisibility.get(tag_name, self.divisibility.get('*', frozenset()))

        if not common_ancestor._children:
            attributes.pop(self.chain_attr_name, None)
            markup_leaf(common_ancestor, pos_A, pos_B, tag_name, attributes)
            if ((not self.greedy or common_ancestor.name[0:1] == ":") and i != 0
                    and (common_ancestor.name in divisible or common_ancestor.anonymous)):
                for child in common_ancestor.children:
                    if child.name == TOKEN_PTYPE:
                        child.name = common_ancestor.name
                        child.with_attr(common_ancestor.attr)
                    elif not common_ancestor.anonymous:
                        assert child.name == tag_name
                        assert not child._children
                        child.result = Node(common_ancestor.name, child.result).with_attr(common_ancestor.attr)
                ur_ancestor = path_A[i - 1]
                t = ur_ancestor.index(common_ancestor)
                ur_ancestor.result = ur_ancestor[:t] + common_ancestor.children + ur_ancestor[t + 1:]
                common_ancestor = ur_ancestor
            assert not (common_ancestor.name == ':Text' and common_ancestor.children)
            if self.auto_cleanup:
                self.rebuild_mapping_slice(self.get_path_index(start_pos),
                                           self.get_path_index(end_pos, left_biased=True))
            return NodeLocation(common_ancestor, path_index)

        stump_A = path_A[i:]
        stump_B = path_B[i:]

        q = can_split(
            stump_A, pos_A, False, self.greedy, self.select_func, self.ignore_func, divisible)
        r = can_split(
            stump_B, pos_B, True, self.greedy, self.select_func, self.ignore_func, divisible)

        # BEWARE: the following deep_spit()-calls mess up the paths self._path_list from path_A
        #         through to path_B from common_ancestor downwards!

        i = -1
        k = -1
        if q < abs(q) == len(stump_A) - 1:
            i = deep_split(stump_A, pos_A, False, self.greedy, self.select_func,
                           self.ignore_func, self.chain_attr_name)
        if r < abs(r) == len(stump_B) - 1:
            k = deep_split(stump_B, pos_B, True, self.greedy, self.select_func,
                           self.ignore_func, self.chain_attr_name)

        if i >= 0 and k >= 0:
            attributes.pop(self.chain_attr_name, None)
            nd = Node(tag_name, common_ancestor[i:k]).with_attr(attributes)
            nd._pos = common_ancestor[i]._pos
            common_ancestor.result = common_ancestor[:i] + (nd,) + common_ancestor[k:]
        elif i >= 0:
            t = common_ancestor.index(stump_B[1])
            nd = Node(tag_name, common_ancestor[i:t]).with_attr(attributes)
            nd._pos = common_ancestor[i]._pos
            markup_left(stump_B[1:], pos_B, tag_name, attributes,
                        self.greedy, self.select_func, self.ignore_func,
                        divisible, self.chain_attr_name)
            common_ancestor.result = common_ancestor[:i] + (nd,) + common_ancestor[t:]
        elif k >= 0:
            t = common_ancestor.index(stump_A[1])
            nd = Node(tag_name, common_ancestor[t + 1:k]).with_attr(attributes)
            nd._pos = common_ancestor[t + 1]._pos
            markup_right(stump_A[1:], pos_A, tag_name, attributes,
                         self.greedy, self.select_func, self.ignore_func,
                         divisible, self.chain_attr_name)
            common_ancestor.result = common_ancestor[:t + 1] + (nd,) + common_ancestor[k:]
        else:
            t = common_ancestor.index(stump_A[1])
            u = common_ancestor.index(stump_B[1])
            markup_right(stump_A[1:], pos_A, tag_name, attributes,
                         self.greedy, self.select_func, self.ignore_func,
                         divisible, self.chain_attr_name)
            markup_left(stump_B[1:], pos_B, tag_name, attributes,
                        self.greedy, self.select_func, self.ignore_func,
                        divisible, self.chain_attr_name)
            if u - t > 1:
                nd = Node(tag_name, common_ancestor[t + 1:u]).with_attr(attributes)
                nd._pos = common_ancestor[t + 1]._pos
                common_ancestor.result = common_ancestor[:t + 1] + (nd,) + common_ancestor[u:]

        if self.auto_cleanup:
            self.rebuild_mapping_slice(self.get_path_index(start_pos, left_biased=True),
                                       self.get_path_index(end_pos, left_biased=False))
            # TODO: add a suitable unit-test a case to demonstrate that left_biased=True and
            #       left_biased=False parameter values are indeed neded! They are, to be sure!
        return NodeLocation(common_ancestor, path_index)
        # assert not common_ancestor.pick_if(lambda nd: nd.name == ':Text' and bool(nd.children),
        #     include_root=True), common_ancestor.as_sxpr()
        # return NodeLocation(common_ancestor, path_index)

    def markup(self, start_pos: cython.int,
               end_pos: cython.int,
               name: str,
               exclude_regions: Sequence[Union[Range, Tuple[int, int]]] = [], *,
               use_cache: bool = False,
               attributes: Optional[Dict] = None, **additional_attrs) -> Optional[NodeLocation]:
        """Marks the span [start_pos, end_pos[ up by adding one or more Node's
        with ``name``, eventually cutting through ``divisible`` nodes and
        - in contrast to :py:meth:`add_markup` - circumventing "excluded" regions.
        Returns the nearest common ancestor of ``start_pos`` and ``end_pos``.

        :param start_pos:  The string-position of the first character to be marked
            up. Note that this is the position in the string-content of the tree
            over which the content mapping has been generated and not the position
            in the XML or any other serialization of the tree!
        :param end_pos:  The string-position after the last character to be included
            in the markup. Similar to the slicing of Python lists
            or strings, the beginning and ending define a half-open intervall,
            [start_pos, ent_pos[. The character indexed by end_pos is not included
            in the markup. Also, keep in mind that ``end_pos`` is the position in
            the string-content of the tree over which the content mapping has been
            generated and not the position in the XML or any other serialization
            of the tree!
        :param name:  The name, or "tag-name" in XML-terminology, of the element
            (or tag) to be added.
        :param exclude_regions: A sequence of ranges that will be excluded from
            the markup. If any of these ranges lies within [start_pos, end_pos[,
            the markup will be split in two or more non-contiguous regions!
            Note that the regions are a) interpreted a) as half-open intervalls
            [low, high[ and b) related to the exhaustive string content of the
            root-Node ("origin") of the content mapping ``cm``, not to cm.content!
            The regions can be generated with :py:func:`content_ranges` in case
            you'd like to exclude particular tags or path-patterns.
        :param use_cache: If exclude_regions is not empty, markup
            will build itself an exhaustive mapping that spans the tree of the
            common ancestor for the interval [start_pos, end_pos[ to add markup
            that leaves out the excluded ranges. If markup is called
            several times in sequence, use_cache prevents recomputing this mapping
            when it is not necessary. If use_cache is True, no other tree-changing
            operations should be performed between the calls to markup and at the
            end of the sequence of cached markup calls :py:meth:`flush_markup_cache`
            should be called.
        :param attr_dict: A dictionary of attributes that will
            be added to the newly created tag.
        :param attributes: Alternatively, the attributes can also be passed as a
            list of named parameters.

        :returns: The nearest (from the top of the tree) node, e.g. "ancestor", within
            which the entire markup lies as well as the first path-index of that
            ancestor.
        """
        if attributes is None:
            if isinstance(exclude_regions, Dict):
                attributes = exclude_regions
                exclude_regions = []
            else:
                attributes = {}
        for ambigue in ('exclude', 'exclude_ranges'):
            if ambigue in additional_attrs:
                value = additional_attrs[ambigue]
                if (isinstance(value, Iterable) and
                        all((isinstance(it, Sequence) and len(it) == 2) for it in value)):
                    raise ValueError(
                        f'Wrong argument name: Use "exclude_regions=" instead of "{ambigue}="! '
                        f'In case "{ambigue}" was really meant to be an attribtue, use '
                        f'"attributes={{{ambigue}:{value}}}"!')
        if not exclude_regions:
            if not use_cache:  self._fullcm = None
            return self.add_markup(start_pos, end_pos, name,
                                   attributes=attributes, **additional_attrs)
        if not is_sorted_and_merged(exclude_regions):
            raise ValueError('The sequence passed to parameter exclude_regions '
                             f'has not beensorted and merged: {exclude_regions} ' 
                             'Please run it through sort_and_merge(regsions), first!')

        attributes.update(additional_attrs)
        if self._fullcm is None or self.origin != self._fullcm.origin:
            si = self.get_path_index(start_pos)
            ca, k = find_common_ancestor(self.path(si), self.get_path(end_pos - 1))
            while (si > 0 and len(self._path_list[si - 1]) > k
                   and self._path_list[si - 1][k] == ca):
                si -= 1
            offset = self._pos_list[si]
            assert ca is not None
            if self._fullcm is None or self._fullcm.origin is not ca:
                self._fullcm = ContentMapping(ca, select=LEAF_PATH, ignore=NO_PATH,
                                              greedy=self.greedy, divisibility=self.divisibility,
                                              chain_attr_name=self.chain_attr_name,
                                              auto_cleanup=True, sourcemap=False)
                self._fullcm_offset = offset
        else:
            offset = self._fullcm_offset
        a = self.sourcemap.srcpos(start_pos)
        b = self.sourcemap.srcpos(end_pos)
        rr = range_difference([(a, b)], exclude_regions)
        if not rr:  return None
        nl = [self._fullcm.add_markup(r[0] - offset, r[1] - offset, name,
                                      attributes, **additional_attrs)
              for r in rr]
        if len(nl) == 1:  return nl[0]
        p = self._fullcm.path(nl[0][1])
        ca, _ = find_common_ancestor(p, self._fullcm.path(nl[1][1]))
        for i in range(2, len(nl)):
            ca2, _ = find_common_ancestor(p, self._fullcm.path(nl[i][1]))
            for nd in p:
                if nd is ca:
                    break
                if nd is ca2:
                    ca = ca2
                    break
        start_idx = self.get_path_index(start_pos)
        end_idx = self.get_path_index(end_pos)
        if self.auto_cleanup:
            self.rebuild_mapping_slice(start_idx, end_idx)
        if not use_cache:  self._fullcm = None
        pi = self.get_node_index(ca, reverse=False, start_idx=start_idx, end_idx=end_idx)
        return NodeLocation(ca, pi)


class LocalContentMapping(ContentMapping):
    """A context-mapping (see :py:class:`ContentMapping`) that does not span
    the complete tree, but a section between two paths.

    EXPERIMENTAL AND UNTESTED!!!
    """

    def __init__(self, start_path: Path, end_path: Path,
                 select: PathSelector = LEAF_PATH,
                 ignore: PathSelector = NO_PATH,
                 greedy: bool = True,
                 divisibility: Union[Dict[str, Container], Container, str] = DIVISIBLES,
                 chain_attr_name: str = '',
                 auto_cleanup: bool = True):
        ancestor, index = find_common_ancestor(start_path, end_path)
        if ancestor is None:
            raise AssertionError(f'start_path: {pp_path(start_path)} and end_path: '
                                 f'{pp_path(end_path)} do not belong to the same tree!')
        else:
            super().__init__(ancestor, select, ignore, greedy, divisibility,
                             chain_attr_name, auto_cleanup)
        self.stump: Path = start_path[:index]
        start_path_tail = start_path[index:]
        end_path_tail = end_path[index:]
        for i in range(len(self._path_list)):
            if self._path_list[i] == start_path_tail:
                self.first_index = i
                break
        else:
            i = 0
            self.first_index = 0
        for k in range(i, len(self._path_list)):
            if self._path_list[k] == end_path_tail:
                self.last_index = k
                break
        else:
            k = len(self._path_list) - 1
            self.last_index = k
        self.pos_offset: int = strlen_of(tuple(path[-1] for path in self._path_list[:i]))
        pathL, posL = self._gen_local_path_and_pos_list(i, k)
        self.local_path_list: List[Path] = pathL
        self.local_pos_list: List[int] = posL

    def _gen_local_path_and_pos_list(self, i: cython.int, k: cython.int):
        return ([(self.stump + path) for path in self._path_list[i:k + 1]],
                [pos - self.pos_offset for pos in self._pos_list[i:k + 1]])

    @ContentMapping.path_list.getter
    def _(self) -> List[Path]:
        return self.local_path_list

    @ContentMapping.pos_list.getter
    def _(self) -> List[int]:
        return self.local_pos_list

    def get_path_index(self, pos: int, left_biased: bool = False) -> int:
        return super().get_path_index(pos + self.pos_offset, left_biased) - self.first_index

    def get_path_and_offset(self, pos: int, left_biased: bool = False,
                            index_out: Optional[List[int]] = None) -> Tuple[Path, int]:
        pth, off = super().get_path_and_offset(pos + self.pos_offset, left_biased, index_out)
        return pth, off - self.pos_offset

    def get_location(self, pos: int, left_biased: bool = False) -> LocationInfo:
        idx, pth, off = super().get_location(pos + self.pos_offset, left_biased)
        return LocationInfo(idx, pth, off - self.pos_offset)

    def iterate_paths(self, start_pos: int, end_pos: int, left_biased: bool = False) \
            -> Iterator[Path]:
        yield from super().iterate_paths(
            start_pos + self.pos_offset, end_pos + self.pos_offset, left_biased)

    def rebuild_mapping_slice(self, first_index: int, last_index: int):
        super().rebuild_mapping_slice(first_index + self.first_index,
                                      last_index + self.first_index)
        self.local_path_list, self.local_pos_list = \
            self._gen_local_path_and_pos_list(self.first_index, self.last_index)

    def rebuild_mapping(self, start_pos: int, end_pos: int):
        super().rebuild_mapping(start_pos + self.pos_offset, end_pos + self.pos_offset)

    def insert_node(self, pos: int, node: Node, left_biased: bool = False) -> NodeLocation:
        return super().insert_node(pos + self.pos_offset, node, left_biased)

    def add_markup(self, start_pos: int, end_pos: int, tag_name: str,
                   *attributes, **additional_attrs) -> NodeLocation:
        return super().add_markup(start_pos + self.pos_offset, end_pos + self.pos_offset, tag_name,
                                  *attributes, **additional_attrs)


class SerPart(IntEnum):
    OPENING_TAG = -1
    INSIDE = 0
    CLOSING_TAG = 1


class SerLocation(NamedTuple):
    """A location within a serialized version of the tree (XML, S-expression, SXML)."""
    path: Path
    ser_pos: int
    offset: int
    part: SerPart


class SerializationMapping:
    """Maps serializations (e.g., XML, SXML, S-Expression) to paths. EXPERIMENTAL AND UNTESTED!!!"""

    def __init__(self, tree: Node, serialization: str, raw_mapping: RawMappingType):
        assert serialization[0:1] in ('(', '<'), "XML- or S-Expression-serialization expected!"
        self.tree = tree
        self.serialization = serialization
        self.ser_type = "XML" if serialization[0:1] == '<' else "S-Expression"
        self.raw_mapping = raw_mapping
        self._cook()

    def _cook(self):
        self._path: Dict[Node, Path] = {}
        self._node_list: List[Node] = []
        self._pos_list: List[int] = []
        self._node_pos: Dict[Node, int] = {}

        def cook(path: Path, pos: int) -> int:
            _begin = pos
            node = path[-1]
            self._node_list.append(node)
            self._node_pos[node] = pos
            self._pos_list.append(pos)
            self._path[node] = path.copy()
            pos += self.raw_mapping[node][0]  # add head-length to pos
            if node.children:
                for child in node.children:
                    path.append(child)
                    pos = cook(path, pos)
                    path.pop()
            else:
                pos += (cast(int, self.raw_mapping[node][1])
                        - self.raw_mapping[node][0]
                        - self.raw_mapping[node][2])
            self._node_list.append(node)
            self._pos_list.append(pos)
            pos += self.raw_mapping[node][2]
            assert _begin + cast(int, self.raw_mapping[node][1]) == pos, \
                f'{_begin}, {pos}, {self.raw_mapping[node]}, {node.as_sxpr()}'
            return pos

        cook([self.tree], 0)

    def get_path(self, pos: int, left_biased: bool = False) -> SerLocation:
        """Returns the path of the innermost node which covers the character
        at position ``pos`` in the serialization. The second return value is
        the position of the node within the serialization. The
        third return value is -1 if the character is part of the opening tag,
        0 if it is part of the data, and 1 if it is part of the closing tag.

        The offset of `pos` within the node's serialization can easily be
        dtermined by subtracting from pos the returned serialization-position
        of the node at the end of the returned path."""
        errmsg = lambda i: f'Illegal position value {i}. Must be ' \
                           f'0 <= position < length of serialization ({len(self.serialization)})!'
        if pos < 0:  raise IndexError(errmsg(pos))
        import bisect
        try:
            index = bisect.bisect_right(self._pos_list, pos) - 1
            if left_biased:
                while index > 0 and pos - self._pos_list[index] == 0:
                    index -= 1
            else:
                last = len(self._pos_list) - 1
                pivot = self._pos_list[index]
                while index < last and self._pos_list[index + 1] == pivot:
                    index += 1
        except IndexError:
            raise IndexError(errmsg(pos))
        node = self._node_list[index]
        ser_pos = self._node_pos[node]
        offset = pos - ser_pos
        rm_node_1 = cast(int, self.raw_mapping[node][1])
        assert 0 <= offset <= rm_node_1
        part = -1 if offset < self.raw_mapping[node][0] else \
            1 if offset >= rm_node_1 - self.raw_mapping[node][2] else \
                0
        return SerLocation(self._path[self._node_list[index]], ser_pos, offset, SerPart(part))

    def content_pos(self, node: Node,
                    ser_pos: int,
                    offset: int,
                    part: SerPart = SerPart.INSIDE) -> int:
        """Returns the corresponding position within the pure string content
        of the tree."""
        assert not node._children
        if part < 0: return 0
        if part > 0: return node.strlen()
        mapping = self.raw_mapping[node]
        head, overall, tail = mapping[0], cast(int, mapping[1]), mapping[2]
        offset = offset - head
        if offset < 0: return 0
        if offset >= overall - tail:
            return node.strlen()
        ser_len = overall - head - tail
        if self.ser_type == "XML":
            if ser_len != node.strlen():
                raise ValueError(
                    'Position within the (pure) string-content cannot be determined for '
                    'formatted serialization! Use root.as_xml(inline_tags=={root.name}) '
                    'for an unformatted XML serialization!')
            return offset
        else:  # self.ser_type == "S-Expression"
            ser_content = self.serialization[ser_pos: ser_pos + overall]
            stripped = ser_content.lstrip()  # remove leading blanks
            stripped = stripped.lstrip(stripped[0])  # remove leading quotation marks
            if stripped.startswith(node.content):
                return offset
            else:
                raise ValueError(
                    'Position within the (pure) string-content cannot be determined for '
                    'formatted serialization or for serializations that happen to contain '
                    'escaped quotation marks. Try a flatten_sxpr(tree.as_sxpr()) '
                    'to rule out the first cause!')

# if __name__ == "__main__":
#     st = parse_sxpr("(alpha (beta (gamma i\nj\nk) (delta y)) (epsilon z))")
#     print(st.as_sxpr())
#     print(st.as_xml())
