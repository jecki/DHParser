# configuration.py - default configuration values for DHParser
#
# Copyright 2016  by Eckhart Arnold (arnold@badw.de)
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

"""
Module "configuration.py" defines the default configuration for DHParser.
The configuration values can be changed while running via the
DHParser.toolkit.get_config_value() and DHParser.toolkit.get_config_value()-
functions.

The presets can also be overwritten before(!) spawning any parsing processes by
overwriting the values in the CONFIG_PRESET dictionary.

The recommended way to use a different configuration in any custom code using
DHParser is to use the second method, i.e. to overwrite the values for which
this is desired in the CONFIG_PRESET dictionary right after the start of the
program and before any DHParser-function is invoked.
"""

from typing import Dict, Hashable, Any

__all__ = ('CONFIG_PRESET',)

CONFIG_PRESET = dict()  # type: Dict[Hashable, Any]


# DHParser.ebnfy.EBNFCompiler class adds the the EBNF-grammar to the
# docstring of the generated Grammar-class
# Default value: False
CONFIG_PRESET['add_grammar_source_to_parser_docstring'] = False

# Flattens anonymous nodes, by removing the node and adding its children
# to the parent node in place of the removed node. This is a very useful
# optimization that should be turned on except for learning or teaching
# purposes, in which case a concrete syntax tree that more diligently
# reflects the parser structure may be helpful.
CONFIG_PRESET['flatten_tree_while_parsing'] = True

# # Carries out static analysis on the the parser tree before parsing starts
# # to ensure its correctness. Possible values are:
# # 'early' - static analysis is carried out by DHParser.ebnf.EBNFCompiler,
# #           already. Any errors it revealed will be located in the EBNF
# #           source code. This naturally only works for parser that are
# #           generated from an EBNF syntax declaration.
# # 'late' -  static analysis is carried out when instantiating a Grammar
# #           (sub-)class. This works also for parser trees that are
# #           handwritten in Python using the parser classes from module
# #           `parse`. It slightly slows down instantiation of Grammar
# #           classes, though.
# # 'none' -  no static analysis at all (not recommended).
# # Default value: "early"
# CONFIG_PRESET['static_analysis'] = "early"

# Defines the output format for the serialization of syntax trees.
# Possible values are:
# 'XML'          - output as XML
# 'S-expression' - output as S-expression, i.e. a list-like format
# 'compact'      - compact tree output, i.e. children a represented
#                  on indented lines with no opening or closing tags,
#                  brackets etc.
# Default values: "compact" for concrete syntax trees and "XML" for
#                 abstract syntax trees and "S-expression" for any
#                 other kind of tree.
CONFIG_PRESET['cst_serialization'] = "compact"
CONFIG_PRESET['ast_serialization'] = "XML"
CONFIG_PRESET['default_serialization'] = "S-expression"

# Allows (coarse-grained) parallelization for running tests via the
# Python multiprocessing module
# Default value: True
CONFIG_PRESET['test_parallelization'] = True
