#!/usr/bin/python3

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
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationDict, Whitespace, \
    traverse, remove_children_if, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    is_empty, collapse, replace_content, remove_nodes, remove_content, remove_brackets, change_tag_name, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    WHITESPACE_PTYPE, TOKEN_PTYPE, THREAD_LOCALS
from DHParser.transform import TransformationFunc
from DHParser.log import start_logging


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
    r"""Parser for a BibTeX source file.
    """
    text = Forward()
    source_hash__ = "8839d079e31b568a31f0ea4cbb175aa8"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'//'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('(?i).'))
    CONTENT_STRING = OneOrMore(Alternative(RegExp('(?i)[^{}%]+'), Series(Lookahead(RegExp('(?i)%')), wsp__)))
    COMMA_TERMINATED_STRING = ZeroOrMore(Alternative(RegExp('(?i)[^,%]+'), Series(Lookahead(RegExp('(?i)%')), wsp__)))
    NO_BLANK_STRING = Series(RegExp('(?i)[^ \\t\\n,%]+'), wsp__)
    WORD = Series(RegExp('(?i)\\w+'), wsp__)
    text.set(ZeroOrMore(Alternative(CONTENT_STRING, Series(Series(Token("{"), wsp__), text, Series(Token("}"), wsp__)))))
    plain_content = Synonym(COMMA_TERMINATED_STRING)
    content = Alternative(Series(Series(Token("{"), wsp__), text, Series(Token("}"), wsp__)), plain_content)
    field = Synonym(WORD)
    key = Synonym(NO_BLANK_STRING)
    type = Synonym(WORD)
    entry = Series(RegExp('(?i)@'), type, Series(Token("{"), wsp__), key, ZeroOrMore(Series(Series(Token(","), wsp__), field, Series(Token("="), wsp__), content, mandatory=2)), Option(Series(Token(","), wsp__)), Series(Token("}"), wsp__), mandatory=6)
    comment = Series(Series(Token("@Comment{"), wsp__), text, Series(Token("}"), wsp__), mandatory=2)
    pre_code = ZeroOrMore(Alternative(RegExp('(?i)[^"%]+'), RegExp('(?i)%.*\\n')))
    preamble = Series(Series(Token("@Preamble{"), wsp__), RegExp('(?i)"'), pre_code, RegExp('(?i)"'), wsp__, Series(Token("}"), wsp__), mandatory=5)
    bibliography = ZeroOrMore(Alternative(preamble, comment, entry))
    root__ = bibliography
    
def get_grammar() -> BibTeXGrammar:
    """Returns a thread/process-exclusive BibTeXGrammar-singleton."""
    try:
        grammar = THREAD_LOCALS.BibTeX_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.BibTeX_00000001_grammar_singleton = BibTeXGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.BibTeX_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.BibTeX_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

BibTeX_AST_transformation_table = {
    # AST Transformations for the BibTeX-grammar
    "<": remove_empty,
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
    ":_Token, :_RE": reduce_single_child,
    "*": replace_by_single_child
}


def BibTeXTransform() -> TransformationFunc:
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


def get_compiler() -> BibTeXCompiler:
    global thread_local_BibTeX_compiler_singleton
    try:
        compiler = thread_local_BibTeX_compiler_singleton
    except NameError:
        thread_local_BibTeX_compiler_singleton = BibTeXCompiler()
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
    start_logging("LOGS")
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
