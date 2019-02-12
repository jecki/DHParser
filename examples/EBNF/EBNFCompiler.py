#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

sys.path.append(r'/home/eckhart/Entwicklung/DHParser')

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
    remove_children_if, move_whitespace, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, is_empty, \
    is_expendable, collapse, collapse_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    flatten_anonymous_nodes, error_on, recompile_grammar, GLOBALS


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def EBNFPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return EBNFPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class EBNFGrammar(Grammar):
    r"""Parser for an EBNF source file.
    """
    expression = Forward()
    source_hash__ = "a7119a157d38270e4215972858d0b930"
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'#.*(?:\n|$)'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('.'))
    whitespace = Series(RegExp('~'), wsp__)
    regexp = Series(RegExp('/(?:\\\\/|[^/])*?/'), wsp__)
    plaintext = Series(RegExp('`(?:[^"]|\\\\")*?`'), wsp__)
    literal = Alternative(Series(RegExp('"(?:[^"]|\\\\")*?"'), wsp__), Series(RegExp("'(?:[^']|\\\\')*?'"), wsp__))
    symbol = Series(RegExp('(?!\\d)\\w+'), wsp__)
    option = Series(Series(Token("["), wsp__), expression, Series(Token("]"), wsp__), mandatory=1)
    repetition = Series(Series(Token("{"), wsp__), expression, Series(Token("}"), wsp__), mandatory=1)
    oneormore = Series(Series(Token("{"), wsp__), expression, Series(Token("}+"), wsp__))
    unordered = Series(Series(Token("<"), wsp__), expression, Series(Token(">"), wsp__), mandatory=1)
    group = Series(Series(Token("("), wsp__), expression, Series(Token(")"), wsp__), mandatory=1)
    retrieveop = Alternative(Series(Token("::"), wsp__), Series(Token(":"), wsp__))
    flowmarker = Alternative(Series(Token("!"), wsp__), Series(Token("&"), wsp__), Series(Token("-!"), wsp__), Series(Token("-&"), wsp__))
    factor = Alternative(Series(Option(flowmarker), Option(retrieveop), symbol, NegativeLookahead(Series(Token("="), wsp__))), Series(Option(flowmarker), literal), Series(Option(flowmarker), plaintext), Series(Option(flowmarker), regexp), Series(Option(flowmarker), whitespace), Series(Option(flowmarker), oneormore), Series(Option(flowmarker), group), Series(Option(flowmarker), unordered), repetition, option)
    term = OneOrMore(Series(Option(Series(Token("§"), wsp__)), factor))
    expression.set(Series(term, ZeroOrMore(Series(Series(Token("|"), wsp__), term))))
    directive = Series(Series(Token("@"), wsp__), symbol, Series(Token("="), wsp__), Alternative(regexp, literal, symbol), ZeroOrMore(Series(Series(Token(","), wsp__), Alternative(regexp, literal, symbol))), mandatory=1)
    definition = Series(symbol, Series(Token("="), wsp__), expression, mandatory=1)
    syntax = Series(Option(Series(wsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF, mandatory=2)
    root__ = syntax
    
def get_grammar() -> EBNFGrammar:
    global GLOBALS
    try:
        grammar = GLOBALS.EBNF_00000001_grammar_singleton
    except AttributeError:
        GLOBALS.EBNF_00000001_grammar_singleton = EBNFGrammar()
        if hasattr(get_grammar, 'python_src__'):
            GLOBALS.EBNF_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = GLOBALS.EBNF_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

EBNF_AST_transformation_table = {
    # AST Transformations for the EBNF-grammar
    "<": flatten_anonymous_nodes,
    "syntax": [],
    "definition": [],
    "directive": [],
    "expression": [],
    "term": [],
    "factor": [],
    "flowmarker": [],
    "retrieveop": [],
    "group": [],
    "unordered": [],
    "oneormore": [],
    "repetition": [],
    "option": [],
    "symbol": [],
    "literal": [],
    "plaintext": [],
    "regexp": [],
    "whitespace": [],
    "EOF": []
}

def EBNFTransform() -> TransformationDict:
    return partial(traverse, processing_table=EBNF_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    try:
        transformer = GLOBALS.EBNF_00000001_transformer_singleton
    except AttributeError:
        GLOBALS.EBNF_00000001_transformer_singleton = EBNFTransform()
        transformer = GLOBALS.EBNF_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class EBNFCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a EBNF source file.
    """

    def __init__(self):
        super(EBNFCompiler, self).__init__()

    def _reset(self):
        super()._reset()
        # initialize your variables here, not in the constructor!
    def on_syntax(self, node):
        return self.fallback_compiler(node)

    # def on_definition(self, node):
    #     return node

    # def on_directive(self, node):
    #     return node

    # def on_expression(self, node):
    #     return node

    # def on_term(self, node):
    #     return node

    # def on_factor(self, node):
    #     return node

    # def on_flowmarker(self, node):
    #     return node

    # def on_retrieveop(self, node):
    #     return node

    # def on_group(self, node):
    #     return node

    # def on_unordered(self, node):
    #     return node

    # def on_oneormore(self, node):
    #     return node

    # def on_repetition(self, node):
    #     return node

    # def on_option(self, node):
    #     return node

    # def on_symbol(self, node):
    #     return node

    # def on_literal(self, node):
    #     return node

    # def on_plaintext(self, node):
    #     return node

    # def on_regexp(self, node):
    #     return node

    # def on_whitespace(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler() -> EBNFCompiler:
    try:
        compiler = GLOBALS.EBNF_00000001_compiler_singleton
    except AttributeError:
        GLOBALS.EBNF_00000001_compiler_singleton = EBNFCompiler()
        compiler = GLOBALS.EBNF_00000001_compiler_singleton
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
        print("Usage: EBNFCompiler.py [FILENAME]")
