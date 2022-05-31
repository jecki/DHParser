AST-Transformation
==================

Module ``transform`` provides means for quasi-declarative transformation of trees, with
a focus of transforming concrete syntax trees to abstract syntax trees or, more generally,
simplifying and streamlining syntax trees in a much for fine-grained manner than is
possible at the parsing stage (see :ref:`simplifying_syntax_trees`).

A "concrete syntax tree" (CST) is a data tree, the structure of which represents the grammatical
structure of a text according to a given grammar. If unabridged, the concatenated content of
all leaf-nodes of the concrete syntax tree yields the text original document. Thus, the shape
and the content of the concrete syntax tree is precisely determined by the grammar and the
text-document which must be written in a language adhering to this grammar.

The structure of the "abstract syntax tree" (AST) is a tree structure that represents the data of
the parsed document in a form that is suitable for a given purpose. In the context of a
programming language the AST often represents a structure that can be executed by an interpreter
or compiled into a machine language, or more generally, a lower level language by a compiler.
Because the shape of the AST depends on its purpose, the abstract syntax tree cannot logically
be derived from the concrete syntax tree, but the transformation of the CST to the
AST must be specified (or programmed) separately from the grammar.

In pure data-processing contexts, the concept of the the abstract syntax tree is of much less import
than in the field of compiler building. Typically, the data passes through several
stages of tree-transformation after being parsed. This can be stages like "data tree" and
"output tree", after which the transformation pipeline may even be split up to
yield a "print-output tree" and "screen-output-tree" both of which are directly derived
from the "output tree". Here, the abstract syntax tree, if that notion is used at all,
merely signifies the a further streamlined version of the concrete syntax tree.

DHParser offers two different kinds of scaffolding for for tree-transformation, one contained
in the module :py:mod:`DHParser.transform` which follows a functional and declarative style,
and one contained in module :py:mod:`DHParser.compile` which follows a classical object-oriented style.
Both are different installments of the well known `visitor pattern <https://en.wikipedia.org/wiki/Visitor_pattern>`_.
However, the former is only suitable for in place tree transformations which yield another tree structure as its
result, while the latter can also be used
to transform the tree into a different kind of object, like for example program-code. (Thus, the name "compile"
for this module.)

The assumption behind this is that for the transformation
of concrete syntax trees into abstract syntax trees or, more generally, the streamlining of syntax trees,
the leaner functional style is preferable, while for more complex tree-transformations or the
transformation of a syntax tree into something else the more
powerful object-oriented version of the visitor pattern is to be preferred, because it allows to exchange
data between the visiting methods via the :py:class:`~compile.Compiler`-object to which they are attached.
There is of course not "must" to use the ``transform`` and the ``compile``-module for their envisioned
purposes, but you can choose freely which transformation-scaffolding to use for which of your tree-transformations.

In the following the functional and declarative scaffolding for tree transformations provided
by the module :py:mod:`DHParser.transform` will be described.


Declarative Tree-Transformation
-------------------------------

Declarative tree-transformations are realized via functions that take a :ref:`trail <trails>`
as argument and which are organized in a dictionary that maps tag-names to sequences of such
transformation functions which are called on every node with that tag-name. The tree as whole
is traversed depth-first. Module :py:mod:`DHParser.transform` provides a large number of
predefined transformation functions that can be combined to transform the tree in the desired
manner.

To demonstrate how declarative tree-transformations via the functional-style visitor pattern work,
we'll take a parser for simple arithmetic formulas as an example:

    >>> arithmetic_ebnf = '''
    ... @ whitespace  = vertical             # implicit whitespace, includes any number of line feeds
    ... @ literalws   = right                # literals have implicit whitespace on the right hand side
    ... @ comment     = /#.*/                # comments range from a '#'-character to the end of the line
    ... @ ignorecase  = False                # literals and regular expressions are case-sensitive
    ... @ drop        = whitespace, strings  # drop insignificant whitespace and unnamed string literals
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

This syntax tree is already devoid of superfluous characters such as the brackets
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
a string-key that contains a comma-separated list of node-names will be interpreted
as so many different keys that are mapped onto the same sequence of
transformations.

Next, we traverse the tree and call each of the transformations
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
   on a particular node, or rather trail (see :ref:_trails), all
   children of that node have already been transformed.

2. As any other tree transformation method in DHParser, function
   :py:func:`~transform.traverse` transforms trees *in place*.
   So, if for some reason you need to preserve earlier states of the
   tree, you'll have to make a `deep copy <https://docs.python.org/3/library/copy.html#copy.deepcopy>`_ first.

The resulting tree looks much closer to the syntax tree of an arithmetic formula we had in mind.
Every one-term "expression", "term", "factor" etc. has essentially been replaced by
what it is. Now, we'd still like to do this for the two-term expressions. Since this
is an operation which is specific to our arithmetic example, we would not expect
module :py:mod:`DHParser.transform` to already contain such an operation (although
in this particular case, in fact, it does). But we can write a suitable transformation
on our own, easily::

   >>> from DHParser.nodetree import Node, Trail
   >>> def left_associative(trail: Trail):
   ...     "Re-arranges a flat node with infix operators into a left associative tree."
   ...     node = trail[-1]
   ...     if len(node._children) >= 3:
   ...         assert (len(node._children) + 1) % 2 == 0
   ...         rest = list(node._children)
   ...         left, rest = rest[0], rest[1:]
   ...         while rest:
   ...             infix, right, rest = rest[0], rest[1], rest[2:]
   ...             assert not infix._children
   ...             assert infix.name[0:1] != ":"
   ...             left = Node(infix.name, (left, right))
   ...         node.result = (left,)

A transformation function is a function with the tree-trail as single argument and
no return value. The tree-trail is the list of all nodes on the path from the
root node of the tree up to and including the node that shall be transformed.
It is good practice that transformations only change the last node in the trail-list
and its children (which have already been transformed by the time this node
has been reached by :py:func:`~transform.traverse`), but not any parents or siblings
in the trail. The trail, rather than the node alone, is passed to transformation
function only in order to enable it to query the parents or siblings in order to allow
the transformation to make choices depending on the trail. This said, it sometimes
makes sense to deviate from this rule, none the less.

The just defined function does nothing if the last node in the trail-list (which is
the node that is just being visited during the tree-traversal and which
the transformation-function should operate on) has three or more children. If so, it
is assumed that the children form a sequence of value interspersed with dyadic
operators, e.g. "3 + 4 - 5 + 2". These will then be rearranged as (binary) tree assuming that
the operators are `left-associative <https://en.wikipedia.org/wiki/Operator_associativity>`_.
The nodes containing the operators will then be eliminated, but their tag-names will be
kept as tag-names of the nodes of the generated tree, so that the tag-name of each node
indicates the kind of operator while the children are the argument of the operation. For
example, ``(expression (NUMBER "4") (PLUS "+") (NUMBER "5"))`` will become
``(PLUS (NUMBER "4") (NUMBER "5"))``. Thus, in the resultant abstract syntax tree,
the structure of the formula is expressed by the structure of the tree.

The function ``left_associative()`` can only be meaningfully applied to "term" and "expression"-nodes. So,
we have to split our transformation table up in order to apply it only
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
            ...            'NUMBER': float,
            ...            'VARIABLE': eval }
            >>> formula_cst.evaluate(actions)
            27.0

See :py:meth:`~nodetree.Node.evaluate` in case you wonder what the last statement does.
(The ``evaluate()``-method of the :py:class:`~nodetree.Node`-class is actually a third
and most trivial installment of the visitor-pattern in DHParser.)



The Transformation Table
------------------------

As shown by the examples earlier, the transformation table is a "smart" dictionary
that maps tag-names to sequences of transformation functions. It is called "smart",
because it allows to list several tag names within one and the same dictionary
keys, thus assigning each one of them to one and the same sequences of transformation
functions. (You could think of the transformation table as a simple "embedded" or
`internal DSL (Domain Specific Languag) <https://martinfowler.com/bliki/DomainSpecificLanguage.html>`_
realized within Python, if you liked.) This is quite useful, because it allows to cover similar idioms used at
different places of a grammar (and with different tag-names) with the same sequence
of transformation functions, without having to type the same list of functions
over and over again.

The transformation table has three special keys: ``<``, ``>``, ``*``. The asterix ``*`` is a joker,
which means that the sequence of transformations assigned to the asterix will be called for
every node, the tag-name of which does not occur in the table. The ``<``-key marks a sequence of functions
that will be executed before any of the individual sequences assigned to particular tag-names (including the
joker ``*``) will be executed. The ``>``-key takes a transformation-sequence that will be executed after
every tag-specific transformation-sequence has been processed. Because of the time-penalty incurred, the
``<``- and ``>``-keys should only be used when really needed. Most of the time the desired result can
be achieved more effectively with the ``@disposable``- and ``@drop``-directives at the
parsing-stage, already (see :ref:`simplifying_syntax_trees`)).

To give a better impression of how tree-transformation works and what primitives the transformation-module
provides, here is an excerpt from the transformation-table of the LaTeX-Parser example::

    LaTeX_AST_transformation_table = {
        "hide_from_toc, no_numbering": replace_content_with(''),
        "_known_environment": replace_by_single_child,
        "inline_math": reduce_single_child,
        "paragraph": strip(is_one_of({'S'})),
        "text, urlstring": collapse,
        "ESCAPED": [apply_ifelse(transform_content(lambda result: result[1:]),
                                 replace_content_with('~'),
                                 lambda ctx: '~' not in ctx[-1].content)],
        "UMLAUT": replace_Umlaut,
        "QUOTEMARK": replace_quotationmark,
        ":Whitespace, _WSPC, S": streamline_whitespace,
        "WARN_Komma": add_error('No komma allowed at the end of a list', WARNING),
        # ...
    }

The first entry of the dictionary turns nodes with the either of the names "hide_from_toc" or "no_numbering"
into empty nodes, which is reasonable, because these markers which in the LaTeX-source consist of a simple asterix that is
appended to a section-command or a command for an equation array shall not
be printed as part of the text. At the same time, it is reasonable to keep the empty nodes as flags to
indicate to latter processing stages that a certain section or chapter shall not appear in the table
of contents or the numbering of an equation array shall be suppressed.

The second entry replaces any node with the name "_known_environment" by its single child in case it has only one child.
(See :py:func:`DHParser.transform.replace_by_single_child`.)
This is a very useful transformation rule for symbols that are defined as alternatives in the grammar. In the file ``LaTeX.ebnf`` 
the "_known_environment"-symbols is defined as 
``_known_environment = itemize | enumerate | description | figure | tabular | quotation | verbatim | math_block``. For any 
such known environment, the concrete syntax tree consists of a node of with the name "_known_environment" that contains
the actual environment as a single child, say:: 

    (_known_environment
      (enumerate
        (item ...)
        (item ...)
        ...
      )
    )


(This can easily be checked by marking one or more of the environment-tests in the
"test_grammar"-subfolder of the LaTeX-example with an asterix so as to show the concrete syntax tree in the test report.)
Now, since we are only interested in the actual environment, it is only reasonable to replace any "_known_environment"-node
in the concrete syntax tree by the actual environment it contains as its single child node. 

The same effect can also be achieved by early tree-reduction during the parsing stage 
(see :ref:`Simplifying Trees <_simplifying_syntax_trees>` in the documentation of the :doc:`ebnf`-module.) by listing
the symbol "_known_environment" in the ``@disposable``-directeive at the beginning of the grammar. In cases as simple 
as this one, it is preferable way to eliminate superfluous nodes as early as possible by using the ``@disposable``-directive.

The opposite case where you want to reatain the parent node but eliminate a single child is demonstrated by the following
entry. The symbol "inline_math" is meant to mark mathematical notation that occurs within the text of a paragraph. 
LaTeX has two different sets of symbols, ``\( ... \)`` and ``$ ... $`` to mark the begining and end of a stretch of
inline maths, which are captured by "_im_bracket" and "_im_dollar"-symbol, respectively. Thus, "inline_math" is defined
in the grammar as ``inline_math = _im_bracket | _im_dollar``. Hower, this time we are only interested in the fact that
some piece of text is a piece of inline math and not what set of delimiters has been used to mark it as such. Therefore
we use the :py:func:`DHParser.transform.reduce_single_child`-primitive to eliminate the child node while transfering it data to the parent.

Again, the same can more efficiently be achieved by adding the symbols "_im_bracket" and "_im_dollar" to the list
of disposable symbols at the top of the grammar. However, when still developing the grammar, it can, for debugging purposes, 
still be helpful to eliminate them during the tree-transformation stage and not already while parsing. Once it has been
superseeded by the disposable directive, the ``reduce_single_child``-primitive should be removed from the table, because -
other than the ``replace_by_single_child``-primitive it can produce undesired side effect if the child to be reduced to
its parent has already been eliminated earlier.

In the grammar of the LaTeX-example, the symbol "S" captures significant whitespace. However, at the beginning and 
the end of a paragraph, explicit whitespace is really unneccessary, because begining or ending a paragraph already
implies that there is a linefeed (and thus whitespace). The entry for the "paragraph" symbol therefore eliminates
whitespace that has been captured by the "paragraph"-parser at the beginning or the end. This is achieved with the 
:py:func:`DHParser.transform.strip`-primitive. Like the :py:func:`DHParser.transform.replace_content_with`-primitive
it takes an argument, only this time, the argument is another primitive (applied to the current trail of the 
node under inspection), namely :py:func:`DHParser.transform.is_one_of`, which returns true if the trail passed
to it ends with a node the name of which is one of a set of names. In this case this is the set with the
single element "S": ``strip(is_one_of({'S'}))``.

The following entry uses a rather trivial primitive, :py:func:`DHParser.transform.collapse` which simply replaces
the the result of the node to which it is applied by the concatenated string content of all of its children
(if any). Here it serves to yield the string content for sub-trees the structure of which is not relevant for
further processing. "urlstring", to pick this one out, is defined as ``urlstring = [protocol] { path } [target]``.
Each of the components of urlstring has a syntax of its own, which results in an intricate tree-structure when
parsed. 

Given that this structure is not relevant in the further processing of the parsed document one might
ask the question why not a very much simplified URL-parser might have been suficient. A possible reason for specifying
a detailed parser in cases where the structure does not matter is to capture syntax errors early on. Otherwise
a misspelled URL that hasn't been rejected by a simplified parser might cause trouble later on. In cases where
this is not to be feared simplified parsers are often a good choice, not in the least, 
because they usually increase parsing speed. The parser of the LaTeX-example uses simplified parsers for the mathematical 
notation, because this can be passed through to Javascript rendering libraries like `MathJax`_ or `KaTeX`_ as is.

The transformation rule for the "ESCAPED" symbol is more complex. Usually, escaping in LaTeX works simply by 
writing a backslash followed by the symbol that shall be escaped (i.e. not be interpreted as a control character but 
simply written out), e.g. "\#" writes a "#"-character instead of starting a comment which would be the usual 
meaning of the "#" in LaTeX. However, the case of the tilde "~" is more complicated, because if LaTeX encounters 
an escaped tilde character, it will try to write the tilde *above* the following character. In order to really get
a single tilde character one has to write "\~{ }" in LaTeX. The definition of the ESCAPED-symbol: 
``ESCAPED = /\\(?:(?:[#%$&_\/{} \n])|(?:~\{\s*\}))/`` knows about this special case. But this means that while 
usually just dropping the leading backslash "\" when unescaping a character during AST-transformation, we
need to eliminate the following characters, too, in the case of the tilde.

This case differentiation is effected by the :py:func:`DHParser.transform.apply_ifelse`-function which applies
one (list of) primitive(s) or an alternative (list of) primitive(s) depending on boolean condition. Note that
the the boolean condition is stated as the last term in the list of paramters of the ``apply_if_else``-operator.
 






Transformation Functions
------------------------

Parameterized Transformations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


Conditional Transformations
^^^^^^^^^^^^^^^^^^^^^^^^^^^


Writing Custom Functions
^^^^^^^^^^^^^^^^^^^^^^^^

Debugging the transformation-table
----------------------------------



*Functions-Reference*
---------------------

The full documentation of all functions can be found in module
:py:mod:`DHParser.transform`. The following table lists only the most
important of these:


.. _MathJAX: https://www.mathjax.org/
.. _KaTeX: https://katex.org/
