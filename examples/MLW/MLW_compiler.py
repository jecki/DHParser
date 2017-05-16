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
from DHParser.parsers import GrammarBase, CompilerBase, nil_scanner, \
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, \
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Sequence, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source
from DHParser.syntaxtree import Node, traverse, remove_enclosing_delimiters, \
    remove_children_if, reduce_single_child, replace_by_single_child, remove_whitespace, \
    no_operation, remove_expendables, remove_tokens, flatten, is_whitespace, is_expendable, \
    WHITESPACE_PTYPE, TOKEN_PTYPE


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def MLWScanner(text):
    return text

def get_MLW_scanner():
    return MLWScanner


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class MLWGrammar(GrammarBase):
    r"""Parser for a MLW source file, with this grammar:
    
    # EBNF-Syntax für MLW-Artikel
    
    @ comment         =  /#.*(?:\n|$)/    # Kommentare beginnen mit '#' und reichen bis zum Zeilenende
    @ whitespace      =  /[\t ]*/         # Zeilensprünge zählen nicht als Leerraum
    @ literalws       =  right            # Leerraum vor und nach Literalen wird automatisch entfernt
    
    
    ##############################################################################
    
    Artikel           = [LZ]
                        §LemmaPosition
                        [ArtikelKopf]
                        §BedeutungsPosition
                        §Autorinfo
                        [LZ]  DATEI_ENDE
    
    
    #### LEMMA-POSITION ##########################################################
    
    LemmaPosition     = "LEMMA" [LZ] §HauptLemma §TR [LemmaVarianten] §GrammatikPosition
    
    HauptLemma        = [klassisch] [gesichert] lemma
      klassisch       = "*"
      gesichert       = "$"
    
    LemmaVarianten   = "VARIANTEN" [LZ]
                       { lemma §TR }+
                       [LemmaZusatz §ABS]
    
    lemma            = LAT_WORT_TEIL { ("|" | "-") LAT_WORT_TEIL }
    
    LemmaZusatz      = "ZUSATZ" §lzs_typ
      lzs_typ        = /sim\./
    
    
    ## GRAMMATIK-POSITION ##
    
    GrammatikPosition = "GRAMMATIK" [LZ] §wortart §ABS §Flexion [genus]
                        {GrammatikVariante} [ABS]
    
    wortart         = "nomen"  | "n." |
                      "verb"   | "v." |
                      "adverb" | "adv." |
                      "adjektiv" | "adj."
    
    GrammatikVariante = ABS GVariante
    GVariante       = Flexionen  [genus]  ":"  Beleg
    
    Flexionen       = Flexion { "," §Flexion }
    Flexion         = /-?[a-z]+/~
    
    genus           = "maskulinum" | "m." |
                      "femininum" | "f." |
                      "neutrum" | "n."
    
    
    
    #### ARTIKEL-KOPF ############################################################
    
    ArtikelKopf     = SchreibweisenPosition
    SchreibweisenPosition =  "SCHREIBWEISE" [LZ] §SWTyp ":" [LZ]
                             §SWVariante { ABS SWVariante} [LZ]
    SWTyp           = "script." | "script. fat-"
    SWVariante      = Schreibweise ":" Beleg
    Schreibweise    = "vizreg-" | "festregel(a)" | "fezdregl(a)" | "fat-"
    
    Beleg           = Verweis
    Verweis         = ~/\w+/~
    VerweisZiel     = ~/<\w+>/~
    
    
    #### BEDEUTUNGS-POSITION #####################################################
    
    BedeutungsPosition = { "BEDEUTUNG" [LZ] §Bedeutung }+
    
    Bedeutung       = (Interpretamente | Bedeutungskategorie) [Belege]
    Bedeutungskategorie = /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~ [LZ]
    Interpretamente = LateinischeBedeutung [LZ] §DeutscheBedeutung [LZ]
    LateinischeBedeutung = "LAT" /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    DeutscheBedeutung = "DEU" /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    Belege          = "BELEGE" [LZ] { "*" EinBeleg }
    EinBeleg        = { !([LZ] ("*" | "BEDEUTUNG" | "AUTOR" | "NAME" | "ZUSATZ"))
                        /\s*.*\s*/ }+
                      [Zusatz]
    Zusatz          = "ZUSATZ" /\s*.*/ ABS
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    Autorinfo       = ("AUTORIN" | "AUTOR") Name
    Name            = { NAME | NAMENS_ABKÜRZUNG }+
    
    
    #### ATOMARE AUSDRÜCKE #######################################################
    
    NAMENS_ABKÜRZUNG = /[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\./~
    NAME             = /[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+/~
    
    DEU_WORT         = /[A-ZÄÖÜ]?[a-zäöüß]+/~
    DEU_GROSS        = /[A-ZÄÖÜ][a-zäöüß]+/~
    DEU_KLEIN        = /[a-zäöüß]+/~
    LAT_WORT         = /[a-z]+/~
    LAT_WORT_TEIL    = /[a-z]+/
    GROSSSCHRIFT     = /[A-ZÄÖÜ]+/~
    
    TR               = ABS | LZ             # (beliebiger) Trenner
    ABS              = /\s*;\s*/ | { ZW }+  # Abschluss (durch Semikolon oder Zeilenwechsel)
    ZW               = /\n/~                # Zeilenwechsel
    LZ               = /\s+/                # Leerzeichen oder -zeilen
    
    DATEI_ENDE       = !/./
    NIEMALS          = /(?!.)/
    """
    source_hash__ = "2d6f71148926868bfeba2e2a30b07fec"
    parser_initialization__ = "upon instatiation"
    COMMENT__ = r'#.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'[\t ]*', comment=r'#.*(?:\n|$)')
    wspL__ = ''
    wspR__ = WSP__
    NIEMALS = RE('(?!.)', wR='')
    DATEI_ENDE = NegativeLookahead(RE('.', wR=''))
    LZ = RE('\\s+', wR='')
    ZW = RE('\\n')
    ABS = Alternative(RE('\\s*;\\s*', wR=''), OneOrMore(ZW))
    TR = Alternative(ABS, LZ)
    GROSSSCHRIFT = RE('[A-ZÄÖÜ]+')
    LAT_WORT_TEIL = RE('[a-z]+', wR='')
    LAT_WORT = RE('[a-z]+')
    DEU_KLEIN = RE('[a-zäöüß]+')
    DEU_GROSS = RE('[A-ZÄÖÜ][a-zäöüß]+')
    DEU_WORT = RE('[A-ZÄÖÜ]?[a-zäöüß]+')
    NAME = RE('[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+')
    NAMENS_ABKÜRZUNG = RE('[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\\.')
    Name = OneOrMore(Alternative(NAME, NAMENS_ABKÜRZUNG))
    Autorinfo = Sequence(Alternative(Token("AUTORIN"), Token("AUTOR")), Name)
    Zusatz = Sequence(Token("ZUSATZ"), RE('\\s*.*', wR=''), ABS)
    EinBeleg = Sequence(OneOrMore(Sequence(NegativeLookahead(Sequence(Optional(LZ), Alternative(Token("*"), Token("BEDEUTUNG"), Token("AUTOR"), Token("NAME"), Token("ZUSATZ")))), RE('\\s*.*\\s*', wR=''))), Optional(Zusatz))
    Belege = Sequence(Token("BELEGE"), Optional(LZ), ZeroOrMore(Sequence(Token("*"), EinBeleg)))
    DeutscheBedeutung = Sequence(Token("DEU"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'))
    LateinischeBedeutung = Sequence(Token("LAT"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'))
    Interpretamente = Sequence(LateinischeBedeutung, Optional(LZ), Required(DeutscheBedeutung), Optional(LZ))
    Bedeutungskategorie = Sequence(RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'), Optional(LZ))
    Bedeutung = Sequence(Alternative(Interpretamente, Bedeutungskategorie), Optional(Belege))
    BedeutungsPosition = OneOrMore(Sequence(Token("BEDEUTUNG"), Optional(LZ), Required(Bedeutung)))
    VerweisZiel = RE('<\\w+>', wL=WSP__)
    Verweis = RE('\\w+', wL=WSP__)
    Beleg = Verweis
    Schreibweise = Alternative(Token("vizreg-"), Token("festregel(a)"), Token("fezdregl(a)"), Token("fat-"))
    SWVariante = Sequence(Schreibweise, Token(":"), Beleg)
    SWTyp = Alternative(Token("script."), Token("script. fat-"))
    SchreibweisenPosition = Sequence(Token("SCHREIBWEISE"), Optional(LZ), Required(SWTyp), Token(":"), Optional(LZ), Required(SWVariante), ZeroOrMore(Sequence(ABS, SWVariante)), Optional(LZ))
    ArtikelKopf = SchreibweisenPosition
    genus = Alternative(Token("maskulinum"), Token("m."), Token("femininum"), Token("f."), Token("neutrum"), Token("n."))
    Flexion = RE('-?[a-z]+')
    Flexionen = Sequence(Flexion, ZeroOrMore(Sequence(Token(","), Required(Flexion))))
    GVariante = Sequence(Flexionen, Optional(genus), Token(":"), Beleg)
    GrammatikVariante = Sequence(ABS, GVariante)
    wortart = Alternative(Token("nomen"), Token("n."), Token("verb"), Token("v."), Token("adverb"), Token("adv."), Token("adjektiv"), Token("adj."))
    GrammatikPosition = Sequence(Token("GRAMMATIK"), Optional(LZ), Required(wortart), Required(ABS), Required(Flexion), Optional(genus), ZeroOrMore(GrammatikVariante), Optional(ABS))
    lzs_typ = RE('sim\\.', wR='')
    LemmaZusatz = Sequence(Token("ZUSATZ"), Required(lzs_typ))
    lemma = Sequence(LAT_WORT_TEIL, ZeroOrMore(Sequence(Alternative(Token("|"), Token("-")), LAT_WORT_TEIL)))
    LemmaVarianten = Sequence(Token("VARIANTEN"), Optional(LZ), OneOrMore(Sequence(lemma, Required(TR))), Optional(Sequence(LemmaZusatz, Required(ABS))))
    gesichert = Token("$")
    klassisch = Token("*")
    HauptLemma = Sequence(Optional(klassisch), Optional(gesichert), lemma)
    LemmaPosition = Sequence(Token("LEMMA"), Optional(LZ), Required(HauptLemma), Required(TR), Optional(LemmaVarianten), Required(GrammatikPosition))
    Artikel = Sequence(Optional(LZ), Required(LemmaPosition), Optional(ArtikelKopf), Required(BedeutungsPosition), Required(Autorinfo), Optional(LZ), DATEI_ENDE)
    root__ = Artikel
    
def get_MLW_grammar():
    global thread_local_MLW_grammar_singleton
    try:
        grammar = thread_local_MLW_grammar_singleton
        return grammar
    except NameError:
        thread_local_MLW_grammar_singleton = MLWGrammar()
        return thread_local_MLW_grammar_singleton


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

MLW_AST_transformation_table = {
    # AST Transformations for the MLW-grammar
    "Artikel": no_operation,
    "LemmaPosition": no_operation,
    "HauptLemma": no_operation,
    "klassisch": no_operation,
    "gesichert": no_operation,
    "LemmaVarianten": no_operation,
    "lemma": no_operation,
    "LemmaZusatz": no_operation,
    "lzs_typ": no_operation,
    "GrammatikPosition": no_operation,
    "wortart": no_operation,
    "GrammatikVariante": no_operation,
    "GVariante": no_operation,
    "Flexionen": no_operation,
    "Flexion": no_operation,
    "genus": no_operation,
    "ArtikelKopf": no_operation,
    "SchreibweisenPosition": no_operation,
    "SWTyp": no_operation,
    "SWVariante": no_operation,
    "Schreibweise": no_operation,
    "Beleg": no_operation,
    "Verweis": no_operation,
    "VerweisZiel": no_operation,
    "BedeutungsPosition": no_operation,
    "Bedeutung": no_operation,
    "Bedeutungskategorie": no_operation,
    "Interpretamente": no_operation,
    "LateinischeBedeutung": no_operation,
    "DeutscheBedeutung": no_operation,
    "Belege": no_operation,
    "EinBeleg": no_operation,
    "Zusatz": no_operation,
    "Autorinfo": no_operation,
    "Name": no_operation,
    "NAMENS_ABKÜRZUNG": no_operation,
    "NAME": no_operation,
    "DEU_WORT": no_operation,
    "DEU_GROSS": no_operation,
    "DEU_KLEIN": no_operation,
    "LAT_WORT": no_operation,
    "LAT_WORT_TEIL": no_operation,
    "GROSSSCHRIFT": no_operation,
    "TR": no_operation,
    "NEUE_ZEILE": no_operation,
    "LZ": no_operation,
    "DATEI_ENDE": no_operation,
    "NIEMALS": no_operation,
    "": no_operation
}

MLWTransform = partial(traverse, processing_table=MLW_AST_transformation_table)


def get_MLW_transformer():
    return MLWTransform


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class MLWCompiler(CompilerBase):
    """Compiler for the abstract-syntax-tree of a MLW source file.
    """

    def __init__(self, grammar_name="MLW", grammar_source=""):
        super(MLWCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_Artikel(self, node):
        return node

    def on_LemmaPosition(self, node):
        pass

    def on_HauptLemma(self, node):
        pass

    def on_klassisch(self, node):
        pass

    def on_gesichert(self, node):
        pass

    def on_LemmaVarianten(self, node):
        pass

    def on_lemma(self, node):
        pass

    def on_LemmaZusatz(self, node):
        pass

    def on_lzs_typ(self, node):
        pass

    def on_GrammatikPosition(self, node):
        pass

    def on_wortart(self, node):
        pass

    def on_GrammatikVariante(self, node):
        pass

    def on_GVariante(self, node):
        pass

    def on_Flexionen(self, node):
        pass

    def on_Flexion(self, node):
        pass

    def on_genus(self, node):
        pass

    def on_ArtikelKopf(self, node):
        pass

    def on_SchreibweisenPosition(self, node):
        pass

    def on_SWTyp(self, node):
        pass

    def on_SWVariante(self, node):
        pass

    def on_Schreibweise(self, node):
        pass

    def on_Beleg(self, node):
        pass

    def on_Verweis(self, node):
        pass

    def on_VerweisZiel(self, node):
        pass

    def on_BedeutungsPosition(self, node):
        pass

    def on_Bedeutung(self, node):
        pass

    def on_Bedeutungskategorie(self, node):
        pass

    def on_Interpretamente(self, node):
        pass

    def on_LateinischeBedeutung(self, node):
        pass

    def on_DeutscheBedeutung(self, node):
        pass

    def on_Belege(self, node):
        pass

    def on_EinBeleg(self, node):
        pass

    def on_Zusatz(self, node):
        pass

    def on_Autorinfo(self, node):
        pass

    def on_Name(self, node):
        pass

    def on_NAMENS_ABKÜRZUNG(self, node):
        pass

    def on_NAME(self, node):
        pass

    def on_DEU_WORT(self, node):
        pass

    def on_DEU_GROSS(self, node):
        pass

    def on_DEU_KLEIN(self, node):
        pass

    def on_LAT_WORT(self, node):
        pass

    def on_LAT_WORT_TEIL(self, node):
        pass

    def on_GROSSSCHRIFT(self, node):
        pass

    def on_TR(self, node):
        pass

    def on_NEUE_ZEILE(self, node):
        pass

    def on_LZ(self, node):
        pass

    def on_DATEI_ENDE(self, node):
        pass

    def on_NIEMALS(self, node):
        pass


def get_MLW_compiler(grammar_name="MLW", 
                        grammar_source=""):
    global thread_local_MLW_compiler_singleton
    try:
        compiler = thread_local_MLW_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except NameError:
        thread_local_MLW_compiler_singleton = \
            MLWCompiler(grammar_name, grammar_source)
        return thread_local_MLW_compiler_singleton 


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_MLW(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging("LOGS"):
        compiler = get_MLW_compiler()
        cname = compiler.__class__.__name__
        log_file_name = os.path.basename(os.path.splitext(source)[0]) \
            if is_filename(source) < 0 else cname[:cname.find('.')] + '_out'    
        result = compile_source(source, get_MLW_scanner(), 
                                get_MLW_grammar(),
                                get_MLW_transformer(), compiler)
    return result


if __name__ == "__main__":
    if len(sys.argv) > 1:
        result, errors, ast = compile_MLW(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
                sys.exit(1)
        else:
            print(result)
    else:
        print("Usage: MLW_compiler.py [FILENAME]")
