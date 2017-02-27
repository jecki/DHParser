#!/usr/bin/python3

"""ParserCombinators.py - parser combinators for left-recursive grammers


Copyright 2016  by Eckhart Arnold

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Module parser_combinators contains a number of classes that together make up
parser combinators for left-recursive grammers. For each element of the
extended Backus-Naur-Form as well as for a regular expression token a class is
defined. The set of classes can be used to define a parser for
(ambiguous) left-recursive grammers.


References and Acknowledgements:

Dominikus Herzberg: Objekt-orientierte Parser-Kombinatoren in Python,
Blog-Post, September, 18th 2008 on denkspuren. gedanken, ideen, anregungen und
links rund um informatik-themen, URL:
http://denkspuren.blogspot.de/2008/09/objekt-orientierte-parser-kombinatoren.html

Dominikus Herzberg: Eine einfache Grammatik für LaTeX, Blog-Post, September,
18th 2008 on denkspuren. gedanken, ideen, anregungen und links rund
um informatik-themen, URL:
http://denkspuren.blogspot.de/2008/09/eine-einfache-grammatik-fr-latex.html

Dominikus Herzberg: Uniform Syntax, Blog-Post, February, 27th 2007 on
denkspuren. gedanken, ideen, anregungen und links rund um informatik-themen,
URL:
http://denkspuren.blogspot.de/2007/02/uniform-syntax.html

Richard A. Frost, Rahmatullah Hafiz and Paul Callaghan: Parser Combinators
for Ambiguous Left-Recursive Grammars, in: P. Hudak and D.S. Warren (Eds.):
PADL 2008, LNCS 4902, pp. 167–181, Springer-Verlag Berlin Heidelberg 2008.

Juancarlo Añez: grako, a PEG parser generator in Python,
https://bitbucket.org/apalala/grako
"""

# TODO: Replace copy.deepcopy() call in ParserRoot class by custom copy()-methods in the Parser classes. Is that really better?


import collections
import copy
import keyword
import os

# try:
#     import regex as re
# except ImportError:
#     import re
import re       # as of now use `re` - even hough `regex` appears to be better
import sys
import types
from functools import reduce, partial


DEBUG = True
DEBUG_DUMP_AST = ""


def DEBUG_DUMP_SYNTAX_TREE(parser_root, syntax_tree, compiler, ext):
    global DEBUG, DEBUG_DUMP_AST
    if DEBUG:
        if os.path.exists("DEBUG"):
            prefix = "DEBUG" if os.path.isdir("DEBUG") else ""
        else:
            os.mkdir("DEBUG")
            prefix = "DEBUG"
        ast_file_name = (DEBUG_DUMP_AST or compiler.grammar_name or \
                         parser_root.__class__.__name__) + ext
        with open(os.path.join(prefix, ast_file_name), "w", encoding="utf-8") as f:
            f.write(syntax_tree.as_sexpr())


class Error(Exception):
    """Base class for errors in module `ParserCombinators`.
    """
    pass


##############################################################################
#
# Scanner / Preprocessor support
#
##############################################################################


RX_SCANNER_TOKEN = re.compile('\w+')
BEGIN_SCANNER_TOKEN = '\x1b'
END_SCANNER_TOKEN = '\x1c'


def make_token(token, argument=''):
    assert RX_SCANNER_TOKEN.match(token)
    assert argument.find(BEGIN_SCANNER_TOKEN) < 0
    assert argument.find(END_SCANNER_TOKEN) < 0
    return BEGIN_SCANNER_TOKEN + token + argument + END_SCANNER_TOKEN


nil_scanner = lambda text: text


##############################################################################
#
# Parser tree
#
##############################################################################

def line_col(text, pos):
    """Returns the 'pos' within text as (line, column)-tuple.
    """
    line = text.count("\n", 0, pos) + 1
    column = pos - text.rfind("\n", 0, pos)
    return line, column


class Node:
    def __init__(self, parser, result):
        # self.children = False # will be set by the following assignment
        self.result = result   # sets self.children to `True` if there are any
        self.parser = parser or ZOMBIE_PARSER
        self.errors = []
        self.fatal_error = any(r.fatal_error for r in self.result) \
            if self.children else False
        self.len_before_AST = len(self.result) if not self.children \
            else sum(child.len_before_AST for child in self.result)
        self.pos = 0

    def __str__(self):
        if self.children:
            # assert all(isinstance(child, Node) for child in self.result), \
            #     str(self.result)
            return "".join([str(child) for child in self.result])
        return str(self.result)

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, result):
        assert (isinstance(result, tuple) and
                all(isinstance(child, Node) for child in result)) or \
               isinstance(result, Node) or \
               isinstance(result, str)
        if isinstance(result, Node):
            result = (result,)
        self._result = result or ''
        self.children = result if isinstance(result, tuple) else ()

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos
        offset = 0
        for child in self.children:
            child.pos = pos + offset
            offset += child.len_before_AST

    def as_tree(self, tab, openF, closeF, dataF=lambda s: s):
        """Generates a tree representation of this node and its children
        in string from. This could be an XML-representation or a lisp-like
        S-expression. Exactly which form the tree representation takes is
        defined by the parameters of the function.

        Args:
            tab:      the tab string for indentation, e.g. '\t' or '    '
            openF:    a function that returns an opening string (e.g. an
                      XML-tag) for a given node.
            closeF:   a function that returns a closeF string (e.g. an
                      XML-tag for a given node.
            dataF:    filters data string before printing, e.g. to add
                      quotation marks
        Returns:
            a string that contains a (serialized) tree representation of the
            node and its children.
        """
        head = openF(self)
        tail = closeF(self)

        if not self.result:
            return head + tail

        head = head + '\n'        # place the head, tail and content
        tail = '\n' + tail        # of the node on different lines

        if self.children:
            content = []
            for child in self.result:
                subtree = child.as_tree(tab, openF, closeF, dataF).split('\n')
                content.append('\n'.join((tab + s) for s in subtree))
            return head + '\n'.join(content) + tail

        return head + '\n'.join([tab + dataF(s)
                                 for s in str(self.result).split('\n')]) + tail

    def as_sexpr(self, src=None):
        """Returns content as S-expression, i.e. in lisp-like form.

        Args:
            src:    The source text or `None`. In case the source text is given
                    the position of the element in the text will be reported as
                    line and column.
        """
        def opening(node):
            s = '(' + (node.parser.component or node.parser.__class__.__name__)
            # s += " '(pos %i)" % node.pos
            if src:
                s += " '(pos %i  %i %i)" % (node.pos, *line_col(src, node.pos))
            if node.errors:
                s += " '(err '(%s))" % ' '.join(str(err).replace('"', r'\"')
                                                for err in node.errors)
            return s
        return self.as_tree('    ', opening, lambda node: ')',
                            lambda s: '"' + s.replace('"', r'\"') + '"')

    def as_xml(self, src=None):
        """Returns content as S-expression, i.e. in lisp-like form.

        Args:
            src:    The source text or `None`. In case the source text is given
                    the position will also be reported as line and column.
        """

        def opening(node):
            s = '<' + (node.parser.component or node.parser.__class__.__name__)
            # s += ' pos="%i"' % node.pos
            if src:
                s += ' line="%i" col="%i"' % line_col(src, node.pos)
            if node.errors:
                s += ' err="%s"' % ''.join(str(err).replace('"', r'\"')
                                           for err in node.errors)
            s += ">"
            return s

        def closing(node):
            s = '</' + \
                (node.parser.component or node.parser.__class__.__name__) + '>'
            return s

        return self.as_tree('    ', opening, closing, lambda s: s)

    def add_error(self, error):
        self.errors.append(error)
        return self

    def collect_errors(self, clear=False):
        """Returns all errors of this node or any child node in the form of a
        list of tuples (position: int, error_message: string), where position
        is always relative to this node. If `clear` is true, errors messages
        are cleared after collecting.
        """
        errors = [(0, self.errors)] if self.errors else []
        if clear:
            self.errors = []
            self.fatal_error = False
        if self.children:
            offset = 0
            for child in self.result:
                errors.extend((pos + offset, err)
                              for pos, err in child.collect_errors(clear))
                offset += child.len_before_AST
        return errors


def error_messages(text, errors):
    """Converts the list of `errors` collected from the root node of the
    parse tree of `text` into a human readable (and IDE or editor parsable
    text) with line an column numbers. Error messages are separated by an
    empty line.
    """
    return "\n\n".join("line: %i, column: %i, error: %s" %
                       (*line_col(text, entry[0]), " and ".join(entry[1]))
                       for entry in errors)


##############################################################################
#
# Parser base classes
#
##############################################################################

LEFT_RECURSION_DEPTH = 10  # because of pythons recursion depth limit, this
                           # value ought not to be set too high
MAX_DROPOUTS = 25  # stop trying to recover parsing after so many

WHITESPACE_KEYWORD = 'wspc__'
TOKEN_KEYWORD = 'token__'


def left_recursion_guard(callfunc):
    def call(parser, text):
        try:
            location = len(text)
            # if location has already been visited by the current parser,
            # return saved result
            #### if parser.component: print(parser.component, location, text[:10] + '...')
            if location in parser.visited:
                return parser.visited[location]
            # break left recursion at the maximum allowed depth
            if parser.recursion_counter.setdefault(location, 0) > \
                    LEFT_RECURSION_DEPTH:
                return None, text

            parser.recursion_counter[location] += 1

            # # call preprocess hook
            # if parser.preprocess is not None:
            #     text = parser.preprocess(parser, text)

            # run original __call__ method
            result = callfunc(parser, text)

            if result[0] is not None:
                # in case of a recursive call saves the result of the first
                # (or left-most) call that matches
                parser.visited[location] = result
                parser.head.last_node = result[0]
            elif location in parser.visited:
                # if parser did non match but a saved result exits, assume
                # left recursion and use the saved result
                result = parser.visited[location]

            # # call postprocess hook
            # if parser.postprocess is not None:
            #     text, result = parser.postprocess(parser, text, result)

            parser.recursion_counter[location] -= 1

        except RecursionError:
            node = Node(None, text[:min(10, max(1, text.find("\n")))] + " ...")
            node.add_error("maximum recursion depth of parser reached; "
                           "potentially due to too many errors!")
            node.fatal_error = True
            result = (node, '')

        return result

    return call


class ParserMetaClass(type):
    def __init__(C, name, bases, attrs):
        C.__call__ = left_recursion_guard(C.__call__)
        super(ParserMetaClass, C).__init__(name, bases, attrs)


class Parser(metaclass=ParserMetaClass):
    def __init__(self, component=None):
        assert component is None or isinstance(component, str)
        self.component = component or ''
        self.head = None          # head quater for global variables etc.
        self.visited = dict()
        self.recursion_counter = dict()
        self.cycle_detection = set()
        # self.preprocess = None  # f(str) -> str
        # self.postprocess = None  # f(str, Node or str) -> (str, Node or str)

    def __call__(self, text):
        raise NotImplementedError

    def __str__(self):
        return self.component + ("<%s>" % self.__class__.__name__)

    def apply(self, func):
        """Applies function `func(parser)` recursively to this parser and all
        descendendants of the tree of parsers. MIND THAT due to the current
        implementation of cycle detection one and the same function can never
        be applied twice!
        """
        if func in self.cycle_detection:
            return False
        else:
            self.cycle_detection.add(func)
            func(self)
            return True

    def addHooks(self, preprocess, postprocess):
        assert preprocess is None or isinstance(preprocess, types.FunctionType)
        assert postprocess is None or isinstance(postprocess, types.FunctionType)
        self.preprocess = preprocess
        self.postprocess = postprocess
        return self


class ParserRoot:
    def __init__(self, root=None):
        self.root__ = root if root else copy.deepcopy(self.__class__.root__)
        self.root__.apply(self._add_parser)
        self.variables = dict()
        self.last_node = None
        self.unused = True

    def _add_parser(self, parser):
        """Adds the copy of the parser object to this instance of ParserRoot.
        """
        if parser.component:  # overwrite class variable with instance variable
            self.__setattr__(parser.component, parser)
        parser.head = self

    def parse(self, document):
        """Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
            parser (Parser):  The root object of the parser combinator ensemble
                that is to be used for parsing the source text.
        Returns:
            Node: The root node ot the parse tree.
        """
        assert self.unused, ("Parser has been used up. Please create a new "
                             "instance of the ParserRoot class!")
        self.unused = False
        parser = self.root__
        stitches = [];
        rest = document
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
            if result and stitches[-1] != result:
                stitches.append(result)
            if rest:
                stitches.append(Node(None, rest))
        return result if not stitches else Node(None, tuple(stitches))


ZOMBIE_PARSER = Parser()  # zombie object to avoid distinction of cases
# for the Node.parser variable
RE_WSPC = Parser(WHITESPACE_KEYWORD)  # Dummy Parser for comments that were captured
                                      # by an RE Parser via the `comment`-parameter


##############################################################################
#
# Token and Regular Expression parser classes (i.e. leaf classes)
#
##############################################################################


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
                node = Node(self, text[len(self.component) + 1:end])
                node.add_error(
                    'Scanner tokens must not be nested or contain '
                    'BEGIN_SCANNER_TOKEN delimiter as part of their argument. '
                    '(Most likely due to a scanner bug!)')
                return node, text[end:]
            if text[1:len(self.component) + 1] == self.component:
                return Node(self, text[len(self.component) + 1:end]), \
                       text[end + 1:]
        return None, text


class RegExp(Parser):
    def __init__(self, component, regexp, orig_re = ''):
        super(RegExp, self).__init__(component)
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp
        self.orig_re = orig_re

    def __deepcopy__(self, memo):
        # this method is obsolete with the new `regex` module!
        try:
            regexp = copy.deepcopy(self.regexp)
        except TypeError:
            regexp = self.regexp.pattern
        duplicate = RegExp(self.component, regexp, self.orig_re)
        duplicate.head = self.head
        duplicate.visited = copy.deepcopy(self.visited, memo)
        duplicate.recursion_counter = copy.deepcopy(self.recursion_counter,
                                                    memo)
        # duplicate.preprocess = self.preprocess
        # duplicate.postprocess = self.postprocess
        return duplicate

    def __call__(self, text):
        match = text[0:1] != BEGIN_SCANNER_TOKEN and self.regexp.match(text)  # ESC starts a scanner token.
        if match:
            end = match.end()
            groups = set(match.groups())
            if len(groups) >= 1:
                split = sorted([i for i in reduce(lambda s, r: s | set(r),
                                                match.regs, set()) if i >= 0])
                parts = (text[i:j] for i, j in zip(split[:-1], split[1:]))
                result = tuple(Node(None if part in groups else RE_WSPC, part)
                               for part in parts)
                if all(r.parser == RE_WSPC for r in result):
                    return Node(RE_WSPC, text[:end]), text[end:]
                return Node(self, result), text[end:]
            return Node(self, match.group()), text[end:]
        return None, text

    def __str__(self):
        pattern = self.orig_re if self.orig_re else self.regexp.pattern  # for readability of error messages !
        return Parser.__str__(self) + "(" + pattern + ")"


def escape_re(s):
    """Returns `s` with all regular expression special characters escaped.
    """
    assert isinstance(s, str)
    re_chars = r"\.^$*+?{}[]()#<>=|!"
    for esc_ch in re_chars:
        s = s.replace(esc_ch, '\\' + esc_ch)
    return s


def mixin_comment(whitespace, comment):
    """Mixes comment-regexp into whitespace regexp.
    """
    wspc = '(?:' + whitespace + '(?:' + comment + whitespace + ')*)'
    return wspc


def RE(regexp, component=None, wspcL='', wspcR=''):
    rA = '('
    rB = '\n)' if regexp.find('(?x)') >= 0 else ')'     # otherwise the closing bracket might erroneously
                                                        # be append to the end of a line comment!
    return RegExp(component or TOKEN_KEYWORD, wspcL + rA + regexp + rB + wspcR,
                  regexp)


def Token(token, component=None, wspcL='', wspcR=''):
    return RE(escape_re(token), component, wspcL, wspcR)


##############################################################################
#
# Combinator parser classes (i.e. trunk classes of the parser tree)
#
##############################################################################


class UnaryOperator(Parser):
    def __init__(self, component, parser):
        super(UnaryOperator, self).__init__(component)
        assert isinstance(parser, Parser)
        self.parser = parser

    def apply(self, func):
        if super(UnaryOperator, self).apply(func):
            self.parser.apply(func)

    def __str__(self):
        return Parser.__str__(self) + \
               ("" if self.component else "(" + str(self.parser) + ")")


class NaryOperator(Parser):
    def __init__(self, component, *parsers):
        super(NaryOperator, self).__init__(component)
        assert all([isinstance(parser, Parser) for parser in parsers])
        self.parsers = parsers

    def apply(self, func):
        if super(NaryOperator, self).apply(func):
            for parser in self.parsers:
                parser.apply(func)

    def __str__(self):
        return Parser.__str__(self) + \
               ("" if self.component else str([str(p) for p in self.parsers]))
        # return "(" + ",\n".join(["\n    ".join(str(parser).split("\n"))
        #                          for parser in self.parsers]) + ")"


class Optional(UnaryOperator):
    def __init__(self, component, parser):
        super(Optional, self).__init__(component, parser)
        assert isinstance(parser, Parser)
        assert not isinstance(parser, Optional), \
            "Nesting options would be redundant!"
        assert not isinstance(parser, Required), \
            "Nestion options with required elemts is contradictory!"

    def __call__(self, text):
        node, text = self.parser(text)
        if node:
            return Node(self, node), text
        return Node(self, ()), text


class ZeroOrMore(Optional):
    def __call__(self, text):
        results = ()
        while text:
            node, text = self.parser(text)
            if not node:
                break
            results += (node,)
        return Node(self, results), text


class OneOrMore(UnaryOperator):
    def __init__(self, component, parser):
        super(OneOrMore, self).__init__(component, parser)
        assert not isinstance(parser, Optional), \
            "Use ZeroOrMore instead of nesting OneOrMore and Optional!"

    def __call__(self, text):
        results = ()
        text_ = text
        while text_:
            node, text_ = self.parser(text_)
            if not node:
                break
            results += (node,)
        if results == ():
            return None, text
        return Node(self, results), text_


class Sequence(NaryOperator):
    def __init__(self, component, *parsers):
        super(Sequence, self).__init__(component, *parsers)
        assert len(self.parsers) >= 1
        # commented, because sequences can be empty:
        # assert not all(isinstance(p, Optional) for p in self.parsers)

    def __call__(self, text):
        results = ()
        text_ = text
        for parser in self.parsers:
            node, text_ = parser(text_)
            if not node:
                return node, text
            if node.result:  # Nodes with zero-length result are silently omitted
                results += (node,)
            if node.fatal_error:
                break
        assert len(results) <= len(self.parsers)
        return Node(self, results), text_


class Alternative(NaryOperator):
    def __init__(self, component, *parsers):
        super(Alternative, self).__init__(component, *parsers)
        assert len(self.parsers) >= 1
        assert all(not isinstance(p, Optional) for p in self.parsers)

    def __call__(self, text):
        for parser in self.parsers:
            node, text_ = parser(text)
            if node:
                return Node(self, node), text_
        return None, text


##############################################################################
#
# Flow control operators
#
##############################################################################


class FlowOperator(UnaryOperator):
    def __init__(self, parser):
        super(FlowOperator, self).__init__(None, parser)


class Required(FlowOperator):
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
    def __init__(self, parser, sign):
        super(Lookahead, self).__init__(parser)
        self.sign = sign

    def __call__(self, text):
        node, text_ = self.parser(text)
        if self.sign(node is not None):
            return Node(self, ''), text
        else:
            return None, text


def PositiveLookahead(parser):
    return Lookahead(parser, lambda boolean: boolean)


def NegativeLookahead(parser):
    return Lookahead(parser, lambda boolean: not boolean)


def iter_right_branch(node):
    """Iterates over the right branch of `node` starting with node itself.
    Iteration is stopped if either there are no child nodes any more or
    if the parser of a node is a Lookahead parser. (Reason is: Since
    lookahead nodes do not advance the parser, it does not make sense
    to look back to them.)
    """
    while node and not isinstance(node.parser, Lookahead):  # the second condition should not be necessary
        yield node                                          # for well-formed EBNF code
        node = node.children[-1] if node.children else None


class Lookbehind(FlowOperator):
    def __init__(self, parser, sign):
        print("WARNING: Lookbehind Operator is experimental!")
        super(Lookbehind, self).__init__(parser)
        self.sign = sign

    def __call__(self, text):
        if isinstance(self.head.last_node, Lookahead):
            return Node(self, '').add_error('Lookbehind right after Lookahead '
                                            'does not make sense!'), text
        if self.sign(self.condition()):
            return Node(self, ''), text
        else:
            return None, text

    def condition(self):
        node = None
        for node in iter_right_branch(self.head.last_node):
            if node.parser.component == self.parser.component:
                return True
        if node and isinstance(self.parser, RegExp) and \
                self.parser.regexp.match(str(node)):    # Is there really a use case for this?
            return True
        return False


def PositiveLookbehind(parser):
    return Lookbehind(parser, lambda boolean: boolean)


def NegativeLookbehind(parser):
    return Lookbehind(parser, lambda boolean: not boolean)


##############################################################################
#
# Capture and Retrieve operators (for passing variables in the parser)
#
##############################################################################


class Capture(UnaryOperator):
    def __init__(self, component, parser):
        assert component
        super(Capture, self).__init__(component, parser)

    def __call__(self, text):
        node, text = self.parser(text)
        if node:
            stack = self.head.variables.setdefault(self.component, [])
            stack.append(str(node))
        return Node(self, node), text


class Retrieve(Parser):
    def __init__(self, symbol):
        super(Retrieve, self).__init__(symbol if isinstance(symbol, str)
                                       else symbol.component)
        assert self.component

    def __call__(self, text):
        stack = self.head.variables[self.component]
        value = self.pick_value(stack)
        if text.startswith(value):
            return Node(self, value), text[len(value):]
        else:
            return None, text

    def pick_value(self, stack):
        return stack[-1]


class Pop(Retrieve):
    def pick_value(self, stack):
        return stack.pop()


##############################################################################
#
# Forward class (for recursive symbols)
#
##############################################################################


class Forward(Parser):
    def __init__(self):
        Parser.__init__(self)
        self.parser = None
        self.cycle_reached = False

    def __call__(self, text):
        return self.parser(text)

    def __str__(self):
        if self.cycle_reached:
            if self.parser and self.parser.component:
                return str(self.parser.component)
            return "..."
        else:
            self.cycle_reached = True
            s = str(self.parser)
            self.cycle_reached = False
            return s

    def set(self, parser):
        assert isinstance(parser, Parser)
        self.component = parser.component
        self.parser = parser

    def apply(self, func):
        # old code to avoid endless loop (can be eliminated)
        # if not self.cycle_reached:
        #     self.cycle_reached = True
        #     super(Forward, self).apply(func)
        #     assert not self.visited
        #     self.parser.apply(func)
        #     self.cycle_reached = False
        if super(Forward, self).apply(func):
            assert not self.visited
            self.parser.apply(func)


PARSER_SYMBOLS = {'RegExp', 'mixin_comment', 'RE', 'Token', 'Required',
                  'PositiveLookahead', 'NegativeLookahead', 'Optional',
                  'ZeroOrMore', 'Sequence', 'Alternative', 'Forward',
                  'OneOrMore', 'ParserRoot', 'Capture', 'Retrieve', 'Pop'}


##############################################################################
#
# Abstract syntax tree support
#
##############################################################################


def expand_table(compact_table):
    """Expands a table by separating keywords that are tuples or strings
    containing comma separated words into single keyword entries with
    the same values. Returns the expanded table.
    Example:
    expand_table({"a, b": 1, "b": 1, ('d','e','f'):5, "c":3}) yields
    {'a': 1, 'b': 1, 'c': 3, 'd': 5, 'e': 5, 'f': 5}
    """
    expanded_table = {}
    keys = list(compact_table.keys())
    for key in keys:
        value = compact_table[key]
        if isinstance(key, str):
            parts = (s.strip() for s in key.split(','))
        else:
            assert isinstance(key, collections.abc.Iterable)
            parts = key
        for p in parts:
            expanded_table[p] = value
    return expanded_table


def ASTTransform(node, transtable):
    """Transforms the parse tree starting with the given `node` into an
    abstract syntax tree by calling transformation functions registered in a
    transformation table.

    Args:
        node (Node): The root note of the parse tree (or sub-tree) to be
                transformed into the abstract syntax tree.
        trans_table (dict): A dictionary that assigns a transformation
                transformation functions to parser component strings.
    """
    # normalize transformation entries by turning single transformations
    # into lists with a single item
    table = {component: transformation
    if isinstance(transformation, collections.abc.Sequence)
    else [transformation]
             for component, transformation in list(transtable.items())}
    table = expand_table(table)

    def recursive_ASTTransform(node):
        if node.children:
            for child in node.result:
                recursive_ASTTransform(child)
        transformation = table.get(node.parser.component,
                                   table.get('*', [lambda node: None]))
        for transform in transformation:
            if transform(node):
                break   # break loop if a transformation is already complete

    recursive_ASTTransform(node)


# ------------------------------------------------
#
# rearranging transformations:
#     - tree may be rearranged (flattened)
#     - order is preserved
#     - all leaves are kept
#
# ------------------------------------------------


def replace_by_single_child(node):
    """Remove single branch node, replacing it by its immediate descendant.
    (In case the descendant's component is empty (i.e. anonymous) the
    component of this node's parser is kept.)
    """
    if node.children and len(node.result) == 1:
        if not node.result[0].parser.component:
            node.result[0].parser.component = node.parser.component
        node.parser = node.result[0].parser
        node.errors.extend(node.result[0].errors)
        node.result = node.result[0].result
        return "STOP"    # discard any further transformations if node has been replaced


def reduce_single_child(node):
    """Reduce a single branch node, by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    """
    if node.children and len(node.result) == 1:
        node.errors.extend(node.result[0].errors)
        node.result = node.result[0].result


# ------------------------------------------------
#
# destructive transformations:
#     - tree may be rearranged (flattened),
#     - order is preserved
#     - but (irrelevant) leaves may be destroyed
#
# ------------------------------------------------

def no_transformation(node):
    pass


def remove_children_if(node, condition):
    """Removes all nodes from the result field if the function `condition` evaluates
    to `True`."""
    if node.children:
        new_result = tuple(r for r in node.result if not condition(r))
        if len(new_result) < len(node.result):
            node.result = new_result


is_whitespace = lambda node: not node.result or (isinstance(node.result, str)
                                                 and not node.result.strip())
is_comment = lambda node: node.parser == RE_WSPC
is_scanner_token = lambda node: isinstance(node.parser, ScannerToken)
is_expendable = lambda node: is_whitespace(node) or is_comment(node) or \
                             is_scanner_token(node)

remove_whitespace = partial(remove_children_if, condition=is_whitespace)
remove_comments = partial(remove_children_if, condition=is_comment)
remove_scanner_tokens = partial(remove_children_if, condition=is_scanner_token)
remove_expendables = partial(remove_children_if, condition=is_expendable)


def flatten(node):
    """Recursively flattens all unnamed sub-nodes. Flattening means that
    wherever a node has child nodes, the child nodes are inserted in place
    of the node. In other words, all leaves of this node and its child nodes
    are collected in-order as direct children of this node.
    """
    if node.children:
        new_result = []
        for child in node.result:
            if not child.parser.component:
                flatten(child)
                new_result.extend(child.result)
            else:
                new_result.append(child)
        node.result = tuple(new_result)


def remove_tokens(node, tokens):
    """Reomoves any of a set of tokens whereever they appear in the result
    of the node.
    """
    assert node.children
    node.result = tuple(child for child in node.result
                        if child.parser.component != TOKEN_KEYWORD or
                        child.result not in tokens)


def remove_enclosing_delimiters(node):
    """Removes the enclosing delimiters from a structure (e.g. quotation marks
    from a literal or braces from a group).
    """
    if node.children and len(node.result) >= 3:
        assert isinstance(node.result[0].result, str) and \
               isinstance(node.result[-1].result, str)
        node.result = node.result[1:-1]


AST_SYMBOLS = {'replace_by_single_child', 'reduce_single_child',
               'no_transformation', 'remove_children_if', 'is_whitespace',
               'is_comment', 'is_scanner_token', 'is_expendable',
               'remove_whitespace', 'remove_comments',
               'remove_scanner_tokens', 'remove_expendables', 'flatten',
               'remove_tokens', 'remove_enclosing_delimiters'}


##############################################################################
#
# Syntax driven compilation support
#
##############################################################################

class CompilerBase:
    def compile__(self, node):
        comp, cls = node.parser.component, node.parser.__class__.__name__
        elem = comp if comp else cls
        if elem == 'compile__' or elem[:2] == '__' or elem[-2:] == '__':
            node.add_error("Must not use reserved name '%s' as parser "
                           "component! " % elem + "(Any name starting with "
                           "'_' or '__' or ending with '__' is reserved.)")
            return None
        else:
            compiler = self.__getattribute__(elem)  # TODO Add support for python keyword attributes
            return compiler(node)


def full_compilation(source, parser_root, AST_transformations, compiler):
    """Compiles a source in three stages:
        1. Parsing
        2. AST-transformation
        3. Compiling.
    The compilations stage is only invoked if no errors occurred in either of
    the two previous stages.

    Args:
        source (str):                the input source for compilation
        parser_root (ParserRoot):    the ParserRoot object
        AST_transformations (dict):  a table that assigns AST transformation
                functions to parser components (see function ASTTransform)
        compiler (object):  an instance of a class derived from `CompilerBase`
                with a suitable method for every parser component or class.
    Returns:
        tuple: (result (?), messages (str), syntax_tree (Node))
            Result as returned by the compiler or `None` if an error occurred
            during parsing or AST-transformation and the compiler wasn't
            invoked; error messages; abstract syntax tree
    """
    syntax_tree = parser_root.parse(source)
    DEBUG_DUMP_SYNTAX_TREE(parser_root, syntax_tree, compiler, ext='.cst')

    errors = syntax_tree.collect_errors(clear=True)
    assert errors or str(syntax_tree) == source
    # only compile if there were no snytax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    if not errors:
        ASTTransform(syntax_tree, AST_transformations)
        DEBUG_DUMP_SYNTAX_TREE(parser_root, syntax_tree, compiler, ext='.ast')
        # print(syntax_tree.as_sexpr())
        result = compiler.compile__(syntax_tree)
        errors.extend(syntax_tree.collect_errors(clear=True))
    else:
        result = None
    errors.sort()
    messages = error_messages(source, errors)
    return result, messages, syntax_tree


COMPILER_SYMBOLS = {'CompilerBase', 'Error', 'Node'}


##############################################################################
#
# EBNF-Grammar-Compiler
#
##############################################################################


class EBNFGrammar(ParserRoot):
    r"""Parser for an EBNF source file, with this grammar:

    # EBNF-Grammar in EBNF

    @ comment    :  /#.*(?:\n|$)/                    # comments start with '#' and eat all chars upto and including '\n'
    @ whitespace :  /\s*/                            # whitespace includes linefeed
    @ literalws  :  right                            # trailing whitespace of literals will be ignored tacitly

    syntax     :  [~//] { definition | directive } §EOF
    definition :  symbol §":" expression
    directive  :  "@" §symbol §":" ( regexp | literal | list_ )

    expression :  term { "|" term }
    term       :  factor { factor }
    factor     :  [flowmarker] [retrieveop] symbol !":"    # negative lookahead to be sure it's not a definition
                | [flowmarker] literal
                | [flowmarker] regexp
                | [flowmarker] group
                | [flowmarker] oneormore
                | repetition
                | option

    flowmarker :  "!"  | "&"  | "§" |                # '!' negative lookahead, '&' positive lookahead, '§' required
                  "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
    retrieveop :  "=" | "@"                          # '=' retrieve,  '@' pop

    group      :  "(" expression §")"
    option     :  "[" expression §"]"
    repetition :  "{" expression §"}"
    oneormore  :  "<" expression §">"

    symbol     :  /\w+/~                             # e.g. expression, factor, parameter_list
    literal    :  /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
                | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
    regexp     :  /~?\/(?:[^\/]|(?<=\\)\/)*\/~?/~    # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                     # '~' is a whitespace-marker, if present leading or trailing
                                                     # whitespace of a regular expression will be ignored tacitly.
    list_      :  /\w+\s*(?:,\s*\w+\s*)*/~           # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                     # BEGIN_QUOTE, END_QUOTE ; see markdown.py for an exmaple
    EOF :  !/./
    """
    expression = Forward()
    wspc__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    EOF = NegativeLookahead(RE('.', "EOF"))
    list_ = RE('\\w+\\s*(?:,\\s*\\w+\\s*)*', "list_", wspcR=wspc__)
    regexp = RE('~?/(?:[^/]|(?<=\\\\)/)*/~?', "regexp", wspcR=wspc__)
    literal = Alternative("literal", RE('"(?:[^"]|\\\\")*?"', wspcR=wspc__), RE("'(?:[^']|\\\\')*?'", wspcR=wspc__))
    symbol = RE('\\w+', "symbol", wspcR=wspc__)
    oneormore = Sequence("oneormore", Token("<", wspcR=wspc__), expression, Required(Token(">", wspcR=wspc__)))
    repetition = Sequence("repetition", Token("{", wspcR=wspc__), expression, Required(Token("}", wspcR=wspc__)))
    option = Sequence("option", Token("[", wspcR=wspc__), expression, Required(Token("]", wspcR=wspc__)))
    group = Sequence("group", Token("(", wspcR=wspc__), expression, Required(Token(")", wspcR=wspc__)))
    retrieveop = Alternative("retrieveop", Token("=", wspcR=wspc__), Token("@", wspcR=wspc__))
    flowmarker = Alternative("flowmarker", Token("!", wspcR=wspc__), Token("&", wspcR=wspc__), Token("§", wspcR=wspc__),
                             Token("-!", wspcR=wspc__), Token("-&", wspcR=wspc__))
    factor = Alternative("factor", Sequence(None, Optional(None, flowmarker), Optional(None, retrieveop), symbol,
                                            NegativeLookahead(Token("=", wspcR=wspc__))),
                         Sequence(None, Optional(None, flowmarker), literal),
                         Sequence(None, Optional(None, flowmarker), regexp),
                         Sequence(None, Optional(None, flowmarker), group),
                         Sequence(None, Optional(None, flowmarker), oneormore), repetition, option)
    term = Sequence("term", factor, ZeroOrMore(None, factor))
    expression.set(Sequence("expression", term, ZeroOrMore(None, Sequence(None, Token("|", wspcR=wspc__), term))))
    directive = Sequence("directive", Token("@", wspcR=wspc__), Required(symbol), Required(Token("=", wspcR=wspc__)),
                         Alternative(None, regexp, literal, list_))
    definition = Sequence("definition", symbol, Required(Token("=", wspcR=wspc__)), expression)
    syntax = Sequence("syntax", Optional(None, RE('', wspcL=wspc__)),
                      ZeroOrMore(None, Alternative(None, definition, directive)), Required(EOF))
    root__ = syntax


EBNFTransTable = {
    # AST Transformations for EBNF-grammar
    "syntax":
        remove_expendables,
    "directive, definition":
        partial(remove_tokens, tokens={'@', '='}),
    "expression":
        [replace_by_single_child, flatten,
         partial(remove_tokens, tokens={'|'})],
    "term":
        [replace_by_single_child, flatten],
    "factor, flowmarker, retrieveop":
        replace_by_single_child,
    "group":
        [remove_enclosing_delimiters, replace_by_single_child],
    "oneormore, repetition, option":
        [reduce_single_child, remove_enclosing_delimiters],
    "symbol, literal, regexp, list_":
        [remove_expendables, reduce_single_child],
    (TOKEN_KEYWORD, WHITESPACE_KEYWORD):
        [remove_expendables, reduce_single_child],
    "":
        [remove_expendables, replace_by_single_child]
}


def load_if_file(text_or_file):
    """Reads and returns content of a file if parameter `text_or_file` is a
    file name (i.e. a single line string), otherwise (i.e. if `text_or_file` is
    a multiline string) returns the content of `text_or_file`.
    """
    if text_or_file and text_or_file.find('\n') < 0:
        with open(text_or_file, encoding="utf-8") as f:
            content = f.read()
        return content
    else:
        return text_or_file


class EBNFCompilerError(Error):
    """Error raised by `EBNFCompiler` class. (Not compilation errors
    in the strict sense, see `CompilationError` below)"""
    pass


Scanner = collections.namedtuple('Scanner',
                                 'symbol instantiation_call cls_name cls')


class EBNFCompiler(CompilerBase):
    """Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.
    """
    # RX_DIRECTIVE = re.compile('(?:#|@)\s*(?P<key>\w*)\s*=\s*(?P<value>.*)')  # this can be removed, soon
    RESERVED_SYMBOLS = {TOKEN_KEYWORD, WHITESPACE_KEYWORD, 'wspc__'}
    KNOWN_DIRECTIVES = {'comment', 'whitespace', 'tokens', 'literalws'}
    VOWELS = {'A', 'E', 'I', 'O', 'U'}  # what about cases like 'hour', 'universe' etc. ?
    AST_ERROR = "Badly structured syntax tree. " \
                "Potentially due to erroneuos AST transformation."

    def __init__(self, grammar_name="", source_text=""):
        super(EBNFCompiler, self).__init__()
        assert grammar_name == "" or re.match('\w+\Z', grammar_name)
        self.grammar_name = grammar_name
        self.source_text = load_if_file(source_text)
        self._reset()

    def _reset(self):
        self.rules = set()
        self.symbols = set()
        self.variables = set()
        self.scanner_tokens = set()
        self.definition_names = []
        self.component = str(None)
        self.recursive = set()
        self.root = ""
        self.directives = {'whitespace': '\s*',
                           'comment': '',
                           'literalws': ['wspcR=wspc__']}

    def gen_Scanner_Skeleton(self):
        name = self.grammar_name + "Scanner"
        return "def %s(text):\n    return text\n" % name


    def gen_AST_Skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_AST_Skeleton()"!')
        transtable = [self.grammar_name + 'TransTable = {',
                      '    # AST Transformations for the ' +
                      self.grammar_name + '-grammar']
        for name in self.definition_names:
            transtable.append('    "' + name + '": no_transformation,')
        transtable += ['    "": no_transformation', '}', '']
        return '\n'.join(transtable)

    def gen_Compiler_Skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_Compiler_Skeleton()"!')
        compiler = ['class ' + self.grammar_name + 'Compiler(CompilerBase):',
                    '    """Compiler for the abstract-syntax-tree of a ' + \
                    self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self, grammar_name="' + \
                    self.grammar_name + '"):',
                    '        super(' + self.grammar_name + \
                    'Compiler, self).__init__()',
                    "        assert re.match('\w+\Z', grammar_name)", '']
        for name in self.definition_names:
            if name == self.root:
                compiler += ['    def ' + name + '(self, node):',
                             '        return node', '']
            else:
                compiler += ['    def ' + name + '(self, node):',
                             '        pass', '']
        return '\n'.join(compiler + [''])

    def syntax(self, node):
        self._reset()
        definitions = []

        # drop the wrapping sequence node
        if isinstance(node.parser, Sequence) and \
                isinstance(node.result[0].parser, ZeroOrMore):
            node = node.result[0]

        # compile definitions and directives and collect definitions
        for nd in node.result:
            if nd.parser.component == "definition":
                definitions.append(self.compile__(nd))
            else:
                assert nd.parser.component == "directive", nd.as_sexpr()
                self.compile__(nd)

        # fix capture of variables that have been defined before usage [sic!]
        if self.variables:
            for i in range(len(definitions)):
                if definitions[i][0] in self.variables:
                    definitions[i] = (definitions[i][0],
                                      'Capture("%s", %s)' % definitions[i])

        # remember definition names for AST skeleton generation
        self.definition_names = [defn[0] for defn in definitions]
        definitions.append(('wspc__',
                            ("mixin_comment(whitespace="
                             "r'{whitespace}', comment=r'{comment}')"). \
                            format(**self.directives)))

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class
        article = 'an ' if self.grammar_name[0:1].upper() \
                           in EBNFCompiler.VOWELS else 'a '
        declarations = ['class ' + self.grammar_name + 'Grammar(ParserRoot):',
                        'r"""Parser for ' + article + self.grammar_name +
                        ' source file' +
                        (', with this grammar:' if self.source_text else '.')]
        if self.source_text:
            declarations.append('')
            declarations += [line for line in self.source_text.split('\n')]
            while declarations[-1].strip() == '':
                declarations = declarations[:-1]
        declarations.append('"""')

        # turn definitions into declarations in reverse order
        self.root = definitions[0][0] if definitions else ""
        definitions.reverse()
        declarations += [symbol + ' = Forward()'
                         for symbol in sorted(list(self.recursive))]
        for symbol, statement in definitions:
            if symbol in self.recursive:
                declarations += [symbol + '.set(' + statement + ')']
            else:
                declarations += [symbol + ' = ' + statement]
        for nd in self.symbols:
            if nd.result not in self.rules:
                nd.add_error("Missing production for symbol '%s'" % nd.result)
        if self.root and 'root__' not in self.symbols:
            declarations.append('root__ = ' + self.root)
        declarations.append('')
        return '\n    '.join(declarations)

    def definition(self, node):
        rule = node.result[0].result
        if rule in EBNFCompiler.RESERVED_SYMBOLS:
            node.add_error('Symbol "%s" is a reserved symbol.' % rule)
        elif rule in self.scanner_tokens:
            node.add_error('Symbol "%s" has already been defined as '
                           'a scanner token.' % rule)
        elif keyword.iskeyword(rule):
            node.add_error('Python keyword "%s" may not be used as a symbol. '
                           % rule + '(This may change in the furute.)')
        elif rule in self.rules:
            node.add_error('A rule with name "%s" has already been defined.' %
                           rule)
        try:
            self.component = '"' + rule + '"'
            self.rules.add(rule)
            defn = self.compile__(node.result[1])
            if rule in self.variables:
                defn = 'Capture("%s", %s)' % (rule, defn)
                self.variables.remove(rule)
        except TypeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + \
                     node.as_sexpr()
            node.add_error(errmsg)
            rule, defn = 'error', '"' + errmsg + '"'
        return (rule, defn)

    def _check_rx(self, node, rx):
        """Checks whether the string `rx` represents a valid regular
        expression. Makes sure that multiline regular expressions are
        prepended by the multiline-flag. Returns the regular expression string.
        """
        rx = rx if rx.find('\n') < 0 or rx[0:4] == '(?x)' else '(?x)' + rx
        try:
            re.compile(rx)
        except Exception as re_error:
            node.add_error("malformed regular expression %s: %s" %
                           (repr(rx), str(re_error)))
        return rx

    def directive(self, node):
        key = node.result[0].result.lower()
        assert key not in self.scanner_tokens
        if key in {'comment', 'whitespace'}:
            value = node.result[1].result
            if value[0] + value[-1] in {'""', "''"}:
                value = escape_re(value[1:-1])
            elif value[0] + value[-1] == '//':
                value = self._check_rx(node, value[1:-1])
            else:
                value = self._check_rx(node, value)
            self.directives[key] = value
        elif key == 'literalws':
            value = {item.lower() for item in self.compile__(node.result[1])}
            conv = {'left': 'wspcL=wspc__', 'right': 'wspcR=wspc__'}
            ws = {conv['left'], conv['right']} if 'both' in value else set()
            value.discard('both')
            value.discard('none')  # 'none' will be overridden if combined with other values
            try:
                ws |= {conv[it] for it in value}
            except KeyError as key_error:
                node.add_error('Directive "literalws" allows the values '
                               '`left`, `right`, `both` or `none`, '
                               'but not `%s`' % key_error.args[0])
            self.directives[key] = list(ws)

        elif key == 'tokens':
            self.scanner_tokens |= self.compile__(node.result[1])
        else:
            node.add_error('Unknown directive %s ! (Known ones are %s .)' %
                           (key,
                            ', '.join(list(EBNFCompiler.KNOWN_DIRECTIVES))))
        return ""

    def non_terminal(self, node, kind):
        """Compiles any non-terminal, where `kind` indicates the Parser class
        name for the particular non-terminal.
        """
        comp = self.component
        self.component = str(None)
        arguments = filter(lambda arg: arg,  # remove comments at this stage
                           [comp] + [self.compile__(r) for r in node.result])
        return kind + '(' + ', '.join(arguments) + ')'

    def expression(self, node):
        return self.non_terminal(node, 'Alternative')

    def term(self, node):
        return self.non_terminal(node, 'Sequence')

    def factor(self, node):
        assert isinstance(node.parser, Sequence)  # these assert statements can be removed
        assert node.children
        assert len(node.result) >= 2
        assert isinstance(node.result[0].parser, RegExp), str(node.as_sexpr())
        prefix = node.result[0].result
        if len(node.result) > 2:
            assert prefix not in {':', '::'}
            node.result = node.result[1:]
            arg = self.factor(node)
        else:
            arg = self.compile__(node.result[1])
        if prefix == '§':
            return 'Required(' + arg + ')'
        elif prefix == '!':
            return 'NegativeLookahead(' + arg + ')'
        elif prefix == '&':
            return 'PositiveLookahead(' + arg + ')'
        elif prefix == '-!':
            return 'NegativeLookbehind(' + arg + ')'
        elif prefix == '-&':
            return 'PositiveLookbehind(' + arg + ')'
        else:
            if node.result[1].parser.component != 'symbol':
                node.add_error(('Can apply retrieve operator "%s" only to '
                                'symbols, but not to %s.') %
                               (prefix, str(node.result[1].parser)))
                return arg
            self.variables.add(arg)
            if prefix == ":":
                return 'Retrieve(' + arg + ')'
            elif prefix == "::":
                return 'Pop(' + arg + ')'
            assert False, ("Unknown prefix %s \n" % prefix) + node.as_sexpr()

    def option(self, node):
        return self.non_terminal(node, 'Optional')

    def repetition(self, node):
        return self.non_terminal(node, 'ZeroOrMore')

    def oneormore(self, node):
        return self.non_terminal(node, 'OneOrMore')

    def group(self, node):
        raise EBNFCompilerError("Group nodes should have been eliminated by "
                                "AST transformation!")

    def symbol(self, node):
        if node.result in self.scanner_tokens:
            return 'ScannerToken("' + node.result + '")'
        else:
            self.symbols.add(node)
            if node.result in self.rules:
                self.recursive.add(node.result)
            return node.result

    def _get_component(self):
        comp = [self.component] if self.component != str(None) else []
        self.component = str(None)
        return comp

    def literal(self, node):
        comp = self._get_component() + self.directives["literalws"]
        return 'Token(' + ', '.join([node.result] + comp) + ')'

    def regexp(self, node):
        comp = self._get_component()
        rx = node.result
        if rx[:2] == '~/':
            comp += ['wspcL=wspc__']
            rx = rx[1:]
        if rx[-2:] == '/~':
            comp += ['wspcR=wspc__']
            rx = rx[:-1]
        try:
            arg = repr(self._check_rx(node, rx[1:-1].replace(r'\/', '/')))
        except AttributeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + \
                     node.as_sexpr()
            node.add_error(errmsg)
            return '"' + errmsg + '"'
        return 'RE(' + ', '.join([arg] + comp) + ')'

    def list_(self, node):
        return set(item.strip() for item in node.result.split(','))


##############################################################################
#
# support for compiling DSLs based on an EBNF-grammar
#
##############################################################################

DELIMITER = "\n\n### DON'T EDIT OR REMOVE THIS LINE ###\n\n"


def is_python_code(text_or_file):
    """Checks whether 'text_or_file' is python code or the name of a file that
    contains python code.
    """
    if text_or_file.find('\n') < 0:
        return text_or_file[-3:].lower() == '.py'
    try:
        compile(text_or_file, '<string>', 'exec')
        return True
    except (SyntaxError, ValueError, OverflowError):
        pass
    return False


class GrammarError(Error):
    """Raised when (already) the grammar of a domain specific language (DSL)
    contains errors.
    """
    def __init__(self, error_messages, grammar_src):
        self.error_messages = error_messages
        self.grammar_src = grammar_src


class CompilationError(Error):
    """Raised when a string or file in a domain specific language (DSL)
    contains errors.
    """
    def __init__(self, error_messages, dsl_text, dsl_grammar, AST):
        self.error_messages = error_messages
        self.dsl_text = dsl_text
        self.dsl_grammar = dsl_grammar
        self.AST = AST

    def __str__(self):
        return self.error_messages


def compile_python_object(python_src, obj_name_ending="Grammar"):
    """Compiles the python source code and returns the object the name of which
    ends with `obj_name_ending`.
     """
    code = compile(python_src, '<string>', 'exec')
    module_vars = globals()
    allowed_symbols = PARSER_SYMBOLS | AST_SYMBOLS | COMPILER_SYMBOLS
    namespace = {k: module_vars[k] for k in allowed_symbols}
    exec(code, namespace)  # safety risk?
    for key in namespace.keys():
        if key.endswith(obj_name_ending):
            parser = namespace[key]
            break
    return parser


def get_grammar_instance(grammar):
    """Returns a grammar object and the source code of the grammar, from
    the given `grammar`-data which can be either a file name, ebnf-code,
    python-code, a ParserRoot-derived grammar class or an instance of
    such a class (i.e. a grammar object already).
    """
    if isinstance(grammar, str):
        # read grammar
        grammar_src = load_if_file(grammar)
        if is_python_code(grammar):
            parser_py, errors, AST = grammar_src, '', None
        else:
            parser_py, errors, AST = full_compilation(grammar_src,
                EBNFGrammar(), EBNFTransTable, EBNFCompiler())
        if errors:
            raise GrammarError(errors, grammar_src)
        parser_root = compile_python_object(parser_py, 'Grammar')()
    else:
        # assume that dsl_grammar is a ParserRoot object or Grammar class
        grammar_src = ''
        if isinstance(grammar, ParserRoot):
            parser_root = grammar
        else:
            # assume `grammar` is a grammar class and get the root object
            parser_root = grammar()
    return parser_root, grammar_src


def load_compiler_suite(compiler_suite):
    """
    """
    assert isinstance(compiler_suite, str)
    source = load_if_file(compiler_suite)
    if is_python_code(compiler_suite):
        scanner_py, parser_py, ast_py, compiler_py = source.split(DELIMITER)
        scanner = compile_python_object(scanner_py, 'Scanner')
        ast = compile_python_object(ast_py, 'TransTable')
        compiler = compile_python_object(compiler_py, 'Compiler')
    else:
        # assume source is an ebnf grammar
        parser_py, errors, AST = full_compilation(source,
                                                  EBNFGrammar(), EBNFTransTable, EBNFCompiler())
        if errors:
            raise GrammarError(errors, source)
        scanner = nil_scanner
        ast = EBNFTransTable
        compiler = EBNFCompiler()
    parser = compile_python_object(parser_py, 'Grammar')()

    return scanner, parser, ast, compiler


def compileDSL(text_or_file, dsl_grammar, trans_table, compiler,
               scanner=nil_scanner):
    """Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Returns the compiled text.
    """
    assert isinstance(text_or_file, str)
    assert isinstance(compiler, CompilerBase)
    assert isinstance(trans_table, dict)

    parser_root, grammar_src = get_grammar_instance(dsl_grammar)
    src = scanner(load_if_file(text_or_file))
    result, errors, AST = full_compilation(src, parser_root, trans_table,
                                           compiler)
    if errors:  raise CompilationError(errors, src, grammar_src, AST)
    return result


##############################################################################
#
# quick system test
#
##############################################################################

def self_test():
    if len(sys.argv) > 1:
        filepath = os.path.normpath(sys.argv[1])
        source = load_if_file(sys.argv[1])
        rootname = os.path.splitext(filepath)[0]
        if len(sys.argv) > 2:
            scanner, parser, trans, compiler = load_compiler_suite(sys.argv[2])
        else:
            scanner = nil_scanner
            parser = EBNFGrammar()
            trans = EBNFTransTable
            compiler = EBNFCompiler(os.path.basename(rootname), source)
        DEBUG_DUMP_AST = rootname
        print(compiler)
        result, errors, ast = full_compilation(scanner(source), parser,
                                               trans, compiler)
        if errors:
            print(errors)
            sys.exit(1)
        elif trans == EBNFTransTable:
            f = None
            DELIMITER = "\n\n### DON'T EDIT OR REMOVE THIS LINE ###\n\n"

            try:
                f = open(rootname + '_compiler.py', 'r', encoding="utf-8")
                source = f.read()
                scanner, parser, ast, compiler = source.split(DELIMITER)
            except (PermissionError, FileNotFoundError, IOError) as error:
                scanner = compiler.gen_Scanner_Skeleton()
                ast = compiler.gen_AST_Skeleton()
                compiler = compiler.gen_Compiler_Skeleton()
            finally:
                if f:  f.close()

            try:
                f = open(rootname + '_compiler.py', 'w', encoding="utf-8")
                f.write(scanner)
                f.write(DELIMITER)
                f.write(result)
                f.write(DELIMITER)
                f.write(ast)
                f.write(DELIMITER)
                f.write(compiler)
            except (PermissionError, FileNotFoundError, IOError) as error:
                print('# Could not write file "' + rootname + '.py" because of: '
                      + "\n# ".join(str(error).split('\n)')))
                print(result)
            finally:
                if f:  f.close()
        else:
            print(result)
            print(errors)
            print(ast)

    else:
        # self-test
        # compileDSL("examples/EBNF/EBNF.ebnf", "examples/EBNF/grammars/EBNF.ebnf", EBNFTransTable, EBNFCompiler())

        assert (str(EBNFGrammar.syntax) == str(EBNFGrammar.syntax))

        def test(file_name):
            print(file_name)
            with open('examples/' + file_name, encoding="utf-8") as f:
                grammar = f.read()
            compiler_name = os.path.basename(os.path.splitext(file_name)[0])
            compiler = EBNFCompiler(compiler_name, grammar)
            result, errors, syntax_tree = full_compilation(grammar, 
                    EBNFGrammar(), EBNFTransTable, compiler)
            # print(syntax_tree.as_xml())
            print(syntax_tree.as_sexpr(grammar))
            print(errors)
            print(compiler.gen_AST_Skeleton())
            print(compiler.gen_Compiler_Skeleton())
            result = compileDSL(grammar, result, EBNFTransTable, compiler)
            print(result)
            return result

        test('EBNF/EBNF.ebnf')


if __name__ == "__main__":
    self_test()
