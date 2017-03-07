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

# TODO: Replace copy.deepcopy() call in ParserHeadquarter class by custom copy()-methods in the Parser classes. Is that really better?


import collections
import copy
import hashlib
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


__version__ = '0.5.1' + '_dev' + str(os.stat(__file__).st_mtime)


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
        ast_file_name = (DEBUG_DUMP_AST or compiler.grammar_name or
                         parser_root.__class__.__name__) + ext
        with open(os.path.join(prefix, ast_file_name), "w",
                  encoding="utf-8") as f:
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
    def name(self):
        return self.parser.name or self.parser.__class__.__name__

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
            s = '(' + node.name
            # s += " '(pos %i)" % node.pos
            if src:
                s += " '(pos %i  %i %i)" % (node.pos, *line_col(src, node.pos))
            if node.errors:
                s += " '(err '(%s))" % ' '.join(str(err).replace('"', r'\"')
                                                for err in node.errors)
            return s
        return self.as_tree('    ', opening, lambda node: ')')
                            # lambda s: '"' + s.replace('"', r'\"') + '"')

    def as_xml(self, src=None):
        """Returns content as S-expression, i.e. in lisp-like form.

        Args:
            src:    The source text or `None`. In case the source text is given
                    the position will also be reported as line and column.
        """

        def opening(node):
            s = '<' + node.name
            # s += ' pos="%i"' % node.pos
            if src:
                s += ' line="%i" col="%i"' % line_col(src, node.pos)
            if node.errors:
                s += ' err="%s"' % ''.join(str(err).replace('"', r'\"')
                                           for err in node.errors)
            s += ">"
            return s

        def closing(node):
            s = '</' + node.name + '>'
            return s

        return self.as_tree('    ', opening, closing)

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

    def navigate(self, path):
        """Returns the first descendant element matched by `path`, e.g.
        'd/s' returns 'l' from (d (s l)(e (r x1) (r x2))
        'e/r' returns 'x2'
        'e'   returns (r x1)(r x2)
        :param path: the path of the object, e.g. 'a/b/c'
        :return: the object at the path, either a string or a Node or
                 `None`, if the path did not match.
        """
        pl = path.strip('')
        assert pl[0] != '/', 'Path must noch start with "/"!'
        nd = self
        for p in pl:
            if isinstance(nd.result, str):
                return p if (p == nd.result) and (p == pl[-1]) else None
            for child in nd.result:
                if str(child) == p:
                    nd = child
                    break
            else:
                return None
        return child


def error_messages(text, errors):
    """Converts the list of `errors` collected from the root node of the
    parse tree of `text` into a human readable (and IDE or editor parsable
    text) with line an column numbers. Error messages are separated by an
    empty line.
    """
    return "\n\n".join("line: %i, column: %i, error: %s" %
                       (*line_col(text, entry[0]), " and ".join(entry[1]))
                       for entry in errors)


# lambda compact_sexpr s : re.sub('\s(?=\))', '', re.sub('\s+', ' ', s)).strip()


##############################################################################
#
# Parser base classes
#
##############################################################################

LEFT_RECURSION_DEPTH = 10   # because of pythons recursion depth limit, this
                            # value ought not to be set too high
MAX_DROPOUTS = 25   # stop trying to recover parsing after so many errors

WHITESPACE_KEYWORD = 'wsp__'
TOKEN_KEYWORD = 'token__'


def wrap_parser(parser_func):
    def wrapper(parser, text):
        try:
            location = len(text)
            # if location has already been visited by the current parser,
            # return saved result
            if location in parser.visited:
                return parser.visited[location]
            # break left recursion at the maximum allowed depth
            if parser.recursion_counter.setdefault(location, 0) > \
                    LEFT_RECURSION_DEPTH:
                return None, text

            parser.recursion_counter[location] += 1

            parser.headquarter.call_stack.append(parser)
            parser.headquarter.moving_forward = True

            # run original __call__ method
            result = parser_func(parser, text)

            if parser.headquarter.moving_forward:  # and result[0] == None
                parser.headquarter.moving_forward = False
                global DEBUG
                if DEBUG:
                    st = "->".join((str(p) for p in parser.headquarter.call_stack))
                    if result[0]:
                        print(st, '\t"%s"' % str(result[0]).replace('\n', ' '), "\tHIT")
                        pass
                    else:
                        t = text[:20].replace('\n',' ')
                        print(st, '\t"%s"' % (t + ("..." if t else "")), "\tfail")
                        pass
            parser.headquarter.call_stack.pop()

            if result[0] is not None:
                # in case of a recursive call saves the result of the first
                # (or left-most) call that matches
                parser.visited[location] = result
                parser.headquarter.last_node = result[0]
            elif location in parser.visited:
                # if parser did non match but a saved result exits, assume
                # left recursion and use the saved result
                result = parser.visited[location]

            parser.recursion_counter[location] -= 1

        except RecursionError:
            node = Node(None, text[:min(10, max(1, text.find("\n")))] + " ...")
            node.add_error("maximum recursion depth of parser reached; "
                           "potentially due to too many errors!")
            node.fatal_error = True
            result = (node, '')

        return result

    return wrapper


class ParserMetaClass(type):
    def __init__(cls, name, bases, attrs):
        # The following condition is necessary for classes that don't override
        # the __call__() method, because in these cases the non-overridden
        # __call__()-method would be substituted a second time!
        if cls.__call__.__code__ != wrap_parser(cls.__call__).__code__:
            cls.__call__ = wrap_parser(cls.__call__)
        super(ParserMetaClass, cls).__init__(name, bases, attrs)


def sane_parser_name(name):
    """"Checks whether given name is an acceptable parser name. Parser names
    must not be preceeded or succeeded by a double underscore '__'!
    """
    return name and name[:2] != '__' and name[-2:] != '__'


class Parser(metaclass=ParserMetaClass):
    def __init__(self, name=None):
        assert name is None or isinstance(name, str), str(name)
        self.name = name or ''
        self.headquarter = None          # head quater for global variables etc.
        self.visited = dict()
        self.recursion_counter = dict()
        self.cycle_detection = set()

    def __call__(self, text):
        raise NotImplementedError

    def __str__(self):
        return self.name or self.__class__.__name__

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


class ParserHeadquarter:
    root__ = None   # should be overwritten by grammar subclass

    @classmethod
    def _assign_parser_names(cls):
        """Initializes the `parser.name` fields of those
        Parser objects that are directly assigned to a class field with
        the field's name, e.g.
            class Grammar(ParserHeadquarter):
                ...
                symbol = RE('(?!\\d)\\w+')
        After the call of this method symbol.name == "symbol"
        holds. If the `name` field has been assigned a different
        name in the constructor, a ValueError will be raised.
        """
        if cls.parser_initialization__ == "done":
            return
        cdict = cls.__dict__
        for entry in cdict:
            if sane_parser_name(entry):
                parser = cdict[entry]
                if isinstance(parser, Parser):
                    # print(type(parser), parser.name, entry)
                    if isinstance(parser, Forward):
                        assert not parser.name or parser.name == entry
                        if parser.name and parser.name != entry:
                            raise ValueError(("Parser named %s should not be "
                                " assigned to field with different name: %s"
                                % (parser.name, entry)))
                        parser.parser.name = entry
                    else:
                        parser.name = entry
        cls.parser_initialization__ = "done"

    def __init__(self):
        self._assign_parser_names()
        self.root__ = copy.deepcopy(self.__class__.root__)
        self.root__.apply(self._add_parser)
        self.variables = dict()                 # support for Pop and Retrieve operators
        self.last_node = None
        self.call_stack = []
        self.moving_forward = True
        self.unused = True

    def _add_parser(self, parser):
        """Adds the copy of the parser object to this instance of ParserHeadquarter.
        """
        # print(parser.name)
        if sane_parser_name(parser.name):  # overwrite class variable with instance variable
            setattr(self, parser.name, parser)
        parser.headquarter = self

    def parse(self, document):
        """Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
        Returns:
            Node: The root node ot the parse tree.
        """
        assert self.unused, ("Parser has been used up. Please create a new "
                             "instance of the ParserHeadquarter class!")
        if self.root__ is None:
            raise NotImplementedError()
        self.unused = False
        parser = self.root__
        result = ""
        stitches = []
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


ZOMBIE_PARSER = Parser(name="Zombie")   # zombie object to avoid distinction of cases
                                        # for the Node.parser variable
RE_WSPC = Parser(WHITESPACE_KEYWORD)    # Dummy Parser for comments that were captured
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
    def __init__(self, regexp, orig_re = '', name=None):
        super(RegExp, self).__init__(name)
        # self.name = name
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp
        self.orig_re = orig_re

    def __deepcopy__(self, memo):
        # this method is obsolete with the new `regex` module!
        try:
            regexp = copy.deepcopy(self.regexp)
        except TypeError:
            regexp = self.regexp.pattern
        duplicate = RegExp(self.name, regexp, self.orig_re)
        duplicate.name = self.name  # this ist needed!!!!
        duplicate.regexp = self.regexp
        duplicate.orig_re = self.orig_re
        duplicate.headquarter = self.headquarter
        duplicate.visited = copy.deepcopy(self.visited, memo)
        duplicate.recursion_counter = copy.deepcopy(self.recursion_counter,
                                                    memo)
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
        pattern = self.orig_re or self.regexp.pattern  # for readability of error messages !
        return Parser.__str__(self) + "/" + pattern + "/"


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


def RE(regexp, wL='', wR='', name=None):
    rA = '('
    rB = '\n)' if regexp.find('(?x)') >= 0 else ')'     # otherwise the closing bracket might erroneously
                                                        # be append to the end of a line comment!
    return RegExp(wL + rA + regexp + rB + wR, regexp,
                  name or TOKEN_KEYWORD)


def Token(token, wL='', wR='', name=None):
    return RE(escape_re(token), wL, wR, name)


##############################################################################
#
# Combinator parser classes (i.e. trunk classes of the parser tree)
#
##############################################################################


class UnaryOperator(Parser):
    def __init__(self, parser, name=None):
        super(UnaryOperator, self).__init__(name)
        assert isinstance(parser, Parser)
        self.parser = parser

    def apply(self, func):
        if super(UnaryOperator, self).apply(func):
            self.parser.apply(func)

    # def __str__(self):
    #     return Parser.__str__(self) + \
    #            ("" if self.name else "(" + str(self.parser) + ")")


class NaryOperator(Parser):
    def __init__(self, *parsers, name=None):
        super(NaryOperator, self).__init__(name)
        assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        self.parsers = parsers

    def apply(self, func):
        if super(NaryOperator, self).apply(func):
            for parser in self.parsers:
                parser.apply(func)

    # def __str__(self):
    #     return Parser.__str__(self) + \
    #            ("" if self.name else str([str(p) for p in self.parsers]))
    #     # return "(" + ",\n".join(["\n    ".join(str(parser).split("\n"))
    #     #                          for parser in self.parsers]) + ")"


class Optional(UnaryOperator):
    def __init__(self, parser, name=None):
        super(Optional, self).__init__(parser, name)
        assert isinstance(parser, Parser)
        assert not isinstance(parser, Optional), \
            "Nesting options would be redundant: %s(%s)" % \
            (str(name), str(parser.name))
        assert not isinstance(parser, Required), \
            "Nestion options with required elements is contradictory: " \
            "%s(%s)" % (str(name), str(parser.name))

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
    def __init__(self, parser, name=None):
        super(OneOrMore, self).__init__(parser, name)
        assert not isinstance(parser, Optional), \
            "Use ZeroOrMore instead of nesting OneOrMore and Optional: " \
            "%s(%s)" % (str(name), str(parser.name))

    def __call__(self, text):
        results = ()
        text_ = text
        while text_:
            node, text_ = self.parser(text_)
            if not node:
                break
            results += (node,)
        if results == ():       # TODO: Add debugging print statements or breakpoint for `Bedeutungsposition` here!!
            return None, text
        return Node(self, results), text_


class Sequence(NaryOperator):
    def __init__(self, *parsers, name=None):
        super(Sequence, self).__init__(*parsers, name=name)
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


##############################################################################
#
# Flow control operators
#
##############################################################################


class FlowOperator(UnaryOperator):
    def __init__(self, parser, name=None):
        super(FlowOperator, self).__init__(parser, name)


class Required(FlowOperator):
    # TODO: Add constructor that checks for logical errors, like `Required(Optional(...))` constructs
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
            node.fatal_error = True
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
        yield node                                          # for well-formed EBNF code
        node = node.children[-1] if node.children else None


class Lookbehind(FlowOperator):
    def __init__(self, parser, name=None):
        super(Lookbehind, self).__init__(parser, name)
        print("WARNING: Lookbehind Operator is experimental!")

    def __call__(self, text):
        if isinstance(self.headquarter.last_node, Lookahead):
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
        for node in iter_right_branch(self.headquarter.last_node):
            if node.parser.name == self.parser.name:
                return True
        if node and isinstance(self.parser, RegExp) and \
                self.parser.regexp.match(str(node)):    # Is there really a use case for this?
            return True
        return False


class NegativeLookbehind(Lookbehind):
    def sign(self, bool_value):
        return not bool_value


##############################################################################
#
# Capture and Retrieve operators (for passing variables in the parser)
#
##############################################################################


class Capture(UnaryOperator):
    def __init__(self, parser, name=None):
        super(Capture, self).__init__(parser, name)

    def __call__(self, text):
        node, text = self.parser(text)
        if node:
            stack = self.headquarter.variables.setdefault(self.name, [])
            stack.append(str(node))
        return Node(self, node), text


class Retrieve(Parser):
    def __init__(self, symbol, name=None):
        super(Retrieve, self).__init__(name)
        self.symbol = symbol  # if isinstance(symbol, str) else symbol.name

    def __call__(self, text):
        symbol = self.symbol if isinstance(self.symbol, str) \
                             else self.symbol.name
        stack = self.headquarter.variables[symbol]
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
        self.name = parser.name  # redundant, because of constructor of ParserHeadquarter
        self.parser = parser

    def apply(self, func):
        if super(Forward, self).apply(func):
            assert not self.visited
            self.parser.apply(func)


PARSER_SYMBOLS = {'RegExp', 'mixin_comment', 'RE', 'Token', 'Required',
                  'Lookahead', 'NegativeLookahead', 'Optional',
                  'Lookbehind', 'NegativeLookbehind',
                  'ZeroOrMore', 'Sequence', 'Alternative', 'Forward',
                  'OneOrMore', 'ParserHeadquarter', 'Capture', 'Retrieve',
                  'Pop'}


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
        transtable (dict): A dictionary that assigns a transformation
                transformation functions to parser name strings.
    """
    # normalize transformation entries by turning single transformations
    # into lists with a single item
    table = {name: transformation
             if isinstance(transformation, collections.abc.Sequence)
             else [transformation]
             for name, transformation in list(transtable.items())}
    table = expand_table(table)

    def recursive_ASTTransform(node):
        if node.children:
            for child in node.result:
                recursive_ASTTransform(child)
        transformation = table.get(node.parser.name,
                                   table.get('*', [lambda nd: None]))
        for transform in transformation:
            transform(node)

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
    (In case the descendant's name is empty (i.e. anonymous) the
    name of this node's parser is kept.)
    """
    if node.children and len(node.result) == 1:
        if not node.result[0].parser.name:
            node.result[0].parser.name = node.parser.name
        node.parser = node.result[0].parser
        node.errors.extend(node.result[0].errors)
        node.result = node.result[0].result


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
    """Recursively flattens all unnamed sub-nodes, in case there is more
    than one sub-node present. Flattening means that
    wherever a node has child nodes, the child nodes are inserted in place
    of the node. In other words, all leaves of this node and its child nodes
    are collected in-order as direct children of this node.
    This is meant to achieve the following structural transformation:
    X (+ Y + Z)  ->   X + Y + Z
    """
    if len(node.children) >= 2:
        new_result = []
        for child in node.result:
            if not child.parser.name:
                flatten(child)
                new_result.extend(child.result)
            else:
                new_result.append(child)
        node.result = tuple(new_result)


def remove_tokens(node, tokens):
    """Reomoves any of a set of tokens whereever they appear in the result
    of the node.
    """
    if node.children:
        node.result = tuple(child for child in node.result
                            if child.parser.name != TOKEN_KEYWORD or
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
        comp, cls = node.parser.name, node.parser.__class__.__name__
        elem = comp or cls
        if not sane_parser_name(elem):
            node.add_error("Must not use reserved name '%s' as parser "
                           "name! " % elem + "(Any name starting with "
                           "'_' or '__' or ending with '__' is reserved.)")
            return None
        else:
            compiler = self.__getattribute__(elem)  # TODO Add support for python keyword attributes
            return compiler(node)


def full_compilation(source, parser_HQ, AST_transformations, compiler):
    """Compiles a source in three stages:
        1. Parsing
        2. AST-transformation
        3. Compiling.
    The compilations stage is only invoked if no errors occurred in either of
    the two previous stages.

    Args:
        source (str):                the input source for compilation
        parser_HQ (ParserHQ):        the ParserHeadquarter object
        AST_transformations (dict):  a table that assigns AST transformation
                functions to parser names (see function ASTTransform)
        compiler (object):  an instance of a class derived from `CompilerBase`
                with a suitable method for every parser name or class.
    Returns:
        tuple: (result (?), messages (str), syntax_tree (Node))
            Result as returned by the compiler or `None` if an error occurred
            during parsing or AST-transformation and the compiler wasn't
            invoked; error messages; abstract syntax tree
    """
    assert isinstance(compiler, CompilerBase)

    syntax_tree = parser_HQ.parse(source)
    DEBUG_DUMP_SYNTAX_TREE(parser_HQ, syntax_tree, compiler, ext='.cst')

    errors = syntax_tree.collect_errors(clear=True)
    assert errors or str(syntax_tree) == source
    # only compile if there were no snytax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    if not errors:
        ASTTransform(syntax_tree, AST_transformations)
        DEBUG_DUMP_SYNTAX_TREE(parser_HQ, syntax_tree, compiler, ext='.ast')
        result = compiler.compile__(syntax_tree)
        errors.extend(syntax_tree.collect_errors(clear=True))
    else:
        result = None
    errors.sort()
    messages = error_messages(source, errors)
    return result, messages, syntax_tree


COMPILER_SYMBOLS = {'CompilerBase', 'Error', 'Node', 're'}


##############################################################################
#
# EBNF-Grammar-Compiler
#
##############################################################################


class EBNFGrammar(ParserHeadquarter):
    r"""Parser for an EBNF source file, with this grammar:

    # EBNF-Grammar in EBNF

    @ comment    =  /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
    @ whitespace =  /\s*/                            # whitespace includes linefeed
    @ literalws  =  right                            # trailing whitespace of literals will be ignored tacitly

    syntax     =  [~//] { definition | directive } §EOF
    definition =  symbol §"=" expression
    directive  =  "@" §symbol §"=" ( regexp | literal | list_ )

    expression =  term { "|" term }
    term       =  { factor }+
    factor     =  [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
                | [flowmarker] literal
                | [flowmarker] regexp
                | [flowmarker] group
                | [flowmarker] oneormore
                | repetition
                | option

    flowmarker =  "!"  | "&"  | "§" |                # '!' negative lookahead, '&' positive lookahead, '§' required
                  "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
    retrieveop =  "::" | ":"                         # '::' pop, ':' retrieve

    group      =  "(" expression §")"
    option     =  "[" expression §"]"
    oneormore  =  "{" expression "}+"
    repetition =  "{" expression §"}"

    symbol     =  /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
    literal    =  /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
                | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
    regexp     =  /~?\/(?:[^\/]|(?<=\\)\/)*\/~?/~    # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                     # '~' is a whitespace-marker, if present leading or trailing
                                                     # whitespace of a regular expression will be ignored tacitly.
    list_      =  /\w+\s*(?:,\s*\w+\s*)*/~           # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                     # BEGIN_QUOTE, END_QUOTE ; see CommonMark/markdown.py for an exmaple
    EOF =  !/./
    """
    expression = Forward()
    source_hash__ = "205fd680c1c77175b9b9807ea4b96160"
    parser_initialization__ = "upon instatiation"
    wsp__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    EOF = NegativeLookahead(RE('.'))
    list_ = RE('\\w+\\s*(?:,\\s*\\w+\\s*)*', wR=wsp__)
    regexp = RE('~?/(?:[^/]|(?<=\\\\)/)*/~?', wR=wsp__)
    literal = Alternative(RE('"(?:[^"]|\\\\")*?"', wR=wsp__), RE("'(?:[^']|\\\\')*?'", wR=wsp__))
    symbol = RE('(?!\\d)\\w+', wR=wsp__)
    repetition = Sequence(Token("{", wR=wsp__), expression, Required(Token("}", wR=wsp__)))
    oneormore = Sequence(Token("{", wR=wsp__), expression, Token("}+", wR=wsp__))
    option = Sequence(Token("[", wR=wsp__), expression, Required(Token("]", wR=wsp__)))
    group = Sequence(Token("(", wR=wsp__), expression, Required(Token(")", wR=wsp__)))
    retrieveop = Alternative(Token("::", wR=wsp__), Token(":", wR=wsp__))
    flowmarker = Alternative(Token("!", wR=wsp__), Token("&", wR=wsp__), Token("§", wR=wsp__), Token("-!", wR=wsp__),
                             Token("-&", wR=wsp__))
    factor = Alternative(
        Sequence(Optional(flowmarker), Optional(retrieveop), symbol, NegativeLookahead(Token("=", wR=wsp__))),
        Sequence(Optional(flowmarker), literal), Sequence(Optional(flowmarker), regexp),
        Sequence(Optional(flowmarker), group), Sequence(Optional(flowmarker), oneormore), repetition, option)
    term = OneOrMore(factor)
    expression.set(Sequence(term, ZeroOrMore(Sequence(Token("|", wR=wsp__), term))))
    directive = Sequence(Token("@", wR=wsp__), Required(symbol), Required(Token("=", wR=wsp__)),
                         Alternative(regexp, literal, list_))
    definition = Sequence(symbol, Required(Token("=", wR=wsp__)), expression)
    syntax = Sequence(Optional(RE('', wL=wsp__)), ZeroOrMore(Alternative(definition, directive)), Required(EOF))
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
        [replace_by_single_child, flatten],  # supports both idioms:  "{ factor }+" and "factor { factor }"
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


def md5(*txt):
    """Returns the md5-checksum for `txt`. This can be used to test if
    some piece of text, for example a grammar source file, has changed.
    """
    md5_hash = hashlib.md5()
    for t in txt:
        md5_hash.update(t.encode('utf8'))
    return md5_hash.hexdigest()


class EBNFCompiler(CompilerBase):
    """Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.
    """
    # RX_DIRECTIVE = re.compile('(?:#|@)\s*(?P<key>\w*)\s*=\s*(?P<value>.*)')  # old, can be removed!
    RESERVED_SYMBOLS = {TOKEN_KEYWORD, WHITESPACE_KEYWORD}
    KNOWN_DIRECTIVES = {'comment', 'whitespace', 'tokens', 'literalws'}
    VOWELS           = {'A', 'E', 'I', 'O', 'U'}  # what about cases like 'hour', 'universe' etc. ?
    AST_ERROR        = "Badly structured syntax tree. " \
                       "Potentially due to erroneuos AST transformation."
    PREFIX_TABLE     = [('§', 'Required'), ('&', 'Lookahead'),
                        ('!', 'NegativeLookahead'), ('-&', 'Lookbehind'),
                        ('-!', 'NegativeLookbehind'), ('::', 'Pop'),
                        (':', 'Retrieve')]

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
        self.curr_name = str(None)
        self.recursive = set()
        self.root = ""
        self.directives = {'whitespace': '\s*',
                           'comment': '',
                           'literalws': ['wR=' + WHITESPACE_KEYWORD]}

    def gen_scanner_skeleton(self):
        name = self.grammar_name + "Scanner"
        return "def %s(text):\n    return text\n" % name

    def gen_AST_skeleton(self):
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

    def gen_compiler_skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_Compiler_Skeleton()"!')
        compiler = ['class ' + self.grammar_name + 'Compiler(CompilerBase):',
                    '    """Compiler for the abstract-syntax-tree of a ' +
                    self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self, grammar_name="' +
                    self.grammar_name + '"):',
                    '        super(' + self.grammar_name +
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

    def gen_parser(self, definitions):
        # fix capture of variables that have been defined before usage [sic!]
        if self.variables:
            for i in range(len(definitions)):
                if definitions[i][0] in self.variables:
                    definitions[i] = (definitions[i][0], 'Capture(%s, "%s")' %
                                      (definitions[1], definitions[0]))

        self.definition_names = [defn[0] for defn in definitions]
        definitions.append((WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace="
                             "r'{whitespace}', comment=r'{comment}')").
                            format(**self.directives)))

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class
        article = 'an ' if self.grammar_name[0:1].upper() \
                in EBNFCompiler.VOWELS else 'a '
        declarations = ['class ' + self.grammar_name +
                        'Grammar(ParserHeadquarter):',
                        'r"""Parser for ' + article + self.grammar_name +
                        ' source file' +
                        (', with this grammar:' if self.source_text else '.')]
        definitions.append(('parser_initialization__', '"upon instatiation"'))
        if self.source_text:
            definitions.append(('source_hash__',
                                '"%s"' % md5(self.source_text, __version__)))
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

    def syntax(self, node):
        self._reset()
        definitions = []

        # drop the wrapping sequence node
        if isinstance(node.parser, Sequence) and \
                isinstance(node.result[0].parser, ZeroOrMore):
            node = node.result[0]

        # compile definitions and directives and collect definitions
        for nd in node.result:
            if nd.parser.name == "definition":
                definitions.append(self.compile__(nd))
            else:
                assert nd.parser.name == "directive", nd.as_sexpr()
                self.compile__(nd)

        return self.gen_parser(definitions)

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
            self.curr_name = '"' + rule + '"'
            self.rules.add(rule)
            defn = self.compile__(node.result[1])
            if rule in self.variables:
                defn = 'Capture(%s, "%s")' % (defn, rule)
                self.variables.remove(rule)
        except TypeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + node.as_sexpr()
            node.add_error(errmsg)
            rule, defn = rule + ':error', '"' + errmsg + '"'
        return (rule, defn)

    @staticmethod
    def _check_rx(node, rx):
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
            conv = {'left': 'wL=' + WHITESPACE_KEYWORD,
                    'right': 'wR=' + WHITESPACE_KEYWORD}
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

    def _current_name(self):
        # if self.curr_name in {'', str(None)}:
        #     name = []
        # else:
        #     name = ["name=" + self.curr_name]
        name = []  # turn explicit names declaration off
        self.curr_name = str(None)
        return name

    def non_terminal(self, node, parser_class):
        """Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        name = self._current_name()
        arguments = filter(lambda arg: arg,
                           [self.compile__(r) for r in node.result] + name)
        return parser_class + '(' + ', '.join(arguments) + ')'

    def expression(self, node):
        return self.non_terminal(node, 'Alternative')

    def term(self, node):
        return self.non_terminal(node, 'Sequence')

    def factor(self, node):
        assert isinstance(node.parser, Sequence), node.as_sexpr()  # these assert statements can be removed
        assert node.children
        assert len(node.result) >= 2, node.as_sexpr()
        prefix = node.result[0].result

        arg = node.result[-1]
        if prefix in {'::', ':'}:
            assert len(node.result) == 2
            if arg.parser.name != 'symbol':
                node.add_error(('Retrieve Operator "%s" requires a symbols, '
                                'and not a %s.') % (prefix, str(arg.parser)))
                return str(arg.result)
            self.variables.add(arg.result)

        if len(node.result) > 2:
            # shift = (Node(node.parser, node.result[1].result),)
            # node.result[1].result = shift + node.result[2:]
            node.result[1].result = (Node(node.result[1].parser,
                                          node.result[1].result),) \
                                    + node.result[2:]
            node.result[1].parser = node.parser
            node.result = (node.result[0], node.result[1])

        node.result = node.result[1:]
        for match, parser_class in self.PREFIX_TABLE:
            if prefix == match:
                return self.non_terminal(node, parser_class)

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

    def literal(self, node):
        name = self.directives["literalws"] + self._current_name()
        return 'Token(' + ', '.join([node.result] + name) + ')'

    def regexp(self, node):
        name = self._current_name()
        rx = node.result
        if rx[:2] == '~/':
            name = ['wL=' + WHITESPACE_KEYWORD] + name
            rx = rx[1:]
        if rx[-2:] == '/~':
            name = ['wR=' + WHITESPACE_KEYWORD] + name
            rx = rx[:-1]
        try:
            arg = repr(self._check_rx(node, rx[1:-1].replace(r'\/', '/')))
        except AttributeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + \
                     node.as_sexpr()
            node.add_error(errmsg)
            return '"' + errmsg + '"'
        return 'RE(' + ', '.join([arg] + name) + ')'

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
    else:
        parser = None
    return parser


def get_grammar_instance(grammar):
    """Returns a grammar object and the source code of the grammar, from
    the given `grammar`-data which can be either a file name, ebnf-code,
    python-code, a ParserHeadquarter-derived grammar class or an instance of
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
        # assume that dsl_grammar is a ParserHQ-object or Grammar class
        grammar_src = ''
        if isinstance(grammar, ParserHeadquarter):
            parser_root = grammar
        else:
            # assume `grammar` is a grammar class and get the root object
            parser_root = grammar()
    return parser_root, grammar_src


def load_compiler_suite(compiler_suite):
    """
    """
    global DELIMITER
    assert isinstance(compiler_suite, str)
    source = load_if_file(compiler_suite)
    if is_python_code(compiler_suite):
        scanner_py, parser_py, ast_py, compiler_py = source.split(DELIMITER)
        scanner = compile_python_object(scanner_py, 'Scanner')
        ast = compile_python_object(ast_py, 'TransTable')
        compiler = compile_python_object(compiler_py, 'Compiler')
    else:
        # assume source is an ebnf grammar
        parser_py, errors, AST = full_compilation(
                source, EBNFGrammar(), EBNFTransTable, EBNFCompiler())
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


def run_compiler(source_file, compiler_suite="", extension=".dst"):
    """Compiles the a source file with a given compiler and writes the result
     to a file. If no `compiler_suite` is given it is assumed that the source
     file is an EBNF grammar. In this case the result will be a Python
     script containing a parser for that grammar as well as the skeletons
     for a scanner, AST transformation table, and compiler. If the Python
     script already exists only the parser name in the script will be
     updated. (For this to work, the different names need to be delimited
     by the standard `DELIMITER`-line!).
     `run_compiler()` returns a list of error messages or an empty list if no
     errors occured.
     """
    filepath = os.path.normpath(source_file)
    with open(source_file, encoding="utf-8") as f:
        source = f.read()
    rootname = os.path.splitext(filepath)[0]
    if compiler_suite:
        scanner, parser, trans, cclass = load_compiler_suite(compiler_suite)
        compiler = cclass()
    else:
        scanner = nil_scanner
        parser = EBNFGrammar()
        trans = EBNFTransTable
        compiler = EBNFCompiler(os.path.basename(rootname), source)
    global DEBUG_DUMP_AST
    DEBUG_DUMP_AST = rootname
    result, errors, ast = full_compilation(scanner(source), parser,
                                           trans, compiler)
    if errors:
        return errors

    elif trans == EBNFTransTable:  # either an EBNF- or no compiter suite given
        f = None

        global DELIMITER
        try:
            f = open(rootname + '_compiler.py', 'r', encoding="utf-8")
            source = f.read()
            scanner, parser, ast, compiler = source.split(DELIMITER)
        except (PermissionError, FileNotFoundError, IOError) as error:
            scanner = compiler.gen_scanner_skeleton()
            ast = compiler.gen_AST_skeleton()
            compiler = compiler.gen_compiler_skeleton()
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
        try:
            f = open(rootname + extension, 'w', encoding="utf-8")
            f.write(result.as_sexpr(source))
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:  f.close()
        if DEBUG:
            print(ast)

    return []


def has_source_changed(grammar_source, grammar_class):
    """Returns `True` if `grammar_class` does not reflect the latest
    changes of `grammar_source`

    :param grammar_source: file name or string representation of the
        grammar source
    :param grammar_class: the parser class representing the grammar
        or the file name of a compiler suite containing the grammar
    :return:    True, if the source text of the grammar is different
        from the source from which the grammar class was generated
    """
    grammar = load_if_file(grammar_source)
    chksum = md5(grammar, __version__)
    if isinstance(grammar_class, str):
        # grammar_class = load_compiler_suite(grammar_class)[1]
        with open(grammar_class, 'r', encoding='utf8') as f:
            pycode = f.read()
        m = re.search('class \w*\(ParserHeadquarter\)', pycode)
        if m:
            m = re.search('    source_hash__ *= *"([a-z0-9]*)"',
                          pycode[m.span()[1]:])
            return not (m and m.groups() and m.groups()[-1] == chksum)
        else:
            return True
    else:
        return chksum != grammar_class.source_hash__


##############################################################################
#
# system test
#
##############################################################################


def test(file_name):
    print(file_name)
    with open('examples/' + file_name, encoding="utf-8") as f:
        grammar = f.read()
    compiler_name = os.path.basename(os.path.splitext(file_name)[0])
    compiler = EBNFCompiler(compiler_name, grammar)
    result, errors, syntax_tree = full_compilation(grammar,
            EBNFGrammar(), EBNFTransTable, compiler)
    # print(syntax_tree.as_xml())
    # print(result)
    # print(syntax_tree.as_sexpr(grammar))
    # print(errors)
    # print(compiler.gen_AST_Skeleton())
    # print(compiler.gen_Compiler_Skeleton())
    result = compileDSL(grammar, result, EBNFTransTable, compiler)
    print(result)
    return result


# Changes in the EBNF source that are not reflected in this file usually are
# a source of sometimes obscure errors! Therefore, we will check this.
if (os.path.exists('examples/EBNF/EBNF.ebnf')
    and has_source_changed('examples/EBNF/EBNF.ebnf', EBNFGrammar)):
#    assert False, "WARNING: Grammar source has changed. The parser may not " \
#        "represent the actual grammar any more!!!"
    pass

if __name__ == "__main__":
    print(sys.argv)
    if len(sys.argv) > 1:
        _errors = run_compiler(sys.argv[1],
                               sys.argv[2] if len(sys.argv) > 2 else "")
        if (_errors):
            print(_errors)
            sys.exit(1)
    else:
        # self-test
        test('EBNF/EBNF.ebnf')
