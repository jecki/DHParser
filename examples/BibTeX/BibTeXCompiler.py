#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys
try:
    import regex as re
except ImportError:
    import re

sys.path.extend(['../../', '../', './'])

from DHParser import is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, \
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationDict, Whitespace, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, remove_nodes, remove_content, remove_brackets, replace_parser, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    WHITESPACE_PTYPE, TOKEN_PTYPE
from DHParser.transform import TransformationFunc
from DHParser.log import logging


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def BibTeXPreprocessor(text):
    return text

def get_preprocessor() -> PreprocessorFunc:
    return BibTeXPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class BibTeXGrammar(Grammar):
    r"""Parser for a BibTeX source file, with this grammar:
    
    # BibTeX-Grammar
    
    
    #######################################################################
    #
    #  EBNF-Directives
    #
    ######################################################################
    
    @ whitespace  = /\s*/
    @ ignorecase  = True
    @ comment     = /%.*(?:\n|$)/
    
    
    #######################################################################
    #
    #  Bib-file Structure and Components
    #
    #######################################################################
    
    bibliography = { preamble | comment | entry }
    
    preamble      = "@Preamble{" /"/ pre_code /"/~ §"}"
    pre_code      = { /[^"%]+/ | /%.*\n/ }
    
    comment       = "@Comment{" text §"}"
    
    entry         = /@/ type "{" key { "," field §"=" content } §"}"
    type          = WORD
    key           = NO_BLANK_STRING
    field         = WORD_
    content       = "{" text "}" | plain_content
    
    plain_content = COMMA_TERMINATED_STRING
    text          = { CONTENT_STRING | "{" text "}" }
    
    
    #######################################################################
    #
    #  Regular Expressions
    #
    #######################################################################
    
    WORD          = /\w+/
    WORD_         = /\w+/~
    NO_BLANK_STRING         = /[^ \t\n,%]+/~
    COMMA_TERMINATED_STRING = { /[^,%]+/ | /(?=%)/~ }
    CONTENT_STRING = { /[^{}%]+/ | /(?=%)/~ }+
    """
    text = Forward()
    source_hash__ = "5ce8838ebbb255548cf3e14cd90bae6d"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'(?i)%.*(?:\n|$)'
    WHITESPACE__ = r'\s*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    whitespace__ = Whitespace(WSP__)
    CONTENT_STRING = OneOrMore(Alternative(RegExp('(?i)[^{}%]+'), RE('(?i)(?=%)')))
    COMMA_TERMINATED_STRING = ZeroOrMore(Alternative(RegExp('(?i)[^,%]+'), RE('(?i)(?=%)')))
    NO_BLANK_STRING = RE('(?i)[^ \\t\\n,%]+')
    WORD_ = RE('(?i)\\w+')
    WORD = RegExp('(?i)\\w+')
    text.set(ZeroOrMore(Alternative(CONTENT_STRING, Series(Token("{"), text, Token("}")))))
    plain_content = Synonym(COMMA_TERMINATED_STRING)
    content = Alternative(Series(Token("{"), text, Token("}")), plain_content)
    field = Synonym(WORD_)
    key = Synonym(NO_BLANK_STRING)
    type = Synonym(WORD)
    entry = Series(RegExp('(?i)@'), type, Token("{"), key, ZeroOrMore(Series(Token(","), field, Token("="), content, mandatory=2)), Token("}"), mandatory=5)
    comment = Series(Token("@Comment{"), text, Token("}"), mandatory=2)
    pre_code = ZeroOrMore(Alternative(RegExp('(?i)[^"%]+'), RegExp('(?i)%.*\\n')))
    preamble = Series(Token("@Preamble{"), RegExp('(?i)"'), pre_code, RE('(?i)"'), Token("}"), mandatory=4)
    bibliography = ZeroOrMore(Alternative(preamble, comment, entry))
    root__ = bibliography
    
def get_grammar() -> BibTeXGrammar:
    global thread_local_BibTeX_grammar_singleton
    try:
        grammar = thread_local_BibTeX_grammar_singleton
    except NameError:
        thread_local_BibTeX_grammar_singleton = BibTeXGrammar()
        grammar = thread_local_BibTeX_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

BibTeX_AST_transformation_table = {
    # AST Transformations for the BibTeX-grammar
    "+": remove_empty,
    "bibliography": [],
    "preamble": [],
    "pre_code": [],
    "comment": [],
    "entry": [],
    "type": [],
    "key": [],
    "field": [],
    "content": [replace_or_reduce],
    "plain_content": [],
    "text": [],
    ":Token, :RE": reduce_single_child,
    "*": replace_by_single_child
}


def BibTeXTransform() -> TransformationDict:
    return partial(traverse, processing_table=BibTeX_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_BibTeX_transformer_singleton
    try:
        transformer = thread_local_BibTeX_transformer_singleton
    except NameError:
        thread_local_BibTeX_transformer_singleton = BibTeXTransform()
        transformer = thread_local_BibTeX_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class BibTeXCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a BibTeX source file.
    """

    def __init__(self, grammar_name="BibTeX", grammar_source=""):
        super(BibTeXCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_bibliography(self, node):
        return node

    def on_preamble(self, node):
        pass

    def on_pre_code(self, node):
        pass

    def on_comment(self, node):
        pass

    def on_entry(self, node):
        pass

    def on_type(self, node):
        pass

    def on_key(self, node):
        pass

    def on_field(self, node):
        pass

    def on_content(self, node):
        pass

    def on_plain_content(self, node):
        pass

    def on_text(self, node):
        pass


def get_compiler(grammar_name="BibTeX", grammar_source="") -> BibTeXCompiler:
    global thread_local_BibTeX_compiler_singleton
    try:
        compiler = thread_local_BibTeX_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_BibTeX_compiler_singleton = \
            BibTeXCompiler(grammar_name, grammar_source)
        compiler = thread_local_BibTeX_compiler_singleton
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
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: BibTeXCompiler.py [FILENAME]")
