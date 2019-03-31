# compile.py - Syntax driven compilation support for DHParser
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
Module ``compile`` contains a skeleton class for syntax
driven compilation support. Class ``Compiler`` can serve as base
class for a compiler. Compiler objects
are callable an receive the Abstract syntax tree (AST)
as argument and yield whatever output the compiler produces. In
most Digital Humanities applications this will be
XML-code. However, it can also be anything else, like binary
code or, as in the case of DHParser's EBNF-compiler, Python
source code.

Function ``compile_source`` invokes all stages of the compilation
process, i.e. pre-processing, parsing, CST to AST-transformation
and compilation.

See module ``ebnf`` for a sample of the implementation of a
compiler object.
"""

import copy
from typing import Any, Optional, Tuple, List

from DHParser.preprocess import with_source_mapping, PreprocessorFunc, SourceMapFunc
from DHParser.syntaxtree import Node, RootNode, ZOMBIE_TAG, StrictResultType
from DHParser.transform import TransformationFunc
from DHParser.parse import Grammar
from DHParser.error import adjust_error_locations, is_error, Error
from DHParser.log import log_parsing_history, log_ST, is_logging, logfile_basename
from DHParser.toolkit import load_if_file


__all__ = ('CompilerError', 'Compiler', 'compile_source', 'visitor_name')


class CompilerError(Exception):
    """
    Exception raised when an error of the compiler itself is detected.
    Compiler errors are not to be confused with errors in the source
    code to be compiled, which do not raise Exceptions but are merely
    reported as an error.
    """
    pass


def visitor_name(node_name: str) -> str:
    """
    Returns the method name for `node_name`, e.g.::

        >>> visitor_name('expression')
        'on_expression'
    """
    # assert re.match(r'\w+$', node_name)
    return 'on_' + node_name


ROOTNODE_PLACEHOLDER = RootNode()


class Compiler:
    """
    Class Compiler is the abstract base class for compilers. Compiler
    objects are callable and take the root node of the abstract
    syntax tree (AST) as argument and return the compiled code in a
    format chosen by the compiler itself.

    Subclasses implementing a compiler must define `on_XXX()`-methods
    for each node name that can occur in the AST where 'XXX' is the
    node's name(for unnamed nodes it is the node's ptype without the
    leading colon ':').

    These compiler methods take the node on which they are run as
    argument. Other than in the AST transformation, which runs depth-first,
    compiler methods are called forward moving starting with the root
    node, and they are responsible for compiling the child nodes
    themselves. This should be done by invoking the `compile(node)`-
    method which will pick the right `on_XXX`-method. It is not
    recommended to call the `on_XXX`-methods directly.

    Attributes:
        context:  A list of parent nodes that ends with the currently
                compiled node.
        tree:  The root of the abstract syntax tree.
        source:  The source code.

        _dirty_flag:  A flag indicating that the compiler has already been
                called at least once and that therefore all compilation
                variables must be reset when it is called again.
    """

    def __init__(self):
        self._reset()

    def _reset(self):
        self.source = ''
        self.tree = ROOTNODE_PLACEHOLDER   # type: RootNode
        self.context = []  # type: List[Node]
        self._None_check = True  # type: bool
        self._dirty_flag = False

    def __call__(self, root: RootNode, source: str = '') -> Any:
        """
        Compiles the abstract syntax tree with the root node `node` and
        returns the compiled code. It is up to subclasses implementing
        the compiler to determine the format of the returned data.
        (This very much depends on the kind and purpose of the
        implemented compiler.)
        """
        assert root.tag_name != ZOMBIE_TAG
        if self._dirty_flag:
            self._reset()
        self._dirty_flag = True
        self.tree = root  # type: RootNode
        self.source = source  # type: str
        result = self.compile(root)
        return result

    def compile_children(self, node: Node) -> StrictResultType:
        """Compiles all children of the given node and returns the tuple
        of the compiled children or the node's (potentially empty) result
        in case the node does not have any children.
        """
        if node.children:
            return tuple(self.compile(child) for child in node.children)
        else:
            return node.result

    def fallback_compiler(self, node: Node) -> Any:
        """This is a generic compiler function which will be called on
        all those node types for which no compiler method `on_XXX` has
        been defined."""
        if node.children:
            result = tuple(self.compile(nd) for nd in node.children)
            node.result = result
        return node

    def compile(self, node: Node) -> Any:
        """
        Calls the compilation method for the given node and returns the
        result of the compilation.

        The method's name is derived from either the node's parser
        name or, if the parser is anonymous, the node's parser's class
        name by adding the prefix ``on_``.

        Note that ``compile`` does not call any compilation functions
        for the parsers of the sub nodes by itself. Rather, this should
        be done within the compilation methods.
        """
        elem = node.tag_name
        if elem.startswith(':'):
            elem = elem[1:]
        try:
            compiler = self.__getattribute__(visitor_name(elem))
        except AttributeError:
            compiler = self.fallback_compiler
        self.context.append(node)
        result = compiler(node)
        self.context.pop()
        if result is None and self._None_check:
            raise CompilerError('Method on_%s returned `None` instead of a valid compilation '
                                'compilation result! Turn this check of by adding '
                                '"self._None_check = False" to the _reset()-Method of your'
                                'compiler class, in case on_%s actually SHOULD return None.'
                                % (elem, elem))
        return result


def compile_source(source: str,
                   preprocessor: Optional[PreprocessorFunc],  # str -> str
                   parser: Grammar,  # str -> Node (concrete syntax tree (CST))
                   transformer: TransformationFunc,  # Node (CST) -> Node (abstract ST (AST))
                   compiler: Compiler,  # Node (AST) -> Any
                   preserve_ast: bool = False) -> Tuple[Optional[Any], List[Error], Optional[Node]]:
    """
    Compiles a source in four stages:
    1. Pre-Processing (if needed)
    2. Parsing
    3. AST-transformation
    4. Compiling.

    The compilations stage is only invoked if no errors occurred in
    either of the two previous stages.

    Args:
        source (str): The input text for compilation or a the name of a
            file containing the input text.
        preprocessor (function):  text -> text. A preprocessor function
            or None, if no preprocessor is needed.
        parser (function):  A parsing function or grammar class
        transformer (function):  A transformation function that takes
            the root-node of the concrete syntax tree as an argument and
            transforms it (in place) into an abstract syntax tree.
        compiler (function): A compiler function or compiler class
            instance
        preserve_ast (bool): Preserves the AST-tree.

    Returns (tuple):
        The result of the compilation as a 3-tuple
        (result, errors, abstract syntax tree). In detail:
        1. The result as returned by the compiler or ``None`` in case of failure
        2. A list of error or warning messages
        3. The root-node of the abstract syntax tree if `preserve_ast` is True
           or `None` otherwise.
    """
    ast = None  # type: Optional[Node]
    original_text = load_if_file(source)  # type: str
    log_file_name = logfile_basename(source, compiler)  # type: str
    if preprocessor is None:
        source_text = original_text  # type: str
        source_mapping = lambda i: i  # type: SourceMapFunc
    else:
        source_text, source_mapping = with_source_mapping(preprocessor(original_text))
    syntax_tree = parser(source_text)  # type: RootNode
    if is_logging():
        log_ST(syntax_tree, log_file_name + '.cst')
        log_parsing_history(parser, log_file_name)

    # assert is_error(syntax_tree.error_flag) or str(syntax_tree) == strip_tokens(source_text), \
    #     str(syntax_tree) # Ony valid if neither tokens or whitespace are dropped early

    # only compile if there were no syntax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    result = None
    # efl = syntax_tree.error_flag
    # messages = syntax_tree.errors(clear_errors=True)
    if not is_error(syntax_tree.error_flag):
        transformer(syntax_tree)
        # efl = max(efl, syntax_tree.error_flag)
        # messages.extend(syntax_tree.errors(clear_errors=True))
        if is_logging():
            log_ST(syntax_tree, log_file_name + '.ast')
        if not is_error(syntax_tree.error_flag):
            if preserve_ast:
                ast = copy.deepcopy(syntax_tree)
            result = compiler(syntax_tree, original_text)
        # print(syntax_tree.as_sxpr())
        # messages.extend(syntax_tree.errors())
        # syntax_tree.error_flag = max(syntax_tree.error_flag, efl)

    messages = syntax_tree.errors_sorted  # type: List[Error]
    adjust_error_locations(messages, original_text, source_mapping)
    return result, messages, ast


# TODO: Verify compiler against grammar, i.e. make sure that for all on_X()-methods, `X` is the name of a parser
