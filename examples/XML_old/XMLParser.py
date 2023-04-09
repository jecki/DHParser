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
from typing import List

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
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, PLACEHOLDER, \
    merge_adjacent, collapse, collapse_children_if, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, any_of, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory, TreeReduction, CombinedParser, \
    apply_unless, ERROR


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

class XMLGrammar(Grammar):
    r"""Parser for a XML source file.
    """
    element = Forward()
    source_hash__ = "eee8012c222c481157040ef9d5d34d56"
    disposable__ = re.compile('Misc$|NameStartChar$|NameChars$|CommentChars$|PubidChars$|PubidCharsSingleQuoted$|VersionNum$|EncName$|Reference$|CData$|EOF$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = NegativeLookahead(RegExp('.'))
    CharRef = Alternative(Series(Drop(Text('&#')), RegExp('[0-9]+'), Drop(Text(';'))), Series(Drop(Text('&#x')), RegExp('[0-9a-fA-F]+'), Drop(Text(';'))))
    CommentChars = RegExp('(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    PIChars = RegExp('(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CData = RegExp('(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CharData = RegExp('(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    CDSect = Series(Drop(Text('<![CDATA[')), CData, Drop(Text(']]>')))
    NameStartChar = RegExp('(?x)_|:|[A-Z]|[a-z]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF]')
    NameChars = RegExp('(?x)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n                   |\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF])+')
    Comment = Series(Drop(Text('<!--')), ZeroOrMore(Alternative(CommentChars, RegExp('-(?!-)'))), dwsp__, Drop(Text('-->')))
    Name = Series(NameStartChar, Option(NameChars))
    PITarget = Series(NegativeLookahead(RegExp('X|xM|mL|l')), Name)
    PI = Series(Drop(Text('<?')), PITarget, RegExp('[~ PIChars]'), Drop(Text('?>')))
    Misc = OneOrMore(Alternative(Comment, PI, dwsp__))
    EntityRef = Series(Drop(Text('&')), Name, Drop(Text(';')))
    Reference = Alternative(EntityRef, CharRef)
    PubidLiteral = Alternative(Series(Drop(Text('"')), Option(PubidChars), Drop(Text('"'))), Series(Drop(Text("\'")), Option(PubidCharsSingleQuoted), Drop(Text("\'"))))
    SystemLiteral = Alternative(Series(Drop(Text('"')), RegExp('[^"]*'), Drop(Text('"'))), Series(Drop(Text("\'")), RegExp("[^']*"), Drop(Text("\'"))))
    AttValue = Alternative(Series(Drop(Text('"')), ZeroOrMore(Alternative(RegExp('[^<&"]+'), Reference)), Drop(Text('"'))), Series(Drop(Text("\'")), ZeroOrMore(Alternative(RegExp("[^<&']+"), Reference)), Drop(Text("\'"))))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Attribute = Series(Name, dwsp__, Drop(Text('=')), dwsp__, AttValue, mandatory=2)
    emptyElement = Series(Drop(Text('<')), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Text('/>')))
    ETag = Series(Drop(Text('</')), Name, dwsp__, Drop(Text('>')), mandatory=1)
    STag = Series(Drop(Text('<')), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Drop(Text('>')))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    ExternalID = Alternative(Series(Drop(Text('SYSTEM')), dwsp__, SystemLiteral, mandatory=1), Series(Drop(Text('PUBLIC')), dwsp__, PubidLiteral, dwsp__, SystemLiteral, mandatory=1))
    doctypedecl = Series(Drop(Text('<!DOCTYPE')), dwsp__, Name, RegExp('[~ ExternalID]'), dwsp__, Drop(Text('>')), mandatory=2)
    SDDecl = Series(dwsp__, Drop(Text('standalone')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), Alternative(Text("yes"), Text("no")), Drop(Text("\'"))), Series(Drop(Text('"')), Alternative(Text("yes"), Text("no")), Drop(Text('"')))))
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl = Series(dwsp__, Drop(Text('encoding')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), EncName, Drop(Text("\'"))), Series(Drop(Text('"')), EncName, Drop(Text('"')))))
    VersionInfo = Series(dwsp__, Drop(Text('version')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), VersionNum, Drop(Text("\'"))), Series(Drop(Text('"')), VersionNum, Drop(Text('"')))))
    XMLDecl = Series(Drop(Text('<?xml')), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, Drop(Text('?>')))
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    document = Series(prolog, element, Option(Misc), EOF)
    root__ = TreeReduction(document, CombinedParser.MERGE_TREETOPS)
    

_raw_grammar = ThreadLocalSingletonFactory(XMLGrammar)

def get_grammar() -> XMLGrammar:
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
    
def parse_XML(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match=complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


XML_AST_transformation_table = {
    # AST Transformations for the XML-grammar
    # "<": [flatten, remove_empty, remove_anonymous_tokens, remove_whitespace, remove_children("S")],
    "document": [flatten(lambda context: context[-1].name == 'prolog', recursive=False)],
    "VersionInfo": [reduce_single_child],
    "EncodingDecl": [reduce_single_child],
    "element": [flatten, replace_by_single_child],
    "content": [flatten],
    "SystemLiteral": [reduce_single_child],
    "PubidLiteral": [reduce_single_child],
    "Reference": [replace_by_single_child],
    "EntityRef": [reduce_single_child],
    "Name": [collapse],
    "Misc": [replace_by_single_child],
    "Comment": [collapse],
    "PITarget": [reduce_single_child],
    "CDSect": [reduce_single_child],
    "CharRef": [replace_or_reduce],
    # "*": replace_by_single_child
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


ERROR_TAG_NAME_MISMATCH = ErrorCode(2000)
ERROR_VALUE_CONSTRAINT_VIOLATION = ErrorCode(2010)
ERROR_VALIDITY_CONSTRAINT_VIOLATION = ErrorCode(2020)
ERROR_WELL_FORMEDNESS_CONSTRAINT_VIOLATION = ErrorCode(2030)


class XMLCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a XML source file.
    """

    def __init__(self):
        super(XMLCompiler, self).__init__()
        self.cleanup_whitespace = True  # remove empty CharData from mixed elements

    def reset(self):
        super().reset()
        self.preserve_whitespace = False

    def extract_attributes(self, node_sequence):
        attributes = collections.OrderedDict()
        for node in node_sequence:
            if node.name == "Attribute":
                assert node[0].name == "Name", node.as_sexpr()
                assert node[1].name == "AttValue", node.as_sxpr()
                attributes[node[0].content] = node[1].content
        return attributes

    def constraint(self, node, condition, err_msg, error_code = ERROR):
        """If `condition` is False an error is issued."""
        if not condition:
            self.tree.new_error(node, err_msg, error_code)

    def value_constraint(self, node, value, allowed):
        """If value is not in allowed, an error is issued."""
        self.constraint(
            node,
            value in allowed,
            'Invalid value "%s" for "standalone"! Must be one of %s.' % (value, str(allowed)),
            ERROR_VALUE_CONSTRAINT_VIOLATION)

    def on_document(self, node):
        self.tree.string_tags.update({'CharData', 'document'})
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

    def on_element(self, node):
        stag = node['STag']
        tag_name = stag['Name'].content
        self.constraint(
            node,
            tag_name == node['ETag']['Name'].content,
            f'Starting tag name "{tag_name}" does not match ending '
            f'tag name "{node["ETag"]["Name"].content}"',
            ERROR_WELL_FORMEDNESS_CONSTRAINT_VIOLATION)
        save_preserve_ws = self.preserve_whitespace
        self.preserve_whitespace |= tag_name in self.tree.inline_tags
        attributes = self.extract_attributes(stag.children)
        if attributes:
            node.attr.update(attributes)
            self.preserve_whitespace |= attributes.get('xml:space', '') == 'preserve'
        node.name = tag_name
        xml_content = tuple(self.compile(nd) for nd in node.get('content', PLACEHOLDER).children)
        if len(xml_content) == 1:
            if xml_content[0].name == "CharData":
                # reduce single CharData children
                xml_content = xml_content[0].content
        elif self.cleanup_whitespace and not self.preserve_whitespace:
            # remove CharData that consists only of whitespace from mixed elements
            xml_content = tuple(child for child in xml_content
                                if child.name != "CharData" or child.content.strip() != '')
        self.preserve_whitespace = save_preserve_ws
        node.result = xml_content
        return node

    def on_emptyElement(self, node):
        attributes = self.extract_attributes(node.children)
        if attributes:
            node.attr.update(attributes)
        node.name = node['Name'].content
        node.result = ''
        self.tree.empty_tags.add(node.name)
        return node


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
        set_config_value('log_syntax_trees', {'cst', 'ast'})
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
