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
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, Synonym, \
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, MockParser, \
    traverse, remove_children_if, merge_children, TRUE_CONDITION, is_anonymous, \
    reduce_single_child, replace_by_single_child, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_parser, remove_content, remove_brackets, replace_parser, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last


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
    
    block_environment   = known_environment | generic_block
    known_environment   = itemize | enumerate | figure | table | quotation
                        | verbatim
    generic_block       = begin_generic_block sequence §end_generic_block
    begin_generic_block = -&LB begin_environment -&LB
    end_generic_block   = -&LB  end_environment  -&LB
    
    itemize             = "\begin{itemize}" [PARSEP] { item } §"\end{itemize}"
    enumerate           = "\begin{enumerate}" [PARSEP] {item } §"\end{enumerate}"
    item                = "\item" [PARSEP] sequence
    
    figure              = "\begin{figure}" sequence "\end{figure}"
    quotation           = ("\begin{quotation}" sequence "\end{quotation}")
                        | ("\begin{quote}" sequence "\end{quote}")
    verbatim            = "\begin{verbatim}" sequence "\end{verbatim}"
    table               = "\begin{tabular}" table_config sequence "\end{tabular}"
    table_config        = "{" /[lcr|]+/~ "}"
    
    
    #### paragraphs and sequences of paragraphs ####
    
    block_of_paragraphs = /{/ sequence §/}/
    sequence            = { (paragraph | block_environment ) [PARSEP] }+
    
    paragraph           = { !blockcmd text_element //~ }+
    text_element       = command | text | block | inline_environment
    
    
    #### inline enivronments ####
    
    inline_environment  = known_inline_env | generic_inline_env
    known_inline_env    = inline_math
    generic_inline_env  = (begin_inline_env { text_element }+ §end_inline_env)
    begin_inline_env    = (-!LB begin_environment) | (begin_environment -!LB)
    end_inline_env      = end_environment
                          # (-!LB end_environment)   | (end_environment   -!LB)  # ambiguity with genric_block when EOF
    begin_environment   = "\begin{" §NAME §"}"
    end_environment     = "\end{" §::NAME §"}"
    
    inline_math         = "$" /[^$]*/ "$"
    
    
    #### commands ####
    
    command             = known_command | generic_command
    known_command       = footnote | includegraphics | caption
    generic_command     = !no_command CMDNAME [[ //~ config ] //~ block ]
    
    footnote            = "\footnote" block_of_paragraphs
    includegraphics     = "\includegraphics" [ config ] block
    caption             = "\caption" block
    
    
    #######################################################################
    #
    # low-level text and character sequences
    #
    #######################################################################
    
    
    config     = "[" cfgtext §"]"
    block      = /{/ { text_element } §/}/
    
    text       = { cfgtext | (BRACKETS //~) }+
    cfgtext    = { word_sequence | (ESCAPED //~) }+
    word_sequence = { TEXTCHUNK //~ }+
    
    no_command = "\begin{" | "\end" | BACKSLASH structural
    blockcmd   = BACKSLASH ( ( "begin{" | "end{" )
                             ( "enumerate" | "itemize" | "figure" | "quote"
                             | "quotation" | "tabular") "}"
                           | structural | begin_generic_block | end_generic_block )
    
    structural = "subsection" | "section" | "chapter" | "subsubsection"
               | "paragraph" | "subparagraph" | "item"
    
    
    #######################################################################
    #
    # Primitives
    #
    #######################################################################
    
    
    CMDNAME    = /\\(?:(?!_)\w)+/~
    NAME       = /\w+/~
    
    ESCAPED    = /\\[%$&_\/]/
    BRACKETS   = /[\[\]]/                       # left or right square bracket: [ ]
    TEXTCHUNK  = /[^\\%$&\{\}\[\]\s\n]+/        # some piece of text excluding whitespace,
                                                # linefeed and special characters
    LF         = !GAP /[ \t]*\n[ \t]*/          # linefeed but not an empty line
    PARSEP     = { GAP }+                       # paragraph separator
    GAP        = /[ \t]*(?:\n[ \t]*)+\n/~       # at least one empty line, i.e.
                                                # [whitespace] linefeed [whitespace] linefeed
    LB         = /\s*?\n|$/                     # backwards line break for Lookbehind-Operator
                                                # beginning of text marker '$' added for test code
    BACKSLASH  = /[\\]/
    
    EOF        = /(?!.)/                        # End-Of-File
    """
    begin_generic_block = Forward()
    block_environment = Forward()
    block_of_paragraphs = Forward()
    end_generic_block = Forward()
    text_element = Forward()
    source_hash__ = "9cdeab7d908861b396d3667373fdcb9a"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'%.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?', comment=r'%.*(?:\n|$)')
    wspL__ = ''
    wspR__ = WSP__
    EOF = RegExp('(?!.)')
    BACKSLASH = RegExp('[\\\\]')
    LB = RegExp('\\s*?\\n|$')
    GAP = RE('[ \\t]*(?:\\n[ \\t]*)+\\n')
    PARSEP = OneOrMore(GAP)
    LF = Series(NegativeLookahead(GAP), RegExp('[ \\t]*\\n[ \\t]*'))
    TEXTCHUNK = RegExp('[^\\\\%$&\\{\\}\\[\\]\\s\\n]+')
    BRACKETS = RegExp('[\\[\\]]')
    ESCAPED = RegExp('\\\\[%$&_/]')
    NAME = Capture(RE('\\w+'))
    CMDNAME = RE('\\\\(?:(?!_)\\w)+')
    structural = Alternative(Token("subsection"), Token("section"), Token("chapter"), Token("subsubsection"), Token("paragraph"), Token("subparagraph"), Token("item"))
    blockcmd = Series(BACKSLASH, Alternative(Series(Alternative(Token("begin{"), Token("end{")), Alternative(Token("enumerate"), Token("itemize"), Token("figure"), Token("quote"), Token("quotation"), Token("tabular")), Token("}")), structural, begin_generic_block, end_generic_block))
    no_command = Alternative(Token("\\begin{"), Token("\\end"), Series(BACKSLASH, structural))
    word_sequence = OneOrMore(Series(TEXTCHUNK, RE('')))
    cfgtext = OneOrMore(Alternative(word_sequence, Series(ESCAPED, RE(''))))
    text = OneOrMore(Alternative(cfgtext, Series(BRACKETS, RE(''))))
    block = Series(RegExp('{'), ZeroOrMore(text_element), Required(RegExp('}')))
    config = Series(Token("["), cfgtext, Required(Token("]")))
    caption = Series(Token("\\caption"), block)
    includegraphics = Series(Token("\\includegraphics"), Optional(config), block)
    footnote = Series(Token("\\footnote"), block_of_paragraphs)
    generic_command = Series(NegativeLookahead(no_command), CMDNAME, Optional(Series(Optional(Series(RE(''), config)), RE(''), block)))
    known_command = Alternative(footnote, includegraphics, caption)
    command = Alternative(known_command, generic_command)
    inline_math = Series(Token("$"), RegExp('[^$]*'), Token("$"))
    end_environment = Series(Token("\\end{"), Required(Pop(NAME)), Required(Token("}")))
    begin_environment = Series(Token("\\begin{"), Required(NAME), Required(Token("}")))
    end_inline_env = Synonym(end_environment)
    begin_inline_env = Alternative(Series(NegativeLookbehind(LB), begin_environment), Series(begin_environment, NegativeLookbehind(LB)))
    generic_inline_env = Series(begin_inline_env, OneOrMore(text_element), Required(end_inline_env))
    known_inline_env = Synonym(inline_math)
    inline_environment = Alternative(known_inline_env, generic_inline_env)
    text_element.set(Alternative(command, text, block, inline_environment))
    paragraph = OneOrMore(Series(NegativeLookahead(blockcmd), text_element, RE('')))
    sequence = OneOrMore(Series(Alternative(paragraph, block_environment), Optional(PARSEP)))
    block_of_paragraphs.set(Series(RegExp('{'), sequence, Required(RegExp('}'))))
    table_config = Series(Token("{"), RE('[lcr|]+'), Token("}"))
    table = Series(Token("\\begin{tabular}"), table_config, sequence, Token("\\end{tabular}"))
    verbatim = Series(Token("\\begin{verbatim}"), sequence, Token("\\end{verbatim}"))
    quotation = Alternative(Series(Token("\\begin{quotation}"), sequence, Token("\\end{quotation}")), Series(Token("\\begin{quote}"), sequence, Token("\\end{quote}")))
    figure = Series(Token("\\begin{figure}"), sequence, Token("\\end{figure}"))
    item = Series(Token("\\item"), Optional(PARSEP), sequence)
    enumerate = Series(Token("\\begin{enumerate}"), Optional(PARSEP), ZeroOrMore(item), Required(Token("\\end{enumerate}")))
    itemize = Series(Token("\\begin{itemize}"), Optional(PARSEP), ZeroOrMore(item), Required(Token("\\end{itemize}")))
    end_generic_block.set(Series(Lookbehind(LB), end_environment, Lookbehind(LB)))
    begin_generic_block.set(Series(Lookbehind(LB), begin_environment, Lookbehind(LB)))
    generic_block = Series(begin_generic_block, sequence, Required(end_generic_block))
    known_environment = Alternative(itemize, enumerate, figure, table, quotation, verbatim)
    block_environment.set(Alternative(known_environment, generic_block))
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
        node.result = '\n'
        # node.result = ('  ' if (n >= c) or (n < 0) else '\n')+ s[c:].rstrip(' \t')
        # node.parser = MockParser('COMMENT', '')
    elif s.find('\n') >= 0:
        node.result = '\n'
    else:
        node.result = ' '


def watch(node):
    print(node.as_sxpr())


LaTeX_AST_transformation_table = {
    # AST Transformations for the LaTeX-grammar
    "+": remove_children_if(lambda node: is_empty(node) or is_one_of(node, {'PARSEP'})),
    # remove_empty,
    "latexdoc": [],
    "preamble": [],
    "document": [],
    "frontpages": [],
    "Chapters": [],
    "Chapter": [],
    "Sections": [],
    "Section": [],
    "SubSections": [],
    "SubSection": [],
    "SubSubSections": [],
    "SubSubSection": [],
    "Paragraphs": [],
    "Paragraph": [],
    "SubParagraphs": [],
    "SubParagraph": [],
    "Bibliography": [],
    "Index": [],
    "block_environment": replace_by_single_child,
    "known_environment": replace_by_single_child,
    "generic_block": [],
    "begin_generic_block, end_generic_block": replace_by_single_child,
    "itemize, enumerate": [remove_brackets, flatten],
    "item": [remove_first],
    "figure": [],
    "quotation": [reduce_single_child, remove_brackets],
    "verbatim": [],
    "table": [],
    "table_config": [],
    "block_of_paragraphs": [],
    "sequence": [flatten],
    "paragraph": [flatten],
    "text_element": [],
    "inline_environment": replace_by_single_child,
    "known_inline_env": replace_by_single_child,
    "generic_inline_env": [],
    "begin_inline_env, end_inline_env": [replace_by_single_child],
    "begin_environment, end_environment": [remove_brackets, reduce_single_child],
    "inline_math": [remove_brackets, reduce_single_child],
    "command": [],
    "known_command": [],
    "generic_command": [flatten],
    "footnote": [],
    "includegraphics": [],
    "caption": [],
    "config": [remove_brackets],
    "block": [remove_brackets, reduce_single_child(is_anonymous)],
    "text": collapse,
    "cfgtext, word_sequence": [],
    "no_command, blockcmd": [],
    "structural": [],
    "CMDNAME": [remove_whitespace, reduce_single_child(is_anonymous)],
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
    ":Token": [],
    ":RE": replace_by_single_child,
    ":Whitespace": streamline_whitespace,
    "*": replace_by_single_child
}

LaTeXTransform = partial(traverse, processing_table=LaTeX_AST_transformation_table)


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
