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
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, AnyChar, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_result, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def json_fail_tolerantPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return json_fail_tolerantPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class json_fail_tolerantGrammar(Grammar):
    r"""Parser for a json_fail_tolerant source file.
    """
    _element = Forward()
    source_hash__ = "42cb00a4f8192986733859d4709c5b37"
    disposable__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    error_messages__ = {'member': [(re.compile(r'[\'`´]'), 'String values must be enclosed by double-quotation marks: "..."!')],
                        'string': [(re.compile(r'\\'), 'Illegal escape sequence "{1}" Allowed values are \\\\/, \\\\\\\\, \\\\b, \\\\n, \\\\r, \\\\t, or \\\\u.'),
                                   (re.compile(r'(?=)'), 'Illegal character "{1}" in string.')],
                        '_OBJECT_SEPARATOR': [(re.compile(r'(?!,)'), 'Missing separator ","')],
                        '_ARRAY_SEPARATOR': [(re.compile(r'(?!,)'), 'Missing separator ","')]}
    skip_rules__ = {'string': [re.compile(r'(?=")')]}
    resume_rules__ = {'object': [re.compile(r'(?:[^{}]|(?:\{.*\}))*\}\s*')],
                      'array': [re.compile(r'(?:[^\[\]]|(?:\[.*\]))*\]\s*')],
                      'member': [re.compile(r'(?=(?:"[^"\n]+"\s*:)|\}|,)')],
                      '_OBJECT_SEPARATOR': [re.compile(r'(?=)')],
                      '_ARRAY_SEPARATOR': [re.compile(r'(?=)')]}
    COMMENT__ = r'(?:\/\/|#).*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    _ARRAY_SEPARATOR = Series(NegativeLookahead(Text("]")), Lookahead(Text(",")), Option(Series(Drop(Text(",")), dwsp__)), mandatory=1)
    _OBJECT_SEPARATOR = Series(NegativeLookahead(Text("}")), Lookahead(Text(",")), Option(Series(Drop(Text(",")), dwsp__)), mandatory=1)
    _EOF = NegativeLookahead(RegExp('.'))
    EXP = Option(Series(Alternative(Text("E"), Text("e")), Option(Alternative(Text("+"), Text("-"))), RegExp('[0-9]+')))
    DOT = Text(".")
    FRAC = Option(Series(DOT, RegExp('[0-9]+')))
    NEG = Text("-")
    INT = Series(Option(NEG), Alternative(RegExp('[0-9]'), RegExp('[1-9][0-9]+')))
    HEX = RegExp('[0-9a-fA-F][0-9a-fA-F]')
    UNICODE = Series(Series(Drop(Text("\\u")), dwsp__), HEX, HEX)
    ESCAPE = Alternative(RegExp('\\\\[/bnrt\\\\]'), UNICODE)
    PLAIN = RegExp('[^"\\\\]+')
    _CHARACTERS = ZeroOrMore(Alternative(PLAIN, ESCAPE))
    null = Series(Text("null"), dwsp__)
    bool = Alternative(Series(RegExp('true'), dwsp__), Series(RegExp('false'), dwsp__))
    number = Series(INT, FRAC, EXP, dwsp__)
    string = Series(Text('"'), _CHARACTERS, Text('"'), dwsp__, mandatory=1)
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(_element, ZeroOrMore(Series(_ARRAY_SEPARATOR, _element, mandatory=1)))), Series(Drop(Text("]")), dwsp__))
    member = Series(string, Series(Drop(Text(":")), dwsp__), _element, mandatory=1)
    object = Series(Series(Drop(Text("{")), dwsp__), member, ZeroOrMore(Series(_OBJECT_SEPARATOR, member, mandatory=1)), Series(Drop(Text("}")), dwsp__), mandatory=3)
    _element.set(Alternative(object, array, string, number, bool, null))
    json = Series(dwsp__, _element, _EOF)
    root__ = json
    

_raw_grammar = ThreadLocalSingletonFactory(json_fail_tolerantGrammar, ident=1)

def get_grammar() -> json_fail_tolerantGrammar:
    grammar = _raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
    
def parse_json_fail_tolerant(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

json_fail_tolerant_AST_transformation_table = {
    # AST Transformations for the json_fail_tolerant-grammar
    "<": flatten,
    "json": [],
    "_element": [],
    "object": [],
    "member": [],
    "array": [],
    "string": [],
    "number": [],
    "bool": [],
    "null": [],
    "_CHARACTERS": [],
    "PLAIN": [],
    "ESCAPE": [],
    "UNICODE": [],
    "HEX": [],
    "INT": [],
    "NEG": [],
    "FRAC": [],
    "DOT": [],
    "EXP": [],
    "_EOF": [],
    "_OBJECT_SEPARATOR": [],
    "_ARRAY_SEPARATOR": [],
    "*": replace_by_single_child
}



def Createjson_fail_tolerantTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=json_fail_tolerant_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.json_fail_tolerant_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.json_fail_tolerant_00000001_transformer_singleton = Createjson_fail_tolerantTransformer()
        transformer = THREAD_LOCALS.json_fail_tolerant_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class json_fail_tolerantCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a json_fail_tolerant source file.
    """

    def __init__(self):
        super(json_fail_tolerantCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_json(self, node):
        return self.fallback_compiler(node)

    # def on__element(self, node):
    #     return node

    # def on_object(self, node):
    #     return node

    # def on_member(self, node):
    #     return node

    # def on_array(self, node):
    #     return node

    # def on_string(self, node):
    #     return node

    # def on_number(self, node):
    #     return node

    # def on_bool(self, node):
    #     return node

    # def on_null(self, node):
    #     return node

    # def on__CHARACTERS(self, node):
    #     return node

    # def on_PLAIN(self, node):
    #     return node

    # def on_ESCAPE(self, node):
    #     return node

    # def on_UNICODE(self, node):
    #     return node

    # def on_HEX(self, node):
    #     return node

    # def on_INT(self, node):
    #     return node

    # def on_NEG(self, node):
    #     return node

    # def on_FRAC(self, node):
    #     return node

    # def on_DOT(self, node):
    #     return node

    # def on_EXP(self, node):
    #     return node

    # def on__EOF(self, node):
    #     return node

    # def on__OBJECT_SEPARATOR(self, node):
    #     return node

    # def on__ARRAY_SEPARATOR(self, node):
    #     return node



def get_compiler() -> json_fail_tolerantCompiler:
    """Returns a thread/process-exclusive json_fail_tolerantCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.json_fail_tolerant_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.json_fail_tolerant_00000001_compiler_singleton = json_fail_tolerantCompiler()
        compiler = THREAD_LOCALS.json_fail_tolerant_00000001_compiler_singleton
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
    parser = ArgumentParser(description="Parses a json_fail_tolerant-file and shows its syntax-tree.")
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
        print(result.serialize(how='default' if args.xml is None else 'xml')
              if isinstance(result, Node) else result)
