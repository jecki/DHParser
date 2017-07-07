#!/usr/bin/python3

"""LatexParser.py - Parses the Erweiterte Backus-Naur-Form


Copyright 2016  by Eckhart Arnold

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


Module latex_parser defines a parser for the Erweiterte Bacchus-Naur-Form.
"""

# TODO: Document all the code!


import re

from ParserCombinators import Alternative, Forward, RE, Sequence, Token, Required, \
    ZeroOrMore, replace_by_single_child, remove_enclosing_delimiters, remove_whitespace, strip_assignment, \
    reduce_single_child, flatten_sameop_sequence, flatten_repetition, CompilerBase, full_compilation, \
    error_messages


class EBNFGrammar:
    expression = Forward()

    regexp = Alternative("regexp", RE('~/(?:[^/]|(?<=\\\\)/)*/~'), RE('/(?:[^/]|(?<=\\\\)/)*/'))
    literal = Alternative("literal", RE('§?"(?:[^"]|\\\\")*"'), RE("§?'(?:[^']|\\\\')*'"))
    symbol = RE('\\w+', "symbol")

    group = Sequence("group", Token("("), expression, Required(Token(")")))
    repetition = Sequence("repetition", Token("{"), expression, Required(Token("}")))
    option = Sequence("option", Token("["), expression, Required(Token("]")))

    factor = Alternative("factor", symbol, literal, regexp, option, repetition, group)
    term = Sequence("term", factor, ZeroOrMore(None, factor))
    expression.set(Sequence("expression", term, ZeroOrMore(None, Sequence(None, Token("|"), term))))

    production = Sequence("production", symbol, Required(Token("=")), expression, Required(Token(".")))
    syntax = ZeroOrMore("syntax", production)


EBNFTransTable = {
    # AST Transformations for EBNF-Grammar
    "production": strip_assignment,
    "expression": flatten_sameop_sequence,
    "term": flatten_repetition,
    "factor": replace_by_single_child,
    "group": [remove_enclosing_delimiters, replace_by_single_child],
    "repetition": remove_enclosing_delimiters,
    "option": remove_enclosing_delimiters,
    "symbol": remove_whitespace,
    "Token": remove_whitespace,
    "RE": remove_whitespace,
    "literal": [reduce_single_child, remove_whitespace],
    "regexp": [reduce_single_child, remove_whitespace],
    "": [remove_whitespace, replace_by_single_child]
}


class EBNFCompiler(CompilerBase):
    """Generates a Parser from an abstract syntax tree of a grammar specified
    in EBNF-Notation.
    """

    def __init__(self, grammar_name="Grammar"):
        super(EBNFCompiler, self).__init__()
        assert re.match('\w+\Z', grammar_name)
        self.grammar_name = grammar_name
        self.rules = set()
        self.symbols = set()
        self.component = str(None)
        self.recursive = set()

    def syntax(self, node):
        productions = []
        for nd in node.result:
            productions += [self.compile__(nd)]
        root = productions[0][0] if productions else ""
        productions.reverse()
        declarations = ['class ' + self.grammar_name + ':']
        declarations += [symbol + ' = Forward()' for symbol in self.recursive]
        for symbol, statement in productions:
            if symbol in self.recursive:
                declarations += [symbol + '.set(' + statement + ')']
            else:
                declarations += [symbol + ' = ' + statement]
        for nd in self.symbols:
            if nd.result not in self.rules:
                nd.add_error("Missing production for symbol '%s'" % nd.result)
        if root and '_root' not in self.symbols:
            declarations.append('_root = ' + root)
        return '\n    '.join(declarations)

    def production(self, node):
        rule = node.result[0].result
        self.component = '"' + rule + '"'
        self.rules.add(rule)
        prod = self.compile__(node.result[1])
        return (rule, prod)

    def _non_terminal(self, node, kind):
        """Compiles any non-terminal, where `kind` indicates the Parser class
        name for the particular non-terminal.
        """
        comp = self.component;  self.component = str(None)
        arguments = [comp] + [self.compile__(r) for r in node.result]
        return kind + '(' + ', '.join(arguments) + ')'

    def expression(self, node):
        return self._non_terminal(node, 'Alternative')

    def term(self, node):
        return self._non_terminal(node, 'Sequence')

    def option(self, node):
        return self._non_terminal(node, 'Option')

    def repetition(self, node):
        return self._non_terminal(node, 'ZeroOrMore')

    def symbol(self, node):
        self.symbols.add(node)
        if node.result in self.rules:
            self.recursive.add(node.result)
        return node.result

    def _re_variant(self, node, kind):
        """Compiles some variant of a regular expression, where `kind`
        indicates the variant, i.e. the classname of the Parser like
        `Token` or `Re`.
        """
        comp = [self.component] if self.component != str(None) else []
        self.component = str(None)
        arg = node.result[1:] if node.result[0:1] == "~" else node.result
        return kind + '(' + ', '.join([arg] + comp) + ')'

    def literal(self, node):
        comp = [self.component] if self.component != str(None) else []
        self.component = str(None)
        if node.result[0] == '§':
            return 'Required(Token(' + ', '.join([node.result[1:]] + comp) + '))'
        else:
            return 'Token(' + ', '.join([node.result] + comp) + ')'

    def regexp(self, node):
        comp = [self.component] if self.component != str(None) else []
        self.component = str(None)
        if (node.result[:2], node.result[-2:]) == ('~/', '/~'):
            arg = repr(node.result[2:-2].replace(r'\/', '/'))
            return 'RE(' + ', '.join([arg] + comp) + ')'
        else:
            comp = comp or [str(None)]
            arg = repr(node.result[1:-1].replace(r'\/', '/'))
            return 'RegExp(' + ', '.join(comp + [arg]) + ')'


def load_if_file(text_or_file):
    """Reads and returns content of a file if parameter `text_or_file` is a
    file name (i.e. a single line string), otherwise (i.e. if `text_or_file` is
    a multiline string) returns the content of `text_or_file`.
    """
    if text_or_file.find('\n') > 0:
        with open(text_or_file) as f:
            content = f.read()
        return content
    else:
        return text_or_file


class Error(Exception):
    """Base class for Errors in this module"""
    pass


class GrammarError(Error):
    """Raised when (already) the grammar of a domain specific language (DSL)
    contains errors.
    """

    def __init__(self, grammar_src, error_messages):
        self.grammar_src = grammar_src
        self.error_messages = error_messages


class CompileError(Error):
    """Raised when a string or file in a domain specific language (DSL)
    contains errors.
    """

    def __init__(self, dsl_text, dsl_grammar, error_messages):
        self.dsl_text = dsl_text
        self.dsl_grammar = dsl_grammar
        self.error_messages = error_messages


def compileDSL(text_or_file, dsl_grammar, trans_table, compiler):
    """Compiles a text in a domain specific language (DSL) with an
    EBNF-specified grammar. Resurns the compiled text.
    """
    assert isinstance(text_or_file, str)
    assert isinstance(dsl_grammar, str)
    assert isinstance(compiler, CompilerBase)
    assert isinstance(trans_table, dict)

    # read grammar
    grammar_src = load_if_file(dsl_grammar)
    parser_py, errors, AST = full_compilation(grammar_src, EBNFGrammar.syntax,
                                              EBNFTransTable, EBNFCompiler())
    if errors:  raise GrammarError(grammar_src, error_messages(grammar_src, errors))
    code = compile(parser_py, '<string>', 'exec')
    name_space = {}
    exec(code, name_space)
    parser = name_space['Grammar']

    src = load_if_file(text_or_file)
    result, errors, AST = full_compilation(src, parser.root, trans_table, compiler)
    if errors:  raise CompileError(src, grammar_src, error_messages(src, errors))
    return result


if __name__ == "__main__":
    assert (str(EBNFGrammar.syntax) == str(EBNFGrammar.syntax))

    def test(file_name):
        print(file_name)
        with open('testdata/' + file_name) as f:
            text = f.read()
        result, errors, syntax_tree = full_compilation(text, EBNFGrammar.syntax,
                                                       EBNFTransTable, EBNFCompiler())
        print(errors)
        print(syntax_tree.as_sxpr())
        print(result)
        return result


    print(EBNFGrammar.syntax)
    test('arithmetic.ebnf')
    test('ebnf_1.ebnf')

    # test('ebnf_modern.ebnf')

    # code = test('left_recursion.ebnf')
    # exec(code)
    # result = parse("1 + 2 - 3 * 5 .", formula)
    # print(result.as_sxpr())
    # print(result.collect_errors())
    # print(result)
