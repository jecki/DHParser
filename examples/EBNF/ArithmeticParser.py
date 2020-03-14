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
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'../..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, Interleave, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_parent, optional_last_value


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def ArithmeticPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return ArithmeticPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ArithmeticGrammar(Grammar):
    r"""Parser for an Arithmetic source file.
    """
    expression = Forward()
    source_hash__ = "23d588c351da60bb265947d5314d13cc"
    anonymous__ = re.compile('..(?<=^)')
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
    group = Series(Series(Drop(Token("(")), dwsp__), expression, Series(Drop(Token(")")), dwsp__))
    sign = Alternative(Drop(Token("+")), Drop(Token("-")))
    factor = Series(Option(sign), Alternative(NUMBER, VARIABLE, group), ZeroOrMore(Alternative(VARIABLE, group)))
    term = Series(factor, ZeroOrMore(Series(Alternative(Series(Drop(Token("*")), dwsp__), Series(Drop(Token("/")), dwsp__)), factor)))
    expression.set(Series(term, ZeroOrMore(Series(Alternative(Series(Drop(Token("+")), dwsp__), Series(Drop(Token("-")), dwsp__)), term))))
    root__ = expression
    

def get_grammar() -> ArithmeticGrammar:
    """Returns a thread/process-exclusive ArithmeticGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.Arithmetic_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.Arithmetic_00000001_grammar_singleton = ArithmeticGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.Arithmetic_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.Arithmetic_00000001_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

Arithmetic_AST_transformation_table = {
    # AST Transformations for the Arithmetic-grammar
    "<": flatten,
    "expression": [],
    "term": [],
    "factor": [],
    "sign": [],
    "group": [],
    "NUMBER": [],
    "VARIABLE": [],
    "*": replace_by_single_child
}



def CreateArithmeticTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=Arithmetic_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
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
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
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

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
            set_config_value('history_tracking', True)
            set_config_value('resume_notices', True)
            set_config_value('log_syntax_trees', set(('cst', 'ast')))
        start_logging(log_dir)
        result, errors, _ = compile_src(file_name)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.serialize() if isinstance(result, Node) else result)
    else:
        print("Usage: ArithmeticParser.py [FILENAME]")
