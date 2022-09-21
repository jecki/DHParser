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

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'../..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, AnyChar, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformerCallable, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, PLACEHOLDER, \
    merge_adjacent, collapse, collapse_children_if, transform_result, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, any_of, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def XMLPreprocessor(text, source_name):
    return None, text, lambda i: i, []


def get_preprocessor() -> PreprocessorFunc:
    return XMLPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class XML_DTDGrammar(Grammar):
    r"""Parser for a XML_DTD source file.
    """
    choice = Forward()
    cp = Forward()
    element = Forward()
    extSubsetDecl = Forward()
    ignoreSectContents = Forward()
    source_hash__ = "b5dd82adc12c32aefc3629d644a5f0f3"
    disposable__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = NegativeLookahead(RegExp('.'))
    S = RegExp('\\s+')
    Char = RegExp('\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]')
    Chars = RegExp('(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF])+')
    CharRef = Alternative(Series(Drop(Text('&#')), RegExp('[0-9]+'), Drop(Text(';'))), Series(Drop(Text('&#x')), RegExp('[0-9a-fA-F]+'), Drop(Text(';'))))
    CommentChars = RegExp('(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    PIChars = RegExp('(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    IgnoreChars = RegExp('(?:(?!(?:<!\\[)|(?:\\]\\]>))(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CData = RegExp('(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CharData = RegExp('(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    CDSect = Series(Drop(Text('<![CDATA[')), CData, Drop(Text(']]>')))
    NameStartChar = RegExp('(?x)_|:|[A-Z]|[a-z]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF]')
    NameChars = RegExp('(?x)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n                   |\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF])+')
    Comment = Series(Drop(Text('<!--')), ZeroOrMore(Alternative(CommentChars, RegExp('-(?!-)'))), Drop(Text('-->')))
    Name = Series(NameStartChar, Option(NameChars))
    PITarget = Series(NegativeLookahead(RegExp('X|xM|mL|l')), Name)
    PI = Series(Drop(Text('<?')), PITarget, Option(Series(dwsp__, PIChars)), Drop(Text('?>')))
    Misc = OneOrMore(Alternative(Comment, PI, S))
    Names = Series(Name, ZeroOrMore(Series(RegExp(' '), Name)))
    Nmtoken = Synonym(NameChars)
    Nmtokens = Series(Nmtoken, ZeroOrMore(Series(RegExp(' '), Nmtoken)))
    PEReference = Series(Drop(Text('%')), Name, Drop(Text(';')))
    EntityRef = Series(Drop(Text('&')), Name, Drop(Text(';')))
    Reference = Alternative(EntityRef, CharRef)
    PubidLiteral = Alternative(Series(Drop(Text('"')), Option(PubidChars), Drop(Text('"'))), Series(Drop(Text("\'")), Option(PubidCharsSingleQuoted), Drop(Text("\'"))))
    SystemLiteral = Alternative(Series(Drop(Text('"')), RegExp('[^"]*'), Drop(Text('"'))), Series(Drop(Text("\'")), RegExp("[^']*"), Drop(Text("\'"))))
    AttValue = Alternative(Series(Drop(Text('"')), ZeroOrMore(Alternative(RegExp('[^<&"]+'), Reference)), Drop(Text('"'))), Series(Drop(Text("\'")), ZeroOrMore(Alternative(RegExp("[^<&']+"), Reference)), Drop(Text("\'"))))
    EntityValue = Alternative(Series(Drop(Text('"')), ZeroOrMore(Alternative(RegExp('[^%&"]+'), PEReference, Reference)), Drop(Text('"'))), Series(Drop(Text("\'")), ZeroOrMore(Alternative(RegExp("[^%&']+"), PEReference, Reference)), Drop(Text("\'"))))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Attribute = Series(Name, dwsp__, Drop(Text('=')), dwsp__, AttValue, mandatory=2)
    TagName = Capture(Synonym(Name), zero_length_warning=True)
    emptyElement = Series(Drop(Text('<')), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Text('/>')))
    ETag = Series(Drop(Text('</')), Pop(TagName), dwsp__, Drop(Text('>')), mandatory=1)
    STag = Series(Drop(Text('<')), TagName, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Text('>')))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    NDataDecl = Series(Drop(Text('NData')), S, Name, mandatory=1)
    PublicID = Series(Drop(Text('PUBLIC')), S, PubidLiteral, mandatory=1)
    ExternalID = Alternative(Series(Drop(Text('SYSTEM')), S, SystemLiteral, mandatory=1), Series(Drop(Text('PUBLIC')), S, PubidLiteral, S, SystemLiteral, mandatory=1))
    NotationDecl = Series(Drop(Text('<!NOTATION')), S, Name, dwsp__, Alternative(ExternalID, PublicID), dwsp__, Drop(Text('>')), mandatory=1)
    PEDef = Alternative(EntityValue, ExternalID)
    EntityDef = Alternative(EntityValue, Series(ExternalID, Option(NDataDecl)))
    PEDecl = Series(Drop(Text('<!ENTITY')), S, Drop(Text('%')), S, Name, S, PEDef, dwsp__, Drop(Text('>')), mandatory=3)
    GEDecl = Series(Drop(Text('<!ENTITY')), S, Name, S, EntityDef, dwsp__, Drop(Text('>')), mandatory=3)
    EntityDecl = Alternative(GEDecl, PEDecl)
    FIXED = Series(Option(Series(Drop(Text('#FIXED')), S)), AttValue)
    IMPLIED = Text('#IMPLIED')
    REQUIRED = Text('#REQUIRED')
    DefaultDecl = Alternative(REQUIRED, IMPLIED, FIXED)
    Enumeration = Series(Drop(Text('(')), dwsp__, Nmtoken, ZeroOrMore(Series(dwsp__, Drop(Text('|')), dwsp__, Nmtoken)), dwsp__, Drop(Text(')')))
    NotationType = Series(Drop(Text('NOTATION')), S, Drop(Text('(')), dwsp__, Name, ZeroOrMore(Series(dwsp__, Drop(Text('|')), dwsp__, Name)), dwsp__, Drop(Text(')')))
    EnumeratedType = Alternative(NotationType, Enumeration)
    NMTOKENS = Text('NMTOKENS')
    NMTOKEN = Text('NMTOKEN')
    ENTITIES = Text('ENTITIES')
    ENTITY = Text('ENTITY')
    IDREFS = Text('IDREFS')
    IDREF = Text('IDREF')
    ID = Text('ID')
    TokenizedType = Alternative(IDREFS, IDREF, ID, ENTITY, ENTITIES, NMTOKENS, NMTOKEN)
    StringType = Text('CDATA')
    AttType = Alternative(StringType, TokenizedType, EnumeratedType)
    AttDef = Series(Name, dwsp__, AttType, S, DefaultDecl, mandatory=2)
    AttlistDecl = Series(Drop(Text('<!ATTLIST')), S, Name, ZeroOrMore(Series(dwsp__, AttDef)), dwsp__, Drop(Text('>')), mandatory=1)
    seq = Series(Drop(Text('(')), dwsp__, cp, ZeroOrMore(Series(dwsp__, Drop(Text(',')), dwsp__, cp)), dwsp__, Drop(Text(')')))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo = Series(dwsp__, Drop(Text('version')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), VersionNum, Drop(Text("\'"))), Series(Drop(Text('"')), VersionNum, Drop(Text('"')))))
    children = Series(Alternative(choice, seq), Option(Alternative(Drop(Text('?')), Drop(Text('*')), Drop(Text('+')))))
    Mixed = Alternative(Series(Drop(Text('(')), dwsp__, Drop(Text('#PCDATA')), ZeroOrMore(Series(dwsp__, Drop(Text('|')), dwsp__, Name)), dwsp__, Drop(Text(')*'))), Series(Drop(Text('(')), dwsp__, Drop(Text('#PCDATA')), dwsp__, Drop(Text(')'))))
    ANY = Text('ANY')
    EMPTY = Text('EMPTY')
    contentspec = Alternative(EMPTY, ANY, Mixed, children)
    elementdecl = Series(Drop(Text('<!ELEMENT')), S, Name, dwsp__, contentspec, dwsp__, Drop(Text('>')), mandatory=1)
    EncodingDecl = Series(dwsp__, Drop(Text('encoding')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), EncName, Drop(Text("\'"))), Series(Drop(Text('"')), EncName, Drop(Text('"')))))
    TextDecl = Series(Drop(Text('<?xml')), Option(VersionInfo), EncodingDecl, dwsp__, Drop(Text('?>')))
    extParsedEnt = Series(Option(TextDecl), content)
    ignoreSect = Series(Drop(Text('<![')), dwsp__, Drop(Text('IGNORE')), dwsp__, Drop(Text('[')), ignoreSectContents, Drop(Text(']]>')))
    includeSect = Series(Drop(Text('<![')), dwsp__, Drop(Text('INCLUDE')), dwsp__, Drop(Text('[')), extSubsetDecl, Drop(Text(']]>')))
    conditionalSect = Alternative(includeSect, ignoreSect)
    SDDecl = Series(dwsp__, Drop(Text('standalone')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), Alternative(Text("yes"), Text("no")), Drop(Text("\'"))), Series(Drop(Text('"')), Alternative(Text("yes"), Text("no")), Drop(Text('"')))))
    extSubset = Series(Option(TextDecl), extSubsetDecl)
    markupdecl = Alternative(elementdecl, AttlistDecl, EntityDecl, NotationDecl, PI, Comment)
    DeclSep = Alternative(PEReference, S)
    intSubset = ZeroOrMore(Alternative(markupdecl, DeclSep))
    doctypedecl = Series(Drop(Text('<!DOCTYPE')), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Option(Series(Drop(Text('[')), intSubset, Drop(Text(']')), dwsp__)), Drop(Text('>')), mandatory=2)
    XMLDecl = Series(Drop(Text('<?xml')), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, Drop(Text('?>')))
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    cp.set(Series(Alternative(Name, choice, seq), Option(Alternative(Drop(Text('?')), Drop(Text('*')), Drop(Text('+'))))))
    choice.set(Series(Drop(Text('(')), dwsp__, OneOrMore(Series(dwsp__, Drop(Text('|')), dwsp__, cp)), dwsp__, Drop(Text(')'))))
    ignoreSectContents.set(Series(IgnoreChars, ZeroOrMore(Series(Drop(Text('<![')), ignoreSectContents, Drop(Text(']]>')), IgnoreChars))))
    extSubsetDecl.set(ZeroOrMore(Alternative(markupdecl, conditionalSect, DeclSep)))
    document = Series(prolog, element, Option(Misc), EOF)
    root__ = document
    

_raw_grammar = ThreadLocalSingletonFactory(XML_DTDGrammar)

def get_grammar() -> XML_DTDGrammar:
    grammar = _raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    try:
        if not grammar.__class__.python_src__:
            grammar.__class__.python_src__ = get_grammar.python_src__
    except AttributeError:
        pass
    return grammar
    
def parse_XML_DTD(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match=complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

XML_AST_transformation_table = {
    # AST Transformations for the XML-grammar
    "<": [flatten, remove_empty, remove_anonymous_tokens, remove_whitespace, remove_children("S")],
    "document": [flatten(lambda context: context[-1].name == 'prolog', recursive=False)],
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
    "Comment": [collapse],
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



def CreateXMLTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=XML_AST_transformation_table.copy())


def get_transformer() -> TransformerCallable:
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
        attributes = collections.OrderedDict()
        for node in node_sequence:
            if node.name == "Attribute":
                assert node[0].name == "Name", node.as_sexpr()
                assert node[1].name == "AttValue", node.as_sxpr()
                attributes[node[0].content] = node[1].content
        return attributes

    def get_parser(self, tag_name):
        """Returns a mock parser with the given name as parser name."""
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
        self.tree.string_tags.update({'CharData', 'document'})
        # TODO: Remove the following line. It is specific for testing with example.xml!
        self.tree.inline_tags.update({'to', 'from', 'heading', 'body', 'remark'})
        return self.fallback_compiler(node)

    # def on_prolog(self, node):
    #     return node

    def on_XMLDecl(self, node):
        attributes = dict()
        for child in node.children:
            s = child.content
            if child.name == "VersionInfo":
                attributes['version'] = s
            elif child.name == "EncodingDecl":
                attributes['encoding'] = s
            elif child.name == "SDDecl":
                attributes['standalone'] = s
                self.value_constraint(node, s, {'yes', 'no'})
        if attributes:
            node.attr.update(attributes)
        node.result = ''
        self.tree.empty_tags.add('?xml')
        node.name = '?xml'  # node.parser = self.get_parser('?xml')
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
        node.name = tag_name
        content = tuple(self.compile(nd) for nd in node.get('content', PLACEHOLDER).children)
        if len(content) == 1:
            if content[0].name == "CharData":
                # reduce single CharData children
                content = content[0].content
        elif self.cleanup_whitespace and not preserve_whitespace:
            # remove CharData that consists only of whitespace from mixed elements
            content = tuple(child for child in content
                            if child.name != "CharData" or child.content.strip() != '')
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
        node.name = node['Name'].content  # node.parser = self.get_parser(node['Name'].content)
        node.result = ''
        self.tree.empty_tags.add(node.name)
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
    if __file__.endswith('Parser.py'):
        grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    else:
        grammar_path = os.path.splitext(__file__)[0] + '.ebnf'
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path) and os.path.isfile(grammar_path):
        if not recompile_grammar(grammar_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_MESSAGES.txt')
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

    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses a XML-file and shows its syntax-tree.")
    parser.add_argument('files', nargs=1)
    parser.add_argument('-d', '--debug', action='store_const', const='debug')
    parser.add_argument('-x', '--xml', action='store_const', const='xml')

    args = parser.parse_args()
    file_name, log_dir = args.files[0], ''

    if not os.path.exists(file_name):
        print('File "%s" not found!' % file_name)
        sys.exit(1)
    if not os.path.isfile(file_name):
        print('"%" is not a file!' % file_name)
        sys.exit(1)

    if args.debug is not None:
        log_dir = 'LOGS'
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
        print(result.serialize(how='default' if args.xml is None else 'xml')
              if isinstance(result, Node) else result)

