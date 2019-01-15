Workshop: DHParser - Domain Specific Languages for the Digital Humanities
=========================================================================

Proposal for a workshop (180 min) for the [deRSE2019
Conference](https://derse19.uni-jena.de/)

by Eckhart Arnold, Bavarian Academy of Sciences and Humanities, arnold@badw.de

Abstract
--------

Domain specific languages have become an ubiquitous tool in the
software-industry, in many cases replacing XML as configuration or
data description language. By now, there exist quite a few mature
DSL-construction toolkits and DSL-parser generators out there
([Xtext], [MPS], [ANTLR], [pyparsing]) that support the creation of
DSLs.

Nonetheless, DSLs are strangely underused in Digital Humanities
Projects, even though they can provide a great addition, if not in
some cases viable alternative to the omnipresent XML-toolchains. One
possible reason why DSLs have not yet become popular in the Digital
Humanities is that the common DSL construction kits and parser
generators are geared towards different application domains, and do
not fulfill the specific demands of Digital Humanities contexts. In
the Digital Humanities DSLs, just like the XML-data-structures, say,
for a historical-critical edition, can become quite complex, evolve
over time, result from an iterative testing and discussion process in
which users interact with programmers and must be understandable and
usable with ease by researchers that not necessarily accustomed to
computer technology.

[DHParser] is a parser generator for DSLs, developed at the Bavarian
Academy of Sciences and Humanities, that specifically addresses the
Digital Humanities. In particular, it offers support for:

- unit testing of DSLs

- specifying meaningful error messages for the user of the DSL and
  locating errors correctly

- debugging support for the DSL-specification and parsing process

- support for abstract-syntax-tree-generation

- a basic framework for compiler construction with XML-output as the
  most common use case in mind

- programming in Python, the most commonly known and used programming
  language in the Digital Humanities

In the workshop, I am going to explain how to develop a Frontend-DSL
for the “[DTA-Basisformat]” (or, for the purpose of introduction, a
subset thereof). We will assume the “DTA-Basisformat” as a given
target-format und run through the whole development process from
designing the syntax of the DSL through examples, specifying it
formally with [EBNF], directing abstract-syntax-tree generation,
generating XML-output, writing test-cases and specifying error
messages. If time permits, we will also look into the process of
preparing an editor / development environment for our DTA-DSL with
[Visual Studio Code].

In the end, every participant will have learned:

- what a DSL is and what the steps for creating one are

- how the syntax of a DSL can be specified in an EBNF-like formalism

- how a simple DSL-XML-compiler is programmed in Python with the
  DHParser-framework

- how important practical concerns like unit-testing of DSLs and
  error-reporting can be addressed

- How DSLs relate to XML: Basically, XML allows you to declare and encode
  the domain specific semantics of any kind of data, DSLs also enable you
  to specify a domain specific syntax for you data, rendering the encoded
  data much more human-readable (and -writable) than XML.

- how to use DHParser ;-)

We will close the workshop with a discussion about the benefits as
well as possible disadvantages of employing DSLs in DH-projects in
relation to the necessary effort in in comparison to the
ordinary XML-workflows.

**Requirements for participating and benefiting from the workshop:**

- good working knowledge of [Python] and [regular expressions]
- a laptop with python installed

Suggested Reading:

- [Introduction to DHParser]
- or, more detailed, the [Step by Step Guide to DHParser]
- or, for a real world example, though work in progress, the [DSL for
  the medival latin dictionary]

[Xtext]: https://www.eclipse.org/Xtext/
[MPS]: https://www.jetbrains.com/mps/
[ANTLR]: https://www.antlr.org/
[pyparsing]: https://pypi.org/project/pyparsing/
[DHParser]: https://gitlab.lrz.de/badw-it/DHParser
[DTA-Basisformat]: http://www.deutschestextarchiv.de/doku/basisformat/
[EBNF]: https://www.cl.cam.ac.uk/~mgk25/iso-14977.pdf
[Visual Studio Code]: https://code.visualstudio.com/
[Python]: https://www.python.org/
[regular expressions]: https://docs.python.org/3/library/re.html
[Introduction to DHParser]: https://gitlab.lrz.de/badw-it/DHParser/blob/development/Introduction.md
[step by step guide to DHParser]: https://gitlab.lrz.de/badw-it/DHParser/blob/development/documentation/StepByStepGuide.rst
[DSL for the medival latin dictionary]: https://gitlab.lrz.de/badw-it/MLW-DSL
