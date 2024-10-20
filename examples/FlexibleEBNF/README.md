# Flexible EBNF

A flexible EBNF grammar for DHParsers that allows to use 
as many different flavors of EBNF as possible. Which
delimiter characters are used (e.g. "::=" or "=" for 
definitions)

Author: Eckhart Arnold <eckhart.arnold@posteo.de>, 
        Bavarian Academy of Sciences and Humanities


This EBNF-grammar is tunes towards maximal flexibility. Its purpose is 
to support as many different variants of EBNF as possible. The price
for this flexibility is that the grammar is less readable than the
grammar for one particular flavor of EBNF. Also, because it makes use
of capturing variables, the generated parser is slower than that for
a plain EBNF grammar.

