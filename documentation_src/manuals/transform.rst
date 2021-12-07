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

    >>> from DHParser.transfrom import replace_by_single_child
    >>> transformation_table = { "sign, group, factor, term, expression":
                                    [replace_by_single_child] }

Note, that the transformation table is an ordinary Python-dictionary, only that
a string-key that contains a comma-separated list of tag_names will be interpreted
as so many different keys that are mapped onto the same sequence of
transformations. Next, we traverse the tree and call each of the transformations
in the list (which in this case is only one, namely, ``replace_by_single_child``)
on every node that has one of the tag-names in the key::

    >>> from DHParser.transform import traverse
    >>> traverse(formula_cst, transformation_table)
    >>> print(formula_cst.as_sxpr(flatten_threshold=0))





*Functions-Reference*
---------------------

The full documentation of all functions can be found in module
:py:mod:`DHParser.transform`. The following table lists only the most
important of these: