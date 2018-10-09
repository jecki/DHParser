# XML

This is a complete XML-Parser, see: https://www.w3.org/TR/REC-xml/

Author: Eckhart Arnold <eckhart.arnold@posteo.de>


## License

XML is open source software under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0)

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


## Goals

* create a non-validating XML-processor
* parsing and compiling of XML-files into Element-Trees
* serializing Element-Tress as XML
* full support of valid any XML-file
* round-trip: valid XML can be turned into an XML file and
  serialized into XML again, without loss of data, i.e. re-parsing
  yields the same element-tree ("structural identity").


## Optional (future) Goals

* support all validity constraints mentioned in
  https://www.w3.org/TR/REC-xml/
* create validating XML-processor, i.e. support for DTDs, in particular
  checking element tree against DTD
* add a python-API for semantic checks à la schematron, only simpler ;-)
* preservance of "insignificant whitespace", i.e. support
  round-trip with "string-identity"


## Non-Goals

* support for HTML
* support of Carriage Return, i.e. Windows line endings...

## Status

+ Parses XML files, i.e. parser and AST-transformation are complete
+ simple XML files are compiled into an element-tree
- limited support for CharData
- no support for CDATA-sections
- processing instrcutions not yet compiled
- no processing of DTDs

