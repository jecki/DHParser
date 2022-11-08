#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from functools import partial
import os
import sys
from typing import Tuple, List

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
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_result, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory, NEVER_MATCH_PATTERN, Error, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def newTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as newGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, '#.*')
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(newTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


def preprocess_new(source):
    return get_preprocessor()(source)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class FlexibleEBNFGrammar(Grammar):
    r"""Parser for a FlexibleEBNF source file.
    """
    countable = Forward()
    element = Forward()
    expression = Forward()
    source_hash__ = "e6d7b1125c464e928175aee7a068f744"
    disposable__ = re.compile('component$|pure_elem$|countable$|FOLLOW_UP$|SYM_REGEX$|ANY_SUFFIX$|EOF$')
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
    regex_heuristics = Series(NegativeLookahead(Alternative(RegExp(' +`[^`]*` +/'), RegExp(' +´[^´]*´ +/'), RegExp(" +'[^']*' +/"), RegExp(' +"[^"]*" +/'), RegExp(' +\\w+ +/'))), Alternative(RegExp('[^/\\n*?+\\\\]*[*?+\\\\][^/\\n]*/'), RegExp('[^\\w]+/'), RegExp('[^ ]')))
    literal_heuristics = Alternative(RegExp('~?\\s*"(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^"]*)*"'), RegExp("~?\\s*'(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^']*)*'"), RegExp('~?\\s*`(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^`]*)*`'), RegExp('~?\\s*´(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^´]*)*´'), RegExp('~?\\s*/(?:[\\\\]\\]|[^\\]]|[^\\\\]\\[[^/]*)*/'))
    more_than_one_blank = RegExp('[^ \\]]*[ ][^ \\]]*[ ]')
    char_range_heuristics = NegativeLookahead(Alternative(RegExp('[\\n]'), more_than_one_blank, Series(dwsp__, literal_heuristics), Series(dwsp__, Option(Alternative(Text("::"), Text(":?"), Text(":"))), SYM_REGEX, RegExp('\\s*\\]'))))
    CH_LEADIN = Capture(Alternative(Text("0x"), Text("#x")), zero_length_warning=False)
    RE_LEADOUT = Capture(Text("/"), zero_length_warning=False)
    RE_LEADIN = Capture(Alternative(Series(Text("/"), Lookahead(regex_heuristics)), Text("^/")), zero_length_warning=False)
    TIMES = Capture(Text("*"), zero_length_warning=False)
    RNG_DELIM = Capture(Text(","), zero_length_warning=False)
    BRACE_SIGN = Capture(Alternative(Text("{"), Text("(")), zero_length_warning=False)
    RNG_BRACE = Capture(Retrieve(BRACE_SIGN), zero_length_warning=True)
    ENDL = Capture(Alternative(Text(";"), Text("")), zero_length_warning=False)
    AND = Capture(Alternative(Text(","), Text("")), zero_length_warning=False)
    OR = Capture(Alternative(Text("|"), Series(Text("/"), NegativeLookahead(regex_heuristics))), zero_length_warning=False)
    _DEF = Alternative(Text("="), Text(":="), Text("::="), Text("<-"), RegExp(':\\n'), Text(": "))
    DEF = Capture(Synonym(_DEF), zero_length_warning=False)
    EOF = Drop(Series(Drop(NegativeLookahead(RegExp('.'))), Drop(Option(Drop(Pop(ENDL, match_func=optional_last_value)))), Drop(Option(Drop(Pop(DEF, match_func=optional_last_value)))), Drop(Option(Drop(Pop(OR, match_func=optional_last_value)))), Drop(Option(Drop(Pop(AND, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RNG_DELIM, match_func=optional_last_value)))), Drop(Option(Drop(Pop(BRACE_SIGN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(CH_LEADIN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(TIMES, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RE_LEADIN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RE_LEADOUT, match_func=optional_last_value))))))
    whitespace = Series(RegExp('~'), dwsp__)
    any_char = Series(Text("."), dwsp__)
    free_char = Alternative(RegExp('[^\\n\\[\\]\\\\]'), RegExp('\\\\[nrtfv`´\'"(){}\\[\\]/\\\\]'))
    character = Series(Retrieve(CH_LEADIN), HEXCODE)
    char_range = Series(Text("["), Lookahead(char_range_heuristics), Option(Text("^")), Alternative(character, free_char), ZeroOrMore(Alternative(Series(Option(Text("-")), character), free_char)), Series(Text("]"), dwsp__))
    regexp = Series(Retrieve(RE_LEADIN), RE_CORE, Retrieve(RE_LEADOUT), dwsp__)
    plaintext = Alternative(Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), dwsp__), Series(RegExp('´(?:(?<!\\\\)\\\\´|[^´])*?´'), dwsp__))
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), dwsp__), Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), dwsp__))
    symbol = Series(SYM_REGEX, dwsp__)
    name = Series(SYM_REGEX, dwsp__)
    argument = Alternative(literal, name)
    parser = Series(Series(Text("@"), dwsp__), name, Series(Text("("), dwsp__), Option(argument), Series(Text(")"), dwsp__))
    multiplier = Series(RegExp('[1-9]\\d*'), dwsp__)
    no_range = Alternative(NegativeLookahead(multiplier), Series(Lookahead(multiplier), Retrieve(TIMES)))
    range = Series(RNG_BRACE, dwsp__, multiplier, Option(Series(Retrieve(RNG_DELIM), dwsp__, multiplier)), Pop(RNG_BRACE, match_func=matching_bracket), dwsp__)
    counted = Alternative(Series(countable, range), Series(countable, Retrieve(TIMES), dwsp__, multiplier), Series(multiplier, Retrieve(TIMES), dwsp__, countable, mandatory=3))
    option = Alternative(Series(NegativeLookahead(char_range), Series(Text("["), dwsp__), expression, Series(Text("]"), dwsp__), mandatory=2), Series(element, Series(Text("?"), dwsp__)))
    repetition = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}"), dwsp__), mandatory=2), Series(element, Series(Text("*"), dwsp__), no_range))
    oneormore = Alternative(Series(Series(Text("{"), dwsp__), no_range, expression, Series(Text("}+"), dwsp__)), Series(element, Series(Text("+"), dwsp__)))
    group = Series(Series(Text("("), dwsp__), no_range, expression, Series(Text(")"), dwsp__), mandatory=2)
    retrieveop = Alternative(Series(Text("::"), dwsp__), Series(Text(":?"), dwsp__), Series(Text(":"), dwsp__))
    flowmarker = Alternative(Series(Text("!"), dwsp__), Series(Text("&"), dwsp__), Series(Text("<-!"), dwsp__), Series(Text("<-&"), dwsp__))
    ANY_SUFFIX = RegExp('[?*+]')
    literals = OneOrMore(literal)
    pure_elem = Series(element, NegativeLookahead(ANY_SUFFIX), mandatory=1)
    procedure = Series(SYM_REGEX, Series(Text("()"), dwsp__))
    term = Alternative(oneormore, counted, repetition, option, pure_elem)
    difference = Series(term, Option(Series(Series(Text("-"), dwsp__), Alternative(oneormore, pure_elem), mandatory=1)))
    lookaround = Series(flowmarker, Alternative(oneormore, pure_elem), mandatory=1)
    interleave = Series(difference, ZeroOrMore(Series(Series(Text("°"), dwsp__), Option(Series(Text("§"), dwsp__)), difference)))
    sequence = Series(Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround), ZeroOrMore(Series(NegativeLookahead(Text("@")), NegativeLookahead(Series(symbol, Retrieve(DEF))), Retrieve(AND), dwsp__, Option(Series(Text("§"), dwsp__)), Alternative(interleave, lookaround))))
    FOLLOW_UP = Alternative(Text("@"), symbol, EOF)
    definition = Series(symbol, Retrieve(DEF), dwsp__, Option(Series(Retrieve(OR), dwsp__)), expression, Retrieve(ENDL), dwsp__, Lookahead(FOLLOW_UP), mandatory=1)
    component = Alternative(regexp, literals, procedure, Series(symbol, NegativeLookahead(_DEF)), Series(Series(Text("("), dwsp__), expression, Series(Text(")"), dwsp__)), Series(RAISE_EXPR_WO_BRACKETS, expression))
    directive = Series(Series(Text("@"), dwsp__), symbol, Series(Text("="), dwsp__), component, ZeroOrMore(Series(Series(Text(","), dwsp__), component)), Lookahead(FOLLOW_UP), mandatory=1)
    element.set(Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(Retrieve(DEF))), literal, plaintext, regexp, char_range, Series(character, dwsp__), any_char, whitespace, group, parser))
    countable.set(Alternative(option, oneormore, element))
    expression.set(Series(sequence, ZeroOrMore(Series(Retrieve(OR), dwsp__, sequence))))
    syntax = Series(dwsp__, ZeroOrMore(Alternative(definition, directive)), EOF)
    resume_rules__ = {'definition': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')],
                      'directive': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')]}
    root__ = syntax
    

_raw_grammar = ThreadLocalSingletonFactory(FlexibleEBNFGrammar)

def get_grammar() -> FlexibleEBNFGrammar:
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
    
def parse_FlexibleEBNF(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match=complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

EBNF_AST_transformation_table = {
    # AST Transformations for the EBNF-grammar
    "<":
        [remove_children_if(all_of(not_one_of('regexp'), is_empty))],
    "syntax":
        [],
    "directive":
        [flatten, remove_tokens('@', '=', ',')],
    "procedure":
        [remove_tokens('()'), reduce_single_child],
    "literals":
        [replace_by_single_child],
    "definition":
        [flatten, remove_children('DEF', 'ENDL'),
         remove_tokens('=')],  # remove_tokens('=') is only for backwards-compatibility
    "expression":
        [replace_by_single_child, flatten, remove_children('OR'),
         remove_tokens('|')],  # remove_tokens('|') is only for backwards-compatibility
    "sequence":
        [replace_by_single_child, flatten, remove_children('AND')],
    "interleave":
        [replace_by_single_child, flatten, remove_tokens('°')],
    "lookaround":
        [],
    "difference":
        [remove_tokens('-'), replace_by_single_child],
    "term, pure_elem, element":
        [replace_by_single_child],
    "flowmarker, retrieveop":
        [reduce_single_child],
    "group":
        [remove_brackets],
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets,  # remove_tokens('?', '*', '+'),
         forbid('repetition', 'option', 'oneormore'), assert_content(r'(?!§)(?:.|\n)*')],
    "counted":
        [remove_children('TIMES')],
    "range":
        [remove_children('BRACE_SIGN', 'RNG_BRACE', 'RNG_DELIM')],
    "symbol, literal, any_char":
        [reduce_single_child],
    "plaintext":
        [],
    "regexp":
        [remove_children('RE_LEADIN', 'RE_LEADOUT'), reduce_single_child],
    "char_range":
        [flatten, remove_tokens('[', ']')],
    "character":
        [remove_children('CH_LEADIN'), reduce_single_child],
    "free_char":
        [],
    (TOKEN_PTYPE, WHITESPACE_PTYPE, "whitespace"):
        [reduce_single_child],
    "EOF, DEF, OR, AND, ENDL, BRACE_SIGN, RNG_BRACE, RNG_DELIM, TIMES, "
    "RE_LEADIN, RE_CORE, RE_LEADOUT, CH_LEADIN":
        [],
    "*":
        [replace_by_single_child]
}



def CreateEBNFTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=EBNF_AST_transformation_table.copy())


def get_transformer() -> TransformerCallable:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.EBNF_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.EBNF_00000001_transformer_singleton = CreateEBNFTransformer()
        transformer = THREAD_LOCALS.EBNF_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class EBNFCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a EBNF source file.
    """

    def __init__(self):
        super(EBNFCompiler, self).__init__()

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

    # def on_RNG_BRACE(self, node):
    #     return node

    # def on_BRACE_SIGN(self, node):
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



def get_compiler() -> EBNFCompiler:
    """Returns a thread/process-exclusive EBNFCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.EBNF_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.EBNF_00000001_compiler_singleton = EBNFCompiler()
        compiler = THREAD_LOCALS.EBNF_00000001_compiler_singleton
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
    parser = ArgumentParser(description="Parses a EBNF-file and shows its syntax-tree.")
    parser.add_argument('files', nargs=1)
    parser.add_argument('-d', '--debug', action='store_const', const='debug')
    parser.add_argument('-x', '--xml', action='store_const', const='xml')

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
