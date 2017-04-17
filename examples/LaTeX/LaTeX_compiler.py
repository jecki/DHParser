#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import sys
try:
    import regex as re
except ImportError:
    import re
from DHParser.toolkit import load_if_file    
from DHParser.parsers import GrammarBase, CompilerBase, nil_scanner, \
    Lookbehind, Lookahead, Alternative, Pop, Required, Token, \
    Optional, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Sequence, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, mixin_comment, full_compilation
from DHParser.syntaxtree import Node, remove_enclosing_delimiters, remove_children_if, \
    reduce_single_child, replace_by_single_child, remove_whitespace, TOKEN_KEYWORD, \
    no_operation, remove_expendables, remove_tokens, flatten, WHITESPACE_KEYWORD, \
    is_whitespace, is_expendable


#######################################################################
#
# SCANNER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def LaTeXScanner(text):
    return text


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LaTeXGrammar(GrammarBase):
    r"""Parser for a LaTeX source file, with this grammar:
    
    # latex Grammar
    
    @ whitespace = /[ \t]*\n?(?!\s*\n)[ \t]*/
    @ comment    = /%.*(?:\n|$)/
    
    genericenv = beginenv sequence endenv
    beginenv   = "\begin" §( "{" name "}" )
    endenv     = "\end" §( "{" ::name "}" )
    
    name       = ~/\w+/
    
    genericcmd = command [ config ] block
    command    = /\\\w+/
    config     = "[" cfgtext §"]"
    
    sequence   = { partext | parblock }
    
    parblock   = "{" { partext | parblock } §"}"
    block      = "{" { text | block } §"}"
    
    partext    = text | par
    text       = cfgtext | brackets
    cfgtext    = chunk | wspc | escaped
    
    escaped    = /\\[%$&]/
    brackets   = /[\[\]]/                   # left and right square brackets: [ ]
    chunk      = /[^\\%$&\{\}\[\]\s\n]+/    # some piece of text excluding whitespace,
                                            # linefeed and special characters
    wspc       = /[ \t]*\n?(?!\s*\n)[ \t]*/ # whitespace, including at most one linefeed
    lf         = /[ \t]*\n(?!\s*\n)/        # a linefeed, but not an empty line (i.e. par)
    par        = /\s*\n\s*\n/               # at least one empty line, i.e.
                                            # [whitespace] linefeed [whitespace] linefeed
    """
    block = Forward()
    parblock = Forward()
    source_hash__ = "9f01a5f7c1df86e103f920fda0339d14"
    parser_initialization__ = "upon instatiation"
    COMMENT__ = r'%.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'[ \t]*\n?(?!\s*\n)[ \t]*', comment=r'%.*(?:\n|$)')
    wspL__ = ''
    wspR__ = WSP__
    par = RE('\\s*\\n\\s*\\n', wR='')
    lf = RE('[ \\t]*\\n(?!\\s*\\n)', wR='')
    wspc = RE('[ \\t]*\\n?(?!\\s*\\n)[ \\t]*', wR='')
    chunk = RE('[^\\\\%$&\\{\\}\\[\\]\\s\\n]+', wR='')
    brackets = RE('[\\[\\]]', wR='')
    escaped = RE('\\\\[%$&]', wR='')
    cfgtext = Alternative(chunk, wspc, escaped)
    text = Alternative(cfgtext, brackets)
    partext = Alternative(text, par)
    block.set(Sequence(Token("{"), ZeroOrMore(Alternative(text, block)), Required(Token("}"))))
    parblock.set(Sequence(Token("{"), ZeroOrMore(Alternative(partext, parblock)), Required(Token("}"))))
    sequence = ZeroOrMore(Alternative(partext, parblock))
    config = Sequence(Token("["), cfgtext, Required(Token("]")))
    command = RE('\\\\\\w+', wR='')
    genericcmd = Sequence(command, Optional(config), block)
    name = Capture(RE('\\w+', wR='', wL=WSP__), "name")
    endenv = Sequence(Token("\\end"), Required(Sequence(Token("{"), Pop(name), Token("}"))))
    beginenv = Sequence(Token("\\begin"), Required(Sequence(Token("{"), name, Token("}"))))
    genericenv = Sequence(beginenv, sequence, endenv)
    root__ = genericenv
    

#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

LaTeX_ASTTransform = {
    # AST Transformations for the LaTeX-grammar
    "genericenv": no_operation,
    "beginenv": no_operation,
    "endenv": no_operation,
    "name": no_operation,
    "genericcmd": no_operation,
    "command": no_operation,
    "config": no_operation,
    "sequence": no_operation,
    "parblock": no_operation,
    "block": no_operation,
    "partext": no_operation,
    "text": no_operation,
    "cfgtext": no_operation,
    "escaped": no_operation,
    "brackets": no_operation,
    "chunk": no_operation,
    "wspc": no_operation,
    "lf": no_operation,
    "par": no_operation,
    "": no_operation
}

LaTeX_ASTPipeline = [LaTeX_ASTTransform]


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class LaTeXCompiler(CompilerBase):
    """Compiler for the abstract-syntax-tree of a LaTeX source file.
    """

    def __init__(self, grammar_name="LaTeX"):
        super(LaTeXCompiler, self).__init__()
        assert re.match('\w+\Z', grammar_name)

    def genericenv(self, node):
        return node

    def beginenv(self, node):
        pass

    def endenv(self, node):
        pass

    def name(self, node):
        pass

    def genericcmd(self, node):
        pass

    def command(self, node):
        pass

    def config(self, node):
        pass

    def sequence(self, node):
        pass

    def parblock(self, node):
        pass

    def block(self, node):
        pass

    def partext(self, node):
        pass

    def text(self, node):
        pass

    def cfgtext(self, node):
        pass

    def escaped(self, node):
        pass

    def brackets(self, node):
        pass

    def chunk(self, node):
        pass

    def wspc(self, node):
        pass

    def lf(self, node):
        pass

    def par(self, node):
        pass


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_LaTeX(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    return full_compilation(source, LaTeXScanner,
        LaTeXGrammar(), LaTeX_ASTPipeline, LaTeXCompiler())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result, errors, ast = compile_LaTeX(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
                sys.exit(1)
        else:
            print(result)
    else:
        print("Usage: LaTeX_compiler.py [FILENAME]")
