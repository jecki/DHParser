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
    ... factor     = [sign] (NUMBER | VARIABLE | group) { VARIABLE | group }
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
    >>> formula_cst = arithmetic_parser("3 + 4 * 5")
    >>> print(formula_cst.as_sxpr(flatten_threshold=0))


