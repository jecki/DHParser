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

dhparser_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if dhparser_path not in sys.path:
    sys.path.append(dhparser_path)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, \
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, \
    collapse, collapse_children_if, WHITESPACE_PTYPE, TOKEN_PTYPE, \
    remove_children, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \
    keep_children, is_one_of, not_one_of, has_content, apply_if, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    forbid, assert_content, remove_infix_operator, \
    error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, INDENTED_SERIALIZATION, \
    JSON_SERIALIZATION, access_thread_locals, access_presets, finalize_presets


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def yamlPreprocessor(text):
    return text, lambda i: i

def get_preprocessor() -> PreprocessorFunc:
    return yamlPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class yamlGrammar(Grammar):
    r"""Parser for a yaml source file.
    """
    element = Forward()
    value = Forward()
    source_hash__ = "0bddf6bf7e765930591dc13edb0e235f"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'(?:\/\/|#).*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = NegativeLookahead(RegExp('.'))
    EXP = Option(Series(Alternative(Drop(Text("E")), Drop(Text("e"))), Option(Alternative(Drop(Text("+")), Drop(Text("-")))), RegExp('[0-9]+')))
    FRAC = Option(Series(Drop(Text(".")), RegExp('[0-9]+')))
    INT = Alternative(Series(Option(Drop(Text("-"))), RegExp('[0-9]')), RegExp('[1-9][0-9]+'))
    HEX = RegExp('[0-9a-fA-F]')
    ESCAPE = Alternative(RegExp('\\\\[/bnrt\\\\]'), Series(RegExp('\\\\u'), HEX, HEX, HEX, HEX))
    CHARACTERS = ZeroOrMore(Alternative(RegExp('[^"\\\\]+'), ESCAPE))
    null = Series(Text("null"), dwsp__)
    bool = Alternative(Series(RegExp('true'), dwsp__), Series(RegExp('false'), dwsp__))
    number = Series(INT, FRAC, EXP, dwsp__)
    string = Series(Drop(Text('"')), CHARACTERS, Drop(Text('"')), dwsp__)
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(value, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), value)))), Series(Drop(Text("]")), dwsp__))
    member = Series(string, Series(Drop(Text(":")), dwsp__), element)
    object = Series(Series(Drop(Text("{")), dwsp__), Option(Series(member, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), member)))), Series(Drop(Text("}")), dwsp__))
    value.set(Alternative(object, array, string, number, bool, null))
    element.set(Synonym(value))
    json = Series(dwsp__, element, EOF)
    root__ = json
    

def get_grammar() -> yamlGrammar:
    """Returns a thread/process-exclusive yamlGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.yaml_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.yaml_00000001_grammar_singleton = yamlGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.yaml_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.yaml_00000001_grammar_singleton
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

yaml_AST_transformation_table = {
    # AST Transformations for the yaml-grammar
    "<": flatten,
    "json": [],
    "element": [],
    "value": [],
    "object": [],
    "member": [],
    "array": [],
    "string": [],
    "number": [],
    "bool": [],
    "null": [],
    "CHARACTERS": [],
    "ESCAPE": [],
    "HEX": [],
    "INT": [],
    "FRAC": [],
    "EXP": [],
    "EOF": [],
    "*": replace_by_single_child
}


def CreateyamlTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=yaml_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    try:
        THREAD_LOCALS = access_thread_locals()
        transformer = THREAD_LOCALS.yaml_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.yaml_00000001_transformer_singleton = CreateyamlTransformer()
        transformer = THREAD_LOCALS.yaml_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class yamlCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a yaml source file.
    """

    def __init__(self):
        super(yamlCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_json(self, node):
        return self.fallback_compiler(node)

    # def on_element(self, node):
    #     return node

    # def on_value(self, node):
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

    # def on_CHARACTERS(self, node):
    #     return node

    # def on_ESCAPE(self, node):
    #     return node

    # def on_HEX(self, node):
    #     return node

    # def on_INT(self, node):
    #     return node

    # def on_FRAC(self, node):
    #     return node

    # def on_EXP(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


def get_compiler() -> yamlCompiler:
    """Returns a thread/process-exclusive yamlCompiler-singleton."""
    try:
        compiler = THREAD_LOCALS.yaml_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.yaml_00000001_compiler_singleton = yamlCompiler()
        compiler = THREAD_LOCALS.yaml_00000001_compiler_singleton
    return compiler


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

def compile_src(source, log_dir=''):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    start_logging(log_dir)
    compiler = get_compiler()
    result_tuple = compile_source(source, get_preprocessor(),
                                  get_grammar(),
                                  get_transformer(), compiler)
    return result_tuple


if __name__ == "__main__":
    # recompile grammar if needed
    grammar_path = os.path.abspath(__file__).replace('Parser.py', '.ebnf')
    if os.path.exists(grammar_path):
        if not recompile_grammar(grammar_path, force=False,
                                  notify=lambda:print('recompiling ' + grammar_path)):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_ERRORS.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
    else:
        print('Could not check whether grammar requires recompiling, '
              'because grammar was not found at: ' + grammar_path)

    if len(sys.argv) > 1:
        # compile file
        file_name, log_dir = sys.argv[1], ''
        if file_name in ['-d', '--debug'] and len(sys.argv) > 2:
            file_name, log_dir = sys.argv[2], 'LOGS'
        result, errors, _ = compile_src(file_name, log_dir)
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.as_xml() if isinstance(result, Node) else result)
    else:
        print("Usage: yamlParser.py [FILENAME]")
