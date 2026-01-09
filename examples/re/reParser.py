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
from stringprep import b1_set
from typing import Tuple, List, Set, Union, Any, Optional, Callable, cast, NamedTuple

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

from DHParser.compile import Compiler, CompilerFunc, compile_source, Junction, full_compile
from DHParser.configuration import set_config_value, add_config_values, get_config_value, \
    access_thread_locals, access_presets, finalize_presets, set_preset_value, \
    get_preset_value, NEVER_MATCH_PATTERN
from DHParser import dsl
from DHParser.dsl import recompile_grammar, never_cancel
from DHParser.ebnf import grammar_changed
from DHParser.error import ErrorCode, Error, canonical_error_strings, has_errors, NOTICE, \
    WARNING, ERROR, FATAL
from DHParser.log import start_logging, suspend_logging, resume_logging
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, RootNode, Path, ZOMBIE_TAG, \
    parse_sxpr
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, DropFrom, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, SmartRE, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, IgnoreCase, \
    LateBindingUnary, mixin_comment, last_value, matching_bracket, optional_last_value, \
    PARSER_PLACEHOLDER, UninitializedError,  RX_NEVER_MATCH
from DHParser.pipeline import end_points, full_pipeline, create_parser_junction, \
    create_preprocess_junction, create_junction, PseudoJunction, PipelineResult
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc, PreprocessorResult, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors, \
    SourceMap, source_map, result_from_mapping, gen_neutral_srcmap_func
from DHParser.stringview import StringView
from DHParser.toolkit import re, is_filename, load_if_file, cpu_count, \
    ThreadLocalSingletonFactory, expand_table, CancelQuery
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

# To capture includes, replace the NEVER_MATCH_PATTERN
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'
RE_INCLUDE = NEVER_MATCH_PATTERN
RE_COMMENT = NEVER_MATCH_PATTERN
RX_VERBOSE = re.compile(r'\(\?[aiLmsu]*x[aiLmsu]*\)')

INCOMPATIBLE_REGULAR_EXPRESSION = ErrorCode(510)
INVALID_REGULAR_EXPRESSION = ErrorCode(20010)  # fatal


def reValidate(original_text, original_name) -> PreprocessorResult:
    import re  # be sure to use Python STL re, not regex, here!
    try:
        i = len(original_text)
        _ = re.compile(original_text)
        return nil_preprocessor(original_text, original_name)
    except Exception as err:
        err_code = INVALID_REGULAR_EXPRESSION
        if re.match(r'\(\?[aixLmsu]*-[aixLmsu]*\)', original_text):
            err_code = INCOMPATIBLE_REGULAR_EXPRESSION
        return PreprocessorResult(
            original_text, original_text,
            gen_neutral_srcmap_func(original_text, original_name),
            [Error(str(err), getattr(err, 'pos', 0), err_code)])


def inCharSet(l: str, k: int) -> bool:
    i = 0
    state = 'neutral'
    while i < k:
        if state == 'escaped':
            state = 'neutral'
        elif l[i] == '\\':
            state = 'escaped'
        elif l[i] == '[':
            state = 'inset'
        elif l[i] == ']':
            state = 'neutral'
        i += 1
    return state == 'inset'


def reStripComments(original_text, original_name) -> PreprocessorResult:
    if not RX_VERBOSE.match(original_text):
        return nil_preprocessor(original_text, original_name)

    positions = [0]
    offsets = [0]
    l = original_text.splitlines(keepends=True)
    for i in range(len(l)):
        n = len(l[i])

        l[i] = l[i].lstrip()

        n = n - len(l[i])
        if n > 0:
            offsets[-1] += n

        n = len(l[i])

        k = l[i].find('#')
        while k >= 0 and inCharSet(l[i], k):
            k = l[i].find('#', k + 1)
        if k >= 0:
            l[i] = l[i][:k]
        l[i] = l[i].rstrip()

        m = len(l[i])
        n = n - m
        if m > 0:
            positions.append(positions[-1] + m)
            offsets.append(offsets[-1] + n)
        else:
            offsets[-1] += n

    stripped_text = ''.join(l)

    if positions[-1] <= len(stripped_text):
        positions.append(len(stripped_text) + 1)
        offsets.append(offsets[-1])

    mapping = SourceMap(original_name, positions, offsets,
                        [original_name] * len(positions),
                        {original_name: original_text})
    return result_from_mapping(mapping, original_text, stripped_text, [])


preprocessing: PseudoJunction = create_preprocess_junction(
    chain_preprocessors(reValidate, reStripComments), RE_INCLUDE, RE_COMMENT,
    func_type=PreprocessorFunc)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class reGrammar(Grammar):
    r"""Parser for a re document.

    Instantiate this class and then call the instance with the source
    code as the single argument in order to use the parser, e.g.:
        parser = re()
        syntax_tree = parser(source_code)
    """
    _entity = Forward()
    _item = Forward()
    sequence = Forward()
    source_hash__ = "f032ce59777a2dfc10b808a0bc4cea6e"
    early_tree_reduction__ = CombinedParser.MERGE_LEAVES
    disposable__ = re.compile('(?:_grpChar$|_grpItem$|_escape$|_nibble$|BS$|_item$|_number$|_illegal$|_extension$|_special$|EOF$|_csEsc$|_char$|_reEsc$|_octal$|_ch$|_grpChars$|_group$|_chars$|_entity$|_escapedCh$|_anyChar$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r''
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp('.')))
    bs = RegExp('\\\\')
    BS = Drop(Synonym(bs))
    _anyChar = RegExp('[^|+*?]')
    _char = Series(NegativeLookahead(_entity), _anyChar)
    char = Series(_char, NegativeLookahead(_char))
    charSeq = Series(_char, OneOrMore(_char))
    _grpChar = Series(NegativeLookahead(_entity), RegExp('[^)|+*?]'))
    grpChar = Series(_grpChar, NegativeLookahead(_grpChar))
    grpCharSeq = Series(_grpChar, OneOrMore(_grpChar))
    _grpChars = Alternative(grpChar, grpCharSeq)
    _chars = Alternative(char, charSeq)
    _grpItem = Alternative(_entity, _grpChars)
    zeroOrOne = Text("?")
    zeroOrMore = Text("*")
    _number = RegExp('[0-9]+')
    groupName = RegExp('(?!\\d)\\w+')
    groupId = RegExp('\\d\\d?')
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
    fixedChSet = RegExp('[dDsSwW]')
    _ch = Series(NegativeLookahead(Drop(Text("]"))), Option(BS), RegExp('.'))
    ch = Synonym(_ch)
    chSpecial = RegExp('[abfnrtv]')
    _nibble = RegExp('[0-9a-fA-F]')
    _csEsc = Series(BS, fixedChSet)
    hex2 = Counted(_nibble, repetitions=(2, 2))
    hex4 = Counted(_nibble, repetitions=(4, 4))
    complement = Text("^")
    hex8 = Counted(_nibble, repetitions=(8, 8))
    absEnd = RegExp('[zZ]')
    absStart = RegExp('[aA]')
    wordBorder = RegExp('[bB]')
    _illegal = RegExp('[a-zA-Z]')
    error = Series(Lookahead(_illegal), Custom(ERR("Unknown escape sequence")), _illegal)
    groupRef = RegExp('\\d\\d?')
    escCh = Alternative(_anyChar, RegExp('[)|+*?]'))
    chName = Series(Drop(Text("N{")), RegExp('[\\w ]+'), Drop(Text("}")))
    _octal = RegExp('[0-7]')
    oct = Alternative(Series(Drop(Text("0")), Counted(_octal, repetitions=(0, 3))), Counted(_octal, repetitions=(3, 3)))
    chCode = Alternative(Series(Drop(Text("x")), hex2), Series(Drop(Text("u")), hex4), Series(Drop(Text("U")), hex8), oct)
    _escapedCh = Series(BS, Alternative(chCode, chSpecial))
    chRange = Series(Alternative(_escapedCh, ch), Drop(Text("-")), NegativeLookahead(_csEsc), Alternative(_escapedCh, ch))
    chSet = Series(_ch, ZeroOrMore(Series(NegativeLookahead(_csEsc), NegativeLookahead(chRange), NegativeLookahead(_escapedCh), NegativeLookahead(BS), _ch)))
    charset = Series(Drop(Text("[")), Option(complement), OneOrMore(Alternative(_csEsc, chRange, _escapedCh, Series(BS, error), chSet)), Drop(Text("]")))
    specialEsc = RegExp('[afnrtv]')
    _reEsc = Series(Lookahead(RegExp('[AbBdDsSwWZ]')), Alternative(fixedChSet, wordBorder, absStart, absEnd))
    _escape = Series(BS, Alternative(bs, chCode, chName, groupRef, _reEsc, specialEsc, error, escCh), mandatory=1)
    end = Text("$")
    start = Text("^")
    any = Text(".")
    _special = Alternative(any, start, end)
    noBacktracking = Text("+")
    notGreedy = Text("?")
    grpRepetition = Series(_grpItem, repType, Option(Alternative(notGreedy, noBacktracking)))
    grpSequence = ZeroOrMore(Alternative(grpRepetition, _grpItem))
    grpAlternative = Series(grpSequence, ZeroOrMore(Series(Drop(Text("|")), grpSequence)))
    lookaround = Series(lrtype, grpAlternative, mandatory=1)
    namedGroup = Series(Drop(Text("P<")), groupName, Drop(Text(">")), grpAlternative, mandatory=1)
    subRegex = Series(Drop(Text(">")), grpAlternative, mandatory=1)
    capturing = Synonym(grpAlternative)
    bifurcation = Series(Drop(Text("(")), Alternative(groupId, groupName), Drop(Text(")")), sequence, Drop(Text("|")), grpSequence, mandatory=1)
    repetition = Series(_item, repType, Option(Alternative(notGreedy, noBacktracking)))
    nonCapturing = Series(Option(flags), Drop(Text(":")), grpAlternative, mandatory=2)
    _extension = Series(Drop(Text("?")), Alternative(nonCapturing, subRegex, namedGroup, backRef, comment, lookaround, bifurcation), mandatory=1)
    _group = Series(Drop(Text("(")), Alternative(_extension, capturing), Drop(Text(")")), mandatory=1)
    flagGroups = OneOrMore(Series(Drop(Text("(?")), flags, Drop(Text(")")), mandatory=2))
    alternative = Series(sequence, ZeroOrMore(Series(Drop(Text("|")), sequence)))
    _entity.set(Alternative(_special, _escape, charset, _group))
    _item.set(Alternative(_entity, _chars))
    sequence.set(ZeroOrMore(Alternative(repetition, _item)))
    regular_expression = Series(Option(flagGroups), Alternative(alternative, Drop(Text(")"))), EOF)
    root__ = regular_expression
    
parsing: PseudoJunction = create_parser_junction(reGrammar)
get_grammar = parsing.factory  # for backwards compatibility, only

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


SPECIAL_MAP = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v' }


re_AST_transformation_table = {
    # AST Transformations for the re-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],  # called for each node after calling its specific rules
    "regular_expression": [],
    # "group": [replace_by_single_child],
    "alternative, grpAlternative": [change_name('alternative'), replace_by_single_child],
    "sequence, grpSequence": [change_name('sequence'),
                            merge_adjacent(is_one_of('charSeq')),
                            replace_by_single_child],
    "grpRepetition": [change_name('repetition')],
    "hex2, hex4, hex8": [transform_result(lambda r: chr(int(r, 16)))],
    "oct": [transform_result(lambda r: chr(int(r, 8)))],
    "grpItem, _grpItem": [change_name('item')],
    "grpChar, char": [change_name('char')],
    "grpChars, grpCharSeq": [change_name('charSeq')],
    "nonCapturing": [apply_if(replace_by_single_child, neg(has_child('flags')))],
    "escCh, bs": [change_name('charSeq')],
    "ch": [],  # [change_name('char')],
    "chCode": [change_name('ch'), reduce_single_child],
    "chSpecial": [change_name('ch'), transform_result(lambda r: SPECIAL_MAP[r])],
    "specialEsc": [change_name('char'), transform_result(lambda r: SPECIAL_MAP[r])],
    "charset": [merge_adjacent(is_one_of('chSet', 'ch'), 'chSet'),
                # replace_child_names({'ch': 'chSet'})
                ],
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
        return f"({''.join(sorted(self.positive))},{''.join(sorted(self.negative))})"

NO_FLAGS = Flags(set(), set())
FLAG_SET = frozenset({
    'a',   # ASCII-only
    'i',   # ignore case
    'L',   # locale dependent (this will be ignored!)
    'm',   # multi-line, i.e. ^ and $ also match the beginning and end of the line
    's',   # dot matches all, including newline characters
    'u',   # Unicode (default)
    'x'    # verbose (global only, preprocessor take care of this)
})

# RX_INTERRUPTED_COMMENT = re.compile(r'([ \t]*(?:#.*)?\n)*(?:[ \t]*(?:#.*)$)')
# RX_COMMENT = re.compile(r'([ \t]*(?:#.*)?\n)*(?:[ \t]*(?:#.*)?$)?')

FLAGS_WARNING        = ErrorCode(520)
FLAGS_ERROR          = ErrorCode(2020)
DUPLICATE_CHARACTERS = ErrorCode(2030)

# default_start = parse_sxpr('(lookaround (lrtype "<!") (any "."))')
# default_end = parse_sxpr('(lookaround (lrtype "!") (any "."))')
# multiline_start = parse_sxpr('(alternative (lookaround (lrtype "<=") (specialEsc "n")) (lookaround (lrtype "<!") (any ".")))')
# multiline_end = parse_sxpr('(alternative (lookaround (lrtype "=") (specialEsc "n")) (lookaround (lrtype "!") (any ".")))')
# word_border = parse_sxpr('(alternative (sequence (lookaround (lrtype "<!") (fixedChSet "L")) (lookaround (lrtype "=") (fixedChSet "L")))'
#                                ' (sequence (lookaround (lrtype "<=") (fixedChSet "L")) (lookaround (lrtype "!") (fixedChSet "L"))))')
default_start = Node('lookaround', (Node('lrtype', '<!'), Node('any', '.')))
default_end   = Node('lookaround', (Node('lrtype', '!'), Node('any', '.')))
multiline_start = Node('alternative', (Node('lookaround', (Node('lrtype', '<='), Node('specialEsc', 'n'))),
                                 Node('lookaround', (Node('lrtype', '<!'), Node('any', '.')))))
multiline_end   = Node('alternative', (Node('lookaround', (Node('lrtype', '='), Node('specialEsc', 'n'))),
                                 Node('lookaround', (Node('lrtype', '!'), Node('any', '.')))))
word_border = Node('alternative', (Node('sequence', (Node('lookaround', (Node('lrtype', '<!'), Node('fixedChSet', 'L'))),
                                              Node('lookaround', (Node('lrtype', '='), Node('fixedChSet', 'L'))))),
                             Node('sequence', (Node('lookaround', (Node('lrtype', '<='), Node('fixedChSet', 'L'))),
                                              Node('lookaround', (Node('lrtype', '!'), Node('fixedChSet', 'L')))))))
no_word_border = Node('alternative', (Node('sequence', (Node('lookaround', (Node('lrtype', '<='), Node('fixedChSet', 'L'))),
                                                 Node('lookaround', (Node('lrtype', '='), Node('fixedChSet', 'L'))))),
                                Node('sequence', (Node('lookaround', (Node('lrtype', '<!'), Node('fixedChSet', 'L'))),
                                                 Node('lookaround', (Node('lrtype', '!'), Node('fixedChSet', 'L')))))))


class FlagProcessing(Compiler):
    """Compiler for the abstract-syntax-tree of a 
        re source file.
    """

    def __init__(self):
        super(FlagProcessing, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        self.last_leaf: Node = EMPTY_NODE
        self.effective_flags: Flags = NO_FLAGS
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "AST", f"Source stage `AST` expected, `but `{root.stage}` found."
        root.stage = "flagsDone"
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
            self.tree.new_error(
                node, f'One or more flags in: "{pstr}" are redundant!', FLAGS_WARNING)
        if len(nflags) > len(nstr):
            self.tree.new_error(
                node, f'One or more flags in: "-{nstr}" are redundant!', FLAGS_WARNING)
        if pflags & nflags:
            self.tree.new_error(
                node, f'Cannot set and unset "{pflags & nflags}" at the same time!', FLAGS_ERROR)
        if 'L' in pflags:
            self.tree.new_error(node, 'Flag "L" ("locale dependent") is ignored!', FLAGS_WARNING)
        if 'a' in pflags and 'u' in pflags:
            self.tree.new_error(
                node, 'Flag "a" ("ASCII-only") and "u" ("Unicode") must not be set '
                'at the same time!', FLAGS_ERROR)
        if 'u' in nflags:  pflags.add('a')
        return Flags(pflags, nflags)

    def evaluate_flags(self) -> Flags:
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
        return effective

    def on_regular_expression(self, node):
        save = self.effective_flags
        if node[0].name == 'flagGroups':
            flags = self.gather_flags(node[0])
            if flags:  node.attr['flags'] = flags
            node.result = node.result[1:]
            self.effective_flags = self.evaluate_flags()
        node = self.fallback_compiler(node)
        self.effective_flags = save
        return node

    def on_nonCapturing(self, node):
        save = self.effective_flags
        if node[0].name == 'flags':
            verbose_already = 'x' in self.effective_flags.positive
            flags = self.gather_flags(node)
            if flags:  node.attr['flags'] = flags
            for i in range(len(node.children)):
                if node[i].name != 'flags':
                    node.result = node.result[i:]
                    break
            self.effective_flags = self.evaluate_flags()
            if 'x' in self.effective_flags.positive \
                    and not verbose_already:
                self.tree.new_error(node,
                    'Flag "x" ("verbose") is ignored in non-capturing groups! '
                    'In order to allow verbose regular expressions, please '
                    'place the flag "x" at the very beginning of your pattern '
                    'with the flag group "(?x)".', WARNING)
        node = self.fallback_compiler(node)
        self.effective_flags = save
        if len(node.result) == 1 and not node.result[0].has_attr():
            replace_by_single_child(self.path)
        return node

    def on_absStart(self, node):
        assert not node.children
        assert node.result in ('A', 'a')
        start = copy.deepcopy(default_start)
        for nd in start.walk_tree():  nd._pos = node._pos
        node.name = 'lookaround'
        node.attr['re'] = r'\A'
        node.result = start.children
        return node

    def on_absEnd(self, node):
        assert not node.children
        assert node.result in ('Z', 'Z')
        end = copy.deepcopy(default_end)
        for nd in end.walk_tree():  nd._pos = node._pos
        node.name = 'lookaround'
        node.attr['re'] = r'\Z'
        node.result = end.children
        return node

    def on_start(self, node):
        assert not node.children
        assert node.result == '^'
        multiline = 'm' in self.effective_flags.positive
        start = copy.deepcopy(multiline_start) if multiline \
            else copy.deepcopy(default_start)
        for nd in start.walk_tree():  nd._pos = node._pos
        node.name = 'nonCapturing' if multiline else 'lookaround'
        node.attr['re'] = node.result
        node.result = start.children
        return node

    def on_end(self, node):
        assert not node.children
        assert node.result == '$'
        multiline = 'm' in self.effective_flags.positive
        end = copy.deepcopy(multiline_end) if multiline \
            else copy.deepcopy(default_end)
        for nd in end.walk_tree():  nd._pos = node._pos
        node.name = 'nonCapturing' if multiline else 'lookaround'
        node.attr['re'] = node.result
        node.result = end.children
        return node

    def on_wordBorder(self, node):
        assert not node.children
        assert node.result in ('b', 'B')
        wb = copy.deepcopy(word_border) if node.result == 'b' else copy.deepcopy(no_word_border)
        for nd in wb.walk_tree():
            nd._pos = node._pos
            if nd.name == 'fixedChSet':
                if 'a' in self.effective_flags.positive:
                    nd.attr['set'] = 'ascii_alpha'
                else:
                    nd.attr['set'] = 'alpha'
        node.name = 'alternative'
        node.attr['re'] = '\\' + node.result
        return node

    def on_fixedChSet(self, node):
        assert not node.children
        assert node.result in "dDsSwW"
        chset = { 'd': 'decimal', 's': 'space', 'w': 'identifier' }[node.result.lower()]
        ascii = 'ascii_' if 'a' in self.effective_flags.positive else ''
        node.attr['set'] = ascii + chset
        if node.result.isupper():
            node.attr['complement'] = '^'
            node.result = node.result.lower()
        node.attr['re'] = '\\' + node.result
        return node

    def on_charSeq(self, node):
        # node = self.fallback_compiler(node)
        assert not node.children
        if 'i' in self.effective_flags.positive:
            seq = []
            for d, ch in enumerate(node.result):
                if ch.lower() == ch.upper():
                    if len(seq) > 0 and seq[-1].name == 'charSeq':
                        seq[-1].result += ch
                    else:
                        seq.append(Node('charSeq', ch).with_pos(node.pos + d))
                else:
                    chSet = Node('chSet', ch.upper() + ch.lower())
                    seq.append(Node('charset', chSet).with_pos(node.pos + d))
            if len(self.path) > 1 and (len(seq) > 1 or seq[-1].name != 'charSeq'):
                node.name = 'sequence'
                node.attr['re'] = node.result
                node.result = tuple(seq)
        return node

    def on_char(self, node):
        """If the ignore case flag ist set, and the character is case-sensitive,
        turn the character into a character set containing both the lower- and
        the upper-case version of the character.
        """
        if 'i' in self.effective_flags.positive:
            assert not node.children
            assert len(node.result) == 1
            upper = node.result.upper()
            lower = node.result.lower()
            if upper != lower:
                node.name = "charset"
                node.attr['re'] = node.result
                node.result = Node(
                    'chSet', upper + lower).with_pos(node.pos)
        return node

    def on_chSet(self, node):
        """Check for duplicate characters and emit an error. If the ignore case
        flag is set, add the missing case for each character. Finally, normalize
        the character set by sorting the characters in ascending order according
        to their ordinal value (i.e. Unicode code point).
        """
        letters = set(node.result)
        if len(letters) != len(node.result):
            dupl = {ch for ch in letters if node.result.count(ch) > 1}
            self.tree.new_error(
                node, f'Duplicate characters {dupl} in character set {repr(node.result)}!',
                DUPLICATE_CHARACTERS)
        if 'i' in self.effective_flags.positive:
            node.attr['re'] = node.result
            node.result = ''.join((sorted(set(node.result.lower()) | set(node.result.upper()))))
        else:
            node.result = ''.join(sorted(letters))
        return node

    def on_chRange(self, node):
        """Reduce character ranges of size 1 to single charcters.
        If the ignore case flag is set and the range contains case-sensitive
        characters, make it two character ranges, one for lower-case and one
        for upper-case characters.
        """
        node = self.fallback_compiler(node)
        assert node.children
        assert len(node.result) == 2
        assert all(nd.name == 'ch' and not nd.children and len(nd.result) == 1
                   for nd in node.result)
        a1 = node.result[0].result
        b1 = node.result[1].result
        assert a1 <= b1
        if a1 == b1:
            node.name = "chSet"
            node.result = a1
            self.on_chSet(node)
        elif 'i' in self.effective_flags.positive:
            a1 = a1.upper()
            a2 = a1.lower()
            if a1 > a2: a1, a2 = a2, a1
            b1 = b1.upper()
            b2 = b1.lower()
            if b1 > b2: b1, b2 = b2, b1
            if (a1 != a1 or b1 != b2):
                assert a1 < a2 and b1 < b2, f"{(a1, b1), (a2, b2)}"
                node.result[0].result = a1
                node.result[1].result = b1
                if a2 <= chr(ord(b1) + 1):
                    node.result[1].result = b2
                elif len(self.path) > 1:
                    nd = Node('chRange', (Node('ch', a2), Node('ch', b2)))\
                        .with_pos(node.pos).with_attr(re=None)
                    parent = self.path[-2]
                    i = parent.index(node)
                    parent.insert(i + 1, nd)
        return node

    def on_charset(self, node):
        node = self.fallback_compiler(node)
        if node[0].name == 'complement':
            node.result = node[1:]
            node.attr['complement'] = '^'
        return node

    def on_any(self, node):
        assert not node.children
        assert node.result == '.'
        if 's' not in self.effective_flags.positive:
            node.name = 'charset'
            node.result = (Node('complement', '^').with_pos(node.pos),
                           Node('ch', '\n').with_pos(node.pos))
        return node

    def on_sequence(self, node):
        node = self.fallback_compiler(node)
        replace_by_single_child(self.path)
        return node


flagProcessing: Junction = create_junction(
    FlagProcessing, "AST", "flagsDone")


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################


#######################################################################
#
# Normalize CharSets
#
#######################################################################


class NormalizeCharsets(Compiler):
    """Normalizes and Optimizies character sets as well as alternatives
    of character sets and character set differences (e.g. (?![aeiou][a-z]))
    """

    def __init__(self):
        super(NormalizeCharsets, self).__init__()
        self.forbid_returning_None = True  # set to False if any compilation-method is allowed to return None

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def prepare(self, root: RootNode) -> None:
        assert root.stage == "flagsDone", f"Source stage `flagsDone` expected, " \
                f"`but `{root.stage}` found."
        root.stage = "normalized"

    def finalize(self, result: Any) -> Any:
        return result

    def on_ch(self, node: Node) -> Node:
        """convert ch-node to char-range"""
        ch = node.content
        node.name = 'chRange'
        node.result = (Node('ch', ch).with_pos(node.pos),
                       Node('ch', ch).with_pos(node.pos))
        return node

    def on_chSet(self, node: Node) -> Node:
        """convert ch-set node to char-range"""
        ranges = tuple(Node('chRange', (Node('ch', ch).with_pos(node.pos + i),
                                        Node('ch', ch).with_pos(node.pos + i)))
                       for i, ch in enumerate(node.content))
        node.name = 'charset'
        node.result = ranges
        return node

    def on_chRange(self, node: Node) -> Node:
        # do not compile children!
        return node

    def on_fixedChSet(self, node: Node) -> Node:
        r"""convert fixed characters sets (e.g. \s) to char-ranges"""
        if not get_config_value('re.KeepFixedCharSets'):
            import unicodeCharSets
            chRange = lambda t: \
                Node('chRange', (Node('ch', chr(t[0])), Node('ch', chr(t[1])))).with_pos(node.pos)
            node.name = 'charset'
            node.result = tuple(chRange(t) for t in getattr(unicodeCharSets, node.attr['set']))
        return node

    def on_charset(self, node: Node) -> Node:
        """Replace nested charset-nodes, which always stem from converted chSet-
        or fixedChSet-Nodes by their children."""
        assert node.children
        needs_to_move = lambda nd: nd.name == 'fixedChSet' and nd.has_attr('complement')
        move = []
        if node.pick_child(needs_to_move):
            stay = []
            for child in node.children:
                if needs_to_move(child):
                    move.append(self.compile(child))
                else:
                    stay.append(child)
            node.result = tuple(stay)

        node = self.fallback_compiler(node)
        new_result = []
        for child in node.children:
            if child.name == "charset":
                assert all(nd.name == "chRange" for nd in child.children)
                new_result.extend(child.children)
            else:
                new_result.append(child)

        if move:
            head = Node('charset', tuple(new_result)).with_pos(node.pos)
            if node.has_attr('complement'):
                for m in move:  del m.attr['complement']
                node.name = 'intersection'
                head.attr['complement'] = '^'
                del node.attr['complement']
            else:
                node.name = 'alternative'
            node.result = (head, *move)
        else:
            node.result = tuple(new_result)
        return node


normalizeCharsets: Junction = create_junction(
    NormalizeCharsets, "flagsDone", "normalized")


#######################################################################
#
# Re-serialization
#
#######################################################################

def ch_code(ch: str) -> str:
    if len(ch) == 1:
        n = ord(ch)
        if 0x20 <= n < 0x7f:
            return ch
        elif n <= 0xff:
            return "\\x" + f"{n:#04x}"[2:]
        elif n <= 0xffff:
            return "\\u" + f"{n:#06x}"[2:]
        elif n <= 0xffffff:
            return "\\U" + f"{n:#08x}"[2:]
        else:
            raise ValueError(f"Illegal character code {n:#0Ax} for character '{ch}'")
    else:
        assert ch[:2] in ("\\x", "\\u", "\\U")
        return ch


def group_if(cond: bool, delimiter: str, items: Tuple[str]) -> str:
    res = delimiter.join(items)
    return ''.join(['(?:', res, ')']) if cond else res


re_serialization_table = expand_table({
    "fixedChSet": lambda p, s: "\\" + (s.upper() if p[-1].has_attr('complement') else s),
    "alternative":  lambda p, *ts:
        group_if(len(p) > 1 and p[-2].name in ("sequence", "repetition"), '|', ts),
    "sequence, charSeq": lambda p, *ts:
        group_if(len(p) > 1 and p[-2].name == "repetition", '', ts),
    "repetition": lambda _, *ts: ''.join(ts),
    "any": lambda _, s: '.',
    "charset": lambda p, *ts: ''.join([('[^' if p[-1].has_attr('complement') else '['), *ts, ']']),
    "ch, char": lambda _, s: ch_code(s),
    "chRange": lambda _, *ts: ''.join([ch_code(ts[0]), '-', ch_code(ts[1])])
                              if ts[0] != ts[1] else ch_code(ts[0]),
    "chSet": lambda _, s: ''.join(ch_code(ch) for ch in s),
    "specialEsc": lambda _, s: '\\' + s,
    "lookaround": lambda _, *ts: ''.join(['(?', *ts, ')']),
    "lrtype, complement, repType, zeroOrOne, zeroOrMore, oneOrMore, min, max, groupId, groupName":
        lambda _, s: s,
    "nonCapturing": lambda _, *ts: ''.join(['(?:', *ts, ')']),
    "capturing": lambda _, *ts: ''.join(['(', *ts, ')']),
    "namedGroup": lambda _, *ts: ''.join([f'(?P<{ts[0]}>', *ts[1:], ')']),
    "range": lambda _, *ts: ''.join(['{', ', '.join(ts), '}']),
    "regular_expression": lambda _, *ts: ''.join(ts),
    "subRegex": lambda _, *ts: ''.join(['(?>', ', '.join(ts), ')']),
    "notGreedy": lambda _, s: '?',
    "groupRef": lambda _, s: '\\' + s,
    "backRef": lambda _, s: f"(?P={s})",
    "bifurcation": lambda _, *ts: f"(?({ts[0]}){ts[1]}|{ts[2]})",
    "intersection": lambda _, *ts: ''.join(['[', '&&'.join(ts), ']']),
    "*": lambda p, *ts: f"(!{p[-1].name}:" + ''.join(ts) + ")"
})

def serialize_re(regex_AST: Node) -> str:
    return regex_AST.evaluate_path(re_serialization_table, [regex_AST])

def reSerializer() -> CompilerFunc:
    return serialize_re

re_from_AST = Junction("AST", reSerializer, "regex_AST")
re_from_flagsDone = Junction("flagsDone", reSerializer, "regex_flagsDone")
re_from_normalized = Junction("normalized", reSerializer, "regex_normalized")


#######################################################################
#
# Post-Processing-Stages [add one or more postprocessing stages, here]
#
#######################################################################

# TODO: Serialization of both AST and flagsDone stage,
#       probably possible with one and the same function
# TODO: Optimize regex tree after flagsDone-stage, most notably
#       use charsets as much as possible, introducing set
#       substraction, here. Otherwise simplify tree, here, i.e.
#       some node types may be dropped, some constructs (charsets)
#       simplified.
# TODO: Compile optimized tree to a PEG-tree (== EBNF-AST)
# TODO: Serialization of EBNF-AST needed in DHParser.ebnf-module

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
junctions = {ASTTransformation, re_from_AST, flagProcessing, re_from_flagsDone,
             normalizeCharsets, re_from_normalized}

# put your targets of interest, here. A target is the name of result (or stage)
# of any transformation, compilation or postprocessing step after parsing.
# Serializations of the stages listed here will be written to disk when
# calling process_file() or batch_process() and also appear in test-reports.
targets = end_points(junctions)
# alternative: targets = set([flagProcessing.dst])

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

def pipeline(source: str,
             target: Union[str, Set[str]] = "{NAME}",
             start_parser: str = "root_parser__",
             *, cancel_query: Optional[CancelQuery] = None) -> PipelineResult:
    """Runs the source code through the processing pipeline. If
    the parameter target is not the empty string, only the stages required
    for the given target will be passed. See :py:func:`compile_src` for the
    explanation of the other parameters.
    """
    global targets
    if target:
        target_set = set([target]) if isinstance(target, str) else target
    else:
        target_set = targets
    return full_pipeline(
        source, preprocessing.factory, parsing.factory, junctions, target_set,
        start_parser, cancel_query = cancel_query)


def compile_src(source: str, target: str = "flagsDone") -> Tuple[Any, List[Error]]:
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

    read_local_config(os.path.join(scriptpath, 'reConfig.ini'))

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
