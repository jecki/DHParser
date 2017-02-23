import os
import sys

sys.path.append(os.path.abspath('../'))

from ParserCombinators import *

arithmetic_EBNF = r"""
expression = term  { ("+" | "-") term}
term       = factor  { ("*"|"/") factor}
factor     = constant | variable | "("  expression  ")"
variable   = "x" | "y" | "z"
constant   = digit {digit}
digit      = "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
test       = digit constant variable
"""

TransTable = {
    "expression": [flatten, remove_operator],
    "term": [replace_by_single_child, flatten, remove_operator],
    "factor": [remove_enclosing_delimiters, replace_by_single_child],
    "constant": [replace_by_single_child, flatten],
    "digit": reduce_single_child,
    'variable': reduce_single_child,
    "Token": [remove_expendables, reduce_single_child],
    "": [remove_expendables, replace_by_single_child]
}

result, errors, syntax_tree = full_compilation(arithmetic_EBNF, EBNFGrammar.root__,
                                               EBNFTransTable, EBNFCompiler('Arithmetic'))
assert not errors
print(result)
parser = compile_python_parser(result)
syntax_tree = parse("2 + 2 * (3 - 4)", parser.root__)
print(syntax_tree.as_sexpr())
ASTTransform(syntax_tree, TransTable)
print(syntax_tree.as_sexpr())

