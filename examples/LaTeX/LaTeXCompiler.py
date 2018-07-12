#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from collections import defaultdict
import os
import sys
from functools import partial

try:
    import regex as re
except ImportError:
    import re
from DHParser import is_filename, Grammar, Compiler, Lookbehind, Alternative, Pop, \
    Synonym, Whitespace, Token, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    PreprocessorFunc, TransformationDict, \
    Node, TransformationFunc, traverse, remove_children_if, is_anonymous, \
    reduce_single_child, replace_by_single_child, remove_whitespace, \
    flatten, is_empty, collapse, replace_content, replace_content_by, remove_brackets, \
    is_one_of, traverse_locally, remove_tokens, remove_nodes, TOKEN_PTYPE, Error
from DHParser.log import logging


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LaTeXPreprocessor(text):
    return text

def get_preprocessor() -> PreprocessorFunc:
    return LaTeXPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LaTeXGrammar(Grammar):
    r"""Parser for a LaTeX source file, with this grammar:
    
    # LaTeX-Grammar for DHParser
    
    # preamble
    @ whitespace = /[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?/    # optional whitespace, including at most one linefeed
    @ comment    = /%.*/
    
    ########################################################################
    #
    # outer document structure
    #
    ########################################################################
    
    latexdoc       = preamble document
    preamble       = { [WSPC] command }+
    
    document       = [WSPC] "\begin{document}"
                     frontpages
                     (Chapters | Sections)
                     [Bibliography] [Index] [WSPC]
                     "\end{document}" [WSPC] §EOF
    frontpages     = sequence
    
    
    #######################################################################
    #
    # document structure
    #
    #######################################################################
    
    Chapters       = { [WSPC] Chapter }+
    Chapter        = "\chapter" heading { sequence | Sections }
    
    Sections       = { [WSPC] Section }+
    Section        = "\section" heading { sequence | SubSections }
    
    SubSections    = { [WSPC] SubSection }+
    SubSection     = "\subsection" heading { sequence | SubSubSections }
    
    SubSubSections = { [WSPC] SubSubSection }+
    SubSubSection  = "\subsubsection" heading { sequence | Paragraphs }
    
    Paragraphs     = { [WSPC] Paragraph  }+
    Paragraph      = "\paragraph" heading { sequence | SubParagraphs }
    
    SubParagraphs  = { [WSPC] SubParagraph }+
    SubParagraph   = "\subparagraph" heading [ sequence ]
    
    Bibliography   = [WSPC] "\bibliography" heading
    Index          = [WSPC] "\printindex"
    
    heading        = block
    
    #######################################################################
    #
    # document content
    #
    #######################################################################
    
    
    #### block environments ####
    
    block_environment   = known_environment | generic_block
    known_environment   = itemize | enumerate | figure | tabular | quotation
                        | verbatim
    generic_block       = begin_generic_block sequence §end_generic_block
    begin_generic_block = -&LB begin_environment LFF
    end_generic_block   = -&LB  end_environment LFF
    
    itemize             = "\begin{itemize}" [WSPC] { item } §"\end{itemize}"
    enumerate           = "\begin{enumerate}" [WSPC] {item } §"\end{enumerate}"
    item                = "\item" sequence
    
    figure              = "\begin{figure}" sequence §"\end{figure}"
    quotation           = ("\begin{quotation}" sequence §"\end{quotation}")
                        | ("\begin{quote}" sequence §"\end{quote}")
    verbatim            = "\begin{verbatim}" sequence §"\end{verbatim}"
    tabular             = "\begin{tabular}" tabular_config { tabular_row } §"\end{tabular}"
    tabular_row         = (multicolumn | tabular_cell) { "&" (multicolumn | tabular_cell) }
                          "\\" ( hline | { cline } )
    tabular_cell        = { line_element //~ }
    tabular_config      = "{" /[lcr|]+/~ §"}"
    
    
    #### paragraphs and sequences of paragraphs ####
    
    block_of_paragraphs = "{" [sequence] §"}"
    sequence            = [WSPC] { (paragraph | block_environment ) [PARSEP] }+
    paragraph           = { !blockcmd text_element //~ }+
    text_element        = line_element | LINEFEED
    line_element        = text | block | inline_environment | command
    
    
    #### inline enivronments ####
    
    inline_environment  = known_inline_env | generic_inline_env
    known_inline_env    = inline_math
    generic_inline_env  = begin_inline_env //~ paragraph §end_inline_env
    begin_inline_env    = (-!LB begin_environment) | (begin_environment !LFF)
    end_inline_env      = end_environment
                          ## (-!LB end_environment)   | (end_environment !LFF)  # ambiguity with generic_block when EOF
    begin_environment   = /\\begin{/ §NAME /}/
    end_environment     = /\\end{/ §::NAME /}/
    
    inline_math         = /\$/ /[^$]*/ §/\$/
    
    
    #### commands ####
    
    command             = known_command | text_command | generic_command
    known_command       = citet | citep | footnote | includegraphics | caption
                        | multicolumn | hline | cline | documentclass | pdfinfo
    text_command        = TXTCOMMAND | ESCAPED | BRACKETS
    generic_command     = !no_command CMDNAME [[ //~ config ] //~ block ]
    
    citet               = "\citet" [config] block
    citep               = ("\citep" | "\cite") [config] block
    footnote            = "\footnote" block_of_paragraphs
    includegraphics     = "\includegraphics" [ config ] block
    caption             = "\caption" block
    multicolumn         = "\multicolumn" "{" INTEGER "}" tabular_config block_of_paragraphs
    hline               = "\hline"
    cline               = "\cline{" INTEGER "-" INTEGER "}"
    documentclass       = "\documentclass" [ config ] block
    pdfinfo             = "\pdfinfo" block
    
    
    #######################################################################
    #
    # low-level text and character sequences
    #
    #######################################################################
    
    
    config     = "[" cfg_text §"]"
    cfg_text   = { ([//~] text) | CMDNAME | SPECIAL }
    block      = /{/ //~ { !blockcmd text_element //~ } §/}/
    text       = TEXTCHUNK { //~ TEXTCHUNK }
    
    no_command = "\begin{" | "\end" | BACKSLASH structural
    blockcmd   = BACKSLASH ( ( "begin{" | "end{" )
                             ( "enumerate" | "itemize" | "figure" | "quote"
                             | "quotation" | "tabular") "}"
                           | structural | begin_generic_block | end_generic_block )
    
    structural = "subsection" | "section" | "chapter" | "subsubsection"
               | "paragraph" | "subparagraph" | "item"
    
    
    #######################################################################
    #
    # primitives
    #
    #######################################################################
    
    
    CMDNAME    = /\\(?:(?!_)\w)+/~
    TXTCOMMAND = /\\text\w+/
    ESCAPED    = /\\[%$&_\/{}]/
    SPECIAL    = /[$&_\\\\\/]/
    BRACKETS   = /[\[\]]/                       # left or right square bracket: [ ]
    LINEFEED   = /[\\][\\]/
    
    NAME       = /\w+/~
    INTEGER    = /\d+/~
    
    TEXTCHUNK  = /[^\\%$&\{\}\[\]\s\n]+/        # some piece of text excluding whitespace,
                                                # linefeed and special characters
    LF         = NEW_LINE { COMMENT__ WHITESPACE__ }   # linefeed but not an empty line
    LFF        = NEW_LINE [ WSPC ]              # at least one linefeed
    PARSEP     = { WHITESPACE__ COMMENT__ } GAP [WSPC] # paragraph separator
    WSPC       = { COMMENT__ | /\s+/ }+         # arbitrary horizontal or vertical whitespace
    GAP        = /[ \t]*(?:\n[ \t]*)+\n/~       # at least one empty line, i.e.
                                                # [whitespace] linefeed [whitespace] linefeed
    NEW_LINE   = /[ \t]*/ [COMMENT__] /\n/
    LB         = /\s*?\n|$/                     # backwards line break for Lookbehind-Operator
                                                # beginning of text marker '$' added for test code
    BACKSLASH  = /[\\]/
    
    EOF        = /(?!.)/                        # End-Of-File
    """
    begin_generic_block = Forward()
    block_environment = Forward()
    block_of_paragraphs = Forward()
    end_generic_block = Forward()
    paragraph = Forward()
    tabular_config = Forward()
    text_element = Forward()
    source_hash__ = "840c0f34c77bbbe0433e7691fe68f884"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'%.*'
    WHITESPACE__ = r'[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    EOF = RegExp('(?!.)')
    BACKSLASH = RegExp('[\\\\]')
    LB = RegExp('\\s*?\\n|$')
    NEW_LINE = Series(RegExp('[ \\t]*'), Option(RegExp(COMMENT__)), RegExp('\\n'))
    GAP = Series(RegExp('[ \\t]*(?:\\n[ \\t]*)+\\n'), wsp__)
    WSPC = OneOrMore(Alternative(RegExp(COMMENT__), RegExp('\\s+')))
    PARSEP = Series(ZeroOrMore(Series(RegExp(WHITESPACE__), RegExp(COMMENT__))), GAP, Option(WSPC))
    LFF = Series(NEW_LINE, Option(WSPC))
    LF = Series(NEW_LINE, ZeroOrMore(Series(RegExp(COMMENT__), RegExp(WHITESPACE__))))
    TEXTCHUNK = RegExp('[^\\\\%$&\\{\\}\\[\\]\\s\\n]+')
    INTEGER = Series(RegExp('\\d+'), wsp__)
    NAME = Capture(Series(RegExp('\\w+'), wsp__))
    LINEFEED = RegExp('[\\\\][\\\\]')
    BRACKETS = RegExp('[\\[\\]]')
    SPECIAL = RegExp('[$&_\\\\\\\\/]')
    ESCAPED = RegExp('\\\\[%$&_/{}]')
    TXTCOMMAND = RegExp('\\\\text\\w+')
    CMDNAME = Series(RegExp('\\\\(?:(?!_)\\w)+'), wsp__)
    structural = Alternative(Series(Token("subsection"), wsp__), Series(Token("section"), wsp__), Series(Token("chapter"), wsp__), Series(Token("subsubsection"), wsp__), Series(Token("paragraph"), wsp__), Series(Token("subparagraph"), wsp__), Series(Token("item"), wsp__))
    blockcmd = Series(BACKSLASH, Alternative(Series(Alternative(Series(Token("begin{"), wsp__), Series(Token("end{"), wsp__)), Alternative(Series(Token("enumerate"), wsp__), Series(Token("itemize"), wsp__), Series(Token("figure"), wsp__), Series(Token("quote"), wsp__), Series(Token("quotation"), wsp__), Series(Token("tabular"), wsp__)), Series(Token("}"), wsp__)), structural, begin_generic_block, end_generic_block))
    no_command = Alternative(Series(Token("\\begin{"), wsp__), Series(Token("\\end"), wsp__), Series(BACKSLASH, structural))
    text = Series(TEXTCHUNK, ZeroOrMore(Series(RegExp(''), wsp__, TEXTCHUNK)))
    block = Series(RegExp('{'), RegExp(''), wsp__, ZeroOrMore(Series(NegativeLookahead(blockcmd), text_element, RegExp(''), wsp__)), RegExp('}'), mandatory=4)
    cfg_text = ZeroOrMore(Alternative(Series(Option(Series(RegExp(''), wsp__)), text), CMDNAME, SPECIAL))
    config = Series(Series(Token("["), wsp__), cfg_text, Series(Token("]"), wsp__), mandatory=2)
    pdfinfo = Series(Series(Token("\\pdfinfo"), wsp__), block)
    documentclass = Series(Series(Token("\\documentclass"), wsp__), Option(config), block)
    cline = Series(Series(Token("\\cline{"), wsp__), INTEGER, Series(Token("-"), wsp__), INTEGER, Series(Token("}"), wsp__))
    hline = Series(Token("\\hline"), wsp__)
    multicolumn = Series(Series(Token("\\multicolumn"), wsp__), Series(Token("{"), wsp__), INTEGER, Series(Token("}"), wsp__), tabular_config, block_of_paragraphs)
    caption = Series(Series(Token("\\caption"), wsp__), block)
    includegraphics = Series(Series(Token("\\includegraphics"), wsp__), Option(config), block)
    footnote = Series(Series(Token("\\footnote"), wsp__), block_of_paragraphs)
    citep = Series(Alternative(Series(Token("\\citep"), wsp__), Series(Token("\\cite"), wsp__)), Option(config), block)
    citet = Series(Series(Token("\\citet"), wsp__), Option(config), block)
    generic_command = Series(NegativeLookahead(no_command), CMDNAME, Option(Series(Option(Series(RegExp(''), wsp__, config)), RegExp(''), wsp__, block)))
    text_command = Alternative(TXTCOMMAND, ESCAPED, BRACKETS)
    known_command = Alternative(citet, citep, footnote, includegraphics, caption, multicolumn, hline, cline, documentclass, pdfinfo)
    command = Alternative(known_command, text_command, generic_command)
    inline_math = Series(RegExp('\\$'), RegExp('[^$]*'), RegExp('\\$'), mandatory=2)
    end_environment = Series(RegExp('\\\\end{'), Pop(NAME), RegExp('}'), mandatory=1)
    begin_environment = Series(RegExp('\\\\begin{'), NAME, RegExp('}'), mandatory=1)
    end_inline_env = Synonym(end_environment)
    begin_inline_env = Alternative(Series(NegativeLookbehind(LB), begin_environment), Series(begin_environment, NegativeLookahead(LFF)))
    generic_inline_env = Series(begin_inline_env, RegExp(''), wsp__, paragraph, end_inline_env, mandatory=4)
    known_inline_env = Synonym(inline_math)
    inline_environment = Alternative(known_inline_env, generic_inline_env)
    line_element = Alternative(text, block, inline_environment, command)
    text_element.set(Alternative(line_element, LINEFEED))
    paragraph.set(OneOrMore(Series(NegativeLookahead(blockcmd), text_element, RegExp(''), wsp__)))
    sequence = Series(Option(WSPC), OneOrMore(Series(Alternative(paragraph, block_environment), Option(PARSEP))))
    block_of_paragraphs.set(Series(Series(Token("{"), wsp__), Option(sequence), Series(Token("}"), wsp__), mandatory=2))
    tabular_config.set(Series(Series(Token("{"), wsp__), RegExp('[lcr|]+'), wsp__, Series(Token("}"), wsp__), mandatory=3))
    tabular_cell = ZeroOrMore(Series(line_element, RegExp(''), wsp__))
    tabular_row = Series(Alternative(multicolumn, tabular_cell), ZeroOrMore(Series(Series(Token("&"), wsp__), Alternative(multicolumn, tabular_cell))), Series(Token("\\\\"), wsp__), Alternative(hline, ZeroOrMore(cline)))
    tabular = Series(Series(Token("\\begin{tabular}"), wsp__), tabular_config, ZeroOrMore(tabular_row), Series(Token("\\end{tabular}"), wsp__), mandatory=3)
    verbatim = Series(Series(Token("\\begin{verbatim}"), wsp__), sequence, Series(Token("\\end{verbatim}"), wsp__), mandatory=2)
    quotation = Alternative(Series(Series(Token("\\begin{quotation}"), wsp__), sequence, Series(Token("\\end{quotation}"), wsp__), mandatory=2), Series(Series(Token("\\begin{quote}"), wsp__), sequence, Series(Token("\\end{quote}"), wsp__), mandatory=2))
    figure = Series(Series(Token("\\begin{figure}"), wsp__), sequence, Series(Token("\\end{figure}"), wsp__), mandatory=2)
    item = Series(Series(Token("\\item"), wsp__), sequence)
    enumerate = Series(Series(Token("\\begin{enumerate}"), wsp__), Option(WSPC), ZeroOrMore(item), Series(Token("\\end{enumerate}"), wsp__), mandatory=3)
    itemize = Series(Series(Token("\\begin{itemize}"), wsp__), Option(WSPC), ZeroOrMore(item), Series(Token("\\end{itemize}"), wsp__), mandatory=3)
    end_generic_block.set(Series(Lookbehind(LB), end_environment, LFF))
    begin_generic_block.set(Series(Lookbehind(LB), begin_environment, LFF))
    generic_block = Series(begin_generic_block, sequence, end_generic_block, mandatory=2)
    known_environment = Alternative(itemize, enumerate, figure, tabular, quotation, verbatim)
    block_environment.set(Alternative(known_environment, generic_block))
    heading = Synonym(block)
    Index = Series(Option(WSPC), Series(Token("\\printindex"), wsp__))
    Bibliography = Series(Option(WSPC), Series(Token("\\bibliography"), wsp__), heading)
    SubParagraph = Series(Series(Token("\\subparagraph"), wsp__), heading, Option(sequence))
    SubParagraphs = OneOrMore(Series(Option(WSPC), SubParagraph))
    Paragraph = Series(Series(Token("\\paragraph"), wsp__), heading, ZeroOrMore(Alternative(sequence, SubParagraphs)))
    Paragraphs = OneOrMore(Series(Option(WSPC), Paragraph))
    SubSubSection = Series(Series(Token("\\subsubsection"), wsp__), heading, ZeroOrMore(Alternative(sequence, Paragraphs)))
    SubSubSections = OneOrMore(Series(Option(WSPC), SubSubSection))
    SubSection = Series(Series(Token("\\subsection"), wsp__), heading, ZeroOrMore(Alternative(sequence, SubSubSections)))
    SubSections = OneOrMore(Series(Option(WSPC), SubSection))
    Section = Series(Series(Token("\\section"), wsp__), heading, ZeroOrMore(Alternative(sequence, SubSections)))
    Sections = OneOrMore(Series(Option(WSPC), Section))
    Chapter = Series(Series(Token("\\chapter"), wsp__), heading, ZeroOrMore(Alternative(sequence, Sections)))
    Chapters = OneOrMore(Series(Option(WSPC), Chapter))
    frontpages = Synonym(sequence)
    document = Series(Option(WSPC), Series(Token("\\begin{document}"), wsp__), frontpages, Alternative(Chapters, Sections), Option(Bibliography), Option(Index), Option(WSPC), Series(Token("\\end{document}"), wsp__), Option(WSPC), EOF, mandatory=9)
    preamble = OneOrMore(Series(Option(WSPC), command))
    latexdoc = Series(preamble, document)
    root__ = latexdoc
    
def get_grammar() -> LaTeXGrammar:
    global thread_local_LaTeX_grammar_singleton
    try:
        grammar = thread_local_LaTeX_grammar_singleton
    except NameError:
        thread_local_LaTeX_grammar_singleton = LaTeXGrammar()
        grammar = thread_local_LaTeX_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def streamline_whitespace(context):
    if context[-2].parser.ptype == ":_Token":
        return
    node = context[-1]
    assert node.tag_name in ['WSPC', ':Whitespace']
    s = node.content
    if s.find('%') >= 0:
        node.result = '\n'
        # c = s.find('%')
        # node.result = ('  ' if (n >= c) or (n < 0) else '\n')+ s[c:].rstrip(' \t')
        # node.parser = MockParser('COMMENT', '')
    elif s.find('\n') >= 0:
        node.result = '\n'
    else:
        node.result = ' ' if s else ''


def watch(node):
    print(node.as_sxpr())

flatten_structure = flatten(lambda context: is_anonymous(context) or is_one_of(
    context, {"Chapters", "Sections", "SubSections", "SubSubSections", "Paragraphs",
              "SubParagraphs", "sequence"}), recursive=True)


def is_commandname(context):
    """Returns True, if last node in the content represents a (potentially
    unknown) LaTeX-command."""
    node = context[-1]
    if node.parser.ptype == TOKEN_PTYPE:
        parent = context[-2]
        if len(parent.children) > 1:
            parent_name = parent.tag_name.lower()
            content = str(node)
            if (content == '\\' + parent_name
                or content == '\\begin{' + parent_name + '}'
                or content == '\\end{' + parent_name + '}'):
                return True
    return False


drop_expendables = remove_children_if(lambda context: is_empty(context) or
                                                      is_one_of(context, {'PARSEP', 'WSPC'}) or
                                                      is_commandname(context))


LaTeX_AST_transformation_table = {
    # AST Transformations for the LaTeX-grammar
    "+": [drop_expendables, flatten_structure],
    "latexdoc": [],
    "preamble": [traverse_locally({'+': remove_whitespace, 'block': replace_by_single_child})],
    "document": [flatten_structure],
    "pdfinfo": [],
    "frontpages": reduce_single_child,
    "Chapters, Sections, SubSections, SubSubSections, Paragraphs, SubParagraphs": [],
    "Chapter, Section, SubSection, SubSubSection, Paragraph, SubParagraph": [],
    "heading": reduce_single_child,
    "Bibliography": [],
    "Index": [],
    "block_environment": replace_by_single_child,
    "known_environment": replace_by_single_child,
    "generic_block": [],
    "begin_generic_block, end_generic_block": [remove_nodes('NEW_LINE'), replace_by_single_child],
    "itemize, enumerate": [remove_brackets, flatten],
    "item": [],
    "figure": [],
    "quotation": [reduce_single_child, remove_brackets],
    "verbatim": [],
    "tabular": [],
    "tabular_config, block_of_paragraphs": [remove_brackets, reduce_single_child],
    "tabular_row": [flatten, remove_tokens('&', '\\')],
    "tabular_cell": [flatten, remove_whitespace],
    "multicolumn": [remove_tokens('{', '}')],
    "hline": [remove_whitespace, reduce_single_child],
    "sequence": [flatten],
    "paragraph": [flatten],
    "text_element": replace_by_single_child,
    "line_element": replace_by_single_child,
    "inline_environment": replace_by_single_child,
    "known_inline_env": replace_by_single_child,
    "generic_inline_env": [],
    "begin_inline_env, end_inline_env": [replace_by_single_child],
    "begin_environment, end_environment": [remove_brackets, reduce_single_child],
    "inline_math": [remove_brackets, reduce_single_child],
    "command": replace_by_single_child,
    "known_command": replace_by_single_child,
    "text_command": [],
    "generic_command": [flatten],
    "footnote": [],
    "includegraphics": [],
    "caption": [],
    "config": [remove_brackets, reduce_single_child],
    "block": [remove_brackets, flatten, replace_by_single_child],
    "text": collapse,
    "no_command, blockcmd": [],
    "structural": [],
    "CMDNAME": [remove_whitespace, reduce_single_child],
    "TXTCOMMAND": [remove_whitespace, reduce_single_child],
    "NAME": [reduce_single_child, remove_whitespace, reduce_single_child],
    "ESCAPED": [replace_content(lambda node: str(node)[1:])],
    "BRACKETS": [],
    "TEXTCHUNK": [],
    "LF": [],
    "PARSEP": replace_content(lambda node: '\n\n'),
    "GAP": [],
    "LB": [],
    "BACKSLASH": [],
    "EOF": [],
    # "PARSEP": [replace_content_by('\n\n')],
    # "WSPC": [replace_content_by(' ')],
    ":Whitespace": streamline_whitespace,
    "*": replace_by_single_child
}


def LaTeXTransform() -> TransformationDict:
    return partial(traverse, processing_table=LaTeX_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    global thread_local_LaTeX_transformer_singleton
    try:
        transformer = thread_local_LaTeX_transformer_singleton
    except NameError:
        thread_local_LaTeX_transformer_singleton = LaTeXTransform()
        transformer = thread_local_LaTeX_transformer_singleton
    return transformer



#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def empty_defaultdict():
    """Returns a defaultdict with an empty defaultdict as default value."""
    return defaultdict(empty_defaultdict)


class LaTeXCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a LaTeX source file.
    """
    KNOWN_DOCUMENT_CLASSES = {'book', 'article'}
    KNOWN_LANGUAGES = {'english', 'german'}

    def __init__(self, grammar_name="LaTeX", grammar_source=""):
        super(LaTeXCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)
        self.metadata = defaultdict(empty_defaultdict)

    # def on_latexdoc(self, node):
    #     self.compile(node['preamble'])
    #     self.compile(node['document'])
    #     return node

    # def on_preamble(self, node):
    #     return node

    # def on_document(self, node):
    #     return node

    # def on_frontpages(self, node):
    #     return node

    # def on_Chapters(self, node):
    #     return node

    # def on_Chapter(self, node):
    #     return node

    # def on_Sections(self, node):
    #     return node

    # def on_Section(self, node):
    #     return node

    # def on_SubSections(self, node):
    #     return node

    # def on_SubSection(self, node):
    #     return node

    # def on_SubSubSections(self, node):
    #     return node

    # def on_SubSubSection(self, node):
    #     return node

    # def on_Paragraphs(self, node):
    #     return node

    # def on_Paragraph(self, node):
    #     return node

    # def on_SubParagraphs(self, node):
    #     return node

    # def on_SubParagraph(self, node):
    #     return node

    # def on_Bibliography(self, node):
    #     return node

    # def on_Index(self, node):
    #     return node

    # def on_heading(self, node):
    #     return node

    # def on_block_environment(self, node):
    #     return node

    # def on_known_environment(self, node):
    #     return node

    # def on_generic_block(self, node):
    #     return node

    # def on_begin_generic_block(self, node):
    #     return node

    # def on_end_generic_block(self, node):
    #     return node

    # def on_itemize(self, node):
    #     return node

    # def on_enumerate(self, node):
    #     return node

    # def on_item(self, node):
    #     return node

    # def on_figure(self, node):
    #     return node

    # def on_quotation(self, node):
    #     return node

    # def on_verbatim(self, node):
    #     return node

    # def on_tabular(self, node):
    #     return node

    # def on_tabular_row(self, node):
    #     return node

    # def on_tabular_cell(self, node):
    #     return node

    # def on_tabular_config(self, node):
    #     return node

    # def on_block_of_paragraphs(self, node):
    #     return node

    # def on_sequence(self, node):
    #     return node

    # def on_paragraph(self, node):
    #     return node

    # def on_text_element(self, node):
    #     return node

    # def on_line_element(self, node):
    #     return node

    # def on_inline_environment(self, node):
    #     return node

    # def on_known_inline_env(self, node):
    #     return node

    # def on_generic_inline_env(self, node):
    #     return node

    # def on_begin_inline_env(self, node):
    #     return node

    # def on_end_inline_env(self, node):
    #     return node

    # def on_begin_environment(self, node):
    #     return node

    # def on_end_environment(self, node):
    #     return node

    # def on_inline_math(self, node):
    #     return node

    # def on_command(self, node):
    #     return node

    # def on_known_command(self, node):
    #     return node

    # def on_text_command(self, node):
    #     return node

    # def on_generic_command(self, node):
    #     return node

    # def on_footnote(self, node):
    #     return node

    # def on_includegraphics(self, node):
    #     return node

    # def on_caption(self, node):
    #     return node

    # def on_multicolumn(self, node):
    #     return node

    # def on_hline(self, node):
    #     return node

    # def on_cline(self, node):
    #     return node

    def on_documentclass(self, node):
        """
        Saves the documentclass (if known) and the language (if given)
        in the metadata dictionary.
        """
        if 'config' in node:
            for it in {part.strip() for part in node['config'].content.split(',')}:
                if it in self.KNOWN_LANGUAGES:
                    if 'language' in node.attr:
                        self.metadata['language'] = it
                    else:
                        self.tree.new_error(node, 'Only one document language supported. '
                                            'Using %s, ignoring %s.'
                                            % (self.metadata['language'], it), Error.WARNING)
        if node['text'] in self.KNOWN_DOCUMENT_CLASSES:
            self.metadata['documentclass'] = node['text']
        return node

    def on_pdfinfo(self, node):
        return node

    # def on_config(self, node):
    #     return node

    # def on_cfg_text(self, node):
    #     return node

    # def on_block(self, node):
    #     return node

    # def on_text(self, node):
    #     return node

    # def on_no_command(self, node):
    #     return node

    # def on_blockcmd(self, node):
    #     return node

    # def on_structural(self, node):
    #     return node

    # def on_CMDNAME(self, node):
    #     return node

    # def on_TXTCOMMAND(self, node):
    #     return node

    # def on_ESCAPED(self, node):
    #     return node

    # def on_SPECIAL(self, node):
    #     return node

    # def on_BRACKETS(self, node):
    #     return node

    # def on_LINEFEED(self, node):
    #     return node

    # def on_NAME(self, node):
    #     return node

    # def on_INTEGER(self, node):
    #     return node

    # def on_TEXTCHUNK(self, node):
    #     return node

    # def on_LF(self, node):
    #     return node

    # def on_LFF(self, node):
    #     return node

    # def on_PARSEP(self, node):
    #     return node

    # def on_WSPC(self, node):
    #     return node

    # def on_GAP(self, node):
    #     return node

    # def on_NEW_LINE(self, node):
    #     return node

    # def on_LB(self, node):
    #     return node

    # def on_BACKSLASH(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler(grammar_name="LaTeX", grammar_source="") -> LaTeXCompiler:
    global thread_local_LaTeX_compiler_singleton
    try:
        compiler = thread_local_LaTeX_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_LaTeX_compiler_singleton = \
            LaTeXCompiler(grammar_name, grammar_source)
        compiler = thread_local_LaTeX_compiler_singleton
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
        print("Usage: LaTeXCompiler.py [FILENAME]")
