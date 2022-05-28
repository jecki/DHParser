# validate.py - validation of node-trees according to a
#               grammar-like schema (inspired by Relax NG)
#
# Copyright 2022  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

# see: https://relaxng.org/spec-20011203.html
#      https://relaxng.org/compact-tutorial-20030326.html
#      https://relaxng.org/tutorial-20011203.html

"""
Module ``validate`` contains functions and classes for the structural
validation (i.e. validation according to a grammar-like schema) of
node-trees. EXPERIMENTAL!!!
"""

from typing import Callable, Dict

from DHParser.nodetree import Node, RootNode, TreeContext, ANY_NODE


ValidationFunction = Callable[[Node, TreeContext], None]  # validate(schema, data)
SchemaLanguage = Dict[str, ValidationFunction]
Schema = Node


def is_schema(schema: Node, language: SchemaLanguage) -> bool:
    return all(node.name in language for node in schema.select(ANY_NODE))


def abstract_validate(language: SchemaLanguage, schema: Schema, data: Node) -> None:
    assert is_schema(schema, language)
    language[schema.name](schema, data)


## relax-like schema validation


def leaf(schema: Node, data: TreeContext) -> None:
    pass


def branch(schema: Node, data: TreeContext) -> None:
    pass


def alternative(schema: Node, data: TreeContext) -> None:
    pass


def optional(schema: Node, data: TreeContext) -> None:
    pass


def zero_or_more(schema: Node, data: TreeContext) -> None:
    pass


def one_or_more(schema: Node, data: TreeContext) -> None:
    pass


def series(schema: Node, data: TreeContext) -> None:
    pass


def interleave(schema: Node, data: TreeContext) -> None:
    pass


def forward(schema: Node, data: TreeContext) -> None:
    pass


Relax = {
    "leaf": leaf,
    "branch": branch,
    "alternative": alternative,
    "optional": optional,
    "zeroOrMore": zero_or_more,
    "oneOrMore": one_or_more,
    "series": series,
    "interleave": interleave,
    "forward": forward
}

