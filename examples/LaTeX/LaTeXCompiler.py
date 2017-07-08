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
from DHParser.parsers import Grammar, Compiler, nil_scanner, \
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, Synonym, \
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, compile_source, \
    last_value, counterpart, accumulate, ScannerFunc
from DHParser.syntaxtree import Node, traverse, remove_brackets, keep_children, \
    remove_children_if, reduce_single_child, replace_by_single_child, remove_whitespace, \
    remove_expendables, remove_tokens, flatten, is_whitespace, is_expendable, join, \
    collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, TransformationFunc, \
    remove_empty, replace_parser, apply_if


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
    
    # latex Grammar
    
    @ testing    = True
    @ whitespace = /[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?/    # optional whitespace, including at most one linefeed
    @ comment    = /%.*(?:\n|$)/
    
    latexdoc   = preamble document
    preamble   = { command }+
    
    document   = [PARSEP] { [PARSEP] paragraph } §EOF
    
    blockenv   = beginenv sequence §endenv
    
    parblock   = "{" sequence §"}"
    
    sequence   = { paragraph [PARSEP] }+
    paragraph  = { !blockcmd (command | block | text) //~ }+
    
    inlineenv  = beginenv { command | block | text }+ endenv
    beginenv   = "\begin{" §NAME §"}"
    endenv     = "\end{" §::NAME §"}"
    
    command    = CMDNAME [[ //~ config ] //~ block ]
    config     = "[" cfgtext §"]"
    block      = /{/ { command | text | block } §/}/
    
    text       = { cfgtext | (BRACKETS //~) }+
    cfgtext    = { word_sequence | (ESCAPED //~) }+
    word_sequence = { TEXTCHUNK //~ }+
    
    blockcmd   = "\subsection" | "\section" | "\chapter" | "\subsubsection"
                 | "\paragraph" | "\subparagraph" | "\begin{enumerate}"
                 | "\begin{itemize}" | "\item" | "\begin{figure}"
    
    CMDNAME    = /\\(?:(?!_)\w)+/~
    NAME       = /\w+/~
    
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
    block = Forward()
    command = Forward()
    source_hash__ = "936e76e84dd027b0af532abfad617d15"
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
    NAME = Capture(RE('\\w+'))
    CMDNAME = RE('\\\\(?:(?!_)\\w)+')
    blockcmd = Alternative(Token("\\subsection"), Token("\\section"), Token("\\chapter"), Token("\\subsubsection"), Token("\\paragraph"), Token("\\subparagraph"), Token("\\begin{enumerate}"), Token("\\begin{itemize}"), Token("\\item"), Token("\\begin{figure}"))
    word_sequence = OneOrMore(Series(TEXTCHUNK, RE('')))
    cfgtext = OneOrMore(Alternative(word_sequence, Series(ESCAPED, RE(''))))
    text = OneOrMore(Alternative(cfgtext, Series(BRACKETS, RE(''))))
    block.set(Series(RE('{', wR=''), ZeroOrMore(Alternative(command, text, block)), Required(RE('}', wR=''))))
    config = Series(Token("["), cfgtext, Required(Token("]")))
    command.set(Series(CMDNAME, Optional(Series(Optional(Series(RE(''), config)), RE(''), block))))
    endenv = Series(Token("\\end{"), Required(Pop(NAME)), Required(Token("}")))
    beginenv = Series(Token("\\begin{"), Required(NAME), Required(Token("}")))
    inlineenv = Series(beginenv, OneOrMore(Alternative(command, block, text)), endenv)
    paragraph = OneOrMore(Series(NegativeLookahead(blockcmd), Alternative(command, block, text), RE('')))
    sequence = OneOrMore(Series(paragraph, Optional(PARSEP)))
    parblock = Series(Token("{"), sequence, Required(Token("}")))
    blockenv = Series(beginenv, sequence, Required(endenv))
    document = Series(Optional(PARSEP), ZeroOrMore(Series(Optional(PARSEP), paragraph)), Required(EOF))
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
