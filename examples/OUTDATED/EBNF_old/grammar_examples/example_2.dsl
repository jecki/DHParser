# An alternative EBNF-Grammar
# Please note: This does not work with the current ebnf.py
# TODO: Transform ASTs stemming from this grammar to ASTs
#       that DHParser.ebnf.EBNFCompiler can compile.

@ comment    = /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
@ whitespace = /\s*/                            # whitespace includes linefeed
@ literalws  = right                            # trailing whitespace of literals will be ignored tacitly

#: top-level

syntax     = [~//] { definition | directive } §EOF
definition = symbol §"=" expression
directive  = "@" §symbol "=" (regexp | literal | symbol) { "," (regexp | literal | symbol) }

#: components

expression = term { "|" term }
term       = { ["§"] factor }+                       # "§" means all following factors mandatory
factor     = [flowmarker] [retrieveop] symbol [suffix] !"="
           | [flowmarker] (  literal
                           | plaintext
                           | regexp
                           | whitespace
                           | group
                           | unordered ) [suffix]

#: flow-operators

flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
           | "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
retrieveop = "::" | ":"                         # '::' pop, ':' retrieve

#: groups

group      = "(" §expression ")"
unordered  = "{" §expression "}"                # elements of expression in arbitrary order

#: suffixes

oneormore  = "+"
repetition = "*"
option     = "?"

#: leaf-elements

symbol     = /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
literal    = /"(?:(?<!\\)\\"|[^"])*?"/~         # e.g. "(", '+', 'while'
           | /'(?:(?<!\\)\\'|[^'])*?'/~         # whitespace following literals will be ignored tacitly.
plaintext  = /`(?:(?<!\\)\\`|[^"])*?`/~         # like literal but does not eat whitespace
regexp     = /\/(?:(?<!\\)\\(?:\/)|[^\/])*?\//~     # e.g. /\w+/, ~/#.*(?:\n|$)/~
whitespace = /~/~                               # insignificant whitespace

EOF = !/./
