"""parsers.py - parser combinators for for DHParser

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.

Module ``parsers.py`` contains a number of classes that together
make up parser combinators for left-recursive grammers. For each
element of the extended Backus-Naur-Form as well as for a regular
expression token a class is defined. The set of classes can be used to
define a parser for (ambiguous) left-recursive grammers.


References and Acknowledgements:

Dominikus Herzberg: Objekt-orientierte Parser-Kombinatoren in Python,
Blog-Post, September, 18th 2008 on denkspuren. gedanken, ideen,
anregungen und links rund um informatik-themen, URL:
http://denkspuren.blogspot.de/2008/09/objekt-orientierte-parser-kombinatoren.html

Dominikus Herzberg: Eine einfache Grammatik für LaTeX, Blog-Post,
September, 18th 2008 on denkspuren. gedanken, ideen, anregungen und
links rund um informatik-themen, URL:
http://denkspuren.blogspot.de/2008/09/eine-einfache-grammatik-fr-latex.html

Dominikus Herzberg: Uniform Syntax, Blog-Post, February, 27th 2007 on
denkspuren. gedanken, ideen, anregungen und links rund um
informatik-themen, URL:
http://denkspuren.blogspot.de/2007/02/uniform-syntax.html

Richard A. Frost, Rahmatullah Hafiz and Paul Callaghan: Parser
Combinators for Ambiguous Left-Recursive Grammars, in: P. Hudak and
D.S. Warren (Eds.): PADL 2008, LNCS 4902, pp. 167–181, Springer-Verlag
Berlin Heidelberg 2008.

Elizabeth Scott and Adrian Johnstone, GLL Parsing,
in: Electronic Notes in Theoretical Computer Science 253 (2010) 177–189,
http://dotat.at/tmp/gll.pdf

Juancarlo Añez: grako, a PEG parser generator in Python,
https://bitbucket.org/apalala/grako

Vegard Øye: General Parser Combinators in Racket, 2012,
https://epsil.github.io/gll/
"""

import collections
import copy
import html
import os

from DHParser.error import Error, is_error, has_errors, linebreaks, line_col, adjust_error_locations
from DHParser.stringview import StringView, EMPTY_STRING_VIEW
from DHParser.syntaxtree import Node, TransformationFunc, ParserBase, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, ZOMBIE_PARSER
from DHParser.preprocess import BEGIN_TOKEN, END_TOKEN, RX_TOKEN_NAME, \
    PreprocessorFunc, with_source_mapping, strip_tokens
from DHParser.toolkit import is_logging, log_dir, logfile_basename, escape_re, sane_parser_name, \
    escape_control_characters, load_if_file, re, typing
from typing import Any, Callable, cast, Dict, List, Set, Tuple, Union, Optional

__all__ = ('HistoryRecord',
           'Parser',
           'UnknownParserError',
           'Grammar',
           'PreprocessorToken',
           'RegExp',
           'RE',
           'Token',
           'mixin_comment',
           # 'UnaryOperator',
           # 'NaryOperator',
           'Synonym',
           'Option',
           'ZeroOrMore',
           'OneOrMore',
           'Series',
           'Alternative',
           'AllOf',
           'SomeOf',
           'Unordered',
           'Lookahead',
           'NegativeLookahead',
           'Lookbehind',
           'NegativeLookbehind',
           'last_value',
           'counterpart',
           'accumulate',
           'Capture',
           'Retrieve',
           'Pop',
           'Forward',
           'Compiler',
           'compile_source')


########################################################################
#
# Grammar and parsing infrastructure
#
########################################################################


LEFT_RECURSION_DEPTH = 8  # type: int
# because of python's recursion depth limit, this value ought not to be
# set too high. PyPy allows higher values than CPython
MAX_DROPOUTS = 3  # type: int
# stop trying to recover parsing after so many errors


class HistoryRecord:
    """
    Stores debugging information about one completed step in the
    parsing history.

    A parsing step is "completed" when the last one of a nested
    sequence of parser-calls returns. The call stack including
    the last parser call will be frozen in the ``HistoryRecord``-
    object. In addition a reference to the generated leaf node
    (if any) will be stored and the result status of the last
    parser call, which ist either MATCH, FAIL (i.e. no match)
    or ERROR.
    """
    __slots__ = ('call_stack', 'node', 'text', 'line_col')

    MATCH = "MATCH"
    ERROR = "ERROR"
    FAIL = "FAIL"
    Snapshot = collections.namedtuple('Snapshot', ['line', 'column', 'stack', 'status', 'text'])

    COLGROUP = '<colgroup>\n<col style="width:2%"/><col style="width:2%"/><col style="width:75"/>' \
               '<col style="width:6%"/><col style="width:15%"/>\n</colgroup>\n'
    HTML_LEAD_IN  = (
        '<html>\n<head>\n<meta charset="utf-8"/>\n<style>\n'
        'td.line, td.column {font-family:monospace;color:darkgrey}\n'
        'td.stack{font-family:monospace}\n'
        'td.status{font-family:monospace;font-weight:bold}\n'
        'td.text{font-family:monospace;color:darkblue}\n'
        'table{border-spacing: 0px; border: thin solid darkgrey; width:100%}\n'
        'td{border-right: thin solid grey; border-bottom: thin solid grey}\n'
        'span.delimiter{color:grey;}\nspan.match{color:darkgreen}\n'
        'span.fail{color:darkgrey}\nspan.error{color:red}\n'
        'span.matchstack{font-weight:bold;color:darkred}'
        '\n</style>\n</head>\n<body>\n<table>\n' + COLGROUP)
    HTML_LEAD_OUT = '\n</table>\n</body>\n</html>\n'

    def __init__(self, call_stack: List['Parser'], node: Node, text: StringView) -> None:
        # copy call stack, dropping uninformative Forward-Parsers
        self.call_stack = [p for p in call_stack if p.ptype != ":Forward"]  # type: List['Parser']
        self.node = node                # type: Node
        self.text = text                # type: StringView
        self.line_col = (1, 1)          # type: Tuple[int, int]
        if call_stack:
            grammar = call_stack[-1].grammar
            document = grammar.document__
            lbreaks = grammar.document_lbreaks__
            self.line_col = line_col(lbreaks, len(document) - len(text))

    def __str__(self):
        return '%4i, %2i:  %s;  %s;  "%s"' % self.as_tuple()

    def as_tuple(self) -> Snapshot:
        """
        Returns history record formatted as a snapshot tuple.
        """
        return self.Snapshot(self.line_col[0], self.line_col[1],
                             self.stack, self.status, self.excerpt)
    def as_csv_line(self) -> str:
        """
        Returns history record formatted as a csv table row.
        """
        return '"{}", "{}", "{}", "{}", "{}"'.format(*self.as_tuple())

    def as_html_tr(self) -> str:
        """
        Returns history record formatted as an html table row.
        """
        stack = html.escape(self.stack).replace(
            '-&gt;', '<span class="delimiter">&shy;-&gt;</span>')
        status = html.escape(self.status)
        excerpt = html.escape(self.excerpt)
        if status == self.MATCH:
            status = '<span class="match">' + status + '</span>'
            i = stack.rfind('-&gt;')
            chr = stack[i+12:i+13]
            while not chr.isidentifier() and i >= 0:
                i = stack.rfind('-&gt;', 0, i)
                chr = stack[i+12:i+13]
            if i >= 0:
                i += 12
                k = stack.find('<', i)
                if k < 0:
                    stack = stack[:i] + '<span class="matchstack">' + stack[i:]
                else:
                    stack = stack[:i] + '<span class="matchstack">' + stack[i:k] \
                            + '</span>' + stack[k:]
        elif status == self.FAIL:
            status = '<span class="fail">' + status + '</span>'
        else:
            stack += '<br/>\n' + status
            status = '<span class="error">ERROR</span>'
        tpl = self.Snapshot(str(self.line_col[0]), str(self.line_col[1]), stack, status, excerpt)
        # return ''.join(['<tr>'] + [('<td>%s</td>' % item) for item in tpl] + ['</tr>'])
        return ''.join(['<tr>'] + [('<td class="%s">%s</td>' % (cls, item))
                                   for cls, item in zip(tpl._fields, tpl)] + ['</tr>'])

    def err_msg(self) -> str:
        return self.ERROR + ": " + "; ".join(
            str(e) for e in (self.node._errors if self.node._errors else
                             self.node.collect_errors()[:2]))

    @property
    def stack(self) -> str:
        return "->".join((p.repr if p.ptype == ':RegExp' else p.name or p.ptype)
                         for p in self.call_stack)

    @property
    def status(self) -> str:
        return self.FAIL if self.node is None else \
            ('"%s"' % self.err_msg()) if self.node.error_flag else self.MATCH  # has_errors(self.node._errors)

    @property
    def excerpt(self):
        length = len(self.node) if self.node else len(self.text)
        excerpt = str(self.node)[:min(length, 20)] if self.node else str(self.text[:20])
        excerpt = escape_control_characters(excerpt)
        if length > 20:
            excerpt += '...'
        return excerpt

    # @property
    # def extent(self) -> slice:
    #     return (slice(-self.remaining - len(self.node), -self.remaining) if self.node
    #             else slice(-self.remaining, None))

    @property
    def remaining(self) -> int:
        return len(self.text) - (len(self.node) if self.node else 0)

    @staticmethod
    def last_match(history: List['HistoryRecord']) -> Union['HistoryRecord', None]:
        """
        Returns the last match from the parsing-history.
        Args:
            history:  the parsing-history as a list of HistoryRecord objects

        Returns:
            the history record of the last match or none if either history is
            empty or no parser could match
        """
        for record in reversed(history):
            if record.status == HistoryRecord.MATCH:
                return record
        return None

    @staticmethod
    def most_advanced_match(history: List['HistoryRecord']) -> Union['HistoryRecord', None]:
        """
        Returns the closest-to-the-end-match from the parsing-history.
        Args:
            history:  the parsing-history as a list of HistoryRecord objects

        Returns:
            the history record of the closest-to-the-end-match or none if either history is
            empty or no parser could match
        """
        remaining = -1
        result = None
        for record in history:
            if (record.status == HistoryRecord.MATCH and
                    (record.remaining < remaining or remaining < 0)):
                result = record
                remaining = record.remaining
        return result


def add_parser_guard(parser_func):
    """
    Add a wrapper function to a parser functions (i.e. Parser.__call__ method)
    that takes care of memoizing, left recursion and, optionally, tracing
    (aka "history tracking") of parser calls. Returns the wrapped call.
    """
    def guarded_call(parser: 'Parser', text: StringView) -> Tuple[Optional[Node], StringView]:
        try:
            grammar = parser.grammar
            location = grammar.document_length__ - len(text)

            if grammar.last_rb__loc__ >= location:
                grammar.rollback_to__(location)

            # if location has already been visited by the current parser,
            # return saved result
            if location in parser.visited:
                # no history recording in case of meomized results
                return parser.visited[location]

            if grammar.history_tracking__:
                grammar.call_stack__.append(parser)
                grammar.moving_forward__ = True

            # break left recursion at the maximum allowed depth
            if grammar.left_recursion_handling__:
                if parser.recursion_counter.setdefault(location, 0) > LEFT_RECURSION_DEPTH:
                    grammar.recursion_locations__.add(location)
                    return None, text
                parser.recursion_counter[location] += 1

            # run original __call__ method
            node, rest = parser_func(parser, text)

            if grammar.left_recursion_handling__:
                parser.recursion_counter[location] -= 1

            if node is None:
                # retrieve an earlier match result (from left recursion) if it exists
                if location in grammar.recursion_locations__:
                    if location in parser.visited:
                        node, rest = parser.visited[location]
                        # TODO: maybe add a warning about occurrence of left-recursion here?
                    # don't overwrite any positive match (i.e. node not None) in the cache
                    # and don't add empty entries for parsers returning from left recursive calls!
                elif grammar.memoization__:
                    # otherwise also cache None-results
                    parser.visited[location] = (None, rest)
            else:
                assert node._pos < 0
                node._pos = location
                assert node._pos >= 0, str("%i < %i" % (grammar.document_length__, location))
                if (grammar.last_rb__loc__ < location
                        and (grammar.memoization__ or location in grammar.recursion_locations__)):
                    # - variable manipulating parsers will not be entered into the cache,
                    #   because caching would interfere with changes of variable state
                    # - in case of left recursion, the first recursive step that
                    #   matches will store its result in the cache
                    parser.visited[location] = (node, rest)

            # Mind that meomized parser calls will not appear in the history record!
            if grammar.history_tracking__:
                # don't track returning parsers except in case an error has occurred
                remaining = len(rest)
                if grammar.moving_forward__ or (node and node.error_flag):  # node._errors
                    record = HistoryRecord(grammar.call_stack__, node, text)
                    grammar.history__.append(record)
                    # print(record.stack, record.status, rest[:20].replace('\n', '|'))
                grammar.moving_forward__ = False
                grammar.call_stack__.pop()

        except RecursionError:
            node = Node(None, str(text[:min(10, max(1, text.find("\n")))]) + " ...")
            node.add_error("maximum recursion depth of parser reached; "
                           "potentially due to too many errors!")
            rest = EMPTY_STRING_VIEW

        return node, rest

    return guarded_call


class Parser(ParserBase):
    """
    (Abstract) Base class for Parser combinator parsers. Any parser
    object that is actually used for parsing (i.e. no mock parsers)
    should should be derived from this class.

    Since parsers can contain other parsers (see classes UnaryOperator
    and NaryOperator) they form a cyclical directed graph. A root
    parser is a parser from which all other parsers can be reached.
    Usually, there is one root parser which serves as the starting
    point of the parsing process. When speaking of "the root parser"
    it is this root parser object that is meant.

    There are two different types of parsers:

    1. *Named parsers* for which a name is set in field `parser.name`.
       The results produced by these parsers can later be retrieved in
       the AST by the parser name.

    2. *Anonymous parsers* where the name-field just contains the empty
       string. AST-transformation of Anonymous parsers can be hooked
       only to their class name, and not to the individual parser.

    Parser objects are callable and parsing is done by calling a parser
    object with the text to parse.

    If the parser matches it returns a tuple consisting of a node
    representing the root of the concrete syntax tree resulting from the
    match as well as the substring `text[i:]` where i is the length of
    matched text (which can be zero in the case of parsers like
    `ZeroOrMore` or `Option`). If `i > 0` then the parser has "moved
    forward".

    If the parser does not match it returns `(None, text). **Note** that
    this is not the same as an empty match `("", text)`. Any empty match
    can for example be returned by the `ZeroOrMore`-parser in case the
    contained parser is repeated zero times.

    Attributes and Properties:
        visited:  Mapping of places this parser has already been to
                during the current parsing process onto the results the
                parser returned at the respective place. This dictionary
                is used to implement memoizing.

        recursion_counter:  Mapping of places to how often the parser
                has already been called recursively at this place. This
                is needed to implement left recursion. The number of
                calls becomes irrelevant once a resault has been memoized.

        cycle_detection:  The apply()-method uses this variable to make
                sure that one and the same function will not be applied
                (recursively) a second time, if it has already been
                applied to this parser.

        grammar:  A reference to the Grammar object to which the parser
                is attached.
    """

    ApplyFunc = Callable[['Parser'], None]

    def __init__(self, name: str = '') -> None:
        # assert isinstance(name, str), str(name)
        super(Parser, self).__init__(name)
        self._grammar = None  # type: 'Grammar'
        self.reset()

        # add "aspect oriented" wrapper around parser calls
        # for memoizing, left recursion and tracing
        if not isinstance(self, Forward):  # should Forward-Parser no be guarded? Not sure...
            guarded_parser_call = add_parser_guard(self.__class__.__call__)
            # The following check is necessary for classes that don't override
            # the __call__() method, because in these cases the non-overridden
            # __call__()-method would be substituted a second time!
            if self.__class__.__call__.__code__ != guarded_parser_call.__code__:
                self.__class__.__call__ = guarded_parser_call

    def __deepcopy__(self, memo):
        """Deepcopy method of the parser. Upon instantiation of a Grammar-
        object, parsers will be deep-copied to the Grammar object. If a
        derived parser-class changes the signature of the constructor,
        `__deepcopy__`-method must be replaced (i.e. overridden without
        calling the same method from the superclass) by the derived class.
        """
        return self.__class__(self.name)

    def reset(self):
        """Initializes or resets any parser variables. If overwritten,
        the `reset()`-method of the parent class must be called from the
        `reset()`-method of the derived class."""
        self.visited = dict()            # type: Dict[int, Tuple[Optional[Node], StringView]]
        self.recursion_counter = dict()  # type: Dict[int, int]
        self.cycle_detection = set()     # type: Set[Callable]

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        """Applies the parser to the given `text` and returns a node with
        the results or None as well as the text at the position right behind
        the matching string."""
        return None, text  # default behaviour: don't match

    def __add__(self, other: 'Parser') -> 'Series':
        """The + operator generates a series-parser that applies two
        parsers in sequence."""
        return Series(self, other)

    def __or__(self, other: 'Parser') -> 'Alternative':
        """The | operator generates an alternative parser that applies
        the first parser and, if that does not match, the second parser.
        """
        return Alternative(self, other)

    @property
    def grammar(self) -> 'Grammar':
        return self._grammar

    @grammar.setter
    def grammar(self, grammar: 'Grammar'):
        if self._grammar is None:
            self._grammar = grammar
            self._grammar_assigned_notifier()
        else:
            assert self._grammar == grammar, \
                "Parser has already been assigned to a different Grammar object!"

    def _grammar_assigned_notifier(self):
        """A function that notifies the parser object that it has been
        assigned to a grammar."""
        pass

    def apply(self, func: ApplyFunc) -> bool:
        """
        Applies function `func(parser)` recursively to this parser and all
        descendant parsers if any exist. The same function can never
        be applied twice between calls of the ``reset()``-method!
        Returns `True`, if function has been applied, `False` if function
        had been applied earlier already and thus has not been applied again.
        """
        if func in self.cycle_detection:
            return False
        else:
            assert not self.visited, "No calls to Parser.apply() during or " \
                                     "after ongoing parsing process. (Call Parser.reset() first.)"
            self.cycle_detection.add(func)
            func(self)
            return True


def mixin_comment(whitespace: str, comment: str) -> str:
    """
    Returns a regular expression that merges comment and whitespace
    regexps. Thus comments cann occur whereever whitespace is allowed
    and will be skipped just as implicit whitespace.

    Note, that because this works on the level of regular expressions,
    nesting comments is not possible. It also makes it much harder to
    use directives inside comments (which isn't recommended, anyway).
    """
    wspc = '(?:' + whitespace + '(?:' + comment + whitespace + ')*)'
    return wspc


class UnknownParserError(KeyError):
    """UnknownParserError is raised if a Grammer object is called with a
    parser that does not exist or if in the course of parsing a parser
    is reffered to that does not exist."""


class Grammar:
    r"""
    Class Grammar directs the parsing process and stores global state
    information of the parsers, i.e. state information that is shared
    accross parsers.

    Grammars are basically collections of parser objects, which are
    connected to an instance object of class Grammar. There exist two
    ways of connecting parsers to grammar objects: Either by passing
    the root parser object to the constructor of a Grammar object
    ("direct instantiation"), or by assigning the root parser to the
    class variable "root__" of a descendant class of class Grammar.

    Example for direct instantian of a grammar:

        >>> number = RE('\d+') + RE('\.') + RE('\d+') | RE('\d+')
        >>> number_parser = Grammar(number)
        >>> number_parser("3.1416").content
        '3.1416'

    Collecting the parsers that define a grammar in a descendant class of
    class Grammar and assigning the named parsers to class variables
    rather than global variables has several advantages:

    1. It keeps the namespace clean.

    2. The parser names of named parsers do not need to be passed to the
       constructor of the Parser object explicitly, but it suffices to
       assign them to class variables, which results in better
       readability of the Python code.

    3. The parsers in the class do not necessarily need to be connected
       to one single root parser, which is helpful for testing and
       building up a parser successively of several components.

    As a consequence, though, it is highly recommended that a Grammar
    class should not define any other variables or methods with names
    that are legal parser names. A name ending with a double
    underscore '__' is *not* a legal parser name and can safely be
    used.

    Example:

        class Arithmetic(Grammar):
            # special fields for implicit whitespace and comment configuration
            COMMENT__ = r'#.*(?:\n|$)'  # Python style comments
            wspR__ = mixin_comment(whitespace=r'[\t ]*', comment=COMMENT__)

            # parsers
            expression = Forward()
            INTEGER = RE('\\d+')
            factor = INTEGER | Token("(") + expression + Token(")")
            term = factor + ZeroOrMore((Token("*") | Token("/")) + factor)
            expression.set(term + ZeroOrMore((Token("+") | Token("-")) + term))
            root__ = expression

    Upon instantiation the parser objects are deep-copied to the
    Grammar object and assigned to object variables of the same name.
    Any parser that is directly assigned to a class variable is a
    'named' parser and its field `parser.name` contains the variable
    name after instantiation of the Grammar class. All other parsers,
    i.e. parsers that are defined within a `named` parser, remain
    "anonymous parsers" where `parser.name` is the empty string, unless
    a name has been passed explicitly upon instantiation.
    If one and the same parser is assigned to several class variables
    such as, for example the parser `expression` in the example above,
    the first name sticks.

    Grammar objects are callable. Calling a grammar object with a UTF-8
    encoded document, initiates the parsing of the document with the
    root parser. The return value is the concrete syntax tree. Grammar
    objects can be reused (i.e. called again) after parsing. Thus, it
    is not necessary to instantiate more than one Grammar object per
    thread.

    Grammar classes contain a few special class fields for implicit
    whitespace and comments that should be overwritten, if the defaults
    (no comments, horizontal right aligned whitespace) don't fit:
    COMMENT__:  regular expression string for matching comments
    WSP__:   regular expression for whitespace and comments

    wspL__:  regular expression string for left aligned whitespace,
             which either equals WSP__ or is empty.

    wspR__:  regular expression string for right aligned whitespace,
             which either equals WSP__ or is empty.

    root__:  The root parser of the grammar. Theoretically, all parsers of the
             grammar should be reachable by the root parser. However, for testing
             of yet incomplete grammars class Grammar does not assume that this
             is the case.

    parser_initializiation__:  Before the parser class (!) has been initialized,
             which happens upon the first time it is instantiated (see doctring for
             method `_assign_parser_names()` for an explanation), this class
             field contains a value other than "done". A value of "done" indicates
             that the class has already been initialized.

    Attributes:
        all_parsers__:  A set of all parsers connected to this grammar object

        history_tracking__:  A flag indicating that the parsing history shall
                be tracked

        wsp_left_parser__:  A parser for the default left-adjacent-whitespace
                or the zombie-parser (see `syntaxtree.ZOMBIE_PARSER`) if the
                default is empty. The default whitespace will be used by parsers
                `Token` and, if no other parsers are passed to its constructor,
                by parser `RE'.

        wsp_right_parser__: The same for the default right-adjacent-whitespace.
                Both wsp_left_parser__ and wsp_right_parser__ merely serve the
                purpose to avoid having to specify the default whitespace
                explicitly every time an `RE`-parser-object is created.

        _dirty_flag__:  A flag indicating that the Grammar has been called at
                least once so that the parsing-variables need to be reset
                when it is called again.

        document__:  the text that has most recently been parsed or that is
                currently being parsed.

        document_length__:  the length of the document.

        document_lbreaks__:  list of linebreaks within the document, starting
                with -1 and ending with EOF. This helps generating line
                and column number for history recording and will only be
                initialized if `history_tracking__` is true.

        _reversed__:  the same text in reverse order - needed by the `Lookbehind'-
                parsers.

        variables__:  A mapping for variable names to a stack of their respective
                string values - needed by the `Capture`-, `Retrieve`- and `Pop`-
                parsers.

        rollback__:  A list of tuples (location, rollback-function) that are
                deposited by the `Capture`- and `Pop`-parsers. If the parsing
                process reaches a dead end then all rollback-functions up to
                the point to which it retreats will be called and the state
                of the variable stack restored accordingly.

        last_rb__loc__:  The last, i.e. most advanced location in the text
                where a variable changing operation occurred. If the parser
                backtracks to a location at or before `last_rb__loc__` (i.e.
                `location <= last_rb__loc__`) then a rollback of all variable
                changing operations is necessary that occurred after the
                location to which the parser backtracks. This is done by
                calling method `.rollback_to__(location)`.

        call_stack__:  A stack of all parsers that have been called. This
                is required for recording the parser history (for debugging)
                and, eventually, i.e. one day in the future, for tracing through
                the parsing process.

        history__:  A list of parser-call-stacks. A parser-call-stack is
                appended to the list each time a parser either matches, fails
                or if a parser-error occurs.

        moving_forward__: This flag indicates that the parsing process is currently
                moving forward . It is needed to reduce noise in history recording
                and should not be considered as having a valid value if history
                recording is turned off! (See `add_parser_guard` and its local
                function `guarded_call`)

        recursion_locations__:  Stores the locations where left recursion was
                detected. Needed to provide minimal memoization for the left
                recursion detection algorithm, but, strictly speaking, superfluous
                if full memoization is enabled. (See `add_parser_guard` and its
                local function `guarded_call`)

        memoization__:  Turns full memoization on or off. Turning memoization off
                results in less memory usage and sometimes reduced parsing time.
                In some situations it may drastically increase parsing time, so
                it is safer to leave it on. (Default: on)

        left_recursion_handling__:  Turns left recursion handling on or off.
                If turned off, a recursion error will result in case of left
                recursion.
    """
    root__ = ZOMBIE_PARSER  # type: ParserBase
    # root__ must be overwritten with the root-parser by grammar subclass
    parser_initialization__ = "pending"  # type: str
    # some default values
    COMMENT__ = r''  # type: str  # r'#.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'[\t ]*', comment=COMMENT__)  # type: str
    wspL__ = ''     # type: str
    wspR__ = WSP__  # type: str


    @classmethod
    def _assign_parser_names__(cls):
        """
        Initializes the `parser.name` fields of those
        Parser objects that are directly assigned to a class field with
        the field's name, e.g.
            class Grammar(Grammar):
                ...
                symbol = RE('(?!\\d)\\w+')
        After the call of this method symbol.name == "symbol"
        holds. Names assigned via the ``name``-parameter of the
        constructor will not be overwritten. Parser names starting or
        ending with a double underscore like ``root__`` will be
        ignored. See ``toolkit.sane_parser_name()``

        This is done only once, upon the first instantiation of the
        grammar class!

        Attention: If there exists more than one reference to the same
        parser, only the first one will be chosen for python versions
        greater or equal 3.6.  For python version <= 3.5 an arbitrarily
        selected reference will be chosen. See PEP 520
        (www.python.org/dev/peps/pep-0520/) for an explanation of why.
        """
        if cls.parser_initialization__ != "done":
            cdict = cls.__dict__
            for entry, parser in cdict.items():
                if isinstance(parser, Parser) and sane_parser_name(entry):
                    if not parser.name:
                        parser._name = entry
                    if isinstance(parser, Forward) and (not parser.parser._name):
                        parser.parser._name = entry
            cls.parser_initialization__ = "done"


    def __init__(self, root: Parser = None) -> None:
        # if not hasattr(self.__class__, 'parser_initialization__'):
        #     self.__class__.parser_initialization__ = "pending"
        # if not hasattr(self.__class__, 'wspL__'):
        #     self.wspL__ = ''
        # if not hasattr(self.__class__, 'wspR__'):
        #     self.wspR__ = ''
        self.all_parsers__ = set()             # type: Set[ParserBase]
        self._dirty_flag__ = False             # type: bool
        self.history_tracking__ = False        # type: bool
        self.memoization__ = True              # type: bool
        self.left_recursion_handling__ = True  # type: bool
        self._reset__()

        # prepare parsers in the class, first
        self._assign_parser_names__()

        # then deep-copy the parser tree from class to instance;
        # parsers not connected to the root object will be copied later
        # on demand (see Grammar.__getitem__()). Usually, the need to
        # do so only arises during testing.
        self.root__ = copy.deepcopy(root) if root else copy.deepcopy(self.__class__.root__)

        if self.wspL__:
            self.wsp_left_parser__ = Whitespace(self.wspL__)  # type: ParserBase
            self.wsp_left_parser__.grammar = self
            self.all_parsers__.add(self.wsp_left_parser__)  # don't you forget about me...
        else:
            self.wsp_left_parser__ = ZOMBIE_PARSER
        if self.wspR__:
            self.wsp_right_parser__ = Whitespace(self.wspR__)  # type: ParserBase
            self.wsp_right_parser__.grammar = self
            self.all_parsers__.add(self.wsp_right_parser__)  # don't you forget about me...
        else:
            self.wsp_right_parser__ = ZOMBIE_PARSER
        self.root__.apply(self._add_parser__)


    def __getitem__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            parser_template = getattr(self, key, None)
            if parser_template:
                # add parser to grammar object on the fly...
                parser = copy.deepcopy(parser_template)
                parser.apply(self._add_parser__)
                # assert self[key] == parser
                return self[key]
            raise UnknownParserError('Unknown parser "%s" !' % key)


    def _reset__(self):
        self.document__ = EMPTY_STRING_VIEW   # type: StringView
        self._reversed__ = EMPTY_STRING_VIEW  # type: StringView
        self.document_length__ = 0            # type: int
        self.document_lbreaks__ = []          # type: List[int]
        # variables stored and recalled by Capture and Retrieve parsers
        self.variables__ = dict()             # type: Dict[str, List[str]]
        self.rollback__ = []                  # type: List[Tuple[int, Callable]]
        self.last_rb__loc__ = -1              # type: int
        # support for call stack tracing
        self.call_stack__ = []                # type: List[Parser]
        # snapshots of call stacks
        self.history__ = []                   # type: List[HistoryRecord]
        # also needed for call stack tracing
        self.moving_forward__ = False         # type: bool
        self.recursion_locations__ = set()    # type: Set[int]


    @property
    def reversed__(self) -> StringView:
        """
        Returns a reversed version of the currently parsed document. As
        about the only case where this is needed is the Lookbehind-parser,
        this is done lazily.
        """
        if not self._reversed__:
            self._reversed__ = StringView(self.document__.text[::-1])
        return self._reversed__


    def _add_parser__(self, parser: Parser) -> None:
        """
        Adds the particular copy of the parser object to this
        particular instance of Grammar.
        """
        if parser.name:
            # prevent overwriting instance variables or parsers of a different class
            assert parser.name not in self.__dict__ or \
                   isinstance(self.__dict__[parser.name], parser.__class__), \
                ('Cannot add parser "%s" because a field with the same name '
                 'already exists in grammar object!' % parser.name)
            setattr(self, parser.name, parser)
        self.all_parsers__.add(parser)
        parser.grammar = self


    def __call__(self, document: str, start_parser="root__") -> Node:
        """
        Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
            start_parser (str): The name of the parser with which to
                start. This is useful for testing particular parsers
                (i.e. particular parts of the EBNF-Grammar.)
        Returns:
            Node: The root node ot the parse tree.
        """

        def tail_pos(predecessors: Union[List[Node], Tuple[Node, ...]]) -> int:
            """Adds the position after the last node in the list of
            predecessors to the node."""
            return predecessors[-1].pos + len(predecessors[-1]) if predecessors else 0

        # assert isinstance(document, str), type(document)
        if self.root__ is None:
            raise NotImplementedError()
        if self._dirty_flag__:
            self._reset__()
            for parser in self.all_parsers__:
                parser.reset()
        else:
            self._dirty_flag__ = True
        self.history_tracking__ = is_logging()
        self.document__ = StringView(document)
        self.document_length__ = len(self.document__)
        self.document_lbreaks__ = linebreaks(document) if self.history_tracking__ else []
        self.last_rb__loc__ = -1  # rollback location
        parser = self[start_parser] if isinstance(start_parser, str) else start_parser
        assert parser.grammar == self, "Cannot run parsers from a different grammar object!" \
                                       " %s vs. %s" % (str(self), str(parser.grammar))
        result = None  # type: Optional[Node]
        stitches = []  # type: List[Node]
        rest = self.document__
        if not rest:
            result, _ = parser(rest)
            if result is None:
                result = Node(None, '').init_pos(0)
                result.add_error('Parser "%s" did not match empty document.' % str(parser))
        while rest and len(stitches) < MAX_DROPOUTS:
            result, rest = parser(rest)
            if rest:
                fwd = rest.find("\n") + 1 or len(rest)
                skip, rest = rest[:fwd], rest[fwd:]
                if result is None:
                    error_msg = 'Parser did not match! Invalid source file?' \
                                '\n    Most advanced: %s\n    Last match:    %s;' % \
                                (str(HistoryRecord.most_advanced_match(self.history__)),
                                 str(HistoryRecord.last_match(self.history__)))
                else:
                    stitches.append(result)
                    error_msg = "Parser stopped before end" + \
                                (("! trying to recover" +
                                  (" but stopping history recording at this point."
                                   if self.history_tracking__ else "..."))
                                 if len(stitches) < MAX_DROPOUTS
                                 else " too often! Terminating parser.")
                stitches.append(Node(None, skip).init_pos(tail_pos(stitches)))
                stitches[-1].add_error(error_msg)
                if self.history_tracking__:
                    # # some parsers may have matched and left history records with nodes != None.
                    # # Because these are not connected to the stitched root node, their pos-
                    # # properties will not be initialized by setting the root node's pos property
                    # # to zero. Therefore, their pos properties need to be initialized here
                    # for record in self.history__:
                    #     if record.node and record.node._pos < 0:
                    #         record.node.init_pos(0)
                    record = HistoryRecord(self.call_stack__.copy(), stitches[-1], rest)
                    self.history__.append(record)
                    # stop history tracking when parser returned too early
                    self.history_tracking__ = False
        if stitches:
            if rest:
                stitches.append(Node(None, rest))
            result = Node(None, tuple(stitches)).init_pos(0)
        if any(self.variables__.values()):
            error_str = "Capture-retrieve-stack not empty after end of parsing: " + \
                            str(self.variables__)
            if result:
                if result.children:
                    # add another child node at the end to ensure that the position
                    # of the error will be the end of the text. Otherwise, the error
                    # message above ("...after end of parsing") would appear illogical.
                    error_node = Node(ZOMBIE_PARSER, '').init_pos(tail_pos(result.children))
                    error_node.add_error(error_str)
                    result.result = result.children + (error_node,)
                else:
                    result.add_error(error_str)
        # result.pos = 0  # calculate all positions
        # result.collect_errors(self.document__)
        return result


    def push_rollback__(self, location, func):
        """
        Adds a rollback function that either removes or re-adds
        values on the variable stack (`self.variables`) that have been
        added (or removed) by Capture or Pop Parsers, the results of
        which have been dismissed.
        """
        self.rollback__.append((location, func))
        self.last_rb__loc__ = location


    def rollback_to__(self, location):
        """
        Rolls back the variable stacks (`self.variables`) to its
        state at an earlier location in the parsed document.
        """
        while self.rollback__ and self.rollback__[-1][0] >= location:
            _, rollback_func = self.rollback__.pop()
            # assert not loc > self.last_rb__loc__, \
            #     "Rollback confusion: line %i, col %i < line %i, col %i" % \
            #     (*line_col(self.document__, len(self.document__) - loc),
            #      *line_col(self.document__, len(self.document__) - self.last_rb__loc__))
            rollback_func()
        self.last_rb__loc__ == self.rollback__[-1][0] if self.rollback__ \
            else (len(self.document__) + 1)


    def log_parsing_history__(self, log_file_name: str = '', html: bool=True) -> None:
        """
        Writes a log of the parsing history of the most recently parsed
        document.
        """
        def write_log(history, log_name):
            htm = '.html' if html else ''
            path = os.path.join(log_dir(), log_name + "_parser.log" + htm)
            if os.path.exists(path):
                os.remove(path)
                print('WARNING: Log-file "%s" already existed and was deleted.' % path)
            if history:
                with open(path, "w", encoding="utf-8") as f:
                    if html:
                        f.write(HistoryRecord.HTML_LEAD_IN)
                        f.write("\n".join(history))
                        f.write(HistoryRecord.HTML_LEAD_OUT)
                    else:
                        f.write("\n".join(history))

        def append_line(log, line):
            """Appends a line to a list of HTML table rows. Starts a new
            table every 100 rows to allow browser to speed up rendering.
            Does this really work...?"""
            log.append(line)
            if html and len(log) % 100 == 0:
                log.append('\n</table>\n<table>\n' + HistoryRecord.COLGROUP)

        if not is_logging():
            raise AssertionError("Cannot log history when logging is turned off!")
        # assert self.history__, \
        #     "Parser did not yet run or logging was turned off when running parser!"
        if not log_file_name:
            name = self.__class__.__name__
            log_file_name = name[:-7] if name.lower().endswith('grammar') else name
        elif log_file_name.lower().endswith('.log'):
            log_file_name = log_file_name[:-4]
        full_history = []  # type: List[str]
        match_history = []  # type: List[str]
        errors_only = []  # type: List[str]
        for record in self.history__:
            line = record.as_html_tr() if html else str(record)
            append_line(full_history, line)
            if record.node and record.node.parser.ptype != WHITESPACE_PTYPE:
                append_line(match_history, line)
                if record.node.error_flag:
                    append_line(errors_only, line)
        write_log(full_history, log_file_name + '_full')
        if len(full_history) > 250:
            write_log(full_history[-200:], log_file_name + '_full.tail')
        write_log(match_history, log_file_name + '_match')
        write_log(errors_only, log_file_name + '_errors')


def dsl_error_msg(parser: Parser, error_str: str) -> str:
    """
    Returns an error message for errors in the parser configuration,
    e.g. errors that result in infinite loops.

    Args:
        parser (Parser):  The parser where the error was noticed. Note
            that this is not necessarily the parser that caused the
            error but only where the error became apparent.
        error_str (str):  A short string describing the error.
    Returns:
        str: An error message including the call stack if history
        tacking has been turned in the grammar object.
    """
    msg = ["DSL parser specification error:", error_str, 'Caught by parser "%s".' % str(parser)]
    if parser.grammar.history__:
        msg.extend(["\nCall stack:", parser.grammar.history__[-1].stack])
    else:
        msg.extend(["\nEnable history tracking in Grammar object to display call stack."])
    return " ".join(msg)


########################################################################
#
# Token and Regular Expression parser classes (i.e. leaf classes)
#
########################################################################


class PreprocessorToken(Parser):
    """
    Parses tokens that have been inserted by a preprocessor.

    Preprocessors can generate Tokens with the ``make_token``-function.
    These tokens start and end with magic characters that can only be
    matched by the PreprocessorToken Parser. Such tokens can be used to
    insert BEGIN - END delimiters at the beginning or ending of a
    quoted block, for example.
    """

    def __init__(self, token: str) -> None:
        assert token and token.isupper()
        assert RX_TOKEN_NAME.match(token)
        super().__init__(token)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        if text[0:1] == BEGIN_TOKEN:
            end = text.find(END_TOKEN, 1)
            if end < 0:
                node = Node(self, '').add_error(
                    'END_TOKEN delimiter missing from preprocessor token. '
                    '(Most likely due to a preprocessor bug!)')  # type: Node
                return node, text[1:]
            elif end == 0:
                node = Node(self, '').add_error(
                    'Preprocessor-token cannot have zero length. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[2:]
            elif text.find(BEGIN_TOKEN, 1, end) >= 0:
                node = Node(self, text[len(self.name) + 1:end])
                node.add_error(
                    'Preprocessor-tokens must not be nested or contain '
                    'BEGIN_TOKEN delimiter as part of their argument. '
                    '(Most likely due to a preprocessor bug!)')
                return node, text[end:]
            if text[1:len(self.name) + 1] == self.name:
                return Node(self, text[len(self.name) + 2:end]), text[end + 1:]
        return None, text


class PlainText(Parser):
    """
    Parses plain text strings. (Could be done by RegExp as well, but is faster.)

    Example:
    >>> while_token = PlainText("while")
    >>> Grammar(while_token)("while").content
    'while'
    """

    def __init__(self, text: str, name: str = '') -> None:
        super().__init__(name)
        self.text = text
        self.len = len(text)

    def __deepcopy__(self, memo):
        return self.__class__(self.text, self.name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        if text.startswith(self.text):
            return Node(self, self.text, True), text[self.len:]
        return None, text


class RegExp(Parser):
    r"""
    Regular expression parser.

    The RegExp-parser parses text that matches a regular expression.
    RegExp can also be considered as the "atomic parser", because all
    other parsers delegate part of the parsing job to other parsers,
    but do not match text directly.

    Example:
    >>> word = RegExp(r'\w+')
    >>> Grammar(word)("Haus").content
    'Haus'

    EBNF-Notation:  `/ ... /`
    EBNF-Example:   `word = /\w+/`
    """

    def __init__(self, regexp, name: str = '') -> None:
        super().__init__(name)
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def __deepcopy__(self, memo):
        # `regex` supports deep copies, but not `re`
        try:
            regexp = copy.deepcopy(self.regexp, memo)
        except TypeError:
            regexp = self.regexp.pattern
        return self.__class__(regexp, self.name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        match = text.match(self.regexp)
        if match:
            capture = match.group(0)
            end = text.index(match.end())
            # regular expression must never match preprocessor-tokens!
            # TODO: Find a better solution here? e.g. static checking/re-mangling at compile time
            i = capture.find(BEGIN_TOKEN)
            if i >= 0:
                capture = capture[:i]
                end = i
            return Node(self, capture, True), text[end:]
        return None, text

    def __repr__(self):
        return escape_control_characters('/%s/' % self.regexp.pattern)


class Whitespace(RegExp):
    """An variant of RegExp that signifies through its class name that it
    is a RegExp-parser for whitespace."""
    assert WHITESPACE_PTYPE == ":Whitespace"


class RE(Parser):
    r"""
    Regular Expressions with optional leading or trailing whitespace.

    The RE-parser parses pieces of text that match a given regular
    expression. Other than the ``RegExp``-Parser it can also skip
    "implicit whitespace" before or after the matched text.

    The whitespace is in turn defined by a regular expression. It should
    be made sure that this expression also matches the empty string,
    e.g. use r'\s*' or r'[\t ]+', but not r'\s+'. If the respective
    parameters in the constructor are set to ``None`` the default
    whitespace expression from the Grammar object will be used.

    Example (allowing whitespace on the right hand side, but not on
    the left hand side of a regular expression):
    >>> word = RE(r'\w+', wR=r'\s*')
    >>> parser = Grammar(word)
    >>> result = parser('Haus ')
    >>> result.content
    'Haus '
    >>> result.structure
    '(:RE (:RegExp "Haus") (:Whitespace " "))'
    >>> str(parser(' Haus'))
    ' <<< Error on " Haus" | Parser did not match! Invalid source file?\n    Most advanced: None\n    Last match:    None; >>> '

    EBNF-Notation:  `/ ... /~`  or  `~/ ... /`  or  `~/ ... /~`
    EBNF-Example:   `word = /\w+/~`
    """

    def __init__(self, regexp, wL=None, wR=None, name: str='') -> None:
        r"""Constructor for class RE.

        Args:
            regexp (str or regex object):  The regular expression to be
                used for parsing.
            wL (str or regexp):  Left whitespace regular expression,
                i.e. either ``None``, the empty string or a regular
                expression (e.g. "\s*") that defines whitespace. An
                empty string means no whitespace will be skipped,
                ``None`` means that the default whitespace will be
                used.
            wR (str or regexp):  Right whitespace regular expression.
                See above.
            name:  The optional name of the parser.
        """
        super().__init__(name)
        self.rx_wsl = wL
        self.rx_wsr = wR
        self.wsp_left = Whitespace(wL) if wL else ZOMBIE_PARSER
        self.wsp_right = Whitespace(wR) if wR else ZOMBIE_PARSER
        self.main = self.create_main_parser(regexp)

    def __deepcopy__(self, memo={}):
        try:
            regexp = copy.deepcopy(self.main.regexp, memo)
        except TypeError:
            regexp = self.main.regexp.pattern
        return self.__class__(regexp, self.rx_wsl, self.rx_wsr, self.name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        # assert self.main.regexp.pattern != "@"
        txt = text    # type: StringView
        wsl, txt = self.wsp_left(txt)
        main, txt = self.main(txt)
        if main:
            wsr, txt = self.wsp_right(txt)
            result = tuple(nd for nd in (wsl, main, wsr) if nd)
            return Node(self, result), txt
        return None, text

    def __repr__(self):
        wsl = '~' if self.wsp_left != ZOMBIE_PARSER else ''
        wsr = '~' if self.wsp_right != ZOMBIE_PARSER else ''
        return wsl + '/%s/' % self.main.regexp.pattern + wsr

    def _grammar_assigned_notifier(self):
        if self.grammar:
            # use default whitespace parsers if not otherwise specified
            if self.rx_wsl is None:
                self.wsp_left = self.grammar.wsp_left_parser__
            if self.rx_wsr is None:
                self.wsp_right = self.grammar.wsp_right_parser__

    def apply(self, func: Parser.ApplyFunc) -> bool:
        if super().apply(func):
            if self.rx_wsl:
                self.wsp_left.apply(func)
            if self.rx_wsr:
                self.wsp_right.apply(func)
            self.main.apply(func)
            return True
        return False

    def create_main_parser(self, arg) -> Parser:
        """Creates the main parser of this compound parser. Can be overridden."""
        return RegExp(arg)


class Token(RE):
    """
    Class Token parses simple strings. Any regular regular expression
    commands will be interpreted as simple sequence of characters.

    Other than that class Token is essentially a renamed version of
    class RE. Because tokens often have a particular semantic different
    from other REs, parsing them with a separate parser class allows to
    distinguish them by their parser type.
    """
    assert TOKEN_PTYPE == ":Token"

    def __init__(self, token: str, wL=None, wR=None, name: str = '') -> None:
        self.token = token
        super().__init__(token, wL, wR, name)

    def __deepcopy__(self, memo={}):
        return self.__class__(self.token, self.rx_wsl, self.rx_wsr, self.name)

    def __repr__(self):
        return '"%s"' % self.token if self.token.find('"') < 0 else "'%s'" % self.token

    def create_main_parser(self, arg) -> Parser:
        return PlainText(arg)


########################################################################
#
# Containing parser classes, i.e. parsers that contain other parsers
# to which they delegate parsing
#
########################################################################


class UnaryOperator(Parser):
    """
    Base class of all unary parser operators, i.e. parser that contains
    one and only one other parser, like the optional parser for example.

    The UnaryOperator base class supplies __deepcopy__ and apply
    methods for unary parser operators. The __deepcopy__ method needs
    to be overwritten, however, if the constructor of a derived class
    has additional parameters.
    """

    def __init__(self, parser: Parser, name: str = '') -> None:
        super(UnaryOperator, self).__init__(name)
        assert isinstance(parser, Parser), str(parser)
        self.parser = parser  # type: Parser

    def __deepcopy__(self, memo):
        parser = copy.deepcopy(self.parser, memo)
        return self.__class__(parser, self.name)

    def apply(self, func: Parser.ApplyFunc) -> bool:
        if super().apply(func):
            self.parser.apply(func)
            return True
        return False


class NaryOperator(Parser):
    """
    Base class of all Nnary parser operators, i.e. parser that
    contains one or more other parsers, like the alternative
    parser for example.

    The NnaryOperator base class supplies __deepcopy__ and apply methods
    for unary parser operators. The __deepcopy__ method needs to be
    overwritten, however, if the constructor of a derived class has
    additional parameters.
    """

    def __init__(self, *parsers: Parser, name: str = '') -> None:
        super().__init__(name)
        assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        self.parsers = parsers  # type: Tuple[Parser, ...]

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        return self.__class__(*parsers, name=self.name)

    def apply(self, func: Parser.ApplyFunc) -> bool:
        if super().apply(func):
            for parser in self.parsers:
                parser.apply(func)
            return True
        return False


class Option(UnaryOperator):
    r"""
    Parser `Optional` always matches, even if its child-parser
    did not match.

    If the child-parser did not match `Optional` returns a node
    with no content and does not move forward in the text.

    If the child-parser did match, `Optional` returns the a node
    with the node returnd by the child-parser as its single
    child and the text at the position where the child-parser
    left it.

    Examples:
    >>> number = Option(Token('-')) + RegExp(r'\d+') + Option(RegExp(r'\.\d+'))
    >>> Grammar(number)('3.14159').content
    '3.14159'
    >>> Grammar(number)('3.14159').structure
    '(:Series (:Option) (:RegExp "3") (:Option (:RegExp ".14159")))'
    >>> Grammar(number)('-1').content
    '-1'

    EBNF-Notation: `[ ... ]`
    EBNF-Example:  `number = ["-"]  /\d+/  [ /\.\d+/ ]
    """

    def __init__(self, parser: Parser, name: str = '') -> None:
        super().__init__(parser, name)
        # assert isinstance(parser, Parser)
        assert not isinstance(parser, Option), \
            "Redundant nesting of options: %s(%s)" % (str(name), str(parser.name))
        # assert not isinstance(parser, Required), \
        #     "Nesting options with required elements is contradictory: " \
        #     "%s(%s)" % (str(name), str(parser.name))

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, text = self.parser(text)
        if node:
            return Node(self, node), text
        return Node(self, ()), text

    def __repr__(self):
        return '[' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.name else self.parser.repr) + ']'


class ZeroOrMore(Option):
    r"""
    `ZeroOrMore` applies a parser repeatedly as long as this parser
    matches. Like `Option` the `ZeroOrMore` parser always matches. In
    case of zero repetitions, the empty match `((), text)` is returned.

    Examples:
    >>> sentence = ZeroOrMore(RE(r'\w+,?')) + Token('.')
    >>> Grammar(sentence)('Wo viel der Weisheit, da auch viel des Grämens.').content
    'Wo viel der Weisheit, da auch viel des Grämens.'
    >>> Grammar(sentence)('.').content  # an empty sentence also matches
    '.'

    EBNF-Notation: `{ ... }`
    EBNF-Example:  `sentence = { /\w+,?/ } "."`
    """

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        n = len(text) + 1
        while text and len(text) < n:
            n = len(text)
            node, text = self.parser(text)
            if not node:
                break
            if len(text) == n:
                node.add_error(dsl_error_msg(self, 'Infinite Loop detected.'))
            results += (node,)
        return Node(self, results), text

    def __repr__(self):
        return '{' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.name else self.parser.repr) + '}'


class OneOrMore(UnaryOperator):
    r"""
    `OneOrMore` applies a parser repeatedly as long as this parser
    matches. Other than `ZeroOrMore` which always matches, at least
    one match is required by `OneOrMore`.

    Examples:
    >>> sentence = OneOrMore(RE(r'\w+,?')) + Token('.')
    >>> Grammar(sentence)('Wo viel der Weisheit, da auch viel des Grämens.').content
    'Wo viel der Weisheit, da auch viel des Grämens.'
    >>> str(Grammar(sentence)('.'))  # an empty sentence also matches
    ' <<< Error on "." | Parser did not match! Invalid source file?\n    Most advanced: None\n    Last match:    None; >>> '

    EBNF-Notation: `{ ... }+`
    EBNF-Example:  `sentence = { /\w+,?/ }+`
    """

    def __init__(self, parser: Parser, name: str = '') -> None:
        super().__init__(parser, name)
        assert not isinstance(parser, Option), \
            "Use ZeroOrMore instead of nesting OneOrMore and Option: " \
            "%s(%s)" % (str(name), str(parser.name))

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        n = len(text) + 1
        while text_ and len(text_) < n:
            n = len(text_)
            node, text_ = self.parser(text_)
            if not node:
                break
            if len(text_) == n:
                node.add_error(dsl_error_msg(self, 'Infinite Loop detected.'))
            results += (node,)
        if results == ():
            return None, text
        return Node(self, results), text_

    def __repr__(self):
        return '{' + (self.parser.repr[1:-1] if isinstance(self.parser, Alternative)
                      and not self.parser.name else self.parser.repr) + '}+'


class Series(NaryOperator):
    r"""
    Matches if each of a series of parsers matches exactly in the order of
    the series.

    Example:
    >>> variable_name = RegExp('(?!\d)\w') + RE('\w*')
    >>> Grammar(variable_name)('variable_1').content
    'variable_1'
    >>> str(Grammar(variable_name)('1_variable'))
    ' <<< Error on "1_variable" | Parser did not match! Invalid source file?\n    Most advanced: None\n    Last match:    None; >>> '

    EBNF-Notation: `... ...`    (sequence of parsers separated by a blank or new line)
    EBNF-Example:  `series = letter letter_or_digit`
    """
    RX_ARGUMENT = re.compile(r'\s(\S)')
    NOPE = 1000

    def __init__(self, *parsers: Parser, mandatory: int = NOPE, name: str = '') -> None:
        super().__init__(*parsers, name=name)
        length = len(self.parsers)
        assert 1 <= length < Series.NOPE, \
            'Length %i of series exceeds maximum length of %i' % (length, Series.NOPE)
        if mandatory < 0:
            mandatory += length
        assert 0 <= mandatory < length or mandatory == Series.NOPE
        self.mandatory = mandatory

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        return self.__class__(*parsers, mandatory=self.mandatory, name=self.name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        pos = 0
        for parser in self.parsers:
            node, text_ = parser(text_)
            if not node:
                if pos < self.mandatory:
                    return None, text
                else:
                    # Provide useful error messages
                    match = text.search(Series.RX_ARGUMENT)
                    i = max(1, text.index(match.regs[1][0])) if match else 1
                    node = Node(self, text_[:i]).init_pos(self.grammar.document_length__ - len(text_))
                    node.add_error('%s expected; "%s"... found!'
                                   % (str(parser), text_[:10].replace('\n', '\\n ')),
                                   code=Error.MANDATORY_CONTINUATION)
                    text_ = text_[i:]
            results += (node,)
            # if node.error_flag:  # break on first error
            #    break
            pos += 1
        assert len(results) <= len(self.parsers)
        return Node(self, results), text_

    def __repr__(self):
        return " ".join([parser.repr for parser in self.parsers[:self.mandatory]]
                        + (['§'] if self.mandatory != Series.NOPE else [])
                        + [parser.repr for parser in self.parsers[self.mandatory:]])

    # The following operator definitions add syntactical sugar, so one can write:
    # `RE('\d+') + Optional(RE('\.\d+)` instead of `Series(RE('\d+'), Optional(RE('\.\d+))`

    @staticmethod
    def combined_mandatory(left: Parser, right: Parser):
        """
        Returns the position of the first mandatory element (if any) when
        parsers `left` and `right` are joined to a sequence.
        """
        left_mandatory, left_length = (left.mandatory, len(left.parsers)) \
            if isinstance(left, Series) else (Series.NOPE, 1)
        if left_mandatory != Series.NOPE:
            return left_mandatory
        right_mandatory = right.mandatory if isinstance(right, Series) else Series.NOPE
        if right_mandatory != Series.NOPE:
            return right_mandatory + left_length
        return Series.NOPE

    def __add__(self, other: Parser) -> 'Series':
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
                        else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Series(*(self.parsers + other_parsers),
                      mandatory=self.combined_mandatory(self, other))

    def __radd__(self, other: Parser) -> 'Series':
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
                        else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Series(*(other_parsers + self.parsers),
                      mandatory=self.combined_mandatory(other, self))

    def __iadd__(self, other: Parser) -> 'Series':
        other_parsers = cast('Series', other).parsers if isinstance(other, Series) \
                        else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        self.parsers += other_parsers
        self.mandatory = self.combined_mandatory(self, other)
        return self


class Alternative(NaryOperator):
    r"""
    Matches if one of several alternatives matches. Returns
    the first match.

    This parser represents the EBNF-operator "|" with the qualification
    that both the symmetry and the ambiguity of the EBNF-or-operator
    are broken by selecting the first match.

    # the order of the sub-expression matters!
    >>> number = RE('\d+') | RE('\d+') + RE('\.') + RE('\d+')
    >>> str(Grammar(number)("3.1416"))
    '3 <<< Error on ".141" | Parser stopped before end! trying to recover... >>> '

    # the most selective expression should be put first:
    >>> number = RE('\d+') + RE('\.') + RE('\d+') | RE('\d+')
    >>> Grammar(number)("3.1416").content
    '3.1416'

    EBNF-Notation: `... | ...`
    EBNF-Example:  `sentence = /\d+\.\d+/ | /\d+/`
    """

    def __init__(self, *parsers: Parser, name: str = '') -> None:
        super().__init__(*parsers, name=name)
        assert len(self.parsers) >= 1
        # only the last alternative may be optional. Could this be checked at compile time?
        assert all(not isinstance(p, Option) for p in self.parsers[:-1]), \
            "Parser-specification Error: only the last alternative may be optional!"

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        for parser in self.parsers:
            node, text_ = parser(text)
            if node:
                return Node(self, node), text_
        return None, text

    def __repr__(self):
        return '(' + ' | '.join(parser.repr for parser in self.parsers) + ')'

    def reset(self):
        super(Alternative, self).reset()
        return self

    # The following operator definitions add syntactical sugar, so one can write:
    # `RE('\d+') + RE('\.') + RE('\d+') | RE('\d+')` instead of:
    # `Alternative(Series(RE('\d+'), RE('\.'), RE('\d+')), RE('\d+'))`

    def __or__(self, other: Parser) -> 'Alternative':
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
                        else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Alternative(*(self.parsers + other_parsers))

    def __ror__(self, other: Parser) -> 'Alternative':
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
                        else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        return Alternative(*(other_parsers + self.parsers))

    def __ior__(self, other: Parser) -> 'Alternative':
        other_parsers = cast('Alternative', other).parsers if isinstance(other, Alternative) \
                        else cast(Tuple[Parser, ...], (other,))  # type: Tuple[Parser, ...]
        self.parsers += other_parsers
        return self


class AllOf(NaryOperator):
    """
    Matches if all elements of a list of parsers match. Each parser must
    match exactly once. Other than in a sequence, the order in which
    the parsers match is arbitrary, however.

    Example:
    >>> prefixes = AllOf(Token("A"), Token("B"))
    >>> Grammar(prefixes)('A B').content
    'A B'
    >>> Grammar(prefixes)('B A').content
    'B A'

    EBNF-Notation: `<... ...>`    (sequence of parsers enclosed by angular brackets)
    EBNF-Example:  `set = <letter letter_or_digit>`
    """

    def __init__(self, *parsers: Parser, name: str = '') -> None:
        if len(parsers) == 1 and isinstance(parsers[0], Series):
            assert isinstance(parsers[0], Series), \
                "Parser-specification Error: No single arguments other than a Series " \
                "allowed as arguments for AllOf-Parser !"
            series = cast(Series, parsers[0])
            assert series.mandatory == Series.NOPE, \
                "AllOf cannot contain mandatory (§) elements!"
            parsers = series.parsers
        super().__init__(*parsers, name=name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        parsers = list(self.parsers)  # type: List[Parser]
        while parsers:
            for i, parser in enumerate(parsers):
                node, text__ = parser(text_)
                if node:
                    results += (node,)
                    text_ = text__
                    del parsers[i]
                    break
            else:
                return None, text
        assert len(results) <= len(self.parsers)
        return Node(self, results), text_

    def __repr__(self):
        return '<' + ' '.join(parser.repr for parser in self.parsers) + '>'


class SomeOf(NaryOperator):
    """
    Matches if at least one element of a list of parsers match. No parser
    must match more than once . Other than in a sequence, the order in which
    the parsers match is arbitrary, however.

    Example:
    >>> prefixes = SomeOf(Token("A"), Token("B"))
    >>> Grammar(prefixes)('A B').content
    'A B'
    >>> Grammar(prefixes)('B A').content
    'B A'
    >>> Grammar(prefixes)('B').content
    'B'

    EBNF-Notation: `<... ...>`    (sequence of parsers enclosed by angular brackets)
    EBNF-Example:  `set = <letter letter_or_digit>`
    """

    def __init__(self, *parsers: Parser, name: str = '') -> None:
        if len(parsers) == 1:
            assert isinstance(parsers[0], Alternative), \
                "Parser-specification Error: No single arguments other than a Alternative " \
                "allowed as arguments for SomeOf-Parser !"
            alternative = cast(Alternative, parsers[0])
            parsers = alternative.parsers
        super().__init__(*parsers, name=name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        results = ()  # type: Tuple[Node, ...]
        text_ = text  # type: StringView
        parsers = list(self.parsers)  # type: List[Parser]
        while parsers:
            for i, parser in enumerate(parsers):
                node, text__ = parser(text_)
                if node:
                    results += (node,)
                    text_ = text__
                    del parsers[i]
                    break
            else:
                parsers = []
        assert len(results) <= len(self.parsers)
        if results:
            return Node(self, results), text_
        else:
            return None, text

    def __repr__(self):
        return '<' + ' | '.join(parser.repr for parser in self.parsers) + '>'


def Unordered(parser: NaryOperator, name: str = '') -> NaryOperator:
    """
    Returns an AllOf- or SomeOf-parser depending on whether `parser`
    is a Series (AllOf) or an Alternative (SomeOf).
    """
    if isinstance(parser, Series):
        return AllOf(parser, name=name)
    elif isinstance(parser, Alternative):
        return SomeOf(parser, name=name)
    else:
        raise AssertionError("Unordered can take only Series or Alternative as parser.")


########################################################################
#
# Flow control operators
#
########################################################################

class FlowOperator(UnaryOperator):
    """
    Base class for all flow operator parsers like Lookahead and Lookbehind.
    """
    def sign(self, bool_value) -> bool:
        """Returns the value. Can be overriden to return the inverted bool."""
        return bool_value


# class Required(FlowOperator):
#     """OBSOLETE. Use mandatory-parameter of Series-parser instead!
#     """
#     RX_ARGUMENT = re.compile(r'\s(\S)')
#
#     def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
#         node, text_ = self.parser(text)
#         if not node:
#             m = text.search(Required.RX_ARGUMENT)  # re.search(r'\s(\S)', text)
#             i = max(1, text.index(m.regs[1][0])) if m else 1
#             node = Node(self, text[:i])
#             text_ = text[i:]
#             node.add_error('%s expected; "%s" found!' % (str(self.parser), text[:10]),
#                            code=Error.MANDATORY_CONTINUATION)
#         return node, text_
#
#     def __repr__(self):
#         return '§' + self.parser.repr


class Lookahead(FlowOperator):
    """
    Matches, if the contained parser would match for the following text,
    but does not consume any text.
    """
    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, _ = self.parser(text)
        if self.sign(node is not None):
            return Node(self, ''), text
        else:
            return None, text

    def __repr__(self):
        return '&' + self.parser.repr


class NegativeLookahead(Lookahead):
    """
    Matches, if the contained parser would *not* match for the following
    text.
    """
    def __repr__(self):
        return '!' + self.parser.repr

    def sign(self, bool_value) -> bool:
        return not bool_value


class Lookbehind(FlowOperator):
    """
    Matches, if the contained parser would match backwards. Requires
    the contained parser to be a RegExp, Re, PlainText or Token parser.
    """
    def __init__(self, parser: Parser, name: str = '') -> None:
        p = parser
        while isinstance(p, Synonym):
            p = p.parser
        assert isinstance(p, RegExp) or isinstance(p, PlainText) or isinstance(p, RE), str(type(p))
        self.regexp = None
        self.text = None
        if isinstance(p, RE):
            if isinstance(cast(RE, p).main, RegExp):
                self.regexp = cast(RegExp, cast(RE, p).main).regexp
            else:  # p.main is of type PlainText
                self.text = cast(PlainText, cast(RE, p).main).text
        elif isinstance(p, RegExp):
            self.regexp = cast(RegExp, p).regexp
        else:  # p is of type PlainText
            self.text = cast(PlainText, p).text
        super().__init__(parser, name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        backwards_text = self.grammar.reversed__[len(text):]
        if self.regexp is None:  # assert self.text is not None
            does_match = backwards_text[:len(self.text)] == self.text
        else:  # assert self.regexp is not None
            does_match = backwards_text.match(self.regexp)
        return (Node(self, ''), text) if self.sign(does_match) else (None, text)

    def __repr__(self):
        return '-&' + self.parser.repr


class NegativeLookbehind(Lookbehind):
    """
    Matches, if the contained parser would *not* match backwards. Requires
    the contained parser to be a RegExp-parser.
    """
    def __repr__(self):
        return '-!' + self.parser.repr

    def sign(self, bool_value) -> bool:
        return not bool(bool_value)


########################################################################
#
# Capture and Retrieve operators (for passing variables in the parser)
#
########################################################################


class Capture(UnaryOperator):
    """
    Applies the contained parser and, in case of a match, saves the result
    in a variable. A variable is a stack of values associated with the
    contained parser's name. This requires the contained parser to be named.
    """
    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, text_ = self.parser(text)
        if node:
            assert self.name, """Tried to apply an unnamed capture-parser!"""
            stack = self.grammar.variables__.setdefault(self.name, [])
            stack.append(node.content)
            location = self.grammar.document_length__ - len(text)
            self.grammar.push_rollback__(location, lambda: stack.pop())
            # caching will be blocked by parser guard (see way above),
            # because it would prevent recapturing of rolled back captures
            return Node(self, node), text_
        else:
            return None, text

    def __repr__(self):
        return self.parser.repr


RetrieveFilter = Callable[[List[str]], str]


def last_value(stack: List[str]) -> str:
    return stack[-1]


def counterpart(stack: List[str]) -> str:
    value = stack[-1]
    return value.replace("(", ")").replace("[", "]").replace("{", "}").replace("<", ">")


def accumulate(stack: List[str]) -> str:
    return "".join(stack) if len(stack) > 1 else stack[-1]  # provoke IndexError if stack empty


class Retrieve(Parser):
    """
    Matches if the following text starts with the value of a particular
    variable. As a variable in this context means a stack of values,
    the last value will be compared with the following text. It will not
    be removed from the stack! (This is the difference between the
    `Retrieve` and the `Pop` parser.)
    The constructor parameter `symbol` determines which variable is
    used.
    """

    def __init__(self, symbol: Parser, rfilter: RetrieveFilter = None, name: str = '') -> None:
        super(Retrieve, self).__init__(name)
        self.symbol = symbol
        self.filter = rfilter if rfilter else last_value

    def __deepcopy__(self, memo):
        return self.__class__(self.symbol, self.filter, self.name)

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        # the following indirection allows the call() method to be called
        # from subclass without triggering the parser guard a second time
        return self.retrieve_and_match(text)

    def __repr__(self):
        return ':' + self.symbol.repr

    def retrieve_and_match(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        """
        Retrieves variable from stack through the filter function passed to
        the class' constructor and tries to match the variable's value with
        the following text. Returns a Node containing the value or `None`
        accordingly.

        This functionality has been move from the __call__ method to an
        independent method to allow calling it from a subclasses __call__
        method without triggering the parser guard a second time.
        """
        try:
            stack = self.grammar.variables__[self.symbol.name]
            value = self.filter(stack)
        except (KeyError, IndexError):
            return Node(self, '').add_error(
                dsl_error_msg(self, "'%s' undefined or exhausted." % self.symbol.name)), text
        if text.startswith(value):
            return Node(self, value), text[len(value):]
        else:
            return None, text


class Pop(Retrieve):
    """
    Matches if the following text starts with the value of a particular
    variable. As a variable in this context means a stack of values,
    the last value will be compared with the following text. Other
    than the `Retrieve`-parser, the `Pop`-parser removes the value
    from the stack in case of a match.

    The constructor parameter `symbol` determines which variable is
    used.
    """

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, txt = super().retrieve_and_match(text)
        if node and not node.error_flag:
            stack = self.grammar.variables__[self.symbol.name]
            value = stack.pop()
            location = self.grammar.document_length__ - len(text)
            self.grammar.push_rollback__(location, lambda: stack.append(value))
        return node, txt

    def __repr__(self):
        return '::' + self.symbol.repr


########################################################################
#
# Aliasing parser classes
#
########################################################################


class Synonym(UnaryOperator):
    r"""
    Simply calls another parser and encapsulates the result in
    another node if that parser matches.

    This parser is needed to support synonyms in EBNF, e.g.
        jahr       = JAHRESZAHL
        JAHRESZAHL = /\d\d\d\d/
    Otherwise the first line could not be represented by any parser
    class, in which case it would be unclear whether the parser
    RE('\d\d\d\d') carries the name 'JAHRESZAHL' or 'jahr'.
    """

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        node, text = self.parser(text)
        if node:
            return Node(self, node), text
        return None, text

    def __repr__(self):
        return self.name or self.parser.repr


class Forward(Parser):
    r"""
    Forward allows to declare a parser before it is actually defined.
    Forward declarations are needed for parsers that are recursively
    nested, e.g.:
    class Arithmetic(Grammar):
        '''
        expression =  term  { ("+" | "-") term }
        term       =  factor  { ("*" | "/") factor }
        factor     =  INTEGER | "("  expression  ")"
        INTEGER    =  /\d+/~
        '''
        expression = Forward()
        INTEGER    = RE('\\d+')
        factor     = INTEGER | Token("(") + expression + Token(")")
        term       = factor + ZeroOrMore((Token("*") | Token("/")) + factor)
        expression.set(term + ZeroOrMore((Token("+") | Token("-")) + term))
        root__     = expression
    """

    def __init__(self):
        Parser.__init__(self)
        self.parser = None
        self.cycle_reached = False

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        memo[id(self)] = duplicate
        parser = copy.deepcopy(self.parser, memo)
        duplicate.set(parser)
        return duplicate

    def __call__(self, text: StringView) -> Tuple[Optional[Node], StringView]:
        return self.parser(text)

    def __cycle_guard(self, func, alt_return):
        """
        Returns the value of `func()` or `alt_return` if a cycle has
        been reached (which can happen if `func` calls methods of
        child parsers).
        """
        if self.cycle_reached:
            return alt_return
        else:
            self.cycle_reached = True
            ret = func()
            self.cycle_reached = False
            return ret

    def __repr__(self):
        return self.__cycle_guard(lambda: repr(self.parser), '...')

    def __str__(self):
        return self.__cycle_guard(lambda: str(self.parser), '...')

    def set(self, parser: Parser):
        """
        Sets the parser to which the calls to this Forward-object
        shall be delegated.
        """
        self.parser = parser

    def apply(self, func: Parser.ApplyFunc) -> bool:
        if super().apply(func):
            self.parser.apply(func)
            return True
        return False


#######################################################################
#
# Syntax driven compilation support
#
#######################################################################


class Compiler:
    """
    Class Compiler is the abstract base class for compilers. Compiler
    objects are callable and take the root node of the abstract
    syntax tree (AST) as argument and return the compiled code in a
    format chosen by the compiler itself.

    Subclasses implementing a compiler must define `on_XXX()`-methods
    for each node name that can occur in the AST where 'XXX' is the
    node's name(for unnamed nodes it is the node's ptype without the
    leading colon ':').

    These compiler methods take the node on which they are run as
    argument. Other than in the AST transformation, which runs depth-first,
    compiler methods are called forward moving starting with the root
    node, and they are responsible for compiling the child nodes
    themselves. This should be done by invoking the `compile(node)`-
    method which will pick the right `on_XXX`-method. It is not
    recommended to call the `on_XXX`-methods directly.

    Attributes:
        context:  A list of parent nodes that ends with the currently
                compiled node.
        grammar_name:  The name of the grammar this compiler is related to
        grammar_source:  The source code of the grammar this compiler is
                related to.
        _dirty_flag:  A flag indicating that the compiler has already been
                called at least once and that therefore all compilation
                variables must be reset when it is called again.
    """

    def __init__(self, grammar_name="", grammar_source=""):
        self._reset()
        self._dirty_flag = False
        self.set_grammar_name(grammar_name, grammar_source)

    def _reset(self):
        self.context = []  # type: List[Node]

    def __call__(self, node: Node) -> Any:
        """
        Compiles the abstract syntax tree with the root node `node` and
        returns the compiled code. It is up to subclasses implementing
        the compiler to determine the format of the returned data.
        (This very much depends on the kind and purpose of the
        implemented compiler.)
        """
        if self._dirty_flag:
            self._reset()
        else:
            self._dirty_flag = True
        result = self.compile(node)
        self.propagate_error_flags(node, lazy=True)
        return result

    def set_grammar_name(self, grammar_name="", grammar_source=""):
        """
        Changes the grammar's name and the grammar's source.

        The grammar name and the source text of the grammar are
        metadata about the grammar that do not affect the compilation
        process. Classes inheriting from `Compiler` can use this
        information to name and annotate its output.
        """
        assert grammar_name == "" or re.match(r'\w+\Z', grammar_name)
        if not grammar_name and re.fullmatch(r'[\w/:\\]+', grammar_source):
            grammar_name = os.path.splitext(os.path.basename(grammar_source))[0]
        self.grammar_name = grammar_name
        self.grammar_source = load_if_file(grammar_source)

    @staticmethod
    def propagate_error_flags(node: Node, lazy: bool = True) -> None:
        # See test_parser.TestCompilerClass.test_propagate_error()..
        if not lazy or node.error_flag < Error.HIGHEST:
            for child in node.children:
                Compiler.propagate_error_flags(child)
                node.error_flag = max(node.error_flag, child.error_flag)
                if lazy and node.error_flag >= Error.HIGHEST:
                    return

    @staticmethod
    def method_name(node_name: str) -> str:
        """Returns the method name for `node_name`, e.g.
        >>> Compiler.method_name('expression')
        'on_expression'
        """
        return 'on_' + node_name

    def compile(self, node: Node) -> Any:
        """
        Calls the compilation method for the given node and returns the
        result of the compilation.

        The method's name is derived from either the node's parser
        name or, if the parser is anonymous, the node's parser's class
        name by adding the prefix 'on_'.

        Note that ``compile`` does not call any compilation functions
        for the parsers of the sub nodes by itself. Rather, this should
        be done within the compilation methods.
        """
        elem = node.parser.name or node.parser.ptype[1:]
        if not sane_parser_name(elem):
            node.add_error("Reserved name '%s' not allowed as parser "
                           "name! " % elem + "(Any name starting with "
                           "'_' or '__' or ending with '__' is reserved.)")
            return None
        else:
            compiler = self.__getattribute__(self.method_name(elem))
            self.context.append(node)
            result = compiler(node)
            self.context.pop()
            # # the following statement makes sure that the error_flag
            # # is propagated early on. Otherwise it is redundant, because
            # # the __call__ method globally propagates the node's error_flag
            # # later anyway. So, maybe it could be removed here.
            # for child in node.children:
            #     node.error_flag = node.error_flag or child.error_flag
            return result


def compile_source(source: str,
                   preprocessor: Optional[PreprocessorFunc],  # str -> str
                   parser: Grammar,  # str -> Node (concrete syntax tree (CST))
                   transformer: TransformationFunc,  # Node -> Node (abstract syntax tree (AST))
                   compiler: Compiler) -> Tuple[Any, List[Error], Node]:  # Node (AST) -> Any
    """
    Compiles a source in four stages:
        1. Preprocessing (if needed)
        2. Parsing
        3. AST-transformation
        4. Compiling.
    The compilations stage is only invoked if no errors occurred in
    either of the two previous stages.

    Args:
        source (str): The input text for compilation or a the name of a
            file containing the input text.
        preprocessor (function):  text -> text. A preprocessor function
            or None, if no preprocessor is needed.
        parser (function):  A parsing function or grammar class
        transformer (function):  A transformation function that takes
            the root-node of the concrete syntax tree as an argument and
            transforms it (in place) into an abstract syntax tree.
        compiler (function): A compiler function or compiler class
            instance

    Returns (tuple):
        The result of the compilation as a 3-tuple
        (result, errors, abstract syntax tree). In detail:
        1. The result as returned by the compiler or ``None`` in case
            of failure,
        2. A list of error or warning messages
        3. The root-node of the abstract syntax tree
    """
    original_text = load_if_file(source)
    log_file_name = logfile_basename(source, compiler)
    if preprocessor is None:
        source_text = original_text
        source_mapping = lambda i: i
    else:
        source_text, source_mapping = with_source_mapping(preprocessor(original_text))
    syntax_tree = parser(source_text)
    if is_logging():
        syntax_tree.log(log_file_name + '.cst')
        parser.log_parsing_history__(log_file_name)

    assert is_error(syntax_tree.error_flag) or str(syntax_tree) == strip_tokens(source_text)
    # only compile if there were no syntax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    result = None
    efl = syntax_tree.error_flag
    messages = syntax_tree.collect_errors(clear_errors=True)
    if not is_error(efl):
        transformer(syntax_tree)
        efl = max(efl, syntax_tree.error_flag)
        messages.extend(syntax_tree.collect_errors(clear_errors=True))
        if is_logging():
            syntax_tree.log(log_file_name + '.ast')
        if not is_error(syntax_tree.error_flag):
            result = compiler(syntax_tree)
        # print(syntax_tree.as_sxpr())
        messages.extend(syntax_tree.collect_errors())
        syntax_tree.error_flag = max(syntax_tree.error_flag, efl)

    adjust_error_locations(messages, original_text, source_mapping)
    return result, messages, syntax_tree
