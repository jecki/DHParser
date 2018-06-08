#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys

sys.path.append(r'/home/eckhart/Entwicklung/DHParser')

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, remove_anonymous_tokens, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def wsPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return wsPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class wsGrammar(Grammar):
    r"""Parser for a ws source file, with this grammar:
    
    # ws-grammar
    
    #######################################################################
    #
    #  EBNF-Directives
    #
    #######################################################################
    
    @ whitespace  = vertical        # implicit whitespace, includes any number of line feeds
    @ literalws   = right           # literals have implicit whitespace on the right hand side
    @ comment     = /#.*/           # comments range from a '#'-character to the end of the line
    @ ignorecase  = False           # literals and regular expressions are case-sensitive
    
    
    #######################################################################
    #
    #  Structure and Components
    #
    #######################################################################
    
    document = ~ { WORD } §EOF    # root parser: a sequence of words preceded by whitespace
                                    # until the end of file
    
    #######################################################################
    #
    #  Regular Expressions
    #
    #######################################################################
    
    WORD     =  /\w+/ ~     # a sequence of letters, optional trailing whitespace
    EOF      =  !/./        # no more characters ahead, end of file reached
    """
    source_hash__ = "35e8b695c47d625c91a181d455b75ed9"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'#.*'
    WHITESPACE__ = r'\s*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    whitespace__ = Whitespace(WSP__)
    EOF = NegativeLookahead(RegExp('.'))
    WORD = Series(RegExp('\\w+'), whitespace__)
    document = Series(whitespace__, ZeroOrMore(WORD), EOF, mandatory=2)
    root__ = document
    
def get_grammar() -> wsGrammar:
    global thread_local_ws_grammar_singleton
    try:
        grammar = thread_local_ws_grammar_singleton
    except NameError:
        thread_local_ws_grammar_singleton = wsGrammar()
        grammar = thread_local_ws_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

ws_AST_transformation_table = {
    # AST Transformations for the ws-grammar
    "+": remove_empty,
    "document": [],
    "WORD": [],
    "EOF": [],
    ":Token, :RE": reduce_single_child,
    "*": replace_by_single_child
}


def wsTransform() -> TransformationDict:
    return partial(traverse, processing_table=ws_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_ws_transformer_singleton
    try:
        transformer = thread_local_ws_transformer_singleton
    except NameError:
        thread_local_ws_transformer_singleton = wsTransform()
        transformer = thread_local_ws_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class wsCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ws source file.
    """

    def __init__(self, grammar_name="ws", grammar_source=""):
        super(wsCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def _reset(self):
        super()._reset()
        # initialize your variables here, not in the constructor!
    def on_document(self, node):
        return self.fallback_compiler(node)

    # def on_WORD(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler(grammar_name="ws", grammar_source="") -> wsCompiler:
    global thread_local_ws_compiler_singleton
    try:
        compiler = thread_local_ws_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_ws_compiler_singleton = \
            wsCompiler(grammar_name, grammar_source)
        compiler = thread_local_ws_compiler_singleton
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
            if grammar_changed(wsGrammar, grammar_file_name):
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
        print("Usage: wsCompiler.py [FILENAME]")
