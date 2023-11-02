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
from typing import Tuple, List, Union, Any, Optional, Callable, Set, cast

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

from DHParser.compile import Compiler, compile_source
from DHParser.pipeline import full_pipeline, Junction, end_points, PseudoJunction, create_preprocess_junction, \
    create_parser_junction, create_junction
from DHParser.configuration import set_config_value, get_config_value, access_thread_locals, \
    access_presets, finalize_presets, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN
from DHParser import dsl
from DHParser.dsl import recompile_grammar, never_cancel
from DHParser.ebnf import grammar_changed
from DHParser.error import ErrorCode, Error, canonical_error_strings, has_errors, NOTICE, \
    WARNING, ERROR, FATAL
from DHParser.log import start_logging, suspend_logging, resume_logging
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, RootNode, Path
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, mixin_comment, \
    last_value, matching_bracket, optional_last_value
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc, PreprocessorResult, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors
from DHParser.toolkit import is_filename, load_if_file, cpu_count, RX_NEVER_MATCH, \
    ThreadLocalSingletonFactory, expand_table, smart_list
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
    has_attr, has_parent, has_children, has_child, apply_unless, apply_ifelse, traverse, \
    three_valued
from DHParser import parse as parse_namespace__

import DHParser.versionnumber
if DHParser.versionnumber.__version_info__ < (1, 4, 0):
    print(f'DHParser version {DHParser.versionnumber.__version__} is lower than the DHParser '
          f'version 1.4.0, {os.path.basename(__file__)} has first been generated with. '
          f'Please install a more recent version of DHParser to avoid unexpected errors!')


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



# To capture includes, replace the NEVER_MATCH_PATTERN 
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'
RE_INCLUDE = NEVER_MATCH_PATTERN
RE_COMMENT = NEVER_MATCH_PATTERN  # THIS MUST ALWAYS BE THE SAME AS outlineGrammar.COMMENT__ !!!


def outlineTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []

preprocessing: PseudoJunction = create_preprocess_junction(
    outlineTokenizer, RE_INCLUDE, RE_COMMENT)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class outlineGrammar(Grammar):
    r"""Parser for an outline source file.
    """
    emphasis = Forward()
    source_hash__ = "b712b509302999dce4802970355c930c"
    early_tree_reduction__ = CombinedParser.MERGE_LEAVES
    disposable__ = re.compile('WS$|EOF$|LINE$|GAP$|LLF$|L$|CHARS$|TEXT$|ESCAPED$|inner_emph$|inner_bold$|blocks$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'[ \t]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp('.')))
    GAP = Drop(RegExp('(?:[ \\t]*\\n)+'))
    WS = Drop(Synonym(GAP))
    PARSEP = Series(dwsp__, RegExp('\\n'), dwsp__, RegExp('\\n'))
    LF = RegExp('[ \\t]*\\n[ \\t]*(?!\\n)')
    L = Series(RegExp('[ \\t]'), dwsp__)
    LLF = Alternative(L, LF)
    ESCAPED = Series(Drop(Text("\\")), RegExp('.'))
    CHARS = RegExp('[^\\s\\\\_*]+')
    TEXT = Series(CHARS, ZeroOrMore(Series(LLF, CHARS)))
    LINE = RegExp('[^\\n]+')
    text = Series(Alternative(TEXT, ESCAPED), ZeroOrMore(Series(Option(LLF), Alternative(TEXT, ESCAPED))))
    inner_bold = Series(Option(Series(dwsp__, Lookahead(RegExp('[*_]')))), Alternative(text, emphasis), ZeroOrMore(Series(Option(LLF), Alternative(text, emphasis))), Option(Series(Lookbehind(RegExp('[*_]')), dwsp__)))
    bold = Alternative(Series(Drop(Text("**")), inner_bold, Drop(Text("**")), mandatory=1), Series(Drop(Text("__")), inner_bold, Drop(Text("__")), mandatory=1))
    is_heading = RegExp('##?#?#?#?#?(?!#)')
    heading = Synonym(LINE)
    inner_emph = Series(Option(Series(dwsp__, Lookahead(RegExp('[*_]')))), Alternative(text, bold), ZeroOrMore(Series(Option(LLF), Alternative(text, bold))), Option(Series(Lookbehind(RegExp('[*_]')), dwsp__)))
    indent = RegExp('[ \\t]+(?=[^\\s])')
    markup = Series(Option(indent), Alternative(text, bold, emphasis), ZeroOrMore(Series(Option(LLF), Alternative(text, bold, emphasis))))
    blocks = Series(NegativeLookahead(is_heading), markup, ZeroOrMore(Series(GAP, NegativeLookahead(is_heading), markup)))
    s6section = Series(Drop(Text("######")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)))
    s5section = Series(Drop(Text("#####")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)), ZeroOrMore(Series(WS, s6section)))
    subsubsection = Series(Drop(Text("####")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)), ZeroOrMore(Series(WS, s5section)))
    subsection = Series(Drop(Text("###")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)), ZeroOrMore(Series(WS, subsubsection)))
    section = Series(Drop(Text("##")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)), ZeroOrMore(Series(WS, subsection)))
    main = Series(Option(WS), Drop(Text("#")), NegativeLookahead(Drop(Text("#"))), dwsp__, heading, Option(Series(WS, blocks)), ZeroOrMore(Series(WS, section)))
    emphasis.set(Alternative(Series(Drop(Text("*")), NegativeLookahead(Drop(Text("*"))), inner_emph, Drop(Text("*")), mandatory=2), Series(Drop(Text("_")), NegativeLookahead(Drop(Text("_"))), inner_emph, Drop(Text("_")), mandatory=2)))
    document = Series(main, Option(WS), EOF, mandatory=2)
    root__ = document
        
parsing: PseudoJunction = create_parser_junction(outlineGrammar)
get_grammar = parsing.factory # for backwards compatibility, only    


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

outline_AST_transformation_table = {
    # AST Transformations for the outline-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],   # called for each node after calling its specific rules
    "markup, bold, emphasis, text":
          [merge_adjacent(is_one_of('text', ':Text', ':L', ':RegExp', ':CHARS'), 'text'),
           apply_if(replace_by_single_child, is_one_of({'text'}))],
          # apply_if(reduce_single_child, has_child({'text'}))],
    "LF": [replace_content_with(' '), change_name(':L')],
    ":GAP": [change_name('GAP')]
}

def outlineTransformer() -> TransformerFunc:
    return partial(transformer, transformation_table=outline_AST_transformation_table.copy(),
                   src_stage='CST', dst_stage='AST')


ASTTransformation: Junction = Junction(
    'CST', ThreadLocalSingletonFactory(outlineTransformer), 'AST')


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


class DOMCompiler(Compiler):
    """Transforms the abstract-syntax-tree to a DOM-tree
    with HTML-based node-names.
    """

    def __init__(self):
        super(DOMCompiler, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "AST", f"Source stage `AST` expected, `but `{root.stage}` found."
        root.stage = "DOM"

    def finalize(self, result: Any) -> Any:
        if result.name in ('main', 'section', 'subsection', 'subsubsection',
                           's5section', 's6section', 'blocks', ':blocks'):
            result.name = 'div'
        return result

    def on_document(self, node):
        node = self.fallback_compiler(node)
        node.name = "body"
        return node

    def compile_structure(self, node, heading_name):
        node = self.fallback_compiler(node)
        node['heading'].name = heading_name
        replace_by_children(self.path)
        return node

    def on_main(self, node):
        return self.compile_structure(node, "h1")

    def on_section(self, node):
        return self.compile_structure(node, "h2")

    def on_subsection(self, node):
        return self.compile_structure(node, "h3")

    def on_subsubsection(self, node):
        return self.compile_structure(node, "h4")

    def on_s5section(self, node):
        return self.compile_structure(node, "h5")

    def on_s6section(self, node):
        return self.compile_structure(node, "h6")

    def on_markup(self, node):
        node = self.fallback_compiler(node)
        if node[0].name == 'indent':
            node.attr['style'] = "text-indent: 2em;"
            del node[0]
        if len(node.children) == 1 and node[0].name == 'text':
           reduce_single_child(self.path)
        node.name = "p"
        return node
    
    def on_bold(self, node):
        node = self.fallback_compiler(node)
        if len(node.children) == 1 and node[0].name == 'text':
            reduce_single_child(self.path)
        node.name = "b"
        return node
    
    def on_emphasis(self, node):
        node = self.fallback_compiler(node)
        if len(node.children) == 1 and node[0].name == 'text':
            reduce_single_child(self.path)
        node.name = "i"
        return node


compiling: Junction = create_junction(
    DOMCompiler, "AST", "DOM")


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

HTML_TMPL = """<!DOCTYPE html>
<html lang="en-GB">
<head>
    <title>{title}</title>
    <meta charset="utf8"/>
</head>
{body}
</html>
"""


class HTMLSerializer(Compiler):
    # def reset(self):
    #     super().reset()
    #     self.title = ''

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "DOM", f"Source stage `DOM` expected, `but `{root.stage}` found."
        root.stage = "html"
        h1 = root.pick('h1')
        self.title = h1.content if h1 else ''

    # # This would be cumbersome for testing
    # def finalize(self, result: Any) -> Any:
    #     if result.startswith('<!DOCTYPE html>'):
    #         return result
    #     else:
    #         body = '\n'.join(['<body>', result, '</body>'])
    #         return HTML_TMPL.format(title=self.title, body=body)

    def on_body(self, node: Node) -> str:
        body = node.as_xml(string_tags={'text'})
        return HTML_TMPL.format(title=self.title, body=body)
    
    def wildcard(self, node: Node) -> str:
        return node.as_xml(string_tags={'text'})

serializing: Junction = create_junction(HTMLSerializer, "DOM", "html")


#######################################################################
#
# Processing-Pipeline
#
#######################################################################

# Add your own stages to the junctions and target-lists, below
# (See DHParser.compile for a description of junctions)

# add your own post-processing junctions, here, e.g. postprocessing.junction
junctions = set([ASTTransformation, compiling, serializing])
# put your targets of interest, here. A target is the name of result (or stage)
# of any transformation, compilation or postprocessing step after parsing.
# Serializations of the stages listed here will be written to disk when
# calling process_file() or batch_process() and also appear in test-reports.
targets = end_points(junctions)
test_targets = {j.dst for j in junctions}

# add one or more serializations for those targets that are node-trees
serializations = expand_table({'DOM': ['sxpr'], '*': ['sxpr']})


#######################################################################

def compile_src(source: str, target: str = "outline".lower()) -> Tuple[Any, List[Error]]:
    """Compiles the source to a single targte and returns the result of the compilation
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
            print(os.path.basename(__file__) + ' has changed. '
                  'Please run again in order to apply updated compiler')
            sys.exit(0)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses a outline-file and shows its syntax-tree.")
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

    if args.xml:
        RESULT_FILE_EXTENSION = '.xml'

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
            if args.xml:  outfmt = 'xml'
            elif args.sxpr:  outfmt = 'sxpr'
            elif args.sxml:  outfmt = 'sxml'
            elif args.tree:  outfmt = 'tree'
            elif args.json:  outfmt = 'json'
            else:  outfmt = 'default'
            print(result.serialize(how=outfmt) if isinstance(result, Node) else result)
            if errors:  print('\n---')

        for err_str in canonical_error_strings(errors):
            print(err_str)
        if has_errors(errors, ERROR):  sys.exit(1)

    return True


if __name__ == "__main__":
    main()
