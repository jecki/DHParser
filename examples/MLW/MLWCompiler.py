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
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, SomeOf, \
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
    
    # TODO: Vervollständigen!!!!
    
    
    @ comment         =  /#.*/            # Kommentare beginnen mit '#' und reichen bis zum Zeilenende
                                          # ohne das Zeilenende zu beinhalten
    @ whitespace      =  /[\t ]*/         # Zeilensprünge zählen nicht als Leerraum
    @ literalws       =  right            # Leerraum vor und nach Literalen wird automatisch entfernt
    
    
    ##############################################################################
    
    Artikel           = [LZ]
                        §{ LemmaPosition }+
                        [EtymologiePosition]
                        [ArtikelKopf]
                        BedeutungsPosition
                        [VerweisPosition]
                        { UnterArtikel }
                        ArtikelVerfasser
                        [LZ]  DATEI_ENDE
    
    
    #### LEMMA-POSITION ##########################################################
    
    LemmaPosition     = [ABS] "LEMMA" [LZ] §Lemma TR [LemmaVarianten]
                        GrammatikPosition [Zusatz]
    
    Lemma             = [< klassisch | gesichert >] LemmaWort
      klassisch       = "*"
      gesichert       = "$"  # TODO: Noch fragen: Welches Zeichen?
    
    LemmaWort         = LAT_WORT
    
    LemmaVarianten    = LemmaVariante { [TR] LemmaVariante }
                        [[TR] Zusatz]
    
    LemmaVariante     = LAT_WORT
    
    
    ## GRAMMATIK-POSITION ##
    
    GrammatikPosition = ZWW "GRAMMATIK" [LZ] §Grammatik { ABS GrammatikVariante }
    
    Grammatik        = wortart §ABS flexion [genus]
    
    wortart          = "nomen"  | "n."
                     | "verb"   | "v."
                     | "adverb" | "adv."
                     | "adjektiv" | "adj."
                     | "praeposition" | "praep."
    
    flexion          = deklination | konjugation
    deklination      = FLEX ["," FLEX]
    konjugation      = FLEX
    FLEX             = /-?[a-z]+/~
    
    genus            = "maskulinum" | "m."
                     | "femininum" | "f."
                     | "neutrum" | "n."
    
    GrammatikVariante  = [wortart ABS] flexion [genus] DPP Beleg { FORTSETZUNG Beleg }   # Beleg { SEM Beleg }
    
    
    
    #### ETYMOLOGIE-POSITION #####################################################
    
    EtymologiePosition = ZWW "ETYMOLOGIE" [LZ] { EtymologieVariante }+
    EtymologieVariante = LAT | GRI [EtymologieBesonderheit] ["ETYM" Etymologie] DPP Beleg
    EtymologieBesonderheit = EINZEILER
    Etymologie         = EINZEILER
    
    
    #### ARTIKEL-KOPF ############################################################
    
    ArtikelKopf     = <   SchreibweisenPosition
                        | StrukturPosition
                        | GebrauchPosition
                        | MetrikPosition
                        | VerwechselungPosition >
    
    SchreibweisenPosition = ZWW "SCHREIBWEISE"  Position
    StrukturPosition      = ZWW "STRUKTUR"      Position
    GebrauchPosition      = ZWW "GEBRAUCH"      Position
    MetrikPosition        = ZWW "METRIK"        Position
    VerwechselungPosition = ZWW "VERWECHSELBAR" Position
    
    ## ARTIKELKOPF POSITIONEN ##
    
    Position       = [LZ] §Kategorien
    Kategorien     = Kategorie { ZWW Kategorie }
    Kategorie      = Besonderheit §DPP [LZ] ( Varianten | Kategorien )
    Besonderheit   = EINZEILER
    Varianten      = Variante { ZWW Variante }
    Variante       = !KATEGORIENZEILE Gegenstand DPP Belege
    Gegenstand     = EINZEILER
    
    
    #### BEDEUTUNGS-POSITION #####################################################
    
    BedeutungsPosition   = { ZWW "BEDEUTUNG" [LZ] §Bedeutung }+
    
    Bedeutung            = (Interpretamente | Bedeutungskategorie) [BelegPosition]
    Bedeutungskategorie  = /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~ [LZ]
    Interpretamente      = LateinischeBedeutung [LZ] §DeutscheBedeutung
    LateinischeBedeutung = LAT [LZ] LateinischerAusdruck { <","|ZW> LateinischerAusdruck }
    DeutscheBedeutung    = DEU [LZ] DeutscherAusdruck { <","|ZW> DeutscherAusdruck }
    
    LateinischerAusdruck = LAT_WORT { //~ LAT_WORT } [/\s*/ BedeutungsQualifikation]
    DeutscherAusdruck    = DEU_WORT { //~ DEU_WORT } [/\s*/ BedeutungsQualifikation]
    
    BedeutungsQualifikation = "[" EINZEILER { <SEM|ZW> EINZEILER } §"]"
    
    BelegPosition = ZWW "BELEGE" ZWW Belege
    
    
    #### VERWEIS-POSITION #####################################################
    
    VerweisPosition = ZWW "VERWEISE"
    
    
    #### UNTER-ARTIKEL ########################################################
    
    UnterArtikel = ZWW "UNTER-ARTIKEL"
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    ArtikelVerfasser = ZWW ("AUTORIN" | "AUTOR") Name
    Name             = { NAME | NAMENS_ABKÜRZUNG }+
    
    
    
    #### Schlüsselwörter #########################################################
    
    LAT = "LATEINISCH" | "LAT"
    DEU = "DEUTSCH" | "DEU"
    GRI = "GRIECHISCH" | "GRIECH" | "GRIE" | "GRI"
    
    SCHLUESSELWORT   = { //~ /\n/ }+ !ROEMISCHE_ZAHL /[A-ZÄÖÜ]{3,}\s+/
    
    
    
    #### ZUSATZ an verschiedenen Stellen der Struktur ############################
    
    Zusatz       = "ZUSATZ" §{ [TR] zusatz_typ }+
      zusatz_typ = "adde" | "al" | "sim." | "saepe" | "vel-rarius" | "vel" | EINZEILER
    
    
    
    #### BELEGE ##################################################################
    
    Belege           = ["*"] Beleg { [LZ] "*" Beleg }
    Beleg            = (Verweis [Zitat]) | Zitat
    Zitat            = Quellenangabe { SEM [ZW] [Anker] <Stelle | Verweis> [[ZW] BelegText] } [[TR] Zusatz]
    Quellenangabe    = [Anker] < BelegQuelle | Verweis >
    BelegQuelle      = Autor DPP Werk
    BelegText        = /"/ MEHRZEILER §/"/~ ["."]
    
    Verweis          = "->" §Anker
    Anker            = "{" ZielID §"}"
    ZielID           = FREITEXT
    
    Autor     = EINZEILER
    Werk      = EINZEILER
    Stelle    = EINZEILER
    Datierung = EINZEILER
    Edition   = EINZEILER
    
    
    #### GENERISCHE UND ATOMARE AUSDRÜCKE ########################################
    
    NAMENS_ABKÜRZUNG = /[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\./~
    NAME             = /[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+/~
    
    DEU_WORT         = DEU_GROSS | DEU_KLEIN | GROSSBUCHSTABE
    DEU_GROSS        = /[A-ZÄÖÜ][a-zäöüßę_\-]+/~
    GROSSBUCHSTABE   = /[A-ZÄÖÜ](?=[ \t\n])/~
    KLEINBUCHSTABE   = /[a-zäöü](?=[ \t\n])/~
    DEU_KLEIN        = /(?!-)[a-zäöüßę_\-]+/~
    LAT_WORT         = /(?!-)[a-z|\-_]+/~
    GROSSSCHRIFT     = /(?!-)[A-ZÄÖÜ_\-]+/~
    ZAHL             = /[\d_]+/~
    ROEMISCHE_ZAHL   = /(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\w])/~
    
    SATZZEICHEN      = /(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|[.()\[\]\-]+)/~  # div. Satzzeichen, aber keine doppelten ,, ;; oder ::
    
    BUCHSTABENFOLGE  = /\w+/~
    ZEICHENFOLGE     = /[\w()-]+/~
    # EINZEILER        = /[\w()-. \t]+/~
    TEXTELEMENT      = DEU_WORT | ZAHL | ROEMISCHE_ZAHL
    EINZEILER        = { TEXTELEMENT | /(?!->)[.()\-]+/~ | /,(?!,)/~ }+
    FREITEXT         = { TEXTELEMENT | SATZZEICHEN | GROSSSCHRIFT }+
    MEHRZEILER       = { FREITEXT | /\s+(?=[\w,;:.\(\)\-])/ }+
    
    TR               = ABS | LZ                  # (beliebiger) Trenner
    ABS              = /\s*;;?\s*/ | ZWW         # Abschluss (durch Semikolon oder Zeilenwechsel)
    # ZW               = /\n/~                   # Zeilenwechsel
    LZ               = /\s+/                     # Leerzeichen oder -zeilen
    DPP              = /::?/~                    # Doppelpunkt als Trenner
    SEM              = /;;?/~                    # Semikolon als Trenner
    
    ZW               = !LÜCKE ZEILENSPRUNG       # Zeilenwechsel, aber keine Leerzeile(n)
    ZWW              = ZEILENSPRUNG [ LEERRAUM ] # mindestens ein Zeilenwechsel
    LÜCKE            = KOMMENTARZEILEN LEERZEILE [LEERRAUM] # Leerraum mit mindestens einer echten Leerzeile
    LEERRAUM         = { COMMENT__ | /\s+/ }+   # beliebiger horizontaler oder vertikaler Leerraum
    LEERZEILE        = /[ \t]*(?:\n[ \t]*)+\n/ ~/\n?/ # eine oder mehrere echte LEERZEILEN
    RZS              = /\s*?\n|$/               # Rückwärtiger Zeilensprung oder Textanfang
    
    ZEILENSPRUNG     = /[ \t]*\n/~
    KOMMENTARZEILEN  = { /[ \t]*\n?[ \t]*/ COMMENT__ }  # echte Kommentarzeilen
    KATEGORIENZEILE  = /[^:\n]+[:][ \t]*\n/     # Kategorienzeilen enthalten genau einen Doppelpunkt am Ende der Zeile
    FORTSETZUNG      = !(ZWW /[^:\n]+[:]/)
    
    DATEI_ENDE       = !/./
    NIEMALS          = /(?!.)/
    
    DUMMY            = "EBNF-Grammatik an dieser Stelle noch nicht definiert!"
    """
    DEU_WORT = Forward()
    FREITEXT = Forward()
    GROSSSCHRIFT = Forward()
    Kategorien = Forward()
    ROEMISCHE_ZAHL = Forward()
    SATZZEICHEN = Forward()
    TEXTELEMENT = Forward()
    ZAHL = Forward()
    ZWW = Forward()
    Zusatz = Forward()
    flexion = Forward()
    genus = Forward()
    wortart = Forward()
    source_hash__ = "7ff4250e122c3a05f3c28e3724c7522d"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'#.*'
    WHITESPACE__ = r'[\t ]*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    DUMMY = Token("EBNF-Grammatik an dieser Stelle noch nicht definiert!")
    NIEMALS = RegExp('(?!.)')
    DATEI_ENDE = NegativeLookahead(RegExp('.'))
    FORTSETZUNG = NegativeLookahead(Series(ZWW, RegExp('[^:\\n]+[:]')))
    KATEGORIENZEILE = RegExp('[^:\\n]+[:][ \\t]*\\n')
    KOMMENTARZEILEN = ZeroOrMore(Series(RegExp('[ \\t]*\\n?[ \\t]*'), RegExp(COMMENT__)))
    ZEILENSPRUNG = RE('[ \\t]*\\n')
    RZS = RegExp('\\s*?\\n|$')
    LEERZEILE = Series(RegExp('[ \\t]*(?:\\n[ \\t]*)+\\n'), RE('\\n?', wR='', wL=WSP__))
    LEERRAUM = OneOrMore(Alternative(RegExp(COMMENT__), RegExp('\\s+')))
    LÜCKE = Series(KOMMENTARZEILEN, LEERZEILE, Option(LEERRAUM))
    ZWW.set(Series(ZEILENSPRUNG, Option(LEERRAUM)))
    ZW = Series(NegativeLookahead(LÜCKE), ZEILENSPRUNG)
    SEM = RE(';;?')
    DPP = RE('::?')
    LZ = RegExp('\\s+')
    ABS = Alternative(RegExp('\\s*;;?\\s*'), ZWW)
    TR = Alternative(ABS, LZ)
    MEHRZEILER = OneOrMore(Alternative(FREITEXT, RegExp('\\s+(?=[\\w,;:.\\(\\)\\-])')))
    FREITEXT.set(OneOrMore(Alternative(TEXTELEMENT, SATZZEICHEN, GROSSSCHRIFT)))
    EINZEILER = OneOrMore(Alternative(TEXTELEMENT, RE('(?!->)[.()\\-]+'), RE(',(?!,)')))
    TEXTELEMENT.set(Alternative(DEU_WORT, ZAHL, ROEMISCHE_ZAHL))
    ZEICHENFOLGE = RE('[\\w()-]+')
    BUCHSTABENFOLGE = RE('\\w+')
    SATZZEICHEN.set(RE('(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|[.()\\[\\]\\-]+)'))
    ROEMISCHE_ZAHL.set(RE('(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\\w])'))
    ZAHL.set(RE('[\\d_]+'))
    GROSSSCHRIFT.set(RE('(?!-)[A-ZÄÖÜ_\\-]+'))
    LAT_WORT = RE('(?!-)[a-z|\\-_]+')
    DEU_KLEIN = RE('(?!-)[a-zäöüßę_\\-]+')
    KLEINBUCHSTABE = RE('[a-zäöü](?=[ \\t\\n])')
    GROSSBUCHSTABE = RE('[A-ZÄÖÜ](?=[ \\t\\n])')
    DEU_GROSS = RE('[A-ZÄÖÜ][a-zäöüßę_\\-]+')
    DEU_WORT.set(Alternative(DEU_GROSS, DEU_KLEIN, GROSSBUCHSTABE))
    NAME = RE('[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+')
    NAMENS_ABKÜRZUNG = RE('[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\\.')
    Edition = Synonym(EINZEILER)
    Datierung = Synonym(EINZEILER)
    Stelle = Synonym(EINZEILER)
    Werk = Synonym(EINZEILER)
    Autor = Synonym(EINZEILER)
    ZielID = Synonym(FREITEXT)
    Anker = Series(Token("{"), ZielID, Token("}"), mandatory=2)
    Verweis = Series(Token("->"), Anker, mandatory=1)
    BelegText = Series(RegExp('"'), MEHRZEILER, RE('"'), Option(Token(".")), mandatory=2)
    BelegQuelle = Series(Autor, DPP, Werk)
    Quellenangabe = Series(Option(Anker), SomeOf(BelegQuelle, Verweis))
    Zitat = Series(Quellenangabe, ZeroOrMore(Series(SEM, Option(ZW), Option(Anker), SomeOf(Stelle, Verweis), Option(Series(Option(ZW), BelegText)))), Option(Series(Option(TR), Zusatz)))
    Beleg = Alternative(Series(Verweis, Option(Zitat)), Zitat)
    Belege = Series(Option(Token("*")), Beleg, ZeroOrMore(Series(Option(LZ), Token("*"), Beleg)))
    zusatz_typ = Alternative(Token("adde"), Token("al"), Token("sim."), Token("saepe"), Token("vel-rarius"), Token("vel"), EINZEILER)
    Zusatz.set(Series(Token("ZUSATZ"), OneOrMore(Series(Option(TR), zusatz_typ)), mandatory=1))
    SCHLUESSELWORT = Series(OneOrMore(Series(RE(''), RegExp('\\n'))), NegativeLookahead(ROEMISCHE_ZAHL), RegExp('[A-ZÄÖÜ]{3,}\\s+'))
    GRI = Alternative(Token("GRIECHISCH"), Token("GRIECH"), Token("GRIE"), Token("GRI"))
    DEU = Alternative(Token("DEUTSCH"), Token("DEU"))
    LAT = Alternative(Token("LATEINISCH"), Token("LAT"))
    Name = OneOrMore(Alternative(NAME, NAMENS_ABKÜRZUNG))
    ArtikelVerfasser = Series(ZWW, Alternative(Token("AUTORIN"), Token("AUTOR")), Name)
    UnterArtikel = Series(ZWW, Token("UNTER-ARTIKEL"))
    VerweisPosition = Series(ZWW, Token("VERWEISE"))
    BelegPosition = Series(ZWW, Token("BELEGE"), ZWW, Belege)
    BedeutungsQualifikation = Series(Token("["), EINZEILER, ZeroOrMore(Series(SomeOf(SEM, ZW), EINZEILER)), Token("]"), mandatory=3)
    DeutscherAusdruck = Series(DEU_WORT, ZeroOrMore(Series(RE(''), DEU_WORT)), Option(Series(RegExp('\\s*'), BedeutungsQualifikation)))
    LateinischerAusdruck = Series(LAT_WORT, ZeroOrMore(Series(RE(''), LAT_WORT)), Option(Series(RegExp('\\s*'), BedeutungsQualifikation)))
    DeutscheBedeutung = Series(DEU, Option(LZ), DeutscherAusdruck, ZeroOrMore(Series(SomeOf(Token(","), ZW), DeutscherAusdruck)))
    LateinischeBedeutung = Series(LAT, Option(LZ), LateinischerAusdruck, ZeroOrMore(Series(SomeOf(Token(","), ZW), LateinischerAusdruck)))
    Interpretamente = Series(LateinischeBedeutung, Option(LZ), DeutscheBedeutung, mandatory=2)
    Bedeutungskategorie = Series(RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+'), Option(LZ))
    Bedeutung = Series(Alternative(Interpretamente, Bedeutungskategorie), Option(BelegPosition))
    BedeutungsPosition = OneOrMore(Series(ZWW, Token("BEDEUTUNG"), Option(LZ), Bedeutung, mandatory=3))
    Gegenstand = Synonym(EINZEILER)
    Variante = Series(NegativeLookahead(KATEGORIENZEILE), Gegenstand, DPP, Belege)
    Varianten = Series(Variante, ZeroOrMore(Series(ZWW, Variante)))
    Besonderheit = Synonym(EINZEILER)
    Kategorie = Series(Besonderheit, DPP, Option(LZ), Alternative(Varianten, Kategorien), mandatory=1)
    Kategorien.set(Series(Kategorie, ZeroOrMore(Series(ZWW, Kategorie))))
    Position = Series(Option(LZ), Kategorien, mandatory=1)
    VerwechselungPosition = Series(ZWW, Token("VERWECHSELBAR"), Position)
    MetrikPosition = Series(ZWW, Token("METRIK"), Position)
    GebrauchPosition = Series(ZWW, Token("GEBRAUCH"), Position)
    StrukturPosition = Series(ZWW, Token("STRUKTUR"), Position)
    SchreibweisenPosition = Series(ZWW, Token("SCHREIBWEISE"), Position)
    ArtikelKopf = SomeOf(SchreibweisenPosition, StrukturPosition, GebrauchPosition, MetrikPosition, VerwechselungPosition)
    Etymologie = Synonym(EINZEILER)
    EtymologieBesonderheit = Synonym(EINZEILER)
    EtymologieVariante = Alternative(LAT, Series(GRI, Option(EtymologieBesonderheit), Option(Series(Token("ETYM"), Etymologie)), DPP, Beleg))
    EtymologiePosition = Series(ZWW, Token("ETYMOLOGIE"), Option(LZ), OneOrMore(EtymologieVariante))
    GrammatikVariante = Series(Option(Series(wortart, ABS)), flexion, Option(genus), DPP, Beleg, ZeroOrMore(Series(FORTSETZUNG, Beleg)))
    genus.set(Alternative(Token("maskulinum"), Token("m."), Token("femininum"), Token("f."), Token("neutrum"), Token("n.")))
    FLEX = RE('-?[a-z]+')
    konjugation = Synonym(FLEX)
    deklination = Series(FLEX, Option(Series(Token(","), FLEX)))
    flexion.set(Alternative(deklination, konjugation))
    wortart.set(Alternative(Token("nomen"), Token("n."), Token("verb"), Token("v."), Token("adverb"), Token("adv."), Token("adjektiv"), Token("adj."), Token("praeposition"), Token("praep.")))
    Grammatik = Series(wortart, ABS, flexion, Option(genus), mandatory=1)
    GrammatikPosition = Series(ZWW, Token("GRAMMATIK"), Option(LZ), Grammatik, ZeroOrMore(Series(ABS, GrammatikVariante)), mandatory=3)
    LemmaVariante = Synonym(LAT_WORT)
    LemmaVarianten = Series(LemmaVariante, ZeroOrMore(Series(Option(TR), LemmaVariante)), Option(Series(Option(TR), Zusatz)))
    LemmaWort = Synonym(LAT_WORT)
    gesichert = Token("$")
    klassisch = Token("*")
    Lemma = Series(Option(SomeOf(klassisch, gesichert)), LemmaWort)
    LemmaPosition = Series(Option(ABS), Token("LEMMA"), Option(LZ), Lemma, TR, Option(LemmaVarianten), GrammatikPosition, Option(Zusatz), mandatory=3)
    Artikel = Series(Option(LZ), OneOrMore(LemmaPosition), Option(EtymologiePosition), Option(ArtikelKopf), BedeutungsPosition, Option(VerweisPosition), ZeroOrMore(UnterArtikel), ArtikelVerfasser, Option(LZ), DATEI_ENDE, mandatory=1)
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
