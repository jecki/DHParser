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
    
    Bedeutung       = (Interpretamente | Bedeutungskategorie) [Belege]
    Bedeutungskategorie = /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    Interpretamente = LateinischeBedeutung  DeutscheBedeutung
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
    source_hash__ = "ca55553a5e483fa08341abecc2aa284c"
    parser_initialization__ = "upon instatiation"
    wsp__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    wspL__ = wsp__
    wspR__ = wsp__
    NIEMALS = RE('(?!.)')
    DATEI_ENDE = NegativeLookahead(RE('.'))
    LEER = RE('\\s*')
    GROSSSCHRIFT = RE('[A-ZÄÖÜ]+', wR=wsp__)
    LAT_WORT = RE('[a-z]+', wR=wsp__)
    WORT_KLEIN = RE('[a-zäöüß]+', wR=wsp__)
    WORT_GROSS = RE('[A-ZÄÖÜ][a-zäöüß]+', wR=wsp__)
    WORT = RE('[A-ZÄÖÜ]?[a-zäöüß]+', wR=wsp__)
    Name = Sequence(WORT, ZeroOrMore(Alternative(WORT, RE('[A-ZÄÖÜÁÀ]\\.'))))
    Autorinfo = Sequence(Alternative(Token("AUTORIN"), Token("AUTOR")), Name)
    Zusatz = Sequence(Token("ZUSATZ"), RE('\\s?.*'))
    EinBeleg = Sequence(OneOrMore(Sequence(NegativeLookahead(Sequence(RE('\\s*'), Alternative(Token("*"), Token("BEDEUTUNG"), Token("AUTOR"), Token("NAME"), Token("ZUSATZ")))), RE('\\s?.*'))), Optional(Zusatz))
    Belege = Sequence(Token("BELEGE"), ZeroOrMore(Sequence(Token("*"), EinBeleg)))
    DeutscheBedeutung = Sequence(Token("DEU"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wR=wsp__))
    LateinischeBedeutung = Sequence(Token("LAT"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wR=wsp__))
    Interpretamente = Sequence(LateinischeBedeutung, DeutscheBedeutung)
    Bedeutungskategorie = RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wR=wsp__)
    Bedeutung = Sequence(Alternative(Interpretamente, Bedeutungskategorie), Optional(Belege))
    BedeutungsPosition = OneOrMore(Sequence(Token("BEDEUTUNG"), Bedeutung))
    VerweisZiel = RE('<\\w+>', wR=wsp__, wL=wsp__)
    Verweis = RE('>>\\w+', wR=wsp__, wL=wsp__)
    Beleg = Verweis
    Schreibweise = Alternative(Token("vizreg-"), Token("festregel(a)"), Token("fezdregl(a)"), Token("fat-"))
    SWVariante = Sequence(Schreibweise, Token(":"), Beleg)
    SWTyp = Alternative(Token("script."), Token("script. fat-"))
    SchreibweisenPosition = Sequence(Token("SCHREIBWEISE"), Required(SWTyp), Token(":"), Required(SWVariante), ZeroOrMore(Sequence(Token(","), Required(SWVariante))))
    ArtikelKopf = SchreibweisenPosition
    _genus = Alternative(Token("maskulinum"), Token("m."), Token("femininum"), Token("f."), Token("neutrum"), Token("n."))
    Flexion = RE('-?[a-z]+', wR=wsp__)
    Flexionen = Sequence(Flexion, ZeroOrMore(Sequence(Token(","), Required(Flexion))))
    GVariante = Sequence(Flexionen, Optional(_genus), Token(":"), Beleg)
    GrammatikVarianten = Sequence(Token(";"), Required(GVariante))
    _wortart = Alternative(Token("nomen"), Token("n."), Token("verb"), Token("v."), Token("adverb"), Token("adv."), Token("adjektiv"), Token("adj."))
    GrammatikPosition = Sequence(Token("GRAMMATIK"), Required(_wortart), Required(Token(";")), Required(Flexionen), Optional(_genus), ZeroOrMore(GrammatikVarianten), Optional(Alternative(Token(";"), Token("."))))
    LVZusatz = Token("sim.")
    LVariante = RE('(?:[a-z]|-)+', wR=wsp__, wL=wsp__)
    LemmaVarianten = Sequence(Token("VARIANTEN"), Required(LVariante), ZeroOrMore(Sequence(Token(","), Required(LVariante))), Optional(Sequence(Token(";"), Required(LVZusatz))))
    _tll = Token("*")
    Lemma = Sequence(Optional(_tll), WORT_KLEIN)
    LemmaPosition = Sequence(Token("LEMMA"), Required(Lemma), Optional(LemmaVarianten), Required(GrammatikPosition))
    Artikel = Sequence(Optional(LEER), Required(LemmaPosition), Optional(ArtikelKopf), Required(BedeutungsPosition), Required(Autorinfo), Optional(LEER), DATEI_ENDE)
    root__ = Artikel
    

### DON'T EDIT OR REMOVE THIS LINE ###


def test(node):
    print(node.as_sexpr())


def join_strings(node, delimiter='\n'):
    new_result = []
    n = 0
    while n < len(node.result):
        nd = node.result[n]
        if not nd.children:
            a = n
            n += 1
            while n < len(node.result) and not node.result[n].children:
                n += 1
            nd.result = delimiter.join((r.result for r in node.result[a:n]))
        new_result.append(nd)
    node.result = tuple(new_result)
    print(node.as_sexpr())


MLWTransTable = {
    # AST Transformations for the MLW-grammar
    "Artikel": no_transformation,
    "LemmaPosition":
        [partial(remove_tokens, tokens={'LEMMA'})],
    "Lemma": no_transformation,
    "_tll, _wortart, _genus":
        [remove_expendables, reduce_single_child],
    "LemmaVarianten":
        [partial(remove_tokens, tokens={'VARIANTEN'}), flatten,
         partial(remove_tokens, tokens={',', ';'})],
    "LVariante, LVZusatz, Schreibweise, Name":
        [remove_expendables, reduce_single_child],
    "SWVariante":
        [remove_expendables, partial(remove_tokens, tokens={':'})],
    "GrammatikPosition":
        [partial(remove_tokens, tokens={'GRAMMATIK', ';'}), flatten],
    "GrammatikVarianten":
        [partial(remove_tokens, tokens={';'}), replace_by_single_child],
    "GVariante":
        [partial(remove_tokens, tokens={':'})],
    "Flexionen":
        [flatten, partial(remove_tokens, tokens={',', ';'})],
    "Flexion, Verweis":
        [remove_expendables, reduce_single_child],
    "Zusatz":
        [remove_expendables, remove_tokens, reduce_single_child],
    "ArtikelKopf": no_transformation,
    "SchreibweisenPosition":
        [partial(remove_tokens, tokens={'SCHREIBWEISE', ':'}),
         flatten, partial(remove_tokens, tokens={','})],
    "SWTyp": no_transformation,
    "BedeutungsPosition":
        [flatten, partial(remove_tokens, tokens={'BEDEUTUNG'})],
    "Bedeutung": no_transformation,
    "Bedeutungskategorie": no_transformation,
    "Interpretamente": no_transformation,
    "LateinischeBedeutung, DeutscheBedeutung":
        [remove_expendables, remove_tokens, reduce_single_child],
    "Belege":
        [flatten, remove_tokens],
    "EinBeleg":
        [flatten, remove_expendables, join_strings, reduce_single_child],
    "Beleg": no_transformation,
    "VerweisZiel": no_transformation,
    "Autorinfo":
        [partial(remove_tokens, tokens={'AUTORIN', 'AUTOR'})],
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

