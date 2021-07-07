#!/usr/bin/env python

# A mini-DSL for a key value store
from DHParser import create_parser

# specify the grammar of your DSL in EBNF-notation
grammar = '''@ drop = whitespace, strings
key_store   = ~ { entry }
entry       = key "=" ~ value
key         = /\w+/~                  # Scannerless parsing: Use regular
value       = /\"[^"\n]*\"/~          # expressions wherever you like'''

# generating a parser is almost as simple as compiling a regular expression
# parser = create_parser(grammar)             # parser factory for thread-safety

parser = create_parser(grammar)

text = '''
            title    = "Odysee 2001"
            director = "Stanley Kubrick"
        '''

if __name__ == "__main__":
    result = parser(text)
    assert not result.errors, str(result.as_sxpr())

