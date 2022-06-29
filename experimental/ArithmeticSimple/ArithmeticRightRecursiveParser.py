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

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../examples', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, \
    collapse, collapse_children_if, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_children, remove_content, remove_brackets, change_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, content_matches, apply_if, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    forbid, assert_content, remove_infix_operator, resume_notices_on, THREAD_LOCALS, \
    error_on, recompile_grammar, left_associative, lean_left, access_thread_locals, \
    get_config_value, ThreadLocalSingletonFactory, set_tracer, trace_history


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def ArithmeticRightRecursivePreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return ArithmeticRightRecursivePreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ArithmeticRightRecursiveGrammar(Grammar):
    r"""Parser for an ArithmeticRightRecursive source file.
    """
    expression = Forward()
    term = Forward()
    source_hash__ = "c26bf1eb08a888559f192b19514bc772"
    disposable__ = re.compile('..(?<=^)')
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
    group = Series(Series(Drop(Text("(")), dwsp__), expression, Series(Drop(Text(")")), dwsp__))
    sign = Alternative(POSITIVE, NEGATIVE)
    factor = Series(Option(sign), Alternative(NUMBER, VARIABLE, group))
    div = Series(factor, Series(Drop(Text("/")), dwsp__), term)
    mul = Series(factor, Series(Drop(Text("*")), dwsp__), term)
    add = Series(term, Series(Drop(Text("+")), dwsp__), expression)
    sub = Series(term, Series(Drop(Text("-")), dwsp__), expression)
    term.set(Alternative(mul, div, factor))
    expression.set(Alternative(add, sub, term))
    root__ = expression
    

_raw_grammar = ThreadLocalSingletonFactory(ArithmeticRightRecursiveGrammar, ident=1)

def get_grammar() -> ArithmeticRightRecursiveGrammar:
    grammar = _raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
    
def parse_ArithmeticRightRecursive(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

ArithmeticRightRecursive_AST_transformation_table = {
    # AST Transformations for the ArithmeticRightRecursive-grammar
    "sign, factor, term, expression": [replace_by_single_child],
    "add, sub": [lean_left({'sub', 'add'})],
    "mul, div": [lean_left({'mul', 'div'})],
}


def CreateArithmeticRightRecursiveTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    def transformation_func(cst: Node, pass_1, pass_2):
        """Special transformation function requires two passes, because
        otherwise elimination of grouping nodes (pass 2) would interfere
        with the adjustment of the tree structure to the left-associativity
        of the `add`, `sub`, `mul` and `div` operators."""
        traverse(cst, pass_1)
        traverse(cst, pass_2)
    return partial(transformation_func,
                   pass_1=ArithmeticRightRecursive_AST_transformation_table.copy(),
                   pass_2={'group': [replace_by_single_child]}.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    try:
        THREAD_LOCALS = access_thread_locals()
        transformer = THREAD_LOCALS.ArithmeticRightRecursive_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.ArithmeticRightRecursive_00000001_transformer_singleton = \
            CreateArithmeticRightRecursiveTransformer()
        transformer = THREAD_LOCALS.ArithmeticRightRecursive_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ArithmeticRightRecursiveCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ArithmeticRightRecursive source file.
    """

    def __init__(self):
        super(ArithmeticRightRecursiveCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_expression(self, node):
        return self.fallback_compiler(node)

    # def on_add(self, node):
    #     return node

    # def on_sub(self, node):
    #     return node

    # def on_term(self, node):
    #     return node

    # def on_mul(self, node):
    #     return node

    # def on_div(self, node):
    #     return node

    # def on_factor(self, node):
    #     return node

    # def on_sign(self, node):
    #     return node

    # def on_group(self, node):
    #     return node

    # def on_POSITIVE(self, node):
    #     return node

    # def on_NEGATIVE(self, node):
    #     return node

    # def on_NUMBER(self, node):
    #     return node

    # def on_VARIABLE(self, node):
    #     return node


def get_compiler() -> ArithmeticRightRecursiveCompiler:
    """Returns a thread/process-exclusive ArithmeticRightRecursiveCompiler-singleton."""
    try:
        compiler = THREAD_LOCALS.ArithmeticRightRecursive_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.ArithmeticRightRecursive_00000001_compiler_singleton = ArithmeticRightRecursiveCompiler()
        compiler = THREAD_LOCALS.ArithmeticRightRecursive_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    start_logging(log_dir)
    compiler = get_compiler()
    cname = compiler.__class__.__name__
    result_tuple = compile_source(source, get_preprocessor(),
                                  get_grammar(),
                                  get_transformer(), compiler)
    return result_tuple


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False,
                                  notify=lambda:print('recompiling ' + grammar_path)):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        result, errors, ast = compile_src(file_name, log_dir)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: ArithmeticRightRecursiveParser.py [FILENAME]")
