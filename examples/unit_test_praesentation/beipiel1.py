import functools
import sys

sys.path.extend(['../../', '../', './'])

from DHParser import *


arithmetik_ebnf = """ 
    expr = expr ("+"|"-") term | term
    term = term ("*"|"/") factor | factor
    factor = /[0-9]+/~ | "(" expr ")"
    """

ASTTable = {
    "+": remove_expendables,
    "*": replace_by_single_child,
    "factor": [reduce_single_child, remove_brackets]
}

parser = grammar_provider(arithmetik_ebnf)()
transformer = functools.partial(traverse, processing_table=ASTTable.copy())


syntax_tree = parser("5 + 3 * 4")
assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())
transformer(syntax_tree)

print(">>>>> Ausdruck ohne Klammern:\n")
print(syntax_tree.as_sxpr(compact = True))


syntax_tree = parser("(5 + 3) * 4")
assert not syntax_tree.error_flag, str(syntax_tree.collect_errors())
transformer(syntax_tree)

print("\n\n>>>>> Ausdruck mit Klammern:\n")
print(syntax_tree.as_sxpr(compact = True))
