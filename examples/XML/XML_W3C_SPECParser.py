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
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, \
    merge_adjacent, collapse, collapse_children_if, transform_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    transform_content, replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, node_maker, any_of, \
    INDENTED_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_tag_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def XML_W3C_SPECPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return XML_W3C_SPECPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class XML_W3C_SPECGrammar(Grammar):
    r"""Parser for a XML_W3C_SPEC source file.
    """
    AttValue = Forward()
    Attribute = Forward()
    CDSect = Forward()
    Char = Forward()
    CharData = Forward()
    CharRef = Forward()
    Comment = Forward()
    DeclSep = Forward()
    EntityValue = Forward()
    Eq = Forward()
    ExternalID = Forward()
    Name = Forward()
    NameChar = Forward()
    NameStartChar = Forward()
    Nmtoken = Forward()
    PI = Forward()
    PubidLiteral = Forward()
    S = Forward()
    SystemLiteral = Forward()
    TextDecl = Forward()
    VersionInfo = Forward()
    content = Forward()
    cp = Forward()
    element = Forward()
    extSubsetDecl = Forward()
    ignoreSectContents = Forward()
    markupdecl = Forward()
    source_hash__ = "09175b3165ddc1481814046dc639de56"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    PublicID = Series(Text('PUBLIC'), S, PubidLiteral)
    NotationDecl = Series(Text('<!NOTATION'), S, Name, S, Alternative(ExternalID, PublicID), Option(S), Text('>'), RegExp('[VC: Unique Notation Name]'))
    EncName = Series(RegExp('[A-Za-z]'), ZeroOrMore(Alternative(RegExp('[A-Za-z0-9._]'), Text('-'))))
    EncodingDecl = Series(S, Text('encoding'), Eq, Alternative(Series(Text('"'), EncName, Text('"')), Series(Text("\'"), EncName, Text("\'"))))
    extParsedEnt = Series(Option(TextDecl), content)
    TextDecl.set(Series(Text('<?xml'), Option(VersionInfo), EncodingDecl, Option(S), Text('?>')))
    NDataDecl = Series(S, Text('NDATA'), S, Name)
    ExternalID.set(Alternative(Series(Text('SYSTEM'), S, SystemLiteral), Series(Text('PUBLIC'), S, PubidLiteral, S, SystemLiteral)))
    PEDef = Alternative(EntityValue, ExternalID)
    EntityDef = Alternative(EntityValue, Series(ExternalID, Option(NDataDecl)))
    PEDecl = Series(Text('<!ENTITY'), S, Text('%'), S, Name, S, PEDef, Option(S), Text('>'))
    GEDecl = Series(Text('<!ENTITY'), S, Name, S, EntityDef, Option(S), Text('>'))
    EntityDecl = Alternative(GEDecl, PEDecl)
    PEReference = Series(Text('%'), Name, Text(';'))
    EntityRef = Series(Text('&'), Name, Text(';'))
    Reference = Alternative(EntityRef, CharRef)
    CharRef.set(Alternative(Series(Text('&#'), OneOrMore(RegExp('[0-9]')), Text(';')), Series(Text('&#x'), OneOrMore(RegExp('[0-9a-fA-F]')), Text(';'))))
    Ignore = Series(NegativeLookahead(Series(ZeroOrMore(Char), Alternative(Text('<!['), Text(']]>')), ZeroOrMore(Char))), ZeroOrMore(Char))
    ignoreSectContents.set(Series(Ignore, ZeroOrMore(Series(Text('<!['), ignoreSectContents, Text(']]>'), Ignore))))
    ignoreSect = Series(Text('<!['), Option(S), Text('IGNORE'), Option(S), Text('['), ZeroOrMore(ignoreSectContents), Text(']]>'))
    includeSect = Series(Text('<!['), Option(S), Text('INCLUDE'), Option(S), Text('['), extSubsetDecl, Text(']]>'))
    conditionalSect = Alternative(includeSect, ignoreSect)
    DefaultDecl = Alternative(Text('#REQUIRED'), Text('#IMPLIED'), Series(Option(Series(Text('#FIXED'), S)), AttValue))
    Enumeration = Series(Text('('), Option(S), Nmtoken, ZeroOrMore(Series(Option(S), Text('|'), Option(S), Nmtoken)), Option(S), Text(')'))
    NotationType = Series(Text('NOTATION'), S, Text('('), Option(S), Name, ZeroOrMore(Series(Option(S), Text('|'), Option(S), Name)), Option(S), Text(')'))
    EnumeratedType = Alternative(NotationType, Enumeration)
    TokenizedType = Alternative(Text('IDREFS'), Text('IDREF'), Text('ID'), Text('ENTITY'), Text('ENTITIES'), Text('NMTOKENS'), Text('NMTOKEN'))
    StringType = Text('CDATA')
    AttType = Alternative(StringType, TokenizedType, EnumeratedType)
    AttDef = Series(S, Name, S, AttType, S, DefaultDecl)
    AttlistDecl = Series(Text('<!ATTLIST'), S, Name, ZeroOrMore(AttDef), Option(S), Text('>'))
    Mixed = Alternative(Series(Text('('), Option(S), Text('#PCDATA'), ZeroOrMore(Series(Option(S), Text('|'), Option(S), Name)), Option(S), Text(')*')), Series(Text('('), Option(S), Text('#PCDATA'), Option(S), Text(')')))
    seq = Series(Text('('), Option(S), cp, ZeroOrMore(Series(Option(S), Text(','), Option(S), cp)), Option(S), Text(')'))
    choice = Series(Text('('), Option(S), cp, OneOrMore(Series(Option(S), Text('|'), Option(S), cp)), Option(S), Text(')'))
    cp.set(Series(Alternative(Name, choice, seq), Option(Alternative(Text('?'), Text('*'), Text('+')))))
    children = Series(Alternative(choice, seq), Option(Alternative(Text('?'), Text('*'), Text('+'))))
    contentspec = Alternative(Text('EMPTY'), Text('ANY'), Mixed, children)
    elementdecl = Series(Text('<!ELEMENT'), S, Name, S, contentspec, Option(S), Text('>'))
    EmptyElemTag = Series(Text('<'), Name, ZeroOrMore(Series(S, Attribute)), Option(S), Text('/>'))
    content.set(Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData)))))
    ETag = Series(Text('</'), Name, Option(S), Text('>'))
    Attribute.set(Series(Name, Eq, AttValue))
    STag = Series(Text('<'), Name, ZeroOrMore(Series(S, Attribute)), Option(S), Text('>'))
    element.set(Alternative(EmptyElemTag, Series(STag, content, ETag)))
    SDDecl = Series(S, Text('standalone'), Eq, Alternative(Series(Text("\'"), Alternative(Text('yes'), Text('no')), Text("\'")), Series(Text('"'), Alternative(Text('yes'), Text('no')), Text('"'))))
    extSubsetDecl.set(ZeroOrMore(Alternative(markupdecl, conditionalSect, DeclSep)))
    extSubset = Series(Option(TextDecl), extSubsetDecl)
    markupdecl.set(Alternative(elementdecl, AttlistDecl, EntityDecl, NotationDecl, PI, Comment))
    intSubset = ZeroOrMore(Alternative(markupdecl, DeclSep))
    DeclSep.set(Alternative(PEReference, S))
    doctypedecl = Series(Text('<!DOCTYPE'), S, Name, Option(Series(S, ExternalID)), Option(S), Option(Series(Text('['), intSubset, Text(']'), Option(S))), Text('>'))
    Misc = Alternative(Comment, PI, S)
    VersionNum = Series(Text('1.'), OneOrMore(RegExp('[0-9]')))
    Eq.set(Series(Option(S), Text('='), Option(S)))
    VersionInfo.set(Series(S, Text('version'), Eq, Alternative(Series(Text("\'"), VersionNum, Text("\'")), Series(Text('"'), VersionNum, Text('"')))))
    XMLDecl = Series(Text('<?xml'), VersionInfo, Option(EncodingDecl), Option(SDDecl), Option(S), Text('?>'))
    prolog = Series(Option(XMLDecl), ZeroOrMore(Misc), Option(Series(doctypedecl, ZeroOrMore(Misc))))
    CDEnd = Text(']]>')
    CData = Series(NegativeLookahead(Series(ZeroOrMore(Char), Text(']]>'), ZeroOrMore(Char))), ZeroOrMore(Char))
    CDStart = Text('<![CDATA[')
    CDSect.set(Series(CDStart, CData, CDEnd))
    PITarget = Series(NegativeLookahead(Series(Alternative(Text('X'), Text('x')), Alternative(Text('M'), Text('m')), Alternative(Text('L'), Text('l')))), Name)
    PI.set(Series(Text('<?'), PITarget, Option(Series(S, Series(NegativeLookahead(Series(ZeroOrMore(Char), Text('?>'), ZeroOrMore(Char))), ZeroOrMore(Char)))), Text('?>')))
    Comment.set(Series(Text('<!--'), ZeroOrMore(Alternative(Series(NegativeLookahead(Text('-')), Char), Series(Text('-'), Series(NegativeLookahead(Text('-')), Char)))), Text('-->')))
    CharData.set(Series(NegativeLookahead(Series(ZeroOrMore(RegExp('[^<&]')), Text(']]>'), ZeroOrMore(RegExp('[^<&]')))), ZeroOrMore(RegExp('[^<&]'))))
    PubidChar = Alternative(RegExp('\x20'), RegExp('\x0D'), RegExp('\x0A'), RegExp('[a-zA-Z0-9]'), RegExp('[-\'()+,./:=?;!*#@$_%]'))
    PubidLiteral.set(Alternative(Series(Text('"'), ZeroOrMore(PubidChar), Text('"')), Series(Text("\'"), ZeroOrMore(Series(NegativeLookahead(Text("\'")), PubidChar)), Text("\'"))))
    SystemLiteral.set(Alternative(Series(Text('"'), ZeroOrMore(RegExp('[^"]')), Text('"')), Series(Text("\'"), ZeroOrMore(RegExp('[^\']')), Text("\'"))))
    AttValue.set(Alternative(Series(Text('"'), ZeroOrMore(Alternative(RegExp('[^<&"]'), Reference)), Text('"')), Series(Text("\'"), ZeroOrMore(Alternative(RegExp('[^<&\']'), Reference)), Text("\'"))))
    EntityValue.set(Alternative(Series(Text('"'), ZeroOrMore(Alternative(RegExp('[^%&"]'), PEReference, Reference)), Text('"')), Series(Text("\'"), ZeroOrMore(Alternative(RegExp('[^%&\']'), PEReference, Reference)), Text("\'"))))
    Nmtokens = Series(Nmtoken, ZeroOrMore(Series(RegExp('\x20'), Nmtoken)))
    Nmtoken.set(OneOrMore(NameChar))
    Names = Series(Name, ZeroOrMore(Series(RegExp('\x20'), Name)))
    Name.set(Series(NameStartChar, ZeroOrMore(NameChar)))
    NameChar.set(Alternative(NameStartChar, Text("-"), Text("."), RegExp('[0-9]'), RegExp('\xB7'), RegExp('[\u0300-\u036F]'), RegExp('[\u203F-\u2040]')))
    NameStartChar.set(Alternative(Text(":"), RegExp('[A-Z]'), Text("_"), RegExp('[a-z]'), RegExp('[\xC0-\xD6]'), RegExp('[\xD8-\xF6]'), RegExp('[\xF8-\u02FF]'), RegExp('[\u0370-\u037D]'), RegExp('[\u037F-\u1FFF]'), RegExp('[\u200C-\u200D]'), RegExp('[\u2070-\u218F]'), RegExp('[\u2C00-\u2FEF]'), RegExp('[\u3001-\uD7FF]'), RegExp('[\uF900-\uFDCF]'), RegExp('[\uFDF0-\uFFFD]'), RegExp('[\U00010000-\U000EFFFF]')))
    S.set(OneOrMore(Alternative(RegExp('\x20'), RegExp('\x09'), RegExp('\x0D'), RegExp('\x0A'))))
    Char.set(Alternative(RegExp('\x09'), RegExp('\x0A'), RegExp('\x0D'), RegExp('[\x20-\uD7FF]'), RegExp('[\uE000-\uFFFD]'), RegExp('[\U00010000-\U0010FFFF]')))
    document = Series(prolog, element, ZeroOrMore(Misc))
    root__ = document
    

def get_grammar() -> XML_W3C_SPECGrammar:
    """Returns a thread/process-exclusive XML_W3C_SPECGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.XML_W3C_SPEC_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.XML_W3C_SPEC_00000001_grammar_singleton = XML_W3C_SPECGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.XML_W3C_SPEC_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.XML_W3C_SPEC_00000001_grammar_singleton
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

XML_W3C_SPEC_AST_transformation_table = {
    # AST Transformations for the XML_W3C_SPEC-grammar
    "<": flatten,
    "document": [],
    "Char": [],
    "S": [],
    "NameStartChar": [],
    "NameChar": [],
    "Name": [],
    "Names": [],
    "Nmtoken": [],
    "Nmtokens": [],
    "EntityValue": [],
    "AttValue": [],
    "SystemLiteral": [],
    "PubidLiteral": [],
    "PubidChar": [],
    "CharData": [],
    "Comment": [],
    "PI": [],
    "PITarget": [],
    "CDSect": [],
    "CDStart": [],
    "CData": [],
    "CDEnd": [],
    "prolog": [],
    "XMLDecl": [],
    "VersionInfo": [],
    "Eq": [],
    "VersionNum": [],
    "Misc": [],
    "doctypedecl": [],
    "DeclSep": [],
    "intSubset": [],
    "markupdecl": [],
    "extSubset": [],
    "extSubsetDecl": [],
    "SDDecl": [],
    "element": [],
    "STag": [],
    "Attribute": [],
    "ETag": [],
    "content": [],
    "EmptyElemTag": [],
    "elementdecl": [],
    "contentspec": [],
    "children": [],
    "cp": [],
    "choice": [],
    "seq": [],
    "Mixed": [],
    "AttlistDecl": [],
    "AttDef": [],
    "AttType": [],
    "StringType": [],
    "TokenizedType": [],
    "EnumeratedType": [],
    "NotationType": [],
    "Enumeration": [],
    "DefaultDecl": [],
    "conditionalSect": [],
    "includeSect": [],
    "ignoreSect": [],
    "ignoreSectContents": [],
    "Ignore": [],
    "CharRef": [],
    "Reference": [],
    "EntityRef": [],
    "PEReference": [],
    "EntityDecl": [],
    "GEDecl": [],
    "PEDecl": [],
    "EntityDef": [],
    "PEDef": [],
    "ExternalID": [],
    "NDataDecl": [],
    "TextDecl": [],
    "extParsedEnt": [],
    "EncodingDecl": [],
    "EncName": [],
    "NotationDecl": [],
    "PublicID": [],
    "*": replace_by_single_child
}



def CreateXML_W3C_SPECTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=XML_W3C_SPEC_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.XML_W3C_SPEC_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.XML_W3C_SPEC_00000001_transformer_singleton = CreateXML_W3C_SPECTransformer()
        transformer = THREAD_LOCALS.XML_W3C_SPEC_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class XML_W3C_SPECCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a XML_W3C_SPEC source file.
    """

    def __init__(self):
        super(XML_W3C_SPECCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_document(self, node):
        return self.fallback_compiler(node)

    # def on_Char(self, node):
    #     return node

    # def on_S(self, node):
    #     return node

    # def on_NameStartChar(self, node):
    #     return node

    # def on_NameChar(self, node):
    #     return node

    # def on_Name(self, node):
    #     return node

    # def on_Names(self, node):
    #     return node

    # def on_Nmtoken(self, node):
    #     return node

    # def on_Nmtokens(self, node):
    #     return node

    # def on_EntityValue(self, node):
    #     return node

    # def on_AttValue(self, node):
    #     return node

    # def on_SystemLiteral(self, node):
    #     return node

    # def on_PubidLiteral(self, node):
    #     return node

    # def on_PubidChar(self, node):
    #     return node

    # def on_CharData(self, node):
    #     return node

    # def on_Comment(self, node):
    #     return node

    # def on_PI(self, node):
    #     return node

    # def on_PITarget(self, node):
    #     return node

    # def on_CDSect(self, node):
    #     return node

    # def on_CDStart(self, node):
    #     return node

    # def on_CData(self, node):
    #     return node

    # def on_CDEnd(self, node):
    #     return node

    # def on_prolog(self, node):
    #     return node

    # def on_XMLDecl(self, node):
    #     return node

    # def on_VersionInfo(self, node):
    #     return node

    # def on_Eq(self, node):
    #     return node

    # def on_VersionNum(self, node):
    #     return node

    # def on_Misc(self, node):
    #     return node

    # def on_doctypedecl(self, node):
    #     return node

    # def on_DeclSep(self, node):
    #     return node

    # def on_intSubset(self, node):
    #     return node

    # def on_markupdecl(self, node):
    #     return node

    # def on_extSubset(self, node):
    #     return node

    # def on_extSubsetDecl(self, node):
    #     return node

    # def on_SDDecl(self, node):
    #     return node

    # def on_element(self, node):
    #     return node

    # def on_STag(self, node):
    #     return node

    # def on_Attribute(self, node):
    #     return node

    # def on_ETag(self, node):
    #     return node

    # def on_content(self, node):
    #     return node

    # def on_EmptyElemTag(self, node):
    #     return node

    # def on_elementdecl(self, node):
    #     return node

    # def on_contentspec(self, node):
    #     return node

    # def on_children(self, node):
    #     return node

    # def on_cp(self, node):
    #     return node

    # def on_choice(self, node):
    #     return node

    # def on_seq(self, node):
    #     return node

    # def on_Mixed(self, node):
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

    # def on_EnumeratedType(self, node):
    #     return node

    # def on_NotationType(self, node):
    #     return node

    # def on_Enumeration(self, node):
    #     return node

    # def on_DefaultDecl(self, node):
    #     return node

    # def on_conditionalSect(self, node):
    #     return node

    # def on_includeSect(self, node):
    #     return node

    # def on_ignoreSect(self, node):
    #     return node

    # def on_ignoreSectContents(self, node):
    #     return node

    # def on_Ignore(self, node):
    #     return node

    # def on_CharRef(self, node):
    #     return node

    # def on_Reference(self, node):
    #     return node

    # def on_EntityRef(self, node):
    #     return node

    # def on_PEReference(self, node):
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

    # def on_ExternalID(self, node):
    #     return node

    # def on_NDataDecl(self, node):
    #     return node

    # def on_TextDecl(self, node):
    #     return node

    # def on_extParsedEnt(self, node):
    #     return node

    # def on_EncodingDecl(self, node):
    #     return node

    # def on_EncName(self, node):
    #     return node

    # def on_NotationDecl(self, node):
    #     return node

    # def on_PublicID(self, node):
    #     return node



def get_compiler() -> XML_W3C_SPECCompiler:
    """Returns a thread/process-exclusive XML_W3C_SPECCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.XML_W3C_SPEC_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.XML_W3C_SPEC_00000001_compiler_singleton = XML_W3C_SPECCompiler()
        compiler = THREAD_LOCALS.XML_W3C_SPEC_00000001_compiler_singleton
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

    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses a XML_W3C_SPEC-file and shows its syntax-tree.")
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
