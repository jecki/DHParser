#!/usr/bin/python3

import sys

LOGGING = True

sys.path.extend(['../../', '../', './'])

from DHParser import grammar_provider, logging, CONFIG_PRESET


CONFIG_PRESET['ast_serialization'] = "S-expression"
CONFIG_PRESET['test_parallelization'] = False
CONFIG_PRESET['left_recursion_depth'] = 2


arithmetic_syntax = """
    expression     = addition | subtraction
    addition       = (expression | term) "+" (expression | term)
    subtraction    = (expression | term) "-" (expression | term)
    term           = multiplication | division
    multiplication = (term | factor) "*" (term | factor)
    division       = (term | factor) "/" (term | factor)
    factor         = [SIGN] ( NUMBER | VARIABLE | group ) { VARIABLE | group }
    group          = "(" §expression ")"
    SIGN           = /[+-]/
    NUMBER         = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
    VARIABLE       = /[A-Za-z]/~        
    """

if __name__ == "__main__":
    arithmetic = grammar_provider(arithmetic_syntax)()
    assert arithmetic
    with logging():
        syntax_tree = arithmetic("(a + b) * (a - b)")
