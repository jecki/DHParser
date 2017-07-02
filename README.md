
DHParser
========

A parser-combinator-based parsing and compiling infrastructure for domain
specific languages (DSL) in Digital Humanities projects.

Author: Eckhart Arnold, Bavarian Academy of Sciences
Email:  arnold@badw.de


License
-------

DHParser is open source software under the [MIT License](https://opensource.org/licenses/MIT)

**Exception**: The module ``DHParser/typing34.py`` was directly taken from the
Python 3.5 source code in order for DHParser to be backwards compatible
with Python 3.4. The module ``DHParser/typing34.py`` is licensed under the
[Python Software Foundation License Version 2](https://docs.python.org/3.5/license.html)


Sources
-------

Find the sources on [gitlab.lrz.de/badw-it/DHParser](https://gitlab.lrz.de/badw-it/DHParser) . 
Get them with:
    
    git clone https://gitlab.lrz.de/badw-it/DHParser


Purpose
-------

DHParser leverages the power of Domain specific languages for the 
Digital Humanities.

Domain specific languages are widespread in 
computer sciences, but seem to be underused in the Digital Humanities.
While DSLs are sometimes introduced to Digital-Humanities-projects as
[practical adhoc-solution][Müller_2016], these solutions are often
somewhat "quick and dirty". In other words they are more of a hack
than a technology. The purpose of DHParser is to introduce
[DSLs as a technology][Arnold_2016] to the Digital Humanities. It is
based on the well known technology of [EBNF][ISO_IEC_14977]-based
parser generators, but employs the more modern form called
"[parsing expression grammar][Ford_2004]" and
[parser combinators][Ford_20XX] as a variant of the classical
recursive descent parser.

Why another parser generator? There are plenty of good parser
generators out there, e.g. [Añez's grako parser generator][Añez_2017], 
[Eclipse XText][XText_Website]. However, DHParser is
intended as a tool that is specifically geared towards digital
humanities applications, while most existing parser generators come
from compiler construction toolkits for programming languages. 
While I expect DSLs in computer science and DSLs in the Digital 
Humanities to be quite similar as far as the technological realization
is concerned, the use cases, requirements and challenges are somewhat 
different. For example, in the humanities annotating text is a central 
use case, which is mostly absent in computer science treatments. 
These differences might sooner or later require to develop the 
DSL-construction toolkits in a different direction. Also,
DHParser shall (in the future) serve as a teaching tool, which
influences some of its design decisions such as, for example, clearly
separating the parsing, syntax-tree-transformation and compilation
stages. Finally, DHParser is intended as a tool to experiment with.  One
possible research area is, how non
[context-free grammars](https://en.wikipedia.org/wiki/Context-free_grammar)
such as the grammars of [TeX][tex_stackexchange_no_bnf] or
[CommonMark][MacFarlane_et_al_2017] can be described with declarative
langauges in the spirit of but beyond EBNF, and what extensions of the
parsing technology are necessary to capture such languages.

Primary use case at the Bavarian Academy of Sciences and Humanities
(for the time being): A DSL for the
"[Mittellateinische Wörterbuch](http://www.mlw.badw.de/)"!

Further (intended) use cases are:

* LaTeX -> XML/HTML conversion. See this
  [discussion on why an EBNF-parser for the complete TeX/LaTeX-grammar][tex_stackexchange_no_bnf]
  is not possible.
* [CommonMark][MacFarlane_et_al_2017] and other DSLs for cross media
  publishing of scientific literature, e.g. journal articles.  (Common
  Mark and Markdown also go beyond what is feasible with pure
  EBNF-based-parsers.)
* EBNF itself. DHParser is already self-hosting ;-)
* Digital and cross-media editions 
* Digital dictionaries

For a simple self-test run `dhparser.py` from the command line. This
compiles the EBNF-Grammer in `examples/EBNF/EBNF.ebnf` and outputs the
Python-based parser class representing that grammar. The concrete and
abstract syntax tree as well as a full and abbreviated log of the
parsing process will be stored in a sub-directory named "LOG".


Introduction
------------

*This is an introduction for absolute beginners.
Full documentation coming soon...*

Motto: *Computers enjoy XML, humans don't.*

Suppose you are a literary scientist and you would like to edit a poem
like Heinrich Heine's "Lyrisches Intermezzo". Usually, the technology 
of choice would be XML and you would use an XML-Editor to write to
code something like this:

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
- The XML encoding, especially TEI-XML, is often unintuitive. Only
  experts understand it. Now, if you had the idea that you humanist
  friend, who is not into digital technologies, might help you with
  proof-reading, you better think about it again.
- There is an awful lot of typing to do: All those lengthy opening 
  and closing tags. This takes time...
- While looking for a good XML-Editor, you find that there hardly exist
  any XML-Editors any more. (And for a reason, actually...) In 
  particular, there are no good open source XML-Editors.

One the other hand, there are good reasons why XML is used in the
humanities: Important encoding standards like TEI-XML are defined in 
XML. It's strict syntax and the possibility to check data against a
schema  help detecting and avoiding encoding errors. If the schema 
is well defined, it is unambiguous, and it is easy to parse for a 
computer. Most of these advantages, however, are on a technical level
and few of them are actually exclusive advantages of XML.

All in all this means, that while XML is a solid backend-technology,
it still is a pain to work with XML as a frontend-technology. This is
where DHParser comes in. It allows you to define your own domain
specific notation that is specifically tailored to your editing needs
and provides an infrastructure that - if you know a little 
Python-programming - makes it very easy to convert your annotated
text into an XML-encoding of your choice. With DHParser, the same poem
above can be simply encoded like this:
 
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

Yes, that's right. It is as simple as that. Observe, how much 
more effacious a verse like "Wenn ich mich lehn' an deine Brust, / 
kommt's über mich wie Himmelslust," can be if it is not uglified by
enclosing XML tags ;-) 

You might now wonder 
whether the second version really does encode the same information
as the XML version. How, for example, would the computer know for 
sure where a verse starts and ends or a stanza or what is 
title and what stanza? Well, for all these matters there exist 
conventions that poets have been using for several thousand years.
For example, a verse always starts and ends in one an the same 
line. There is always a gap between stanzas. And the title is always 
written above the poem and not in the middle of it. So, if there is
a title at all, we can be sure that what is written in the first 
line is the title and not a stanza. 

DHParser is able to exploit all those hints in order to gather much the
same information as was encoded in the XML-Version. Don't believe it?
You can try: Download DHParser from the 
[gitlab-repository](https://gitlab.lrz.de/badw-it/DHParser) and enter
the directory `examples/Tutorial` on the command line interface (shell). 
Just run `python LyrikCompiler_example.py` (you need to have installed
[Python](https://www.python.org/) Version 3.4 or higher on your computer).
The output will be something like this:

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
version and contains all the information that the other version contains.

How does DHParser achieve this? Well, there is the rub. In order to convert
the poem in the domain specific version into the XML-version, DHParser 
requires a structural description of the domain specific encoding. This
is a bit similar to a document type definition (DTD) in XML. This 
structural description uses a slightly enhanced version of the 
[Extended-Backus-Naur-Form (EBNF)](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form) 
that is a well established formalism for the structural description of 
formal languages in computer sciences. And excerpt of the EBNF-definition
of our domain-specific encoding for the poem looks like this. (We leave out
the meta-data here. See 
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

Now, without going into too much detail here, let me just explain a few basics of 
this formal description: The slashes `/` enclose ordinary regular expressions.
Thus, `NZ` for ("Neue Zeile", German for: "new line") is defined as `/\n/~` which
is the newline-token `\n` in a regular expression, plus further horizontal 
whitespace (signified by the tilde `~`), if there is any.

The braces `{` `}` enclose items that can be repeated zero or more times; with
a `+` appended to the closing brace it means one or more times. Now, look at the
definition of `text` in the 6th line: `{ strophe {LEERZEILE} }+`. This reads
as follows: The text of the poem consists of a sequence of stanzas, each of which
is followed by a sequence of empty lines (German: "Leerzeilen"). If you now
look a the structural definition of a stanza, you find that it consists of a 
sequence of verses, each of which starts, i.e. is preceeded by a new line.

Can you figure out the rest? Hint: The angular brackets `[` and `]` mean that and
item is optional and the `§` sign means that it is obligatory. (Strictly speaking, 
the §-signs are not necessary, because an item that is not optional is always
obligatory, but the §-signs help the converter to produce the right error
messages.)


This should be enough for an introduction. It has shown the probably most important
use case of DHParser, i.e. as a frontend-technology form XML-encodings. Of course
it can just as well be used as a frontend for any other kind of structured data,
like SQL or graph-strcutured data. The latter is by the way is a very reasonable
alternative to XML for edition projects with a complex transmission history. 
See Andreas Kuczera's Blog-entry on 
["Graphdatenbanken für Historiker"](http://mittelalter.hypotheses.org/5995).


References
----------

Juancarlo Añez: grako, a PEG parser generator in Python, 2017. URL:
[bitbucket.org/apalala/grako][Añez_2017]

[Añez_2017]: https://bitbucket.org/apalala/grako


Eckhart Arnold: Domänenspezifische Notationen. Eine (noch)
unterschätzte Technologie in den Digitalen Geisteswissenschaften,
Präsentation auf dem
[dhmuc-Workshop: Digitale Editionen und Auszeichnungssprachen](https://dhmuc.hypotheses.org/workshop-digitale-editionen-und-auszeichnungssprachen),
München 2016. Short-URL: [tiny.badw.de/2JVT][Arnold_2016]

[Arnold_2016]: https://f.hypotheses.org/wp-content/blogs.dir/1856/files/2016/12/EA_Pr%C3%A4sentation_Auszeichnungssprachen.pdf


Brian Ford: Parsing Expression Grammars: A Recognition-Based Syntactic
Foundation, Cambridge
Massachusetts, 2004. Short-URL:[http://t1p.de/jihs][Ford_2004]

[Ford_2004]: https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf
  
[Ford_20XX]: http://bford.info/packrat/ 


Richard A. Frost, Rahmatullah Hafiz and Paul Callaghan: Parser
Combinators for Ambiguous Left-Recursive Grammars, in: P. Hudak and
D.S. Warren (Eds.): PADL 2008, LNCS 4902, pp. 167–181, Springer-Verlag
Berlin Heidelberg 2008.


Dominikus Herzberg: Objekt-orientierte Parser-Kombinatoren in Python,
Blog-Post, September, 18th 2008 on denkspuren. gedanken, ideen,
anregungen und links rund um informatik-themen, short-URL:
[http://t1p.de/bm3k][Herzberg_2008a]

[Herzberg_2008a]: http://denkspuren.blogspot.de/2008/09/objekt-orientierte-parser-kombinatoren.html


Dominikus Herzberg: Eine einfache Grammatik für LaTeX, Blog-Post,
September, 18th 2008 on denkspuren. gedanken, ideen, anregungen und
links rund um informatik-themen, short-URL:
[http://t1p.de/7jzh][Herzberg_2008b]

[Herzberg_2008b]: http://denkspuren.blogspot.de/2008/09/eine-einfache-grammatik-fr-latex.html


Dominikus Herzberg: Uniform Syntax, Blog-Post, February, 27th 2007 on
denkspuren. gedanken, ideen, anregungen und links rund um
informatik-themen, short-URL: [http://t1p.de/s0zk][Herzberg_2007]

[Herzberg_2007]: http://denkspuren.blogspot.de/2007/02/uniform-syntax.html


[ISO_IEC_14977]: http://www.cl.cam.ac.uk/~mgk25/iso-14977.pdf


John MacFarlane, David Greenspan, Vicent Marti, Neil Williams,
Benjamin Dumke-von der Ehe, Jeff Atwood: CommonMark. A strongly
defined, highly compatible specification of
Markdown, 2017. [commonmark.org][MacFarlane_et_al_2017]

[MacFarlane_et_al_2017]: http://commonmark.org/


Stefan Müller: DSLs in den digitalen Geisteswissenschaften,
Präsentation auf dem
[dhmuc-Workshop: Digitale Editionen und Auszeichnungssprachen](https://dhmuc.hypotheses.org/workshop-digitale-editionen-und-auszeichnungssprachen),
München 2016. Short-URL: [tiny.badw.de/2JVy][Müller_2016]

[Müller_2016]: https://f.hypotheses.org/wp-content/blogs.dir/1856/files/2016/12/Mueller_Anzeichnung_10_Vortrag_M%C3%BCnchen.pdf

Markus Voelter, Sbastian Benz, Christian Dietrich, Birgit Engelmann, 
Mats Helander, Lennart Kats, Eelco Visser, Guido Wachsmuth: 
DSL Engineering. Designing, Implementing and Using Domain-Specific Languages, 2013.
[http://dslbook.org/][Voelter_2013]  

[voelter_2013]: http://dslbook.org/

[tex_stackexchange_no_bnf]: http://tex.stackexchange.com/questions/4201/is-there-a-bnf-grammar-of-the-tex-language
 
[tex_stackexchange_latex_parsers]: http://tex.stackexchange.com/questions/4223/what-parsers-for-latex-mathematics-exist-outside-of-the-tex-engines 

[XText_website]: https://www.eclipse.org/Xtext/
