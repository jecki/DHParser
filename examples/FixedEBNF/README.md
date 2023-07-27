# FixedEBNF

FixedEBNF (aka ConfigurableEBNF) ist a grammar for a configurable superset of EBNF 
that reads classical  EBNF-syntax (e.g. "{ }" for repetitions) jut as well as 
regex-like EBNF-syntax (e.g. "...*" for repetitions). It is configurable in the sense 
that the hard-coded character-sequences for definitions, line-end etc. can be 
exchanged in the Grammar object (e.g. "::=" for definitions instead of "="), before 
the parser is run.

Author: Eckhart Arnold <eckhart.arnold@posteo.de>


## License

FixedEBNF is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

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
