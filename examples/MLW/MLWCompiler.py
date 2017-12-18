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
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    content_from_child, replace_by_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, remove_nodes, remove_content, remove_brackets, replace_parser, \
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
    
    LemmaVariante     = LAT_WORT [Zusatz]
    
    
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
    
    BedeutungsPosition   = { ZWW "BEDEUTUNG" [LZ] §Bedeutung [U1Bedeutung] }+
    U1Bedeutung          = { ZWW ("U_BEDEUTUNG" | "UNTER_BEDEUTUNG") [LZ] §Bedeutung [U2Bedeutung] }+
    U2Bedeutung          = { ZWW ("UU_BEDEUTUNG" | "UNTER_UNTER_BEDEUTUNG") [LZ] §Bedeutung [U3Bedeutung] }+
    U3Bedeutung          = { ZWW "UUU_BEDEUTUNG" [LZ] §Bedeutung [U4Bedeutung] }+
    U4Bedeutung          = { ZWW "UUUU_BEDEUTUNG" [LZ] §Bedeutung [U5Bedeutung] }+
    U5Bedeutung          = { ZWW "UUUUU_BEDEUTUNG" [LZ] §UntersteBedeutung }+
    
    Bedeutung            = (Interpretamente | Bedeutungskategorie) [BelegPosition]
    UntersteBedeutung    = Interpretamente [BelegPosition]
    Bedeutungskategorie  = { EINZEILER [LZ] [Zusatz] [LZ] } §":"
    Interpretamente      = LateinischeBedeutung ("--"| LZ) §DeutscheBedeutung [":"]
    LateinischeBedeutung = LAT [LZ] [Zusatz] LateinischerAusdruck
    DeutscheBedeutung    = DEU [LZ] [Zusatz] DeutscherAusdruck
    LateinischerAusdruck = LAT_WORT { [ZW] ((/[,;]?/~ [ZW] (LAT_WORT | ("(" LateinischerAusdruck ")")))
                                            | Zusatz) }
    DeutscherAusdruck    = DEU_WORT { [ZW] ((/[,;]?/~ [ZW] (DEU_WORT | ("(" DeutscherAusdruck")")))
                                            | Zusatz) }
    
    # LateinischerAusdruck = LAT_WORT_ERW { //~ LAT_WORT_ERW } [[LZ] BedeutungsQualifikation]
    # DeutscherAusdruck    = DEU_WORT_ERW { //~ DEU_WORT_ERW } [[LZ] BedeutungsQualifikation]
    # LateinischerAusdruck = LAT_WORT [[LZ] BedeutungsQualifikation]
    # DeutscherAusdruck = DEU_WORT [[LZ] BedeutungsQualifikation]
    
    BelegPosition = ZWW ["BELEGE" [LZ]] Belege
    
    
    #### VERWEIS-POSITION ########################################################
    
    VerweisPosition = ZWW "VERWEISE"
    
    
    #### UNTER-ARTIKEL ###########################################################
    
    UnterArtikel = ZWW "UNTER-ARTIKEL"
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    ArtikelVerfasser = ZWW ("AUTORIN" | "AUTOR") §Name
    Name             = { NAME | NAMENS_ABKÜRZUNG | "unbekannt" }+
    
    
    #### STELLENVERZEICHNIS ######################################################
    
    Stellenverzeichnis = ZWW "STELLENVERZEICHNIS" [LemmaWort] ZWW Verweisliste
    Verweisliste       = { [LZ] "*" Stellenverweis }
    Stellenverweis     = BelegQuelle { [ABS] Stelle (NullVerweis | Verweis) }
    NullVerweis        = "{" "-" "}"
    
    
    #### Schlüsselwörter #########################################################
    
    LAT = "LATEINISCH" | "LAT"
    DEU = "DEUTSCH" | "DEU"
    GRI = "GRIECHISCH" | "GRIECH" | "GRIE" | "GRI"
    
    SCHLUESSELWORT   = { //~ /\n/ }+ !ROEMISCHE_ZAHL /[A-ZÄÖÜ]{3,}\s+/
    
    
    #### ZUSATZ an verschiedenen Stellen der Struktur ############################
    
    Zusatz       = { "{" !("=>" | "#") §EinzelnerZusatz { ";;" EinzelnerZusatz } "}" }+
      EinzelnerZusatz  = FesterZusatz | GemischterZusatz | FreierZusatz
      FesterZusatz     = "adde" | "sape" | "persaepe"
      GemischterZusatz = ( "usu" | "plur. sensu sing." ) FreierZusatz
      FreierZusatz     = { FREITEXT | VerweisKern | Verweis }+
    
    
    #### BELEGE ##################################################################
    
    Belege           = ["*"] Beleg { [LZ] "*" Beleg }
    Beleg            = [Zusatz] ((Verweis [Zitat]) | Zitat) [ABS Zusatz] ["."]
    Zitat            = Quellenangabe
                       { SEM [ZW] [Anker] [Zusatz] <Stelle | Verweis>
                         [[ZW] BelegText] [[LZ] Zusatz] }
    
    Quellenangabe    = [<Anker | Zusatz>] < BelegQuelle | Verweis >
    BelegQuelle      = Autor §DPP [Werk] &SEM
    BelegText        = /"/ { MEHRZEILER | Zusatz } §/"/~ ["."]
    
    Autor     = EINZEILER [<Anker | Verweis | Zusatz>]
    Werk      = <EINZEILER [<Anker | Verweis | Zusatz>]>
    Stelle    = EINZEILER
    Datierung = EINZEILER
    Edition   = EINZEILER
    
    
    #### VERWEISE (LINKS) ########################################################
    
    Verweis          = "{" VerweisKern "}"
    VerweisKern      = "=>" §((alias "|" ("-" | URL)) | URL)
    Anker            = "{" "#" §ziel "}"
    URL              = [ ([protokoll] domäne /\//) | /\// ] { pfad /\// } ziel
    
    alias            = FREITEXT
    protokoll        = /\w+:\/\//
    domäne           = /\w+\.\w+(?:\.\w+)*/
    pfad             = /\w+/
    ziel             = /[\w=?.%&\[\] ]+/
    
    
    #### GENERISCHE UND ATOMARE AUSDRÜCKE ########################################
    
    NAMENS_ABKÜRZUNG = /[A-ZÄÖÜÁÀÂÓÒÔÚÙÛ]\./~
    NAME             = /[A-ZÄÖÜÁÀÓÒÚÙÂÔÛ][a-zäöüßáàâóòôúùû]+/~
    
    DEU_WORT         = DEU_GROSS | DEU_KLEIN | GROSSBUCHSTABE
    # DEU_WORT_ERW     = DEU_WORT | (["("] DEU_WORT [")"])
    DEU_GROSS        = /[A-ZÄÖÜ][a-zäöüßę_\-.]+/~
    GROSSBUCHSTABE   = /[A-ZÄÖÜ](?=[ \t\n])/~
    KLEINBUCHSTABE   = /[a-zäöü](?=[ \t\n])/~
    GRI_BUCHSTABE    = /[αβγδεζηθικλμνξοπρςστυφχψω]/
    DEU_KLEIN        = /(?!--)[a-zäöüßęõ_\-.]+/~
    LAT_WORT         = /(?!--)[a-z|\-_.]+/~
    # LAT_WORT_ERW     = LAT_WORT | (["("] LAT_WORT [")"])
    GROSSSCHRIFT     = /(?!--)[A-ZÄÖÜ_\-]+/~
    ZAHL             = /[\d]+/~
    SEITENZAHL       = /[\d]+(?:\^(?:(?:\{[\d\w.]+\})|\w))?/~     # Zahl mit optionale folgendem hochgestelltem Buchstaben oder Text
    ROEMISCHE_ZAHL   = /(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\w])/~
    
    SATZZEICHEN      = /(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|(?:-(?!-))|[.()\[\]]+)|[`''‘’?]/~  # div. Satzzeichen, aber keine doppelten ,, ;; oder ::
    TEIL_SATZZEICHEN = /(?!->)(?:(?:,(?!,))|(?:-(?!-))|[.()]+)|[`''‘’?]/~ # Satzeichen bis auf Doppelpunkt ":", Semikolon ";" und eckige Klammern
    
    BUCHSTABENFOLGE  = /\w+/~
    ZEICHENFOLGE     = /[\w()-]+/~
    TEXTELEMENT      = DEU_WORT | SEITENZAHL | ROEMISCHE_ZAHL
    EINZEILER        = { TEXTELEMENT | TEIL_SATZZEICHEN }+
    FREITEXT         = { TEXTELEMENT | SATZZEICHEN | GROSSSCHRIFT }+
    MEHRZEILER       = { FREITEXT | /\s+(?=[\w,;:.\(\)\-])/ }+
    
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
    DeutscherAusdruck = Forward()
    FREITEXT = Forward()
    GROSSSCHRIFT = Forward()
    Kategorien = Forward()
    LZ = Forward()
    LateinischerAusdruck = Forward()
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
    source_hash__ = "464ddc02bebdae51c3aef3bbee12f793"
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
    MEHRZEILER = OneOrMore(Alternative(FREITEXT, RegExp('\\s+(?=[\\w,;:.\\(\\)\\-])')))
    FREITEXT.set(OneOrMore(Alternative(TEXTELEMENT, SATZZEICHEN, GROSSSCHRIFT)))
    EINZEILER = OneOrMore(Alternative(TEXTELEMENT, TEIL_SATZZEICHEN))
    TEXTELEMENT.set(Alternative(DEU_WORT, SEITENZAHL, ROEMISCHE_ZAHL))
    ZEICHENFOLGE = RE('[\\w()-]+')
    BUCHSTABENFOLGE = RE('\\w+')
    TEIL_SATZZEICHEN.set(RE("(?!->)(?:(?:,(?!,))|(?:-(?!-))|[.()]+)|[`''‘’?]"))
    SATZZEICHEN.set(RE("(?!->)(?:(?:,(?!,))|(?:;(?!;))|(?::(?!:))|(?:-(?!-))|[.()\\[\\]]+)|[`''‘’?]"))
    ROEMISCHE_ZAHL.set(RE('(?=[MDCLXVI])M*(C[MD]|D?C*)(X[CL]|L?X*)(I[XV]|V?I*)(?=[^\\w])'))
    SEITENZAHL.set(RE('[\\d]+(?:\\^(?:(?:\\{[\\d\\w.]+\\})|\\w))?'))
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
    ziel = RegExp('[\\w=?.%&\\[\\] ]+')
    pfad = RegExp('\\w+')
    domäne = RegExp('\\w+\\.\\w+(?:\\.\\w+)*')
    protokoll = RegExp('\\w+://')
    alias = Synonym(FREITEXT)
    URL = Series(Option(Alternative(Series(Option(protokoll), domäne, RegExp('/')), RegExp('/'))), ZeroOrMore(Series(pfad, RegExp('/'))), ziel)
    Anker = Series(Token("{"), Token("#"), ziel, Token("}"), mandatory=2)
    VerweisKern = Series(Token("=>"), Alternative(Series(alias, Token("|"), Alternative(Token("-"), URL)), URL), mandatory=1)
    Verweis = Series(Token("{"), VerweisKern, Token("}"))
    Edition = Synonym(EINZEILER)
    Datierung = Synonym(EINZEILER)
    Stelle = Synonym(EINZEILER)
    Werk = AllOf(EINZEILER, Option(SomeOf(Anker, Verweis, Zusatz)))
    Autor = Series(EINZEILER, Option(SomeOf(Anker, Verweis, Zusatz)))
    BelegText = Series(RegExp('"'), ZeroOrMore(Alternative(MEHRZEILER, Zusatz)), RE('"'), Option(Token(".")), mandatory=2)
    BelegQuelle = Series(Autor, DPP, Option(Werk), Lookahead(SEM), mandatory=1)
    Quellenangabe = Series(Option(SomeOf(Anker, Zusatz)), SomeOf(BelegQuelle, Verweis))
    Zitat = Series(Quellenangabe, ZeroOrMore(Series(SEM, Option(ZW), Option(Anker), Option(Zusatz), SomeOf(Stelle, Verweis), Option(Series(Option(ZW), BelegText)), Option(Series(Option(LZ), Zusatz)))))
    Beleg = Series(Option(Zusatz), Alternative(Series(Verweis, Option(Zitat)), Zitat), Option(Series(ABS, Zusatz)), Option(Token(".")))
    Belege = Series(Option(Token("*")), Beleg, ZeroOrMore(Series(Option(LZ), Token("*"), Beleg)))
    FreierZusatz = OneOrMore(Alternative(FREITEXT, VerweisKern, Verweis))
    GemischterZusatz = Series(Alternative(Token("usu"), Token("plur. sensu sing.")), FreierZusatz)
    FesterZusatz = Alternative(Token("adde"), Token("sape"), Token("persaepe"))
    EinzelnerZusatz = Alternative(FesterZusatz, GemischterZusatz, FreierZusatz)
    Zusatz.set(OneOrMore(Series(Token("{"), NegativeLookahead(Alternative(Token("=>"), Token("#"))), EinzelnerZusatz, ZeroOrMore(Series(Token(";;"), EinzelnerZusatz)), Token("}"), mandatory=2)))
    SCHLUESSELWORT = Series(OneOrMore(Series(RE(''), RegExp('\\n'))), NegativeLookahead(ROEMISCHE_ZAHL), RegExp('[A-ZÄÖÜ]{3,}\\s+'))
    GRI = Alternative(Token("GRIECHISCH"), Token("GRIECH"), Token("GRIE"), Token("GRI"))
    DEU = Alternative(Token("DEUTSCH"), Token("DEU"))
    LAT = Alternative(Token("LATEINISCH"), Token("LAT"))
    NullVerweis = Series(Token("{"), Token("-"), Token("}"))
    Stellenverweis = Series(BelegQuelle, ZeroOrMore(Series(Option(ABS), Stelle, Alternative(NullVerweis, Verweis))))
    Verweisliste = ZeroOrMore(Series(Option(LZ), Token("*"), Stellenverweis))
    Stellenverzeichnis = Series(ZWW, Token("STELLENVERZEICHNIS"), Option(LemmaWort), ZWW, Verweisliste)
    Name = OneOrMore(Alternative(NAME, NAMENS_ABKÜRZUNG, Token("unbekannt")))
    ArtikelVerfasser = Series(ZWW, Alternative(Token("AUTORIN"), Token("AUTOR")), Name, mandatory=2)
    UnterArtikel = Series(ZWW, Token("UNTER-ARTIKEL"))
    VerweisPosition = Series(ZWW, Token("VERWEISE"))
    BelegPosition = Series(ZWW, Option(Series(Token("BELEGE"), Option(LZ))), Belege)
    DeutscherAusdruck.set(Series(DEU_WORT, ZeroOrMore(Series(Option(ZW), Alternative(Series(RE('[,;]?'), Option(ZW), Alternative(DEU_WORT, Series(Token("("), DeutscherAusdruck, Token(")")))), Zusatz)))))
    LateinischerAusdruck.set(Series(LAT_WORT, ZeroOrMore(Series(Option(ZW), Alternative(Series(RE('[,;]?'), Option(ZW), Alternative(LAT_WORT, Series(Token("("), LateinischerAusdruck, Token(")")))), Zusatz)))))
    DeutscheBedeutung = Series(DEU, Option(LZ), Option(Zusatz), DeutscherAusdruck)
    LateinischeBedeutung = Series(LAT, Option(LZ), Option(Zusatz), LateinischerAusdruck)
    Interpretamente = Series(LateinischeBedeutung, Alternative(Token("--"), LZ), DeutscheBedeutung, Option(Token(":")), mandatory=2)
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
    LemmaVariante = Series(LAT_WORT, Option(Zusatz))
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

MLW_AST_transformation_table = {
    # AST Transformations for the MLW-grammar
    "+": remove_empty,
    "Autor": [content_from_child],
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
    "ArtikelKopf": [replace_by_child],
    "SchreibweisenPosition": [],
    "SWTyp": [replace_or_reduce],
    "SWVariante": [],
    "Schreibweise": [replace_by_child],
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
    "Stelle": [content_from_child],
    "SW_LAT": [replace_or_reduce],
    "SW_DEU": [replace_or_reduce],
    "SW_GRIECH": [replace_or_reduce],
    "Beleg": [replace_by_child],
    "Verweis": [],
    "VerweisZiel": [],
    "Werk": [content_from_child],
    "ZielName": [replace_by_child],
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
    ":Token, :RE": content_from_child,
    "*": replace_by_child
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
