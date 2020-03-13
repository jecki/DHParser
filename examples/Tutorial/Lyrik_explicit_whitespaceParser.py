#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

if r'/home/eckhart/Entwicklung/DHParser' not in sys.path:
    sys.path.append(r'/home/eckhart/Entwicklung/DHParser')

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, DropToken, Synonym, AllOf, SomeOf, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if,\
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, COMPACT_SERIALIZATION, \
    JSON_SERIALIZATION, access_thread_locals, access_presets, finalize_presets, ErrorCode, \
    RX_NEVER_MATCH


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
    source_hash__ = "082c362ff149f702e7b1b76032b5febb"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'[\t ]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
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
    verknüpfung = Series(Series(Drop(Token("<")), dwsp__), ziel, Series(Drop(Token(">")), dwsp__))
    namenfolge = OneOrMore(Series(NAME, Option(L)))
    wortfolge = OneOrMore(Series(WORT, Option(L)))
    jahr = Series(JAHRESZAHL, dwsp__)
    ort = Series(wortfolge, Option(verknüpfung))
    untertitel = Series(wortfolge, Option(verknüpfung))
    werk = Series(wortfolge, Option(Series(Series(Drop(Token(".")), dwsp__), untertitel, mandatory=1)), Option(verknüpfung))
    autor = Series(namenfolge, Option(verknüpfung))
    bibliographisches = Series(autor, Series(Drop(Token(",")), dwsp__), Option(Series(NZ, dwsp__)), werk, Series(Drop(Token(",")), dwsp__), Option(Series(NZ, dwsp__)), ort, Series(Drop(Token(",")), dwsp__), Option(Series(NZ, dwsp__)), jahr, Series(Drop(Token(".")), dwsp__), mandatory=1)
    gedicht = Series(bibliographisches, OneOrMore(LEERZEILE), Option(serie), titel, text, RegExp('\\s*'), ENDE, mandatory=3)
    root__ = gedicht
    

def get_grammar() -> Lyrik_explicit_whitespaceGrammar:
    """Returns a thread/process-exclusive Lyrik_explicit_whitespaceGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton = Lyrik_explicit_whitespaceGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

Lyrik_explicit_whitespace_AST_transformation_table = {
    # AST Transformations for the Lyrik_explicit_whitespace-grammar
    "<": flatten,
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
    "*": replace_by_single_child
}


def CreateLyrik_explicit_whitespaceTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=Lyrik_explicit_whitespace_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_explicit_whitespace_00000002_transformer_singleton = CreateLyrik_explicit_whitespaceTransformer()
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
    """Returns a thread/process-exclusive Lyrik_explicit_whitespaceCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
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

def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
        elif parser_update:
            print(os.path.basename(__file__) + ' has changed. '
              'Please run again in order to apply updated compiler')
            sys.exit(0)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        start_logging(log_dir)
        result, errors, _ = compile_src(file_name)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: Lyrik_explicit_whitespaceParser.py [FILENAME]")
