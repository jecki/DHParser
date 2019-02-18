# syntaxtree.py - syntax tree classes for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.


"""
Module ``syntaxtree`` defines the ``Node``-class for syntax trees as well
as an abstract base class for parser-objects. The latter is defined
here, because node-objects refer to parser-objects. All concrete
parser classes are defined in the ``parse`` module.
"""

from collections import OrderedDict
import copy

from DHParser.error import Error, ErrorCode, linebreaks, line_col
from DHParser.stringview import StringView
from DHParser.toolkit import get_config_value, re
from typing import Callable, cast, Iterator, List, AbstractSet, Set, Union, Tuple, Optional


__all__ = ('WHITESPACE_PTYPE',
           'TOKEN_PTYPE',
           'ZOMBIE_TAG',
           'PLACEHOLDER',
           'ResultType',
           'StrictResultType',
           'ChildrenType',
           'Node',
           'serialize',
           'FrozenNode',
           'tree_sanity_check',
           'RootNode',
           'parse_sxpr',
           'parse_xml',
           'parse_tree',
           'flatten_sxpr',
           'flatten_xml')


#######################################################################
#
# parser base and mock parsers
#
#######################################################################


WHITESPACE_PTYPE = ':Whitespace'
TOKEN_PTYPE = ':Token'

ZOMBIE_TAG = "__ZOMBIE__"

#######################################################################
#
# syntaxtree nodes
#
#######################################################################


ChildrenType = Tuple['Node', ...]
NoChildren = cast(ChildrenType, ())  # type: ChildrenType
StrictResultType = Union[ChildrenType, StringView, str]
ResultType = Union[ChildrenType, 'Node', StringView, str, None]


def flatten_sxpr(sxpr: str) -> str:
    """
    Returns S-expression ``sxpr`` as a one-liner without unnecessary
    whitespace.

    Example:
    >>> flatten_sxpr('(a\\n    (b\\n        c\\n    )\\n)\\n')
    '(a (b c))'
    """

    return re.sub(r'\s(?=\))', '', re.sub(r'\s+', ' ', sxpr)).strip()


def flatten_xml(xml: str) -> str:
    """
    Returns an XML-tree as a one liner without unnecessary whitespace,
    i.e. only whitespace within leaf-nodes is preserved.
    A more precise alternative to `flatten_xml` is to use Node.as_xml()
    ans passing a set containing the top level tag to parameter `inline_tags`.
    """

    # works only with regex
    # return re.sub(r'\s+(?=<\w)', '', re.sub(r'(?<=</\w+>)\s+', '', xml))
    def tag_only(m):
        return m.groupdict()['closing_tag']
    return re.sub(r'\s+(?=<[\w:])', '', re.sub(r'(?P<closing_tag></:?\w+>)\s+', tag_only, xml))


RX_AMP = re.compile(r'&(?!\w+;)')


class Node:  # (collections.abc.Sized): Base class omitted for cython-compatibility
    """
    Represents a node in the concrete or abstract syntax tree.

    TODO: Add some documentation and doc-tests here...

    Attributes:
        tag_name (str):  The name of the node, which is either its
            parser's name or, if that is empty, the parser's class name

        result (str or tuple):  The result of the parser which
            generated this node, which can be either a string or a
            tuple of child nodes.

        children (tuple):  The tuple of child nodes or an empty tuple
            if there are no child nodes. READ ONLY!

        content (str):  Yields the contents of the tree as string. The
            difference to ``str(node)`` is that ``node.content`` does
            not add the error messages to the returned string.

        parser (Parser):  The parser which generated this node.
            WARNING: In case you use mock syntax trees for testing or
            parser replacement during the AST-transformation: DO NOT
            rely on this being a real parser object in any phase after
            parsing (i.e. AST-transformation and compiling), for
            example by calling ``isinstance(node.parer, ...)``.

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

        attr (dict): An optional dictionary of XML-attr. This
            dictionary is created lazily upon first usage. The attr
            will only be shown in the XML-Representation, not in the
            S-Expression-output.
    """

    __slots__ = '_result', 'children', '_len', '_pos', 'tag_name', '_xml_attr', '_content'

    def __init__(self, tag_name: str, result: ResultType, leafhint: bool = False) -> None:
        """
        Initializes the ``Node``-object with the ``Parser``-Instance
        that generated the node and the parser's result.
        """
        self._pos = -1                  # type: int
        # Assignment to self.result initializes the attr _result, children and _len
        # The following if-clause is merely an optimization, i.e. a fast-path for leaf-Nodes
        if leafhint:
            self._result = result       # type: StrictResultType  # cast(StrictResultType, result)
            self._content = None        # type: Optional[str]
            self.children = NoChildren  # type: ChildrenType
            self._len = -1              # type: int  # lazy evaluation
        else:
            self.result = result
        self.tag_name = tag_name        # type: str

    def __deepcopy__(self, memo):
        if self.children:
            duplicate = self.__class__(self.tag_name, copy.deepcopy(self.children), False)
        else:
            duplicate = self.__class__(self.tag_name, self.result, True)
        duplicate._pos = self._pos
        duplicate._len = self._len
        if self.attr_active():
            duplicate.attr.update(copy.deepcopy(self._xml_attr))
            # duplicate._xml_attr = copy.deepcopy(self._xml_attr)  # this is not cython compatible
        return duplicate

    def __str__(self):
        if isinstance(self, RootNode):
            root = cast(RootNode, self)
            errors = root.errors_sorted
            if errors:
                e_pos = errors[0].pos
                return self.content[:e_pos] + \
                   ' <<< Error on "%s" | %s >>> ' % \
                   (self.content[e_pos - self.pos:], '; '.join(e.message for e in errors))
        return self.content

    def __repr__(self):
        # mpargs = {'name': self.parser.name, 'ptype': self.parser.ptype}
        # name, ptype = (self._tag_name.split(':') + [''])[:2]
        # parg = "MockParser({name}, {ptype})".format(name=name, ptype=ptype)
        rarg = str(self) if not self.children else \
            "(" + ", ".join(child.__repr__() for child in self.children) + ")"
        return "Node(%s, %s)" % (self.tag_name, rarg)


    def __len__(self):
        if self._len < 0:
            self._len = sum(len(child) for child in self.children) \
                if self.children else len(self._result)
        return self._len


    def __bool__(self):
        # A node that is not None is always True, even if it's empty
        return True


    # can lead to obscure mistakes, where default object comparison behaviour is expected
    # def __eq__(self, other):
    #     """
    #     Equality of nodes: Two nodes are considered as equal, if their tag
    #     name is the same, if their results are equal and if their attributes
    #     and attribute values are the same.
    #     """
    #     return self.tag_name == other.tag_name and self.result == other.result \
    #         and self.compare_attr(other)


    def __hash__(self):
        return hash(self.tag_name)


    def __getitem__(self, index_or_tagname: Union[int, str]) -> Union['Node', Iterator['Node']]:
        """
        Returns the child node with the given index if ``index_or_tagname`` is
        an integer or the first child node with the given tag name. Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")))')
            >>> flatten_sxpr(tree[0].as_sxpr())
            '(b "X")'
            >>> flatten_sxpr(tree["X"].as_sxpr())
            '(X (c "d"))'

        Args:
            index_or_tagname(str): Either an index of a child node or a
                tag name.
        Returns:
            Node: All nodes which have a given tag name.
        """
        if self.children:
            if isinstance(index_or_tagname, int):
                return self.children[index_or_tagname]
            else:
                for child in self.children:
                    if child.tag_name == index_or_tagname:
                        return child
                raise KeyError(index_or_tagname)
        raise ValueError('Leave nodes have no children that can be indexed!')


    def __contains__(self, tag_name: str) -> bool:
        """
        Returns true if a child with the given tag name exists.
        Args:
            tag_name (str): tag_name which will be searched among to immediate
                descendants of this node.
        Returns:
            bool:  True, if at least one descendant node with the given tag
                name exists, False otherwise
        """
        # assert isinstance(tag_name, str)
        if self.children:
            for child in self.children:
                if child.tag_name == tag_name:
                    return True
            return False
        raise ValueError('Leave node cannot contain other nodes')


    def equals(self, other: 'Node') -> bool:
        """
        Equality of value: Two nodes are considered as having the same value,
        if their tag name is the same, if their results are equal and
        if their attributes and attribute values are the same.

        Returns True, if the tree originating in node `self` is equal by
        value to the tree originating in node `other`.
        """
        if self.tag_name == other.tag_name and self.compare_attr(other):
            if self.children:
                return (len(self.children) == len(other.children)
                        and all(a.equals(b) for a, b in zip(self.children, other.children)))
            else:
                return self.result == other.result
        return False


    def get(self, index_or_tagname: Union[int, str],
            surrogate: Union['Node', Iterator['Node']]) -> Union['Node', Iterator['Node']]:
        """Returns the child node with the given index if ``index_or_tagname``
        is an integer or the first child node with the given tag name. If no
        child with the given index or tag_name exists, the ``surrogate`` is
        returned instead. This mimics the behaviour of Python's dictionary's
        get-method.
        """
        try:
            return self[index_or_tagname]
        except KeyError:
            return surrogate


    def is_anonymous(self) -> bool:
        return not self.tag_name or self.tag_name[0] == ':'


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
        assert ((isinstance(result, tuple) and all(isinstance(child, Node) for child in result))
                or isinstance(result, Node)
                or isinstance(result, str)
                or isinstance(result, StringView)), "%s (%s)" % (str(result), str(type(result)))
        # Possible optimization: Do not allow single nodes as argument:
        # assert not isinstance(result, Node)
        self._len = -1        # lazy evaluation
        self._content = None
        if isinstance(result, Node):
            self.children = (result,)
            self._result = self.children
        else:
            if isinstance(result, tuple):
                self.children = result
                self._result = result or ''
            else:
                self.children = NoChildren
                self._result = result  # cast(StrictResultType, result)


    @property
    def content(self) -> str:
        """
        Returns content as string. If the node has child-nodes, the
        string content of the child-nodes is recursively read and then
        concatenated.
        """
        if self._content is None:
            if self.children:
                self._content = "".join(child.content for child in self.children)
            else:
                # self._content = self._result
                self._content = str(self._result)
                self._result = self._content  # self._result might be more efficient as a string!?
        return self._content
    #
    #
    # @content.setter
    # def content(self, content: str):
    #     self.result = content


    @property
    def structure(self) -> str:
        """
        Return structure (and content) as S-expression on a single line
        without any line breaks.
        """
        return flatten_sxpr(self.as_sxpr())


    @property
    def pos(self) -> int:
        """Returns the position of the Node's content in the source text."""
        if self._pos < 0:
            raise AssertionError("Position value not initialized! Use Node.with_pos()")
        return self._pos


    def with_pos(self, pos: int) -> 'Node':
        """
        Initialize position value. Usually, the parser guard
        (`parsers.add_parser_guard()`) takes care of assigning the
        position in the document to newly created nodes. However,
        when Nodes are created outside the reach of the parser
        guard, their document-position must be assigned manually.
        Position values of the child nodes are assigned recursively, too.
        Returns the node itself for convenience.
        """
        # condition self.pos == pos cannot be assumed when tokens or whitespace
        # are dropped early!
        # assert self._pos < 0 or self.pos == pos, ("pos mismatch %i != %i at Node: %s"
        #                                           % (self._pos, pos, repr(self)))
        if pos != self._pos >= 0:
            raise AssertionError("Position value cannot be reassigned to a different value!")
        if self._pos < 0:
            self._pos = pos
            # recursively adjust pos-values of all children
            offset = self.pos
            for child in self.children:
                if child._pos < 0:
                    child.with_pos(offset)
                offset = child.pos + len(child)
        return self


    @property
    def attr(self):
        """
        Returns a dictionary of XML-attr attached to the node.
        """
        try:
            if self._xml_attr is None:          # cython compatibility
                self._xml_attr = OrderedDict()
        except AttributeError:
            self._xml_attr = OrderedDict()
        return self._xml_attr


    def attr_active(self) -> bool:
        """
        Returns True, if XML-Attributes of this node have ever been set
        or queried, even if unsuccessfully.
        """
        try:
            if self._xml_attr is not None:
                return True
        except AttributeError:
            pass
        return False


    def compare_attr(self, other: 'Node') -> bool:
        """
        Returns True, if `self` and `other` have the same attributes with the
        same attribute values.
        """
        if self.attr_active():
            if other.attr_active():
                return self.attr == other.attr
            return len(self.attr) == 0
            # self has empty dictionary and other has no attributes
        elif other.attr_active():
            return len(other.attr) == 0
            # other has empty attribute dictionary and self as no attributes
        return True  # neither self nor other have any attributes


    def _tree_repr(self, tab, open_fn, close_fn, data_fn=lambda i: i,
                   density=0, inline=False, inline_fn=lambda node: False) -> str:
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

        inline = inline or inline_fn(self)
        if inline:
            head = head.rstrip()
            tail = tail.lstrip()
            usetab, sep = '', ''
        else:
            usetab = tab if head else ''    # no indentation if tag is already omitted
            sep = '\n'

        if self.children:
            content = []
            for child in self.children:
                subtree = child._tree_repr(tab, open_fn, close_fn, data_fn,
                                           density, inline, inline_fn)
                if subtree:
                    st = [subtree] if inline else subtree.split('\n')
                    content.append((sep + usetab).join(s for s in st))
            return head + usetab + (sep + usetab).join(content) + tail

        res = self.content
        if not inline and not head:
            # strip whitespace for omitted non inline node, e.g. CharData in mixed elements
            res = res.strip()
        if density & 1 and res.find('\n') < 0:  # and head[0] == "<":
            # except for XML, add a gap between opening statement and content
            gap = ' ' if not inline and head and head.rstrip()[-1:] != '>' else ''
            return head.rstrip() + gap + data_fn(res) + tail.lstrip()
        else:
            return head + '\n'.join([usetab + data_fn(s) for s in res.split('\n')]) + tail


    def as_sxpr(self, src: str = None,
                indentation: int = 2,
                compact: bool = False) -> str:
        """
        Returns content as S-expression, i.e. in lisp-like form. If this
        method is callad on a RootNode-object,

        Args:
            src:  The source text or `None`. In case the source text is
                given the position of the element in the text will be
                reported as line and column.
            indentation: The number of whitespaces for indentation
            compact:  If True, a compact representation is returned where
                brackets are omitted and only the indentation indicates the
                tree structure.
        """

        left_bracket, right_bracket, density = ('', '', 1) if compact else ('(', '\n)', 0)
        lbreaks = linebreaks(src) if src else []  # type: List[int]
        root = cast(RootNode, self) if isinstance(self, RootNode) else None  # type: Optional[Node]

        def opening(node) -> str:
            """Returns the opening string for the representation of `node`."""
            txt = [left_bracket, node.tag_name]
            # s += " '(pos %i)" % node.add_pos
            # txt.append(str(id(node)))  # for debugging
            if node.attr_active():
                txt.extend(' `(%s "%s")' % (k, v) for k, v in node.attr.items())
            if src:
                line, col = line_col(lbreaks, node.pos)
                txt.append(" `(pos %i %i %i)" % (node.pos, line, col))
            if root and id(node) in root.error_nodes:
                txt.append(" `(err `%s)" % ' '.join(str(err) for err in root.get_errors(node)))
            return "".join(txt) + '\n'

        def closing(node) -> str:
            """Returns the closing string for the representation of `node`."""
            return right_bracket

        def pretty(strg):
            """Encloses `strg` with the right kind of quotation marks."""
            return '"%s"' % strg if strg.find('"') < 0 \
                else "'%s'" % strg if strg.find("'") < 0 \
                else '"%s"' % strg.replace('"', r'\"')

        return self._tree_repr(' ' * indentation, opening, closing, pretty, density=density)


    def as_xml(self, src: str = None,
               indentation: int = 2,
               inline_tags: Set[str] = set(),
               omit_tags: Set[str] = set(),
               empty_tags: Set[str] = set()) -> str:
        """
        Returns content as XML-tree.

        Args:
            src:  The source text or `None`. In case the source text is
                given the position will also be reported as line and
                column.
            indentation: The number of whitespaces for indentation
            inline_tags:  A set of tag names, the content of which will always be written
                on a single line, unless it contains explicit line feeds ('\n').
            omit_tags:  A set of tags from which only the content will be printed, but
                neither the opening tag nor its attr nor the closing tag. This
                allows producing a mix of plain text and child tags in the output,
                which otherwise is not supported by the Node object, because it
                requires its content to be either a tuple of children or string content.
            empty_tags:  A set of tags which shall be rendered as empty elements, e.g.
                "<empty/>" instead of "<empty><empty>".
        """
        root = cast(RootNode, self) if isinstance(self, RootNode) else None  # type: Optional[Node]

        def opening(node) -> str:
            """Returns the opening string for the representation of `node`."""
            if node.tag_name in omit_tags:
                return ''
            txt = ['<', node.tag_name]
            has_reserved_attrs = node.attr_active() \
                and any(r in node.attr for r in {'err', 'line', 'col'})
            if node.attr_active():
                txt.extend(' %s="%s"' % (k, v) for k, v in node.attr.items())
            if src and not has_reserved_attrs:
                txt.append(' line="%i" col="%i"' % line_col(line_breaks, node.pos))
            if root and id(node) in root.error_nodes and not has_reserved_attrs:
                txt.append(' err="%s"' % ''.join(str(err).replace('"', r'\"')
                                                 for err in root.get_errors(node)))
            if node.tag_name in empty_tags:
                assert not node.result, ("Node %s with content %s is not an empty element!" %
                                         (node.tag_name, str(node)))
                ending = "/>\n" if not node.tag_name[0] == '?' else "?>\n"
            else:
                ending = ">\n"
            return "".join(txt + [ending])

        def closing(node):
            """Returns the closing string for the representation of `node`."""
            if node.tag_name in omit_tags or node.tag_name in empty_tags:
                return ''
            return ('\n</') + node.tag_name + '>'

        def sanitizer(content: str) -> str:
            """Substitute "&", "<", ">" in XML-content by the respective entities."""
            content = RX_AMP.sub('&amp;', content)
            content = content.replace('<', '&lt;').replace('>', '&gt;')
            return content


        def inlining(node):
            """Returns True, if `node`'s tag name is contained in `inline_tags`,
            thereby signalling that the children of this node shall not be
            printed on several lines to avoid unwanted gaps in the output.
            """
            return node.tag_name in inline_tags \
                or (node.attr_active()
                    and node.attr.get('xml:space', 'default') == 'preserve')

        line_breaks = linebreaks(src) if src else []
        return self._tree_repr(' ' * indentation, opening, closing, sanitizer,
                               density=1, inline_fn=inlining)


    def select(self, match_function: Callable, include_root: bool = False, reverse: bool = False) \
            -> Iterator['Node']:
        """
        Finds nodes in the tree that fulfill a given criterion.

        `select` is a generator that yields all nodes for which the
        given `match_function` evaluates to True. The tree is
        traversed pre-order.

        See function `Node.select_by_tag` for some examples.

        Args:
            match_function (function): A function  that takes as Node
                object as argument and returns True or False
            include_root (bool): If False, only descendant nodes will be
                checked for a match.
            reverse (bool): If True, the tree will be walked in reverse
                order, i.e. last children first.
        Yields:
            Node: All nodes of the tree for which
            ``match_function(node)`` returns True
        """
        if include_root and match_function(self):
            yield self
        child_iterator = reversed(self.children) if reverse else self.children
        for child in child_iterator:
            for node in child.select(match_function, True, reverse):
                yield node


    def select_by_tag(self, tag_names: Union[str, AbstractSet[str]],
                      include_root: bool = False) -> Iterator['Node']:
        """
        Returns an iterator that runs through all descendants that have one
        of the given tag names.

        Examples::

            >>> tree = parse_sxpr('(a (b "X") (X (c "d")) (e (X "F")))')
            >>> list(flatten_sxpr(item.as_sxpr()) for item in tree.select_by_tag("X", False))
            ['(X (c "d"))', '(X "F")']
            >>> list(flatten_sxpr(item.as_sxpr()) for item in tree.select_by_tag({"X", "b"}, False))
            ['(b "X")', '(X (c "d"))', '(X "F")']
            >>> any(tree.select_by_tag('a', False))
            False
            >>> list(flatten_sxpr(item.as_sxpr()) for item in tree.select_by_tag('a', True))
            ['(a (b "X") (X (c "d")) (e (X "F")))']
            >>> flatten_sxpr(next(tree.select_by_tag("X", False)).as_sxpr())
            '(X (c "d"))'

        Args:
            tag_name(set): A tag name or set of tag names that is being
                searched for
            include_root (bool): If False, only descendant nodes will be
                checked for a match.
        Yields:
            Node: All nodes which have a given tag name.
        """
        if isinstance(tag_names, str):
            tag_names = frozenset({tag_names})
        return self.select(lambda node: node.tag_name in tag_names, include_root)


    def pick(self, tag_names: Union[str, Set[str]]) -> Optional['Node']:
        """
        Picks the first descendant with one of the given tag_names.

        This function is mostly just syntactic sugar for
        ``next(node.select_by_tag(tag_names, False))``. However, rather than
        raising a StopIterationError if no descendant with the given tag-name
        exists, it returns None.
        """
        try:
            return next(self.select_by_tag(tag_names, False))
        except StopIteration:
            return None


    def tree_size(self) -> int:
        """
        Recursively counts the number of nodes in the tree including the root node.
        """
        return sum(child.tree_size() for child in self.children) + 1


def serialize(node: Node, how: str='default') -> str:
    """
    Serializes the tree starting with `node` either as S-expression, XML
    or in compact form. Possible values for `how` are 'S-expression',
    'XML', 'compact' accordingly, or 'AST', 'CST', 'default' in which case
    the value of respective configuration variable determines the
    serialization format. (See module `configuration.py`.)
    """
    switch = how.lower()

    if switch == 'ast':
        switch = get_config_value('ast_serialization').lower()
    elif switch == 'cst':
        switch = get_config_value('cst_serialization').lower()
    elif switch == 'default':
        switch = get_config_value('default_serialization').lower()

    if switch == 's-expression':
        return node.as_sxpr()
    elif switch == 'xml':
        return node.as_xml()
    elif switch == 'compact':
        return node.as_sxpr(compact=True)
    else:
        raise ValueError('Unknown serialization %s, %s' % (how, switch))


class FrozenNode(Node):
    """
    FrozenNode is an immutable kind of Node, i.e. it must not be changed
    after initialization. The purpose is mainly to allow certain kinds of
    optimization, like not having to instantiate empty nodes (because they
    are always the same and will be dropped while parsing, anyway).

    Frozen nodes must be used only temporarily during parsing or
    tree-transformation and should not occur in the product of the
    transformation any more. This can be verified with `tree_sanity_check()`.
    """

    def __init__(self, tag_name: str, result: ResultType) -> None:
        if isinstance(result, str) or isinstance(result, StringView):
            result = str(result)
        else:
            raise TypeError('FrozenNode only accepts string as results. '
                            '(Only leaf-nodes can be frozen nodes.)')
        super(FrozenNode, self).__init__(tag_name, result, True)

    @property
    def result(self) -> StrictResultType:
        return self._result

    @result.setter
    def result(self, result: ResultType):
        raise TypeError('FrozenNode does not allow re-assignment of results.')

    @property
    def attr(self):
        raise AssertionError("Attributes cannot be accessed on a frozen node")

    def with_pos(self, pos: int) -> 'Node':
        pass


PLACEHOLDER = FrozenNode('__PLACEHOLDER__', '')


def tree_sanity_check(tree: Node) -> bool:
    """
    Sanity check for syntax trees: One and the same node must never appear
    twice in the syntax tree. Frozen Nodes (EMTPY_NODE, PLACEHOLDER)
    should only exist temporarily and must have been dropped or eliminated
    before any kind of tree generation (i.e. parsing) or transformation
    is finished.
    :param tree: the root of the tree to be checked
    :return: True, if the tree is `sane`, False otherwise.
    """
    node_set = set()
    for node in tree.select(lambda nd: True, include_root=True):
        if node in node_set or isinstance(Node, FrozenNode):
            return False
        node_set.add(node)
    return True


class RootNode(Node):
    """The root node for the syntax tree is a special kind of node that keeps
    and manages global properties of the tree as a whole. These are first and
    foremost the list off errors that occurred during tree generation
    (i.e. parsing) or any transformation of the tree. Other properties concern
    the customization of the XML-serialization.

    The root node can be instantiated before the tree is fully parsed. This is
    necessary, because the root node is needed for managing error messages
    during the parsing process, already. In order to connect the root node to
    the tree, when parsing is finished, the swallow()-method must be called.

        errors (list):  A list of all errors that have occurred so far during
                processing (i.e. parsing, AST-transformation, compiling)
                of this tree.

        error_flag (int):  the highest warning or error level of all errors
                that occurred.

        inline_tags (set of strings): see `Node.as_xml()` for an explanation.

        omit_tags (set of strings): see `Node.as_xml()` for an explanation.

        empty_tags (set oif strings): see `Node.as_xml()` for an explanation.
    """

    def __init__(self, node: Optional[Node] = None):
        super().__init__('__not_yet_ready__', '')
        self.errors = []           # type: List[Error]
        self.error_nodes = dict()      # type: Dict[int, List[Error]]  # id(node) -> error list
        self.error_positions = dict()  # type: Dict[int, Set[int]]  # pos -> set of id(node)
        self.error_flag = 0
        if node is not None:
            self.swallow(node)
        # customization for XML-Representation
        self.inline_tags = set()  # type: Set[str]
        self.omit_tags = set()  # type: Set[str]
        self.empty_tags = set()  # type: Set[str]

    def __deepcopy__(self, memodict={}):
        duplicate = self.__class__(None)
        if self.children:
            duplicate.children = copy.deepcopy(self.children)
            duplicate._result = duplicate.children
        else:
            duplicate.children = NoChildren
            duplicate._result = self._result
        duplicate._pos = self._pos
        duplicate._len = self._len
        if self.attr_active():
            duplicate.attr.update(copy.deepcopy(self._xml_attr))
            # duplicate._xml_attr = copy.deepcopy(self._xml_attr)  # this is blocked by cython
        duplicate.errors = copy.copy(self.errors)
        duplicate.error_nodes = copy.copy(self.error_nodes)
        duplicate.error_positions = copy.deepcopy(self.error_positions)
        duplicate.error_flag = self.error_flag
        duplicate.inline_tags = self.inline_tags
        duplicate.omit_tags = self.omit_tags
        duplicate.empty_tags = self.empty_tags
        duplicate.tag_name = self.tag_name
        return duplicate


    def swallow(self, node: Node) -> 'RootNode':
        """
        Put `self` in the place of `node` by copying all its data.
        Returns self.

        This is done by the parse.Grammar object after
        parsing has finished, so that the Grammar object always
        returns a syntax tree rooted in a RootNode object.

        It is possible to add errors to a RootNode object, before it
        has actually swallowed the root of the syntax tree.
        """
        self._result = node._result
        self.children = node.children
        self._len = node._len
        self._pos = node._pos
        self.tag_name = node.tag_name
        if node.attr_active():
            self._xml_attr = node._xml_attr
        self._content = node._content
        if id(node) in self.error_nodes:
            self.error_nodes[id(self)] = self.error_nodes[id(node)]
        return self

    def add_error(self, node: Node, error: Error) -> 'RootNode':
        """
        Adds an Error object to the tree, locating it at a specific node.
        """
        assert node.pos == error.pos or isinstance(node, FrozenNode)
        self.errors.append(error)
        self.error_flag = max(self.error_flag, error.code)
        self.error_nodes.setdefault(id(node), []).append(error)
        self.error_positions.setdefault(error.pos, set()).add(id(node))
        return self

    def new_error(self,
                  node: Node,
                  message: str,
                  code: ErrorCode = Error.ERROR) -> 'RootNode':
        """
        Adds an error to this tree, locating it at a specific node.
        Parameters:
            pos(int):     The position of the error in the source text
            message(str): A string with the error message.abs
            code(int):    An error code to identify the kind of error
        """
        error = Error(message, node.pos, code)
        self.add_error(node, error)
        return self

    def get_errors(self, node: Node) -> List[Error]:
        """
        Returns the List of errors that occurred on the node or any child node
        at the same position that has already been removed from the tree,
        for example, because it was an anonymous empty child node.
        """
        node_id = id(node)           # type: int
        errors = []                  # type: List[Error]
        for nid in self.error_positions.get(node.pos, frozenset()):
            if nid == node_id:
                errors.extend(self.error_nodes[nid])
            else:
                for nd in node.select(lambda n: id(n) == nid):
                    break
                else:
                    # node is not connected to tree any more => display its errors on its parent
                    errors.extend(self.error_nodes[nid])
        return errors

    @property
    def errors_sorted(self) -> List[Error]:
        """
        Returns the list of errors, ordered bv their position.
        """
        self.errors.sort(key=lambda e: e.pos)
        return self.errors

    def customized_XML(self):
        """
        Returns a customized XML representation of the tree.
        See the docstring of `Node.as_xml()` for an explanation of the
        customizations.
        """
        return self.as_xml(inline_tags=self.inline_tags,
                           omit_tags=self.omit_tags,
                           empty_tags=self.empty_tags)


#######################################################################
#
# S-expression- and XML-parsers
#
#######################################################################


def parse_sxpr(sxpr: Union[str, StringView]) -> Node:
    """
    Generates a tree of nodes from an S-expression.

    This can - among other things - be used for deserialization of trees that
    have been serialized with `Node.as_sxpr()` or as a convenient way to
    generate test data.

    Example:
    >>> parse_sxpr("(a (b c))").as_sxpr()
    '(a\\n  (b\\n    "c"\\n  )\\n)'
    """

    sxpr = StringView(sxpr).strip() if isinstance(sxpr, str) else sxpr.strip()
    # mock_parsers = dict()  # type: Dict[StringView, MockParser]

    def next_block(s: StringView):
        """Generator that yields all characters until the next closing bracket
        that does not match an opening bracket matched earlier within the same
        package.
        """
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

    def inner_parser(sxpr: StringView) -> Node:
        if sxpr[0] != '(':
            raise ValueError('"(" expected, not ' + sxpr[:10])
        # assert sxpr[0] == '(', sxpr
        sxpr = sxpr[1:].strip()
        match = sxpr.match(re.compile(r'[\w:]+'))
        if match is None:
            raise AssertionError('Malformed S-expression Node-tagname or identifier expected, '
                                 'not "%s"' % sxpr[:40].replace('\n', ''))
        end = sxpr.index(match.end())
        tagname = sxpr[:end]
        name, class_name = (tagname.split(':') + [''])[:2]
        sxpr = sxpr[end:].strip()
        attributes = OrderedDict()  # type: OrderedDict[str, str]
        if sxpr[0] == '(':
            result = tuple(inner_parser(block) for block in next_block(sxpr))  # type: ResultType
        else:
            lines = []
            while sxpr and sxpr[0:1] != ')':
                # parse attr
                while sxpr[:2] == "`(":
                    i = sxpr.find('"')
                    k = sxpr.find(')')
                    # read very special attribute pos
                    if sxpr[2:5] == "pos" and 0 < i < k:
                        # pos = int(sxpr[5:k].strip().split(' ')[0])
                        pass
                    # ignore very special attribute err
                    elif sxpr[2:5] == "err" and 0 <= sxpr.find('`', 5) < k:
                        m = sxpr.find('(', 5)
                        while 0 <= m < k:
                            m = sxpr.find('(', k)
                            k = max(k, sxpr.find(')', max(m, 0)))
                    # read attr
                    else:
                        attr = sxpr[2:i].strip()
                        value = sxpr[i:k].strip()[1:-1]
                        attributes[attr] = value
                    sxpr = sxpr[k + 1:].strip()
                # parse content
                for qtmark in ['"""', "'''", '"', "'"]:
                    match = sxpr.match(re.compile(qtmark + r'.*?' + qtmark, re.DOTALL))
                    if match:
                        end = sxpr.index(match.end())
                        i = len(qtmark)
                        lines.append(str(sxpr[i:end - i]))
                        sxpr = sxpr[end:].strip()
                        break
                else:
                    match = sxpr.match(re.compile(r'(?:(?!\)).)*', re.DOTALL))
                    end = sxpr.index(match.end())
                    lines.append(str(sxpr[:end]))
                    sxpr = sxpr[end:]
            result = "\n".join(lines)
        node = Node(name or ':' + class_name, result)
        if attributes:
            node.attr.update(attributes)
        return node

    return inner_parser(StringView(sxpr) if isinstance(sxpr, str) else sxpr)


RX_WHITESPACE_TAIL = re.compile(r'\s*$')


def parse_xml(xml: Union[str, StringView]) -> Node:
    """
    Generates a tree of nodes from a (Pseudo-)XML-source.
    """

    xml = StringView(str(xml))
    # PlainText = MockParser('', TOKEN_PTYPE)
    # mock_parsers = {TOKEN_PTYPE: PlainText}

    def parse_attributes(s: StringView) -> Tuple[StringView, OrderedDict]:
        """
        Parses a sqeuence of XML-Attributes. Returns the string-slice
        beginning after the end of the attr.
        """
        attributes = OrderedDict()  # type: OrderedDict[str, str]
        restart = 0
        for match in s.finditer(re.compile(r'\s*(?P<attr>\w+)\s*=\s*"(?P<value>.*)"\s*')):
            d = match.groupdict()
            attributes[d['attr']] = d['value']
            restart = s.index(match.end())
        return (s[restart:], attributes)

    def parse_opening_tag(s: StringView) -> Tuple[StringView, str, OrderedDict, bool]:
        """
        Parses an opening tag. Returns the string segment following the
        the opening tag, the tag name, a dictionary of attr and
        a flag indicating whether the tag is actually a solitary tag as
        indicated by a slash at the end, i.e. <br/>.
        """
        match = s.match(re.compile(r'<\s*(?P<tagname>[\w:]+)\s*'))
        assert match
        tagname = match.groupdict()['tagname']
        section = s[s.index(match.end()):]
        s, attributes = parse_attributes(section)
        i = s.find('>')
        assert i >= 0
        return s[i + 1:], tagname, attributes, s[i - 1] == "/"

    def parse_closing_tag(s: StringView) -> Tuple[StringView, str]:
        """
        Parses a closing tag and returns the string segment, just after
        the closing tag.
        """
        match = s.match(re.compile(r'</\s*(?P<tagname>[\w:]+)>'))
        assert match
        tagname = match.groupdict()['tagname']
        return s[s.index(match.end()):], tagname

    def parse_leaf_content(s: StringView) -> Tuple[StringView, StringView]:
        """
        Parses a piece of the content of a tag, just until the next opening,
        closing or solitary tag is reached.
        """
        i = 0
        while s[i] != "<" or s[max(0, i - 1)] == "\\":
            i = s.find("<", i)
        return s[i:], s[:i]

    def parse_full_content(s: StringView) -> Tuple[StringView, Node]:
        """
        Parses the full content of a tag, starting right at the beginning
        of the opening tag and ending right after the closing tag.
        """
        res = []  # type: List[Node]
        s, tagname, _, solitary = parse_opening_tag(s)
        name, class_name = (tagname.split(":") + [''])[:2]
        if not solitary:
            while s and not s[:2] == "</":
                s, leaf = parse_leaf_content(s)
                if leaf and (leaf.find('\n') < 0 or not leaf.match(RX_WHITESPACE_TAIL)):
                    res.append(Node(TOKEN_PTYPE, leaf))
                if s[:1] == "<" and s[:2] != "</":
                    s, child = parse_full_content(s)
                    res.append(child)
            s, closing_tagname = parse_closing_tag(s)
            assert tagname == closing_tagname
        if len(res) == 1 and res[0].tag_name == TOKEN_PTYPE:
            result = res[0].result
        else:
            result = tuple(res)
        return s, Node(name or ':' + class_name, result)

    match_header = xml.search(re.compile(r'<(?!\?)'))
    start = xml.index(match_header.start()) if match_header else 0
    _, tree = parse_full_content(xml[start:])
    assert _.match(RX_WHITESPACE_TAIL)
    return tree


def parse_tree(xml_or_sxpr: str) -> Optional[Node]:
    """
    Parses either XML or S-expressions. Which of these is detected automatically.
    """
    if re.match('\s*<', xml_or_sxpr):
        return parse_xml(xml_or_sxpr)
    elif re.match('\s*\(', xml_or_sxpr):
        return parse_sxpr(xml_or_sxpr)
    elif re.match('\s*', xml_or_sxpr):
        return None
    else:
        m = re.match('\s*(.*)\n?', xml_or_sxpr)
        snippet = m.group(1) if m else ''
        raise ValueError('Snippet seems to be neither S-expression nor XML: ' + snippet + ' ...')

# if __name__ == "__main__":
#     st = parse_sxpr("(alpha (beta (gamma i\nj\nk) (delta y)) (epsilon z))")
#     print(st.as_sxpr())
#     print(st.as_xml())
