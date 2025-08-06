#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


import collections
import copy
from functools import partial
import os
import sys
from typing import Tuple, List, Union, Any, Optional, Callable, cast, NamedTuple

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
    from DHParser import versionnumber, EMPTY_NODE, LEAF_NODE
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

BRACKETS = { '(': ')', '[': ']', '{': '}' }


# def is_escaped(t: str, i: int) -> Optional[bool]:
#     """Returns True, if the character at position i is escaped,
#     False if it is not and None in case the position i exceeds
#     the bounds of string t.
#     """
#     if 0 <= i < len(t):
#         r = i
#         while r > 0 and t[r - 1] == '\\':
#             r -= 1
#         return (i - r) % 2 != 0
#     else:
#         return None
#
#
# def find_unescaped(t: str, ch: str, i: int) -> int:
#     r"""Find the position of an unescaped character in a string.
#     Examples::
#
#         >>> r"(a\)b)".find(")", 0)
#         3
#         >>> find_unescaped(r"(a\)b)", ")", 0)
#         5
#         >>> find_unescaped(r"(a\\)b)", ")", 0)
#         4
#         >>> find_unescaped(r"(a\\\)b)", ")", 0)
#         7
#     """
#     while i >= 0:
#         i = t.find(ch, i)
#         if is_escaped(t, i):
#             i += 1
#         else:
#             break
#     return i
#
#
# def matching_bracket(t: str, i: int) -> int:
#     r"""Find matching bracket, ignoring escaped brackets.
#     Examples::
#
#         >>> matching_bracket(r"(a\)b)", 0)
#         5
#         >>> matching_bracket(r"(a\\)b)", 0)
#         4
#         >>> matching_bracket(r"(a\\\)b)", 0)
#         7
#         >>> matching_bracket(r"(a(b(c)))", 0)
#         8
#         >>> matching_bracket(r"(a(b(c)))", 2)
#         7
#         >>> matching_bracket(r"(a(b\(c)))", 2)
#         7
#     """
#     opening = t[i]
#     closing = BRACKETS[opening]
#     counter = 1
#     MAX = len(t)
#     k1 = -1
#     k2 = -1
#     while counter > 0:
#         if k1 <= i:
#             k1 = find_unescaped(t, closing, i + 1)
#         if k1 < 0:
#             return len(t)
#         if k2 <= i:
#             k2 = find_unescaped(t, opening, i + 1)
#         if k2 < 0:
#             k2 = MAX
#         if k2 < k1:
#             counter += 1
#         else:
#             counter -= 1
#         i = min(k1, k2)
#     return k1



# To capture includes, replace the NEVER_MATCH_PATTERN
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'
RE_INCLUDE = NEVER_MATCH_PATTERN
RE_COMMENT = NEVER_MATCH_PATTERN



def reTokenizer(original_text) -> Tuple[str, List[Error]]:
    pattern = original_text
    nesting = 0
    verbose = [(False, nesting)]
    in_class = False
    result = []
    i = 0
    def process_verbose_flag(k):
        default = True
        while k < len(pattern) and pattern[k] in {'-', 'i', 'm', 'x', 'u', 's', 'L', 'a'}:
            if pattern[k] == '-':
                default = False
            if pattern[k] == 'x':
                verbose.append((default, nesting))
                break
            k += 1

    while i < len(pattern): # TODO: very messed up
        char = pattern[i]
        if char == '\\':  # Escape sequence, keep next char as-is
            result.append(char)
            i += 1
            if i < len(pattern):
                result.append(pattern[i])
        elif char == '[' and not in_class:
            in_class = True
            result.append(char)
        elif char == ']' and in_class:
            in_class = False
            result.append(char)
        elif char == '(' and not in_class:
            nesting += 1
            if pattern[i:i + 2] == "(?":
                process_verbose_flag(i + 2)
                if i == 0 and len(verbose) > 1:
                    state = verbose[-1][0]
                    verbose = [(state, -1)]
            result.append(char)
        elif char == ')' and not in_class:
            if verbose[-1][1] == nesting:
                verbose.pop()
            nesting -= 1
            result.append(char)
        elif verbose[-1][0]:
            if char == '#' and not in_class:
                # Skip to end of line (comment)
                while i < len(pattern) and pattern[i] != '\n':
                    i += 1
            elif char in ' \t\n\r' and not in_class:
                # Ignore whitespace outside character classes
                pass
        else:
            result.append(char)
        i += 1
        pattern = ''.join(result)

    # TODO: Source mapping still missing!

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
    source_hash__ = "f33fed6830c6f2cfff59d03b36829c2d"
    early_tree_reduction__ = CombinedParser.MERGE_LEAVES
    disposable__ = re.compile('(?:_item$|_illegal$|BS$|_extension$|EOF$|_special$|_number$|_entity$|_grpItem$|_anyChar$|_character$|_octal$|_nibble$|_escapedCh$|_escape$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r''
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    VERBOSE_WHITESPACE = RegExp('\\s*(?:#.*(?=\\n|$))?\\s*')
    EOF = Drop(NegativeLookahead(RegExp('.')))
    bs = RegExp('\\\\')
    BS = Drop(Synonym(bs))
    _anyChar = RegExp('[^|+*?]')
    charSeq = OneOrMore(Series(NegativeLookahead(_entity), _anyChar, dwsp__))
    _character = RegExp('[^)|+*?]')
    characters = OneOrMore(Series(NegativeLookahead(_entity), _character, dwsp__))
    _grpItem = Series(Alternative(_entity, characters), dwsp__)
    zeroOrOne = Text("?")
    zeroOrMore = Text("*")
    _number = RegExp('[0-9]+')
    groupName = RegExp('(?!\\d)\\w+')
    oneOrMore = Text("+")
    lrtype = Alternative(Text("="), Text("!"), Text("<="), Text("<!"))
    min = Synonym(_number)
    comment = Series(Drop(Text("#")), RegExp('(?:[\\\\]\\)|[^)\\\\]+)+'))
    backRef = Series(Drop(Text("P=")), groupName, mandatory=1)
    max = Synonym(_number)
    range = Series(Drop(Text("{")), min, Option(Series(Drop(Text(",")), max)), Drop(Text("}")))
    positive = RegExp('[aiLmsux]+')
    repType = Alternative(zeroOrOne, zeroOrMore, oneOrMore, range)
    negative = Series(Drop(Text("-")), RegExp('[imsx]+'))
    flags = Alternative(Series(positive, Option(negative)), negative)
    ch = Series(NegativeLookahead(Drop(Text("]"))), Option(BS), _anyChar)
    chSpecial = RegExp('[abfnrtv]')
    _nibble = RegExp('[0-9a-fA-F]')
    escapedSet = Series(BS, RegExp('[dDsSwW]'))
    hex2 = Counted(_nibble, repetitions=(2, 2))
    complement = Text("^")
    hex8 = Counted(_nibble, repetitions=(8, 8))
    _illegal = RegExp('[a-zA-Z]')
    error = Series(Lookahead(_illegal), Custom(ERR("Unknown escape sequence")), _illegal)
    groupId = RegExp('\\d\\d?')
    escCh = Alternative(_anyChar, RegExp('[)|+*?]'))
    chName = Series(Drop(Text("N{")), RegExp('[\\w ]+'), Drop(Text("}")))
    _octal = RegExp('[0-7]')
    oct = Alternative(Series(Drop(Text("0")), Counted(_octal, repetitions=(0, 3))), Counted(_octal, repetitions=(3, 3)))
    hex4 = Counted(_nibble, repetitions=(4, 4))
    chCode = Alternative(Series(Drop(Text("x")), hex2), Series(Drop(Text("u")), hex4), Series(Drop(Text("U")), hex8), oct)
    _escapedCh = Series(BS, Alternative(chCode, chSpecial))
    chRange = Series(Alternative(_escapedCh, ch), Drop(Text("-")), Alternative(_escapedCh, ch))
    charset = Series(Drop(Text("[")), Option(complement), OneOrMore(Alternative(chRange, escapedSet, _escapedCh, Series(BS, error), ch)), Drop(Text("]")))
    specialEsc = RegExp('[abfnNrtUvx]')
    reEsc = RegExp('[AbBdDsSwWZ]')
    _escape = Series(BS, Alternative(bs, chCode, chName, groupId, reEsc, specialEsc, error, escCh), mandatory=1)
    end = Text("$")
    start = Text("^")
    any = Text(".")
    _special = Alternative(any, start, end)
    noBacktracking = Text("+")
    notGreedy = Text("?")
    grpRepetition = Series(_grpItem, repType, Option(Alternative(notGreedy, noBacktracking)), dwsp__)
    grpPattern = ZeroOrMore(Alternative(grpRepetition, _grpItem))
    grpRegex = Series(dwsp__, grpPattern, ZeroOrMore(Series(Drop(Text("|")), dwsp__, grpPattern)))
    lookaround = Series(lrtype, grpRegex, mandatory=1)
    namedGroup = Series(Drop(Text("P<")), groupName, Drop(Text(">")), grpRegex, mandatory=1)
    subRegex = Series(Drop(Text(">")), grpRegex, mandatory=1)
    capturing = Synonym(grpRegex)
    bifurcation = Series(Drop(Text("(")), Alternative(groupId, groupName), Drop(Text(")")), pattern, Drop(Text("|")), grpPattern, mandatory=1)
    repetition = Series(_item, repType, Option(Alternative(notGreedy, noBacktracking)), dwsp__)
    nonCapturing = Series(Option(flags), Drop(Text(":")), grpRegex, mandatory=2)
    _extension = Series(Drop(Text("?")), Alternative(nonCapturing, subRegex, namedGroup, backRef, comment, lookaround, bifurcation), mandatory=1)
    group = Series(Drop(Text("(")), Alternative(_extension, capturing), Drop(Text(")")), mandatory=1)
    flagGroups = OneOrMore(Series(Drop(Text("(?")), flags, Drop(Text(")")), mandatory=2))
    regex = Series(dwsp__, pattern, ZeroOrMore(Series(Drop(Text("|")), dwsp__, pattern)))
    _entity.set(Alternative(_special, _escape, charset, group))
    _item.set(Series(Alternative(_entity, charSeq), dwsp__))
    pattern.set(ZeroOrMore(Alternative(repetition, _item)))
    regular_expression = Series(dwsp__, Option(flagGroups), Alternative(regex, Drop(Text(")"))), EOF)
    root__ = regular_expression
    
parsing: PseudoJunction = create_parser_junction(reGrammar)
get_grammar = parsing.factory # for backwards compatibility, only

try:
    assert RE_INCLUDE == NEVER_MATCH_PATTERN or \
        RE_COMMENT in (reGrammar.COMMENT__, NEVER_MATCH_PATTERN), \
        "Please adjust the pre-processor-variable RE_COMMENT in file reParser.py so that " \
        "it either is the NEVER_MATCH_PATTERN or has the same value as the COMMENT__-attribute " \
        "of the grammar class reGrammar! " \
        'Currently, RE_COMMENT reads "%s" while COMMENT__ is "%s". ' \
        % (RE_COMMENT, reGrammar.COMMENT__) + \
        "\n\nIf RE_COMMENT == NEVER_MATCH_PATTERN then includes will deliberately be " \
        "processed, otherwise RE_COMMENT==reGrammar.COMMENT__ allows the " \
        "preprocessor to ignore comments."
except (AttributeError, NameError):
    pass


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

# TODO: Rewrite non-greedy:
# item* tail -> (!tail item)* tail
# item+ tail -> item (!tail item)* tail
# TODO: Rewrite greedy:
# item* tail -> ((!tail item)* tail)*
# item+ tail -> item ((!tail item)* tail)*
# noBacktracking is default with PEGs, no rewriting necessary!


# def contains_linefeed(path: Path) -> bool:
#     return path[-1].content.find('\n') >= 0


re_AST_transformation_table = {
    # AST Transformations for the re-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],   # called for each node after calling its specific rules
    "regular_expression": [],
    # "group": [replace_by_single_child],
    "regex, grpRegex": [change_name('regex'), replace_by_single_child],
    "pattern, grpPattern": [change_name('pattern'),
                            merge_adjacent(is_one_of('characters')),
                            replace_by_single_child],
    "grpRepetition": [change_name('repetition')],
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


class Flags(NamedTuple):
    positive: set
    negative: set

    def __bool__(self) -> bool:
        return bool(self.positive) or bool(self.negative)

    def __str__(self) -> str:
        return f"({''.join(self.positive)},{''.join(self.negative)})"

NO_FLAGS = Flags(set(), set())
FLAG_SET = frozenset({'a', 'i', 'L', 'm', 's', 'u', 'x'})

RX_INTERRUPTED_COMMENT = re.compile(r'([ \t]*(?:#.*)?\n)*(?:[ \t]*(?:#.*)$)')
RX_COMMENT = re.compile(r'([ \t]*(?:#.*)?\n)*(?:[ \t]*(?:#.*)?$)?')


class reCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a 
        re source file.
    """

    def __init__(self):
        super(reCompiler, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        self.last_leaf: Node = EMPTY_NODE
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "AST", f"Source stage `AST` expected, `but `{root.stage}` found."
        root.stage = "re"
        self.last_leaf = root.pick(LEAF_NODE, reverse=True)

    def finalize(self, result: Any) -> Any:
        return result

    def gather_flags(self, node: Node) -> Flags:
        pos = []
        neg = []
        for i in range(len(node.children)):
            if node[i].name != 'flags':
                break
            pos.append(node[i].get('positive', EMPTY_NODE).content)
            neg.append(node[i].get('negative', EMPTY_NODE).content)
        pstr = ''.join(pos)
        nstr = ''.join(neg)
        pflags = set(pstr)
        nflags = set(nstr)
        if len(pflags) > len(pstr):
            self.tree.new_error(node, f'One or more flags in: "{pstr}" are redundant!', WARNING)
        if len(nflags) > len(nstr):
            self.tree.new_error(node, f'One or more flags in: "-{nstr}" are redundant!', WARNING)
        if pflags & nflags:
            self.tree.new_error(node, f'Cannot set and unset "{pflags & nflags}" at the same time!', ERROR)
        return Flags(pflags, nflags)

    def evaluate_flags(self):
        for i in range(len(self.path) - 1, -1, -1):
            effective = self.path[i].get_attr('effective_flags', NO_FLAGS)
            if effective:
                break
        else:
            effective = Flags({'u'}, set())
            i = -1
        for nd in self.path[i + 1:]:
            flags = nd.get_attr('flags', False)
            if flags:
                effective.positive.update(flags.positive)
                effective.positive.difference_update(flags.negative)
                effective.negative.difference_update(FLAG_SET)
                effective.negative.update(FLAG_SET - effective.positive)
                nd.attr['effective_flags'] = copy.deepcopy(effective)

    def get_effective_flags(self, node) -> Flags:
        path = self.path
        for i in range(len(path) - 1, -1, -1):
            effective = path[i].get_attr('effective_flags', False)
            if effective:
                return effective
            if path[i].has_attr('flags'):
                self.tree.new_error(
                    node,
                    "Internal Error: Effective flags should already have been evaluated",
                    ERROR)
        else:
            return NO_FLAGS

    def on_regular_expression(self, node):
        if node[0].name == 'flagGroups':
            flags = self.gather_flags(node[0])
            if flags:  node.attr['flags'] = flags
            node.result = node.result[1:]
            self.evaluate_flags()
        return self.fallback_compiler(node)

    def on_nonCapturing(self, node):
        if node[0].name == 'flags':
            flags = self.gather_flags(node)
            if flags:  node.attr['flags'] = flags
            for i in range(len(node.children)):
                if node[i].name != 'flags':
                    node.result = node.result[i:]
                    break
            self.evaluate_flags()
        return self.fallback_compiler(node)

    def on_pattern(self, node):
        # if 'x' in self.get_effective_flags(node).positive:  # NEED a pre-processor for this!
        #     result = [node[0]]
        #     for nd in node.children[1:]:
        #         if (result[-1].name == 'characters'
        #                 and (nd.name == 'characters' or
        #                      (nd.name == 'any'
        #                       and RX_INTERRUPTED_COMMENT.fullmatch(result[-1].content)))):
        #                 result[-1].result = result[-1].content + nd.content
        #         else:
        #             result.append(nd)
        #     if len(result) != len(node.children):
        #         node.result = tuple(result)
        node = self.fallback_compiler(node)
        replace_by_single_child(self.path)
        return node

    def on_characters(self, node):
        # content = node.content
        # if node is self.last_leaf or content.find('\n') >= 0:
        #     if RX_COMMENT.fullmatch(node.content):
        #         if 'x' in self.get_effective_flags(node).positive:
        #             return EMPTY_NODE
        return node

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
