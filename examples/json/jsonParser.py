#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


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
    error_on, recompile_grammar, left_associative, lean_left, \
    set_config_value, get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \
    INDENTED_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def jsonPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return jsonPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class jsonGrammar(Grammar):
    r"""Parser for a json source file.
    """
    _element = Forward()
    source_hash__ = "bafbd6f9841d02f5d89991ad92492673"
    anonymous__ = re.compile('..(?<=^)')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'(?:\/\/|#).*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
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
    string = Series(Drop(Text('"')), _CHARACTERS, Drop(Text('"')), dwsp__, mandatory=1)
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(_element, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), _element)))), Series(Drop(Text("]")), dwsp__))
    member = Series(string, Series(Drop(Text(":")), dwsp__), _element, mandatory=1)
    object = Series(Series(Drop(Text("{")), dwsp__), member, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), member, mandatory=1)), Series(Drop(Text("}")), dwsp__), mandatory=3)
    _element.set(Alternative(object, array, string, number, bool, null))
    json = Series(dwsp__, _element, _EOF)
    root__ = json
    

def get_grammar() -> jsonGrammar:
    """Returns a thread/process-exclusive jsonGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.json_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.json_00000001_grammar_singleton = jsonGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.json_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.json_00000001_grammar_singleton
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

json_AST_transformation_table = {
    # AST Transformations for the json-grammar
    "json": [replace_by_single_child],
    "number": [collapse],
    "string": [reduce_single_child],
}


def CreatejsonTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=json_AST_transformation_table.copy())

def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.json_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.json_00000001_transformer_singleton = CreatejsonTransformer()
        transformer = THREAD_LOCALS.json_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class jsonCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a json source file.
    """

    def __init__(self):
        super(jsonCompiler, self).__init__()

    def reset(self):
        super().reset()
        self._None_check = False

    def on_object(self, node):
        return dict(self.compile(child) for child in node.children)

    def on_member(self, node) -> tuple:
        return (self.compile(node.children[0]), self.compile(node.children[1]))

    def on_array(self, node) -> list:
        return [self.compile(child) for child in node.children]

    def on_string(self, node) -> str:
        return node.content

    def on_number(self, node) -> float:
        return float(node.content)

    def on_bool(self, node) -> bool:
        return True if node.content == "true" else False

    def on_null(self, node) -> None:
        return None


def get_compiler() -> jsonCompiler:
    """Returns a thread/process-exclusive jsonCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.json_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.json_00000001_compiler_singleton = jsonCompiler()
        compiler = THREAD_LOCALS.json_00000001_compiler_singleton
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
            print(result.as_sxpr() if isinstance(result, Node) else result)
    else:
        print("Usage: jsonParser.py [FILENAME]")
