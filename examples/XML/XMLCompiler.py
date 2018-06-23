#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from collections import OrderedDict
from functools import partial
import os
import sys


sys.path.append(r'/home/eckhart/Entwicklung/DHParser')

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, RE, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, \
    traverse, remove_children_if, merge_children, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_whitespace, \
    is_empty, is_expendable, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, remove_anonymous_tokens, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, MockParser, \
    ZOMBIE_NODE


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def XMLPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return XMLPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class XMLGrammar(Grammar):
    r"""Parser for a XML source file, with this grammar:
    
    # XML-grammar, see https://www.w3.org/TR/REC-xml/
    
    #######################################################################
    #
    #  EBNF-Directives
    #
    #######################################################################
    
    @ whitespace  = /\s*/           # implicit whitespace, signified by ~
    @ literalws   = none            # literals have no implicit whitespace
    @ comment     = //              # no implicit comments
    @ ignorecase  = False           # literals and regular expressions are case-sensitive
    
    
    #######################################################################
    #
    #  Document Frame and Prolog
    #
    #######################################################################
    
    document        = prolog element [Misc] EOF
    prolog          = [ ~ XMLDecl ] [Misc] [doctypedecl [Misc]]
    XMLDecl         = '<?xml' VersionInfo [EncodingDecl] [SDDecl] ~ '?>'
    
    VersionInfo     = ~ 'version' ~ '=' ~ ("'" VersionNum "'" | '"' VersionNum '"')
    VersionNum      = /[0-9]+\.[0-9]+/
    
    EncodingDecl    = ~ 'encoding' ~ '=' ~ ("'" EncName "'" | '"' EncName '"')
    EncName         = /[A-Za-z][A-Za-z0-9._\-]*/
    
    SDDecl          = ~ 'standalone' ~ '=' ~ (("'" Yes | No "'") | ('"' Yes | No '"'))
    Yes             = 'yes'
    No              = 'no'
    
    
    #######################################################################
    #
    #  Document Type Definition
    #
    #######################################################################
    
    doctypedecl	    = '<!DOCTYPE' ~ Name [~ ExternalID] ~ ['[' intSubset ']' ~] '>'
    intSubset       = { markupdecl | DeclSep }
    DeclSep         = PEReference | S
    markupdecl      = elementdecl | AttlistDecl | EntityDecl | NotationDecl | PI | Comment
    extSubset       = [TextDecl] extSubsetDecl
    extSubsetDecl   = { markupdecl | conditionalSect | DeclSep }
    
    conditionalSect = includeSect | ignoreSect
    includeSect     = '<![' ~ 'INCLUDE' ~ '[' extSubsetDecl ']]>'
    ignoreSect      = '<![' ~ 'IGNORE' ~ '[' ignoreSectContents ']]>'
    ignoreSectContents = IgnoreChars {'<![' ignoreSectContents ']]>' IgnoreChars}
    
    extParsedEnt    = [TextDecl] content
    TextDecl        = '<?xml' [VersionInfo] EncodingDecl ~ '?>'
    
    elementdecl     = '<!ELEMENT' §S Name ~ contentspec ~ '>'
    contentspec     = EMPTY | ANY | Mixed | children
    EMPTY           = 'EMPTY'
    ANY             = 'ANY'
    
    Mixed           = '(' ~ '#PCDATA' { ~ '|' ~ Name } ~ ')*'
                    | '(' ~ '#PCDATA' ~ ')'
    
    children        = (choice | seq) ['?' | '*' | '+']
    choice          = '(' ~ { ~ '|' ~ cp }+ ~ ')'
    cp              = (Name | choice | seq) ['?' | '*' | '+']
    seq             = '(' ~ cp { ~ ',' ~ cp } ~ ')'
    
    AttlistDecl     = '<!ATTLIST' §S Name { ~ AttDef } ~ '>'
    AttDef          = Name ~ §AttType S DefaultDecl
    AttType         = StringType | TokenizedType | EnumeratedType
    StringType      = 'CDATA'
    TokenizedType   = ID | IDREF | IDREFS | ENTITY | ENTITIES | NMTOKEN | NMTOKENS
    ID              = 'ID'
    IDREF           = 'IDREF'
    IDREFS          = 'IDREFS'
    ENTITY          = 'ENTITY'
    ENTITIES        = 'ENTITIES'
    NMTOKEN         = 'NMTOKEN'
    NMTOKENS        = 'NMTOKENS'
    
    EnumeratedType  = NotationType | Enumeration
    NotationType    = 'NOTATION' S '(' ~ Name { ~ '|' ~ Name } ~ ')'
    Enumeration     = '(' ~ Nmtoken { ~ '|' ~ Nmtoken } ~ ')'
    
    DefaultDecl     = REQUIRED | IMPLIED | FIXED
    REQUIRED        = '#REQUIRED'
    IMPLIED         = '#IMPLIED'
    FIXED           = ['#FIXED' S] AttValue
    
    EntityDecl      = GEDecl | PEDecl
    GEDecl          = '<!ENTITY' S Name §S EntityDef ~ '>'
    PEDecl          = '<!ENTITY' S '%' §S Name S PEDef ~ '>'
    EntityDef       = EntityValue | ExternalID [NDataDecl]
    PEDef           = EntityValue | ExternalID
    
    NotationDecl    = '<!NOTATION' §S Name ~ (ExternalID | PublicID) ~ '>'
    
    ExternalID      = 'SYSTEM' §S SystemLiteral
    PublicID        = 'PUBLIC' §S PubidLiteral
    NDataDecl       = 'NData' §S Name
    
    
    #######################################################################
    #
    # Logical Structures
    #
    #######################################################################
    
    element         = emptyElement | STag §content ETag
    STag            = '<' TagName { ~ Attribute } ~ '>'
    ETag            = '</' §::TagName ~ '>'
    
    emptyElement    = '<' Name { ~ Attribute } ~ '/>'
    
    TagName         = Name
    Attribute       = Name ~ §'=' ~ AttValue
    
    content         = [ CharData ]
                      { (element | Reference | CDSect | PI | Comment)
                        [CharData] }
    
    
    #######################################################################
    #
    #  Literals
    #
    #######################################################################
    
    EntityValue     = '"' { /[^%&"]+/ | PEReference | Reference } '"'
    			    | "'" { /[^%&']+/ | PEReference | Reference } "'"
    AttValue        = '"' { /[^<&"]+/ | Reference } '"'
    			    | "'" { /[^<&']+/ | Reference } "'"
    SystemLiteral	= '"' /[^"]*/ '"' | "'" /[^']*/ "'"
    PubidLiteral    = '"' [PubidChars] '"'
                    | "'" [PubidCharsSingleQuoted] "'"
    
    
    #######################################################################
    #
    #  References
    #
    #######################################################################
    
    Reference       = EntityRef | CharRef
    EntityRef       = '&' Name ';'
    PEReference     = '%' Name ';'
    
    
    #######################################################################
    #
    #  Names and Tokens
    #
    #######################################################################
    
    Nmtokens        = Nmtoken { / / Nmtoken }
    Nmtoken         = NameChars
    Names           = Name { / / Name }
    Name            = NameStartChar [NameChars]
    NameStartChar   = /_|:|[A-Z]|[a-z]
                       |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                       |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                       |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                       |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                       |[\U00010000-\U000EFFFF]/
    NameChars       = /(?:_|:|-|\.|[A-Z]|[a-z]|[0-9]
                       |\u00B7|[\u0300-\u036F]|[\u203F-\u2040]
                       |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                       |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                       |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                       |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                       |[\U00010000-\U000EFFFF])+/
    
    
    #######################################################################
    #
    #  Comments, Processing Instructions and CDATA sections
    #
    #######################################################################
    
    Misc            = { Comment | PI | S }+
    Comment         = '<!--' { CommentChars | /-(?!-)/ } '-->'
    PI              = '<?' PITarget [~ PIChars] '?>'
    PITarget        = !/X|xM|mL|l/ Name
    CDSect          = '<![CDATA[' CData ']]>'
    
    
    #######################################################################
    #
    #  Characters, Explicit Whitespace and End of File
    #
    #######################################################################
    
    PubidCharsSingleQuoted = /(?:\x20|\x0D|\x0A|[a-zA-Z0-9]|[-()+,.\/:=?;!*#@$_%])+/
    PubidChars      = /(?:\x20|\x0D|\x0A|[a-zA-Z0-9]|[-'()+,.\/:=?;!*#@$_%])+/
    
    CharData        = /(?:(?!\]\]>)[^<&])+/
    CData           = /(?:(?!\]\]>)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+/
    
    IgnoreChars     = /(?:(?!(?:<!\[)|(?:\]\]>))(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+/
    PIChars         = /(?:(?!\?>)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+/
    CommentChars    = /(?:(?!-)(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]))+/
    CharRef         = ('&#' /[0-9]+/ ';') | ('&#x' /[0-9a-fA-F]+/ ';')
    Chars           = /(?:\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF])+/
    Char            = /\x09|\x0A|\x0D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]/
    S               = /\s+/         # whitespace
    EOF             = !/./          # no more characters ahead, end of file reached
    """
    DeclSep = Forward()
    EncodingDecl = Forward()
    Name = Forward()
    VersionInfo = Forward()
    choice = Forward()
    cp = Forward()
    element = Forward()
    extSubsetDecl = Forward()
    ignoreSectContents = Forward()
    markupdecl = Forward()
    source_hash__ = "5250afe0292b9826a47edc20a203d6c9"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r''
    WHITESPACE__ = r'\s*'
    WSP__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wspL__ = ''
    wspR__ = ''
    whitespace__ = Whitespace(WSP__)
    EOF = NegativeLookahead(RegExp('.'))
    S = RegExp('\\s+')
    Char = RegExp('\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]')
    Chars = RegExp('(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF])+')
    CharRef = Alternative(Series(Token('&#'), RegExp('[0-9]+'), Token(';')), Series(Token('&#x'), RegExp('[0-9a-fA-F]+'), Token(';')))
    CommentChars = RegExp('(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    PIChars = RegExp('(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    IgnoreChars = RegExp('(?:(?!(?:<!\\[)|(?:\\]\\]>))(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CData = RegExp('(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CharData = RegExp('(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    CDSect = Series(Token('<![CDATA['), CData, Token(']]>'))
    PITarget = Series(NegativeLookahead(RegExp('X|xM|mL|l')), Name)
    PI = Series(Token('<?'), PITarget, Option(Series(whitespace__, PIChars)), Token('?>'))
    Comment = Series(Token('<!--'), ZeroOrMore(Alternative(CommentChars, RegExp('-(?!-)'))), Token('-->'))
    Misc = OneOrMore(Alternative(Comment, PI, S))
    NameChars = RegExp('(?x)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n                   |\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF])+')
    NameStartChar = RegExp('(?x)_|:|[A-Z]|[a-z]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF]')
    Name.set(Series(NameStartChar, Option(NameChars)))
    Names = Series(Name, ZeroOrMore(Series(RegExp(' '), Name)))
    Nmtoken = Synonym(NameChars)
    Nmtokens = Series(Nmtoken, ZeroOrMore(Series(RegExp(' '), Nmtoken)))
    PEReference = Series(Token('%'), Name, Token(';'))
    EntityRef = Series(Token('&'), Name, Token(';'))
    Reference = Alternative(EntityRef, CharRef)
    PubidLiteral = Alternative(Series(Token('"'), Option(PubidChars), Token('"')), Series(Token("'"), Option(PubidCharsSingleQuoted), Token("'")))
    SystemLiteral = Alternative(Series(Token('"'), RegExp('[^"]*'), Token('"')), Series(Token("'"), RegExp("[^']*"), Token("'")))
    AttValue = Alternative(Series(Token('"'), ZeroOrMore(Alternative(RegExp('[^<&"]+'), Reference)), Token('"')), Series(Token("'"), ZeroOrMore(Alternative(RegExp("[^<&']+"), Reference)), Token("'")))
    EntityValue = Alternative(Series(Token('"'), ZeroOrMore(Alternative(RegExp('[^%&"]+'), PEReference, Reference)), Token('"')), Series(Token("'"), ZeroOrMore(Alternative(RegExp("[^%&']+"), PEReference, Reference)), Token("'")))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Attribute = Series(Name, whitespace__, Token('='), whitespace__, AttValue, mandatory=2)
    TagName = Capture(Name)
    emptyElement = Series(Token('<'), Name, ZeroOrMore(Series(whitespace__, Attribute)), whitespace__, Token('/>'))
    ETag = Series(Token('</'), Pop(TagName), whitespace__, Token('>'), mandatory=1)
    STag = Series(Token('<'), TagName, ZeroOrMore(Series(whitespace__, Attribute)), whitespace__, Token('>'))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    NDataDecl = Series(Token('NData'), S, Name, mandatory=1)
    PublicID = Series(Token('PUBLIC'), S, PubidLiteral, mandatory=1)
    ExternalID = Series(Token('SYSTEM'), S, SystemLiteral, mandatory=1)
    NotationDecl = Series(Token('<!NOTATION'), S, Name, whitespace__, Alternative(ExternalID, PublicID), whitespace__, Token('>'), mandatory=1)
    PEDef = Alternative(EntityValue, ExternalID)
    EntityDef = Alternative(EntityValue, Series(ExternalID, Option(NDataDecl)))
    PEDecl = Series(Token('<!ENTITY'), S, Token('%'), S, Name, S, PEDef, whitespace__, Token('>'), mandatory=3)
    GEDecl = Series(Token('<!ENTITY'), S, Name, S, EntityDef, whitespace__, Token('>'), mandatory=3)
    EntityDecl = Alternative(GEDecl, PEDecl)
    FIXED = Series(Option(Series(Token('#FIXED'), S)), AttValue)
    IMPLIED = Token('#IMPLIED')
    REQUIRED = Token('#REQUIRED')
    DefaultDecl = Alternative(REQUIRED, IMPLIED, FIXED)
    Enumeration = Series(Token('('), whitespace__, Nmtoken, ZeroOrMore(Series(whitespace__, Token('|'), whitespace__, Nmtoken)), whitespace__, Token(')'))
    NotationType = Series(Token('NOTATION'), S, Token('('), whitespace__, Name, ZeroOrMore(Series(whitespace__, Token('|'), whitespace__, Name)), whitespace__, Token(')'))
    EnumeratedType = Alternative(NotationType, Enumeration)
    NMTOKENS = Token('NMTOKENS')
    NMTOKEN = Token('NMTOKEN')
    ENTITIES = Token('ENTITIES')
    ENTITY = Token('ENTITY')
    IDREFS = Token('IDREFS')
    IDREF = Token('IDREF')
    ID = Token('ID')
    TokenizedType = Alternative(ID, IDREF, IDREFS, ENTITY, ENTITIES, NMTOKEN, NMTOKENS)
    StringType = Token('CDATA')
    AttType = Alternative(StringType, TokenizedType, EnumeratedType)
    AttDef = Series(Name, whitespace__, AttType, S, DefaultDecl, mandatory=2)
    AttlistDecl = Series(Token('<!ATTLIST'), S, Name, ZeroOrMore(Series(whitespace__, AttDef)), whitespace__, Token('>'), mandatory=1)
    seq = Series(Token('('), whitespace__, cp, ZeroOrMore(Series(whitespace__, Token(','), whitespace__, cp)), whitespace__, Token(')'))
    cp.set(Series(Alternative(Name, choice, seq), Option(Alternative(Token('?'), Token('*'), Token('+')))))
    choice.set(Series(Token('('), whitespace__, OneOrMore(Series(whitespace__, Token('|'), whitespace__, cp)), whitespace__, Token(')')))
    children = Series(Alternative(choice, seq), Option(Alternative(Token('?'), Token('*'), Token('+'))))
    Mixed = Alternative(Series(Token('('), whitespace__, Token('#PCDATA'), ZeroOrMore(Series(whitespace__, Token('|'), whitespace__, Name)), whitespace__, Token(')*')), Series(Token('('), whitespace__, Token('#PCDATA'), whitespace__, Token(')')))
    ANY = Token('ANY')
    EMPTY = Token('EMPTY')
    contentspec = Alternative(EMPTY, ANY, Mixed, children)
    elementdecl = Series(Token('<!ELEMENT'), S, Name, whitespace__, contentspec, whitespace__, Token('>'), mandatory=1)
    TextDecl = Series(Token('<?xml'), Option(VersionInfo), EncodingDecl, whitespace__, Token('?>'))
    extParsedEnt = Series(Option(TextDecl), content)
    ignoreSectContents.set(Series(IgnoreChars, ZeroOrMore(Series(Token('<!['), ignoreSectContents, Token(']]>'), IgnoreChars))))
    ignoreSect = Series(Token('<!['), whitespace__, Token('IGNORE'), whitespace__, Token('['), ignoreSectContents, Token(']]>'))
    includeSect = Series(Token('<!['), whitespace__, Token('INCLUDE'), whitespace__, Token('['), extSubsetDecl, Token(']]>'))
    conditionalSect = Alternative(includeSect, ignoreSect)
    extSubsetDecl.set(ZeroOrMore(Alternative(markupdecl, conditionalSect, DeclSep)))
    extSubset = Series(Option(TextDecl), extSubsetDecl)
    markupdecl.set(Alternative(elementdecl, AttlistDecl, EntityDecl, NotationDecl, PI, Comment))
    DeclSep.set(Alternative(PEReference, S))
    intSubset = ZeroOrMore(Alternative(markupdecl, DeclSep))
    doctypedecl = Series(Token('<!DOCTYPE'), whitespace__, Name, Option(Series(whitespace__, ExternalID)), whitespace__, Option(Series(Token('['), intSubset, Token(']'), whitespace__)), Token('>'))
    No = Token('no')
    Yes = Token('yes')
    SDDecl = Series(whitespace__, Token('standalone'), whitespace__, Token('='), whitespace__, Alternative(Alternative(Series(Token("'"), Yes), Series(No, Token("'"))), Alternative(Series(Token('"'), Yes), Series(No, Token('"')))))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl.set(Series(whitespace__, Token('encoding'), whitespace__, Token('='), whitespace__, Alternative(Series(Token("'"), EncName, Token("'")), Series(Token('"'), EncName, Token('"')))))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo.set(Series(whitespace__, Token('version'), whitespace__, Token('='), whitespace__, Alternative(Series(Token("'"), VersionNum, Token("'")), Series(Token('"'), VersionNum, Token('"')))))
    XMLDecl = Series(Token('<?xml'), VersionInfo, Option(EncodingDecl), Option(SDDecl), whitespace__, Token('?>'))
    prolog = Series(Option(Series(whitespace__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    document = Series(prolog, element, Option(Misc), EOF)
    root__ = document
    
def get_grammar() -> XMLGrammar:
    global thread_local_XML_grammar_singleton
    try:
        grammar = thread_local_XML_grammar_singleton
    except NameError:
        thread_local_XML_grammar_singleton = XMLGrammar()
        grammar = thread_local_XML_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

XML_AST_transformation_table = {
    # AST Transformations for the XML-grammar
    "+": [remove_empty, remove_anonymous_tokens, remove_whitespace, remove_nodes("S")],
    "document": [],
    "prolog": [],
    "XMLDecl": [],
    "VersionInfo": [reduce_single_child],
    "VersionNum": [],
    "EncodingDecl": [reduce_single_child],
    "EncName": [],
    "SDDecl": [],
    "Yes": [],
    "No": [],
    "doctypedecl": [],
    "intSubset": [],
    "DeclSep": [replace_or_reduce],
    "markupdecl": [replace_or_reduce],
    "extSubset": [],
    "extSubsetDecl": [],
    "conditionalSect": [replace_or_reduce],
    "includeSect": [],
    "ignoreSect": [],
    "ignoreSectContents": [],
    "extParsedEnt": [],
    "TextDecl": [],
    "elementdecl": [],
    "contentspec": [replace_or_reduce],
    "EMPTY": [],
    "ANY": [],
    "Mixed": [replace_or_reduce],
    "children": [],
    "choice": [],
    "cp": [],
    "seq": [],
    "AttlistDecl": [],
    "AttDef": [],
    "AttType": [replace_or_reduce],
    "StringType": [],
    "TokenizedType": [replace_or_reduce],
    "ID": [],
    "IDREF": [],
    "IDREFS": [],
    "ENTITY": [],
    "ENTITIES": [],
    "NMTOKEN": [],
    "NMTOKENS": [],
    "EnumeratedType": [replace_or_reduce],
    "NotationType": [],
    "Enumeration": [],
    "DefaultDecl": [replace_or_reduce],
    "REQUIRED": [],
    "IMPLIED": [],
    "FIXED": [],
    "EntityDecl": [replace_or_reduce],
    "GEDecl": [],
    "PEDecl": [],
    "EntityDef": [replace_or_reduce],
    "PEDef": [replace_or_reduce],
    "NotationDecl": [],
    "ExternalID": [],
    "PublicID": [],
    "NDataDecl": [],
    "element": [replace_or_reduce],
    "STag": [],
    "ETag": [reduce_single_child],
    "EmptyElemTag": [],
    "TagName": [replace_by_single_child],
    "Attribute": [],
    "content": [flatten],
    "EntityValue": [replace_or_reduce],
    "AttValue": [replace_or_reduce],
    "SystemLiteral": [replace_or_reduce],
    "PubidLiteral": [replace_or_reduce],
    "Reference": [replace_or_reduce],
    "EntityRef": [],
    "PEReference": [],
    "Nmtokens": [],
    "Nmtoken": [reduce_single_child],
    "Names": [],
    "Name": [collapse],
    "NameStartChar": [],
    "NameChars": [],
    "Misc": [],
    "Comment": [],
    "PI": [],
    "PITarget": [reduce_single_child],
    "CDSect": [],
    "PubidCharsSingleQuoted": [],
    "PubidChars": [],
    "CharData": [],
    "CData": [],
    "IgnoreChars": [],
    "PIChars": [],
    "CommentChars": [],
    "CharRef": [replace_or_reduce],
    "Chars": [],
    "Char": [],
    "S": [],
    "EOF": [],
    ":Token, :RE": reduce_single_child,
    "*": replace_by_single_child
}


def XMLTransform() -> TransformationDict:
    return partial(traverse, processing_table=XML_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    global thread_local_XML_transformer_singleton
    try:
        transformer = thread_local_XML_transformer_singleton
    except NameError:
        thread_local_XML_transformer_singleton = XMLTransform()
        transformer = thread_local_XML_transformer_singleton
    return transformer


#######################################################################
#
# Tag conversion
#
#######################################################################


XML_AST_transformation_table = {
    # AST Transformations for the XML-grammar
    "+": [remove_empty, remove_anonymous_tokens, remove_whitespace, remove_nodes("S")],
    "document": [flatten(lambda context: context[-1].tag_name == 'prolog', recursive=False)],
    "prolog": [],
    "XMLDecl": [],
    "VersionInfo": [reduce_single_child],
    "VersionNum": [],
    "EncodingDecl": [reduce_single_child],
    "EncName": [],
    "SDDecl": [],
    "Yes": [],
    "No": [],
    "doctypedecl": [],
    "intSubset": [],
    "DeclSep": [replace_or_reduce],
    "markupdecl": [replace_or_reduce],
    "extSubset": [],
    "extSubsetDecl": [],
    "conditionalSect": [replace_or_reduce],
    "includeSect": [],
    "ignoreSect": [],
    "ignoreSectContents": [],
    "extParsedEnt": [],
    "TextDecl": [],
    "elementdecl": [],
    "contentspec": [replace_or_reduce],
    "EMPTY": [],
    "ANY": [],
    "Mixed": [replace_or_reduce],
    "children": [],
    "choice": [],
    "cp": [],
    "seq": [],
    "AttlistDecl": [],
    "AttDef": [],
    "AttType": [replace_or_reduce],
    "StringType": [],
    "TokenizedType": [replace_or_reduce],
    "ID": [],
    "IDREF": [],
    "IDREFS": [],
    "ENTITY": [],
    "ENTITIES": [],
    "NMTOKEN": [],
    "NMTOKENS": [],
    "EnumeratedType": [replace_or_reduce],
    "NotationType": [],
    "Enumeration": [],
    "DefaultDecl": [replace_or_reduce],
    "REQUIRED": [],
    "IMPLIED": [],
    "FIXED": [],
    "EntityDecl": [replace_or_reduce],
    "GEDecl": [],
    "PEDecl": [],
    "EntityDef": [replace_or_reduce],
    "PEDef": [replace_or_reduce],
    "NotationDecl": [],
    "ExternalID": [],
    "PublicID": [],
    "NDataDecl": [],
    "element": [flatten, replace_by_single_child],
    "STag": [],
    "ETag": [reduce_single_child],
    "emptyElement": [],
    "TagName": [replace_by_single_child],
    "Attribute": [],
    "content": [flatten],
    "EntityValue": [replace_or_reduce],
    "AttValue": [replace_or_reduce],
    "SystemLiteral": [replace_or_reduce],
    "PubidLiteral": [replace_or_reduce],
    "Reference": [replace_or_reduce],
    "EntityRef": [],
    "PEReference": [],
    "Nmtokens": [],
    "Nmtoken": [reduce_single_child],
    "Names": [],
    "Name": [collapse],
    "NameStartChar": [],
    "NameChars": [],
    "Misc": [],
    "Comment": [],
    "PI": [],
    "PITarget": [reduce_single_child],
    "CDSect": [],
    "PubidCharsSingleQuoted": [],
    "PubidChars": [],
    "CharData": [],
    "CData": [],
    "IgnoreChars": [],
    "PIChars": [],
    "CommentChars": [],
    "CharRef": [replace_or_reduce],
    "Chars": [],
    "Char": [],
    "S": [],
    "EOF": [],
    ":Token, :RE": reduce_single_child,
    "*": replace_by_single_child
}


def XMLTransform() -> TransformationDict:
    return partial(traverse, processing_table=XML_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    global thread_local_XML_transformer_singleton
    try:
        transformer = thread_local_XML_transformer_singleton
    except NameError:
        thread_local_XML_transformer_singleton = XMLTransform()
        transformer = thread_local_XML_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

# def internalize(context):
#     """Sets the node's parser type to the tag name and internalizes
#     XML attributes."""
#     node = context[-1]
#     if node.parser.name == 'element':
#         node.parser = MockParser(node['STag']['Name'].content, ':element')
#         node.result = node.result[1:-1]
#     elif node.parser.name == 'emptyElement':
#         node.parser = MockParser(node['Name'].content, ':emptyElement')
#         node.result = node.result[1:]
#     else:
#         assert node.parser.ptype in [':element', ':emptyElement'], \
#             "Tried to internalize tag name and attributes for non element component!"
#         return
#     for nd in node.result:
#         if nd.parser.name == 'Attribute':
#             node.attributes[nd['Name'].content] = nd['AttValue'].content
#     remove_nodes(context, {'Attribute'})


class XMLCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a XML source file.
    """

    def __init__(self, grammar_name="XML", grammar_source=""):
        super(XMLCompiler, self).__init__(grammar_name, grammar_source)
        assert re.match('\w+\Z', grammar_name)
        self.cleanup_whitespace = True  # remove empty CharData from mixed elements

    def _reset(self):
        super()._reset()
        self.mock_parsers = dict()

    def extract_attributes(self, node_sequence):
        attributes = OrderedDict()
        for node in node_sequence:
            if node.tag_name == "Attribute":
                assert node[0].tag_name == "Name", node.as_sexpr()
                assert node[1].tag_name == "AttValue", node.as_sxpr()
                attributes[node[0].content] = node[1].content
        return attributes

    def get_parser(self, tag_name):
        """Returns a mock parser with the given tag_name as parser name."""
        return self.mock_parsers.setdefault(tag_name, MockParser(tag_name))

    def validity_constraint(self, node, condition, err_msg):
        """If `condition` is False an error is issued."""
        if not condition:
            self.tree.add_error(node, err_msg)

    def value_constraint(self, node, value, allowed):
        """If value is not in allowed, an error is issued."""
        self.constraint(node, value in allowed,
            'Invalid value "%s" for "standalone"! Must be one of %s.' % (value, str(allowed)))

    def on_document(self, node):
        self.tree.omit_tags.update({'CharData', 'document'})
        # TODO: Remove the following line. It is specific for testing with example.xml!
        self.tree.inline_tags.update({'to', 'from', 'heading', 'body', 'remark'})
        return self.fallback_compiler(node)

    # def on_prolog(self, node):
    #     return node

    def on_XMLDecl(self, node):
        attributes = dict()
        for child in node.children:
            s = child.content
            if child.tag_name == "VersionInfo":
                attributes['version'] = s
            elif child.tag_name == "EncodingDecl":
                attributes['encoding'] = s
            elif child.tag_name == "SDDecl":
                attributes['standalone'] = s
                self.value_constraint(node, s, {'yes', 'no'})
        if attributes:
            node.attributes.update(attributes)
        node.result = ''
        self.tree.empty_tags.add('?xml')
        node.parser = self.get_parser('?xml')
        return node

    # def on_VersionInfo(self, node):
    #     return node

    # def on_VersionNum(self, node):
    #     return node

    # def on_EncodingDecl(self, node):
    #     return node

    # def on_EncName(self, node):
    #     return node

    # def on_SDDecl(self, node):
    #     return node

    # def on_Yes(self, node):
    #     return node

    # def on_No(self, node):
    #     return node

    # def on_doctypedecl(self, node):
    #     return node

    # def on_intSubset(self, node):
    #     return node

    # def on_DeclSep(self, node):
    #     return node

    # def on_markupdecl(self, node):
    #     return node

    # def on_extSubset(self, node):
    #     return node

    # def on_extSubsetDecl(self, node):
    #     return node

    # def on_conditionalSect(self, node):
    #     return node

    # def on_includeSect(self, node):
    #     return node

    # def on_ignoreSect(self, node):
    #     return node

    # def on_ignoreSectContents(self, node):
    #     return node

    # def on_extParsedEnt(self, node):
    #     return node

    # def on_TextDecl(self, node):
    #     return node

    # def on_elementdecl(self, node):
    #     return node

    # def on_contentspec(self, node):
    #     return node

    # def on_EMPTY(self, node):
    #     return node

    # def on_ANY(self, node):
    #     return node

    # def on_Mixed(self, node):
    #     return node

    # def on_children(self, node):
    #     return node

    # def on_choice(self, node):
    #     return node

    # def on_cp(self, node):
    #     return node

    # def on_seq(self, node):
    #     return node

    # def on_AttlistDecl(self, node):
    #     return node

    # def on_AttDef(self, node):
    #     return node

    # def on_AttType(self, node):
    #     return node

    # def on_StringType(self, node):
    #     return node

    # def on_TokenizedType(self, node):
    #     return node

    # def on_ID(self, node):
    #     return node

    # def on_IDREF(self, node):
    #     return node

    # def on_IDREFS(self, node):
    #     return node

    # def on_ENTITY(self, node):
    #     return node

    # def on_ENTITIES(self, node):
    #     return node

    # def on_NMTOKEN(self, node):
    #     return node

    # def on_NMTOKENS(self, node):
    #     return node

    # def on_EnumeratedType(self, node):
    #     return node

    # def on_NotationType(self, node):
    #     return node

    # def on_Enumeration(self, node):
    #     return node

    # def on_DefaultDecl(self, node):
    #     return node

    # def on_REQUIRED(self, node):
    #     return node

    # def on_IMPLIED(self, node):
    #     return node

    # def on_FIXED(self, node):
    #     return node

    # def on_EntityDecl(self, node):
    #     return node

    # def on_GEDecl(self, node):
    #     return node

    # def on_PEDecl(self, node):
    #     return node

    # def on_EntityDef(self, node):
    #     return node

    # def on_PEDef(self, node):
    #     return node

    # def on_NotationDecl(self, node):
    #     return node

    # def on_ExternalID(self, node):
    #     return node

    # def on_PublicID(self, node):
    #     return node

    # def on_NDataDecl(self, node):
    #     return node

    def on_element(self, node):
        stag = node['STag']
        tag_name = stag['Name'].content
        attributes = self.extract_attributes(stag.children)
        preserve_whitespace = tag_name in self.tree.inline_tags
        if attributes:
            node.attributes.update(attributes)
            preserve_whitespace |= attributes.get('xml:space', '') == 'preserve'
        node.parser = self.get_parser(tag_name)
        content = self.compile_children(node.get('content', ZOMBIE_NODE))
        if len(content) == 1:
            if content[0].tag_name == "CharData":
                # reduce single CharData children
                content = content[0].content
        elif self.cleanup_whitespace and not preserve_whitespace:
            # remove CharData that consists only of whitespace from mixed elements
            content = tuple(child for child in content
                            if child.tag_name != "CharData" or child.content.strip() != '')
        node.result = content
        return node

    # def on_STag(self, node):
    #     return node

    # def on_ETag(self, node):
    #     return node

    def on_emptyElement(self, node):
        attributes = self.extract_attributes(node.children)
        if attributes:
            node.attributes.update(attributes)
        node.parser = self.get_parser(node['Name'].content)
        node.result = ''
        self.tree.empty_tags.add(node.tag_name)
        return node

    # def on_TagName(self, node):
    #     return node

    # def on_Attribute(self, node):
    #     return node

    # def on_content(self, node):
    #     return node

    # def on_EntityValue(self, node):
    #     return node

    # def on_AttValue(self, node):
    #     return node

    # def on_SystemLiteral(self, node):
    #     return node

    # def on_PubidLiteral(self, node):
    #     return node

    # def on_Reference(self, node):
    #     return node

    # def on_EntityRef(self, node):
    #     return node

    # def on_PEReference(self, node):
    #     return node

    # def on_Nmtokens(self, node):
    #     return node

    # def on_Nmtoken(self, node):
    #     return node

    # def on_Names(self, node):
    #     return node

    # def on_Name(self, node):
    #     return node

    # def on_NameStartChar(self, node):
    #     return node

    # def on_NameChars(self, node):
    #     return node

    # def on_Misc(self, node):
    #     return node

    # def on_Comment(self, node):
    #     return node

    # def on_PI(self, node):
    #     return node

    # def on_PITarget(self, node):
    #     return node

    # def on_CDSect(self, node):
    #     return node

    # def on_PubidCharsSingleQuoted(self, node):
    #     return node

    # def on_PubidChars(self, node):
    #     return node

    # def on_CharData(self, node):
    #     return node

    # def on_CData(self, node):
    #     return node

    # def on_IgnoreChars(self, node):
    #     return node

    # def on_PIChars(self, node):
    #     return node

    # def on_CommentChars(self, node):
    #     return node

    # def on_CharRef(self, node):
    #     return node

    # def on_Chars(self, node):
    #     return node

    # def on_Char(self, node):
    #     return node

    # def on_S(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler(grammar_name="XML", grammar_source="") -> XMLCompiler:
    global thread_local_XML_compiler_singleton
    try:
        compiler = thread_local_XML_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except NameError:
        thread_local_XML_compiler_singleton = \
            XMLCompiler(grammar_name, grammar_source)
        compiler = thread_local_XML_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    with logging(log_dir):
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
        try:
            grammar_file_name = os.path.basename(__file__).replace('Compiler.py', '.ebnf')
            if grammar_changed(XMLGrammar, grammar_file_name):
                print("Grammar has changed. Please recompile Grammar first.")
                sys.exit(1)
        except FileNotFoundError:
            print('Could not check for changed grammar, because grammar file "%s" was not found!'
                  % grammar_file_name)    
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        result, errors, ast = compile_src(file_name, log_dir)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_sxpr(compact=True))
            print(result.customized_XML() if isinstance(result, Node) else result)
    else:
        print("Usage: XMLCompiler.py [FILENAME]")
