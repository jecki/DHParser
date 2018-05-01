****************
Module Reference
****************

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


Module ``toolkit``
------------------

.. automodule:: toolkit
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
