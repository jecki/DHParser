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
    remove_empty, remove_tokens, flatten, is_insignificant_whitespace, is_empty, lean_left, \
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
    element = Forward()
    expression = Forward()
    sign = Forward()
    tail = Forward()
    term = Forward()
    source_hash__ = "57a303f28ffb50a84b86e98c71ea2e32"
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
    i = Token("i")
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
    tail_pow = Series(tail_value, Option(i), DropToken("^"), element)
    tail_elem = Alternative(tail_pow, tail_value)
    value = Series(Alternative(number, tail_value), Option(i))
    pow = Series(value, DropToken("^"), Option(sign), element)
    element.set(Alternative(pow, value))
    sign.set(Alternative(PLUS, MINUS))
    seq = Series(tail_elem, tail)
    tail.set(Series(Alternative(seq, tail_elem), Option(i)))
    factor = Series(Option(sign), Alternative(Series(Option(element), tail), element), dwsp__)
    div = Series(factor, Series(DropToken("/"), dwsp__), term)
    mul = Series(factor, Series(DropToken("*"), dwsp__), term)
    term.set(Alternative(mul, div, factor))
    sub = Series(term, Series(DropToken("-"), dwsp__), expression)
    add = Series(term, Series(DropToken("+"), dwsp__), expression)
    expression.set(Alternative(add, sub, term))
    root__ = expression
    
def get_grammar() -> ArithmeticRightRecursiveGrammar:
    """Returns a thread/process-exclusive ArithmeticRightRecursiveGrammar-singleton."""
    try:
        grammar = GLOBALS.ArithmeticRightRecursive_00000001_grammar_singleton
    except AttributeError:
        GLOBALS.ArithmeticRightRecursive_00000001_grammar_singleton = ArithmeticRightRecursiveGrammar()
        if hasattr(get_grammar, 'python_src__'):
            GLOBALS.ArithmeticRightRecursive_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = GLOBALS.ArithmeticRightRecursive_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


ArithmeticRightRecursive_AST_transformation_table = {
    # AST Transformations for the ArithmeticRightRecursive-grammar
    # "<": flatten_anonymous_nodes,
    "special, number, function, tail_value, tail_elem, tail, value, "
    "element, factor, term, expression":
        [replace_by_single_child],
    "pi": [replace_content_by('π')],
    "tail_pow": [change_tag_name('pow')],
    "add, sub": [lean_left({'sub', 'add'})],
    "mul, div": [lean_left({'mul', 'div'})]
}


def ArithmeticRightRecursiveTransform() -> TransformationFunc:
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
    try:
        transformer = GLOBALS.ArithmeticRightRecursive_00000001_transformer_singleton
    except AttributeError:
        GLOBALS.ArithmeticRightRecursive_00000001_transformer_singleton = \
            ArithmeticRightRecursiveTransform()
        transformer = GLOBALS.ArithmeticRightRecursive_00000001_transformer_singleton
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


def get_compiler() -> ArithmeticRightRecursiveCompiler:
    try:
        compiler = GLOBALS.ArithmeticRightRecursive_00000001_compiler_singleton
    except AttributeError:
        GLOBALS.ArithmeticRightRecursive_00000001_compiler_singleton = ArithmeticRightRecursiveCompiler()
        compiler = GLOBALS.ArithmeticRightRecursive_00000001_compiler_singleton
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
        print("Usage: ArithmeticRightRecursiveCompiler.py [FILENAME]")
