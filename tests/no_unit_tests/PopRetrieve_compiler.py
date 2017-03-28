

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from PyDSL import ZeroOrMore, Capture, mixin_comment, OneOrMore, \
    remove_comments, partial, Lookahead, remove_scanner_tokens, \
    Lookbehind, flatten, NegativeLookbehind, remove_enclosing_delimiters, \
    NegativeLookahead, remove_whitespace, is_whitespace, reduce_single_child, \
    RE, is_scanner_token, Retrieve, remove_children_if, \
    Sequence, Token, CompilerBase, is_comment, \
    remove_expendables, remove_tokens, Alternative, is_expendable, \
    Optional, no_transformation, TOKEN_KEYWORD, RegExp, \
    replace_by_single_child, Required, GrammarBase, WHITESPACE_KEYWORD, \
    Forward, Pop



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
    source_hash__ = "50f817c35d08825b20a95664a555d9b0"
    parser_initialization__ = "upon instatiation"
    wsp__ = mixin_comment(whitespace=r'\s*', comment=r'')
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

