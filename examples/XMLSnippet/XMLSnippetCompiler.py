#!/usr/bin/python

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys

sys.path.append(r'C:\Users\di68kap\PycharmProjects\DHParser')

try:
    import regex as re
except ImportError:
    import re
from DHParser import logging, is_filename, load_if_file, Grammar, Compiler, nil_preprocessor, \
    PreprocessorToken, Whitespace, DropWhitespace, DropToken, flatten_anonymous_nodes, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, Unordered, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, counterpart, accumulate, PreprocessorFunc, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    remove_expendables, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, is_empty, \
    is_expendable, collapse, collapse_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_nodes, remove_content, remove_brackets, replace_parser, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, remove_first, remove_last, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, GLOBALS


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
    source_hash__ = "d3c46a530b258f47d6ae47ccf8297702"
    static_analysis_pending__ = False
    parser_initialization__ = ["upon instantiation"]
    resume_rules__ = {}
    COMMENT__ = r'//'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    dwsp__ = DropWhitespace(WSP_RE__)
    wsp__ = Whitespace(WSP_RE__)
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
    intSubset = RegExp('(?:(?!\\][^\\]])[^<&])+')
    ExternalID = Series(DropToken('SYSTEM'), S, SystemLiteral, mandatory=1)
    doctypedecl = Series(DropToken('<!DOCTYPE'), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Option(Series(DropToken('['), intSubset, DropToken(']'), dwsp__)), DropToken('>'))
    No = Token('no')
    Yes = Token('yes')
    SDDecl = Series(dwsp__, DropToken('standalone'), dwsp__, DropToken('='), dwsp__, Alternative(Alternative(Series(DropToken("'"), Yes), Series(No, DropToken("'"))), Alternative(Series(DropToken('"'), Yes), Series(No, DropToken('"')))))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl = Series(dwsp__, DropToken('encoding'), dwsp__, DropToken('='), dwsp__, Alternative(Series(DropToken("'"), EncName, DropToken("'")), Series(DropToken('"'), EncName, DropToken('"'))))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo = Series(dwsp__, DropToken('version'), dwsp__, DropToken('='), dwsp__, Alternative(Series(DropToken("'"), VersionNum, DropToken("'")), Series(DropToken('"'), VersionNum, DropToken('"'))))
    XMLDecl = Series(DropToken('<?xml'), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, DropToken('?>'))
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    document = Series(prolog, element, Option(Misc), EOF)
    root__ = document
    
def get_grammar() -> XMLSnippetGrammar:
    global GLOBALS
    try:
        grammar = GLOBALS.XMLSnippet_00000001_grammar_singleton
    except AttributeError:
        GLOBALS.XMLSnippet_00000001_grammar_singleton = XMLSnippetGrammar()
        if hasattr(get_grammar, 'python_src__'):
            GLOBALS.XMLSnippet_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = GLOBALS.XMLSnippet_00000001_grammar_singleton
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

XMLSnippet_AST_transformation_table = {
    # AST Transformations for the XMLSnippet-grammar
    "<": flatten_anonymous_nodes,
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


def XMLSnippetTransform() -> TransformationDict:
    return partial(traverse, processing_table=XMLSnippet_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    try:
        transformer = GLOBALS.XMLSnippet_1_transformer_singleton
    except AttributeError:
        GLOBALS.XMLSnippet_1_transformer_singleton = XMLSnippetTransform()
        transformer = GLOBALS.XMLSnippet_1_transformer_singleton
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

    def _reset(self):
        super()._reset()
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
    try:
        compiler = GLOBALS.XMLSnippet_1_compiler_singleton
    except AttributeError:
        GLOBALS.XMLSnippet_1_compiler_singleton = XMLSnippetCompiler()
        compiler = GLOBALS.XMLSnippet_1_compiler_singleton
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
        result = compile_source(source, get_preprocessor(),
                                get_grammar(),
                                get_transformer(), compiler)
    return result


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Compiler.py', '.ebnf')
    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False,
                                  notify=lambda:print('recompiling ' + grammar_path)):
            error_file = os.path.basename(__file__).replace('Compiler.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
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
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: XMLSnippetCompiler.py [FILENAME]")
