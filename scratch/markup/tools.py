import sys, os

modulepath = os.path.dirname(__file__) or '.'
abspath = os.path.abspath(modulepath)
if abspath.find('/DHParser/') >= 0 or abspath.find('\\DHParser\\') >= 0:
    sys.path.append(os.path.abspath(os.path.join(modulepath, '..', '..')))
modulepath = abspath

try:
    from DHParser.nodetree import (Node,)
except ImportError as e:
    raise ImportError("Bitte installiere DHParser mit python3 -m pip install DHParser!")


# WARNING: pull_up or pull_out shouldn't be used because they change grandparents
#          which potentially messes up tree-traversal...

def _pull_up_or_out(path, keep_markup: bool):
    """See :py:meth:`pull_up` and :py:meth:`pull_out`."""
    node = path[-1]
    if len(path) <= 2:
        return
    parent = path[-2]
    ur_parent = path[-3]
    try:
        i = parent.index(node)
        i2 = ur_parent.index(parent)
    except ValueError:
        parent = path[0].find_parent(node)
        ur_parent = path[0].find_parent(parent)
        i = parent.index(node)
        i2 = ur_parent.index(parent)
    if keep_markup:
        node._set_result(Node(parent.name, node.result).with_pos(node._pos).with_attr(parent.attr))
    children = ur_parent._children
    inlay = []
    if i > 0:
        inlay.append(Node(parent.name, parent[:i]).with_pos(parent._pos).with_attr(parent.attr))
    inlay.append(node)
    if i < len(parent.children) - 1:
        inlay.append(Node(parent.name, parent[i + 1:]).with_pos(parent[i + 1]._pos).with_attr(parent.attr))
    ur_parent._set_result(children[:i2] + tuple(inlay) + children[i2 + 1:])

def pull_up(path, keep_markup: bool = True):
    """Moves the last Node in the list one level up in the hierarchy but
    leaving markup intact. This means that a single child of the same type
    and with the same attributes as the parent node will be added to the
    moved up node that takes the content the node had before moving up.
    (See examples, below!) Use :py:func:`pull_out` if you don't want to
    keep the markup intact.

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
    """
    _pull_up_or_out(path, keep_markup=True)


def pull_out(path):
    """Moves the last Node in the list one level up in the hierarchy,
    breaking up the surrounding markup. Use :py:func:`pull_up` if you
    want to keep the surrounding markup intact.

    >>> tree = parse_sxpr('(p (t "A") (i (t "1") (X "---") (t "2")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_out(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (i (t "1")) (X "---") (i (t "2")) (t "B"))

    >>> tree = parse_sxpr('(p (t "A") (i (X "---") (t "2")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_out(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (X "---") (i (t "2")) (t "B"))

    >>> tree = parse_sxpr('(p (t "A") (i  (t "1") (X "---")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_out(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (i (t "1")) (X "---") (t "B"))

    >>> tree = parse_sxpr('(p (t "A") (i (X "---")) (t "B"))')
    >>> path = tree.pick_path('X')
    >>> pull_out(path)
    >>> print(tree.as_sxpr())
    (p (t "A") (X "---") (t "B"))
    """
    _pull_up_or_out(path, keep_markup=False)