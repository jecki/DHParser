"""syntaxtree.py - syntax tree classes for DHParser

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

import copy
import os
from functools import partial

try:
    import regex as re
except ImportError:
    import re
try:
    from typing import AbstractSet, Any, ByteString, Callable, cast, Container, Dict, \
        Iterator, List, NamedTuple, Sequence, Union, Text, Tuple
except ImportError:
    from .typing34 import AbstractSet, Any, ByteString, Callable, cast, Container, Dict, \
        Iterator, List, NamedTuple, Sequence, Union, Text, Tuple

from DHParser.toolkit import is_logging, log_dir, line_col, identity

__all__ = ('WHITESPACE_PTYPE',
           'MockParser',
           'TOKEN_PTYPE',
           'ZOMBIE_PARSER',
           'ParserBase',
           'Error',
           'Node',
           'mock_syntax_tree',
           'TransformationFunc')


class ParserBase:
    """
    ParserBase is the base class for all real and mock parser classes.
    It is defined here, because Node objects require a parser object
    for instantiation.
    """
    def __init__(self, name=''):  # , pbases=frozenset()):
        self.name = name  # type: str
        self._ptype = ':' + self.__class__.__name__  # type: str

    def __repr__(self):
        return self.name + self.ptype

    def __str__(self):
        return self.name + (' = ' if self.name else '') + repr(self)

    @property
    def ptype(self) -> str:
        return self._ptype

    @property
    def repr(self) -> str:
        return self.name if self.name else repr(self)


WHITESPACE_PTYPE = ':Whitespace'
TOKEN_PTYPE = ':Token'


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

ChildrenType = Tuple['Node', ...]
StrictResultType = Union[ChildrenType, str]
ResultType = Union[ChildrenType, 'Node', str, None]


def oneliner_sxpr(sxpr: str) -> str:
    """Returns S-expression `sxpr` as a one liner without unnecessary
    whitespace.

    Example:
    >>> oneliner_sxpr('(a\\n    (b\\n        c\\n    )\\n)\\n')
    '(a (b c))'
    """
    return re.sub('\s(?=\))', '', re.sub('\s+', ' ', sxpr)).strip()


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
        # self._result = ''  # type: StrictResultType
        # self._children = ()  # type: ChildrenType
        self._errors = []  # type: List[str]
        self.result = result
        self._len = len(result) if not self._children else \
            sum(child._len for child in self._children)  # type: int
        # self.pos: int  = 0  # continuous updating of pos values wastes a lot of time
        self._pos = -1  # type: int
        self.parser = parser or ZOMBIE_PARSER

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

    @property
    def result(self) -> StrictResultType:
        return self._result

    @result.setter
    def result(self, result: ResultType):
        # # made obsolete by static type checking with mypy is done
        # assert ((isinstance(result, tuple) and all(isinstance(child, Node) for child in result))
        #         or isinstance(result, Node)
        #         or isinstance(result, str)), str(result)
        self._result = (result,) if isinstance(result, Node) else result or ''  # type: StrictResultType
        self._children = cast(ChildrenType, self._result) \
            if isinstance(self._result, tuple) else cast(ChildrenType, ())  # type: ChildrenType
        self.error_flag = any(r.error_flag for r in self._children) \
            if self._children else False  # type: bool

    @property
    def children(self) -> ChildrenType:
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

    def add_error(self, error_str: str) -> 'Node':
        assert isinstance(error_str, str)
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
            self.error_flag = self.error_flag or child.error_flag

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

    def _tree_repr(self, tab, openF, closeF, dataF=identity, density=0) -> str:
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
            return head.rstrip() + tail.lstrip()

        D = None if density & 2 else ''

        if self.children:
            content = []
            for child in self.children:
                subtree = child._tree_repr(tab, openF, closeF, dataF, density).split('\n')
                content.append('\n'.join((tab + s) for s in subtree))
            return head + '\n'.join(content) + tail.lstrip(D)

        res = cast(str, self.result)  # safe, because if there are no children, result is a string
        if density & 1 and res.find('\n') < 0:  # and head[0] == "<":
            # except for XML, add a gap between opening statement and content
            gap = ' ' if head.rstrip()[-1] != '>' else ''
            return head.rstrip() + gap + dataF(self.result) + tail.lstrip()
        else:
            return head + '\n'.join([tab + dataF(s) for s in res.split('\n')]) + tail.lstrip(D)

    def as_sxpr(self, src: str=None) -> str:
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
            return s + '\n'

        def pretty(s):
            return '"%s"' % s if s.find('"') < 0 \
                else "'%s'" % s if s.find("'") < 0 \
                else '"%s"' % s.replace('"', r'\"')

        return self._tree_repr('    ', opening, lambda node: '\n)', pretty, density=0)

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
            return s + ">\n"

        def closing(node):
            return '\n</' + node.tag_name + '>'

        return self._tree_repr('    ', opening, closing, density=1)

    def structure(self) -> str:
        """Return structure (and content) as S-expression on a single line
        without any line breaks."""
        return oneliner_sxpr(self.as_sxpr())

    def content(self) -> str:
        """
        Returns content as string, inserting error messages where
        errors occurred.
        """
        s = "".join(child.content() for child in self.children) if self.children \
            else str(self.result)
        return (
        ' <<< Error on "%s" | %s >>> ' % (s, '; '.join(self._errors))) if self._errors else s

    def find(self, match_function: Callable) -> Iterator['Node']:
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

    def log(self, log_file_name):
        if is_logging():
            st_file_name = log_file_name
            with open(os.path.join(log_dir(), st_file_name), "w", encoding="utf-8") as f:
                f.write(self.as_sxpr())


def mock_syntax_tree(sxpr):
    """
    Generates a tree of nodes from an S-expression.

    Example:
    >>> mock_syntax_tree("(a (b c))").as_sxpr()
    '(a\\n    (b\\n        "c"\\n    )\\n)'
    """

    def next_block(s):
        s = s.strip()
        while s[0] != ')':
            if s[0] != '(': raise ValueError('"(" expected, not ' + s[:10])
            # assert s[0] == '(', s
            level = 1
            i = 1
            while level > 0:
                if s[i] == '(':
                    level += 1
                elif s[i] == ')':
                    level -= 1
                i += 1
            yield s[:i]
            s = s[i:].strip()

    sxpr = sxpr.strip()
    if sxpr[0] != '(': raise ValueError('"(" expected, not ' + sxpr[:10])
    # assert sxpr[0] == '(', sxpr
    sxpr = sxpr[1:].strip()
    m = re.match('[\w:]+', sxpr)
    name, class_name = (sxpr[:m.end()].split(':') + [''])[:2]
    sxpr = sxpr[m.end():].strip()
    if sxpr[0] == '(':
        result = tuple(mock_syntax_tree(block) for block in next_block(sxpr))
    else:
        lines = []
        while sxpr and sxpr[0] != ')':
            for qm in ['"""', "'''", '"', "'"]:
                m = re.match(qm + r'.*?' + qm, sxpr, re.DOTALL)
                if m:
                    i = len(qm)
                    lines.append(sxpr[i:m.end() - i])
                    sxpr = sxpr[m.end():].strip()
                    break
            else:
                m = re.match(r'(?:(?!\)).)*', sxpr, re.DOTALL)
                lines.append(sxpr[:m.end()])
                sxpr = sxpr[m.end():]
        result = "\n".join(lines)
    return Node(MockParser(name, ':' + class_name), result)


TransformationFunc = Union[Callable[[Node], Any], partial]


# if __name__ == "__main__":
#     st = mock_syntax_tree("(alpha (beta (gamma i\nj\nk) (delta y)) (epsilon z))")
#     print(st.as_sxpr())
#     print(st.as_xml())
