DHParser
========

![](https://img.shields.io/pypi/v/DHParser) 
![](https://img.shields.io/pypi/status/DHParser)
![](https://img.shields.io/pypi/l/DHParser)
![](https://img.shields.io/pypi/pyversions/DHParser)

DHParser - Rapid prototyping of formal grammars and 
domain specific languages (DSL) in the Digital Humanities.
See https://dhparser.readthedocs.io/en/latest/

This software is open source software under the Apache 2.0-License (see section License, below).

Copyright 2016-2025  Eckhart Arnold, Bavarian Academy of Sciences and Humanities


Purpose
-------

DHParser is a parser development-framwork that has been developed 
with three main purposes in mind:

1. Developing *parsers for domain specific languages* and notations, either existing
   notations, like, LaTeX, or newly created DSLs, like the
   [Medieval-Latin-Dictionary-DSL](https://gitlab.lrz.de/badw-it/mlw-dsl-oeffentlich).
   Typically, these languages are strict formal languages the grammar of
   which can be described with context-free grammars. (In cases where
   this does not hold like TeX, it is often still possible to describe a 
   reasonably large subset of the formal language with a context free grammar.) 

2. Developing *parsers for semi-structured or informally structured
   text-data*.    
   This kind of data is typically what you get when retro-digitizing
   textual data like printed bibliographies, or reference works or
   dictionaries. Often such works can be captured with a formal 
   grammar, but these grammars require a lot of iterations and tests
   to develop and usually become much more ramified than the grammars
   of well-designed formal languages. Thus, DHParser's elaborated
   testing and debugging-framework for grammars.

   (See Florian Zacherl's [Dissertation on the retro-digitalization of dictionary data](https://www.kit.gwi.uni-muenchen.de/?band=82908&v=1)
   for an interesting case study. I am confident that the development of
   a suitable formal grammar is much easier with an elaborated framework
   like DHParser than with the PHP-parsing-expression-grammar-kit that
   Florian Zacherl has used.)

3. Developing *processing pipelines for tree-structured data*.
   In typical digital-humanities-applications one wants to produce
   different forms of output (say, printed, online-human-readable,
   online-machine-readable) from one and the same source of data.
   Therefore, the parsing stage (if the data source is structured
   text-data) will be followed by more or less intricate bifurcated
   processing pipelines.
   

Features
--------

* Memoizing packrat-parser based on Parsing Expression Grammars. This
  means: 
  
    - Linear parsing time

    - Any EBNF-grammar supported, including left-recursive grammars 
      (via "seed and grow"-algorithm)

    - Unlimited look ahead and look behind

* [Macros](
  https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#macros)
  to avoid code-repetition within grammars

* [Declarative tree-transformations](
  https://dhparser.readthedocs.io/en/latest/manuals/03_AST-transformation.html#declarative-tree-transformation)
  for post-processing syntax-trees

* Unit testing framework and post-mortem-debuger for [test-driven grammar
  development](
  https://dhparser.readthedocs.io/en/latest/Overview.html#test-driven-grammar-development)
  and rapid-prototyping of grammars

* [Customizable error reporting](
  https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#error-catching),
  [recovery after syntax errors](
  https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#skip-and-resume) 
  and support for [fail-tolerant parsers](
  https://dhparser.readthedocs.io/en/latest/manuals/01_EBNF-grammars.html#fail-tolerant-parsing)

* Support for [Language-servers](https://microsoft.github.io/language-server-protocol/)

* Workflow-support and [data-processing-pipelines](
  https://dhparser.readthedocs.io/en/latest/manuals/04_postprocessing.html#processing-pipelines)

* XML-support like [mapping flat-text to the DOM-tree](
  https://dhparser.readthedocs.io/en/latest/manuals/02_document-trees.html#content-mappings)
  ("node-tree" in DHParser's terminology) and 
  [adding markup in arbitrary places](
  https://dhparser.readthedocs.io/en/latest/manuals/02_document-trees.html#markup-insertion),
  even if this requires splitting tags.

* Full Unicode support

* No dependencies except the Python Standard Library

* [Extensive documentation](https://dhparser.readthedocs.io) and examples


Ease of use
-----------

**Directly compile existing EBNF-grammars:**

DHParser recognizes various dialects of EBNF or PEG-syntax for specifying
grammars. For any already given grammar-specification in EBNF or PEG, 
it is not unlikely that DHParser can generate a parser either right away or 
with only minor changes or additions.

You can try this by compiling the file `XML_W3C_SPEC.ebnf` in the `examples/XML`
of the source-tree which contains the official XML-grammar directly extracted
from [www.w3.org/TR/xml/](https://www.w3.org/TR/xml/):

    $ dhparser examples/XML/XML_W3C_SPEC.ebnf

This command produces a Python-Script `XML_W3C_SPECParser.py` in the same
directory as the EBNF-file. This file can be run on any XML-file and will
yield its concrete syntax tree, e.g.:

    $ python examples/XML/XML_W3C_SPECParser.py examples/XML/example.xml

Note, that the concrete syntax tree of an XML file as returned by the generated
parser is not the same as the data-tree encoded by that very XML-file. In 
order to receive the data tree, further transformations are necessary. See
`examples/XML/XMLParser.py` for an example of how this can be done.

**Use (small) grammars on the fly in Python code:**

Small grammars can also directly be compiled from Python-code. (Here, we
use DHParser's preferred syntax which does not require trailing semicolons
and uses the tilde `~` as a special sign to denote "insignificant" whitespace.)

key_value_store.py:

    #!/usr/bin/env python 
    # A mini-DSL for a key value store
    from DHParser.dsl import create_parser

    # specify the grammar of your DSL in EBNF-notation
    grammar = '''@ drop = whitespace, strings
    key_store   = ~ { entry }
    entry       = key "="~ value          # ~ means: insignificant whitespace 
    key         = /\w+/~                  # Scanner-less parsing: Use regular
    value       = /\"[^"\n]*\"/~          # expressions wherever you like'''

    # generating a parser is almost as simple as compiling a regular expression
    parser = create_parser(grammar)       # parser factory for thread-safety

Now, parse some text and extract the data from the Python-shell:

    >>> from key_value_store import parser
    >>> text = '''
            title    = "Odysee 2001"
            director = "Stanley Kubrick"
        '''
    >>> data = parser(text)
    >>> for entry in data.select('entry'):
            print(entry['key'], entry['value'])

    title "Odysee 2001"
    director "Stanley Kubrick"

Or, serialize as XML:

    >>> print(data.as_xml())

    <key_store>
      <entry>
        <key>title</key>
        <value>"Odysee 2001"</value>
      </entry>
      <entry>
        <key>director</key>
        <value>"Stanley Kubrick"</value>
      </entry>
    </key_store>

**Set up DSL-projects with unit-tests:** 

For larger DSL projects that require testing and incremental 
grammar development, use:
  
  $ dhparser NEW_PROJECT_NAME 

to set up a project-directory with all the scaffolding that a 
serious DSL-project needs, including the full unit-testing-framework.

Installation
------------

You can install DHParser from the Python package index [pypi.org](https://pypi.org):

    python -m pip install --user DHParser

Alternatively, you can clone the latest version from 
[gitlab.lrz.de/badw-it/DHParser](https://gitlab.lrz.de/badw-it/DHParser)

And these are the steps, if you want set up a DHParser-Project with the latest 
DHParser-development version:

    $ git clone --depth=1 --branch development https://gitlab.lrz.de/badw-it/DHParser
    $ python3 DHParser/DHParser/scripts/dhparser.py MyNewParserProject
    $ ln -s ../DHParser/DHParser MyNewParserProject/DHParser
    $ cd MyNewParserProject


Getting Started
---------------

See [Introduction.md](https://gitlab.lrz.de/badw-it/DHParser/blob/master/Introduction.md) for the
motivation and an overview how DHParser works or jump right into the
[Step by Step Guide](https://gitlab.lrz.de/badw-it/DHParser/blob/master/documentation_src/StepByStepGuide.rst) to
learn how to set up and use DHParser.
Or have a look at the 
[comprehensive overview of DHParser's features](https://gitlab.lrz.de/badw-it/DHParser/-/blob/master/documentation_src/Overview.rst) 
to see how DHParser supports the construction of domain specific languages.

Documentation
-------------

For the full documentation see: [dhparser.readthedocs.io](https://dhparser.readthedocs.io/en/latest/)

License
-------

DHParser is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).

Copyright 2016-2022  Eckhart Arnold, Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Third-Party-Software
--------------------

DHParser includes the following third-party-software:

* [typing_extensions](https://pypi.org/project/typing-extensions/): 
  needed for backwards compatibility with older Python versions.
  Licensed under the 
  [Python Software Foundation License](https://docs.python.org/3/license.html#psf-license)

* shadow_cython: a single module from [Cython](https://cython.org/) to
  avoid error-messages resulting from the use of the cython-decorators 
  when cython is not installed on the system using DHParser.
  License: [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

The following are only needed for building the documentation:

* [Sphinx book theme](https://sphinx-book-theme.readthedocs.io): Makes
  the documentation look better than the built-in 
  [sphinx](https://www.sphinx-doc.org)-themes. License: 
  [BSD 3-clause license](https://github.com/executablebooks/sphinx-book-theme/blob/master/LICENSE)

* [pydata sphinx theme](https://github.com/pydata/pydata-sphinx-theme): Nedded
  by sphinx_book_theme, also licensed under the BSD 3-clause license. 

* [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/): Needed by
  by pydata_sphinx_theme, licensed unter the [MIT-License](https://mit-license.org/) 

* [soupsive](https://github.com/facelessuser/soupsieve): Needed by Beautifulsoup,
  licensed unter the [MIT-License](https://github.com/facelessuser/soupsieve/blob/main/LICENSE.md)

Optional Post-Installation
--------------------------

It is recommended that you install the `regex`-module
(https://bitbucket.org/mrabarnett/mrab-regex). If present, DHParser
will use `regex` instead of the built-in `re`-module for regular
expressions. `regex` is faster and more powerful than `re`.

In order to speed up DHParser even more, it can be compiled with
the Python to C compiler [Cython](https://cython.org). Cython
version 3.0 or higher is required to compile DHParser. Type:

    pip install cython
 
on the command-line to install cython. Once cython has been 
built and installed, you can run the "dhparser_cythonize"-script 
from the command line:

    dhparser_cythonize

On Linux-systems, in case you want to use clang instead of the
gcc-compiler, type:

    export CC=/usr/bin/clang; dhparser_cythonize 

Using clang may also help to circumvent C-errors like 
"incompatible pointer types".

The Cython-compiled version is about 2-3 times faster than the 
CPython-interpreted version. Compiling can take quite a while. 
If you are in a hurry, you can just can also just call
`dhparser_cythonize_stringview` which just compiles the 
stringview-module, which profits the most from being "cythonized".

Depending on the use case, e.g. when parsing large files, 
[PyPy3](https://www.pypy.org/) yields even greater speed-ups. 
However, in other cases pypy can also be noticeably slower than cpython!
To circumvent the longer startup times of pypy3 in comparison to CPython, 
it is recommended to use the xxxServer.py-scripts rather than calling 
the xxxParser.py-script each time when parsing many documents subsequently.

Another way to speed up your parser is by adding "@ optimizations = all"
at the beginning of your EBNF-grammar-file. DHParser then tries to 
compile (some) non-recursive parts of your grammar to entirely to regular 
rexpressions which yields a 10-20% speedup. Beware that this option
is still experimental!


Sources
-------

Find the sources on [gitlab.lrz.de/badw-it/DHParser](https://gitlab.lrz.de/badw-it/DHParser) .
Get them with:

    git clone https://gitlab.lrz.de/badw-it/DHParser

There exists a mirror of this repository on Github:
https://github.com/jecki/DHParser Be aware, though, that the github-mirror
may occasionally lag behind a few commits.


Packaging
---------

DHParser uses [Poetry](https://python-poetry.org/) for packaging and
dependency-management. In order to build a package from the sources,
type:

    poetry build

on the command line. The packages will then appear in the "dist" subdirectory.


Author
------

Author: Eckhart Arnold, Bavarian Academy of Sciences
Email:  arnold@badw.de

How to cite
-----------

If you use DHParser for Scientific Work, then please cite it as:

DHParser. A Parser-Generator for Digital-Humanities-Applications,  
Division for Digital Humanities Research & Development, Bavarian Academy of Science and Technology, 
Munich Germany 2017-2025, https://gitlab.lrz.de/badw-it/dhparser

References and Acknowledgement
------------------------------

Eckhart Arnold: Domänenspezifische Notationen. Eine (noch)
unterschätzte Technologie in den Digitalen Geisteswissenschaften,
Präsentation auf dem
[dhmuc-Workshop: Digitale Editionen und Auszeichnungssprachen](https://dhmuc.hypotheses.org/workshop-digitale-editionen-und-auszeichnungssprachen),
München 2016. Short-URL: [tiny.badw.de/2JVT][Arnold_2016]

[Arnold_2016]: https://dhmuc.hypotheses.org/files/2016/12/EA_Pr%C3%A4sentation_Auszeichnungssprachen.pdf

Brian Ford: Parsing Expression Grammars: A Recognition-Based Syntactic
Foundation, Cambridge
Massachusetts, 2004. Short-URL:[t1p.de/jihs][Ford_2004]

[Ford_2004]: https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf

[Ford_20XX]: https://bford.info/packrat/

Richard A. Frost, Rahmatullah Hafiz and Paul Callaghan: Parser
Combinators for Ambiguous Left-Recursive Grammars, in: P. Hudak and
D.S. Warren (Eds.): PADL 2008, LNCS 4902, pp. 167–181, Springer-Verlag
Berlin Heidelberg 2008.

Elizabeth Scott and Adrian Johnstone, GLL Parsing,
in: Electronic Notes in Theoretical Computer Science 253 (2010) 177–189,
[dotat.at/tmp/gll.pdf][scott_johnstone_2010]

[scott_johnstone_2010]: https://dotat.at/tmp/gll.pdf

Dominikus Herzberg: Objekt-orientierte Parser-Kombinatoren in Python,
Blog-Post, September, 18th 2008 on denkspuren. gedanken, ideen,
anregungen und links rund um informatik-themen, short-URL:
[t1p.de/bm3k][Herzberg_2008a]

[Herzberg_2008a]: https://denkspuren.blogspot.de/2008/09/objekt-orientierte-parser-kombinatoren.html

Dominikus Herzberg: Eine einfache Grammatik für LaTeX, Blog-Post,
September, 18th 2008 on denkspuren. gedanken, ideen, anregungen und
links rund um informatik-themen, short-URL:
[t1p.de/7jzh][Herzberg_2008b]

[Herzberg_2008b]: https://denkspuren.blogspot.de/2008/09/eine-einfache-grammatik-fr-latex.html

Dominikus Herzberg: Uniform Syntax, Blog-Post, February, 27th 2007 on
denkspuren. gedanken, ideen, anregungen und links rund um
informatik-themen, short-URL: [t1p.de/s0zk][Herzberg_2007]

[Herzberg_2007]: https://denkspuren.blogspot.de/2007/02/uniform-syntax.html

[ISO_IEC_14977]: https://www.cl.cam.ac.uk/~mgk25/iso-14977.pdf

John MacFarlane, David Greenspan, Vicent Marti, Neil Williams,
Benjamin Dumke-von der Ehe, Jeff Atwood: CommonMark. A strongly
defined, highly compatible specification of
Markdown, 2017. [commonmark.org][MacFarlane_et_al_2017]

[MacFarlane_et_al_2017]: https://commonmark.org/

Stefan Müller: DSLs in den digitalen Geisteswissenschaften,
Präsentation auf dem
[dhmuc-Workshop: Digitale Editionen und Auszeichnungssprachen](https://dhmuc.hypotheses.org/workshop-digitale-editionen-und-auszeichnungssprachen),
München 2016. Short-URL: [tiny.badw.de/2JVy][Müller_2016]

[Müller_2016]: https://dhmuc.hypotheses.org/files/2016/12/Mueller_Anzeichnung_10_Vortrag_M%C3%BCnchen.pdf

Markus Voelter, Sbastian Benz, Christian Dietrich, Birgit Engelmann,
Mats Helander, Lennart Kats, Eelco Visser, Guido Wachsmuth:
DSL Engineering. Designing, Implementing and Using Domain-Specific Languages, 2013.
[dslbook.org/][voelter_2013]

Christopher Seaton: A Programming Language Where the Syntax and Semantics
are Mutuable at Runtime, University of Bristol 2007,
[chrisseaton.com/katahdin/katahdin.pdf][seaton_2007]

Vegard Øye: General Parser Combinators in Racket, 2012,
[epsil.github.io/gll/][vegard_2012]

[vegard_2012]: https://epsil.github.io/gll/

[seaton_2007]: https://chrisseaton.com/katahdin/katahdin.pdf

[voelter_2013]: http://dslbook.org/

[tex_stackexchange_no_bnf]: https://tex.stackexchange.com/questions/4201/is-there-a-bnf-grammar-of-the-tex-language

[tex_stackexchange_latex_parsers]: http://tex.stackexchange.com/questions/4223/what-parsers-for-latex-mathematics-exist-outside-of-the-tex-engines

[XText_website]: https://www.eclipse.org/Xtext/

and many more...
