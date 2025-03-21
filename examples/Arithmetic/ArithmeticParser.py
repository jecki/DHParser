#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, '..', '..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser.compile import Compiler, compile_source
from DHParser.pipeline import full_pipeline, Junction, PseudoJunction, create_preprocess_junction, \
    create_parser_junction, create_junction
from DHParser.configuration import set_config_value, get_config_value, access_thread_locals, \
    access_presets, finalize_presets, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN
from DHParser import dsl
from DHParser.dsl import recompile_grammar, never_cancel
from DHParser.ebnf import grammar_changed
from DHParser.error import ErrorCode, Error, canonical_error_strings, has_errors, ERROR, FATAL
from DHParser.log import start_logging, suspend_logging, resume_logging
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, RootNode
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, mixin_comment, \
    last_value, matching_bracket, optional_last_value, SmartRE
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc, PreprocessorResult, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors
from DHParser.toolkit import is_filename, load_if_file, cpu_count, RX_NEVER_MATCH, \
    ThreadLocalSingletonFactory, expand_table, INFINITE
from DHParser.trace import set_tracer, resume_notices_on, trace_history
from DHParser.transform import is_empty, remove_if, TransformationDict, TransformerFunc, \
    transformation_factory, remove_children_if, move_fringes, normalize_whitespace, \
    is_anonymous, name_matches, reduce_single_child, replace_by_single_child, replace_or_reduce, \
    remove_whitespace, replace_by_children, remove_empty, remove_tokens, flatten, all_of, \
    any_of, transformer, merge_adjacent, collapse, collapse_children_if, transform_result, \
    remove_children, remove_content, remove_brackets, change_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, add_error, error_on, \
    left_associative, lean_left, node_maker, has_descendant, neg, has_ancestor, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, traverse
from DHParser import parse as parse_namespace__

from DHParser.dsl import PseudoJunction, create_parser_junction

from DHParser.dsl import PseudoJunction, create_parser_junction

from DHParser.dsl import PseudoJunction, create_parser_junction


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def get_preprocessor() -> PreprocessorFunc:
    return nil_preprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ArithmeticGrammar(Grammar):
    r"""Parser for an Arithmetic source file.
    """
    expression = Forward()
    source_hash__ = "ae82073b3e74d71d0bae7d6e7a81dedf"
    disposable__ = re.compile('$.')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'#.*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    VARIABLE = Series(RegExp('[A-Za-z]'), dwsp__)
    NUMBER = Series(RegExp('(?:0|(?:[1-9]\\d*))(?:\\.\\d+)?'), dwsp__)
    NEGATIVE = RegExp('[-]')
    POSITIVE = RegExp('[+]')
    DIV = Series(Text("/"), dwsp__)
    MUL = Series(Text("*"), dwsp__)
    MINUS = Series(Text("-"), dwsp__)
    PLUS = Series(Text("+"), dwsp__)
    group = Series(Series(Drop(Text("(")), dwsp__), expression, Series(Drop(Text(")")), dwsp__))
    sign = Alternative(POSITIVE, NEGATIVE)
    factor = Series(Option(sign), Alternative(NUMBER, VARIABLE, group), ZeroOrMore(Alternative(VARIABLE, group)))
    term = Series(factor, ZeroOrMore(Series(Alternative(DIV, MUL), factor)))
    expression.set(Series(term, ZeroOrMore(Series(Alternative(PLUS, MINUS), term))))
    root__ = expression
    
parsing: PseudoJunction = create_parser_junction(ArithmeticGrammar)
get_grammar = parsing.factory # for backwards compatibility, only


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

get_grammar = parsing.factory

Arithmetic_AST_transformation_table = {
    # AST Transformations for the Arithmetic-grammar
    "expression, term": [left_associative, replace_by_single_child],
    "factor, sign": replace_by_single_child,
    "group": [remove_tokens('(', ')'), replace_by_single_child],
}


def CreateArithmeticTransformer() -> TransformerFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=Arithmetic_AST_transformation_table.copy())


def get_transformer() -> TransformerFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.Arithmetic_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Arithmetic_00000001_transformer_singleton = CreateArithmeticTransformer()
        transformer = THREAD_LOCALS.Arithmetic_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ArithmeticCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Arithmetic source file.
    """

    def __init__(self):
        super(ArithmeticCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_expression(self, node):
        return self.fallback_compiler(node)

    # def on_term(self, node):
    #     return node

    # def on_factor(self, node):
    #     return node

    # def on_sign(self, node):
    #     return node

    # def on_group(self, node):
    #     return node

    # def on_PLUS(self, node):
    #     return node

    # def on_MINUS(self, node):
    #     return node

    # def on_MUL(self, node):
    #     return node

    # def on_DIV(self, node):
    #     return node

    # def on_POSITIVE(self, node):
    #     return node

    # def on_NEGATIVE(self, node):
    #     return node

    # def on_NUMBER(self, node):
    #     return node

    # def on_VARIABLE(self, node):
    #     return node



def get_compiler() -> ArithmeticCompiler:
    """Returns a thread/process-exclusive ArithmeticCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.Arithmetic_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.Arithmetic_00000001_compiler_singleton = ArithmeticCompiler()
        compiler = THREAD_LOCALS.Arithmetic_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple


if __name__ == "__main__":
    # recompile grammar if needed
    if __file__.endswith('Parser.py'):
        grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    else:
        grammar_path = os.path.splitext(__file__)[0] + '.ebnf'
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path) and os.path.isfile(grammar_path):
        if not recompile_grammar(grammar_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_MESSAGES.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
        elif parser_update:
            print(os.path.basename(__file__) + ' has changed. '
                  'Please run again in order to apply updated compiler')
            sys.exit(0)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses a Arithmetic-file and shows its syntax-tree.")
    parser.add_argument('files', nargs=1)
    parser.add_argument('-d', '--debug', action='store_const', const='debug')
    parser.add_argument('-x', '--xml', action='store_const', const='xml')

    args = parser.parse_args()
    file_name, log_dir = args.files[0], ''

    if not os.path.exists(file_name):
        print('File "%s" not found!' % file_name)
        sys.exit(1)
    if not os.path.isfile(file_name):
        print('"%s" is not a file!' % file_name)
        sys.exit(1)

    if args.debug is not None:
        log_dir = 'LOGS'
        set_config_value('history_tracking', True)
        set_config_value('resume_notices', True)
        set_config_value('log_syntax_trees', set(['cst', 'ast']))  # don't use a set literal, here
    start_logging(log_dir)

    result, errors, _ = compile_src(file_name)

    if errors:
        cwd = os.getcwd()
        rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
        for error in errors:
            print(rel_path + ':' + str(error))
        sys.exit(1)
    else:
        print(result.serialize(how='default' if args.xml is None else 'xml')
              if isinstance(result, Node) else result)
