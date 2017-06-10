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
from DHParser.toolkit import logging, is_filename, load_if_file    
from DHParser.parsers import Grammar, Compiler, nil_scanner, \
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, \
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Sequence, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    nop_filter, counterpart_filter, accumulating_filter
from DHParser.syntaxtree import Node, traverse, remove_enclosing_delimiters, \
    remove_children_if, reduce_single_child, replace_by_single_child, remove_whitespace, \
    no_operation, remove_expendables, remove_tokens, flatten, is_whitespace, is_expendable, \
    collapse, map_content, WHITESPACE_PTYPE, TOKEN_PTYPE


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LyrikScanner(text):
    return text

def get_scanner():
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
    source_hash__ = "3e9ec28cf58667fc259569326f76cf90"
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
    
def get_grammar():
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
    "gedicht": no_operation,
    "bibliographisches": no_operation,
    "autor": no_operation,
    "werk": no_operation,
    "untertitel": no_operation,
    "ort": no_operation,
    "jahr": no_operation,
    "wortfolge": no_operation,
    "namenfolge": no_operation,
    "verknüpfung": no_operation,
    "ziel": no_operation,
    "serie": no_operation,
    "titel": no_operation,
    "zeile": no_operation,
    "text": no_operation,
    "strophe": no_operation,
    "vers": no_operation,
    "WORT": no_operation,
    "NAME": no_operation,
    "ZEICHENFOLGE": no_operation,
    "NZ": no_operation,
    "LEERZEILE": no_operation,
    "JAHRESZAHL": no_operation,
    "ENDE": no_operation,
    "*": no_operation
}

LyrikTransform = partial(traverse, processing_table=Lyrik_AST_transformation_table)


def get_transformer():
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

    def on_gedicht(self, node: Node) -> str:
        return node

    def on_bibliographisches(self, node: Node) -> str:
        pass

    def on_autor(self, node: Node) -> str:
        pass

    def on_werk(self, node: Node) -> str:
        pass

    def on_untertitel(self, node: Node) -> str:
        pass

    def on_ort(self, node: Node) -> str:
        pass

    def on_jahr(self, node: Node) -> str:
        pass

    def on_wortfolge(self, node: Node) -> str:
        pass

    def on_namenfolge(self, node: Node) -> str:
        pass

    def on_verknüpfung(self, node: Node) -> str:
        pass

    def on_ziel(self, node: Node) -> str:
        pass

    def on_serie(self, node: Node) -> str:
        pass

    def on_titel(self, node: Node) -> str:
        pass

    def on_zeile(self, node: Node) -> str:
        pass

    def on_text(self, node: Node) -> str:
        pass

    def on_strophe(self, node: Node) -> str:
        pass

    def on_vers(self, node: Node) -> str:
        pass

    def on_WORT(self, node: Node) -> str:
        pass

    def on_NAME(self, node: Node) -> str:
        pass

    def on_ZEICHENFOLGE(self, node: Node) -> str:
        pass

    def on_NZ(self, node: Node) -> str:
        pass

    def on_LEERZEILE(self, node: Node) -> str:
        pass

    def on_JAHRESZAHL(self, node: Node) -> str:
        pass

    def on_ENDE(self, node: Node) -> str:
        pass


def get_compiler(grammar_name="Lyrik", grammar_source=""):
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
