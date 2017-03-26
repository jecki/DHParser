#!/usr/bin/python3

"""ParserCombinators.py - parser combinators for left-recursive grammers

Copyright 2016  by Eckhart Arnold

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.


Module parser_combinators contains a number of classes that together
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

# TODO: Replace copy.deepcopy() call in GrammarBase class by custom copy()-methods in the Parser classes. Is that really better?


import collections
import copy
from functools import partial
import hashlib
import keyword
import os
from typing import NamedTuple
try:
    import regex as re
except ImportError:
    import re
import sys


__version__ = '0.5.3' + '_dev' + str(os.stat(__file__).st_mtime)


DEBUG = "DEBUG"


def DEBUG_DIR():
    """Returns a path of a directory where debug files will be stored.
    Usually, this is just a sub-directory named 'DEBUG'. The directory
    will be created if it does not exist.
    """
    global DEBUG
    if not DEBUG:
        raise AssertionError("Cannot use DEBUG_DIR() if debugging is turned off!")
    dirname = DEBUG
    if os.path.exists(DEBUG):
        if not os.path.isdir(DEBUG):
            raise IOError('"' + DEBUG + '" cannot be used as debug directory, '
                          'because it is not a directory!')
    else:
        os.mkdir(DEBUG)
    return dirname


def DEBUG_FILE_NAME(grammar_base):
    """Returns a file name without extension based on the class name of
     the ``grammar_base``-object.
     """
    name = grammar_base.__class__.__name__
    return name[:-7] if name.endswith('Grammar') else name



########################################################################
#
# Scanner / Preprocessor support
#
########################################################################


RX_SCANNER_TOKEN = re.compile('\w+')
BEGIN_SCANNER_TOKEN = '\x1b'
END_SCANNER_TOKEN = '\x1c'


def make_token(token, argument=''):
    """Turns the ``token`` and ``argument`` into a special token that
    will be caught by the `ScannerToken`-parser.
    """
    assert RX_SCANNER_TOKEN.match(token)
    assert argument.find(BEGIN_SCANNER_TOKEN) < 0
    assert argument.find(END_SCANNER_TOKEN) < 0

    return BEGIN_SCANNER_TOKEN + token + argument + END_SCANNER_TOKEN


nil_scanner = lambda text: text



########################################################################
#
# Parser tree
#
########################################################################


def line_col(text, pos):
    """Returns the position within a text as (line, column)-tuple.
    """
    assert pos < len(text)
    line = text.count("\n", 0, pos) + 1
    column = pos - text.rfind("\n", 0, pos)
    return line, column


class ZombieParser:
    """
    Serves as a substitute for a Parser instance.

    ``ZombieParser`` is the class of the singelton object
    ``ZOMBIE_PARSER``. The  ``ZOMBIE_PARSER`` has a name and can be
    called, but it never matches. It serves as a substitute where only
    these (or one of these properties) is needed, but no real Parser-
    object is instantiated.
    """
    alive = False
    def __init__(self):
        assert not self.__class__.alive, "There can be only one!"
        assert self.__class__ == ZombieParser, "No derivatives, please!"
        self.name = "ZOMBIE"
        self.__class__.alive = True

    def __str__(self):
        return self.name

    def __call__(self, text):
        """Better call Saul ;-)"""
        return None, text


ZOMBIE_PARSER = ZombieParser()


class Error(NamedTuple):
    pos: int
    msg: str


class Node:
    """
    Represents a node in the concrete or abstract syntax tree.

    Attributes:
        tag_name (str):  The name of the node, which is either its
            parser's name or, if that is empty, the parser's class name
        result (str or tuple):  The result of the parser which
            generated this node, which can be either a string or a
            tuple of child nodes.
        children (tuple):  The tuple of child nodes or an empty tuple
            if there are no child nodes. READ ONLY!
        parser (Parser):  The parser which generated this node.
        errors (list):  A list of parser- or compiler-errors:
            tuple(position, string) attached to this node
        len (int):  The full length of the node's string result if the
            node is a leaf node or, otherwise, the concatenated string
            result's of its descendants. The figure always represents
            the length before AST-transformation ans will never change
            through AST-transformation. READ ONLY!
        pos (int):  the position of the node within the parsed text.

            The value of ``pos`` is zero by default and it will be
            updated if the node or any of its parents is attached
            to a new parent.

            From the point of view of a client, this value should
            be considered READ ONLY. At any rate, it should only be
            reassigned only during parsing stage and never during or
            after the AST-transformation.
    """

    def __init__(self, parser, result):
        """Initializes the ``Node``-object with the ``Parser``-Instance
        that generated the node and the parser's result.
        """
        self.result = result
        self.parser = parser or ZOMBIE_PARSER
        self._errors = []
        self.error_flag = any(r.error_flag for r in self.result) if self.children else False
        self._len = len(self.result) if not self.children else \
            sum(child._len for child in self.result)
        self.pos = 0

    def __str__(self):
        if self.children:
            return "".join([str(child) for child in self.result])
        return str(self.result)

    @property
    def tag_name(self):
        return self.parser.name or self.parser.__class__.__name__

    @property
    def result(self):
        return self._result

    @result.setter
    def result(self, result):
        assert ((isinstance(result, tuple) and all(isinstance(child, Node) for child in result))
                or isinstance(result, Node)
                or isinstance(result, str)), str(result)
        self._result = (result,) if isinstance(result, Node) else result or ''
        self._children = self._result if isinstance(self._result, tuple) else ()

    @property
    def children(self):
        return self._children

    @property
    def len(self):
        return self._len

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, pos):
        self._pos = pos
        offset = 0
        for child in self.children:
            child.pos = pos + offset
            offset += child.len

    @property
    def errors(self):
        return [Error(self.pos, err) for err in self._errors]

    def _tree_repr(self, tab, openF, closeF, dataF=lambda s: s):
        """
        Generates a tree representation of this node and its children
        in string from.

        The kind ot tree-representation that is determined by several
        function parameters. This could be an XML-representation or a
        lisp-like S-expression.

        Parameters:
            tab (str):  The indentation string, e.g. '\t' or '    '
            openF:  (Node->str) A function that returns an opening
                string (e.g. an XML-tag_name) for a given node
            closeF:  (Node->str) A function that returns a closeF
                string (e.g. an XML-tag_name) for a given node.
            dataF:  (str->str) A function that filters the data string
                before printing, e.g. to add quotation marks

        Returns (str):
            A string that contains a (serialized) tree representation
            of the node and its children.
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
                subtree = child._tree_repr(tab, openF, closeF, dataF).split('\n')
                content.append('\n'.join((tab + s) for s in subtree))
            return head + '\n'.join(content) + tail

        return head + '\n'.join([tab + dataF(s)
                                 for s in str(self.result).split('\n')]) + tail

    def as_sexpr(self, src=None):
        """
        Returns content as S-expression, i.e. in lisp-like form.

        Parameters:
            src:  The source text or `None`. In case the source text is
                given the position of the element in the text will be
                reported as line and column.
        """
        def opening(node):
            s = '(' + node.tag_name
            # s += " '(pos %i)" % node.pos
            if src:
                s += " '(pos %i  %i %i)" % (node.pos, *line_col(src, node.pos))
            if node.errors:
                s += " '(err '(%s))" % ' '.join(str(err).replace('"', r'\"')
                                                for err in node.errors)
            return s
        def pretty(s):
            return '"%s"' % s if s.find('"') < 0 \
                else "'%s'" % s if s.find("'") < 0 \
                else '"%s"' % s.replace('"', r'\"')
        return self._tree_repr('    ', opening, lambda node: ')', pretty)

    def as_xml(self, src=None):
        """
        Returns content as XML-tree.

        Parameters:
            src:  The source text or `None`. In case the source text is
                given the position will also be reported as line and
                column.
        """

        def opening(node):
            s = '<' + node.tag_name
            # s += ' pos="%i"' % node.pos
            if src:
                s += ' line="%i" col="%i"' % line_col(src, node.pos)
            if node.errors:
                s += ' err="%s"' % ''.join(str(err).replace('"', r'\"') for err in node.errors)
            s += ">"
            return s

        def closing(node):
            s = '</' + node.tag_name + '>'
            return s

        return self._tree_repr('    ', opening, closing)

    def add_error(self, error_str):
        self._errors.append(error_str)
        self.error_flag = True
        return self

    def collect_errors(self, clear_errors=False):
        """
        Returns all errors of this node or any child node in the form
        of a set of tuples (position, error_message), where position
        is always relative to this node.
        """
        if self.error_flag:
            errors = self.errors
            if clear_errors:
                self._errors = []
                self.error_flag = False
            if self.children:
                for child in self.result:
                    errors.extend(child.collect_errors(clear_errors))
            return errors
        return []

    def navigate(self, path):
        """EXPERIMENTAL! NOT YET TESTED!!!
        Returns the first descendant element matched by `path`, e.g.
        'd/s' returns 'l' from (d (s l)(e (r x1) (r x2))
        'e/r' returns 'x2'
        'e'   returns (r x1)(r x2)

        Parameters:
            path (str):  The path of the object, e.g. 'a/b/c'

        Returns:
            The object at the path, either a string or a Node or
            ``None``, if the path did not match.
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
    """
    Converts the list of ``errors`` collected from the root node of the
    parse tree of `text` into a human readable (and IDE or editor
    parsable text) with line an column numbers. Error messages are
    separated by an empty line.
    """
    return "\n\n".join("line: %i, column: %i, error: %s" %
                       (*line_col(text, err.pos), err.msg)
                       for err in sorted(list(errors)))


# lambda compact_sexpr s : re.sub('\s(?=\))', '', re.sub('\s+', ' ', s)).strip()



########################################################################
#
# Abstract syntax tree support
#
########################################################################


def DEBUG_DUMP_SYNTAX_TREE(grammar_base, syntax_tree, ext):
    global DEBUG
    if DEBUG:
        st_file_name = DEBUG_FILE_NAME(grammar_base) + ext
        with open(os.path.join(DEBUG_DIR(), st_file_name), "w",  encoding="utf-8") as f:
            f.write(syntax_tree.as_sexpr())


def expand_table(compact_table):
    """Expands a table by separating keywords that are tuples or strings
    containing comma separated words into single keyword entries with
    the same values. Returns the expanded table.
    Example:
    >>> expand_table({"a, b": 1, "b": 1, ('d','e','f'):5, "c":3})
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
    """Transforms the parse tree starting with the given ``node`` into
    an abstract syntax tree by calling transformation functions
    registered in the transformation dictionary ``transtable``.
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
                            table.get('~', [])) + table.get('*', [])
        for transform in transformation:
            transform(node)

    recursive_ASTTransform(node)


def no_transformation(node):
    pass


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
        node._errors.extend(node.result[0].errors)
        node.result = node.result[0].result


def reduce_single_child(node):
    """Reduce a single branch node, by transferring the result of its
    immediate descendant to this node, but keeping this node's parser entry.
    """
    if node.children and len(node.result) == 1:
        node._errors.extend(node.result[0].errors)
        node.result = node.result[0].result


# ------------------------------------------------
#
# destructive transformations:
#     - tree may be rearranged (flattened),
#     - order is preserved
#     - but (irrelevant) leaves may be dropped
#     - errors of dropped leaves will be lost
#
# ------------------------------------------------


def is_whitespace(node):
    """Removes whitespace and comments defined with the
    ``@comment``-directive."""
    return node.parser.name == WHITESPACE_KEYWORD


def is_scanner_token(node):
    return isinstance(node.parser, ScannerToken)


def is_empty(node):
    return not node.result


def is_expendable(node):
    return is_empty(node) or is_whitespace(node) or is_scanner_token(node)


def is_token(node, token_set={}):
    return node.parser.name == TOKEN_KEYWORD and (not token_set or node.result in token_set)


def remove_children_if(node, condition):
    """Removes all nodes from the result field if the function 
    ``condition(child_node)`` evaluates to ``True``."""
    if node.children:
        node.result = tuple(c for c in node.children if not condition(c))


remove_whitespace = partial(remove_children_if, condition=is_whitespace)
remove_scanner_tokens = partial(remove_children_if, condition=is_scanner_token)
remove_expendables = partial(remove_children_if, condition=is_expendable)


def remove_tokens(node, tokens=set()):
    """Reomoves any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed.
    """
    remove_children_if(node, partial(is_token, token_set=tokens))


def flatten(node):
    """Recursively flattens all unnamed sub-nodes, in case there is more
    than one sub-node present. Flattening means that
    wherever a node has child nodes, the child nodes are inserted in place
    of the node. In other words, all leaves of this node and its child nodes
    are collected in-order as direct children of this node.
    This is meant to achieve the following structural transformation:
    """
    if node.children:
        new_result = []
        for child in node.children:
            if not child.parser.name and child.children:
                assert child.children, node.as_sexpr()
                flatten(child)
                new_result.extend(child.result)
            else:
                new_result.append(child)
        node.result = tuple(new_result)


def remove_brackets(node):
    """Removes any enclosing delimiters from a structure (e.g. quotation marks
    from a literal or braces from a group).
    """
    if len(node.children) >= 3:
        assert not node.children[0].children and not node.children[-1].children, node.as_sexpr()
        node.result = node.result[1:-1]


AST_SYMBOLS = {'replace_by_single_child', 'reduce_single_child',
               'no_transformation', 'remove_children_if',
               'is_whitespace', 'is_scanner_token', 'is_expendable',
               'remove_whitespace', 'remove_scanner_tokens',
               'remove_expendables', 'flatten', 'remove_tokens',
               'remove_brackets',
               'TOKEN_KEYWORD', 'WHITESPACE_KEYWORD', 'partial'}



########################################################################
#
# Parser base classes
#
########################################################################


LEFT_RECURSION_DEPTH = 10   # because of pythons recursion depth limit, this
                            # value ought not to be set too high
MAX_DROPOUTS = 25   # stop trying to recover parsing after so many errors

WHITESPACE_KEYWORD = 'wsp__'
TOKEN_KEYWORD = 'token__'


class HistoryRecord:
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

            if grammar.track_history:
                grammar.call_stack.append(parser)
                grammar.moving_forward = True

            # run original __call__ method
            node, rest = parser_func(parser, text)

            if grammar.track_history:
                if grammar.moving_forward:  # and result[0] == None
                    grammar.moving_forward = False
                    record = HistoryRecord(grammar.call_stack.copy(), node, len(rest))
                    grammar.history.append(record)
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
        self.grammar = None          # center for global variables etc.
        self.reset()

    def reset(self):
        self.visited = dict()
        self.recursion_counter = dict()
        self.cycle_detection = set()

    def __call__(self, text):
        return None, text               # default behaviour: don't match

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
        descendendants of the tree of parsers. The same function can never
        be applied twice between calls of the ``reset()``-method!
        """
        if func in self.cycle_detection:
            return False
        else:
            self.cycle_detection.add(func)
            func(self)
            return True


class GrammarBase:
    root__ = None   # should be overwritten by grammar subclass

    @classmethod
    def _assign_parser_names(cls):
        """Initializes the `parser.name` fields of those
        Parser objects that are directly assigned to a class field with
        the field's name, e.g.
            class Grammar(GrammarBase):
                ...
                symbol = RE('(?!\\d)\\w+')
        After the call of this method symbol.name == "symbol"
        holds. Names assigned via the `name`-parameter of the
        constructor will not be overwritten.
        """
        if cls.parser_initialization__ == "done":
            return
        cdict = cls.__dict__
        for entry, parser in cdict.items():
            if isinstance(parser, Parser):
                if not parser.name or parser.name == TOKEN_KEYWORD:
                    parser.name = entry
                if (isinstance(parser, Forward) and (not parser.parser.name
                    or parser.parser.name == TOKEN_KEYWORD)):
                    parser.parser.name = entry
        cls.parser_initialization__ = "done"

    def __init__(self):
        self.all_parsers = set()
        self.dirty_flag = False
        self.track_history = DEBUG
        self._reset()
        self._assign_parser_names()
        self.root__ = copy.deepcopy(self.__class__.root__)
        if self.wspL__:
            self.wsp_left_parser__ = RegExp(self.wspL__, WHITESPACE_KEYWORD)
            self.wsp_left_parser__.grammar = self
        else:
            self.wsp_left_parser__ = ZOMBIE_PARSER
        if self.wspR__:
            self.wsp_right_parser__ = RegExp(self.wspR__, WHITESPACE_KEYWORD)
            self.wsp_right_parser__.grammar = self
        else:
            self.wsp_right_parser__ = ZOMBIE_PARSER
        self.root__.apply(self._add_parser)

    def _reset(self):
        self.variables = dict()                 # support for Pop and Retrieve operators
        self.last_node = None
        self.call_stack = []                    # support for call stack tracing
        self.history = []                       # snapshots of call stacks
        self.moving_forward = True              # also needed for call stack tracing

    def _add_parser(self, parser):
        """Adds the copy of the classes parser object to this
        particular instance of GrammarBase.
        """
        setattr(self, parser.name, parser)
        self.all_parsers.add(parser)
        parser.grammar = self

    def parse(self, document):
        """Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
        Returns:
            Node: The root node ot the parse tree.
        """
        if self.root__ is None:
            raise NotImplementedError()
        if self.dirty_flag:
            self._reset()
            for parser in self.all_parsers:
                parser.reset()
        else:
            self.dirty_flag = True
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


def DEBUG_DUMP_PARSING_HISTORY(grammar_base, document):
    def prepare_line(record):
        excerpt = document.__getitem__(slice(*record.extent))[:25].replace('\n', '\\n')
        excerpt = "'%s'" % excerpt if len(excerpt) < 25 else "'%s...'" % excerpt
        return (record.stack, record.status, excerpt)

    def write_log(history, log_name):
        path = os.path.join(DEBUG_DIR(), DEBUG_FILE_NAME(grammar_base) + log_name + "_parser.log")
        if history:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(history))
        elif os.path.exists(path):
            os.remove(path)

    global DEBUG
    if DEBUG:
        full_history, match_history, errors_only = [], [], []
        for record in grammar_base.history:
            line = ";  ".join(prepare_line(record))
            full_history.append(line)
            if record.node and record.node.parser.name != WHITESPACE_KEYWORD:
                match_history.append(line)
                if record.node.errors:
                    errors_only.append(line)
        write_log(full_history, '_full')
        write_log(match_history, '_match')
        write_log(errors_only, '_errors')


########################################################################
#
# Token and Regular Expression parser classes (i.e. leaf classes)
#
########################################################################


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
    def __init__(self, regexp, name=None):
        super(RegExp, self).__init__(name)
        self.regexp = re.compile(regexp) if isinstance(regexp, str) else regexp

    def __deepcopy__(self, memo):
        # This method is obsolete with the new `regex` module! It's
        # being kept for compatibility with Python's standard library
        try:
            regexp = copy.deepcopy(self.regexp)
        except TypeError:
            regexp = self.regexp.pattern
        duplicate = RegExp(self.name, regexp)
        duplicate.name = self.name  # this ist needed!!!!
        duplicate.regexp = self.regexp
        duplicate.grammar = self.grammar
        duplicate.visited = copy.deepcopy(self.visited, memo)
        duplicate.recursion_counter = copy.deepcopy(self.recursion_counter,
                                                    memo)
        return duplicate

    def __call__(self, text):
        match = text[0:1] != BEGIN_SCANNER_TOKEN and self.regexp.match(text)  # ESC starts a scanner token.
        if match:
            end = match.end()
            return Node(self, text[:end]), text[end:]
        return None, text


class RE(Parser):
    """Regular Expressions with optional leading or trailing whitespace.
    """
    def __init__(self, regexp, wL=None, wR=None, name=None):
        super(RE, self).__init__(name)
        # assert wR or regexp == '.' or isinstance(self, Token)
        self.wL = wL
        self.wR = wR
        self.wspLeft = RegExp(wL, WHITESPACE_KEYWORD) if wL else ZOMBIE_PARSER
        self.wspRight = RegExp(wR, WHITESPACE_KEYWORD) if wR else ZOMBIE_PARSER
        self.main = RegExp(regexp)

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


def escape_re(s):
    """Returns `s` with all regular expression special characters escaped.
    """
    assert isinstance(s, str)
    re_chars = r"\.^$*+?{}[]()#<>=|!"
    for esc_ch in re_chars:
        s = s.replace(esc_ch, '\\' + esc_ch)
    return s


def Token(token, wL=None, wR=None, name=None):
    return RE(escape_re(token), wL, wR, name or TOKEN_KEYWORD)


def mixin_comment(whitespace, comment):
    """Mixes comment-regexp into whitespace regexp.
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

    def apply(self, func):
        if super(UnaryOperator, self).apply(func):
            self.parser.apply(func)


class NaryOperator(Parser):
    def __init__(self, *parsers, name=None):
        super(NaryOperator, self).__init__(name)
        assert all([isinstance(parser, Parser) for parser in parsers]), str(parsers)
        self.parsers = parsers

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
        if results == ():
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
                self.parser.regexp.match(str(node)):    # Is there really a use case for this?
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

    def __call__(self, text):
        node, text = self.parser(text)
        if node:
            stack = self.grammar.variables.setdefault(self.name, [])
            stack.append(str(node))
        return Node(self, node), text


class Retrieve(Parser):
    def __init__(self, symbol, name=None):
        super(Retrieve, self).__init__(name)
        self.symbol = symbol  # if isinstance(symbol, str) else symbol.name

    def __call__(self, text):
        symbol = self.symbol if isinstance(self.symbol, str) \
                             else self.symbol.name
        stack = self.grammar.variables[symbol]
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


########################################################################
#
# Forward class (for recursive symbols)
#
########################################################################


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
        self.name = parser.name  # redundant, because of constructor of GrammarBase
        self.parser = parser

    def apply(self, func):
        if super(Forward, self).apply(func):
            assert not self.visited
            self.parser.apply(func)


PARSER_SYMBOLS = {'RegExp', 'mixin_comment', 'RE', 'Token', 'Required',
                  'Lookahead', 'NegativeLookahead', 'Optional',
                  'Lookbehind', 'NegativeLookbehind',
                  'ZeroOrMore', 'Sequence', 'Alternative', 'Forward',
                  'OneOrMore', 'GrammarBase', 'Capture', 'Retrieve',
                  'Pop'}


#######################################################################
#
# Syntax driven compilation support
#
#######################################################################


def sane_parser_name(name):
    """Checks whether given name is an acceptable parser name. Parser names
    must not be preceeded or succeeded by a double underscore '__'!
    """
    return name and name[:2] != '__' and name[-2:] != '__'


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


def full_compilation(source, grammar_base, AST_transformations, compiler):
    """Compiles a source in three stages:
        1. Parsing
        2. AST-transformation
        3. Compiling.
    The compilations stage is only invoked if no errors occurred in
    either of the two previous stages.

    Paraemters:
        source (str): The input text for compilation
        grammar_base (GrammarBase):  The GrammarBase object
        AST_transformations (dict):  The transformation-table that
            assigns AST transformation functions to parser names (see
            function ASTTransform)
        compiler (object):  An instance of a class derived from
            ``CompilerBase`` with a suitable method for every parser
            name or class.

    Returns (tuple):
        The result of the compilation as a 3-tuple
        (result, errors, abstract syntax tree). In detail:
        1. The result as returned by the compiler or ``None`` in case
            of failure,
        2. A list of error messages, each of which is a tuple
            (position: int, error: str)
        3. The root-node of the abstract syntax tree
    """
    assert isinstance(compiler, CompilerBase)

    syntax_tree = grammar_base.parse(source)
    DEBUG_DUMP_SYNTAX_TREE(grammar_base, syntax_tree, ext='.cst')
    DEBUG_DUMP_PARSING_HISTORY(grammar_base, source)

    assert syntax_tree.error_flag or str(syntax_tree) == source, str(syntax_tree)
    # only compile if there were no syntax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    if syntax_tree.error_flag:
        result = None
    else:
        ASTTransform(syntax_tree, AST_transformations)
        DEBUG_DUMP_SYNTAX_TREE(grammar_base, syntax_tree, ext='.ast')
        result = compiler.compile__(syntax_tree)
    errors = syntax_tree.collect_errors()
    messages = error_messages(source, errors)
    return result, messages, syntax_tree


COMPILER_SYMBOLS = {'CompilerBase', 'Node', 're'}


########################################################################
#
# EBNF-Grammar-Compiler
#
########################################################################


class EBNFGrammar(GrammarBase):
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
    source_hash__ = "1065c2e43262a5cb3aa438ec4d347c32"
    parser_initialization__ = "upon instatiation"
    wsp__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    wspL__ = ''
    wspR__ = wsp__
    EOF = NegativeLookahead(RE('.', wR=''))
    list_ = RE('\\w+\\s*(?:,\\s*\\w+\\s*)*')
    regexp = RE('~?/(?:[^/]|(?<=\\\\)/)*/~?')
    literal = Alternative(RE('"(?:[^"]|\\\\")*?"'), RE("'(?:[^']|\\\\')*?'"))
    symbol = RE('(?!\\d)\\w+')
    repetition = Sequence(Token("{"), expression, Required(Token("}")))
    oneormore = Sequence(Token("{"), expression, Token("}+"))
    option = Sequence(Token("["), expression, Required(Token("]")))
    group = Sequence(Token("("), expression, Required(Token(")")))
    retrieveop = Alternative(Token("::"), Token(":"))
    flowmarker = Alternative(Token("!"), Token("&"), Token("§"), Token("-!"), Token("-&"))
    factor = Alternative(Sequence(Optional(flowmarker), Optional(retrieveop), symbol, NegativeLookahead(Token("="))),
                         Sequence(Optional(flowmarker), literal), Sequence(Optional(flowmarker), regexp),
                         Sequence(Optional(flowmarker), group), Sequence(Optional(flowmarker), oneormore), repetition,
                         option)
    term = OneOrMore(factor)
    expression.set(Sequence(term, ZeroOrMore(Sequence(Token("|"), term))))
    directive = Sequence(Token("@"), Required(symbol), Required(Token("=")), Alternative(regexp, literal, list_))
    definition = Sequence(symbol, Required(Token("=")), expression)
    syntax = Sequence(Optional(RE('', wR='', wL=wsp__)), ZeroOrMore(Alternative(definition, directive)), Required(EOF))
    root__ = syntax


remove_enclosing_delimiters = partial(remove_tokens, tokens={})

EBNFTransTable = {
    # AST Transformations for EBNF-grammar
    "syntax":
        remove_expendables,
    "directive, definition":
        partial(remove_tokens, tokens={'@', '='}),
    "expression, chain":
        [replace_by_single_child, flatten,
         partial(remove_tokens, tokens={'|', '--'})],
    "term":
        [replace_by_single_child, flatten],  # supports both idioms:  "{ factor }+" and "factor { factor }"
    "factor, flowmarker, retrieveop":
        replace_by_single_child,
    "group":
        [remove_brackets, replace_by_single_child],
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets],
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


class EBNFCompilerError(Exception):
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
    RESERVED_SYMBOLS = {TOKEN_KEYWORD, WHITESPACE_KEYWORD}
    KNOWN_DIRECTIVES = {'comment', 'whitespace', 'tokens', 'literalws'}
    VOWELS           = {'A', 'E', 'I', 'O', 'U'}  # what about cases like 'hour', 'universe' etc.?
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
        definitions.append(('wspR__', 'wsp__' \
            if 'right' in self.directives['literalws'] else "''"))
        definitions.append(('wspL__', 'wsp__' \
            if 'left' in self.directives['literalws'] else "''"))
        definitions.append((WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace="
                             "r'{whitespace}', comment=r'{comment}')").
                            format(**self.directives)))

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class
        article = 'an ' if self.grammar_name[0:1].upper() \
                in EBNFCompiler.VOWELS else 'a '
        declarations = ['class ' + self.grammar_name +
                        'Grammar(GrammarBase):',
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
        elif not sane_parser_name(rule):
            node.add_error('Illegal symbol "%s". Symbols must not start or '
                           ' end with a doube underscore "__".' % rule)
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
            if (len(value - {'left', 'right', 'both', 'none'}) > 0
                or ('none' in value and len(value) > 1)):
                node.add_error('Directive "literalws" allows the values '
                               '`left`, `right`, `both` or `none`, '
                               'but not `%s`' % ", ".join(value))
            ws = {'left', 'right'} if 'both' in value \
                else {} if 'none' in value else value
            self.directives[key] = list(ws)

        elif key == 'tokens':
            self.scanner_tokens |= self.compile__(node.result[1])
        else:
            node.add_error('Unknown directive %s ! (Known ones are %s .)' %
                           (key,
                            ', '.join(list(EBNFCompiler.KNOWN_DIRECTIVES))))
        return ""

    def non_terminal(self, node, parser_class):
        """Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        arguments = filter(lambda arg: arg,
                           [self.compile__(r) for r in node.result])
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
        return 'Token(' + ', '.join([node.result]) + ')'

    def regexp(self, node):
        rx = node.result
        name = []
        if rx[:2] == '~/':
            if not 'left' in self.directives['literalws']:
                name = ['wL=' + WHITESPACE_KEYWORD] + name
            rx = rx[1:]
        elif 'left' in self.directives['literalws']:
            name = ["wL=''"] + name
        if rx[-2:] == '/~':
            if not 'right' in self.directives['literalws']:
                name = ['wR=' + WHITESPACE_KEYWORD] + name
            rx = rx[:-1]
        elif 'right' in self.directives['literalws']:
            name = ["wR=''"] + name
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



#######################################################################
#
# support for compiling DSLs based on an EBNF-grammar
#
#######################################################################


SECTION_MARKER = """\n
#######################################################################
#
# {marker}
#
#######################################################################
\n"""

RX_SECTION_MARKER = re.compile(SECTION_MARKER.format(marker=r'.*?SECTION.*?'))

SYMBOLS_SECTION = "SYMBOLS SECTION - Can be edited. Changes will be preserved."
SCANNER_SECTION = "SCANNER SECTION - Can be edited. Changes will be preserved."
PARSER_SECTION = "PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!"
AST_SECTION = "AST SECTION - Can be edited. Changes will be preserved."
COMPILER_SECTION = "COMPILER SECTION - Can be edited. Changes will be preserved."
END_SECTIONS_MARKER = "END OF PYDSL-SECTIONS"

# DELIMITER = "\n\n### DON'T EDIT OR REMOVE THIS LINE ###\n\n"


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


class GrammarError(Exception):
    """Raised when (already) the grammar of a domain specific language (DSL)
    contains errors.
    """
    def __init__(self, error_messages, grammar_src):
        self.error_messages = error_messages
        self.grammar_src = grammar_src


class CompilationError(Exception):
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
    python-code, a GrammarBase-derived grammar class or an instance of
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
        if isinstance(grammar, GrammarBase):
            parser_root = grammar
        else:
            # assume `grammar` is a grammar class and get the root object
            parser_root = grammar()
    return parser_root, grammar_src


def load_compiler_suite(compiler_suite):
    """
    """
    global RX_SECTION_MARKER
    assert isinstance(compiler_suite, str)
    source = load_if_file(compiler_suite)
    if is_python_code(compiler_suite):
        try:
            intro, syms, scanner_py, parser_py, ast_py, compiler_py, outro = \
                RX_SECTION_MARKER.split(source)
        except ValueError as error:
            raise ValueError('File "' + compiler_suite + '" seems to be corrupted. '
                             'Please delete or repair file manually.')
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


def run_compiler(source_file, compiler_suite="", extension=".xml"):
    """Compiles the a source file with a given compiler and writes the
    result to a file.

     If no ``compiler_suite`` is given it is assumed that the source
     file is an EBNF grammar. In this case the result will be a Python
     script containing a parser for that grammar as well as the
     skeletons for a scanner, AST transformation table, and compiler.
     If the Python script already exists only the parser name in the
     script will be updated. (For this to work, the different names
     need to be delimited section marker blocks.). `run_compiler()`
     returns a list of error messages or an empty list if no errors
     occurred.
     """
    def import_block(module, symbols):
        """Generates an Python-``import`` statement that imports all
        alls symbols in ``symbols`` (set or other container) from
        module ``module``."""
        symlist = list(symbols)
        grouped = [symlist[i:i + 4] for i in range(0, len(symlist), 4)]
        return ("\nfrom " + module + " import "
                + ', \\\n    '.join(', '.join(g) for g in grouped) + '\n\n')

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
    result, errors, ast = full_compilation(scanner(source), parser,
                                           trans, compiler)
    if errors:
        return errors

    elif trans == EBNFTransTable:  # either an EBNF- or no compiler suite given
        f = None

        global SECTION_MARKER, RX_SECTION_MARKER, SCANNER_SECTION, PARSER_SECTION, \
            AST_SECTION, COMPILER_SECTION, END_SECTIONS_MARKER
        try:
            f = open(rootname + '_compiler.py', 'r', encoding="utf-8")
            source = f.read()
            intro, syms, scanner, parser, ast, compiler, outro = RX_SECTION_MARKER.split(source)
        except (PermissionError, FileNotFoundError, IOError) as error:
            intro, outro = '', ''
            syms = import_block("PyDSL", PARSER_SYMBOLS | AST_SYMBOLS | {'CompilerBase'})
            scanner = compiler.gen_scanner_skeleton()
            ast = compiler.gen_AST_skeleton()
            compiler = compiler.gen_compiler_skeleton()
        except ValueError as error:
            raise ValueError('File "' + rootname + '_compiler.py" seems to be corrupted. '
                             'Please delete or repair file manually!')
        finally:
            if f:  f.close()

        try:
            f = open(rootname + '_compiler.py', 'w', encoding="utf-8")
            f.write(intro)
            f.write(SECTION_MARKER.format(marker=SYMBOLS_SECTION))
            f.write(syms)
            f.write(SECTION_MARKER.format(marker=SCANNER_SECTION))
            f.write(scanner)
            f.write(SECTION_MARKER.format(marker=PARSER_SECTION))
            f.write(result)
            f.write(SECTION_MARKER.format(marker=AST_SECTION))
            f.write(ast)
            f.write(SECTION_MARKER.format(marker=COMPILER_SECTION))
            f.write(compiler)
            f.write(SECTION_MARKER.format(marker=END_SECTIONS_MARKER))
            f.write(outro)
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '_compiler.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:  f.close()

    else:
        try:
            f = open(rootname + extension, 'w', encoding="utf-8")
            if isinstance(result, Node):
                f.write(result.as_xml())
            else:
                f.write(result)
        except (PermissionError, FileNotFoundError, IOError) as error:
            print('# Could not write file "' + rootname + '.py" because of: '
                  + "\n# ".join(str(error).split('\n)')))
            print(result)
        finally:
            if f:  f.close()
        if DEBUG:
            print(ast)

    return []


def source_changed(grammar_source, grammar_class):
    """Returns `True` if `grammar_class` does not reflect the latest
    changes of `grammar_source`

    Parameters:
        grammar_source:  File name or string representation of the
            grammar source
        grammar_class:  the parser class representing the grammar
            or the file name of a compiler suite containing the grammar

    Returns (bool):
        True, if the source text of the grammar is different from the
        source from which the grammar class was generated
    """
    grammar = load_if_file(grammar_source)
    chksum = md5(grammar, __version__)
    if isinstance(grammar_class, str):
        # grammar_class = load_compiler_suite(grammar_class)[1]
        with open(grammar_class, 'r', encoding='utf8') as f:
            pycode = f.read()
        m = re.search('class \w*\(GrammarBase\)', pycode)
        if m:
            m = re.search('    source_hash__ *= *"([a-z0-9]*)"',
                          pycode[m.span()[1]:])
            return not (m and m.groups() and m.groups()[-1] == chksum)
        else:
            return True
    else:
        return chksum != grammar_class.source_hash__


########################################################################
#
# system test
#
########################################################################


def test(file_name):
    global DEBUG
    DEBUG = "DEBUG"
    print(file_name)
    with open('examples/' + file_name, encoding="utf-8") as f:
        grammar = f.read()
    compiler_name = os.path.basename(os.path.splitext(file_name)[0])
    compiler = EBNFCompiler(compiler_name, grammar)
    parser = EBNFGrammar()
    result, errors, syntax_tree = full_compilation(grammar,
            parser, EBNFTransTable, compiler)
    print(result)
    if errors:
        print(errors)
        sys.exit(1)
    else:
        result = compileDSL(grammar, result, EBNFTransTable, compiler)
        print(result)
    return result


# # Changes in the EBNF source that are not reflected in this file could be
# # a source of sometimes obscure errors! Therefore, we will check this.
# if (os.path.exists('examples/EBNF/EBNF.ebnf')
#     and source_changed('examples/EBNF/EBNF.ebnf', EBNFGrammar)):
#     assert False, "WARNING: Grammar source has changed. The parser may not " \
#         "represent the actual grammar any more!!!"
#     pass

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
