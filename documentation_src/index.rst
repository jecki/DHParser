.. DHParser documentation master file, created by
   sphinx-quickstart on Sat Mar  3 13:46:42 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. default-domain::py

Welcome to DHParser's documentation!
====================================

DHParser is a parser generator and domain specific language
construction kit, designed for but not restricted to
Digital Humanities applications.

DHParser offers:

* Rapid Prototyping of EBNF based grammar specifications with support for
  different flavors of EBNF 
* Macros to reduce code repetition within grammars and includes to
  avoid code repetition between grammars.
* Parsing Expression Grammar (PEG) parser with memoization
  and full left recursion support
* unit testing framework for grammars
* post mortem debugger for generated parsers
* support for fail tolerant parsing
* customizable error messages
* extensive tree processing facilities
* support for building language servers (experimental)
* full unicode support

DHParser is by now mature and "production ready". It is being used in several projects,
most notably for the domain specific notation of the `Medieval Latin Dictionary`_
and the Typescript-to-Python interface transpiler `ts2python`_

License
--------

DHParser is open source software under the `Apache 2.0 License`_.

Copyright 2016-2024  `Eckhart Arnold <arnold@badw.de>`_, Bavarian Academy of Sciences and Humanities

The source code can downloaded from: `gitlab.lrz.de/badw-it/DHParser <https://gitlab.lrz.de/badw-it/DHParser>`_


Install DHParser
----------------

.. code:: bash

    $ python -m pip install --user DHParser

In order to use DHParser directly from the git repository, the best way is to make
a shallow clone of the repository and then add a symlink to the DHParser subdirectory
inside the DHParser repository in your project's directory. For setting up an entirely
new project with DHParser without using "pip install", the commands are the following:

.. code:: bash

    $ git clone --depth=1 https://gitlab.lrz.de/badw-it/DHParser
    $ python3 DHParser/DHParser/scripts/dhparser.py MyNewParserProject
    $ ln -s ../DHParser/DHParser MyNewParserProject/DHParser

In case you would like to use latest bugfixes from the development branch, the first command
should be exchanged with:

.. code:: bash

   $ git clone --depth=1 --single-branch --branch development https://gitlab.lrz.de/badw-it/DHParser

In order to verify that your local clone of the DHParser repository has been
correctly linked to your project's directory, type:

.. code:: bash

    $ cd MyNewParserProject
    $ python3 tst_MyNewParserProect_grammar.py



Documentation
-------------

.. toctree::
   :glob:
   :maxdepth: 2


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