#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys
sys.path.extend(['../../', '../', './'])

try:
    import regex as re
except ImportError:
    import re
from DHParser import is_filename, Grammar, Compiler, Lookbehind, \
    Alternative, Pop, Token, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    PreprocessorFunc, TransformationDict, remove_empty, reduce_single_child, \
    Node, TransformationFunc, traverse, remove_children_if, is_anonymous, \
    reduce_single_child, replace_by_single_child, remove_whitespace, \
    flatten, is_empty, collapse, replace_content, remove_brackets, \
    is_one_of, remove_first, remove_last, remove_tokens, remove_nodes, \
    is_whitespace, TOKEN_PTYPE
from DHParser.log import logging


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LyrikPreprocessor(text):
    return text

def get_preprocessor() -> PreprocessorFunc:
    return LyrikPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LyrikGrammar(Grammar):
    r"""Parser for a Lyrik source file, with this grammar:
    
    gedicht           = bibliographisches { LEERZEILE }+ [serie] §titel text /\s*/ ENDE
    
    bibliographisches = autor §"," [NZ] werk "," [NZ] ort "," [NZ] jahr "."
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
    source_hash__ = "e4060274178d9c633c6dbfafb34471bd"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r''
    WHITESPACE__ = r'[\t ]*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    ENDE = NegativeLookahead(RegExp('.'))
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
    werk = Series(wortfolge, Option(Series(Token("."), untertitel, mandatory=1)), Option(verknüpfung))
    autor = Series(namenfolge, Option(verknüpfung))
    bibliographisches = Series(autor, Token(","), Option(NZ), werk, Token(","), Option(NZ), ort, Token(","), Option(NZ), jahr, Token("."), mandatory=1)
    gedicht = Series(bibliographisches, OneOrMore(LEERZEILE), Option(serie), titel, text, RegExp('\\s*'), ENDE, mandatory=3)
    root__ = gedicht
    
def get_grammar() -> LyrikGrammar:
    global thread_local_Lyrik_grammar_singleton
    try:
        grammar = thread_local_Lyrik_grammar_singleton
    except NameError:
        thread_local_Lyrik_grammar_singleton = LyrikGrammar()
        grammar = thread_local_Lyrik_grammar_singleton
    return grammar


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
        [remove_nodes('NZ'), remove_tokens],
    "autor": [],
    "werk": [],
    "untertitel": [],
    "ort": [],
    "jahr":
        [reduce_single_child],
    "wortfolge":
        [flatten(is_one_of('WORT'), recursive=False), remove_last(is_whitespace), collapse],
    "namenfolge":
        [flatten(is_one_of('NAME'), recursive=False), remove_last(is_whitespace), collapse],
    "verknüpfung":
        [remove_tokens('<', '>'), reduce_single_child],
    "ziel":
        reduce_single_child,
    "gedicht, strophe, text":
        [flatten, remove_nodes('LEERZEILE'), remove_nodes('NZ')],
    "titel, serie":
        [flatten, remove_nodes('LEERZEILE'), remove_nodes('NZ'), collapse],
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
        print("Usage: LyrikCompiler.py [FILENAME]")
