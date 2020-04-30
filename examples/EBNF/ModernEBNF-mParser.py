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
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Interleave, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
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

def ModernEBNF_mPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return ModernEBNF_mPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ModernEBNF_mGrammar(Grammar):
    r"""Parser for a ModernEBNF_m source file.
    """
    expression = Forward()
    retrieveop = Forward()
    source_hash__ = "9f678046c464f55a73dbbdc37728b9ea"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'#.*(?:\n|$)'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = NegativeLookahead(RegExp('.'))
    whitespace = Series(RegExp('~'), dwsp__)
    regexp = Series(RegExp('/(?:(?<!\\\\)\\\\(?:/)|[^/])*?/'), dwsp__)
    plaintext = Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), dwsp__)
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), dwsp__), Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), dwsp__))
    symbol = Series(RegExp('(?!\\d)\\w+'), dwsp__)
    group = Series(Series(Text("("), dwsp__), expression, Series(Text(")"), dwsp__), mandatory=1)
    element = Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(Series(Text("="), dwsp__))), literal, plaintext, regexp, whitespace, group)
    option = Series(element, Series(Text("?"), dwsp__))
    repetition = Series(element, Series(Text("*"), dwsp__))
    oneormore = Series(element, Series(Text("+"), dwsp__))
    interleave = Alternative(oneormore, repetition, option, element)
    unordered = Series(interleave, OneOrMore(Series(Series(Text("^"), dwsp__), interleave)))
    retrieveop.set(Alternative(Series(Text("::"), dwsp__), Series(Text(":"), dwsp__)))
    flowmarker = Alternative(Series(Text("!"), dwsp__), Series(Text("&"), dwsp__), Series(Text("-!"), dwsp__), Series(Text("-&"), dwsp__))
    term = Alternative(repetition, option, Series(Option(flowmarker), Alternative(unordered, oneormore, element)))
    sequence = OneOrMore(Series(Option(Series(Text("§"), dwsp__)), term))
    expression.set(Series(sequence, ZeroOrMore(Series(Series(Text("|"), dwsp__), sequence))))
    directive = Series(Series(Text("@"), dwsp__), symbol, Series(Text("="), dwsp__), Alternative(regexp, literal, symbol), ZeroOrMore(Series(Series(Text(","), dwsp__), Alternative(regexp, literal, symbol))), mandatory=1)
    definition = Series(symbol, Series(Text("="), dwsp__), expression, mandatory=1)
    syntax = Series(Option(Series(dwsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF, mandatory=2)
    root__ = syntax
    

def get_grammar() -> ModernEBNF_mGrammar:
    """Returns a thread/process-exclusive ModernEBNF_mGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.ModernEBNF_m_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.ModernEBNF_m_00000001_grammar_singleton = ModernEBNF_mGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.ModernEBNF_m_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.ModernEBNF_m_00000001_grammar_singleton
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

ModernEBNF_m_AST_transformation_table = {
    # AST Transformations for the ModernEBNF_m-grammar
    "<": flatten,
    "syntax": [],
    "definition": [],
    "directive": [],
    "expression": [],
    "sequence": [],
    "term": [],
    "flowmarker": [],
    "retrieveop": [],
    "unordered": [],
    "interleave": [],
    "oneormore": [],
    "repetition": [],
    "option": [],
    "element": [],
    "group": [],
    "symbol": [],
    "literal": [],
    "plaintext": [],
    "regexp": [],
    "whitespace": [],
    "EOF": [],
    "*": replace_by_single_child
}



def CreateModernEBNF_mTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=ModernEBNF_m_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.ModernEBNF_m_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.ModernEBNF_m_00000001_transformer_singleton = CreateModernEBNF_mTransformer()
        transformer = THREAD_LOCALS.ModernEBNF_m_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ModernEBNF_mCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ModernEBNF_m source file.
    """

    def __init__(self):
        super(ModernEBNF_mCompiler, self).__init__()

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

    # def on_term(self, node):
    #     return node

    # def on_flowmarker(self, node):
    #     return node

    # def on_retrieveop(self, node):
    #     return node

    # def on_unordered(self, node):
    #     return node

    # def on_interleave(self, node):
    #     return node

    # def on_oneormore(self, node):
    #     return node

    # def on_repetition(self, node):
    #     return node

    # def on_option(self, node):
    #     return node

    # def on_element(self, node):
    #     return node

    # def on_group(self, node):
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



def get_compiler() -> ModernEBNF_mCompiler:
    """Returns a thread/process-exclusive ModernEBNF_mCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.ModernEBNF_m_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.ModernEBNF_m_00000001_compiler_singleton = ModernEBNF_mCompiler()
        compiler = THREAD_LOCALS.ModernEBNF_m_00000001_compiler_singleton
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
            print(result.serialize() if isinstance(result, Node) else result)
    else:
        print("Usage: ModernEBNF_mParser.py [FILENAME]")
