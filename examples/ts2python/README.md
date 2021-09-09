# ts2python

A transpiler from TypeScript-Interface-definitions to TypedDict classes.

## License

ts2python is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

Copyright 2021 Eckhart Arnold <arnold@badw.de>, Bavarian Academy of Sciences and Humanities

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Purpose

When processing JSON data, as for example form a 
[JSON-RPC](https://www.jsonrpc.org/) call, with Python, it would
be helpful to have Python-definitions of the JSON-structures at
hand, in order to solicit IDE-Support, static type checking and,
potentially to enable structural validation at runtime. 

There exist different technologies for defining the structure of
JSON-data. Next to [JSON-schema](http://json-schema.org/), a 
de facto very popular technology for defining JSON-obejcts are
[Typescript-Interfaces](https://www.typescriptlang.org/docs/handbook/2/objects.html). 
For example, the 
[language server protocol](https://microsoft.github.io/language-server-protocol/specifications/specification-current/) 
defines the structure of the JSON-data exchanged between client 
and server with Typescript-Interfaces.

In order to enable structural validation on the Python-side, 
ts2python transpiles the typescript-interface definitions
to Python-[TypedDicts](https://www.python.org/dev/peps/pep-0589/).

## Installation

ts2python can be installed from the command line with the command:

    # pip install ts2python

ts2typedict requires the parsing-expression-grammar-framwork DHParser
which will automatically be installed as a dependency by 
the `pip`-command. ts2typedict requires at least Python Version 3.8
to run. (If there is any interest, I might backport it to Python 3.6.)

## Usage

In order to generate TypedDict-classes from Typescript-Interfaces,
run `ts2python` on the Typescript-Interface definitions:

    # ts2python interface_definitions.ts

This generates a .py-file in same directory as the source
file that contains the typescript classes and can simpy be 
imported in Python-Code:

    >>> from interface_definitions import *

## Validation

