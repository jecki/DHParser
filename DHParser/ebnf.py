# ebnf.py - EBNF -> Python-Parser compilation for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.


"""
Module ``ebnf`` provides a self-hosting parser for EBNF-Grammars as
well as an EBNF-compiler that compiles an EBNF-Grammar into a
DHParser based Grammar class that can be executed to parse source text
conforming to this grammar into contrete syntax trees.
"""


from collections import OrderedDict
from functools import partial
import keyword
import os
from typing import Callable, Dict, List, Set, Tuple, Sequence, Union, Optional, Any, cast

from DHParser.compile import CompilerError, Compiler, compile_source, visitor_name
from DHParser.configuration import THREAD_LOCALS, get_config_value
from DHParser.error import Error
from DHParser.parse import Grammar, mixin_comment, Forward, RegExp, DropWhitespace, \
    NegativeLookahead, Alternative, Series, Option, OneOrMore, ZeroOrMore, Token, \
    GrammarError
from DHParser.preprocess import nil_preprocessor, PreprocessorFunc
from DHParser.syntaxtree import Node, WHITESPACE_PTYPE, TOKEN_PTYPE
from DHParser.toolkit import load_if_file, escape_re, md5, sane_parser_name, re, expand_table, \
    unrepr, compile_python_object, DHPARSER_PARENTDIR, NEVER_MATCH_PATTERN
from DHParser.transform import TransformationFunc, traverse, remove_brackets, \
    reduce_single_child, replace_by_single_child, remove_whitespace, remove_empty, \
    remove_tokens, flatten, forbid, assert_content
from DHParser.versionnumber import __version__


__all__ = ('get_ebnf_preprocessor',
           'get_ebnf_grammar',
           'get_ebnf_transformer',
           'get_ebnf_compiler',
           'EBNFGrammar',
           'EBNFTransform',
           'EBNFCompilerError',
           'EBNFCompiler',
           'grammar_changed',
           'compile_ebnf',
           'PreprocessorFactoryFunc',
           'ParserFactoryFunc',
           'TransformerFactoryFunc',
           'CompilerFactoryFunc')


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

if r'{dhparser_parentdir}' not in sys.path:
    sys.path.append(r'{dhparser_parentdir}')

try:
    import regex as re
except ImportError:
    import re
from DHParser import start_logging, suspend_logging, resume_logging, is_filename, load_if_file, \\
    Grammar, Compiler, nil_preprocessor, PreprocessorToken, Whitespace, DropWhitespace, \\
    Lookbehind, Lookahead, Alternative, Pop, Token, DropToken, Synonym, AllOf, SomeOf, \\
    Unordered, Option, NegativeLookbehind, OneOrMore, RegExp, Retrieve, Series, Capture, \\
    ZeroOrMore, Forward, NegativeLookahead, Required, mixin_comment, compile_source, \\
    grammar_changed, last_value, counterpart, PreprocessorFunc, is_empty, remove_if, \\
    Node, TransformationFunc, TransformationDict, transformation_factory, traverse, \\
    remove_children_if, move_adjacent, normalize_whitespace, is_anonymous, matches_re, \\
    reduce_single_child, replace_by_single_child, replace_or_reduce, remove_whitespace, \\
    replace_by_children, remove_empty, remove_tokens, flatten, is_insignificant_whitespace, \\
    merge_adjacent, collapse, collapse_children_if, replace_content, WHITESPACE_PTYPE, TOKEN_PTYPE, \\
    remove_nodes, remove_content, remove_brackets, change_tag_name, remove_anonymous_tokens, \\
    keep_children, is_one_of, not_one_of, has_content, apply_if, remove_first, remove_last, \\
    remove_anonymous_empty, keep_nodes, traverse_locally, strip, lstrip, rstrip, \\
    replace_content, replace_content_by, forbid, assert_content, remove_infix_operator, \\
    error_on, recompile_grammar, left_associative, lean_left, set_config_value, \\
    get_config_value, XML_SERIALIZATION, SXPRESSION_SERIALIZATION, COMPACT_SERIALIZATION, \\
    JSON_SERIALIZATION, access_thread_locals, access_presets, finalize_presets, ErrorCode, \\
    RX_NEVER_MATCH
'''.format(dhparser_parentdir=DHPARSER_PARENTDIR)


########################################################################
#
# EBNF scanning
#
########################################################################


def get_ebnf_preprocessor() -> PreprocessorFunc:
    """
    Returns the preprocessor function for the EBNF compiler.
    As of now, no preprocessing is needed for EBNF-sources. Therefore,
    just a dummy function is returned.
    """
    return nil_preprocessor


########################################################################
#
# EBNF parsing
#
########################################################################


class EBNFGrammar(Grammar):
    r"""
    Parser for an EBNF source file, with this grammar:

    @ comment    = /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
    @ whitespace = /\s*/                            # whitespace includes linefeed
    @ literalws  = right                            # trailing whitespace of literals will be ignored tacitly
    @ drop       = whitespace                       # do not include whitespace in concrete syntax tree

    #: top-level

    syntax     = [~//] { definition | directive } §EOF
    definition = symbol §"=" expression
    directive  = "@" §symbol "=" (regexp | literal | symbol) { "," (regexp | literal | symbol) }

    #: components

    expression = term { "|" term }
    term       = { ["§"] factor }+                       # "§" means all following factors mandatory
    factor     = [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
               | [flowmarker] literal
               | [flowmarker] plaintext
               | [flowmarker] regexp
               | [flowmarker] whitespace
               | [flowmarker] oneormore
               | [flowmarker] group
               | [flowmarker] unordered
               | repetition
               | option

    #: flow-operators

    flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
               | "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
    retrieveop = "::" | ":"                         # '::' pop, ':' retrieve

    #: groups

    group      = "(" §expression ")"
    unordered  = "<" §expression ">"                # elements of expression in arbitrary order
    oneormore  = "{" expression "}+"
    repetition = "{" §expression "}"
    option     = "[" §expression "]"

    #: leaf-elements

    symbol     = /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
    literal    = /"(?:(?<!\\)\\"|[^"])*?"/~         # e.g. "(", '+', 'while'
               | /'(?:(?<!\\)\\'|[^'])*?'/~         # whitespace following literals will be ignored tacitly.
    plaintext  = /`(?:(?<!\\)\\`|[^`])*?`/~         # like literal but does not eat whitespace
    regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~     # e.g. /\w+/, ~/#.*(?:\n|$)/~
    whitespace = /~/~                               # insignificant whitespace

    EOF = !/./
    """
    expression = Forward()
    source_hash__ = "82a7c668f86b83f86515078e6c9093ed"
    static_analysis_pending__ = []
    parser_initialization__ = ["upon instantiation"]
    COMMENT__ = r'#.*(?:\n|$)'
    WHITESPACE__ = r'\s*'
    WSP_RE__ = mixin_comment(whitespace=WHITESPACE__, comment=COMMENT__)
    wsp__ = DropWhitespace(WSP_RE__)
    EOF = NegativeLookahead(RegExp('.'))
    whitespace = Series(RegExp('~'), wsp__)
    regexp = Series(RegExp('/(?:(?<!\\\\)\\\\(?:/)|[^/])*?/'), wsp__)
    plaintext = Series(RegExp('`(?:(?<!\\\\)\\\\`|[^`])*?`'), wsp__)
    literal = Alternative(Series(RegExp('"(?:(?<!\\\\)\\\\"|[^"])*?"'), wsp__),
                          Series(RegExp("'(?:(?<!\\\\)\\\\'|[^'])*?'"), wsp__))
    symbol = Series(RegExp('(?!\\d)\\w+'), wsp__)
    option = Series(Series(Token("["), wsp__), expression, Series(Token("]"), wsp__), mandatory=1)
    repetition = Series(Series(Token("{"), wsp__), expression, Series(Token("}"), wsp__), mandatory=1)
    oneormore = Series(Series(Token("{"), wsp__), expression, Series(Token("}+"), wsp__))
    unordered = Series(Series(Token("<"), wsp__), expression, Series(Token(">"), wsp__), mandatory=1)
    group = Series(Series(Token("("), wsp__), expression, Series(Token(")"), wsp__), mandatory=1)
    retrieveop = Alternative(Series(Token("::"), wsp__), Series(Token(":"), wsp__))
    flowmarker = Alternative(Series(Token("!"), wsp__), Series(Token("&"), wsp__),
                             Series(Token("-!"), wsp__), Series(Token("-&"), wsp__))
    factor = Alternative(Series(Option(flowmarker), Option(retrieveop), symbol,
                                NegativeLookahead(Series(Token("="), wsp__))), Series(Option(flowmarker), literal),
                         Series(Option(flowmarker), plaintext), Series(Option(flowmarker), regexp),
                         Series(Option(flowmarker), whitespace), Series(Option(flowmarker), oneormore),
                         Series(Option(flowmarker), group), Series(Option(flowmarker), unordered), repetition, option)
    term = OneOrMore(Series(Option(Series(Token("§"), wsp__)), factor))
    expression.set(Series(term, ZeroOrMore(Series(Series(Token("|"), wsp__), term))))
    directive = Series(Series(Token("@"), wsp__), symbol, Series(Token("="), wsp__),
                       Alternative(regexp, literal, symbol),
                       ZeroOrMore(Series(Series(Token(","), wsp__), Alternative(regexp, literal, symbol))), mandatory=1)
    definition = Series(symbol, Series(Token("="), wsp__), expression, mandatory=1)
    syntax = Series(Option(Series(wsp__, RegExp(''))), ZeroOrMore(Alternative(definition, directive)), EOF, mandatory=2)
    root__ = syntax


def grammar_changed(grammar_class, grammar_source: str) -> bool:
    """
    Returns ``True`` if ``grammar_class`` does not reflect the latest
    changes of ``grammar_source``

    Parameters:
        grammar_class:  the parser class representing the grammar
            or the file name of a compiler suite containing the grammar
        grammar_source:  File name or string representation of the
            EBNF code of the grammar

    Returns (bool):
        True, if the source text of the grammar is different from the
        source from which the grammar class was generated
    """
    grammar = load_if_file(grammar_source)
    chksum = md5(grammar, __version__)
    if isinstance(grammar_class, str):
        # grammar_class = load_compiler_suite(grammar_class)[1]
        with open(grammar_class, 'r', encoding='utf8') as f:
            pycode = f.read()
        m = re.search(r'class \w*\(Grammar\)', pycode)
        if m:
            m = re.search('    source_hash__ *= *"([a-z0-9]*)"',
                          pycode[m.span()[1]:])
            return not (m and m.groups() and m.groups()[-1] == chksum)
        else:
            return True
    else:
        return chksum != grammar_class.source_hash__


def get_ebnf_grammar() -> EBNFGrammar:
    try:
        grammar = THREAD_LOCALS.ebnf_grammar_singleton
        return grammar
    except AttributeError:
        THREAD_LOCALS.ebnf_grammar_singleton = EBNFGrammar()
        return THREAD_LOCALS.ebnf_grammar_singleton


########################################################################
#
# EBNF concrete to abstract syntax tree transformation and validation
#
########################################################################


EBNF_AST_transformation_table = {
    # AST Transformations for EBNF-grammar
    "<":
        [remove_empty],  # remove_whitespace
    "syntax":
        [],  # otherwise '"*": replace_by_single_child' would be applied
    "directive, definition":
        [flatten, remove_tokens('@', '=', ',')],
    "expression":
        [replace_by_single_child, flatten, remove_tokens('|')],  # remove_infix_operator],
    "term":
        [replace_by_single_child, flatten],  # supports both idioms:
                                             # "{ factor }+" and "factor { factor }"
    "factor, flowmarker, retrieveop":
        replace_by_single_child,
    "group":
        [remove_brackets, replace_by_single_child],
    "unordered":
        remove_brackets,
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets,
         forbid('repetition', 'option', 'oneormore'), assert_content(r'(?!§)(?:.|\n)*')],
    "symbol, literal, regexp":
        reduce_single_child,
    (TOKEN_PTYPE, WHITESPACE_PTYPE):
        reduce_single_child,
    "*":
        replace_by_single_child
}


def EBNFTransform() -> TransformationFunc:
    return partial(traverse, processing_table=EBNF_AST_transformation_table.copy())


def get_ebnf_transformer() -> TransformationFunc:
    try:
        transformer = THREAD_LOCALS.EBNF_transformer_singleton
    except AttributeError:
        THREAD_LOCALS.EBNF_transformer_singleton = EBNFTransform()
        transformer = THREAD_LOCALS.EBNF_transformer_singleton
    return transformer


########################################################################
#
# EBNF abstract syntax tree to Python parser compilation
#
########################################################################


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
DROP_VALUES = {DROP_TOKEN, DROP_WSPC}

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
        filter:  mapping of symbols to python filter functions that
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
                for the series-parser when a mandatory item failed to
                match the following text.

        resume:  mapping of symbols to a list of search expressions. A
                search expressions can be either a string ot a regular
                expression. The closest match is the point of reentry
                for after a parsing error has error occurred. Other
                than the skip field, this configures resuming after
                the failing parser has returned.
    """
    __slots__ = ['whitespace', 'comment', 'literalws', 'tokens', 'filter', 'error', 'skip',
                 'resume', 'drop']

    def __init__(self):
        self.whitespace = WHITESPACE_TYPES['vertical']  # type: str
        self.comment = ''     # type: str
        self.literalws = {'right'}  # type: Collection[str]
        self.tokens = set()   # type: Collection[str]
        self.filter = dict()  # type: Dict[str, str]
        self.error = dict()   # type: Dict[str, List[Tuple[ReprType, ReprType]]]
        self.skip = dict()    # type: Dict[str, List[Union[unrepr, str]]]
        self.resume = dict()  # type: Dict[str, List[Union[unrepr, str]]]
        self.drop = set()     # type: Set[str]

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        assert hasattr(self, key)
        setattr(self, key, value)

    def keys(self):
        return self.__slots__


class EBNFCompilerError(CompilerError):
    """Error raised by `EBNFCompiler` class. (Not compilation errors
    in the strict sense, see `CompilationError` in module ``dsl.py``)"""
    pass


class EBNFCompiler(Compiler):
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

        deferred_tasks:  A list of callables that is filled during
                compilatation, but that will be executed only after
                compilation has finished. Typically, it contains
                sementatic checks that require information that
                is only available upon completion of compilation.

        root_symbol: The name of the root symbol.

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

        grammar_name:  The name of the grammar to be compiled

        grammar_source:  The source code of the grammar to be compiled.

        grammar_id: a unique id for every compiled grammar. (Required for
                disambiguation of of thread local variables storing
                compiled texts.)
    """
    COMMENT_KEYWORD = "COMMENT__"
    COMMENT_RX_KEYWORD = "comment_rx__"
    WHITESPACE_KEYWORD = "WSP_RE__"
    RAW_WS_KEYWORD = "WHITESPACE__"
    WHITESPACE_PARSER_KEYWORD = "wsp__"
    DROP_WHITESPACE_PARSER_KEYWORD = "dwsp__"
    RESUME_RULES_KEYWORD = "resume_rules__"
    SKIP_RULES_SUFFIX = '_skip__'
    ERR_MSG_SUFFIX = '_err_msg__'
    RESERVED_SYMBOLS = {COMMENT_KEYWORD, COMMENT_RX_KEYWORD, WHITESPACE_KEYWORD, RAW_WS_KEYWORD,
                        WHITESPACE_PARSER_KEYWORD, DROP_WHITESPACE_PARSER_KEYWORD,
                        RESUME_RULES_KEYWORD}
    AST_ERROR = "Badly structured syntax tree. " \
                "Potentially due to erroneous AST transformation."
    PREFIX_TABLE = {'§': 'Required',
                    '&': 'Lookahead', '!': 'NegativeLookahead',
                    '-&': 'Lookbehind', '-!': 'NegativeLookbehind',
                    '::': 'Pop', ':': 'Retrieve'}
    REPEATABLE_DIRECTIVES = {'tokens'}


    def __init__(self, grammar_name="DSL", grammar_source=""):
        self.grammar_id = 0
        super(EBNFCompiler, self).__init__()  # calls the reset()-method
        self.set_grammar_name(grammar_name, grammar_source)


    def reset(self):
        super(EBNFCompiler, self).reset()
        self._result = ''           # type: str
        self.re_flags = set()       # type: Set[str]
        self.rules = OrderedDict()  # type: OrderedDict[str, List[Node]]
        self.current_symbols = []   # type: List[Node]
        self.symbols = {}           # type: Dict[str, Node]
        self.variables = set()      # type: Set[str]
        self.recursive = set()      # type: Set[str]
        self.definitions = {}       # type: Dict[str, str]
        self.deferred_tasks = []    # type: List[Callable]
        self.root_symbol = ""       # type: str
        self.directives = EBNFDirectives()   # type: EBNFDirectives
        self.defined_directives = set()      # type: Set[str]
        self.consumed_custom_errors = set()  # type: Set[str]
        self.consumed_skip_rules = set()     # type: Set[str]
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
        # TODO: Support atomic grouping: https://stackoverflow.com/questions/13577372/do-python-regular-expressions-have-an-equivalent-to-rubys-atomic-grouping
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
            return unrepr("re.compile(r'%s')" % self._extract_regex(nd))
        elif nd.tag_name == 'literal':
            s = nd.content.strip()
            return s.strip('"') if s[0] == '"' else s.strip("'")
        return ''

    def _gen_search_list(self, nodes: Sequence[Node]) -> List[Union[unrepr, str]]:
        search_list = []  # type: List[Union[unrepr, str]]
        for child in nodes:
            rule = self._gen_search_rule(child)
            search_list.append(rule if rule else unrepr(child.content.strip()))
        return search_list


    def assemble_parser(self, definitions: List[Tuple[str, str]], root_node: Node) -> str:
        """
        Creates the Python code for the parser after compilation of
        the EBNF-Grammar
        """

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

        if DROP_WSPC in self.directives.drop:
            definitions.append((self.DROP_WHITESPACE_PARSER_KEYWORD,
                                'DropWhitespace(%s)' % self.WHITESPACE_KEYWORD))
        else:
            definitions.append((self.WHITESPACE_PARSER_KEYWORD,
                                'Whitespace(%s)' % self.WHITESPACE_KEYWORD))
        definitions.append((self.WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace=" + self.RAW_WS_KEYWORD
                             + ", comment=" + self.COMMENT_KEYWORD + ")")))
        definitions.append((self.RAW_WS_KEYWORD, "r'{}'".format(self.directives.whitespace)))
        comment_rx = "re.compile(COMMENT__)" if self.directives.comment else "RX_NEVER_MATCH"
        definitions.append((self.COMMENT_RX_KEYWORD, comment_rx))
        definitions.append((self.COMMENT_KEYWORD, "r'{}'".format(self.directives.comment)))

        # prepare and add resume-rules

        resume_rules = dict()  # type: Dict[str, List[ReprType]]
        for symbol, raw_rules in self.directives.resume.items():
            refined_rules = []
            for rule in raw_rules:
                if isinstance(rule, unrepr) and rule.s.isidentifier():
                    try:
                        nd = self.rules[rule.s][0].children[1]
                        refined = self._gen_search_rule(nd)
                    except IndexError:
                        refined = ""
                    if refined:
                        refined_rules.append(refined)
                    else:
                        self.tree.new_error(nd, 'Symbol "%s" cannot be used in resume rule, since'
                                                ' it represents neither literal nor regexp!')
                else:
                    refined_rules.append(rule)
            resume_rules[symbol] = refined_rules
        definitions.append((self.RESUME_RULES_KEYWORD, repr(resume_rules)))

        # prepare and add customized error-messages

        for symbol, err_msgs in self.directives.error.items():
            custom_errors = []  # type: List[Tuple[ReprType, ReprType]]
            for search, message in err_msgs:
                if isinstance(search, unrepr) and search.s.isidentifier():
                    try:
                        nd = self.rules[search.s][0].children[1]
                        search = self._gen_search_rule(nd)
                    except IndexError:
                        search = ''
                custom_errors.append((search, message))
            definitions.append((symbol + self.ERR_MSG_SUFFIX, repr(custom_errors)))

        for symbol in self.directives.error.keys():
            if symbol not in self.consumed_custom_errors:
                def_node = self.rules[symbol][0]
                self.tree.new_error(
                    def_node, 'Customized error message for symbol "{}" will never be used, '
                    'because the mandatory marker "§" appears nowhere in its definiendum!'
                    .format(symbol), Error.UNUSED_ERROR_HANDLING_WARNING)

        # prepare and add skip-rules

        for symbol, skip in self.directives.skip.items():
            skip_rules = []  # type: List[ReprType]
            for search in skip:
                if isinstance(search, unrepr) and search.s.isidentifier():
                    try:
                        nd = self.rules[search.s][0].children[1]
                        search = self._gen_search_rule(nd)
                    except IndexError:
                        search = ''
                skip_rules.append(search)
            definitions.append((symbol + self.SKIP_RULES_SUFFIX, repr(skip_rules)))

        for symbol in self.directives.error.keys():
            if symbol not in self.consumed_skip_rules:
                def_node = self.rules[symbol][0]
                self.tree.new_error(
                    def_node, '"Skip-rules" for symbol "{}" will never be used, '
                    'because the mandatory marker "§" appears nowhere in its definiendum!'
                    .format(symbol), Error.UNUSED_ERROR_HANDLING_WARNING)

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class

        article = 'an ' if self.grammar_name[0:1] in "AaEeIiOoUu" else 'a '  # what about 'hour', 'universe' etc.?
        show_source = get_config_value('add_grammar_source_to_parser_docstring')
        declarations = ['class ' + self.grammar_name
                        + 'Grammar(Grammar):',
                        'r"""Parser for ' + article + self.grammar_name
                        + ' source file'
                        + ('. Grammar:' if self.grammar_source and show_source else '.')]
        definitions.append(('parser_initialization__', '["upon instantiation"]'))
        definitions.append(('static_analysis_pending__', '[True]'))
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
                # root_node.error_flag = True

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


    ## compilation methods

    def on_syntax(self, node: Node) -> str:
        definitions = []  # type: List[Tuple[str, str]]

        # drop the wrapping sequence node
        if len(node.children) == 1 and node.children[0].is_anonymous():
            node = node.children[0]

        # compile definitions and directives and collect definitions
        for nd in node.children:
            if nd.tag_name == "definition":
                definitions.append(self.compile(nd))
            else:
                assert nd.tag_name == "directive", nd.as_sxpr()
                self.compile(nd)
            # node.error_flag = max(node.error_flag, nd.error_flag)
        self.definitions.update(definitions)

        grammar_python_src = self.assemble_parser(definitions, node)
        if get_config_value('static_analysis') == 'early':
            try:
                grammar_class = compile_python_object(DHPARSER_IMPORTS + grammar_python_src,
                                                      self.grammar_name)
                _ = grammar_class()
                grammar_python_src = grammar_python_src.replace(
                    'static_analysis_pending__ = [True]', 'static_analysis_pending__ = []', 1)
            except NameError:
                pass  # undefined name in the grammar are already caught and reported
            except GrammarError as error:
                for sym, prs, err in error.errors:
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
        elif rule in EBNFCompiler.RESERVED_SYMBOLS:
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
            defn = self.compile(node.children[1])
            if rule in self.variables:
                defn = 'Capture(%s)' % defn
                self.variables.remove(rule)
            elif defn.find("(") < 0:
                # assume it's a synonym, like 'page = REGEX_PAGE_NR'
                defn = 'Synonym(%s)' % defn
        except TypeError as error:
            from traceback import extract_tb
            trace = str(extract_tb(error.__traceback__)[-1])
            errmsg = "%s (TypeError: %s; %s)\n%s" \
                     % (EBNFCompiler.AST_ERROR, str(error), trace, node.as_sxpr())
            self.tree.new_error(node, errmsg)
            rule, defn = rule + ':error', '"' + errmsg + '"'
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

        elif key == 'drop':
            check_argnum(2)
            for child in node.children[1:]:
                content = child.content
                node_type = content.lower()
                assert node_type in DROP_VALUES, content
                self.directives[key].add(node_type)

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
                else {} if 'none' in values else values
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
                                    + 'must be defined before the symbol!')
            if node.children[1 if len(node.children) == 2 else 2].tag_name != 'literal':
                self.tree.new_error(
                    node, 'Directive "%s" requires message string or a a pair ' % key +
                    '(regular expression or search string, message string) as argument!')
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

        try:
            if symbol not in self.symbols:
                # remember first use of symbol, so that dangling references or
                # redundant definitions or usages of symbols can be detected later
                self.symbols[symbol] = node
        except NameError:
            pass  # no symbol was referred to in directive

        return ""


    def non_terminal(self, node: Node, parser_class: str, custom_args: List[str] = []) -> str:
        """
        Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        arguments = [self.compile(r) for r in node.children] + custom_args
        return parser_class + '(' + ', '.join(arguments) + ')'


    def on_expression(self, node) -> str:
        # TODO: Add check for errors like "a" | "ab" (which will always yield a, even for ab)
        return self.non_terminal(node, 'Alternative')


    def _error_customization(self, node) -> Tuple[Tuple[Node, ...], List[str]]:
        mandatory_marker = []
        filtered_children = []  # type: List[Node]
        for nd in node.children:
            if nd.tag_name == TOKEN_PTYPE and nd.content == "§":
                mandatory_marker.append(len(filtered_children))
                if len(mandatory_marker) > 1:
                    self.tree.new_error(nd, 'One mandatory marker (§) sufficient to declare '
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
                        node, "Cannot apply customized error messages unambigiously, because "
                        "symbol {} contains more than one parser with a mandatory marker '§' "
                        "in its definiens.".format(current_symbol),
                        Error.AMBIGUOUS_ERROR_HANDLING)
                else:
                    # use class field instead or direct representation of error messages!
                    custom_args.append('err_msgs=' + current_symbol + self.ERR_MSG_SUFFIX)
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
                    custom_args.append('skip=' + current_symbol + self.SKIP_RULES_SUFFIX)
                    self.consumed_skip_rules.add(current_symbol)
        return tuple(filtered_children), custom_args


    def on_term(self, node) -> str:
        filtered_result, custom_args = self._error_customization(node)
        mock_node = Node(node.tag_name, filtered_result)
        return self.non_terminal(mock_node, 'Series', custom_args)


    def on_factor(self, node: Node) -> str:
        assert node.children
        assert len(node.children) >= 2, node.as_sxpr()
        prefix = node.children[0].content
        custom_args = []  # type: List[str]

        if prefix in {'::', ':'}:
            assert len(node.children) == 2
            arg = node.children[-1]
            if arg.tag_name != 'symbol':
                self.tree.new_error(node, ('Retrieve Operator "%s" requires a symbol, '
                                    'and not a %s.') % (prefix, arg.tag_name))
                return str(arg.result)
            if str(arg) in self.directives.filter:
                custom_args = ['rfilter=%s' % self.directives.filter[str(arg)]]
            self.variables.add(str(arg))  # cast(str, arg.result)

        elif len(node.children) > 2:
            # shift = (Node(node.parser, node.result[1].result),)
            # node.result[1].result = shift + node.result[2:]
            node.children[1].result = (Node(node.children[1].tag_name, node.children[1].result),) \
                + node.children[2:]
            node.children[1].tag_name = node.tag_name
            node.result = (node.children[0], node.children[1])

        node.result = node.children[1:]
        try:
            parser_class = self.PREFIX_TABLE[prefix]
            result = self.non_terminal(node, parser_class, custom_args)
            if prefix[:1] == '-':
                def check(node):
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
                    self.deferred_tasks.append(lambda: check(node))
            return result
        except KeyError:
            self.tree.new_error(node, 'Unknown prefix "%s".' % prefix)
        return ""


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
        if nd.tag_name == "term":
            filtered_result, custom_args = self._error_customization(nd)
            mock_node = Node(nd.tag_name, filtered_result)
            return self.non_terminal(mock_node, 'AllOf', custom_args)
        elif nd.tag_name == "expression":
            if any(c.tag_name == TOKEN_PTYPE and nd.content == '§' for c in nd.children):
                self.tree.new_error(node, "No mandatory items § allowed in SomeOf-operator!")
            args = ', '.join(self.compile(child) for child in nd.children)
            return "SomeOf(" + args + ")"
        else:
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
            if symbol in EBNFCompiler.RESERVED_SYMBOLS:
                # (EBNFCompiler.WHITESPACE_KEYWORD, EBNFCompiler.COMMENT_KEYWORD):
                return "RegExp(%s)" % symbol
            return symbol


    def TOKEN_PARSER(self):
        if DROP_TOKEN in self.directives.drop and self.context[-2].tag_name != "definition":
            return 'DropToken('
        return 'Token('


    def WSPC_PARSER(self):
        if DROP_WSPC in self.directives.drop and (self.context[-2].tag_name != "definition"
                                                  or self.context[-1].tag_name == 'literal'):
            return 'dwsp__'
        return 'wsp__'

    def on_literal(self, node: Node) -> str:
        center = self.TOKEN_PARSER() + node.content.replace('\\', r'\\') + ')'
        left = self.WSPC_PARSER() if 'left' in self.directives.literalws else ''
        right = self.WSPC_PARSER() if 'right' in self.directives.literalws else ''
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
        return self.TOKEN_PARSER() + tk + ')'


    def on_regexp(self, node: Node) -> str:
        rx = node.content
        name = []   # type: List[str]
        assert rx[0] == '/' and rx[-1] == '/'
        parser = 'RegExp('
        try:
            arg = repr(self._check_rx(node, rx[1:-1].replace(r'\/', '/')))
        except AttributeError as error:
            from traceback import extract_tb
            trace = str(extract_tb(error.__traceback__)[-1])
            errmsg = "%s (AttributeError: %s; %s)\n%s" \
                     % (EBNFCompiler.AST_ERROR, str(error), trace, node.as_sxpr())
            self.tree.new_error(node, errmsg)
            return '"' + errmsg + '"'
        return parser + ', '.join([arg] + name) + ')'


    def on_whitespace(self, node: Node) -> str:
        return self.WSPC_PARSER()

def get_ebnf_compiler(grammar_name="", grammar_source="") -> EBNFCompiler:
    try:
        compiler = THREAD_LOCALS.ebnf_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except AttributeError:
        compiler = EBNFCompiler(grammar_name, grammar_source)
        compiler.set_grammar_name(grammar_name, grammar_source)
        THREAD_LOCALS.ebnf_compiler_singleton = compiler
        return compiler


########################################################################
#
# EBNF compiler
#
########################################################################

def compile_ebnf(ebnf_source: str, branding: str = 'DSL') \
        -> Tuple[Optional[Any], List[Error], Optional[Node]]:
    """
    Compiles an `ebnf_source` (file_name or EBNF-string) and returns
    a tuple of the python code of the compiler, a list of warnings or errors
    and the abstract syntax tree of the EBNF-source.
    This function is merely syntactic sugar.
    """
    return compile_source(ebnf_source,
                          get_ebnf_preprocessor(),
                          get_ebnf_grammar(),
                          get_ebnf_transformer(),
                          get_ebnf_compiler(branding, ebnf_source))

