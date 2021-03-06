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
from typing import Tuple, List, Union, Any, Optional, Callable, Type, cast

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
    Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, TreeReduction, \
    ZeroOrMore, Forward, NegativeLookahead, Required, CombinedParser, mixin_comment, \
    compile_source, grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, \
    remove_if, Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \
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



USE_PYTHON_3_10_TYPE_UNION = False  # https://www.python.org/dev/peps/pep-0604/


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN 
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def ts2dataclassTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as ts2dataclassGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, '(?:\\/\\/.*)|(?:\\/\\*(?:.|\\n)*?\\*\\/)')
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(ts2dataclassTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class ts2dataclassGrammar(Grammar):
    r"""Parser for a ts2dataclass source file.
    """
    _literal = Forward()
    _type = Forward()
    declaration = Forward()
    declarations_block = Forward()
    index_signature = Forward()
    types = Forward()
    source_hash__ = "5f9e38899e4238611532f9504cd149f0"
    disposable__ = re.compile('INT$|NEG$|FRAC$|DOT$|EXP$|EOF$|_type$|_literal$|_name$|_array_ellipsis$|_top_level_assignment$|_top_level_literal$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'(?:\/\/.*)|(?:\/\*(?:.|\n)*?\*\/)'
    comment_rx__ = re.compile(COMMENT__)
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    EOF = Drop(NegativeLookahead(RegExp('.')))
    EXP = Option(Series(Alternative(Text("E"), Text("e")), Option(Alternative(Text("+"), Text("-"))), RegExp('[0-9]+')))
    DOT = Text(".")
    FRAC = Option(Series(DOT, RegExp('[0-9]+')))
    NEG = Text("-")
    INT = Series(Option(NEG), Alternative(RegExp('[1-9][0-9]+'), RegExp('[0-9]')))
    identifier = Series(RegExp('(?!\\d)\\w+'), dwsp__)
    variable = Series(identifier, ZeroOrMore(Series(Text("."), identifier)))
    basic_type = Series(Alternative(Text("object"), Text("array"), Text("string"), Text("number"), Text("boolean"), Series(Text("null"), Text("integer")), Text("uinteger")), dwsp__)
    _name = Alternative(identifier, Series(Series(Drop(Text('"')), dwsp__), identifier, Series(Drop(Text('"')), dwsp__)))
    association = Series(_name, Series(Drop(Text(":")), dwsp__), _literal)
    object = Series(Series(Drop(Text("{")), dwsp__), Option(Series(association, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), association)))), Series(Drop(Text("}")), dwsp__))
    array = Series(Series(Drop(Text("[")), dwsp__), Option(Series(_literal, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), _literal)))), Series(Drop(Text("]")), dwsp__))
    string = Alternative(Series(RegExp('"[^"\\n]*"'), dwsp__), Series(RegExp("'[^'\\n]*'"), dwsp__))
    number = Series(INT, FRAC, EXP, dwsp__)
    type_parameter = Series(Series(Drop(Text("<")), dwsp__), identifier, Series(Drop(Text(">")), dwsp__))
    _top_level_literal = Drop(Synonym(_literal))
    _array_ellipsis = Drop(Series(_literal, Drop(ZeroOrMore(Drop(Series(Series(Drop(Text(",")), dwsp__), _literal))))))
    assignment = Series(variable, Series(Drop(Text("=")), dwsp__), _literal, Series(Drop(Text(";")), dwsp__))
    _top_level_assignment = Drop(Synonym(assignment))
    const = Series(Option(Series(Drop(Text("export")), dwsp__)), Series(Drop(Text("const")), dwsp__), declaration, Series(Drop(Text("=")), dwsp__), Alternative(_literal, identifier), Series(Drop(Text(";")), dwsp__), mandatory=2)
    item = Series(identifier, Option(Series(Series(Drop(Text("=")), dwsp__), _literal)))
    enum = Series(Option(Series(Drop(Text("export")), dwsp__)), Series(Drop(Text("enum")), dwsp__), Option(identifier), Series(Drop(Text("{")), dwsp__), item, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), item)), Series(Drop(Text("}")), dwsp__), mandatory=3)
    namespace = Series(Option(Series(Drop(Text("export")), dwsp__)), Series(Drop(Text("namespace")), dwsp__), identifier, Series(Drop(Text("{")), dwsp__), ZeroOrMore(const), Series(Drop(Text("}")), dwsp__), mandatory=2)
    map_signature = Series(index_signature, Series(Drop(Text(":")), dwsp__), types)
    mapped_type = Series(Series(Drop(Text("{")), dwsp__), map_signature, Option(Series(Drop(Text(";")), dwsp__)), Series(Drop(Text("}")), dwsp__))
    type_tuple = Series(Series(Drop(Text("[")), dwsp__), _type, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), _type)), Series(Drop(Text("]")), dwsp__))
    array_of = Series(Alternative(basic_type, Series(Series(Drop(Text("(")), dwsp__), types, Series(Drop(Text(")")), dwsp__)), identifier), Series(Drop(Text("[]")), dwsp__))
    extends = Series(Series(Drop(Text("extends")), dwsp__), identifier, ZeroOrMore(Series(Series(Drop(Text(",")), dwsp__), identifier)))
    type_alias = Series(Option(Series(Drop(Text("export")), dwsp__)), Series(Drop(Text("type")), dwsp__), identifier, Series(Drop(Text("=")), dwsp__), types, Series(Drop(Text(";")), dwsp__), mandatory=2)
    interface = Series(Option(Series(Drop(Text("export")), dwsp__)), Series(Drop(Text("interface")), dwsp__), identifier, Option(type_parameter), Option(extends), declarations_block, mandatory=2)
    optional = Series(Text("?"), dwsp__)
    qualifier = Series(Text("readonly"), dwsp__)
    _literal.set(Alternative(number, string, array, object))
    _type.set(Alternative(array_of, basic_type, identifier, Series(Series(Drop(Text("(")), dwsp__), types, Series(Drop(Text(")")), dwsp__)), mapped_type, declarations_block, type_tuple, _literal))
    types.set(Series(_type, ZeroOrMore(Series(Series(Drop(Text("|")), dwsp__), _type))))
    index_signature.set(Series(Series(Drop(Text("[")), dwsp__), identifier, Alternative(Series(Drop(Text(":")), dwsp__), Series(Series(Drop(Text("in")), dwsp__), Series(Drop(Text("keyof")), dwsp__))), _type, Series(Drop(Text("]")), dwsp__)))
    declaration.set(Series(Option(qualifier), identifier, Option(optional), Option(Series(Series(Drop(Text(":")), dwsp__), types))))
    declarations_block.set(Series(Series(Drop(Text("{")), dwsp__), Option(Series(declaration, ZeroOrMore(Series(Series(Drop(Text(";")), dwsp__), declaration)), Option(Series(Series(Drop(Text(";")), dwsp__), map_signature)), Option(Series(Drop(Text(";")), dwsp__)))), Series(Drop(Text("}")), dwsp__)))
    document = Series(dwsp__, ZeroOrMore(Alternative(interface, type_alias, namespace, enum, const, Series(declaration, Series(Drop(Text(";")), dwsp__)), _top_level_assignment, _array_ellipsis, _top_level_literal)), EOF)
    root__ = TreeReduction(document, CombinedParser.MERGE_TREETOPS)
    

_raw_grammar = ThreadLocalSingletonFactory(ts2dataclassGrammar, ident=1)

def get_grammar() -> ts2dataclassGrammar:
    grammar = _raw_grammar()
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
    
def parse_ts2dataclass(document, start_parser = "root_parser__", *, complete_match=True):
    return get_grammar()(document, start_parser, complete_match)


#######################################################################
#
# AST SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

ts2dataclass_AST_transformation_table = {
    # AST Transformations for the ts2dataclass-grammar
    # "<": flatten,
    "types": [replace_by_single_child],
    ":Text": change_tag_name('TEXT')
    # "*": replace_by_single_child
}


def ts2dataclassTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=ts2dataclass_AST_transformation_table.copy())

get_transformer = ThreadLocalSingletonFactory(ts2dataclassTransformer, ident=1)

def transform_ts2dataclass(cst):
    get_transformer()(cst)


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class ts2dataclassCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a ts2dataclass source file.
    """

    def __init__(self):
        super(ts2dataclassCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_document(self, node):
        return node

    def on_interface(self, node):
        return node

    # def on_type_parameter(self, node):
    #     return node

    # def on_type_alias(self, node):
    #     return node

    def on_declarations_block(self, node):
        declarations = '\n'.join(self.compile(nd) for nd in node
                                 if nd.tag_name == 'declaration')
        # ignore map_signature for now
        return declarations

    def on_declaration(self, node):
        if node[-1].tag_name in ('identifier', 'optional'):
            # no types were specified
            T = 'Any'
        else:
            T = self.compile(node[-1])
        if 'optional' in node:
            T = f"Optional[{T}]"
        identifier = self.compile(node['identifier'])
        return f"{identifier}: {T}"

    # def on_optional(self, node):
    #     return node

    def on_index_signature(self, node) -> str:
        return node['type'].content

    def on_types(self, node):
        if sys.version_info >= (3, 10) and USE_PYTHON_3_10_TYPE_UNION:
            return '| '.join(self.any_type(nd) for nd in node)
        else:
            return f"Union[{', '.join(self.any_type(nd) for nd in node)}]"

    def any_type(self, node) -> str:
        # assert node.tag_name in ('array_of', 'basic_type', 'identifier',
        #                          'types', 'mapped_type', 'declarations_blokc',
        #                          'type_tuple',
        #                          'number', 'string', 'array', 'object') ?
        return self.compile(node)

    # def on_type_tuple(self, node):
    #     return node

    def on_mapped_type(self, node) -> str:
        return cast(str, self.compile(node['map_signature']))

    def on_map_signature(self, node) -> str:
        return "Dict[%s, %s]" % (self.compile(node['index_signature']),
                                 self.compile(node['types']))

    # def on_namespace(self, node):
    #     return node

    # def on_enum(self, node):
    #     return node

    # def on_item(self, node):
    #     return node

    # def on_const(self, node):
    #     return node

    def on_assignment(self, node) -> str:
        return node[0].content + ' = ' + self.any_literal(node[1])

    def any_literal(self, node) -> str:
        nd = node[0] if node.children else node
        assert nd.tag_name in ('string', 'number', 'array', 'object')
        return self.compile(nd)

    def on_number(self, node) -> str:
        return node.content

    def on_string(self, node) -> str:
        return node.content

    def on_array(self, node) -> str:
        return '[' + \
               ', '.join(self.any_literal(nd) for nd in node.children) + \
               ']'

    def on_object(self, node) -> str:
        return '{\n' + \
               ',\n'.join(self.compile(nd) for nd in node.children) + \
               '\n}'

    def on_association(self, node) -> str:
        return f'"{node[0].content}": ' + self.any_literal(node[1])

    def on_basic_type(self, node) -> str:
        python_basic_types = {'object': 'object',
                              'array': 'List',
                              'string': 'str',
                              'number': 'float',
                              'integer': 'int',
                              'uinteger': 'int',
                              'boolean': 'bool',
                              'null': 'None'}
        return python_basic_types[node.content]

    # def on_array_marker(self, node):
    #     return node

    # def on_qualifier(self, node):
    #     return node

    def on_identifier(self, node) -> str:
        return node.content

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

    # def on_EOF(self, node):
    #     return node


get_compiler = ThreadLocalSingletonFactory(ts2dataclassCompiler, ident=1)

def compile_ts2dataclass(ast):
    return get_compiler()(ast)


#######################################################################
#
# END OF DHPARSER-SECTIONS
#
#######################################################################

RESULT_FILE_EXTENSION = ".sxpr"  # Change this according to your needs!


def compile_src(source: str) -> Tuple[Any, List[Error]]:
    """Compiles ``source`` and returns (result, errors, ast)."""
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
    parser = ArgumentParser(description="Parses a ts2dataclass-file and shows its syntax-tree.")
    parser.add_argument('files', nargs='+')
    parser.add_argument('-d', '--debug', action='store_const', const='debug',
                        help='Store debug information in LOGS subdirectory')
    parser.add_argument('-x', '--xml', action='store_const', const='xml',
                        help='Store result as XML instead of S-expression')
    parser.add_argument('-o', '--out', nargs=1, default=['out'],
                        help='Output directory for batch processing')
    parser.add_argument('-v', '--verbose', action='store_const', const='verbose',
                        help='Verbose output')
    parser.add_argument('--singlethread', action='store_const', const='singlethread',
                        help='Sun batch jobs in a single thread (recommended only for debugging)')

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
        set_config_value('history_tracking', True)
        set_config_value('resume_notices', True)
        set_config_value('log_syntax_trees', set(['cst', 'ast']))  # don't use a set literal, here
    start_logging(log_dir)

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

        print(result.serialize(how='default' if args.xml is None else 'xml')
              if isinstance(result, Node) else result)
