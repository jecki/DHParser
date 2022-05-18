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

DHParser is by now mature and "production ready". It is being used in several projects,
most notably for the domain specific notation of the `Medieval Latin Dictionary`_
and the Typescript-to-Python-interface-transpiler `ts2python`_

License
--------

DHParser is open source software under the `Apache 2.0 License`_.

Copyright 2016-2022  `Eckhart Arnold <arnold@badw.de>`_, Bavarian Academy of Sciences and Humanities

The source code can downloaded from: `gitlab.lrz.de/badw-it/DHParser <https://gitlab.lrz.de/badw-it/DHParser>`_


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
   Manuals.rst
   Reference.rst

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _Medieval Latin Dictionary: https://mlw.badw.de/en/
.. _ts2python: https://github.com/jecki/ts2python
.. _Apache 2.0 License: https://www.apache.org/licenses/LICENSE-2.0