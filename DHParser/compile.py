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
import functools
import os
import traceback
from typing import Any, Optional, Tuple, List, Set, Union, Callable, cast

from DHParser.configuration import get_config_value
from DHParser.preprocess import with_source_mapping, PreprocessorFunc, SourceMapFunc
from DHParser.syntaxtree import Node, RootNode
from DHParser.transform import TransformationFunc
from DHParser.parse import Grammar
from DHParser.error import adjust_error_locations, is_error, is_fatal, Error, \
    TREE_PROCESSING_CRASH, COMPILER_CRASH, AST_TRANSFORM_CRASH
from DHParser.log import log_parsing_history, log_ST, is_logging
from DHParser.toolkit import load_if_file, is_filename


__all__ = ('CompilerError',
           'Compiler',
           'GrammarCallable',
           'CompilerCallable',
           'ResultTuple',
           'compile_source',
           'visitor_name',
           'TreeProcessor',
           'process_tree')


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
        finalizers:  A stack of tuples (function, parameters) that will be
                called in reverse order after compilation.

        _dirty_flag:  A flag indicating that the compiler has already been
                called at least once and that therefore all compilation
                variables must be reset when it is called again.
        _debug: A flag indicating that debugging is turned on the value
                for this flag is read before each call of the configuration
                (see debugging section in DHParser.configuration)
                If debugging is turned on the compiler class raises en
                error if a node is attempted to be compiled twice.
        _debug_already_compiled: A set of nodes that have already been compiled.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        # self.source = ''
        self.tree = ROOTNODE_PLACEHOLDER   # type: RootNode
        self.context = []  # type: List[Node]
        self._None_check = True  # type: bool
        self._dirty_flag = False
        self._debug = get_config_value('debug_compiler')  # type: bool
        self._debug_already_compiled = set()              # type: Set[Node]
        self.finalizers = []  # type: List[Tuple[Callable, Tuple]]

    def prepare(self) -> None:
        """
        A preparation method that will be called after everything else has
        been initialized and immediately before compilation starts. This method
        can be overwritten in order to implement preparation tasks.
        """
        pass

    def finalize(self) -> None:
        """
        A finalization method that is called after compilation has finished and
        after all tasks from the finalizers stack have been executed
        """
        pass

    def __call__(self, root: RootNode) -> Any:
        """
        Compiles the abstract syntax tree with the root node `node` and
        returns the compiled code. It is up to subclasses implementing
        the compiler to determine the format of the returned data.
        (This very much depends on the kind and purpose of the
        implemented compiler.)
        """
        if self._dirty_flag:
            self.reset()
        self._dirty_flag = True
        self.tree = root
        # self.source = source  # type: str
        self.prepare()
        result = self.compile(root)
        while self.finalizers:
            task, parameters = self.finalizers.pop()
            task(*parameters)
        self.finalize()
        return result

    def fallback_compiler(self, node: Node) -> Any:
        """This is a generic compiler function which will be called on
        all those node types for which no compiler method `on_XXX` has
        been defined."""
        result = []
        if node.children:
            for child in node.children:
                nd = self.compile(child)
                if not isinstance(nd, Node):
                    tn = node.tag_name
                    raise TypeError(
                        'Fallback compiler for Node `%s` received a value of type '
                        '`%s` from child `%s` instead of the required return type `Node`. '
                        'Override `DHParser.compile.Compiler.fallback_compiler()` or add '
                        'method `on_%s(self, node)` in class `%s` to avoid this error!'
                        % (tn, str(type(nd)), child.tag_name, tn, self.__class__.__name__))
                result.append(nd)
            node.result = tuple(result)
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
        if self._debug:
            assert node not in self._debug_already_compiled
            self._debug_already_compiled.add(node)

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
                                '"self._None_check = False" to the reset()-Method of your'
                                'compiler class, in case on_%s actually SHOULD return None.'
                                % (elem, elem))
        return result


def logfile_basename(filename_or_text, function_or_class_or_instance) -> str:
    """Generates a reasonable logfile-name (without extension) based on
    the given information.
    """
    if is_filename(filename_or_text):
        return os.path.basename(os.path.splitext(filename_or_text)[0])
    else:
        try:
            name = function_or_class_or_instance.__qualname__
        except AttributeError:
            name = function_or_class_or_instance.__class__.__name__
        i = name.find('.')
        return name[:i] + '_out' if i >= 0 else name


GrammarCallable = Union[Grammar, Callable[[str], RootNode], functools.partial]
CompilerCallable = Union[Compiler, Callable[[Node], Any], functools.partial]
ResultTuple = Tuple[Optional[Any], List[Error], Optional[Node]]


def filter_stacktrace(stacktrace: List[str]) -> List[str]:
    """Removes those frames from a formatted stacktrace that are located
    within the DHParser-code."""
    for n, frame in enumerate(stacktrace):
        i = frame.find('"')
        k = frame.find('"', i + 1)
        if frame.find("DHParser", i, k) < 0:
            break
    return stacktrace[n:]


def compile_source(source: str,
                   preprocessor: Optional[PreprocessorFunc],  # str -> str
                   parser: GrammarCallable,  # str -> Node (concrete syntax tree (CST))
                   transformer: TransformationFunc,  # Node (CST) -> Node (abstract ST (AST))
                   compiler: CompilerCallable,  # Node (AST), Source -> Any
                   preserve_AST: bool = False) -> Tuple[Optional[Any], List[Error], Optional[Node]]:
    """Compiles a source in four stages:

    1. Pre-Processing (if needed)
    2. Parsing
    3. AST-transformation
    4. Compiling.

    The later stages AST-transformation, compilation will only be invoked if
    no fatal errors occurred in any of the earlier stages of the processing
    pipeline.

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
        preserve_AST (bool): Preserves the AST-tree.

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
    log_file_name = logfile_basename(source, compiler) if is_logging() else ''  # type: str
    log_syntax_trees = get_config_value('log_syntax_trees')

    # preprocessing

    if preprocessor is None:
        source_text = original_text  # type: str
        source_mapping = lambda i: i  # type: SourceMapFunc
    else:
        source_text, source_mapping = with_source_mapping(preprocessor(original_text))

    # parsing

    syntax_tree = parser(source_text)  # type: RootNode
    if 'cst' in log_syntax_trees:
        log_ST(syntax_tree, log_file_name + '.cst')
    if get_config_value('history_tracking'):
        log_parsing_history(parser, log_file_name)

    # assert is_error(syntax_tree.error_flag) or str(syntax_tree) == strip_tokens(source_text), \
    #     str(syntax_tree) # Ony valid if neither tokens or whitespace are dropped early

    result = None
    if not is_fatal(syntax_tree.error_flag):

        # AST-transformation

        if is_error(syntax_tree.error_flag):
            # catch Python exception, because if an error has occured
            # earlier, the syntax tree might not look like expected,
            # which could (fatally) break AST transformations.
            try:
                transformer(syntax_tree)
            except Exception as e:
                syntax_tree.new_error(syntax_tree,
                                      "AST-Transformation failed due to earlier parser errors. "
                                      "Crash Message: %s: %s" % (e.__class__.__name__, str(e)),
                                      AST_TRANSFORM_CRASH)
        else:
            transformer(syntax_tree)

        if 'ast' in log_syntax_trees:
            log_ST(syntax_tree, log_file_name + '.ast')

        if not is_fatal(syntax_tree.error_flag):
            if preserve_AST:
                ast = copy.deepcopy(syntax_tree)

            # Compilation

            if is_error(syntax_tree.error_flag):
                # assume Python crashes are merely a consequence of earlier
                # errors, so let's catch them
                try:
                    result = compiler(syntax_tree)
                except Exception as e:
                    # raise e
                    node = syntax_tree  # type: Node
                    if isinstance(compiler, Compiler) and compiler.context:
                        node = compiler.context[-1]
                    st = traceback.format_list(traceback.extract_tb(e.__traceback__))
                    trace = ''.join(filter_stacktrace(st))
                    syntax_tree.new_error(
                        node, "Compilation failed, most likely, due to errors earlier "
                              "in the processing pipeline. Crash Message: %s: %s\n%s"
                              % (e.__class__.__name__, str(e), trace),
                        COMPILER_CRASH)
            else:
                # assume Python crashes are programming mistakes, so let
                # the exceptions through
                result = compiler(syntax_tree)

    messages = syntax_tree.errors_sorted  # type: List[Error]
    adjust_error_locations(messages, original_text, source_mapping)
    return result, messages, ast


class TreeProcessor(Compiler):
    """A special kind of Compiler class that take a tree as input (just like
    `Compiler`) but always yields a tree as result.

    The intended use case for TreeProcessor are digital-humanities-applications
    where domain specific languages often describe data structures that, again,
    most of the times are tree structures that can be serialized as XML or HTML.
    Typically, these tree structures pass through several processing stages in
    sequence that - as long as no fatal errors occur on the way - end with
    HTML-preview or a preprint-XML.

    The tree-processors can most suitably be invoked with the `process-tree()`-
    functions which makes sure that a tree-processor is only invoked if no
    fatal errors have occurred in any of the earlier stages.
    """
    def __call__(self, root: RootNode) -> RootNode:
        result = super().__call__(root)
        assert isinstance(result, RootNode)
        return cast(RootNode, result)


def process_tree(tp: TreeProcessor, tree: RootNode) -> RootNode:
    """Process a tree with the tree-processor `tp` only if no fatal error
    has occurred so far. Catch any Python exceptions in case
    any normal errors have occurred earlier in the processing pipeline.
    Don't catch Python-exceptions if no errors have occurred earlier.

    This behaviour is based on the assumption that given any non-fatal
    errors have occurred earlier, the tree passed through the pipeline
    might not be in a state that is expected by the later stages, thus if
    an exception occurs it is not really to be considered a programming
    error. Processing stages should be written with possible errors
    occurring in earlier stages in mind, though. However, because it could
    be difficult to provide for all possible kinds of badly structured
    trees resulting from errors, exceptions occurring on code processing
    potentially faulty trees will be dealt with gracefully.

    Although process_tree returns the root-node of the processed tree,
    tree processing should generally be assumed to change the tree
    in place, even if a different root-node is returned than was passed
    to the tree. If the input tree shall be prserved, it is necessary to
    make a deep copy of the input tree, before calling process_tree.
    """
    assert isinstance(tp, TreeProcessor)
    if not is_fatal(tree.error_flag):
        if is_error(tree.error_flag):
            # assume Python crashes are merely a consequence of earlier
            # errors, so let's catch them
            try:
                tree = tp(tree)
            except Exception as e:
                node = tp.context[-1] if tp.context else tree
                st = traceback.format_list(traceback.extract_tb(e.__traceback__))
                trace = ''.join(filter_stacktrace(st))
                tree.new_error(
                    node, "Tree-processing failed, most likely, due to errors earlier in "
                          "in the processing pipeline. Crash Message: %s: %s\n%s"
                          % (e.__class__.__name__, str(e), trace),
                    TREE_PROCESSING_CRASH)
        else:
            # assume Python crashes are programming mistakes, so let
            # the exceptions through
            tree = tp(tree)
        assert isinstance(tree, RootNode)
    return tree


# TODO: Verify compiler against grammar,
#       i.e. make sure that for all on_X()-methods, `X` is the name of a parser
# TODO: AST validation against an ASDSL-Specification
