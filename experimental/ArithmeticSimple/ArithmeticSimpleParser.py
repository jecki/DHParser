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

from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym,\
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, is_empty, \
    collapse, collapse_children_if, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_children, remove_content, remove_brackets, change_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, content_matches, apply_if, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    forbid, assert_content, remove_infix_operator, ThreadLocalSingletonFactory, \
    error_on, recompile_grammar, left_associative, access_thread_locals, get_config_value, re


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def ArithmeticSimplePreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return ArithmeticSimplePreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ArithmeticSimpleGrammar(Grammar):
    r"""Parser for an ArithmeticSimple source file.
    """
    expression = Forward()
    source_hash__ = "b71be6a6745f20dda18beebbda77902b"
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
    div = Series(Text("/"), dwsp__)
    mul = Series(Text("*"), dwsp__)
    sub = Series(Text("-"), dwsp__)
    add = Series(Text("+"), dwsp__)
    group = Series(Series(Drop(Text("(")), dwsp__), expression, Series(Drop(Text(")")), dwsp__))
    sign = Alternative(POSITIVE, NEGATIVE)
    factor = Series(Option(sign), Alternative(NUMBER, VARIABLE, group))
    term = Series(factor, ZeroOrMore(Series(Alternative(div, mul), factor)))
    expression.set(Series(term, ZeroOrMore(Series(Alternative(add, sub), term))))
    root__ = expression
    

_raw_grammar = ThreadLocalSingletonFactory(ArithmeticSimpleGrammar, ident=1)

def get_grammar() -> ArithmeticSimpleGrammar:
    grammar = _raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
    
def parse_ArithmeticSimple(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def group_no_asterix_mul(context):
    pass
    # TODO: Find an algorithm, here

ArithmeticSimple_AST_transformation_table = {
    # AST Transformations for the ArithmeticSimple-grammar
    "expression, term": [left_associative, replace_by_single_child],
    "factor, sign": replace_by_single_child,
    "group": [replace_by_single_child],
}


def ArithmeticSimpleTransform() -> TransformationFunc:
    return partial(traverse, transformation_table=ArithmeticSimple_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    try:
        THREAD_LOCALS = access_thread_locals()
        transformer = THREAD_LOCALS.ArithmeticSimple_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.ArithmeticSimple_00000001_transformer_singleton = ArithmeticSimpleTransform()
        transformer = THREAD_LOCALS.ArithmeticSimple_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ArithmeticSimpleCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ArithmeticSimple source file.
    """

    def __init__(self):
        super(ArithmeticSimpleCompiler, self).__init__()

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


def get_compiler() -> ArithmeticSimpleCompiler:
    try:
        compiler = THREAD_LOCALS.ArithmeticSimple_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.ArithmeticSimple_00000001_compiler_singleton = ArithmeticSimpleCompiler()
        compiler = THREAD_LOCALS.ArithmeticSimple_00000001_compiler_singleton
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
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_MESSAGES.txt')
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
        print("Usage: ArithmeticSimpleParser.py [FILENAME]")
