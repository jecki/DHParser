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
from typing import Tuple, List, Union, Any, Optional, Callable, cast

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
from DHParser.configuration import set_config_value, add_config_values, get_config_value, \
    access_thread_locals, access_presets, finalize_presets, set_preset_value, \
    get_preset_value, NEVER_MATCH_PATTERN
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
    ThreadLocalSingletonFactory, expand_table
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
if DHParser.versionnumber.__version_info__ < (1, 8, 0):
    print(f'DHParser version {DHParser.versionnumber.__version__} is lower than the DHParser '
          f'version 1.8.0, {os.path.basename(__file__)} has first been generated with. '
          f'Please install a more recent version of DHParser to avoid unexpected errors!')


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



# To capture includes, replace the NEVER_MATCH_PATTERN
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'
RE_INCLUDE = NEVER_MATCH_PATTERN
RE_COMMENT = '#.*'  # THIS MUST ALWAYS BE THE SAME AS reGrammar.COMMENT__ !!!


def reTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []

preprocessing: PseudoJunction = create_preprocess_junction(
    reTokenizer, RE_INCLUDE, RE_COMMENT)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class reGrammar(Grammar):
    r"""Parser for a re source file.
    """
    _entity = Forward()
    _item = Forward()
    pattern = Forward()
    source_hash__ = "a280e5b66bba49dc6ed2e06fafca6697"
    early_tree_reduction__ = CombinedParser.MERGE_LEAVES
    disposable__ = re.compile('(?:_special$|_entity$|_item$|_octal$|_extension$|BS$|_illegal$|_anyChar$|_escapedCh$|EOF$|_repeater$|_escape$|_character$|_grpItem$|_number$|_nibble$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'#.*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp('.')))
    bs = RegExp('\\\\')
    BS = Drop(Synonym(bs))
    _anyChar = RegExp('[^|+*?]')
    charSeq = OneOrMore(Series(NegativeLookahead(_entity), _anyChar))
    _character = RegExp('[^)|+*?]')
    characters = OneOrMore(Series(NegativeLookahead(_entity), _character))
    _grpItem = Alternative(_entity, characters)
    zeroOrOne = Text("?")
    zeroOrMore = Text("*")
    _number = RegExp('[0-9]+')
    oneOrMore = Text("+")
    lrtype = Alternative(Text("="), Text("!"), Text("<="), Text("<!"))
    notGreedy = Text("?")
    comment = Series(Drop(Text("#")), RegExp('(?:[\\\\]\\)|[^)\\\\]+)+'))
    groupName = RegExp('(?!\\d)\\w+')
    max = Synonym(_number)
    min = Synonym(_number)
    flags = Series(RegExp('[aiLmsux]+'), Option(Series(Drop(Text("-")), RegExp('[imsx]+'))))
    range = Series(Drop(Text("{")), min, Option(Series(Drop(Text(",")), max)), Drop(Text("}")))
    _repeater = Alternative(zeroOrOne, zeroOrMore, oneOrMore, range)
    _illegal = RegExp('[a-zA-Z]')
    chSpecial = RegExp('[abfnrtv]')
    _nibble = RegExp('[0-9a-fA-F]')
    escapedSet = Series(BS, RegExp('[dDsSwW]'))
    hex2 = Counted(_nibble, repetitions=(2, 2))
    hex8 = Counted(_nibble, repetitions=(8, 8))
    error = Series(Lookahead(_illegal), Custom(ERR("Unknown escape sequence")), _illegal)
    ch = Alternative(Series(BS, error), Series(NegativeLookahead(Drop(Text("]"))), Option(BS), _anyChar))
    backRef = Series(Drop(Text("P=")), groupName, mandatory=1)
    groupId = RegExp('\\d\\d?')
    escCh = Alternative(_anyChar, RegExp('[)|+*?]'))
    chName = Series(Drop(Text("N")), Drop(Text("{")), RegExp('[\\w ]+'), Drop(Text("}")), mandatory=1)
    _octal = RegExp('[0-7]')
    oct = Alternative(Series(Drop(Text("0")), Counted(_octal, repetitions=(0, 3))), Counted(_octal, repetitions=(3, 3)))
    hex4 = Counted(_nibble, repetitions=(4, 4))
    chCode = Alternative(Series(Drop(Text("x")), hex2), Series(Drop(Text("u")), hex4), Series(Drop(Text("U")), hex8), oct)
    _escapedCh = Series(BS, Alternative(chCode, chSpecial))
    chRange = Series(Alternative(_escapedCh, ch), Drop(Text("-")), Alternative(_escapedCh, ch))
    charset = Series(Drop(Text("[")), OneOrMore(Alternative(chRange, escapedSet, _escapedCh, ch)), Drop(Text("]")))
    specialEsc = RegExp('[abdDfnrsStvwW]')
    reEsc = RegExp('[AbBZ]')
    _escape = Series(BS, Alternative(reEsc, bs, specialEsc, chCode, chName, groupId, error, escCh))
    end = Text("$")
    start = Text("^")
    any = Text(".")
    _special = Alternative(any, start, end)
    noBacktracking = Text("+")
    grpRepetition = Series(_grpItem, _repeater, Option(Alternative(notGreedy, noBacktracking)))
    grpPattern = ZeroOrMore(Alternative(grpRepetition, _grpItem))
    grpRegex = Series(grpPattern, ZeroOrMore(Series(Drop(Text("|")), grpPattern)))
    lookaround = Series(lrtype, grpRegex, mandatory=1)
    namedGroup = Series(Drop(Text("P<")), groupName, Drop(Text(">")), grpRegex, mandatory=1)
    subRegex = Series(Drop(Text(">")), grpRegex, mandatory=1)
    nonCapturing = Series(Option(flags), Drop(Text(":")), grpRegex, mandatory=2)
    bifurcation = Series(Drop(Text("(")), Alternative(groupId, groupName), Drop(Text(")")), pattern, Drop(Text("|")), grpPattern, mandatory=1)
    _extension = Series(Drop(Text("?")), Alternative(nonCapturing, subRegex, namedGroup, backRef, comment, lookaround, bifurcation), mandatory=1)
    repetition = Series(_item, _repeater, Option(Alternative(notGreedy, noBacktracking)))
    group = Series(Drop(Text("(")), Alternative(_extension, grpRegex), Drop(Text(")")), mandatory=1)
    flagGroups = OneOrMore(Series(Drop(Text("(?")), flags, Drop(Text(")")), mandatory=2))
    regex = Series(pattern, ZeroOrMore(Series(Drop(Text("|")), pattern)))
    _entity.set(Alternative(_special, _escape, charset, group))
    _item.set(Alternative(_entity, charSeq))
    pattern.set(ZeroOrMore(Alternative(repetition, _item)))
    regular_expression = Series(Option(flagGroups), Alternative(regex, Drop(Text(")"))), EOF)
    root__ = regular_expression
    
parsing: PseudoJunction = create_parser_junction(reGrammar)
get_grammar = parsing.factory # for backwards compatibility, only


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

re_AST_transformation_table = {
    # AST Transformations for the re-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],   # called for each node after calling its specific rules
    "regular_expression": [],
    "regex, grpRegex": [change_name('regex'), replace_by_single_child],
    "pattern, grpPattern": [change_name('pattern'), merge_adjacent(is_one_of('characters')), replace_by_single_child],
    "hex2, hex4, hex8": [change_name('hex')],
    "escCh, charSeq, bs": [change_name('characters')],
}


# DEPRECATED, because it requires pickling the transformation-table, which rules out lambdas!
# ASTTransformation: Junction = create_junction(
#     re_AST_transformation_table, "CST", "AST", "transtable")

def reTransformer() -> TransformerFunc:
    return partial(transformer, transformation_table=re_AST_transformation_table.copy(),
                   src_stage='CST', dst_stage='AST')

ASTTransformation: Junction = Junction(
    'CST', ThreadLocalSingletonFactory(reTransformer), 'AST')


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class reCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a 
        re source file.
    """

    def __init__(self):
        super(reCompiler, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "AST", f"Source stage `AST` expected, `but `{root.stage}` found."
        root.stage = "re"
    def finalize(self, result: Any) -> Any:
        return result

    def on_regular_expression(self, node):
        return self.fallback_compiler(node)

    # def on_regex(self, node):
    #     return node

    # def on_pattern(self, node):
    #     return node

    # def on_item(self, node):
    #     return node

    # def on_flagGroups(self, node):
    #     return node

    # def on_flags(self, node):
    #     return node

    # def on_repetition(self, node):
    #     return node

    # def on_repeater(self, node):
    #     return node

    # def on_zeroOrOne(self, node):
    #     return node

    # def on_zeroOrMore(self, node):
    #     return node

    # def on_oneOrMore(self, node):
    #     return node

    # def on_range(self, node):
    #     return node

    # def on_min(self, node):
    #     return node

    # def on_max(self, node):
    #     return node

    # def on__number(self, node):
    #     return node

    # def on_notGreedy(self, node):
    #     return node

    # def on_noBacktracking(self, node):
    #     return node

    # def on_special(self, node):
    #     return node

    # def on_any(self, node):
    #     return node

    # def on_start(self, node):
    #     return node

    # def on_end(self, node):
    #     return node

    # def on_characters(self, node):
    #     return node

    # def on_character(self, node):
    #     return node

    # def on_escape(self, node):
    #     return node

    # def on_reEsc(self, node):
    #     return node

    # def on_chEsc(self, node):
    #     return node

    # def on_chCode(self, node):
    #     return node

    # def on_hex(self, node):
    #     return node

    # def on_octal(self, node):
    #     return node

    # def on_oct(self, node):
    #     return node

    # def on_chName(self, node):
    #     return node

    # def on_groupId(self, node):
    #     return node

    # def on_groupName(self, node):
    #     return node

    # def on_error(self, node):
    #     return node

    # def on__illegal(self, node):
    #     return node

    # def on_charset(self, node):
    #     return node

    # def on_chRange(self, node):
    #     return node

    # def on_escapedSet(self, node):
    #     return node

    # def on_escapedCh(self, node):
    #     return node

    # def on_ch(self, node):
    #     return node

    # def on_group(self, node):
    #     return node

    # def on_extension(self, node):
    #     return node

    # def on_nonCapturing(self, node):
    #     return node

    # def on_subRegex(self, node):
    #     return node

    # def on_namedGroup(self, node):
    #     return node

    # def on_backRef(self, node):
    #     return node

    # def on_comment(self, node):
    #     return node

    # def on_lookaround(self, node):
    #     return node

    # def on_lrtype(self, node):
    #     return node

    # def on_bifurcation(self, node):
    #     return node

    # def on_BS(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node



compiling: Junction = create_junction(
    reCompiler, "AST", "re")


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
# # ("re") in this example must be the name of some earlier stage, though.
# postprocessing: Junction = create_junction(PostProcessing, "re", "refined")
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
serializations = expand_table(dict([('*', [get_config_value('default_serialization')])]))


#######################################################################
#
# Main program
#
#######################################################################

def compile_src(source: str, target: str = "re") -> Tuple[Any, List[Error]]:
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
    global serializations
    serializations = get_config_value('re_serializations', serializations)
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
    parser = ArgumentParser(description="Parses a re-file and shows its syntax-tree.")
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
    parser.add_argument('-s', '--serialize', nargs='+', default=[])

    args = parser.parse_args()
    file_names, out, log_dir = args.files, args.out[0], ''

    if args.serialize:
        serializations['*'] = args.serialize
        access_presets()
        set_preset_value('re_serializations', serializations, allow_new_key=True)
        finalize_presets()

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
            print(result.serialize(serializations['*'][0])
                  if isinstance(result, Node) else result)
            if errors:  print('\n---')

        for err_str in canonical_error_strings(errors):
            print(err_str)
        if has_errors(errors, ERROR):  sys.exit(1)

    return True


if __name__ == "__main__":
    main()
