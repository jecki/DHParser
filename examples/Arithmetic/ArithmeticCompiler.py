#!/usr/bin/python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

sys.path.extend([os.path.join('..', '..'), '..', '.'])

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, DropWhitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, DropToken, Synonym, AllOf, SomeOf, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, is_insignificant_whitespace, is_empty, \
    collapse, collapse_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, left_associative, access_thread_locals


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
    source_hash__ = "b75119067b29e37cd0bfe66facbcad22"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'#.*'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    VARIABLE = Series(RegExp('[A-Za-z]'), dwsp__)
    NUMBER = Series(RegExp('(?:0|(?:[1-9]\\d*))(?:\\.\\d+)?'), dwsp__)
    NEGATIVE = RegExp('[-]')
    POSITIVE = RegExp('[+]')
    DIV = Series(Token("/"), dwsp__)
    MUL = Series(Token("*"), dwsp__)
    MINUS = Series(Token("-"), dwsp__)
    PLUS = Series(Token("+"), dwsp__)
    group = Series(Series(DropToken("("), dwsp__), expression, Series(DropToken(")"), dwsp__))
    sign = Alternative(POSITIVE, NEGATIVE)
    factor = Series(Option(sign), Alternative(NUMBER, VARIABLE, group), ZeroOrMore(Alternative(VARIABLE, group)))
    term = Series(factor, ZeroOrMore(Series(Alternative(DIV, MUL), factor)))
    expression.set(Series(term, ZeroOrMore(Series(Alternative(PLUS, MINUS), term))))
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
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def group_no_asterix_mul(context):
    pass
    # TODO: Find an algorithm, here

Arithmetic_AST_transformation_table = {
    # AST Transformations for the Arithmetic-grammar
    "expression, term": [left_associative, replace_by_single_child],
    "factor, sign": replace_by_single_child,
    "group": [remove_tokens('(', ')'), replace_by_single_child],
}


def ArithmeticTransform() -> TransformationFunc:
    return partial(traverse, processing_table=Arithmetic_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    try:
        THREAD_LOCALS = access_thread_locals()
        transformer = THREAD_LOCALS.Arithmetic_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Arithmetic_00000001_transformer_singleton = ArithmeticTransform()
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

    # def on_NUMBER(self, node):
    #     return node

    # def on_VARIABLE(self, node):
    #     return node


def get_compiler() -> ArithmeticCompiler:
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
    grammar_path = os.path.abspath(__file__).replace('Compiler.py', '.ebnf')
    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False,
                                  notify=lambda:print('recompiling ' + grammar_path)):
            error_file = os.path.basename(__file__).replace('Compiler.py', '_ebnf_ERRORS.txt')
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
        print("Usage: ArithmeticCompiler.py [FILENAME]")
