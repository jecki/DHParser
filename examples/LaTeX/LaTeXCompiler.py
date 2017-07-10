#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import os
import sys
from functools import partial

try:
    import regex as re
except ImportError:
    import re
from DHParser.toolkit import logging, is_filename
from DHParser.parsers import Grammar, Compiler, Alternative, Pop, Required, Token, Synonym, \
    Optional, OneOrMore, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    ScannerFunc
from DHParser.syntaxtree import traverse, remove_brackets, reduce_single_child, replace_by_single_child, \
    remove_expendables, flatten, join, \
    collapse, replace_content, TransformationFunc, \
    remove_empty


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LaTeXScanner(text):
    return text

def get_scanner() -> ScannerFunc:
    return LaTeXScanner


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LaTeXGrammar(Grammar):
    r"""Parser for a LaTeX source file, with this grammar:
    
    # LaTeX-Grammar for DHParser
    
    @ testing    = True
    @ whitespace = /[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?/    # optional whitespace, including at most one linefeed
    @ comment    = /%.*(?:\n|$)/
    
    
    latexdoc       = preamble document
    preamble       = { command }+
    
    document       = [PARSEP] "\begin{document}" [PARSEP]
                     frontpages [PARSEP]
                     (Chapters | Sections) [PARSEP]
                     [Bibliography] [Index] [PARSEP]
                     "\end{document}" [PARSEP] §EOF
    frontpages     = sequence
    
    
    #######################################################################
    #
    # document structure
    #
    #######################################################################
    
    Chapters       = { Chapter [PARSEP] }+
    Chapter        = "\Chapter" block [PARSEP] { sequence | Sections }
    
    Sections       = { Section [PARSEP] }+
    Section        = "\Section" block [PARSEP] { sequence | SubSections }
    
    SubSections    = { SubSection [PARSEP] }+
    SubSection     = "\SubSection" block [PARSEP] { sequence | SubSubSections }
    
    SubSubSections = { SubSubSection [PARSEP] }+
    SubSubSection  = "\SubSubSection" block [PARSEP] { sequence | Paragraphs }
    
    Paragraphs     = { Paragraph [PARSEP] }+
    Paragraph      = "\paragraph" block [PARSEP] { sequence | SubParagraphs }
    
    SubParagraphs  = { SubParagraph [PARSEP] }+
    SubParagraph   = "\subparagpaph" block [PARSEP] { sequence }
    
    Bibliography   = "\bibliography" block [PARSEP]
    Index          = "\printindex" [PARSEP]
    
    
    #######################################################################
    #
    # document content
    #
    #######################################################################
    
    
    #### block environments ####
    
    block_enrivonment   = known_enrivonment | generic_enrivonment
    known_enrivonment   = itemize | enumerate | figure | table | quotation
                        | verbatim
    generic_enrivonment = begin_enrivonment sequence §end_enrivonment
    
    itemize             = "\begin{itemize}" [PARSEP] { item } §"\end{itemize}"
    enumerate           = "\begin{enumerate}" [PARSEP] {item } §"end{enumerate}"
    item                = "\item" [PARSEP] sequence
    
    figure              = "\begin{figure}" sequence "\end{figure}"
    quotation           = ("\begin{quotation}" sequence "\end{quotation}")
                        | ("\begin{quote}" sequence "\end{quote}")
    verbatim            = "\begin{verbatim}" sequence "\end{verbatim}"
    table               = "\begin{tabular}" table_config sequence "\end{tabular}"
    table_config        = "{" /[lcr|]+/~ "}"
    
    
    #### paragraphs and sequences of paragraphs ####
    
    block_of_paragraphs = /{/ sequence §/}/
    sequence            = { (paragraph | block_enrivonment ) [PARSEP] }+
    
    paragraph           = { !blockcmd text_elements //~ }+
    text_elements       = command | text | block | inline_enrivonment
    
    
    #### inline enivronments ####
    
    inline_enrivonment  = known_inline_env | generic_inline_env
    known_inline_env    = inline_math
    generic_inline_env  = begin_enrivonment { text_elements }+ §end_enrivonment
    begin_enrivonment   = "\begin{" §NAME §"}"
    end_enrivonment     = "\end{" §::NAME §"}"
    
    inline_math         = "$" MATH "$"
    
    
    #### commands ####
    
    command             = known_command | generic_command
    known_command       = footnote | includegraphics | caption
    generic_command     = CMDNAME [[ //~ config ] //~ block ]
    
    footnote            = "\footnote" block_of_paragraphs
    includegraphics     = "\includegraphics" config block
    caption             = "\caption" block
    
    #######################################################################
    #
    # low-level text and character sequences
    #
    #######################################################################
    
    config     = "[" cfgtext §"]"
    block      = /{/ { text_elements } §/}/
    
    text       = { cfgtext | (BRACKETS //~) }+
    cfgtext    = { word_sequence | (ESCAPED //~) }+
    word_sequence = { TEXTCHUNK //~ }+
    
    blockcmd   = /[\\]/ ("begin{" ("enumerate" | "itemize" | "figure" | "quote"
                                  | "quotation" | "tabular") "}"
                         | "subsection" | "section" | "chapter" | "subsubsection"
                         | "paragraph" | "subparagraph" | "item")
    
    
    #######################################################################
    #
    # Primitives
    #
    #######################################################################
    
    CMDNAME    = /\\(?:(?!_)\w)+/~
    NAME       = /\w+/~
    MATH       = /[\w_^{}[\]]*/~
    
    ESCAPED    = /\\[%$&_\/]/
    BRACKETS   = /[\[\]]/                       # left or right square bracket: [ ]
    TEXTCHUNK  = /[^\\%$&\{\}\[\]\s\n]+/        # some piece of text excluding whitespace,
                                                # linefeed and special characters
    WSPC       = /[ \t]+/                       # (horizontal) whitespace
    LF         = !PARSEP /[ \t]*\n[ \t]*/       # LF but not an empty line
    PARSEP     = /[ \t]*(?:\n[ \t]*)+\n[ \t]*/  # at least one empty line, i.e.
                                                # [whitespace] linefeed [whitespace] linefeed
    EOF        = !/./
    """
    block_enrivonment = Forward()
    block_of_paragraphs = Forward()
    text_elements = Forward()
    source_hash__ = "9f1579db1994211dc53dd4a8f317bfb6"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'%.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?', comment=r'%.*(?:\n|$)')
    wspL__ = ''
    wspR__ = WSP__
    EOF = NegativeLookahead(RE('.', wR=''))
    PARSEP = RE('[ \\t]*(?:\\n[ \\t]*)+\\n[ \\t]*', wR='')
    LF = Series(NegativeLookahead(PARSEP), RE('[ \\t]*\\n[ \\t]*', wR=''))
    WSPC = RE('[ \\t]+', wR='')
    TEXTCHUNK = RE('[^\\\\%$&\\{\\}\\[\\]\\s\\n]+', wR='')
    BRACKETS = RE('[\\[\\]]', wR='')
    ESCAPED = RE('\\\\[%$&_/]', wR='')
    MATH = RE('[\\w_^{}[\\]]*')
    NAME = Capture(RE('\\w+'))
    CMDNAME = RE('\\\\(?:(?!_)\\w)+')
    blockcmd = Series(RE('[\\\\]', wR=''), Alternative(Series(Token("begin{"), Alternative(Token("enumerate"), Token("itemize"), Token("figure"), Token("quote"), Token("quotation"), Token("tabular")), Token("}")), Token("subsection"), Token("section"), Token("chapter"), Token("subsubsection"), Token("paragraph"), Token("subparagraph"), Token("item")))
    word_sequence = OneOrMore(Series(TEXTCHUNK, RE('')))
    cfgtext = OneOrMore(Alternative(word_sequence, Series(ESCAPED, RE(''))))
    text = OneOrMore(Alternative(cfgtext, Series(BRACKETS, RE(''))))
    block = Series(RE('{', wR=''), ZeroOrMore(text_elements), Required(RE('}', wR='')))
    config = Series(Token("["), cfgtext, Required(Token("]")))
    caption = Series(Token("\\caption"), block)
    includegraphics = Series(Token("\\includegraphics"), config, block)
    footnote = Series(Token("\\footnote"), block_of_paragraphs)
    generic_command = Series(CMDNAME, Optional(Series(Optional(Series(RE(''), config)), RE(''), block)))
    known_command = Alternative(footnote, includegraphics, caption)
    command = Alternative(known_command, generic_command)
    inline_math = Series(Token("$"), MATH, Token("$"))
    end_enrivonment = Series(Token("\\end{"), Required(Pop(NAME)), Required(Token("}")))
    begin_enrivonment = Series(Token("\\begin{"), Required(NAME), Required(Token("}")))
    generic_inline_env = Series(begin_enrivonment, OneOrMore(text_elements), Required(end_enrivonment))
    known_inline_env = Synonym(inline_math)
    inline_enrivonment = Alternative(known_inline_env, generic_inline_env)
    text_elements.set(Alternative(command, text, block, inline_enrivonment))
    paragraph = OneOrMore(Series(NegativeLookahead(blockcmd), text_elements, RE('')))
    sequence = OneOrMore(Series(Alternative(paragraph, block_enrivonment), Optional(PARSEP)))
    block_of_paragraphs.set(Series(RE('{', wR=''), sequence, Required(RE('}', wR=''))))
    table_config = Series(Token("{"), RE('[lcr|]+'), Token("}"))
    table = Series(Token("\\begin{tabular}"), table_config, sequence, Token("\\end{tabular}"))
    verbatim = Series(Token("\\begin{verbatim}"), sequence, Token("\\end{verbatim}"))
    quotation = Alternative(Series(Token("\\begin{quotation}"), sequence, Token("\\end{quotation}")), Series(Token("\\begin{quote}"), sequence, Token("\\end{quote}")))
    figure = Series(Token("\\begin{figure}"), sequence, Token("\\end{figure}"))
    item = Series(Token("\\item"), Optional(PARSEP), sequence)
    enumerate = Series(Token("\\begin{enumerate}"), Optional(PARSEP), ZeroOrMore(item), Required(Token("end{enumerate}")))
    itemize = Series(Token("\\begin{itemize}"), Optional(PARSEP), ZeroOrMore(item), Required(Token("\\end{itemize}")))
    generic_enrivonment = Series(begin_enrivonment, sequence, Required(end_enrivonment))
    known_enrivonment = Alternative(itemize, enumerate, figure, table, quotation, verbatim)
    block_enrivonment.set(Alternative(known_enrivonment, generic_enrivonment))
    Index = Series(Token("\\printindex"), Optional(PARSEP))
    Bibliography = Series(Token("\\bibliography"), block, Optional(PARSEP))
    SubParagraph = Series(Token("\\subparagpaph"), block, Optional(PARSEP), ZeroOrMore(sequence))
    SubParagraphs = OneOrMore(Series(SubParagraph, Optional(PARSEP)))
    Paragraph = Series(Token("\\paragraph"), block, Optional(PARSEP), ZeroOrMore(Alternative(sequence, SubParagraphs)))
    Paragraphs = OneOrMore(Series(Paragraph, Optional(PARSEP)))
    SubSubSection = Series(Token("\\SubSubSection"), block, Optional(PARSEP), ZeroOrMore(Alternative(sequence, Paragraphs)))
    SubSubSections = OneOrMore(Series(SubSubSection, Optional(PARSEP)))
    SubSection = Series(Token("\\SubSection"), block, Optional(PARSEP), ZeroOrMore(Alternative(sequence, SubSubSections)))
    SubSections = OneOrMore(Series(SubSection, Optional(PARSEP)))
    Section = Series(Token("\\Section"), block, Optional(PARSEP), ZeroOrMore(Alternative(sequence, SubSections)))
    Sections = OneOrMore(Series(Section, Optional(PARSEP)))
    Chapter = Series(Token("\\Chapter"), block, Optional(PARSEP), ZeroOrMore(Alternative(sequence, Sections)))
    Chapters = OneOrMore(Series(Chapter, Optional(PARSEP)))
    frontpages = Synonym(sequence)
    document = Series(Optional(PARSEP), Token("\\begin{document}"), Optional(PARSEP), frontpages, Optional(PARSEP), Alternative(Chapters, Sections), Optional(PARSEP), Optional(Bibliography), Optional(Index), Optional(PARSEP), Token("\\end{document}"), Optional(PARSEP), Required(EOF))
    preamble = OneOrMore(command)
    latexdoc = Series(preamble, document)
    root__ = latexdoc
    
def get_grammar() -> LaTeXGrammar:
    global thread_local_LaTeX_grammar_singleton
    try:
        grammar = thread_local_LaTeX_grammar_singleton
        return grammar
    except NameError:
        thread_local_LaTeX_grammar_singleton = LaTeXGrammar()
        return thread_local_LaTeX_grammar_singleton


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def streamline_whitespace(node):
    assert node.tag_name in ['WSPC', ':Whitespace']
    s = str(node)
    c = s.find('%')
    n = s.find('\n')
    if c >= 0:
        node.result = ('  ' if (n >= c) or (n < 0) else '\n')+ s[c:].rstrip(' \t')
    elif s.find('\n') >= 0:
        node.result = '\n'
    else:
        node.result = ' '


LaTeX_AST_transformation_table = {
    # AST Transformations for the LaTeX-grammar
    "+":
        remove_empty,
    "latexdoc": [],
    "preamble": [],
    "document": [],
    "blockenv": [],
    "parblock": [],
    "sequence":
        flatten,
    "paragraph":
        [flatten(lambda node: not node.parser.name or node.parser.name == "text"),
         join('text', ':Whitespace')],
    "inlineenv": [],
    "beginenv": [],
    "endenv": [],
    "command": [],
    "config": [],
    "block": [remove_brackets, reduce_single_child],
    "text":
        [reduce_single_child, join('text', 'word_sequence', ':Whitespace')],
    "cfgtext": [flatten, reduce_single_child],
    "word_sequence":
        [collapse],
    "blockcmd": [],
    "CMDNAME":
        [remove_expendables, reduce_single_child],
    "NAME": [],
    "ESCAPED": [reduce_single_child],
    "BRACKETS": [],
    "TEXTCHUNK": [],
    "WSPC, :Whitespace":
        streamline_whitespace,
    "LF":
        replace_content(lambda node: '\n'),
    "PARSEP":
        replace_content(lambda node: '\n\n'),
    "EOF": [],
    "*":
        replace_by_single_child,
}

LaTeXTransform = partial(traverse, processing_table=LaTeX_AST_transformation_table)
# LaTeXTransform = lambda tree : 1

def get_transformer() -> TransformationFunc:
    return LaTeXTransform


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class LaTeXCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a LaTeX source file.
    """

    def __init__(self, grammar_name="LaTeX", grammar_source=""):
        super(LaTeXCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_latexdoc(self, node):
        return node.as_sexpr()

    def on_preamble(self, node):
        pass

    def on_document(self, node):
        pass

    def on_blockenv(self, node):
        pass

    def on_parblock(self, node):
        pass

    def on_sequence(self, node):
        pass

    def on_paragraph(self, node):
        pass

    def on_inlineenv(self, node):
        pass

    def on_beginenv(self, node):
        pass

    def on_endenv(self, node):
        pass

    def on_command(self, node):
        pass

    def on_config(self, node):
        pass

    def on_block(self, node):
        pass

    def on_text(self, node):
        pass

    def on_cfgtext(self, node):
        pass

    def on_word_sequence(self, node):
        pass

    def on_blockcmd(self, node):
        pass

    def on_CMDNAME(self, node):
        pass

    def on_NAME(self, node):
        pass

    def on_ESCAPED(self, node):
        pass

    def on_BRACKETS(self, node):
        pass

    def on_TEXTCHUNK(self, node):
        pass

    def on_WSPC(self, node):
        pass

    def on_LF(self, node):
        pass

    def on_PARSEP(self, node):
        pass

    def on_EOF(self, node):
        pass


def get_compiler(grammar_name="LaTeX", grammar_source="") -> LaTeXCompiler:
    global thread_local_LaTeX_compiler_singleton
    try:
        compiler = thread_local_LaTeX_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except NameError:
        thread_local_LaTeX_compiler_singleton = \
            LaTeXCompiler(grammar_name, grammar_source)
        return thread_local_LaTeX_compiler_singleton 


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
        result = compile_source(source, get_scanner(), 
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
            print(result)
    else:
        print("Usage: LaTeXCompiler.py [FILENAME]")
