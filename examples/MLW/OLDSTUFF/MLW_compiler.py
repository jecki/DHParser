#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import sys
from functools import partial

try:
    import regex as re
except ImportError:
    import re
from DHParser.parsers import Grammar, Compiler, Alternative, Required, Token, \
    Optional, OneOrMore, Series, RE, ZeroOrMore, NegativeLookahead, mixin_comment, compile_source
from DHParser.syntaxtree import traverse, reduce_single_child, replace_by_single_child, no_transformation, \
    remove_expendables, remove_tokens, flatten, \
    WHITESPACE_KEYWORD, TOKEN_KEYWORD


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def MLWScanner(text):
    return text


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class MLWGrammar(Grammar):
    r"""Parser for a MLW source file, with this grammar:
    
    # EBNF-Syntax für MLW-Artikel
    
    @ comment       =  /#.*(?:\n|$)/    # Kommentare beginnen mit '#' und reichen bis zum Zeilenende
    @ whitespace    =  /[\t ]*/         # Zeilensprünge zählen nicht als Leerraum
    @ literalws     =  both             # Leerraum vor und nach Literalen wird automatisch entfernt
    
    Artikel         = [LEER]
                      §LemmaPosition  [ArtikelKopf]  §BedeutungsPosition  §Autorinfo
                      [LEER]  DATEI_ENDE
    
    
    #### LEMMA-POSITION ##########################################################
    
    LemmaPosition   = "LEMMA"  §Lemma  [LemmaVarianten]  §GrammatikPosition
    
    Lemma           = [_tll]  WORT_KLEIN [LEER]
    _tll            = "*"
    
    LemmaVarianten  = "VARIANTEN" [LEER] §LVariante  { TRENNER LVariante }
                      [TRENNER LVZusatz] [TRENNER]
    LVariante       = ~/(?:[a-z]|-)+/~      # Buchstabenfolge mit Trennzeichen "-"
    LVZusatz        = "ZUSATZ" "sim."
    
    
    
    #### GRAMMATIK-POSITION ######################################################
    
    GrammatikPosition = "GRAMMATIK" [LEER] §_wortart §TRENNER §Flexionen [_genus]
                        {GrammatikVarianten} [TRENNER]
    
    _wortart        = "nomen"  | "n." |
                      "verb"   | "v." |
                      "adverb" | "adv." |
                      "adjektiv" | "adj."
    
    GrammatikVarianten = TRENNER GVariante
    GVariante       = Flexionen  [_genus]  ":"  Beleg
    
    Flexionen       = Flexion { "," §Flexion }
    Flexion         = /-?[a-z]+/~
    
    _genus          = "maskulinum" | "m." |
                      "femininum" | "f." |
                      "neutrum" | "n."
    
    
    
    #### ARTIKEL-KOPF ############################################################
    
    ArtikelKopf     = SchreibweisenPosition
    SchreibweisenPosition =  "SCHREIBWEISE" [LEER] §SWTyp ":" [LEER]
                             §SWVariante { TRENNER SWVariante} [LEER]
    SWTyp           = "script." | "script. fat-"
    SWVariante      = Schreibweise ":" Beleg
    Schreibweise    = "vizreg-" | "festregel(a)" | "fezdregl(a)" | "fat-"
    
    Beleg           = Verweis
    Verweis         = ~/\w+/~
    VerweisZiel     = ~/<\w+>/~
    
    
    #### BEDEUTUNGS-POSITION #####################################################
    
    BedeutungsPosition = { "BEDEUTUNG" [LEER] §Bedeutung }+
    
    Bedeutung       = (Interpretamente | Bedeutungskategorie) [Belege]
    Bedeutungskategorie = /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~ [LEER]
    Interpretamente = LateinischeBedeutung [LEER] §DeutscheBedeutung [LEER]
    LateinischeBedeutung = "LAT" /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    DeutscheBedeutung = "DEU" /(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+/~
    Belege          = "BELEGE" [LEER] { "*" EinBeleg }
    EinBeleg        = { !([LEER] ("*" | "BEDEUTUNG" | "AUTOR" | "NAME" | "ZUSATZ"))
                        /\s*.*\s*/ }+
                      [Zusatz]
    Zusatz          = "ZUSATZ" /\s*.*/ TRENNER
    
    
    #### AUTOR/AUTORIN ###########################################################
    
    Autorinfo       = ("AUTORIN" | "AUTOR") Name
    Name            = WORT { WORT | NAMENS_ABKÜRZUNG }
    
    
    #### ATOMARE AUSDRÜCKE #######################################################
    
    NAMENS_ABKÜRZUNG = /[A-ZÄÖÜÁÀ]\./
    
    WORT             = /[A-ZÄÖÜ]?[a-zäöüß]+/~
    WORT_GROSS       = /[A-ZÄÖÜ][a-zäöüß]+/~
    WORT_KLEIN       = /[a-zäöüß]+/~
    LAT_WORT         = /[a-z]+/~
    GROSSSCHRIFT     = /[A-ZÄÖÜ]+/~
    
    TRENNER          = /\s*;\s*/ | { ZSPRUNG }+
    ZSPRUNG          = /\n/~
    
    LEER             = /\s+/        # horizontaler und(!) vertikaler Leerraum
    DATEI_ENDE       = !/./
    NIEMALS          = /(?!.)/
    """
    source_hash__ = "9fce888d1b21b2d11a6228e0b97f9291"
    parser_initialization__ = "upon instatiation"
    COMMENT__ = r'#.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'[\t ]*', comment=r'#.*(?:\n|$)')
    wspL__ = WSP__
    wspR__ = WSP__
    NIEMALS = RE('(?!.)', wR='', wL='')
    DATEI_ENDE = NegativeLookahead(RE('.', wR='', wL=''))
    LEER = RE('\\s+', wR='', wL='')
    ZSPRUNG = RE('\\n', wL='')
    TRENNER = Alternative(RE('\\s*;\\s*', wR='', wL=''), OneOrMore(ZSPRUNG))
    GROSSSCHRIFT = RE('[A-ZÄÖÜ]+', wL='')
    LAT_WORT = RE('[a-z]+', wL='')
    WORT_KLEIN = RE('[a-zäöüß]+', wL='')
    WORT_GROSS = RE('[A-ZÄÖÜ][a-zäöüß]+', wL='')
    WORT = RE('[A-ZÄÖÜ]?[a-zäöüß]+', wL='')
    NAMENS_ABKÜRZUNG = RE('[A-ZÄÖÜÁÀ]\\.', wR='', wL='')
    Name = Series(WORT, ZeroOrMore(Alternative(WORT, NAMENS_ABKÜRZUNG)))
    Autorinfo = Series(Alternative(Token("AUTORIN"), Token("AUTOR")), Name)
    Zusatz = Series(Token("ZUSATZ"), RE('\\s*.*', wR='', wL=''), TRENNER)
    EinBeleg = Series(OneOrMore(Series(NegativeLookahead(Series(Optional(LEER), Alternative(Token("*"), Token("BEDEUTUNG"), Token("AUTOR"), Token("NAME"), Token("ZUSATZ")))), RE('\\s*.*\\s*', wR='', wL=''))), Optional(Zusatz))
    Belege = Series(Token("BELEGE"), Optional(LEER), ZeroOrMore(Series(Token("*"), EinBeleg)))
    DeutscheBedeutung = Series(Token("DEU"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wL=''))
    LateinischeBedeutung = Series(Token("LAT"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wL=''))
    Interpretamente = Series(LateinischeBedeutung, Optional(LEER), Required(DeutscheBedeutung), Optional(LEER))
    Bedeutungskategorie = Series(RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wL=''), Optional(LEER))
    Bedeutung = Series(Alternative(Interpretamente, Bedeutungskategorie), Optional(Belege))
    BedeutungsPosition = OneOrMore(Series(Token("BEDEUTUNG"), Optional(LEER), Required(Bedeutung)))
    VerweisZiel = RE('<\\w+>')
    Verweis = RE('\\w+')
    Beleg = Verweis
    Schreibweise = Alternative(Token("vizreg-"), Token("festregel(a)"), Token("fezdregl(a)"), Token("fat-"))
    SWVariante = Series(Schreibweise, Token(":"), Beleg)
    SWTyp = Alternative(Token("script."), Token("script. fat-"))
    SchreibweisenPosition = Series(Token("SCHREIBWEISE"), Optional(LEER), Required(SWTyp), Token(":"), Optional(LEER), Required(SWVariante), ZeroOrMore(Series(TRENNER, SWVariante)), Optional(LEER))
    ArtikelKopf = SchreibweisenPosition
    _genus = Alternative(Token("maskulinum"), Token("m."), Token("femininum"), Token("f."), Token("neutrum"), Token("n."))
    Flexion = RE('-?[a-z]+', wL='')
    Flexionen = Series(Flexion, ZeroOrMore(Series(Token(","), Required(Flexion))))
    GVariante = Series(Flexionen, Optional(_genus), Token(":"), Beleg)
    GrammatikVarianten = Series(TRENNER, GVariante)
    _wortart = Alternative(Token("nomen"), Token("n."), Token("verb"), Token("v."), Token("adverb"), Token("adv."), Token("adjektiv"), Token("adj."))
    GrammatikPosition = Series(Token("GRAMMATIK"), Optional(LEER), Required(_wortart), Required(TRENNER), Required(Flexionen), Optional(_genus), ZeroOrMore(GrammatikVarianten), Optional(TRENNER))
    LVZusatz = Series(Token("ZUSATZ"), Token("sim."))
    LVariante = RE('(?:[a-z]|-)+')
    LemmaVarianten = Series(Token("VARIANTEN"), Optional(LEER), Required(LVariante), ZeroOrMore(Series(TRENNER, LVariante)), Optional(Series(TRENNER, LVZusatz)), Optional(TRENNER))
    _tll = Token("*")
    Lemma = Series(Optional(_tll), WORT_KLEIN, Optional(LEER))
    LemmaPosition = Series(Token("LEMMA"), Required(Lemma), Optional(LemmaVarianten), Required(GrammatikPosition))
    Artikel = Series(Optional(LEER), Required(LemmaPosition), Optional(ArtikelKopf), Required(BedeutungsPosition), Required(Autorinfo), Optional(LEER), DATEI_ENDE)
    root__ = Artikel
    

#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

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
        elif nd.parser.name != "Zusatz":
            raise AssertionError(nd.as_sexpr())
        else:
            n += 1
        new_result.append(nd)
    node.result = tuple(new_result)


MLW_AST_transformation_table = {
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

MLWTransform = partial(traverse, processing_table=MLW_AST_transformation_table)


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class MLWCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a MLW source file.
    """

    def __init__(self, grammar_name="MLW"):
        super(MLWCompiler, self).__init__()
        assert re.match('\w+\Z', grammar_name)

    def on_Artikel(self, node):
        return node

    def on_LemmaPosition(self, node):
        pass

    def on_Lemma(self, node):
        pass

    def on__tll(self, node):
        pass

    def on_LemmaVarianten(self, node):
        pass

    def on_LVariante(self, node):
        pass

    def on_LVZusatz(self, node):
        pass

    def on_GrammatikPosition(self, node):
        pass

    def on__wortart(self, node):
        pass

    def on_GrammatikVarianten(self, node):
        pass

    def on_GVariante(self, node):
        pass

    def on_Flexionen(self, node):
        pass

    def on_Flexion(self, node):
        pass

    def on__genus(self, node):
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

    def on_WORT(self, node):
        pass

    def on_WORT_GROSS(self, node):
        pass

    def on_WORT_KLEIN(self, node):
        pass

    def on_LAT_WORT(self, node):
        pass

    def on_GROSSSCHRIFT(self, node):
        pass

    def on_TRENNER(self, node):
        pass

    def on_ZSPRUNG(self, node):
        pass

    def on_LEER(self, node):
        pass

    def on_DATEI_ENDE(self, node):
        pass

    def on_NIEMALS(self, node):
        pass


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_MLW(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    return compile_source(source, MLWScanner,
                          MLWGrammar(), MLWTransform, MLWCompiler())

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
