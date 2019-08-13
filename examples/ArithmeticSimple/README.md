# Arithmetic

This example demonstrates two alternative ways to write a parser
for simple arithmetic formulae. Both grammar's yield the same abstract
syntax tree with the right (i.e. grammar-specific) AST-transformations.
Any further compiler or formular-evaluation step (not demonstrated) 
here can then in principle be shared by both parsers. Because of this, 
both parsers can also use the same grammar-testsuite.

"ArithmeticRightRecursive" incidently demonstrates how to parse
left-associatve operators with a right-recursive grammar (left-recursive
grammars are possible with DHParser, but not reccomended) and then
transforming then into a left-leaning tree with 
`DHParser.transform.lean_left`. Please, observe, that this requires 
to place the removal of "group"-nodes in a second transformation pass.
 
In my opinion, it is easier to write a grammar in the style of
"ArithmeticSimple.ebnf" than in the style of 
"ArithmeticRightRecursive.ebnf", while both require about the same 
amount of attention when designing the abstract syntax tree 
transformations. But decide for yourself.

Author: Eckhart Arnod (eckhart.arnold@posteo.de)


## License

Arithmetic is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

Copyright YEAR AUTHOR'S NAME <EMAIL>, AFFILIATION

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
