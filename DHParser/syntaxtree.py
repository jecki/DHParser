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

import collections.abc
import copy
import os
from functools import partial

from DHParser.error import Error, linebreaks, line_col
from DHParser.stringview import StringView
from DHParser.toolkit import is_logging, log_dir, re, typing
from typing import Any, Callable, cast, Iterator, List, Union, Tuple, Hashable, Optional


__all__ = ('ParserBase',
           'WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'MockParser',
           'ZombieParser',
           'ZOMBIE_PARSER',
           'Node',
           'mock_syntax_tree',
           'TransformationFunc')


#######################################################################
#
# parser base and mock parsers
#
#######################################################################


class ParserBase:
    """
    ParserBase is the base class for all real and mock parser classes.
    It is defined here, because Node objects require a parser object
    for instantiation.
    """
    def __init__(self, name=''):  # , pbases=frozenset()):
        self._name = name  # type: str
        self._ptype = ':' + self.__class__.__name__  # type: str

    def __repr__(self):
        return self.name + self.ptype

    def __str__(self):
        return self.name + (' = ' if self.name else '') + repr(self)

    def __call__(self, text: StringView) -> Tuple[Optional['Node'], StringView]:
        return None, text

    @property
    def name(self):
        """Returns the name of the parser or the empty string '' for unnamed
        parsers."""
        return self._name

    @property
    def ptype(self) -> str:
        """Returns the type of the parser. By default this is the parser's
        class name preceded by a colon, e.g. ':ZeroOrMore'."""
        return self._ptype

    @property
    def repr(self) -> str:
        """Returns the parser's name if it has a name and the parser's
        `ptype` otherwise. Note that for named parsers this is not the
        same as `repr(parsers)` which always returns the comined name
        and ptype, e.g. 'term:OneOrMore'."""
        return self.name if self.name else repr(self)

    def reset(self):
        """Resets any parser variables. (Should be overridden.)"""
        pass

    def grammar(self) -> Optional[object]:
        """Returns the Grammar object to which the parser belongs. If not
        yet connected to any Grammar object, None is returned."""
        return None

    def apply(self, func: Callable) -> bool:
        """Applies the function `func` to the parser. Returns False, if
        - for whatever reason - the functions has not been applied, True
        otherwise."""
        return False


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
        super().__init__(name)
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


#######################################################################
#
# syntaxtree nodes
#
#######################################################################


ChildrenType = Tuple['Node', ...]
NoChildren = cast(ChildrenType, ())  # type: ChildrenType
StrictResultType = Union[ChildrenType, str]
ResultType = Union[ChildrenType, 'Node', StringView, str, None]


def flatten_sxpr(sxpr: str) -> str:
    """Returns S-expression `sxpr` as a one-liner without unnecessary
    whitespace.

    Example:
    >>> flatten_sxpr('(a\\n    (b\\n        c\\n    )\\n)\\n')
    '(a (b c))'
    """
    return re.sub(r'\s(?=\))', '', re.sub(r'\s+', ' ', sxpr)).strip()


class Node(collections.abc.Sized):
    """
    Represents a node in the concrete or abstract syntax tree.

    Attributes and Properties:
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
        error_flag (int):  0 if no error occurred in either the node
            itself or any of its descendants. Otherwise contains the
            highest warning or error level or all errors that occurred.
        len (int):  The full length of the node's string result if the
            node is a leaf node or, otherwise, the concatenated string
            result's of its descendants. The figure always represents
            the length before AST-transformation and will never change
            through AST-transformation. READ ONLY!
        pos (int):  the position of the node within the parsed text.

            The value of ``pos`` is -1 meaning invalid by default.
            Setting this value will set the positions of all child
            nodes relative to this value.

            To set the pos values of all nodes in a syntax tree, the
            pos value of the root node should be set to 0 right
            after parsing.

            Other than that, this value should be considered READ ONLY.
            At any rate, it should only be reassigned during the parsing
            stage and never during or after the AST-transformation.
    """

    __slots__ = ['_result', 'children', '_errors', '_len', '_pos', 'parser', 'error_flag']


    def __init__(self, parser, result: ResultType, leafhint: bool = False) -> None:
        """
        Initializes the ``Node``-object with the ``Parser``-Instance
        that generated the node and the parser's result.
        """
        self.error_flag = 0             # type: int
        self._errors = []               # type: List[Error]
        self._pos = -1                  # type: int
        # Assignment to self.result initializes the attributes _result, children and _len
        # The following if-clause is merely an optimization, i.e. a fast-path for leaf-Nodes
        if leafhint:
            self._result = str(result)  # type: StrictResultType
            self.children = NoChildren  # type: ChildrenType
            self._len = -1              # type: int  # lazy evaluation
        else:
            self.result = result
        self.parser = parser or ZOMBIE_PARSER


    def __str__(self):
        s = "".join(str(child) for child in self.children) if self.children else self.result
        if self._errors:
            return ' <<< Error on "%s" | %s >>> ' % \
                   (s, '; '.join(e.message for e in self._errors))
        return s


    def __repr__(self):
        mpargs = {'name': self.parser.name, 'ptype': self.parser.ptype}
        parg = "MockParser({name}, {ptype})".format(**mpargs)
        rarg = str(self) if not self.children else \
               "(" + ", ".join(repr(child) for child in self.children) + ")"
        return "Node(%s, %s)" % (parg, rarg)


    def __len__(self):
        if self._len < 0:
            self._len = sum(len(child) for child in self.children) \
                if self.children else len(self._result)
        return self._len



    def __bool__(self):
        # A node that is not None is always True, even if it's empty
        return True


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
        """
        Returns the tage name of Node, i.e. the name for XML or
        S-expression representation. By default the tag name is the
        name of the node's parser or, if the node's parser is unnamed, the
        node's parser's `ptype`.
        """
        return self.parser.name or self.parser.ptype


    @property
    def result(self) -> StrictResultType:
        """
        Returns the result from the parser that created the node.
        Error messages are not included in the result. Use `self.content()`
        if the result plus any error messages is needed.
        """
        return self._result


    @result.setter
    def result(self, result: ResultType):
        # # made obsolete by static type checking with mypy
        # assert ((isinstance(result, tuple) and all(isinstance(child, Node) for child in result))
        #         or isinstance(result, Node)
        #         or isinstance(result, str)), str(result)
        # Possible optimization: Do not allow single nodes as argument:
        # assert not isinstance(result, Node)
        self._len = -1  # lazy evaluation
        if isinstance(result, Node):
            self.children = (result,)
            self._result = self.children
            self.error_flag = result.error_flag
            # if self._pos < 0:
            #     self._pos = result._pos
        else:
            if isinstance(result, tuple):
                self.children = result
                self._result = result or ''
                if result:
                    if self.error_flag == 0:
                        self.error_flag = max(child.error_flag for child in self.children)
                    # if self._pos < 0:
                    #     self._pos = result[0]._pos
            else:
                self.children = NoChildren
                self._result = str(result)
        # # shorter but slower:
        # self._result = (result,) if isinstance(result, Node) else result or ''  # type: StrictResultType
        # self.children = cast(ChildrenType, self._result) \
        #     if isinstance(self._result, tuple) else NoChildren  # type: ChildrenType
        # if self.children:
        #     self.error_flag = max(self.error_flag,
        #                           max(child.error_flag for child in self.children))  # type: bool


    @property
    def content(self) -> str:
        """
        Returns content as string, inserting error messages where
        errors occurred.
        """
        if self.children:
            return "".join(child.content for child in self.children)
        return self._result


    @property
    def structure(self) -> str:
        """
        Return structure (and content) as S-expression on a single line
        without any line breaks.
        """
        return flatten_sxpr(self.as_sxpr(showerrors=False))


    @property
    def pos(self) -> int:
        """Returns the position of the Node's content in the source text."""
        if self._pos < 0:
            raise AssertionError("Position value not initialized!")
        return self._pos


    def init_pos(self, pos: int, overwrite: bool = False) -> 'Node':
        """
        (Re-)initialize position value. Usually, the parser guard
        (`parsers.add_parser_guard()`) takes care of assigning the
        position in the document to newly created nodes. However,
        where Nodes are created outside the reach of the parser
        guard, their document-position must be assigned manually.
        This function recursively reassigns the position values
        of the child nodes, too.
        """
        if overwrite or self._pos < 0:
            self._pos = pos
            for err in self._errors:
                err.pos = pos
        else:
            assert self._pos == pos, str("%i != %i" % (self._pos, pos))
        # recursively adjust pos-values of all children
        offset = self.pos
        for child in self.children:
            child.init_pos(offset, overwrite)
            offset = child.pos + len(child)
        return self


    @property
    def errors(self) -> List[Error]:
        """
        Returns the errors that occurred at this Node,
        not including any errors from child nodes.
        """
        return self._errors.copy()


    def add_error(self,
                  message: str,
                  code: int = Error.ERROR) -> 'Node':
        """
        Adds an error to this Node.
        Parameters:
            message(str): A string with the error message.abs
            code(int):    An error code to identify the kind of error
        """
        self._errors.append(Error(message, code))
        self.error_flag = max(self.error_flag, self._errors[-1].code)
        return self


    def collect_errors(self, clear_errors=False) -> List[Error]:
        """
        Recursively adds line- and column-numbers to all error objects.
        Returns all errors of this node or any child node in the form
        of a set of tuples (position, error_message), where position
        is always relative to this node.
        """
        errors = self.errors
        for err in errors:
            err.pos = self.pos
        if self.children:
            for child in self.children:
                errors.extend(child.collect_errors(clear_errors))
        if clear_errors:
            self._errors = []
            self.error_flag = 0
        else:
            if self._errors:
                self.error_flag = max(err.code for err in self.errors)
            if self.children:
                max_child_error = max(child.error_flag for child in self.children)
                self.error_flag = max(self.error_flag, max_child_error)
        return errors



    def _tree_repr(self, tab, open_fn, close_fn, data_fn=lambda i: i, density=0) -> str:
        """
        Generates a tree representation of this node and its children
        in string from.

        The kind ot tree-representation that is determined by several
        function parameters. This could be an XML-representation or a
        lisp-like S-expression.

        Args:
            tab (str):  The indentation string, e.g. '\t' or '    '
            open_fn:   (Node->str) A function that returns an opening
                string (e.g. an XML-tag_name) for a given node
            close_fn:  (Node->str) A function that returns a closeF
                string (e.g. an XML-tag_name) for a given node.
            data_fn:   (str->str) A function that filters the data string
                before printing, e.g. to add quotation marks

        Returns (str):
            A string that contains a (serialized) tree representation
            of the node and its children.
        """
        head = open_fn(self)
        tail = close_fn(self)

        if not self.result:
            return head.rstrip() + tail.lstrip()

        tail = tail.lstrip(None if density & 2 else '')

        if self.children:
            content = []
            for child in self.children:
                subtree = child._tree_repr(tab, open_fn, close_fn, data_fn, density).split('\n')
                content.append('\n'.join((tab + s) for s in subtree))
            return head + '\n'.join(content) + tail

        res = cast(str, self.result)  # safe, because if there are no children, result is a string
        if density & 1 and res.find('\n') < 0:  # and head[0] == "<":
            # except for XML, add a gap between opening statement and content
            gap = ' ' if head.rstrip()[-1] != '>' else ''
            return head.rstrip() + gap + data_fn(self.result) + tail.lstrip()
        else:
            return head + '\n'.join([tab + data_fn(s) for s in res.split('\n')]) + tail


    def as_sxpr(self, src: str = None, compact: bool = False, showerrors: bool = True) -> str:
        """
        Returns content as S-expression, i.e. in lisp-like form.

        Args:
            src:  The source text or `None`. In case the source text is
                given the position of the element in the text will be
                reported as line and column.
            compact:  If True a compact representation is returned where
                brackets are ommited and only the indentation indicates the
                tree structure.
        """

        left_bracket, right_bracket, density = ('', '', 1) if compact else ('(', '\n)', 0)

        def opening(node) -> str:
            """Returns the opening string for the representation of `node`."""
            txt = left_bracket + node.tag_name
            # s += " '(pos %i)" % node.pos
            if src:
                txt += " '(pos %i " % node.pos  # + " %i %i)" % line_col(src, node.pos)
            # if node.error_flag:   # just for debugging error collecting
            #     txt += " HAS ERRORS"
            if showerrors and node.errors:
                txt += " '(err '(%s))" % ' '.join(str(err).replace('"', r'\"')
                                                  for err in node.errors)
            return txt + '\n'

        def closing(node) -> str:
            """Returns the closing string for the representation of `node`."""
            return right_bracket

        def pretty(strg):
            """Encloses `strg` with the right kind of quotation marks."""
            return '"%s"' % strg if strg.find('"') < 0 \
                else "'%s'" % strg if strg.find("'") < 0 \
                else '"%s"' % strg.replace('"', r'\"')

        return self._tree_repr('    ', opening, closing, pretty, density=density)


    def as_xml(self, src: str = None, showerrors: bool = True) -> str:
        """
        Returns content as XML-tree.

        Args:
            src:  The source text or `None`. In case the source text is
                given the position will also be reported as line and
                column.
        """

        def opening(node) -> str:
            """Returns the opening string for the representation of `node`."""            
            txt = '<' + node.tag_name
            # s += ' pos="%i"' % node.pos
            if src:
                txt += ' line="%i" col="%i"' % line_col(line_breaks, node.pos)
            if showerrors and node.errors:
                txt += ' err="%s"' % ''.join(str(err).replace('"', r'\"') for err in node.errors)
            return txt + ">\n"

        def closing(node):
            """Returns the closing string for the representation of `node`."""            
            return '\n</' + node.tag_name + '>'

        line_breaks = linebreaks(src) if src else []
        return self._tree_repr('    ', opening, closing, density=1)


    def find(self, match_function: Callable) -> Iterator['Node']:
        """
        Finds nodes in the tree that match a specific criterion.

        `find` is a generator that yields all nodes for which the
        given `match_function` evaluates to True. The tree is
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
                for node in child.find(match_function):
                    yield node


    def tree_size(self) -> int:
        """
        Recursively counts the number of nodes in the tree including the root node.
        """
        return sum(child.tree_size() for child in self.children) + 1


    def log(self, log_file_name):
        """
        Writes an S-expression-representation of the tree with root `self` to a file.
        """
        if is_logging():
            path = os.path.join(log_dir(), log_file_name)
            if os.path.exists(path):
                print('WARNING: Log-file "%s" already exists and will be overwritten!' % path)
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.as_sxpr())


def mock_syntax_tree(sxpr):
    """
    Generates a tree of nodes from an S-expression. The main purpose of this is
    to generate test data.

    Example:
    >>> mock_syntax_tree("(a (b c))").as_sxpr()
    '(a\\n    (b\\n        "c"\\n    )\\n)'
    """

    def next_block(s):
        """Generator that yields all characters until the next closing bracket
        that does not match an opening bracket matched earlier within the same
        package."""
        s = s.strip()
        try:
            while s[0] != ')':
                if s[0] != '(':
                    raise ValueError('"(" expected, not ' + s[:10])
                # assert s[0] == '(', s
                level = 1
                k = 1
                while level > 0:
                    if s[k] == '(':
                        level += 1
                    elif s[k] == ')':
                        level -= 1
                    k += 1
                yield s[:k]
                s = s[k:].strip()
        except IndexError:
            errmsg = ('Malformed S-expression. Unprocessed part: "%s"' % s) if s \
                else 'Malformed S-expression. Closing bracket(s) ")" missing.'
            raise AssertionError(errmsg)

    sxpr = sxpr.strip()
    if sxpr[0] != '(':
        raise ValueError('"(" expected, not ' + sxpr[:10])
    # assert sxpr[0] == '(', sxpr
    sxpr = sxpr[1:].strip()
    match = re.match(r'[\w:]+', sxpr)
    if match is None:
        raise AssertionError('Malformed S-expression Node-tagname or identifier expected, '
                             'not "%s"' % sxpr[:40].replace('\n', ''))
    name, class_name = (sxpr[:match.end()].split(':') + [''])[:2]
    sxpr = sxpr[match.end():].strip()
    if sxpr[0] == '(':
        result = tuple(mock_syntax_tree(block) for block in next_block(sxpr))
        pos = 0
        for node in result:
            node._pos = pos
            pos += len(node)
    else:
        lines = []
        while sxpr and sxpr[0] != ')':
            for qtmark in ['"""', "'''", '"', "'"]:
                match = re.match(qtmark + r'.*?' + qtmark, sxpr, re.DOTALL)
                if match:
                    i = len(qtmark)
                    lines.append(sxpr[i:match.end() - i])
                    sxpr = sxpr[match.end():].strip()
                    break
            else:
                match = re.match(r'(?:(?!\)).)*', sxpr, re.DOTALL)
                lines.append(sxpr[:match.end()])
                sxpr = sxpr[match.end():]
        result = "\n".join(lines)
    node = Node(MockParser(name, ':' + class_name), result)
    node._pos = 0
    return node


TransformationFunc = Union[Callable[[Node], Any], partial]


# if __name__ == "__main__":
#     st = mock_syntax_tree("(alpha (beta (gamma i\nj\nk) (delta y)) (epsilon z))")
#     print(st.as_sxpr())
#     print(st.as_xml())
