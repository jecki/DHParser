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
from DHParser.compile import Compiler, compile_source
from DHParser.pipeline import full_pipeline, Junction, PseudoJunction, create_preprocess_junction, \
    create_parser_junction, create_junction
from DHParser.configuration import set_config_value, get_config_value, access_thread_locals, \
    access_presets, finalize_presets, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN
from DHParser import dsl
from DHParser.dsl import recompile_grammar, never_cancel
from DHParser.ebnf import grammar_changed, EBNF_AST_transformation_table
from DHParser.error import ErrorCode, Error, canonical_error_strings, has_errors, ERROR, FATAL
from DHParser.log import start_logging, suspend_logging, resume_logging
from DHParser.nodetree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE, RootNode
from DHParser.parse import Grammar, PreprocessorToken, Whitespace, Drop, AnyChar, Parser, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, ERR, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, Custom, mixin_comment, \
    last_value, matching_bracket, optional_last_value
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc, PreprocessorResult, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors
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
    has_attr, has_parent, traverse
from DHParser import parse as parse_namespace__


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


def get_preprocessor() -> PreprocessorFunc:
    return nil_preprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class FixedEBNFGrammar(Grammar):
    r"""Parser for a FixedEBNF source file.
    """
    countable = Forward()
    element = Forward()
    expression = Forward()
    source_hash__ = "8c6cd9632a94beeab184261dccaf25f4"
    disposable__ = re.compile('(?:$.)|(?:countable$|is_mdef$|MOD_SYM$|component$|pure_elem$|EOF$|no_range$|MOD_SEP$|ANY_SUFFIX$|FOLLOW_UP$)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'definition': [(re.compile(r','), 'Delimiter "," not expected in definition!\\nEither this was meant to be a directive and the directive symbol @ is missing\\nor the error is due to inconsistent use of the comma as a delimiter\\nfor the elements of a sequence.')]}
    COMMENT__ = r'(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/|\(\*(?:.|\n)*?\*\)'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    RAISE_EXPR_WO_BRACKETS = Text("")
    HEXCODE = RegExp('[A-Fa-f0-9]{1,8}')
    SYM_REGEX = RegExp('(?!\\d)\\w+')
    RE_CORE = RegExp('(?:(?<!\\\\)\\\\(?:/)|[^/])*')
    MOD_SYM = Drop(Text("->"))
    CH_LEADIN = Text("0x")
    RE_LEADOUT = Text("/")
    RE_LEADIN = Text("/")
    TIMES = Text("*")
    RNG_DELIM = Text(",")
    RNG_CLOSE = Text("}")
    RNG_OPEN = Text("{")
    ENDL = Text("")
    AND = Text("")
    OR = Text("|")
    DEF = Text("=")
    EOF = Drop(NegativeLookahead(RegExp('.')))
    name = Synonym(SYM_REGEX)
    placeholder = Series(Series(Text("$"), dwsp__), name, NegativeLookahead(Text("(")), dwsp__)
    multiplier = Series(RegExp('[1-9]\\d*'), dwsp__)
    whitespace = Series(RegExp('~'), dwsp__)
    any_char = Series(Text("."), dwsp__)
    character = Series(CH_LEADIN, HEXCODE)
    regexp = Series(RE_LEADIN, RE_CORE, RE_LEADOUT, dwsp__)
    plaintext = Alternative(Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), dwsp__), Series(RegExp('´(?:(?<!\\\\)\\\\´|[^´])*?´'), dwsp__))
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), dwsp__), Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), dwsp__), Series(RegExp('’(?:(?<!\\\\)\\\\’|[^’])*?’'), dwsp__))
    symbol = Series(SYM_REGEX, dwsp__)
    argument = Alternative(literal, Series(name, dwsp__))
    parser = Series(Series(Text("@"), dwsp__), name, Series(Text("("), dwsp__), Option(argument), Series(Text(")"), dwsp__), mandatory=3)
    no_range = Drop(Alternative(NegativeLookahead(multiplier), Series(Lookahead(multiplier), TIMES)))
    macro = Series(Series(Text("$"), dwsp__), name, Series(Text("("), dwsp__), no_range, expression, ZeroOrMore(Series(Series(Text(","), dwsp__), no_range, expression)), Series(Text(")"), dwsp__))
    range = Series(RNG_OPEN, dwsp__, multiplier, Option(Series(RNG_DELIM, dwsp__, multiplier)), RNG_CLOSE, dwsp__)
    counted = Alternative(Series(countable, range), Series(countable, TIMES, dwsp__, multiplier), Series(multiplier, TIMES, dwsp__, countable, mandatory=3))
    option = Alternative(Series(Series(Text("["), dwsp__), expression, Series(Text("]"), dwsp__), mandatory=1), Series(element, Series(Text("?"), dwsp__)))
    repetition = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}"), dwsp__), mandatory=2), Series(element, Series(Text("*"), dwsp__), no_range))
    oneormore = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}+"), dwsp__)), Series(element, Series(Text("+"), dwsp__)))
    group = Series(Series(Text("("), dwsp__), no_range, expression, Series(Text(")"), dwsp__), mandatory=2)
    retrieveop = Alternative(Series(Text("::"), dwsp__), Series(Text(":?"), dwsp__), Series(Text(":"), dwsp__))
    flowmarker = Alternative(Series(Text("!"), dwsp__), Series(Text("&"), dwsp__), Series(Text("<-!"), dwsp__), Series(Text("<-&"), dwsp__))
    ANY_SUFFIX = RegExp('[?*+]')
    is_mdef = Series(Series(Text("$"), dwsp__), name, Option(Series(Series(Text("("), dwsp__), placeholder, ZeroOrMore(Series(Series(Text(","), dwsp__), placeholder)), Series(Text(")"), dwsp__))), dwsp__, DEF)
    pure_elem = Series(element, NegativeLookahead(ANY_SUFFIX), mandatory=1)
    MOD_SEP = RegExp(' *: *')
    hide = Alternative(Series(Text("HIDE"), dwsp__), Series(Text("Hide"), dwsp__), Series(Text("hide"), dwsp__), Series(Text("DISPOSE"), dwsp__), Series(Text("Dispose"), dwsp__), Series(Text("dispose"), dwsp__))
    drop = Alternative(Series(Text("DROP"), dwsp__), Series(Text("Drop"), dwsp__), Series(Text("drop"), dwsp__), Series(Text("SKIP"), dwsp__), Series(Text("Skip"), dwsp__), Series(Text("skip"), dwsp__))
    part = Series(Alternative(oneormore, pure_elem), Option(Series(MOD_SYM, dwsp__, drop)))
    term = Series(Alternative(oneormore, counted, repetition, option, pure_elem), Option(Series(MOD_SYM, dwsp__, drop)))
    difference = Series(term, Option(Series(NegativeLookahead(Text("->")), Series(Text("-"), dwsp__), part, mandatory=2)))
    lookaround = Series(flowmarker, part, mandatory=1)
    interleave = Series(difference, ZeroOrMore(Series(Series(Text("°"), dwsp__), Option(Series(Text("§"), dwsp__)), difference)))
    sequence = Series(Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround), ZeroOrMore(Series(AND, dwsp__, Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround))))
    modifier = Series(Alternative(drop, Option(hide)), MOD_SEP)
    FOLLOW_UP = Alternative(Text("@"), Text("$"), modifier, symbol, EOF)
    is_def = Alternative(Series(Option(Series(MOD_SEP, symbol)), DEF), Series(MOD_SEP, is_mdef))
    macrobody = Synonym(expression)
    definition = Series(Option(modifier), symbol, DEF, dwsp__, Option(Series(OR, dwsp__)), expression, Option(Series(MOD_SYM, dwsp__, hide)), ENDL, dwsp__, Lookahead(FOLLOW_UP), mandatory=2)
    procedure = Series(SYM_REGEX, Series(Text("()"), dwsp__))
    literals = OneOrMore(literal)
    component = Alternative(regexp, literals, procedure, Series(symbol, NegativeLookahead(is_def)), Series(Lookahead(Text("$")), NegativeLookahead(is_mdef), placeholder, NegativeLookahead(is_def), mandatory=2), Series(Series(Text("("), dwsp__), expression, Series(Text(")"), dwsp__)), Series(RAISE_EXPR_WO_BRACKETS, expression))
    directive = Series(Series(Text("@"), dwsp__), symbol, Series(Text("="), dwsp__), component, ZeroOrMore(Series(Series(Text(","), dwsp__), component)), Lookahead(FOLLOW_UP), mandatory=1)
    macrodef = Series(Option(modifier), Series(Text("$"), dwsp__), name, dwsp__, Option(Series(Series(Text("("), dwsp__), placeholder, ZeroOrMore(Series(Series(Text(","), dwsp__), placeholder)), Series(Text(")"), dwsp__), mandatory=1)), DEF, dwsp__, Option(Series(OR, dwsp__)), macrobody, Option(Series(MOD_SYM, dwsp__, hide)), ENDL, dwsp__, Lookahead(FOLLOW_UP))
    element.set(Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(is_def)), literal, plaintext, regexp, Series(character, dwsp__), any_char, whitespace, group, Series(macro, NegativeLookahead(is_def)), Series(placeholder, NegativeLookahead(is_def)), parser))
    countable.set(Alternative(option, oneormore, element))
    expression.set(Series(sequence, ZeroOrMore(Series(OR, dwsp__, sequence))))
    syntax = Series(dwsp__, ZeroOrMore(Alternative(definition, directive, macrodef)), EOF)
    resume_rules__ = {'definition': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')],
                      'directive': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')]}
    root__ = syntax
        
parsing: PseudoJunction = create_parser_junction(FixedEBNFGrammar)
get_grammar = parsing.factory # for backwards compatibility, only


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

# EBNF_AST_transformation_table imported form DHParser.ebnf


def CreateFixedEBNFTransformer() -> TransformerFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(transformer,
                   transformation_table=EBNF_AST_transformation_table.copy(),
                   src_stage='cst', dst_stage='ast')


def get_transformer() -> TransformerFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.FixedEBNF_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.FixedEBNF_00000001_transformer_singleton = CreateFixedEBNFTransformer()
        transformer = THREAD_LOCALS.FixedEBNF_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class FixedEBNFCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a FixedEBNF source file.
    """

    def __init__(self):
        super(FixedEBNFCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_syntax(self, node):
        return self.fallback_compiler(node)

    # def on_definition(self, node):
    #     return node

    # def on_directive(self, node):
    #     return node

    # def on_literals(self, node):
    #     return node

    # def on_procedure(self, node):
    #     return node

    # def on_FOLLOW_UP(self, node):
    #     return node

    # def on_expression(self, node):
    #     return node

    # def on_sequence(self, node):
    #     return node

    # def on_interleave(self, node):
    #     return node

    # def on_lookaround(self, node):
    #     return node

    # def on_difference(self, node):
    #     return node

    # def on_term(self, node):
    #     return node

    # def on_countable(self, node):
    #     return node

    # def on_pure_elem(self, node):
    #     return node

    # def on_element(self, node):
    #     return node

    # def on_ANY_SUFFIX(self, node):
    #     return node

    # def on_flowmarker(self, node):
    #     return node

    # def on_retrieveop(self, node):
    #     return node

    # def on_group(self, node):
    #     return node

    # def on_oneormore(self, node):
    #     return node

    # def on_repetition(self, node):
    #     return node

    # def on_option(self, node):
    #     return node

    # def on_counted(self, node):
    #     return node

    # def on_range(self, node):
    #     return node

    # def on_no_range(self, node):
    #     return node

    # def on_multiplier(self, node):
    #     return node

    # def on_symbol(self, node):
    #     return node

    # def on_literal(self, node):
    #     return node

    # def on_plaintext(self, node):
    #     return node

    # def on_regexp(self, node):
    #     return node

    # def on_char_range(self, node):
    #     return node

    # def on_character(self, node):
    #     return node

    # def on_free_char(self, node):
    #     return node

    # def on_any_char(self, node):
    #     return node

    # def on_whitespace(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node

    # def on_DEF(self, node):
    #     return node

    # def on_OR(self, node):
    #     return node

    # def on_AND(self, node):
    #     return node

    # def on_ENDL(self, node):
    #     return node

    # def on_RNG_OPEN(self, node):
    #     return node

    # def on_RNG_CLOSE(self, node):
    #     return node

    # def on_RNG_DELIM(self, node):
    #     return node

    # def on_TIMES(self, node):
    #     return node

    # def on_RE_LEADIN(self, node):
    #     return node

    # def on_RE_LEADOUT(self, node):
    #     return node

    # def on_CH_LEADIN(self, node):
    #     return node

    # def on_char_range_heuristics(self, node):
    #     return node

    # def on_literal_heuristics(self, node):
    #     return node

    # def on_regex_heuristics(self, node):
    #     return node

    # def on_RE_CORE(self, node):
    #     return node

    # def on_SYM_REGEX(self, node):
    #     return node

    # def on_HEXCODE(self, node):
    #     return node



def get_compiler() -> FixedEBNFCompiler:
    """Returns a thread/process-exclusive FixedEBNFCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.FixedEBNF_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.FixedEBNF_00000001_compiler_singleton = FixedEBNFCompiler()
        compiler = THREAD_LOCALS.FixedEBNF_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

def compile_src(source: str):
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
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_MESSAGES.txt')
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
    parser = ArgumentParser(description="Parses a FixedEBNF-file and shows its syntax-tree.")
    parser.add_argument('files', nargs=1)
    parser.add_argument('-d', '--debug', action='store_const', const='debug')
    outformat = parser.add_mutually_exclusive_group()
    outformat.add_argument('-x', '--xml', action='store_const', const='xml')
    outformat.add_argument('-s', '--sxpr', action='store_const', const='sxpr')
    outformat.add_argument('-t', '--tree', action='store_const', const='tree')
    outformat.add_argument('-j', '--json', action='store_const', const='json')

    args = parser.parse_args()
    file_name, log_dir = args.files[0], ''

    if not os.path.exists(file_name):
        print('File "%s" not found!' % file_name)
        sys.exit(1)
    if not os.path.isfile(file_name):
        print('"%s" is not a file!' % file_name)
        sys.exit(1)

    if args.debug is not None:
        log_dir = 'LOGS'
        set_config_value('history_tracking', True)
        set_config_value('resume_notices', True)
        set_config_value('log_syntax_trees', set(['cst', 'ast']))  # don't use a set literal, here
    start_logging(log_dir)

    result, errors, _ = compile_src(file_name)

    if errors:
        cwd = os.getcwd()
        rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
        for error in errors:
            print(rel_path + ':' + str(error))
        sys.exit(1)
    else:
        if args.xml:  outfmt = 'xml'
        elif args.sxpr:  outfmt = 'sxpr'
        elif args.tree:  outfmt = 'tree'
        elif args.json:  outfmt = 'json'
        else:  outfmt = 'default'
        print(result.serialize(how=outfmt) if isinstance(result, Node) else result)
