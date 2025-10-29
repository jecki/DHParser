#!/usr/bin/env python
# A mini-DSL for a key value store
from DHParser.dsl import create_parser
from DHParser.ebnf import grammar_changed

# specify the grammar of your DSL in EBNF-notation
grammar = r'''@ drop = whitespace, strings
key_store   = ~ { entry }
entry       = key "="~ value          # ~ means: insignificant whitespace 
key         = /\w+/~                  # Scanner-less parsing: Use regular
value       = /\"[^"\n]*\"/~          # expressions wherever you like'''

# generating a parser is almost as simple as compiling a regular expression
parser = create_parser(grammar, branding="KeyValue")  # parser factory for thread-safety
print(parser.python_src__)
print(grammar_changed(parser, grammar))