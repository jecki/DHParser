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

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, is_insignificant_whitespace, is_empty, lean_left, \
    collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_children, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, access_thread_locals, get_config_value


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
    source_hash__ = "3d81c718b586fbd4490776d2cd4e3e53"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'#.*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    VARIABLE = RegExp('[a-dj-z]')
    NUMBER = RegExp('(?:0|(?:[1-9]\\d*))(?:\\.\\d+)?')
    MINUS = RegExp('-')
    PLUS = RegExp('\\+')
    i = Token("i")
    e = Token("e")
    pi = Alternative(Drop(Token("pi")), Drop(Token("π")))
    special = Alternative(pi, e)
    number = Synonym(NUMBER)
    log = Series(Series(Drop(Token('log(')), dwsp__), expression, Drop(Token(")")), mandatory=1)
    tan = Series(Series(Drop(Token('tan(')), dwsp__), expression, Drop(Token(")")), mandatory=1)
    cos = Series(Series(Drop(Token('cos(')), dwsp__), expression, Drop(Token(")")), mandatory=1)
    sin = Series(Series(Drop(Token('sin(')), dwsp__), expression, Drop(Token(")")), mandatory=1)
    function = Alternative(sin, cos, tan, log)
    group = Series(Drop(Token("(")), expression, Drop(Token(")")), mandatory=1)
    tail_value = Alternative(special, function, VARIABLE, group)
    tail_pow = Series(tail_value, Option(i), Drop(Token("^")), element)
    tail_elem = Alternative(tail_pow, tail_value)
    value = Series(Alternative(number, tail_value), Option(i))
    pow = Series(value, Drop(Token("^")), Option(sign), element)
    element.set(Alternative(pow, value))
    sign.set(Alternative(PLUS, MINUS))
    seq = Series(tail_elem, tail)
    tail.set(Series(Alternative(seq, tail_elem), Option(i)))
    factor = Series(Option(sign), Alternative(Series(Option(element), tail), element), dwsp__)
    div = Series(factor, Series(Drop(Token("/")), dwsp__), term)
    mul = Series(factor, Series(Drop(Token("*")), dwsp__), term)
    term.set(Alternative(mul, div, factor))
    sub = Series(term, Series(Drop(Token("-")), dwsp__), expression)
    add = Series(term, Series(Drop(Token("+")), dwsp__), expression)
    expression.set(Alternative(add, sub, term))
    root__ = expression
    

def get_grammar() -> ArithmeticRightRecursiveGrammar:
    """Returns a thread/process-exclusive ArithmeticRightRecursiveGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.ArithmeticRightRecursive_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.ArithmeticRightRecursive_00000001_grammar_singleton = ArithmeticRightRecursiveGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.ArithmeticRightRecursive_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.ArithmeticRightRecursive_00000001_grammar_singleton
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
        THREAD_LOCALS = access_thread_locals()
        transformer = THREAD_LOCALS.ArithmeticRightRecursive_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.ArithmeticRightRecursive_00000001_transformer_singleton = \
            ArithmeticRightRecursiveTransform()
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
