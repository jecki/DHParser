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
from typing import Tuple, List, Union, Any, Optional, Callable

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
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, all_of, any_of, \
    merge_adjacent, collapse, collapse_children_if, transform_content, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_tag_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    transform_content, replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, access_thread_locals, access_presets, PreprocessorResult, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_tag_names, add_attributes, delimit_children, merge_connected, \
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


def indentedTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as indentedGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, '#[^\\n]*')
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(indentedTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


def preprocess_indented(source):
    return get_preprocessor()(source)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class indentedGrammar(Grammar):
    r"""Parser for an indented source file.
    """
    node = Forward()
    source_hash__ = "19b7777c34ee9ea85470f923354b5f5a"
    disposable__ = re.compile('EOF$|LF$|DEEPER_LEVEL$|SAME_LEVEL$|empty_line$|DEDENT$|single_quoted$|double_quoted$|continuation$|empty_content$|content$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'#[^\n]*'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'[\t ]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp('.')))
    LF = Drop(RegExp('\\n'))
    IDENTIFIER = Series(RegExp('\\w+'), dwsp__)
    INDENT = Capture(RegExp(' *'))
    DEDENT = Drop(Lookahead(Drop(Pop(INDENT, match_func=optional_last_value))))
    HAS_DEEPER_INDENT = Series(Retrieve(INDENT), RegExp(' +'))
    SAME_INDENT = Series(Retrieve(INDENT), NegativeLookahead(RegExp(' ')), mandatory=1)
    double_quoted = Series(Drop(Text('"')), RegExp('(?:\\\\"|[^"\\n])*'), Drop(Text('"')), dwsp__)
    single_quoted = Series(Drop(Text("\'")), RegExp("(?:\\\\'|[^'\\n])*"), Drop(Text("\'")), dwsp__)
    string = Alternative(single_quoted, double_quoted)
    empty_line = Drop(Series(LF, dwsp__, Drop(Lookahead(LF))))
    value = Series(Drop(Text('"')), RegExp('[^"\\n]*'), Drop(Text('"')), dwsp__)
    attribute = Series(Drop(Text("`")), IDENTIFIER)
    attr = Series(attribute, value)
    tag_name = Synonym(IDENTIFIER)
    SAME_LEVEL = Drop(Series(Drop(ZeroOrMore(empty_line)), LF, SAME_INDENT))
    DEEPER_LEVEL = Drop(Series(Drop(ZeroOrMore(empty_line)), Drop(Lookahead(Drop(Series(LF, HAS_DEEPER_INDENT)))), LF, INDENT))
    empty_content = Drop(Series(dwsp__, Drop(Alternative(LF, EOF)), Drop(ZeroOrMore(empty_line))))
    continuation = Drop(Series(Drop(ZeroOrMore(empty_line)), Drop(NegativeLookahead(Drop(Series(LF, HAS_DEEPER_INDENT)))), DEDENT, mandatory=1))
    branch_content = Series(DEEPER_LEVEL, node, ZeroOrMore(Series(SAME_LEVEL, node, mandatory=1)), continuation)
    leaf_content = Alternative(Series(string, ZeroOrMore(empty_line)), Series(DEEPER_LEVEL, string, ZeroOrMore(Series(SAME_LEVEL, string, mandatory=1)), continuation))
    content = Alternative(leaf_content, branch_content, empty_content)
    node.set(Series(tag_name, ZeroOrMore(attr), content, dwsp__, mandatory=2))
    tree = Series(ZeroOrMore(Alternative(empty_line, Series(dwsp__, LF))), OneOrMore(Series(Option(LF), Retrieve(INDENT), node, DEDENT)), RegExp('\\s*'), EOF)
    root__ = tree
    

_raw_grammar = ThreadLocalSingletonFactory(indentedGrammar, ident=1)

def get_grammar() -> indentedGrammar:
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
    
def parse_indented(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

indented_AST_transformation_table = {
    # AST Transformations for the indented-grammar
    # "<": flatten
    # "*": replace_by_single_child
    # ">: []
    "tree": [],
    "node": [],
    "content": [],
    "leaf_content": [],
    "branch_content": [],
    "continuation": [],
    "empty_content": [],
    "DEEPER_LEVEL": [],
    "SAME_LEVEL": [],
    "tag_name": [],
    "attr": [],
    "attribute": [],
    "value": [],
    "empty_line": [],
    "string": [],
    "single_quoted": [],
    "double_quoted": [],
    "INDENT": [],
    "SAME_INDENT": [],
    "HAS_DEEPER_INDENT": [],
    "DEDENT": [],
    "IDENTIFIER": [],
    "LF": [],
    "EOF": [],
}


def indentedTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=indented_AST_transformation_table.copy())


get_transformer = ThreadLocalSingletonFactory(indentedTransformer, ident=1)


def transform_indented(cst):
    return get_transformer()(cst)


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class indentedCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a indented source file.
    """

    def __init__(self):
        super(indentedCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_tree(self, node):
        return self.fallback_compiler(node)

    # def on_node(self, node):
    #     return node

    # def on_content(self, node):
    #     return node

    # def on_leaf_content(self, node):
    #     return node

    # def on_branch_content(self, node):
    #     return node

    # def on_continuation(self, node):
    #     return node

    # def on_empty_content(self, node):
    #     return node

    # def on_DEEPER_LEVEL(self, node):
    #     return node

    # def on_SAME_LEVEL(self, node):
    #     return node

    # def on_tag_name(self, node):
    #     return node

    # def on_attr(self, node):
    #     return node

    # def on_attribute(self, node):
    #     return node

    # def on_value(self, node):
    #     return node

    # def on_empty_line(self, node):
    #     return node

    # def on_string(self, node):
    #     return node

    # def on_single_quoted(self, node):
    #     return node

    # def on_double_quoted(self, node):
    #     return node

    # def on_INDENT(self, node):
    #     return node

    # def on_SAME_INDENT(self, node):
    #     return node

    # def on_HAS_DEEPER_INDENT(self, node):
    #     return node

    # def on_DEDENT(self, node):
    #     return node

    # def on_IDENTIFIER(self, node):
    #     return node

    # def on_LF(self, node):
    #     return node

    # def on_EOF(self, node):
    #     return node


get_compiler = ThreadLocalSingletonFactory(indentedCompiler, ident=1)


def compile_indented(ast):
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
    else:
        return repr(result)


def process_file(source: str, result_filename: str = '') -> str:
    """Compiles the source and writes the serialized results back to disk,
    unless any fatal errors have occurred. Error and Warning messages are
    written to a file with the same name as `result_filename` with an
    appended "_ERRORS.txt" or "_WARNINGS.txt" in place of the name's
    extension. Returns the name of the error-messages file or an empty
    string, if no errors of warnings occurred.
    """
    source_filename = source if is_filename(source) else ''
    result, errors = compile_src(source)
    if not has_errors(errors, FATAL):
        if os.path.abspath(source_filename) != os.path.abspath(result_filename):
            with open(result_filename, 'w') as f:
                f.write(serialize_result(result))
        else:
            errors.append(Error('Source and destination have the same name "%s"!'
                                % result_filename, 0, FATAL))
    if errors:
        err_ext = '_ERRORS.txt' if has_errors(errors, ERROR) else '_WARNINGS.txt'
        err_filename = os.path.splitext(result_filename)[0] + err_ext
        with open(err_filename, 'w') as f:
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


if __name__ == "__main__":
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
    parser = ArgumentParser(description="Parses a indented-file and shows its syntax-tree.")
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
