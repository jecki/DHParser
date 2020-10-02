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
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, node_maker, \
    INDENTED_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_tag_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent


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
    source_hash__ = "ee294ee943b48e437c9e1ecb64055b92"
    anonymous__ = re.compile('_[A-Za-z]+|[A-Z]+')
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
    INT = Alternative(Series(Option(NEG), RegExp('[1-9][0-9]+')), RegExp('[0-9]'))
    HEX = RegExp('[0-9a-fA-F][0-9a-fA-F]')
    UNICODE = Series(Series(Drop(Text("\\u")), dwsp__), HEX, HEX)
    ESCAPE = Alternative(RegExp('\\\\[/bnrt\\\\]'), UNICODE)
    PLAIN = RegExp('[^"\\\\]+')
    _CHARACTERS = ZeroOrMore(Alternative(PLAIN, ESCAPE))
    null = Series(Text("null"), dwsp__)
    false = Series(Drop(Text("false")), dwsp__)
    true = Series(Drop(Text("true")), dwsp__)
    _bool = Alternative(true, false)
    number = Series(INT, FRAC, EXP, dwsp__)
    string = Series(Drop(Text('"')), _CHARACTERS, Drop(Text('"')), dwsp__, mandatory=1)
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(_element, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), _element)))), Series(Drop(Text("]")), dwsp__), mandatory=2)
    member = Series(string, Series(Drop(Text(":")), dwsp__), _element, mandatory=1)
    object = Series(Series(Drop(Text("{")), dwsp__), member, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), member, mandatory=1)), Series(Drop(Text("}")), dwsp__), mandatory=3)
    _element.set(Alternative(object, array, string, number, _bool, null))
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
    "<": [], # flatten,
    "json": [],
    "_element": [],
    "object": [],
    "member": [],
    "array": [],
    "string": [],
    "number": [],
    "_bool": [],
    "true": [],
    "false": [],
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
    "*": [], # replace_by_single_child
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
        # initialize your variables here, not in the constructor!

    def on_json(self, node):
        assert len(node.children) == 1
        return self.compile(node.children[0])

    def on_object(self, node):
        return dict(self.compile(child) for child in node.children)

    def on_member(self, node):
        return (self.compile(node.children[0]),
                self.compile(node.children[-1]))

    def on_array(self, node):
        return [self.compile(child) for child in node.children]

    def on_string(self, node):
        return node.content

    def on_number(self, node):
        if node.children:
            return float(node.content)
        else:
            return int(node.content)

    def on_true(self, node):
        return True

    def on_false(self, node):
        return False

    def on_null(self, node):
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

def compile_src(source):
    """Compiles ``source`` and returns (result, errors, ast).
    """
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple


def cpu_profile(func, *args):
    import cProfile as profile
    import pstats
    pr = profile.Profile()
    pr.enable()
    result = func(*args)
    pr.disable()
    st = pstats.Stats(pr)
    st.strip_dirs()
    st.sort_stats('time').print_stats(40)
    return result


def mem_profile(func, *args):
    import tracemalloc
    tracemalloc.start()
    result = func(*args)
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    print("[ Top 20 ]")
    for stat in top_stats[:40]:
        print(stat)
    return result


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
    parser = ArgumentParser(description="Parses a json-file and shows its syntax-tree.")
    parser.add_argument('files', nargs='+')
    parser.add_argument('-d', '--debug', action='store_const', const='debug',
                        help='Store debug information in LOGS subdirectory.')
    parser.add_argument('-x', '--xml', action='store_const', const='xml',
                        help='Store result as XML instead of S-expression')
    parser.add_argument('-o', '--out', nargs=1, default=['out'],
                        help='Output directory')

    args = parser.parse_args()
    file_names, log_dir = args.files, ''

    if args.debug is not None:
        log_dir = 'LOGS'
        set_config_value('history_tracking', True)
        set_config_value('resume_notices', True)
        set_config_value('log_syntax_trees', set(['cst', 'ast']))  # don't use a set literal, here
    start_logging(log_dir)

    batch_processing = True
    if len(file_names) == 1:
        if os.path.isdir(file_names[0]):
            dir_name = file_names[0]
            print('Processing all files in directory: ' + dir_name)
            file_names = [os.path.join(dir_name, fn)
                          for fn in os.listdir(dir_name) if os.path.isfile(fn)]
            print(file_names)
        else:
            batch_processing = False

    if batch_processing:
        if os.path.exists(args.out[0]):
            if not os.path.isdir(args.out[0]):
                print('Cannot output to %s, because there already exists a file of the same name'
                      % args.out[0])
                sys.exit(1)
        else:
            os.mkdir(args.out[0])

    file_errors = False
    errors = []
    for file_name in file_names:
        if not os.path.exists(file_name):
            print('File "%s" not found!' % file_name)
            file_errors = True
        elif not os.path.isfile(file_name):
            print('"%s" is not a file!' % file_name)
            file_errors = True
        else:
            result, errors, _ = compile_src(file_name)
            if batch_processing:
                out_name = os.path.join(args.out, os.path.splitext(os.path.basename(file_name))[0])
                if errors:
                    print('Errors found in: ' + file_name)
                    extension = '_ERRORS.txt'
                    data = '\n'.join(str(err) for err in errors)
                else:
                    print('Successfully processed: ' + file_name)
                    extension = '.xml' if args.xml else '.sxpr'
                    data = result.serialize(how='default' if args.xml is None else 'xml') \
                        if isinstance(result, Node) else str(result)
                with open(out_name + extension, 'w') as f:
                    f.write(data)


    # result, errors, _ = cpu_profile(compile_src, file_name);  sys.exit(0)

    if not batch_processing:
        if errors:
            cwd = os.getcwd()
            rel_path = file_name[len(cwd):] if file_name.startswith(cwd) else file_name
            for error in errors:
                print(rel_path + ':' + str(error))
            sys.exit(1)
        else:
            print(result.serialize(how='default' if args.xml is None else 'xml')
                  if isinstance(result, Node) else result)
    if file_errors:
        sys.exit(1)
