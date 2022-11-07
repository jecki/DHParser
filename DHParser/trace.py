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

from __future__ import annotations

from typing import Tuple, Optional, List, Iterable, Union

try:
    import cython
    cint = cython.int
except NameError:
    cint = int
except ImportError:
    import DHParser.externallibs.shadow_cython as cython
    cint = int

from DHParser.error import Error, RESUME_NOTICE, RECURSION_DEPTH_LIMIT_HIT
from DHParser.nodetree import Node, REGEXP_PTYPE, TOKEN_PTYPE, WHITESPACE_PTYPE
from DHParser.log import HistoryRecord
from DHParser.parse import Grammar, Parser, ParserError, ParseFunc, ContextSensitive
from DHParser.toolkit import line_col

__all__ = ('trace_history', 'all_descendants', 'set_tracer',
           'resume_notices_on', 'resume_notices_off')


def symbol_name(parser: Parser, grammar: Grammar) -> str:
    name = str(parser) if isinstance(parser, ContextSensitive) else parser.node_name
    # name = parser.name
    if name[:1] == ':':
        name = grammar.associated_symbol__(parser).pname + '->' + name
    return name


@cython.locals(location_=cython.int, delta=cython.int, cs_len=cython.int,
               i=cython.int, L=cython.int)
def trace_history(self: Parser, location: cint) -> Tuple[Optional[Node], cint]:
    grammar = self._grammar  # type: Grammar
    if not grammar.history_tracking__:
        try:
            node, location = self._parse(location)  # <===== call to the actual parser!
        except ParserError as pe:
            raise pe
        return node, location

    mre: Optional[ParserError] = grammar.most_recent_error__
    if mre is not None and location >= mre.error.pos:
        # add resume notice (mind that skip notices are added by
        # `parse.MandatoryElementsParser.mandatory_violation()`
        if mre.error.code == RECURSION_DEPTH_LIMIT_HIT:
            return mre.node, location

        grammar.most_recent_error__ = None
        errors = [mre.error]  # type: List[Error]
        text_ = grammar.document__[mre.error.pos:]
        orig_lc = line_col(grammar.document_lbreaks__, mre.error.pos)
        orig_snippet= text_ if len(text_) <= 10 else text_[:7] + '...'
        # orig_snippet = orig_rest if len(orig_rest) <= 10 else orig_rest[:7] + '...'
        target_lc = line_col(grammar.document_lbreaks__, location)
        target_text_ = grammar.document__[location:]
        target_snippet = target_text_ if len(target_text_) <= 10 else target_text_[:7] + '...'
        # target = text if len(text) <= 10 else text[:7] + '...'

        if mre.first_throw:
            # origin = callstack_as_str(mre.callstack_snapshot, depth=3)
            # resumer = callstack_as_str(grammar.call_stack__, depth=3)
            origin = symbol_name(mre.parser, grammar)
            resumer = symbol_name(self, grammar)
            notice = Error(  # resume notice
                'Resuming from {} at {}:{} {} with {} at {}:{} {}'
                .format(origin, *orig_lc, repr(orig_snippet),
                        resumer, *target_lc, repr(target_snippet)),
                location, RESUME_NOTICE)
        else:
            origin = symbol_name(self, grammar)
            notice = Error(  # skip notice
                'Skipping from {}:{} {} within {} to {}:{} {}'
                .format(*orig_lc, repr(orig_snippet), origin,
                        *target_lc, repr(target_snippet)),
                location, RESUME_NOTICE)
        if grammar.resume_notices__:
            grammar.tree__.add_error(mre.node, notice)
        errors.append(notice)
        grammar.history__.append(HistoryRecord(
            getattr(mre, 'callstack_snapshot', grammar.call_stack__), mre.node, text_,
            line_col(grammar.document_lbreaks__, mre.error.pos), errors))

    grammar.call_stack__.append(
        (((' ' + self.repr) if self.node_name in (REGEXP_PTYPE, TOKEN_PTYPE, ":Retrieve", ":Pop")
          else (self.pname or self.node_name)), location))  # ' ' added to avoid ':' as first char!
    grammar.moving_forward__ = True

    doc = self.grammar.document__
    try:
        node, location_ = self._parse(location)   # <===== call to the actual parser!
    except ParserError as pe:
        if pe.first_throw:
            pe.callstack_snapshot = grammar.call_stack__.copy()
            grammar.most_recent_error__ = pe
        if self == grammar.start_parser__ and grammar.most_recent_error__:
            fe = grammar.most_recent_error__  # type: ParserError
            lc = line_col(grammar.document_lbreaks__, fe.error.pos)
            # TODO: get the call stack from when the error occurred, here
            nd = fe.node
            grammar.history__.append(
                HistoryRecord(grammar.call_stack__, nd, doc[fe.location + nd.strlen():],
                              lc, [fe.error]))
        grammar.call_stack__.pop()
        raise pe

    # Mind that memoized parser calls will not appear in the history record!
    # Don't track returning parsers except in case an error has occurred!
    if ((self.node_name != WHITESPACE_PTYPE)
        and (grammar.moving_forward__
             or (not self.disposable
                 and (node
                      or grammar.history__ and grammar.history__[-1].node)))):
        # record history
        # TODO: Make dropping insignificant whitespace from history configurable
        hnd = Node(node.name, doc[location:location_]).with_pos(location) if node else None
        lc = line_col(grammar.document_lbreaks__, location)
        record = HistoryRecord(grammar.call_stack__, hnd, doc[location_:], lc, [])
        cs_len = len(record.call_stack)
        if (not grammar.history__ or not node
                or lc != grammar.history__[-1].line_col
                or record.call_stack != grammar.history__[-1].call_stack[:cs_len]
                or self == grammar.start_parser__):
            grammar.history__.append(record)

    grammar.moving_forward__ = False
    grammar.call_stack__.pop()
    return node, location_


def all_descendants(root: Parser) -> List[Parser]:
    """Returns a list with the parser `root` and all of its descendants."""
    descendants = []

    def visit(trail: List[Parser]):
        descendants.append(trail[-1])
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


def resume_notices_off(grammar: Grammar):
    """Turns off resume-notices as well as history tracking!"""
    set_tracer(grammar, None)
