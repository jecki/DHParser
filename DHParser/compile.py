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

from __future__ import annotations

from collections import namedtuple
import copy
import functools
import os
import traceback
from typing import Any, Optional, Tuple, List, Set, Dict, Union, Callable, cast

from DHParser.configuration import get_config_value
from DHParser.preprocess import PreprocessorFunc
from DHParser.nodetree import Node, RootNode, EMPTY_PTYPE, Path
from DHParser.transform import TransformerCallable
from DHParser.parse import Grammar
from DHParser.preprocess import gen_neutral_srcmap_func
from DHParser.error import is_error, is_fatal, Error, FATAL, \
    TREE_PROCESSING_CRASH, COMPILER_CRASH, AST_TRANSFORM_CRASH, has_errors
from DHParser.log import log_parsing_history, log_ST, is_logging
from DHParser.toolkit import load_if_file, is_filename, re, TypeAlias


__all__ = ('CompilerError',
           'Compiler',
           'ParserCallable',
           'CompilerCallable',
           'CompilerFactory',
           'CompilationResult',
           'process_tree',
           'Junction',
           'extract_data',
           'run_pipeline',
           'compile_source')


class CompilerError(Exception):
    """
    Exception raised when an error of the compiler itself is detected.
    Compiler errors are not to be confused with errors in the source
    code to be compiled, which do not raise Exceptions but are merely
    reported as an error.
    """
    pass


ROOTNODE_PLACEHOLDER = RootNode()
CompilerFunc: TypeAlias = Callable[[Node], Any]


class Compiler:
    """
    Class Compiler is the abstract base class for compilers. Compiler
    objects are callable and take the root node of the abstract
    syntax tree (AST) as argument and return the compiled code in a
    format chosen by the compiler itself.

    Subclasses implementing a compiler must define ``on_XXX()``-methods
    for each node name that can occur in the AST where 'XXX' is the
    node's name(for unnamed nodes it is the node's ptype without the
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
        the possibility to return None-values. In this case
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

    :ivar has_attribute_visitors:  A flag indicating that the class has
        attribute-visitor-methods which are named 'attr_ATTRIBUTENAME'
        and will be called if the currently processed node has one
        or more attributes for which such visitors exist.

    :ivar _dirty_flag:  A flag indicating that the compiler has already been
        called at least once and that therefore all compilation
        variables must be reset when it is called again.
    :ivar _debug: A flag indicating that debugging is turned on. The value
        for this flag is read before each call of the configuration
        (see debugging section in :py:mod:`DHParser.configuration`).
        If debugging is turned on the compiler class raises en
        error if there is an attempt to be compiled one and the same
        node a second time.
    :ivar _debug_already_compiled: A set of nodes that have already been compiled.
    """

    def __init__(self):
        self.has_attribute_visitors: bool = any(field[0:5] == 'attr_' and callable(getattr(self, field))
                                          for field in dir(self))
        self.forbid_returning_None: bool = True
        self.reset()

    def reset(self):
        """
        Resets alls variables to their default values before the next call
        of the object.
        """
        self.tree = ROOTNODE_PLACEHOLDER   # type: RootNode
        self.path = []  # type: Path
        self._dirty_flag = False
        self._debug = get_config_value('debug_compiler')  # type: bool
        self._debug_already_compiled = set()              # type: Set[Node]
        self.finalizers = []  # type: List[Tuple[Callable, Tuple]]
        self.method_dict = {}  # type: Dict[str, CompilerFunc]

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
        else:
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
        A finalization method that is called after compilation has finished and
        after all tasks from the finalizers-stack have been executed
        """
        return result

    def wildcard(self, node: Node) -> Any:
        """
        The wildcard method is called on nodes for which no other compilation-
        method has been specified. This allows to check, whether illegal
        nodes occur in the tree (although, a static structural validation
        is to be preferred.) or whether a compilation node has been
        forgotten.

        Per default, wildcard() just redirects to self.fallback_compiler()
        """
        return self.fallback_compiler(node)

    def __call__(self, root: Node) -> Any:
        """
        Compiles the abstract syntax tree with the root node `node` and
        returns the compiled code. It is up to subclasses implementing
        the compiler to determine the format of the returned data.
        (This very much depends on the kind and purpose of the
        implemented compiler.)

        The ``__call__``-method is also responsible for initializations
        required before the compilation and the finalization the compilation
        has been finished by taking the following steps::

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
        self.tree = cast(RootNode, root) if isinstance(root, RootNode) else RootNode(root)
        self.prepare(self.tree)
        result = self.compile(self.tree)
        while self.finalizers:
            task, parameters = self.finalizers.pop()
            task(*parameters)
        result = self.finalize(result)
        return result

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
        """This is a generic compiler function which will be called on
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
                        'Fallback compiler for Node `%s` received a value of type '
                        '`%s` from child `%s` instead of the required return type `Node`. '
                        'Override `DHParser.compile.Compiler.fallback_compiler()` or add '
                        'method `on_%s(self, node)` in class `%s` to avoid this error!'
                        % (tn, str(type(nd)), child.name, tn, self.__class__.__name__))
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

    def find_compilation_method(self, node_name: str) -> CompilerFunc:
        try:
            method = self.method_dict[node_name]
        except KeyError:
            method_name = self.visitor_name(node_name)
            try:
                method = self.__getattribute__(method_name)
            except AttributeError:
                if self.wildcard != Compiler.wildcard:
                    method = self.wildcard
                else:
                    method = self.fallback_compiler
            self.method_dict[node_name] = method
        return method

    def compile(self, node: Node) -> Any:
        """
        Calls the compilation method for the given node and returns the
        result of the compilation.

        The method's name is derived from either the node's parser
        name or, if the parser is disposable, the node's parser's class
        name by adding the prefix ``on_``.

        Note that ``compile`` does not call any compilation functions
        for the parsers of the sub nodes by itself. Rather, this should
        be done within the compilation methods.
        """
        if self._debug:
            assert node not in self._debug_already_compiled
            self._debug_already_compiled.add(node)

        elem = node.name
        if elem[:1] == ':':
            elem = elem[1:] + '__'
        compiler = self.find_compilation_method(elem)
        self.path.append(node)
        result = compiler(node)     
        self.path.pop()
        if self.has_attribute_visitors:
            self.visit_attributes(node)          
        if result is None and self.forbid_returning_None:
            raise CompilerError(
                ('Method on_%s returned `None` instead of a valid compilation '
                 'result! It is recommended to use `nodetree.EMPTY_NODE` as a '
                 'void value. This Error can be turn off by adding '
                 '`self.forbid_returning_None = False` to the reset()-Method of your'
                 'compiler class, in case on_%s actually SHOULD be allowed to '
                 'return None.') % (elem, elem))
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

ParserCallable: TypeAlias = Union[Grammar, Callable[[str], RootNode], functools.partial]
CompilerCallable: TypeAlias = Union[Compiler, Callable[[RootNode], Any], functools.partial]
CompilerFactory: TypeAlias = Union[Callable[[], CompilerCallable], functools.partial]


CompilationResult = namedtuple('CompilationResult',
    ['result',      ## type: Optional[Any]
     'messages',    ## type: List[Error]
     'AST'],        ## type: Optional[RootNode]
    module=__name__)


def compile_source(source: str,
                   preprocessor: Optional[PreprocessorFunc],
                   parser: ParserCallable,
                   transformer: TransformerCallable,
                   compiler: CompilerCallable,
                   *, preserve_AST: bool = False) -> CompilationResult:
    """Compiles a source in four stages:

    1. Pre-Processing (if needed)
    2. Parsing
    3. AST-transformation
    4. Compiling.

    The later stages AST-transformation, compilation will only be invoked if
    no fatal errors occurred in any of the earlier stages of the processing
    pipeline.

    :param source: The input text for compilation or a the name of a
            file containing the input text.
    :param preprocessor:  text -> text. A preprocessor function
            or None, if no preprocessor is needed.
    :param parser:  A parsing function or grammar class
    :param transformer:  A transformation function that takes
            the root-node of the concrete syntax tree as an argument and
            transforms it (in place) into an abstract syntax tree.
    :param compiler: A compiler function or compiler class
            instance
    :param preserve_AST: Preserves the AST-tree.

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
    if not hasattr(parser, 'free_char_parsefunc__') or parser.history_tracking__:
        # log only for custom parser/transformer/compilers
        log_syntax_trees = get_config_value('log_syntax_trees')
    else:
        log_syntax_trees = set()

    # preprocessing

    errors = []
    if preprocessor is None:
        source_text = original_text  # type: str
        source_mapping = gen_neutral_srcmap_func(source_text, source_name)
            # lambda i: SourceLocation(source_name, 0, i)    # type: SourceMapFunc
    else:
        _, source_text, source_mapping, errors = preprocessor(original_text, source_name)

    if has_errors(errors, FATAL):
        return CompilationResult(None, errors, None)

    # parsing

    syntax_tree: RootNode = parser(source_text, source_mapping=source_mapping)
    syntax_tree.docname = source_name if source_name else "DHParser_Document"
    for e in errors:  syntax_tree.add_error(None, e)
    syntax_tree.source = original_text
    syntax_tree.source_mapping = source_mapping
    if 'cst' in log_syntax_trees:
        log_ST(syntax_tree, log_file_name + '.cst')
    if parser.history_tracking__:
        log_parsing_history(parser, log_file_name)

    # assert is_error(syntax_tree.error_flag) or str(syntax_tree) == strip_tokens(source_text), \
    #     str(syntax_tree) # Ony valid if neither tokens or whitespace are dropped early

    result = None
    if not is_fatal(syntax_tree.error_flag):

        # AST-transformation

        if is_error(syntax_tree.error_flag):
            # catch Python exception, because if an error has occurred
            # earlier, the syntax tree might not look like expected,
            # which could (fatally) break AST transformations.
            try:
                syntax_tree = transformer(syntax_tree)
            except Exception as e:
                syntax_tree.new_error(syntax_tree,
                                      "AST-Transformation failed due to earlier parser errors. "
                                      "Crash Message: %s: %s" % (e.__class__.__name__, str(e)),
                                      AST_TRANSFORM_CRASH)
        else:
            syntax_tree = transformer(syntax_tree)

        if 'ast' in log_syntax_trees:
            log_ST(syntax_tree, log_file_name + '.ast')

        if not is_fatal(syntax_tree.error_flag):
            if preserve_AST:
                ast = copy.deepcopy(syntax_tree)

            # Compilation

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


def process_tree(tp: CompilerCallable, tree: RootNode) -> Any:
    """Process a tree with the tree-processor `tp` only if no fatal error
    has occurred so far. Catch any Python-exceptions in case
    any normal errors have occurred earlier in the processing pipeline.
    Don't catch Python-exceptions if no errors have occurred earlier.

    This behavior is based on the assumption that given any non-fatal
    errors have occurred earlier, the tree passed through the pipeline
    might not be in a state that is expected by the later stages, thus if
    an exception occurs it is not really to be considered a programming
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
                # node = tp.path[-1] if hasattr(tp, 'path') and tp.path else tree
                node = getattr(tp, 'path', [tree])[-1]
                st = traceback.format_list(traceback.extract_tb(e.__traceback__))
                trace = ''.join(st)  # filter_stacktrace(st)
                tree.new_error(
                    node, "Tree-processing failed, most likely, due to errors earlier in "
                          "in the processing pipeline. Crash Message: %s: %s\n%s"
                          % (e.__class__.__name__, str(e), trace),
                    TREE_PROCESSING_CRASH)
        else:
            # assume Python crashes are programming mistakes, so let
            # the exceptions through
            result = tp(tree)
    return result


Junction: TypeAlias = Tuple[str, CompilerFactory, str]  # source stage name, source->target, target stage name


def extract_data(tree_or_data: Union[RootNode, Node, Any]) -> Any:
    """Retrieves the data from the given tree or just passes the data through
    if argument ``tree_or_data`` is not of type RootNode."""
    if isinstance(tree_or_data, RootNode):
        return cast(RootNode, tree_or_data).data
    return tree_or_data


def run_pipeline(junctions: Set[Junction],
                 source_stages: Dict[str, RootNode],
                 target_stages: Set[str]) -> Dict[str, Tuple[Any, List[Error]]]:
    """
    Runs all the intermediary compilation-steps that are necessary to produce
    the "target-stages" from the given "source-stages". Here, each source-stage
    consists of a name for that stage, say "AST", and a node-tree that
    represents the data at this stage of the processing pipeline. In the
    target-stage, the data can be a node-tree or data of any other kind.

    The stages or connected through chains of junctions, where a junction is
    essentially a function that transforms a tree from one particular stage
    (identified by its name) to another stage, again itentified by its name.

    TODO: Parallelize processing of junctions
    """
    def cmp_junctions(a, b) -> int:
        if a[-1] == b[0]:
            return -11
        if b[-1] == a[0]:
            return 1
        return 0

    t_to_j = {j[-1]: j for j in junctions}
    steps = []
    targets = target_stages.copy()
    already_reached = targets.copy() | source_stages.keys()
    while targets:
        try:
            j_sequence = [t_to_j[t] for t in targets if t not in source_stages]
            j_sequence.sort(key=functools.cmp_to_key(cmp_junctions))
            steps.append(j_sequence)
        except KeyError as e:
            raise AssertionError(f"{e.args[0]} is not a valid target.")
        targets = {j[0] for j in steps[-1] if j[0] not in already_reached}
        already_reached |= targets
        for step in steps[:-1]:
            for j in steps[-1]:
                try:
                    step.remove(j)
                except ValueError:
                    pass
    if not (target_stages <= already_reached):
        raise ValueError(f'Target-stages: {target_stages - already_reached} '
                         f'cannot be reached with junctions: {junctions}.')
    sources = [j[0] for step in steps for j in step]
    disposables = {s for s in set(sources) if s not in target_stages and sources.count(s) <= 1}
    steps.reverse()
    results: Dict[str, Any] = source_stages.copy()
    errata: Dict[str, List[Error]] = {s: source_stages[s].errors_sorted for s in source_stages}
    for step in steps:
        for junction in step:
            t = junction[-1]
            if t not in results:
                s = junction[0]
                tree = results[s] if s in disposables else copy.deepcopy(results[s])
                if s not in target_stages:
                    sources.remove(s)
                    if sources.count(s) <= 1:
                        disposables.add(s)
                if tree is None:
                    results[t] = None
                    errata[t] = []
                else:
                    if not isinstance(tree, RootNode):
                        raise ValueError(f'Object in stage {s} is not a tree but a {type(tree)} '
                                         f'and, therefore, cannot be processed to {t}')
                    results[t] = process_tree(junction[1](), tree)
                    errata[t] = copy.copy(tree.errors_sorted)
    return {t: (extract_data(results[t]), errata[t]) for t in results.keys()}


# TODO: Verify compiler against grammar,
#       i.e. make sure that for all on_X()-methods, `X` is the name of a parser
#       Does that make sense? Tag names could change during AST-Transformation!
# TODO: AST validation against an ASDL-Specification
