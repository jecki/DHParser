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
node-trees. EXPERIMENTAL!!! THIS IS STILL A STUB!!!
"""

from __future__ import annotations

import re
from typing import Callable, Dict

from DHParser.nodetree import Node, RootNode, Path, ANY_NODE
from DHParser.toolkit import TypeAlias


ValidationFunction: TypeAlias = Callable[[Node, Path], None]  # validate(schema, data)
SchemaLanguage: TypeAlias = Dict[str, ValidationFunction]
Schema: TypeAlias = Node


def is_schema(schema: Node, language: SchemaLanguage) -> bool:
    return all(node.name in language for node in schema.select(ANY_NODE))


def abstract_validate(language: SchemaLanguage, schema: Schema, data: Node) -> None:
    assert is_schema(schema, language)
    language[schema.name](schema, [data])


# relax-like schema validation

RX_ANYSTRING = re.compile('.?')


def verify_attributes(schema: Node, data: Path) -> bool:
    attributes = schema.get_attr('attributes', '').split(',')
    if isinstance(attributes, str):
        attributes = attributes.split(',')
        schema.attr['attributes'] = tuple(attributes)
    else:
        assert isinstance(attributes, tuple)
        attributes = list(attributes)
    value_patterns = schema.get_attr('values', '').split(',')
    if attributes:
        allow_free_attributes = False
        if attributes[-1] == '*':
            allow_free_attributes = True
            attributes.pop()
        if not value_patterns:
            for _ in range(len(attributes)):
                value_patterns.append(RX_ANYSTRING)
        assert len(attributes) == len(value_patterns)
        
    else:
        assert not value_patterns


def leaf(schema: Node, data: Path) -> None:
    global Relax
    pass


def branch(schema: Node, data: Path) -> None:
    pass


def alternative(schema: Node, data: Path) -> None:
    pass


def optional(schema: Node, data: Path) -> None:
    pass


def zero_or_more(schema: Node, data: Path) -> None:
    pass


def one_or_more(schema: Node, data: Path) -> None:
    pass


def series(schema: Node, data: Path) -> None:
    pass


def interleave(schema: Node, data: Path) -> None:
    pass


def forward(schema: Node, data: Path) -> None:
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

