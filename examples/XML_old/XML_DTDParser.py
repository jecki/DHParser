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
from typing import Tuple, List, Union, Any, Optional, Callable

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
if scriptpath and scriptpath not in sys.path:
    sys.path.append(scriptpath)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, AnyChar, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, mixin_comment, \
    compile_source, grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, \
    remove_if, Node, TransformationDict, TransformerCallable, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    transform_content, replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, access_thread_locals, access_presets, PreprocessorResult, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory, Error, canonical_error_strings, \
    has_errors, ERROR, FATAL, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN 
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def XML_DTDTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as XML_DTDGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, NEVER_MATCH_PATTERN)
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(XML_DTDTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


def preprocess_XML_DTD(source):
    return get_preprocessor()(source)


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
    source_hash__ = "5037aaec98c9395c5ed90b37d4e00ef8"
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
    PI = Series(Drop(Text('<?')), PITarget, RegExp('[~ PIChars]'), Drop(Text('?>')))
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
    doctypedecl = Series(Drop(Text('<!DOCTYPE')), dwsp__, Name, RegExp('[~ ExternalID]'), dwsp__, Option(Series(Drop(Text('[')), intSubset, Drop(Text(']')), dwsp__)), Drop(Text('>')), mandatory=2)
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

XML_DTD_AST_transformation_table = {
    # AST Transformations for the XML_DTD-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],   # called for each node after calling its specific rules
    "document": [],
    "prolog": [],
    "XMLDecl": [],
    "VersionInfo": [],
    "VersionNum": [],
    "EncodingDecl": [],
    "EncName": [],
    "SDDecl": [],
    "doctypedecl": [],
    "intSubset": [],
    "DeclSep": [],
    "markupdecl": [],
    "extSubset": [],
    "extSubsetDecl": [],
    "conditionalSect": [],
    "includeSect": [],
    "ignoreSect": [],
    "ignoreSectContents": [],
    "extParsedEnt": [],
    "TextDecl": [],
    "elementdecl": [],
    "contentspec": [],
    "EMPTY": [],
    "ANY": [],
    "Mixed": [],
    "children": [],
    "choice": [],
    "cp": [],
    "seq": [],
    "AttlistDecl": [],
    "AttDef": [],
    "AttType": [],
    "StringType": [],
    "TokenizedType": [],
    "ID": [],
    "IDREF": [],
    "IDREFS": [],
    "ENTITY": [],
    "ENTITIES": [],
    "NMTOKEN": [],
    "NMTOKENS": [],
    "EnumeratedType": [],
    "NotationType": [],
    "Enumeration": [],
    "DefaultDecl": [],
    "REQUIRED": [],
    "IMPLIED": [],
    "FIXED": [],
    "EntityDecl": [],
    "GEDecl": [],
    "PEDecl": [],
    "EntityDef": [],
    "PEDef": [],
    "NotationDecl": [],
    "ExternalID": [],
    "PublicID": [],
    "NDataDecl": [],
    "element": [],
    "STag": [],
    "ETag": [],
    "emptyElement": [],
    "TagName": [],
    "Attribute": [],
    "content": [],
    "EntityValue": [],
    "AttValue": [],
    "SystemLiteral": [],
    "PubidLiteral": [],
    "Reference": [],
    "EntityRef": [],
    "PEReference": [],
    "Nmtokens": [],
    "Nmtoken": [],
    "Names": [],
    "Name": [],
    "NameStartChar": [],
    "NameChars": [],
    "Misc": [],
    "Comment": [],
    "PI": [],
    "PITarget": [],
    "CDSect": [],
    "PubidCharsSingleQuoted": [],
    "PubidChars": [],
    "CharData": [],
    "CData": [],
    "IgnoreChars": [],
    "PIChars": [],
    "CommentChars": [],
    "CharRef": [],
    "Chars": [],
    "Char": [],
    "S": [],
    "EOF": [],
}


def XML_DTDTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=XML_DTD_AST_transformation_table.copy())


get_transformer = ThreadLocalSingletonFactory(XML_DTDTransformer, ident=1)


def transform_XML_DTD(cst):
    return get_transformer()(cst)


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class XML_DTDCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a XML_DTD source file.
    """

    def __init__(self):
        super(XML_DTDCompiler, self).__init__()

    def reset(self):
        super().reset()
        self._None_check = True  # set to False if any compilation is allowed to return None
        # initialize your variables here, not in the constructor!

    def on_document(self, node):
        return self.fallback_compiler(node)

    # def on_prolog(self, node):
    #     return node

    # def on_XMLDecl(self, node):
    #     return node

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

    # def on_element(self, node):
    #     return node

    # def on_STag(self, node):
    #     return node

    # def on_ETag(self, node):
    #     return node

    # def on_emptyElement(self, node):
    #     return node

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


get_compiler = ThreadLocalSingletonFactory(XML_DTDCompiler, ident=1)


def compile_XML_DTD(ast):
    return get_compiler()(ast)


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

RESULT_FILE_EXTENSION = ".sxpr"  # Change this according to your needs!


def compile_src(source: str) -> Tuple[Any, List[Error]]:
    """Compiles ``source`` and returns (result, errors)."""
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple[:2]  # drop the AST at the end of the result tuple


def serialize_result(result: Any) -> Union[str, bytes]:
    """Serialization of result. REWRITE THIS, IF YOUR COMPILATION RESULT
    IS NOT A TREE OF NODES.
    """
    if isinstance(result, Node):
        return result.serialize(how='default' if RESULT_FILE_EXTENSION != '.xml' else 'xml')
    elif isinstance(result, str):
        return result
    else:
        return repr(result)


def process_file(source: str, result_filename: str = '') -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors or warnings occurred.
    """
    source_filename = source if is_filename(source) else ''
    result, errors = compile_src(source)
    if not has_errors(errors, FATAL):
        if os.path.abspath(source_filename) != os.path.abspath(result_filename):
            with open(result_filename, 'w', encoding='utf-8') as f:
                f.write(serialize_result(result))
        else:
            errors.append(Error('Source and destination have the same name "%s"!'
                                % result_filename, 0, FATAL))
    if errors:
        err_ext = '_ERRORS.txt' if has_errors(errors, ERROR) else '_WARNINGS.txt'
        err_filename = os.path.splitext(result_filename)[0] + err_ext
        with open(err_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(canonical_error_strings(errors)))
        return err_filename
    return ''


def batch_process(file_names: List[str], out_dir: str,
                  *, submit_func: Callable = None,
                  log_func: Callable = None) -> List[str]:
    """Compiles all files listed in filenames and writes the results and/or
    error messages to the directory `our_dir`. Returns a list of error
    messages files.
    """
    error_list =  []

    def gen_dest_name(name):
        return os.path.join(out_dir, os.path.splitext(os.path.basename(name))[0] \
                                     + RESULT_FILE_EXTENSION)

    def run_batch(submit_func: Callable):
        nonlocal error_list
        err_futures = []
        for name in file_names:
            dest_name = gen_dest_name(name)
            err_futures.append(submit_func(process_file, name, dest_name))
        for file_name, err_future in zip(file_names, err_futures):
            error_filename = err_future.result()
            if log_func:
                log_func('Compiling "%s"' % file_name)
            if error_filename:
                error_list.append(error_filename)

    if submit_func is None:
        import concurrent.futures
        from DHParser.toolkit import instantiate_executor
        with instantiate_executor(get_config_value('batch_processing_parallelization'),
                                  concurrent.futures.ProcessPoolExecutor) as pool:
            run_batch(pool.submit)
    else:
        run_batch(submit_func)
    return error_list


def main():
    # recompile grammar if needed
    script_path = os.path.abspath(__file__)
    if script_path.endswith('Parser.py'):
        grammar_path = script_path.replace('Parser.py', '.ebnf')
    else:
        grammar_path = os.path.splitext(script_path)[0] + '.ebnf'
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path) and os.path.isfile(grammar_path):
        if not recompile_grammar(grammar_path, script_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
            with open(error_file, 'r', encoding="utf-8") as f:
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
    parser = ArgumentParser(description="Parses a XML_DTD-file and shows its syntax-tree.")
    parser.add_argument('files', nargs='+')
    parser.add_argument('-d', '--debug', action='store_const', const='debug',
                        help='Store debug information in LOGS subdirectory')
    parser.add_argument('-o', '--out', nargs=1, default=['out'],
                        help='Output directory for batch processing')
    parser.add_argument('-v', '--verbose', action='store_const', const='verbose',
                        help='Verbose output')
    parser.add_argument('--singlethread', action='store_const', const='singlethread',
                        help='Run batch jobs in a single thread (recommended only for debugging)')
    outformat = parser.add_mutually_exclusive_group()
    outformat.add_argument('-x', '--xml', action='store_const', const='xml', 
                           help='Format result as XML')
    outformat.add_argument('-s', '--sxpr', action='store_const', const='sxpr',
                           help='Format result as S-expression')
    outformat.add_argument('-t', '--tree', action='store_const', const='tree',
                           help='Format result as indented tree')
    outformat.add_argument('-j', '--json', action='store_const', const='json',
                           help='Format result as JSON')

    args = parser.parse_args()
    file_names, out, log_dir = args.files, args.out[0], ''

    # if not os.path.exists(file_name):
    #     print('File "%s" not found!' % file_name)
    #     sys.exit(1)
    # if not os.path.isfile(file_name):
    #     print('"%s" is not a file!' % file_name)
    #     sys.exit(1)

    if args.debug is not None:
        log_dir = 'LOGS'
        access_presets()
        set_preset_value('history_tracking', True)
        set_preset_value('resume_notices', True)
        set_preset_value('log_syntax_trees', frozenset(['cst', 'ast']))  # don't use a set literal, here!
        finalize_presets()
    start_logging(log_dir)

    if args.singlethread:
        set_config_value('batch_processing_parallelization', False)

    if args.xml:
        RESULT_FILE_EXTENSION = '.xml'

    def echo(message: str):
        if args.verbose:
            print(message)

    batch_processing = True
    if len(file_names) == 1:
        if os.path.isdir(file_names[0]):
            dir_name = file_names[0]
            echo('Processing all files in directory: ' + dir_name)
            file_names = [os.path.join(dir_name, fn) for fn in os.listdir(dir_name)
                          if os.path.isfile(os.path.join(dir_name, fn))]
        elif not ('-o' in sys.argv or '--out' in sys.argv):
            batch_processing = False

    if batch_processing:
        if not os.path.exists(out):
            os.mkdir(out)
        elif not os.path.isdir(out):
            print('Output directory "%s" exists and is not a directory!' % out)
            sys.exit(1)
        error_files = batch_process(file_names, out, log_func=print if args.verbose else None)
        if error_files:
            category = "ERRORS" if any(f.endswith('_ERRORS.txt') for f in error_files) \
                else "warnings"
            print("There have been %s! Please check files:" % category)
            print('\n'.join(error_files))
            if category == "ERRORS":
                sys.exit(1)
    else:
        result, errors = compile_src(file_names[0])

        if errors:
            for err_str in canonical_error_strings(errors):
                print(err_str)
            if has_errors(errors, ERROR):
                sys.exit(1)

        if args.xml:  outfmt = 'xml'
        elif args.sxpr:  outfmt = 'sxpr'
        elif args.tree:  outfmt = 'tree'
        elif args.json:  outfmt = 'json'
        else:  outfmt = 'default'
        print(result.serialize(how=outfmt) if isinstance(result, Node) else result)


if __name__ == "__main__":
    main()
