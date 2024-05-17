#!/usr/bin/env python3

import sys

LOGGING = True

sys.path.extend([os.path.join('..', '..'), '..', '.'])

from DHParser import grammar_provider, access_presets, finalize_presets, set_config_preset


access_presets()
set_config_preset('AST_serialization', "S-expression")
set_config_preset('test_parallelization', False)
set_config_preset('left_recursion_depth', 2)
finalize_presets()


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
    syntax_tree = arithmetic("(a + b) * (a - b)")
