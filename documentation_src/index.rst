.. DHParser documentation master file, created by
   sphinx-quickstart on Sat Mar  3 13:46:42 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. default-domain::py

Welcome to DHParser's documentation!
====================================

DHParser is a parser-generator and and domain-specific-languages
construction kit, designed for but not restricted to
Digital-Humanities-applications.

DHParser offers:

* EBNF-based grammar-specification language with support for
  different flavors of EBNF
* Parsing-Expression-Grammar (PEG)-parser with memoization
  and full left-recursion support
* full unicode support
* unit-testing-framework for grammars
* post-mortem debugger for generated parsers
* support for fail-tolerant parsing
* customizable error messages
* extensive tree-processing facilities
* support for building language servers (experimental)

Install DHParser
----------------

.. code:: bash

    $ python -m pip install --user DHParser

Resources
---------

.. toctree::
   :glob:
   :maxdepth: 2
   :caption: Contents:

   Overview.rst
   StepByStepGuide.rst
   Manual.rst
   Reference.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`