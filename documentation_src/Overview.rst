Overview of DHParser
====================

DHParser is a parser-generator and domain-specific-language (DSL) construction kit that
is designed to make the process of designing, implementing and revising as DSL as
simple as possible. It can be used in an adhoc-fashion for small projects and
the grammar can be specified in Python like `pyparsing <https://pypi.org/project/pyparsing/>`
or in a slightly amended version of the
`Extended-Backus-Naur-Form (EBNF) <https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form>`
directly within the Python-code. Or DHParser can used for large projects where you set up a
directory tree with the grammar, parser, test-runner each residing in a separate file und the
test and example code in dedicated sub-directories.

DHParser uses `packrat parsing <https://bford.info/packrat/>` with full left-recursion support
which allows to build parsers for any context-free-grammar. It's got a post-mortem debugger
to analyse the parsing process and it offers facilities for unit-testing grammars and some
support for fail-tolerant parsing so that the parser does not stop at the first syntax error
it encounters. Finally, there is some support for writing language servers for DSLs
in Python that adhere to editor-independent the
`languag server-protocol <https://microsoft.github.io/language-server-protocol/>`.


Writing a parser quickly
------------------------

In case you just need a parser for some very simple DSL, you can directly add a string
the EBNF-grammar of that DSL to you python code and compile if into an executable parser
much like you'd compile a regular expresseion. Let's do this for a
`JSON <https://www.json.org/json-en.html>`-parser::

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

        INT         = [NEG] ( /[1-9][0-9]+/ | /[0-9]/ )
        NEG         = `-`
        FRAC        = DOT /[0-9]+/
        DOT         = `.`
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
        print(syntax_tree.serialize(how='indented'))

Mind that this little script does not yield the json data in form of a
nested tree of python dictionaries and arrays but only the syntax tree
of the string encoding that data::

    $ python parse_json.py
    json
      json_object
        member
          string
            :Text '"'
            PLAIN "one"
            :Text '"'
          number
            INT "1"
        member
          string
            :Text '"'
            PLAIN "two"
            :Text '"'
          number
            INT "2"


In order to retrieve the actual data
from the syntax tree a few more transformations are necessary, but the
example should suffice to show how a parser for a context-free grammar
can be generated right inside a Python-program.

Nodes, the name of which starts with a colon ":" are nodes that have
been produced by an unnamed part of a parser, in this case the parts
that parse the quotation marks within the string-parser. Usually, such
nodes are either renamed or removed during abstract-syntaxtree-transformation.

The three lines starting with an ``@``-sign at the beginning of the
grammar-string are DHParser-directives (see :py:mod:`ebnf`) which
in this case help to the syntax-tree which otherwise would can turn
out to be rather verbose.

Specifying a parser can also be done directly with Python-code
instead of compiling an EBNF-grammar first::

    import sys, re

    from DHParser.parse import Grammar, Forward, Whitespace, Drop, NegativeLookahead, \
        ZeroOrMore, RegExp, Option, TKN, DTKN, Text

    _element = Forward().name('_element', disposable=True)
    _dwsp = Drop(Whitespace(r'\s*'))
    _EOF = NegativeLookahead(RegExp('.'))
    EXP = (Text("E") | Text("e") + Option(Text("+") | Text("-")) + RegExp(r'[0-9]+')).name('EXP')
    DOT = Text(".").name('DOT')
    FRAC = (DOT + RegExp(r'[0-9]+')).name('FRAC')
    NEG = Text("-").name('NEG')
    INT = (Option(NEG) + RegExp(r'[1-9][0-9]+') | RegExp(r'[0-9]')).name('INT')
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

In order to avoid namespace pollution, the variables defining the parser could be encapsulated by
a class definition::

    class JSON:
        _element = Forward().name('_element', disposable=True)
        ...
        json = (_dwsp + _element + _EOF).name('json')

    json_parser = Grammar(JSON.json)
    ...

Usually, it is best to specify the grammar in EBNF, compile it and then copy and paste the
compiled grammar into your script, in case you want to save the startup-time that is wasted
when the grammar is compiled when running the script. This can by done by writing the EBNF
grammar into a text file and then calling the "dhparser"-command with the EBNF-file::

    $ dhparser json.ebnf

This produces a script ``jsonParser.py`` from the EBNF-grammar that can be called with any
text-file that adheres to the EBNF-grammar and outputs it as syntax-tree::

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


Larger scale DSL-projects
-------------------------

Larger and more complex DSL-projects can easily be setup by calling the "dhparser"-script
with a name of a project-directory that will then be created and filled with some templates::

   $ dhparser json
   $ cd json
   $ dir
   example.dsl  json.ebnf	jsonServer.py  README.md  tests_grammar  tst_json_grammar.py

The first step is to replace the ".ebnf"-file that contains a simple demo-grammar with your
own grammar. For the sake of the example we'll write our json-Grammar into this file::

    #  EBNF-Directives

    @literalws  = right  # eat insignificant whitespace to the right of literals
    @whitespace = /\s*/  # regular expression for insignificant whitespace
    @comment    = /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/  # C++ style comments
    @drop       = whitespace, strings  # silently drop bare strings and whitespace
    @disposable = /_\w+/  # regular expression to identify disposable symbols

    #:  compound elememts

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

    INT         = [NEG] ( /[1-9][0-9]+/ | /[0-9]/ )
    NEG         = `-`
    FRAC        = DOT /[0-9]+/
    DOT         = `.`
    EXP         = (`E`|`e`) [`+`|`-`] /[0-9]+/

    _EOF        =  !/./

The division of the grammar into several sections is purely conventional. If
a comment-line starts with ``#:`` this is a hint to the test script
to generate a separate unit-test-template for the following section.

The ``tst_..._grammar.py``-script is the most important tool in any DSL-project.
The script generates or updates the ``...Parser.py``-program if the grammar
has changed and runs the unit tests in the ``tests_grammar`` subdirectory.
After filling in the above grammar in the ``json.ebnf``-file, a parser can
be generated by running the test skript::

    $ python tst_json_grammar.py

If there were no errors, a new ``jsonParser.py`` appears in the directory.
Before we can try it, we need some test-data. Then we can run the script
just like before::

    $ rm example.dsl
    $ echo '{ "one": 1, "two": 2 }' >example.json
    $ jsonParser.py --xml example.json
    <json>
      <object>
      ...

Clutter-free grammars
---------------------

DHParser tries to minimize unnecessary clutter in grammar definitions.
To reach this goal DHParser follows a few, mostly intuitive, conventions:

1. The symbols on the left hand side of any definition (or "rule" or "production"
   if you prefer one of theses terms) in the grammar is considered significant
   by default. The nodes produced by the parsing-expression on the right hand
   side will carry the symbol as a tag-name.

2. Some symbols can explicitly be marked as "disposable" (or "insignificant"),
   however. These may not appear in the syntax-tree and nodes of their type
   type may be replaced by their children, silently. Thus, you'll never see
   an "_elment"-node in a JSON-syntaxtree produced by the above grammar,
   but only object-, array-, string-, number-, true-, false- or null-nodes.

3. Insignificant whitespace is denoted by the single character ``~``.

4. Comments defined by the ``@comment``-directive at the top of the grammar
   are allowed in any place where insignificant ``~``-whitespace is
   allowed. Thus, you never need to worry about where to provide for
   comments in you grammar. It is as easy as it is intuitive.

5. Delimiters like "," or "[", "]" etc. typically appear as literal
   string values in a grammar. Now, since delimiters are typically
   surrounded by insignificant whitespace, DHParser can be advised via
   the ``@literalws`` to automatically eat whitespace to the right hand
   side (or to the left hand side, if you prefer) of any string literal
   in the grammar without mentioning. This immediately removes a lot of
   clutter from most grammars.

   In case you want to grab a string without
   eating its adjacent whitespace, you can still use the "backticked"
   notation for string literals ```backticked string```.

6. DHParser can be advised (vie the ``@drop``-directive) to drop
   tokens in form of (non-backticked) strings from the syntax-tree
   already while parsing. Likewise with insignificant whitespace
   or any disposable symbol. This greatly simplifies syntax-trees
   at a very early stage, already.

   In case you want to keep a particular string token in the tree
   none the less, you can still do so by assigning it to a
   non-disposable symbol, e.g. ``opening_bracket = "("`` and using
   this symbol instead of the string literal in other expressions.

7. Ah, and yes, of course you do not need to end grammar definitions
   with a semicolon ``;`` as demanded by the ISO-norm for EBNF :-)


Declarative Abstract-syntax-tree transformation
-----------------------------------------------



Test-driven grammar development
-------------------------------

Invoking the post-mortem debugger
---------------------------------

Tree compilation with the Visitor-pattern
-----------------------------------------

Fail-tolerant parsing
---------------------

Running the DSL-parser as a server
----------------------------------

Performance considerations
--------------------------

