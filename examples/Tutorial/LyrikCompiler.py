#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import os
import sys
from functools import partial

try:
    import regex as re
except ImportError:
    import re
from DHParser.toolkit import logging, is_filename
from DHParser.parsers import Grammar, Compiler, Required, Token, \
    Optional, OneOrMore, Sequence, RE, ZeroOrMore, NegativeLookahead, mixin_comment, compile_source, \
    ScannerFunc
from DHParser.syntaxtree import traverse, no_transformation, TransformationFunc


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LyrikScanner(text):
    return text

def get_scanner() -> ScannerFunc:
    return LyrikScanner


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LyrikGrammar(Grammar):
    r"""Parser for a Lyrik source file, with this grammar:
    
    gedicht           = bibliographisches { LEERZEILE }+ [serie] §titel §text /\s*/ §ENDE
    
    bibliographisches = autor §"," [NZ] werk §"," [NZ] ort §"," [NZ] jahr §"."
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
    source_hash__ = "7a99fa77a7d2b81976293d54696eb4f3"
    parser_initialization__ = "upon instatiation"
    COMMENT__ = r''
    WSP__ = mixin_comment(whitespace=r'[\t ]*', comment=r'')
    wspL__ = ''
    wspR__ = WSP__
    ENDE = NegativeLookahead(RE('.', wR=''))
    JAHRESZAHL = RE('\\d\\d\\d\\d')
    LEERZEILE = RE('\\n[ \\t]*(?=\\n)')
    NZ = RE('\\n')
    ZEICHENFOLGE = RE('[^ \\n<>]+')
    NAME = RE('\\w+\\.?')
    WORT = RE('\\w+')
    vers = OneOrMore(ZEICHENFOLGE)
    strophe = OneOrMore(Sequence(NZ, vers))
    text = OneOrMore(Sequence(strophe, ZeroOrMore(LEERZEILE)))
    zeile = OneOrMore(ZEICHENFOLGE)
    titel = Sequence(OneOrMore(Sequence(NZ, zeile)), OneOrMore(LEERZEILE))
    serie = Sequence(NegativeLookahead(Sequence(titel, vers, NZ, vers)), OneOrMore(Sequence(NZ, zeile)), OneOrMore(LEERZEILE))
    ziel = ZEICHENFOLGE
    verknüpfung = Sequence(Token("<"), ziel, Token(">"))
    namenfolge = OneOrMore(NAME)
    wortfolge = OneOrMore(WORT)
    jahr = JAHRESZAHL
    ort = Sequence(wortfolge, Optional(verknüpfung))
    untertitel = Sequence(wortfolge, Optional(verknüpfung))
    werk = Sequence(wortfolge, Optional(Sequence(Token("."), Required(untertitel))), Optional(verknüpfung))
    autor = Sequence(namenfolge, Optional(verknüpfung))
    bibliographisches = Sequence(autor, Required(Token(",")), Optional(NZ), werk, Required(Token(",")), Optional(NZ), ort, Required(Token(",")), Optional(NZ), jahr, Required(Token(".")))
    gedicht = Sequence(bibliographisches, OneOrMore(LEERZEILE), Optional(serie), Required(titel), Required(text), RE('\\s*', wR=''), Required(ENDE))
    root__ = gedicht
    
def get_grammar() -> LyrikGrammar:
    global thread_local_Lyrik_grammar_singleton
    try:
        grammar = thread_local_Lyrik_grammar_singleton
        return grammar
    except NameError:
        thread_local_Lyrik_grammar_singleton = LyrikGrammar()
        return thread_local_Lyrik_grammar_singleton


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

Lyrik_AST_transformation_table = {
    # AST Transformations for the Lyrik-grammar
    "gedicht": no_transformation,
    "bibliographisches": no_transformation,
    "autor": no_transformation,
    "werk": no_transformation,
    "untertitel": no_transformation,
    "ort": no_transformation,
    "jahr": no_transformation,
    "wortfolge": no_transformation,
    "namenfolge": no_transformation,
    "verknüpfung": no_transformation,
    "ziel": no_transformation,
    "serie": no_transformation,
    "titel": no_transformation,
    "zeile": no_transformation,
    "text": no_transformation,
    "strophe": no_transformation,
    "vers": no_transformation,
    "WORT": no_transformation,
    "NAME": no_transformation,
    "ZEICHENFOLGE": no_transformation,
    "NZ": no_transformation,
    "LEERZEILE": no_transformation,
    "JAHRESZAHL": no_transformation,
    "ENDE": no_transformation,
    "*": no_transformation
}

LyrikTransform = partial(traverse, processing_table=Lyrik_AST_transformation_table)


def get_transformer() -> TransformationFunc:
    return LyrikTransform


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class LyrikCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Lyrik source file.
    """

    def __init__(self, grammar_name="Lyrik", grammar_source=""):
        super(LyrikCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

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


def get_compiler(grammar_name="Lyrik", grammar_source="") -> LyrikCompiler:
    global thread_local_Lyrik_compiler_singleton
    try:
        compiler = thread_local_Lyrik_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except NameError:
        thread_local_Lyrik_compiler_singleton = \
            LyrikCompiler(grammar_name, grammar_source)
        return thread_local_Lyrik_compiler_singleton 


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
        result = compile_source(source, get_scanner(), 
                                get_grammar(),
                                get_transformer(), compiler)
    return result


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("Lyrisches_Intermezzo_IV.txt")
    if len(sys.argv) > 1:
        result, errors, ast = compile_src(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
            sys.exit(1)
        else:
            print(result)
    else:
        print("Usage: LyrikCompiler.py [FILENAME]")
