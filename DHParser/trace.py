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

from DHParser.error import Error, line_col
from DHParser.stringview import StringView
from DHParser.syntaxtree import Node, REGEXP_PTYPE, TOKEN_PTYPE, WHITESPACE_PTYPE, ZOMBIE_TAG
from DHParser.log import freeze_callstack, HistoryRecord
from DHParser.parse import Grammar, Parser, ParserError, ParseFunc

__all__ = ('trace_history', 'all_descendants', 'set_tracer',
           'resume_notices_on')


def trace_history(self: Parser, text: StringView) -> Tuple[Optional[Node], StringView]:
    grammar = self._grammar
    location = grammar.document_length__ - text._len

    if grammar.most_recent_error__:
        # add resume notice (mind that skip notices are added by
        # `parse.MandatoryElementsParser.mandatory_violation()`
        pe = grammar.most_recent_error__
        grammar.most_recent_error__ = None

        errors = [pe.error]
        # ignore inflated length due to gap jumping (see parse.Parser.__call__)
        l = sum(len(nd) for nd in pe.node.select_if(lambda n: True, include_root=True)
                if not nd.children and nd.tag_name != ZOMBIE_TAG)
        text_ = pe.rest[l:]
        lc = line_col(grammar.document_lbreaks__, pe.error.pos)
        target = text
        if len(target) >= 10:
            target = target[:7] + '...'
        if pe.first_throw:
            # resume notice
            notice = Error('Resuming from parser "{}" with parser "{}" at point: {}'
                           .format(pe.node.tag_name, grammar.call_stack__[-1][0],
                                   repr(target)),
                           grammar.document_length__ - len(text_), Error.RESUME_NOTICE)
        else:
            # skip notice
            notice = Error('Skipping within parser {} to point {}'
                           .format(grammar.call_stack__[-1][0], repr(target)),
                           self._grammar.document_length__ - len(text_), Error.RESUME_NOTICE)
        if grammar.resume_notices__:
            grammar.tree__.add_error(pe.node, notice)
        errors.append(notice)
        grammar.history__.append(HistoryRecord(
            getattr(pe, 'frozen_callstack', grammar.call_stack__), pe.node, text_, lc, errors))

    grammar.call_stack__.append(
        ((self.repr if self.tag_name in (REGEXP_PTYPE, TOKEN_PTYPE)
          else (self.pname or self.tag_name)), location))
    grammar.moving_forward__ = True

    try:
        node, rest = self._parse(text)   # <===== call to the actual parser!
    except ParserError as pe:
        if pe.first_throw:
            pe.frozen_callstack = freeze_callstack(grammar.call_stack__)
            grammar.most_recent_error__ = pe
        if self == grammar.start_parser__:
            fe = grammar.most_recent_error__
            lc = line_col(grammar.document_lbreaks__, fe.error.pos)
            # TODO: get the call stack from when the error occured, here
            nd = fe.node
            grammar.history__.append(
                HistoryRecord(grammar.call_stack__, nd, fe.rest[len(nd):], lc, [fe.error]))
        grammar.call_stack__.pop()
        raise pe

    # Mind that memoized parser calls will not appear in the history record!
    # Don't track returning parsers except in case an error has occurred!

    if ((grammar.moving_forward__ or (node and not self.anonymous))
            and (self.tag_name != WHITESPACE_PTYPE)):
        # record history
        # TODO: Make dropping insignificant whitespace from history configurable
        delta = text._len - rest._len
        nd = Node(node.tag_name, text[:delta]).with_pos(location) if node else None
        lc = line_col(grammar.document_lbreaks__, location)
        record = HistoryRecord(grammar.call_stack__, nd, rest, lc, [])
        cs_len = len(record.call_stack)
        if (not grammar.history__ or lc != grammar.history__[-1].line_col
                or record.call_stack != grammar.history__[-1].call_stack[:cs_len]
                or self == grammar.start_parser__):
            grammar.history__.append(record)

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
