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

sys.path.append(r'C:\Users\di68kap\PycharmProjects\DHParser')

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, transformation_factory, \
    traverse, remove_children_if, merge_children, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, remove_anonymous_tokens, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def EBNF_oldPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return EBNF_oldPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class EBNF_oldGrammar(Grammar):
    r"""Parser for an EBNF_old source file, with this grammar:
    
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
    regexp     = /~?\/(?:\\\/|[^\/])*?\/~?/~        # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                    # '~' is a whitespace-marker, if present leading or trailing
                                                    # whitespace of a regular expression will be ignored tacitly.
    whitespace = /~/~                               # implicit or default whitespace
    list_      = /\w+/~ { "," /\w+/~ }              # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                    # BEGIN_QUOTE, END_QUOTE ; see CommonMark/markdown.py for an exmaple
    EOF = !/./
    """
    expression = Forward()
    source_hash__ = "876bb760b35a20924a3ee449820f4316"
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
    regexp = Series(RegExp('~?/(?:\\\\/|[^/])*?/~?'), wsp__)
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
    
def get_grammar() -> EBNF_oldGrammar:
    global thread_local_EBNF_old_grammar_singleton
    try:
        grammar = thread_local_EBNF_old_grammar_singleton
    except NameError:
        thread_local_EBNF_old_grammar_singleton = EBNF_oldGrammar()
        grammar = thread_local_EBNF_old_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

EBNF_old_AST_transformation_table = {
    # AST Transformations for the EBNF_old-grammar
    "+": remove_empty,
    "syntax": [],
    "definition": [],
    "directive": [],
    "expression": [],
    "term": [],
    "factor": [replace_or_reduce],
    "flowmarker": [replace_or_reduce],
    "retrieveop": [replace_or_reduce],
    "group": [],
    "unordered": [],
    "oneormore": [],
    "repetition": [],
    "option": [],
    "symbol": [],
    "literal": [replace_or_reduce],
    "plaintext": [],
    "regexp": [],
    "whitespace": [],
    "list_": [],
    "EOF": [],
    ":Token": reduce_single_child,
    "*": replace_by_single_child
}


def EBNF_oldTransform() -> TransformationDict:
    return partial(traverse, processing_table=EBNF_old_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_EBNF_old_transformer_singleton
    try:
        transformer = thread_local_EBNF_old_transformer_singleton
    except NameError:
        thread_local_EBNF_old_transformer_singleton = EBNF_oldTransform()
        transformer = thread_local_EBNF_old_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class EBNF_oldCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a EBNF_old source file.
    """

    def __init__(self, grammar_name="EBNF_old", grammar_source=""):
        super(EBNF_oldCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

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

    # def on_list_(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler(grammar_name="EBNF_old", grammar_source="") -> EBNF_oldCompiler:
    global thread_local_EBNF_old_compiler_singleton
    try:
        compiler = thread_local_EBNF_old_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_EBNF_old_compiler_singleton = \
            EBNF_oldCompiler(grammar_name, grammar_source)
        compiler = thread_local_EBNF_old_compiler_singleton
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
        try:
            grammar_file_name = os.path.basename(__file__).replace('Compiler.py', '.ebnf')
            if grammar_changed(EBNF_oldGrammar, grammar_file_name):
                print("Grammar has changed. Please recompile Grammar first.")
                sys.exit(1)
        except FileNotFoundError:
            print('Could not check for changed grammar, because grammar file "%s" was not found!'
                  % grammar_file_name)    
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
        print("Usage: EBNF_oldCompiler.py [FILENAME]")
