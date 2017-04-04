

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

import re


from DHParser.syntaxtree import remove_whitespace, no_transformation, replace_by_single_child, \
    is_expendable, remove_children_if, TOKEN_KEYWORD, \
    remove_brackets, partial, flatten, \
    remove_expendables, WHITESPACE_KEYWORD, is_whitespace, \
    remove_tokens, reduce_single_child
from DHParser.parser import mixin_comment, Required, Pop, \
    ZeroOrMore, Token, CompilerBase, \
    Sequence, Retrieve, Lookahead, \
    GrammarBase, Optional, NegativeLookbehind, \
    RegExp, Lookbehind, Capture, \
    NegativeLookahead, Alternative, OneOrMore, \
    Forward, RE



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
    source_hash__ = "4a1025732f79bf6787d1f753cbec7fc3"
    parser_initialization__ = "upon instatiation"
    COMMENT__ = r''
    WSP__ = mixin_comment(whitespace=r'\s*', comment=r'')
    wspL__ = ''
    wspR__ = ''
    text = RE('[^`]+')
    delimiter_sign = RE('`+')
    delimiter = Capture(delimiter_sign, "delimiter")
    codeblock = Sequence(delimiter, ZeroOrMore(Alternative(text, Sequence(NegativeLookahead(Retrieve(delimiter)), delimiter_sign))), Pop(delimiter))
    document = ZeroOrMore(Alternative(text, codeblock))
    root__ = document
    

#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

PopRetrieveTransTable = {
    # AST Transformations for the PopRetrieve-grammar
    "document": no_transformation,
    "codeblock": no_transformation,
    "delimiter": no_transformation,
    "delimiter_sign": no_transformation,
    "text": no_transformation,
    "": no_transformation
}


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
# END OF PYDSL-SECTIONS
#
#######################################################################

