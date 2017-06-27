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

import abc
import copy
import inspect
import itertools
import os
from functools import partial, singledispatch
try:
    import regex as re
except ImportError:
    import re
from .typing import AbstractSet, Any, ByteString, Callable, cast, Container, Iterator, List, \
    NamedTuple, Sequence, Union, Text, Tuple

from DHParser.toolkit import log_dir, expand_table, line_col, smart_list


__all__ = ['WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'ZOMBIE_PARSER',
           'ParserBase',
           'Error',
           'Node',
           'TransformationFunc',
           'transformation_factory',
           'key_parser_name',
           'key_tag_name',
           'traverse',
           'no_transformation',
           'replace_by_single_child',
           'reduce_single_child',
           'replace_parser',
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


class ParserBase:
    """
    ParserBase is the base class for all real and mock parser classes.
    It is defined here, because Node objects require a parser object
    for instantiation.
    """
    def __init__(self, name=''):  # , pbases=frozenset()):
        self.name = name  # type: str
        self._ptype = ':' + self.__class__.__name__  # type: str

    def __str__(self):
        return self.name or self.ptype

    @property
    def ptype(self) -> str:
        return self._ptype


class MockParser(ParserBase):
    """
    MockParser objects can be used to reconstruct syntax trees from a
    serialized form like S-expressions or XML. Mock objects can mimic
    different parser types by assigning them a ptype on initialization.
    
    Mock objects should not be used for anything other than 
    syntax tree (re-)construction. In all other cases where a parser
    object substitute is needed, chose the singleton ZOMBIE_PARSER.
    """
    def __init__(self, name='', ptype=''):  # , pbases=frozenset()):
        assert not ptype or ptype[0] == ':'
        super(MockParser, self).__init__(name)
        self.name = name
        self._ptype = ptype or ':' + self.__class__.__name__

    def __str__(self):
        return self.name or self.ptype


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
        super(ZombieParser, self).__init__("__ZOMBIE__")
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


# # Python 3.6:
# class Error(NamedTuple):
#     pos: int
#     msg: str
Error = NamedTuple('Error', [('pos', int), ('msg', str)])

StrictResultType = Union[Tuple['Node', ...], str]
ResultType = Union[Tuple['Node', ...], 'Node', str, None]


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
            WARNING: In case you use mock syntax trees for testing or
            parser replacement during the AST-transformation: DO NOT
            rely on this being a real parser object in any phase after 
            parsing (i.e. AST-transformation and compiling), for 
            example by calling ``isinstance(node.parer, ...)``.
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

    def __init__(self, parser, result: ResultType) -> None:
        """Initializes the ``Node``-object with the ``Parser``-Instance
        that generated the node and the parser's result.
        """
        self._result = ''  # type: StrictResultType
        self._errors = []  # type: List[str]
        self._children = ()  # type: Tuple['Node', ...]
        self.result = result
        self._len = len(self.result) if not self.children else \
            sum(child._len for child in self.children)  # type: int
        # self.pos: int  = 0  # continuous updating of pos values
        self._pos = -1  # type: int
        self.parser = parser or ZOMBIE_PARSER
        self.error_flag = any(r.error_flag for r in self.children) \
            if self.children else False  # type: bool

    def __str__(self):
        if self.children:
            return "".join(str(child) for child in self.children)
        return str(self.result)

    def __repr__(self):
        mpargs = {'name': self.parser.name, 'ptype': self.parser.ptype}
        parg = "MockParser({name}, {ptype})".format(**mpargs)
        rarg = str(self) if not self.children else \
               "(" + ", ".join(repr(child) for child in self.children) + ")"
        return "Node(%s, %s)" % (parg, rarg)

    def __eq__(self, other):
        # return str(self.parser) == str(other.parser) and self.result == other.result
        return self.tag_name == other.tag_name and self.result == other.result

    def __hash__(self):
        return hash(self.tag_name)

    def __deepcopy__(self, memodict={}):
        result = copy.deepcopy(self.result)
        other = Node(self.parser, result)
        other._pos = self._pos
        return other

    @property   # this needs to be a (dynamic) property, in case sef.parser gets updated
    def tag_name(self) -> str:
        return self.parser.name or self.parser.ptype
        # ONLY FOR DEBUGGING: return self.parser.name + ':' + self.parser.ptype

    @property
    def result(self) -> StrictResultType:
        return self._result

    @result.setter
    def result(self, result: ResultType):
        # # made obsolete by static type checking with mypy is done
        # assert ((isinstance(result, tuple) and all(isinstance(child, Node) for child in result))
        #         or isinstance(result, Node)
        #         or isinstance(result, str)), str(result)
        self._result = (result,) if isinstance(result, Node) else result or ''
        self._children = cast(Tuple['Node', ...], self._result) \
            if isinstance(self._result, tuple) else cast(Tuple['Node', ...], ())

    @property
    def children(self) -> Tuple['Node', ...]:
        return self._children

    @property
    def len(self) -> int:
        # DEBUGGING:  print(self.tag_name, str(self.pos), str(self._len), str(self)[:10].replace('\n','.'))
        return self._len

    @property
    def pos(self) -> int:
        assert self._pos >= 0, "position value not initialized!"
        return self._pos

    @pos.setter
    def pos(self, pos: int):
        # assert isinstance(pos, int)
        self._pos = pos
        offset = 0
        for child in self.children:
            child.pos = pos + offset
            offset += child.len

    @property
    def errors(self) -> List[Error]:
        return [Error(self.pos, err) for err in self._errors]

    def show(self) -> str:
        """Returns content as string, inserting error messages where
        errors ocurred.
        """
        s = "".join(child.show_errors() for child in self.children) if self.children \
            else str(self.result)
        return (' <<< Error on "%s" | %s >>> ' % (s, '; '.join(self._errors))) if self._errors else s

    def _tree_repr(self, tab, openF, closeF, dataF=lambda s: s) -> str:
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
            for child in self.children:
                subtree = child._tree_repr(tab, openF, closeF, dataF).split('\n')
                content.append('\n'.join((tab + s) for s in subtree))
            return head + '\n'.join(content) + tail

        res = cast(str, self.result)  # safe, because if there are no children, result is a string
        if head[0] == "<" and res.find('\n') < 0:
            # for XML: place tags for leaf-nodes on one line if possible
            return head[:-1] + self.result + tail[1:]
        else:
            return head + '\n'.join([tab + dataF(s) for s in res.split('\n')]) + tail

    def as_sexpr(self, src: str=None) -> str:
        """
        Returns content as S-expression, i.e. in lisp-like form.

        Args:
            src:  The source text or `None`. In case the source text is
                given the position of the element in the text will be
                reported as line and column.
        """

        def opening(node) -> str:
            s = '(' + node.tag_name
            # s += " '(pos %i)" % node.pos
            if src:
                s += " '(pos %i " % node.pos + " %i %i)" % line_col(src, node.pos)
            if node.errors:
                s += " '(err '(%s))" % ' '.join(str(err).replace('"', r'\"')
                                                for err in node.errors)
            return s

        def pretty(s):
            return '"%s"' % s if s.find('"') < 0 \
                else "'%s'" % s if s.find("'") < 0 \
                else '"%s"' % s.replace('"', r'\"')

        return self._tree_repr('    ', opening, lambda node: ')', pretty)

    def as_xml(self, src: str=None) -> str:
        """
        Returns content as XML-tree.

        Args:
            src:  The source text or `None`. In case the source text is
                given the position will also be reported as line and
                column.
        """

        def opening(node) -> str:
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

    def add_error(self, error_str) -> 'Node':
        self._errors.append(error_str)
        self.error_flag = True
        return self

    def propagate_error_flags(self) -> None:
        """Recursively propagates error flags set on child nodes to its
        parents. This can be used if errors are added to descendant 
        nodes after syntaxtree construction, i.e. in the compile phase.
        """
        for child in self.children:
            child.propagate_error_flags()
            self.error_flag |= child.error_flag

    def collect_errors(self, clear_errors=False) -> List[Error]:
        """
        Returns all errors of this node or any child node in the form
        of a set of tuples (position, error_message), where position
        is always relative to this node.
        """
        errors = self.errors
        if clear_errors:
            self._errors = []
            self.error_flag = False
        if self.children:
            for child in self.children:
                errors.extend(child.collect_errors(clear_errors))
        return errors

    def log(self, log_file_name):
        st_file_name = log_file_name
        with open(os.path.join(log_dir(), st_file_name), "w", encoding="utf-8") as f:
            f.write(self.as_sexpr())

    def find(self, match_function) -> Iterator['Node']:
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


    # def navigate(self, path):
    #     """Yields the results of all descendant elements matched by
    #     ``path``, e.g.
    #     'd/s' yields 'l' from (d (s l)(e (r x1) (r x2))
    #     'e/r' yields 'x1', then 'x2'
    #     'e'   yields (r x1)(r x2)
    #
    #     Args:
    #         path (str):  The path of the object, e.g. 'a/b/c'. The
    #             components of ``path`` can be regular expressions
    #
    #     Returns:
    #         The object at the path, either a string or a Node or
    #         ``None``, if the path did not match.
    #     """
    #     def nav(node, pl):
    #         if pl:
    #             return itertools.chain(nav(child, pl[1:]) for child in node.children
    #                                    if re.match(pl[0], child.tag_name))
    #         else:
    #             return self.result,
    #     return nav(path.split('/'))


########################################################################
#
# syntax tree transformation functions
#
########################################################################


TransformationFunc = Union[Callable[[Node], Any], partial]


def transformation_factory(t=None):
    """Creates factory functions from transformation-functions that
    dispatch on the first parameter after the node parameter.

    Decorating a transformation-function that has more than merely the
    ``node``-parameter with ``transformation_factory`` creates a
    function with the same name, which returns a partial-function that
    takes just the node-parameter.

    Additionally, there is some some syntactic sugar for
    transformation-functions that receive a collection as their second
    parameter and do not have any further parameters. In this case a
    list of parameters passed to the factory function will be converted
    into a collection.

    Main benefit is readability of processing tables.

    Usage:
        @transformation_factory(AbtractSet[str])
        def remove_tokens(node, tokens):
            ...
      or, alternatively:
        @transformation_factory
        def remove_tokens(node, tokens: AbstractSet[str]):
            ...

    Example:
        trans_table = { 'expression': remove_tokens('+', '-') }
      instead of:
        trans_table = { 'expression': partial(remove_tokens, tokens={'+', '-'}) }
    """

    def decorator(f):
        sig = inspect.signature(f)
        params = list(sig.parameters.values())[1:]
        if len(params) == 0:
            return f  # '@transformer' not needed w/o free parameters
        assert t or params[0].annotation != params[0].empty, \
            "No type information on second parameter found! Please, use type " \
            "annotation or provide the type information via transfomer-decorator."
        p1type = t or params[0].annotation
        f = singledispatch(f)
        if len(params) == 1 and issubclass(p1type, Container) and not issubclass(p1type, Text) \
                and not issubclass(p1type, ByteString):
            def gen_special(*args):
                c = set(args) if issubclass(p1type, AbstractSet) else \
                    list(args) if issubclass(p1type, Sequence) else args
                d = {params[0].name: c}
                return partial(f, **d)

            f.register(p1type.__args__[0], gen_special)

        def gen_partial(*args, **kwargs):
            d = {p.name: arg for p, arg in zip(params, args)}
            d.update(kwargs)
            return partial(f, **d)

        f.register(p1type, gen_partial)
        return f

    if isinstance(t, type(lambda: 1)):
        # Provide for the case that transformation_factory has been
        # written as plain decorator and not as a function call that
        # returns the decorator proper.
        func = t;  t = None
        return decorator(func)
    else:
        return decorator


WHITESPACE_PTYPE = ':Whitespace'
TOKEN_PTYPE = ':Token'


def key_parser_name(node) -> str:
    return node.parser.name


def key_tag_name(node) -> str:
    return node.tag_name


def traverse(root_node, processing_table, key_func=key_tag_name) -> None:
    """Traverses the snytax tree starting with the given ``node`` depth
    first and applies the sequences of callback-functions registered
    in the ``calltable``-dictionary.
    
    The most important use case is the transformation of a concrete
    syntax tree into an abstract tree (AST). But it is also imaginable
    to employ tree-traversal for the semantic analysis of the AST.

    In order to assign sequences of callback-functions to nodes, a
    dictionary ("processing table") is used. The keys usually represent
    tag names, but any other key function is possible. There exist
    three special keys:
        '+': always called (before any other processing function)
        '*': called for those nodes for which no (other) processing
             function appears in the table
        '~': always called (after any other processing function)

    Args:
        root_node (Node): The root-node of the syntax tree to be traversed 
        processing_table (dict): node key -> sequence of functions that
            will be applied to matching nodes in order. This dictionary
            is interpreted as a ``compact_table``. See 
            ``toolkit.expand_table`` or ``EBNFCompiler.EBNFTransTable``
        key_func (function): A mapping key_func(node) -> keystr. The default
            key_func yields node.parser.name.
            
    Example:
        table = { "term": [replace_by_single_child, flatten], 
            "factor, flowmarker, retrieveop": replace_by_single_child }
        traverse(node, table)
    """
    # commented, because this approach is too error prone!
    # def funclist(call):
    #     return [as_partial(func) for func in smart_list(call)]

    # normalize processing_table entries by turning single values into lists
    # with a single value
    table = {name: smart_list(call) for name, call in list(processing_table.items())}
    table = expand_table(table)
    cache = {}

    def traverse_recursive(node):
        if node.children:
            for child in node.result:
                traverse_recursive(child)            # depth first
                node.error_flag |= child.error_flag  # propagate error flag

        key = key_func(node)
        sequence = cache.get(key, None)
        if sequence is None:
            sequence = table.get('+', []) + \
                       table.get(key, table.get('*', [])) + \
                       table.get('~', [])
            # '+' always called (before any other processing function)
            # '*' called for those nodes for which no (other) processing function
            #     appears in the table
            # '~' always called (after any other processing function)
            cache[key] = sequence

        for call in sequence:
            call(node)

    traverse_recursive(root_node)


def no_transformation(node):
    pass


# ------------------------------------------------
#
# rearranging transformations:
#     - tree may be rearranged (e.g.flattened)
#     - nodes that are not leaves may be dropped
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


@transformation_factory
def replace_parser(node, name: str):
    """Replaces the parser of a Node with a mock parser with the given
    name.

    Parameters:
        name(str): "NAME:PTYPE" of the surogate. The ptype is optional
        node(Node): The node where the parser shall be replaced
    """
    name, ptype = (name.split(':') + [''])[:2]
    node.parser = MockParser(name, ptype)


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


def collapse(node):
    """Collapses all sub-nodes by replacing the node's result with it's
    string representation.
    """
    node.result = str(node)


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
    return node.parser.ptype == WHITESPACE_PTYPE


def is_empty(node):
    return not node.result


def is_expendable(node):
    return is_empty(node) or is_whitespace(node)


def is_token(node, tokens: AbstractSet[str] = frozenset()) -> bool:
    return node.parser.ptype == TOKEN_PTYPE and (not tokens or node.result in tokens)


@transformation_factory(Callable)  # @singledispatch
def remove_children_if(node, condition):
    """Removes all nodes from the result field if the function 
    ``condition(child_node)`` evaluates to ``True``."""
    if node.children:
        node.result = tuple(c for c in node.children if not condition(c))


remove_whitespace = remove_children_if(is_whitespace)  # partial(remove_children_if, condition=is_whitespace)
remove_expendables = remove_children_if(is_expendable)  # partial(remove_children_if, condition=is_expendable)
# remove_scanner_tokens = remove_children_if(is_scanner_token)  # partial(remove_children_if, condition=is_scanner_token)


@transformation_factory
def remove_tokens(node, tokens: AbstractSet[str] = frozenset()):
    """Reomoves any among a particular set of tokens from the immediate
    descendants of a node. If ``tokens`` is the empty set, all tokens
    are removed.
    """
    remove_children_if(node, partial(is_token, tokens=tokens))


def remove_enclosing_delimiters(node):
    """Removes any enclosing delimiters from a structure (e.g. quotation marks
    from a literal or braces from a group).
    """
    if len(node.children) >= 3:
        assert not node.children[0].children and not node.children[-1].children, node.as_sexpr()
        node.result = node.result[1:-1]


def map_content(node, func: Callable[[Node], ResultType]):
    """Replaces the content of the node. ``func`` takes the node
    as an argument an returns the mapped result.
    """
    node.result = func(node.result)


########################################################################
#
# AST semantic validation functions
# EXPERIMENTAL!
#
########################################################################


@transformation_factory
def require(node, child_tags: AbstractSet[str]):
    for child in node.children:
        if child.tag_name not in child_tags:
            node.add_error('Element "%s" is not allowed inside "%s".' %
                           (child.parser.name, node.parser.name))


@transformation_factory
def forbid(node, child_tags: AbstractSet[str]):
    for child in node.children:
        if child.tag_name in child_tags:
            node.add_error('Element "%s" cannot be nested inside "%s".' %
                           (child.parser.name, node.parser.name))


@transformation_factory
def assert_content(node, regex: str):
    content = str(node)
    if not re.match(regex, content):
        node.add_error('Element "%s" violates %s on %s' %
                       (node.parser.name, str(regex), content))

