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

import os
import re

from DHParser.preprocess import strip_tokens, with_source_mapping, PreprocessorFunc
from DHParser.syntaxtree import Node, RootNode, StrictResultType
from DHParser.transform import TransformationFunc
from DHParser.parse import Grammar
from DHParser.error import adjust_error_locations, is_error, Error
from DHParser.log import log_parsing_history, log_ST, is_logging, logfile_basename
from DHParser.toolkit import typing, sane_parser_name, load_if_file
from typing import Any, Optional, Tuple, List, Callable


__all__ = ('CompilerError', 'Compiler', 'compile_source')


class CompilerError(Exception):
    """Exception raised when an error of the compiler itself is detected.
    Compiler errors are not to be confused with errors in the source
    code to be compiled, which do not raise Exceptions but are merely
    reported as an error."""
    pass


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
        grammar_name:  The name of the grammar this compiler is related to
        grammar_source:  The source code of the grammar this compiler is
                related to.
        _dirty_flag:  A flag indicating that the compiler has already been
                called at least once and that therefore all compilation
                variables must be reset when it is called again.
    """

    def __init__(self, grammar_name="", grammar_source=""):
        self.set_grammar_name(grammar_name, grammar_source)
        self._reset()

    def _reset(self):
        self.tree = None   # type: Optional[RootNode]
        self.context = []  # type: List[Node]
        self._dirty_flag = False

    def __call__(self, root: RootNode) -> Any:
        """
        Compiles the abstract syntax tree with the root node `node` and
        returns the compiled code. It is up to subclasses implementing
        the compiler to determine the format of the returned data.
        (This very much depends on the kind and purpose of the
        implemented compiler.)
        """
        if self._dirty_flag:
            self._reset()
        self._dirty_flag = True
        self.tree = root
        result = self.compile(root)
        return result

    def set_grammar_name(self, grammar_name: str="", grammar_source: str=""):
        """
        Changes the grammar's name and the grammar's source.

        The grammar name and the source text of the grammar are
        metadata about the grammar that do not affect the compilation
        process. Classes inheriting from `Compiler` can use this
        information to name and annotate its output. Returns `self`.
        """
        assert grammar_name == "" or re.match(r'\w+\Z', grammar_name)
        if not grammar_name and re.fullmatch(r'[\w/:\\]+', grammar_source):
            grammar_name = os.path.splitext(os.path.basename(grammar_source))[0]
        self.grammar_name = grammar_name
        self.grammar_source = load_if_file(grammar_source)
        return self

    # @staticmethod
    # def propagate_error_flags(node: Node, lazy: bool = True) -> None:
    #     # See test_parser.TestCompilerClass.test_propagate_error()..
    #     """Propagates error flags from children to parent nodes to make sure
    #     that the parent's error flag is always greater or equal the maximum
    #     of the children's error flags."""
    #     if not lazy or node.error_flag < Error.HIGHEST:
    #         for child in node.children:
    #             Compiler.propagate_error_flags(child)
    #             node.error_flag = max(node.error_flag, child.error_flag)
    #             if lazy and node.error_flag >= Error.HIGHEST:
    #                 return

    @staticmethod
    def method_name(node_name: str) -> str:
        """
        Returns the method name for `node_name`, e.g.::

            >>> Compiler.method_name('expression')
            'on_expression'
        """
        assert re.match(r'\w+$', node_name)
        return 'on_' + node_name

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
        elem = node.parser.name or node.parser.ptype[1:]
        if not sane_parser_name(elem):
            node.add_error("Reserved name '%s' not allowed as parser "
                           "name! " % elem + "(Any name starting with "
                           "'_' or '__' or ending with '__' is reserved.)")
            return None
        else:
            try:
                compiler = self.__getattribute__(self.method_name(elem))
            except AttributeError:
                compiler = self.fallback_compiler
            self.context.append(node)
            result = compiler(node)
            self.context.pop()
            if result is None:
                raise CompilerError('Method on_%s returned `None` instead of a '
                                    'valid compilation result!' % elem)
            # # the following statement makes sure that the error_flag
            # # is propagated early on. Otherwise it is redundant, because
            # # the __call__ method globally propagates the node's error_flag
            # # later anyway. So, maybe it could be removed here.
            # for child in node.children:
            #     node.error_flag = node.error_flag or child.error_flag
            return result


def compile_source(source: str,
                   preprocessor: Optional[PreprocessorFunc],  # str -> str
                   parser: Grammar,  # str -> Node (concrete syntax tree (CST))
                   transformer: TransformationFunc,  # Node -> Node (abstract syntax tree (AST))
                   compiler: Compiler) -> Tuple[Any, List[Error], Node]:  # Node (AST) -> Any
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

    Returns (tuple):
        The result of the compilation as a 3-tuple
        (result, errors, abstract syntax tree). In detail:
        1. The result as returned by the compiler or ``None`` in case of failure
        2. A list of error or warning messages
        3. The root-node of the abstract syntax tree
    """
    original_text = load_if_file(source)
    log_file_name = logfile_basename(source, compiler)
    if preprocessor is None:
        source_text = original_text
        source_mapping = lambda i: i
    else:
        source_text, source_mapping = with_source_mapping(preprocessor(original_text))
    syntax_tree = parser(source_text)
    if is_logging():
        log_ST(syntax_tree, log_file_name + '.cst')
        log_parsing_history(parser, log_file_name)

    assert is_error(syntax_tree.error_flag) or str(syntax_tree) == strip_tokens(source_text)
    # only compile if there were no syntax errors, for otherwise it is
    # likely that error list gets littered with compile error messages
    result = None
    # efl = syntax_tree.error_flag
    # messages = syntax_tree.collect_errors(clear_errors=True)
    if not is_error(syntax_tree.error_flag):
        transformer(syntax_tree)
        # efl = max(efl, syntax_tree.error_flag)
        # messages.extend(syntax_tree.collect_errors(clear_errors=True))
        if is_logging():
            log_ST(syntax_tree, log_file_name + '.ast')
        if not is_error(syntax_tree.error_flag):
            result = compiler(syntax_tree)
        # print(syntax_tree.as_sxpr())
        # messages.extend(syntax_tree.collect_errors())
        # syntax_tree.error_flag = max(syntax_tree.error_flag, efl)

    messages = syntax_tree.collect_errors()
    adjust_error_locations(messages, original_text, source_mapping)
    return result, messages, syntax_tree
