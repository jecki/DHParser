Overview of DHParser
====================

DHParser is a parser-generator and domain-specific-language (DSL) construction kit that
is designed to make the process of designing, implementing and revising a DSL as
simple as possible. It can be used in an adhoc-fashion for small projects and
the grammar can be specified in Python like `pyparsing <https://pypi.org/project/pyparsing/>`_
or in a slightly amended version of the
`Extended-Backus-Naur-Form (EBNF) <https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form>`_
directly within the Python-code. Or DHParser can used for large projects where you set up a
directory tree with the grammar, parser, test-runner each residing in a separate file und the
test and example code in dedicated sub-directories.

DHParser uses `packrat parsing <https://bford.info/packrat/>`_ with full left-recursion support
which allows to build parsers for any context-free grammar. It's got a post-mortem debugger
to analyse the parsing process and it offers facilities for unit-testing grammars and some
support for fail-tolerant parsing so that the parser does not stop at the first syntax error
it encounters. Finally, there is some support for writing language servers for DSLs
in Python that adhere to editor-independent the
`language server-protocol <https://microsoft.github.io/language-server-protocol/>`_.


Generating a parser from a Grammar
----------------------------------

Generating a parser does not requires more than writing your grammar in EBNF
and compiling it with the "dhparser"-command into a readily usable Python-script!
To generate a json-Parser, just store the following EBNF-code in a file named "json.ebnf"::

        @literalws  = right
        @drop       = whitespace, strings
        @disposable = /_\w+/

        json        = ~ _element _EOF
        _element    = object | array | string | number | _bool | null
        object      = "{" member { "," §member } §"}"
        member      = string §":" _element
        array       = "[" [ _element { "," _element } ] §"]"
        string      = `"` §_CHARACTERS `"` ~
        number      = INT [ FRAC ] [ EXP ] ~
        _bool       = true | false
        true        = `true` ~
        false       = `false` ~
        null        = "null"

        _CHARACTERS = { PLAIN | ESCAPE }
        PLAIN       = /[^"\\]+/
        ESCAPE      = /\\[\/bnrt\\]/ | UNICODE
        UNICODE     = "\u" HEX HEX
        HEX         = /[0-9a-fA-F][0-9a-fA-F]/

        INT         = [`-`] ( /[1-9][0-9]+/ | /[0-9]/ )
        FRAC        = `.` /[0-9]+/
        EXP         = (`E`|`e`) [`+`|`-`] /[0-9]+/

        _EOF        =  !/./

(The three lines starting with an ``@``-sign at the beginning of the
grammar-string are not standard EBNF-code,  but DHParser-directives (see :py:mod:`ebnf`)
which help to streamline the syntax-tree that the parser produces.)

Then, run the "dhparser"-script to generate a parser::

    $ dhparser json.ebnf

This generates a script ``jsonParser.py`` that can be called with any
text-file or string to produce a syntax-tree::

    $ echo '{ "one": 1, "two": 2 }' >test.json
    $ python jsonParser.py --xml test.json
    <json>
      <object>
        <member>
          <string>
            <ANONYMOUS_Text__>"</ANONYMOUS_Text__>
            <PLAIN>one</PLAIN>
            <ANONYMOUS_Text__>"</ANONYMOUS_Text__>
          </string>
          <number>
            <INT>1</INT>
          </number>
        </member>
        <member>
          <string>
            <ANONYMOUS_Text__>"</ANONYMOUS_Text__>
            <PLAIN>two</PLAIN>
            <ANONYMOUS_Text__>"</ANONYMOUS_Text__>
          </string>
          <number>
            <INT>2</INT>
          </number>
        </member>
      </object>
    </json>


Mind that the generated script does not yield the json data in form of a
nested tree of python dictionaries and arrays but only the syntax tree
of the json-data. However, it is easy to get from there to your json-objects.


Creating parsers within a Python-script
---------------------------------------

In case you just need a parser for some very simple DSL, you can directly add a string
with the EBNF-grammar of that DSL to you python code and compile if into an executable
parser much like you'd compile a regular expresseion. Let's do this for a
`JSON <https://www.json.org/json-en.html>`_-parser::

    import sys
    from DHParser.dsl import create_parser

    json_grammar = r"""
        @literalws  = right
        @drop       = whitespace, strings
        @disposable = /_\w+/

        json        = ~ _element _EOF
        _element    = object | array | string | number | _bool | null
        object      = "{" member { "," §member } §"}"
        member      = string §":" _element
        array       = "[" [ _element { "," _element } ] §"]"
        string      = `"` §_CHARACTERS `"` ~
        number      = INT [ FRAC ] [ EXP ] ~
        _bool       = true | false
        true        = `true` ~
        false       = `false` ~
        null        = "null"

        _CHARACTERS = { PLAIN | ESCAPE }
        PLAIN       = /[^"\\]+/
        ESCAPE      = /\\[\/bnrt\\]/ | UNICODE
        UNICODE     = "\u" HEX HEX
        HEX         = /[0-9a-fA-F][0-9a-fA-F]/

        INT         = [`-`] ( /[1-9][0-9]+/ | /[0-9]/ )
        FRAC        = `.` /[0-9]+/
        EXP         = (`E`|`e`) [`+`|`-`] /[0-9]+/

        _EOF        =  !/./
        """

    json_parser = create_parser(json_grammar, 'JSON')

    if __name__ == '__main__':
        if len(sys.argv) > 1:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                json_text = f.read()
        else:
            # just a test
            json_text = '{ "one": 1, "two": 2 }'
        syntax_tree = json_parser(json_text)
        print(syntax_tree.serialize(how='XML'))


Specifying a parser can also be done directly with Python-code
instead of compiling an EBNF-grammar first::

    import sys, re

    from DHParser.parse import Grammar, Forward, Whitespace, Drop, NegativeLookahead, \
        ZeroOrMore, RegExp, Option, TKN, DTKN, Text

    _element = Forward().name('_element', disposable=True)
    _dwsp = Drop(Whitespace(r'\s*'))
    _EOF = NegativeLookahead(RegExp('.'))
    EXP = (Text("E") | Text("e") + Option(Text("+") | Text("-")) + RegExp(r'[0-9]+')).name('EXP')
    FRAC = (Text(".") + RegExp(r'[0-9]+')).name('FRAC')
    INT = (Option(Text("-")) + RegExp(r'[1-9][0-9]+') | RegExp(r'[0-9]')).name('INT')
    HEX = RegExp(r'[0-9a-fA-F][0-9a-fA-F]').name('HEX')
    UNICODE = (DTKN("\\u") + HEX + HEX).name('unicode')
    ESCAPE = (RegExp('\\\\[/bnrt\\\\]') | UNICODE).name('ESCAPE')
    PLAIN = RegExp('[^"\\\\]+').name('PLAIN')
    _CHARACTERS = ZeroOrMore(PLAIN | ESCAPE)
    null = TKN("null").name('null')
    false = TKN("false").name('false')
    true = TKN("true").name('true')
    _bool = true | false
    number = (INT + Option(FRAC) + Option(EXP) + _dwsp).name('number')
    string = (Text('"') + _CHARACTERS + Text('"') + _dwsp).name('string')
    array = (DTKN("[") + Option(_element + ZeroOrMore(DTKN(",") + _element)) + DTKN("]")).name('array')
    member = (string + DTKN(":") + _element).name('member')
    json_object = (DTKN("{") + member +  ZeroOrMore(DTKN(",") + member) + DTKN("}")).name('json_object')
    _element.set(json_object | array | string | number | _bool | null)
    json = (_dwsp + _element + _EOF).name('json')

    json_parser = Grammar(json)

    if __name__ == '__main__':
        if len(sys.argv) > 1:
            with open(sys.argv[1], 'r', encoding='utf-8') as f:
                json_text = f.read()
        else:
            # just a test
            json_text = '{ "one": 1, "two": 2 }'
        syntax_tree = json_parser(json_text)
        print(syntax_tree.serialize(how='indented'))

There are few caveats when defining parsers directly within Python-code:
Any parser that is referred to in other parsers must be assigned to a variable. Unless they are
disposable (see :py:ref`~ebnf.simlpifying_syntax_trees`), they also must be assigned their name
explicitly with the :py:meth:`~parse.Parser.name`-method. Forward-declarations always need to be
named explicitly, even if the declared parser is considered disposable.

In order to avoid namespace pollution, the variables defining the parser can be encapsulated in
a class definition::

    class JSON:
        _element = Forward().name('_element', disposable=True)
        ...
        json = (_dwsp + _element + _EOF).name('json')

    json_parser = Grammar(JSON.json)
    ...

Usually, however, it is best to specify the grammar in EBNF, compile it and then copy and paste the
compiled grammar into your script, because this saves startup time over compiling the
grammar within the script.


.. _full_scale_DSLs:

Full scale DSLs
---------------

Larger and more complex DSL-projects can easily be setup by calling the "dhparser"-script
with a name of a project-directory that will then be created and filled with some templates::

   $ dhparser JSON
   $ cd JSON
   $ dir
   example.dsl  JSON.ebnf    JSONServer.py  README.md  tests_grammar  tst_JSON_grammar.py

The first step is to replace the ".ebnf"-file that contains a simple demo-grammar with your
own grammar. For the sake of the example we'll write our json-Grammar into this file::

    #  EBNF-Directives

    @literalws  = right  # eat insignificant whitespace to the right of literals
    @whitespace = /\s*/  # regular expression for insignificant whitespace
    @comment    = /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/  # C++ style comments
    @drop       = whitespace, strings  # silently drop bare strings and whitespace
    @disposable = /_\w+/  # regular expression to identify disposable symbols

    #:  compound elements

    json        = ~ _element _EOF
    _element    = object | array | string | number | _bool | null
    object      = "{" member { "," §member } §"}"
    member      = string §":" _element
    array       = "[" [ _element { "," _element } ] §"]"

    #:  simple elements

    string      = `"` §_CHARACTERS `"` ~
    number      = INT [ FRAC ] [ EXP ] ~
    _bool       = true | false
    true        = `true` ~
    false       = `false` ~
    null        = "null"

    #:  atomic expressions types

    _CHARACTERS = { PLAIN | ESCAPE }
    PLAIN       = /[^"\\]+/
    ESCAPE      = /\\[\/bnrt\\]/ | UNICODE
    UNICODE     = "\u" HEX HEX
    HEX         = /[0-9a-fA-F][0-9a-fA-F]/

    INT         = [`-`] ( /[1-9][0-9]+/ | /[0-9]/ )
    FRAC        = `.` /[0-9]+/
    EXP         = (`E`|`e`) [`+`|`-`] /[0-9]+/

    _EOF        =  !/./

The division of the grammar into several sections is purely conventional. If
a comment-line starts with ``#:`` this is a hint to the test script
to generate a separate unit-test-template for the following section.

The ``tst_..._grammar.py``-script is the most important tool in any DSL-project.
The script generates or updates the ``...Parser.py``-program if the grammar
has changed and runs the unit tests in the ``tests_grammar`` subdirectory.
After filling in the above grammar in the ``json.ebnf``-file, a parser can
be generated by running the test script::

    $ python tst_JSON_grammar.py

If there were no errors, a new ``jsonParser.py`` appears in the directory.
Before we can try it, we need some test-data. Then we can run the script
just like before::

    $ rm example.dsl
    $ echo '{ "one": 1, "two": 2 }' >example.json
    $ python JSONParser.py --xml example.json
    <json>
      <object>
      ...

Clutter-free grammars
---------------------

DHParser tries to minimize unnecessary clutter in grammar definitions.
To reach this goal DHParser follows a few, mostly intuitive, conventions:

1. The symbols on the left hand side of any definition (or "rule" or "production")
   are considered significant by default.

   Nodes generated by a parser associated to a symbol will carry the
   symbol's name and cannot be eliminated, silently. All other nodes are
   considered as disposable and may silently be removed from the tree to
   simplify its structure, but preserving the content.

2. Symbols can, however, be marked as "disposable", too.

   Thus, you'll never see an "_elment"-node in a JSON-syntax-tree produced
   by the above grammar, but only object-, array-, string-, number-, true-,
   false- or null-nodes. (See :py:func:`~ebnf.simplifying_syntax_trees`.)

3. Insignificant whitespace is denoted with a the single character: ``~``.

4. Comments defined by the ``@comment``-directive at the top of the grammar
   are allowed in any place where insignificant ``~``-whitespace is
   allowed.

   Thus, you never need to worry about where to provide for
   comments in you grammar. It is as easy as it is intuitive.
   (See :py:func:`~ebnf.comments_and_whitespace`.)

5. To keep the grammar clean, delimiters like "," or "[", "]"
   can catch adjacent whitespace (and comments), automatically.

   Since delimiters are typically surrounded by insignificant whitespace,
   DHParser can be advised via the ``@literalws``-directive to
   catch insignificant whitespace to the
   right or left hand side of string literals, keeping the
   grammar clear of too many whitespace markers.

   In case you want to grab a string without
   eating its adjacent whitespace, you can still use the "backt-icked"
   notation for string literals ```back-ticked string```.

6. DHParser can be advised (vie the ``@drop``-directive) to drop
   string-tokens completely from the syntax-tree and, likewise,
   insignificant whitespace or disposable symbols. This greatly reduces
   the verbosity of the concrete syntax tree.

   In case you want to keep a particular string-token in the tree
   none the less, you can still do so by assigning it to a
   non-disposable symbol, e.g. ``opening_bracket = "("`` and using
   this symbol instead of the string literal in other expressions.

7. Ah, and yes, of course, you do not need to end grammar definitions
   with a semicolon ``;`` as demanded by the ISO-norm for EBNF :-)


Declarative AST-building
------------------------

DHParser does does not hide any stages of the tree generation
process. Thus, you get full access to the (simplified) concrete
syntax tree (CST) as well as to the abstract syntax tree (AST).

An internal mini-DSL for AST-transformation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Abstract syntax tree generation is controlled in
declarative style by simple lists of transformations
applied to each node depending on its type. Remember
our JSON-example from above? In the simplified
concrete syntax tree string-objects still contained the
quotation mark delimiting the string. Since these are not
needed in the data you'd like to retrieve from a JSON-file,
let's remove them from the abstract syntax-tree::

    JSON_AST_transformation_table = {
        "string": [remove_brackets]
    }

The ``JSON_AST_transformation_table``-dictionary can
be found in the generated ``JSONParser.py``-script.
Simply add the rule "remove_bracket" from the
:py:mod:`transform`-module to the list of rules
for those nodes where you wish to remove any delimiters
at the beginning or end::

    $ python JSONParser.py --xml example.json
    <json>
      <object>
        <member>
          <string>
            <PLAIN>one</PLAIN>
          </string>
    ...

Alternatively, you could also have used the rule
``"string": [remove_children(':Text')]`` in case you
are sure that nodes with the tag-name ":Text" can
only occur in a string at the beginning and at the
end as nodes containing the quotation mark-delimiters
of that string.

To give an expression how AST-transformation-tables
may look like, here is an excerpt from (a former
version of) DHParser's own transformation table
to derive a lean AST from the concrete syntax-tree
of an EBNF grammar::

    EBNF_AST_transformation_table = {
        # AST Transformations for EBNF-grammar
        "syntax":     [],
        "directive":  [flatten, remove_tokens('@', '=', ',')],
        "definition": [flatten, remove_tokens('=')]
        "expression": [replace_by_single_child, flatten,
                       remove_tokens('|')]
        "sequence":   [replace_by_single_child, flatten],
        ...
    }

The :py:mod:`transform`-module
contains a number of useful transformation-rules
that can be combined almost arbitrarily in order
to reshape the concrete syntax-tree and carve
out the abstract syntax tree. However, if the
grammar is well-designed and if the
concrete syntax tree has already been simplified
with the help of DHParser's ``@disposable``-,
``@reduction``- and ``@drop``-directives, only
few transformations should be necessary to produce
the abstract syntax-tree.

In specific application cases it is often desirable
to model the abstract syntax-tree as a tree of
objects of different classes. However, since DHParser
is a generic Parser-generator, DHParser's syntax-trees
are composed of a single :py:class:`~nodetree.Node`-type.
Nodes contain either text-data or have one or more other nodes
as children (but not both). The "kind" or "type"
of a node is indicated by its "tag-name". It should be
easy, though, to this tree of nodes into an
application-specific tree of objects of different classes.

Serialization as you like it: XML, JSON, S-expressions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

DHParser makes it easy to visualize the various stages
of tree-transformation (CST, AST, ...) by offering
manifold serialization methods that output syntax-trees
in either a nicely formatted or compact form.

1. S-expressions::

    >>> syntax_tree = JSONParser.parse_JSON('{ "one": 1, "two": 2 }')
    >>> JSONParser.transform_JSON(syntax_tree)
    >>> print(syntax_tree.as_sxpr())
    (json
      (object
        (member
          (string
            (PLAIN "one"))
          (number
            (INT "1")))
        (member
          (string
            (PLAIN "two"))
          (number
            (INT "2")))))

2. XML::

    >>> print(syntax_tree.as_xml(indent=None))
    <json>
      <object>
        <member>
          <string>
            <PLAIN>one</PLAIN>
          </string>
          <number>
            <INT>1</INT>
          </number>
        </member>
        <member>
          <string>
            <PLAIN>two</PLAIN>
          </string>
          <number>
            <INT>2</INT>
          </number>
        </member>
      </object>
    </json>

3. JSON::

    >>> print(syntax_tree.as_json(indent=None))
    ["json",[["object",[["member",[["string",[["PLAIN","one",3]],2],["number",[["INT","1",9]],9]],2],["member",[["string",[["PLAIN","two",13]],12],["number",[["INT","2",19]],19]],10]],0]],0]

4. Indented text-tree::

    >>> print(syntax_tree.as_tree())
    json
      object
        member
          string
            PLAIN "one"
          number
            INT "1"
        member
          string
            PLAIN "two"
          number
            INT "2"

All but the last serialization-formats can be de-serialized into
a tree of nodes with the functions: :py:func:`~nodetree.parse_sxpr`,
:py:func:`~nodetree.parse_xml`, :py:func:`~nodetree.parse_json`.
The :py:func:`~nodetree.parse_xml` is not restricted to de-serialization but
can parse any XML into a tree of nodes.

XML-connection
^^^^^^^^^^^^^^

Since DHParser has been build with Digital-Humanities-applications in mind,
it offers to further methods to connect to X-technologies. The methods
:py:meth:`~nodetree.Node.as_etree` and :py:meth:`~nodetree.Node.from_etree`
allow direct transfer to and from the xml-ElementTrees of either the
Python standard-library or the lxml-package which offers full support for
XPath, XQuery and XSLT.


Test-driven grammar development
-------------------------------

Just like regular expressions, it is quite difficult to get
EBNF-grammars right on the first try - especially, if you are
new to the technology. DHParser offers a unit-testing
environment and a dbugger for EBNF-grammars which
is helpful when learning to work with parser-technology
and almost indispensable when refactoring the grammar of
evolving DSLs.

This unit-testing system is quite simple to handle: Tests
for any symbol of the grammar are written into ``.ini``-Files
in the ``tests_grammar`` sub-directory of the DSL-project.
Test-cases look like this::

    [match:number]
    M1: "-3.2E-32"
    M2: "42"

Here, we test, whether the parser "number" really matches the
given strings as we would expect. "M1" and "M2" are arbitrary
names for the individual test-cases. Since parsers should not
only match strings that conform to the grammar of that
parser, but must also fail to match strings that don't, it
is also possible to specify "fail-tests"::

    [fail:number]
    F1: "π"

Running the ``tst_JSON_grammar.py``-script on a test-file
the test-directory yields the results of those tests::

    $ python tst_JSON_grammar.py tests_grammar/02_simple_elements.ini
    GRAMMAR TEST UNIT: 02_test_simple_elements
      Match-Tests for parser "number"
        match-test "M1" ... OK
        match-test "M2" ... OK
      Fail-Tests for parser "number"
        fail-test  "F1" ... OK

    SUCCESS! All tests passed :-)

In addition to this summary-report the test-script stores
detailed reports of all tests for each test-file into
Markdown-documents in the "test_grammar/REPORTS" directory.
These reports contain the ASTs of all matches and the
error messages for all fail-tests. If we look at the
AST of the first match-test "M1" we might find to our
surprise that it is not what we expect, but much more verbose::

   (number (INT (NEG "-") (:RegExp "3"))
           (FRAC (DOT ".") (:RegExp "2"))
           (EXP (:Text "E") (:Text "-") (:RegExp "32")))

None, of these details are really needed in an abstract syntax-tree.
Luckily, ASTs can also be tested for, which allows to develop
AST-generation in a test driven manner. We simply need to add
an AST-Test to the grammar with the same name as the match-test
that yields the AST we'd like to test::

    [ast:number]
    M1: (number "-3.2E-32")

Running the test-suite will, of course, yield a failure for the
AST-Test until we fix the issue, which in this case could be done
by adding ``"number": [collapse]`` to our AST-transformations.
Since it is sometimes helpful to inspect the CST as well, a
match test's name can be marked with an asterix, e.g.
``M1*:  "-3.2E-32"`` to include the CST for this test in the
report, too.

If a parser fails to match it is sometimes hard to tell, what
mistake in the grammar definition has been responsible for that
failure. DHParser's testing-framwork therefore includes a
post-mortem debugger that delivers a detailed account of the
parsing process up to the failure. These accounts will be
written in HTML-format into the ``test_grammar/LOGS``-subdirectory
and can be viewed with a browser.

To see what this looks like, let's introduce a little mistake
into our grammar, let's assume that we had forgotten that
the exponent of a decimal number can also be introduced by
a capital letter "E": ``EXP = `e` [`+`|`-`] /[0-9]+/``.

.. image:: debugger_snippet.png
    :alt: a screenshot of DHParser's post-mortem-debugger

While error messages help to locate errors in the source
text, the grammar-debugger helps to locate the cause of
an error that is not due to a faulty source text but a
faulty grammar in the grammar.

Fail-tolerant parsing
---------------------

Fail-tolerance is the ability of a parser to resume parsing after an
error has been encountered. A parser that is fail-tolerant does not
stop parsing at the first error but can report several if not all
errors in a source-code file in one single run. Thus, the user is
not forced to fix an earlier error before she is even being informed
of the next error. Fail-tolerance is a particularly desirable property
when using a modern IDE that annotates errors while typing the
source code.

DHParser offers support for fail-tolerant parsing that goes beyond what
can be achieved within EBNF alone. A prerequisite for fail-tolerant-parsing
is to annotate the the grammar with ``§``-markers ("mandatory-marker") at
places where one can be sure that the parser annotated with the marker
must match if it is called at all. This is usually the case for parsers
in a series after the point where it is uniquely determined.

F or example, once the opening bracket of a bracketed expression has
been matched by a parser it is clear that eventually the closing bracket will be matched
by its respective parser, too, or it is an error. Thus, in our JSON-grammar
we could write::

    array       = "[" [ _element { "," _element } ] §"]"

The ``§`` advises the following parser(s) in the series to raise an error
on the spot instead of merely returning a non-match if they fail.
If we wantet to, we could also add a ``§``-marker in front of the second
``_element``-parser, because after a komma there must always be another
element in an array or it is an error.

The §-marker can be supplemented with a ``@ ..._resume``-directive that
tells the calling parsers where to continue after the array parser has failed.
So, the parser resuming the parsing process is not the array parser that
has failed, but the first of the parsers in the call-stack of the array-parser that
catches up at the location indicated by the ``@ ..._resume``-directive.
The location itself is determined by a regular expression, where the
point for reentry is the location *after* the next match of the regular
expression::

    @array_resume = /\]/
    array       = "[" [ _element { "," _element } ] §"]"

Here, the whole array up to and including the closing bracket ``]`` will
be skipped and the calling parser continue just as if the array had matched.

Let's see the difference this makes by running both versions of the grammar
over a simple test case::

    [match:json]
    M1: '''{ "number":  1,
             "array": [1,2 3,4],
             "string": "two" }'''

First, without re-entrance and without ``§``-marker the error message is not very informative and
no structure has been detected correctly. At least the location of the error has been determined
with good precision by the "farthest failure"-principle.::

    ### Error:

    2:15: Error (1040): Parser "array->`,`" did not match: »3,4],
    "string": "two ...«
        Most advanced fail:    2, 15:  json->_element->object->member->_element->array-> `,`;  FAIL;  "3,4],\n"string": "two" }"
        Last match:       2, 13:  json->_element->object->member->_element->array->_element->number;  MATCH;  "2 ";

    ### AST

        (ZOMBIE__ (ZOMBIE__ `() '{ "number": 1,' "") (ZOMBIE__ '"array": [1,2 3,4],' '"string": "two" }'))

Secondly, still without re-entrance but with the ``§``-marker. The error-message is more precise, though the
followup-error "Parser stopped before end" may be confusing. The AST-tree (not shown here) contains more
structure, but is still littered with ``ZOMBIE__``-nodes of unidentified parts of the input::

    ### Error:

    2:12: Error (1040): Parser "json" stopped before end, at:  3,4],
    "str ...  Terminating parser.
    2:15: Error (1010): `]` ~ expected by parser 'array', »3,4],\n "str...« found!


Finally, with both ``§``-marker and resume-directive as denoted in the EBNF snippet
above, we receive a sound error message and, even more surprising, an almost complete
AST::

    ### Error:

    2:15: Error (1010): `]` ~ expected by parser 'array', »3,4],\n "str...« found!

    ### AST

        (json
          (object
            (member
              (string
                (PLAIN "number"))
              (number "1"))
            (member
              (string
                (PLAIN "array"))
              (array
                (number "1")
                (number "2")
                (ZOMBIE__ `(2:15: Error (1010): `]` ~ expected by parser 'array', »3,4],\n "str...« found!) ",2 3,4]")))
            (member
              (string
                (PLAIN "string"))
              (string
                (PLAIN "two")))))



Compiling DSLs
--------------

As explained earlier (see :ref:_full_scale_DSLs), full scale DSL-projects
contain a test-script the name of which starts with ``tst_...`` that generates
and updates (if the grammar has been changed) a parser-script the name of which
ends with ``...Parser.py``. This parser script can be used to "compile" documents
written in the DSL described by the ebnf-Grammar in the project directory. When
running this script yields a concrete-syntax-tree. In almost all cases, you'll
want to adjust the ``...Parser.py`` script, so that yields the data in contained
in the compiled document. This, however, requires further processing steps than
just parsing. The ``...Parser.py``-script contains four different sections,
nameley, the **Preprocesser**-, **Parser**-, **AST**- and **Compiler**-sections.
Once this script has been generated, only the Parser-section will be updated
automatically when running the ``tst_...``-scripts. The Parser-section should
therefore be left untouched, because any change might be overwritten without
warning. For the same reason the comments demarking the different sections should
be left intact. All other sections can and - with the exceptions of the
Preprocessor-section - usually must be edited by hand in order to allow the
``..Parser.py``-script to return the parsed data in the desired form.

Because for most typical DSL-projects, preprocessors are not needed, the
Preprocessor-section will be not be discussed, here. The other two sections,
AST and Compiler, contain skeletons for (different kinds of)
tree-transformations that can be edited as will or even completely be substituted
by custom code. All sections (including "Preprocessor") comprise a callable class
or an "instantiation function" returning a transformation function that should be
edited as well as a ``get_...``-function
that returns a thread-specific instance of this class or function and a function
that passes a call through to this thread-specific instance. Only the
transformation-function proper needs to be touched. The other two functions are
merely scaffolding to ensure thread-safety so that you do not have to worry
about it, when filling in the transformation-function proper.

In the case of our json-parser, the skeleton for the Compilation  looks
like this::

    class jsonCompiler(Compiler):
        """Compiler for the abstract-syntax-tree of a json source file.
        """

        def __init__(self):
            super(jsonCompiler, self).__init__()

        def reset(self):
            super().reset()
            # initialize your variables here, not in the constructor!

        def on_json(self, node):
            return self.fallback_compiler(node)

        ...

        # def on__EOF(self, node):
        #     return node


    get_compiler = ThreadLocalSingletonFactory(jsonCompiler, ident=1)

    def compile_json(ast):
        return get_compiler()(ast)


Here, the ``get_compiler()``- and ``compile_json()``-functions do not need to be
touched, while the ``jsonCompiler``-class should be edited at will or be replaced
by a functions that returns a transformation functions, i.e. a function that
takes a syntax tree as input and returns an arbitrary kind of output. In this example,
it is reasonable to expect a nested Python-data-structure as output that contains
the data of the json-file. We'll se below, how this could be done.

Let's first look at the AST-transformation-skeleton::

    json_AST_transformation_table = {
        # AST Transformations for the json-grammar
        "json": [],
        ...
        "_EOF": []
    }

    def jsonTransformer() -> TransformationFunc:
        """Creates a transformation function that does not share state with other
        threads or processes."""
        return partial(traverse, transformation_table=json_AST_transformation_table.copy())

    get_transformer = ThreadLocalSingletonFactory(jsonTransformer, ident=1)

    def transform_json(cst):
        get_transformer()(cst)

This may look slightly more complicated, because per default the AST-transformations
are defined declaratively by a transformation-table. Of course, you are free to replace
the table-definition and the ``jsonTransformer``-instantian function alltogether by
class like in the compilation section. (See the XML-example in the examples-subdirectory
of the DHParser-repository.) However, filling in the table, allows to define
the abstract-syntax-tree-transformation to be described by sequences of simple rules
that are applied to each node that simplify and streamline the syntax-tree coming from
the parser, which is most of the time sufficient to distill an abstract-syntax-tree
from a concrete syntax-tree::

Language Servers
----------------

Performance
-----------

