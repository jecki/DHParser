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

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

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
    TOKEN_PTYPE, remove_nodes, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    chain, get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_parent


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def XMLSnippetPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return XMLSnippetPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class XMLSnippetGrammar(Grammar):
    r"""Parser for a XMLSnippet source file.
    """
    Name = Forward()
    element = Forward()
    source_hash__ = "251e31d28ec63ce674dc7a67686acaf1"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = [True]
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
    TagName = Capture(Name)
    emptyElement = Series(Drop(Token('<')), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Token('/>')))
    ETag = Series(Drop(Token('</')), Pop(TagName), dwsp__, Drop(Token('>')), mandatory=1)
    STag = Series(Drop(Token('<')), TagName, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Token('>')))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    intSubset = RegExp('(?:(?!\\][^\\]])[^<&])+')
    ExternalID = Series(Drop(Token('SYSTEM')), S, SystemLiteral, mandatory=1)
    doctypedecl = Series(Drop(Token('<!DOCTYPE')), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Option(Series(Drop(Token('[')), intSubset, Drop(Token(']')), dwsp__)), Drop(Token('>')))
    No = Token('no')
    Yes = Token('yes')
    SDDecl = Series(dwsp__, Drop(Token('standalone')), dwsp__, Drop(Token('=')), dwsp__, Alternative(Alternative(Series(Drop(Token("'")), Yes), Series(No, Drop(Token("'")))), Alternative(Series(Drop(Token('"')), Yes), Series(No, Drop(Token('"'))))))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl = Series(dwsp__, Drop(Token('encoding')), dwsp__, Drop(Token('=')), dwsp__, Alternative(Series(Drop(Token("'")), EncName, Drop(Token("'"))), Series(Drop(Token('"')), EncName, Drop(Token('"')))))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo = Series(dwsp__, Drop(Token('version')), dwsp__, Drop(Token('=')), dwsp__, Alternative(Series(Drop(Token("'")), VersionNum, Drop(Token("'"))), Series(Drop(Token('"')), VersionNum, Drop(Token('"')))))
    XMLDecl = Series(Drop(Token('<?xml')), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, Drop(Token('?>')))
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    document = Series(prolog, element, Option(Misc), EOF)
    root__ = document
    

def get_grammar() -> XMLSnippetGrammar:
    """Returns a thread/process-exclusive XMLSnippetGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.XMLSnippet_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.XMLSnippet_00000001_grammar_singleton = XMLSnippetGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.XMLSnippet_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.XMLSnippet_00000001_grammar_singleton
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

XMLSnippet_AST_transformation_table = {
    # AST Transformations for the XMLSnippet-grammar
    "<": flatten,
    "document": [],
    "prolog": [],
    "XMLDecl": [],
    "VersionInfo": [],
    "VersionNum": [],
    "EncodingDecl": [],
    "EncName": [],
    "SDDecl": [],
    "Yes": [],
    "No": [],
    "doctypedecl": [],
    "ExternalID": [],
    "intSubset": [],
    "element": [replace_or_reduce],
    "STag": [],
    "ETag": [],
    "emptyElement": [],
    "TagName": [],
    "Attribute": [],
    "content": [],
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
    "CharRef": [replace_or_reduce],
    "Chars": [],
    "Char": [],
    "S": [],
    "EOF": [],
    ":Token": reduce_single_child,
    "*": replace_by_single_child
}


def CreateXMLSnippetTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=XMLSnippet_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.XMLSnippet_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.XMLSnippet_00000001_transformer_singleton = CreateXMLSnippetTransformer()
        transformer = THREAD_LOCALS.XMLSnippet_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class XMLSnippetCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a XMLSnippet source file.
    """

    def __init__(self):
        super(XMLSnippetCompiler, self).__init__()

    def reset(self):
        super().reset()
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

    # def on_Yes(self, node):
    #     return node

    # def on_No(self, node):
    #     return node

    # def on_doctypedecl(self, node):
    #     return node

    # def on_ExternalID(self, node):
    #     return node

    # def on_intSubset(self, node):
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


def get_compiler() -> XMLSnippetCompiler:
    """Returns a thread/process-exclusive XMLSnippetCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.XMLSnippet_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.XMLSnippet_00000001_compiler_singleton = XMLSnippetCompiler()
        compiler = THREAD_LOCALS.XMLSnippet_00000001_compiler_singleton
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
        print("Usage: XMLSnippetParser.py [FILENAME]")
