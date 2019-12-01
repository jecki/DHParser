# trace.py - tracing of the parsing process (for debugging)
#
# Copyright 2018  by Eckhart Arnold (arnold@badw.de)
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
Module ``trace`` provides trace-debugging functionality for the
parser. The tracers are added or removed via monkey patching to
all or some particular parsers of a grammar and trace the actions
of these parsers, making use of the `call_stack__`, `history__`
and `moving_forward__`, `most_recent_error__`-hooks in the
Grammar-object.

This allows for more flexible and at the same time more focused
tracing of the parsing process than the (older) parsing-history-
tracking-mechanism in the `parse` module, which will eventually
be superceded by tracing.
"""

from typing import Tuple, Optional, List, Collection, Union

from DHParser.stringview import StringView
from DHParser.syntaxtree import Node, REGEXP_PTYPE, TOKEN_PTYPE, WHITESPACE_PTYPE, \
    EMPTY_PTYPE, EMPTY_NODE
from DHParser.log import HistoryRecord
from DHParser.parse import Parser, ParserError, ParseFunc

__all__ = ('trace_history', 'with_all_descendants', 'with_unnamed_descendants', 'set_tracer')


def trace_history(self, text: StringView) -> Tuple[Optional[Node], StringView]:
    grammar = self._grammar
    location = grammar.document_length__ - text._len
    grammar.call_stack__.append(
        ((self.repr if self.tag_name in (REGEXP_PTYPE, TOKEN_PTYPE)
          else (self.pname or self.tag_name)), location))
    # TODO: Record history on turning points here? i.e. when moving_forward is False
    grammar.moving_forward__ = True

    try:
        node, rest = self._parse(text)
    except ParserError as pe:
        grammar.call_stack__.pop()
        raise pe

    # Mind that memoized parser calls will not appear in the history record!
    # Don't track returning parsers except in case an error has occurred!
    # TODO: Try recording all named parsers on the way back?
    delta = text._len - rest._len
    if ((grammar.moving_forward__ or grammar.most_recent_error__ or (node and not self.anonymous))
            and (self.tag_name != WHITESPACE_PTYPE)):  # TODO: Make dropping insignificant whitespace from history configurable
        errors = [grammar.most_recent_error__] if grammar.most_recent_error__ else []
        grammar.most_recent_error__ = None
        line_col = grammar.line_col__(text)
        nd = Node(node.tag_name, text[:delta]).with_pos(location) if node else None
        record = HistoryRecord(grammar.call_stack__, nd, rest, line_col, errors)
        if (not grammar.history__ or line_col != grammar.history__[-1].line_col
            or record.call_stack != grammar.history__[-1].call_stack[:len(record.call_stack)]):
            grammar.history__.append(record)
    grammar.moving_forward__ = False
    grammar.call_stack__.pop()

    return node, rest


def with_all_descendants(root: Parser) -> List[Parser]:
    """Returns a list with the parser `root` and all of its descendants."""
    descendants = []
    def visit(parser: Parser):
        descendants.append(parser)
    root.apply(visit)
    return descendants


def with_unnamed_descendants(root: Parser) -> List[Parser]:
    """Returns a list that contains the parser `root` and """
    descendants = [root]
    for parser in root.sub_parsers():
        if not parser.pname:
            descendants.extend(with_unnamed_descendants(parser))
    return descendants


def set_tracer(parsers: Union[Parser, Collection[Parser]], tracer: Optional[ParseFunc]):
    if isinstance(parsers, Parser):
        parsers = [parsers]
    for parser in parsers:
        if parser.ptype != ':Forward':
            parser.set_proxy(tracer)

