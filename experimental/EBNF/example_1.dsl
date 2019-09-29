# Arithmetic-grammar

#######################################################################
#
#  EBNF-Directives
#
#######################################################################

@ whitespace  = vertical           # implicit whitespace, includes any number of line feeds
@ literalws   = right              # literals have implicit whitespace on the right hand side
@ comment     = /#.*/              # comments range from a '#'-character to the end of the line
@ ignorecase  = False              # literals and regular expressions are case-sensitive
@ drop        = whitespace, token  # drop anonymous whitespace

#######################################################################
#
#  Structure and Components
#
#######################################################################

expression = term  { EXPR_OP~ term}
term       = factor  { TERM_OP~ factor}
factor     = [SIGN] ( NUMBER | VARIABLE | group ) { VARIABLE | group }
group      = "(" expression ")"

#######################################################################
#
# "Leaf"-Expressions
#
#######################################################################

EXPR_OP    = /\+/ | /-/
TERM_OP    = /\*/ | /\//
SIGN       = /-/

NUMBER     = /(?:0|(?:[1-9]\d*))(?:\.\d+)?/~
VARIABLE   = /[A-Za-z]/~
