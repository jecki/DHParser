******
Manual
******

At the core of DHParser lies a parser generator for parsing expression grammars.
As a parser generator it offers similar functionality as pyparsing_ or lark_.
But it goes far beyond a mere parser generator by offering rich support of
the testing an debugging of grammars, tree-processing (always needed in the
XML-prone Digital Humanities ;-) ), fail-tolerant grammars and some
(as of now, experimental) support for editing via the
`language server protocol`_.

DHParser is both suitable for small projects or "on the fly" use of parsing
expression grammar as a more powerful substitute for regular expressions and
for big projects. (The workflow for the latter is described in the `Step by
Step Guide`_.) The usage and API of DHParser is (or will be) described
with many examples in the doctrings of its various modules. The following
reading-order is recommended to understand DHParser:

1. `ebnf.py` - Although DHParser also offers a Python-interface for specifying
   grammers (similar to pyparsing_), the recommended way of using DHParser
   is by specifying the grammar in EBNF_. Here it is described how grammars
   are specified in EBNF_ and how parsers can be auto-generated from these
   grammars and how they are used to parse text.

2. `syntaxtree.py` - Syntax-trees are the central data-structure of any
   parsing system. The description to this modules explains how syntax-trees
   are represented within DHParser, how they can be manipulated, queried
   and serialized or deserialized as XML, S-expressions or json.

3. `transform.py` - It is not untypical for digital humanities applications
   that document tress are transformed again and again to produce different
   representations of research data or various output forms. DHParser
   supplies the scaffolding for two different types of tree transformations,
   both of which a variations of the `visitor pattern`_. The scaffolding supplied
   by the transform-module allows to specify tree-transformations in a
   declarative style by filling in a dictionary of tag-names with lists
   of transformation functions that are called in sequence on a node.
   A number of transformations are pre-defined that cover the most needed
   cases that occur in particular when transforming concrete syntax trees
   to more abstract syntax trees.
   (An example for this kind of declaratively specified transformation is
    the ``EBNF_AST_transformation_table`` within the DHParser's ebnf-module.)

4. `compile.py` - The compile-module offers an object-oriented scaffolding
   for the `visitor pattern`_ that is more suitable for complex
   transformations that make heavy use of algorithms as well as
   transformations from trees to non-tree objects like program code.
   (An example for the latter kind of transformation is the ``EBNFCompiler class``
    of DHParser's ebnf-module.)

    With the documentation of these four modules you should have enough
    knowledge to realize projects that follow the workflow described
    in the `Step by Step Guide`_. There will seldom be need to interact
    with the other modules directly. However, reading their documentation
    may help deepening the understanding of how DHParser works under
    the hood and be useful for more special usa cases.

.. _pyparsing: https://github.com/pyparsing/pyparsing/
.. _lark: https://github.com/lark-parser/lark
.. _`language server protocol`: https://langserver.org/
.. _EBNF: https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form
.. _`visitor pattern`: https://en.wikipedia.org/wiki/Visitor_pattern
.. _`Step by Step Guide`: StepByStepGuide.rst


DHParser is split into a number of modules plus one command line utility
(``dhparser.py``, which will not be described here.)

Usually, the user or "importer" of DHParser does not need to worry
about its internal module structure, because DHParser provides a flat
namespace form which all of its symbols can be imported, e.g.::

   from DHParser import *

or::

   from DHParser import recompile_grammar, grammar_suite, compile_source

However, in order to add or change the source code of DHParser, its module
structure must be understood. DHParser's modules can roughly be sorted into
three different categories:

1. Modules that contain the basic functionality for packrat-parsing,
   AST-transformation and the skeleton for a DSL-compilers.

2. Modules for EBNF-Grammars and DSL compilation.

3. Support or "toolkit"-modules that contain different helpful functions

The import-order of DHParser's modules runs across these categories. In the
following list the modules further below in the list may import one or
more of the modules further above in the list, but not the other way round:

- versionnumber.py -- contains the verison number of DHParser

- toolkit.py -- utility functions for DHParser

- stringview.py -- a string class where slices are views not copies as
  with the standard Python strings.

- preprocess.py -- preprocessing of source files for DHParser

- error.py -- error handling for DHParser

- syntaxtree.py -- syntax tree classes for DHParser

- transform.py -- transformation functions for converting the concrete
   into the abstract syntax tree

- logging.py -- logging and debugging for DHParser

- parse.py -- parser combinators for for DHParser

- compile.py -- abstract base class for compilers that transform an AST
   into something useful

- ebnf.py -- EBNF -> Python-Parser compilation for DHParser

- dsl.py -- Support for domain specific notations for DHParser

- testing.py -- test support for DHParser based grammars and compilers



Main Modules Reference
======================

The core of DHParser are the modules containing the functionality
for the parsing and compiling process. The modules ``preprocess``,
``parse``, ``transform`` and ``compile`` represent particular stages of the
parsing/compiling process, while ``syntaxtree`` and ``error`` define
classes for syntax trees and parser/compiler errors, respectively.

Module ``preprocess``
---------------------

.. automodule:: preprocess
   :members:

Module ``syntaxtree``
---------------------

.. automodule:: syntaxtree
   :members:

Module ``parse``
----------------

.. automodule:: parse
   :members:

Module ``transform``
--------------------

.. automodule:: transform
   :members:

Module ``compile``
--------------------

.. automodule:: compile
   :members:

Module ``error``
----------------

.. automodule:: error
   :members:


Domain Specific Language Modules Reference
==========================================

DHParser contains additional support for domain specific languages.
Module ``ebnf`` provides a self-hosting parser for EBNF-Grammars as
well as an EBNF-compiler that compiles an EBNF-Grammar into a
DHParser based Grammar class that can be executed to parse source text
conforming to this grammar into contrete syntax trees.

Module ``dsl`` contains additional functions to support the compilation
of arbitrary domain specific languages (DSL).

One very indispensable part of the systematic construction of domain
specific languages is testing. DHParser supports unit testing of
smaller as well as larger components of the Grammar of a DSL.



Module ``ebnf``
---------------

.. automodule:: ebnf
   :members:

Module ``dsl``
--------------

.. automodule:: dsl
   :members:

Module ``testing``
------------------

.. automodule:: testing
   :members:



Supporting Modules Reference
============================

Finally, DHParser comprises a number of "toolkit"-modules which
define helpful functions and classes that will are used at different
places throughout the other DHParser-modules.

Module ``server``
------------------

.. automodule:: server
   :members:

Module ``toolkit``
------------------

.. automodule:: toolkit
   :members:

Module ``trace``
------------------

.. automodule:: trace
   :members:

Module ``log``
--------------

.. automodule:: log
   :members:

Module ``stringview``
---------------------

.. automodule:: stringview
   :members:

Module ``versionnumber``
------------------------

.. automodule:: versionnumber
   :members:
