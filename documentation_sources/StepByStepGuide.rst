*****************************
DHParser's Step by Step Guide
*****************************

This step by step guide goes through the whole process of desining and testing
a domain specific notation from the very start. (The terms "domain specific
noation" and "domain specific language" are used interchangeably in the
following. Both will abbreviated by "DSL", however.) We will design a simple
domain specific notation for poems as a teaching example. On the way we will
learn:

1. how to setup a new DHParser project

2. how to use the test driven development approach to designing a DSL

3. how to describe the syntax of a DSL with the EBNF-notation

4. how to specify the transformations for converting the concrete syntax tree
   that results from parsing a text denoted in our DLS into an abstract syntax
   tree that represents or comes close to representing out data model.

5. how to write a compiler that transforms the abstract syntax tree into a
   target representation which might be a html page, epub or printable pdf in
   the case of typical Digital-Humanities-projects.


Setting up a new DHParser project
=================================

Since DHParser, while quite mature in terms of implemented features, is still
in a pre-first-release state, it is for the time being more recommendable to
clone the most current version of DHParser from the git-repository rather than
installing the packages from the Python Package Index (PyPI).

This section takes you from cloning the DHParser git repository to setting up
a new DHParser-project in the ``experimental``-subdirectory and testing
whether the setup works. Similarily to current web development practices, most
of the work with DHParser is done from the shell. In the following, we assume a Unix (Linux) environment. The same can most likely be done on other operating systems in a very similar way, but there might be subtle differences.

Installing DHParser from the git repository
-------------------------------------------

In order to install DHParser from the git repository, open up a shell window
and type::

   $ git clone git@gitlab.lrz.de:badw-it/DHParser.git
   $ cd DHParser

The second command changes to the DHParser directory. Within this directory
you should recognise the following subdirectories and files. There are more
files and directories for sure, but those will not concern us for now::

   DHParser/            - the DHParser python packages
   documentation/       - DHParser's documentation in html-form
   documentation_source - DHParser's documentation in reStructedText-Format
   examples/            - some exmamples for DHParser (mostly incomplete)
   experimental/        - an empty directory for experimenting
   test/                - DHParser's unit-tests
   dhparser.py          - DHParser's command line tool for setting up projects
   README.md            - General information about DHParser
   LICENSE.txt          - DHParser's license. It's open source (hooray!)
   Introduction.md      - An introduction and appetizer for DHParser

In order to setup a new DHParser project, you run the ``dhparser.py``-script
with the name of the new project. For the sake of the example, let's type::

   $ python dhparser.py experimental/poetry

   Creating new DHParser-project "poetry".
   Creating file "grammar_tests/01_test_word.ini".
   Creating file "grammar_tests/02_test_document.ini".
   Creating file "poetry.ebnf".
   Creating file "README.md".
   Creating file "tst_poetry_grammar.py".
   Creating file "example.dsl".
   ready.

   $ cd experimental/poetry

This creates a new DHParser-project with the name "poetry" in directory with the same name within the subdirectory "experimental".