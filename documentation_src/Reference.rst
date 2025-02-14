Reference
=========

EBNF-Reference
--------------

.. _ebnf_syntax:

Syntax
^^^^^^

DHParser supports two different variants of the EBNF-snytax, called classical
and regular-expression-like (or "regex-like"). The former resembles the
ISO-standard for EBNF, the latter is more akin to the commonly used EBNF-syntax
for parsing expression grammars.

A grammar consists of a sequence of definitions (also known as "productions")
of the form: *symbol* **=** *rule*. A rule is always a sequence of literals
and operators. DHParser supports the following literals and operators:

===========================  ====================  ================
literals and operators       classical syntax      regex-like
===========================  ====================  ================
*literals*
---------------------------  --------------------  ----------------
insignificant whitespace¹⁾   ~                     ~
string literal               "..." or \`...\`      "..." or \`...\`
regular expr.                /.../                 /.../
---------------------------  --------------------  ----------------
*operators*
---------------------------  --------------------  ----------------
sequences                    A B C                 A B C
alternatives                 A | B | C             A | B | C
interleave ²⁾                A ° B ° C             A ° B ° C
grouping                     (...)                 (...)
options                      [ ... ]               ...?
repetitions                  { ... }               ...*
one or more                  { ... }+              ...+
repetition range             ...(i, k)             ...{i, k}
---------------------------  --------------------  ----------------
*lookahead assertions*
---------------------------  --------------------  ----------------
positive lookahead           & ...                 & ...
negative lookahead           ! ...                 ! ...
---------------------------  --------------------  ----------------
*lookbehind assertions* ³⁾
---------------------------  --------------------  ----------------
positive lookbehind          <-& ...               <-& ...
negative lookahead           <-! ...               <-! ...
---------------------------  --------------------  ----------------
*error raising* ⁴⁾
---------------------------  --------------------  ----------------
mandatory-marker             § ...                 § ...
error-message                @Error("...")         @Error("...")
---------------------------  --------------------  ----------------
*macros* ⁵⁾
---------------------------  --------------------  ----------------
macro definition             $macro($p1, ...) =    same
macro usage                  $macro(expr, ...)     same
---------------------------  --------------------  ----------------
*custom parsers* ⁶⁾
---------------------------  --------------------  ----------------
custom parser                @Custom(parse_func)   same
parser factory               @factory_func("...")  same
---------------------------  --------------------  ----------------
*context sensitive ops.* ⁷⁾
---------------------------  --------------------  ----------------
pop and match                :: ...                :: ...
retrieve and match           : ...                 : ...
pop and always match         :? ...                :? ...
filter-definition            @SYM_filter = func()  same
===========================  ====================  ================


¹⁾ :ref:`Insignificant whitespace <insignificant_whitespace>` is whitespace
   that neither carries any syntactic significance (say, as a delimiter) nor
   has any semantic relevance (say as part of the data).

²⁾ Interleave means that the following elements must appear (like in a
   sequence), but it does not matter in which order.

³⁾ In DHParser :ref:`lookbehind-assertions <lookaraound_operators>` always
   operate on the reverse input string! This allows to exploit the full
   capabilities of regular expressions without need to worry about
   regex-engines supporting only constant-length look-behinds etc.
   Keep in mind that looking back for the keyword "BEGIN" then means
   that you have to check for "NIGEB", e.g. "<-& /\s*NIGEB/" means
   that the prvious token read "BEGIN".

⁴⁾ :ref:`Mandatory markers <mandatory_items>` express expectations about
   the following items in a document. If a sequences has matched up to the
   marker but then fails to match an element after the marker, this is
   mot just a non-match, but an error that will be reported.
   ref:`Error messages <grammar_code_for_errors>` should be added to
   paths in the grammar that should never be reached if the parsed
   document is correct.

⁵⁾ See the :ref:`Marcros-section <macro_system>` in the manual for a detailed
   explanation how macros work in DHParser.

⁶⁾ :ref:`Custom parsers <custom_parsers>` are parsers that are defined
   as Python-functions which will be called from the generated Python-parser
   during parsing.

⁷⁾ :ref:`Constext sensitive parsers <context_sensitive_parsers>` break with
   the paradigm of context-free-grammars and may slow down the parsing
   process. In connections with filter-functions they provide next to custom
   parsers another means of realizing semantic actions.


Example
^^^^^^^

Here is an example for the **classical-syntax**::

    # Arithmetic-grammar

    # directives

    @ whitespace  = vertical             # implicit whitespace, denoted by ~, includes any number of line feeds
    @ literalws   = right                # literals have implicit whitespace on the right hand side
    @ comment     = /#.*/                # comments range from a '#'-character to the end of the line
    @ ignorecase  = False                # literals and regular expressions are case-sensitive
    @ drop        = whitespace, strings  # drop anonymous whitespace and (anonymous) string literals

    # grammar

    expression = term  { (PLUS | MINUS) term }
    term       = factor { (DIV | MUL) factor }
    factor     = [sign] (NUMBER | VARIABLE | group) { VARIABLE | group }
    sign       = POSITIVE | NEGATIVE
    group      = "(" expression ")"

    PLUS       = "+"
    MINUS      = "-"
    MUL        = "*"
    DIV        = "/"

    POSITIVE   = /[+]/      # no implicit whitespace after signs!
    NEGATIVE   = /[-]/

    NUMBER     = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
    VARIABLE   = /[A-Za-z]/~

In **regex-like syntax** the first part of the grammar for arithmetical expressions
would read like this::

    expression = term  ( (PLUS | MINUS) term )*
    term       = factor { (DIV | MUL) factor }
    factor     = sign? (NUMBER | VARIABLE | group) (VARIABLE | group )*
    sign       = POSITIVE | NEGATIVE
    group      = "(" expression ")"

DHParser has a heuristic-mode that allows to write grammars using other characters
as delimiters. For example, the same passage in strict ISO-style would look like::

    @flavor = heuristic

    expression ::= term  { (PLUS | MINUS) term };
    term       ::= factor { (DIV | MUL) factor };
    factor     ::= [sign] (NUMBER | VARIABLE | group) { VARIABLE | group };
    sign       ::= POSITIVE | NEGATIVE;
    group      ::= "(" expression ")";

Or, in the more recent parsing expression grammar (PEG)-style::

    @flavor = heuristic

    expression = term  ( (PLUS / MINUS) term )*
    term       = factor { (DIV / MUL) factor }
    factor     = sign? (NUMBER / VARIABLE / group) (VARIABLE / group )*
    sign       = POSITIVE / NEGATIVE
    group      = "(" expression ")"

Mind that in PEG-style it can be difficult to avoid ambiguities when using
regular expressions to define the atomic-expressions. This can lead to unexpected
parser-errors. Therefore it is better to use the `|`-sign for denoting alternatives,
rather than a slash `/`. The meaning is in any case the same, namely, that of
PEG-grammars where the first alternative that matches is used rather than checking
all alternatives (as Earley-parsers would do).

Note that despite of being based on parsing expression grammars DHParser fully
supports direct and indirect left recursion in the grammar-definition. In order
to avoid endless-loops it employs the seed-and grow-algorithm.


.. _directives_reference:

Directives
^^^^^^^^^^

The following is a table of DHParser's EBNF-directives.
EBNF-Directives control how the grammar is interpreted and processed by DHParser.
They also influence the verbostiy or sparseness of the concrete-syntax-tree
that the parser yields.

EBNF-Directives always have the form::

    @[DIRECTIVE] = [VALUES]

============== =======================================================================================================================
Directive      purpose and possible values
============== =======================================================================================================================
@comment       Regular expression for comments, e.g. /#.*(?:\n|$)/
@whitspace     Regular expression for whitespace or one of the predifined values: horizontal, linefeed, linestart, vertical
@literalws     Implicitly assume insignificant whitespace adjacent to string-literals: left, right, both or none
@ignorecase    Global case-sensitivity: True or False
@include       include other EBNF files
@tokens        List of names of all valid preprocessor-tokens
@hide          List of symbols that shall produce anonymous nodes instead of nodes named by the symbol
@drop          List of symbols that shall be dropped entirely from the tree
@reduction     Reduction level for simplifying trees while parsing: none, flatten, merge_treetops, merge
@[SYM]_filter  Name of a Python function that yields a counterpart of the captured symbols, e.g. ")" for "("
@[SYM]_error   A regular expression followed by an error message that is produced if the expression matches at the error-location
@[SYM]_skip    List of regular expressions or grammar symbols or function names to find a reentry point after an error
@[SYM]_resume  Same as above, only this time the parent parser rather than the failing parser continues at the reentry point
@optimizations Optimization level for speeding up the parsing-process: none, some, all
@Error(...)    Attach a parsing-error to the syntax-tree if the parser reaches this point
@flavor        The syntax for the EBNF-grammar: dhparser (strict) or heuristic (tolerant with respect to variants of EBNF, but slower)
============== =======================================================================================================================


Examples 1: :ref:`Comments and Whitespace <comments_and_whitespace>`::

    @comment = /#.*(?:\n|$)/     # form the first `#` everything until
                                 # the end of the line or file is a comment

    @whitespace = /[ \t\n]*/     # insignificant whitespace consists of blanks, tabs or linefeeds
                                 # Note: Insignificant whitespace should always be defined in such
                                 #       a way that the empty string is also always matched!

    @literalws  = right          # If a string literal is defined in the grammar it is always assumed
                                 # to be succeeded by insignificant whitespace, i.e. you can
                                 # write "+" instead of "+"~ in your grammar to make it easier to read

Examples 2: ref:`Merge, hide and drop <simplifying_syntax_trees>` parts of the concrete syntax tree::

    @hide = /_\w+/               # Let all symbols starting with an underscore produce anonymous Nodes.
                                 # Symbol names with an underscore can then be used for symbols are
                                 # merely introduced for structuring the grammar.

    @hide = INT, FRAC, EXP       # Capture parts of a number, e.g. 1.5E+10 but the
    or @disposable (deprecated!) # division into parts is not needed, anymore, after it's been captured

    # Instead of using a directive, "HIDE:" can be written in front of the symbols, e.g.
    HIDE:INT = [`-`] ( /[1-9][0-9]+/ | /[0-9]/ )

    @hide = comma, full_stop     # Drop the delimiters comma and full_stop entirely. Note: Only
    @drop = comma, full_stop     # hidden symbols can be dropped! This @drop can only be used in
                                 # combination with hide if used as a directive

    # Instead of using a directive, "DROP:" can be written in front of the symbols to be dropped, e.g.
    DROP:comma = ","

    # There is also an inline version of DROP, e.g.
    list = word { ("," -> DROP) word }

    @reduction = merge           # reduce and merge anonymous nodes whereever possible
                                 # in the concrete syntax tree


Example 3: :ref:`Error Handling <error_catching>` and :ref:`Fail-tolerant parsing <fail_tolerant_parsing>`::

    # Attach an error to the syntax-tree if an illegal character follows a backspace
    escape = backspace ("n" | "s" | "t" | @Error("1001:Unknown escpae sequence") /./)

    @street_error = /(?!\d)/, "1001:House number expected!"
    @street_error = '', "1002:House number too high!"
    @street_skip  = /\d+/  # in case "street" fails, skip behind the next sequence of digits
    @street_resume = /\n/  # if that does not work, resume street's parent parser with the next line
    street = /\w+/~ § /\d\d?/ !/\d/

Examples 4: Other directives::

    @include = "numbers.ebnf"    # insert the content of "numbers.ebf" here

    @tokens = BEGIN_INDENTATION, END_INDENTATION  # names of preprocessor tokens. These should match
    or @preprocessor_tokens = ...                 # the names in the Python code for the preprocessor

    @bracket_filter = matching_bracket  # matching_bracket = lambda s: {"(": ")", "[": "]"}[s]
    remark = bracket text ::bracket     # a remark is a text block enclosed by either (...) or [...]
    bracket = "(" | "["

    @flavor = heuristic          # try to auto-detect the EBNF-style used (e.g ISO, PEG, etc.)

    @ignorecase = True           # Capital and small letters do not make a difference when caputing a
                                 # document. Note: Usually it is better not to set this globally, but
                                 # to specify it locally with the I-Flag within the regular expressions
                                 # that capture the "atomic" parts, e.g. word = /(?i)[a-z]/

    @optimizations = all         # make the parser a little faster by using regular expressions for
                                 # some non-recursive parts of the grammar


.. _modules_reference:


Modules
-------


:py:mod:`ebnf`
   Although DHParser also offers a
   Python-interface for specifying grammars (similar to pyparsing_), the
   recommended way of using DHParser is by specifying the grammar in
   EBNF_. Here it is described how grammars are specified in EBNF_ and
   how parsers can be auto-generated from these grammars and how they
   are used to parse text.

:py:mod:`nodetree`
   Syntax-trees are the central
   data-structure of any parsing system. The description to this modules
   explains how syntax-trees are represented within DHParser, how they
   can be manipulated, queried and serialized or deserialized as XML,
   S-expressions or json.

:py:mod:`transform`
   It is not untypical for
   digital humanities applications that document tress are transformed
   again and again to produce different representations of research data
   or various output forms. DHParser supplies the scaffolding for two
   different types of tree transformations, both of which a variations
   of the `visitor pattern`_. The scaffolding supplied by the
   transform-module allows to specify tree-transformations in a
   declarative style by filling in a dictionary of tag-names with lists
   of transformation functions that are called in sequence on a node. A
   number of transformations are pre-defined that cover the most needed
   cases that occur in particular when transforming concrete syntax
   trees to more abstract syntax trees. (An example for this kind of
   declaratively specified transformation is the
   ``EBNF_AST_transformation_table`` within DHParser's ebnf-module.)

:py:mod:`compile`
   offers an
   object-oriented scaffolding for the `visitor pattern`_ that is more
   suitable for complex transformations that make heavy use of
   algorithms as well as transformations from trees to non-tree objects
   like program code. (An example for the latter kind of transformation
   is the :py:class:`~ebnf.EBNFCompiler`-class of DHParser's
   ebnf-module.)

:py:mod:`pipeline`
   offers support for "processing-pipelines" composed out of "junctions"
   A processing pipe-line consists of a series of tree-transformations
   that are applied in sequence. "Junctions" declare which
   source-tree-stage is transformed by which transformation-routine into
   which destination tree-stage. Processing-pipelines can contain
   bifurcations, which are needed if from one source-document different
   kinds of output-data shall be derived.

:py:mod:`testing`
   provides a rich framework for
   unit-testing of grammars, parsers and any kind of tree-transformation.
   Usually, developers will not need to interact with this module directly,
   but rely on the unit-testing script generated by the "dhparser.py"
   command-line tool. The tests themselves a specified declaratively
   in test-input-files (in the very simple ".ini"-format) that reside by
   default in the "test_grammar"-directory of a DHParser-project.

:py:mod:`preprocess`
   provides support for DSL-pre-processors as well as source
   mapping of (error-)locations from the preprocessed document to the original
   document(s). Pre-processors are a practical means for adding features to
   a DSL which are difficult or impossible to define with context-free-grammars
   in EBNF-notation, like for example scoping based on indentation (as used
   by Python) or chaining of source-texts via an "include"-directive.

:py:mod:`parse`
   contains the parsing algorithms and the
   Python-Interface for defining parsers. DHParser features a packrat-parser
   for parsing-expression-grammars with full left-recursion support as well
   configurable error catching an continuation after error. The
   Python-Interface allows to define grammars directly as Python-code
   without the need to compile an EBNF-grammar first. This is an alternative
   approach to defining grammars similar to that of pyparsing_.

:py:mod:`dsl`
   contains high-level functions for compiling
   ebnf-grammars and domain specific languages "on the fly".

:py:mod:`error`
   defines the ``Error``-class, the objects of which describe
   errors in the source document. Errors are defined by - at least - an
   error code (indicating at the same time the level of severity), a human
   readable error message and a position in the source text.

:py:mod:`trace`
   Apart from unit-testing DHParser offers "post-mortem"
   debugging of the parsing process itself - as described in the
   :doc:`StepByStepGuide`. This is helpful to figure out why a parser went
   wrong. Again, there is little need to interact with this module directly,
   as it functionality is turned on by setting the configuration variables
   ``history_tracking`` and, for tracing continuation after errors,
   ``resume_notices``, which in turn can be triggered by calling the
   auto-generated -Parser.py-scripts with the parameter ``--debug``.

:py:mod:`log`
   logging facilities for DHParser as well as tracking of the
   parsing-history in connection with module :py:mod:`trace`.

:py:mod:`configuration`
    the central place for all configuration settings of
    DHParser. Be sure to use the ``access``, ``set`` and  ``get`` functions
    to change presets and configuration values in order to make sure that
    changes to the configuration work when used in combination with
    multithreading or multiprocessing.

:py:mod:`server`
    In order to avoid startup times or to provide a language
    sever for a domain-specific-language (DSL), DSL-parsers generated by
    DHParser can be run as a server. Module :py:mod:`server` provides
    the scaffolding for an asynchronous language server. The
    -Server.py"-script generated by DHParser provides a minimal language
    server (sufficient) for compiling a DSL. Especially if used with the
    just-in-time compiler `pypy`_ using the -Server.py script allows for
    a significant speed-up.

lsp
    (as of now, this is just a stub!) provides data classes that
    resemble the typescript-interfaces of the `language server protocol specification`_.

:py:mod:`stringview`
    defines a low level class that provides views on slices
    of strings. It is used by the :py:mod:`parse`-module to avoid
    excessive copying of data when slicing strings. (Python always
    creates a copy of the data when slicing strings as a design
    decision.) If any, this module can significantly be sped up by
    compiling it with cython_. (Use the ``cythonize_stringview``-script
    in  DHParser's main directory or, even better, compile (almost) all
    modules with the ``build_cython-modules``-script. This yields a 2-3x
    speed increase.)

:py:mod:`toolkit`
    various little helper functions for DHParser. Usually,
    there is no need to call any of these directly.



Module ``ebnf``
---------------

.. automodule:: ebnf
   :members:

Module ``nodetree``
-------------------

.. automodule:: nodetree
   :members:

Module ``transform``
--------------------

.. automodule:: transform
   :members:

Module ``compile``
------------------

.. automodule:: compile
   :members:

Module ``pipeline``
-------------------

.. automodule:: pipeline
   :members:

Module ``parse``
----------------

.. automodule:: parse
   :members:

Module ``dsl``
--------------

.. automodule:: dsl
   :members:

Module ``preprocess``
---------------------

.. automodule:: preprocess
   :members:

Module ``error``
----------------

.. automodule:: error
   :members:

Module ``testing``
------------------

.. automodule:: testing
   :members:

Module ``trace``
----------------

.. automodule:: trace
   :members:

Module ``log``
--------------

.. automodule:: log
   :members:

Module ``configuration``
------------------------

.. automodule:: configuration
   :members:

Module ``server``
-----------------

.. automodule:: server
   :members:

Module ``stringview``
---------------------

.. automodule:: stringview
   :members:

Module ``toolkit``
------------------

.. automodule:: toolkit
   :members:

Module ``versionnumber``
------------------------

.. automodule:: versionnumber
   :members:


.. _pyparsing: https://github.com/pyparsing/pyparsing/
.. _lark: https://github.com/lark-parser/lark
.. _cython: https://cython.org/
.. _`language server`: https://langserver.org/
.. _`language server protocol`: https://microsoft.github.io/language-server-protocol/
.. _`language server protocol specification`: https://microsoft.github.io/language-server-protocol/specifications/specification-current/
.. _EBNF: https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form
.. _`visitor pattern`: https://en.wikipedia.org/wiki/Visitor_pattern
.. _pypy: https://www.pypy.org/
