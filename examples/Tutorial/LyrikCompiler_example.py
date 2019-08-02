#!/usr/bin/python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

try:
    import regex as re
except ImportError:
    import re
from DHParser import is_filename, Grammar, Compiler, Lookbehind, \
    Alternative, Pop, Token, Synonym, Whitespace, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    PreprocessorFunc, TransformationDict, remove_empty, reduce_single_child, \
    Node, TransformationFunc, traverse, remove_children_if, is_anonymous, \
    reduce_single_child, replace_by_single_child, remove_whitespace, \
    flatten, is_empty, collapse, replace_content, remove_brackets, \
    is_one_of, rstrip, strip, remove_tokens, remove_nodes, peek, \
    is_insignificant_whitespace, TOKEN_PTYPE, access_thread_locals
from DHParser.log import start_logging


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LyrikPreprocessor(text):
    return text

def get_preprocessor() -> PreprocessorFunc:
    return LyrikPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LyrikGrammar(Grammar):
    r"""Parser for a Lyrik source file, with this grammar:
    
    gedicht           = bibliographisches { LEERZEILE }+ [serie] §titel text /\s*/ ENDE
    
    bibliographisches = autor §"," [NZ] werk "," [NZ] ort "," [NZ] jahr "."
    autor             = namenfolge [verknüpfung]
    werk              = wortfolge ["." §untertitel] [verknüpfung]
    untertitel        = wortfolge [verknüpfung]
    ort               = wortfolge [verknüpfung]
    jahr              = JAHRESZAHL
    
    wortfolge         = { WORT }+
    namenfolge        = { NAME }+
    verknüpfung       = "<" ziel ">"
    ziel              = ZEICHENFOLGE
    
    serie             = !(titel vers NZ vers) { NZ zeile }+ { LEERZEILE }+
    
    titel             = { NZ zeile}+ { LEERZEILE }+
    zeile             = { ZEICHENFOLGE }+
    
    text              = { strophe {LEERZEILE} }+
    strophe           = { NZ vers }+
    vers              = { ZEICHENFOLGE }+
    
    WORT              = /\w+/~
    NAME              = /\w+\.?/~
    ZEICHENFOLGE      = /[^ \n<>]+/~
    NZ                = /\n/~
    LEERZEILE         = /\n[ \t]*(?=\n)/~
    JAHRESZAHL        = /\d\d\d\d/~
    ENDE              = !/./
    """
    source_hash__ = "6602d99972ef2883e28bd735e1fe0401"
    parser_initialization__ = ["upon instantiation"]
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
    bibliographisches = Series(autor, Series(Token(","), wsp__), Option(NZ), werk, Series(Token(","), wsp__),
                               Option(NZ), ort, Series(Token(","), wsp__), Option(NZ), jahr, Series(Token("."), wsp__), mandatory=1)
    gedicht = Series(bibliographisches, OneOrMore(LEERZEILE), Option(serie), titel, text, RegExp('\\s*'), ENDE, mandatory=3)
    root__ = gedicht
    
def get_grammar() -> LyrikGrammar:
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.Lyrik_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_grammar_singleton = LyrikGrammar()
        grammar = THREAD_LOCALS.Lyrik_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def halt(node):
    assert False

Lyrik_AST_transformation_table = {
    # AST Transformations for the Lyrik-grammar
    "<": remove_empty,
    "bibliographisches":
        [flatten, remove_nodes('NZ'), remove_whitespace, remove_tokens],
    "autor": [],
    "werk": [],
    "untertitel": [],
    "ort": [],
    "jahr":
        [reduce_single_child, remove_whitespace, reduce_single_child],
    "wortfolge":
        [flatten(is_one_of('WORT'), recursive=False), rstrip, collapse],
    "namenfolge":
        [flatten(is_one_of('NAME'), recursive=False), rstrip, collapse],
    "verknüpfung":
        [flatten, remove_tokens('<', '>'), remove_whitespace, reduce_single_child],
    "ziel":
        [reduce_single_child, remove_whitespace, reduce_single_child],
    "gedicht, strophe, text":
        [flatten, remove_nodes('LEERZEILE'), remove_nodes('NZ')],
    "titel, serie":
        [flatten, remove_nodes('LEERZEILE'), remove_nodes('NZ'), collapse],
    "zeile": [strip],
    "vers":
        [strip, collapse],
    "WORT": [],
    "NAME": [],
    "ZEICHENFOLGE":
        reduce_single_child,
    "NZ":
        reduce_single_child,
    "LEERZEILE": [],
    "JAHRESZAHL":
        [reduce_single_child],
    "ENDE": [],
    ":Whitespace":
        replace_content(lambda node: " "),
    "*": replace_by_single_child
}

def LyrikTransform() -> TransformationFunc:
    return partial(traverse, processing_table=Lyrik_AST_transformation_table)


def get_transformer() -> TransformationFunc:
    THREAD_LOCALS = access_thread_locals()
    try:
        transform = THREAD_LOCALS.Lyrik_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_transformer_singleton = LyrikTransform()
        transform = THREAD_LOCALS.Lyrik_transformer_singleton
    return transform


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class LyrikCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Lyrik source file.
    """

    def on_gedicht(self, node):
        return node

    def on_bibliographisches(self, node):
        pass

    def on_autor(self, node):
        pass

    def on_werk(self, node):
        pass

    def on_untertitel(self, node):
        pass

    def on_ort(self, node):
        pass

    def on_jahr(self, node):
        pass

    def on_wortfolge(self, node):
        pass

    def on_namenfolge(self, node):
        pass

    def on_verknüpfung(self, node):
        pass

    def on_ziel(self, node):
        pass

    def on_serie(self, node):
        pass

    def on_titel(self, node):
        pass

    def on_zeile(self, node):
        pass

    def on_text(self, node):
        pass

    def on_strophe(self, node):
        pass

    def on_vers(self, node):
        pass

    def on_WORT(self, node):
        pass

    def on_NAME(self, node):
        pass

    def on_ZEICHENFOLGE(self, node):
        pass

    def on_NZ(self, node):
        pass

    def on_LEERZEILE(self, node):
        pass

    def on_JAHRESZAHL(self, node):
        pass

    def on_ENDE(self, node):
        pass


def get_compiler() -> LyrikCompiler:
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.Lyrik_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_compiler_singleton = LyrikCompiler()
        compiler = THREAD_LOCALS.Lyrik_compiler_singleton
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
        print("Usage: LyrikCompiler.py [FILENAME]")
