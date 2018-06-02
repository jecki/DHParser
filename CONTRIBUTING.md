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

In case you are interested in getting deeper into DHParser, there are
some bigger projects, below:


Ideas for further development
=============================

Testing for specific error messages
-----------------------------------

Allow testing of error reporting by extending testing.grammar_unit in
such a way that it is possible to test for specific error codes


Better error reporting I
------------------------

A problem with error reporting consists in the fact that at best only
the very first parsing error is reported accurately and then triggers a
number of pure follow up errors. Stopping after the first error would
mean that in order for the user to detect all (true) errors in his or
her file, the parser would have to be run just as many times.

A possible solution could be to define reentry points that can be caught
by a regular expression and where the parsing process restarts in a
defined way.

A reentry point could be defined as a pair (regular expression, parser)
or a triple (regular expression, parent parser, parser), where "parent
parser" would be the parser in the call stack to which the parsing
process retreats, before restarting.

A challenge could be to manage a clean retreat (captured variables,
left recursion stack, etc. without making the parser guard (see
`parse.add_parser_guard`) more complex than it already is.

Also, a good variety of test cases would be desirable.


Optimization and Enhancement: Two-way-Traversal for AST-Transformation
----------------------------------------------------------------------

AST-transformation are done via a depth-first tree-traversal, that is,
the traversal function first goes all the way up the tree to the leaf
nodes and calls the transformation routines successively on the way
down. The routines are picked from the transformation-table which is a
dictionary mapping Node's tag names to sequences of transformation
functions.

The rationale for depth-first is that it is easier to transform a node,
if all of its children have already been transformed, i.e. simplified.
However, there are quite a few cases where depth-last would be better.
For example if you know you are going to discard a whole branch starting
from a certain node, it is a waste to transform all the child nodes
first.

As the tree is traversed anyway, there is no good reason why certain
transformation routines should not already be called on the way up. Of
course, as most routines more or less assume depth first, we would need
two transformation tables one for the routines that are called on the
way up. And one for the routines that are called on the way down.

This should be fairly easy to implement.


Optimization: Early discarding of nodes
---------------------------------------

Reason: `traverse_recursive` and `Node.result-setter` are top time
consumers!

Allow to specify parsers/nodes, the result of which will be dropped
right away, so that the nodes they produce do not need to be removed
during the AST-Transformations. Typical candidates would be:

1. Tokens ":Token"
2. Whitespace ":Whitespace" (in some cases)
3. empty Nodes

and basically anything that would be removed globally ("+" entry in the
AST-Transformation dictionary) later anyway. A directive ("@discarable =
...") could be introduced to specify the discardables

Challenges:

1. Discardable Nodes should not even be created in the first place to
   avoid costly object creation and assignment of result to the Node
   object on creation.

2. ...but discarded or discardable nodes are not the same as a not
   matching parser. Possible solution would be to introduce a
   dummy/zombie-Node that will be discarded by the calling Parser, i.e.
   ZeroOrMore, Series etc.

3. Two kinds of conditions for discarding...?

4. Capture/Retrieve/Pop - need the parsed data even if the node would
   otherwise be discardable (Example: Variable Delimiters.) So, either:

   a. temporarily suspend discarding by Grammar-object-flag set and
      cleared by Capture/Retrieve/Pop. Means yet another flag has to be
      checked every time the decision to discard or not needs to be
      taken...

   b. statically check (i.e. check at compile time) that
      Capture/Retrieve/Pop neither directly nor indirectly call a
      discardable parser. Downside: Some parsers cannot profit from the
      optimization. For example variable delimiters, otherwise as all
      delimiters a good candidate for discarding cannot be discarded any
      more.


Debugging
---------

Supplement the History-Recording functionality of DHParser with a
tracing debugger, i.e. a debugger that allows to trace particular
parsers:

- Add a tracing parser class that - like the Forward-Parser-class -
  "contains" another parser without its calls being run through the
  parser guard, but that records every call of the parser and its
  results, e.g. to trace the `option`-parser from the ebnf-parser (see
  DHParser/ebnf.py) you'd write: `option = Trace(Series(Token("["),
  expression, Token("]"), mandatory=1))`

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
