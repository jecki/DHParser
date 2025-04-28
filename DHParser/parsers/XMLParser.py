#!/usr/bin/env python3

from __future__ import annotations

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
from functools import partial
import os
import sys
from typing import Tuple, List, Union, Any, Optional, Callable, Set, Dict

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, os.path.pardir, os.path.pardir))
if scriptpath and scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser.compile import Compiler, compile_source
from DHParser.pipeline import full_pipeline, Junction, PseudoJunction, create_preprocess_junction, \
    create_parser_junction, create_junction
from DHParser.configuration import set_config_value, get_config_value, access_thread_locals, \
    access_presets, finalize_presets, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN, \
    add_config_values
from DHParser import dsl
from DHParser.dsl import recompile_grammar, never_cancel, PseudoJunction
from DHParser.ebnf import grammar_changed
from DHParser.error import ErrorCode, Error, canonical_error_strings, has_errors, NOTICE, \
    WARNING, ERROR, FATAL
from DHParser.log import start_logging, suspend_logging, resume_logging
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, RootNode, ZOMBIE_TAG, \
    CHAR_REF_PTYPE, ENTITY_REF_PTYPE, LEAF_PTYPES, EMPTY_NODE
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, mixin_comment, \
    last_value, matching_bracket, optional_last_value, SmartRE
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc, PreprocessorResult, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors
from DHParser.toolkit import is_filename, load_if_file, cpu_count, RX_NEVER_MATCH, \
    ThreadLocalSingletonFactory, expand_table, line_col, INFINITE
from DHParser.trace import set_tracer, resume_notices_on, trace_history
from DHParser.transform import is_empty, remove_if, TransformationDict, TransformerFunc, \
    transformation_factory, remove_children_if, move_fringes, normalize_whitespace, \
    is_anonymous, name_matches, reduce_single_child, replace_by_single_child, replace_or_reduce, \
    remove_whitespace, replace_by_children, remove_empty, remove_tokens, flatten, all_of, \
    any_of, transformer, merge_adjacent, collapse, collapse_children_if, transform_result, \
    remove_children, remove_content, remove_brackets, change_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, add_error, error_on, \
    left_associative, lean_left, node_maker, has_descendant, neg, has_ancestor, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, has_children, apply_unless, apply_ifelse
from DHParser import parse as parse_namespace__


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN 
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def XMLTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as XMLGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, '#.*')
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(XMLTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory)


def preprocess_XML(source):
    return get_preprocessor()(source)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class XMLGrammar(Grammar):
    r"""Parser for an XML source file.
    """
    element = Forward()
    source_hash__ = "44aaa6af7a9e915d4166bf64e3810265"
    early_tree_reduction__ = CombinedParser.MERGE_TREETOPS
    disposable__ = re.compile('(?:PubidCharsSingleQuoted$|Misc$|VersionNum$|PubidChars$|EncName$|EOF$|tagContent$|XmlPIAtts$|BOM$|NameChars$|Reference$|NameStartChar$|CData$|prolog$|CommentChars$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'tagContent': [('', "syntax error in tag-name of opening or empty tag:  {1}")],
                        'ETag': [('', "syntax error in tag-name of closing tag:  {1}")],
                        'Attribute': [('', "syntax error in attribute definition:  {1}")]}
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(SmartRE(f'(?!.)', '!/./'))
    S = RegExp('\\s+')
    Char = RegExp('(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FF'
       'FF])+')
    CharRef = SmartRE(f'(?:\\&\\#)([0-9]+)(?:;)|(?:\\&\\#x)([0-9a-fA-F]+)(?:;)', "'&#' /[0-9]+/ ';'|'&#x' /[0-9a-fA-F]+/ ';'")
    CommentChars = RegExp('(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-'
       '\\U0010FFFF]))+')
    PIChars = RegExp('(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U0001000'
       '0-\\U0010FFFF]))+')
    CData = RegExp('(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U0001'
       '0000-\\U0010FFFF]))+')
    CharData = RegExp('(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    CDSect = Series(Drop(Text('<![CDATA[')), CData, Drop(Text(']]>')))
    PredefEntityRef = SmartRE(f'\\&amp;|\\&lt;|\\&gt;|\\&quot;|\\&apos;', '"&amp;"|"&lt;"|"&gt;"|"&quot;"|"&apos;"')
    NameChars = RegExp('(?x)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n'
                          '|\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n'
                          '|[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n'
                          '|[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n'
                          '|[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n'
                          '|[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n'
                          '|[\\U00010000-\\U000EFFFF])+')
    NameStartChar = RegExp('(?x)_|:|[A-Z]|[a-z]\n'
                          '|[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n'
                          '|[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n'
                          '|[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n'
                          '|[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n'
                          '|[\\U00010000-\\U000EFFFF]')
    PseudoAttValue = Alternative(Series(Drop(Text('"')), ZeroOrMore(Alternative(RegExp('[^"<&]+'), CharRef, PredefEntityRef)), Drop(Text('"'))), Series(Drop(Text("\'")), ZeroOrMore(Alternative(RegExp("[^'<&]+"), CharRef, PredefEntityRef)), Drop(Text("\'"))))
    Name = Series(NameStartChar, Option(NameChars))
    PseudoAtt = Series(Name, dwsp__, Drop(Text("=")), dwsp__, PseudoAttValue, mandatory=2)
    Comment = Series(Drop(Text('<!--')), ZeroOrMore(Alternative(CommentChars, RegExp('-(?!-)'))), dwsp__, Drop(Text('-->')))
    XmlPIAtts = Series(NegativeLookahead(Series(Option(Char), Drop(Text("?>")), Option(Char))), ZeroOrMore(Series(dwsp__, PseudoAtt)), dwsp__)
    PITarget = Series(SmartRE(f'(?![Xx][Mm][Ll])', '!/[Xx][Mm][Ll]/'), Name)
    PI = Series(Drop(Text('<?')), PITarget, Option(Series(dwsp__, PIChars)), Drop(Text('?>')), mandatory=1)
    UnknownXmlPI = Series(Drop(Text("<?")), Drop(RegExp('[Xx][Mm][Ll]-?')), Name, XmlPIAtts, Drop(Text("?>")), mandatory=3)
    EntityRef = Series(Drop(Text('&')), Name, Drop(Text(';')))
    Reference = Alternative(EntityRef, CharRef)
    XmlModelPI = Series(Drop(Text("<?xml-model")), XmlPIAtts, Drop(Text("?>")), mandatory=1)
    StyleSheetPI = Series(Drop(Text("<?xml-stylesheet")), XmlPIAtts, Drop(Text("?>")), mandatory=1)
    PubidLiteral = Alternative(Series(Drop(Text('"')), Option(PubidChars), Drop(Text('"'))), Series(Drop(Text("\'")), Option(PubidCharsSingleQuoted), Drop(Text("\'"))))
    SystemLiteral = SmartRE(f'(?:")([^"]*)(?:")|(?:\')([^\']*)(?:\')', '\'"\' /[^"]*/ \'"\'|"\'" /[^\']*/ "\'"')
    AttValue = Alternative(Series(Drop(Text('"')), ZeroOrMore(Alternative(RegExp('[^<&"]+'), Reference)), Drop(Text('"'))), Series(Drop(Text("\'")), ZeroOrMore(Alternative(RegExp("[^<&']+"), Reference)), Drop(Text("\'"))))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Misc = Series(dwsp__, OneOrMore(Alternative(Series(Comment, dwsp__), Series(StyleSheetPI, dwsp__), Series(XmlModelPI, dwsp__), Series(UnknownXmlPI, dwsp__), Series(PI, dwsp__))))
    Attribute = Series(Name, dwsp__, Drop(Text('=')), dwsp__, AttValue, mandatory=2)
    ETag = Series(Drop(Text('</')), Name, dwsp__, Drop(Text('>')), mandatory=1)
    tagContent = Series(SmartRE(f'(?![/!?])', '!/[\\/!?]/'), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, SmartRE(f'(?=>|/>)', "&'>'|'/>'"), mandatory=1)
    STag = Series(Drop(Text('<')), tagContent, Drop(Text('>')))
    emptyElement = Series(Drop(Text('<')), tagContent, Drop(Text('/>')))
    BOM = Drop(RegExp('[\\ufeff]|[\\ufffe]|[\\u0000feff]|[\\ufffe0000]'))
    ExternalID = Alternative(Series(Drop(Text('SYSTEM')), dwsp__, SystemLiteral, mandatory=1), Series(Drop(Text('PUBLIC')), dwsp__, PubidLiteral, dwsp__, SystemLiteral, mandatory=1))
    doctypedecl = Series(Drop(Text('<!DOCTYPE')), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Drop(Text('>')), mandatory=2)
    SDDecl = SmartRE(f'{WSP_RE__}standalone{WSP_RE__}={WSP_RE__}(?:(?:(?:\')(?P<:Text>yes|no)(?:\'))|(?:(?:")(?P<:Text>yes|no)(?:")))', '~ \'standalone\' ~ \'=\' ~ "\'" `yes`|`no` "\'"|\'"\' `yes`|`no` \'"\'')
    EncName = RegExp('[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl = Series(dwsp__, Drop(Text('encoding')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), EncName, Drop(Text("\'"))), Series(Drop(Text('"')), EncName, Drop(Text('"')))))
    VersionNum = RegExp('[0-9]+\\.[0-9]+')
    VersionInfo = Series(dwsp__, Drop(Text('version')), dwsp__, Drop(Text('=')), dwsp__, Alternative(Series(Drop(Text("\'")), VersionNum, Drop(Text("\'"))), Series(Drop(Text('"')), VersionNum, Drop(Text('"')))))
    XMLDecl = Series(Drop(Text('<?xml')), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, Drop(Text('?>')), mandatory=1)
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), dwsp__, Option(Series(doctypedecl, Option(Misc), dwsp__)))
    element.set(Alternative(emptyElement, Series(STag, content, ETag, mandatory=1)))
    document = Series(Option(BOM), prolog, element, Option(Misc), dwsp__, EOF, mandatory=2)
    resume_rules__ = {'tagContent': [re.compile(r'(?=>|/>)')],
                      'ETag': [re.compile(r'(?=>)')],
                      'Attribute': [re.compile(r'(?=>|/>)')]}
    root__ = document
        
parsing: PseudoJunction = create_parser_junction(XMLGrammar)
get_grammar = parsing.factory # for backwards compatibility, only


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


XML_PTYPE = ":XML"

WARNING_AMBIGUOUS_EMPTY_ELEMENT = ErrorCode(205)

ERROR_TAG_NAME_MISMATCH = ErrorCode(2000)
ERROR_VALUE_CONSTRAINT_VIOLATION = ErrorCode(2010)
ERROR_VALIDITY_CONSTRAINT_VIOLATION = ErrorCode(2020)


class XMLTransformer(Compiler):
    """Compiler for the abstract-syntax-tree of a XML source file.

    As of now, Cdata-sections and document-type definition will be parsed, but
    not transformed into an AST and may not be re-serialized properly with Node.as_xml()
    """
    def __init__(self):
        super().__init__()
        self.expendables = set()  # {'CDSect', 'doctypedecl', 'XmlModelPI', 'StyleSheetPI', 'UnknownXmlPI', 'PI'}

    def reset(self):
        super().reset()
        self.preserve_whitespace = get_config_value("XML.preserve_whitespace", False)
        self.non_empty_tags: Set[str] = set()

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "CST", f"Source stage `CST` expected, `but `{root.stage}` found."
        root.stage = "AST"

    def finalize(self, result: Any) -> Any:
        return result

    def extract_attributes(self, node_sequence):
        attributes = collections.OrderedDict()
        for node in node_sequence:
            if node.name in ("Attribute", "PseudoAtt"):
                assert node[0].name == "Name", node.as_sexpr()
                # assert node[1].name in ("AttValue", "PseudoAttValue"), node.as_sxpr()
                attributes[node[0].content] = node[1].content.replace('\n', '')
        return attributes

    def value_constraint(self, node, value, allowed):
        """If value is not in allowed, an error is issued."""
        if not value in allowed:
            self.tree.new_error(node,
                                'Invalid value "%s" for "standalone"! Must be one of %s.' \
                                % (value, str(allowed)), ERROR_VALUE_CONSTRAINT_VIOLATION)

    def on_document(self, node):
        node.name = XML_PTYPE
        self.tree.string_tags.update(LEAF_PTYPES)
        self.tree.empty_tags.update({'?xml'})
        node.result = tuple(self.compile(nd) for nd in node.children
                            if nd.name not in self.expendables)
        strip(self.path, lambda p: is_one_of(p, self.expendables | {'S'}))
        replace_by_single_child(self.path)
        return node

    def on_prolog(self, node):
        node.result = tuple(self.compile(nd) for nd in node.children
                            if nd.name not in self.expendables)
        return node

    def on_CharData(self, node):
        node.name = TOKEN_PTYPE
        return node

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
        node.name = '?xml'  # node.parser = self.get_parser('?xml')
        return node

    def XmlPI(self, node) -> Node:
        attributes = self.extract_attributes(node.children)
        if attributes:
            node.attr.update(attributes)
        node.result = ''
        return node

    def on_XmlModelPI(self, node) -> Node:
        node.name = "?xml-model"
        node = self.XmlPI(node)
        return node

    def on_StyleSheetPI(self, node) -> Node:
        node.name = "?xml-stylesheet"
        node = self.XmlPI(node)
        return node

    def on_UnknownXmlPI(self, node) -> Node:
        node.name = f"?xml-{node['Name'].content}"
        node = self.XmlPI(node)
        return node

    def on_PI(self, node) -> Node:
        target = node['PITarget'].content
        instructions = node.get('PIChars', EMPTY_NODE).content
        node.name = f'?{target}'
        if instructions:
            node.attr['instructions__'] = instructions
        node.result = ''
        return node

    def on_doctypedecl(self, node) -> Node:
        return node

    def on_CDSect(self, node) -> Node:
        return node

    def on_content(self, node) -> Union[Tuple[Node, ...], str]:
        xml_content: List[Node] = []
        preserve_ws = self.preserve_whitespace
        for nd in node.children:
            if nd.name in self.expendables:  continue
            child = self.compile(nd)
            if child.name != TOKEN_PTYPE:
                xml_content.append(child)
            elif preserve_ws or child.content.strip() != '':
                if xml_content and xml_content[-1].name == TOKEN_PTYPE:
                    xml_content[-1].result = xml_content[-1].content + child.content
                else:
                    xml_content.append(child)
        if len(xml_content) == 1 and xml_content[0].name == TOKEN_PTYPE:
            return xml_content[0].content
        return tuple(xml_content)

    def on_element(self, node):
        if len(node.children) == 1:
            try:
                return self.on_emptyElement(node['emptyElement'])
            except KeyError:  # in case of a malformed tree...
                return node[0]
        stag = node['STag']
        etag = node.get('ETag', stag)  # in case of malformed XML this could be missing
        tag_name = stag['Name'].content

        if tag_name != etag['Name'].content:
            l, c = line_col(self.tree.lbreaks, etag['Name'].pos)
            self.tree.new_error(stag['Name'],
                                f'Starting tag name "{tag_name}" does not match ending '
                                f'tag name "{etag["Name"].content}" at {l}:{c}',
                                ERROR_TAG_NAME_MISMATCH)

        if tag_name in self.tree.empty_tags \
                and tag_name not in self.non_empty_tags:  # warn only once!
            self.tree.new_error(node,
                                f'Tag-name "{tag_name}" has already been used for an empty-tag '
                                f'<{tag_name}/> earlier. This is considered bad XML-practice!',
                                WARNING_AMBIGUOUS_EMPTY_ELEMENT)

        self.non_empty_tags.add(tag_name)
        save_preserve_ws = self.preserve_whitespace
        self.preserve_whitespace |= tag_name in self.tree.inline_tags
        attributes = self.extract_attributes(stag.children)
        if attributes:
            node.attr.update(attributes)
            self.preserve_whitespace |= attributes.get('xml:space', '') == 'preserve'
        node.name = tag_name
        node.result = self.compile(node['content']) if 'content' in node else tuple()
        self.preserve_whitespace = save_preserve_ws
        return node

    def on_emptyElement(self, node):
        attributes = self.extract_attributes(node.children)
        if attributes:
            node.attr.update(attributes)
        node.name = node['Name'].content
        node.result = ''

        if node.name in self.non_empty_tags \
                and node.name not in self.tree.empty_tags:  # warn only once!
            self.tree.new_error(node,
                                f'Tag-name "{node.name}" has already been used for a non empty-tag '
                                f'<{node.name}> ... </{node.name}> earlier. This is considered bad XML-practice!',
                                WARNING_AMBIGUOUS_EMPTY_ELEMENT)

        self.tree.empty_tags.add(node.name)
        return node

    def on_CharRef(self, node) -> Node:
        # node.result = f"&#{node.content};"
        node.name = ":CharRef"
        return node

    def on_EntityRef(self, node) -> Node:
        # node.result = f"&{node.content};"
        node.result = node.content
        node.name = ":EntityRef"
        return node

    def on_Reference(self, node) -> Node:
        assert len(node.children) == 1
        return self.compile(node.children[0])

    def on_Comment(self, node):
        node.name = '!--'
        return node

    def on_Series__(self, node):
        """Visitor for ":Series"-nodes to make XML-Transformer
        more resilient against bad input data.

        Becomes only relevant if
        there is an error in the input data, in which case files
        with errors might yield CSTs that still contain
        ":Series"-nodes (Note: 0x3a == ":") might result in a TypeError
        if not handled by a dedicated visitor."""
        node.name = ZOMBIE_TAG
        result = []
        for nd in node.children:
            if nd.name not in self.expendables:
                if nd.name == 'content':
                    result.extend(self.compile(nd))
                else:
                    result.append(self.compile(nd))
        node.result = tuple(result)
        return node


get_transformer = ThreadLocalSingletonFactory(XMLTransformer)


def transform_XML(cst):
    return get_transformer()(cst)



#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

# get_compiler = ThreadLocalSingletonFactory(XMLCompiler)

def get_compiler() -> Callable:
    def nop(ast: Node) -> Node:
        return ast
    return nop

def compile_XML(ast):
    return get_compiler()(ast)


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

RESULT_FILE_EXTENSION = ".sxpr"  # Change this according to your needs!


def compile_src(source: str, cfg: Dict={}) -> Tuple[Any, List[Error]]:
    """Compiles ``source`` and returns (result, errors)."""
    add_config_values(cfg)
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


def process_file(source: str, result_filename: str = '', cfg: Dict={}) -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors of warnings occurred.
    """
    source_filename = source if is_filename(source) else ''
    result, errors = compile_src(source, cfg)
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


def batch_process(file_names: List[str], out_dir: str, cfg: Dict={},
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
            err_futures.append(submit_func(process_file, name, dest_name, cfg))
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
    script_path = os.path.abspath(os.path.realpath(__file__))
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
    parser = ArgumentParser(description="Parses a XML-file and shows its syntax-tree.")
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
    outformat.add_argument('-w', '--whitespace', action='store_const', const='whitespace',
                           help='Preserve all whitespaces and linefeeds')

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
        set_preset_value('XTML.preserve_whitespace', bool(args.whitespace))
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
        if outfmt == 'xml' and get_config_value('XML.preserve_whitespace', False):
            print(result.as_xml(inline_tags={result.name}))
        else:
            print(result.serialize(how=outfmt) if isinstance(result, Node) else result)
