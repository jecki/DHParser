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
from DHParser import logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, TRUE_CONDITION, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, remove_parser, remove_content, remove_brackets, replace_parser, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def MLWPreprocessor(text):
    return text

def get_preprocessor() -> PreprocessorFunc:
    return MLWPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class MLWGrammar(Grammar):
    r"""Parser for a MLW source file, with this grammar:
    
    # EBNF-Syntax für MLW-Artikel
    
    
    @ comment         =  /#.*/            # Kommentare beginnen mit '#' und reichen bis zum Zeilenende
                                          # ohne das Zeilenende zu beinhalten
    @ whitespace      =  /[\t ]*/         # Zeilensprünge zählen nicht als Leerraum
    @ literalws       =  right            # Leerraum vor und nach Literalen wird automatisch entfernt
    
    
    ##############################################################################
    
    Artikel           = [LZ]
                        §LemmaPosition
                        [ArtikelKopf]
                        §BedeutungsPosition
                        §ArtikelVerfasser
                        [LZ]  DATEI_ENDE
    
    
    #### LEMMA-POSITION ##########################################################
    
    LemmaPosition     = "LEMMA" [LZ] §Lemma §TR [LemmaVarianten]
                        §GrammatikPosition [EtymologiePosition]
    
    Lemma             = [klassisch] [gesichert] LemmaWort
      klassisch       = "*"
      gesichert       = "$"
    
    LemmaVarianten    = [LZ]
                        { LemmaWort §TR }+
                        [LemmaZusatz §ABS]
    
    LemmaWort         = LAT_WORT_TEIL { ("|" | "-") LAT_WORT_TEIL }
    
    LemmaZusatz       = "ZUSATZ" §lzs_typ
      lzs_typ         = /sim\./
    
    
    ## GRAMMATIK-POSITION ##
    
    GrammatikPosition = "GRAMMATIK" [LZ] §wortart §ABS §flexion [genus] §ABS
                        [GrammatikVarianten]
    
    wortart          = "nomen"  | "n."
                     | "verb"   | "v."
                     | "adverb" | "adv."
                     | "adjektiv" | "adj."
                     | "praeposition" | "praep."
    
    GrammatikVarianten = { [wortart ABS] flexion [genus]  ":"  Beleg §ABS }+
    
    flexion          = FLEX { "," §FLEX }
    FLEX             = /-?[a-z]+/~
    
    genus            = "maskulinum" | "m."
                     | "femininum" | "f."
                     | "neutrum" | "n."
    
    
    ## ETYMOLOGIE-POSITION ##
    
    EtymologiePosition = "ETYMOLOGIE" [LZ] EtymologieVarianten
    EtymologieVarianten = { !([LZ] GROSSFOLGE) EtymologieVariante }+
    EtymologieVariante = /.*/   # NOCH ZU VERFOLLSTÄNDIGEN
    
    
    #### ARTIKEL-KOPF ############################################################
    
    ArtikelKopf     = SchreibweisenPosition
    SchreibweisenPosition =  "SCHREIBWEISE" [LZ] §SWTyp ":" [LZ]
                             §SWVariante { ABS SWVariante} [LZ]
    SWTyp           = "script." | "script. fat-"
    SWVariante      = Schreibweise ":" Beleg
    Schreibweise    = ZEICHENFOLGE
    
    
    #### BEDEUTUNGS-POSITION #####################################################
    
    BedeutungsPosition = { "BEDEUTUNG" [LZ] §Bedeutung }+
    
    Bedeutung       = (Interpretamente | Bedeutungskategorie) [Belege]
    Bedeutungskategorie = /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~ [LZ]
    Interpretamente = LateinischeBedeutung [LZ] §DeutscheBedeutung [LZ]
    LateinischeBedeutung = SW_LAT /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    DeutscheBedeutung = SW_DEU /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    
    Belege          = "BELEGE" [LZ] (EinBeleg | { "*" EinBeleg })
    EinBeleg        = { !([LZ] ("*" | GROSSFOLGE )) /\s*[^\n]*\s*/ }+ [Zusatz]
    Zusatz          = "ZUSATZ" /\s*.*/ ABS
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    ArtikelVerfasser = ("AUTORIN" | "AUTOR") Name
    Name             = { NAME | NAMENS_ABKÜRZUNG }+
    
    
    #### Schlüsselwörter #########################################################
    
    SW_LAT           = "LATEINISCH" | "LAT"
    SW_DEU           = "DEUTSCH" | "DEUT"
    SW_GRIECH        = "GRIECHISCH" | "GRIECH" | "GRIE" | "GRI"
    
    
    #### GENERISCHE UND ATOMARE AUSDRÜCKE ########################################
    
    Beleg            = Verweis
    
    Verweis          = "->" ZielName
    VerweisZiel      = "[" ZielName "]"
    ZielName         = BUCHSTABENFOLGE
    
    NAMENS_ABKÜRZUNG = /[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\./~
    NAME             = /[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+/~
    
    DEU_WORT         = /[A-ZÄÖÜ]?[a-zäöüß]+/~
    DEU_GROSS        = /[A-ZÄÖÜ][a-zäöüß]+/~
    DEU_KLEIN        = /[a-zäöüß]+/~
    LAT_WORT         = /[a-z]+/~
    LAT_WORT_TEIL    = /[a-z]+/
    GROSSSCHRIFT     = /[A-ZÄÖÜ]+/~
    GROSSFOLGE       = /[A-ZÄÖÜ][A-ZÄÖÜ][A-ZÄÖÜ]/   # drei Großbuchstaben in Folge
    
    BUCHSTABENFOLGE  = /\w+/~
    ZEICHENFOLGE     = /[\w()-]+/~
    
    TR               = ABS | LZ             # (beliebiger) Trenner
    ABS              = /\s*;\s*/ | { ZWW }+  # Abschluss (durch Semikolon oder Zeilenwechsel)
    # ZW               = /\n/~                # Zeilenwechsel
    LZ               = /\s+/                # Leerzeichen oder -zeilen
    
    ZW               = !LÜCKE ZEILENSPRUNG       # Zeilenwechsel, aber keine Leerzeile(n)
    ZWW              = ZEILENSPRUNG [ LEERRAUM ] # mindestens ein Zeilenwechsel
    LÜCKE            = KOMMENTARZEILEN LEERZEILE [LEERRAUM] # Leerraum mit mindestens einer echten Leerzeile
    LEERRAUM         = { COMMENT__ | /\s+/ }+   # beliebiger horizontaler oder vertikaler Leerraum
    LEERZEILE        = /[ \t]*(?:\n[ \t]*)+\n/ ~/\n?/ # eine oder mehrere echte LEERZEILEN
    RZS              = /\s*?\n|$/               # Rückwärtiger Zeilensprung oder Textanfang
    
    ZEILENSPRUNG     = /[ \t]*\n/~
    KOMMENTARZEILEN  = { /[ \t]*\n?[ \t]*/ COMMENT__ }  # echte Kommentarzeilen
    
    DATEI_ENDE       = !/./
    NIEMALS          = /(?!.)/
    """
    wortart = Forward()
    source_hash__ = "86cbd5a83fff876fb99e4920ead1335d"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'#.*'
    WHITESPACE__ = r'[\t ]*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    NIEMALS = RegExp('(?!.)')
    DATEI_ENDE = NegativeLookahead(RegExp('.'))
    KOMMENTARZEILEN = ZeroOrMore(Series(RegExp('[ \\t]*\\n?[ \\t]*'), RegExp(COMMENT__)))
    ZEILENSPRUNG = RE('[ \\t]*\\n')
    RZS = RegExp('\\s*?\\n|$')
    LEERZEILE = Series(RegExp('[ \\t]*(?:\\n[ \\t]*)+\\n'), RE('\\n?', wR='', wL=WSP__))
    LEERRAUM = OneOrMore(Alternative(RegExp(COMMENT__), RegExp('\\s+')))
    LÜCKE = Series(KOMMENTARZEILEN, LEERZEILE, Option(LEERRAUM))
    ZWW = Series(ZEILENSPRUNG, Option(LEERRAUM))
    ZW = Series(NegativeLookahead(LÜCKE), ZEILENSPRUNG)
    LZ = RegExp('\\s+')
    ABS = Alternative(RegExp('\\s*;\\s*'), OneOrMore(ZWW))
    TR = Alternative(ABS, LZ)
    ZEICHENFOLGE = RE('[\\w()-]+')
    BUCHSTABENFOLGE = RE('\\w+')
    GROSSFOLGE = RegExp('[A-ZÄÖÜ][A-ZÄÖÜ][A-ZÄÖÜ]')
    GROSSSCHRIFT = RE('[A-ZÄÖÜ]+')
    LAT_WORT_TEIL = RegExp('[a-z]+')
    LAT_WORT = RE('[a-z]+')
    DEU_KLEIN = RE('[a-zäöüß]+')
    DEU_GROSS = RE('[A-ZÄÖÜ][a-zäöüß]+')
    DEU_WORT = RE('[A-ZÄÖÜ]?[a-zäöüß]+')
    NAME = RE('[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+')
    NAMENS_ABKÜRZUNG = RE('[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\\.')
    ZielName = Synonym(BUCHSTABENFOLGE)
    VerweisZiel = Series(Token("["), ZielName, Token("]"))
    Verweis = Series(Token("->"), ZielName)
    Beleg = Synonym(Verweis)
    SW_GRIECH = Alternative(Token("GRIECHISCH"), Token("GRIECH"), Token("GRIE"), Token("GRI"))
    SW_DEU = Alternative(Token("DEUTSCH"), Token("DEUT"))
    SW_LAT = Alternative(Token("LATEINISCH"), Token("LAT"))
    Name = OneOrMore(Alternative(NAME, NAMENS_ABKÜRZUNG))
    ArtikelVerfasser = Series(Alternative(Token("AUTORIN"), Token("AUTOR")), Name)
    Zusatz = Series(Token("ZUSATZ"), RegExp('\\s*.*'), ABS)
    EinBeleg = Series(OneOrMore(Series(NegativeLookahead(Series(Option(LZ), Alternative(Token("*"), GROSSFOLGE))), RegExp('\\s*[^\\n]*\\s*'))), Option(Zusatz))
    Belege = Series(Token("BELEGE"), Option(LZ), Alternative(EinBeleg, ZeroOrMore(Series(Token("*"), EinBeleg))))
    DeutscheBedeutung = Series(SW_DEU, RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'))
    LateinischeBedeutung = Series(SW_LAT, RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'))
    Interpretamente = Series(LateinischeBedeutung, Option(LZ), Required(DeutscheBedeutung), Option(LZ))
    Bedeutungskategorie = Series(RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'), Option(LZ))
    Bedeutung = Series(Alternative(Interpretamente, Bedeutungskategorie), Option(Belege))
    BedeutungsPosition = OneOrMore(Series(Token("BEDEUTUNG"), Option(LZ), Required(Bedeutung)))
    Schreibweise = Synonym(ZEICHENFOLGE)
    SWVariante = Series(Schreibweise, Token(":"), Beleg)
    SWTyp = Alternative(Token("script."), Token("script. fat-"))
    SchreibweisenPosition = Series(Token("SCHREIBWEISE"), Option(LZ), Required(SWTyp), Token(":"), Option(LZ), Required(SWVariante), ZeroOrMore(Series(ABS, SWVariante)), Option(LZ))
    ArtikelKopf = Synonym(SchreibweisenPosition)
    EtymologieVariante = RegExp('.*')
    EtymologieVarianten = OneOrMore(Series(NegativeLookahead(Series(Option(LZ), GROSSFOLGE)), EtymologieVariante))
    EtymologiePosition = Series(Token("ETYMOLOGIE"), Option(LZ), EtymologieVarianten)
    genus = Alternative(Token("maskulinum"), Token("m."), Token("femininum"), Token("f."), Token("neutrum"), Token("n."))
    FLEX = RE('-?[a-z]+')
    flexion = Series(FLEX, ZeroOrMore(Series(Token(","), Required(FLEX))))
    GrammatikVarianten = OneOrMore(Series(Option(Series(wortart, ABS)), flexion, Option(genus), Token(":"), Beleg, Required(ABS)))
    wortart.set(Alternative(Token("nomen"), Token("n."), Token("verb"), Token("v."), Token("adverb"), Token("adv."), Token("adjektiv"), Token("adj."), Token("praeposition"), Token("praep.")))
    GrammatikPosition = Series(Token("GRAMMATIK"), Option(LZ), Required(wortart), Required(ABS), Required(flexion), Option(genus), Required(ABS), Option(GrammatikVarianten))
    lzs_typ = RegExp('sim\\.')
    LemmaZusatz = Series(Token("ZUSATZ"), Required(lzs_typ))
    LemmaWort = Series(LAT_WORT_TEIL, ZeroOrMore(Series(Alternative(Token("|"), Token("-")), LAT_WORT_TEIL)))
    LemmaVarianten = Series(Option(LZ), OneOrMore(Series(LemmaWort, Required(TR))), Option(Series(LemmaZusatz, Required(ABS))))
    gesichert = Token("$")
    klassisch = Token("*")
    Lemma = Series(Option(klassisch), Option(gesichert), LemmaWort)
    LemmaPosition = Series(Token("LEMMA"), Option(LZ), Required(Lemma), Required(TR), Option(LemmaVarianten), Required(GrammatikPosition), Option(EtymologiePosition))
    Artikel = Series(Option(LZ), Required(LemmaPosition), Option(ArtikelKopf), Required(BedeutungsPosition), Required(ArtikelVerfasser), Option(LZ), DATEI_ENDE)
    root__ = Artikel
    
def get_grammar() -> MLWGrammar:
    global thread_local_MLW_grammar_singleton
    try:
        grammar = thread_local_MLW_grammar_singleton
    except NameError:
        thread_local_MLW_grammar_singleton = MLWGrammar()
        grammar = thread_local_MLW_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

MLW_AST_transformation_table = {
    # AST Transformations for the MLW-grammar
    "+": remove_empty,
    "Artikel": [],
    "LemmaPosition": [],
    "Lemma": [],
    "klassisch": [],
    "gesichert": [],
    "LemmaVarianten": [],
    "LemmaWort": [],
    "LemmaZusatz": [],
    "lzs_typ": [],
    "GrammatikPosition": [],
    "wortart": [replace_or_reduce],
    "GrammatikVarianten": [],
    "flexion": [],
    "FLEX": [],
    "genus": [replace_or_reduce],
    "EtymologiePosition": [],
    "EtymologieVarianten": [],
    "EtymologieVariante": [],
    "ArtikelKopf": [replace_by_single_child],
    "SchreibweisenPosition": [],
    "SWTyp": [replace_or_reduce],
    "SWVariante": [],
    "Schreibweise": [replace_by_single_child],
    "BedeutungsPosition": [],
    "Bedeutung": [],
    "Bedeutungskategorie": [],
    "Interpretamente": [],
    "LateinischeBedeutung": [],
    "DeutscheBedeutung": [],
    "Belege": [],
    "EinBeleg": [],
    "Zusatz": [],
    "ArtikelVerfasser": [],
    "Name": [],
    "SW_LAT": [replace_or_reduce],
    "SW_DEU": [replace_or_reduce],
    "SW_GRIECH": [replace_or_reduce],
    "Beleg": [replace_by_single_child],
    "Verweis": [],
    "VerweisZiel": [],
    "ZielName": [replace_by_single_child],
    "NAMENS_ABKÜRZUNG": [],
    "NAME": [],
    "DEU_WORT": [],
    "DEU_GROSS": [],
    "DEU_KLEIN": [],
    "LAT_WORT": [],
    "LAT_WORT_TEIL": [],
    "GROSSSCHRIFT": [],
    "GROSSFOLGE": [],
    "BUCHSTABENFOLGE": [],
    "ZEICHENFOLGE": [],
    "TR": [replace_or_reduce],
    "ABS": [replace_or_reduce],
    "LZ": [],
    "ZW": [],
    "ZWW": [],
    "LÜCKE": [],
    "LEERRAUM": [],
    "LEERZEILE": [],
    "RZS": [],
    "ZEILENSPRUNG": [],
    "KOMMENTARZEILEN": [],
    "DATEI_ENDE": [],
    "NIEMALS": [],
    ":Token, :RE": reduce_single_child,
    "*": replace_by_single_child
}


def MLWTransform() -> TransformationDict:
    return partial(traverse, processing_table=MLW_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    global thread_local_MLW_transformer_singleton
    try:
        transformer = thread_local_MLW_transformer_singleton
    except NameError:
        thread_local_MLW_transformer_singleton = MLWTransform()
        transformer = thread_local_MLW_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class MLWCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a MLW source file.
    """

    def __init__(self, grammar_name="MLW", grammar_source=""):
        super(MLWCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_Artikel(self, node):
        return node

    def on_LemmaPosition(self, node):
        pass

    def on_Lemma(self, node):
        pass

    def on_klassisch(self, node):
        pass

    def on_gesichert(self, node):
        pass

    def on_LemmaVarianten(self, node):
        pass

    def on_LemmaWort(self, node):
        pass

    def on_LemmaZusatz(self, node):
        pass

    def on_lzs_typ(self, node):
        pass

    def on_GrammatikPosition(self, node):
        pass

    def on_wortart(self, node):
        pass

    def on_GrammatikVarianten(self, node):
        pass

    def on_flexion(self, node):
        pass

    def on_FLEX(self, node):
        pass

    def on_genus(self, node):
        pass

    def on_EtymologiePosition(self, node):
        pass

    def on_EtymologieVarianten(self, node):
        pass

    def on_EtymologieVariante(self, node):
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

    def on_ArtikelVerfasser(self, node):
        pass

    def on_Name(self, node):
        pass

    def on_SW_LAT(self, node):
        pass

    def on_SW_DEU(self, node):
        pass

    def on_SW_GRIECH(self, node):
        pass

    def on_Beleg(self, node):
        pass

    def on_Verweis(self, node):
        pass

    def on_VerweisZiel(self, node):
        pass

    def on_ZielName(self, node):
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

    def on_GROSSFOLGE(self, node):
        pass

    def on_BUCHSTABENFOLGE(self, node):
        pass

    def on_ZEICHENFOLGE(self, node):
        pass

    def on_TR(self, node):
        pass

    def on_ABS(self, node):
        pass

    def on_LZ(self, node):
        pass

    def on_ZW(self, node):
        pass

    def on_ZWW(self, node):
        pass

    def on_LÜCKE(self, node):
        pass

    def on_LEERRAUM(self, node):
        pass

    def on_LEERZEILE(self, node):
        pass

    def on_RZS(self, node):
        pass

    def on_ZEILENSPRUNG(self, node):
        pass

    def on_KOMMENTARZEILEN(self, node):
        pass

    def on_DATEI_ENDE(self, node):
        pass

    def on_NIEMALS(self, node):
        pass


def get_compiler(grammar_name="MLW", grammar_source="") -> MLWCompiler:
    global thread_local_MLW_compiler_singleton
    try:
        compiler = thread_local_MLW_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_MLW_compiler_singleton = \
            MLWCompiler(grammar_name, grammar_source)
        compiler = thread_local_MLW_compiler_singleton
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
        print("Usage: MLWCompiler.py [FILENAME]")
