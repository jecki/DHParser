#!/usr/bin/python3

"""syntaxtree.py - syntax tree classes and transformation functions for 
converting the concrete into the abstract syntax tree for DHParser

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
"""

import collections
import itertools
import os
from functools import partial
try:
    import regex as re
except ImportError:
    import re
from typing import NamedTuple

from logs import LOGGING, LOGS_DIR


__all__ = ['WHITESPACE_KEYWORD',
           'TOKEN_KEYWORD',
           'line_col',
           'ZOMBIE_PARSER',
           'Error',
           'Node',
           'error_messages',
           'compact_sexpr',
           'ASTTransform',
           'no_transformation',
           'replace_by_single_child',
           'reduce_single_child',
           'is_whitespace',
           'is_empty',
           'is_expendable',
           'is_token',
           'remove_children_if',
           'remove_whitespace',
           'remove_expendables',
           'remove_tokens',
           'flatten',
           'remove_enclosing_delimiters',
           'AST_SYMBOLS']


WHITESPACE_KEYWORD = 'WSP__'
TOKEN_KEYWORD = 'TOKEN__'


def line_col(text, pos):
    """Returns the position within a text as (line, column)-tuple.
    """
    assert pos < len(text), str(pos) + " >= " + str(len(text))
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

            The value of ``pos`` is -1 meaning invalid by default. 
            Setting this value will set the positions of all child
            nodes relative to this value.  

            To set the pos values of all nodes in a syntax tree, the
            pos value of the root node should be set to 0 right 
            after parsing.

            Other than that, this value should be considered READ ONLY. 
            At any rate, it should only be reassigned only during
            parsing stage and never during or after the
            AST-transformation.
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
            sum(child._len for child in self.children)
        # self.pos = 0  # coninuous updating of pos values
        self._pos = -1

    def __str__(self):
        if self.children:
            return "".join(str(child) for child in self.result)
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
        # DEBUGGING:  print(str(self.parser), str(self.pos), str(self._len), str(self)[:10].replace('\n','.'))
        return self._len

    @property
    def pos(self):
        assert self._pos >= 0, "position value not initialized!"
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

        head = head + '\n'  # place the head, tail and content
        tail = '\n' + tail  # of the node on different lines

        if self.children:
            content = []
            for child in self.result:
                subtree = child._tree_repr(tab, openF, closeF, dataF).split('\n')
                content.append('\n'.join((tab + s) for s in subtree))
            return head + '\n'.join(content) + tail

        return head + '\n'.join([tab + dataF(s)
                                 for s in str(self.result).split('\n')]) + tail

    def as_sexpr(self, src=None, prettyprint=True):
        """
        Returns content as S-expression, i.e. in lisp-like form.

        Parameters:
            src:  The source text or `None`. In case the source text is
                given the position of the element in the text will be
                reported as line and column.
            prettyprint(bool):  True (default), if pretty printing 
                of leaf nodes shall be applied for better readability.
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

        return self._tree_repr('    ', opening, lambda node: ')',
                               pretty if prettyprint else lambda s: s)

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

    def log(self, log_file_name, ext):
        # global LOGGING
        if LOGGING:
            st_file_name = log_file_name + ext
            with open(os.path.join(LOGS_DIR(), st_file_name), "w", encoding="utf-8") as f:
                f.write(self.as_sexpr())

    def find(self, match_function):
        """Finds nodes in the tree that match a specific criterion.
        
        ``find`` is a generator that yields all nodes for which the
        given ``match_function`` evaluates to True. The tree is 
        traversed pre-order.
        
        Args:
            match_function (function): A function  that takes as Node
                object as argument and returns True or False

        Yields:
            Node: all nodes of the tree for which 
            ``match_function(node)`` returns True
        """
        if match_function(self):
            yield self
        else:
            for child in self.children:
                for nd in child.find(match_function):
                    yield nd

    def navigate(self, path):
        """Yields the results of all descendant elements matched by
        ``path``, e.g.
        'd/s' yields 'l' from (d (s l)(e (r x1) (r x2))
        'e/r' yields 'x1', then 'x2'
        'e'   yields (r x1)(r x2)

        Parameters:
            path (str):  The path of the object, e.g. 'a/b/c'. The
                components of ``path`` can be regular expressions

        Returns:
            The object at the path, either a string or a Node or
            ``None``, if the path did not match.
        """
        def nav(node, pl):
            if pl:
                return itertools.chain(nav(child, pl[1:]) for child in node.children
                                       if re.match(pl[0], child.tag_name))
            else:
                return self.result,
        return nav(path.split('/'))


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


def compact_sexpr(s):
    """Returns S-expression ``s`` as a one liner without unnecessary
    whitespace.
    
    Example:
        >>> compact_sexpr("(a\n    (b\n        c\n    )\n)\n")
        (a (b c))
    """
    return re.sub('\s(?=\))', '', re.sub('\s+', ' ', s)).strip()


########################################################################
#
# syntax tree transformation functions
#
########################################################################


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
    table = {name: transformation if isinstance(transformation, collections.abc.Sequence)
             else [transformation] for name, transformation in list(transtable.items())}
    table = expand_table(table)

    def recursive_ASTTransform(nd):
        if nd.children:
            for child in nd.result:
                recursive_ASTTransform(child)
        transformation = table.get(nd.parser.name,
                                   table.get('~', [])) + table.get('*', [])
        for transform in transformation:
            transform(nd)

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


# def is_scanner_token(node):
#     return isinstance(node.parser, ScannerToken)


def is_empty(node):
    return not node.result


def is_expendable(node):
    return is_empty(node) or is_whitespace(node)  # or is_scanner_token(node)


def is_token(node, token_set=frozenset()):
    return node.parser.name == TOKEN_KEYWORD and (not token_set or node.result in token_set)


def remove_children_if(node, condition):
    """Removes all nodes from the result field if the function 
    ``condition(child_node)`` evaluates to ``True``."""
    if node.children:
        node.result = tuple(c for c in node.children if not condition(c))


remove_whitespace = partial(remove_children_if, condition=is_whitespace)
# remove_scanner_tokens = partial(remove_children_if, condition=is_scanner_token)
remove_expendables = partial(remove_children_if, condition=is_expendable)


def remove_tokens(node, tokens=frozenset()):
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
    This is meant to achieve these kinds of structural transformation:
        (1 (+ 2) (+ 3)     ->   (1 + 2 + 3)
        (1 (+ (2 + (3))))  ->   (1 + 2 + 3)

    Warning: Use with care. Du tue its recursive nature, flattening can
    have unexpected side-effects.
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


def remove_enclosing_delimiters(node):
    """Removes any enclosing delimiters from a structure (e.g. quotation marks
    from a literal or braces from a group).
    """
    if len(node.children) >= 3:
        assert not node.children[0].children and not node.children[-1].children, node.as_sexpr()
        node.result = node.result[1:-1]


AST_SYMBOLS = {'replace_by_single_child', 'reduce_single_child',
               'no_transformation', 'remove_children_if',
               'is_whitespace', 'is_expendable', 'remove_whitespace',
               # 'remove_scanner_tokens', 'is_scanner_token',
               'remove_expendables', 'flatten', 'remove_tokens',
               'remove_enclosing_delimiters',
               'TOKEN_KEYWORD', 'WHITESPACE_KEYWORD', 'partial'}
