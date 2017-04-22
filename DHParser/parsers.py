#!/usr/bin/python3

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

Juancarlo Añez: grako, a PEG parser generator in Python,
https://bitbucket.org/apalala/grako
"""


import copy
import os
try:
    import regex as re
except ImportError:
    import re
import sys

from .toolkit import IS_LOGGING, LOGS_DIR, escape_re, sane_parser_name, smart_list
from .syntaxtree import WHITESPACE_KEYWORD, TOKEN_KEYWORD, ZOMBIE_PARSER, Node, \
    traverse
from DHParser.toolkit import load_if_file, error_messages

__all__ = ['HistoryRecord',
           'Parser',
           'GrammarBase',
           'RX_SCANNER_TOKEN',
           'BEGIN_SCANNER_TOKEN',
           'END_SCANNER_TOKEN',
           'make_token',
           'nil_scanner',
           'ScannerToken',
           'RegExp',
           'RE',
           'Token',
           'mixin_comment',
           'UnaryOperator',
           'NaryOperator',
           'Optional',
           'ZeroOrMore',
           'OneOrMore',
           'Sequence',
           'Alternative',
           'FlowOperator',
           'Required',
           'Lookahead',
           'NegativeLookahead',
           'Lookbehind',
           'NegativeLookbehind',
           'Capture',
           'Retrieve',
           'Pop',
           'Forward',
           'CompilerBase',
           'full_compilation']


LEFT_RECURSION_DEPTH = 10  # because of pythons recursion depth limit, this
                           # value ought not to be set too high
MAX_DROPOUTS = 25  # stop trying to recover parsing after so many errors


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
    __slots__ = ('call_stack', 'node', 'remaining')

    MATCH = "MATCH"
    ERROR = "ERROR"
    FAIL = "FAIL"

    def __init__(self, call_stack, node, remaining):
        self.call_stack = call_stack
        self.node = node
        self.remaining = remaining

    @property
    def stack(self):
        return "->".join(str(parser) for parser in self.call_stack)

    @property
    def status(self):
        return self.FAIL if self.node is None else self.ERROR if self.node._errors else self.MATCH

    @property
    def extent(self):
        return ((-self.remaining - self.node.len, -self.remaining) if self.node
                else (-self.remaining, None))


def add_parser_guard(parser_func):
    def guarded_call(parser, text):
        try:
            location = len(text)
            # if location has already been visited by the current parser,
            # return saved result
            if location in parser.visited:
                return parser.visited[location]
            # break left recursion at the maximum allowed depth
            if parser.recursion_counter.setdefault(location, 0) > LEFT_RECURSION_DEPTH:
                return None, text

            parser.recursion_counter[location] += 1
            grammar = parser.grammar

            if grammar.history_tracking:
                grammar.call_stack.append(parser)
                grammar.moving_forward = True

            # run original __call__ method
            node, rest = parser_func(parser, text)

            if grammar.history_tracking:
                if grammar.moving_forward:  # and result[0] == None
                    grammar.moving_forward = False
                    record = HistoryRecord(grammar.call_stack.copy(), node, len(rest))
                    grammar.history.append(record)
                    # print(record.stack, record.status, rest[:20].replace('\n', '|'))
                grammar.call_stack.pop()

            if node is not None:
                # in case of a recursive call saves the result of the first
                # (or left-most) call that matches
                parser.visited[location] = (node, rest)
                grammar.last_node = node
            elif location in parser.visited:
                # if parser did non match but a saved result exits, assume
                # left recursion and use the saved result
                node, rest = parser.visited[location]

            parser.recursion_counter[location] -= 1

        except RecursionError:
            node = Node(None, text[:min(10, max(1, text.find("\n")))] + " ...")
            node.add_error("maximum recursion depth of parser reached; "
                           "potentially due to too many errors!")
            node.error_flag = True
            rest = ''

        return node, rest

    return guarded_call


class ParserMetaClass(type):
    def __init__(cls, name, bases, attrs):
        # The following condition is necessary for classes that don't override
        # the __call__() method, because in these cases the non-overridden
        # __call__()-method would be substituted a second time!
        guarded_parser_call = add_parser_guard(cls.__call__)
        if cls.__call__.__code__ != guarded_parser_call.__code__:
            cls.__call__ = guarded_parser_call
        super(ParserMetaClass, cls).__init__(name, bases, attrs)


class Parser(metaclass=ParserMetaClass):
    def __init__(self, name=None):
        assert name is None or isinstance(name, str), str(name)
        self.name = name or ''
        self._grammar = None  # center for global variables etc.
        self.reset()

    def __deepcopy__(self, memo):
        return self.__class__(self.name)

    def reset(self):
        self.visited = dict()
        self.recursion_counter = dict()
        self.cycle_detection = set()
        return self

    def __call__(self, text):
        return None, text  # default behaviour: don't match

    def __str__(self):
        return self.name or self.__class__.__name__

    @property
    def grammar(self):
        return self._grammar

    @grammar.setter
    def grammar(self, grammar_base):
        self._grammar = grammar_base
        self._grammar_assigned_notifier()

    def _grammar_assigned_notifier(self):
        pass

    def apply(self, func):
        """Applies function `func(parser)` recursively to this parser and all
        descendants of the tree of parsers. The same function can never
        be applied twice between calls of the ``reset()``-method!
        """
        if func in self.cycle_detection:
            return False
        else:
            self.cycle_detection.add(func)
            func(self)
            return True


class GrammarBase:
    root__ = None  # should be overwritten by grammar subclass

    @classmethod
    def _assign_parser_names(cls):
        """Initializes the `parser.name` fields of those
        Parser objects that are directly assigned to a class field with
        the field's name, e.g.
            class Grammar(GrammarBase):
                ...
                symbol = RE('(?!\\d)\\w+')
        After the call of this method symbol.name == "symbol"
        holds. Names assigned via the ``name``-parameter of the
        constructor will not be overwritten. Parser names starting or
        ending with a double underscore like ``root__`` will be
        ignored. See ``toolkit.sane_parser_name()``
        
        Attention: If there exists more than one reference to the same
        parser, only the first one will be chosen for python versions 
        greater or equal 3.6.  For python version <= 3.5 an arbitrarily
        selected reference will be chosen. See PEP 520
        (www.python.org/dev/peps/pep-0520/) for an explanation of why. 
        """
        if cls.parser_initialization__ == "done":
            return
        cdict = cls.__dict__
        for entry, parser in cdict.items():
            if isinstance(parser, Parser) and sane_parser_name(entry):
                if not parser.name or parser.name == TOKEN_KEYWORD:
                    parser.name = entry
                if (isinstance(parser, Forward) and (not parser.parser.name
                                                     or parser.parser.name == TOKEN_KEYWORD)):
                    parser.parser.name = entry
        cls.parser_initialization__ = "done"

    def __init__(self):
        self.all_parsers = set()
        self.dirty_flag = False
        self.history_tracking = IS_LOGGING()
        self._reset()
        self._assign_parser_names()
        self.root__ = copy.deepcopy(self.__class__.root__)
        if self.wspL__:
            self.wsp_left_parser__ = RegExp(self.wspL__, WHITESPACE_KEYWORD)
            self.wsp_left_parser__.grammar = self
            self.all_parsers.add(self.wsp_left_parser__)  # don't you forget about me...
        else:
            self.wsp_left_parser__ = ZOMBIE_PARSER
        if self.wspR__:
            self.wsp_right_parser__ = RegExp(self.wspR__, WHITESPACE_KEYWORD)
            self.wsp_right_parser__.grammar = self
            self.all_parsers.add(self.wsp_right_parser__)  # don't you forget about me...
        else:
            self.wsp_right_parser__ = ZOMBIE_PARSER
        self.root__.apply(self._add_parser)

    def __getitem__(self, key):
        return self.__dict__[key]

    def _reset(self):
        self.variables = dict()  # support for Pop and Retrieve operators
        self.document = ""  # source document
        self.last_node = None
        self.call_stack = []  # support for call stack tracing
        self.history = []  # snapshots of call stacks
        self.moving_forward = True  # also needed for call stack tracing

    def _add_parser(self, parser):
        """Adds the copy of the classes parser object to this
        particular instance of GrammarBase.
        """
        if parser.name:
            setattr(self, parser.name, parser)
        self.all_parsers.add(parser)
        parser.grammar = self

    def parse(self, document, start_parser="root__"):
        """Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
        Returns:
            Node: The root node ot the parse tree.
        """
        assert isinstance(document, str)
        if self.root__ is None:
            raise NotImplementedError()
        if self.dirty_flag:
            self._reset()
            for parser in self.all_parsers:
                parser.reset()
        else:
            self.dirty_flag = True
        self.document = document
        parser = self[start_parser]
        stitches = []
        rest = document
        result = Node(None, '')
        while rest and len(stitches) < MAX_DROPOUTS:
            result, rest = parser(rest)
            if rest:
                fwd = rest.find("\n") + 1 or len(rest)
                skip, rest = rest[:fwd], rest[fwd:]
                if result is None:
                    error_msg = "Parser did not match! Invalid source file?"
                else:
                    stitches.append(result)
                    error_msg = "Parser stopped before end" + \
                                ("! trying to recover..."
                                 if len(stitches) < MAX_DROPOUTS
                                 else " too often! Terminating parser.")
                stitches.append(Node(None, skip))
                stitches[-1].add_error(error_msg)
        if stitches:
            if rest:
                stitches.append(Node(None, rest))
            result = Node(None, tuple(stitches))
        result.pos = 0  # calculate all positions
        return result

    def log_parsing_history(self, log_file_name=''):
        """Writes a log of the parsing history of the most recently parsed
        document. 
        """

        def prepare_line(record):
            excerpt = self.document.__getitem__(slice(*record.extent))[:25].replace('\n', '\\n')
            excerpt = "'%s'" % excerpt if len(excerpt) < 25 else "'%s...'" % excerpt
            return record.stack, record.status, excerpt

        def write_log(history, log_name):
            path = os.path.join(LOGS_DIR(), log_name + "_parser.log")
            if history:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("\n".join(history))
            elif os.path.exists(path):
                os.remove(path)

        if IS_LOGGING():
            if not log_file_name:
                name = self.__class__.__name__
                log_file_name = name[:-7] if name.lower().endswith('grammar') else name
            full_history, match_history, errors_only = [], [], []
            for record in self.history:
                line = ";  ".join(prepare_line(record))
                full_history.append(line)
                if record.node and record.node.parser.name != WHITESPACE_KEYWORD:
                    match_history.append(line)
                    if record.node.errors:
                        errors_only.append(line)
            write_log(full_history, log_file_name + '_full')
            write_log(match_history, log_file_name + '_match')
            write_log(errors_only, log_file_name + '_errors')


def dsl_error_msg(parser, error_str):
    """Returns an error messsage for errors in the parser configuration,
    e.g. errors that result in infinite loops.

    Args:
        parser (Parser:  The parser where the error was noticed. Note
            that this is not necessarily the parser that caused the
            error but only where the error became apparaent.
        error_str (str):  A short string describing the error.
    Returns:  
        str: An error message including the call stack if history 
        tacking has been turned in the grammar object.
    """
    msg = ["DSL parser specification error:", error_str, "caught by parser", str(parser)]
    if parser.grammar.history:
        msg.extend(["\nCall stack:", parser.grammar.history[-1].stack])
    else:
        msg.extend(["\nEnable history tracking in Grammar object to display call stack."])
    return " ".join(msg)


########################################################################
#
# Token and Regular Expression parser classes (i.e. leaf classes)
#
########################################################################


RX_SCANNER_TOKEN = re.compile('\w+')
BEGIN_SCANNER_TOKEN = '\x1b'
END_SCANNER_TOKEN = '\x1c'


def make_token(token, argument=''):
    """Turns the ``token`` and ``argument`` into a special token that
    will be caught by the `ScannerToken`-parser.

    This function is a support function that should be used by scanners
    to inject scanner tokens into the source text.
    """
    assert RX_SCANNER_TOKEN.match(token)
    assert argument.find(BEGIN_SCANNER_TOKEN) < 0
    assert argument.find(END_SCANNER_TOKEN) < 0

    return BEGIN_SCANNER_TOKEN + token + argument + END_SCANNER_TOKEN


def nil_scanner(text):
    return text


class ScannerToken(Parser):
    def __init__(self, scanner_token):
        assert isinstance(scanner_token, str) and scanner_token and \
               scanner_token.isupper()
        assert RX_SCANNER_TOKEN.match(scanner_token)
        super(ScannerToken, self).__init__(scanner_token)

    def __call__(self, text):
        if text[0:1] == BEGIN_SCANNER_TOKEN:
            end = text.find(END_SCANNER_TOKEN, 1)
            if end < 0:
                node = Node(self, '').add_error(
                    'END_SCANNER_TOKEN delimiter missing from scanner token. '
                    '(Most likely due to a scanner bug!)')
                return node, text[1:]
            elif end == 0:
                node = Node(self, '').add_error(
                    'Scanner token cannot have zero length. '
                    '(Most likely due to a scanner bug!)')
                return node, text[2:]
            elif text.find(BEGIN_SCANNER_TOKEN, 1, end) >= 0:
                node = Node(self, text[len(self.name) + 1:end])
                node.add_error(
                    'Scanner tokens must not be nested or contain '
                    'BEGIN_SCANNER_TOKEN delimiter as part of their argument. '
                    '(Most likely due to a scanner bug!)')
                return node, text[end:]
            if text[1:len(self.name) + 1] == self.name:
                return Node(self, text[len(self.name) + 1:end]), \
                       text[end + 1:]
        return None, text


class RegExp(Parser):
    """Regular expression parser.
    
    The RegExp-parser parses text that matches a regular expression.
    RegExp can also be considered as the "atomic parser", because all
    other parsers delegate part of the parsing job to other parsers,
    but do not match text directly.
    """
    def __init__(self, regexp, name=None):
        super(RegExp, self).__init__(name)
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def __deepcopy__(self, memo):
        # `regex` supports deep copies, but not `re`
        try:
            regexp = copy.deepcopy(self.regexp, memo)
        except TypeError:
            regexp = self.regexp.pattern
        return RegExp(regexp, self.name)

    def __call__(self, text):
        match = text[0:1] != BEGIN_SCANNER_TOKEN and self.regexp.match(text)  # ESC starts a scanner token.
        if match:
            end = match.end()
            return Node(self, text[:end]), text[end:]
        return None, text


class RE(Parser):
    """Regular Expressions with optional leading or trailing whitespace.
    
    The RE-parser parses pieces of text that match a given regular
    expression. Other than the ``RegExp``-Parser it can also skip 
    "implicit whitespace" before or after the matched text.
    
    The whitespace is in turn defined by a regular expression. It
    should be made sure that this expression also matches the empty
    string, e.g. use r'\s*' or r'[\t ]+', but not r'\s+'. If the
    respective parameters in the constructor are set to ``None`` the
    default whitespace expression from the Grammar object will be used.
    """
    def __init__(self, regexp, wL=None, wR=None, name=None):
        """Constructor for class RE.
                
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
        super(RE, self).__init__(name)
        self.wL = wL
        self.wR = wR
        self.wspLeft = RegExp(wL, WHITESPACE_KEYWORD) if wL else ZOMBIE_PARSER
        self.wspRight = RegExp(wR, WHITESPACE_KEYWORD) if wR else ZOMBIE_PARSER
        self.main = RegExp(regexp)

    def __deepcopy__(self, memo={}):
        try:
            regexp = copy.deepcopy(self.main.regexp, memo)
        except TypeError:
            regexp = self.main.regexp.pattern
        return self.__class__(regexp, self.wL, self.wR, self.name)

    def __call__(self, text):
        # assert self.main.regexp.pattern != "@"
        t = text
        wL, t = self.wspLeft(t)
        main, t = self.main(t)
        if main:
            wR, t = self.wspRight(t)
            result = tuple(nd for nd in (wL, main, wR)
                           if nd and nd.result != '')
            return Node(self, result), t
        return None, text

    def __str__(self):
        if self.name == TOKEN_KEYWORD:
            return 'Token "%s"' % self.main.regexp.pattern.replace('\\', '')
        return self.name or ('RE ' + ('~' if self.wL else '')
                             + '/%s/' % self.main.regexp.pattern + ('~' if self.wR else ''))

    def _grammar_assigned_notifier(self):
        if self.grammar:
            # use default whitespace parsers if not otherwise specified
            if self.wL is None:
                self.wspLeft = self.grammar.wsp_left_parser__
            if self.wR is None:
                self.wspRight = self.grammar.wsp_right_parser__

    def apply(self, func):
        if super(RE, self).apply(func):
            if self.wL:
                self.wspLeft.apply(func)
            if self.wR:
                self.wspRight.apply(func)
            self.main.apply(func)


def Token(token, wL=None, wR=None, name=None):
    """Returns an RE-parser that matches plain strings that are
    considered as 'tokens'. 
    
    If the ``name``-parameter is empty, the parser's name will be set
    to the TOKEN_KEYWORD, making it easy to identify tokens in the 
    abstract syntax tree transformation and compilation stage.
    """
    return RE(escape_re(token), wL, wR, name or TOKEN_KEYWORD)


def mixin_comment(whitespace, comment):
    """Returns a regular expression that merges comment and whitespace
    regexps. Thus comments cann occur whereever whitespace is allowed
    and will be skipped just as implicit whitespace.
    
    Note, that because this works on the level of regular expressions,
    nesting comments is not possible. It also makes it much harder to
    use directives inside comments (which isn't recommended, anyway).
    """
    wspc = '(?:' + whitespace + '(?:' + comment + whitespace + ')*)'
    return wspc


########################################################################
#
# Combinator parser classes (i.e. trunk classes of the parser tree)
#
########################################################################


class UnaryOperator(Parser):
    def __init__(self, parser, name=None):
        super(UnaryOperator, self).__init__(name)
        assert isinstance(parser, Parser)
        self.parser = parser

    def __deepcopy__(self, memo):
        parser = copy.deepcopy(self.parser, memo)
        return self.__class__(parser, self.name)

    def apply(self, func):
        if super(UnaryOperator, self).apply(func):
            self.parser.apply(func)


class NaryOperator(Parser):
    def __init__(self, *parsers, name=None):
        super(NaryOperator, self).__init__(name)
        assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        self.parsers = parsers

    def __deepcopy__(self, memo):
        parsers = copy.deepcopy(self.parsers, memo)
        return self.__class__(*parsers, name=self.name)

    def apply(self, func):
        if super(NaryOperator, self).apply(func):
            for parser in self.parsers:
                parser.apply(func)


class Optional(UnaryOperator):
    def __init__(self, parser, name=None):
        super(Optional, self).__init__(parser, name)
        assert isinstance(parser, Parser)
        assert not isinstance(parser, Optional), \
            "Nesting options would be redundant: %s(%s)" % \
            (str(name), str(parser.name))
        assert not isinstance(parser, Required), \
            "Nesting options with required elements is contradictory: " \
            "%s(%s)" % (str(name), str(parser.name))

    def __call__(self, text):
        node, text = self.parser(text)
        if node:
            return Node(self, node), text
        return Node(self, ()), text


class ZeroOrMore(Optional):
    def __call__(self, text):
        results = ()
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


class OneOrMore(UnaryOperator):
    def __init__(self, parser, name=None):
        super(OneOrMore, self).__init__(parser, name)
        assert not isinstance(parser, Optional), \
            "Use ZeroOrMore instead of nesting OneOrMore and Optional: " \
            "%s(%s)" % (str(name), str(parser.name))

    def __call__(self, text):
        results = ()
        text_ = text
        n = len(text) + 1
        while text_ and len(text_) < n:
            n = len(text_)
            node, text_ = self.parser(text_)
            if not node:
                break
            if len(text_) == n:
                node.add_error(dsl_error_msg(self, 'Infinite Loop dtected.'))
            results += (node,)
        if results == ():
            return None, text
        return Node(self, results), text_


class Sequence(NaryOperator):
    def __init__(self, *parsers, name=None):
        super(Sequence, self).__init__(*parsers, name=name)
        assert len(self.parsers) >= 1

    def __call__(self, text):
        results = ()
        text_ = text
        for parser in self.parsers:
            node, text_ = parser(text_)
            if not node:
                return node, text
            if node.result:  # Nodes with zero-length result are silently omitted
                results += (node,)
            if node.error_flag:
                break
        assert len(results) <= len(self.parsers)
        return Node(self, results), text_


class Alternative(NaryOperator):
    def __init__(self, *parsers, name=None):
        super(Alternative, self).__init__(*parsers, name=name)
        assert len(self.parsers) >= 1
        assert all(not isinstance(p, Optional) for p in self.parsers)

    def __call__(self, text):
        for parser in self.parsers:
            node, text_ = parser(text)
            if node:
                return Node(self, node), text_
        return None, text


########################################################################
#
# Flow control operators
#
########################################################################


class FlowOperator(UnaryOperator):
    def __init__(self, parser, name=None):
        super(FlowOperator, self).__init__(parser, name)


class Required(FlowOperator):
    # Add constructor that checks for logical errors, like `Required(Optional(...))` constructs ?
    def __call__(self, text):
        node, text_ = self.parser(text)
        if not node:
            m = re.search(r'\s(\S)', text)
            i = max(1, m.regs[1][0]) if m else 1
            node = Node(self, text[:i])
            text_ = text[i:]
            # assert False, "*"+text[:i]+"*"
            node.add_error('%s expected; "%s..." found!' %
                           (str(self.parser), text[:10]))
        return node, text_


class Lookahead(FlowOperator):
    def __init__(self, parser, name=None):
        super(Lookahead, self).__init__(parser, name)

    def __call__(self, text):
        node, text_ = self.parser(text)
        if self.sign(node is not None):
            return Node(self, ''), text
        else:
            return None, text

    def sign(self, bool_value):
        return bool_value


class NegativeLookahead(Lookahead):
    def sign(self, bool_value):
        return not bool_value


def iter_right_branch(node):
    """Iterates over the right branch of `node` starting with node itself.
    Iteration is stopped if either there are no child nodes any more or
    if the parser of a node is a Lookahead parser. (Reason is: Since
    lookahead nodes do not advance the parser, it does not make sense
    to look back to them.)
    """
    while node and not isinstance(node.parser, Lookahead):  # the second condition should not be necessary
        yield node  # for well-formed EBNF code
        node = node.children[-1] if node.children else None


class Lookbehind(FlowOperator):
    def __init__(self, parser, name=None):
        super(Lookbehind, self).__init__(parser, name)
        print("WARNING: Lookbehind Operator is experimental!")

    def __call__(self, text):
        if isinstance(self.grammar.last_node, Lookahead):
            return Node(self, '').add_error('Lookbehind right after Lookahead '
                                            'does not make sense!'), text
        if self.sign(self.condition()):
            return Node(self, ''), text
        else:
            return None, text

    def sign(self, bool_value):
        return bool_value

    def condition(self):
        node = None
        for node in iter_right_branch(self.grammar.last_node):
            if node.parser.name == self.parser.name:
                return True
        if node and isinstance(self.parser, RegExp) and \
                self.parser.regexp.match(str(node)):  # Is there really a use case for this?
            return True
        return False


class NegativeLookbehind(Lookbehind):
    def sign(self, bool_value):
        return not bool_value


########################################################################
#
# Capture and Retrieve operators (for passing variables in the parser)
#
########################################################################


class Capture(UnaryOperator):
    def __init__(self, parser, name=None):
        super(Capture, self).__init__(parser, name)
        print("WARNING: Capture operator is experimental")

    def __call__(self, text):
        node, text = self.parser(text)
        if node:
            stack = self.grammar.variables.setdefault(self.name, [])
            stack.append(str(node))
            return Node(self, node), text
        else:
            return None, text


class Retrieve(Parser):
    def __init__(self, symbol, counterpart=None, name=None):
        if not name:
            name = symbol.name
        super(Retrieve, self).__init__(name)
        self.symbol = symbol
        self.counterpart = counterpart if counterpart else lambda value: value
        print("WARNING: Retrieve operator is experimental")

    def __deepcopy__(self, memo):
        return self.__class__(self.symbol, self.counterpart, self.name)

    def __call__(self, text):
        stack = self.grammar.variables[self.symbol.name]
        value = self.counterpart(self.pick_value(stack))
        if text.startswith(value):
            return Node(self, value), text[len(value):]
        else:
            return None, text

    def pick_value(self, stack):
        return stack[-1]


class Pop(Retrieve):
    def pick_value(self, stack):
        return stack.pop()


########################################################################
#
# Forward class (for recursive symbols)
#
########################################################################


class Forward(Parser):
    def __init__(self):
        Parser.__init__(self)
        self.parser = None
        self.name = ''
        self.cycle_reached = False

    def __deepcopy__(self, memo):
        duplicate = self.__class__()
        memo[id(self)] = duplicate
        parser = copy.deepcopy(self.parser, memo)
        duplicate.set(parser)
        return duplicate

    def __call__(self, text):
        return self.parser(text)

    def __str__(self):
        if self.cycle_reached:
            if self.parser and self.parser.name:
                return str(self.parser.name)
            return "..."
        else:
            self.cycle_reached = True
            s = str(self.parser)
            self.cycle_reached = False
            return s

    def set(self, parser):
        assert isinstance(parser, Parser)
        self.name = parser.name  # redundant, see GrammarBase-constructor
        self.parser = parser

    def apply(self, func):
        if super(Forward, self).apply(func):
            assert not self.visited
            self.parser.apply(func)


#######################################################################
#
# Syntax driven compilation support
#
#######################################################################


class CompilerBase:
    def __init__(self):
        self.dirty_flag = False

    def _reset(self):
        pass

    def compile__(self, node):
        # if self.dirty_flag:
        #     self._reset()
        # else:
        #     self.dirty_flag = True

        comp, cls = node.parser.name, node.parser.__class__.__name__
        elem = comp or cls
        if not sane_parser_name(elem):
            node.add_error("Must not use reserved name '%s' as parser "
                           "name! " % elem + "(Any name starting with "
                                             "'_' or '__' or ending with '__' is reserved.)")
            return None
        else:
            compiler = self.__getattribute__(elem)  # TODO Add support for python keyword attributes
            result = compiler(node)
            for child in node.children:
                node.error_flag |= child.error_flag
            return result


def full_compilation(source, scanner, parser, transform, compiler):
    """Compiles a source in four stages:
        1. Scanning (if needed)
        2. Parsing
        3. AST-transformation
        4. Compiling.
    The compilations stage is only invoked if no errors occurred in
    either of the two previous stages.

    Args:
        source (str): The input text for compilation or a the name of a
            file containing the input text.
        scanner (function):  text -> text. A scanner function or None,
            if no scanner is needed.
        parser (GrammarBase):  The GrammarBase object
        transform (function):  A transformation function that takes
            the root-node of the concrete syntax tree as an argument and
            transforms it (in place) into an abstract syntax tree.
        compiler (object):  An instance of a class derived from
            ``CompilerBase`` with a suitable method for every parser
            name or class.

    Returns (tuple):
        The result of the compilation as a 3-tuple
        (result, errors, abstract syntax tree). In detail:
        1. The result as returned by the compiler or ``None`` in case
            of failure,
        2. A list of error messages
        3. The root-node of the abstract syntax treelow
    """
    assert isinstance(compiler, CompilerBase)

    source_text = load_if_file(source)
    log_file_name = os.path.basename(os.path.splitext(source)[0]) if source != source_text \
        else compiler.__class__.__name__ + '_out'
    if scanner is not None:
        source_text = scanner(source_text)
    syntax_tree = parser.parse(source_text)
    syntax_tree.log(log_file_name, ext='.cst')
    parser.log_parsing_history(log_file_name)

    assert syntax_tree.error_flag or str(syntax_tree) == source_text, str(syntax_tree)
    # only compile if there were no syntax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    if syntax_tree.error_flag:
        result = None
        errors = syntax_tree.collect_errors()
    else:
        transform(syntax_tree)
        syntax_tree.log(log_file_name, ext='.ast')
        errors = syntax_tree.collect_errors()
        if not errors:
            result = compiler.compile__(syntax_tree)
            errors = syntax_tree.collect_errors()
    messages = error_messages(source_text, errors)
    return result, messages, syntax_tree

