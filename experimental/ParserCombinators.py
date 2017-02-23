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

"""

import collections
import copy
import keyword
import os

# try:
#     import regex as re
# except ImportError:
#     import re
import re       # for the time being use `re` although `regex` appears to be better
import sys
import types
from functools import reduce


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


class Node:
    def __init__(self, parser, result):
        assert isinstance(result, tuple) or \
               isinstance(result, Node) or \
               isinstance(result, str)
        if isinstance(result, Node):
            result = (result,)
        self.parser = parser or ZOMBIE_PARSER
        self.result = result
        self.errors = []
        self.fatalError = any(r.fatalError for r in result) if isinstance(result, tuple) else False
        self.lenCache = None

    def __str__(self):
        if isinstance(self.result, tuple):
            assert all(isinstance(child, Node) for child in self.result), str(self.result)
            return "".join([str(child) for child in self.result])
        return str(self.result)

    def as_sexpr(self):
        """Returns content as S-expression, i.e. in lisp-like form.
        """
        err = " *** " + str(self.errors) + " ***" if self.errors else ''
        head = "(" + Parser.__str__(self.parser) + err + "\n"
        tail, tab = "\n)\n", "    "
        if not self.result:
            return head[:-1] + tail[1:]
        if isinstance(self.result, tuple):
            assert all(isinstance(child, Node) for child in self.result)
            content = []
            for child in self.result:
                e = "\n".join([(tab + s).rstrip()
                               for s in child.as_sexpr().split("\n")])
                content.append(e)
            return head + ''.join(content) + tail[1:]
        return head + \
            "\n".join([tab + "'" + s + "'"
                       for s in str(self.result).split("\n")]) + tail

    def len(self):
        """Returns the string-length of this node.
        """
        if self.lenCache is None:
            self.lenCache = len(str(self))
        return self.lenCache

    def pos(self, desc_node):
        """Returns the string-position of the descendant node `desc_node`.
        Returns 0 if `self` is `desc_node` or -1 if `desc_node` is not a
        descendant.
        """
        if self == desc_node:
            return 0
        if isinstance(self.result, tuple):
            offset = 0
            for child in self.result:
                pos = child.pos(desc_node)
                if pos >= 0:
                    return offset + pos
                offset += child.len()
        return -1

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
            self.fatalError = False
        if isinstance(self.result, tuple):
            offset = 0
            for child in self.result:
                errors.extend((pos + offset, error)
                              for pos, error in child.collect_errors(clear))
                offset += child.len()
        return errors


def line_col(text, pos):
    """Returns the 'pos' wihin text as (line, column)-tuple.
    """
    line = text.count("\n", 0, pos) + 1
    column = pos - text.rfind("\n", 0, pos)
    return line, column


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

LEFT_RECURSION_DEPTH = 16  # because of pythons recursion depth limit, this
                           # value ought not to be set too high
MAX_DROPOUTS = 25  # stop trying to recover parsing after so many


# errors occured


def left_recursion_guard(callfunc):
    def call(obj, text):
        try:
            location = len(text)
            # if location has already been visited by the current parser,
            # return saved result
            if location in obj.visited:
                return obj.visited[location]
            # break left recursion at the maximum allowed depth
            if obj.recursion_counter.setdefault(location, 0) > LEFT_RECURSION_DEPTH:
                return None, text

            obj.recursion_counter[location] += 1

            # call preprocess hook and run original __call__ method
            if obj.preprocess is not None:
                text = obj.preprocess(obj, text)

            result = callfunc(obj, text)

            # in case of a recursive call saves the result of the first
            # (or left-most) call that matches
            if result[0] is not None:
                obj.visited[location] = result
            # if parser did non match but a saved result exits, assume
            # left recursion and use the saved result
            elif location in obj.visited:
                result = obj.visited[location]

            # call postprocess hook
            if obj.postprocess is not None:
                text, result = obj.postprocess(obj, text, result)

            obj.recursion_counter[location] -= 1

        except RecursionError:
            node = Node(None, text[:min(10, max(1, text.find("\n")))] + " ...")
            node.add_error("maximum recursion depth of parser reached; "
                           "potentially due to too many errors!")
            node.fatalError = True
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
        self.root = None
        self.visited = dict()
        self.recursion_counter = dict()
        self.preprocess = None  # f(str) -> str
        self.postprocess = None  # f(str, Node or str) -> (str, Node or str)

    def __call__(self, text):
        raise NotImplementedError

    def __str__(self):
        return self.component + ':' + self.__class__.__name__
        # if self.component:
        #     return self.component
        # else:
        #     return "<" + self.__class__.__name__ + ">"

    def prepare(self, root):
        """Connects parser with ParserRoor-object and resets the call tracing
        variables."""
        self.root = root
        self.visited = dict()
        self.recursion_counter = dict()

    def addHooks(self, preprocess, postprocess):
        assert preprocess is None or isinstance(preprocess, types.FunctionType)
        assert postprocess is None or isinstance(postprocess, types.FunctionType)
        self.preprocess = preprocess
        self.postprocess = postprocess
        return self


class ParserRoot:
    def __init__(self, root=None):
        self.root__ = root if root else copy.deepcopy(self.__class__.root__)

    def parse(self, document):
        """Parses a document with with parser-combinators.

        Args:
            document (str): The source text to be parsed.
            parser (Parser):  The root object of the parser combinator ensemble
                that is to be used for parsing the source text.
        Returns:
            Node: The root node ot the parse tree.
        """
        parser = self.root__
        parser.prepare(self)
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
                                ("! trying to recover..." if len(stitches) < MAX_DROPOUTS \
                                     else "too often! Terminating parser.")
                stitches.append(Node(None, skip))
                stitches[-1].add_error(error_msg)
        if stitches:
            if result and stitches[-1] != result:
                stitches.append(result)
            if rest:
                stitches.append(Node(None, rest))
        return result if not stitches else Node(None, tuple(stitches))


ZOMBIE_PARSER = Parser()          # zombie object to avoid distinction of cases
                                  # for the Node.parser variable
RE_WSPC = Parser('whitespace__')  # Dummy Parser for comments that were captured
                                  # by an RE Parser via the `comment`-parameter


##############################################################################
#
# Token parser classes
#
##############################################################################


class ScannerToken(Parser):
    def __init__(self, scanner_token):
        assert isinstance(scanner_token, str) and scanner_token and scanner_token.isupper()
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
                return Node(self, text[len(self.component) + 1:end]), text[end + 1:]
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
        duplicate.root = self.root
        duplicate.visited = copy.deepcopy(self.visited, memo)
        duplicate.recursion_counter = copy.deepcopy(self.recursion_counter, memo)
        duplicate.preprocess = self.preprocess
        duplicate.postprocess = self.postprocess
        return duplicate

    def __call__(self, text):
        match = text[0:1] != BEGIN_SCANNER_TOKEN and self.regexp.match(text)  # ESC starts a scanner token.
        if match:
            end = match.end()
            groups = set(match.groups())
            if len(groups) >= 1:
                split = sorted([i for i in reduce(lambda s, r: s | set(r), match.regs, set()) if i >= 0])
                parts = (text[i:j] for i, j in zip(split[:-1], split[1:]))
                result = tuple(Node(None if part in groups else RE_WSPC, part) for part in parts)
                if len(result) > 1:
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
    return RegExp(component or "RE", wspcL + rA + regexp + rB + wspcR, regexp)


def Token(token, component=None, wspcL='', wspcR=''):
    return RE(escape_re(token), component or "Token", wspcL, wspcR)


##############################################################################
#
# Combinator parser classes
#
##############################################################################


class UnaryOperator(Parser):
    def __init__(self, component, parser):
        super(UnaryOperator, self).__init__(component)
        assert isinstance(parser, Parser)
        self.parser = parser

    def prepare(self, root):
        super(UnaryOperator, self).prepare(root)
        self.parser.prepare(root)

    def __str__(self):
        return Parser.__str__(self) + "(" + str(self.parser) + ")"


class NaryOperator(Parser):
    def __init__(self, component, *parsers):
        super(NaryOperator, self).__init__(component)
        assert all([isinstance(parser, Parser) for parser in parsers])
        self.parsers = parsers

    def prepare(self, root):
        super(NaryOperator, self).prepare(root)
        for parser in self.parsers:
            parser.prepare(root)


class FlowOperator(UnaryOperator):
    def __init__(self, parser):
        UnaryOperator.__init__(self, None, parser)


class Required(FlowOperator):
    def __call__(self, text):
        node, text_ = self.parser(text)
        if not node:
            m = re.search('\W', text)
            i = max(1, m.start()) if m else 1
            node = Node(self, text[:i])
            text_ = text[i:]
            node.add_error('%s expected; "%s..." found!' %
                           (str(self.parser), text[:10]))
        return node, text_


class PositiveLookahead(FlowOperator):
    def __call__(self, text):
        node, text_ = self.parser(text)
        if node:
            return Node(self, ''), text
        else:
            return None, text


class NegativeLookahead(FlowOperator):
    def __call__(self, text):
        node, text_ = self.parser(text)
        if not node:
            return Node(self, ''), text
        else:
            return None, text


class Optional(UnaryOperator):
    def __init__(self, component, parser):
        super(Optional, self).__init__(component, parser)
        assert isinstance(parser, Parser)
        assert not isinstance(parser, Optional), "Nesting options would is redundant!"
        assert not isinstance(parser, Required), "Nestion options with required elemts is contradictory!"

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
        assert not isinstance(parser, Optional)

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
        # commented, because sequences can be empty assert not all(isinstance(p, Optional) for p in self.parsers)

    def __call__(self, text):
        results = ()
        text_ = text
        for parser in self.parsers:
            node, text_ = parser(text_)
            if not node:
                return node, text
            if node.result:  # Nodes with zero-length result are silently omitted
                results += (node,)
            if node.fatalError:
                break
        assert len(results) <= len(self.parsers)
        return Node(self, results), text_

    def __str__(self):
        return "(" + ",\n".join(["\n    ".join(str(parser).split("\n")) for parser in self.parsers]) + ")"


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

    def __str__(self):
        return "(" + " |\n".join(["\n    ".join(str(parser).split("\n")) for parser in self.parsers]) + ")"


##############################################################################
#
# Special classes
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

    def prepare(self, root):
        # the following if clause is not necessary, because `cycle_reached`
        # should be false unless inside a recursive call of `prepare` in
        # which case it is set to false before return.
        # if self.visited:
        #     self.cycle_reached = False
        if not self.cycle_reached:
            self.cycle_reached = True
            super(Forward, self).prepare(root)
            assert not self.visited
            self.parser.prepare(root)
            self.cycle_reached = False


##############################################################################
#
# Abstract syntax tree support
#
##############################################################################


def ASTTransform(node, trans_table):
    """Transforms the parse tree starting with the given `node` to an abstract
    syntax tree by calling transformation functions registered in a
    transformation table.

    Args:
        node (Node): The root note of the parse tree (or sub-tree) to be
                transformed into the abstract syntax tree.
        trans_table (dict): A dictionary that assigns a transformation
                transformation functions to parser component strings.
    """
    # invoking `len()` saves the length in cache, so error location is still
    # possible on the AST tree, even if some nodes are dropped entirely during
    # AST-transformation.
    node.len()
    if isinstance(node.result, tuple):
        for child in node.result:
            ASTTransform(child, trans_table)

    transformation = trans_table.get(node.parser.component,
                                     trans_table.get('*', lambda node: 0))
    if not isinstance(transformation, collections.abc.Sequence):
        transformation = [transformation]
    for transform in transformation:
        if transform(node):
            break


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
    if isinstance(node.result, tuple) and len(node.result) == 1:
        if not node.result[0].parser.component:
            node.result[0].parser.component = node.parser.component
        node.parser = node.result[0].parser
        node.errors.extend(node.result[0].errors)
        node.result = node.result[0].result
        return "STOP"    # discard any further transformations if node has been replaced


def reduce_single_child(node):
    """Reduce a single branch node, by transferring the result of its
    immediate descendant to this node, but keeping this node's parser
    entry.
    """
    if isinstance(node.result, tuple) and len(node.result) == 1:
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


def remove_delimiters(node):
    """Removes the enclosing delimiters from a structure (e.g. quotation marks
    from a literal or braces from a group).
    """
    if isinstance(node.result, tuple) and len(node.result) >= 3:
        assert isinstance(node.result[0].result, str) and isinstance(node.result[-1].result, str)
        node.result = node.result[1:-1]


def remove_children_if(node, condition):
    """Removes all nodes from the result field if the function `condition` evaluates
    to `True`."""
    if isinstance(node.result, tuple):
        new_result = tuple(r for r in node.result if not condition(r))
        if len(new_result) < len(node.result):
            node.result = new_result


is_whitespace = lambda node: not node.result or (isinstance(node.result, str) and not node.result.strip())
is_comment = lambda node: node.parser == RE_WSPC
is_scanner_token = lambda node: isinstance(node.parser, ScannerToken)
is_expendable = lambda node: is_whitespace(node) or is_comment(node) or is_scanner_token(node)

remove_whitespace = lambda node: remove_children_if(node, is_whitespace)
remove_comments = lambda node: remove_children_if(node, is_comment)
remove_scanner_tokens = lambda node: remove_children_if(node, is_scanner_token)
remove_expendables = lambda node: remove_children_if(node, is_expendable)


def flatten(node):
    """Recursively flattens all unnamed sub-nodes.
    """
    if isinstance(node.result, tuple):
        new_result = []
        for child in node.result:
            if not child.parser.component:
                flatten(child)
                new_result.extend(child.result)
            else:
                new_result.append(child)
        node.result = tuple(new_result)


def remove_operator(node):
    """Removes a (repeated) operator, i.e. x + y + z becomes x y z."""
    assert isinstance(node.result, tuple)
    assert len(node.result) % 2 == 1
    assert all(isinstance(child.result, str) for child in node.result[1::2])
    assert all(node.result[1].result == child.result for child in node.result[3::2])
    node.result = node.result[0::2]


def strip_assignment(node):
    """Reduces assignments to symbol, value pairs by removing token signs
    from the assignment expression, e.g. "a = b + c;" becomes a b+c and
    "@ wspc = /\s*/;" becomes "wspc /\s*/"
    """
    assert isinstance(node.result, tuple), str(node.result)
    sym = 1 if node.result[0].parser.component == "Token" else 0
    val = -2 if node.result[-1].parser.component == "Token" else -1
    node.result = (node.result[sym], node.result[val])


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
            node.add_error("Must not use reserved name '%s' as parser component! " % elem +
                           "(Any name starting with '_' or '__' or ending with '__' is reserved.)")
            return None
        else:
            compiler = self.__getattribute__(elem)  # TODO Add support for python keyword attributes
            # except AttributeError:
            #     node.add_error("No compiler method for component '%s' in class '%s' !" %
            #                    (elem, self.__class__.__name__))
            #     return None
            return compiler(node)


def full_compilation(source, parser_root, AST_transformations, compiler):
    """Compiles a source in three stages:
        1. Parsing
        2. AST-transformiation
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
            Result as returned by the compiler or `None` if an error occured during parsing
            or AST-transformation and the compiler wasn't inveoked;
            error messages; abstract syntax tree
     """
    syntax_tree = parser_root.parse(source)
    errors = syntax_tree.collect_errors(clear=True)
    assert errors or str(syntax_tree) == source
    # only compile if there were no snytax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    if not errors:
        ASTTransform(syntax_tree, AST_transformations)
        result = compiler.compile__(syntax_tree)
        errors.extend(syntax_tree.collect_errors(clear=True))
    else:
        result = None
    errors.sort()
    messages = error_messages(source, errors)
    return result, messages, syntax_tree


##############################################################################
#
# EBNF-Grammar-Compiler
#
##############################################################################

class EBNFGrammar(ParserRoot):
    r"""Parser for an EBNF source file, with this grammar:
    
    # EBNF-Grammar in EBNF
    
    @ whitespace := /\s*/                            # whitespace includes linefeed
    @ comment    := /#.*(?:\n|$)/                    # comments start with '#' and eat all chars upto and including '\n'
    
    syntax     := { definition | directive } [//~] §EOF
    definition := symbol §":=" expression
    directive  := "@" §symbol §":=" ( regexp | literal | list_)
    
    expression := term { "|" term }
    term       := factor { factor }
    factor     := [flowmarker] symbol !":="          # negative lookahead !":=" to be sure it's not a definition
               | [flowmarker] literal
               | [flowmarker] regexp
               | [flowmarker] group
               | [flowmarker] oneormore
               | repetition
               | option
    
    flowmarker := "!" | "&" | "§"                    # '!' negative lookahead, '&' positive lookahead, '§' required
    
    option     := "[" expression §"]"
    repetition := "{" expression §"}"
    oneormore  := "<" expression §">"
    group      := "(" expression §")"
    
    symbol     := ~/\w+/                             # e.g. expression, factor, parameter_list
    literal    := ~/"(?:[^"]|\\")*?"/                # e.g. "(", '+', 'while'
               | ~/'(?:[^']|\\')*?'/                 # whitespace surrounding literals will be ignored tacitly.
    regexp     := ~/~?\/(?:[^\/]|(?<=\\)\/)*\/~?/    # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                     # '~' is a whitespace-marker, if present leading and trailing
                                                     # whitespace of a regular expression will be ignored tacitly.
    list_      := ~/\w+\s*(?:,\s*\w+\s*)*/           # comman separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                     # BEGIN_QUOTE, END_QUOTE ; see markdown.py for an exmapel
    EOF := !/./
    """

    expression = Forward()
    wspc__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    EOF = NegativeLookahead(RE('.', "EOF"))
    list_ = RE('\\w+\\s*(?:,\\s*\\w+\\s*)*', "list_", wspcL=wspc__)
    regexp = RE('~?/(?:[^/]|(?<=\\\\)/)*/~?', "regexp", wspcL=wspc__)
    literal = Alternative("literal", RE('"(?:[^"]|\\\\")*?"', wspcL=wspc__), RE("'(?:[^']|\\\\')*?'", wspcL=wspc__))
    symbol = RE('\\w+', "symbol", wspcL=wspc__)
    group = Sequence("group", Token("(", wspcL=wspc__), expression, Required(Token(")", wspcL=wspc__)))
    oneormore = Sequence("oneormore", Token("<", wspcL=wspc__), expression, Required(Token(">", wspcL=wspc__)))
    repetition = Sequence("repetition", Token("{", wspcL=wspc__), expression, Required(Token("}", wspcL=wspc__)))
    option = Sequence("option", Token("[", wspcL=wspc__), expression, Required(Token("]", wspcL=wspc__)))
    flowmarker = Alternative("flowmarker", Token("!", wspcL=wspc__), Token("&", wspcL=wspc__), Token("§", wspcL=wspc__))
    factor = Alternative("factor", Sequence(None, Optional(None, flowmarker), symbol,
                                            NegativeLookahead(Token(":=", wspcL=wspc__))),
                         Sequence(None, Optional(None, flowmarker), literal),
                         Sequence(None, Optional(None, flowmarker), regexp),
                         Sequence(None, Optional(None, flowmarker), group),
                         Sequence(None, Optional(None, flowmarker), oneormore), repetition, option)
    term = Sequence("term", factor, ZeroOrMore(None, factor))
    expression.set(Sequence("expression", term, ZeroOrMore(None, Sequence(None, Token("|", wspcL=wspc__), term))))
    directive = Sequence("directive", Token("@", wspcL=wspc__), Required(symbol), Required(Token(":=", wspcL=wspc__)),
                         Alternative(None, regexp, literal, list_))
    definition = Sequence("definition", symbol, Required(Token(":=", wspcL=wspc__)), expression)
    syntax = Sequence("syntax", ZeroOrMore(None, Alternative(None, definition, directive)),
                      Optional(None, RE('', wspcR=wspc__)), Required(EOF))
    root__ = syntax
    

EBNFTransTable = {
    # AST Transformations for EBNF-grammar
    "syntax": [remove_expendables],
    "definition": strip_assignment,
    "directive": strip_assignment,
    "expression": [replace_by_single_child, flatten, remove_operator],
    "term": [replace_by_single_child, flatten],
    "factor": replace_by_single_child,
    "flowmarker": replace_by_single_child,
    "group": [remove_delimiters, replace_by_single_child],
    "oneormore": remove_delimiters,
    "repetition": remove_delimiters,
    "option": remove_delimiters,
    "symbol": [remove_expendables, reduce_single_child],
    "Token": [remove_expendables, reduce_single_child],
    "RE": [remove_expendables, reduce_single_child],
    "whitespace__": [remove_whitespace, reduce_single_child],
    "literal": [remove_expendables, reduce_single_child],
    "regexp": [remove_expendables, reduce_single_child],
    "list_": [remove_expendables, reduce_single_child],
    "": [remove_expendables, replace_by_single_child]
}


def load_if_file(text_or_file):
    """Reads and returns content of a file if parameter `text_or_file` is a
    file name (i.e. a single line string), otherwise (i.e. if `text_or_file` is
    a multiline string) returns the content of `text_or_file`.
    """
    if text_or_file and text_or_file.find('\n') < 0:
        with open(text_or_file) as f:
            content = f.read()
        return content
    else:
        return text_or_file


class EBNFCompilerError(Error):
    """Error raised by `EBNFCompiler` class. (Not compilation errors
    in the strict sense, see `CompilationError` below)"""
    pass


Scanner = collections.namedtuple('Scanner', 'symbol instantiation_call cls_name cls')


class EBNFCompiler(CompilerBase):
    """Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.
    """
    # RX_DIRECTIVE = re.compile('(?:#|@)\s*(?P<key>\w*)\s*=\s*(?P<value>.*)')  # this can be removed, soon
    KNOWN_DIRECTIVES = {'comment', 'whitespace', 'tokens'}
    VOWELS = {'A', 'E', 'I', 'O', 'U'}  # what about cases like 'hour', 'universe' etc. ?
    AST_ERROR = "Badly structured syntax tree. Potentially due to erroneuos AST transformation. "

    def __init__(self, grammar_name="", source_text=""):
        super(EBNFCompiler, self).__init__()
        assert grammar_name == "" or re.match('\w+\Z', grammar_name)
        self.grammar_name = grammar_name
        self.source_text = load_if_file(source_text)
        self.directives = {'whitespace': '\s*', 'comment': ''}
        self._reset()

    def _reset(self):
        self.rules = set()
        self.symbols = set()
        self.scanner_tokens = set()
        self.definition_names = []
        self.component = str(None)
        self.recursive = set()

    def gen_AST_Skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling "gen_AST_Skeleton()"!')
        transtable = [self.grammar_name + 'TransTable = {',
                      '    # AST Transformations for the ' + self.grammar_name + '-grammar']
        for name in self.definition_names:
            transtable.append('    "' + name + '": no_transformation,')
        transtable += ['    "": no_transformation', '}', '']
        return '\n'.join(transtable)

    def gen_Compiler_Skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling "gen_Compiler_Skeleton()"!')
        compiler = ['class ' + self.grammar_name + 'Compiler(CompilerBase):',
                    '    """Compiler for the abstract-syntax-tree of a ' + self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self, grammar_name="' + self.grammar_name + '"):',
                    '        super(' + self.grammar_name + 'Compiler, self).__init__()',
                    "        assert re.match('\w+\Z', grammar_name)", '']
        for name in self.definition_names:
            compiler += ['    def ' + name + '(self, node):',
                         '        pass', '']
        return '\n'.join(compiler + [''])

    def syntax(self, node):
        self._reset()
        definitions = []
        if isinstance(node.parser, Sequence) and isinstance(node.result[0].parser, ZeroOrMore):
            node = node.result[0]
        for nd in node.result:
            if nd.parser.component == "definition":
                definitions += [self.compile__(nd)]
            else:
                assert nd.parser.component == "directive", nd.as_sexpr()
                self.compile__(nd)
        self.definition_names = [defn[0] for defn in definitions]
        root = definitions[0][0] if definitions else ""
        # definitions.append(('wspc__', "'(?:' + '{whitespace}' + '(?:' + '{comment}' + '{whitespace}' + ')*)'". \
        #                     format(**self.directives)))
        definitions.append(('wspc__', "mixin_comment(whitespace=r'{whitespace}', comment=r'{comment}')". \
                            format(**self.directives)))
        definitions.reverse()
        article = 'an ' if self.grammar_name[0:1].upper() in EBNFCompiler.VOWELS else 'a '
        declarations = ['class ' + self.grammar_name + 'Grammar(ParserRoot):',
                        'r"""Parser for ' + article + self.grammar_name + ' source file' +
                        (', with this grammar:' if self.source_text else '.')]
        if self.source_text:
            # add source as comment
            declarations.append('')
            declarations += [line for line in self.source_text.split('\n')]
            while declarations[-1].strip() == '':
                declarations = declarations[:-1]
        declarations.append('"""')
        declarations += [symbol + ' = Forward()' for symbol in sorted(list(self.recursive))]
        for symbol, statement in definitions:
            if symbol in self.recursive:
                declarations += [symbol + '.set(' + statement + ')']
            else:
                declarations += [symbol + ' = ' + statement]
        for nd in self.symbols:
            if nd.result not in self.rules:
                nd.add_error("Missing production for symbol '%s'" % nd.result)
        if root and 'root__' not in self.symbols:
            declarations.append('root__ = ' + root)
        declarations.append('')
        return '\n    '.join(declarations)

    def definition(self, node):
        rule = node.result[0].result
        assert not keyword.iskeyword(rule)
        try:
            self.component = '"' + rule + '"'
            self.rules.add(rule)
            defn = self.compile__(node.result[1])
        except TypeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + node.as_sexpr()
            node.add_error(errmsg)
            rule, defn = 'error', '"' + errmsg + '"'
        return (rule, defn)

    def _check_rx(self, node, rx):
        """Checks whether the string `rx` represents a valid regular expression. Makes
        sure that multiline regular expressions are prepended by the multiline-flag.
        Returns `repr(rx)`.
        """
        rx = rx if rx.find('\n') < 0 or rx[0:4] == '(?x)' else '(?x)' + rx
        try:
            re.compile(rx)
        except Exception as re_error:
            node.add_error("malformed regular expression %s: %s" % (repr(rx), str(re_error)))
        return rx

    def directive(self, node):
        key = node.result[0].result
        assert key not in self.scanner_tokens
        if key in {'comment', 'whitespace'}:
            value = node.result[1].result
            if value[0] + value[-1] in {'""', "''"}:
                value = escape_re(value[1:-1])
            elif value[0] + value[-1] == '//':
                value = self._check_rx(node, value[1:-1])
            self.directives[key] = value
        elif key == 'tokens':
            self.scanner_tokens |= self.compile__(node.result[1])
        else:
            node.add_error('Unknown directive %s ! (Known directives are %s .)' %
                           (key, ', '.join(list(EBNFCompiler.KNOWN_DIRECTIVES))))
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
        assert isinstance(node.result, tuple)
        assert len(node.result) == 2
        assert isinstance(node.result[0].parser, RegExp), str(node.as_sexpr())
        prefix = node.result[0].result
        arg = self.compile__(node.result[1])
        if prefix == '§':
            return 'Required(' + arg + ')'
        elif prefix == '!':
            return 'NegativeLookahead(' + arg + ')'
        elif prefix == '&':
            return 'PositiveLookahead(' + arg + ')'
        else:
            assert prefix in {'§', '!', '&'}, node.as_sexpr()

    def option(self, node):
        return self.non_terminal(node, 'Optional')

    def repetition(self, node):
        return self.non_terminal(node, 'ZeroOrMore')

    def oneormore(self, node):
        return self.non_terminal(node, 'OneOrMore')

    def group(self, node):
        raise EBNFCompilerError("Group nodes should have been eliminated by AST transformation!")

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
        comp = self._get_component() + ['wspcL=wspc__']
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
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + node.as_sexpr()
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


DEBUG_AST = None


def compile_python_parser(python_src):
    """Compiles the python source code of a grammar class as returned by
     `EBNFCompiler`. Returns the class.
     """
    code = compile(python_src, '<string>', 'exec')
    module_vars = globals()
    namespace = {k: module_vars[k] for k in {'RegExp', 'mixin_comment', 'RE', 'Token', 'Required',
                                             'PositiveLookahead', 'NegativeLookahead', 'Optional',
                                             'ZeroOrMore', 'Sequence', 'Alternative', 'Forward',
                                             'ParserRoot'}}
    exec(code, namespace)  # safety risk?
    for key in namespace.keys():
        if key.endswith('Grammar'):
            parser = namespace[key]
            break
    return parser


def compileDSL(text_or_file, dsl_grammar, trans_table, compiler, scanner=nil_scanner):
    """Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Resurns the compiled text.
    """
    assert isinstance(text_or_file, str)
    assert isinstance(compiler, CompilerBase)
    assert isinstance(trans_table, dict)

    if isinstance(dsl_grammar, str):
        # read grammar
        grammar_src = load_if_file(dsl_grammar)
        if is_python_code(dsl_grammar):
            parser_py, errors, AST = grammar_src, '', None
        else:
            parser_py, errors, AST = full_compilation(grammar_src, EBNFGrammar(),
                                                      EBNFTransTable, EBNFCompiler())
        if errors:  raise GrammarError(errors, grammar_src)
        parser_root = compile_python_parser(parser_py)()
    else:
        # assume that dsl_grammar is a ParserRoot object or Grammar class
        grammar_src = ''
        if not isinstance(dsl_grammar, ParserRoot):
            # in case it is a grammar class, get the root object
            parser_root = dsl_grammar()

    src = scanner(load_if_file(text_or_file))
    result, errors, AST = full_compilation(src, parser_root, trans_table, compiler)
    global DEBUG_AST;  DEBUG_AST = AST
    if errors:  raise CompilationError(errors, src, grammar_src, AST)
    return result


##############################################################################
#
# quick system test
#
##############################################################################

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = os.path.normpath(sys.argv[1])
        source = load_if_file(sys.argv[1])
        rootname = os.path.splitext(filepath)[0]
        compiler = EBNFCompiler(os.path.basename(rootname), source)
        result, errors, ast = full_compilation(source, EBNFGrammar(),
                                               EBNFTransTable, compiler)
        if errors:
            print(errors)
            sys.exit(1)
        else:
            f = None
            try:
                f = open(rootname + '_parser.py', 'w')
                f.write(result)
            except (PermissionError, FileNotFoundError, IOError) as error:
                print('# Could not write file "' + rootname + '.py" because of: '
                      + "\n# ".join(str(error).split('\n)')))
                print(result)
            finally:
                if f:  f.close()

    else:
        # self-test
        # compileDSL("grammars/EBNF.ebnf", "grammars/EBNF.ebnf", EBNFTransTable, EBNFCompiler())

        assert (str(EBNFGrammar.syntax) == str(EBNFGrammar.syntax))

        def test(file_name):
            print(file_name)
            with open('scratch/' + file_name) as f:
                text = f.read()
            compiler = EBNFCompiler(os.path.splitext(file_name)[0], text)
            result, errors, syntax_tree = full_compilation(text, EBNFGrammar(),
                                                           EBNFTransTable, compiler)
            print(syntax_tree.as_sexpr())
            print(errors)
            print(compiler.gen_AST_Skeleton())
            print(compiler.gen_Compiler_Skeleton())
            result = compileDSL(text, result, EBNFTransTable, compiler)
            print(result)
            return result


        # print(EBNFGrammar.syntax)
        # test('arithmetic.ebnf')
        test('EBNF.ebnf')
        # test('left_recursion.ebnf')
