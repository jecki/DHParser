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
from typing import Tuple, List

sys.path.extend([os.path.join('..', '..'), '..', '.'])


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
    Node, TransformerCallable, TransformationDict, transformation_factory, traverse, \
    remove_children_if, move_fringes, normalize_whitespace, is_anonymous, name_matches, \
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \
    replace_by_children, remove_empty, remove_tokens, flatten, \
    merge_adjacent, collapse, collapse_children_if, transform_result, WHITESPACE_PTYPE, \
    TOKEN_PTYPE, remove_children, remove_content, remove_brackets, change_name, \
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, content_matches, apply_if, peek, \
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \
    replace_content_with, forbid, assert_content, remove_infix_operator, \
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \
    get_config_value, node_maker, any_of, access_thread_locals, access_presets, \
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \
    trace_history, has_descendant, neg, has_ancestor, optional_last_value, insert, \
    positions_of, replace_child_names, add_attributes, delimit_children, merge_connected, \
    has_attr, has_parent, ThreadLocalSingletonFactory, NEVER_MATCH_PATTERN, gen_find_include_func, \
    preprocess_includes, make_preprocessor, chain_preprocessors, Error


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

RE_INCLUDE = NEVER_MATCH_PATTERN
# To capture includes, replace the NEVER_MATCH_PATTERN
# by a pattern with group "name" here, e.g. r'\input{(?P<name>.*)}'


def LyrikTokenizer(original_text) -> Tuple[str, List[Error]]:
    # Here, a function body can be filled in that adds preprocessor tokens
    # to the source code and returns the modified source.
    return original_text, []


def preprocessor_factory() -> PreprocessorFunc:
    # below, the second parameter must always be the same as LyrikGrammar.COMMENT__!
    find_next_include = gen_find_include_func(RE_INCLUDE, '#.*')
    include_prep = partial(preprocess_includes, find_next_include=find_next_include)
    tokenizing_prep = make_preprocessor(LyrikTokenizer)
    return chain_preprocessors(include_prep, tokenizing_prep)


get_preprocessor = ThreadLocalSingletonFactory(preprocessor_factory, ident=1)


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class LyrikGrammar(Grammar):
    r"""Parser for a Lyrik source file.
    """
    source_hash__ = "fd6b4bce06103ceaab2b3ae06128cc6e"
    disposable__ = re.compile('JAHRESZAHL$|ZEICHENFOLGE$|ENDE$|LEERRAUM$|ziel$|wortfolge$')
    static_analysis_pending__ = []  # type: List[bool]
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r''
    comment_rx__ = RX_NEVER_MATCH
    WHITESPACE__ = r'[\t ]*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = Whitespace(WSP_RE__)
    dwsp__ = Drop(Whitespace(WSP_RE__))
    ENDE = Drop(Drop(NegativeLookahead(RegExp('.'))))
    JAHRESZAHL = RegExp('\\d\\d\\d\\d')
    LEERRAUM = Drop(RegExp('\\s+'))
    LEERZEILEN = RegExp('\\n(?:[ \\t]*\\n)+')
    L = RegExp(' +')
    ZW = RegExp('\\n')
    ZEICHENFOLGE = RegExp('[^ \\n<>]+')
    NAME = RegExp('\\w+\\.?')
    WORT = RegExp('\\w+')
    TEXT = Synonym(ZEICHENFOLGE)
    zeile = Series(dwsp__, TEXT, ZeroOrMore(Series(L, TEXT)), dwsp__)
    vers = Synonym(zeile)
    strophe = Series(vers, OneOrMore(Series(ZW, vers)))
    text = Series(strophe, ZeroOrMore(Series(LEERZEILEN, strophe)))
    titel = Synonym(zeile)
    gedicht = Series(titel, LEERZEILEN, text, mandatory=2)
    serie = Series(NegativeLookahead(Series(titel, vers, ZW, vers)), dwsp__,
                   zeile, ZeroOrMore(Series(ZW, zeile)))
    ziel = Series(ZEICHENFOLGE, dwsp__)
    verknüpfung = Series(Series(Drop(Text("<")), dwsp__), ziel,
                         Series(Drop(Text(">")), dwsp__))
    wortfolge = Series(WORT, ZeroOrMore(Series(L, WORT)), dwsp__)
    jahr = Series(JAHRESZAHL, dwsp__)
    ortsname = Synonym(wortfolge)
    ort = Series(ortsname, Option(verknüpfung))
    untertitel = Synonym(wortfolge)
    werktitel = Synonym(wortfolge)
    werk = Series(werktitel,
                  Option(Series(Series(Drop(Text(".")), dwsp__), untertitel,
                                mandatory=1)),
                  Option(verknüpfung))
    name = Series(NAME, ZeroOrMore(Series(L, NAME)), dwsp__)
    autor = Series(name, Option(verknüpfung))
    bibliographisches = Series(autor, Series(Drop(Text(",")), dwsp__),
                               Option(Series(ZW, dwsp__)), werk,
                               Series(Drop(Text(",")), dwsp__),
                               Option(Series(ZW, dwsp__)), ort,
                               Series(Drop(Text(",")), dwsp__),
                               Option(Series(ZW, dwsp__)), jahr,
                               Series(Drop(Text(".")), dwsp__), mandatory=1)
    Dokument = Series(Option(LEERRAUM), bibliographisches, LEERZEILEN,
                      Option(serie), OneOrMore(Series(LEERZEILEN, gedicht)),
                      Option(LEERRAUM), ENDE, mandatory=1)
    root__ = Dokument
    

def get_grammar() -> LyrikGrammar:
    """Returns a thread/process-exclusive LyrikGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.Lyrik_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_00000001_grammar_singleton = LyrikGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.Lyrik_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.Lyrik_00000001_grammar_singleton
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

Lyrik_AST_transformation_table = {
    # AST Transformations for the Lyrik-grammar
    "<": flatten,
    "Dokument": [],
    "gedicht": [],
    "bibliographisches": [],
    "autor": [],
    "name": [collapse],
    "werk": [],
    "werktitel": [collapse],
    "untertitel": [],
    "ort": [],
    "ortsname": [collapse],
    "jahr": [],
    "verknüpfung": [],
    "serie": [reduce_single_child],
    "titel": [collapse],
    "text": [],
    "strophe": [],
    "vers": [reduce_single_child],
    "zeile": [collapse],
    "T": [],
    "WORT": [],
    "NAME": [],
    "ZW": [],
    "L": [],
    "LEERZEILE": [],
    "*": replace_by_single_child
}



def CreateLyrikTransformer() -> TransformerCallable:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, transformation_table=Lyrik_AST_transformation_table.copy())


def get_transformer() -> TransformerCallable:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.Lyrik_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_00000001_transformer_singleton = CreateLyrikTransformer()
        transformer = THREAD_LOCALS.Lyrik_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

class LyrikCompiler(Compiler):
    """Compiler for the abstract-syntax-tree of a Lyrik source file.
    """

    def __init__(self):
        super(LyrikCompiler, self).__init__()

    def reset(self):
        super().reset()
        # initialize your variables here, not in the constructor!

    def on_gedicht(self, node):
        return self.fallback_compiler(node)

    # def on_bibliographisches(self, node):
    #     return node

    # def on_autor(self, node):
    #     return node

    # def on_name(self, node):
    #     return node

    # def on_werk(self, node):
    #     return node

    # def on_werktitel(self, node):
    #     return node

    # def on_untertitel(self, node):
    #     return node

    # def on_ort(self, node):
    #     return node

    # def on_ortsname(self, node):
    #     return node

    # def on_jahr(self, node):
    #     return node

    # def on_wortfolge(self, node):
    #     return node

    # def on_verknüpfung(self, node):
    #     return node

    # def on_ziel(self, node):
    #     return node

    # def on_serie(self, node):
    #     return node

    # def on_titel(self, node):
    #     return node

    # def on_text(self, node):
    #     return node

    # def on_strophe(self, node):
    #     return node

    # def on_vers(self, node):
    #     return node

    # def on_zeile(self, node):
    #     return node

    # def on_T(self, node):
    #     return node

    # def on_WORT(self, node):
    #     return node

    # def on_NAME(self, node):
    #     return node

    # def on_ZEICHENFOLGE(self, node):
    #     return node

    # def on_ZW(self, node):
    #     return node

    # def on_L(self, node):
    #     return node

    # def on_LEERRAUM(self, node):
    #     return node

    # def on_LEERZEILE(self, node):
    #     return node

    # def on_JAHRESZAHL(self, node):
    #     return node

    # def on_ENDE(self, node):
    #     return node



def get_compiler() -> LyrikCompiler:
    """Returns a thread/process-exclusive LyrikCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.Lyrik_00000001_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.Lyrik_00000001_compiler_singleton = LyrikCompiler()
        compiler = THREAD_LOCALS.Lyrik_00000001_compiler_singleton
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
            error_file = os.path.basename(__file__).replace('Parser.py', '_ebnf_MESSAGES.txt')
            with open(error_file, encoding="utf-8") as f:
                print(f.read())
            sys.exit(1)
        elif parser_update:
            print(os.path.basename(__file__) + ' has changed. '
              'Please run again in order to apply updated compiler')
            sys.exit(0)
    else:
        print('Warning: Could not check whether grammar requires recompiling, '
              'because grammar was not found at: %s\n' % grammar_path)

    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses a Lyrik-file and shows its syntax-tree.")
    parser.add_argument('files', nargs=1)
    parser.add_argument('-d', '--debug', action='store_const', const='debug')
    parser.add_argument('-x', '--xml', action='store_const', const='xml')

    args = parser.parse_args()
    file_name, log_dir = args.files[0], ''

    if not os.path.exists(file_name):
        print('File "%s" not found!' % file_name)
        sys.exit(1)
    if not os.path.isfile(file_name):
        print('"%" is not a file!' % file_name)
        sys.exit(1)

    if args.debug is not None:
        log_dir = 'LOGS'
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
        print(result.serialize(how='default' if args.xml is None else 'xml')
              if isinstance(result, Node) else result)
