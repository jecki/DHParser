AST-Transformation
==================

Module ``transform`` provides means for quasi-declarative transformation of trees, with
a focus of transforming concrete syntax trees to abstract syntax trees or, more generally,
simplifying and streamlining syntax trees in a much for fine-grained manner than is
possible at the parsing stage (see :ref:`simplifying_syntax_trees`).


Declarative Tree-Transformation
-------------------------------

Declarative tree-transformations are realized via functions that take a :ref:`context <contexts>`
as argument and which are organized in a dictionary that maps tag-names to sequences of such
transformation functions which are called on every node with that tag-name. The tree as whole
is traversed depth-first. Module :py:mod:`DHParser.transform` provides a large number of
predefined transformation functions that can be combined to transform the tree in the desired
manner. Let's take a parser for simple arithmetic formulas as an example:

    >>> arithmetic_ebnf = '''
    ... @ whitespace  = vertical             # implicit whitespace, includes any number of line feeds
    ... @ literalws   = right                # literals have implicit whitespace on the right hand side
    ... @ comment     = /#.*/                # comments range from a '#'-character to the end of the line
    ... @ ignorecase  = False                # literals and regular expressions are case-sensitive
    ... @ drop        = whitespace, strings  # drop anonymous whitespace
    ...
    ... expression = term  { (PLUS | MINUS) term}
    ... term       = factor { (DIV | MUL) factor}
    ... factor     = [sign] (NUMBER | VARIABLE | group)
    ... sign       = POSITIVE | NEGATIVE
    ... group      = "(" expression ")"
    ... PLUS       = "+"
    ... MINUS      = "-"
    ... MUL        = "*"
    ... DIV        = "/"
    ... POSITIVE   = /[+]/      # no implicit whitespace after signs
    ... NEGATIVE   = /[-]/
    ... NUMBER     = /(?:0|(?:[1-9]\\d*))(?:\\.\\d+)?/~
    ... VARIABLE   = /[A-Za-z]/~ '''
    >>> from DHParser.dsl import create_parser
    >>> arithmetic_parser = create_parser(arithmetic_ebnf)
    >>> formula_cst = arithmetic_parser("3 * (4 + 5)")
    >>> print(formula_cst.as_sxpr(flatten_threshold=0))
    (expression
      (term
        (factor
          (NUMBER "3"))
        (MUL "*")
        (factor
          (group
            (expression
              (term
                (factor
                  (NUMBER "4")))
              (PLUS "+")
              (term
                (factor
                  (NUMBER "5"))))))))

This syntax tree is already devoid of superflous characters such as the brackets
to delimit groups or the insignificant whitespace between the numbers and operators.
(The whitespace has been removed by the ``@drop = whitespace`` directive, while any
string that has not directly been assigned to a symbol has been removed by the
``@drop = strings``-directive. See :ref:`simplifying_syntax_trees`)
Still, the syntax tree is unnecessarily tedious and would therefore
also be overly complicated to evaluate. A concise syntax tree for arithmetic formulae
should resemble the formula in `prefix <https://en.wikipedia.org/wiki/Polish_notation>`_-notation
and look like ``* 3 + 45``. In order to arrive at a simpler representation, we begin by
replacing those nodes that contain merely a single child by its child. Now, any of the
following elements may (though doesn't have to) consist of a single child:
``sign, group, factor, term, expression``. A suitable transformation for this purpose is
the :py:func:`~transform.replace_by_single_child` which replaces a node by its single
child in case the node has exactly one child, no more, no less. To apply this
transformation to every node that has one of the above mentioned five tag-names,
we assign this function to these tag-names in the transformation dictionary or, as
we shall call it henceforth, "transformation table"::

    >>> from DHParser.transform import replace_by_single_child
    >>> transformation_table = { "sign, group, factor, term, expression":
    ...                             [replace_by_single_child] }

Note, that the transformation table is an ordinary Python-dictionary, only that
a string-key that contains a comma-separated list of tag_names will be interpreted
as so many different keys that are mapped onto the same sequence of
transformations. Next, we traverse the tree and call each of the transformations
in the list (which in this case is only one, namely, ``replace_by_single_child``)
on every node that has one of the tag-names in the key::

    >>> from DHParser.transform import traverse
    >>> from copy import deepcopy
    >>> save_cst = deepcopy(formula_cst)
    >>> _ = traverse(formula_cst, transformation_table)
    >>> print(formula_cst.as_sxpr(flatten_threshold=0))
    (term
      (NUMBER "3")
      (MUL "*")
      (expression
        (NUMBER "4")
        (PLUS "+")
        (NUMBER "5")))

Two things are important to know about :py:func:`~transform.traverse`:

1. Trees are transformed depth first. So, when a transformation is called
   on a particular node, or rather context (see :ref:contexts_), all
   children of that node have already been transformed.

2. As any other tree transformation method in DHParser, function
   :py:func:`~transform.traverse` transforms trees *in place*.
   So, if for some reason you need to preserve earlier states of the
   tree, you'll have to make a deep copy first.

The resulting tree looks much closer to the syntax tree of an arithmetic formula we had in mind.
Every one-term "expression", "term", "factor" etc. has essentially been replaced by
what it is. Now, we'd still like to do this for the two-term expressions. Since this
is an operation which is specific to our arithmetic example, we would not expect
module :py:mod:`DHParser.transform` to already contain such an operation (although
in this particlar case, in fact, it does). But we can write a suitable transformation
on our own, easily::

   >>> from DHParser.syntaxtree import Node, TreeContext
   >>> def left_associative(context: TreeContext):
   ...     "Re-arranges a flat node with infix operators into a left associative tree."
   ...     node = context[-1]
   ...     if len(node._children) >= 3:
   ...         assert (len(node._children) + 1) % 2 == 0
   ...         rest = list(node._children)
   ...         left, rest = rest[0], rest[1:]
   ...         while rest:
   ...             infix, right, rest = rest[0], rest[1], rest[2:]
   ...             assert not infix._children
   ...             assert infix.tag_name[0:1] != ":"
   ...             left = Node(infix.tag_name, (left, right))
   ...         node.result = (left,)

A transformation function is functions with the tree context as single argument and
no return value. The tree context is the list of all nodes on the path from the
root node of the tree up to and including the node that shall be transformed.
It is good practice that transformations only change the last node in the context-list
and its children (which have already been transformed by the time this node
has been reached by :py:func:`~transform.traverse`), but not any parents or siblings
in the context. The context, rather than the node alone, is passed to transformation
function only in order to enable it to query the parents or siblings in order to allow
the transformation to make choices depending on the context. This said, it sometimes
makes sense to deviate from this rule, none the less.

This function can only be meaningfully applied to "term" and "expression"-nodes. So
we have to split our transformation table up a little bit in order to apply it only
to nodes with these tag names::

    >>> transformation_table = { "term, expression":
    ...                              [left_associative, replace_by_single_child],
    ...                          "sign, group, factor":
    ...                              [replace_by_single_child] }

We still keep the transformation :py:func:`~transform.replace_by_single_child` in
the list of transformations for "term" and "expression"-node for those cases
where these nodes have only one child. Now, let's see what difference this makes::

    >>> formula_cst = deepcopy(save_cst)  # restore concrete syntax tree
    >>> _ = traverse(formula_cst, transformation_table)
    >>> print(formula_cst.as_sxpr(flatten_threshold=0))
    (MUL
      (NUMBER "3")
      (PLUS
        (NUMBER "4")
        (NUMBER "5")))

Now that our syntax tree has been properly transformed, using this tree to
calculate the result of the formula becomes a breeze::

            >>> from operator import add, sub, mul, truediv
            >>> actions = {'PLUS': add,
            ...            'MINUS': sub,
            ...            'MUL': mul,
            ...            'DIV': truediv,
            ...            'NUMBER': float}
            >>> formula_cst.evaluate(actions)
            27.0


*Functions-Reference*
---------------------

The full documentation of all functions can be found in module
:py:mod:`DHParser.transform`. The following table lists only the most
important of these: