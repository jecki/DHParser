# EBNF-Grammar in EBNF

@ comment    = /#.*(?:\n|$)/                    # comments start with '#' and eat all chars up to and including '\n'
@ whitespace = /\s*/                            # whitespace includes linefeed
@ literalws  = right                            # trailing whitespace of literals will be ignored tacitly

syntax     = [~//] { definition | directive } §EOF
definition = symbol §"=" expression
directive  = "@" §symbol "=" (regexp | literal | symbol) { "," (regexp | literal | symbol) }

expression = term { "|" term }
term       = { ["§"] factor }+                       # "§" means all following factors mandatory
factor     = [flowmarker] [retrieveop] symbol !"="   # negative lookahead to be sure it's not a definition
           | [flowmarker] literal
           | [flowmarker] plaintext
           | [flowmarker] regexp
           | [flowmarker] whitespace
           | [flowmarker] oneormore
           | [flowmarker] group
           | [flowmarker] unordered
           | repetition
           | option

flowmarker = "!"  | "&"                         # '!' negative lookahead, '&' positive lookahead
           | "-!" | "-&"                        # '-' negative lookbehind, '-&' positive lookbehind
retrieveop = "::" | ":"                         # '::' pop, ':' retrieve

group      = "(" §expression ")"
unordered  = "<" §expression ">"                # elements of expression in arbitrary order
oneormore  = "{" expression "}+"
repetition = "{" §expression "}"
option     = "[" §expression "]"

symbol     = /(?!\d)\w+/~                       # e.g. expression, factor, parameter_list
literal    = /"(?:[^"]|\\")*?"/~                # e.g. "(", '+', 'while'
           | /'(?:[^']|\\')*?'/~                # whitespace following literals will be ignored tacitly.
plaintext  = /`(?:[^"]|\\")*?`/~                # like literal but does not eat whitespace
regexp     = /\/(?:\\\/|[^\/])*?\//~            # e.g. /\w+/, ~/#.*(?:\n|$)/~
whitespace = /~/~                               # insignificant whitespace

EOF = !/./
