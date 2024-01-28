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
from typing import Tuple, List, Union, Any, Optional, Callable, cast, Set

try:
    import regex as re
except ImportError:
    import re

try:
    scriptdir = os.path.dirname(os.path.realpath(__file__))
except NameError:
    scriptdir = ''
if scriptdir and scriptdir not in sys.path: sys.path.append(scriptdir)

try:
    from DHParser import versionnumber
except (ImportError, ModuleNotFoundError):
    i = scriptdir.rfind("/DHParser/")
    if i >= 0:
        dhparserdir = scriptdir[:i + 10]  # 10 = len("/DHParser/")
        if dhparserdir not in sys.path:  sys.path.insert(0, dhparserdir)

from DHParser.compile import Compiler, compile_source, Junction, full_compile
from DHParser.configuration import set_config_value, get_config_value, access_thread_locals, \
    access_presets, finalize_presets, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN
from DHParser import dsl
from DHParser.dsl import recompile_grammar, never_cancel
from DHParser.ebnf import grammar_changed
from DHParser.error import ErrorCode, Error, canonical_error_strings, has_errors, NOTICE, \
    WARNING, ERROR, FATAL
from DHParser.log import start_logging, suspend_logging, resume_logging
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, RootNode, Path, ZOMBIE_TAG
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, DropFrom, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, SmartRE, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, IgnoreCase, \
    LateBindingUnary, mixin_comment, last_value, matching_bracket, optional_last_value, \
    PARSER_PLACEHOLDER, UninitializedError
from DHParser.pipeline import end_points, full_pipeline, create_parser_junction, \
    create_preprocess_junction, create_junction, PseudoJunction 
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc, PreprocessorResult, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors
from DHParser.stringview import StringView
from DHParser.toolkit import is_filename, load_if_file, cpu_count, RX_NEVER_MATCH, \
    ThreadLocalSingletonFactory, expand_table, line_col
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
    has_attr, has_parent, has_children, has_child, apply_unless, apply_ifelse, traverse
from DHParser import parse as parse_namespace__

import DHParser.versionnumber
if DHParser.versionnumber.__version_info__ < (1, 7, 0):
    print(f'DHParser version {DHParser.versionnumber.__version__} is lower than the DHParser '
          f'version 1.7.0, {os.path.basename(__file__)} has first been generated with. '
          f'Please install a more recent version of DHParser to avoid unexpected errors!')


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



# To capture includes, replace the NEVER_MATCH_PATTERN 
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'
RE_INCLUDE = NEVER_MATCH_PATTERN
RE_COMMENT = NEVER_MATCH_PATTERN  # THIS MUST ALWAYS BE THE SAME AS HTMLGrammar.COMMENT__ !!!


def HTMLTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []

preprocessing: PseudoJunction = create_preprocess_junction(
    HTMLTokenizer, RE_INCLUDE, RE_COMMENT)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class HTMLGrammar(Grammar):
    r"""Parser for a HTML source file.
    """
    element = Forward()
    source_hash__ = "23e161f9fc8e1ef4bc7006dff6ffd207"
    early_tree_reduction__ = CombinedParser.MERGE_TREETOPS
    disposable__ = re.compile('(?:$.)|(?:prolog$|PubidChars$|CData$|NameStartChar$|CommentChars$|BOM$|VersionNum$|EOF$|tagContent$|PubidCharsSingleQuoted$|Reference$|EncName$|Misc$|NameChars$)')
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
    EOF = Drop(NegativeLookahead(RegExp('(?i).')))
    CharRef = Alternative(Series(Drop(IgnoreCase('&#')), RegExp('(?i)[0-9]+'), Drop(IgnoreCase(';'))), Series(Drop(IgnoreCase('&#x')), RegExp('(?i)[0-9a-fA-F]+'), Drop(IgnoreCase(';'))))
    CommentChars = RegExp('(?i)(?:(?!-)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    PIChars = RegExp('(?i)(?:(?!\\?>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CData = RegExp('(?i)(?:(?!\\]\\]>)(?:\\x09|\\x0A|\\x0D|[\\u0020-\\uD7FF]|[\\uE000-\\uFFFD]|[\\U00010000-\\U0010FFFF]))+')
    CharData = RegExp('(?i)(?:(?!\\]\\]>)[^<&])+')
    PubidChars = RegExp("(?i)(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-'()+,./:=?;!*#@$_%])+")
    PubidCharsSingleQuoted = RegExp('(?i)(?:\\x20|\\x0D|\\x0A|[a-zA-Z0-9]|[-()+,./:=?;!*#@$_%])+')
    S = RegExp('(?i)\\s+')
    CDSect = Series(Drop(IgnoreCase('<![CDATA[')), CData, Drop(IgnoreCase(']]>')))
    NameStartChar = RegExp('(?xi)_|:|[A-Z]|[a-z]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF]')
    NameChars = RegExp('(?xi)(?:_|:|-|\\.|[A-Z]|[a-z]|[0-9]\n                   |\\u00B7|[\\u0300-\\u036F]|[\\u203F-\\u2040]\n                   |[\\u00C0-\\u00D6]|[\\u00D8-\\u00F6]|[\\u00F8-\\u02FF]\n                   |[\\u0370-\\u037D]|[\\u037F-\\u1FFF]|[\\u200C-\\u200D]\n                   |[\\u2070-\\u218F]|[\\u2C00-\\u2FEF]|[\\u3001-\\uD7FF]\n                   |[\\uF900-\\uFDCF]|[\\uFDF0-\\uFFFD]\n                   |[\\U00010000-\\U000EFFFF])+')
    Comment = Series(Drop(IgnoreCase('<!--')), ZeroOrMore(Alternative(CommentChars, RegExp('(?i)-(?!-)'))), dwsp__, Drop(IgnoreCase('-->')))
    Name = Series(NameStartChar, Option(NameChars))
    PITarget = Series(NegativeLookahead(RegExp('(?i)X|xM|mL|l')), Name)
    PI = Series(Drop(IgnoreCase('<?')), PITarget, Option(Series(dwsp__, PIChars)), Drop(IgnoreCase('?>')))
    Misc = OneOrMore(Alternative(Comment, PI, S))
    EntityRef = Series(Drop(IgnoreCase('&')), Name, Drop(IgnoreCase(';')))
    Reference = Alternative(EntityRef, CharRef)
    PubidLiteral = Alternative(Series(Drop(IgnoreCase('"')), Option(PubidChars), Drop(IgnoreCase('"'))), Series(Drop(IgnoreCase("\'")), Option(PubidCharsSingleQuoted), Drop(IgnoreCase("\'"))))
    SystemLiteral = Alternative(Series(Drop(IgnoreCase('"')), RegExp('(?i)[^"]*'), Drop(IgnoreCase('"'))), Series(Drop(IgnoreCase("\'")), RegExp("(?i)[^']*"), Drop(IgnoreCase("\'"))))
    AttValue = Alternative(Series(Drop(IgnoreCase('"')), ZeroOrMore(Alternative(RegExp('(?i)[^<&"]+'), Reference)), Drop(IgnoreCase('"'))), Series(Drop(IgnoreCase("\'")), ZeroOrMore(Alternative(RegExp("(?i)[^<&']+"), Reference)), Drop(IgnoreCase("\'"))), ZeroOrMore(Alternative(RegExp("(?i)[^<&'>\\s]+"), Reference)))
    content = Series(Option(CharData), ZeroOrMore(Series(Alternative(element, Reference, CDSect, PI, Comment), Option(CharData))))
    Attribute = Series(Name, dwsp__, Drop(IgnoreCase('=')), dwsp__, AttValue, mandatory=2)
    ETag = Series(Drop(IgnoreCase('</')), Name, dwsp__, Drop(IgnoreCase('>')), mandatory=1)
    tagContent = Series(NegativeLookahead(RegExp('(?i)[/!?]')), Name, ZeroOrMore(Series(dwsp__, Attribute)), dwsp__, Lookahead(Alternative(Drop(IgnoreCase('>')), Drop(IgnoreCase('/>')))), mandatory=1)
    STag = Series(Drop(IgnoreCase('<')), tagContent, Drop(IgnoreCase('>')))
    voidElement = Series(Drop(IgnoreCase('<')), Lookahead(Alternative(Drop(IgnoreCase('area')), Drop(IgnoreCase('base')), Drop(IgnoreCase('br')), Drop(IgnoreCase('col')), Drop(IgnoreCase('embed')), Drop(IgnoreCase('hr')), Drop(IgnoreCase('img')), Drop(IgnoreCase('input')), Drop(IgnoreCase('link')), Drop(IgnoreCase('meta')), Drop(IgnoreCase('param')), Drop(IgnoreCase('source')), Drop(IgnoreCase('track')), Drop(IgnoreCase('wbr')))), tagContent, Drop(IgnoreCase('>')))
    emptyElement = Series(Drop(IgnoreCase('<')), tagContent, Drop(IgnoreCase('/>')))
    BOM = Drop(RegExp('(?i)[\\ufeff]|[\\ufffe]|[\\u0000feff]|[\\ufffe0000]'))
    ExternalID = Alternative(Series(Drop(IgnoreCase('SYSTEM')), dwsp__, SystemLiteral, mandatory=1), Series(Drop(IgnoreCase('PUBLIC')), dwsp__, PubidLiteral, dwsp__, SystemLiteral, mandatory=1))
    doctypedecl = Series(Drop(IgnoreCase('<!DOCTYPE')), dwsp__, Name, Option(Series(dwsp__, ExternalID)), dwsp__, Drop(IgnoreCase('>')), mandatory=2)
    SDDecl = Series(dwsp__, Drop(IgnoreCase('standalone')), dwsp__, Drop(IgnoreCase('=')), dwsp__, Alternative(Series(Drop(IgnoreCase("\'")), Alternative(IgnoreCase("yes"), IgnoreCase("no")), Drop(IgnoreCase("\'"))), Series(Drop(IgnoreCase('"')), Alternative(IgnoreCase("yes"), IgnoreCase("no")), Drop(IgnoreCase('"')))))
    EncName = RegExp('(?i)[A-Za-z][A-Za-z0-9._\\-]*')
    EncodingDecl = Series(dwsp__, Drop(IgnoreCase('encoding')), dwsp__, Drop(IgnoreCase('=')), dwsp__, Alternative(Series(Drop(IgnoreCase("\'")), EncName, Drop(IgnoreCase("\'"))), Series(Drop(IgnoreCase('"')), EncName, Drop(IgnoreCase('"')))))
    VersionNum = RegExp('(?i)[0-9]+\\.[0-9]+')
    VersionInfo = Series(dwsp__, Drop(IgnoreCase('version')), dwsp__, Drop(IgnoreCase('=')), dwsp__, Alternative(Series(Drop(IgnoreCase("\'")), VersionNum, Drop(IgnoreCase("\'"))), Series(Drop(IgnoreCase('"')), VersionNum, Drop(IgnoreCase('"')))))
    XMLDecl = Series(Drop(IgnoreCase('<?xml')), VersionInfo, Option(EncodingDecl), Option(SDDecl), dwsp__, Drop(IgnoreCase('?>')), mandatory=1)
    prolog = Series(Option(Series(dwsp__, XMLDecl)), Option(Misc), Option(Series(doctypedecl, Option(Misc))))
    element.set(Alternative(emptyElement, voidElement, Series(STag, content, ETag, mandatory=2)))
    document = Series(Option(BOM), prolog, element, Option(Misc), EOF, mandatory=2)
    resume_rules__ = {'tagContent': [re.compile(r'(?i)(?=>|\/>)')],
                      'ETag': [re.compile(r'(?i)(?=>)')],
                      'Attribute': [re.compile(r'(?i)(?=>|\/>)')],
                      'element': [re.compile(r'(?i)(?=.|$)')]}
    root__ = document
        
parsing: PseudoJunction = create_parser_junction(HTMLGrammar)
get_grammar = parsing.factory # for backwards compatibility, only


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

HTML_PTYPE = ":HTML"

WARNING_AMBIGUOUS_EMPTY_ELEMENT = ErrorCode(205)

ERROR_TAG_NAME_MISMATCH = ErrorCode(2000)
ERROR_VALUE_CONSTRAINT_VIOLATION = ErrorCode(2010)
ERROR_VALIDITY_CONSTRAINT_VIOLATION = ErrorCode(2020)


class HTMLTransformer(Compiler):
    """Compiler for the abstract-syntax-tree of a XML source file.

    As of now, processing instructions, cdata-sections an document-type definition
    declarations are simply dropped.
    """
    def __init__(self):
        super().__init__()
        self.cleanup_whitespace = True  # remove empty CharData from mixed elements
        self.expendables = {'PI', 'CDSect', 'doctypedecl'}

    def reset(self):
        super().reset()
        self.preserve_whitespace = False
        self.non_empty_tags: Set[str] = set()

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "CST", f"Source stage `CST` expected, `but `{root.stage}` found."
        root.stage = "AST"

    def finalize(self, result: Any) -> Any:
        return result

    def extract_attributes(self, node_sequence):
        attributes = collections.OrderedDict()
        for node in node_sequence:
            if node.name == "Attribute":
                assert node[0].name == "Name", node.as_sexpr()
                # assert node[1].name == "AttValue", node.as_sxpr()
                attributes[node[0].content] = node[1].content.replace('\n', '')
        return attributes

    def value_constraint(self, node, value, allowed):
        """If value is not in allowed, an error is issued."""
        if not value in allowed:
            self.tree.new_error(node,
                                'Invalid value "%s" for "standalone"! Must be one of %s.' \
                                % (value, str(allowed)), ERROR_VALUE_CONSTRAINT_VIOLATION)

    def on_document(self, node):
        node.name = HTML_PTYPE
        self.tree.string_tags.update({TOKEN_PTYPE, HTML_PTYPE, 'CharRef', 'EntityRef'})
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
        # self.tree.empty_tags.add('?xml')
        node.name = '?xml'  # node.parser = self.get_parser('?xml')
        return node

    def on_content(self, node) -> Union[Tuple[Node], str]:
        xml_content = tuple(self.compile(nd) for nd in node.children
                            if nd.name not in self.expendables)
        if len(xml_content) == 1:
            if xml_content[0].name == TOKEN_PTYPE:
                # reduce single CharData children
                xml_content = xml_content[0].content
        elif self.cleanup_whitespace and not self.preserve_whitespace:
            # remove CharData that consists only of whitespace from mixed elements
            xml_content = tuple(child for child in xml_content
                                if child.name != TOKEN_PTYPE or child.content.strip() != '')
        return xml_content

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

    def on_Reference(self, node):
        replace_by_single_child(self.path)
        return node

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


ASTTransformation: Junction = Junction(
    'CST', ThreadLocalSingletonFactory(HTMLTransformer), 'AST')


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class HTMLCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a 
        HTML source file.
    """

    def __init__(self):
        super(HTMLCompiler, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "AST", f"Source stage `AST` expected, `but `{root.stage}` found."
        root.stage = "HTML"
    def finalize(self, result: Any) -> Any:
        return result

    def on_document(self, node):
        return self.fallback_compiler(node)


compiling: Junction = create_junction(
    HTMLCompiler, "AST", "HTML")


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

#######################################################################
#
# Post-Processing-Stages [add one or more postprocessing stages, here]
#
#######################################################################

# class PostProcessing(Compiler):
#     ...

# # change the names of the source and destination stages. Source
# # ("HTML") in this example must be the name of some earlier stage, though.
# postprocessing: Junction = create_junction(PostProcessing, "HTML", "refined")
#
# DON'T FORGET TO ADD ALL POSTPROCESSING-JUNCTIONS TO THE GLOBAL
# "junctions"-set IN SECTION "Processing-Pipeline" BELOW!

#######################################################################
#
# Processing-Pipeline
#
#######################################################################

# Add your own stages to the junctions and target-lists, below
# (See DHParser.compile for a description of junctions)

# ADD YOUR OWN POST-PROCESSING-JUNCTIONS HERE:
junctions = set([ASTTransformation, compiling])

# put your targets of interest, here. A target is the name of result (or stage)
# of any transformation, compilation or postprocessing step after parsing.
# Serializations of the stages listed here will be written to disk when
# calling process_file() or batch_process() and also appear in test-reports.
targets = end_points(junctions)
# alternative: targets = set([compiling.dst])

# provide a set of those stages for which you would like to see the output
# in the test-report files, here. (AST is always included)
test_targets = set(j.dst for j in junctions)
# alternative: test_targets = targets

# add one or more serializations for those targets that are node-trees
serializations = expand_table(dict([('*', ['sxpr'])]))


#######################################################################
#
# Main program
#
#######################################################################

def compile_src(source: str, target: str = "HTML") -> Tuple[Any, List[Error]]:
    """Compiles the source to a single target and returns the result of the compilation
    as well as a (possibly empty) list or errors or warnings that have occurred in the
    process.
    """
    full_compilation_result = full_pipeline(
        source, preprocessing.factory, parsing.factory, junctions, set([target]))
    return full_compilation_result[target]


def process_file(source: str, out_dir: str = '') -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors or warnings occurred.
    """
    return dsl.process_file(source, out_dir, preprocessing.factory, parsing.factory,
                            junctions, targets, serializations)


def _process_file(args: Tuple[str, str]) -> str:
    return process_file(*args)


def batch_process(file_names: List[str], out_dir: str,
                  *, submit_func: Callable = None,
                  log_func: Callable = None,
                  cancel_func: Callable = never_cancel) -> List[str]:
    """Compiles all files listed in file_names and writes the results and/or
    error messages to the directory `our_dir`. Returns a list of error
    messages files.
    """
    return dsl.batch_process(file_names, out_dir, _process_file,
        submit_func=submit_func, log_func=log_func, cancel_func=cancel_func)


def main(called_from_app=False) -> bool:
    # recompile grammar if needed
    scriptpath = os.path.abspath(__file__)
    if scriptpath.endswith('Parser.py'):
        grammar_path = scriptpath.replace('Parser.py', '.ebnf')
    else:
        grammar_path = os.path.splitext(scriptpath)[0] + '.ebnf'
    parser_update = False

    def notify():
        nonlocal parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path) and os.path.isfile(grammar_path):
        if not recompile_grammar(grammar_path, scriptpath, force=False, notify=notify):
            error_file = os.path.basename(__file__)\
                .replace('Parser.py', '_ebnf_MESSAGES.txt')
            with open(error_file, 'r', encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
        elif parser_update:
            if '--dontrerun' in sys.argv:
                print(os.path.basename(__file__) + ' has changed. '
                      'Please run again in order to apply updated compiler')
                sys.exit(0)
            else:
                import platform, subprocess
                call = ['python', __file__, '--dontrerun'] + sys.argv[1:]
                result = subprocess.run(call, capture_output=True)
                print(result.stdout.decode('utf-8'))
                sys.exit(result.returncode)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses a HTML-file and shows its syntax-tree.")
    parser.add_argument('files', nargs='*' if called_from_app else '+')
    parser.add_argument('-d', '--debug', action='store_const', const='debug',
                        help='Store debug information in LOGS subdirectory')
    parser.add_argument('-o', '--out', nargs=1, default=['out'],
                        help='Output directory for batch processing')
    parser.add_argument('-v', '--verbose', action='store_const', const='verbose',
                        help='Verbose output')
    parser.add_argument('-f', '--force', action='store_const', const='force',
                        help='Write output file even if errors have occurred')
    parser.add_argument('--singlethread', action='store_const', const='singlethread',
                        help='Run batch jobs in a single thread (recommended only for debugging)')
    parser.add_argument('--dontrerun', action='store_const', const='dontrerun',
                        help='Do not automatically run again if the grammar has been recompiled.')
    outformat = parser.add_mutually_exclusive_group()
    outformat.add_argument('-x', '--xml', action='store_const', const='xml', 
                           help='Format result as XML')
    outformat.add_argument('-s', '--sxpr', action='store_const', const='sxpr',
                           help='Format result as S-expression')
    outformat.add_argument('-m', '--sxml', action='store_const', const='sxml',
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
        set_preset_value('log_syntax_trees', frozenset(['CST', 'AST']))  # don't use a set literal, here!
        finalize_presets()
    start_logging(log_dir)

    if args.singlethread:
        set_config_value('batch_processing_parallelization', False)

    if args.xml:  outfmt = 'xml'
    elif args.sxpr:  outfmt = 'sxpr'
    elif args.sxml:  outfmt = 'sxml'
    elif args.tree:  outfmt = 'tree'
    elif args.json:  outfmt = 'json'
    else:  outfmt = get_config_value('default_serialization')
    serializations['*'] = [outfmt]

    def echo(message: str):
        if args.verbose:
            print(message)

    if called_from_app and not file_names:  return False

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

        if not errors or (not has_errors(errors, ERROR)) \
                or (not has_errors(errors, FATAL) and args.force):
            print(result.serialize(how=outfmt) if isinstance(result, Node) else result)
            if errors:  print('\n---')

        for err_str in canonical_error_strings(errors):
            print(err_str)
        if has_errors(errors, ERROR):  sys.exit(1)

    return True


if __name__ == "__main__":
    main()
