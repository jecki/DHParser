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

__all__ = ('CONFIG_PRESET',
           'XML_SERIALIZATION',
           'SXPRESSION_SERIALIZATION',
           'COMPACT_SERIALIZATION',
           'SMART_SERIALIZATION',
           'JSON_SERIALIZATION',
           'SERIALIZATIONS')

CONFIG_PRESET = dict()  # type: Dict[Hashable, Any]


########################################################################
#
# parser configuration
#
########################################################################

# Flattens anonymous nodes, by removing the node and adding its children
# to the parent node in place of the removed node. This is a very useful
# optimization that should be turned on except for learning or teaching
# purposes, in which case a concrete syntax tree that more diligently
# reflects the parser structure may be helpful.
# Default value: True
CONFIG_PRESET['flatten_tree_while_parsing'] = True

# Maximum depth of parser's left recursion
# This limit should not be set to high, because the left recursion
# catching algorithm can take exponential time, and, of course,
# because of python's recursion depth limit
# Left recursion handling can be turned off by setting this value to zero
# Default value: 5
CONFIG_PRESET['left_recursion_depth'] = 5

# Maximum allowed number of retries after errors where the parser
# would exit before the complete document has been parsed. Should
# not be set too high, because automatic retry works poorly.
# This value does not affect the @resume-directive.
# Default value: 3
CONFIG_PRESET['max_parser_dropouts'] = 3


########################################################################
#
# syntaxtree configuration
#
########################################################################

# Defines the output format for the serialization of syntax trees.
# Possible values are:
# 'XML'          - output as XML
# 'S-expression' - output as S-expression, i.e. a list-like format
# 'compact'      - compact tree output, i.e. children a represented on
#                  indented lines with no opening or closing tags, brackets
#                  etc.
# 'smart'        - serialize as S-expression if the S-expression fits on
#                  one line (see 'flatten_sxpr_threshold'), otherwise
#                  serialize as compact tree output
# 'json'         - output in JSON-format. This is probably the least
#                  readable representation, but useful for serialization, for
#                  example, to return syntax trees from remote procedure calls.
# Default values: "compact" for concrete syntax trees and "XML" for abstract
#                 syntax trees and "S-expression" for any other kind of tree.
XML_SERIALIZATION = "XML"
SXPRESSION_SERIALIZATION = "S-expression"
COMPACT_SERIALIZATION = "compact"
SMART_SERIALIZATION = "smart"
JSON_SERIALIZATION = "json"

SERIALIZATIONS = frozenset({XML_SERIALIZATION,
                            SXPRESSION_SERIALIZATION,
                            COMPACT_SERIALIZATION,
                            JSON_SERIALIZATION})

CONFIG_PRESET['cst_serialization'] = SMART_SERIALIZATION
CONFIG_PRESET['ast_serialization'] = SMART_SERIALIZATION
CONFIG_PRESET['default_serialization'] = SMART_SERIALIZATION

# Defines the maximum line length for flattened S-expressions.
# Below this threshold S-expressions will be returned in flattened
# form by DhParser.syntaxtree.serialize() and other functions
# that use serialize(), like, for example, the reporting functions
# in DHParser.testing.
# Default value: 120
CONFIG_PRESET['flatten_sxpr_threshold'] = 120


########################################################################
#
# ebnf compiler configuration
#
########################################################################

# Carries out static analysis on the the parser tree before parsing starts
# to ensure its correctness. Possible values are:
# 'early' - static analysis is carried out by DHParser.ebnf.EBNFCompiler,
#           already. Any errors it revealed will be located in the EBNF
#           source code. This naturally only works for parser that are
#           generated from an EBNF syntax declaration.
# 'late' -  static analysis is carried out when instantiating a Grammar
#           (sub-)class. This works also for parser trees that are
#           handwritten in Python using the parser classes from module
#           `parse`. It slightly slows down instantiation of Grammar
#           classes, though.
# 'none' -  no static analysis at all (not recommended).
# Default value: "early"
CONFIG_PRESET['static_analysis'] = "none"

# DHParser.ebnfy.EBNFCompiler class adds the the EBNF-grammar to the
# docstring of the generated Grammar-class
# Default value: False
CONFIG_PRESET['add_grammar_source_to_parser_docstring'] = False


########################################################################
#
# compiler server configuration
#
########################################################################

# Maximum allowed source size for reomote procedure calls (including
# parameters) in server.Server. The default value is rather large in
# order to allow transmitting complete source texts as parameter.
# Default value: 4 MB
CONFIG_PRESET['max_rpc_size'] = 4 * 1024 * 1024

# Defaut host name or IP-adress for the compiler server. Should usually
# be localhost (127.0.0.1)
# Default value: 127.0.0.1.
CONFIG_PRESET['server_default_host'] = "127.0.0.1"

# Default port number for the compiler server.
# Default value: 8888
CONFIG_PRESET['server_default_port'] = 8888


########################################################################
#
# debugging support configuration
#
########################################################################

# Turn on (costly) debugging functionality for any of the respective
# modules or subsystems.
# Default value: always False
CONFIG_PRESET['debug_compiler'] = False


########################################################################
#
# logging support configuration
#
########################################################################

# Log server traffic (requests and responses)
# Default value: False
CONFIG_PRESET['log_server'] = False


########################################################################
#
# testing framework configuration
#
########################################################################

# Allows (coarse-grained) parallelization for running tests via the
# Python multiprocessing module
# Default value: True
CONFIG_PRESET['test_parallelization'] = True
