Introduction to [DHParser](https://gitlab.lrz.de/badw-it/DHParser)
==================================================================

Motto: **Computers enjoy XML, humans don't.**

Why use domain specific languages in the humanities
---------------------------------------------------

Suppose you are a literary scientist and you would like to edit a poem
like Heinrich Heine's "Lyrisches Intermezzo". Usually, the technology of
choice would be XML and you would use an XML-Editor to write
something like this:

    <?xml version="1.0" encoding="UTF-8" ?>
    <gedicht>
        <bibliographisches>
            <autor gnd="118548018">Heinrich Heine</autor>
            <werk href="http://www.deutschestextarchiv.de/book/show/heine_lieder_1827"
                  urn="nbn:de:kobv:b4-200905192211">
                Buch der Lieder
            </werk>
            <ort gnd="4023118-5">Hamburg</ort>
            <jahr>1927</jahr>
            <serie>Lyrisches Intermezzo</serie>
            <titel>IV.</titel>
        </bibliographisches>
        <text>
            <strophe>
                <vers>Wenn ich in deine Augen seh',</vers>
                <vers>so schwindet all' mein Leid und Weh!</vers>
                <vers>Doch wenn ich küsse deinen Mund,</vers>
                <vers>so werd' ich ganz und gar gesund.</vers>
            </strophe>
            <strophe>
                <vers>Wenn ich mich lehn' an deine Brust,</vers>
                <vers>kommt's über mich wie Himmelslust,</vers>
                <vers>doch wenn du sprichst: Ich liebe dich!</vers>
                <vers>so muß ich weinen bitterlich.</vers>
            </strophe>
        </text>
    </gedicht>

Now, while you might think that this all works well enough, there are
a few drawbacks to this approach:

- The syntax is cumbersome and the encoding not very legible to humans
  working with it. (And I did not even use
  [TEI-XML](http://www.tei-c.org/index.xml), yet...)
  Editing and revising XML-encoded text is a pain. Just ask the
  literary scientists who have to work with it.

- The XML encoding, especially TEI-XML, is often not intuitive. Only
  experts understand it. Now, if you had the idea that your humanist
  friend, who is not into digital technologies, might help you with
  proof-reading, you better think about it again.

- There is an awful lot of typing to do: All those lengthy opening
  and closing tags. This takes time...

- While looking for a good XML-Editor, you find that there hardly exist
  any XML-Editors any more. (And for a reason, actually...) In
  particular, there are no good open source XML-Editors.

On the other hand, there are good reasons why XML is used in the
humanities: Important encoding standards like
[TEI-XML](http://www.tei-c.org/index.xml) are defined in XML. Its strict
syntax and the possibility to check data against schema help to detect
and avoiding encoding errors. If the schema is well-defined, it is
unambiguous, and it is easy to parse for a computer. Most of these
advantages, however, are on a technical level and few of them are
actually exclusive advantages of XML.

All in all this means, that while XML is a solid back-end-technology, it
still is a pain to work with XML as a frontend-technology. This is where
DHParser comes in. It allows you to define your own domain specific
notation that is specifically tailored to your editing needs and
provides an infrastructure that - if you know a little
Python-programming - makes it very easy to convert your annotated text
into an XML-encoding of your choice. With DHParser, the same poem above
can be simply encoded like this:

    Heinrich Heine <gnd:118548018>,
    Buch der Lieder <urn:nbn:de:kobv:b4-200905192211>,
    Hamburg <gnd:4023118-5>, 1927.

        Lyrisches Intermezzo

                 IV.

    Wenn ich in deine Augen seh',
    so schwindet all' mein Leid und Weh!
    Doch wenn ich küsse deinen Mund,
    so werd' ich ganz und gar gesund.

    Wenn ich mich lehn' an deine Brust,
    kommt's über mich wie Himmelslust,
    doch wenn du sprichst: Ich liebe dich!
    so muß ich weinen bitterlich.

Yes, that's right. It is as simple as that. Observe, how much more
efficacious a verse like "Wenn ich mich lehn' an deine Brust, / kommt's
über mich wie Himmelslust," can be if it is not cluttered with XML tags
;-)

You might now wonder whether the second version really does encode the
same information as the XML version. How, for example, would the
computer know for sure where a verse starts and ends or a stanza or what
is title and what stanza? Well, for all these matters there exist
conventions that poets have been using for several thousand years. For
example, a verse always starts and ends on the same line. There is
always a gap between stanzas. And the title is always written above the
poem and not in the middle of it. So, if there is a title at all, we can
be sure that what is written in the first line is the title and not a
stanza.

DHParser is able to exploit all those hints in order to gather much the
same information as was encoded in the XML-Version. Don't believe it?
You can try: Download DHParser from the
[gitlab-repository](https://gitlab.lrz.de/badw-it/DHParser) and enter
the directory `examples/Tutorial` on the command line interface (shell).
Just run `python LyrikCompiler_example.py` (you need to have installed
[Python](https://www.python.org/) Version 3.4 or higher on your
computer). The output will be something like this:

    <gedicht>
        <bibliographisches>
            <autor>
                <namenfolge>Heinrich Heine</namenfolge>
                <verknüpfung>gnd:118548018</verknüpfung>
            </autor>
            <werk>
                <wortfolge>Buch der Lieder</wortfolge>
                <verknüpfung>urn:nbn:de:kobv:b4-200905192211</verknüpfung>
            </werk>
            <ort>
                <wortfolge>Hamburg</wortfolge>
                <verknüpfung>gnd:4023118-5</verknüpfung>
            </ort>
            <jahr>1927</jahr>
        </bibliographisches>
        <serie>Lyrisches Intermezzo</serie>
        <titel>IV.</titel>
        <text>
            <strophe>
                <vers>Wenn ich in deine Augen seh',</vers>
                <vers>so schwindet all' mein Leid und Weh!</vers>
                <vers>Doch wenn ich küsse deinen Mund,</vers>
                <vers>so werd' ich ganz und gar gesund.</vers>
            </strophe>
            <strophe>
                <vers>Wenn ich mich lehn' an deine Brust,</vers>
                <vers>kommt's über mich wie Himmelslust,</vers>
                <vers>doch wenn du sprichst: Ich liebe dich!</vers>
                <vers>so muß ich weinen bitterlich.</vers>
            </strophe>
        </text>
    </gedicht>

Now, you might notice that this is not exactly the XML-encoding as shown
above. (Can you spot the differences?) But you will probably believe me
without further proof that it can easily be converted into the other
version and contains all the information that the other version
contains.

How does DHParser achieve this? Well, there is the rub. In order to
convert the poem in the domain specific version into the XML-version,
DHParser requires a structural description of the domain specific
encoding. This is a bit similar to a document type definition (DTD) in
XML. This structural description uses a slightly enhanced version of the
[Extended-Backus-Naur-Form
(EBNF)](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form),
which is a well-established formalism for the structural description of
formal languages in computer sciences. An excerpt of the EBNF-definition
of our domain-specific encoding for the poem looks like this. (We leave
out the meta-data here. See
[`examples/Tutorial/Lyrik.ebnf`](https://gitlab.lrz.de/badw-it/DHParser/blob/master/examples/Tutorial/Lyrik.ebnf)
for the full EBNF):

    gedicht           = { LEERZEILE }+ [serie] §titel §text /\s*/ §ENDE
    serie             = !(titel vers NZ vers) { NZ zeile }+ { LEERZEILE }+
    titel             = { NZ zeile}+ { LEERZEILE }+
    zeile             = { ZEICHENFOLGE }+

    text              = { strophe {LEERZEILE} }+
    strophe           = { NZ vers }+
    vers              = { ZEICHENFOLGE }+

    ZEICHENFOLGE      = /[^ \n<>]+/~
    NZ                = /\n/~
    LEERZEILE         = /\n[ \t]*(?=\n)/~
    ENDE              = !/./

Without going into too much detail here, let me just explain a few
basics of this formal description: The slashes `/` enclose ordinary
regular expressions. Thus, `NZ` for ("Neue Zeile", German for: "new
line") is defined as `/\n/~` which is the newline-token `\n` in a
regular expression, plus further horizontal whitespace (signified by the
tilde `~`), if there is any.

The braces `{` `}` enclose items that can be repeated zero or more
times; with a `+` appended to the closing brace it means one or more
times. Now, look at the definition of `text` in the 6th line: `{ strophe
{LEERZEILE} }+`. This reads as follows: The text of the poem consists of
a sequence of stanzas, each of which is followed by a sequence of empty
lines (German: "Leerzeilen"). If you now look at the structural
definition of a stanza, you find that it consists of a sequence of
verses, each of which starts, i.e. is preceded by a new line.

Can you figure out the rest? Hint: The angular brackets `[` and `]` mean
that and item is optional and the `§` sign means that it is obligatory.
(Strictly speaking, the §-signs are not necessary, because an item that
is not optional is always obligatory, but the §-signs help the converter
to produce more useful error messages.)

This should be enough for an introduction to the purpose of DSLs in the
humanities. It has shown the probably most important use case of
DHParser, i.e. as a frontend-technology form XML-encodings. Of course,
it can just as well be used as a frontend for any other kind of
structured data, like SQL or graph-structured data. The latter is by the
way is a very reasonable alternative to XML for edition projects with a
complex transmission history. See Andreas Kuczera's Blog-entry on
["Graphdatenbanken für
Historiker"](http://mittelalter.hypotheses.org/5995).

Tutorial: First Steps with DHParser
-----------------------------------

*You'll need to be able to use a shell and have some basic knowledge of
Python programming to be able to follow this section!* Also, you need to
have [git](https://git-scm.com/) and [python 3](https://www.python.org/)
installed on you system. It is important that you have at least python
version 3.5. DHParser will not work with python 2. You can simply start
python to find out which version you have got.

In order to try the example above, you should fetch DHParsers from its
git-repository. Open a shell and type:

    $ git clone git@gitlab.lrz.de:badw-it/DHParser.git

Now, if you enter the repo, you'll find among others these subdirectories:

    DHParser
    documentation
    examples
    test

The directory `DHParser` contains the Python modules of the
DHParser-package, `test` - as you can guess - contains the unit-tests
for DHParser. Now, enter the `examples/Tutorial`-directory. Presently,
most other examples are pretty rudimentary. So, don't worry about them.

In this directory, you'll find a simple EBNF Grammar for poetry in the
file `Lyrik.ebnf`. Have a look at it. You'll find that is the same
grammar (plus a few additions) that has been mentioned just before.
You'll also find a little script `recompile_grammar.py` that is used to
compile an EBNF-Grammar into an executable Python-module that can be
used to parse any piece of text that this grammar is meant for; in this
case poetry.

Any DHParser-Project needs such a script. The content of the script is
pretty self-explanatory:

    from DHParser.testing import recompile_grammar
    if not recompile_grammar('.', force=True):
        with open('Lyrik_ebnf_ERRORS.txt') as f:
            print(f.read())
        sys.exit(1)

The script simply (re-)compiles any EBNF grammar that it finds in the
current directory. "Recompiling" means that DHParser notices if a
grammar has already been compiled and overwrites only that part of the
generated file that contains the actual parser. All other parts - we
will come to that later what these are - can safely be edited by you.
Now just run `recompile_grammar.py` from the command line:

    $ python recompile_grammar.py

You'll find that `recompile_grammar.py` has generated a new script with
the name `LyrikCompiler.py`. This script contains the Parser for the
`Lyrik.ebnf`-grammar and some skeleton-code for a DSL->XML-Compiler (or
rather, a DSL-whatever compiler), which you can later fill in. Now let's
see how this script works:

    $ python LyrikCompiler.py Lyrisches_Intermezzo_IV.txt >result.xml

The file `Lyrisches_Intermezzo_IV.txt` contains the fourth part of
Heinrich Heine's Lyrisches Intermezzo encoded in our own human-readable
poetry-DSL that has been shown above. Since we have redirected the
output to `result.xml`, you'll find a new file with this name in the
directory. If you look at it with an editor - preferably one that
provides syntax-highlighting for XML-files, you'll find that it look's
pretty much like XML. However, this XML-code still looks much more
obfuscated than in the Introduction before. If you look closely, you can
nonetheless see that the poem itself has faithfully been preserved. For
example, if you scroll down a few lines, you'll find the (hardly
recognizable!) first verse of the poem:

    ...
    <vers>
        <ZEICHENFOLGE>
            <:RegExp>Wenn</:RegExp>
            <:Whitespace> </:Whitespace>
        </ZEICHENFOLGE>
        <ZEICHENFOLGE>
            <:RegExp>ich</:RegExp>
            <:Whitespace> </:Whitespace>
        </ZEICHENFOLGE>
        <ZEICHENFOLGE>
            <:RegExp>in</:RegExp>
            <:Whitespace> </:Whitespace>
        </ZEICHENFOLGE>
        <ZEICHENFOLGE>
            <:RegExp>deine</:RegExp>
            <:Whitespace> </:Whitespace>
        </ZEICHENFOLGE>
        <ZEICHENFOLGE>
            <:RegExp>Augen</:RegExp>
            <:Whitespace> </:Whitespace>
        </ZEICHENFOLGE>
        <ZEICHENFOLGE>
            <:RegExp>seh',</:RegExp>
        </ZEICHENFOLGE>
    </vers>
    ...

How come it is so obfuscated, and where do all those pseudo-tags like
`<:RegExp>` and `<:Whitespace>` come from? Well, this is probably the
right time to explain a bit about parsing and compilation in general.
Parsing and compilation of a text with DHParser takes place in three
strictly separated steps:

1. Parsing of the text and generation of the "concrete syntax tree"
   (CST)

2. Transformation of the CST into an "abstract syntax tree" (AST)

3. And, finally, compilation of the AST into valid XML, HTML, LaTeX or
   what you like.

DHParser automatically only generates a parser for the very first step.
The other steps have to be programmed by hand, though DHParser tries to
make those parts as easy as possible. What you have just seen in your
editor is a Pseudo-XML-representation of the concrete syntax tree. (The
output of a parser is always a tree structure, just like XML.) It is
called concrete syntax tree, because it contains all the syntactic
details that have been described in the `Lyrik.ebnf`-grammar; and the
grammar needs to describe all those details, because otherwise it would
not be possible to parse the text. On the other hand most of these
details do not carry any important information. This is the reason why
in the second step the transformation into an abstract syntax tree that
leaves out the unimportant details. There is now general rule of how to
derive abstract syntax trees from concrete syntax trees, and there
cannot be, because it depends on the particular domain of application
which details are important and which not. For poems these might be
different from, say, for a catalogue entry. Therefore, the
AST-transformation has to be specified for each grammar separately, just
as the grammar has to be specified for each application domain.

Before I'll explain how to specify an AST-transformation for DHParser,
you may want to know what difference it makes. There is a script
`LyrikCompiler_example.py` in the directory where the
AST-transformations are already included. Running the script

    $ python LyrikCompiler_example.py Lyrisches_Intermezzo_IV.txt

yields the fairly clean Pseudo-XML-representation of the DSL-encoded
poem that we have seen above. Just as a teaser, you might want to look
up, how the AST-transformation is specified with DHParser. For this
purpose, you can have a look in file `LyrikCompiler_example.py`. If you
scroll down to the AST section, you'll see something like this:

    Lyrik_AST_transformation_table = {
        # AST Transformations for the Lyrik-grammar
        "+": remove_empty,
        "bibliographisches": [remove_nodes('NZ'), remove_tokens],
        "autor, werk, untertitel, ort": [],
        "jahr": [content_from_sinlge_child],
        "wortfolge": [flatten(is_one_of('WORT'), recursive=False), remove_last(is_whitespace), collapse],
        "namenfolge": [flatten(is_one_of('NAME'), recursive=False), remove_last(is_whitespace), collapse],
        "verknüpfung": [remove_tokens('<', '>'), content_from_sinlge_child],
        "ziel": content_from_sinlge_child,
        "gedicht, strophe, text": [flatten, remove_nodes('LEERZEILE'), remove_nodes('NZ')],
        "titel, serie": [flatten, remove_nodes('LEERZEILE'), remove_nodes('NZ'), collapse],
        "vers": collapse,
        "zeile": [],
        "ZEICHENFOLGE, NZ, JAHRESZAHL": content_from_sinlge_child,
        "WORT, NAME, LEERZEILE, ENDE": [],
        ":Whitespace": replace_content(lambda node : " "),
        ":Token, :RE": content_from_sinlge_child,
        "*": replace_by_single_child
    }

As you can see, AST-transformations a specified declaratively (with the
option to add your own Python-programmed transformation rules). This
keeps the specification of the AST-transformation simple and concise. At
the same, we avoid adding hints for the AST-transformation in the
grammar specification, which would render the grammar less readable.

Now that you have seen how DHParser basically works, it is time to go
through the process of desining and testing a domain specific notation
step by step from the very start. Head over to the documentation in
subdirectory and read the step by step guide.