DHParser
========

A parser-combinator-based parsing and compiling infrastructure for domain
specific languages (DSL) in Digital Humanities projects.

Author: Eckhart Arnold, Bavarian Academy of Sciences
Email:  arnold@badw.de

License
-------

DHParser is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

Copyright 2016-2017  Eckhart Arnold, Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

**Exception**: The module ``DHParser/foreign_typing.py`` was directly taken from the
Python 3.5 source code in order for DHParser to be backwards compatible
with Python 3.4. The module ``DHParser/foreign_typing.py`` is licensed under the
[Python Software Foundation License Version 2](https://docs.python.org/3.5/license.html)

Sources
-------

Find the sources on [gitlab.lrz.de/badw-it/DHParser](https://gitlab.lrz.de/badw-it/DHParser) .
Get them with:

    git clone https://gitlab.lrz.de/badw-it/DHParser

There exists a mirror of this repository on github:
https://github.com/jecki/DHParser Be aware, though, that the github-mirror
may occasionally lag behind a few commits.

Please contact me, if you are intested in contributing to the
development or just using DHParser.

Disclaimer
----------

DHParser is still in an early development stage. While it is definitaly
usable, features may be dropped or added without notice and class or
function names changed in future versions. The API is NOT YET STABLE!

Use it for testing an evaluation, but not in an production environment
or contact me first, if you intend to do so.

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

see [Introduction.md](https://gitlab.lrz.de/badw-it/DHParser/blob/master/Introduction.md)

References and Acknowledment
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
Massachusetts, 2004. Short-URL:[t1p.de/jihs][Ford_2004]

[Ford_2004]: https://pdos.csail.mit.edu/~baford/packrat/popl04/peg-popl04.pdf

[Ford_20XX]: http://bford.info/packrat/

Richard A. Frost, Rahmatullah Hafiz and Paul Callaghan: Parser
Combinators for Ambiguous Left-Recursive Grammars, in: P. Hudak and
D.S. Warren (Eds.): PADL 2008, LNCS 4902, pp. 167–181, Springer-Verlag
Berlin Heidelberg 2008.

Elizabeth Scott and Adrian Johnstone, GLL Parsing,
in: Electronic Notes in Theoretical Computer Science 253 (2010) 177–189,
[dotat.at/tmp/gll.pdf][scott_johnstone_2010]

[scott_johnstone_2010]: http://dotat.at/tmp/gll.pdf

Dominikus Herzberg: Objekt-orientierte Parser-Kombinatoren in Python,
Blog-Post, September, 18th 2008 on denkspuren. gedanken, ideen,
anregungen und links rund um informatik-themen, short-URL:
[t1p.de/bm3k][Herzberg_2008a]

[Herzberg_2008a]: http://denkspuren.blogspot.de/2008/09/objekt-orientierte-parser-kombinatoren.html

Dominikus Herzberg: Eine einfache Grammatik für LaTeX, Blog-Post,
September, 18th 2008 on denkspuren. gedanken, ideen, anregungen und
links rund um informatik-themen, short-URL:
[t1p.de/7jzh][Herzberg_2008b]

[Herzberg_2008b]: http://denkspuren.blogspot.de/2008/09/eine-einfache-grammatik-fr-latex.html

Dominikus Herzberg: Uniform Syntax, Blog-Post, February, 27th 2007 on
denkspuren. gedanken, ideen, anregungen und links rund um
informatik-themen, short-URL: [t1p.de/s0zk][Herzberg_2007]

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
[dslbook.org/][Voelter_2013]

Christopher Seaton: A Programming Language Where the Syntax and Semantics
are Mutuable at Runtime, University of Bristol 2007,
[chrisseaton.com/katahdin/katahdin.pdf][seaton_2007]

Vegard Øye: General Parser Combinators in Racket, 2012,
[epsil.github.io/gll/][vegard_2012]

[vegard_2012]: https://epsil.github.io/gll/ 

[seaton_2007]: http://chrisseaton.com/katahdin/katahdin.pdf

[voelter_2013]: http://dslbook.org/

[tex_stackexchange_no_bnf]: http://tex.stackexchange.com/questions/4201/is-there-a-bnf-grammar-of-the-tex-language

[tex_stackexchange_latex_parsers]: http://tex.stackexchange.com/questions/4223/what-parsers-for-latex-mathematics-exist-outside-of-the-tex-engines

[XText_website]: https://www.eclipse.org/Xtext/
