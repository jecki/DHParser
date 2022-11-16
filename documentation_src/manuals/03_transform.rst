AST-Transformation
==================

Module :py:mod:`transform` provides means for quasi-declarative transformation of
trees, with a focus of transforming concrete syntax trees to abstract syntax
trees or, more generally, simplifying and streamlining syntax trees in a much
for fine-grained manner than is possible at the parsing stage (see
:ref:`simplifying_syntax_trees`).

A "concrete syntax tree" (CST) is a data tree the structure of which represents
the grammatical structure of a text according to a given grammar. If unabridged,
the concatenated content of all leaf-nodes of the concrete syntax tree yields
the text original document. Thus, the shape and the content of the concrete
syntax tree is precisely determined by the grammar and the text-document which
must be written in a language adhering to this grammar.

The structure of the "abstract syntax tree" (AST) is a tree structure that
represents the data of the parsed document in a form that is suitable for a
given purpose. In the context of a programming language the AST often represents
a structure that can be executed by an interpreter or compiled into a machine
language, or more generally, a lower level language by a compiler. Because the
shape of the AST depends on its purpose, the abstract syntax tree cannot
logically be derived from the concrete syntax tree, but the transformation of
the CST to the AST must be specified (or programmed) separately from the
grammar.

In pure data-processing contexts, the concept of the the abstract syntax tree is
of much less import than in the field of compiler building. Typically, the data
passes through several stages of tree-transformation after being parsed. This
can be stages like "data tree" and "output tree", after which the transformation
pipeline may even be split up to yield a "print-output tree" and
"screen-output-tree" both of which are directly derived from the "output tree".
Here, the abstract syntax tree, if that notion is used at all, merely signifies
the a further streamlined version of the concrete syntax tree.

DHParser offers two different kinds of scaffolding for for tree-transformation,
one contained in the module :py:mod:`DHParser.transform` which follows a
functional and declarative style, and one contained in module
:py:mod:`DHParser.compile` which follows a classical object-oriented style. Both
are different installments of the well known `visitor pattern
<https://en.wikipedia.org/wiki/Visitor_pattern>`_. However, the former is only
suitable for in place tree transformations which yield another tree structure as
its result, while the latter can also be used to transform the tree into a
different kind of object, like for example program-code. (Thus, the name
"compile" for this module.)

The assumption behind this is that for the transformation of concrete syntax
trees into abstract syntax trees or, more generally, the streamlining of syntax
trees, the leaner functional style is preferable, while for more complex
tree-transformations or the transformation of a syntax tree into something else
the more powerful object-oriented version of the visitor pattern is to be
preferred, because it allows to exchange data between the visiting methods via
the :py:class:`~compile.Compiler`-object to which they are attached. There is of
course not "must" to use the ``transform`` and the ``compile``-module for their
envisioned purposes, but you can choose freely which transformation-scaffolding
to use for which of your tree-transformations.

In the following the functional and declarative scaffolding for tree
transformations provided by the module :py:mod:`DHParser.transform` will be
described.


Declarative Tree-Transformation
-------------------------------

Declarative tree-transformations are realized via functions that take a
:ref:`path <paths>` as argument and which are organized in a dictionary that
maps tag-names to sequences of such transformation functions which are called on
every node with that tag-name. The tree as a whole is traversed depth-first.
Module :py:mod:`DHParser.transform` provides a large number of predefined
transformation functions that can be combined to transform the tree in the
desired manner.

To demonstrate how declarative tree-transformations via the functional-style
visitor pattern work, we'll take a parser for simple arithmetic formulas as an
example::

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

This syntax tree is already devoid of superfluous characters such as the
brackets to delimit groups or the insignificant whitespace between the numbers
and operators. (The whitespace has been removed by the ``@drop = whitespace``
directive, while any string that has not directly been assigned to a symbol has
been removed by the ``@drop = strings``-directive. See
:ref:`simplifying_syntax_trees`) Still, the syntax tree is unnecessarily tedious
and would therefore also be overly complicated to evaluate. A concise syntax
tree for arithmetic formulae should resemble the formula in `prefix
<https://en.wikipedia.org/wiki/Polish_notation>`_-notation and look like ``* 3 +
45``. In order to arrive at a simpler representation, we begin by replacing
those nodes that contain merely a single child by its child. Now, any of the
following elements may (though doesn't have to) consist of a single child:
``sign, group, factor, term, expression``. A suitable transformation for this
purpose is the :py:func:`~transform.replace_by_single_child` which replaces a
node by its single child in case the node has exactly one child, no more, no
less. To apply this transformation to every node that has one of the above
mentioned five tag-names, we assign this function to these tag-names in the
transformation dictionary or, as we shall call it henceforth, "transformation
table"::

    >>> from DHParser.transform import replace_by_single_child
    >>> transformation_table = { "sign, group, factor, term, expression":
    ...                             [replace_by_single_child] }

Note, that the transformation table is an ordinary Python-dictionary, only that
a string-key that contains a comma-separated list of node-names will be
interpreted as so many different keys that are mapped onto the same sequence of
transformations.

Next, we traverse the tree and call each of the transformations in the list
(which in this case is only one, namely, ``replace_by_single_child``) on every
node that has one of the tag-names in the key::

    >>> from DHParser.transform import traverse
    >>> from copy import deepcopy
    >>> save_cst = deepcopy(formula_cst)
    >>> formula_cst = traverse(formula_cst, transformation_table)
    >>> print(formula_cst.as_sxpr(flatten_threshold=0))
    (term
      (NUMBER "3")
      (MUL "*")
      (expression
        (NUMBER "4")
        (PLUS "+")
        (NUMBER "5")))

Three things are important to know about :py:func:`~transform.traverse`:

1. Trees are transformed depth first. So, when a transformation is called on a
   particular node, or rather path (see :ref:_paths), all children of that
   node have already been transformed.

2. As any other tree transformation method in DHParser, function
   :py:func:`~transform.traverse` transforms trees *in place*. So, if for some
   reason you need to preserve earlier states of the tree, you'll have to make a
   `deep copy <https://docs.python.org/3/library/copy.html#copy.deepcopy>`_
   first.

3. Although trees are transformed in place, it may happen that certain nodes
   are replaced by other existing or even completely new nodes during the
   transformation. In particular, if the node passed to :py:func:`~transform.traverse`
   as the first argument is not of type :py:class:`~nodetree.RootNode`, it will
   be replaced by a node of type :py:class:`~nodetree.RootNode`. There, it is
   good practice to always assign the return value of :py:func:`~transform.traverse`
   to the variable passed as its first argument, e.g.
   ``formula_cst = traverse(formula_cst, transformation_table)``.

The resulting tree looks much closer to the syntax tree of an arithmetic formula
we had in mind. Every one-term "expression", "term", "factor" etc. has
essentially been replaced by what it is. Now, we'd still like to do this for the
two-term expressions. Since this is an operation which is specific to our
arithmetic example, we would not expect module :py:mod:`DHParser.transform` to
already contain such an operation (although in this particular case, in fact, it
does). But we can write a suitable transformation on our own, easily::

   >>> from DHParser.nodetree import Node, Path
   >>> def left_associative(path: Path):
   ...     "Re-arranges a flat node with infix operators into a left associative tree."
   ...     node = path[-1]
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

A transformation function is a function with the tree-path as single argument
and no return value. The tree-path is the list of all nodes on the path from
the root node of the tree up to and including the node that shall be
transformed. It is good practice that transformations only change the last node
in the path and its children (which have already been transformed by the
time this node has been reached by :py:func:`~transform.traverse`), but not any
parents or siblings in the path. The path, rather than the node alone, is
passed to transformation function only in order to enable it to query the
parents or siblings in order to allow the transformation to make choices
depending on the path. This said, it sometimes makes sense to deviate from this
rule, none the less.

The just defined function does nothing if the last node in the path (which
is the node that is just being visited during the tree-traversal and which the
transformation-function should operate on) has three or more children. If so, it
is assumed that the children form a sequence of value interspersed with dyadic
operators, e.g. "3 + 4 - 5 + 2". These will then be rearranged as (binary) tree
assuming that the operators are `left-associative
<https://en.wikipedia.org/wiki/Operator_associativity>`_. The nodes containing
the operators will then be eliminated, but their tag-names will be kept as
tag-names of the nodes of the generated tree, so that the tag-name of each node
indicates the kind of operator while the children are the argument of the
operation. For example, ``(expression (NUMBER "4") (PLUS "+") (NUMBER "5"))``
will become ``(PLUS (NUMBER "4") (NUMBER "5"))``. Thus, in the resultant
abstract syntax tree, the structure of the formula is expressed by the structure
of the tree.

The function ``left_associative()`` can only be meaningfully applied to "term"
and "expression"-nodes. So, we have to split our transformation table up in
order to apply it only to nodes with these tag names::

    >>> transformation_table = { "term, expression":
    ...                              [left_associative, replace_by_single_child],
    ...                          "sign, group, factor":
    ...                              [replace_by_single_child] }

We still keep the transformation :py:func:`~transform.replace_by_single_child` in
the list of transformations for "term" and "expression"-node for those cases
where these nodes have only one child. Now, let's see what difference this makes::

    >>> formula_cst = deepcopy(save_cst)  # restore concrete syntax tree
    >>> formula_cst = traverse(formula_cst, transformation_table)
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

See :py:meth:`~nodetree.Node.evaluate` in case you wonder what the last
statement does. (The ``evaluate()``-method of the
:py:class:`~nodetree.Node`-class is actually a third and most trivial
installment of the visitor-pattern in DHParser.)


A Walk Through the Transformation Table
---------------------------------------

As shown by the examples earlier, the transformation table is a "smart"
dictionary that maps tag-names to sequences of transformation functions. It is
called "smart", because it allows to list several tag names within one and the
same dictionary keys, thus assigning each one of them to one and the same
sequences of transformation functions. (You could think of the transformation
table as a simple "embedded" or `internal DSL (Domain Specific Languag)
<https://martinfowler.com/bliki/DomainSpecificLanguage.html>`_ realized within
Python, if you liked.) This is quite useful, because it allows to cover similar
idioms used at different places of a grammar (and with different tag-names) with
the same sequence of transformation functions, without having to type the same
list of functions over and over again.

The transformation table has three special keys: ``<``, ``>``, ``*``. The
asterix ``*`` is a joker, which means that the sequence of transformations
assigned to the asterix will be called for every node, the tag-name of which
does not occur in the table. The ``<``-key marks a sequence of functions that
will be executed before any of the individual sequences assigned to particular
tag-names (including the joker ``*``) will be executed. The ``>``-key takes a
transformation-sequence that will be executed after every tag-specific
transformation-sequence has been processed. Because of the time-penalty
incurred, the ``<``- and ``>``-keys should only be used when really needed. Most
of the time the desired result can be achieved more effectively with the
``@disposable``- and ``@drop``-directives at the parsing-stage, already (see
:ref:`simplifying_syntax_trees`)).

To give a better impression of how tree-transformation works and what primitives
the transformation-module provides, here is an excerpt from the
transformation-table of the LaTeX-Parser example::

    LaTeX_AST_transformation_table = {
        "hide_from_toc, no_numbering": replace_content_with(''),
        "_known_environment": replace_by_single_child,
        "inline_math": reduce_single_child,
        "paragraph": strip(is_one_of({'S'})),
        "text, urlstring": collapse,
        "ESCAPED": [apply_ifelse(transform_result(lambda result: result[1:]),
                                 replace_content_with('~'),
                                 lambda path: '~' not in path[-1].content)],
        "UMLAUT": replace_Umlaut,
        "QUOTEMARK": replace_quotationmark,
        ":Whitespace, _WSPC, S": streamline_whitespace,
        "WARN_Komma": add_error('No komma allowed at the end of a list', WARNING),
        # ...
    }

The first entry of the dictionary turns nodes with the either of the names
"hide_from_toc" or "no_numbering" into empty nodes, which is reasonable, because
these markers which in the LaTeX-source consist of a simple asterix that is
appended to a section-command or a command for an equation array shall not be
printed as part of the text. At the same time, it is reasonable to keep the
empty nodes as flags to indicate to latter processing stages that a certain
section or chapter shall not appear in the table of contents or the numbering of
an equation array shall be suppressed.

The second entry replaces any node with the name "_known_environment" by its
single child in case it has only one child. (See
:py:func:`DHParser.transform.replace_by_single_child`.) This is a very useful
transformation rule for symbols that are defined as alternatives in the grammar.
In the file ``LaTeX.ebnf`` the "_known_environment"-symbols is defined as
``_known_environment = itemize | enumerate | description | figure | tabular |
quotation | verbatim | math_block``. For any such known environment, the
concrete syntax tree consists of a node of with the name "_known_environment"
that contains the actual environment as a single child, say:: 

    (_known_environment
      (enumerate
        (item ...)
        (item ...)
        ...
      )
    )


(This can easily be checked by marking one or more of the environment-tests in
the "test_grammar"-subfolder of the LaTeX-example with an asterix so as to show
the concrete syntax tree in the test report.) Now, since we are only interested
in the actual environment, it is only reasonable to replace any
"_known_environment"-node in the concrete syntax tree by the actual environment
it contains as its single child node. 

The same effect can also be achieved by early tree-reduction during the parsing
stage (see :ref:`Simplifying Trees <simplifying_syntax_trees>` in the
documentation of the :doc:`01_ebnf`-module.) by listing the symbol
"_known_environment" in the ``@disposable``-directive at the beginning of the
grammar. In cases as simple as this one, it is preferable way to eliminate
superfluous nodes as early as possible by using the ``@disposable``-directive.

The opposite case where you want to retain the parent node but eliminate a
single child is demonstrated by the following entry. The symbol "inline_math" is
meant to mark mathematical notation that occurs within the text of a paragraph.
LaTeX has two different sets of symbols, ``\( ... \)`` and ``$ ... $`` to mark
the beginning and end of a stretch of inline maths, which are captured by
"_im_bracket" and "_im_dollar"-symbol, respectively. Thus, "inline_math" is
defined in the grammar as ``inline_math = _im_bracket | _im_dollar``. However,
this time we are only interested in the fact that some piece of text is a piece
of inline math and not what set of delimiters has been used to mark it as such.
Therefore we use the :py:func:`DHParser.transform.reduce_single_child`-primitive
to eliminate the child node while transferring it data to the parent.

Again, the same can more efficiently be achieved by adding the symbols
"_im_bracket" and "_im_dollar" to the list of disposable symbols at the top of
the grammar. However, when still developing the grammar, it can, for debugging
purposes, still be helpful to eliminate them during the tree-transformation
stage and not already while parsing. Once it has been superseded by the
disposable directive, the ``reduce_single_child``-primitive should be removed
from the table, because - other than the ``replace_by_single_child``-primitive
it can produce undesired side effect if the child to be reduced to its parent
has already been eliminated earlier.

In the grammar of the LaTeX-example, the symbol "S" captures significant
whitespace. However, at the beginning and the end of a paragraph, explicit
whitespace is really unnecessary, because beginning or ending a paragraph
already implies that there is a linefeed (and thus whitespace). The entry for
the "paragraph" symbol therefore eliminates whitespace that has been captured by
the "paragraph"-parser at the beginning or the end. This is achieved with the
:py:func:`DHParser.transform.strip`-primitive. Like the
:py:func:`DHParser.transform.replace_content_with`-primitive it takes an
argument, only this time, the argument is another primitive (applied to the
current path of the node under inspection), namely
:py:func:`DHParser.transform.is_one_of`, which returns true if the path passed
to it ends with a node the name of which is one of a set of names. In this case
this is the set with the single element "S": ``strip(is_one_of({'S'}))``.

The following entry uses a rather trivial primitive,
:py:func:`DHParser.transform.collapse` which simply replaces the the result of
the node to which it is applied by the concatenated string content of all of its
children (if any). Here it serves to yield the string content for sub-trees the
structure of which is not relevant for further processing. "urlstring", to pick
this one out, is defined as ``urlstring = [protocol] { path } [target]``. Each
of the components of urlstring has a syntax of its own, which results in an
intricate tree-structure when parsed. 

Given that this structure is not relevant in the further processing of the
parsed document one might ask the question why not a very much simplified
URL-parser might have been sufficient. A possible reason for specifying a
detailed parser in cases where the structure does not matter is to capture
syntax errors early on. Otherwise a misspelled URL that hasn't been rejected by
a simplified parser might cause trouble later on. In cases where this is not to
be feared simplified parsers are often a good choice, not in the least, because
they usually increase parsing speed. The parser of the LaTeX-example uses
simplified parsers for the mathematical notation, because this can be passed
through to Javascript rendering libraries like `MathJax`_ or `KaTeX`_ as is.

The transformation rule for the "ESCAPED" symbol is more complex. Usually,
escaping in LaTeX works simply by writing a backslash followed by the symbol
that shall be escaped (i.e. not be interpreted as a control character but simply
written out), e.g. "\#" writes a "#"-character instead of starting a comment
which would be the usual meaning of the "#" in LaTeX. However, the case of the
tilde "~" is more complicated, because if LaTeX encounters an escaped tilde
character, it will try to write the tilde *above* the following character. In
order to really get a single tilde character one has to write "\~{ }" in LaTeX.
The definition of the ESCAPED-symbol: ``ESCAPED = /\\(?:(?:[#%$&_\/{}
\n])|(?:~\{\s*\}))/`` knows about this special case. But this means that while
usually just dropping the leading backslash "\" when un-escaping a character
during AST-transformation, we need to eliminate the following characters, too,
in the case of the tilde.

This case differentiation is effected by the
:py:func:`DHParser.transform.apply_ifelse`-function which applies one (list of)
primitive(s) or an alternative (list of) primitive(s) depending on boolean
condition. Note that the the boolean condition is stated as the last term in the
list of parameters of the ``apply_if_else``-operator! In this case the
boolean-primitive is defined inline as a lambda function::
    
    lambda path: '~' not in path[-1].content

Just like the transformation-functions proper, boolean-primitives
(or "probing functions") take the whole
path (i.e. a list of all nodes starting with the root and ending with the node
under inspection) as argument, but - different from the transformation-functions
- they return a boolean value. The
:py:func:`DHParser.transform.transform_result`-primitive takes a function as an
argument to which the result of a Node (i.e. a string or a tuple of child-Nodes)
is passed and that returns the transformed result. The
:py:func:`DHParser.transform.replace_content_with`-primitive replaces the result
of the last node in the path with the given string content. Observe the subtle
difference between the two primitives: `replace_content_with` always yields a
leaf node with string content but no children.

The following three entries apply custom functions, specifically written for the
LaTeX example case. ``replace_Umlaut`` replaces LaTeX-Umlaute like ``\"a`` by
their unicode-counterpart, in this case "ä". ``replace_quotationmark`` does the
same for quotation marks. And ``streamline_whitspace`` compresses any whitespace
either to a single blank or single linefeed.

Finally, the entry for ``WARN_Komma`` adds a syntax warning to all nodes with
the name "WARN_Komma". This follows a pattern for fail tolerant parsing
described in the documentation of the :py:mod:`DHParser.ebnf` as :ref:`generic
fail tolerant parsing <generic_fail_tolerant_parsing>`.


Transformation Functions
------------------------

A transformation function is a function that takes the path of a node
(i.e. the list of nodes that connects the node with the root of the
tree, starting with the root and ending with the node) as single argument
and has no return value.

By convention transformation functions should only make changes to the
node and descending nodes, but not to its siblings or any nodes further
down the tree. The path, rather than the node, is passed as argument
in order to allow the inspection of the environment of the node. And,
well, in rare cases it makes sense to deviate from the just mentioned rule.

However, it should be kept in mind that the tree is traversed depth-first
and that changes to the ancestry of a node will not affect the tree traversal
which still operates on the children-tuples of the ancestors before the
change by a transformation-function takes effect. To avoid confusion,
it is best, not to change the ancestry.

Generally speaking, transformation function will see the effects of
any other transformation further up the tree (i.e. those affecting
the last node in the path and its descendants) or earlier in the
list of transformations assigned to an entry in the transformation-table.

See the section on :ref:`debugging <debugging_transformations>`, below,
for an example of what can happen when this is not taken into consideration.

There is a special kind of transformation functions, called "probing
functions", that take the path as an argument but return a boolean
value. Probing functions should not make any changes to the tree.
Also, it does not make sense to add probing functions directly to a list
of transformation-function in the transformation table. Rather, probing
functions are passed as arguments to conditional transformation functions.

While transformation functions are functions with a single argument, it
would often be helpful to pass further parameters, like the just
mentioned boolean conditions, to a transformation. Such transformation
functions with further parameters can be called "parameterized
transformation function" where we consider the second argument of the
parameterized transformation function as its first parameter.

One obvious way to turn a parameterized transformation function into
a transformation function proper with a single argument is by deriving
partial functions as described in
`Python documentation <https://docs.python.org/3/library/functools.html#functools.partial>`_.
Example::

    >>> from functools import partial
    >>> from DHParser.transform import remove_children_if, is_empty
    >>> trans_table = {"*": partial(remove_children_if, condition=is_empty)}

However, since this makes the transformation-table less readable,
:py:mod:`DHParser.transform` provides the
:py:func:`DHParser.transform.transformation_factory`-decorator that
must be added to the definition of transformation functions that
have further arguments after the `path`-argument. Example::

    >>> from collections.abc import Callable
    >>> from DHParser.transform import transformation_factory
    >>> @transformation_factory
    ... def remove_children_if(path: Path, condition: Callable):
    ...     node = path[-1]
    ...     if node.children:
    ...         node.result = tuple(c for c in node.children if not condition(path + [c]))

The decorator must be parameterized with the type of the second argument, unless
this argument has already been annotated with the type. Now, it is possible
to rewrite the transformation table above as::

    >>> trans_table = {"*": remove_children_if(is_empty)}

While the transformations with parameters in transformation table look like
functions calls where the first argument is missing, they are actually
calls to the transformation_factory decorator that returns a partial function
where all arguments are fixed except the "paths"-argument at the beginning
of the argument sequence. However, transformation functions with parameters
can still be called like regular functions, if the first parameter is given.
In this case the ``transformation_factory``-decorator simply passes the
the call through to the original function. The ``transformation_factory``-decorator::

    >>> from DHParser import parse_sxpr, content_matches
    >>> tree = parse_sxpr('(WORT "hallo")')
    >>> content_matches([tree], r'\w+')
    True
    >>> type(content_matches(r'\w+'))
    <class 'functools.partial'>


The distinction between function call and partial function generation
is made on the basis of the type of the first argument.
If the first argument is of type ``Path`` (defined as ``List[Node]``)
the call is passed through, otherwise a partial function is generated.
This places some subtle restrictions on the type of the first parameter
(i.e. second argument) of a parameterized transformation function in so
far as this must not be a type that could be mistaken for the type
``Path`` of a subtype of ``Path``. As a rule of thumb it is advisable
to avoid lists as types of the first parameter (or second argument,
respectively) and use tuples or sets instead if a container type is needed.

While this technical background may sound complicated, there is in fact little
need to worry. For, parameterized transformation functions have turned
out to be easy and intuitive to handle in practice.

Probing functions can be parameterized in exactly the same fashion as regular
transformation functions with the same decorator ``transformation_factory``::

    >>> from typing import AbstractSet
    >>> from collections.abc import Set
    >>> @transformation_factory(Set)
    ... def is_one_of(path: Path, name_set: AbstractSet[str]) -> bool:
    ...     return path[-1].name in name_set

This example also shows that the type parameter of the
``transformation_factory``-argument overrides the type annotation, which
is useful in cases where this annotation does not work for
technical reasons.


.. hint:: Transformation functions usually either assume that the
   path on which they are called ends with e leaf-node or with
   a branch-node but do not make much sense in the other case.
   It is therefore good practie to check this as a pre-condition
   with an if-clause (see function ``remove_children_if`` above)
   or an assert-statement::

       >>> def normalize_whitespace(path):
       ...     node = path[-1]
       ...     assert not node.children
       ...     node.result = re.sub(r'\\s+', ' ', node.content)


.. _debugging_transformations:

Debugging the transformation-table
----------------------------------

Complex tranformations can become hard to follow and to debug. The
transformation-module provides a simple "printf-style" debugging
facility in form of the peek-function to help spotting mistakes.
Additionally, the :py:mod:`DHParser.testing`-module provides
unit-testing-facilities that also cover the AST-transformation-step.

Here is an example that demonstrates potentially unexpected results
of badly ordered transformation-rules::

    >>> import copy
    >>> from DHParser.transform import collapse
    >>> from DHParser.nodetree import parse_sxpr
    >>> def duplicate_children(path: Path):
    ...     node = path[-1]
    ...     if node.children:
    ...         node.result = node.children + node.children
    >>> trans_table = { 'bag': [collapse, duplicate_children] }  # <-- bad mistake
    >>> testdata = parse_sxpr('(bag (item "apple") (item "orange"))')
    >>> traverse(copy.deepcopy(testdata), trans_table).as_sxpr()
    '(bag "appleorange")'

If we had expected that the contents of "bag" would be doubled,
we might find the result disappointing. Now, the mistake is easy to
spot and to understand. But let's for the sake of the example assume
that we are just surprised and have no clue where the error lies. Then
using the :py:func:`DHParser.transform.peek`-function can help us
debugging the transformation-list. The ``peek``-function, while technically
a transformation function, does not change the tree, but simply
prints the tree as S-expression::

    >>> from DHParser.transform import peek
    >>> trans_table = { 'bag': [collapse, peek, duplicate_children] }
    >>> _ = traverse(copy.deepcopy(testdata), trans_table)
    (bag "appleorange")

Thus, we can see the tree that the ``collapse``-function leaves behind and which
the the ``duplicate_children``-functions receives as input. Since the collapse
functions "collapses" the last node of the path into a leaf-node. Therefore,
the function ``duplicate_children`` does not receive a node with children
that could be duplicated. We could remedy the situation by changing the the
order of the transformations functions::

    >>> trans_table = { 'bag': [duplicate_children, collapse] }
    >>> traverse(copy.deepcopy(testdata), trans_table).as_sxpr()
    '(bag "appleorangeappleorange")'


*Functions-Reference*
---------------------

The full documentation of all functions can be found in module
:py:mod:`DHParser.transform`. The following table lists only the most
important of these:

* :py:func:`~transform.transformation_factory`: A decorator that turns
   parameterized transformation of probing functions into simple
   transformation or probing functions with a singe argument.

* :py:func:`~transform.traverse`: Traverses a tree depth-first and
   calls zero or more transformation functions on each node picked
   from the transformation table by the name of the node.

Basic Re-Arranging Transformations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These transformations change und usually simplify the structure of the
tree but do not touch the string-content of the node-tree. When speaking
of the "node" a transformation function operates on in the following,
we always mean the last node in the path that is passed to the
transformation function as argument.


* :py:func:`~transform.replace_by_single_child`: Replaces a node with its
  single child, in case it has exactly one chile. Thus, ``(a (b "x"))``
  becomes ``(b "x")``, if the function is called on node "a", e.g. the
  path ending with "a".

* :py:func:`~transform.replace_by_children`: Replaces a node by all of its
  children, if possible, e.g. ``(root (a (b "x") (c "y")))`` ->
  ``(root (b "x") (c "y"))``

* :py:func:`~transform.raduce_single_child`: "Reduces" a single child
  to its parent. ``(a (b "x"))`` -> ``(a "x")``

* :py:func:`~transform.change_name`: Changes the name of the node.

* :py:func:`~transform.flatten`: "Flattens" a node by replacing all
  of its children that are not leave nodes and which fulfil a given
  critrion by that child's children. The default criterion is
  :py:func:`~transform.is_anonymous`. Example:
  ``(expr (term "5") (:OneOrMore (PLUS "+") (term "4") (MINUS "-") (term "3")))``
  -> ``(expr (term "5") (PLUS "+") (term "4") (MINUS "-") (term "3"))``

* :py:func:`~transform.collapse`: Replaces the children of the node
  by their concatenated string content, e.g.
  ``(number (digits "3") (dot ".") (decimal "14159"))``
  -> (number "3.15159"). The function "collapse" is mostly useful
  in cases when grammatical constructs have been added merely to validate an
  input string and the deep structure is not of interest in the further
  processing stages any more.

* :py:func:`~transform.collapse_children_if`. Merges adjacent children
  that fulfil a given condition, e.g.
  ``(place (abbreviation "p.") (page "26") (superscript "b") (mark ",") (page "18"))``
  -> ``(place (text "p.26") (superscript "b") (text ",18"))``
  (In this example the condition was "not_one_of({'superscript', 'subscript'})"
  and the target name for merged children was "test". See the docstring
  of :py:func:`~transform.collapse_children_if`.)

* :py:func:`~transform.merge_adjacent`. Like the previous function, only
  that the children to be merged will not be collapsed and the target-name
  (here called 'preferred_name') will only be used if it already occurs
  as node-name among the nodes to be merged. See the doc-string of this
  function for more details.

* :py:func:`~transform.move_fringes`. Moves children from the left and right
  fringes to the parent node as long as the children on the fringes fulfil
  a given condition. This functions can help to patch up badly formulated
  grammars.


Content-Changing Transformations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* :py:func:`~transform.lstrip`, :py:func:`~transform.rstrip`,
  :py:func:`~transform.strip`. Recursively removes all leading, trailing or
  both child-nodes that fulfil a given condition like 'is_whitespace'.

* :py:func:`~transform.remove_children_if`. Removes all children that
  fulfil a given condition.

* :py:func:`~transform.remove_children`. A more specialized form of
  'remove_children_if' that removes children based on their names.

* :py:func:`~transform.remove_content`: Removes all children, the string content of 
  which matches a given regular expression.

* :py:func:`~transform.remove_brackets`: Removes any leading or trailing sequence
  of (insignificant) whitespaces, anonymous text or anonymous regular expression nodes,
  e.g. ``(formular (:Text "(") (number "5") (operator "+") (number "3") (:Text ")") (:Whitespace " "))``
  -> ``(formular (number "5") (operator "+") (number "3"))``

* :py:func:`~transform.remove_tokens`: Removes and tokens, i.e. anonymous Text-nodes,
  e.g. ``(plus (number "5") (:Text "+") (number 3))`` -> ``(plus (number "5") (number 3))``

* :py:func:`~transform.remove_if`: Removes the last node of the path from ist parent'S
  children. (Note: This transformation breaks the rule not to touch a node's parent's 
  children-tuple! But, depending on the use case, the meaning of the transformation 
  might become clearer when using "remove_if" on the node to be removed rather than 
  "remove_children_if" on its parent node.)


Conditional Transformations
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Conditional Transformations apply a transformation or a sequences of transformations
depending on the result of a probing function or boolean combination of probing functions.

* :py:func:`~transform.apply_if`: Applies a transformation or sequence of transformations
  if the given probing function returns True. Note, that the transformation is the
  first parameter while the probing-function (or if-condition) comes second, e.g. 
  ``apply_if([replace_content_with(' '), change_name('blank')], content_matches(r'\s+'))`` 
  (normalizes nodes that contain only whitespace to nodes with single blanks and
  the name to 'blank').

* :py:func:`~transform.apply_unless`: Applies a transformation or sequence of transformations
  if the given probing function does not return True. (Again, the probing function is listed
  last in  the parameter-list.)

* :py:func:`~transform.apply_ifelse`: Applies either of two transformation-functions depending
  on the truth-value the given probing function (last parameter!) returns.


Probing Functions
^^^^^^^^^^^^^^^^^

* :py:func:`~transform.is_anonymous`: Returns True, if the node either does not have 
  name at all, or a name that starts with a colon ":" as do those nodes that have
  been generated by an unnamed parse.

* :py:func:`~transform.is_empty`: Returns True, if the node has neither children nor
  any string content (i.e. not even blanks).

* :py:func:`~transform.is_token`: Returns True, if the node's name is ":Text" (which 
  means that it is an anonymous node produces by the String-Text-Parser) or any other
  of the given Token-names.

* :py:func:`~transform.is_one_of`: Returns True, if the node has one of the given names.

* :py:func:`~transform.not_one_of`: The opposite of the above. Returns True, if the 
  node has none of the given names.

* :py:func:`~transform.name_matches`: Returns True, if the node's name matches 
  the given regular expression completely.

* :py:func:`~transform.content_matches`: Returns True, if the node's content matches
  the given regular expression completely.

* :py:func:`~transform.has_content`: Returns True, if the node's content is the
  same as the given string. (This is a faster special case of the the above.)

* :py:func:`~transform.has_attr`: Checks whether the node has a particular attribute
  and if a value is given, also whether the attributes value is the given value.

* :py:func:`~transfrom.has_ancestor`: Checks whether the node has an has an has an ancestor 
  with one of the given names.

* :py:func:`~transform.has_descendant`: Checks whether the node has a descendant with
  one of the given names. There are further functions like :py:func:`~transform.has_parent`, 
  :py:func:`~transform.has_child`, :py:func:`~transform.has_sibling` to check for immediate
  ancestors, descendants or for neighbors on the same level.



Boolean Combinators
^^^^^^^^^^^^^^^^^^^

* :py:func:`~transform.any_of`: Returns True, if any one of the zero or more given
  probing functions returns True. Note that like Python's "any()" this is
  False if the set of given functions is empty.

* :py:func:`~transform.all_of`: Returns True, if all of the zero or more given probing 
  functions return True. Note that like Python's "all()" this is True if the set of given
  functions if empty, e.g. ``remove_if(all_of([is_empty, is_anonymous]))`` (remove a node
  if it is both empty and anonymous).

* :py:func:`~transform.neg`: Inverts the boolean return value of the given probing function.


.. _MathJAX: https://www.mathjax.org/
.. _KaTeX: https://katex.org/
