def PopRetrieveScanner(text):
    return text


### DON'T EDIT OR REMOVE THIS LINE ###

class PopRetrieveGrammar(ParserCenter):
    r"""Parser for a PopRetrieve source file, with this grammar:
    
    document       = { text | codeblock }
    codeblock      = delimiter { text | (!:delimiter delimiter_sign) } ::delimiter
    delimiter      = delimiter_sign
    delimiter_sign = /`+/
    text           = /[^`]+/ 
    """
    source_hash__ = "525d71c131f2dfeed4edeec81070201c"
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
    

### DON'T EDIT OR REMOVE THIS LINE ###

PopRetrieveTransTable = {
    # AST Transformations for the PopRetrieve-grammar
    "document": no_transformation,
    "codeblock": no_transformation,
    "delimiter": no_transformation,
    "delimiter_sign": no_transformation,
    "text": no_transformation,
    "": no_transformation
}


### DON'T EDIT OR REMOVE THIS LINE ###

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

