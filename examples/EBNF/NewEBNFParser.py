#!/usr/bin/env python3

#######################################################################
#
# SYMBOLS SECTION - Can be edited. Changes will be preserved.
#
#######################################################################


from collections import OrderedDict
from functools import partial
import keyword
import os
import sys
from typing import Callable, Dict, List, Set, Tuple, Sequence, Union, Optional, Any

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'../..'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

from DHParser.compile import CompilerError, Compiler, ResultTuple, compile_source, visitor_name
from DHParser.configuration import access_thread_locals, get_config_value, set_config_value
from DHParser.dsl import recompile_grammar
from DHParser.error import Error
from DHParser.log import start_logging
from DHParser.parse import Grammar, mixin_comment, mixin_nonempty, Forward, RegExp, \
    Drop, NegativeLookahead, Alternative, Series, Option, OneOrMore, ZeroOrMore, \
    Token, GrammarError, Whitespace
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc
from DHParser.syntaxtree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE
from DHParser.toolkit import load_if_file, escape_re, md5, sane_parser_name, re, expand_table, \
    unrepr, compile_python_object, DHPARSER_PARENTDIR, RX_NEVER_MATCH
from DHParser.trace import set_tracer, resume_notices_on, trace_history
from DHParser.transform import TransformationFunc, traverse, remove_brackets, \
    reduce_single_child, replace_by_single_child, remove_empty, \
    remove_tokens, flatten, forbid, assert_content
from DHParser.versionnumber import __version__


########################################################################
#
# source code support
#
########################################################################


DHPARSER_IMPORTS = '''
import collections
from functools import partial
import os
import sys

try:
    scriptpath = os.path.dirname(__file__)
except NameError:
    scriptpath = ''
dhparser_parentdir = os.path.abspath(os.path.join(scriptpath, r'{dhparser_parentdir}'))
if scriptpath not in sys.path:
    sys.path.append(scriptpath)
if dhparser_parentdir not in sys.path:
    sys.path.append(dhparser_parentdir)

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \\
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, Drop, \\
    Lookbehind, Lookahead, Alternative, Pop, Token, Synonym, AllOf, SomeOf, \\
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \\
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \\
    grammar_changed, last_value, matching_bracket, PreprocessorFunc, is_empty, remove_if, \\
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \\
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \\
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \\
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \\
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, \\
    TOKEN_PTYPE, remove_nodes, remove_content, remove_brackets, change_tag_name, \\
    remove_anonymous_tokens, keep_children, is_one_of, not_one_of, has_content, apply_if, peek, \\
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \\
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \\
    add_error, error_on, recompile_grammar, left_associative, lean_left, set_config_value, \\
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, \\
    COMPACT_SERIALIZATION, JSON_SERIALIZATION, access_thread_locals, access_presets, \\
    finalize_presets, ErrorCode, RX_NEVER_MATCH, set_tracer, resume_notices_on, \\
    trace_history, has_descendant, neg, has_parent, optional_last_value
'''


#######################################################################
#
# PREPROCESSOR SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

def NewEBNFPreprocessor(text):
    return text, lambda i: i


def get_preprocessor() -> PreprocessorFunc:
    return NewEBNFPreprocessor


#######################################################################
#
# PARSER SECTION - Don't edit! CHANGES WILL BE OVERWRITTEN!
#
#######################################################################

class NewEBNFGrammar(Grammar):
    r"""Parser for a NewEBNF source file.
    """
    element = Forward()
    expression = Forward()
    source_hash__ = "abd9bf9a97d8534bd6d7eaf27e1e4b8b"
    anonymous__ = re.compile('pure_elem$')
    static_analysis_pending__ = [True]
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
    option = Alternative(Series(Series(Token("["), dwsp__), expression, Series(Token("]"), dwsp__), mandatory=1), Series(element, Series(Token("?"), dwsp__)))
    repetition = Alternative(Series(Series(Token("{"), dwsp__), expression, Series(Token("}"), dwsp__), mandatory=1), Series(element, Series(Token("*"), dwsp__)))
    oneormore = Alternative(Series(Series(Token("{"), dwsp__), expression, Series(Token("}+"), dwsp__)), Series(element, Series(Token("+"), dwsp__)))
    group = Series(Series(Token("("), dwsp__), expression, Series(Token(")"), dwsp__), mandatory=1)
    retrieveop = Alternative(Series(Token("::"), dwsp__), Series(Token(":?"), dwsp__), Series(Token(":"), dwsp__))
    flowmarker = Alternative(Series(Token("!"), dwsp__), Series(Token("&"), dwsp__), Series(Token("<-!"), dwsp__), Series(Token("<-&"), dwsp__))
    element.set(Alternative(Series(Option(retrieveop), symbol, NegativeLookahead(Series(Token("="), dwsp__))), literal, plaintext, regexp, whitespace, group))
    pure_elem = Series(element, NegativeLookahead(RegExp('[?*+]')), mandatory=1)
    term = Alternative(oneormore, repetition, option, pure_elem)
    lookaround = Series(flowmarker, Alternative(oneormore, pure_elem))
    interleave = Series(term, ZeroOrMore(Series(Series(Token("°"), dwsp__), Option(Series(Token("§"), dwsp__)), term)))
    sequence = OneOrMore(Series(Option(Series(Token("§"), dwsp__)), Alternative(interleave, lookaround)))
    expression.set(Series(sequence, ZeroOrMore(Series(Series(Token("|"), dwsp__), sequence))))
    directive = Series(Series(Token("@"), dwsp__), symbol, Series(Token("="), dwsp__), Alternative(regexp, literal, symbol), ZeroOrMore(Series(Series(Token(","), dwsp__), Alternative(regexp, literal, symbol))), mandatory=1)
    definition = Series(symbol, Series(Token("="), dwsp__), expression, mandatory=1)
    syntax = Series(Option(Series(dwsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF, mandatory=2)
    root__ = syntax
    

def get_grammar() -> NewEBNFGrammar:
    """Returns a thread/process-exclusive NewEBNFGrammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.NewEBNF_00000001_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.NewEBNF_00000001_grammar_singleton = NewEBNFGrammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.NewEBNF_00000001_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.NewEBNF_00000001_grammar_singleton
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

NewEBNF_AST_transformation_table = {
    # AST Transformations for the NewEBNF-grammar
    "<": [remove_empty],
    "syntax": [],
    "directive, definition": [flatten, remove_tokens('@', '=', ',')],
    "expression": [replace_by_single_child, flatten, remove_tokens('|')],
    "sequence, interleave": [replace_by_single_child, flatten],
    "term, pure_elem, element": [replace_by_single_child],
    "flowmarker, retrieveop": [reduce_single_child],
    "group": [remove_brackets, replace_by_single_child],
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets, # remove_tokens('?', '*', '+'),
         forbid('repetition', 'option', 'oneormore'), assert_content(r'(?!§)(?:.|\n)*')],
    "symbol, literal, regexp": [reduce_single_child],
    (TOKEN_PTYPE, WHITESPACE_PTYPE): [reduce_single_child],
    "*": [replace_by_single_child]
}



def CreateNewEBNFTransformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table=NewEBNF_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.NewEBNF_00000001_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.NewEBNF_00000001_transformer_singleton = CreateNewEBNFTransformer()
        transformer = THREAD_LOCALS.NewEBNF_00000001_transformer_singleton
    return transformer


#######################################################################
#
# COMPILER SECTION - Can be edited. Changes will be preserved.
#
#######################################################################

PreprocessorFactoryFunc = Callable[[], PreprocessorFunc]
ParserFactoryFunc = Callable[[], Grammar]
TransformerFactoryFunc = Callable[[], TransformationFunc]
CompilerFactoryFunc = Callable[[], Compiler]

PREPROCESSOR_FACTORY = '''

def get_preprocessor() -> PreprocessorFunc:
    return {NAME}Preprocessor
'''


GRAMMAR_FACTORY = '''

def get_grammar() -> {NAME}Grammar:
    """Returns a thread/process-exclusive {NAME}Grammar-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        grammar = THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton
    except AttributeError:
        THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton = {NAME}Grammar()
        if hasattr(get_grammar, 'python_src__'):
            THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton.python_src__ = get_grammar.python_src__
        grammar = THREAD_LOCALS.{NAME}_{ID:08d}_grammar_singleton
    if get_config_value('resume_notices'):
        resume_notices_on(grammar)
    elif get_config_value('history_tracking'):
        set_tracer(grammar, trace_history)
    return grammar
'''


TRANSFORMER_FACTORY = '''

def Create{NAME}Transformer() -> TransformationFunc:
    """Creates a transformation function that does not share state with other
    threads or processes."""
    return partial(traverse, processing_table={NAME}_AST_transformation_table.copy())


def get_transformer() -> TransformationFunc:
    """Returns a thread/process-exclusive transformation function."""
    THREAD_LOCALS = access_thread_locals()
    try:
        transformer = THREAD_LOCALS.{NAME}_{ID:08d}_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.{NAME}_{ID:08d}_transformer_singleton = Create{NAME}Transformer()
        transformer = THREAD_LOCALS.{NAME}_{ID:08d}_transformer_singleton
    return transformer
'''


COMPILER_FACTORY = '''

def get_compiler() -> {NAME}Compiler:
    """Returns a thread/process-exclusive {NAME}Compiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.{NAME}_{ID:08d}_compiler_singleton
    except AttributeError:
        THREAD_LOCALS.{NAME}_{ID:08d}_compiler_singleton = {NAME}Compiler()
        compiler = THREAD_LOCALS.{NAME}_{ID:08d}_compiler_singleton
    return compiler
'''


WHITESPACE_TYPES = {'horizontal': r'[\t ]*',  # default: horizontal
                    'linefeed': r'[ \t]*\n?(?!\s*\n)[ \t]*',
                    'vertical': r'\s*'}

DROP_TOKEN  = 'token'
DROP_WSPC   = 'whitespace'
DROP_REGEXP = 'regexp'
DROP_VALUES = {DROP_TOKEN, DROP_WSPC, DROP_REGEXP}

# Representation of Python code or, rather, something that will be output as Python code
ReprType = Union[str, unrepr]


class EBNFDirectives:
    """
    A Record that keeps information about compiler directives
    during the compilation process.

    Attributes:
        whitespace:  the regular expression string for (insignificant)
                whitespace

        comment:  the regular expression string for comments

        literalws:  automatic whitespace eating next to literals. Can
                be either 'left', 'right', 'none', 'both'

        tokens:  set of the names of preprocessor tokens

        filter:  mapping of symbols to python match functions that
                will be called on any retrieve / pop - operations on
                these symbols

        error:  mapping of symbols to tuples of match conditions and
                customized error messages. A match condition can be
                either a string or a regular expression. The first
                error message where the search condition matches will
                be displayed. An empty string '' as search condition
                always matches, so in case of multiple error messages,
                this condition should be placed at the end.

        skip:  mapping of symbols to a list of search expressions. A
                search expressions can be either a string ot a regular
                expression. The closest match is the point of reentry
                for the series- or allof-parser when a mandatory item
                failed to match the following text.

        resume:  mapping of symbols to a list of search expressions. A
                search expressions can be either a string ot a regular
                expression. The closest match is the point of reentry
                for after a parsing error has error occurred. Other
                than the skip field, this configures resuming after
                the failing parser (`parser.Series` or `parser.AllOf`)
                has returned.

        drop:   A set that may contain the elements `DROP_TOKEN` and
                `DROP_WSP', 'DROP_REGEXP' or any name of a symbol
                of an anonymous parser (e.g. '_linefeed') the results
                of which will be dropped during the parsing process,
                already.

        super_ws(property): Cache for the "super whitespace" which
                is a regular expression that merges whitespace and
                comments. This property should only be accessed after
                the `whitespace` and `comment` field have been filled
                with the values parsed from the EBNF source.
    """
    __slots__ = ['whitespace', 'comment', 'literalws', 'tokens', 'filter', 'error', 'skip',
                 'resume', 'drop', '_super_ws']

    def __init__(self):
        self.whitespace = WHITESPACE_TYPES['vertical']  # type: str
        self.comment = ''      # type: str
        self.literalws = {'right'}  # type: Set[str]
        self.tokens = set()    # type: Set[str]
        self.filter = dict()   # type: Dict[str, str]
        self.error = dict()    # type: Dict[str, List[Tuple[ReprType, ReprType]]]
        self.skip = dict()     # type: Dict[str, List[Union[unrepr, str]]]
        self.resume = dict()   # type: Dict[str, List[Union[unrepr, str]]]
        self.drop = set()      # type: Set[str]
        self._super_ws = None  # type: Optional[str]

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        assert hasattr(self, key)
        setattr(self, key, value)

    @property
    def super_ws(self):
        if self._super_ws is None:
            self._super_ws = mixin_comment(self.whitespace, self.comment)
        return self._super_ws

    def keys(self):
        return self.__slots__


class EBNFCompilerError(CompilerError):
    """Error raised by `EBNFCompiler` class. (Not compilation errors
    in the strict sense, see `CompilationError` in module ``dsl.py``)"""
    pass


class NewEBNFCompiler(Compiler):
    """
    Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.

    Instances of this class must be called with the root-node of the
    abstract syntax tree from an EBNF-specification of a formal language.
    The returned value is the Python-source-code of a Grammar class for
    this language that can be used to parse texts in this language.
    See classes `parser.Compiler` and `parser.Grammar` for more information.

    Additionally, class EBNFCompiler provides helper methods to generate
    code-skeletons for a preprocessor, AST-transformation and full
    compilation of the formal language. These method's names start with
    the prefix `gen_`.

    Attributes:
        current_symbols:  During compilation, a list containing the root
                node of the currently compiled definition as first element
                and then the nodes of the symbols that are referred to in
                the currently compiled definition.

        rules:  Dictionary that maps rule names to a list of Nodes that
                contain symbol-references in the definition of the rule.
                The first item in the list is the node of the rule-
                definition itself. Example:

                           `alternative = a | b`

                Now `[node.content for node in self.rules['alternative']]`
                yields `['alternative = a | b', 'a', 'b']`

        symbols:  A mapping of symbol names to their first usage (not
                their definition!) in the EBNF source.

        variables:  A set of symbols names that are used with the
                Pop or Retrieve operator. Because the values of these
                symbols need to be captured they are called variables.
                See `test_parser.TestPopRetrieve` for an example.

        recursive:  A set of symbols that are used recursively and
                therefore require a `Forward`-operator.

        definitions:  A dictionary of definitions. Other than `rules`
                this maps the symbols to their compiled definienda.

        required_keywords: A list of keywords (like `comment__` or
                `whitespace__` that need to be defined at the beginning
                of the grammar class because they are referred to later.

        deferred_tasks:  A list of callables that is filled during
                compilatation, but that will be executed only after
                compilation has finished. Typically, it contains
                sementatic checks that require information that
                is only available upon completion of compilation.

        root_symbol: The name of the root symbol.

        drop_flag: This flag is set temporarily when compiling the definition
                of a parser that shall drop its content. If this flag is
                set all contained parser will also drop their content as an
                optimization.

        directives:  A record of all directives and their default values.

        defined_directives:  A set of all directives that have already been
                defined. With the exception of those directives contained
                in EBNFCompiler.REPEATABLE_DIRECTIVES, directives must only
                be defined once.

        consumed_custom_errors:  A set of symbols for which a custom error
                has been defined and(!) consumed during compilation. This
                allows to add a compiler error in those cases where (i) an
                error message has been defined but will never used or (ii)
                an error message is accidently used twice. For examples, see
                `test_ebnf.TestErrorCustomization`.

        consumed_skip_rules: The same as `consumed_custom_errors` only for
                in-series-resume-rules (aka 'skip-rules') for Series-parsers.

        re_flags:  A set of regular expression flags to be added to all
                regular expressions found in the current parsing process

        anonymous_regexp: A regular expression to identify symbols that stand
                for parsers that shall yield anonymous nodes. The pattern of
                the regular expression is configured in configuration.py but
                can also be set by a directive. The default value is a regular
                expression that catches names with a leading underscore.
                See also `parser.Grammar.anonymous__`

        grammar_name:  The name of the grammar to be compiled

        grammar_source:  The source code of the grammar to be compiled.

        grammar_id: a unique id for every compiled grammar. (Required for
                disambiguation of of thread local variables storing
                compiled texts.)
    """
    COMMENT_KEYWORD = "COMMENT__"
    COMMENT_PARSER_KEYWORD = "comment__"
    DROP_COMMENT_PARSER_KEYWORD = "dcomment__"
    COMMENT_RX_KEYWORD = "comment_rx__"
    WHITESPACE_KEYWORD = "WSP_RE__"
    RAW_WS_KEYWORD = "WHITESPACE__"
    RAW_WS_PARSER_KEYWORD = "whitespace__"
    DROP_RAW_WS_PARSER_KEYWORD = "dwhitespace__"
    WHITESPACE_PARSER_KEYWORD = "wsp__"
    DROP_WHITESPACE_PARSER_KEYWORD = "dwsp__"
    RESUME_RULES_KEYWORD = "resume_rules__"
    SKIP_RULES_KEYWORD = 'skip_rules__'
    ERR_MSGS_KEYWORD = 'error_messages__'
    COMMENT_OR_WHITESPACE = {COMMENT_PARSER_KEYWORD, DROP_COMMENT_PARSER_KEYWORD,
                             RAW_WS_PARSER_KEYWORD, DROP_RAW_WS_PARSER_KEYWORD,
                             WHITESPACE_PARSER_KEYWORD, DROP_WHITESPACE_PARSER_KEYWORD}
    RESERVED_SYMBOLS = {COMMENT_KEYWORD, COMMENT_RX_KEYWORD, COMMENT_PARSER_KEYWORD,
                        WHITESPACE_KEYWORD, RAW_WS_KEYWORD, RAW_WS_PARSER_KEYWORD,
                        WHITESPACE_PARSER_KEYWORD, DROP_WHITESPACE_PARSER_KEYWORD,
                        RESUME_RULES_KEYWORD}
    KEYWORD_SUBSTITUTION = {COMMENT_KEYWORD: COMMENT_PARSER_KEYWORD,
                            COMMENT_PARSER_KEYWORD: COMMENT_PARSER_KEYWORD,
                            RAW_WS_KEYWORD: RAW_WS_PARSER_KEYWORD,
                            RAW_WS_PARSER_KEYWORD: RAW_WS_PARSER_KEYWORD,
                            WHITESPACE_KEYWORD: WHITESPACE_PARSER_KEYWORD,
                            WHITESPACE_PARSER_KEYWORD: WHITESPACE_PARSER_KEYWORD,
                            DROP_WHITESPACE_PARSER_KEYWORD: DROP_WHITESPACE_PARSER_KEYWORD}
    AST_ERROR = "Badly structured syntax tree. " \
                "Potentially due to erroneous AST transformation."
    PREFIX_TABLE = {'§': 'Required',
                    '&': 'Lookahead', '!': 'NegativeLookahead',
                    '-&': 'Lookbehind', '-!': 'NegativeLookbehind',
                    '::': 'Pop', ':?': 'Pop', ':': 'Retrieve'}
    REPEATABLE_DIRECTIVES = {'tokens'}


    def __init__(self, grammar_name="DSL", grammar_source=""):
        self.grammar_id = 0  # type: int
        super(NewEBNFCompiler, self).__init__()  # calls the reset()-method
        self.set_grammar_name(grammar_name, grammar_source)


    def reset(self):
        super(NewEBNFCompiler, self).reset()
        self._result = ''               # type: str
        self.re_flags = set()           # type: Set[str]
        self.rules = OrderedDict()      # type: OrderedDict[str, List[Node]]
        self.current_symbols = []       # type: List[Node]
        self.symbols = {}               # type: Dict[str, Node]
        self.variables = set()          # type: Set[str]
        self.recursive = set()          # type: Set[str]
        self.definitions = {}           # type: Dict[str, str]
        self.required_keywords = set()  # type: Set[str]
        self.deferred_tasks = []        # type: List[Callable]
        self.root_symbol = ""           # type: str
        self.drop_flag = False          # type: bool
        self.directives = EBNFDirectives()   # type: EBNFDirectives
        self.defined_directives = set()      # type: Set[str]
        self.consumed_custom_errors = set()  # type: Set[str]
        self.consumed_skip_rules = set()     # type: Set[str]
        self.anonymous_regexp = re.compile(get_config_value('default_anonymous_regexp'))
        self.grammar_id += 1


    @property
    def result(self) -> str:
        return self._result


    def set_grammar_name(self, grammar_name: str = "", grammar_source: str = ""):
        """
        Changes the grammar name and source.

        The grammar name and the source text are metadata that do not affect the
        compilation process. It is used to name and annotate the output.
        Returns `self`.
        """
        assert grammar_name == "" or re.match(r'\w+\Z', grammar_name)
        if not grammar_name and re.fullmatch(r'[\w/:\\]+', grammar_source):
            grammar_name = os.path.splitext(os.path.basename(grammar_source))[0]
        self.grammar_name = grammar_name or "NameUnknown"
        self.grammar_source = load_if_file(grammar_source)
        return self

    # methods for generating skeleton code for preprocessor, transformer, and compiler

    def gen_preprocessor_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for a preprocessor-function for
        the previously compiled formal language.
        """
        name = self.grammar_name + "Preprocessor"
        return "def %s(text):\n    return text, lambda i: i\n" % name \
               + PREPROCESSOR_FACTORY.format(NAME=self.grammar_name)


    def gen_transformer_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for the AST-transformation for the
        previously compiled formal language.
        """
        if not self.rules:
            raise EBNFCompilerError('Compiler must be run before calling '
                                    '"gen_transformer_Skeleton()"!')
        tt_name = self.grammar_name + '_AST_transformation_table'
        transtable = [tt_name + ' = {',
                      '    # AST Transformations for the ' + self.grammar_name + '-grammar']
        transtable.append('    "<": flatten,')
        for name in self.rules:
            transformations = '[]'
            # rule = self.definitions[name]
            # if rule.startswith('Alternative'):
            #     transformations = '[replace_or_reduce]'
            # elif rule.startswith('Synonym'):
            #     transformations = '[reduce_single_child]'
            transtable.append('    "' + name + '": %s,' % transformations)
        # transtable.append('    ":Token": reduce_single_child,')
        transtable += ['    "*": replace_by_single_child', '}', '']
        transtable += [TRANSFORMER_FACTORY.format(NAME=self.grammar_name, ID=self.grammar_id)]
        return '\n'.join(transtable)


    def gen_compiler_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for a Compiler-class for the
        previously compiled formal language.
        """
        if not self.rules:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_Compiler_Skeleton()"!')
        compiler = ['class ' + self.grammar_name + 'Compiler(Compiler):',
                    '    """Compiler for the abstract-syntax-tree of a '
                    + self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self):',
                    '        super(' + self.grammar_name + 'Compiler, self).__init__()',
                    '',
                    '    def reset(self):',
                    '        super().reset()',
                    '        # initialize your variables here, not in the constructor!',
                    '']
        for name in self.rules:
            method_name = visitor_name(name)
            if name == self.root_symbol:
                compiler += ['    def ' + method_name + '(self, node):',
                             '        return self.fallback_compiler(node)', '']
            else:
                compiler += ['    # def ' + method_name + '(self, node):',
                             '    #     return node', '']
        compiler += [COMPILER_FACTORY.format(NAME=self.grammar_name, ID=self.grammar_id)]
        return '\n'.join(compiler)

    def verify_transformation_table(self, transtable):
        """
        Checks for symbols that occur in the transformation-table but have
        never been defined in the grammar. Usually, this kind of
        inconsistency results from an error like a typo in the transformation
        table.
        """
        assert self._dirty_flag
        table_entries = set(expand_table(transtable).keys()) - {'*', '<', '>', '~'}
        symbols = self.rules.keys()
        messages = []
        for entry in table_entries:
            if entry not in symbols and not entry.startswith(":"):
                messages.append(Error(('Symbol "%s" is not defined in grammar %s but appears in '
                                       'the transformation table!') % (entry, self.grammar_name),
                                      0, Error.UNDEFINED_SYMBOL_IN_TRANSTABLE_WARNING))
        return messages

    def verify_compiler(self, compiler):
        """
        Checks for on_XXXX()-methods that occur in the compiler, although XXXX
        has never been defined in the grammar. Usually, this kind of
        inconsistency results from an error like a typo in the compiler-code.
        """
        pass  # TODO: add verification code here


    def _check_rx(self, node: Node, rx: str) -> str:
        """
        Checks whether the string `rx` represents a valid regular
        expression. Makes sure that multi-line regular expressions are
        prepended by the multi-line-flag. Returns the regular expression string.
        """
        # TODO: Support atomic grouping: https://stackoverflow.com/questions/13577372/
        #       do-python-regular-expressions-have-an-equivalent-to-rubys-atomic-grouping
        flags = self.re_flags | {'x'} if rx.find('\n') >= 0 else self.re_flags
        if flags:
            rx = "(?%s)%s" % ("".join(flags), rx)
        try:
            re.compile(rx)
        except Exception as re_error:
            self.tree.new_error(node, "malformed regular expression %s: %s" %
                                (repr(rx), str(re_error)))
        return rx


    def _extract_regex(self, node: Node) -> str:
        """Extracts regular expression string from regexp-Node."""
        value = node.content.strip("~")
        if value[0] + value[-1] in {'""', "''"}:
            value = escape_re(value[1:-1])
        elif value[0] + value[-1] == '//' and value != '//':
            value = self._check_rx(node, value[1:-1])
        return value


    def _gen_search_rule(self, nd: Node) -> ReprType:
        """Generates a search rule, which can be either a string for simple
        string search or a regular expression from the nodes content. Returns
        an empty string in case the node is neither regexp nor literal.
        """
        if nd.tag_name == 'regexp':
            super_ws = self.directives.super_ws
            nonempty_ws = mixin_nonempty(super_ws)
            search_regex = self._extract_regex(nd)\
                .replace(r'\~!', nonempty_ws).replace(r'\~', super_ws)
            return unrepr("re.compile(r'%s')" % search_regex)
        elif nd.tag_name == 'literal':
            s = nd.content[1:-1]  # remove quotation marks
            return unrepr("re.compile(r'(?=%s)')" % escape_re(s))
        return ''


    def _gen_search_list(self, nodes: Sequence[Node]) -> List[Union[unrepr, str]]:
        search_list = []  # type: List[Union[unrepr, str]]
        for child in nodes:
            rule = self._gen_search_rule(child)
            search_list.append(rule if rule else unrepr(child.content.strip()))
        return search_list


    def assemble_parser(self, definitions: List[Tuple[str, str]]) -> str:
        """
        Creates the Python code for the parser after compilation of
        the EBNF-Grammar
        """

        def pp_rules(rule_name: str, ruleset: Dict[str, List]) -> Tuple[str, str]:
            """Pretty-print skip- and resume-rule and error-messages dictionaries
            to avoid excessively long lines in the generated python source."""
            assert ruleset
            indent = ",\n" + " " * (len(rule_name) + 8)
            rule_repr = []
            for k, v in ruleset.items():
                if len(v) > 1:
                    delimiter = indent + ' ' * (len(k) + 5)
                    val = '[' + delimiter.join(str(it) for it in v) + ']'
                else:
                    val = v
                rule_repr.append("'{key}': {value}".format(key=k, value=str(val)))
            rule_repr[0] = '{' + rule_repr[0]
            rule_repr[-1] = rule_repr[-1] + '}'
            return rule_name, indent.join(rule_repr)

        # execute deferred tasks, for example semantic checks that cannot
        # be done before the symbol table is complete

        for task in self.deferred_tasks:
            task()

        # provide for capturing of symbols that are variables, i.e. the
        # value of which will be retrieved at some point during the parsing process

        if self.variables:
            for i in range(len(definitions)):
                if definitions[i][0] in self.variables:
                    definitions[i] = (definitions[i][0], 'Capture(%s)' % definitions[i][1])

        # add special fields for Grammar class

        if DROP_WSPC in self.directives.drop or DROP_TOKEN in self.directives.drop:
            definitions.append((NewEBNFCompiler.DROP_WHITESPACE_PARSER_KEYWORD,
                                'Drop(Whitespace(%s))' % NewEBNFCompiler.WHITESPACE_KEYWORD))
        definitions.append((NewEBNFCompiler.WHITESPACE_PARSER_KEYWORD,
                            'Whitespace(%s)' % NewEBNFCompiler.WHITESPACE_KEYWORD))
        definitions.append((NewEBNFCompiler.WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace=" + NewEBNFCompiler.RAW_WS_KEYWORD
                             + ", comment=" + NewEBNFCompiler.COMMENT_KEYWORD + ")")))
        if NewEBNFCompiler.RAW_WS_PARSER_KEYWORD in self.required_keywords:
            definitions.append((NewEBNFCompiler.RAW_WS_PARSER_KEYWORD,
                                "Whitespace(%s)" % NewEBNFCompiler.RAW_WS_KEYWORD))
        definitions.append((NewEBNFCompiler.RAW_WS_KEYWORD,
                            "r'{}'".format(self.directives.whitespace)))
        comment_rx = ("re.compile(%s)" % NewEBNFCompiler.COMMENT_KEYWORD) \
            if self.directives.comment else "RX_NEVER_MATCH"
        if NewEBNFCompiler.COMMENT_PARSER_KEYWORD in self.required_keywords:
            definitions.append((NewEBNFCompiler.COMMENT_PARSER_KEYWORD,
                                "RegExp(%s)" % NewEBNFCompiler.COMMENT_RX_KEYWORD))
        definitions.append((NewEBNFCompiler.COMMENT_RX_KEYWORD, comment_rx))
        definitions.append((NewEBNFCompiler.COMMENT_KEYWORD,
                            "r'{}'".format(self.directives.comment)))

        # prepare and add resume-rules

        resume_rules = dict()  # type: Dict[str, List[ReprType]]
        for symbol, raw_rules in self.directives.resume.items():
            refined_rules = []  # type: List[ReprType]
            for rule in raw_rules:
                if isinstance(rule, unrepr) and rule.s.isidentifier():
                    try:
                        nd = self.rules[rule.s][0].children[1]
                        refined = self._gen_search_rule(nd)
                    except IndexError:
                        nd = self.tree
                        refined = ""
                    if refined:
                        refined_rules.append(refined)
                    else:
                        self.tree.new_error(nd, 'Symbol "%s" cannot be used in resume rule, since'
                                                ' it represents neither literal nor regexp!')
                else:
                    refined_rules.append(rule)
            resume_rules[symbol] = refined_rules
        if resume_rules:
            definitions.append(pp_rules(self.RESUME_RULES_KEYWORD, resume_rules))

        # prepare and add skip-rules

        skip_rules = dict()  # # type: Dict[str, List[ReprType]]
        for symbol, skip in self.directives.skip.items():
            rules = []  # type: List[ReprType]
            for search in skip:
                if isinstance(search, unrepr) and search.s.isidentifier():
                    try:
                        nd = self.rules[search.s][0].children[1]
                        search = self._gen_search_rule(nd)
                    except IndexError:
                        search = ''
                rules.append(search)
            skip_rules[symbol] = rules
        if skip_rules:
            definitions.append(pp_rules(self.SKIP_RULES_KEYWORD, skip_rules))

        for symbol in self.directives.skip.keys():
            if symbol not in self.consumed_skip_rules:
                try:
                    def_node = self.rules[symbol][0]
                    self.tree.new_error(
                        def_node, '"Skip-rules" for symbol "{}" will never be used, '
                        'because the mandatory marker "§" appears nowhere in its definiendum!'
                        .format(symbol), Error.UNUSED_ERROR_HANDLING_WARNING)
                except KeyError:
                    pass  # error has already been notified earlier!

        # prepare and add customized error-messages

        error_messages = dict()  # type: Dict[str, List[Tuple[ReprType, ReprType]]]
        for symbol, err_msgs in self.directives.error.items():
            custom_errors = []  # type: List[List[ReprType, ReprType]]
            for search, message in err_msgs:
                if isinstance(search, unrepr) and search.s.isidentifier():
                    try:
                        nd = self.rules[search.s][0].children[1]
                        search = self._gen_search_rule(nd)
                    except IndexError:
                        search = ''
                custom_errors.append([search, message])
            error_messages[symbol] = custom_errors
        if error_messages:
            definitions.append(pp_rules(self.ERR_MSGS_KEYWORD, error_messages))

        for symbol in self.directives.error.keys():
            if symbol not in self.consumed_custom_errors:
                try:
                    def_node = self.rules[symbol][0]
                    self.tree.new_error(
                        def_node, 'Customized error message for symbol "{}" will never be used, '
                        'because the mandatory marker "§" appears nowhere in its definiendum!'
                        .format(symbol), Error.UNUSED_ERROR_HANDLING_WARNING)
                except KeyError:
                    def match_function(nd: Node) -> bool:
                        return bool(nd.children) and nd.children[0].content.startswith(symbol + '_')
                    dir_node = self.tree.pick(match_function)
                    if dir_node:
                        directive = dir_node.children[0].content
                        self.tree.new_error(
                            dir_node, 'Directive "{}" relates to undefined symbol "{}"!'
                            .format(directive, directive.split('_')[0]))

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class

        article = 'an ' if self.grammar_name[0:1] in "AaEeIiOoUu" else 'a '
        # what about 'hour', 'universe' etc.?
        show_source = get_config_value('add_grammar_source_to_parser_docstring')
        declarations = ['class ' + self.grammar_name
                        + 'Grammar(Grammar):',
                        'r"""Parser for ' + article + self.grammar_name
                        + ' source file'
                        + ('. Grammar:' if self.grammar_source and show_source else '.')]
        definitions.append(('parser_initialization__', '["upon instantiation"]'))
        definitions.append(('static_analysis_pending__', '[True]'))
        definitions.append(('anonymous__',
                            're.compile(' + repr(self.anonymous_regexp.pattern) + ')'))
        if self.grammar_source:
            definitions.append(('source_hash__',
                                '"%s"' % md5(self.grammar_source, __version__)))
            declarations.append('')
            if show_source:
                declarations += [line for line in self.grammar_source.split('\n')]
            while declarations[-1].strip() == '':
                declarations = declarations[:-1]
        declarations.append('"""')

        # turn definitions into declarations in reverse order

        self.root_symbol = definitions[0][0] if definitions else ""
        definitions.reverse()
        declarations += [symbol + ' = Forward()'
                         for symbol in sorted(list(self.recursive))]
        for symbol, statement in definitions:
            if symbol in self.recursive:
                declarations += [symbol + '.set(' + statement + ')']
            else:
                declarations += [symbol + ' = ' + statement]

        # check for symbols used but never defined

        defined_symbols = set(self.rules.keys()) | self.RESERVED_SYMBOLS
        for symbol in self.symbols:
            if symbol not in defined_symbols:
                self.tree.new_error(self.symbols[symbol],
                                    "Missing definition for symbol '%s'" % symbol)

        # check for unconnected rules

        defined_symbols.difference_update(self.RESERVED_SYMBOLS)

        def remove_connections(symbol):
            """Recursively removes all symbols which appear in the
            definiens of a particular symbol."""
            if symbol in defined_symbols:
                defined_symbols.remove(symbol)
                for related in self.rules[symbol][1:]:
                    remove_connections(str(related))

        remove_connections(self.root_symbol)
        for leftover in defined_symbols:
            self.tree.new_error(self.rules[leftover][0],
                                ('Rule "%s" is not connected to parser root "%s" !') %
                                (leftover, self.root_symbol), Error.WARNING)

        # set root_symbol parser and assemble python grammar definition

        if self.root_symbol and 'root__' not in self.rules:
            declarations.append('root__ = ' + self.root_symbol)
        declarations.append('')
        self._result = '\n    '.join(declarations) \
                       + GRAMMAR_FACTORY.format(NAME=self.grammar_name, ID=self.grammar_id)
        return self._result


    # compilation methods ###


    def on_ZOMBIE__(self, node: Node) -> str:
        result = ['Errors in EBNF-source! Fragments found: ']
        result.extend([str(self.compile(child)) for child in node.children])
        return '\n'.join(result)


    def on_syntax(self, node: Node) -> str:
        definitions = []  # type: List[Tuple[str, str]]

        # drop the wrapping sequence node
        if len(node.children) == 1 and node.children[0].anonymous:
            node = node.children[0]

        # compile definitions and directives and collect definitions
        for nd in node.children:
            if nd.tag_name == "definition":
                definitions.append(self.compile(nd))
            else:
                assert nd.tag_name == "directive", nd.as_sxpr()
                self.compile(nd)
        self.definitions.update(definitions)

        grammar_python_src = self.assemble_parser(definitions)
        if get_config_value('static_analysis') == 'early':
            try:
                grammar_class = compile_python_object(
                    DHPARSER_IMPORTS.format(dhparser_parentdir=DHPARSER_PARENTDIR)
                    + grammar_python_src, self.grammar_name)
                _ = grammar_class()
                grammar_python_src = grammar_python_src.replace(
                    'static_analysis_pending__ = [True]',
                    'static_analysis_pending__ = []  # type: List[bool]', 1)
            except NameError:
                pass  # undefined name in the grammar are already caught and reported
            except GrammarError as error:
                for sym, _, err in error.errors:
                    symdef_node = self.rules[sym][0]
                    err.pos = self.rules[sym][0].pos
                    self.tree.add_error(symdef_node, err)
        return grammar_python_src


    def on_definition(self, node: Node) -> Tuple[str, str]:
        rule = node.children[0].content
        if rule in self.rules:
            first = self.rules[rule][0]
            if not id(first) in self.tree.error_nodes:
                self.tree.new_error(first, 'First definition of rule "%s" '
                                    'followed by illegal redefinitions.' % rule)
            self.tree.new_error(node, 'A rule "%s" has already been defined earlier.' % rule)
        elif rule in NewEBNFCompiler.RESERVED_SYMBOLS:
            self.tree.new_error(node, 'Symbol "%s" is a reserved symbol.' % rule)
        elif not sane_parser_name(rule):
            self.tree.new_error(node, 'Illegal symbol "%s". Symbols must not start or '
                                ' end with a doube underscore "__".' % rule)
        elif rule in self.directives.tokens:
            self.tree.new_error(node, 'Symbol "%s" has already been defined as '
                                'a preprocessor token.' % rule)
        elif keyword.iskeyword(rule):
            self.tree.new_error(node, 'Python keyword "%s" may not be used as a symbol. '
                                % rule + '(This may change in the future.)')
        try:
            self.current_symbols = [node]
            self.rules[rule] = self.current_symbols
            self.drop_flag = rule in self.directives['drop'] and rule not in DROP_VALUES
            defn = self.compile(node.children[1])
            if rule in self.variables:
                defn = 'Capture(%s)' % defn
                self.variables.remove(rule)
            elif defn.find("(") < 0:
                # assume it's a synonym, like 'page = REGEX_PAGE_NR'
                defn = 'Synonym(%s)' % defn
            # if self.drop_flag:
            #     defn = 'Drop(%s)' % defn
            # TODO: Recursively drop all contained parsers for optimization
        except TypeError as error:
            from traceback import extract_tb, format_list
            trace = ''.join(format_list((extract_tb(error.__traceback__))))
            errmsg = "%s (TypeError: %s;\n%s)\n%s" \
                     % (NewEBNFCompiler.AST_ERROR, str(error), trace, node.as_sxpr())
            self.tree.new_error(node, errmsg)
            rule, defn = rule + ':error', '"' + errmsg + '"'
        finally:
            self.drop_flag = False
        return rule, defn


    def on_directive(self, node: Node) -> str:
        key = node.children[0].content
        assert key not in self.directives.tokens

        if key not in self.REPEATABLE_DIRECTIVES and not key.endswith('_error'):
            if key in self.defined_directives:
                self.tree.new_error(node, 'Directive "%s" has already been defined earlier. '
                                    % key + 'Later definition will be ignored!',
                                    code=Error.REDEFINED_DIRECTIVE)
                return ""
            self.defined_directives.add(key)

        def check_argnum(n: int = 1):
            if len(node.children) > n + 1:
                self.tree.new_error(node, 'Directive "%s" can have at most %i values.' % (key, n))

        if key in {'comment', 'whitespace'}:
            check_argnum()
            if node.children[1].tag_name == "symbol":
                value = node.children[1].content
                if key == 'whitespace' and value in WHITESPACE_TYPES:
                    value = WHITESPACE_TYPES[value]  # replace whitespace-name by regex
                else:
                    self.tree.new_error(node, 'Value "%s" not allowed for directive "%s".'
                                        % (value, key))
            else:
                value = self._extract_regex(node.children[1])
                if key == 'whitespace' and not re.match(value, ''):
                    self.tree.new_error(node, "Implicit whitespace should always "
                                        "match the empty string, /%s/ does not." % value)
            self.directives[key] = value

        elif key == 'anonymous':
            if node.children[1].tag_name == "regexp":
                check_argnum()
                re_pattern = node.children[1].content[1:-1]
                if re.match(re_pattern, ''):
                    self.tree.new_error(
                        node, "The regular expression r'%s' matches any symbol, "
                        "which is not allowed!" % re_pattern)
                else:
                    self.anonymous_regexp = re.compile(re_pattern)
            else:
                args = node.children[1:]
                assert all(child.tag_name == "symbol" for child in args)
                alist = [child.content for child in args]
                for asym in alist:
                    if asym not in self.symbols:
                        self.symbols[asym] = node
                self.anonymous_regexp = re.compile('$|'.join(alist) + '$')

        elif key == 'drop':
            if len(node.children) <= 1:
                self.tree.new_error(node, 'Directive "@ drop" requires as least one argument!')
            for child in node.children[1:]:
                content = child.content
                if self.anonymous_regexp.match(content):
                    self.directives[key].add(content)
                elif content.lower() in DROP_VALUES:
                    self.directives[key].add(content.lower())
                else:
                    if self.anonymous_regexp == RX_NEVER_MATCH:
                        self.tree.new_error(node, 'Illegal value "%s" for Directive "@ drop"! '
                                            ' Should be one of %s.' % (content, str(DROP_VALUES)))
                    else:
                        self.tree.new_error(
                            node, 'Illegal value "%s" for Directive "@ drop"! Should be one of '
                            '%s or a string matching r"%s".' % (content, str(DROP_VALUES),
                                                                self.anonymous_regexp.pattern))

        elif key == 'ignorecase':
            check_argnum()
            if node.children[1].content.lower() not in {"off", "false", "no"}:
                self.re_flags.add('i')

        elif key == 'literalws':
            values = {child.content.strip().lower() for child in node.children[1:]}
            if ((values - {'left', 'right', 'both', 'none'})
                    or ('none' in values and len(values) > 1)):
                self.tree.new_error(node, 'Directive "literalws" allows only `left`, `right`, '
                                    '`both` or `none`, not `%s`' % ", ".join(values))
            wsp = {'left', 'right'} if 'both' in values \
                else set() if 'none' in values else values
            self.directives.literalws = wsp

        elif key in {'tokens', 'preprocessor_tokens'}:
            tokens = {child.content.strip() for child in node.children[1:]}
            redeclared = self.directives.tokens & tokens
            if redeclared:
                self.tree.new_error(node, 'Tokens %s have already been declared earlier. '
                                    % str(redeclared) + 'Later declaration will be ignored',
                                    code=Error.REDECLARED_TOKEN_WARNING)
            self.directives.tokens |= tokens - redeclared

        elif key.endswith('_filter'):
            check_argnum()
            symbol = key[:-7]
            self.directives.filter[symbol] = node.children[1].content.strip()

        elif key.endswith('_error'):
            check_argnum(2)
            symbol = key[:-6]
            error_msgs = self.directives.error.get(symbol, [])
            if symbol in self.rules:
                self.tree.new_error(node, 'Custom error message for symbol "%s"' % symbol
                                    + ' must be defined before the symbol!')
            if node.children[1 if len(node.children) == 2 else 2].tag_name != 'literal':
                self.tree.new_error(
                    node, 'Directive "%s" requires message string or a a pair ' % key
                    + '(regular expression or search string, message string) as argument!')
            if len(node.children) == 2:
                error_msgs.append(('', unrepr(node.children[1].content)))
            elif len(node.children) == 3:
                rule = self._gen_search_rule(node.children[1])
                error_msgs.append((rule if rule else unrepr(node.children[1].content),
                                   unrepr(node.children[2].content)))
            else:
                self.tree.new_error(node, 'Directive "%s" allows at most two parameters' % key)
            self.directives.error[symbol] = error_msgs

        elif key.endswith('_skip'):
            symbol = key[:-5]
            if symbol in self.rules:
                self.tree.new_error(node, 'Skip list for resuming in series for symbol "{}"'
                                    'must be defined before the symbol!'.format(symbol))
            self.directives.skip[symbol] = self._gen_search_list(node.children[1:])

        elif key.endswith('_resume'):
            symbol = key[:-7]
            self.directives.resume[symbol] = self._gen_search_list(node.children[1:])

        else:
            if any(key.startswith(directive) for directive in ('skip', 'error', 'resume')):
                kl = key.split('_')
                proper_usage = '_'.join(kl[1:] + kl[0:1])
                self.tree.new_error(node, 'Directive "%s" must be used as postfix not prefix to '
                                    'the symbolname. Please, write: "%s"' % (kl[0], proper_usage))
            else:
                self.tree.new_error(node, 'Unknown directive %s ! (Known ones are %s .)' %
                                    (key, ', '.join(list(self.directives.keys()))))
        #
        # try:
        #     if symbol not in self.symbols:
        #         # remember first use of symbol, so that dangling references or
        #         # redundant definitions or usages of symbols can be detected later
        #         self.symbols[symbol] = node
        # except NameError:
        #     pass  # no symbol was referred to in directive

        return ""


    def non_terminal(self, node: Node, parser_class: str, custom_args: List[str] = []) -> str:
        """
        Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        arguments = [self.compile(r) for r in node.children] + custom_args
        assert all(isinstance(arg, str) for arg in arguments), str(arguments)
        # remove drop clause for non dropping definitions of forms like "/\w+/~"
        if (parser_class == "Series" and node.tag_name not in self.directives.drop
            and DROP_REGEXP in self.directives.drop and self.context[-2].tag_name == "definition"
            and all((arg.startswith('Drop(RegExp(') or arg.startswith('Drop(Token(')
                     or arg in NewEBNFCompiler.COMMENT_OR_WHITESPACE) for arg in arguments)):
            arguments = [arg.replace('Drop(', '').replace('))', ')') for arg in arguments]
        if self.drop_flag:
            return 'Drop(' + parser_class + '(' + ', '.join(arguments) + '))'
        else:
            return parser_class + '(' + ', '.join(arguments) + ')'


    def on_expression(self, node) -> str:
        # TODO: Add check for errors like "a" | "ab" (which will always yield a, even for ab)
        return self.non_terminal(node, 'Alternative')


    def _error_customization(self, node) -> Tuple[Tuple[Node, ...], List[str]]:
        """Generates the customization arguments (mantary, error_msgs, skip) for
        `MandatoryNary`-parsers (Series, Allof, ...)."""
        mandatory_marker = []
        filtered_children = []  # type: List[Node]
        for nd in node.children:
            if nd.tag_name == TOKEN_PTYPE and nd.content == "§":
                mandatory_marker.append(len(filtered_children))
                if len(mandatory_marker) > 1:
                    self.tree.new_error(nd, 'One mandatory marker (§) is sufficient to declare '
                                        'the rest of the elements as mandatory.', Error.WARNING)
            else:
                filtered_children.append(nd)
        custom_args = ['mandatory=%i' % mandatory_marker[0]] if mandatory_marker else []
        # add custom error message if it has been declared for the current definition
        if custom_args:
            current_symbol = next(reversed(self.rules.keys()))
            # add customized error messages, if defined
            if current_symbol in self.directives.error:
                if current_symbol in self.consumed_custom_errors:
                    self.tree.new_error(
                        node, "Cannot apply customized error messages unambiguously, because "
                        "symbol {} contains more than one parser with a mandatory marker '§' "
                        "in its definiens.".format(current_symbol),
                        Error.AMBIGUOUS_ERROR_HANDLING)
                else:
                    # use class field instead or direct representation of error messages!
                    custom_args.append('err_msgs={err_msgs_name}["{symbol}"]'
                                       .format(err_msgs_name=self.ERR_MSGS_KEYWORD,
                                               symbol=current_symbol))
                    self.consumed_custom_errors.add(current_symbol)
            # add skip-rules to resume parsing of a series, if rules have been declared
            if current_symbol in self.directives.skip:
                if current_symbol in self.consumed_skip_rules:
                    self.tree.new_error(
                        node, "Cannot apply 'skip-rules' unambigiously, because symbol "
                        "{} contains more than one parser with a mandatory marker '§' "
                        "in its definiens.".format(current_symbol),
                        Error.AMBIGUOUS_ERROR_HANDLING)
                else:
                    # use class field instead or direct representation of error messages!
                    custom_args.append('skip={skip_rules_name}["{symbol}"]'
                                       .format(skip_rules_name=self.SKIP_RULES_KEYWORD,
                                               symbol=current_symbol))
                    self.consumed_skip_rules.add(current_symbol)
        return tuple(filtered_children), custom_args


    def on_sequence(self, node) -> str:
        filtered_result, custom_args = self._error_customization(node)
        mock_node = Node(node.tag_name, filtered_result)
        return self.non_terminal(mock_node, 'Series', custom_args)


    def on_lookaround(self, node: Node) -> str:
        assert node.children
        assert len(node.children) == 2
        assert node.children[0].tag_name == 'flowmarker'
        prefix = node.children[0].content
        arg_node = node.children[1]
        node.result = node.children[1:]
        assert prefix in {'&', '!', '<-&', '<-!'}

        parser_class = self.PREFIX_TABLE[prefix]
        result = self.non_terminal(node, parser_class)
        if prefix[:2] == '<-':
            def verify(node):
                nd = node
                if len(nd.children) >= 1:
                    nd = nd.children[0]
                while nd.tag_name == "symbol":
                    symlist = self.rules.get(nd.content, [])
                    if len(symlist) == 2:
                        nd = symlist[1]
                    else:
                        if len(symlist) == 1:
                            nd = symlist[0].children[1]
                        break
                content = nd.content
                if (nd.tag_name != "regexp" or content[:1] != '/' or content[-1:] != '/'):
                    self.tree.new_error(node, "Lookbehind-parser can only be used with RegExp"
                                              "-parsers, not: " + nd.tag_name)

            if not result.startswith('RegExp('):
                self.deferred_tasks.append(partial(verify, node= node))
        return result


    def on_element(self, node: Node) -> str:
        assert node.children
        assert len(node.children) == 2
        assert node.children[0].tag_name == "retrieve_op"
        assert node.children[1].tag_name == "symbol"
        prefix = node.children[0].content  # type: str
        arg = node.children[1].content     # type: str
        node.result = node.children[1:]
        assert prefix in {'::', ':?', ':'}

        if self.anonymous_regexp.match(arg):
            self.tree.new_error(
                node, ('Retrive operator "%s" does not work with anonymous parsers like %s')
                      % (prefix, arg))
            return arg

        custom_args = []           # type: List[str]
        match_func = 'last_value'  # type: str
        if arg in self.directives.filter:
            match_func = self.directives.filter[arg]
        if prefix.endswith('?'):
            match_func = 'optional_' + match_func
        if match_func != 'last_value':
            custom_args = ['match_func=%s' % match_func]

        self.variables.add(arg)
        parser_class = self.PREFIX_TABLE[prefix]
        return self.non_terminal(node, parser_class, custom_args)


    def on_option(self, node) -> str:
        return self.non_terminal(node, 'Option')


    def on_repetition(self, node) -> str:
        return self.non_terminal(node, 'ZeroOrMore')


    def on_oneormore(self, node) -> str:
        return self.non_terminal(node, 'OneOrMore')


    def on_group(self, node) -> str:
        raise EBNFCompilerError("Group nodes should have been eliminated by "
                                "AST transformation!")

    def on_unordered(self, node) -> str:
        # return self.non_terminal(node, 'Unordered')
        assert len(node.children) == 1
        nd = node.children[0]
        if nd.tag_name == "sequence":
            filtered_result, custom_args = self._error_customization(nd)
            mock_node = Node(nd.tag_name, filtered_result)
            return self.non_terminal(mock_node, 'AllOf', custom_args)
        elif nd.tag_name == "expression":
            if any(c.tag_name == TOKEN_PTYPE and nd.content == '§' for c in nd.children):
                self.tree.new_error(node, "No mandatory items § allowed in SomeOf-operator!")
            # args = ', '.join(self.compile(child) for child in nd.children)
            return self.non_terminal(nd, 'SomeOf')  # "SomeOf(" + args + ")"
        else:
            # if a sequence or expression has only one element, it will have
            # been reduced during AST-transformation. Thus, if the tag-name of
            # a child of unordered is neither "sequence" nor "expression", there
            # are too few arguments for "unordered".
            self.tree.new_error(node, "Unordered sequence or alternative "
                                      "requires at least two elements.")
            return ""

    def on_symbol(self, node: Node) -> str:     # called only for symbols on the right hand side!
        symbol = node.content  # ; assert result == cast(str, node.result)
        if symbol in self.directives.tokens:
            return 'PreprocessorToken("' + symbol + '")'
        else:
            self.current_symbols.append(node)
            if symbol not in self.symbols:
                # remember first use of symbol, so that dangling references or
                # redundant definitions or usages of symbols can be detected later
                self.symbols[symbol] = node
            if symbol in self.rules:
                self.recursive.add(symbol)
            if symbol in NewEBNFCompiler.KEYWORD_SUBSTITUTION:
                keyword = NewEBNFCompiler.KEYWORD_SUBSTITUTION[symbol]
                self.required_keywords.add(keyword)
                return keyword
            elif symbol.endswith('__'):
                self.tree.new_error(node, 'Illegal use of reserved symbol name "%s"!' % symbol)
            return symbol


    def TOKEN_PARSER(self, token):
        if DROP_TOKEN in self.directives.drop and self.context[-2].tag_name != "definition":
            return 'Drop(Token(' + token + '))'
        return 'Token(' + token + ')'

    def REGEXP_PARSER(self, regexp):
        if DROP_REGEXP in self.directives.drop and self.context[-2].tag_name != "definition":
            return 'Drop(RegExp(' + regexp + '))'
        return 'RegExp(' + regexp + ')'


    def WSPC_PARSER(self, force_drop=False):
        if ((force_drop or DROP_WSPC in self.directives.drop)
                and (self.context[-2].tag_name != "definition"
                     or self.context[-1].tag_name == 'literal')):
            return 'dwsp__'
        return 'wsp__'

    def on_literal(self, node: Node) -> str:
        center = self.TOKEN_PARSER(node.content.replace('\\', r'\\'))
        force = DROP_TOKEN in self.directives.drop
        left = self.WSPC_PARSER(force) if 'left' in self.directives.literalws else ''
        right = self.WSPC_PARSER(force) if 'right' in self.directives.literalws else ''
        if left or right:
            return 'Series(' + ", ".join(item for item in (left, center, right) if item) + ')'
        return center


    def on_plaintext(self, node: Node) -> str:
        tk = node.content.replace('\\', r'\\')
        rpl = '"' if tk.find('"') < 0 else "'" if tk.find("'") < 0 else ''
        if rpl:
            tk = rpl + tk[1:-1] + rpl
        else:
            tk = rpl + tk.replace('"', '\\"')[1:-1] + rpl
        return self.TOKEN_PARSER(tk)


    def on_regexp(self, node: Node) -> str:
        rx = node.content
        name = []   # type: List[str]
        assert rx[0] == '/' and rx[-1] == '/'
        try:
            arg = repr(self._check_rx(node, rx[1:-1].replace(r'\/', '/')))
        except AttributeError as error:
            from traceback import extract_tb, format_list
            trace = ''.join(format_list(extract_tb(error.__traceback__)))
            errmsg = "%s (AttributeError: %s;\n%s)\n%s" \
                     % (NewEBNFCompiler.AST_ERROR, str(error), trace, node.as_sxpr())
            self.tree.new_error(node, errmsg)
            return '"' + errmsg + '"'
        return self.REGEXP_PARSER(', '.join([arg] + name))


    def on_whitespace(self, node: Node) -> str:
        return self.WSPC_PARSER()



# class NewEBNFCompiler(Compiler):
#     """Compiler for the abstract-syntax-tree of a NewEBNF source file.
#     """
#
#     def __init__(self):
#         super(NewEBNFCompiler, self).__init__()
#
#     def reset(self):
#         super().reset()
#         # initialize your variables here, not in the constructor!
#
#     def on_syntax(self, node):
#         return self.fallback_compiler(node)
#
#     # def on_definition(self, node):
#     #     return node
#
#     # def on_directive(self, node):
#     #     return node
#
#     # def on_expression(self, node):
#     #     return node
#
#     # def on_sequence(self, node):
#     #     return node
#
#     # def on_interleave(self, node):
#     #     return node
#
#     # def on_term(self, node):
#     #     return node
#
#     # def on_pure_elem(self, node):
#     #     return node
#
#     # def on_element(self, node):
#     #     return node
#
#     # def on_flowmarker(self, node):
#     #     return node
#
#     # def on_retrieveop(self, node):
#     #     return node
#
#     # def on_group(self, node):
#     #     return node
#
#     # def on_oneormore(self, node):
#     #     return node
#
#     # def on_repetition(self, node):
#     #     return node
#
#     # def on_option(self, node):
#     #     return node
#
#     # def on_symbol(self, node):
#     #     return node
#
#     # def on_literal(self, node):
#     #     return node
#
#     # def on_plaintext(self, node):
#     #     return node
#
#     # def on_regexp(self, node):
#     #     return node
#
#     # def on_whitespace(self, node):
#     #     return node
#
#     # def on_EOF(self, node):
#     #     return node



def get_compiler(grammar_name="", grammar_source="") -> NewEBNFCompiler:
    """Returns a thread/process-exclusive NewEBNFCompiler-singleton."""
    THREAD_LOCALS = access_thread_locals()
    try:
        compiler = THREAD_LOCALS.NewEBNF_00000001_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    except AttributeError:
        THREAD_LOCALS.NewEBNF_00000001_compiler_singleton = NewEBNFCompiler()
        compiler = THREAD_LOCALS.NewEBNF_00000001_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
    return compiler


def compile_ebnf_ast(ast: Node) -> str:
    """Compiles the abstract-syntax-tree of an EBNF-source-text into
    python code of a class derived from `parse.Grammar` that can
    parse text following the grammar describend with the EBNF-code."""
    return get_compiler()(ast)


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
        print("Usage: NewEBNFParser.py [FILENAME]")
