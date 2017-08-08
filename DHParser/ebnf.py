"""ebnf.py - EBNF -> Python-Parser compilation for DHParser

Copyright 2016  by Eckhart Arnold (arnold@badw.de)
                Bavarian Academy of Sciences an Humanities (badw.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
implied.  See the License for the specific language governing
permissions and limitations under the License.
"""

import keyword
from collections import OrderedDict

try:
    import regex as re
except ImportError:
    import re
try:
    from typing import Callable, Dict, List, Set, Tuple
except ImportError:
    from .typing34 import Callable, Dict, List, Set, Tuple

from DHParser.toolkit import load_if_file, escape_re, md5, sane_parser_name
from DHParser.parser import Grammar, mixin_comment, nil_preprocessor, Forward, RE, NegativeLookahead, \
    Alternative, Series, Optional, Required, OneOrMore, ZeroOrMore, Token, Compiler, \
    PreprocessorFunc
from DHParser.syntaxtree import WHITESPACE_PTYPE, TOKEN_PTYPE, Node, TransformationFunc
from DHParser.transform import traverse, remove_brackets, \
    reduce_single_child, replace_by_single_child, remove_expendables, \
    remove_tokens, flatten, forbid, assert_content, key_tag_name, remove_infix_operator
from DHParser.versionnumber import __version__

__all__ = ('get_ebnf_preprocessor',
           'get_ebnf_grammar',
           'get_ebnf_transformer',
           'get_ebnf_compiler',
           'EBNFGrammar',
           'EBNFTransformer',
           'EBNFCompilerError',
           'EBNFCompiler',
           'grammar_changed',
           'PreprocessorFactoryFunc',
           'ParserFactoryFunc',
           'TransformerFactoryFunc',
           'CompilerFactoryFunc')


########################################################################
#
# EBNF scanning
#
########################################################################


def get_ebnf_preprocessor() -> PreprocessorFunc:
    return nil_preprocessor


########################################################################
#
# EBNF parsing
#
########################################################################


class EBNFGrammar(Grammar):
    r"""Parser for an EBNF source file, with this grammar:

    # EBNF-Grammar in EBNF

    @ comment    =  /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
    @ whitespace =  /\s*/                            # whitespace includes linefeed
    @ literalws  =  right                            # trailing whitespace of literals will be ignored tacitly

    syntax     =  [~//] { definition | directive } §EOF
    definition =  symbol §"=" expression
    directive  =  "@" §symbol §"=" ( regexp | literal | list_ )

    expression =  term { "|" term }
    term       =  { factor }+
    factor     =  [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
                | [flowmarker] literal
                | [flowmarker] regexp
                | [flowmarker] group
                | [flowmarker] oneormore
                | repetition
                | option

    flowmarker =  "!"  | "&"  | "§" |                # '!' negative lookahead, '&' positive lookahead, '§' required
                  "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
    retrieveop =  "::" | ":"                         # '::' pop, ':' retrieve

    group      =  "(" expression §")"
    oneormore  =  "{" expression "}+"
    repetition =  "{" expression §"}"
    option     =  "[" expression §"]"

    symbol     =  /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
    literal    =  /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
                | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
    regexp     =  /~?\/(?:[^\/]|(?<=\\)\/)*\/~?/~    # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                     # '~' is a whitespace-marker, if present leading or trailing
                                                     # whitespace of a regular expression will be ignored tacitly.
    list_      =  /\w+/~ { "," /\w+/~ }              # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                     # BEGIN_QUOTE, END_QUOTE ; see CommonMark/markdown.py for an exmaple
    EOF =  !/./
    """
    expression = Forward()
    source_hash__ = "a410e1727fb7575e98ff8451dbf8f3bd"
    parser_initialization__ = "upon instantiation"
    COMMENT__ = r'#.*(?:\n|$)'
    WSP__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    wspL__ = ''
    wspR__ = WSP__
    EOF = NegativeLookahead(RE('.', wR=''))
    list_ = Series(RE('\\w+'), ZeroOrMore(Series(Token(","), RE('\\w+'))))
    regexp = RE(r'~?/(?:\\/|[^/])*?/~?')  # RE('~?/(?:[^/]|(?<=\\\\)/)*/~?')
    literal = Alternative(RE('"(?:[^"]|\\\\")*?"'), RE("'(?:[^']|\\\\')*?'"))
    symbol = RE('(?!\\d)\\w+')
    option = Series(Token("["), expression, Required(Token("]")))
    repetition = Series(Token("{"), expression, Required(Token("}")))
    oneormore = Series(Token("{"), expression, Token("}+"))
    group = Series(Token("("), expression, Required(Token(")")))
    retrieveop = Alternative(Token("::"), Token(":"))
    flowmarker = Alternative(Token("!"), Token("&"), Token("§"), Token("-!"), Token("-&"))
    factor = Alternative(Series(Optional(flowmarker), Optional(retrieveop), symbol, NegativeLookahead(Token("="))),
                         Series(Optional(flowmarker), literal), Series(Optional(flowmarker), regexp),
                         Series(Optional(flowmarker), group), Series(Optional(flowmarker), oneormore),
                         repetition, option)
    term = OneOrMore(factor)
    expression.set(Series(term, ZeroOrMore(Series(Token("|"), term))))
    directive = Series(Token("@"), Required(symbol), Required(Token("=")), Alternative(regexp, literal, list_))
    definition = Series(symbol, Required(Token("=")), expression)
    syntax = Series(Optional(RE('', wR='', wL=WSP__)), ZeroOrMore(Alternative(definition, directive)), Required(EOF))
    root__ = syntax


def grammar_changed(grammar_class, grammar_source: str) -> bool:
    """Returns ``True`` if ``grammar_class`` does not reflect the latest
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
        m = re.search('class \w*\(Grammar\)', pycode)
        if m:
            m = re.search('    source_hash__ *= *"([a-z0-9]*)"',
                          pycode[m.span()[1]:])
            return not (m and m.groups() and m.groups()[-1] == chksum)
        else:
            return True
    else:
        return chksum != grammar_class.source_hash__


def get_ebnf_grammar() -> EBNFGrammar:
    global thread_local_ebnf_grammar_singleton
    try:
        grammar = thread_local_ebnf_grammar_singleton
        return grammar
    except NameError:
        thread_local_ebnf_grammar_singleton = EBNFGrammar()
        return thread_local_ebnf_grammar_singleton


########################################################################
#
# EBNF concrete to abstract syntax tree transformation and validation
#
########################################################################


EBNF_transformation_table = {
    # AST Transformations for EBNF-grammar
    "+":
        remove_expendables,
    "syntax":
        [],  # otherwise '"*": replace_by_single_child' would be applied
    "directive, definition":
        remove_tokens('@', '='),
    "expression":
        [replace_by_single_child, flatten, remove_tokens('|')],  # remove_infix_operator],
    "term":
        [replace_by_single_child, flatten],  # supports both idioms:  "{ factor }+" and "factor { factor }"
    "factor, flowmarker, retrieveop":
        replace_by_single_child,
    "group":
        [remove_brackets, replace_by_single_child],
    "oneormore, repetition, option":
        [reduce_single_child, remove_brackets,
         forbid('repetition', 'option', 'oneormore'), assert_content(r'(?!§)')],
    "symbol, literal, regexp":
        reduce_single_child,
    (TOKEN_PTYPE, WHITESPACE_PTYPE):
        reduce_single_child,
    "list_":
        [flatten, remove_infix_operator],
    "*":
        replace_by_single_child
}


def EBNFTransformer(syntax_tree: Node):
    traverse(syntax_tree, EBNF_transformation_table, key_tag_name)


def get_ebnf_transformer() -> TransformationFunc:
    return EBNFTransformer


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
    global thread_local_{NAME}_grammar_singleton
    try:
        grammar = thread_local_{NAME}_grammar_singleton
        return grammar
    except NameError:
        thread_local_{NAME}_grammar_singleton = {NAME}Grammar()
        return thread_local_{NAME}_grammar_singleton
'''


TRANSFORMER_FACTORY = '''
def get_transformer() -> TransformationFunc:
    return {NAME}Transform
'''


COMPILER_FACTORY = '''
def get_compiler(grammar_name="{NAME}", grammar_source="") -> {NAME}Compiler:
    global thread_local_{NAME}_compiler_singleton
    try:
        compiler = thread_local_{NAME}_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except NameError:
        thread_local_{NAME}_compiler_singleton = \\
            {NAME}Compiler(grammar_name, grammar_source)
        return thread_local_{NAME}_compiler_singleton 
'''


class EBNFCompilerError(Exception):
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

    Addionally, class EBNFCompiler provides helper methods to generate
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

                Now `[str(node) for node in self.rules['alternative']]`
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

        deferred_taks:  A list of callables that is filled during
                compilatation, but that will be executed only after
                compilation has finished. Typically, it contains
                sementatic checks that require information that
                is only available upon completion of compilation.

        root:   The name of the root symbol.

        directives:  A dictionary of all directives and their default
                values.
    """
    COMMENT_KEYWORD = "COMMENT__"
    WHITESPACE_KEYWORD = "WSP__"
    RESERVED_SYMBOLS = {WHITESPACE_KEYWORD, COMMENT_KEYWORD}
    AST_ERROR = "Badly structured syntax tree. " \
                "Potentially due to erroneuos AST transformation."
    PREFIX_TABLE = {'§': 'Required',
                    '&': 'Lookahead', '!': 'NegativeLookahead',
                    '-&': 'Lookbehind', '-!': 'NegativeLookbehind',
                    '::': 'Pop', ':': 'Retrieve'}
    WHITESPACE = {'horizontal': r'[\t ]*',  # default: horizontal
                  'linefeed': r'[ \t]*\n?(?!\s*\n)[ \t]*',
                  'vertical': r'\s*'}


    def __init__(self, grammar_name="", grammar_source=""):
        super(EBNFCompiler, self).__init__(grammar_name, grammar_source)
        self._reset()


    def _reset(self):
        super(EBNFCompiler, self)._reset()
        self._result = ''           # type: str
        self.rules = OrderedDict()  # type: OrderedDict[str, List[Node]]
        self.current_symbols = []   # type: List[Node]
        self.symbols = {}           # type: Dict[str, Node]
        self.variables = set()      # type: Set[str]
        self.recursive = set()      # type: Set[str]
        self.definitions = {}       # type: Dict[str, str]
        self.deferred_tasks = []    # type: List[Callable]
        self.root_symbol = ""  # type: str
        self.directives = {'whitespace': self.WHITESPACE['horizontal'],
                           'comment': '',
                           'literalws': ['right'],
                           'tokens': set(),  # alt. 'preprocessor_tokens'
                           'filter': dict(),  # alt. 'filter'
                           'testing': False}

    @property
    def result(self) -> str:
        return self._result

    # methods for generating skeleton code for preprocessor, transformer, and compiler

    def gen_preprocessor_skeleton(self) -> str:
        """
        Returns Python-skeleton-code for a preprocessor-function for
        the previously compiled formal language.
        """
        name = self.grammar_name + "Preprocessor"
        return "def %s(text):\n    return text\n" % name \
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
        tf_name = self.grammar_name + 'Transform'
        transtable = [tt_name + ' = {',
                      '    # AST Transformations for the ' +
                      self.grammar_name + '-grammar']
        transtable.append('    "+": remove_empty,')
        for name in self.rules:
            tf = '[]'
            rule = self.definitions[name]
            if rule.startswith('Alternative'):
                tf = '[replace_or_reduce]'
            elif rule.startswith('Synonym'):
                tf = '[replace_by_single_child]'
            transtable.append('    "' + name + '": %s,' % tf)
        transtable.append('    ":Token, :RE": reduce_single_child,')
        transtable += ['    "*": replace_by_single_child', '}', '', tf_name +
                       ' = partial(traverse, processing_table=%s)' % tt_name, '']
        transtable += [TRANSFORMER_FACTORY.format(NAME=self.grammar_name)]
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
                    '    """Compiler for the abstract-syntax-tree of a ' +
                    self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self, grammar_name="' +
                    self.grammar_name + '", grammar_source=""):',
                    '        super(' + self.grammar_name +
                    'Compiler, self).__init__(grammar_name, grammar_source)',
                    "        assert re.match('\w+\Z', grammar_name)", '']
        for name in self.rules:
            method_name = Compiler.method_name(name)
            if name == self.root_symbol:
                compiler += ['    def ' + method_name + '(self, node):',
                             '        return node', '']
            else:
                compiler += ['    def ' + method_name + '(self, node):',
                             '        pass', '']
        compiler += [COMPILER_FACTORY.format(NAME=self.grammar_name)]
        return '\n'.join(compiler)


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
        # value of will be retrieved at some point during the parsing process

        if self.variables:
            for i in range(len(definitions)):
                if definitions[i][0] in self.variables:
                    definitions[i] = (definitions[i][0], 'Capture(%s)' % definitions[i][1])

        # add special fields for Grammar class

        definitions.append(('wspR__', self.WHITESPACE_KEYWORD
                            if 'right' in self.directives['literalws'] else "''"))
        definitions.append(('wspL__', self.WHITESPACE_KEYWORD
                            if 'left' in self.directives['literalws'] else "''"))
        definitions.append((self.WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace="
                             "r'{whitespace}', comment=r'{comment}')").
                            format(**self.directives)))
        definitions.append((self.COMMENT_KEYWORD, "r'{comment}'".format(**self.directives)))

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class

        article = 'an ' if self.grammar_name[0:1] in "AaEeIiOoUu" else 'a '  # what about 'hour', 'universe' etc.?
        declarations = ['class ' + self.grammar_name +
                        'Grammar(Grammar):',
                        'r"""Parser for ' + article + self.grammar_name +
                        ' source file' +
                        (', with this grammar:' if self.grammar_source else '.')]
        definitions.append(('parser_initialization__', '"upon instantiation"'))
        if self.grammar_source:
            definitions.append(('source_hash__',
                                '"%s"' % md5(self.grammar_source, __version__)))
            declarations.append('')
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
                self.symbols[symbol].add_error("Missing definition for symbol '%s'" % symbol)
                # root_node.error_flag = True

        # check for unconnected rules

        if not self.directives['testing']:
            defined_symbols.difference_update(self.RESERVED_SYMBOLS)

            def remove_connections(symbol):
                if symbol in defined_symbols:
                    defined_symbols.remove(symbol)
                    for related in self.rules[symbol][1:]:
                        remove_connections(str(related))

            remove_connections(self.root_symbol)
            for leftover in defined_symbols:
                self.rules[leftover][0].add_error(('Rule "%s" is not connected to parser '
                                                   'root "%s" !') % (leftover,
                                                                     self.root_symbol) + ' (Use directive "@testing=True" '
                    'to supress this error message.)')
                # root_node.error_flag = True

        # set root_symbol parser and assemble python grammar definition

        if self.root_symbol and 'root__' not in self.rules:
            declarations.append('root__ = ' + self.root_symbol)
        declarations.append('')
        self._result = '\n    '.join(declarations) \
                       + GRAMMAR_FACTORY.format(NAME=self.grammar_name)
        return self._result


    ## compilation methods

    def on_syntax(self, node: Node) -> str:
        definitions = []  # type: List[Tuple[str, str]]

        # drop the wrapping sequence node
        if len(node.children) == 1 and not node.children[0].parser.name:
            node = node.children[0]

        # compile definitions and directives and collect definitions
        for nd in node.children:
            if nd.parser.name == "definition":
                definitions.append(self.compile(nd))
            else:
                assert nd.parser.name == "directive", nd.as_sxpr()
                self.compile(nd)
                node.error_flag = node.error_flag or nd.error_flag
        self.definitions.update(definitions)

        return self.assemble_parser(definitions, node)


    def on_definition(self, node: Node) -> Tuple[str, str]:
        rule = str(node.children[0])
        if rule in self.rules:
            node.add_error('A rule with name "%s" has already been defined.' % rule)
        elif rule in EBNFCompiler.RESERVED_SYMBOLS:
            node.add_error('Symbol "%s" is a reserved symbol.' % rule)
        elif not sane_parser_name(rule):
            node.add_error('Illegal symbol "%s". Symbols must not start or '
                           ' end with a doube underscore "__".' % rule)
        elif rule in self.directives['tokens']:
            node.add_error('Symbol "%s" has already been defined as '
                           'a preprocessor token.' % rule)
        elif keyword.iskeyword(rule):
            node.add_error('Python keyword "%s" may not be used as a symbol. '
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
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + node.as_sxpr()
            node.add_error(errmsg)
            rule, defn = rule + ':error', '"' + errmsg + '"'
        return rule, defn


    @staticmethod
    def _check_rx(node: Node, rx: str) -> str:
        """
        Checks whether the string `rx` represents a valid regular
        expression. Makes sure that multiline regular expressions are
        prepended by the multiline-flag. Returns the regular expression string.
        """
        rx = rx if rx.find('\n') < 0 or rx[0:4] == '(?x)' else '(?x)' + rx
        try:
            re.compile(rx)
        except Exception as re_error:
            node.add_error("malformed regular expression %s: %s" %
                           (repr(rx), str(re_error)))
        return rx


    def on_directive(self, node: Node) -> str:
        key = str(node.children[0]).lower()
        assert key not in self.directives['tokens']

        if key in {'comment', 'whitespace'}:
            if node.children[1].parser.name == "list_":
                if len(node.children[1].result) != 1:
                    node.add_error('Directive "%s" must have one, but not %i values.' %
                                   (key, len(node.children[1].result)))
                value = self.compile(node.children[1]).pop()
                if key == 'whitespace' and value in EBNFCompiler.WHITESPACE:
                    value = EBNFCompiler.WHITESPACE[value]  # replace whitespace-name by regex
                else:
                    node.add_error('Value "%s" not allowed for directive "%s".' % (value, key))
            else:
                value = str(node.children[1]).strip("~")  # cast(str, node.children[1].result).strip("~")
                if value != str(node.children[1]):  # cast(str, node.children[1].result):
                    node.add_error("Whitespace marker '~' not allowed in definition of "
                                   "%s regular expression." % key)
                if value[0] + value[-1] in {'""', "''"}:
                    value = escape_re(value[1:-1])
                elif value[0] + value[-1] == '//':
                    value = self._check_rx(node, value[1:-1])
                if key == 'whitespace' and not re.match(value, ''):
                    node.add_error("Implicit whitespace should always match the empty string, "
                                   "/%s/ does not." % value)
            self.directives[key] = value

        elif key == 'testing':
            value = str(node.children[1])
            self.directives['testing'] = value.lower() not in {"off", "false", "no"}

        elif key == 'literalws':
            value = {item.lower() for item in self.compile(node.children[1])}
            if (len(value - {'left', 'right', 'both', 'none'}) > 0
                    or ('none' in value and len(value) > 1)):
                node.add_error('Directive "literalws" allows the values '
                               '`left`, `right`, `both` or `none`, '
                               'but not `%s`' % ", ".join(value))
            ws = {'left', 'right'} if 'both' in value \
                else {} if 'none' in value else value
            self.directives[key] = list(ws)

        elif key in {'tokens', 'preprocessor_tokens'}:
            self.directives['tokens'] |= self.compile(node.children[1])

        elif key.endswith('_filter'):
            filter_set = self.compile(node.children[1])
            if not isinstance(filter_set, set) or len(filter_set) != 1:
                node.add_error('Directive "%s" accepts exactly on symbol, not %s'
                               % (key, str(filter_set)))
            self.directives['filter'][key[:-7]] = filter_set.pop()

        else:
            node.add_error('Unknown directive %s ! (Known ones are %s .)' %
                           (key,
                            ', '.join(list(self.directives.keys()))))
        return ""


    def non_terminal(self, node: Node, parser_class: str, custom_args: List[str]=[]) -> str:
        """
        Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        arguments = [self.compile(r) for r in node.children] + custom_args
        return parser_class + '(' + ', '.join(arguments) + ')'


    def on_expression(self, node) -> str:
        return self.non_terminal(node, 'Alternative')


    def on_term(self, node) -> str:
        return self.non_terminal(node, 'Series')


    def on_factor(self, node: Node) -> str:
        assert node.children
        assert len(node.children) >= 2, node.as_sxpr()
        prefix = str(node.children[0])  # cast(str, node.children[0].result)
        custom_args = []  # type: List[str]

        if prefix in {'::', ':'}:
            assert len(node.children) == 2
            arg = node.children[-1]
            if arg.parser.name != 'symbol':
                node.add_error(('Retrieve Operator "%s" requires a symbol, '
                                'and not a %s.') % (prefix, str(arg.parser)))
                return str(arg.result)
            if str(arg) in self.directives['filter']:
                custom_args = ['filter=%s' % self.directives['filter'][str(arg)]]
            self.variables.add(str(arg))  # cast(str, arg.result)

        elif len(node.children) > 2:
            # shift = (Node(node.parser, node.result[1].result),)
            # node.result[1].result = shift + node.result[2:]
            node.children[1].result = (Node(node.children[1].parser, node.children[1].result),) \
                                    + node.children[2:]
            node.children[1].parser = node.parser
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
                    while nd.parser.name == "symbol":
                        symlist = self.rules.get(str(nd), [])
                        if len(symlist) == 2:
                            nd = symlist[1]
                        else:
                            if len(symlist) == 1:
                                nd = symlist[0].children[1]
                            break
                    if (nd.parser.name != "regexp" or str(nd)[:1] != '/'
                        or str(nd)[-1:] != '/'):
                        node.add_error("Lookbehind-parser can only be used with plain RegExp-"
                                       "parsers, not with: " + nd.parser.name + nd.parser.ptype)

                if not result.startswith('RegExp('):
                    self.deferred_tasks.append(lambda: check(node))
            return result
        except KeyError:
            node.add_error('Unknown prefix "%s".' % prefix)
        return ""


    def on_option(self, node) -> str:
        return self.non_terminal(node, 'Optional')


    def on_repetition(self, node) -> str:
        return self.non_terminal(node, 'ZeroOrMore')


    def on_oneormore(self, node) -> str:
        return self.non_terminal(node, 'OneOrMore')


    def on_regexchain(self, node) -> str:
        raise EBNFCompilerError("Not yet implemented!")


    def on_group(self, node) -> str:
        raise EBNFCompilerError("Group nodes should have been eliminated by "
                                "AST transformation!")


    def on_symbol(self, node: Node) -> str:     # called only for symbols on the right hand side!
        symbol = str(node)  # ; assert result == cast(str, node.result)
        if symbol in self.directives['tokens']:
            return 'PreprocessorToken("' + symbol + '")'
        else:
            self.current_symbols.append(node)
            if symbol not in self.symbols:
                self.symbols[symbol] = node  # remember first use of symbol
            if symbol in self.rules:
                self.recursive.add(symbol)
            if symbol in (EBNFCompiler.WHITESPACE_KEYWORD, EBNFCompiler.COMMENT_KEYWORD):
                return "RegExp(%s)" % symbol
            return symbol


    def on_literal(self, node) -> str:
        return 'Token(' + str(node).replace('\\', r'\\') + ')'  # return 'Token(' + ', '.merge_children([node.result]) + ')' ?


    def on_regexp(self, node: Node) -> str:
        rx = str(node)
        name = []   # type: List[str]
        if rx[0] == '/' and rx[-1] == '/':
            parser = 'RegExp('
        else:
            parser = 'RE('
            if rx[:2] == '~/':
                if not 'left' in self.directives['literalws']:
                    name = ['wL=' + self.WHITESPACE_KEYWORD] + name
                rx = rx[1:]
            elif 'left' in self.directives['literalws']:
                name = ["wL=''"] + name
            if rx[-2:] == '/~':
                if 'right' not in self.directives['literalws']:
                    name = ['wR=' + self.WHITESPACE_KEYWORD] + name
                rx = rx[:-1]
            elif 'right' in self.directives['literalws']:
                name = ["wR=''"] + name
        try:
            arg = repr(self._check_rx(node, rx[1:-1].replace(r'\/', '/')))
        except AttributeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + \
                     node.as_sxpr()
            node.add_error(errmsg)
            return '"' + errmsg + '"'
        return parser + ', '.join([arg] + name) + ')'


    def on_list_(self, node) -> Set[str]:
        assert node.children
        return set(item.result.strip() for item in node.children)


def get_ebnf_compiler(grammar_name="", grammar_source="") -> EBNFCompiler:
    global thread_local_ebnf_compiler_singleton
    try:
        compiler = thread_local_ebnf_compiler_singleton
        compiler.set_grammar_name(grammar_name, grammar_source)
        return compiler
    except NameError:
        thread_local_ebnf_compiler_singleton = EBNFCompiler(grammar_name, grammar_source)
        return thread_local_ebnf_compiler_singleton
