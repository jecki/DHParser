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
    source_hash__ = "9a341fad79f7e8eb46f1a657b553bec7"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'#.*(?:\n|$)'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('.'))
    whitespace = Series(RegExp('~'), dwsp__)
    regexp = Series(RegExp('/(?:(?<!\\\\)\\\\(?:/)|[^/])*?/'), dwsp__)
    plaintext = Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), dwsp__)
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), dwsp__), Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), dwsp__))
    symbol = Series(RegExp('(?!\\d)\\w+'), dwsp__)
    option = Series(Series(Token("["), dwsp__), expression, Series(Token("]"), dwsp__), mandatory=1)
    repetition = Series(Series(Token("{"), dwsp__), expression, Series(Token("}"), dwsp__), mandatory=1)
    oneormore = Series(Series(Token("{"), dwsp__), expression, Series(Token("}+"), dwsp__))
    unordered = Series(Series(Token("<"), dwsp__), expression, Series(Token(">"), dwsp__), mandatory=1)
    group = Series(Series(Token("("), dwsp__), expression, Series(Token(")"), dwsp__), mandatory=1)
    retrieveop = Alternative(Series(Token("::"), dwsp__), Series(Token(":"), dwsp__))
    flowmarker = Alternative(Series(Token("!"), dwsp__), Series(Token("&"), dwsp__), Series(Token("-!"), dwsp__), Series(Token("-&"), dwsp__))
    factor = Alternative(Series(Option(flowmarker), Option(retrieveop), symbol, NegativeLookahead(Series(Token("="), dwsp__))), Series(Option(flowmarker), literal), Series(Option(flowmarker), plaintext), Series(Option(flowmarker), regexp), Series(Option(flowmarker), whitespace), Series(Option(flowmarker), oneormore), Series(Option(flowmarker), group), Series(Option(flowmarker), unordered), repetition, option)
    term = OneOrMore(Series(Option(Series(Token("§"), dwsp__)), factor))
    expression.set(Series(term, ZeroOrMore(Series(Series(Token("|"), dwsp__), term))))
    directive = Series(Series(Token("@"), dwsp__), symbol, Series(Token("="), dwsp__), Alternative(regexp, literal, symbol), ZeroOrMore(Series(Series(Token(","), dwsp__), Alternative(regexp, literal, symbol))), mandatory=1)
    definition = Series(symbol, Series(Token("="), dwsp__), expression, mandatory=1)
    syntax = Series(Option(Series(dwsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF, mandatory=2)
    root__ = syntax
    
def get_grammar() -> EBNFGrammar:
    """Returns a thread/process-exclusive EBNFGrammar-singleton."""
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
    # AST Transformations for EBNF-grammar
    "<":
        [remove_empty, remove_whitespace],
    "syntax":
        [],  # otherwise '"*": replace_by_single_child' would be applied
    "directive, definition":
        [flatten, remove_tokens('@', '=', ',')],
    "expression":
        [replace_by_single_child, flatten, remove_tokens('|')],  # remove_infix_operator],
    "term":
        [replace_by_single_child, flatten],  # supports both idioms:
                                             # "{ factor }+" and "factor { factor }"
    "factor, flowmarker, retrieveop":
        replace_by_single_child,
    "group":
        [remove_brackets, replace_by_single_child],
    "unordered":
        remove_brackets,
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets,
         forbid('repetition', 'option', 'oneormore'), assert_content(r'(?!§)(?:.|\n)*')],
    "symbol, literal, regexp":
        reduce_single_child,
    (TOKEN_PTYPE, WHITESPACE_PTYPE):
        reduce_single_child,
    # "list_":
    #     [flatten, remove_infix_operator],
    "*":
        replace_by_single_child
}

def EBNFTransform() -> TransformationFunc:
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
