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

from DHParser.error import Error, RESUME_NOTICE
from DHParser.stringview import StringView
from DHParser.syntaxtree import Node, REGEXP_PTYPE, TOKEN_PTYPE, WHITESPACE_PTYPE, ZOMBIE_TAG
from DHParser.log import freeze_callstack, HistoryRecord
from DHParser.parse import Grammar, Parser, ParserError, ParseFunc
from DHParser.toolkit import cython, line_col

__all__ = ('trace_history', 'all_descendants', 'set_tracer',
           'resume_notices_on')


@cython.locals(location=cython.int, loc=cython.int, delta=cython.int, cs_len=cython.int)
def trace_history(self: Parser, text: StringView) -> Tuple[Optional[Node], StringView]:
    grammar = self._grammar  # type: Grammar
    location = grammar.document_length__ - text._len  # type: int

    if grammar.most_recent_error__:
        # add resume notice (mind that skip notices are added by
        # `parse.MandatoryElementsParser.mandatory_violation()`
        mre = grammar.most_recent_error__  # type: ParserError
        grammar.most_recent_error__ = None
        errors = [mre.error]  # type: List[Error]
        text_ = grammar.document__[mre.error.pos:]
        lc = line_col(grammar.document_lbreaks__, mre.error.pos)
        resume_pos = self.grammar.document_length__ - len(text)
        target = text if len(text) <= 10 else text[:7] + '...'

        resumers = [grammar.call_stack__[-1][0]]
        i = 2;  L = len(grammar.call_stack__)
        while resumers[-1].startswith(':') and i <= len(grammar.call_stack__):
            resumers.append(grammar.call_stack__[-i][0])
            i += 1
        resumer = '->'.join(reversed(resumers))

        if mre.first_throw:
            notice = Error(  # resume notice
                'Resuming from parser "{}" at position {}:{} with parser "{}": {}'
                .format(mre.node.tag_name, *lc, resumer, repr(target)),
                resume_pos, RESUME_NOTICE)
        else:
            notice = Error(  # skip notice
                'Skipping from position {}:{} within parser {}: {}'
                .format(*lc, resumer, repr(target)), resume_pos, RESUME_NOTICE)
        if grammar.resume_notices__:
            grammar.tree__.add_error(mre.node, notice)
        errors.append(notice)
        grammar.history__.append(HistoryRecord(
            getattr(mre, 'frozen_callstack', grammar.call_stack__), mre.node, text_,
            line_col(grammar.document_lbreaks__, mre.error.pos), errors))

    grammar.call_stack__.append(
        (((' ' + self.repr) if self.tag_name in (REGEXP_PTYPE, TOKEN_PTYPE, ":Retrieve", ":Pop")
          else (self.pname or self.tag_name)), location))  # ' ' added to avoid ':' as first char!
    grammar.moving_forward__ = True

    try:
        node, rest = self._parse(text)   # <===== call to the actual parser!
    except ParserError as pe:
        if pe.first_throw:
            pe.frozen_callstack = freeze_callstack(grammar.call_stack__)
            grammar.most_recent_error__ = pe
        if self == grammar.start_parser__ and grammar.most_recent_error__:
            fe = grammar.most_recent_error__  # type: ParserError
            lc = line_col(grammar.document_lbreaks__, fe.error.pos)
            # TODO: get the call stack from when the error occurred, here
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
        hnd = Node(node.tag_name, text[:delta]).with_pos(location) if node else None
        lc = line_col(grammar.document_lbreaks__, location)
        record = HistoryRecord(grammar.call_stack__, hnd, rest, lc, [])
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

    def visit(context: List[Parser]):
        descendants.append(context[-1])
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
