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

if r'/home/eckhart/Entwicklung/DHParser' not in sys.path:
    sys.path.append(r'/home/eckhart/Entwicklung/DHParser')

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, \
    Lookbehind, Lookahead, Alternative, Pop, Text, DropText, Synonym, AllOf, SomeOf, \
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, \
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_children, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, COMPACT_SERIALIZATION, \
    JSON_SERIALIZATION, access_thread_locals, access_presets, finalize_presets, ErrorCode, \
    RX_NEVER_MATCH


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
    source_hash__ = "eb1250cddc18f92b9b0582b3aa386238"
    anonymous__ = re.compile('..(?<=^)')
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
    _ARRAY_SEPARATOR = Series(NegativeLookahead(Drop(Text("]"))), Lookahead(Drop(Text(","))), Option(Series(Drop(Text(",")), dwsp__)), mandatory=1, err_msgs=error_messages__["_ARRAY_SEPARATOR"])
    _OBJECT_SEPARATOR = Series(NegativeLookahead(Drop(Text("}"))), Lookahead(Drop(Text(","))), Option(Series(Drop(Text(",")), dwsp__)), mandatory=1, err_msgs=error_messages__["_OBJECT_SEPARATOR"])
    _EOF = NegativeLookahead(RegExp('.'))
    EXP = Option(Series(Alternative(Drop(Text("E")), Drop(Text("e"))), Option(Alternative(Drop(Text("+")), Drop(Text("-")))), RegExp('[0-9]+')))
    DOT = Text(".")
    FRAC = Option(Series(DOT, RegExp('[0-9]+')))
    NEG = Text("-")
    INT = Alternative(Series(Option(NEG), RegExp('[0-9]')), RegExp('[1-9][0-9]+'))
    HEX = RegExp('[0-9a-fA-F][0-9a-fA-F]')
    UNICODE = Series(Series(Drop(Text("\\u")), dwsp__), HEX, HEX)
    ESCAPE = Alternative(RegExp('\\\\[/bnrt\\\\]'), UNICODE)
    PLAIN = RegExp('[^"\\\\]+')
    _CHARACTERS = ZeroOrMore(Alternative(PLAIN, ESCAPE))
    null = Series(Text("null"), dwsp__)
    bool = Alternative(Series(RegExp('true'), dwsp__), Series(RegExp('false'), dwsp__))
    number = Series(INT, FRAC, EXP, dwsp__)
    string = Series(Drop(Text('"')), _CHARACTERS, Drop(Text('"')), dwsp__, mandatory=1, err_msgs=error_messages__["string"], skip=skip_rules__["string"])
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(_element, ZeroOrMore(Series(_ARRAY_SEPARATOR, _element, mandatory=1)))), Series(Drop(Text("]")), dwsp__))
    member = Series(string, Series(Drop(Text(":")), dwsp__), _element, mandatory=1, err_msgs=error_messages__["member"])
    object = Series(Series(Drop(Text("{")), dwsp__), member, ZeroOrMore(Series(_OBJECT_SEPARATOR, member, mandatory=1)), Series(Drop(Text("}")), dwsp__), mandatory=3)
    _element.set(Alternative(object, array, string, number, bool, null))
    json = Series(dwsp__, _element, _EOF)
    root__ = json
    

def get_grammar() -> json_fail_tolerantGrammar:
    """Returns a thread/process-exclusive json_fail_tolerantGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.json_fail_tolerant_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.json_fail_tolerant_00000001_grammar_singleton = json_fail_tolerantGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.json_fail_tolerant_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.json_fail_tolerant_00000001_grammar_singleton
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
    return partial(traverse, processing_table=json_fail_tolerant_AST_transformation_table.copy())

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
        start_logging(log_dir)
        result, errors, _ = compile_src(file_name)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: json_fail_tolerantParser.py [FILENAME]")
