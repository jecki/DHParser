def MLWScanner(text):
    return text


### DON'T EDIT OR REMOVE THIS LINE ###

class MLWGrammar(ParserHeadquarter):
    r"""Parser for a MLW source file, with this grammar:
    
    # EBNF-Syntax für MLW-Artikel
    
    @ comment       =  /#.*(?:\n|$)/    # Kommentare beginnen mit '#' und reichen bis zum Zeilenende
    @ whitespace    =  /\s*/            # Auch Zeilenspränge zählen als Leerraum
    @ literalws     =  both             # Leerraum vor und nach Literalen wird automatisch entfernt
    
    
    Artikel         = [LEER]
                      §LemmaPosition  [ArtikelKopf]  §BedeutungsPosition  §Autorinfo
                      [LEER]  DATEI_ENDE
    
    
    #### LEMMA-POSITION ##########################################################
    
    LemmaPosition   = "LEMMA"  §Lemma  [LemmaVarianten]  §GrammatikPosition
    
    Lemma           = [_tll]  WORT_KLEIN
    _tll            = "*"
    
    LemmaVarianten  = "VARIANTEN" §LVariante  { "," §LVariante }  [";" §LVZusatz]
    LVariante       = ~/(?:[a-z]|-)+/~  # Buchstabenfolge mit Trennzeichen "-"
    LVZusatz        = "sim."
    
    
    
    #### GRAMMATIK-POSITION ######################################################
    
    GrammatikPosition = "GRAMMATIK" §_wortart §";"  §Flexionen  [_genus]  {GrammatikVarianten} [";" | "."]
    
    _wortart        = "nomen"  | "n." |
                      "verb"   | "v." |
                      "adverb" | "adv." |
                      "adjektiv" | "adj."
    
    
    GrammatikVarianten = ";" §GVariante
    GVariante       = Flexionen  [_genus]  ":"  Beleg
    
    Flexionen       = Flexion { "," §Flexion }
    Flexion         = /-?[a-z]+/~
    
    _genus          = "maskulinum" | "m." |
                      "femininum" | "f." |
                      "neutrum" | "n."
    
    
    
    #### ARTIKEL-KOPF ############################################################
    
    ArtikelKopf     = SchreibweisenPosition
    SchreibweisenPosition =  "SCHREIBWEISE" §SWTyp ":" §SWVariante { "," §SWVariante}
    SWTyp           = "script." | "script. fat-"
    SWVariante      = Schreibweise ":" Beleg
    Schreibweise    = "vizreg-" | "festregel(a)" | "fezdregl(a)" | "fat-"
    
    Beleg           = Verweis
    Verweis         = ~/>>\w+/~
    VerweisZiel     = ~/<\w+>/~
    
    
    #### BEDEUTUNGS-POSITION #####################################################
    
    BedeutungsPosition = { "BEDEUTUNG" Bedeutung }+
    
    Bedeutung       = Interpretamente | Bedeutungskategorie
    Bedeutungskategorie = /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    Interpretamente = LateinischeBedeutung  DeutscheBedeutung  [Belege]
    LateinischeBedeutung = "LAT" /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    DeutscheBedeutung = "DEU" /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    Belege          = "BELEGE" { "*" EinBeleg }
    EinBeleg        = { !(/\s*/ ("*" | "BEDEUTUNG" | "AUTOR" | "NAME" | "ZUSATZ")) /\s?.*/ }+
                      [Zusatz]
    Zusatz          = "ZUSATZ" /\s?.*/
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    Autorinfo       = ("AUTORIN" | "AUTOR") Name
    Name            = WORT { WORT | /[A-ZÄÖÜÁÀ]\./ }
    
    
    #### MISZELLANEEN ############################################################
    
    WORT            = /[A-ZÄÖÜ]?[a-zäöüß]+/~
    WORT_GROSS      = /[A-ZÄÖÜ][a-zäöüß]+/~
    WORT_KLEIN      = /[a-zäöüß]+/~
    LAT_WORT        = /[a-z]+/~
    GROSSSCHRIFT    = /[A-ZÄÖÜ]+/~
    
    LEER            = /\s*/
    DATEI_ENDE      = !/./
    NIEMALS         = /(?!.)/
    """
    source_hash__ = "460019891fffc4dbf8d8e8573f5f699c"
    parser_initialization__ = "upon instatiation"
    wsp__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    NIEMALS = RE('(?!.)')
    DATEI_ENDE = NegativeLookahead(RE('.'))
    LEER = RE('\\s*')
    GROSSSCHRIFT = RE('[A-ZÄÖÜ]+', wR=wsp__)
    LAT_WORT = RE('[a-z]+', wR=wsp__)
    WORT_KLEIN = RE('[a-zäöüß]+', wR=wsp__)
    WORT_GROSS = RE('[A-ZÄÖÜ][a-zäöüß]+', wR=wsp__)
    WORT = RE('[A-ZÄÖÜ]?[a-zäöüß]+', wR=wsp__)
    Name = Sequence(WORT, ZeroOrMore(Alternative(WORT, RE('[A-ZÄÖÜÁÀ]\\.'))))
    Autorinfo = Sequence(Alternative(Token("AUTORIN", wL=wsp__, wR=wsp__), Token("AUTOR", wL=wsp__, wR=wsp__)), Name)
    Zusatz = Sequence(Token("ZUSATZ", wL=wsp__, wR=wsp__), RE('\\s?.*'))
    EinBeleg = Sequence(OneOrMore(Sequence(NegativeLookahead(Sequence(RE('\\s*'), Alternative(Token("*", wL=wsp__, wR=wsp__), Token("BEDEUTUNG", wL=wsp__, wR=wsp__), Token("AUTOR", wL=wsp__, wR=wsp__), Token("NAME", wL=wsp__, wR=wsp__), Token("ZUSATZ", wL=wsp__, wR=wsp__)))), RE('\\s?.*'))), Optional(Zusatz))
    Belege = Sequence(Token("BELEGE", wL=wsp__, wR=wsp__), ZeroOrMore(Sequence(Token("*", wL=wsp__, wR=wsp__), EinBeleg)))
    DeutscheBedeutung = Sequence(Token("DEU", wL=wsp__, wR=wsp__), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wR=wsp__))
    LateinischeBedeutung = Sequence(Token("LAT", wL=wsp__, wR=wsp__), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wR=wsp__))
    Interpretamente = Sequence(LateinischeBedeutung, DeutscheBedeutung, Optional(Belege))
    Bedeutungskategorie = RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wR=wsp__)
    Bedeutung = Alternative(Interpretamente, Bedeutungskategorie)
    BedeutungsPosition = OneOrMore(Sequence(Token("BEDEUTUNG", wL=wsp__, wR=wsp__), Bedeutung))
    VerweisZiel = RE('<\\w+>', wR=wsp__, wL=wsp__)
    Verweis = RE('>>\\w+', wR=wsp__, wL=wsp__)
    Beleg = Verweis
    Schreibweise = Alternative(Token("vizreg-", wL=wsp__, wR=wsp__), Token("festregel(a)", wL=wsp__, wR=wsp__), Token("fezdregl(a)", wL=wsp__, wR=wsp__), Token("fat-", wL=wsp__, wR=wsp__))
    SWVariante = Sequence(Schreibweise, Token(":", wL=wsp__, wR=wsp__), Beleg)
    SWTyp = Alternative(Token("script.", wL=wsp__, wR=wsp__), Token("script. fat-", wL=wsp__, wR=wsp__))
    SchreibweisenPosition = Sequence(Token("SCHREIBWEISE", wL=wsp__, wR=wsp__), Required(SWTyp), Token(":", wL=wsp__, wR=wsp__), Required(SWVariante), ZeroOrMore(Sequence(Token(",", wL=wsp__, wR=wsp__), Required(SWVariante))))
    ArtikelKopf = SchreibweisenPosition
    _genus = Alternative(Token("maskulinum", wL=wsp__, wR=wsp__), Token("m.", wL=wsp__, wR=wsp__), Token("femininum", wL=wsp__, wR=wsp__), Token("f.", wL=wsp__, wR=wsp__), Token("neutrum", wL=wsp__, wR=wsp__), Token("n.", wL=wsp__, wR=wsp__))
    Flexion = RE('-?[a-z]+', wR=wsp__)
    Flexionen = Sequence(Flexion, ZeroOrMore(Sequence(Token(",", wL=wsp__, wR=wsp__), Required(Flexion))))
    GVariante = Sequence(Flexionen, Optional(_genus), Token(":", wL=wsp__, wR=wsp__), Beleg)
    GrammatikVarianten = Sequence(Token(";", wL=wsp__, wR=wsp__), Required(GVariante))
    _wortart = Alternative(Token("nomen", wL=wsp__, wR=wsp__), Token("n.", wL=wsp__, wR=wsp__), Token("verb", wL=wsp__, wR=wsp__), Token("v.", wL=wsp__, wR=wsp__), Token("adverb", wL=wsp__, wR=wsp__), Token("adv.", wL=wsp__, wR=wsp__), Token("adjektiv", wL=wsp__, wR=wsp__), Token("adj.", wL=wsp__, wR=wsp__))
    GrammatikPosition = Sequence(Token("GRAMMATIK", wL=wsp__, wR=wsp__), Required(_wortart), Required(Token(";", wL=wsp__, wR=wsp__)), Required(Flexionen), Optional(_genus), ZeroOrMore(GrammatikVarianten), Optional(Alternative(Token(";", wL=wsp__, wR=wsp__), Token(".", wL=wsp__, wR=wsp__))))
    LVZusatz = Token("sim.", wL=wsp__, wR=wsp__)
    LVariante = RE('(?:[a-z]|-)+', wR=wsp__, wL=wsp__)
    LemmaVarianten = Sequence(Token("VARIANTEN", wL=wsp__, wR=wsp__), Required(LVariante), ZeroOrMore(Sequence(Token(",", wL=wsp__, wR=wsp__), Required(LVariante))), Optional(Sequence(Token(";", wL=wsp__, wR=wsp__), Required(LVZusatz))))
    _tll = Token("*", wL=wsp__, wR=wsp__)
    Lemma = Sequence(Optional(_tll), WORT_KLEIN)
    LemmaPosition = Sequence(Token("LEMMA", wL=wsp__, wR=wsp__), Required(Lemma), Optional(LemmaVarianten), Required(GrammatikPosition))
    Artikel = Sequence(Optional(LEER), Required(LemmaPosition), Optional(ArtikelKopf), Required(BedeutungsPosition), Required(Autorinfo), Optional(LEER), DATEI_ENDE)
    root__ = Artikel
    

### DON'T EDIT OR REMOVE THIS LINE ###

def test(node):
    if node.parser.name == "WORT_KLEIN":
        assert False, node.as_sexpr()
        node = remove_expendables(node)
        node = reduce_single_child(node)
        assert False, node.parser.name
    return node

MLWTransTable = {
    # AST Transformations for the MLW-grammar
    "Artikel": no_transformation,
    "LemmaPosition": no_transformation,
    "Lemma":
        partial(remove_tokens, tokens={'LEMMA'}),
    "_tll":
        [remove_expendables, reduce_single_child],
    "LemmaVarianten":
        [partial(remove_tokens, tokens={'VARIANTEN'}), flatten,
         partial(remove_tokens, tokens={',', ';'})],
    "LVariante":
        [reduce_single_child],
    "LVZusatz": no_transformation,
    "GrammatikPosition": no_transformation,
    "_wortart": no_transformation,
    "GrammatikVarianten": no_transformation,
    "GVariante": no_transformation,
    "Flexionen": no_transformation,
    "Flexion": no_transformation,
    "_genus": no_transformation,
    "ArtikelKopf": no_transformation,
    "SchreibweisenPosition": no_transformation,
    "SWTyp": no_transformation,
    "SWVariante": no_transformation,
    "Schreibweise": no_transformation,
    "BedeutungsPosition": no_transformation,
    "Bedeutung": no_transformation,
    "Bedeutungskategorie": no_transformation,
    "Interpretamente": no_transformation,
    "LateinischeBedeutung": no_transformation,
    "DeutscheBedeutung": no_transformation,
    "Belege": no_transformation,
    "EinBeleg": no_transformation,
    "Beleg": no_transformation,
    "Verweis": no_transformation,
    "VerweisZiel": no_transformation,
    "WORT, WORT_KLEIN, WORT_GROSS, GROSSSCHRIFT":
        # test,
        [remove_expendables, reduce_single_child],
    "LEER": no_transformation,
    "DATEI_ENDE": no_transformation,
    "NIEMALS": no_transformation,
    (TOKEN_KEYWORD, WHITESPACE_KEYWORD):
        [remove_expendables, reduce_single_child],
    "*":
        remove_expendables,
    "~":
        partial(remove_tokens, tokens={',', ';'}),
    "":
        [remove_expendables, replace_by_single_child]
}


### DON'T EDIT OR REMOVE THIS LINE ###

class MLWCompiler(CompilerBase):
    """Compiler for the abstract-syntax-tree of a MLW source file.
    """

    def __init__(self, grammar_name="MLW"):
        super(MLWCompiler, self).__init__()
        assert re.match('\w+\Z', grammar_name)

    def Artikel(self, node):
        return node

    def LemmaPosition(self, node):
        pass

    def Lemma(self, node):
        pass

    def _tll(self, node):
        pass

    def LemmaVarianten(self, node):
        pass

    def LVariante(self, node):
        pass

    def LVZusatz(self, node):
        pass

    def GrammatikPosition(self, node):
        pass

    def _wortart(self, node):
        pass

    def GrammatikVarianten(self, node):
        pass

    def GVariante(self, node):
        pass

    def Flexionen(self, node):
        pass

    def Flexion(self, node):
        pass

    def _genus(self, node):
        pass

    def ArtikelKopf(self, node):
        pass

    def SchreibweisenPosition(self, node):
        pass

    def SWTyp(self, node):
        pass

    def SWVariante(self, node):
        pass

    def Schreibweise(self, node):
        pass

    def BedeutungsPosition(self, node):
        pass

    def Bedeutung(self, node):
        pass

    def Bedeutungskategorie(self, node):
        pass

    def Interpretamente(self, node):
        pass

    def LateinischeBedeutung(self, node):
        pass

    def DeutscheBedeutung(self, node):
        pass

    def Belege(self, node):
        pass

    def EinBeleg(self, node):
        pass

    def Beleg(self, node):
        pass

    def Verweis(self, node):
        pass

    def VerweisZiel(self, node):
        pass

    def WORT(self, node):
        pass

    def WORT_KLEIN(self, node):
        pass

    def GROSSSCHRIFT(self, node):
        pass

    def LEER(self, node):
        pass

    def DATEI_ENDE(self, node):
        pass

    def NIEMALS(self, node):
        pass

