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
    WHITESPACE_PTYPE, TOKEN_PTYPE, replace_parser



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
    source_hash__ = "5e5f53f5ef36706df8dc1ec0ecd73859"
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
    Name = Sequence(WORT, ZeroOrMore(Alternative(WORT, NAMENS_ABKÜRZUNG)))
    Autorinfo = Sequence(Alternative(Token("AUTORIN"), Token("AUTOR")), Name)
    Zusatz = Sequence(Token("ZUSATZ"), RE('\\s*.*', wR='', wL=''), TRENNER)
    EinBeleg = Sequence(OneOrMore(Sequence(NegativeLookahead(Sequence(Optional(LEER), Alternative(Token("*"), Token("BEDEUTUNG"), Token("AUTOR"), Token("NAME"), Token("ZUSATZ")))), RE('\\s*.*\\s*', wR='', wL=''))), Optional(Zusatz))
    Belege = Sequence(Token("BELEGE"), Optional(LEER), ZeroOrMore(Sequence(Token("*"), EinBeleg)))
    DeutscheBedeutung = Sequence(Token("DEU"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wL=''))
    LateinischeBedeutung = Sequence(Token("LAT"), RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wL=''))
    Interpretamente = Sequence(LateinischeBedeutung, Optional(LEER), Required(DeutscheBedeutung), Optional(LEER))
    Bedeutungskategorie = Sequence(RE('(?:(?![A-ZÄÖÜ][A-ZÄÖÜ]).)+', wL=''), Optional(LEER))
    Bedeutung = Sequence(Alternative(Interpretamente, Bedeutungskategorie), Optional(Belege))
    BedeutungsPosition = OneOrMore(Sequence(Token("BEDEUTUNG"), Optional(LEER), Required(Bedeutung)))
    VerweisZiel = RE('<\\w+>')
    Verweis = RE('\\w+')
    Beleg = Verweis
    Schreibweise = Alternative(Token("vizreg-"), Token("festregel(a)"), Token("fezdregl(a)"), Token("fat-"))
    SWVariante = Sequence(Schreibweise, Token(":"), Beleg)
    SWTyp = Alternative(Token("script."), Token("script. fat-"))
    SchreibweisenPosition = Sequence(Token("SCHREIBWEISE"), Optional(LEER), Required(SWTyp), Token(":"), Optional(LEER), Required(SWVariante), ZeroOrMore(Sequence(TRENNER, SWVariante)), Optional(LEER))
    ArtikelKopf = SchreibweisenPosition
    _genus = Alternative(Token("maskulinum"), Token("m."), Token("femininum"), Token("f."), Token("neutrum"), Token("n."))
    Flexion = RE('-?[a-z]+', wL='')
    Flexionen = Sequence(Flexion, ZeroOrMore(Sequence(Token(","), Required(Flexion))))
    GVariante = Sequence(Flexionen, Optional(_genus), Token(":"), Beleg)
    GrammatikVarianten = Sequence(TRENNER, GVariante)
    _wortart = Alternative(Token("nomen"), Token("n."), Token("verb"), Token("v."), Token("adverb"), Token("adv."), Token("adjektiv"), Token("adj."))
    GrammatikPosition = Sequence(Token("GRAMMATIK"), Optional(LEER), Required(_wortart), Required(TRENNER), Required(Flexionen), Optional(_genus), ZeroOrMore(GrammatikVarianten), Optional(TRENNER))
    LVZusatz = Sequence(Token("ZUSATZ"), Token("sim."))
    LVariante = RE('(?:[a-z]|-)+')
    LemmaVarianten = Sequence(Token("VARIANTEN"), Optional(LEER), Required(LVariante), ZeroOrMore(Sequence(TRENNER, LVariante)), Optional(Sequence(TRENNER, LVZusatz)), Optional(TRENNER))
    _tll = Token("*")
    Lemma = Sequence(Optional(_tll), WORT_KLEIN, Optional(LEER))
    LemmaPosition = Sequence(Token("LEMMA"), Required(Lemma), Optional(LemmaVarianten), Required(GrammatikPosition))
    Artikel = Sequence(Optional(LEER), Required(LemmaPosition), Optional(ArtikelKopf), Required(BedeutungsPosition), Required(Autorinfo), Optional(LEER), DATEI_ENDE)
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
    "Artikel": no_operation,
    "LemmaPosition":
        [partial(remove_tokens, tokens={'LEMMA'})],
    "Lemma": no_operation,
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
    "ArtikelKopf": no_operation,
    "SchreibweisenPosition":
        [partial(remove_tokens, tokens={'SCHREIBWEISE', ':'}),
         flatten, partial(remove_tokens, tokens={','})],
    "SWTyp": no_operation,
    "BedeutungsPosition":
        [flatten, partial(remove_tokens, tokens={'BEDEUTUNG'})],
    "Bedeutung": no_operation,
    "Bedeutungskategorie": no_operation,
    "Interpretamente": no_operation,
    "LateinischeBedeutung, DeutscheBedeutung":
        [remove_expendables, remove_tokens, reduce_single_child],
    "Belege":
        [flatten, remove_tokens],
    "EinBeleg":
        [flatten, remove_expendables, join_strings, reduce_single_child],
    "Beleg": no_operation,
    "VerweisZiel": no_operation,
    "Autorinfo":
        [partial(remove_tokens, tokens={'AUTORIN', 'AUTOR'})],
    "WORT, WORT_KLEIN, WORT_GROSS, GROSSSCHRIFT":
        [remove_expendables, reduce_single_child],
    "LEER, TRENNER, ZSPRUNG": partial(replace_parser, parser_name=WHITESPACE_KEYWORD),
    "DATEI_ENDE": no_operation,
    "NIEMALS": no_operation,
    (TOKEN_PTYPE, WHITESPACE_PTYPE):
        [remove_expendables, reduce_single_child],
    "+":
        remove_expendables,
    "~":
        partial(remove_tokens, tokens={',', ';'}),
    "*":
        [remove_expendables, replace_by_single_child]
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
