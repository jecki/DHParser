#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import os
import sys
from functools import partial

sys.path.append('../../')

try:
    import regex as re
except ImportError:
    import re
from DHParser.toolkit import logging, is_filename
from DHParser.parsers import Grammar, Compiler, Required, Token, \
    Option, OneOrMore, Series, RE, ZeroOrMore, NegativeLookahead, mixin_comment, compile_source, \
    PreprocessorFunc, Synonym
from DHParser.syntaxtree import Node, traverse, remove_last, \
    reduce_single_child, replace_by_single_child, remove_tokens, flatten, is_whitespace, collapse, replace_content, \
    TransformationFunc, \
    remove_parser, remove_empty, has_name


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LyrikScanner(text):
    return text


def get_scanner() -> PreprocessorFunc:
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
    source_hash__ = "a2832bea27ad1a4e48e87ad7b1cef2c3"
    parser_initialization__ = "upon instantiation"
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
    strophe = OneOrMore(Series(NZ, vers))
    text = OneOrMore(Series(strophe, ZeroOrMore(LEERZEILE)))
    zeile = OneOrMore(ZEICHENFOLGE)
    titel = Series(OneOrMore(Series(NZ, zeile)), OneOrMore(LEERZEILE))
    serie = Series(NegativeLookahead(Series(titel, vers, NZ, vers)), OneOrMore(Series(NZ, zeile)), OneOrMore(LEERZEILE))
    ziel = Synonym(ZEICHENFOLGE)
    verknüpfung = Series(Token("<"), ziel, Token(">"))
    namenfolge = OneOrMore(NAME)
    wortfolge = OneOrMore(WORT)
    jahr = Synonym(JAHRESZAHL)
    ort = Series(wortfolge, Option(verknüpfung))
    untertitel = Series(wortfolge, Option(verknüpfung))
    werk = Series(wortfolge, Option(Series(Token("."), Required(untertitel))), Option(verknüpfung))
    autor = Series(namenfolge, Option(verknüpfung))
    bibliographisches = Series(autor, Required(Token(",")), Option(NZ), werk, Required(Token(",")), Option(NZ), ort,
                               Required(Token(",")), Option(NZ), jahr, Required(Token(".")))
    gedicht = Series(bibliographisches, OneOrMore(LEERZEILE), Option(serie), Required(titel), Required(text),
                     RE('\\s*', wR=''), Required(ENDE))
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

def halt(node):
    assert False

Lyrik_AST_transformation_table = {
    # AST Transformations for the Lyrik-grammar
    "+": remove_empty,
    "bibliographisches":
        [remove_parser('NZ'), remove_tokens],
    "autor": [],
    "werk": [],
    "untertitel": [],
    "ort": [],
    "jahr":
        [reduce_single_child],
    "wortfolge":
        [flatten(has_name('WORT'), recursive=False), remove_last(is_whitespace), collapse],
    "namenfolge":
        [flatten(has_name('NAME'), recursive=False), remove_last(is_whitespace), collapse],
    "verknüpfung":
        [remove_tokens('<', '>'), reduce_single_child],
    "ziel":
        reduce_single_child,
    "gedicht, strophe, text":
        [flatten, remove_parser('LEERZEILE'), remove_parser('NZ')],
    "titel, serie":
        [flatten, remove_parser('LEERZEILE'), remove_parser('NZ'), collapse],
    "zeile": [],
    "vers":
        collapse,
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
        replace_content(lambda node : " "),
    ":Token, :RE":
        reduce_single_child,
    "*": replace_by_single_child
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
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: LyrikCompiler.py [FILENAME]")
