#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

dhparser_parentdir = os.path.abspath(r'../..')
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor


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
    r"""Parser for a XML source file.
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
    source_hash__ = "4cd0cef2b3f3559b014e4d34e5d8b1f6"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'//'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = NegativeLookahead(RegExp('.'))
    S = RegExp('\\s+')
    Char = RegExp('\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]')
    Chars = RegExp('(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF])+')
    CharRef = Alternative(Series(Drop(Token('&#')), RegExp('[0-9]+'), Drop(Token(';'))), Series(Drop(Token('&#x')), RegExp('[0-9a-fA-F]+'), Drop(Token(';'))))
    CommentChars = RegExp('(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    PIChars = RegExp('(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    IgnoreChars = RegExp('(?:(?!(?:<!\\[)|(?:\\]\\]>))(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CData = RegExp('(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CharData = RegExp('(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    CDSect = Series(Drop(Token('<![CDATA[')), CData, Drop(Token(']]>')))
    PITarget = Series(NegativeLookahead(RegExp('X|xM|mL|l')), Name)
    PI = Series(Drop(Token('<?')), PITarget, Option(Series(dwsp__, PIChars)), Drop(Token('?>')))
    Comment = Series(Drop(Token('<!--')), ZeroOrMore(Alternative(CommentChars, RegExp('-(?!-)'))), Drop(Token('-->')))
    Misc = OneOrMore(Alternative(Comment, PI, S))
    NameChars = RegExp('(?x)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n                   |\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF])+')
    NameStartChar = RegExp('(?x)_|:|[A-Z]|[a-z]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF]')
    Name.set(Series(NameStartChar, Option(NameChars)))
    Names = Series(Name, ZeroOrMore(Series(RegExp(' '), Name)))
    Nmtoken = Synonym(NameChars)
    Nmtokens = Series(Nmtoken, ZeroOrMore(Series(RegExp(' '), Nmtoken)))
    PEReference = Series(Drop(Token('%')), Name, Drop(Token(';')))
    EntityRef = Series(Drop(Token('&')), Name, Drop(Token(';')))
    Reference = Alternative(EntityRef, CharRef)
    PubidLiteral = Alternative(Series(Drop(Token('"')), Option(PubidChars), Drop(Token('"'))), Series(Drop(Token("'")), Option(PubidCharsSingleQuoted), Drop(Token("'"))))
    SystemLiteral = Alternative(Series(Drop(Token('"')), RegExp('[^"]*'), Drop(Token('"'))), Series(Drop(Token("'")), RegExp("[^']*"), Drop(Token("'"))))
    AttValue = Alternative(Series(Drop(Token('"')), ZeroOrMore(Alternative(RegExp('[^<&"]+'), Reference)), Drop(Token('"'))), Series(Drop(Token("'")), ZeroOrMore(Alternative(RegExp("[^<&']+"), Reference)), Drop(Token("'"))))
    EntityValue = Alternative(Series(Drop(Token('"')), ZeroOrMore(Alternative(RegExp('[^%&"]+'), PEReference, Reference)), Drop(Token('"'))), Series(Drop(Token("'")), ZeroOrMore(Alternative(RegExp("[^%&']+"), PEReference, Reference)), Drop(Token("'"))))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Attribute = Series(Name, dwsp__, Drop(Token('=')), dwsp__, AttValue, mandatory=2)
    TagName = Capture(Synonym(Name))
    emptyElement = Series(Drop(Token('<')), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Token('/>')))
    ETag = Series(Drop(Token('</')), Pop(TagName), dwsp__, Drop(Token('>')), mandatory=1)
    STag = Series(Drop(Token('<')), TagName, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Token('>')))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    NDataDecl = Series(Drop(Token('NData')), S, Name, mandatory=1)
    PublicID = Series(Drop(Token('PUBLIC')), S, PubidLiteral, mandatory=1)
    ExternalID = Series(Drop(Token('SYSTEM')), S, SystemLiteral, mandatory=1)
    NotationDecl = Series(Drop(Token('<!NOTATION')), S, Name, dwsp__, Alternative(ExternalID, PublicID), dwsp__, Drop(Token('>')), mandatory=1)
    PEDef = Alternative(EntityValue, ExternalID)
    EntityDef = Alternative(EntityValue, Series(ExternalID, Option(NDataDecl)))
    PEDecl = Series(Drop(Token('<!ENTITY')), S, Drop(Token('%')), S, Name, S, PEDef, dwsp__, Drop(Token('>')), mandatory=3)
    GEDecl = Series(Drop(Token('<!ENTITY')), S, Name, S, EntityDef, dwsp__, Drop(Token('>')), mandatory=3)
    EntityDecl = Alternative(GEDecl, PEDecl)
    FIXED = Series(Option(Series(Drop(Token('#FIXED')), S)), AttValue)
    IMPLIED = Token('#IMPLIED')
    REQUIRED = Token('#REQUIRED')
    DefaultDecl = Alternative(REQUIRED, IMPLIED, FIXED)
    Enumeration = Series(Drop(Token('(')), dwsp__, Nmtoken, ZeroOrMore(Series(dwsp__, Drop(Token('|')), dwsp__, Nmtoken)), dwsp__, Drop(Token(')')))
    NotationType = Series(Drop(Token('NOTATION')), S, Drop(Token('(')), dwsp__, Name, ZeroOrMore(Series(dwsp__, Drop(Token('|')), dwsp__, Name)), dwsp__, Drop(Token(')')))
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
    AttDef = Series(Name, dwsp__, AttType, S, DefaultDecl, mandatory=2)
    AttlistDecl = Series(Drop(Token('<!ATTLIST')), S, Name, ZeroOrMore(Series(dwsp__, AttDef)), dwsp__, Drop(Token('>')), mandatory=1)
    seq = Series(Drop(Token('(')), dwsp__, cp, ZeroOrMore(Series(dwsp__, Drop(Token(',')), dwsp__, cp)), dwsp__, Drop(Token(')')))
    cp.set(Series(Alternative(Name, choice, seq), Option(Alternative(Drop(Token('?')), Drop(Token('*')), Drop(Token('+'))))))
    choice.set(Series(Drop(Token('(')), dwsp__, OneOrMore(Series(dwsp__, Drop(Token('|')), dwsp__, cp)), dwsp__, Drop(Token(')'))))
    children = Series(Alternative(choice, seq), Option(Alternative(Drop(Token('?')), Drop(Token('*')), Drop(Token('+')))))
    Mixed = Alternative(Series(Drop(Token('(')), dwsp__, Drop(Token('#PCDATA')), ZeroOrMore(Series(dwsp__, Drop(Token('|')), dwsp__, Name)), dwsp__, Drop(Token(')*'))), Series(Drop(Token('(')), dwsp__, Drop(Token('#PCDATA')), dwsp__, Drop(Token(')'))))
    ANY = Token('ANY')
    EMPTY = Token('EMPTY')
    contentspec = Alternative(EMPTY, ANY, Mixed, children)
    elementdecl = Series(Drop(Token('<!ELEMENT')), S, Name, dwsp__, contentspec, dwsp__, Drop(Token('>')), mandatory=1)
    TextDecl = Series(Drop(Token('<?xml')), Option(VersionInfo), EncodingDecl, dwsp__, Drop(Token('?>')))
    extParsedEnt = Series(Option(TextDecl), content)
    ignoreSectContents.set(Series(IgnoreChars, ZeroOrMore(Series(Drop(Token('<![')), ignoreSectContents, Drop(Token(']]>')), IgnoreChars))))
    ignoreSect = Series(Drop(Token('<![')), dwsp__, Drop(Token('IGNORE')), dwsp__, Drop(Token('[')), ignoreSectContents, Drop(Token(']]>')))
    includeSect = Series(Drop(Token('<![')), dwsp__, Drop(Token('INCLUDE')), dwsp__, Drop(Token('[')), extSubsetDecl, Drop(Token(']]>')))
    conditionalSect = Alternative(includeSect, ignoreSect)
    extSubsetDecl.set(ZeroOrMore(Alternative(markupdecl, conditionalSect, DeclSep)))
    extSubset = Series(Option(TextDecl), extSubsetDecl)
    markupdecl.set(Alternative(elementdecl, AttlistDecl, EntityDecl, NotationDecl, PI, Comment))
    DeclSep.set(Alternative(PEReference, S))
    intSubset = ZeroOrMore(Alternative(markupdecl, DeclSep))
    doctypedecl = Series(Drop(Token('<!DOCTYPE')), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Option(Series(Drop(Token('[')), intSubset, Drop(Token(']')), dwsp__)), Drop(Token('>')))
    No = Token('no')
    Yes = Token('yes')
    SDDecl = Series(dwsp__, Drop(Token('standalone')), dwsp__, Drop(Token('=')), dwsp__, Alternative(Alternative(Series(Drop(Token("'")), Yes), Series(No, Drop(Token("'")))), Alternative(Series(Drop(Token('"')), Yes), Series(No, Drop(Token('"'))))))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl.set(Series(dwsp__, Drop(Token('encoding')), dwsp__, Drop(Token('=')), dwsp__, Alternative(Series(Drop(Token("'")), EncName, Drop(Token("'"))), Series(Drop(Token('"')), EncName, Drop(Token('"'))))))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo.set(Series(dwsp__, Drop(Token('version')), dwsp__, Drop(Token('=')), dwsp__, Alternative(Series(Drop(Token("'")), VersionNum, Drop(Token("'"))), Series(Drop(Token('"')), VersionNum, Drop(Token('"'))))))
    XMLDecl = Series(Drop(Token('<?xml')), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, Drop(Token('?>')))
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    document = Series(prolog, element, Option(Misc), EOF)
    root__ = document
    

def get_grammar() -> XMLGrammar:
    """Returns a thread/process-exclusive XMLGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.XML_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.XML_00000001_grammar_singleton = XMLGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.XML_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.XML_00000001_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

XML_AST_transformation_table = {
    # AST Transformations for the XML-grammar
    "<": [flatten, remove_empty, remove_anonymous_tokens, remove_whitespace, remove_children("S")],
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
    "*": replace_by_single_child
}


def CreateXMLTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=XML_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.XML_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.XML_00000001_transformer_singleton = CreateXMLTransformer()
        transformer = THREAD_LOCALS.XML_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

# def internalize(context):
#     """Sets the node's parser type to the tag name and internalizes
#     XML attr."""
#     node = context[-1]
#     if node.parser.name == 'element':
#         node.parser = MockParser(node['STag']['Name'].content, ':element')
#         node.result = node.result[1:-1]
#     elif node.parser.name == 'emptyElement':
#         node.parser = MockParser(node['Name'].content, ':emptyElement')
#         node.result = node.result[1:]
#     else:
#         assert node.parser.ptype in [':element', ':emptyElement'], \
#             "Tried to internalize tag name and attr for non element component!"
#         return
#     for nd in node.result:
#         if nd.parser.name == 'Attribute':
#             node.attr[nd['Name'].content] = nd['AttValue'].content
#     remove_children(context, {'Attribute'})


class XMLCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a XML source file.
    """

    def __init__(self):
        super(XMLCompiler, self).__init__()
        self.cleanup_whitespace = True  # remove empty CharData from mixed elements

    def reset(self):
        super().reset()
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
            node.attr.update(attributes)
        node.result = ''
        self.tree.empty_tags.add('?xml')
        node.tag_name = '?xml'  # node.parser = self.get_parser('?xml')
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
            node.attr.update(attributes)
            preserve_whitespace |= attributes.get('xml:space', '') == 'preserve'
        node.tag_name = tag_name
        content = tuple(self.compile(nd) for nd in node.get('content', PLACEHOLDER).children)
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
            node.attr.update(attributes)
        node.tag_name = node['Name'].content  # node.parser = self.get_parser(node['Name'].content)
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


def get_compiler() -> XMLCompiler:
    """Returns a thread/process-exclusive XMLCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.XML_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.XML_00000001_compiler_singleton = XMLCompiler()
        compiler = THREAD_LOCALS.XML_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
        elif parser_update:
            print(os.path.basename(__file__) + ' has changed. '
              'Please run again in order to apply updated compiler')
            sys.exit(0)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
            set_config_value('history_tracking', True)
            set_config_value('resume_notices', True)
            set_config_value('log_syntax_trees', set(('cst', 'ast')))
        start_logging(log_dir)
        result, errors, _ = compile_src(file_name)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.serialize() if isinstance(result, Node) else result)
    else:
        print("Usage: XMLParser.py [FILENAME]")
