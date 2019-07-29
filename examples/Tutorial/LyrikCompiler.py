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
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, is_empty, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    collapse, collapse_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, error_on, recompile_grammar, access_thread_locals


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LyrikPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return LyrikPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LyrikGrammar(Grammar):
    r"""Parser for a Lyrik source file.
    """
    source_hash__ = "06c4d5d864de1ee662251e1e50dbafa0"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r''
    WHITESPACE__ = r'[\t ]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    ENDE = NegativeLookahead(RegExp('.'))
    JAHRESZAHL = Series(RegExp('\\d\\d\\d\\d'), wsp__)
    LEERZEILE = Series(RegExp('\\n[ \\t]*(?=\\n)'), wsp__)
    NZ = Series(RegExp('\\n'), wsp__)
    ZEICHENFOLGE = Series(RegExp('[^ \\n<>]+'), wsp__)
    NAME = Series(RegExp('\\w+\\.?'), wsp__)
    WORT = Series(RegExp('\\w+'), wsp__)
    vers = OneOrMore(ZEICHENFOLGE)
    strophe = OneOrMore(Series(NZ, vers))
    text = OneOrMore(Series(strophe, ZeroOrMore(LEERZEILE)))
    zeile = OneOrMore(ZEICHENFOLGE)
    titel = Series(OneOrMore(Series(NZ, zeile)), OneOrMore(LEERZEILE))
    serie = Series(NegativeLookahead(Series(titel, vers, NZ, vers)), OneOrMore(Series(NZ, zeile)), OneOrMore(LEERZEILE))
    ziel = Synonym(ZEICHENFOLGE)
    verknüpfung = Series(Series(Token("<"), wsp__), ziel, Series(Token(">"), wsp__))
    namenfolge = OneOrMore(NAME)
    wortfolge = OneOrMore(WORT)
    jahr = Synonym(JAHRESZAHL)
    ort = Series(wortfolge, Option(verknüpfung))
    untertitel = Series(wortfolge, Option(verknüpfung))
    werk = Series(wortfolge, Option(Series(Series(Token("."), wsp__), untertitel, mandatory=1)), Option(verknüpfung))
    autor = Series(namenfolge, Option(verknüpfung))
    bibliographisches = Series(autor, Series(Token(","), wsp__), Option(NZ), werk, Series(Token(","), wsp__), Option(NZ), ort, Series(Token(","), wsp__), Option(NZ), jahr, Series(Token("."), wsp__), mandatory=1)
    gedicht = Series(bibliographisches, OneOrMore(LEERZEILE), Option(serie), titel, text, RegExp('\\s*'), ENDE, mandatory=3)
    root__ = gedicht
    
def get_grammar() -> LyrikGrammar:
    """Returns a thread/process-exclusive LyrikGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()    
    try:
        grammar = THREAD_LOCALS.Lyrik_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_00000001_grammar_singleton = LyrikGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.Lyrik_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.Lyrik_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

Lyrik_AST_transformation_table = {
    # AST Transformations for the Lyrik-grammar
    "<": remove_empty,
    "gedicht": [],
    "bibliographisches": [],
    "autor": [],
    "werk": [],
    "untertitel": [],
    "ort": [],
    "jahr": [reduce_single_child],
    "wortfolge": [],
    "namenfolge": [],
    "verknüpfung": [],
    "ziel": [reduce_single_child],
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
    ":Token": reduce_single_child,
    "*": replace_by_single_child
}


def LyrikTransform() -> TransformationFunc:
    return partial(traverse, processing_table=Lyrik_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.Lyrik_1_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_1_transformer_singleton = LyrikTransform()
        transformer = THREAD_LOCALS.Lyrik_1_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class LyrikCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Lyrik source file.
    """

    def __init__(self):
        super(LyrikCompiler, self).__init__()

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


def get_compiler() -> LyrikCompiler:
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.Lyrik_1_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_1_compiler_singleton = LyrikCompiler()
        compiler = THREAD_LOCALS.Lyrik_1_compiler_singleton
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
    cname = compiler.__class__.__name__
    result = compile_source(source, get_preprocessor(),
                            get_grammar(),
                            get_transformer(), compiler)
    return result


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
        print("Usage: LyrikCompiler.py [FILENAME]")
