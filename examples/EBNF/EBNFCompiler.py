#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys

sys.path.extend(['..\\', '..\\..\\'])

try:
    import regex as re
except ImportError:
    import re
from DHParser import is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, \
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, Whitespace, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    forbid, assert_content, remove_infix_operator
from DHParser.log import logging


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def EBNFPreprocessor(text):
    return text

def get_preprocessor() -> PreprocessorFunc:
    return EBNFPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class EBNFGrammar(Grammar):
    r"""Parser for an EBNF source file, with this grammar:
    
    # EBNF-Grammar in EBNF
    
    @ comment    = /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
    @ whitespace = /\s*/                            # whitespace includes linefeed
    @ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
    
    syntax     = [~//] { definition | directive } §EOF
    definition = symbol §"=" expression
    directive  = "@" §symbol "=" ( regexp | literal | list_ )
    
    expression = term { "|" term }
    term       = { ["§"] factor }+                       # "§" means all following factors mandatory
    factor     = [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
               | [flowmarker] literal
               | [flowmarker] plaintext
               | [flowmarker] regexp
               | [flowmarker] whitespace
               | [flowmarker] oneormore
               | [flowmarker] group
               | [flowmarker] unordered
               | repetition
               | option
    
    flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
               | "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
    retrieveop = "::" | ":"                         # '::' pop, ':' retrieve
    
    group      = "(" §expression ")"
    unordered  = "<" §expression ">"                # elements of expression in arbitrary order
    oneormore  = "{" expression "}+"
    repetition = "{" §expression "}"
    option     = "[" §expression "]"
    
    symbol     = /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
    literal    = /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
               | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
    plaintext  = /`(?:[^"]|\\")*?`/~                # like literal but does not eat whitespace
    regexp     = /\/(?:\\\/|[^\/])*?\//~            # e.g. /\w+/, ~/#.*(?:\n|$)/~
    whitespace = /~/~                               # insignificant whitespace
    list_      = /\w+/~ { "," /\w+/~ }              # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                    # BEGIN_QUOTE, END_QUOTE ; see CommonMark/markdown.py for an exmaple
    EOF = !/./
    """
    expression = Forward()
    source_hash__ = "97b616756462a59e1f5162a95ae84c5f"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'#.*(?:\n|$)'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP_RE__
    wsp__ = Whitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('.'))
    list_ = Series(RegExp('\\w+'), wsp__, ZeroOrMore(Series(Series(Token(","), wsp__), RegExp('\\w+'), wsp__)))
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
    directive = Series(Series(Token("@"), wsp__), symbol, Series(Token("="), wsp__), Alternative(regexp, literal, list_), mandatory=1)
    definition = Series(symbol, Series(Token("="), wsp__), expression, mandatory=1)
    syntax = Series(Option(Series(wsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF, mandatory=2)
    root__ = syntax
    
def get_grammar() -> EBNFGrammar:
    global thread_local_EBNF_grammar_singleton
    try:
        grammar = thread_local_EBNF_grammar_singleton
    except NameError:
        thread_local_EBNF_grammar_singleton = EBNFGrammar()
        grammar = thread_local_EBNF_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

EBNF_AST_transformation_table = {
    # AST Transformations for EBNF-grammar
    "+":
        remove_expendables,
    "syntax":
        [],  # otherwise '"*": replace_by_single_child' would be applied
    "directive, definition":
        remove_tokens('@', '='),
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
    "list_":
        [flatten, remove_infix_operator],
    "*":
        replace_by_single_child
}


def EBNFTransform() -> TransformationDict:
    return partial(traverse, processing_table=EBNF_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_EBNF_transformer_singleton
    try:
        transformer = thread_local_EBNF_transformer_singleton
    except NameError:
        thread_local_EBNF_transformer_singleton = EBNFTransform()
        transformer = thread_local_EBNF_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class EBNFCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a EBNF source file.
    """

    def __init__(self, grammar_name="EBNF", grammar_source=""):
        super(EBNFCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_syntax(self, node):
        return node

    def on_definition(self, node):
        pass

    def on_directive(self, node):
        pass

    def on_expression(self, node):
        pass

    def on_term(self, node):
        pass

    def on_factor(self, node):
        pass

    def on_flowmarker(self, node):
        pass

    def on_retrieveop(self, node):
        pass

    def on_group(self, node):
        pass

    def on_oneormore(self, node):
        pass

    def on_repetition(self, node):
        pass

    def on_option(self, node):
        pass

    def on_symbol(self, node):
        pass

    def on_literal(self, node):
        pass

    def on_regexp(self, node):
        pass

    def on_list_(self, node):
        pass

    def on_EOF(self, node):
        pass


def get_compiler(grammar_name="EBNF", grammar_source="") -> EBNFCompiler:
    global thread_local_EBNF_compiler_singleton
    try:
        compiler = thread_local_EBNF_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_EBNF_compiler_singleton = \
            EBNFCompiler(grammar_name, grammar_source)
        compiler = thread_local_EBNF_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging("LOGS"):
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
        result, errors, ast = compile_src(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
            sys.exit(1)
        else:
            print(result.as_sxpr() if isinstance(result, Node) else result)
    else:
        print("Usage: EBNFCompiler.py [FILENAME]")
