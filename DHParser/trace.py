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
"""

from typing import Tuple, Optional, List, Iterable, Union

from DHParser.error import Error
from DHParser.stringview import StringView
from DHParser.syntaxtree import Node, REGEXP_PTYPE, TOKEN_PTYPE, WHITESPACE_PTYPE, EMPTY_NODE
from DHParser.log import HistoryRecord
from DHParser.parse import Grammar, Parser, ParserError, ParseFunc

__all__ = ('trace_history', 'all_descendants', 'set_tracer',
           'resume_notices_on')


def add_resume_notice(parser, rest: StringView, err_node: Node) -> None:
    """Adds a resume notice to the error node with information about
    the reentry point and the parser."""
    if parser == parser._grammar.start_parser__:
        return
    call_stack = parser._grammar.call_stack__
    if len(call_stack) >= 2:
        i, N = -2, -len(call_stack)
        while i >= N and call_stack[i][0][0:1] in (':', '/', '"', "'", "`"):
            i -= 1
        if i >= N and i != -2:
            parent_info = "{}->{}".format(call_stack[i][0], call_stack[-2][0])
        else:
            parent_info = call_stack[-2][0]
    else:
        parent_info = "?"
    notice = Error('Resuming from parser {} with parser {} at point: {}'
                   .format(parser.pname or parser.ptype, parent_info, repr(rest[:10])),
                   parser._grammar.document_length__ - len(rest), Error.RESUME_NOTICE)
    parser._grammar.tree__.add_error(err_node, notice)


def trace_history(self: Parser, text: StringView) -> Tuple[Optional[Node], StringView]:
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
    parser_error = grammar.most_recent_error__
    if ((grammar.moving_forward__ or parser_error or (node and not self.anonymous))
            and (self.tag_name != WHITESPACE_PTYPE)):
        # TODO: Make dropping insignificant whitespace from history configurable
        errors = [parser_error.error] if parser_error else []  # type: List[Error]
        line_col = grammar.line_col__(text)
        nd = Node(node.tag_name, text[:delta]).with_pos(location) if node else None
        record = HistoryRecord(grammar.call_stack__, nd, rest, line_col, errors)
        if (not grammar.history__ or line_col != grammar.history__[-1].line_col
                or record.call_stack != grammar.history__[-1].call_stack[:len(record.call_stack)]):
            grammar.history__.append(record)
        if parser_error:
            if grammar.resume_notices__:
                add_resume_notice(self, rest, parser_error.node)
            grammar.most_recent_error__ = None
    grammar.moving_forward__ = False
    grammar.call_stack__.pop()

    return node, rest


def all_descendants(root: Parser) -> List[Parser]:
    """Returns a list with the parser `root` and all of its descendants."""
    descendants = []

    def visit(parser: Parser):
        descendants.append(parser)
    root.apply(visit)
    return descendants


# def with_unnamed_descendants(root: Parser) -> List[Parser]:
#     """Returns a list that contains the parser `root` and only unnamed parsers."""
#     descendants = [root]
#     for parser in root.sub_parsers():
#         if not parser.pname:
#             descendants.extend(with_unnamed_descendants(parser))
#     return descendants


def set_tracer(parsers: Union[Grammar, Parser, Iterable[Parser]], tracer: Optional[ParseFunc]):
    if isinstance(parsers, Grammar):
        if tracer is None:
            parsers.history_tracking__ = False
            parsers.resume_notices__ = False
        parsers = parsers.all_parsers__
    elif isinstance(parsers, Parser):
        parsers = [parsers]
    if parsers:
        pivot = next(parsers.__iter__())
        assert all(pivot.grammar == parser.grammar for parser in parsers)
        if tracer is not None:
            pivot.grammar.history_tracking__ = True
        for parser in parsers:
            if parser.ptype != ':Forward':
                parser.set_proxy(tracer)


def resume_notices_on(grammar: Grammar):
    grammar.history_tracking__ = True
    grammar.resume_notices__ = True
    set_tracer(grammar, trace_history)
