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
from DHParser import is_filename, Grammar, Compiler, Lookbehind, Alternative, Pop, \
    Token, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    PreprocessorFunc, TransformationDict, \
    Node, TransformationFunc, traverse, remove_children_if, is_anonymous, \
    reduce_single_child, replace_by_single_child, remove_whitespace, \
    flatten, is_empty, collapse, replace_content, remove_brackets, is_one_of, remove_first, \
    remove_tokens, remove_nodes, TOKEN_PTYPE
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
                          ## (-!LB end_environment)   | (end_environment !LFF)  # ambiguity with genric_block when EOF
    begin_environment   = /\\begin{/ §NAME /}/
    end_environment     = /\\end{/ §::NAME /}/
    
    inline_math         = /\$/ /[^$]*/ §/\$/
    
    
    #### commands ####
    
    command             = known_command | text_command | generic_command
    known_command       = footnote | includegraphics | caption | multicolumn | hline | cline
    text_command        = TXTCOMMAND | ESCAPED | BRACKETS
    generic_command     = !no_command CMDNAME [[ //~ config ] //~ block ]
    
    footnote            = "\footnote" block_of_paragraphs
    includegraphics     = "\includegraphics" [ config ] block
    caption             = "\caption" block
    multicolumn         = "\multicolumn" "{" INTEGER "}" tabular_config block_of_paragraphs
    hline               = "\hline"
    cline               = "\cline{" INTEGER "-" INTEGER "}"
    
    
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
    source_hash__ = "a078d3d46ee55a7543f37c62b3fb24a7"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'%.*'
    WHITESPACE__ = r'[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = WSP__
    EOF = RegExp('(?!.)')
    BACKSLASH = RegExp('[\\\\]')
    LB = RegExp('\\s*?\\n|$')
    NEW_LINE = Series(RegExp('[ \\t]*'), Option(RegExp(COMMENT__)), RegExp('\\n'))
    GAP = RE('[ \\t]*(?:\\n[ \\t]*)+\\n')
    WSPC = OneOrMore(Alternative(RegExp(COMMENT__), RegExp('\\s+')))
    PARSEP = Series(ZeroOrMore(Series(RegExp(WHITESPACE__), RegExp(COMMENT__))), GAP, Option(WSPC))
    LFF = Series(NEW_LINE, Option(WSPC))
    LF = Series(NEW_LINE, ZeroOrMore(Series(RegExp(COMMENT__), RegExp(WHITESPACE__))))
    TEXTCHUNK = RegExp('[^\\\\%$&\\{\\}\\[\\]\\s\\n]+')
    INTEGER = RE('\\d+')
    NAME = Capture(RE('\\w+'))
    LINEFEED = RegExp('[\\\\][\\\\]')
    BRACKETS = RegExp('[\\[\\]]')
    SPECIAL = RegExp('[$&_\\\\\\\\/]')
    ESCAPED = RegExp('\\\\[%$&_/{}]')
    TXTCOMMAND = RegExp('\\\\text\\w+')
    CMDNAME = RE('\\\\(?:(?!_)\\w)+')
    structural = Alternative(Token("subsection"), Token("section"), Token("chapter"), Token("subsubsection"), Token("paragraph"), Token("subparagraph"), Token("item"))
    blockcmd = Series(BACKSLASH, Alternative(Series(Alternative(Token("begin{"), Token("end{")), Alternative(Token("enumerate"), Token("itemize"), Token("figure"), Token("quote"), Token("quotation"), Token("tabular")), Token("}")), structural, begin_generic_block, end_generic_block))
    no_command = Alternative(Token("\\begin{"), Token("\\end"), Series(BACKSLASH, structural))
    text = Series(TEXTCHUNK, ZeroOrMore(Series(RE(''), TEXTCHUNK)))
    block = Series(RegExp('{'), RE(''), ZeroOrMore(Series(NegativeLookahead(blockcmd), text_element, RE(''))), RegExp('}'), mandatory=3)
    cfg_text = ZeroOrMore(Alternative(Series(Option(RE('')), text), CMDNAME, SPECIAL))
    config = Series(Token("["), cfg_text, Token("]"), mandatory=2)
    cline = Series(Token("\\cline{"), INTEGER, Token("-"), INTEGER, Token("}"))
    hline = Token("\\hline")
    multicolumn = Series(Token("\\multicolumn"), Token("{"), INTEGER, Token("}"), tabular_config, block_of_paragraphs)
    caption = Series(Token("\\caption"), block)
    includegraphics = Series(Token("\\includegraphics"), Option(config), block)
    footnote = Series(Token("\\footnote"), block_of_paragraphs)
    generic_command = Series(NegativeLookahead(no_command), CMDNAME, Option(Series(Option(Series(RE(''), config)), RE(''), block)))
    text_command = Alternative(TXTCOMMAND, ESCAPED, BRACKETS)
    known_command = Alternative(footnote, includegraphics, caption, multicolumn, hline, cline)
    command = Alternative(known_command, text_command, generic_command)
    inline_math = Series(RegExp('\\$'), RegExp('[^$]*'), RegExp('\\$'), mandatory=2)
    end_environment = Series(RegExp('\\\\end{'), Pop(NAME), RegExp('}'), mandatory=1)
    begin_environment = Series(RegExp('\\\\begin{'), NAME, RegExp('}'), mandatory=1)
    end_inline_env = Synonym(end_environment)
    begin_inline_env = Alternative(Series(NegativeLookbehind(LB), begin_environment), Series(begin_environment, NegativeLookahead(LFF)))
    generic_inline_env = Series(begin_inline_env, RE(''), paragraph, end_inline_env, mandatory=3)
    known_inline_env = Synonym(inline_math)
    inline_environment = Alternative(known_inline_env, generic_inline_env)
    line_element = Alternative(text, block, inline_environment, command)
    text_element.set(Alternative(line_element, LINEFEED))
    paragraph.set(OneOrMore(Series(NegativeLookahead(blockcmd), text_element, RE(''))))
    sequence = Series(Option(WSPC), OneOrMore(Series(Alternative(paragraph, block_environment), Option(PARSEP))))
    block_of_paragraphs.set(Series(Token("{"), Option(sequence), Token("}"), mandatory=2))
    tabular_config.set(Series(Token("{"), RE('[lcr|]+'), Token("}"), mandatory=2))
    tabular_cell = ZeroOrMore(Series(line_element, RE('')))
    tabular_row = Series(Alternative(multicolumn, tabular_cell), ZeroOrMore(Series(Token("&"), Alternative(multicolumn, tabular_cell))), Token("\\\\"), Alternative(hline, ZeroOrMore(cline)))
    tabular = Series(Token("\\begin{tabular}"), tabular_config, ZeroOrMore(tabular_row), Token("\\end{tabular}"), mandatory=3)
    verbatim = Series(Token("\\begin{verbatim}"), sequence, Token("\\end{verbatim}"), mandatory=2)
    quotation = Alternative(Series(Token("\\begin{quotation}"), sequence, Token("\\end{quotation}"), mandatory=2), Series(Token("\\begin{quote}"), sequence, Token("\\end{quote}"), mandatory=2))
    figure = Series(Token("\\begin{figure}"), sequence, Token("\\end{figure}"), mandatory=2)
    item = Series(Token("\\item"), sequence)
    enumerate = Series(Token("\\begin{enumerate}"), Option(WSPC), ZeroOrMore(item), Token("\\end{enumerate}"), mandatory=3)
    itemize = Series(Token("\\begin{itemize}"), Option(WSPC), ZeroOrMore(item), Token("\\end{itemize}"), mandatory=3)
    end_generic_block.set(Series(Lookbehind(LB), end_environment, LFF))
    begin_generic_block.set(Series(Lookbehind(LB), begin_environment, LFF))
    generic_block = Series(begin_generic_block, sequence, end_generic_block, mandatory=2)
    known_environment = Alternative(itemize, enumerate, figure, tabular, quotation, verbatim)
    block_environment.set(Alternative(known_environment, generic_block))
    heading = Synonym(block)
    Index = Series(Option(WSPC), Token("\\printindex"))
    Bibliography = Series(Option(WSPC), Token("\\bibliography"), heading)
    SubParagraph = Series(Token("\\subparagraph"), heading, Option(sequence))
    SubParagraphs = OneOrMore(Series(Option(WSPC), SubParagraph))
    Paragraph = Series(Token("\\paragraph"), heading, ZeroOrMore(Alternative(sequence, SubParagraphs)))
    Paragraphs = OneOrMore(Series(Option(WSPC), Paragraph))
    SubSubSection = Series(Token("\\subsubsection"), heading, ZeroOrMore(Alternative(sequence, Paragraphs)))
    SubSubSections = OneOrMore(Series(Option(WSPC), SubSubSection))
    SubSection = Series(Token("\\subsection"), heading, ZeroOrMore(Alternative(sequence, SubSubSections)))
    SubSections = OneOrMore(Series(Option(WSPC), SubSection))
    Section = Series(Token("\\section"), heading, ZeroOrMore(Alternative(sequence, SubSections)))
    Sections = OneOrMore(Series(Option(WSPC), Section))
    Chapter = Series(Token("\\chapter"), heading, ZeroOrMore(Alternative(sequence, Sections)))
    Chapters = OneOrMore(Series(Option(WSPC), Chapter))
    frontpages = Synonym(sequence)
    document = Series(Option(WSPC), Token("\\begin{document}"), frontpages, Alternative(Chapters, Sections), Option(Bibliography), Option(Index), Option(WSPC), Token("\\end{document}"), Option(WSPC), EOF, mandatory=9)
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
    if context[-2].parser.ptype == ":Token":
        return
    node = context[-1]
    assert node.tag_name in ['WSPC', ':Whitespace']
    s = str(node)
    c = s.find('%')
    n = s.find('\n')
    if c >= 0:
        node.result = '\n'
        # node.result = ('  ' if (n >= c) or (n < 0) else '\n')+ s[c:].rstrip(' \t')
        # node.parser = MockParser('COMMENT', '')
    elif s.find('\n') >= 0:
        node.result = '\n'
    else:
        node.result = ' '


def watch(node):
    print(node.as_sxpr())

flatten_structure = flatten(lambda context: is_anonymous(context) or is_one_of(
    context, {"Chapters", "Sections", "SubSections", "SubSubSections", "Paragraphs",
              "SubParagraphs", "sequence"}), True)


def is_commandname(context):
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
    "preamble": [],
    "document": [flatten_structure],
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
    ":Token":
        [remove_whitespace, reduce_single_child],
    ":RE": replace_by_single_child,
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

class LaTeXCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a LaTeX source file.
    """

    def __init__(self, grammar_name="LaTeX", grammar_source=""):
        super(LaTeXCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)

    def on_latexdoc(self, node):
        return node

    def on_preamble(self, node):
        pass

    def on_document(self, node):
        pass

    def on_frontpages(self, node):
        pass

    def on_Chapters(self, node):
        pass

    def on_Chapter(self, node):
        pass

    def on_Sections(self, node):
        pass

    def on_Section(self, node):
        pass

    def on_SubSections(self, node):
        pass

    def on_SubSection(self, node):
        pass

    def on_SubSubSections(self, node):
        pass

    def on_SubSubSection(self, node):
        pass

    def on_Paragraphs(self, node):
        pass

    def on_Paragraph(self, node):
        pass

    def on_SubParagraphs(self, node):
        pass

    def on_SubParagraph(self, node):
        pass

    def on_Bibliography(self, node):
        pass

    def on_Index(self, node):
        pass

    def on_block_environment(self, node):
        pass

    def on_known_environment(self, node):
        pass

    def on_generic_block(self, node):
        pass

    def on_begin_generic_block(self, node):
        pass

    def on_end_generic_block(self, node):
        pass

    def on_itemize(self, node):
        pass

    def on_enumerate(self, node):
        pass

    def on_item(self, node):
        pass

    def on_figure(self, node):
        pass

    def on_quotation(self, node):
        pass

    def on_verbatim(self, node):
        pass

    def on_table(self, node):
        pass

    def on_table_config(self, node):
        pass

    def on_block_of_paragraphs(self, node):
        pass

    def on_sequence(self, node):
        pass

    def on_paragraph(self, node):
        pass

    def on_text_element(self, node):
        pass

    def on_inline_environment(self, node):
        pass

    def on_known_inline_env(self, node):
        pass

    def on_generic_inline_env(self, node):
        pass

    def on_begin_inline_env(self, node):
        pass

    def on_begin_environment(self, node):
        pass

    def on_end_environment(self, node):
        pass

    def on_inline_math(self, node):
        pass

    def on_command(self, node):
        pass

    def on_known_command(self, node):
        pass

    def on_generic_command(self, node):
        pass

    def on_footnote(self, node):
        pass

    def on_includegraphics(self, node):
        pass

    def on_caption(self, node):
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

    def on_no_command(self, node):
        pass

    def on_blockcmd(self, node):
        pass

    def on_structural(self, node):
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

    def on_LB(self, node):
        pass

    def on_BACKSLASH(self, node):
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
