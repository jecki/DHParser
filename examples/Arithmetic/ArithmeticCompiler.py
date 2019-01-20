#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys

sys.path.extend(['../../', '../', './'])

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, \
    traverse, remove_children_if, is_anonymous, Whitespace, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip


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
    constant = Forward()
    digit = Forward()
    expression = Forward()
    variable = Forward()
    source_hash__ = "120070baa84f5a2bd1bbb900627078fc"
    parser_initialization__ = "upon instantiation"
    resume_rules__ = {}
    COMMENT__ = r''
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    test = Series(digit, constant, variable)
    digit.set(Alternative(Series(Token("0"), wsp__), Series(Token("1"), wsp__), Series(Token("..."), wsp__), Series(Token("9"), wsp__)))
    constant.set(Series(digit, ZeroOrMore(digit)))
    variable.set(Alternative(Series(Token("x"), wsp__), Series(Token("y"), wsp__), Series(Token("z"), wsp__)))
    factor = Alternative(constant, variable, Series(Series(Token("("), wsp__), expression, Series(Token(")"), wsp__)))
    term = Series(factor, ZeroOrMore(Series(Alternative(Series(Token("*"), wsp__), Series(Token("/"), wsp__)), factor)))
    expression.set(Series(term, ZeroOrMore(Series(Alternative(Series(Token("+"), wsp__), Series(Token("-"), wsp__)), term))))
    root__ = expression
    
def get_grammar() -> ArithmeticGrammar:
    global GLOBALS
    try:
        grammar = GLOBALS.Arithmetic_00000001_grammar_singleton
    except AttributeError:
        GLOBALS.Arithmetic_00000001_grammar_singleton = ArithmeticGrammar()
        if hasattr(get_grammar, 'python_src__'):
            GLOBALS.Arithmetic_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = GLOBALS.Arithmetic_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

Arithmetic_AST_transformation_table = {
    # AST Transformations for the Arithmetic-grammar
    "<": remove_empty,
    "expression": [],
    "term": [],
    "factor": [replace_or_reduce],
    "variable": [replace_or_reduce],
    "constant": [],
    "digit": [replace_or_reduce],
    "test": [],
    ":_Token, :_RE": reduce_single_child,
    "*": replace_by_single_child
}


def ArithmeticTransform() -> TransformationDict:
    return partial(traverse, processing_table=Arithmetic_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_Arithmetic_transformer_singleton
    try:
        transformer = thread_local_Arithmetic_transformer_singleton
    except NameError:
        thread_local_Arithmetic_transformer_singleton = ArithmeticTransform()
        transformer = thread_local_Arithmetic_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ArithmeticCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Arithmetic source file.
    """

    def on_expression(self, node):
        return node

    # def on_term(self, node):
    #     return node

    # def on_factor(self, node):
    #     return node

    # def on_variable(self, node):
    #     return node

    # def on_constant(self, node):
    #     return node

    # def on_digit(self, node):
    #     return node

    # def on_test(self, node):
    #     return node


def get_compiler() -> ArithmeticCompiler:
    global thread_local_Arithmetic_compiler_singleton
    try:
        compiler = thread_local_Arithmetic_compiler_singleton
    except NameError:
        thread_local_Arithmetic_compiler_singleton = ArithmeticCompiler()
        compiler = thread_local_Arithmetic_compiler_singleton
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
        log_file_name = os.path.basename(os.path.splitext(source)[0]) \
            if is_filename(source) < 0 else cname[:cname.find('.')] + '_out'
        result = compile_source(source, get_preprocessor(),
                                get_grammar(),
                                get_transformer(), compiler)
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
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
