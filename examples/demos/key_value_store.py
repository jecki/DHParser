# A mini-DSL for a key value store
from DHParser import *

# specify the grammar of your DSL in EBNF-notation
grammar = '''
@ drop = whitespace, strings
key_store   = ~ { entry }
entry       = key "=" value 
key         = /\w+/~             # Scannerless parsing, use regular
value       = /\"[^"\n]*\"/~     # expressions wherever you like'''

parser = grammar_provider(grammar)()

if __name__ == '__main__':
    text = '''
        title    = "Odysee 2001"
        director = "Stanley Kubrick"
    '''
    data = parser(text)

    for entry in data.select('entry'):
        print(entry['key'], entry['value'])
