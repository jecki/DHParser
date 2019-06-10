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
    error_on, recompile_grammar, THREAD_LOCALS


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def Lyrik_explicit_whitespacePreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return Lyrik_explicit_whitespacePreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class Lyrik_explicit_whitespaceGrammar(Grammar):
    r"""Parser for a Lyrik_explicit_whitespace source file.
    """
    source_hash__ = "10fbc58b65d0fd5a178572b3776456f0"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r''
    WHITESPACE__ = r'[\t ]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    L = Series(RegExp('[ \\t]+'), dwsp__)
    ENDE = NegativeLookahead(RegExp('.'))
    JAHRESZAHL = RegExp('\\d\\d\\d\\d')
    LEERZEILE = Series(RegExp('\\n[ \\t]*(?=\\n)'), dwsp__)
    NZ = RegExp('\\n')
    ZEICHENFOLGE = RegExp('[^ \\n<>]+')
    NAME = RegExp('\\w+\\.?')
    WORT = RegExp('\\w+')
    vers = OneOrMore(Series(ZEICHENFOLGE, Option(L)))
    strophe = OneOrMore(Series(NZ, vers))
    text = OneOrMore(Series(strophe, ZeroOrMore(LEERZEILE)))
    zeile = OneOrMore(Series(ZEICHENFOLGE, Option(L)))
    titel = OneOrMore(Series(NZ, Option(L), zeile, OneOrMore(LEERZEILE)))
    serie = Series(NegativeLookahead(Series(titel, vers, NZ, vers)), OneOrMore(Series(NZ, zeile)), OneOrMore(LEERZEILE))
    ziel = Series(ZEICHENFOLGE, dwsp__)
    verknüpfung = Series(Series(DropToken("<"), dwsp__), ziel, Series(DropToken(">"), dwsp__))
    namenfolge = OneOrMore(Series(NAME, Option(L)))
    wortfolge = OneOrMore(Series(WORT, Option(L)))
    jahr = Series(JAHRESZAHL, dwsp__)
    ort = Series(wortfolge, Option(verknüpfung))
    untertitel = Series(wortfolge, Option(verknüpfung))
    werk = Series(wortfolge, Option(Series(Series(DropToken("."), dwsp__), untertitel, mandatory=1)), Option(verknüpfung))
    autor = Series(namenfolge, Option(verknüpfung))
    bibliographisches = Series(autor, Series(DropToken(","), dwsp__), Option(Series(NZ, dwsp__)), werk, Series(DropToken(","), dwsp__), Option(Series(NZ, dwsp__)), ort, Series(DropToken(","), dwsp__), Option(Series(NZ, dwsp__)), jahr, Series(DropToken("."), dwsp__), mandatory=1)
    gedicht = Series(bibliographisches, OneOrMore(LEERZEILE), Option(serie), titel, text, RegExp('\\s*'), ENDE, mandatory=3)
    root__ = gedicht
    
def get_grammar() -> Lyrik_explicit_whitespaceGrammar:
    """Returns a thread/process-exclusive Lyrik_explicit_whitespaceGrammar-singleton."""
    try:
        grammar = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton = Lyrik_explicit_whitespaceGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

Lyrik_explicit_whitespace_AST_transformation_table = {
    # AST Transformations for the Lyrik_explicit_whitespace-grammar
    "<": remove_empty,
    "gedicht": [],
    "bibliographisches": [],
    "autor": [],
    "werk": [],
    "untertitel": [],
    "ort": [],
    "jahr": [],
    "wortfolge": [],
    "namenfolge": [],
    "verknüpfung": [],
    "ziel": [],
    "serie": [],
    "titel": [],
    "zeile": [],
    "text": [],
    "strophe": [],
    "vers": [],
    "WORT": [],
    "NAME": [],
    "ZEICHENFOLGE": [],
    "NZ": [],
    "LEERZEILE": [],
    "JAHRESZAHL": [],
    "ENDE": [],
    "L": [],
    ":Token": reduce_single_child,
    "*": replace_by_single_child
}


def Lyrik_explicit_whitespaceTransform() -> TransformationDict:
    return partial(traverse, processing_table=Lyrik_explicit_whitespace_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    try:
        transformer = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_transformer_singleton = Lyrik_explicit_whitespaceTransform()
        transformer = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class Lyrik_explicit_whitespaceCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Lyrik_explicit_whitespace source file.
    """

    def __init__(self):
        super(Lyrik_explicit_whitespaceCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!
    def on_gedicht(self, node):
        return self.fallback_compiler(node)

    # def on_bibliographisches(self, node):
    #     return node

    # def on_autor(self, node):
    #     return node

    # def on_werk(self, node):
    #     return node

    # def on_untertitel(self, node):
    #     return node

    # def on_ort(self, node):
    #     return node

    # def on_jahr(self, node):
    #     return node

    # def on_wortfolge(self, node):
    #     return node

    # def on_namenfolge(self, node):
    #     return node

    # def on_verknüpfung(self, node):
    #     return node

    # def on_ziel(self, node):
    #     return node

    # def on_serie(self, node):
    #     return node

    # def on_titel(self, node):
    #     return node

    # def on_zeile(self, node):
    #     return node

    # def on_text(self, node):
    #     return node

    # def on_strophe(self, node):
    #     return node

    # def on_vers(self, node):
    #     return node

    # def on_WORT(self, node):
    #     return node

    # def on_NAME(self, node):
    #     return node

    # def on_ZEICHENFOLGE(self, node):
    #     return node

    # def on_NZ(self, node):
    #     return node

    # def on_LEERZEILE(self, node):
    #     return node

    # def on_JAHRESZAHL(self, node):
    #     return node

    # def on_ENDE(self, node):
    #     return node

    # def on_L(self, node):
    #     return node


def get_compiler() -> Lyrik_explicit_whitespaceCompiler:
    try:
        compiler = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_compiler_singleton = Lyrik_explicit_whitespaceCompiler()
        compiler = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_compiler_singleton
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
        print("Usage: Lyrik_explicit_whitespaceCompiler.py [FILENAME]")
