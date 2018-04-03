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
of the work with DHParser is done from the shell. In the following, we assume
a Unix (Linux) environment. The same can most likely be done on other
operating systems in a very similar way, but there might be subtle
differences.

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

In order to verify that the installation works, you can simply run the
"dhparser.py" script and, when asked, chose "3" for the self-test. If the
self-test runs through without error, the installation has succeded.

Staring a new DHParser project
------------------------------

In order to setup a new DHParser project, you run the ``dhparser.py``-script
with the name of the new project. For the sake of the example, let's type::

   $ python dhparser.py experimental/poetry
   $ cd experimental/poetry

This creates a new DHParser-project with the name "poetry" in directory with
the same name within the subdirectory "experimental". This new directory
contains the following files::

    README.md           - a stub for a readme-file explaiing the project
    poetry.ebnf         - a trivial demo grammar for the new project
    example.dsl         - an example file written in this grammar
    tst_poetry_grammar.py - a python script ("test-script") that re-compiles
                            the grammar (if necessary) and runs the unit tests
    grammar_tests/01_test_word.ini     - a demo unit test
    grammar_tests/02_test_document.ini - another unit test

Now, if you look into the file "example.dsl" you will find that it contains a
simple sequence of words, namely "Life is but a walking shadow". In fact, the
demo grammar that comes with a newly created project is nothing but simple
grammar for sequences of words separated by whitespace. Now, since we alread
have unit tests, our first exercise will be to run the unit tests by starting
the script "tst_poetry_grammar.py"::

   $ python tst_poetry_grammar.py

This will run through the unit-tests in the grammar_tests directory and print
their success or failure on the screen. If you check the contents of your
project directory after running the script, you might notice that there now
exists a new file "poetryCompiler.py" in the project directory. This is an
auto-generated compiler-script for our DSL. You can use this script to compile
any source file of your DSL, like "example.dsl". Let's try::

   $ python poetryCompiler.py example.dsl

The output is a block of pseudo-XML, looking like this::

   <document>
     <:ZeroOrMore>
       <WORD>
         <:RegExp>Life</:RegExp>
         <:Whitespace> </:Whitespace>
       </WORD>
       <WORD>
         <:RegExp>is</:RegExp>
         <:Whitespace> </:Whitespace>
       </WORD>
    ...

Now, this does not look too helpful yet, partly, because it is cluttered with
all sorts of seemingly superflous pseudo-XML-tags like "<:ZeroOrMore>".
However, you might notice that it contains the original sequence of words
"Life is but a walkting shadow" in a structured form, where each word is
(among other things) surrounded by <WORD>-tags. In fact, the output of the
compiler script is a pseudo-XML-representation of the *contrete syntax tree*
of our "example.dsl"-document according the grammar specified in "poetry.ebnf"
(which we haven't looked into yet, but we will do so soon).

If you see the pseudo-XML on screen, the setup of the new DHParser-project
has been successful.

Understanding how compilation of DSL-documents with DHParser works
------------------------------------------------------------------

Generally speaking, the compilation process consists of three stages:

1. Parsing a document. This yields a *concrete syntax tree* (CST) of the
   document.

2. Transforming. This transforms the CST into the much more concise *abstract
   syntax tree* (AST) of the document.

3. Compiling. This turns the AST into anything you'd like, for example, an
   XML-representation or a relational database record.

Now, DHParser can fully automize the generation of a parser from a
syntax-description in EBNF-form, like our "poetry.ebnf", but it cannot
automize the transformation from the concrete into the abstract syntax tree
(which for the sake of brevity we will simply call "AST-Transformation" in the
following), and neither can it automize the compilation of the abstract syntax
tree into something more useful. Therefore, the AST-Transformation in the
autogenerated compile-script is simply left empty, while the compiling stage
simply converts the syntax tree into a pseudo-XML-format.

The latter two stages have to be coded into the compile-script by hand, with
the support of templates within this script. If the grammar of the DSL is
changed - as it will be frequently during the development of a DSL - the
parser-part of this script will be regenerated by the testing-script before
the unit tests are run. The script will notice if the grammar has changed.
This also means that the parser part of this script will be overwritten and
should never be edited by hand. The other two stages can and should be edited
by hand. Stubs for theses parts of the compile-script will only be generated
if the compile-script does not yet exist, that is, on the very first calling
of the test-srcipt.

Usually, if you have adjusted the grammar, you will want to run the unit tests
anyway. Therefore, the regeneration of the parser-part of the compile-script
is triggered by the test-script.

The development workflow for DSLs
---------------------------------

When developing a domain specific notation it is recommendable to first develop the grammar and the parser for that notation, then to the
abstract syntax tree transformations and finally to implement the compiler. Of course one can always come back and change the grammar later. But in order to avoid revising the AST-transformations and the compiler time and again it helps if the grammar has been worked out before. A bit of interlocking between these steps does not hurt, though.

A resonable workflow for developing the grammar proceeds like this:

1. Set out by writing down a few example documents for your DSL. It is
   advisable to start with a few simple examples that use only a subset of the
   intended features of your DSL.

2. Next you sktech a grammar for your DSL that is just rich enough to capture
   those examples.

3. Right after sketching the grammar you should write test cases for your
   grammar. The test cases can be small parts or snippets of your example
   documents. You could also use your example documents as test cases, but
   usually the test cases should have a smaller granularity to make locating
   errors easier.

4. Next, you should run the test script. Usually, some test will fail at
   the first attempt. So you'll keep revising the EBNF-grammar, adjusting and adding test cases until all tests pass.

5. Now it is time to try and compile the example documents. By this time the
   test-script should have generated the compile-script, which you can be
   called with the example documents. Don't worry too much about the output, yet. What is important at this stage is merely whether the parser can
   handle the examples or not. If not, further test cases and adjustments the
   EBNF grammar will be needed - or revision of the examples in case you decide to use different syntactic constructs.

   If all examples can be parsed, you go back to step one and add further more complex examples, and continue to do so until you have the feeling that you DSL's grammar is rich enough for all intended application cases.

Let's try this with the trivial demo example that comes with creating a new project with the "dhparser.py"-script. Now, you have already seen that the
"example.dsl"-document merely contains a simple sequence of words: "Life is but a walking shadow" Now, wouldn't it be nice, if we could end this sequence with a full stop to turn it into a proper sentence. So, open "examples.dsl" with a text editor and add a full stop::

   Life is but a walking shadow.

Now, try to compile "examples.dsl" with the compile-script::

   $ python poetryCompiler.py example.dsl
   example.dsl:1:29: Error: EOF expected; ".\n " found!

Since the grammar, obviously, did not allow full stops so far, the parser
returns an error message. The error message is pretty self-explanatory in this
case. (Often, you will unfortunately find that the error message are somewhat
difficult to decipher. In particular, because it so happens that an error the parser complains about is just the consequence of an error made at an earlier location that the parser may not have been able to recognize as such. We will learn more about how to avoid such situations, later.) EOF is actually the name of a parser that captures the end of the file, thus "EOF"! But instead of the expected end of file an, as of now, unparsable construct, namely a full stop followed by a line feed, signified by "\n", was found.


