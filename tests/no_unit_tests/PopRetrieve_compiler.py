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

def PopRetrieveScanner(text):
    return text


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class PopRetrieveGrammar(GrammarBase):
    r"""Parser for a PopRetrieve source file, with this grammar:
    
    document       = { text | codeblock }
    codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
    delimiter      = delimiter_sign
    delimiter_sign = /`+/
    text           = /[^`]+/ 
    """
    source_hash__ = "1312f8befacbc4d03bcc320644f37015"
    parser_initialization__ = "upon instatiation"
    COMMENT__ = r''
    WSP__ = mixin_comment(whitespace=r'[\t ]*', comment=r'')
    wspL__ = ''
    wspR__ = WSP__
    text = RE('[^`]+', wR='')
    delimiter_sign = RE('`+', wR='')
    delimiter = Capture(delimiter_sign, "delimiter")
    codeblock = Sequence(delimiter, ZeroOrMore(Alternative(text, Sequence(NegativeLookahead(Retrieve(delimiter)), delimiter_sign))), Pop(delimiter))
    document = ZeroOrMore(Alternative(text, codeblock))
    root__ = document
    

#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

PopRetrieve_ASTTransform = {
    # AST Transformations for the PopRetrieve-grammar
    "document": no_operation,
    "codeblock": no_operation,
    "delimiter": no_operation,
    "delimiter_sign": no_operation,
    "text": no_operation,
    "": no_operation
}

PopRetrieve_ASTPipeline = [PopRetrieve_ASTTransform]


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class PopRetrieveCompiler(CompilerBase):
    """Compiler for the abstract-syntax-tree of a PopRetrieve source file.
    """

    def __init__(self, grammar_name="PopRetrieve"):
        super(PopRetrieveCompiler, self).__init__()
        assert re.match('\w+\Z', grammar_name)

    def document(self, node):
        return node

    def codeblock(self, node):
        pass

    def delimiter(self, node):
        pass

    def delimiter_sign(self, node):
        pass

    def text(self, node):
        pass


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_PopRetrieve(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    return full_compilation(source, PopRetrieveScanner,
        PopRetrieveGrammar(), PopRetrieve_ASTPipeline, PopRetrieveCompiler())

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result, errors, ast = compile_PopRetrieve(sys.argv[1])
        if errors:
            for error in errors:
                print(error)
                sys.exit(1)
        else:
            print(result)
    else:
        print("Usage: PopRetrieve_compiler.py [FILENAME]")
