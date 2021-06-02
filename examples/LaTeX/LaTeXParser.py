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
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    transform_content, replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, access_thread_locals, access_presets, has_children, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_tag_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory, Error, canonical_error_strings, \
    has_errors, apply_unless, WARNING, ERROR, FATAL, EMPTY_NODE, TreeReduction, CombinedParser, \
    PreprocessorResult, preprocess_includes, gen_find_include_func, flatten_sxpr, \
    gen_neutral_srcmap_func, make_preprocessor, chain_preprocessors


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


RE_INCLUDE = r'\\input{(?P<name>.*)}'


def LaTeXTokenizer(original_text) -> Tuple[str, List[Error]]:
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    find_next_include = gen_find_include_func(RE_INCLUDE, LaTeXGrammar.comment_rx__)
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    LaTeXPreprocessor = make_preprocessor(LaTeXTokenizer)
    return chain_preprocessors(include_prep, LaTeXPreprocessor)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LaTeXGrammar(Grammar):
    r"""Parser for a LaTeX source file.
    """
    block = Forward()
    block_environment = Forward()
    block_of_paragraphs = Forward()
    paragraph = Forward()
    param_block = Forward()
    text_element = Forward()
    source_hash__ = "00aaf8a57639b405c72446c2daee4627"
    disposable__ = re.compile('_WSPC$|_GAP$|_LB$|_PARSEP$|_LETTERS$|_NAME$|INTEGER$|FRAC$|_QUALIFIED$|TEXT_NOPAR$|TEXT$|_block_content$|PATH$|PATHSEP$|HASH$|COLON$|TAG$|_inline_math_text$|_has_block_start$|block_environment$|known_environment$|text_element$|_block_math$|line_element$|inline_environment$|known_inline_env$|info_block$|begin_inline_env$|end_inline_env$|command$|known_command$|_dmath_long_form$|_dmath_short_form$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'%.*'
    comment_rx__ = re.compile(COMMENT__)
    comment__ = RegExp(comment_rx__)
    WHITESPACE__ = r'[ \t]*(?:\n(?![ \t]*\n)[ \t]*)?'
    whitespace__ = Whitespace(WHITESPACE__)
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = RegExp('(?!.)')
    BACKSLASH = RegExp('[\\\\]')
    _LB = Drop(RegExp('\\s*?\\n|$'))
    NEW_LINE = Series(Drop(RegExp('[ \\t]*')), Option(comment__), Drop(RegExp('\\n')))
    _GAP = Drop(Series(RegExp('[ \\t]*(?:\\n[ \\t]*)+\\n'), dwsp__))
    _WSPC = Drop(OneOrMore(Drop(Alternative(comment__, Drop(RegExp('\\s+'))))))
    _PARSEP = Drop(Series(Drop(ZeroOrMore(Drop(Series(whitespace__, comment__)))), _GAP, Drop(Option(_WSPC))))
    S = Series(Lookahead(Drop(RegExp('[% \\t\\n]'))), NegativeLookahead(_GAP), wsp__)
    LFF = Series(NEW_LINE, Option(_WSPC))
    LF = Series(NEW_LINE, ZeroOrMore(Series(comment__, whitespace__)))
    _LETTERS = RegExp('\\w+')
    CHARS = RegExp('[^\\\\%$&\\{\\}\\[\\]\\s\\n]+')
    LINE = RegExp('[^\\\\%$&\\{\\}\\[\\]\\n]+')
    TEXT_NOPAR = RegExp('(?:[^\\\\%$&\\{\\}\\[\\]\\(\\)\\n]+(?:\\n(?![ \\t]*\\n))?)+')
    TEXT = RegExp('(?:[^\\\\%$&\\{\\}\\[\\]\\n]+(?:\\n(?![ \\t]*\\n))?)+')
    TAG = RegExp('[\\w=?.:\\-%&\\[\\] /]+')
    COLON = Text(":")
    HASH = Text("#")
    PATHSEP = RegExp('/(?!\\*)')
    PATH = RegExp('[\\w=~?.,%&\\[\\]-]+')
    UNIT = RegExp('(?!\\d)\\w+')
    FRAC = RegExp('\\.[0-9]+')
    INTEGER = RegExp('-?(?:(?:[1-9][0-9]+)|[0-9])')
    _NAME = RegExp('(?!\\d)\\w+\\*?')
    NAME = Capture(Synonym(_NAME))
    IDENTIFIER = Synonym(_NAME)
    _QUALIFIED = Series(IDENTIFIER, ZeroOrMore(Series(Drop(RegExp('[:.-]')), IDENTIFIER)))
    LINEFEED = RegExp('[\\\\][\\\\]')
    BRACKETS = RegExp('[\\[\\]]')
    SPECIAL = RegExp('[$&_/\\\\\\\\]')
    ESCAPED = RegExp('\\\\[%$&_/{} ]')
    TXTCOMMAND = RegExp('\\\\text\\w+')
    CMDNAME = Series(RegExp('\\\\@?(?:(?![\\d_])\\w)+'), dwsp__)
    WARN_Komma = Series(Text(","), dwsp__)
    esc_char = Text(",")
    number = Series(INTEGER, Option(FRAC))
    magnitude = Series(number, Option(UNIT))
    info_value = Series(TEXT_NOPAR, ZeroOrMore(Series(S, TEXT_NOPAR)))
    info_key = Series(Drop(Text("/")), _NAME)
    info_assoc = Series(info_key, dwsp__, Option(Series(Series(Drop(Text("(")), dwsp__), info_value, Series(Drop(Text(")")), dwsp__), mandatory=1)))
    info_block = Series(Series(Drop(Text("{")), dwsp__), ZeroOrMore(info_assoc), Series(Drop(Text("}")), dwsp__), mandatory=1)
    value = Alternative(magnitude, _LETTERS, CMDNAME, param_block, block)
    key = Synonym(_QUALIFIED)
    flag = Alternative(_QUALIFIED, magnitude)
    association = Series(key, dwsp__, Series(Drop(Text("=")), dwsp__), value, dwsp__)
    parameters = Series(Alternative(association, flag), ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), Alternative(association, flag))), Option(WARN_Komma))
    sequence = Series(Option(_WSPC), OneOrMore(Series(Alternative(paragraph, block_environment), Option(Alternative(_PARSEP, S)))))
    item = Series(Series(Drop(Text("\\item")), dwsp__), sequence)
    special = Alternative(Drop(Text("\\-")), Series(Drop(RegExp('\\\\')), esc_char))
    structural = Alternative(Series(Drop(Text("subsection")), dwsp__), Series(Drop(Text("section")), dwsp__), Series(Drop(Text("chapter")), dwsp__), Series(Drop(Text("subsubsection")), dwsp__), Series(Drop(Text("paragraph")), dwsp__), Series(Drop(Text("subparagraph")), dwsp__), Series(Drop(Text("item")), dwsp__))
    begin_environment = Series(Drop(RegExp('\\\\begin{')), NAME, Drop(RegExp('}')), mandatory=1)
    no_command = Alternative(Series(Drop(Text("\\begin{")), dwsp__), Series(Drop(Text("\\end")), dwsp__), Series(BACKSLASH, structural))
    text = Series(TEXT, ZeroOrMore(Series(Alternative(S, special), TEXT)))
    cfg_text = ZeroOrMore(Alternative(Series(dwsp__, text), CMDNAME, SPECIAL))
    config = Series(Series(Drop(Text("[")), dwsp__), Alternative(Series(parameters, Lookahead(Series(Drop(Text("]")), dwsp__))), cfg_text), Series(Drop(Text("]")), dwsp__), mandatory=1)
    _block_content = ZeroOrMore(Series(Alternative(block_environment, text_element, paragraph), Option(Alternative(_PARSEP, S))))
    heading = Synonym(block)
    target = Series(PATH, ZeroOrMore(Series(NegativeLookbehind(Drop(RegExp('s?ptth'))), COLON, PATH)), Option(Series(Alternative(HASH, Series(NegativeLookbehind(Drop(RegExp('s?ptth'))), COLON)), TAG)))
    path = Series(PATH, PATHSEP)
    protocol = RegExp('\\w+://(?!\\*)')
    urlstring = Series(Option(protocol), ZeroOrMore(path), Option(target))
    href = Series(Series(Drop(Text("\\href{")), dwsp__), urlstring, Series(Drop(Text("}")), dwsp__), block)
    url = Series(Series(Drop(Text("\\url{")), dwsp__), urlstring, Series(Drop(Text("}")), dwsp__))
    ref = Series(Alternative(Series(Drop(Text("\\ref{")), dwsp__), Series(Drop(Text("\\pageref{")), dwsp__)), CHARS, Series(Drop(Text("}")), dwsp__))
    label = Series(Series(Drop(Text("\\label{")), dwsp__), CHARS, Series(Drop(Text("}")), dwsp__))
    hypersetup = Series(Series(Drop(Text("\\hypersetup")), dwsp__), param_block)
    pdfinfo = Series(Series(Drop(Text("\\pdfinfo")), dwsp__), info_block)
    documentclass = Series(Series(Drop(Text("\\documentclass")), dwsp__), Option(config), block)
    cline = Series(Series(Drop(Text("\\cline{")), dwsp__), INTEGER, Series(Drop(Text("-")), dwsp__), INTEGER, Series(Drop(Text("}")), dwsp__))
    hline = Series(Text("\\hline"), dwsp__)
    cfg_celltype = RegExp('[lcrp]')
    caption = Series(Series(Drop(Text("\\caption")), dwsp__), block)
    includegraphics = Series(Series(Drop(Text("\\includegraphics")), dwsp__), Option(config), block)
    footnote = Series(Series(Drop(Text("\\footnote")), dwsp__), block_of_paragraphs)
    citep = Series(Alternative(Series(Drop(Text("\\citep")), dwsp__), Series(Drop(Text("\\cite")), dwsp__)), Option(config), block)
    citet = Series(Series(Drop(Text("\\citet")), dwsp__), Option(config), block)
    generic_command = Alternative(Series(NegativeLookahead(no_command), CMDNAME, Option(Series(Option(Series(dwsp__, config)), OneOrMore(Series(dwsp__, block))))), Series(Drop(Text("{")), CMDNAME, _block_content, Drop(Text("}")), mandatory=3))
    assignment = Series(NegativeLookahead(no_command), CMDNAME, Series(Drop(Text("=")), dwsp__), Alternative(Series(number, Option(UNIT)), block, CHARS))
    text_command = Alternative(TXTCOMMAND, ESCAPED, BRACKETS)
    cfg_unit = Series(Drop(Text("{")), number, UNIT, Drop(Text("}")))
    cfg_separator = Text("|")
    _inline_math_text = RegExp('[^$]*')
    _im_bracket = Series(Drop(Text("\\(")), _inline_math_text, Drop(Text("\\)")), mandatory=1)
    _im_dollar = Series(Drop(Text("$")), _inline_math_text, Drop(Text("$")), mandatory=1)
    inline_math = Alternative(_im_dollar, _im_bracket)
    end_environment = Series(Drop(RegExp('\\\\end{')), Pop(NAME), Drop(RegExp('}')), mandatory=1)
    begin_generic_block = Series(Lookbehind(_LB), begin_environment, LFF)
    end_inline_env = Synonym(end_environment)
    begin_inline_env = Alternative(Series(NegativeLookbehind(_LB), begin_environment), Series(begin_environment, NegativeLookahead(LFF)))
    generic_inline_env = Series(begin_inline_env, dwsp__, paragraph, end_inline_env, mandatory=3)
    known_inline_env = Synonym(inline_math)
    inline_environment = Alternative(known_inline_env, generic_inline_env)
    tabular_config = Series(Series(Drop(Text("{")), dwsp__), OneOrMore(Alternative(Series(cfg_celltype, Option(cfg_unit)), cfg_separator)), Series(Drop(Text("}")), dwsp__), mandatory=2)
    SubParagraph = Series(Series(Drop(Text("\\subparagraph")), dwsp__), heading, Option(sequence))
    SubParagraphs = OneOrMore(Series(Option(_WSPC), SubParagraph))
    Paragraph = Series(Series(Drop(Text("\\paragraph")), dwsp__), heading, ZeroOrMore(Alternative(sequence, SubParagraphs)))
    frontpages = Synonym(sequence)
    TBCFG_VALUE = Series(RegExp('[lcr|]+'), dwsp__)
    multicolumn = Series(Series(Drop(Text("\\multicolumn")), dwsp__), Series(Drop(Text("{")), dwsp__), INTEGER, Series(Drop(Text("}")), dwsp__), tabular_config, block_of_paragraphs)
    known_command = Alternative(citet, citep, footnote, includegraphics, caption, multicolumn, hline, cline, documentclass, pdfinfo, hypersetup, label, ref, href, url, item)
    command = Alternative(known_command, text_command, assignment, generic_command)
    line_element = Alternative(text, inline_environment, command, block)
    rb_down = Series(Series(Drop(Text("[")), dwsp__), number, UNIT, dwsp__, Series(Drop(Text("]")), dwsp__))
    rb_up = Series(Series(Drop(Text("[")), dwsp__), number, UNIT, dwsp__, Series(Drop(Text("]")), dwsp__))
    rb_offset = Series(Series(Drop(Text("{")), dwsp__), number, UNIT, dwsp__, Series(Drop(Text("}")), dwsp__))
    raisebox = Series(Series(Drop(Text("\\raisebox")), dwsp__), rb_offset, Option(rb_up), Option(rb_down), block)
    tabular_cell = Alternative(Series(raisebox, Option(Alternative(S, _PARSEP))), ZeroOrMore(Series(line_element, Option(Alternative(S, _PARSEP)))))
    tabular_row = Series(Alternative(multicolumn, tabular_cell), ZeroOrMore(Series(Series(Drop(Text("&")), dwsp__), Alternative(multicolumn, tabular_cell))), Alternative(Series(Series(Drop(Text("\\\\")), dwsp__), Alternative(hline, ZeroOrMore(cline)), Option(_PARSEP)), Lookahead(Drop(Text("\\end{tabular}")))))
    tabular = Series(Series(Drop(Text("\\begin{tabular}")), dwsp__), tabular_config, ZeroOrMore(tabular_row), Series(Drop(Text("\\end{tabular}")), dwsp__), mandatory=3)
    no_numbering = Text("*")
    _block_math = RegExp('(?:[^\\\\]*(?!\\\\end\\{(?:eqnarray|equation|displaymath)\\*?\\}|[\\\\]\\])[\\\\]*\\s*)*')
    eqnarray = Series(Drop(Text("\\begin{eqnarray")), Option(no_numbering), Series(Drop(Text("}")), dwsp__), _block_math, Drop(Text("\\end{eqnarray")), Option(Drop(Text("*"))), Series(Drop(Text("}")), dwsp__), mandatory=3)
    equation = Series(Drop(Text("\\begin{equation")), Option(no_numbering), Series(Drop(Text("}")), dwsp__), _block_math, Drop(Text("\\end{equation")), Option(Drop(Text("*"))), Series(Drop(Text("}")), dwsp__), mandatory=3)
    _dmath_short_form = Series(Series(Drop(Text("\\[")), dwsp__), _block_math, Series(Drop(Text("\\]")), dwsp__), mandatory=1)
    _dmath_long_form = Series(Drop(Text("\\begin{displaymath")), Option(no_numbering), Series(Drop(Text("}")), dwsp__), _block_math, Drop(Text("\\end{displaymath")), Option(Drop(Text("*"))), Series(Drop(Text("}")), dwsp__), mandatory=3)
    displaymath = Alternative(_dmath_long_form, _dmath_short_form)
    verbatim = Series(Series(Drop(Text("\\begin{verbatim}")), dwsp__), sequence, Series(Drop(Text("\\end{verbatim}")), dwsp__), mandatory=2)
    quotation = Alternative(Series(Series(Drop(Text("\\begin{quotation}")), dwsp__), sequence, Series(Drop(Text("\\end{quotation}")), dwsp__), mandatory=2), Series(Series(Drop(Text("\\begin{quote}")), dwsp__), sequence, Series(Drop(Text("\\end{quote}")), dwsp__), mandatory=2))
    figure = Series(Series(Drop(Text("\\begin{figure}")), dwsp__), sequence, Series(Drop(Text("\\end{figure}")), dwsp__), mandatory=2)
    hide_from_toc = Series(Text("*"), dwsp__)
    enumerate = Series(Series(Drop(Text("\\begin{enumerate}")), dwsp__), Option(_WSPC), ZeroOrMore(Alternative(item, command)), Series(Drop(Text("\\end{enumerate}")), dwsp__), mandatory=3)
    itemize = Series(Series(Drop(Text("\\begin{itemize}")), dwsp__), Option(_WSPC), ZeroOrMore(Alternative(item, command)), Series(Drop(Text("\\end{itemize}")), dwsp__), mandatory=3)
    end_generic_block = Series(Lookbehind(_LB), end_environment, LFF)
    blockcmd = Series(BACKSLASH, Alternative(Series(Alternative(Series(Drop(Text("begin{")), dwsp__), Series(Drop(Text("end{")), dwsp__)), Alternative(Series(Drop(Text("enumerate")), dwsp__), Series(Drop(Text("itemize")), dwsp__), Series(Drop(Text("figure")), dwsp__), Series(Drop(Text("quote")), dwsp__), Series(Drop(Text("quotation")), dwsp__), Series(Drop(Text("tabular")), dwsp__)), Series(Drop(Text("}")), dwsp__)), structural, begin_generic_block, end_generic_block))
    generic_block = Series(begin_generic_block, sequence, end_generic_block, mandatory=2)
    math_block = Alternative(equation, eqnarray, displaymath)
    known_environment = Alternative(itemize, enumerate, figure, tabular, quotation, verbatim, math_block)
    _has_block_start = Drop(Text("\\begin{"))
    preamble = OneOrMore(Series(Option(_WSPC), command))
    Paragraphs = OneOrMore(Series(Option(_WSPC), Paragraph))
    Index = Series(Option(_WSPC), Series(Drop(Text("\\printindex")), dwsp__))
    Bibliography = Series(Option(_WSPC), Series(Drop(Text("\\bibliography")), dwsp__), heading)
    SubSubSection = Series(Drop(Text("\\subsubsection")), Option(hide_from_toc), heading, ZeroOrMore(Alternative(sequence, Paragraphs)))
    SubSubSections = OneOrMore(Series(Option(_WSPC), SubSubSection))
    SubSection = Series(Drop(Text("\\subsection")), Option(hide_from_toc), heading, ZeroOrMore(Alternative(sequence, SubSubSections)))
    SubSections = OneOrMore(Series(Option(_WSPC), SubSection))
    Section = Series(Drop(Text("\\section")), Option(hide_from_toc), heading, ZeroOrMore(Alternative(sequence, SubSections)))
    Sections = OneOrMore(Series(Option(_WSPC), Section))
    Chapter = Series(Drop(Text("\\chapter")), Option(hide_from_toc), heading, ZeroOrMore(Alternative(sequence, Sections)))
    Chapters = OneOrMore(Series(Option(_WSPC), Chapter))
    document = Series(Option(_WSPC), Series(Drop(Text("\\begin{document}")), dwsp__), frontpages, Alternative(Chapters, Sections), Option(Bibliography), Option(Index), Option(_WSPC), Series(Drop(Text("\\end{document}")), dwsp__), Option(_WSPC), EOF, mandatory=2)
    param_block.set(Series(Series(Drop(Text("{")), dwsp__), Option(parameters), Series(Drop(Text("}")), dwsp__)))
    block.set(Series(Series(Drop(Text("{")), dwsp__), _block_content, Drop(Text("}")), mandatory=2))
    text_element.set(Alternative(line_element, LINEFEED))
    paragraph.set(OneOrMore(Series(NegativeLookahead(blockcmd), text_element, Option(S))))
    block_of_paragraphs.set(Series(Series(Drop(Text("{")), dwsp__), Option(sequence), Series(Drop(Text("}")), dwsp__), mandatory=2))
    block_environment.set(Alternative(Series(Lookahead(_has_block_start), known_environment), generic_block))
    latexdoc = Series(preamble, document, mandatory=1)
    root__ = TreeReduction(latexdoc, CombinedParser.MERGE_TREETOPS)
    

_raw_grammar = ThreadLocalSingletonFactory(LaTeXGrammar, ident=1)

def get_grammar() -> LaTeXGrammar:
    grammar = _raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
    
def parse_LaTeX(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def streamline_whitespace(context):
    # if context[-2].tag_name == TOKEN_PTYPE:
    #     return
    node = context[-1]
    assert node.tag_name in ['WSPC', ':Whitespace', 'S']
    s = node.content
    if s.find('%') >= 0:
        node.result = '\n'
        # c = s.find('%')
        # node.result = ('  ' if (n >= c) or (n < 0) else '\n')+ s[c:].rstrip(' \t')
        # node.parser = MockParser('COMMENT', '')
    elif s.find('\n') >= 0:
        node.result = '\n'
    else:
        node.result = ' ' if s else ''


def watch(node):
    print(node.as_sxpr())

flatten_structure = flatten(lambda context: is_one_of(
    context, {"Chapters", "Sections", "SubSections", "SubSubSections", "Paragraphs",
              "SubParagraphs", "sequence"}), recursive=True)


def transform_generic_command(context: List[Node]):
    node = context[-1]
    if node.children[0].tag_name == 'CMDNAME':
        node.tag_name = 'cmd_' + node.children[0].content.lstrip('\\')
        node.result = node.children[1:]


def transform_generic_block(context: List[Node]):
    node = context[-1]
    if not node.children or not node.children[0].children:
        context[0].new_error(node, 'unknown kind of block: ' + flatten_sxpr(node.as_sxpr()))
    else:
        # assert node.children[0].tag_name == "begin_generic_block"
        # assert node.children[0].children[0].tag_name == "begin_environment"
        # assert node.children[-1].tag_name == "end_generic_block"
        # assert node.children[-1].children[0].tag_name == "end_environment"
        node.tag_name = 'env_' + node.children[0].children[0].content.lstrip('\\')
        node.result = node.children[1:-1]


def is_expendable(context: List[Node]):
    node = context[-1]
    return not node._result and not node.tag_name.startswith('cmd_')


def show(context: List[Node]):
    print(context[-1].as_xml())


LaTeX_AST_transformation_table = {
    # AST Transformations for the LaTeX-grammar
    "<": [flatten, flatten_structure, remove_children_if(is_expendable)],
    "latexdoc": [],
    "document": [flatten_structure],
    "pdfinfo": [],
    "TEXT_NOPAR": [apply_unless(normalize_whitespace, has_children)],
    "info_assoc": [change_tag_name('association'), replace_by_single_child],
    "info_key": [change_tag_name('key')],
    "info_value": [apply_unless(normalize_whitespace, has_children), change_tag_name('value')],
    "parameters": [replace_by_single_child],
    "association": [replace_by_single_child],
    "key": reduce_single_child,
    "frontpages": reduce_single_child,
    "Chapters, Sections, SubSections, SubSubSections, Paragraphs, SubParagraphs": [],
    "Chapter, Section, SubSection, SubSubSection, Paragraph, SubParagraph": [],
    "hide_from_toc, no_numbering": [replace_content_with('')],
    "heading": reduce_single_child,
    "Bibliography": [],
    "Index": [],
    "block_environment": replace_by_single_child,
    "known_environment": replace_by_single_child,
    "generic_block": [transform_generic_block],
    "generic_command": [transform_generic_command, reduce_single_child],  # [flatten],
    "begin_generic_block, end_generic_block": [],
        # [remove_children({'NEW_LINE', 'LFF'}), replace_by_single_child],
    "itemize, enumerate": [flatten],
    "item": [],
    "figure": [],
    "quotation": [reduce_single_child, remove_brackets],
    "verbatim": [],
    "tabular": [],
    "tabular_config, block_of_paragraphs": [remove_brackets, reduce_single_child],
    "tabular_row": [flatten, remove_tokens('&', '\\')],
    "tabular_cell": [flatten, remove_whitespace],
    "multicolumn": [remove_tokens('{', '}')],
    "hline": [remove_whitespace, reduce_single_child],
    "ref, label, pageref, url": reduce_single_child,
    "sequence": [flatten],
    "paragraph": [flatten, strip(is_one_of({'S'}))],
    "text_element": replace_by_single_child,
    "line_element": replace_by_single_child,
    "inline_environment": replace_by_single_child,
    "known_inline_env": replace_by_single_child,
    "generic_inline_env": [],
    "begin_inline_env, end_inline_env": [replace_by_single_child],
    "begin_environment, end_environment": [],  # [remove_brackets, reduce_single_child],
    "inline_math": [reduce_single_child],
    "command": replace_by_single_child,
    "known_command": replace_by_single_child,
    "text_command": [],
    "citet, citep": [reduce_single_child],
    "footnote": [],
    "includegraphics": [],
    "caption": [],
    "config": [reduce_single_child],
    "cfg_text": [reduce_single_child],
    "block": [flatten, reduce_single_child],
    "flag": [reduce_single_child],
    "text": collapse,
    "no_command, blockcmd": [],
    "structural": [],
    "CMDNAME": [remove_whitespace, reduce_single_child],
    "TXTCOMMAND": [remove_whitespace, reduce_single_child],
    "NO_CMD": [add_error("unknown kind of command")],
    "NAME": [reduce_single_child, remove_whitespace, reduce_single_child],
    "ESCAPED": [transform_content(lambda node: str(node)[1:])],
    "BRACKETS": [],
    "TEXTCHUNK": [],
    "LF": [],
    "GAP": [],
    "LB": [],
    "BACKSLASH": [],
    "EOF": [],
    "PARSEP": [replace_content_with('\n\n')],
    ":Whitespace, WSPC, S": streamline_whitespace,
    "WARN_Komma": add_error('No komma allowed at the end of a list', WARNING),
    "*": apply_unless(replace_by_single_child,
                      lambda ctx: ctx[-1].tag_name[:4] not in ('cmd_', 'env_'))
}


def LaTeXTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=LaTeX_AST_transformation_table.copy())

get_transformer = ThreadLocalSingletonFactory(LaTeXTransformer, ident=1)

def transform_LaTeX(cst):
    get_transformer()(cst)


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def empty_defaultdict():
    """Returns a defaultdict with an empty defaultdict as default value."""
    return collections.defaultdict(empty_defaultdict)


class LaTeXCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a LaTeX source file.
    """
    KNOWN_DOCUMENT_CLASSES = {'book', 'article'}
    KNOWN_LANGUAGES = {'english', 'german'}

    def __init__(self):
        super(LaTeXCompiler, self).__init__()
        self.metadata = collections.defaultdict(empty_defaultdict)

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!
        self.tree.inline_tags = set()  # {'paragraph'}
        self.tree.empty_tags = set()
        self.tree.omit_tags = {'S', 'PARSEP'}

    def fallback_generic_command(self, node: Node) -> Node:
        # if not node.result:
        #      return EMPTY_NODE
        return node

    def fallback_generic_environment(self, node) -> Node:
        node = super().fallback_compiler(node)
        node.tag_name = 'VOID'
        return node

    def fallback_compiler(self, node: Node) -> Any:
        if node.tag_name.startswith('cmd_'):
            node = self.fallback_generic_command(node)
        elif node.tag_name.startswith('env_'):
            node = self.fallback_generic_environment(node)
        else:
            node = super().fallback_compiler(node)
        # replace void nodes by their children
        if node.children:
            result = [];  void_flag = False
            for child in node.children:
                if child.tag_name == 'VOID' and child.children:
                    result.extend(child.children);  void_flag = True
                else:
                    result.append(child)
            if void_flag:  # use flag, because assignment can be costly
                node.result = tuple(result)
        return node

    def on_latexdoc(self, node):
        return self.fallback_compiler(node)

    # def on_preamble(self, node):
    #     return node

    # def on_document(self, node):
    #     return node

    # def on_frontpages(self, node):
    #     return node

    # def on_Chapters(self, node):
    #     return node

    # def on_Chapter(self, node):
    #     return node

    # def on_Sections(self, node):
    #     return node

    # def on_Section(self, node):
    #     return node

    # def on_SubSections(self, node):
    #     return node

    # def on_SubSection(self, node):
    #     return node

    # def on_SubSubSections(self, node):
    #     return node

    # def on_SubSubSection(self, node):
    #     return node

    # def on_Paragraphs(self, node):
    #     return node

    # def on_Paragraph(self, node):
    #     return node

    # def on_SubParagraphs(self, node):
    #     return node

    # def on_SubParagraph(self, node):
    #     return node

    # def on_Bibliography(self, node):
    #     return node

    # def on_Index(self, node):
    #     return node

    # def on_heading(self, node):
    #     return node

    # def on_block_environment(self, node):
    #     return node

    # def on_known_environment(self, node):
    #     return node

    # def on_generic_block(self, node):
    #     return node

    # def on_begin_generic_block(self, node):
    #     return node

    # def on_end_generic_block(self, node):
    #     return node

    # def on_itemize(self, node):
    #     return node

    # def on_enumerate(self, node):
    #     return node

    # def on_item(self, node):
    #     return node

    # def on_figure(self, node):
    #     return node

    # def on_quotation(self, node):
    #     return node

    # def on_verbatim(self, node):
    #     return node

    # def on_tabular(self, node):
    #     return node

    # def on_tabular_row(self, node):
    #     return node

    # def on_tabular_cell(self, node):
    #     return node

    # def on_tabular_config(self, node):
    #     return node

    # def on_TBCFG_VALUE(self, node):
    #     return node

    # def on_block_of_paragraphs(self, node):
    #     return node

    # def on_sequence(self, node):
    #     return node

    # def on_paragraph(self, node):
    #     return node

    # def on_text_element(self, node):
    #     return node

    # def on_line_element(self, node):
    #     return node

    # def on_inline_environment(self, node):
    #     return node

    # def on_known_inline_env(self, node):
    #     return node

    # def on_generic_inline_env(self, node):
    #     return node

    # def on_begin_inline_env(self, node):
    #     return node

    # def on_end_inline_env(self, node):
    #     return node

    # def on_begin_environment(self, node):
    #     return node

    # def on_end_environment(self, node):
    #     return node

    # def on_inline_math(self, node):
    #     return node

    # def on_command(self, node):
    #     return node

    # def on_known_command(self, node):
    #     return node

    # def on_text_command(self, node):
    #     return node

    # def on_generic_command(self, node):
    #     return node

    def get_author_year(self, bibkey: str) -> str:
        return bibkey  # for now...

    def arange_citation(self, node):
        node = self.fallback_compiler(node)
        if node.children:
            config = node.pick('config')
            block = node.pick('block')
            bibkey = block.content
            if config is not None:
                assert len(node.children) == 2
                block.result = self.get_author_year(bibkey)
                node.result = (block, Node('text', ', '), config)
            else:
                node.result = self.get_author_year(bibkey)
        else:
            bibkey = node.content
            node.result = self.get_author_year(bibkey)

    def on_citet(self, node):
        self.arange_citation(node)
        return node

    def on_citep(self, node):
        self.arange_citation(node)
        if node.children:
            node.result = (Node('text', '('), *node.children, Node('text', ')'))
        else:
            node.result = '(' + node.content + ')'
        return node

    # def on_footnote(self, node):
    #     return node

    # def on_includegraphics(self, node):
    #     return node

    # def on_caption(self, node):
    #     return node

    # def on_multicolumn(self, node):
    #     return node

    # def on_hline(self, node):
    #     return node

    # def on_cline(self, node):
    #     return node

    def on_documentclass(self, node):
        """
        Saves the documentclass (if known) and the language (if given)
        in the metadata dictionary.
        """
        if 'config' in node:
            for it in {part.strip() for part in node['config'].content.split(',')}:
                if it in self.KNOWN_LANGUAGES:
                    if 'language' in self.metadata:
                        self.metadata['language'] = it
                    else:
                        self.tree.new_error(node, 'Only one document language supported. '
                                            'Using %s, ignoring %s.'
                                            % (self.metadata['language'], it), WARNING)
        if node['block'].content in self.KNOWN_DOCUMENT_CLASSES:
            self.metadata['documentclass'] = node['block'].content
        return node

    # def on_pdfinfo(self, node):
    #     return node

    # def on_config(self, node):
    #     return node

    # def on_cfg_text(self, node):
    #     return node

    # def on_block(self, node):
    #     return node

    # def on_text(self, node):
    #     return node

    # def on_no_command(self, node):
    #     return node

    # def on_blockcmd(self, node):
    #     return node

    # def on_structural(self, node):
    #     return node

    # def on_CMDNAME(self, node):
    #     return node

    # def on_TXTCOMMAND(self, node):
    #     return node

    # def on_ESCAPED(self, node):
    #     return node

    # def on_SPECIAL(self, node):
    #     return node

    # def on_BRACKETS(self, node):
    #     return node

    # def on_LINEFEED(self, node):
    #     return node

    # def on_NAME(self, node):
    #     return node

    # def on_INTEGER(self, node):
    #     return node

    # def on_TEXT(self, node):
    #     return node

    # def on_LINE(self, node):
    #     return node

    # def on_CHARS(self, node):
    #     return node

    # def on_LETTERS(self, node):
    #     return node

    # def on_LF(self, node):
    #     return node

    # def on_LFF(self, node):
    #     return node

    # def on_S(self, node):
    #     return node

    # def on__PARSEP(self, node):
    #     return node

    # def on__WSPC(self, node):
    #     return node

    # def on__GAP(self, node):
    #     return node

    # def on_NEW_LINE(self, node):
    #     return node

    # def on__LB(self, node):
    #     return node

    # def on_BACKSLASH(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


get_compiler = ThreadLocalSingletonFactory(LaTeXCompiler, ident=1)

def compile_LaTeX(ast):
    return get_compiler()(ast)


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

RESULT_FILE_EXTENSION = ".sxpr"  # Change this according to your needs!


def compile_src(source: str) -> Tuple[Any, List[Error]]:
    """Compiles ``source`` and returns (result, errors, ast)."""
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
            f.write('\n'.join(canonical_error_strings(errors, source_filename)))
        return err_filename
    return ''


def batch_process(file_names: List[str], out_dir: str,
                  *, submit_func: Callable = None,
                  log_func: Callable = None) -> List[str]:
    """Compiles all files listed in filenames and writes the results and/or
    error messages to the directory `our_dir`. Returns a list of error
    messages files.
    """
    def gen_dest_name(name):
        return os.path.join(out_dir, os.path.splitext(os.path.basename(name))[0] \
                                     + RESULT_FILE_EXTENSION)

    error_list =  []
    if get_config_value('batch_processing_parallelization'):
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

        if True or submit_func is None:
            import concurrent.futures
            import multiprocessing
            with concurrent.futures.ProcessPoolExecutor(multiprocessing.cpu_count()) as pool:
                run_batch(pool.submit)
        else:
            run_batch(submit_func)
    else:
        for name in filenames:
            if log_func:  log_func(name, gen_dest_name(name))
            error_filename = process_file(name, gen_dest_name(name), log_func)
            if error_filename:
                error_list.append(error_filename)

    return error_list


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
    parser = ArgumentParser(description="Parses a LaTeX-file and shows its syntax-tree.")
    parser.add_argument('files', nargs='+')
    parser.add_argument('-d', '--debug', action='store_const', const='debug',
                        help='Store debug information in LOGS subdirectory')
    parser.add_argument('-x', '--xml', action='store_const', const='xml',
                        help='Store result as XML instead of S-expression')
    parser.add_argument('-o', '--out', nargs=1, default=['out'],
                        help='Output directory for batch processing')
    parser.add_argument('-v', '--verbose', action='store_const', const='verbose',
                        help='Verbose output')

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
        set_config_value('history_tracking', True)
        set_config_value('resume_notices', True)
        set_config_value('log_syntax_trees', set(['cst', 'ast']))  # don't use a set literal, here!
    start_logging(log_dir)

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

        print(result.serialize(how='default' if args.xml is None else 'xml')
              if isinstance(result, Node) else result)
