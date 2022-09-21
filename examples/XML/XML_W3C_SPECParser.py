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
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_result, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
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


def XML_W3C_SPECTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as XML_W3C_SPECGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, NEVER_MATCH_PATTERN)
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(XML_W3C_SPECTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


def preprocess_XML_W3C_SPEC(source):
    return get_preprocessor()(source)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class XML_W3C_SPECGrammar(Grammar):
    r"""Parser for a XML_W3C_SPEC source file.
    """
    content = Forward()
    cp = Forward()
    element = Forward()
    extSubsetDecl = Forward()
    ignoreSectContents = Forward()
    source_hash__ = "ac5909c47cac99f289d336638ae4fc5d"
    disposable__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'[ \t]*(?:\n[ \t]*)?(?!\n)'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    PubidChar = Alternative(RegExp('\x20'), RegExp('\x0D'), RegExp('\x0A'), RegExp('[a-zA-Z0-9]'), RegExp('[-\'()+,./:=?;!*#@$_%]'))
    PubidLiteral = Alternative(Series(Text('"'), ZeroOrMore(PubidChar), Text('"')), Series(Text("\'"), ZeroOrMore(Series(NegativeLookahead(Text("\'")), PubidChar)), Text("\'")))
    EncName = Series(RegExp('[A-Za-z]'), ZeroOrMore(Alternative(RegExp('[A-Za-z0-9._]'), Text('-'))))
    S = OneOrMore(Alternative(RegExp('\x20'), RegExp('\x09'), RegExp('\x0D'), RegExp('\x0A')))
    Eq = Series(Option(S), Text('='), Option(S))
    VersionNum = Series(Text('1.'), OneOrMore(RegExp('[0-9]')))
    NameStartChar = Alternative(Text(":"), RegExp('[A-Z]'), Text("_"), RegExp('[a-z]'), RegExp('[\xC0-\xD6]'), RegExp('[\xD8-\xF6]'), RegExp('[\xF8-\u02FF]'), RegExp('[\u0370-\u037D]'), RegExp('[\u037F-\u1FFF]'), RegExp('[\u200C-\u200D]'), RegExp('[\u2070-\u218F]'), RegExp('[\u2C00-\u2FEF]'), RegExp('[\u3001-\uD7FF]'), RegExp('[\uF900-\uFDCF]'), RegExp('[\uFDF0-\uFFFD]'), RegExp('[\U00010000-\U000EFFFF]'))
    SystemLiteral = Alternative(Series(Text('"'), ZeroOrMore(RegExp('[^"]')), Text('"')), Series(Text("\'"), ZeroOrMore(RegExp('[^\']')), Text("\'")))
    EncodingDecl = Series(S, Text('encoding'), Eq, Alternative(Series(Text('"'), EncName, Text('"')), Series(Text("\'"), EncName, Text("\'"))))
    NameChar = Alternative(NameStartChar, Text("-"), Text("."), RegExp('[0-9]'), RegExp('\xB7'), RegExp('[\u0300-\u036F]'), RegExp('[\u203F-\u2040]'))
    CharRef = Alternative(Series(Text('&#'), OneOrMore(RegExp('[0-9]')), Text(';')), Series(Text('&#x'), OneOrMore(RegExp('[0-9a-fA-F]')), Text(';')))
    PublicID = Series(Text('PUBLIC'), S, PubidLiteral)
    ExternalID = Alternative(Series(Text('SYSTEM'), S, SystemLiteral), Series(Text('PUBLIC'), S, PubidLiteral, S, SystemLiteral))
    Name = Series(NameStartChar, ZeroOrMore(NameChar))
    NDataDecl = Series(S, Text('NDATA'), S, Name)
    EntityRef = Series(Text('&'), Name, Text(';'))
    Reference = Alternative(EntityRef, CharRef)
    Char = Alternative(RegExp('\x09'), RegExp('\x0A'), RegExp('\x0D'), RegExp('[\x20-\uD7FF]'), RegExp('[\uE000-\uFFFD]'), RegExp('[\U00010000-\U0010FFFF]'))
    PEReference = Series(Text('%'), Name, Text(';'))
    NotationDecl = Series(Text('<!NOTATION'), S, Name, S, Alternative(ExternalID, PublicID), Option(S), Text('>'))
    ignoreSect = Series(Text('<!['), Option(S), Text('IGNORE'), Option(S), Text('['), ZeroOrMore(ignoreSectContents), Text(']]>'))
    includeSect = Series(Text('<!['), Option(S), Text('INCLUDE'), Option(S), Text('['), extSubsetDecl, Text(']]>'))
    EntityValue = Alternative(Series(Text('"'), ZeroOrMore(Alternative(RegExp('[^%&"]'), PEReference, Reference)), Text('"')), Series(Text("\'"), ZeroOrMore(Alternative(RegExp('[^%&\']'), PEReference, Reference)), Text("\'")))
    PEDef = Alternative(EntityValue, ExternalID)
    conditionalSect = Alternative(includeSect, ignoreSect)
    AttValue = Alternative(Series(Text('"'), ZeroOrMore(Alternative(RegExp('[^<&"]'), Reference)), Text('"')), Series(Text("\'"), ZeroOrMore(Alternative(RegExp('[^<&\']'), Reference)), Text("\'")))
    TokenizedType = Alternative(Text('IDREFS'), Text('IDREF'), Text('ID'), Text('ENTITY'), Text('ENTITIES'), Text('NMTOKENS'), Text('NMTOKEN'))
    StringType = Text('CDATA')
    Nmtoken = OneOrMore(NameChar)
    NotationType = Series(Text('NOTATION'), S, Text('('), Option(S), Name, ZeroOrMore(Series(Option(S), Text('|'), Option(S), Name)), Option(S), Text(')'))
    Enumeration = Series(Text('('), Option(S), Nmtoken, ZeroOrMore(Series(Option(S), Text('|'), Option(S), Nmtoken)), Option(S), Text(')'))
    DefaultDecl = Alternative(Text('#REQUIRED'), Text('#IMPLIED'), Series(Option(Series(Text('#FIXED'), S)), AttValue))
    Mixed = Alternative(Series(Text('('), Option(S), Text('#PCDATA'), ZeroOrMore(Series(Option(S), Text('|'), Option(S), Name)), Option(S), Text(')*')), Series(Text('('), Option(S), Text('#PCDATA'), Option(S), Text(')')))
    seq = Series(Text('('), Option(S), cp, ZeroOrMore(Series(Option(S), Text(','), Option(S), cp)), Option(S), Text(')'))
    EnumeratedType = Alternative(NotationType, Enumeration)
    choice = Series(Text('('), Option(S), cp, OneOrMore(Series(Option(S), Text('|'), Option(S), cp)), Option(S), Text(')'))
    children = Series(Alternative(choice, seq), Option(Alternative(Text('?'), Text('*'), Text('+'))))
    contentspec = Alternative(Text('EMPTY'), Text('ANY'), Mixed, children)
    elementdecl = Series(Text('<!ELEMENT'), S, Name, S, contentspec, Option(S), Text('>'))
    AttType = Alternative(StringType, TokenizedType, EnumeratedType)
    VersionInfo = Series(S, Text('version'), Eq, Alternative(Series(Text("\'"), VersionNum, Text("\'")), Series(Text('"'), VersionNum, Text('"'))))
    AttDef = Series(S, Name, S, AttType, S, DefaultDecl)
    ETag = Series(Text('</'), Name, Option(S), Text('>'))
    Attribute = Series(Name, Eq, AttValue)
    EmptyElemTag = Series(Text('<'), Name, ZeroOrMore(Series(S, Attribute)), Option(S), Text('/>'))
    Ignore = Series(NegativeLookahead(Series(ZeroOrMore(Char), Alternative(Text('<!['), Text(']]>')), ZeroOrMore(Char))), ZeroOrMore(Char))
    TextDecl = Series(Text('<?xml'), Option(VersionInfo), EncodingDecl, Option(S), Text('?>'))
    AttlistDecl = Series(Text('<!ATTLIST'), S, Name, ZeroOrMore(AttDef), Option(S), Text('>'))
    PEDecl = Series(Text('<!ENTITY'), S, Text('%'), S, Name, S, PEDef, Option(S), Text('>'))
    DeclSep = Alternative(PEReference, S)
    EntityDef = Alternative(EntityValue, Series(ExternalID, Option(NDataDecl)))
    Comment = Series(Text('<!--'), ZeroOrMore(Alternative(Series(NegativeLookahead(Text('-')), Char), Series(Text('-'), Series(NegativeLookahead(Text('-')), Char)))), Text('-->'))
    extParsedEnt = Series(Option(TextDecl), content)
    SDDecl = Series(S, Text('standalone'), Eq, Alternative(Series(Text("\'"), Alternative(Text('yes'), Text('no')), Text("\'")), Series(Text('"'), Alternative(Text('yes'), Text('no')), Text('"'))))
    extSubset = Series(Option(TextDecl), extSubsetDecl)
    XMLDecl = Series(Text('<?xml'), VersionInfo, Option(EncodingDecl), Option(SDDecl), Option(S), Text('?>'))
    GEDecl = Series(Text('<!ENTITY'), S, Name, S, EntityDef, Option(S), Text('>'))
    CDEnd = Text(']]>')
    CData = Series(NegativeLookahead(Series(ZeroOrMore(Char), Text(']]>'), ZeroOrMore(Char))), ZeroOrMore(Char))
    CDStart = Text('<![CDATA[')
    CDSect = Series(CDStart, CData, CDEnd)
    PITarget = Series(NegativeLookahead(Series(Alternative(Text('X'), Text('x')), Alternative(Text('M'), Text('m')), Alternative(Text('L'), Text('l')))), Name)
    PI = Series(Text('<?'), PITarget, Option(Series(S, Series(NegativeLookahead(Series(ZeroOrMore(Char), Text('?>'), ZeroOrMore(Char))), ZeroOrMore(Char)))), Text('?>'))
    Misc = Alternative(Comment, PI, S)
    CharData = Series(NegativeLookahead(Series(ZeroOrMore(RegExp('[^<&]')), Text(']]>'), ZeroOrMore(RegExp('[^<&]')))), ZeroOrMore(RegExp('[^<&]')))
    EntityDecl = Alternative(GEDecl, PEDecl)
    markupdecl = Alternative(elementdecl, AttlistDecl, EntityDecl, NotationDecl, PI, Comment)
    intSubset = ZeroOrMore(Alternative(markupdecl, DeclSep))
    STag = Series(Text('<'), Name, ZeroOrMore(Series(S, Attribute)), Option(S), Text('>'))
    doctypedecl = Series(Text('<!DOCTYPE'), S, Name, Option(Series(S, ExternalID)), Option(S), Option(Series(Text('['), intSubset, Text(']'), Option(S))), Text('>'))
    prolog = Series(Option(XMLDecl), ZeroOrMore(Misc), Option(Series(doctypedecl, ZeroOrMore(Misc))))
    Nmtokens = Series(Nmtoken, ZeroOrMore(Series(RegExp('\x20'), Nmtoken)))
    Names = Series(Name, ZeroOrMore(Series(RegExp('\x20'), Name)))
    ignoreSectContents.set(Series(Ignore, ZeroOrMore(Series(Text('<!['), ignoreSectContents, Text(']]>'), Ignore))))
    cp.set(Series(Alternative(Name, choice, seq), Option(Alternative(Text('?'), Text('*'), Text('+')))))
    content.set(Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData)))))
    element.set(Alternative(EmptyElemTag, Series(STag, content, ETag)))
    extSubsetDecl.set(ZeroOrMore(Alternative(markupdecl, conditionalSect, DeclSep)))
    document = Series(prolog, element, ZeroOrMore(Misc))
    root__ = document
    

_raw_grammar = ThreadLocalSingletonFactory(XML_W3C_SPECGrammar)

def get_grammar() -> XML_W3C_SPECGrammar:
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
    
def parse_XML_W3C_SPEC(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match=complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

XML_W3C_SPEC_AST_transformation_table = {
    # AST Transformations for the XML_W3C_SPEC-grammar
    # "<": flatten
    # "*": replace_by_single_child
    # ">: []
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
}


def XML_W3C_SPECTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=XML_W3C_SPEC_AST_transformation_table.copy())


get_transformer = ThreadLocalSingletonFactory(XML_W3C_SPECTransformer, ident=1)


def transform_XML_W3C_SPEC(cst):
    return get_transformer()(cst)


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


get_compiler = ThreadLocalSingletonFactory(XML_W3C_SPECCompiler, ident=1)


def compile_XML_W3C_SPEC(ast):
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
    else:
        return repr(result)


def process_file(source: str, result_filename: str = '') -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors of warnings occurred.
    """
    source_filename = source if is_filename(source) else ''
    result, errors = compile_src(source)
    if not has_errors(errors, FATAL):
        if os.path.abspath(source_filename) != os.path.abspath(result_filename):
            with open(result_filename, 'w') as f:
                f.write(serialize_result(result))
        else:
            errors.append(Error('Source and destination have the same name "%s"!'
                                % result_filename, 0, FATAL))
    if errors:
        err_ext = '_ERRORS.txt' if has_errors(errors, ERROR) else '_WARNINGS.txt'
        err_filename = os.path.splitext(result_filename)[0] + err_ext
        with open(err_filename, 'w') as f:
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


if __name__ == "__main__":
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
    parser = ArgumentParser(description="Parses a XML_W3C_SPEC-file and shows its syntax-tree.")
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
