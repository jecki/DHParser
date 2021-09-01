Contributing
============

DHParser while already fairly mature in terms of implemented features is
still in an experimental state, where the API is changed and smaller
features will be added or dropped from version to version.

The best (and easiest) way to contribute at this stage is to try to
implement a small DSL with DHParser and report bugs and problems and
make suggestions for further development. Have a look at the
README.md-file to get started.

Please, use the code from the git repository. Because code still changes
quickly, any prepackaged builds may be outdated. The repository is here:

    https://gitlab.lrz.de/badw-it/DHParser

Also helpful, would be examples for Editor and IDE-Support for DSLs
built with DHParser. See
https://gitlab.lrz.de/badw-it/MLW-DSL/tree/master/VSCode for one such
example.

Furthermore, documentation and documented case studies of projects
realized with DHParser would be very useful.

In case you are interested in getting deeper into DHParser, there are
some bigger projects, below:


Ideas for further development
=============================


Validation of Abstract Syntax Trees
-----------------------------------

Presently, defining the transformations from the concrete to the
abstract syntax tree is at best a test-driven trial and error process.
A first step to allow for a more systematic process, might be to 
support structural validation of abstract syntax trees. One could
either use the Abstract Syntax Description Language described in:
https://www.cs.princeton.edu/research/techreps/TR-554-97 
(my preferred choice) or, potentially, any of the XML-validation 
techniques, like RelaxNG.

The next step and, evidently, the hard part would be to not only 
validate various specimen of abstract syntax trees, but to verify 
automatically, that, given a certain grammar and a table of 
transformations, the abstract syntax tree thet any well formed 
source code yields is valid according to the structural definition.    


Debugging
---------

Supplement the History-Recording functionality of DHParser with a
tracing debugger, i.e. a debugger that allows to trace particular
parsers:

- Add a tracing parser class that - like the Forward-Parser-class -
  "contains" another parser without its calls being run through the
  parser guard, but that records every call of the parser and its
  results, e.g. to trace the `option`-parser from the ebnf-parser (see
  DHParser/ebnf.py) you'd write: `option = Trace(Series(_Token("["),
  expression, _Token("]"), mandatory=1))`

- For the ebnf-representation a tracing-prefix could be added, say `?`,
  e.g. `option = ?("[" §expression "]")` or, alternatively, `?option =
  "[" §expression "]"`

- Another Alternative would be to add an EBNF-compiler directive, say `@
  trace`, so one could write `@ trace = option` at the beginning of the
  EBNF-code.
  * disadvantage: only parsers represented by symobols can be traced
    (can always be circumvented by introducing further symbols.)
  * advantages: less clutter in the EBNF-code and easier to switch
    between debugging and production code by simply commenting out the
    trace-statements at the beginning.


Semantic Actions
----------------

A alternative way (instead of using Capture-Pop/Retrieve with retrieve
filters) to implement semantic actions would be by using derived classes
in place of of the stock parser classes in the Grammar object. The
derived classes can easily implement semantic actions.

In order to integrate derived classes into the ebnf-based parser
generation, a directive could be implemented that either allows binding
derived classes to certain symbols or defining substitutes for stock
parser classes or both.

The difference between the two cases (let's call them "binding" and
"substitution" to make the distinction) is that the former only
substitutes a particular parser (`term` in the example below) while the
latter substitutes all parsers of a kind (Alternative in the examples
below).

In any case ebnf.EBNFCompiler should be extended to generate stubs for
the respective derived classes. The base class would either be the root
parser class for the symbol or the substituted class referred to in the
directive. Furthermore, ebnf.EBNFCompiler must, of course use the
substituting parsers in the generated Grammar class.

Syntax proposal and example (EBNF directive)

    @semantic_action = term, SemanticAlternative:Alternative

    expression = term  { ("+" | "-") term}
    term = factor { ("*"|"/") factor }
    ...

 The generated code might look like:

    class TermSeries(Series):
        """A derived class of parser Series with semantic actions"""

        def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
            result = super().__call__(text)
            # please implement your semantic action here


    class SemanticAlternative(Alternative):
        """A derived class of parser Series with semantic actions"""

        def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
            result = super().__call__(text)
            # please implement your semantic action here


    class ArithmeticGrammar(Gramma):
        ...
        expression = Forward()
        term = TermSeries(factor, ZeroOrMore(Series(SemanticAlternative(Token("*"), Token("/")), factor)))
        expression.set(Series(term, ZeroOrMore(Series(SemanticAlternative(Token("+"), Token("-")), term))))
        root__ = expression
