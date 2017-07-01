#!/usr/bin/python3

"""test_ParserCombinators.py - unit tests for module ParserCombinators


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

"""

import os
import re
import sys

sys.path.append(os.path.abspath('../'))

from ParserCombinators import EBNFGrammar, EBNFTransTable, EBNFCompiler, full_compilation, Forward, RegExp, \
    Alternative, Sequence, Token, compile_python_object, compileDSL, GrammarBase

arithmetic_EBNF = r"""
expression =  term  { ("+" | "-") term}
term       =  factor  { ("*"|"/") factor}
factor     =  constant | variable | "("  expression  ")"
variable   =  "x" | "y" | "z"
constant   =  digit {digit}
digit      =  "0" | "1" | "..." | "9"
test       =  digit constant variable
"""

arithmetic_expected_result = """
class ArithmeticGrammar(ParserRoot):
    constant = Forward()
    digit = Forward()
    expression = Forward()
    variable = Forward()
    wspc__ = mixin_comment(whitespace=r'\s*', comment=r'')
    test = Sequence("test", digit, constant, variable)
    digit.set(Alternative("digit", Token("0", wspcR=wspc__), Token("1", wspcR=wspc__), Token("...", wspcR=wspc__), Token("9", wspcR=wspc__)))
    constant.set(Sequence("constant", digit, ZeroOrMore(None, digit)))
    variable.set(Alternative("variable", Token("x", wspcR=wspc__), Token("y", wspcR=wspc__), Token("z", wspcR=wspc__)))
    factor = Alternative("factor", constant, variable, Sequence(None, Token("(", wspcR=wspc__), expression, Token(")", wspcR=wspc__)))
    term = Sequence("term", factor, ZeroOrMore(None, Series(None, Alternative(None, Token("*", wspcR=wspc__), Token("/", wspcR=wspc__)), factor)))
    expression.set(Sequence("expression", term, ZeroOrMore(None, Series(None, Alternative(None, Token("+", wspcR=wspc__), Token("-", wspcR=wspc__)), term))))
    root__ = expression
"""

ebnf_EBNF = r"""
# Starting comment
@ whitespace =  /\s*/         # '@' means the folowing assingment is a compiler directive

syntax     =  { production }
production =  symbol "=" expression "."

expression =  term { "|" term }
term       =  factor { factor }
factor     =  symbol
           | literal
           | regexp    # regular expressions
           | option
           | repetition
           | group

option     =  "[" expression "]"
repetition =  "{" expression "}"
group      =  "(" expression ")"

symbol     =  ~/\w+/~
literal    =  ~/"(?:[^"]|\\")*"/~
           | ~/'(?:[^']|\\')*'/~
regexp     =  ~/~\/(?:[^\/]|(?<=\\)\/)*\/~/~
           | ~/\/(?:[^\/]|(?<=\\)\/)*\//~
           
# trailing whitespace and comments
"""

ebnf_expected_result = r"""
class EBNFGrammar(ParserRoot):
    expression = Forward()
    wspc__ = mixin_comment(whitespace=r'\s*', comment=r'')
    regexp = Alternative("regexp", RE('~/(?:[^/]|(?<=\\\\)/)*/~', wspcL=wspc__, wspcR=wspc__), RE('/(?:[^/]|(?<=\\\\)/)*/', wspcL=wspc__, wspcR=wspc__))
    literal = Alternative("literal", RE('"(?:[^"]|\\\\")*"', wspcL=wspc__, wspcR=wspc__), RE("'(?:[^']|\\\\')*'", wspcL=wspc__, wspcR=wspc__))
    symbol = RE('\\w+', "symbol", wspcL=wspc__, wspcR=wspc__)
    group = Sequence("group", Token("(", wspcR=wspc__), expression, Token(")", wspcR=wspc__))
    repetition = Sequence("repetition", Token("{", wspcR=wspc__), expression, Token("}", wspcR=wspc__))
    option = Sequence("option", Token("[", wspcR=wspc__), expression, Token("]", wspcR=wspc__))
    factor = Alternative("factor", symbol, literal, regexp, option, repetition, group)
    term = Sequence("term", factor, ZeroOrMore(None, factor))
    expression.set(Sequence("expression", term, ZeroOrMore(None, Series(None, Token("|", wspcR=wspc__), term))))
    production = Sequence("production", symbol, Token("=", wspcR=wspc__), expression, Token(".", wspcR=wspc__))
    syntax = ZeroOrMore("syntax", production)
    root__ = syntax
"""


class LeftRecursiveGrammar(GrammarBase):
    """formula = expr "."
    expr = expr ("+"|"-") term | term
    term = term ("*"|"/") factor | factor
    factor = /[0-9]+/
    """
    expr = Forward()
    term = Forward()
    factor = RegExp("factor", '[0-9]+')
    term.set(Alternative("term", Sequence(None, term, Alternative(None, Token("*"), Token("/")), factor), factor))
    expr.set(Alternative("expr", Sequence(None, expr, Alternative(None, Token("+"), Token("-")), term), term))
    formula = Sequence("formula", expr, Token("."))
    root__ = formula


def rem_docstring(class_py):
    return re.sub(r'r"""(?:.|\n)*"""\n    ', '', class_py).strip()


class TestEBNFCompiler:
    def test_EBNFGrammar(self):
        assert (str(EBNFGrammar.root__) == str(EBNFGrammar.root__))

    def test_arithmeticEBNF(self):
        result, errors, syntax_tree = full_compilation(arithmetic_EBNF, EBNFGrammar(),
                                                       EBNFTransTable, EBNFCompiler('Arithmetic'))
        assert result is not None, errors
        assert arithmetic_expected_result.strip() == rem_docstring(result)

    def test_ebnfEBNF(self):
        result, errors, syntax_tree = full_compilation(ebnf_EBNF, EBNFGrammar(),
                                                       EBNFTransTable, EBNFCompiler('EBNF'))
        assert not errors, str(errors)
        assert ebnf_expected_result.strip() == rem_docstring(result)

    def test_compileDSL(self):
        bootstrap1 = compileDSL("../examples/EBNF/EBNF.ebnf", "../examples/EBNF/EBNF.ebnf",
                                EBNFTransTable, EBNFCompiler())
        bootstrap2 = compileDSL("../examples/EBNF/EBNF.ebnf", bootstrap1, EBNFTransTable, EBNFCompiler())
        assert bootstrap1 == bootstrap2

    def test_regexErrorHandling(self):
        ebnf_line = r"""regexfine =  ~/~\/(?:[^\/]|(?<=\\)\/)*\/~/~""" + '\n'  # no errors should be raised
        result, messages, syntax_tree = full_compilation(ebnf_line, EBNFGrammar(),
                                                         EBNFTransTable, EBNFCompiler('RegExTest'))
        assert messages == "", messages
        ebnf_line = r"""regexbad =  ~/\/(?:[^\/]|(?<=\\)*\//~""" + '\n'  # missing ")" should be detected
        result = EBNFGrammar()(ebnf_line)
        result, messages, syntax_tree = full_compilation(ebnf_line, EBNFGrammar(),
                                                         EBNFTransTable, EBNFCompiler('RegExTest'))
        assert messages != ""

    def test_multilineRegex(self):
        mlregex = r"""
        regex =  /\w+    # one or more alphabetical characters including the underscore
                  [+]    # followed by a plus sign
                  \w*    # possibly followed by more alpha chracters/
        """
        result, messages, syntax_tree = full_compilation(mlregex, EBNFGrammar(), EBNFTransTable,
                                                         EBNFCompiler('MultilineRegexTest'))
        assert result is not None, messages
        assert not messages
        parser = compile_python_object(result)()
        node, rest = parser.regex('abc+def')
        assert rest == ''
        assert node.parser.component == "regex"
        assert str(node) == 'abc+def'


def test_LeftRecursion():
    input_str = "5 + 3 * 4 .\n"
    syntax_tree = LeftRecursiveGrammar().parse(input_str)
    assert str(syntax_tree) == input_str
