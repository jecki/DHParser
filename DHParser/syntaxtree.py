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

import itertools
import os
from functools import partial
try:
    import regex as re
except ImportError:
    import re
from typing import NamedTuple

from .toolkit import IS_LOGGING, LOGS_DIR, expand_table, line_col, smart_list


__all__ = ['WHITESPACE_KEYWORD',
           'TOKEN_KEYWORD',
           'ZOMBIE_PARSER',
           'Error',
           'Node',
           'mock_syntax_tree',
           'traverse',
           'no_operation',
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
           'forbid',
           'require',
           'assert_content']


class MockParser:
    """
    MockParser objects can be used to reconstruct syntax trees from a
    serialized form like S-expressions or XML. Mock objects are needed,
    because Node objects require a parser object for instantiation.
    Mock objects have just enough properties to serve that purpose. 
    
    Mock objects should not be used for anything other than 
    syntax tree (re-)construction. In all other cases where a parser
    object substitute is needed, chose the singleton ZOMBIE_PARSER.
    """
    def __init__(self, name=''):
        self.name = name

    def __str__(self):
        return self.name or self.__class__.__name__


class ZombieParser(MockParser):
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
        super(ZombieParser, self).__init__("ZOMBIE")
        assert not self.__class__.alive, "There can be only one!"
        assert self.__class__ == ZombieParser, "No derivatives, please!"
        self.__class__.alive = True

    def __copy__(self):
        return self

    def __deepcopy__(self, memo):
        return self

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

    def __eq__(self, other):
        return str(self.parser) == str(other.parser) and self.result == other.result

    @property
    def tag_name(self):
        return str(self.parser)
        # ONLY FOR DEBUGGING: return self.parser.name + ':' + self.parser.__class__.__name__

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
        assert isinstance(pos, int)
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

        Args:
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

    def as_sexpr(self, src=None):
        """
        Returns content as S-expression, i.e. in lisp-like form.

        Args:
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

        return self._tree_repr('    ', opening, lambda node: ')', pretty)  # pretty if prettyprint else lambda s: s)

    def as_xml(self, src=None):
        """
        Returns content as XML-tree.

        Args:
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
        errors = []
        if self.error_flag:
            errors = self.errors
            if clear_errors:
                self._errors = []
                self.error_flag = False
            if self.children:
                for child in self.result:
                    errors.extend(child.collect_errors(clear_errors))
        return errors

    def log(self, log_file_name, ext):
        if IS_LOGGING():
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

    # def range(self, match_first, match_last):
    #     """Iterates over the range of nodes, starting from the first
    #     node for which ``match_first`` becomes True until the first node
    #     after this one for which ``match_last`` becomes true or until
    #     the end if it never does.
    #
    #     Args:
    #         match_first (function): A function  that takes as Node
    #             object as argument and returns True or False
    #         match_last (function): A function  that takes as Node
    #             object as argument and returns True or False
    #     Yields:
    #         Node: all nodes of the tree for which
    #         ``match_function(node)`` returns True
    #     """


    def navigate(self, path):
        """Yields the results of all descendant elements matched by
        ``path``, e.g.
        'd/s' yields 'l' from (d (s l)(e (r x1) (r x2))
        'e/r' yields 'x1', then 'x2'
        'e'   yields (r x1)(r x2)

        Args:
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


def mock_syntax_tree(sexpr):
    """Generates a tree of nodes from an S-expression.

    Example: 
    >>> mock_syntax_tree("(a (b c))").as_sexpr()
    (a 
        (b 
            "c" 
        )
    )
    """
    def next_block(s):
        s = s.strip()
        while s[0] != ')':
            assert s[0] == '(', s
            level = 1;
            i = 1
            while level > 0:
                if s[i] == '(':
                    level += 1
                elif s[i] == ')':
                    level -= 1
                i += 1
            yield s[:i]
            s = s[i:].strip()

    sexpr = sexpr.strip()
    assert sexpr[0] == '(', sexpr
    sexpr = sexpr[1:].strip()
    m = re.match('\w+', sexpr)
    name = sexpr[:m.end()]
    sexpr = sexpr[m.end():].strip()
    if sexpr[0] == '(':
        result = tuple(mock_syntax_tree(block) for block in next_block(sexpr))
    else:
        lines = []
        while sexpr and sexpr[0] != ')':
            for qm in ['"""', "'''", '"', "'"]:
                m = re.match(qm + r'.*?' + qm, sexpr)
                if m:
                    i = len(qm)
                    lines.append(sexpr[i:m.end() - i])
                    sexpr = sexpr[m.end():].strip()
                    break
            else:
                m = re.match(r'(?:(?!\)).)*', sexpr)
                lines.append(sexpr[:m.end()])
                sexpr = sexpr[m.end():]
        result = "\n".join(lines)
    return Node(MockParser(name), result)


########################################################################
#
# syntax tree transformation functions
#
########################################################################


WHITESPACE_KEYWORD = 'WSP__'
TOKEN_KEYWORD = 'TOKEN__'


def traverse(root_node, processing_table):
    """Traverses the snytax tree starting with the given ``node`` depth
    first and applies the sequences of callback functions registered
    in the ``calltable``-dictionary.
    
    Possible use cases are the transformation of a concrete syntax tree
    into an abstract tree (AST) or the semantic analysis of the AST.
    
    Args:
        root_node (Node): The root-node of the syntax tree to be traversed 
        processing_table (dict): parser.name -> sequence of functions that
            will be applied to matching nodes in order. This dictionary
            is interpreted as a ``compact_table``. See 
            ``toolkit.expand_table`` or ``EBNFCompiler.EBNFTransTable``
            
    Example:
        table = { "term": [replace_by_single_child, flatten], 
            "factor, flowmarker, retrieveop": replace_by_single_child }
        traverse(node, table)
    """
    # normalize processing_table entries by turning single values into lists
    # with a single value
    table = {name: smart_list(call) for name, call in list(processing_table.items())}
    table = expand_table(table)

    def traverse_recursive(node):
        if node.children:
            for child in node.result:
                traverse_recursive(child)
                node.error_flag |= child.error_flag  # propagate error flag
        sequence = table.get('*', []) + \
                   table.get(node.parser.name, table.get('?', [])) + \
                   table.get('~', [])
        # '*' always called (before any other processing function)
        # '?' called for those nodes for which no (other) processing functions is in the table
        # '~' always called (after any other processing function)
        for call in sequence:
            call(node)

    traverse_recursive(root_node)


def no_operation(node):
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


########################################################################
#
# syntax tree validation functions
#
########################################################################


def require(node, child_tags):
    for child in node.children:
        if child.tag_name not in child_tags:
            node.add_error('Element "%s" is not allowed inside "%s".' %
                           (child.tag_name, node.tag_name))


def forbid(node, child_tags):
    for child in node.children:
        if child.tag_name in child_tags:
            node.add_error('Element "%s" cannot be nested inside "%s".' %
                           (child.tag_name, node.tag_name))


def assert_content(node, regex):
    content = str(node)
    if not re.match(regex, content):
        node.add_error('Element "%s" violates %s on %s' %
                       (node.tag_name, str(regex), content))
