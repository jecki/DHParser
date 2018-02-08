#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys
import webbrowser

sys.path.extend(['../', '../../'])

try:
    import regex as re
except ImportError:
    import re
from DHParser import is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, remove_nodes, remove_content, \
    remove_brackets, replace_parser, traverse_locally, remove_nodes, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    lstrip, rstrip, strip, keep_nodes, remove_anonymous_empty, has_parent, MockParser
from DHParser.log import logging


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
    
    
    @ comment         =  /(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)/   # Kommentare im C++ Stil
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
                        [Stellenverzeichnis]
                        [LZ] DATEI_ENDE
    
    
    #### LEMMA-POSITION ##########################################################
    
    LemmaPosition     = [ABS] "LEMMA" [LZ] §Lemma TR [LemmaVarianten]
                        GrammatikPosition [Zusatz]
    
    Lemma             = [< klassisch | gesichert >] LemmaWort
      klassisch       = "*"
      gesichert       = "$"  # TODO: Noch fragen: Welches Zeichen?
    
    LemmaWort         = LAT_WORT
    
    LemmaVarianten    = LemmaVariante { [";" | ","] [ZW] LemmaVariante } [ ABS Zusatz ]
    
    LemmaVariante     = LAT_WORT  # Ist eine Lemma immer ein einzelnes Wort?
    
    
    ## GRAMMATIK-POSITION ##
    
    GrammatikPosition = ZWW "GRAMMATIK" [LZ] §Grammatik { ABS GrammatikVariante }
    
    Grammatik        = wortart §ABS flexion [[";"] genus]
    
    wortart          = nomen | verb | adverb | adjektiv | praeposition
    nomen            = "nomen"  | "n."
    verb             = "verb"   | "v."
    adverb           = "adverb" | "adv."
    adjektiv         = "adjektiv" | "adj."
    praeposition     = "praeposition" | "praep."
    
    flexion          = deklination | konjugation
    deklination      = FLEX ["," FLEX]
    konjugation      = FLEX
    FLEX             = /-?[a-z]+/~
    
    genus            = maskulinum | femininum | neutrum
    maskulinum       = "maskulinum" | "m."
    femininum        = "femininum" | "f."
    neutrum          = "neutrum" | "n."
    
    
    GrammatikVariante  = [wortart ABS] flexion [[";"] genus] DPP Beleg { FORTSETZUNG Beleg }   # Beleg { SEM Beleg }
    
    
    
    #### ETYMOLOGIE-POSITION #####################################################
    
    EtymologiePosition = ZWW "ETYMOLOGIE" [LZ] { EtymologieVariante }+
    EtymologieVariante = LAT | GRI [EtymologieBesonderheit] ["ETYM" Etymologie] DPP Beleg
    EtymologieBesonderheit = EINZEILER
    Etymologie         = EINZEILER
    
    
    #### ARTIKEL-KOPF ############################################################
    
    ArtikelKopf     = <   SchreibweisenPosition
                        | StrukturPosition
                        | GebrauchsPosition
                        | MetrikPosition
                        | VerwechselungsPosition >
    
    SchreibweisenPosition = ZWW "SCHREIBWEISE"  Position
    StrukturPosition      = ZWW "STRUKTUR"      Position
    GebrauchsPosition     = ZWW "GEBRAUCH"      Position
    MetrikPosition        = ZWW "METRIK"        Position
    VerwechselungsPosition = ZWW "VERWECHSELBAR" Position
    
    ## ARTIKELKOPF POSITIONEN ##
    
    Position       = [LZ] §Kategorien
    Kategorien     = Kategorie { ZWW Kategorie }
    Kategorie      = Besonderheit §DPP [LZ] ( Varianten | Kategorien )
    Besonderheit   = EINZEILER
    Varianten      = Variante { ZWW Variante }
    Variante       = !KATEGORIENZEILE Gegenstand DPP Belege
    Gegenstand     = EINZEILER
    
    
    #### BEDEUTUNGS-POSITION #####################################################
    
    BedeutungsPosition   = { ZWW "BEDEUTUNG" [LZ] §Bedeutung [U1Bedeutung] }+
    U1Bedeutung          = { ZWW ("U_BEDEUTUNG" | "UNTER_BEDEUTUNG") [LZ] §Bedeutung [U2Bedeutung] }+
    U2Bedeutung          = { ZWW ("UU_BEDEUTUNG" | "UNTER_UNTER_BEDEUTUNG") [LZ] §Bedeutung [U3Bedeutung] }+
    U3Bedeutung          = { ZWW "UUU_BEDEUTUNG" [LZ] §Bedeutung [U4Bedeutung] }+
    U4Bedeutung          = { ZWW "UUUU_BEDEUTUNG" [LZ] §Bedeutung [U5Bedeutung] }+
    U5Bedeutung          = { ZWW "UUUUU_BEDEUTUNG" [LZ] §UntersteBedeutung }+
    
    Bedeutung            = (Interpretamente | Bedeutungskategorie) [BelegPosition]
    UntersteBedeutung    = Interpretamente [BelegPosition]
    Bedeutungskategorie  = { EINZEILER [LZ] [Zusatz] [LZ] } §":"
    
    Interpretamente      = LateinischeBedeutung (LZ | " " | "--") §DeutscheBedeutung [":"]
    LateinischeBedeutung = LAT [ZW] LateinischerAusdruck { "," [ZW] LateinischerAusdruck }
    DeutscheBedeutung    = DEU [ZW] DeutscherAusdruck { "," [ZW] DeutscherAusdruck }
    LateinischerAusdruck = { <LateinischesWort [Zusatz]> }+
    DeutscherAusdruck    = { <DeutschesWort [Zusatz]> }+
    LateinischesWort     = (LAT_WORT | "(" { LAT_WORT }+ ")")
    DeutschesWort        = (DEU_WORT | "(" { DEU_WORT }+ ")")
    
    LAT = "LATEINISCH" | "LAT"
    DEU = "DEUTSCH" | "DEU"
    GRI = "GRIECHISCH" | "GRIECH" | "GRIE" | "GRI"
    
    
    BelegPosition = ZWW ["BELEGE" [LZ]] Belege
    
    
    #### VERWEIS-POSITION ########################################################
    
    VerweisPosition = ZWW "VERWEISE"
    
    
    #### UNTER-ARTIKEL ###########################################################
    
    UnterArtikel = ZWW "UNTER-ARTIKEL"
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    ArtikelVerfasser = ZWW ("AUTORIN" | "AUTOR") §Name
    Name             = { NAME | NAMENS_ABKÜRZUNG | unbekannt }+
    unbekannt        = "unbekannt"
    
    #### STELLENVERZEICHNIS ######################################################
    
    Stellenverzeichnis = ZWW "STELLENVERZEICHNIS" [LemmaWort] ZWW Verweisliste
    Verweisliste       = { [LZ] "*" Stellenverweis }
    Stellenverweis     = BelegQuelle { [ABS] Stelle (NullVerweis | Verweis) }
    NullVerweis        = "{" "-" "}"
    
    
    #### ZUSATZ an verschiedenen Stellen der Struktur ############################
    
    Zusatz       = { "{" !("=>" | "@" | "^") §EinzelnerZusatz { ";;" EinzelnerZusatz } "}" }+  # mehrteilige Zusätze unnötig
      EinzelnerZusatz  = FesterZusatz | GemischterZusatz | FreierZusatz
      FesterZusatz     = adde | saepe | persaepe
        adde     = "adde"
        saepe    = "saepe"
        persaepe = "persaepe"
      GemischterZusatz = ( GebrauchsHinweis | PlurSingHinweis ) FreierZusatz
      GebrauchsHinweis = "usu"
      PlurSingHinweis  = "plur. sensu sing."
      FreierZusatz     = { FREITEXT | VerweisKern | Verweis }+
    
    
    #### BELEGE ##################################################################
    
    Belege           = ["*"] Beleg { [LZ] (SonderBelege | "*" Beleg) }
    SonderBelege     = "**" Beleg { [LZ] "**" Beleg }
    Beleg            = [Zusatz] ((Verweis [Zitat]) | Zitat) [ABS Zusatz] ["."]
    Zitat            = Quellenangabe { SEM [ZW] BelegStelle }
    Quellenangabe    = [<Anker | Zusatz>] < BelegQuelle | Verweis >
    BelegQuelle      = AutorWerk &SEM
    BelegStelle      = [<Anker | Zusatz>] (Stelle [[ZW] BelegText] | Verweis) [[ZW] Zusatz]
    BelegText        = /"/ { MEHRZEILER | Anker | Zusatz } §/"/~ ["."]
    
    AutorWerk = EINZEILER
    Werk      = EINZEILER
    Stelle    = EINZEILER
    Datierung = EINZEILER
    Edition   = EINZEILER
    
    
    #### VERWEISE (LINKS) ########################################################
    
    Verweis          = "{" VerweisKern "}"
    VerweisKern      = "=>" §((alias "|" ("-" | URL)) | URL)
    Anker            = "{" "@" §ziel "}"
    # URL              = [ ([protokoll] domäne /\//) | /\// ] { pfad /\// } ziel
    URL              = [protokoll] [/\//] { pfad /\// } ziel
    
    alias            = FREITEXT
    protokoll        = /\w+:\/\//
    # domäne           = /\w+\.\w+(?:\.\w+)*/
    pfad             = PFAD_NAME # /\w+/
    ziel             = PFAD_NAME # /[\w=?.%&\[\] ]+/
    
    
    #### GENERISCHE UND ATOMARE AUSDRÜCKE ########################################
    
    PFAD_NAME        = /[\w=?.%&\[\] ]+/
    
    NAMENS_ABKÜRZUNG = /[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\./~
    NAME             = /[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+/~
    
    DEU_WORT         = DEU_GROSS | DEU_KLEIN | GROSSBUCHSTABE
    DEU_GROSS        = /[A-ZÄÖÜ][a-zäöüßę_\-.]+/~
    GROSSBUCHSTABE   = /[A-ZÄÖÜ](?=[ \t\n])/~
    KLEINBUCHSTABE   = /[a-zäöü](?=[ \t\n])/~
    GRI_BUCHSTABE    = /[αβγδεζηθικλμνξοπρςστυφχψω]/
    DEU_KLEIN        = /(?!--)[a-zäöüßęõ_\-.]+/~
    LAT_WORT         = /(?!--)[a-z|\-_.]+/~
    GROSSSCHRIFT     = /(?!--)[A-ZÄÖÜ_\-]+/~
    ZAHL             = /[\d]+/~
    SEITENZAHL       = /[\d]+(?:\^(?:(?:\{[\d\w.,!? ]+\})|[\d\w.]+))?/~     # Zahl mit optionale folgendem hochgestelltem Buchstaben oder Text
    ROEMISCHE_ZAHL   = /(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\w])/~
    SCHLUESSELWORT   = { //~ /\n/ }+ !ROEMISCHE_ZAHL /[A-ZÄÖÜ]{3,}\s+/
    
    SATZZEICHEN      = /(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|(?:-(?!-))|[.()\[\]]+)|[`''‘’?]/~  # div. Satzzeichen, aber keine doppelten ,, ;; oder ::
    TEIL_SATZZEICHEN = /(?!->)(?:(?:,(?!,))|(?:-(?!-))|[.()]+)|[`''‘’?]/~ # Satzeichen bis auf Doppelpunkt ":", Semikolon ";" und eckige Klammern
    
    BUCHSTABENFOLGE  = /\w+/~
    ZEICHENFOLGE     = /[\w()-]+/~
    TEXTELEMENT      = DEU_WORT | SEITENZAHL | ROEMISCHE_ZAHL
    EINZEILER        = { TEXTELEMENT | TEIL_SATZZEICHEN }+
    FREITEXT         = { TEXTELEMENT | SATZZEICHEN | GROSSSCHRIFT }+
    MEHRZEILER       = { FREITEXT | /\s+(?=[\w,;:.\(\)\-])/ | /\n\s*/ }+
    
    TR               = ABS | LZ                  # (beliebiger) Trenner
    ABS              = /\s*;;?\s*/ | ZWW         # Abschluss (durch Semikolon oder Zeilenwechsel)
    # ZW               = /\n/~                   # Zeilenwechsel
    LZ               = { COMMENT__ | /\s+/ }+    # Leerzeichen oder -zeilen
    DPP              = /::?/~                    # Doppelpunkt als Trenner
    SEM              = /;;?/~                    # Semikolon als Trenner
    
    ZW               = !LÜCKE ZEILENSPRUNG       # Zeilenwechsel, aber keine Leerzeile(n)
    ZWW              = ZEILENSPRUNG [ LZ ]       # mindestens ein Zeilenwechsel
    LÜCKE            = KOMMENTARZEILEN LEERZEILE [LZ] # Leerraum mit mindestens einer echten Leerzeile
    LEERZEILE        = /[ \t]*(?:\n[ \t]*)+\n/ ~/\n?/ # eine oder mehrere echte LEERZEILEN
    RZS              = /\s*?\n|$/               # Rückwärtiger Zeilensprung oder Textanfang
    
    ZEILENSPRUNG     = /[ \t]*\n/~
    KOMMENTARZEILEN  = { /[ \t]*\n?[ \t]*/ COMMENT__ }  # echte Kommentarzeilen
    KATEGORIENZEILE  = /[^:\n]+[:][ \t]*\n/     # Kategorienzeilen enthalten genau einen Doppelpunkt am Ende der Zeile
    FORTSETZUNG      = !(ZWW /[^:\n]+[:]/)
    
    DATEI_ENDE       = !/./
    NIEMALS          = /(?!.)/
    """
    DEU_WORT = Forward()
    FREITEXT = Forward()
    GROSSSCHRIFT = Forward()
    Kategorien = Forward()
    LZ = Forward()
    LemmaWort = Forward()
    ROEMISCHE_ZAHL = Forward()
    SATZZEICHEN = Forward()
    SEITENZAHL = Forward()
    TEIL_SATZZEICHEN = Forward()
    TEXTELEMENT = Forward()
    ZWW = Forward()
    Zusatz = Forward()
    flexion = Forward()
    genus = Forward()
    wortart = Forward()
    source_hash__ = "006973bb80648bce916ec3ac284ba94f"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)'
    WHITESPACE__ = r'[\t ]*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    NIEMALS = RegExp('(?!.)')
    DATEI_ENDE = NegativeLookahead(RegExp('.'))
    FORTSETZUNG = NegativeLookahead(Series(ZWW, RegExp('[^:\\n]+[:]')))
    KATEGORIENZEILE = RegExp('[^:\\n]+[:][ \\t]*\\n')
    KOMMENTARZEILEN = ZeroOrMore(Series(RegExp('[ \\t]*\\n?[ \\t]*'), RegExp(COMMENT__)))
    ZEILENSPRUNG = RE('[ \\t]*\\n')
    RZS = RegExp('\\s*?\\n|$')
    LEERZEILE = Series(RegExp('[ \\t]*(?:\\n[ \\t]*)+\\n'), RE('\\n?', wR='', wL=WSP__))
    LÜCKE = Series(KOMMENTARZEILEN, LEERZEILE, Option(LZ))
    ZWW.set(Series(ZEILENSPRUNG, Option(LZ)))
    ZW = Series(NegativeLookahead(LÜCKE), ZEILENSPRUNG)
    SEM = RE(';;?')
    DPP = RE('::?')
    LZ.set(OneOrMore(Alternative(RegExp(COMMENT__), RegExp('\\s+'))))
    ABS = Alternative(RegExp('\\s*;;?\\s*'), ZWW)
    TR = Alternative(ABS, LZ)
    MEHRZEILER = OneOrMore(Alternative(FREITEXT, RegExp('\\s+(?=[\\w,;:.\\(\\)\\-])'), RegExp('\\n\\s*')))
    FREITEXT.set(OneOrMore(Alternative(TEXTELEMENT, SATZZEICHEN, GROSSSCHRIFT)))
    EINZEILER = OneOrMore(Alternative(TEXTELEMENT, TEIL_SATZZEICHEN))
    TEXTELEMENT.set(Alternative(DEU_WORT, SEITENZAHL, ROEMISCHE_ZAHL))
    ZEICHENFOLGE = RE('[\\w()-]+')
    BUCHSTABENFOLGE = RE('\\w+')
    TEIL_SATZZEICHEN.set(RE("(?!->)(?:(?:,(?!,))|(?:-(?!-))|[.()]+)|[`''‘’?]"))
    SATZZEICHEN.set(RE("(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|(?:-(?!-))|[.()\\[\\]]+)|[`''‘’?]"))
    SCHLUESSELWORT = Series(OneOrMore(Series(RE(''), RegExp('\\n'))), NegativeLookahead(ROEMISCHE_ZAHL), RegExp('[A-ZÄÖÜ]{3,}\\s+'))
    ROEMISCHE_ZAHL.set(RE('(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\\w])'))
    SEITENZAHL.set(RE('[\\d]+(?:\\^(?:(?:\\{[\\d\\w.,!? ]+\\})|[\\d\\w.]+))?'))
    ZAHL = RE('[\\d]+')
    GROSSSCHRIFT.set(RE('(?!--)[A-ZÄÖÜ_\\-]+'))
    LAT_WORT = RE('(?!--)[a-z|\\-_.]+')
    DEU_KLEIN = RE('(?!--)[a-zäöüßęõ_\\-.]+')
    GRI_BUCHSTABE = RegExp('[αβγδεζηθικλμνξοπρςστυφχψω]')
    KLEINBUCHSTABE = RE('[a-zäöü](?=[ \\t\\n])')
    GROSSBUCHSTABE = RE('[A-ZÄÖÜ](?=[ \\t\\n])')
    DEU_GROSS = RE('[A-ZÄÖÜ][a-zäöüßę_\\-.]+')
    DEU_WORT.set(Alternative(DEU_GROSS, DEU_KLEIN, GROSSBUCHSTABE))
    NAME = RE('[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+')
    NAMENS_ABKÜRZUNG = RE('[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\\.')
    PFAD_NAME = RegExp('[\\w=?.%&\\[\\] ]+')
    ziel = Synonym(PFAD_NAME)
    pfad = Synonym(PFAD_NAME)
    protokoll = RegExp('\\w+://')
    alias = Synonym(FREITEXT)
    URL = Series(Option(protokoll), Option(RegExp('/')), ZeroOrMore(Series(pfad, RegExp('/'))), ziel)
    Anker = Series(Token("{"), Token("@"), ziel, Token("}"), mandatory=2)
    VerweisKern = Series(Token("=>"), Alternative(Series(alias, Token("|"), Alternative(Token("-"), URL)), URL), mandatory=1)
    Verweis = Series(Token("{"), VerweisKern, Token("}"))
    Edition = Synonym(EINZEILER)
    Datierung = Synonym(EINZEILER)
    Stelle = Synonym(EINZEILER)
    Werk = Synonym(EINZEILER)
    AutorWerk = Synonym(EINZEILER)
    BelegText = Series(RegExp('"'), ZeroOrMore(Alternative(MEHRZEILER, Anker, Zusatz)), RE('"'), Option(Token(".")), mandatory=2)
    BelegStelle = Series(Option(SomeOf(Anker, Zusatz)), Alternative(Series(Stelle, Option(Series(Option(ZW), BelegText))), Verweis), Option(Series(Option(ZW), Zusatz)))
    BelegQuelle = Series(AutorWerk, Lookahead(SEM))
    Quellenangabe = Series(Option(SomeOf(Anker, Zusatz)), SomeOf(BelegQuelle, Verweis))
    Zitat = Series(Quellenangabe, ZeroOrMore(Series(SEM, Option(ZW), BelegStelle)))
    Beleg = Series(Option(Zusatz), Alternative(Series(Verweis, Option(Zitat)), Zitat), Option(Series(ABS, Zusatz)), Option(Token(".")))
    SonderBelege = Series(Token("**"), Beleg, ZeroOrMore(Series(Option(LZ), Token("**"), Beleg)))
    Belege = Series(Option(Token("*")), Beleg, ZeroOrMore(Series(Option(LZ), Alternative(SonderBelege, Series(Token("*"), Beleg)))))
    FreierZusatz = OneOrMore(Alternative(FREITEXT, VerweisKern, Verweis))
    PlurSingHinweis = Token("plur. sensu sing.")
    GebrauchsHinweis = Token("usu")
    GemischterZusatz = Series(Alternative(GebrauchsHinweis, PlurSingHinweis), FreierZusatz)
    persaepe = Token("persaepe")
    saepe = Token("saepe")
    adde = Token("adde")
    FesterZusatz = Alternative(adde, saepe, persaepe)
    EinzelnerZusatz = Alternative(FesterZusatz, GemischterZusatz, FreierZusatz)
    Zusatz.set(OneOrMore(Series(Token("{"), NegativeLookahead(Alternative(Token("=>"), Token("@"), Token("^"))), EinzelnerZusatz, ZeroOrMore(Series(Token(";;"), EinzelnerZusatz)), Token("}"), mandatory=2)))
    NullVerweis = Series(Token("{"), Token("-"), Token("}"))
    Stellenverweis = Series(BelegQuelle, ZeroOrMore(Series(Option(ABS), Stelle, Alternative(NullVerweis, Verweis))))
    Verweisliste = ZeroOrMore(Series(Option(LZ), Token("*"), Stellenverweis))
    Stellenverzeichnis = Series(ZWW, Token("STELLENVERZEICHNIS"), Option(LemmaWort), ZWW, Verweisliste)
    unbekannt = Token("unbekannt")
    Name = OneOrMore(Alternative(NAME, NAMENS_ABKÜRZUNG, unbekannt))
    ArtikelVerfasser = Series(ZWW, Alternative(Token("AUTORIN"), Token("AUTOR")), Name, mandatory=2)
    UnterArtikel = Series(ZWW, Token("UNTER-ARTIKEL"))
    VerweisPosition = Series(ZWW, Token("VERWEISE"))
    BelegPosition = Series(ZWW, Option(Series(Token("BELEGE"), Option(LZ))), Belege)
    GRI = Alternative(Token("GRIECHISCH"), Token("GRIECH"), Token("GRIE"), Token("GRI"))
    DEU = Alternative(Token("DEUTSCH"), Token("DEU"))
    LAT = Alternative(Token("LATEINISCH"), Token("LAT"))
    DeutschesWort = Alternative(DEU_WORT, Series(Token("("), OneOrMore(DEU_WORT), Token(")")))
    LateinischesWort = Alternative(LAT_WORT, Series(Token("("), OneOrMore(LAT_WORT), Token(")")))
    DeutscherAusdruck = OneOrMore(AllOf(DeutschesWort, Option(Zusatz)))
    LateinischerAusdruck = OneOrMore(AllOf(LateinischesWort, Option(Zusatz)))
    DeutscheBedeutung = Series(DEU, Option(ZW), DeutscherAusdruck, ZeroOrMore(Series(Token(","), Option(ZW), DeutscherAusdruck)))
    LateinischeBedeutung = Series(LAT, Option(ZW), LateinischerAusdruck, ZeroOrMore(Series(Token(","), Option(ZW), LateinischerAusdruck)))
    Interpretamente = Series(LateinischeBedeutung, Alternative(LZ, Token(" "), Token("--")), DeutscheBedeutung, Option(Token(":")), mandatory=2)
    Bedeutungskategorie = Series(ZeroOrMore(Series(EINZEILER, Option(LZ), Option(Zusatz), Option(LZ))), Token(":"), mandatory=1)
    UntersteBedeutung = Series(Interpretamente, Option(BelegPosition))
    Bedeutung = Series(Alternative(Interpretamente, Bedeutungskategorie), Option(BelegPosition))
    U5Bedeutung = OneOrMore(Series(ZWW, Token("UUUUU_BEDEUTUNG"), Option(LZ), UntersteBedeutung, mandatory=3))
    U4Bedeutung = OneOrMore(Series(ZWW, Token("UUUU_BEDEUTUNG"), Option(LZ), Bedeutung, Option(U5Bedeutung), mandatory=3))
    U3Bedeutung = OneOrMore(Series(ZWW, Token("UUU_BEDEUTUNG"), Option(LZ), Bedeutung, Option(U4Bedeutung), mandatory=3))
    U2Bedeutung = OneOrMore(Series(ZWW, Alternative(Token("UU_BEDEUTUNG"), Token("UNTER_UNTER_BEDEUTUNG")), Option(LZ), Bedeutung, Option(U3Bedeutung), mandatory=3))
    U1Bedeutung = OneOrMore(Series(ZWW, Alternative(Token("U_BEDEUTUNG"), Token("UNTER_BEDEUTUNG")), Option(LZ), Bedeutung, Option(U2Bedeutung), mandatory=3))
    BedeutungsPosition = OneOrMore(Series(ZWW, Token("BEDEUTUNG"), Option(LZ), Bedeutung, Option(U1Bedeutung), mandatory=3))
    Gegenstand = Synonym(EINZEILER)
    Variante = Series(NegativeLookahead(KATEGORIENZEILE), Gegenstand, DPP, Belege)
    Varianten = Series(Variante, ZeroOrMore(Series(ZWW, Variante)))
    Besonderheit = Synonym(EINZEILER)
    Kategorie = Series(Besonderheit, DPP, Option(LZ), Alternative(Varianten, Kategorien), mandatory=1)
    Kategorien.set(Series(Kategorie, ZeroOrMore(Series(ZWW, Kategorie))))
    Position = Series(Option(LZ), Kategorien, mandatory=1)
    VerwechselungsPosition = Series(ZWW, Token("VERWECHSELBAR"), Position)
    MetrikPosition = Series(ZWW, Token("METRIK"), Position)
    GebrauchsPosition = Series(ZWW, Token("GEBRAUCH"), Position)
    StrukturPosition = Series(ZWW, Token("STRUKTUR"), Position)
    SchreibweisenPosition = Series(ZWW, Token("SCHREIBWEISE"), Position)
    ArtikelKopf = SomeOf(SchreibweisenPosition, StrukturPosition, GebrauchsPosition, MetrikPosition, VerwechselungsPosition)
    Etymologie = Synonym(EINZEILER)
    EtymologieBesonderheit = Synonym(EINZEILER)
    EtymologieVariante = Alternative(LAT, Series(GRI, Option(EtymologieBesonderheit), Option(Series(Token("ETYM"), Etymologie)), DPP, Beleg))
    EtymologiePosition = Series(ZWW, Token("ETYMOLOGIE"), Option(LZ), OneOrMore(EtymologieVariante))
    GrammatikVariante = Series(Option(Series(wortart, ABS)), flexion, Option(Series(Option(Token(";")), genus)), DPP, Beleg, ZeroOrMore(Series(FORTSETZUNG, Beleg)))
    neutrum = Alternative(Token("neutrum"), Token("n."))
    femininum = Alternative(Token("femininum"), Token("f."))
    maskulinum = Alternative(Token("maskulinum"), Token("m."))
    genus.set(Alternative(maskulinum, femininum, neutrum))
    FLEX = RE('-?[a-z]+')
    konjugation = Synonym(FLEX)
    deklination = Series(FLEX, Option(Series(Token(","), FLEX)))
    flexion.set(Alternative(deklination, konjugation))
    praeposition = Alternative(Token("praeposition"), Token("praep."))
    adjektiv = Alternative(Token("adjektiv"), Token("adj."))
    adverb = Alternative(Token("adverb"), Token("adv."))
    verb = Alternative(Token("verb"), Token("v."))
    nomen = Alternative(Token("nomen"), Token("n."))
    wortart.set(Alternative(nomen, verb, adverb, adjektiv, praeposition))
    Grammatik = Series(wortart, ABS, flexion, Option(Series(Option(Token(";")), genus)), mandatory=1)
    GrammatikPosition = Series(ZWW, Token("GRAMMATIK"), Option(LZ), Grammatik, ZeroOrMore(Series(ABS, GrammatikVariante)), mandatory=3)
    LemmaVariante = Synonym(LAT_WORT)
    LemmaVarianten = Series(LemmaVariante, ZeroOrMore(Series(Option(Alternative(Token(";"), Token(","))), Option(ZW), LemmaVariante)), Option(Series(ABS, Zusatz)))
    LemmaWort.set(Synonym(LAT_WORT))
    gesichert = Token("$")
    klassisch = Token("*")
    Lemma = Series(Option(SomeOf(klassisch, gesichert)), LemmaWort)
    LemmaPosition = Series(Option(ABS), Token("LEMMA"), Option(LZ), Lemma, TR, Option(LemmaVarianten), GrammatikPosition, Option(Zusatz), mandatory=3)
    Artikel = Series(Option(LZ), OneOrMore(LemmaPosition), Option(EtymologiePosition), Option(ArtikelKopf), BedeutungsPosition, Option(VerweisPosition), ZeroOrMore(UnterArtikel), ArtikelVerfasser, Option(Stellenverzeichnis), Option(LZ), DATEI_ENDE, mandatory=1)
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

LemmaVariante_table = {
    "LAT_WORT, DEU_WORT": [remove_whitespace, reduce_single_child],
    "Zusatz": [reduce_single_child]
}

def content_from_parser_name(context):
    assert not context[-1].result
    context[-1].result = context[-1].tag_name

MLW_AST_transformation_table = {
    # AST Transformations for the MLW-grammar
    "+": [remove_anonymous_empty, remove_nodes('ZWW', 'ZW', 'LZ', 'DPP', 'COMMENT__', 'ABS', 'SEM', 'TR'),
          remove_tokens(":")],
    "Autor": [reduce_single_child],
    "Artikel": [],
    "LemmaPosition": [],
    "Lemma": [],
    "klassisch": [reduce_single_child],
    "gesichert": [reduce_single_child],
    "LemmaWort": [reduce_single_child],
    "LemmaVariante": [reduce_single_child, traverse_locally(LemmaVariante_table)],
    "LemmaVarianten": [flatten],
    "LemmaZusatz": [],
    "lzs_typ": [],
    "GrammatikPosition": [flatten],
    "wortart": [replace_or_reduce],
    "GrammatikVarianten": [],
    "flexion": [],
    "deklination": [],
    "konjugation": [],
    "FLEX": [remove_whitespace, reduce_single_child],
    "genus": [replace_or_reduce],
    "nomen, verb, adverb, adjektiv, praeposition": [content_from_parser_name],
    "maskulinum, femininum, neutrum": [content_from_parser_name],
    "EtymologiePosition": [],
    "EtymologieVarianten": [],
    "EtymologieVariante": [],
    "ArtikelKopf": [replace_by_single_child],
    "SchreibweisenPosition, StrukturPosition, VerwechselungsPosition, GebrauchsPosition":
        [],
    "SWTyp": [replace_or_reduce],
    "SWVariante": [],
    "Schreibweise": [replace_by_single_child],
    "Kategorie": [],
    "Varianten": [flatten],
    "Variante": [],
    "Gegenstand": [reduce_single_child],
    "Besonderheit": [reduce_single_child],
    "BedeutungsPosition": [flatten, remove_tokens("BEDEUTUNG")],
    "Bedeutung": [],
    "U1Bedeutung, U2Bedeutung, U3Bedeutung, U4Bedeutung, U5Bedeutung":
        [flatten],
    "Bedeutungskategorie": [flatten],
    "Beleg": [],
    "BelegText":
        [strip(lambda context: is_expendable(context) or has_content(context, '[".]')),
         reduce_single_child],
    "BelegStelle": [flatten],
    "Interpretamente": [],
    "LateinischeBedeutung": [remove_nodes("LAT"), flatten],
    "DeutscheBedeutung": [remove_nodes("DEU"), flatten],
    "LateinischerAusdruck": [flatten, reduce_single_child],
    "DeutscherAusdruck": [flatten, reduce_single_child],
    "LateinischesWort, DeutschesWort": [strip, collapse],
    "Belege": [flatten],
    "Beleg": [],
    "EinBeleg": [],
    "Zitat": [flatten],
    "Zusatz": [reduce_single_child, flatten],
    "ArtikelVerfasser": [],
    "Stellenverzeichnis": [],
    "Verweisliste": [flatten],
    "Stellenverweis": [flatten],
    "GebrauchsHinweis, PlurSingHinweis": [remove_whitespace, reduce_single_child],
    "Name": [collapse],
    "Stelle": [collapse],
    "SW_LAT": [replace_or_reduce],
    "SW_DEU": [replace_or_reduce],
    "SW_GRIECH": [replace_or_reduce],
    "Verweis": [],
    "VerweisKern": [flatten],
    "pfad, ziel": [reduce_single_child], # [apply_if(replace_content(lambda s: ''), has_parent("URL"))],
    "Anker": [reduce_single_child],
    "Werk": [reduce_single_child],
    "ZielName": [replace_by_single_child],
    "URL": [flatten, keep_nodes('protokoll', 'domäne', 'pfad', 'ziel'), replace_by_single_child],
    "NAMENS_ABKÜRZUNG": [],
    "NAME": [],
    "DEU_WORT": [reduce_single_child],
    "DEU_GROSS": [reduce_single_child],
    "DEU_KLEIN": [reduce_single_child],
    "LAT_WORT": [reduce_single_child],
    "LAT_WORT_TEIL": [],
    "GROSSSCHRIFT": [],
    "GROSSFOLGE": [],
    "BUCHSTABENFOLGE": [],
    "EINZEILER, FREITEXT, MEHRZEILER": [strip, collapse],
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
    ":Token": [remove_whitespace, reduce_single_child],
    "RE": reduce_single_child,
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


def lemma_verdichtung(lemma, variante):
    # finde den ersten Unterschied von links
    l = 0
    while l < min(len(lemma), len(variante)) and lemma[l] == variante[l]:
        l += 1

    # finde den ersten Unterschied von rechts
    r = 1
    while r <= min(len(lemma), len(variante)) and lemma[-r] == variante[-r]:
        r += 1
    r -= 1

    l -= 1              # beginne 1 Zeichen vor dem ersten Unterschied
    if l <= 1:  l = 0   # einzelne Buchstaben nicht abtrennen

    r -= 1              # beginne 1 Zeichen nach dem letzten Unterschied
    if r <= 1:  r = 0   # einzelne Buchstaben nicht abtrennen

    # gib Zeichenkette der Unterschide ab dem letzten gemeinsamen (von links) bzw.
    # ab dem ersten gemeinsamen (von rechts) Buchstaben mit Trennstrichen zurück
    return (('-' if l > 0 else '') + variante[l:(-r) or None] + ('-' if r > 0 else ''))


class MLWCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a MLW source file.
    """

    ZÄHLER = (
        ('I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'),
        'ABCDEFGHI',
        '123456789',
        'abcdefghi',
        'αβγδεζηθι'
    )

    def __init__(self, grammar_name="MLW", grammar_source=""):
        super(MLWCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)
        self.lemmawort = ""

    def on_VerweisKern(self, node):
        if node.children[0].parser.name == "FREITEXT":
            node.children[1].result = ""
        elif node.children[0].parser.name == "ziel":
            node.children[0].result = "v. ibi."
        return node

    def ergänze_Zähler(self, node, tiefe):
        i = 0
        for nd in node.children:
            if nd.parser.name == "Bedeutung":
                zähler = Node(MockParser("Zähler", ":RE"), self.ZÄHLER[tiefe][i])
                i += 1
                nd2 = nd.children[0]
                nd2.children = (zähler,) + nd2.children

    def on_BedeutungsPosition(self, node):
        self.ergänze_Zähler(node, 0)
        return self.fallback_compiler(node)

    def on_U1Bedeutung(self, node):
        self.ergänze_Zähler(node, 1)
        return self.fallback_compiler(node)

    def on_U2Bedeutung(self, node):
        self.ergänze_Zähler(node, 2)
        return self.fallback_compiler(node)

    def on_U3Bedeutung(self, node):
        self.ergänze_Zähler(node, 3)
        return self.fallback_compiler(node)

    def on_U4Bedeutung(self, node):
        self.ergänze_Zähler(node, 4)
        return self.fallback_compiler(node)

    def on_U5Bedeutung(self, node):
        self.ergänze_Zähler(node, 5)
        return self.fallback_compiler(node)

    def on_LemmaWort(self, node):
        assert not node.children
        self.lemmawort = node.result
        return node

    def on_LemmaVariante(self, node):
        assert not node.children
        node.xml_attr['verdichtung'] = lemma_verdichtung(self.lemmawort, node.result)
        return node

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


def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging(log_dir):
        compiler = get_compiler()
        cname = compiler.__class__.__name__
        log_file_name = os.path.basename(os.path.splitext(source)[0]) \
            if is_filename(source) < 0 else cname[:cname.find('.')] + '_out'    
        result = compile_source(source, get_preprocessor(), 
                                get_grammar(),
                                get_transformer(), compiler)
    return result


HTML_LEAD_IN = """<html>
<head>
<meta charset="UTF-8"/>
<link rel="stylesheet" href="MLW.css" />
</head>

<body>
"""

HTML_LEAD_OUT = """
</body>
</html>
"""

def write_as_html(file_name, tree, show=False):
    out_name = os.path.splitext(file_name)[0] + '.html'
    with open(out_name, 'w', encoding="utf-8") as f:
        f.write(HTML_LEAD_IN)
        f.write(tree.as_xml())
        f.write(HTML_LEAD_OUT)
    if show:
        webbrowser.open(out_name)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        result, errors, ast = compile_src(file_name, log_dir)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            print('\nLeider hat es ein paar Fehler gegeben :-(\n')
            sys.exit(1)
        else:
            write_as_html(file_name, result, show=True)
            print("Das Einlesen war erfolgreich :-)")
    else:
        print("Aufruf: MLWCompiler.py [--debug] FILENAME")
