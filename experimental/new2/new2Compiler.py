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
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    grammar_changed


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def new2Preprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return new2Preprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class new2Grammar(Grammar):
    r"""Parser for a new2 source file, with this grammar:

    document = ~ { sentence } §EOF
    sentence = part {"," part } "."
    part     = { WORD }+
    WORD     =  /[\w’]+/~
    EOF      =  !/./
    """
    source_hash__ = "7a9984368b1c959222099d389d18c54f"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r''
    WHITESPACE__ = r'\s*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    whitespace__ = Whitespace(WSP__)
    EOF = NegativeLookahead(RegExp('.'))
    WORD = RE('[\\w’]+')
    part = OneOrMore(WORD)
    sentence = Series(part, ZeroOrMore(Series(Token(","), part)), Token("."))
    document = Series(whitespace__, ZeroOrMore(sentence), EOF, mandatory=2)
    root__ = document

def get_grammar() -> new2Grammar:
    global thread_local_new2_grammar_singleton
    try:
        grammar = thread_local_new2_grammar_singleton
    except NameError:
        thread_local_new2_grammar_singleton = new2Grammar()
        grammar = thread_local_new2_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

new2_AST_transformation_table = {
    # AST Transformations for the new2-grammar
    "+": remove_empty,
    "document": [remove_whitespace, reduce_single_child],
    "sentence": [flatten],
    "part": [],
    "WORD": [remove_whitespace, reduce_single_child],
    "EOF": [],
    ":Token": [remove_whitespace, reduce_single_child],
    ":RE": reduce_single_child,
    "*": replace_by_single_child
}


def new2Transform() -> TransformationDict:
    return partial(traverse, processing_table=new2_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_new2_transformer_singleton
    try:
        transformer = thread_local_new2_transformer_singleton
    except NameError:
        thread_local_new2_transformer_singleton = new2Transform()
        transformer = thread_local_new2_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class new2Compiler(Compiler):
    """Compiler for the abstract-syntax-tree of a new2 source file.
    """

    def __init__(self, grammar_name="new2", grammar_source=""):
        super(new2Compiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_document(self, node):
        return self.fallback_compiler(node)

    # def on_WORD(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler(grammar_name="new2", grammar_source="") -> new2Compiler:
    global thread_local_new2_compiler_singleton
    try:
        compiler = thread_local_new2_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_new2_compiler_singleton = \
            new2Compiler(grammar_name, grammar_source)
        compiler = thread_local_new2_compiler_singleton
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
            if grammar_changed(new2Grammar, grammar_file_name):
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
        print("Usage: new2Compiler.py [FILENAME]")
