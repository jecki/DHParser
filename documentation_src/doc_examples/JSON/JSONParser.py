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
from typing import Tuple, List, Union, Any, Optional, Callable, Dict

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
if scriptpath and scriptpath not in sys.path:
    sys.path.append(scriptpath)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, AnyChar, \
    Lookbehind, Lookahead, Alternative, Pop, Text, Synonym, Counted, Interleave, INFINITE, \
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, mixin_comment, \
    compile_source, grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, \
    remove_if, Node, TransformationDict, TransformerCallable, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_result, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, access_thread_locals, access_presets, PreprocessorResult, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory, Error, canonical_error_strings, \
    has_errors, ERROR, FATAL, set_preset_value, get_preset_value, NEVER_MATCH_PATTERN, \
    gen_find_include_func, preprocess_includes, make_preprocessor, chain_preprocessors


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################



RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN 
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def JSONTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as JSONGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, NEVER_MATCH_PATTERN)
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(JSONTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


def preprocess_JSON(source):
    return get_preprocessor()(source)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class JSONGrammar(Grammar):
    r"""Parser for a JSON source file.
    """
    _element = Forward()
    source_hash__ = "d932fa46e6d7c2b3b4a3f2d848472a1c"
    disposable__ = re.compile('_\\w+')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    _EOF = NegativeLookahead(RegExp('.'))
    EXP = Series(Alternative(Text("E"), Text("e")), Option(Alternative(Text("+"), Text("-"))), RegExp('[0-9]+'))
    FRAC = Series(Text("."), RegExp('[0-9]+'))
    INT = Series(Option(Text("-")), Alternative(RegExp('[1-9][0-9]+'), RegExp('[0-9]')))
    HEX = RegExp('[0-9a-fA-F][0-9a-fA-F]')
    UNICODE = Series(Series(Drop(Text("\\u")), dwsp__), HEX, HEX)
    ESCAPE = RegExp('\\\\[/bnrt\\\\"]')
    PLAIN = RegExp('[^"\\\\]+')
    _CHARACTERS = ZeroOrMore(Alternative(PLAIN, ESCAPE, UNICODE))
    null = Series(Text("null"), dwsp__)
    false = Series(Text("false"), dwsp__)
    true = Series(Text("true"), dwsp__)
    _bool = Alternative(true, false)
    number = Series(INT, Option(FRAC), Option(EXP), dwsp__)
    string = Series(Text('"'), _CHARACTERS, Text('"'), dwsp__, mandatory=1)
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(_element, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), _element)))), Series(Drop(Text("]")), dwsp__), mandatory=2)
    member = Series(string, Series(Drop(Text(":")), dwsp__), _element, mandatory=1)
    object = Series(Series(Drop(Text("{")), dwsp__), member, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), member, mandatory=1)), Series(Drop(Text("}")), dwsp__), mandatory=3)
    _element.set(Alternative(object, array, string, number, _bool, null))
    json = Series(dwsp__, _element, _EOF)
    root__ = json
    

_raw_grammar = ThreadLocalSingletonFactory(JSONGrammar, ident=1)

def get_grammar() -> JSONGrammar:
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
    
def parse_JSON(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match=complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

JSON_AST_transformation_table = {
    # AST Transformations for the JSON-grammar
    # "<": [],  # called for each node before calling its specific rules
    # "*": [],  # fallback for nodes that do not appear in this table
    # ">": [],   # called for each node after calling its specific rules
    "json": [],
    "_element": [],
    "object": [],
    "member": [],
    "array": [],
    "string": [remove_brackets],
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
}


def JSONTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=JSON_AST_transformation_table.copy())


get_transformer = ThreadLocalSingletonFactory(JSONTransformer, ident=1)


def transform_JSON(cst):
    return get_transformer()(cst)


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

JSONType = Union[Dict, List, str, int, float, None]


class JSONCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a json source file.
    """

    def __init__(self):
        super(JSONCompiler, self).__init__()

    def reset(self):
        super().reset()
        self.forbid_returning_None = False  # set to False if any compilation is allowed to return None
        # initialize your variables here, not in the constructor!

    def on_json(self, node) -> JSONType:
        assert len(node.children) == 1
        return self.compile(node[0])

    def on_object(self, node) -> Dict[str, JSONType]:
        return {k: v for k, v in (self.compile(child) for child in node)}

    def on_member(self, node) -> Tuple[str, JSONType]:
        assert len(node.children) == 2
        return (self.compile(node[0]), self.compile(node[1]))

    def on_array(self, node) -> List[JSONType]:
        return [self.compile(child) for child in node]

    def on_string(self, node) -> str:
        if node.children:
            return ''.join(self.compile(child) for child in node)
        else:
            return node.content

    def on_number(self, node) -> Union[float, int]:
        num_str = node.content
        if num_str.find('.') >= 0 or num_str.upper().find('E') >= 0:
            return float(num_str)
        else:
            return int(num_str)

    def on_true(self, node) -> bool:
        return True

    def on_false(self, node) -> bool:
        return False

    def on_null(self, node) -> None:
        return None

    def on_PLAIN(self, node) -> str:
        return node.content

    def on_ESCAPE(self, node) -> str:
        assert len(node.content) == 2
        code = node.content[1]
        return {
            '/': '/',
            '\\': '\\',
            '"': '"',
            'b': '\b',
            'f': '\f',
            'n': '\n',
            'r': '\r',
            't': '\t'
        }[code]

    def on_UNICODE(self, node) -> str:
        try:
            return chr(int(node.content, 16))
        except ValueError:
            self.tree.new_error(node, f'Illegal unicode character: {node.content}')
            return '?'


get_compiler = ThreadLocalSingletonFactory(JSONCompiler, ident=1)


def compile_JSON(ast):
    return get_compiler()(ast)


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

RESULT_FILE_EXTENSION = ".sxpr"  # Change this according to your needs!


def compile_src(source: str) -> Tuple[Any, List[Error]]:
    """Compiles ``source`` and returns (result, errors)."""
    result_tuple = compile_source(source, get_preprocessor(), get_grammar(), get_transformer(),
                                  get_compiler())
    return result_tuple[:2]  # drop the AST at the end of the result tuple


def serialize_result(result: Any) -> Union[str, bytes]:
    """Serialization of result. REWRITE THIS, IF YOUR COMPILATION RESULT
    IS NOT A TREE OF NODES.
    """
    if isinstance(result, Node):
        return result.serialize(how='default' if RESULT_FILE_EXTENSION != '.xml' else 'xml')
    elif isinstance(result, str):
        return result
    else:
        return repr(result)


def process_file(source: str, result_filename: str = '') -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors or warnings occurred.
    """
    source_filename = source if is_filename(source) else ''
    result, errors = compile_src(source)
    if not has_errors(errors, FATAL):
        if os.path.abspath(source_filename) != os.path.abspath(result_filename):
            with open(result_filename, 'w', encoding='utf-8') as f:
                f.write(serialize_result(result))
        else:
            errors.append(Error('Source and destination have the same name "%s"!'
                                % result_filename, 0, FATAL))
    if errors:
        err_ext = '_ERRORS.txt' if has_errors(errors, ERROR) else '_WARNINGS.txt'
        err_filename = os.path.splitext(result_filename)[0] + err_ext
        with open(err_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(canonical_error_strings(errors)))
        return err_filename
    return ''


def batch_process(file_names: List[str], out_dir: str,
                  *, submit_func: Callable = None,
                  log_func: Callable = None) -> List[str]:
    """Compiles all files listed in filenames and writes the results and/or
    error messages to the directory `our_dir`. Returns a list of error
    messages files.
    """
    error_list =  []

    def gen_dest_name(name):
        return os.path.join(out_dir, os.path.splitext(os.path.basename(name))[0] \
                                     + RESULT_FILE_EXTENSION)

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

    if submit_func is None:
        import concurrent.futures
        from DHParser.toolkit import instantiate_executor
        with instantiate_executor(get_config_value('batch_processing_parallelization'),
                                  concurrent.futures.ProcessPoolExecutor) as pool:
            run_batch(pool.submit)
    else:
        run_batch(submit_func)
    return error_list


def main():
    # recompile grammar if needed
    script_path = os.path.abspath(__file__)
    if script_path.endswith('Parser.py'):
        grammar_path = script_path.replace('Parser.py', '.ebnf')
    else:
        grammar_path = os.path.splitext(script_path)[0] + '.ebnf'
    parser_update = False

    def notify():
        global parser_update
        parser_update = True
        print('recompiling ' + grammar_path)

    if os.path.exists(grammar_path) and os.path.isfile(grammar_path):
        if not recompile_grammar(grammar_path, script_path, force=False, notify=notify):
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_MESSAGES.txt')
            with open(error_file, 'r', encoding="utf-8") as f:
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
    parser = ArgumentParser(description="Parses a JSON-file and shows its syntax-tree.")
    parser.add_argument('files', nargs='+')
    parser.add_argument('-d', '--debug', action='store_const', const='debug',
                        help='Store debug information in LOGS subdirectory')
    parser.add_argument('-o', '--out', nargs=1, default=['out'],
                        help='Output directory for batch processing')
    parser.add_argument('-v', '--verbose', action='store_const', const='verbose',
                        help='Verbose output')
    parser.add_argument('--singlethread', action='store_const', const='singlethread',
                        help='Run batch jobs in a single thread (recommended only for debugging)')
    outformat = parser.add_mutually_exclusive_group()
    outformat.add_argument('-x', '--xml', action='store_const', const='xml', 
                           help='Format result as XML')
    outformat.add_argument('-s', '--sxpr', action='store_const', const='sxpr',
                           help='Format result as S-expression')
    outformat.add_argument('-t', '--tree', action='store_const', const='tree',
                           help='Format result as indented tree')
    outformat.add_argument('-j', '--json', action='store_const', const='json',
                           help='Format result as JSON')

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
        access_presets()
        set_preset_value('history_tracking', True)
        set_preset_value('resume_notices', True)
        set_preset_value('log_syntax_trees', frozenset(['cst', 'ast']))  # don't use a set literal, here!
        finalize_presets()
    start_logging(log_dir)

    if args.singlethread:
        set_config_value('batch_processing_parallelization', False)

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

        if args.xml:  outfmt = 'xml'
        elif args.sxpr:  outfmt = 'sxpr'
        elif args.tree:  outfmt = 'tree'
        elif args.json:  outfmt = 'json'
        else:  outfmt = 'default'
        print(result.serialize(how=outfmt) if isinstance(result, Node) else result)


if __name__ == "__main__":
    main()
