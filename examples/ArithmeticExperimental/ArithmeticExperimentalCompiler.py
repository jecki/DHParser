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

sys.path.extend(['../../', '../', './'])

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, \
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
    error_on, recompile_grammar, GLOBALS


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def ArithmeticExperimentalPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return ArithmeticExperimentalPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ArithmeticExperimentalGrammar(Grammar):
    r"""Parser for an ArithmeticExperimental source file.
    """
    element = Forward()
    expression = Forward()
    pow = Forward()
    sign = Forward()
    tail = Forward()
    term = Forward()
    source_hash__ = "275cee2bc98d92d9330bcc71dde3afe3"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'#.*'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    VARIABLE = RegExp('[a-dj-z]')
    NUMBER = RegExp('(?:0|(?:[1-9]\\d*))(?:\\.\\d+)?')
    MINUS = RegExp('-')
    PLUS = RegExp('\\+')
    imaginary = Token("i")
    e = Token("e")
    pi = Alternative(DropToken("pi"), DropToken("π"))
    special = Alternative(pi, e)
    number = Synonym(NUMBER)
    log = Series(Series(DropToken('log('), dwsp__), expression, DropToken(")"), mandatory=1)
    tan = Series(Series(DropToken('tan('), dwsp__), expression, DropToken(")"), mandatory=1)
    cos = Series(Series(DropToken('cos('), dwsp__), expression, DropToken(")"), mandatory=1)
    sin = Series(Series(DropToken('sin('), dwsp__), expression, DropToken(")"), mandatory=1)
    function = Alternative(sin, cos, tan, log)
    group = Series(DropToken("("), expression, DropToken(")"), mandatory=1)
    tail_value = Alternative(special, function, VARIABLE, group)
    tail_pow = Series(tail_value, DropToken("^"), pow)
    tail_elem = Alternative(tail_pow, tail_value)
    value = Series(Alternative(number, tail_value), Option(imaginary))
    pow.set(Series(value, DropToken("^"), Option(sign), element))
    element.set(Alternative(pow, value))
    sign.set(Alternative(PLUS, MINUS))
    seq = Series(tail_elem, tail)
    tail.set(Alternative(seq, tail_elem))
    factor = Series(Option(sign), Alternative(Series(Option(element), tail), element), dwsp__)
    div = Series(factor, Series(DropToken("/"), dwsp__), term)
    mul = Series(factor, Series(DropToken("*"), dwsp__), term)
    term.set(Alternative(mul, div, factor))
    sub = Series(term, Series(DropToken("-"), dwsp__), expression)
    add = Series(term, Series(DropToken("+"), dwsp__), expression)
    expression.set(Alternative(add, sub, term))
    root__ = expression
    
def get_grammar() -> ArithmeticExperimentalGrammar:
    global GLOBALS
    try:
        grammar = GLOBALS.ArithmeticExperimental_00000001_grammar_singleton
    except AttributeError:
        GLOBALS.ArithmeticExperimental_00000001_grammar_singleton = ArithmeticExperimentalGrammar()
        if hasattr(get_grammar, 'python_src__'):
            GLOBALS.ArithmeticExperimental_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = GLOBALS.ArithmeticExperimental_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


ArithmeticExperimental_AST_transformation_table = {
    # AST Transformations for the ArithmeticExperimental-grammar
    # "<": flatten_anonymous_nodes,
    "expression, term, sign, group, factor": [replace_by_single_child],
}


def ArithmeticExperimentalTransform() -> TransformationFunc:
    return partial(traverse, processing_table=ArithmeticExperimental_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    try:
        transformer = GLOBALS.ArithmeticExperimental_00000001_transformer_singleton
    except AttributeError:
        GLOBALS.ArithmeticExperimental_00000001_transformer_singleton = ArithmeticExperimentalTransform()
        transformer = GLOBALS.ArithmeticExperimental_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ArithmeticExperimentalCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ArithmeticExperimental source file.
    """

    def __init__(self):
        super(ArithmeticExperimentalCompiler, self).__init__()

    def _reset(self):
        super()._reset()
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


def get_compiler() -> ArithmeticExperimentalCompiler:
    try:
        compiler = GLOBALS.ArithmeticExperimental_00000001_compiler_singleton
    except AttributeError:
        GLOBALS.ArithmeticExperimental_00000001_compiler_singleton = ArithmeticExperimentalCompiler()
        compiler = GLOBALS.ArithmeticExperimental_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging(log_dir):
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
        print("Usage: ArithmeticExperimentalCompiler.py [FILENAME]")
