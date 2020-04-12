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
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, Interleave, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    merge_adjacent, collapse, collapse_children_if, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def FlexibleEBNFPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return FlexibleEBNFPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class FlexibleEBNFGrammar(Grammar):
    r"""Parser for a FlexibleEBNF source file.
    """
    AND = Forward()
    BRACE_SIGN = Forward()
    CH_LEADIN = Forward()
    DEF = Forward()
    ENDL = Forward()
    OR = Forward()
    RNG_DELIM = Forward()
    TIMES = Forward()
    character = Forward()
    element = Forward()
    expression = Forward()
    source_hash__ = "962e48ea1622c9b397ef94805c4588ad"
    anonymous__ = re.compile('pure_elem$|FOLLOW_UP$|SYM_REGEX$|EOF$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'definition': [(re.compile(r','), 'Delimiter "," not expected in definition!\\nEither this was meant to be a directive and the directive symbol @ is missing\\nor the error is due to inconsistent use of the comma as a delimiter\\nfor the elements of a sequence.')]}
    resume_rules__ = {'definition': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')],
                      'directive': [re.compile(r'\n\s*(?=@|\w+\w*\s*=)')]}
    COMMENT__ = r'(?!#x[A-Fa-f0-9])#.*(?:\n|$)|\/\*(?:.|\n)*?\*\/'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(Drop(Series(Drop(NegativeLookahead(RegExp('.'))), Drop(Option(Drop(Pop(DEF, match_func=optional_last_value)))), Drop(Option(Drop(Pop(OR, match_func=optional_last_value)))), Drop(Option(Drop(Pop(AND, match_func=optional_last_value)))), Drop(Option(Drop(Pop(ENDL, match_func=optional_last_value)))), Drop(Option(Drop(Pop(RNG_DELIM, match_func=optional_last_value)))), Drop(Option(Drop(Pop(BRACE_SIGN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(CH_LEADIN, match_func=optional_last_value)))), Drop(Option(Drop(Pop(TIMES, match_func=optional_last_value)))))))
    CH_LEADIN.set(Capture(Alternative(Token("0x"), Token("#x"))))
    TIMES.set(Capture(Token("*")))
    RNG_DELIM.set(Capture(Token(",")))
    BRACE_SIGN.set(Capture(Token("{")))
    RNG_BRACE = Capture(Retrieve(BRACE_SIGN))
    ENDL.set(Capture(Alternative(Token(";"), Token(""))))
    AND.set(Capture(Alternative(Token(","), Token(""))))
    OR.set(Capture(Token("|")))
    DEF.set(Capture(Alternative(Token("="), Token(":="), Token("::="))))
    HEXCODE = OneOrMore(RegExp('[A-Fa-f0-9]'))
    SYM_REGEX = RegExp('(?!\\d)\\w+')
    whitespace = Series(RegExp('~'), dwsp__)
    char_range = Series(Series(Token('['), dwsp__), character, Series(Token('-'), dwsp__), character, Series(Token(']'), dwsp__))
    character.set(Series(Retrieve(CH_LEADIN), HEXCODE))
    regexp = Series(RegExp('/(?:(?<!\\\\)\\\\(?:/)|[^/])*?/'), dwsp__)
    plaintext = Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), dwsp__)
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), dwsp__), Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), dwsp__))
    symbol = Series(SYM_REGEX, dwsp__)
    multiplier = Series(RegExp('\\d+'), dwsp__)
    RANGE = Series(RNG_BRACE, dwsp__, multiplier, Option(Series(Retrieve(RNG_DELIM), dwsp__, multiplier)), Pop(RNG_BRACE, match_func=matching_bracket), dwsp__)
    counted = Alternative(Series(element, RANGE), Series(element, Retrieve(TIMES), dwsp__, multiplier), Series(multiplier, Retrieve(TIMES), dwsp__, element, mandatory=3))
    option = Alternative(Series(NegativeLookahead(char_range), Series(Token("["), dwsp__), expression, Series(Token("]"), dwsp__), mandatory=2), Series(element, Series(Token("?"), dwsp__)))
    repetition = Alternative(Series(Series(Token("{"), dwsp__), NegativeLookahead(multiplier), expression, Series(Token("}"), dwsp__), mandatory=2), Series(element, Series(Token("*"), dwsp__), NegativeLookahead(multiplier)))
    oneormore = Alternative(Series(Series(Token("{"), dwsp__), NegativeLookahead(multiplier), expression, Series(Token("}+"), dwsp__)), Series(element, Series(Token("+"), dwsp__)))
    group = Series(Series(Token("("), dwsp__), NegativeLookahead(multiplier), expression, Series(Token(")"), dwsp__), mandatory=2)
    retrieveop = Alternative(Series(Token("::"), dwsp__), Series(Token(":?"), dwsp__), Series(Token(":"), dwsp__))
    flowmarker = Alternative(Series(Token("!"), dwsp__), Series(Token("&"), dwsp__), Series(Token("<-!"), dwsp__), Series(Token("<-&"), dwsp__))
    element.set(Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(DEF)), literal, plaintext, regexp, char_range, character, whitespace, group))
    pure_elem = Series(element, NegativeLookahead(RegExp('[?*+]')), mandatory=1)
    term = Alternative(oneormore, counted, repetition, option, pure_elem)
    difference = Series(term, Option(Series(Series(Token("-"), dwsp__), Alternative(oneormore, pure_elem), mandatory=1)))
    lookaround = Series(flowmarker, Alternative(oneormore, pure_elem), mandatory=1)
    interleave = Series(difference, ZeroOrMore(Series(Series(Token("°"), dwsp__), Option(Series(Token("§"), dwsp__)), difference)))
    sequence = Series(Option(Series(Token("§"), dwsp__)), Alternative(interleave, lookaround), ZeroOrMore(Series(Retrieve(AND), dwsp__, Option(Series(Token("§"), dwsp__)), Alternative(interleave, lookaround))))
    expression.set(Series(sequence, ZeroOrMore(Series(Retrieve(OR), dwsp__, sequence))))
    FOLLOW_UP = Alternative(Token("@"), symbol, EOF)
    procedure = Series(SYM_REGEX, Series(Token("()"), dwsp__))
    literals = OneOrMore(literal)
    directive = Series(Series(Token("@"), dwsp__), symbol, Series(Token("="), dwsp__), Alternative(regexp, literals, procedure, symbol), ZeroOrMore(Series(Series(Token(","), dwsp__), Alternative(regexp, literals, procedure, symbol))), Lookahead(FOLLOW_UP), mandatory=1)
    definition = Series(symbol, Retrieve(DEF), dwsp__, expression, Retrieve(ENDL), dwsp__, Lookahead(FOLLOW_UP), mandatory=1, err_msgs=error_messages__["definition"])
    syntax = Series(Option(Series(dwsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF)
    root__ = syntax
    

def get_grammar() -> FlexibleEBNFGrammar:
    """Returns a thread/process-exclusive FlexibleEBNFGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.FlexibleEBNF_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.FlexibleEBNF_00000001_grammar_singleton = FlexibleEBNFGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.FlexibleEBNF_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.FlexibleEBNF_00000001_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

FlexibleEBNF_AST_transformation_table = {
    # AST Transformations for the FlexibleEBNF-grammar
    "<": flatten,
    "syntax": [],
    "definition": [],
    "directive": [],
    "expression": [],
    "sequence": [],
    "interleave": [],
    "lookaround": [],
    "term": [],
    "pure_elem": [],
    "element": [],
    "flowmarker": [],
    "retrieveop": [],
    "group": [],
    "oneormore": [],
    "repetition": [],
    "option": [],
    "symbol": [],
    "literal": [],
    "plaintext": [],
    "regexp": [],
    "whitespace": [],
    "EOF": [],
    "DEF": [],
    "OR": [],
    "AND": [],
    "ENDL": [],
    "*": replace_by_single_child
}



def CreateFlexibleEBNFTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=FlexibleEBNF_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.FlexibleEBNF_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.FlexibleEBNF_00000001_transformer_singleton = CreateFlexibleEBNFTransformer()
        transformer = THREAD_LOCALS.FlexibleEBNF_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class FlexibleEBNFCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a FlexibleEBNF source file.
    """

    def __init__(self):
        super(FlexibleEBNFCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_syntax(self, node):
        return self.fallback_compiler(node)

    # def on_definition(self, node):
    #     return node

    # def on_directive(self, node):
    #     return node

    # def on_expression(self, node):
    #     return node

    # def on_sequence(self, node):
    #     return node

    # def on_interleave(self, node):
    #     return node

    # def on_lookaround(self, node):
    #     return node

    # def on_term(self, node):
    #     return node

    # def on_pure_elem(self, node):
    #     return node

    # def on_element(self, node):
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

    # def on_symbol(self, node):
    #     return node

    # def on_literal(self, node):
    #     return node

    # def on_plaintext(self, node):
    #     return node

    # def on_regexp(self, node):
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



def get_compiler() -> FlexibleEBNFCompiler:
    """Returns a thread/process-exclusive FlexibleEBNFCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.FlexibleEBNF_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.FlexibleEBNF_00000001_compiler_singleton = FlexibleEBNFCompiler()
        compiler = THREAD_LOCALS.FlexibleEBNF_00000001_compiler_singleton
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
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path):
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

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
            set_config_value('history_tracking', True)
            set_config_value('resume_notices', True)
            set_config_value('log_syntax_trees', set(('cst', 'ast')))
        start_logging(log_dir)
        result, errors, _ = compile_src(file_name)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.serialize('xml') if isinstance(result, Node) else result)
    else:
        print("Usage: FlexibleEBNFParser.py [FILENAME]")
