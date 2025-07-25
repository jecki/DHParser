# compile.py - Syntax driven compilation support for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
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
are callable and receive the Abstract syntax tree (AST)
as argument and yield whatever output the compiler produces. In
most Digital Humanities applications, this will be
XML-code. However, it can also be anything else, like binary
code or, as in the case of DHParser's EBNF-compiler, Python
source code.

Function ``compile_source`` invokes all stages of the compilation
process, i.e. pre-processing, parsing, CST to AST-transformation
and compilation.

See module ``ebnf`` for a sample of the implementation of a
compiler object.
"""

from __future__ import annotations

import functools
import os
from typing import Any, Optional, Tuple, List, Set, Dict, Union, Callable, NamedTuple

from DHParser.configuration import get_config_value
from DHParser.preprocess import PreprocessorFunc, gen_neutral_srcmap_func
from DHParser.nodetree import Node, RootNode, EMPTY_PTYPE, Path
from DHParser.transform import TransformerFunc
from DHParser.parse import ParserCallable, Parser
from DHParser.error import is_error, is_fatal, Error, FATAL, CANCELED, \
    TREE_PROCESSING_CRASH, COMPILER_CRASH, AST_TRANSFORM_CRASH, has_errors
from DHParser.log import log_parsing_history, log_ST, is_logging
from DHParser.toolkit import load_if_file, is_filename, re, TypeAlias, \
    deprecated, DHPARSER_FILES, CancelQuery


__all__ = ('CompilerError',
           'Compiler',
           'CompileMethod',
           'CompilerFunc',
           'CompilerFactory',
           'CompilationResult',
           'NoTransformation',
           'compile_source',
           'process_tree')


class CompilerError(Exception):
    """
    Exception raised when an error of the compiler itself is detected.
    Compiler errors are not to be confused with errors in the source
    code to be compiled, which do not raise Exceptions but are merely
    reported as an error.
    """
    pass


ROOTNODE_PLACEHOLDER = RootNode()
CompileMethod: TypeAlias = Callable[[Node], Any]


class CancelRequest(Exception):
    pass


class Compiler:
    """
    Class Compiler is the abstract base class for compilers. Compiler
    objects are callable and take the root node of the abstract
    syntax tree (AST) as argument and return the compiled code in a
    format chosen by the compiler itself.

    Subclasses implementing a compiler must define ``on_XXX()``-methods
    for each node name that can occur in the AST where 'XXX' is the
    node's name (for unnamed nodes it is the node's ptype without the
    leading colon ':').

    These compiler methods take the node on which they are run as
    argument. Other than in the AST transformation, which runs depth-first,
    compiler methods are called forward moving starting with the root
    node, and they are responsible for compiling the child nodes
    themselves. This should be done by invoking the ``compile(node)``-
    method which will pick the right ``on_XXX()``-method or,
    more commonly, by calling ``fallback_compiler()``-methods which
    compiles of child-nodes and updates the tuple of children according
    to the results. It is not recommended to call the ``on_XXX()``-methods
    directly!

    Variables that are (re-)set only in the constructor and retain their
    value if changed during subesquent calls:

    :ivar forbid_returning_None:  Default value: True. Most of the time,
        if a compiler-method (i.e. on_XXX()) returns None, this is
        a mistake due to a forgotten return statement. The method
        compile() checks for this mistake and raises an error if
        a compiler-method returns None. However, some compilers require
        the possibility to return None values. In this case
        ``forbis_returing_None`` should be set to False in the constructor
        of the derived class.

        (Another Alternativ would be to return a sentinel object instead of
        None.)

    Object-Variables that are reset after each call of the Compiler-object:

    :ivar path:  A list of parent nodes that ends with the currently
        compiled node.
    :ivar tree: The root of the abstract syntax tree.
    :ivar finalizers:  A stack of tuples (function, parameters) that will be
        called in reverse order after compilation.
    :ivar method_dict: A cache that maps node-names to their respective
        compile-methods.
    :ivar has_attribute_visitors:  A flag indicating that the class has
        attribute-visitor-methods which are named 'attr_ATTRIBUTENAME'
        and will be called if the currently processed node has one
        or more attributes for which such visitors exist.
    :ivar forbid_returning_None: A boolean flag that is true by default to
        catch a common error (i.e. ommiting the return value) when filling
        in compile-methods. Should be set to False in sub-classes that
        do want to allow compile-methods to return None
    :ivar cancel_query: An optional cancel_query function that will be
        called by the compile method and stop short compilation with
        a fatal error if it returns True.

    :ivar _dirty_flag:  A flag indicating that the compiler has already been
        called at least once and that therefore all compilation
        variables must be reset when it is called again.
    :ivar _debug: A flag indicating that debugging is turned on. The value
        for this flag is read before each call of the configuration
        (see debugging-section in :py:mod:`DHParser.configuration`).
        If debugging is turned on, the compiler class raises en
        error if there is an attempt to be compiled one and the same
        node a second time.
    :ivar _debug_already_compiled: A set of nodes that have already been compiled.
    """

    def __init__(self):
        self.has_attribute_visitors: bool = any(field[0:5] == 'attr_' and callable(getattr(self, field))
                                          for field in dir(self))
        self.forbid_returning_None: bool = True
        self.cancel_query = None  # type: Optional[CancelQuery]
        self.reset()

    def reset(self):
        """
        Resets all variables to their default values before the next call
        of the object.
        """
        self.tree = ROOTNODE_PLACEHOLDER   # type: RootNode
        self.path = []  # type: Path
        self._dirty_flag = False
        self._debug = get_config_value('debug_compiler')  # type: bool
        self._debug_already_compiled = set()              # type: Set[Node]
        self.finalizers = []  # type: List[Tuple[Callable, Tuple]]
        self.method_dict = {}  # type: Dict[str, CompileMethod]

    def visitor_name(self, node_name: str) -> str:
        """
        Returns the visitor_method name for `name`, e.g.::

            >>> c = Compiler()
            >>> c.visitor_name('expression')
            'on_expression'
            >>> c.visitor_name('!--')
            'on_212d2d'
        """
        if re.match(r'\w+$', node_name):
            return 'on_' + node_name
        if node_name[:1] ==  ':':
            vname = 'on_' + node_name[1:] + '__'
            if re.match(r'\w+$', vname):  return vname
        letters = []
        for ch in node_name:
            if not re.match(r'\w', ch):
                ch = hex(ord(ch))[2:]
            letters.append(ch)
        return 'on_' + ''.join(letters)

    def attr_visitor_name(self, attr_name: str) -> str:
        """
        Returns the visitor_method name for `attr_name`, e.g.::

            >>> c = Compiler()
            >>> c.attr_visitor_name('class')
            'attr_class'
        """
        return 'attr_' + attr_name.replace('-', '_').replace('.', '_').replace(':', '_')

    def prepare(self, root: RootNode) -> None:
        """
        A preparation method that will be called after everything else has
        been initialized and immediately before compilation starts. This method
        can be overwritten in order to implement preparation tasks.
        """
        pass

    def finalize(self, result: Any) -> Any:
        """
        A finalization method that is called after compilation has finished,
        and after all tasks from the finalizers-stack have been executed.
        """
        if isinstance(self.tree, RootNode):
            self.tree.stage = ''   # turn of stage-verification as default to keep matters simple
        return result

    def wildcard(self, node: Node) -> Any:
        """
        The wildcard method is called on nodes for which no other compilation
        method has been specified. This allows to check, whether illegal
        nodes occur in the tree (although, a static structural validation
        is to be preferred.) or whether a compilation node has been
        forgotten.

        Per default, wildcard() just redirects to self.fallback_compiler()
        """
        return self.fallback_compiler(node)

    def __call__(self, root: Node, *, cancel_query: Optional[CancelQuery] = None) -> Any:
        """
        Compiles the abstract syntax tree with the root node `node` and
        returns the compiled code. It is up to subclasses implementing
        the compiler to determine the format of the returned data.
        (This very much depends on the kind and purpose of the
        implemented compiler.)

        The ``__call__``-method is also responsible for initializations
        required before the compilation and the finalization of the
        compilation has been finished by taking the following steps::

            1. reset all variables and initialize ``self.tree`` with ``root``
            2. call the :py:meth:`Compiler.prepare()`-method.
            3. compile the syntax-tree originating in ``root`` by calling
               :py:meth:`Compiler.compile()` on the root-node.
            4. call all finalizers in the ``self.finalizers``-list.
            5. call the :py:meth:`Compiler.finalize()`-method.

        :param root: The root-node of the syntax tree to be compiled. ``root``
            does not need to be of type :py:class:`~nodetree.RootNode` in order
            to allow compiling parts of a syntax tree.
        :returns: The resulting object of the compilation.
        """
        if self._dirty_flag:
            self.reset()
        self._dirty_flag = True
        self.cancel_query = cancel_query
        self.tree = root if isinstance(root, RootNode) else RootNode(root)
        self.prepare(self.tree)
        try:
            result = self.compile(self.tree)
            while self.finalizers:
                task, parameters = self.finalizers.pop()
                task(*parameters)
            result = self.finalize(result)
            return result
        except CancelRequest:
            return None
        finally:
            self.cancel_query = None

    def visit_attributes(self, node):
        if node.has_attr():
            self.path.append(node)
            for attribute, value in tuple(node.attr.items()):
                try:
                    attribute_visitor = self.__getattribute__(self.attr_visitor_name(attribute))
                    attribute_visitor(node, value)
                except AttributeError:
                    pass
            self.path.pop()

    def fallback_compiler(self, node: Node) -> Any:
        """This is a generic compiler function that will be called on
        all those node types for which no compiler method `on_XXX` has
        been defined."""
        replacements = {}  # type: Dict[int, Node]
        if node.children:
            for child in node.children:
                nd = self.compile(child)
                if id(nd) != id(child):
                    replacements[id(child)] = nd
                if nd is not None and not isinstance(nd, Node):
                    tn = node.name
                    raise TypeError(
                        f'Fallback compiler for Node "{tn}" received a value of type '
                        f'`{type(nd)}` from child "{child.name}" instead of the required '
                        f'return type `Node`. Override method `fallback_compiler()` or '
                        f'add method `{self.visitor_name(tn)}(self, node)` in class '
                        f'`{self.__class__.__name__}` to avoid this error!')
            if replacements:
                # replace Nodes the identity of which has been changed during transformation
                # and drop any returned None-results
                result = []
                for child in node.children:
                    nd = replacements.get(id(child), child)
                    if nd is not None and nd.name != EMPTY_PTYPE:
                        result.append(nd)
                node.result = tuple(result)
        if self.has_attribute_visitors:
            self.visit_attributes(node)
        return node

    def find_compilation_method(self, node: Node) -> CompileMethod:
        def wildcard_or_fallback():
            if self.wildcard != Compiler.wildcard:
                return self.wildcard
            else:
                return self.fallback_compiler

        node_name = node.name
        try:
            method = self.method_dict[node_name]  # check cache, first
        except KeyError:
            method_name = self.visitor_name(node_name)
            try:
                method = getattr(self, method_name)
            except AttributeError:
                if node_name.startswith(':'):
                    try:
                        method = getattr(self, 'on_3a' + node_name[1:])
                    except AttributeError:
                        method = wildcard_or_fallback()
                else:
                    method = wildcard_or_fallback()
            self.method_dict[node_name] = method
        return method

    def compile(self, node: Node,
                find_compilation_method: Optional[Callable[[Node], CompileMethod]] = None) -> Any:
        """
        Calls the compilation method for the given node and returns the
        result of the compilation.

        The method's name is derived from either the node's parser
        name or, if the parser is disposable, the node's parser's class
        name by adding the prefix ``on_``. Other ways of determining
        the right compilation method are possible by providing a function
        that returns a compilation-method for a given node to the
        parameter "find_compilation_method".

        Note that ``compile`` does not call any compilation functions
        for the parsers of the sub nodes by itself. Rather, this should
        be done within the compilation methods.

        :param Node: The node that shall be compiled next. (The path
            of nodes leading from the root of the tree is kept in
            the instance-variable self.path.)
        :param find_compilation_method: A function that returns a
            compilation method for a given node. If None, the
            default method described above will be used.
        :returns: An object of any type (determined by the
            sub-class deriving from class Compile).
        """
        if self._debug:
            assert node not in self._debug_already_compiled
            self._debug_already_compiled.add(node)

        if self.cancel_query is not None:
            if self.cancel_query():
                self.tree.new_error(node, "Compilation stopped by cancel request!", CANCELED)
                raise CancelRequest

        compiler = self.find_compilation_method(node) if find_compilation_method is None \
                   else find_compilation_method(node)
        self.path.append(node)
        result = compiler(node)
        self.path.pop()   # do not put this into a try ... finally: clause, as error reporting still requires the path
        if self.has_attribute_visitors:
            self.visit_attributes(node)
        if result is None and self.forbid_returning_None:
            raise CompilerError(
                ('Method on_%s returned `None` instead of a valid compilation '
                 'result! It is recommended to use `nodetree.EMPTY_NODE` as a '
                 'void value. This Error can be turned off by adding '
                 '`self.forbid_returning_None = False` to the reset()-Method of your'
                 'compiler class, in case on_%s actually SHOULD be allowed to '
                 'return None.') % (node.name.replace(':', '3a'), self.visitor_name(node.name)))
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


# processing pipeline support #########################################

CompilerFunc: TypeAlias = Union[Compiler, Callable[[RootNode], Any], functools.partial]
CompilerFactory: TypeAlias = Union[Callable[[], CompilerFunc], functools.partial]

class CompilationResult(NamedTuple):
    result: Optional[Any]
    messages: List[Error]
    AST: Optional[RootNode]
    __module__ = __name__  # needed for cython compatibility


def NoTransformation(root: RootNode) -> RootNode:
    """Simply passes through the unaltered node-tree."""
    return root


def compile_source(source: str,
                   preprocessor: Optional[PreprocessorFunc],
                   parser: ParserCallable,
                   transformer: TransformerFunc = NoTransformation,
                   compiler: CompilerFunc = NoTransformation,
                   *, start_parser: Union[str, Parser] = "root_parser__",
                      preserve_AST: bool = False,
                      cancel_query: Optional[CancelQuery] = None) -> CompilationResult:
    """Compiles a source in four stages:

    1. Pre-Processing (if needed)
    2. Parsing
    3. AST-transformation
    4. Compiling.

    The later stages AST-transformation, compilation will only be invoked if
    no fatal errors occurred in any of the earlier stages of the processing
    pipeline. Function "compile_source" does not invoke any postprocessing
    after compiling. See functions: :py:func:`run_pipeline`
    and :py:func:`full_compile` for postprocessing and compiling plus
    postprocessing.

    :param source: The input text for compilation or the name of a
            file containing the input text.
    :param preprocessor:  text -> text. A preprocessor function
            or None, if no preprocessor is needed.
    :param parser:  A parsing function or grammar class
    :param transformer:  A transformation function that takes
            the root-node of the concrete syntax tree as an argument and
            transforms it (in place) into an abstract syntax tree.
    :param compiler: A compiler function or compiler class
            instance
    :param start_parser: The name of the parser (or the parser-object itself)
            with which to start. This is useful for compiling sections of
            entire documents without the need to provide a dummy-wrapper.
    :param preserve_AST: Preserves the AST-tree.
    :param cancel_query: A boolean-valued function that will be called
            between the different compilation-stages as to whether
            further processing shall be canceled.

    :returns: The result of the compilation as a 3-tuple
        (result, errors, abstract syntax tree). In detail:

        1. The result as returned by the compiler or ``None`` in case of failure
        2. A list of error or warning messages
        3. The root-node of the abstract syntax tree if `preserve_ast` is True
           or `None` otherwise.
    """
    ast = None  # type: Optional[Node]
    try:
        original_text = load_if_file(source)  # type: str
    except (FileNotFoundError, IOError) as e:
        return CompilationResult(None, [Error(str(e), 0, COMPILER_CRASH)], None)
    source_name = source if is_filename(source) else ''
    log_file_name = logfile_basename(source, compiler) if is_logging() else ''  # type: str
    if not hasattr(parser, 'free_char_parsefunc__') \
            or getattr(parser, 'history_tracking__', False):
        # log only for custom parser/transformer/compilers
        log_syntax_trees = {t.upper() for t in get_config_value('log_syntax_trees')}
    else:
        log_syntax_trees = set()

    # preprocessing

    errors = []
    if preprocessor is None:
        source_text = original_text  # type: str
        source_mapping = gen_neutral_srcmap_func(source_text, source_name)
            # lambda i: SourceLocation(source_name, 0, i)    # type: SourceMapFunc
    else:
        if hasattr(preprocessor, 'cancel_query'):  preprocessor.cancel_query = cancel_query
        _, source_text, source_mapping, errors = preprocessor(original_text, source_name)

    if has_errors(errors, FATAL):
        return CompilationResult(None, errors, None)

    # parsing

    if hasattr(parser, 'cancel_query__'):  parser.cancel_query__ = cancel_query
    syntax_tree: RootNode = parser(source_text, start_parser, source_mapping)
    syntax_tree.docname = source_name if source_name else "DHParser_Document"
    for e in errors:  syntax_tree.add_error(None, e)
    syntax_tree.source = original_text
    syntax_tree.source_mapping = source_mapping
    if 'CST' in log_syntax_trees:
        log_ST(syntax_tree, log_file_name + '.cst')
    if getattr(parser, 'history_tracking__', False):
        log_parsing_history(parser, log_file_name)

    # assert is_error(syntax_tree.error_flag) or str(syntax_tree) == strip_tokens(source_text), \
    #     str(syntax_tree) # Ony valid if neither tokens nor whitespace are dropped early

    result = None
    if cancel_query is not None and not is_fatal(syntax_tree.error_flag) and cancel_query():
        syntax_tree.new_error(syntax_tree, "Processing stopped by cancel request!", CANCELED)
    if not is_fatal(syntax_tree.error_flag):

        # AST-transformation

        if is_error(syntax_tree.error_flag):
            # catch Python exception, because if an error has occurred
            # earlier, the syntax tree might not look like expected,
            # which could (fatally) break AST transformations.
            try:
                if hasattr(transformer, 'cancel_query'):  transformer.cancel_query = cancel_query
                syntax_tree = transformer(syntax_tree)
            except Exception as e:
                syntax_tree.new_error(syntax_tree,
                                      "AST-Transformation failed due to earlier parser errors. "
                                      "Crash Message: %s: %s" % (e.__class__.__name__, str(e)),
                                      AST_TRANSFORM_CRASH)
        else:
            syntax_tree = transformer(syntax_tree)
        assert isinstance(syntax_tree, RootNode)
        # syntax_tree.stage = 'AST'

        if 'AST' in log_syntax_trees:
            log_ST(syntax_tree, log_file_name + '.ast')

        if cancel_query is not None and not is_fatal(syntax_tree.error_flag) and cancel_query():
            syntax_tree.new_error(syntax_tree, "Processing stopped by cancel request!", CANCELED)
        if not is_fatal(syntax_tree.error_flag):
            if preserve_AST:
                import copy
                ast = copy.deepcopy(syntax_tree)
                ast.stage = ''  # turn stage-verification off on copied ast as default

            # Compilation

            if hasattr(compiler, 'cancel_query'):
                compiler.cancel_query = cancel_query
            result = process_tree(compiler, syntax_tree)

    messages = syntax_tree.errors_sorted  # type: List[Error]
    # Obsolete, because RootNode adjusts error locations whenever an error is added:
    # adjust_error_locations(messages, original_text, source_mapping)
    return CompilationResult(result, messages, ast)


def filter_stacktrace(stacktrace: List[str]) -> List[str]:
    """Removes those frames from a formatted stacktrace that are located
    within the DHParser-code."""
    n = 0
    for n, frame in enumerate(stacktrace):
        i = frame.find('"')
        k = frame.find('"', i + 1)
        if frame.find("DHParser", i, k) < 0:
            break
    return stacktrace[n:]


RX_STACKTRACE_FNAME = re.compile(r' *File "([^"]*)"')


def process_tree(tp: CompilerFunc, tree: RootNode) -> Any:
    """Process a tree with the tree-processor `tp` only if no fatal error
    has occurred so far. Catch any Python exceptions in case
    any normal errors have occurred earlier in the processing pipeline.
    Don't catch Python exceptions if no errors have occurred earlier.

    This behavior is based on the assumption that given any non-fatal
    errors have occurred earlier, the tree passed through the pipeline
    might not be in a state that is expected by the later stages, thus if
    an exception occurrs it is not really to be considered a programming
    error. Processing stages should be written with possible errors
    occurring in earlier stages in mind, though. However, because it could
    be difficult to provide for all possible kinds of badly structured
    trees resulting from errors, exceptions occurring when processing
    potentially faulty trees will be dealt with gracefully.

    Tree processing should generally be assumed to change the tree
    in place. If the input tree shall be preserved, it is necessary to
    make a deep copy of the input tree, before calling process_tree.
    """
    assert isinstance(tree, RootNode)
    result = None
    if not is_fatal(tree.error_flag):
        if is_error(tree.error_flag):
            # assume Python crashes are merely a consequence of earlier
            # errors, so let's catch them
            try:
                result = tp(tree)
            except Exception as e:
                node = (getattr(tp, 'path', [tree]) or [tree])[-1]
                import traceback
                st = traceback.format_list(traceback.extract_tb(e.__traceback__))
                for i in range(1, len(st)):  # find last call in client-code
                    m = RX_STACKTRACE_FNAME.match(st[-i])
                    if m and os.path.basename(m.group(1)) not in DHPARSER_FILES:
                        # _ = m.group(1)
                        break
                mini_trace = st[-i][:st[-i].rstrip().rfind('\n')].replace('\n', '\\n')
                tree.new_error(
                    node, "Tree-processing failed, most likely, due to errors earlier in "
                          f"the processing pipeline: {repr(e)}  {mini_trace}", TREE_PROCESSING_CRASH)
        else:
            # assume Python crashes are programming mistakes, so let
            # the exceptions through
            result = tp(tree)
    return result

# TODO: Verify compiler against grammar,
#       i.e. make sure that for all on_X()-methods, `X` is the name of a parser
#       Does that make sense? Tag names could change during AST-Transformation!
# TODO: AST validation against an ASDL-Specification or other structural validation
#       of trees


# Junction = namedtuple('Junction', ['src', 'factory', 'dst'], module=__name__)
class Junction(NamedTuple):
    """DEPRECATED, use: pipeline.Junction"""
    src: str
    factory: Union[CompilerFactory, Any]
    dst: str
    __module__ = __name__
FullCompilationResult = Dict[str, Tuple[Any, List[Error]]]  # DEPRECATED, use pipeline.PipelineResult


@deprecated('extract_data() has movee to the pipeline-module! Use "from DHParser.pipeline import extract_data"')
def extract_data(tree_or_data):
    from DHParser import pipeline
    return pipeline.extract_data(tree_or_data)


@deprecated('end_points() has moved to the pipeline-module! Use "from DHParser.pipeline import end_points"')
def end_points(junctions):
    from DHParser import pipeline
    return pipeline.end_points(junctions)


@deprecated('full_pipeline() has been renamed and moved to the pipeline-module! Use "from DHParser.pipeline import full_pipeline"')
def full_compile(source: str, preprocessor_factory, parser_factory,
                 junctions, target_stages):
    from DHParser import pipeline
    return pipeline.full_pipeline(source, preprocessor_factory, parser_factory,
                                  junctions, target_stages)
