#!/usr/bin/python3

"""EBNFcompiler.py - EBNF -> Python-Parser compilation for DHParser

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

# import collections
import keyword
from functools import partial
try:
    import regex as re
except ImportError:
    import re

from .__init__ import __version__
from .toolkit import load_if_file, escape_re, md5, sane_parser_name
from .parsercombinators import GrammarBase, mixin_comment, Forward, RE, NegativeLookahead, \
    Alternative, Sequence, Optional, Required, OneOrMore, ZeroOrMore, Token, CompilerBase
from .syntaxtree import Node, remove_enclosing_delimiters, reduce_single_child, \
    replace_by_single_child, TOKEN_KEYWORD, remove_expendables, remove_tokens, flatten, \
    WHITESPACE_KEYWORD


__all__ = ['EBNFGrammar',
           'EBNFTransTable',
           'EBNFCompilerError',
           # 'Scanner',
           'EBNFCompiler']


class EBNFGrammar(GrammarBase):
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
    option     =  "[" expression §"]"
    oneormore  =  "{" expression "}+"
    repetition =  "{" expression §"}"

    symbol     =  /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
    literal    =  /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
                | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
    regexp     =  /~?\/(?:[^\/]|(?<=\\)\/)*\/~?/~    # e.g. /\w+/, ~/#.*(?:\n|$)/~
                                                     # '~' is a whitespace-marker, if present leading or trailing
                                                     # whitespace of a regular expression will be ignored tacitly.
    list_      =  /\w+\s*(?:,\s*\w+\s*)*/~           # comma separated list of symbols, e.g. BEGIN_LIST, END_LIST,
                                                     # BEGIN_QUOTE, END_QUOTE ; see CommonMark/markdown.py for an exmaple
    EOF =  !/./
    """
    expression = Forward()
    source_hash__ = "1065c2e43262a5cb3aa438ec4d347c32"
    parser_initialization__ = "upon instatiation"
    wsp__ = mixin_comment(whitespace=r'\s*', comment=r'#.*(?:\n|$)')
    wspL__ = ''
    wspR__ = wsp__
    EOF = NegativeLookahead(RE('.', wR=''))
    list_ = RE('\\w+\\s*(?:,\\s*\\w+\\s*)*')
    regexp = RE('~?/(?:[^/]|(?<=\\\\)/)*/~?')
    literal = Alternative(RE('"(?:[^"]|\\\\")*?"'), RE("'(?:[^']|\\\\')*?'"))
    symbol = RE('(?!\\d)\\w+')
    repetition = Sequence(Token("{"), expression, Required(Token("}")))
    oneormore = Sequence(Token("{"), expression, Token("}+"))
    option = Sequence(Token("["), expression, Required(Token("]")))
    group = Sequence(Token("("), expression, Required(Token(")")))
    retrieveop = Alternative(Token("::"), Token(":"))
    flowmarker = Alternative(Token("!"), Token("&"), Token("§"), Token("-!"), Token("-&"))
    factor = Alternative(Sequence(Optional(flowmarker), Optional(retrieveop), symbol, NegativeLookahead(Token("="))),
                         Sequence(Optional(flowmarker), literal), Sequence(Optional(flowmarker), regexp),
                         Sequence(Optional(flowmarker), group), Sequence(Optional(flowmarker), oneormore), repetition,
                         option)
    term = OneOrMore(factor)
    expression.set(Sequence(term, ZeroOrMore(Sequence(Token("|"), term))))
    directive = Sequence(Token("@"), Required(symbol), Required(Token("=")), Alternative(regexp, literal, list_))
    definition = Sequence(symbol, Required(Token("=")), expression)
    syntax = Sequence(Optional(RE('', wR='', wL=wsp__)), ZeroOrMore(Alternative(definition, directive)), Required(EOF))
    root__ = syntax


EBNF_ASTTransform = {
    # AST Transformations for EBNF-grammar
    "syntax":
        remove_expendables,
    "directive, definition":
        partial(remove_tokens, tokens={'@', '='}),
    "expression, chain":
        [replace_by_single_child, flatten,
         partial(remove_tokens, tokens={'|', '--'})],
    "term":
        [replace_by_single_child, flatten],  # supports both idioms:  "{ factor }+" and "factor { factor }"
    "factor, flowmarker, retrieveop":
        replace_by_single_child,
    "group":
        [remove_enclosing_delimiters, replace_by_single_child],
    "oneormore, repetition, option, regexchain":
        [reduce_single_child, remove_enclosing_delimiters],
    "symbol, literal, regexp":
        [remove_expendables, reduce_single_child],
    (TOKEN_KEYWORD, WHITESPACE_KEYWORD):
        [remove_expendables, reduce_single_child],
    "list_":
        [partial(remove_tokens, tokens={','})],
    "":
        [remove_expendables, replace_by_single_child]
}


EBNF_ASTPipeline = [EBNF_ASTTransform]


class EBNFCompilerError(Exception):
    """Error raised by `EBNFCompiler` class. (Not compilation errors
    in the strict sense, see `CompilationError` below)"""
    pass


# Scanner = collections.namedtuple('Scanner',
#                                  'symbol instantiation_call cls_name cls')


class EBNFCompiler(CompilerBase):
    """Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.
    """
    COMMENT_KEYWORD = "COMMENT__"
    DEFAULT_WHITESPACE = r'[\t ]*'
    RESERVED_SYMBOLS = {TOKEN_KEYWORD, WHITESPACE_KEYWORD, COMMENT_KEYWORD}
    KNOWN_DIRECTIVES = {'comment', 'whitespace', 'tokens', 'literalws'}
    VOWELS = {'A', 'E', 'I', 'O', 'U'}  # what about cases like 'hour', 'universe' etc.?
    AST_ERROR = "Badly structured syntax tree. " \
                "Potentially due to erroneuos AST transformation."
    PREFIX_TABLE = [('§', 'Required'), ('&', 'Lookahead'),
                    ('!', 'NegativeLookahead'), ('-&', 'Lookbehind'),
                    ('-!', 'NegativeLookbehind'), ('::', 'Pop'),
                    (':', 'Retrieve')]

    def __init__(self, grammar_name="", source_text=""):
        super(EBNFCompiler, self).__init__()
        assert grammar_name == "" or re.match('\w+\Z', grammar_name)
        self.grammar_name = grammar_name
        self.source_text = load_if_file(source_text)
        self._reset()

    def _reset(self):
        self.rules = set()
        self.symbols = set()
        self.variables = set()
        self.scanner_tokens = set()
        self.definition_names = []
        self.recursive = set()
        self.root = ""
        self.directives = {'whitespace': self.DEFAULT_WHITESPACE,
                           'comment': '',
                           'literalws': ['right']}

    def gen_scanner_skeleton(self):
        name = self.grammar_name + "Scanner"
        return "def %s(text):\n    return text\n" % name

    def gen_AST_skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_AST_Skeleton()"!')
        tt_name = self.grammar_name + '_ASTTransform'
        pl_name = self.grammar_name + '_ASTPipeline'
        transtable = [tt_name + ' = {',
                      '    # AST Transformations for the ' +
                      self.grammar_name + '-grammar']
        for name in self.definition_names:
            transtable.append('    "' + name + '": no_operation,')
        transtable += ['    "": no_operation', '}', '',  pl_name + ' = [%s]' % tt_name, '']
        return '\n'.join(transtable)

    def gen_compiler_skeleton(self):
        if not self.definition_names:
            raise EBNFCompilerError('Compiler has not been run before calling '
                                    '"gen_Compiler_Skeleton()"!')
        compiler = ['class ' + self.grammar_name + 'Compiler(CompilerBase):',
                    '    """Compiler for the abstract-syntax-tree of a ' +
                    self.grammar_name + ' source file.',
                    '    """', '',
                    '    def __init__(self, grammar_name="' +
                    self.grammar_name + '"):',
                    '        super(' + self.grammar_name +
                    'Compiler, self).__init__()',
                    "        assert re.match('\w+\Z', grammar_name)", '']
        for name in self.definition_names:
            if name == self.root:
                compiler += ['    def ' + name + '(self, node):',
                             '        return node', '']
            else:
                compiler += ['    def ' + name + '(self, node):',
                             '        pass', '']
        return '\n'.join(compiler)

    def gen_parser(self, definitions):
        # fix capture of variables that have been defined before usage [sic!]
        if self.variables:
            for i in range(len(definitions)):
                if definitions[i][0] in self.variables:
                    definitions[i] = (definitions[i][0], 'Capture(%s, "%s")' %
                                      (definitions[1], definitions[0]))

        self.definition_names = [defn[0] for defn in definitions]
        definitions.append(('wspR__', WHITESPACE_KEYWORD
                            if 'right' in self.directives['literalws'] else "''"))
        definitions.append(('wspL__', WHITESPACE_KEYWORD
                            if 'left' in self.directives['literalws'] else "''"))
        definitions.append((WHITESPACE_KEYWORD,
                            ("mixin_comment(whitespace="
                             "r'{whitespace}', comment=r'{comment}')").
                            format(**self.directives)))
        definitions.append((self.COMMENT_KEYWORD, "r'{comment}'".format(**self.directives)))

        # prepare parser class header and docstring and
        # add EBNF grammar to the doc string of the parser class
        article = 'an ' if self.grammar_name[0:1].upper() \
                           in EBNFCompiler.VOWELS else 'a '
        declarations = ['class ' + self.grammar_name +
                        'Grammar(GrammarBase):',
                        'r"""Parser for ' + article + self.grammar_name +
                        ' source file' +
                        (', with this grammar:' if self.source_text else '.')]
        definitions.append(('parser_initialization__', '"upon instatiation"'))
        if self.source_text:
            definitions.append(('source_hash__',
                                '"%s"' % md5(self.source_text, __version__)))
            declarations.append('')
            declarations += [line for line in self.source_text.split('\n')]
            while declarations[-1].strip() == '':
                declarations = declarations[:-1]
        declarations.append('"""')

        # turn definitions into declarations in reverse order
        self.root = definitions[0][0] if definitions else ""
        definitions.reverse()
        declarations += [symbol + ' = Forward()'
                         for symbol in sorted(list(self.recursive))]
        for symbol, statement in definitions:
            if symbol in self.recursive:
                declarations += [symbol + '.set(' + statement + ')']
            else:
                declarations += [symbol + ' = ' + statement]
        for nd in self.symbols:
            if nd.result not in self.rules:
                nd.add_error("Missing production for symbol '%s'" % nd.result)
        if self.root and 'root__' not in self.symbols:
            declarations.append('root__ = ' + self.root)
        declarations.append('')
        return '\n    '.join(declarations)

    def syntax(self, node):
        self._reset()
        definitions = []

        # drop the wrapping sequence node
        if isinstance(node.parser, Sequence) and \
                isinstance(node.result[0].parser, ZeroOrMore):
            node = node.result[0]

        # compile definitions and directives and collect definitions
        for nd in node.result:
            if nd.parser.name == "definition":
                definitions.append(self.compile__(nd))
            else:
                assert nd.parser.name == "directive", nd.as_sexpr()
                self.compile__(nd)

        return self.gen_parser(definitions)

    def definition(self, node):
        rule = node.result[0].result
        if rule in EBNFCompiler.RESERVED_SYMBOLS:
            node.add_error('Symbol "%s" is a reserved symbol.' % rule)
        elif not sane_parser_name(rule):
            node.add_error('Illegal symbol "%s". Symbols must not start or '
                           ' end with a doube underscore "__".' % rule)
        elif rule in self.scanner_tokens:
            node.add_error('Symbol "%s" has already been defined as '
                           'a scanner token.' % rule)
        elif keyword.iskeyword(rule):
            node.add_error('Python keyword "%s" may not be used as a symbol. '
                           % rule + '(This may change in the furute.)')
        elif rule in self.rules:
            node.add_error('A rule with name "%s" has already been defined.' %
                           rule)
        try:
            self.rules.add(rule)
            defn = self.compile__(node.result[1])
            if rule in self.variables:
                defn = 'Capture(%s, "%s")' % (defn, rule)
                self.variables.remove(rule)
        except TypeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + node.as_sexpr()
            node.add_error(errmsg)
            rule, defn = rule + ':error', '"' + errmsg + '"'
        return rule, defn

    @staticmethod
    def _check_rx(node, rx):
        """Checks whether the string `rx` represents a valid regular
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

    def directive(self, node):
        key = node.result[0].result.lower()
        assert key not in self.scanner_tokens
        if key in {'comment', 'whitespace'}:
            if node.result[1].parser.name == "list_":
                if len(node.result[1].result) != 1:
                    node.add_error("Directive %s must have one, but not %i values" %
                                   (key, len(node.result[1])))
                value = self.compile__(node.result[1]).pop()
                if value in {'linefeed', 'standard'} and key == 'whitespace':
                    value = '\s*' if value == "linefeed" else self.DEFAULT_WHITESPACE
                else:
                    node.add_error('Value "%" not allowed for directive %s' % (value, key))
            else:
                value = node.result[1].result.strip("~")
                if value != node.result[1].result:
                    node.add_error("Whitespace marker '~' not allowed in definition of "
                                   "%s regular expression." % key)
                if value[0] + value[-1] in {'""', "''"}:
                    value = escape_re(value[1:-1])
                elif value[0] + value[-1] == '//':
                    value = self._check_rx(node, value[1:-1])
            self.directives[key] = value
        elif key == 'literalws':
            value = {item.lower() for item in self.compile__(node.result[1])}
            if (len(value - {'left', 'right', 'both', 'none'}) > 0
                    or ('none' in value and len(value) > 1)):
                node.add_error('Directive "literalws" allows the values '
                               '`left`, `right`, `both` or `none`, '
                               'but not `%s`' % ", ".join(value))
            ws = {'left', 'right'} if 'both' in value \
                else {} if 'none' in value else value
            self.directives[key] = list(ws)

        elif key == 'tokens':
            self.scanner_tokens |= self.compile__(node.result[1])
        else:
            node.add_error('Unknown directive %s ! (Known ones are %s .)' %
                           (key,
                            ', '.join(list(EBNFCompiler.KNOWN_DIRECTIVES))))
        return ""

    def non_terminal(self, node, parser_class):
        """Compiles any non-terminal, where `parser_class` indicates the Parser class
        name for the particular non-terminal.
        """
        arguments = filter(lambda arg: arg,
                           [self.compile__(r) for r in node.result])
        return parser_class + '(' + ', '.join(arguments) + ')'

    def expression(self, node):
        return self.non_terminal(node, 'Alternative')

    def term(self, node):
        return self.non_terminal(node, 'Sequence')

    def factor(self, node):
        assert isinstance(node.parser, Sequence), node.as_sexpr()  # these assert statements can be removed
        assert node.children
        assert len(node.result) >= 2, node.as_sexpr()
        prefix = node.result[0].result

        arg = node.result[-1]
        if prefix in {'::', ':'}:
            assert len(node.result) == 2
            if arg.parser.name != 'symbol':
                node.add_error(('Retrieve Operator "%s" requires a symbols, '
                                'and not a %s.') % (prefix, str(arg.parser)))
                return str(arg.result)
            self.variables.add(arg.result)

        if len(node.result) > 2:
            # shift = (Node(node.parser, node.result[1].result),)
            # node.result[1].result = shift + node.result[2:]
            node.result[1].result = (Node(node.result[1].parser,
                                          node.result[1].result),) \
                                    + node.result[2:]
            node.result[1].parser = node.parser
            node.result = (node.result[0], node.result[1])

        node.result = node.result[1:]
        for match, parser_class in self.PREFIX_TABLE:
            if prefix == match:
                return self.non_terminal(node, parser_class)

        assert False, ("Unknown prefix %s \n" % prefix) + node.as_sexpr()

    def option(self, node):
        return self.non_terminal(node, 'Optional')

    def repetition(self, node):
        return self.non_terminal(node, 'ZeroOrMore')

    def oneormore(self, node):
        return self.non_terminal(node, 'OneOrMore')

    def regexchain(self, node):
        raise EBNFCompilerError("Not yet implemented!")

    def group(self, node):
        raise EBNFCompilerError("Group nodes should have been eliminated by "
                                "AST transformation!")

    def symbol(self, node):
        if node.result in self.scanner_tokens:
            return 'ScannerToken("' + node.result + '")'
        else:
            self.symbols.add(node)
            if node.result in self.rules:
                self.recursive.add(node.result)
            return node.result

    def literal(self, node):
        return 'Token(' + ', '.join([node.result]) + ')'

    def regexp(self, node):
        rx = node.result
        name = []
        if rx[:2] == '~/':
            if not 'left' in self.directives['literalws']:
                name = ['wL=' + WHITESPACE_KEYWORD] + name
            rx = rx[1:]
        elif 'left' in self.directives['literalws']:
            name = ["wL=''"] + name
        if rx[-2:] == '/~':
            if 'right' not in self.directives['literalws']:
                name = ['wR=' + WHITESPACE_KEYWORD] + name
            rx = rx[:-1]
        elif 'right' in self.directives['literalws']:
            name = ["wR=''"] + name
        try:
            arg = repr(self._check_rx(node, rx[1:-1].replace(r'\/', '/')))
        except AttributeError as error:
            errmsg = EBNFCompiler.AST_ERROR + " (" + str(error) + ")\n" + \
                     node.as_sexpr()
            node.add_error(errmsg)
            return '"' + errmsg + '"'
        return 'RE(' + ', '.join([arg] + name) + ')'

    def list_(self, node):
        assert node.children
        return set(item.result.strip() for item in node.result)
