# pipeline.py - Processing-pipelines for consecutive stages of tree/data-transformations
#
# Copyright 2023  by Eckhart Arnold (arnold@badw.de)
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
Module ``pipeline`` implements support for processing-pipelines for
connecting successive stages of tree transformations (called
"junctions") to processing pipelines. Processing pipelines have
one staring point, the source-document, but can have one or more
end points. For example, if the source is a text-document, the
end points can be an HTML document for the online-presentation
and a LaTeX-document to produce a printed version.

Each junction is a triple of the name of the source-stage,
the transformation-function and the name of the destination-stage.
Pipelines are defined by the set of junctions from which paths
connecting the source-point to the end-points are derived
algorithmically.
"""

from __future__ import annotations

import functools

from functools import partial
from typing import Set, Union, Any, Dict, List, Tuple, Iterable, Optional, Sequence, NamedTuple, \
    Callable

from DHParser.compile import compile_source, process_tree, CompilerFactory
from DHParser.configuration import get_config_value
from DHParser.error import Error, has_errors, is_fatal, FATAL, CANCELED
from DHParser.nodetree import RootNode, Node
from DHParser.parse import Grammar, ParserFactory, Parser
from DHParser.preprocess import PreprocessorFactory, PreprocessorFunc, Tokenizer, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors, \
    DeriveFileNameFunc
from DHParser.toolkit import ThreadLocalSingletonFactory, deprecation_warning, deprecated, \
    get_annotations, CancelQuery
from DHParser.trace import resume_notices_on, set_tracer, trace_history
from DHParser.transform import TransformerFunc, TransformerFactory, transformer, TransformationDict

__all__ = ('Junction',
           'PipelineResult',
           'end_points',
           'extract_data',
           'run_pipeline',
           'full_pipeline',
           'PseudoJunction',
           'create_preprocess_junction',
           'create_parser_junction',
           'create_compiler_junction',
           'create_evaluation_junction',
           'create_junction')


class Junction(NamedTuple):
    """A junction is a triple of the name of the source-stage,
    a factory-function that returns the actual transformation
    function and the name of the destination-stage."""
    src: str
    factory: Union[ParserFactory, CompilerFactory, TransformerFactory]
    dst: str
    __module__ = __name__  # needed for cython compatibility


# compilation and postprocessing result:
# Dict: target-stage-name -> (result, errors)
PipelineResult = Dict[str, Tuple[Union[RootNode, Any], List[Error]]]


def end_points(junctions: Iterable[Junction]) -> Set[str]:
    """Returns all "final" destination stages, i.e. destinations
    that are not a source of another junction."""
    sources = { j.src for j in junctions }
    return {j.dst for j in junctions if j.dst not in sources}


def extract_data(tree_or_data: Union[RootNode, Node, Any]) -> Any:
    """Retrieves the data from the given tree or just passes the data through
    if argument ``tree_or_data`` is not of type RootNode."""
    if isinstance(tree_or_data, RootNode):
        return tree_or_data.data
    return tree_or_data


def run_pipeline(junctions: Set[Junction],
                 source_stages: Dict[str, RootNode],
                 target_stages: Set[str],
                 *, cancel_query: Optional[CancelQuery] = None) -> PipelineResult:
    """
    Runs all the intermediary compilation-steps that are necessary to produce
    the "target-stages" from the given "source-stages". Here, each source-stage
    consists of a name for that stage, say "AST", and a node-tree that
    represents the data at this stage of the processing pipeline. In the
    target-stage, the data can be a node-tree or data of any other kind.

    The stages or connected through chains of junctions, where a junction is
    essentially a function that transforms a tree from one particular stage
    (identified by its name) to another stage, again identified by its name.

    TODO: Parallelize processing of junctions? Requires copying a lot ot tree-data!?
    """
    import copy

    def cmp_junctions(a, b) -> int:
        if a[-1] == b[0]:
            return -1
        if b[-1] == a[0]:
            return 1
        if b[-1] > a[-1]:
            return -1
        else:
            return 0

    def verify_stage(given_stage, junction, field, further_info=''):
        if not given_stage:  return  # verification is considered as turned off
        assert field in (0, 2)
        expected_stage = junction[field]
        stage_type = 'source stage' if field == 0 else 'target stage'
        if given_stage.lower() != expected_stage.lower():
            if isinstance(junction[1], ThreadLocalSingletonFactory):
                func = junction[1].class_or_factory.__name__
            else:
                func = junction[1].__name__
            error_msg = (f'Expected {stage_type} "{expected_stage}" but found '
                f'"{given_stage}" when applying {junction[0]}->{junction[2]} ({func})! '
                'Possible causes: a) wrong stage name specified in junction  b) stage name not '
                f'updated by compilation-function  c) internal error of DHParser. {further_info}')
            import traceback
            stack = traceback.extract_stack()
            for call in stack:
                if call.line and call.line.find('run_grammar_tests') >= 0:
                    if call.line.find('get_') >= 0:
                        # Be kind and backwards-compatible with old code
                        deprecation_warning(f'Your transformation {junction[0]}->{junction[2]}: '
                            f"{func} failed to update RootNode.stage "
                            f'with the name of the target stage: "{junction[2]}"! '
                            f'Future versions of DHParser might fail right here.')
                        print(error_msg)
                        break
            else:
                raise AssertionError(error_msg)

    def normalize_name(name: str) -> str:
        NAME = name.upper()
        return NAME if NAME in ('AST', 'CST') else name

    def normalize_junction(j: Junction):
        SRC = j[0].upper()
        if SRC == 'CST':
            return Junction('CST', j[1], normalize_name(j[2]))
        elif SRC == 'AST' and SRC != j[0]:
            return Junction('AST', j[1], j[2])
        else:
            return j

    t_to_j = {normalize_name(j[-1]): normalize_junction(j) for j in junctions}
    target_stages = {normalize_name(t) for t in target_stages}
    source_stages = {normalize_name(s): source_stages[s] for s in source_stages}
    steps = []
    targets = target_stages.copy()
    already_reached = targets | source_stages.keys()
    while targets:
        try:
            j_sequence = [t_to_j[t] for t in targets if t not in source_stages]
            j_sequence.sort(key=functools.cmp_to_key(cmp_junctions))
            steps.append(j_sequence)
        except KeyError as e:
            raise AssertionError(f"{e.args[0]} is not a valid target.") from e
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
    cancel = False
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
                    errata[t] = errata[s]
                else:
                    if not isinstance(tree, RootNode):
                        raise ValueError(f'Object in stage "{s}" is not a tree but a {type(tree)}'
                                         f' and, therefore, cannot be processed to {t}')
                    verify_stage(tree.stage, junction, 0)
                    transformation = junction[1]()
                    if hasattr(transformation, 'cancel_query'):
                        transformation.cancel_query = cancel_query
                    elif hasattr(transformation, 'cancel_query__'):
                        transformation.cancel_query__ = cancel_query
                    results[t] = process_tree(transformation, tree)  # TODO: pass cancel query, here
                    errata[t] = copy.copy(tree.errors_sorted)
                    if cancel_query is not None and cancel_query():
                        tree.new_error(tree, "Pipeline-processing canceled!", CANCELED)
                    if is_fatal(tree.error_flag):
                        cancel = True
                        break
                    if tree.stage == s:  # tree stage hasn't been set by the processing function
                        tree.stage = junction[2]
                    else:
                        verify_stage(tree.stage, junction, 2)
        if cancel:
            break
    return {t: (extract_data(results[t]), errata[t]) for t in results.keys()}


def full_pipeline(source: str,
                  preprocessor_factory: PreprocessorFactory,
                  parser_factory: ParserFactory,
                  junctions: Set[Junction],
                  target_stages: Set[str],
                  start_parser: Union[str, Parser] = "root_parser__",
                  *, cancel_query: Optional[CancelQuery] = None) -> PipelineResult:
    """Runs a processing pipeline starting from the source-code (in contrast
    to "run_pipeline()" which starts from any tree-stage, typically, from
    the concrete syntax-tree (CST).

    "full_pipeline()" preprocesses and compiles the source-document,
    first. And then it post-processes the source into the given target stages.
    Mind that if there are fatal errors earlier in the pipeline, some or all
    target stages might not be reached and thus not be included in the result.
    """
    cst, msgs, _ = compile_source(source, preprocessor_factory(), parser_factory(),
                                  start_parser=start_parser, cancel_query=cancel_query)
    if has_errors(msgs, FATAL):
        return {ts: (cst, msgs) for ts in target_stages}
    return run_pipeline(junctions, {cst.stage: cst}, target_stages,
                        cancel_query=cancel_query)


#######################################################################
#
# Helper-functions for creating junctions
#
#######################################################################

# In the following PARTIAL FUNCTIONS are used rather than local functions,
# because the closure of local functions cannot be pickled!

# Preprocessing-Stage #################################################

# def _preprocess(source, factory) -> Union[str, StringView]:
#     return factory()(source)

class PseudoJunction(NamedTuple):
    factory: Union[PreprocessorFactory, ParserFactory]
    __module__ = __name__  # needed for cython compatibility


def _preprocessor_factory(prep_func: Union[PreprocessorFunc, Tokenizer],
                          include_regex,
                          comment_regex,
                          derive_file_name,
                          func_type: Optional[type]=None) -> PreprocessorFunc:
    # below, the second parameter must always be the same as Grammar.COMMENT__!
    find_next_include = gen_find_include_func(include_regex, comment_regex, derive_file_name)
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    anno = get_annotations(prep_func)
    try:
        if anno['return'] == "PreprocessorResult":
            assert func_type is None or func_type is PreprocessorFunc, \
                f"func_type={func_type} is incompatible with return type PreprocessorResult of " \
                f"parameter prep_func when calling DHParser.pipeline.create_preprocess_junction()"
            prep = prep_func
        else:
            assert func_type is None or func_type is Tokenizer, \
                f"func_type={func_type} is incompatible with return type {anno['return']} of " \
                f"parameter prep_func when calling DHParser.pipeline.create_preprocess_junction()"
            prep = make_preprocessor(prep_func)
    except KeyError:
        assert func_type is not None, \
            "Please specify the kind of preprocessor by passing parameter func_type=Tokenizer " \
            "or func_type=PreprocessorFunc to DHParser.pipeline.create_preprocess_junction()"
        prep = prep_func if func_type is PreprocessorFunc else make_preprocessor(prep_func)
    return chain_preprocessors(include_prep, prep)

def same_name(name: str) -> str:
    return name


def create_preprocess_junction(prep_func: Union[PreprocessorFunc, Tokenizer],
                               include_regex,
                               comment_regex,
                               derive_file_name: DeriveFileNameFunc=same_name,
                               func_type: Optional[type]=None) -> PseudoJunction:
    """Creates a factory for thread-safe preprocessing functions as well as a
    thread-safe preprocessing function."""
    preprocessor_factory = partial(
        _preprocessor_factory, prep_func=prep_func,
        include_regex=include_regex, comment_regex=comment_regex,
        derive_file_name=derive_file_name, func_type=func_type)
    thread_safe_factory = ThreadLocalSingletonFactory(preprocessor_factory)
    # preprocess = partial(_preprocess, factory=thread_safe_factory)
    return PseudoJunction(thread_safe_factory)  # , preprocess)


# Parsing-stage #######################################################

# def _parse_func(parser_factory: Callable, document, start_parser = "root_parser__",
#                 *, complete_match=True):
#     return parser_factory()(document, start_parser, complete_match=complete_match)

def _parser_factory(raw_grammar) -> Grammar:
    grammar = raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    try:
        if not grammar.__class__.python_src__:
            grammar.__class__.python_src__ = getattr(_parser_factory, 'python_src__','')
    except AttributeError:
        pass
    return grammar


def create_parser_junction(grammar_class: type) -> PseudoJunction:
    """Creates a factory for thread-safe parser functions as well as a
    thread-safe parser function."""
    assert issubclass(grammar_class, Grammar)
    raw_grammar = ThreadLocalSingletonFactory(grammar_class)
    factory = partial(_parser_factory, raw_grammar=raw_grammar)
    # process = partial(_parse_func, parser_factory=factory)
    return PseudoJunction(factory)  # , process)


# Tree-Processing-Stages ##############################################

# 1. tree-processing with Compiler-class

# def process_template(src_tree: Node, src_stage: str, dst_stage: str,
#                      factory_function) -> Any:
#     """A generic templare for tree-transformation-functions."""
#     if isinstance(src_tree, RootNode):
#         assert src_tree.stage == src_stage
#     result = factory_function()(src_tree)
#     if isinstance(result, RootNode):
#         assert result.stage in (src_stage, dst_stage)
#         result.stage = dst_stage
#     return result

def create_compiler_junction(compile_class: type,
                             src_stage: str,
                             dst_stage: str) -> Junction:
    """Creates a thread-safe transformation function and function-factory from
    a :py:class:`compile.Compiler` or another callable class.
    """
    assert callable(compile_class)
    # assert src_stage and src_stage.islower()
    # assert dst_stage and dst_stage.islower()
    factory = ThreadLocalSingletonFactory(compile_class)
    # process = partial(process_template, src_stage=src_stage, dst_stage=dst_stage,
    #                   factory_function=factory)
    return Junction(src_stage, factory, dst_stage)


# 2. tree-processing with transformation-table

def _make_transformer(src_stage, dst_stage, table) -> TransformerFunc:
    return staticmethod(partial(transformer, transformation_table=table.copy(),
                                src_stage=src_stage, dst_stage=dst_stage))


@deprecated("DHParser.pipeline.create_transtable_transition() is deprecated, "
            "because it does not work with lambdas as transformer functions!")
def create_transtable_junction(table: TransformationDict,
                               src_stage: str,
                               dst_stage: str) -> Junction:
    """Creates a thread-safe transformation function and function-factory from
    a transformation-table :py:func:`transform.traverse`.

    TODO: This does not work if table contains functions that cannot be pickled (i.e. lambda-functions)!
    """
    assert isinstance(table, dict)
    assert src_stage and src_stage.islower()
    assert dst_stage and dst_stage.islower()
    make_transformer = partial(_make_transformer, src_stage, dst_stage, table)
    factory = ThreadLocalSingletonFactory(make_transformer, uniqueID=id(table))
    return Junction(src_stage, factory, dst_stage)


@deprecated('The name "create_transtable_transition()" is deprecated. Use "create_transtable_junction()" instead.')
def create_transtable_transition(*args, **kwargs):
    return   create_transtable_junction(*args, **kwargs)


# 3. tree-processing with evaluation-table

def _make_evaluation(actions, supply_path_arg) -> Callable[[Node], Any]:
    def evaluate_with_path(node: Node) -> Any:
        return node.evaluate(actions, [node])

    def evaluate_without_path(node: Node) -> Any:
        return node.evaluate(actions, path=[])

    return evaluate_with_path if supply_path_arg else evaluate_without_path


def create_evaluation_junction(actions: Dict[str, Callable],
                               src_stage: str,
                               dst_stage: str,
                               supply_path_arg: bool=True) -> Junction:
    """Creates a thread-safe transformation function and function-factory from
    an evaluation-table :py:meth:`nodetree.Node.evaluate`.
    """
    assert isinstance(actions, dict)
    assert src_stage and src_stage.islower()
    assert dst_stage and dst_stage.islower()
    make_evaluation = partial(
        _make_evaluation, actions=actions, supply_path_arg=supply_path_arg)
    factory = ThreadLocalSingletonFactory(make_evaluation, uniqueID=id(actions))
    # process = partial(process_template, src_stage=src_stage, dst_stage=dst_stage,
    #                   factory_function=factory)
    return Junction(src_stage, factory, dst_stage)


# generic tree-processing function

def create_junction(tool: Union[dict, type],
                    src_stage: str,
                    dst_stage: str,
                    hint: str = '?') -> Junction:
    """Generic stage-creation function for tree-transforming stages where a tree-transforming
    stage is a stage which either reshapes a node-tree or transforms a nodetree into
    something else, but not a stage where something else (e.g. a text) is turned into
    a node-tree."""
    if isinstance(tool, type):
        return create_compiler_junction(tool, src_stage, dst_stage)
    else:
        assert isinstance(tool, dict)
        if any(isinstance(value, Sequence) for value in tool.values()) \
                or hint == "transtable":
            return create_transtable_junction(tool, src_stage, dst_stage)
        elif hint == "evaluate_with_path":
            return create_evaluation_junction(tool, src_stage, dst_stage, True)
        elif hint == "evaluate_without_path":
            return create_evaluation_junction(tool, src_stage, dst_stage, False)
        else:
            raise AssertionError('Cannot determine transformation-type automatically! '
                'Please, add optional parameter "hint" to the function call with one of the '
                'following values: "transtable", "evaluate_with_path", "evaluate_without_path"!')
