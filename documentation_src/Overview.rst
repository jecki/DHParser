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
of the string encoding that data. In order to retrieve the actual data
from the sytnax tree a few more transformations are necessary, but the
example should suffice to show how a parser for a context-free grammar
can be generated right inside a Python-program.

The three lines starting with an ``@``-sign at the beginning of the
grammar-string are DHParser-directives (see :py:mod:`ebnf`) which
in this case help to the syntax-tree which otherwise would can turn
out to be rather verbose.

If you want to specify the parser a Python-script, this can also be
done directly with Python-code instead of compiling an EBNF-grammar
first. For simple DSLs this might even be the preferred way, because
compiling an EBNF-grammar to Python code within a script increases
its startup-time considerably::

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

