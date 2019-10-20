#!/usr/bin/python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from collections import OrderedDict
from functools import partial
import os
import sys

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, Token, DropToken, DropWhitespace, \
    traverse, remove_children_if, is_anonymous, access_thread_locals, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    is_empty, collapse, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, PLACEHOLDER


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
    source_hash__ = "fabca55375f62d0a2f009cdfd76f0f77"
    static_analysis_pending__ = [True]
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'//'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('.'))
    S = RegExp('\\s+')
    Char = RegExp('\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]')
    Chars = RegExp('(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF])+')
    CharRef = Alternative(Series(DropToken('&#'), RegExp('[0-9]+'), DropToken(';')), Series(DropToken('&#x'), RegExp('[0-9a-fA-F]+'), DropToken(';')))
    CommentChars = RegExp('(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    PIChars = RegExp('(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    IgnoreChars = RegExp('(?:(?!(?:<!\\[)|(?:\\]\\]>))(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CData = RegExp('(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CharData = RegExp('(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    CDSect = Series(DropToken('<![CDATA['), CData, DropToken(']]>'))
    PITarget = Series(NegativeLookahead(RegExp('X|xM|mL|l')), Name)
    PI = Series(DropToken('<?'), PITarget, Option(Series(dwsp__, PIChars)), DropToken('?>'))
    Comment = Series(DropToken('<!--'), ZeroOrMore(Alternative(CommentChars, RegExp('-(?!-)'))), DropToken('-->'))
    Misc = OneOrMore(Alternative(Comment, PI, S))
    NameChars = RegExp('(?x)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n                   |\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF])+')
    NameStartChar = RegExp('(?x)_|:|[A-Z]|[a-z]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF]')
    Name.set(Series(NameStartChar, Option(NameChars)))
    Names = Series(Name, ZeroOrMore(Series(RegExp(' '), Name)))
    Nmtoken = Synonym(NameChars)
    Nmtokens = Series(Nmtoken, ZeroOrMore(Series(RegExp(' '), Nmtoken)))
    PEReference = Series(DropToken('%'), Name, DropToken(';'))
    EntityRef = Series(DropToken('&'), Name, DropToken(';'))
    Reference = Alternative(EntityRef, CharRef)
    PubidLiteral = Alternative(Series(DropToken('"'), Option(PubidChars), DropToken('"')), Series(DropToken("'"), Option(PubidCharsSingleQuoted), DropToken("'")))
    SystemLiteral = Alternative(Series(DropToken('"'), RegExp('[^"]*'), DropToken('"')), Series(DropToken("'"), RegExp("[^']*"), DropToken("'")))
    AttValue = Alternative(Series(DropToken('"'), ZeroOrMore(Alternative(RegExp('[^<&"]+'), Reference)), DropToken('"')), Series(DropToken("'"), ZeroOrMore(Alternative(RegExp("[^<&']+"), Reference)), DropToken("'")))
    EntityValue = Alternative(Series(DropToken('"'), ZeroOrMore(Alternative(RegExp('[^%&"]+'), PEReference, Reference)), DropToken('"')), Series(DropToken("'"), ZeroOrMore(Alternative(RegExp("[^%&']+"), PEReference, Reference)), DropToken("'")))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Attribute = Series(Name, dwsp__, DropToken('='), dwsp__, AttValue, mandatory=2)
    TagName = Capture(Name)
    emptyElement = Series(DropToken('<'), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, DropToken('/>'))
    ETag = Series(DropToken('</'), Pop(TagName), dwsp__, DropToken('>'), mandatory=1)
    STag = Series(DropToken('<'), TagName, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, DropToken('>'))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    NDataDecl = Series(DropToken('NData'), S, Name, mandatory=1)
    PublicID = Series(DropToken('PUBLIC'), S, PubidLiteral, mandatory=1)
    ExternalID = Series(DropToken('SYSTEM'), S, SystemLiteral, mandatory=1)
    NotationDecl = Series(DropToken('<!NOTATION'), S, Name, dwsp__, Alternative(ExternalID, PublicID), dwsp__, DropToken('>'), mandatory=1)
    PEDef = Alternative(EntityValue, ExternalID)
    EntityDef = Alternative(EntityValue, Series(ExternalID, Option(NDataDecl)))
    PEDecl = Series(DropToken('<!ENTITY'), S, DropToken('%'), S, Name, S, PEDef, dwsp__, DropToken('>'), mandatory=3)
    GEDecl = Series(DropToken('<!ENTITY'), S, Name, S, EntityDef, dwsp__, DropToken('>'), mandatory=3)
    EntityDecl = Alternative(GEDecl, PEDecl)
    FIXED = Series(Option(Series(DropToken('#FIXED'), S)), AttValue)
    IMPLIED = Token('#IMPLIED')
    REQUIRED = Token('#REQUIRED')
    DefaultDecl = Alternative(REQUIRED, IMPLIED, FIXED)
    Enumeration = Series(DropToken('('), dwsp__, Nmtoken, ZeroOrMore(Series(dwsp__, DropToken('|'), dwsp__, Nmtoken)), dwsp__, DropToken(')'))
    NotationType = Series(DropToken('NOTATION'), S, DropToken('('), dwsp__, Name, ZeroOrMore(Series(dwsp__, DropToken('|'), dwsp__, Name)), dwsp__, DropToken(')'))
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
    AttlistDecl = Series(DropToken('<!ATTLIST'), S, Name, ZeroOrMore(Series(dwsp__, AttDef)), dwsp__, DropToken('>'), mandatory=1)
    seq = Series(DropToken('('), dwsp__, cp, ZeroOrMore(Series(dwsp__, DropToken(','), dwsp__, cp)), dwsp__, DropToken(')'))
    cp.set(Series(Alternative(Name, choice, seq), Option(Alternative(DropToken('?'), DropToken('*'), DropToken('+')))))
    choice.set(Series(DropToken('('), dwsp__, OneOrMore(Series(dwsp__, DropToken('|'), dwsp__, cp)), dwsp__, DropToken(')')))
    children = Series(Alternative(choice, seq), Option(Alternative(DropToken('?'), DropToken('*'), DropToken('+'))))
    Mixed = Alternative(Series(DropToken('('), dwsp__, DropToken('#PCDATA'), ZeroOrMore(Series(dwsp__, DropToken('|'), dwsp__, Name)), dwsp__, DropToken(')*')), Series(DropToken('('), dwsp__, DropToken('#PCDATA'), dwsp__, DropToken(')')))
    ANY = Token('ANY')
    EMPTY = Token('EMPTY')
    contentspec = Alternative(EMPTY, ANY, Mixed, children)
    elementdecl = Series(DropToken('<!ELEMENT'), S, Name, dwsp__, contentspec, dwsp__, DropToken('>'), mandatory=1)
    TextDecl = Series(DropToken('<?xml'), Option(VersionInfo), EncodingDecl, dwsp__, DropToken('?>'))
    extParsedEnt = Series(Option(TextDecl), content)
    ignoreSectContents.set(Series(IgnoreChars, ZeroOrMore(Series(DropToken('<!['), ignoreSectContents, DropToken(']]>'), IgnoreChars))))
    ignoreSect = Series(DropToken('<!['), dwsp__, DropToken('IGNORE'), dwsp__, DropToken('['), ignoreSectContents, DropToken(']]>'))
    includeSect = Series(DropToken('<!['), dwsp__, DropToken('INCLUDE'), dwsp__, DropToken('['), extSubsetDecl, DropToken(']]>'))
    conditionalSect = Alternative(includeSect, ignoreSect)
    extSubsetDecl.set(ZeroOrMore(Alternative(markupdecl, conditionalSect, DeclSep)))
    extSubset = Series(Option(TextDecl), extSubsetDecl)
    markupdecl.set(Alternative(elementdecl, AttlistDecl, EntityDecl, NotationDecl, PI, Comment))
    DeclSep.set(Alternative(PEReference, S))
    intSubset = ZeroOrMore(Alternative(markupdecl, DeclSep))
    doctypedecl = Series(DropToken('<!DOCTYPE'), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Option(Series(DropToken('['), intSubset, DropToken(']'), dwsp__)), DropToken('>'))
    No = Token('no')
    Yes = Token('yes')
    SDDecl = Series(dwsp__, DropToken('standalone'), dwsp__, DropToken('='), dwsp__, Alternative(Alternative(Series(DropToken("'"), Yes), Series(No, DropToken("'"))), Alternative(Series(DropToken('"'), Yes), Series(No, DropToken('"')))))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl.set(Series(dwsp__, DropToken('encoding'), dwsp__, DropToken('='), dwsp__, Alternative(Series(DropToken("'"), EncName, DropToken("'")), Series(DropToken('"'), EncName, DropToken('"')))))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo.set(Series(dwsp__, DropToken('version'), dwsp__, DropToken('='), dwsp__, Alternative(Series(DropToken("'"), VersionNum, DropToken("'")), Series(DropToken('"'), VersionNum, DropToken('"')))))
    XMLDecl = Series(DropToken('<?xml'), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, DropToken('?>'))
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
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


XML_AST_transformation_table = {
    # AST Transformations for the XML-grammar
    "<": [flatten, remove_empty, remove_anonymous_tokens, remove_whitespace, remove_nodes("S")],
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


def XMLTransform() -> TransformationFunc:
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
#     remove_nodes(context, {'Attribute'})


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
    global thread_local_XML_compiler_singleton
    try:
        compiler = thread_local_XML_compiler_singleton
    except NameError:
        thread_local_XML_compiler_singleton = XMLCompiler()
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
    start_logging(log_dir)
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
