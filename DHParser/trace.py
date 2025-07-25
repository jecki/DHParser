# trace.py - tracing of the parsing process (for debugging) and
#            interrupting long running parser processes.
#
# Copyright 2018  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""
Module ``trace`` provides trace-debugging functionality for the
parser. The tracers are added or removed via monkey patching to
all or some parsers of a grammar and trace the actions
of these parsers, making use of the `call_stack__`, `history__`
and `moving_forward__`, `most_recent_error__`-hooks in the
Grammar-object.

This functionality can be used for several purposes:

1. "live" or "breakpoint"-debugging (not implemented)

2. recording of parsing history and "post-mortem"-debugging,
   implemented here and in module :py:mod:`log`

3. Interrupting long-running parser processes by polling
   a threading.Event or multiprocessing.Event once in a while
"""


from __future__ import annotations

from typing import Tuple, Optional, List, Iterable, Union, cast

try:
    import cython
except ImportError:
    import DHParser.externallibs.shadow_cython as cython

from DHParser.error import Error, RESUME_NOTICE, RECURSION_DEPTH_LIMIT_HIT
from DHParser.nodetree import Node, REGEXP_PTYPE, TOKEN_PTYPE, WHITESPACE_PTYPE
from DHParser.log import HistoryRecord, NONE_NODE
from DHParser.parse import Grammar, Parser, ParserError, ParseFunc, ContextSensitive, \
    UnaryParser, SmartRE, cancel_proxy
from DHParser.toolkit import line_col, INFINITE

__all__ = ('trace_history', 'set_tracer', 'resume_notices_on', 'resume_notices_off')


#######################################################################
#
# Adding and removing tracers
#
#######################################################################


def set_tracer(parsers: Union[Grammar, Parser, Iterable[Parser]], tracer: Optional[ParseFunc]):
    """Adds or removes a tracing function to (or from) a single parser, a set of
    parsers or all parsers in a grammar.

    :param parsers: the parsers or single parser or grammar-object containing
        parsers where the ``tracer`` shall be added or removed.
    :param tracer: a tracer function or ``None``. If ``None`` any existing
        tracer will be removed. If not None, tracer must be a parsing function.
        It is up to the tracer to call the original parsing function
        (``self._parse()``).
    """
    if isinstance(parsers, Grammar):
        if tracer is None:
            parsers.history_tracking__ = False
            parsers.resume_notices__ = False
        parsers = parsers.all_parsers__
    elif isinstance(parsers, Parser):
        parsers = [parsers]
    if parsers:
        pivot = next(iter(parsers))
        assert all(pivot._grammar == parser._grammar for parser in parsers)
        if tracer is None:
            pivot._grammar.history_tracking__ = False
            pivot._grammar.resume_notices__ = False
        else:
            pivot._grammar.history_tracking__ = True
            pivot._grammar.resume_notices__ = True
        for parser in parsers:
            if parser.ptype != ':Forward':
                parser.set_proxy(tracer)


#######################################################################
#
# History-Recording for post-mortem debugging
#
#######################################################################


def symbol_name(parser: Parser, grammar: Grammar) -> str:
    name = str(parser) if isinstance(parser, ContextSensitive) else parser.node_name
    # name = parser.name
    if name[:1] == ':':
        name = grammar.associated_symbol__(parser).pname + '->' + name
    return name


def result_changed(node, history) -> bool:
    current_result = node is None
    if history:
        last_result = history[-1].node is NONE_NODE
    else:
        return False
    return last_result != current_result


def call_item(parser: Parser, location: int, prefix: str = '') -> Tuple[str, int]:
    if parser.node_name in (REGEXP_PTYPE, TOKEN_PTYPE, ":Retrieve", ":Pop",
                            ":SmartRE", ":SmartRE_Lookahead"):
        return f"{' ' or prefix}{parser.repr}", location  # ' ' added to avoid ':' as first char!
    else:
        name = parser.pname or parser.node_name
        if isinstance(parser, SmartRE) and parser.is_lookahead():
            name += ":SmartRE_Lookahead"
        return f"{prefix}{name}", location


def history_record(parser: Parser, grammar: Grammar,
                   node: Node,
                   location: int,
                   location_: int,
                   prefix: str = '') -> HistoryRecord:
    doc = grammar.document__
    hnd = Node(node.name, doc[location:location_]).with_pos(location) if node else None
    lc = line_col(grammar.document_lbreaks__, location)
    errors = grammar.tree__.error_nodes.get(id(node), [])
    if parser.node_name[0:1] == ':' \
            and not (isinstance(parser, SmartRE) and parser.is_lookahead()):
        if parser.pname:
            grammar.call_stack__[-1] = (f"{prefix}{parser.pname}", location)
        else:
            grammar.call_stack__[-1] = (f"{prefix}{parser} ", location)
    return HistoryRecord(grammar.call_stack__, hnd, doc[location_:], lc, errors)


@cython.locals(location_=cython.int, delta=cython.int, cs_len=cython.int,
               i=cython.int, L=cython.int)
def trace_history(self: Parser, location: cython.int) -> Tuple[Optional[Node], cython.int]:
    grammar = self._grammar  # type: Grammar

    if not grammar.history_tracking__:
        if location < 0:
            if location <= -INFINITE:  location = 0
            return self.visited[-location]
        try:
            node, location = self._parse(location)  # <===== call to the actual parser!
        except ParserError as pe:
            raise pe
        return node, location

    if location < 0:  # a negative location signals a memo-hit. see parse.Parser.__call__() !!!
        if location <= -INFINITE:  location = 0
        location = -location
        grammar.call_stack__.append(call_item(self, location, "RECALL: "))
        node, location_ = self.visited[location]
        record = history_record(self, grammar, node, location, location_, "RECALL: ")
        grammar.history__.append(record)
        grammar.call_stack__.pop()
        return node, location_


    mre: Optional[ParserError] = grammar.most_recent_error__
    if mre is not None and location >= mre.error.pos:
        # add resume notice (mind that skip notices are added by
        # `parse.MandatoryElementsParser.mandatory_violation()`)
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

    grammar.call_stack__.append(call_item(self, location))
    stack_counter = 1
    if self.node_name in (":Lookbehind", ":NegativeLookbehind"):
        grammar.call_stack__.append((' ' + cast(UnaryParser, self).parser.repr, location))
        stack_counter += 1
    elif isinstance(self, SmartRE) and self.is_lookahead() \
            and not grammar.call_stack__[-1][0].endswith(':SmartRE_Lookahead'):
        grammar.call_stack__.append((' :SmartRE_Lookahead', location))
        stack_counter += 1
    grammar.moving_forward__ = True

    try:

        if grammar.cancel_query__ is not None:
            node, location = cancel_proxy(self, location)
        else:
#####################################################################################
            node, location_ = self._parse(location)   # <===== call to the actual parser!
#####################################################################################

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
                HistoryRecord(grammar.call_stack__, nd,
                              grammar.document__[fe.location + nd.strlen():],
                              lc, [fe.error]))
        while stack_counter > 0:
            grammar.call_stack__.pop()
            stack_counter -= 1
        raise pe

    except KeyboardInterrupt as ctrlC:
        lc = line_col(grammar.document_lbreaks__, location)
        grammar.history__.append(
            HistoryRecord(grammar.call_stack__, None,
                          grammar.document__[location:],
                          lc, [Error('KeyboardInterrupt (Ctrl-C)', location)]))
        raise ctrlC


    # Don't track returning parsers except in case an error has occurred!
    if ((self.node_name != WHITESPACE_PTYPE)
        and (grammar.moving_forward__
             or (not self.disposable
                 and (node and grammar.history__[-1].node))
             or result_changed(node, grammar.history__))):
        # record history
        # TODO: Make dropping insignificant whitespace from history configurable
        record = history_record(self, grammar, node, location, location_)
        cs_len = len(record.call_stack)
        if (not grammar.history__ or not node
                or record.line_col != grammar.history__[-1].line_col
                or record.call_stack != grammar.history__[-1].call_stack[:cs_len]
                or self == grammar.start_parser__):
            if len(record.call_stack) >= 2 and \
                    record.call_stack[-2][0] in (":Lookbehind", ":NegativeLookbehind"):
                record.text = grammar.reversed__[len(grammar.document__) - location_:]
            if not grammar.moving_forward__ \
                    and not any(tag in (':Lookahead', ":NegativeLookahead")
                                or tag.endswith(":SmartRE_Lookahead")
                                for tag, _ in grammar.history__[-1].call_stack):
                grammar.history__.pop()
            grammar.history__.append(record)


    grammar.moving_forward__ = False
    while stack_counter > 0:
        grammar.call_stack__.pop()
        stack_counter -= 1
    return node, location_


def resume_notices_on(grammar: Grammar):
    """Turns resume-notices as well as history tracking on!"""
    # grammar.history_tracking__ = True
    grammar.resume_notices__ = True
    set_tracer(grammar, trace_history)


def resume_notices_off(grammar: Grammar):
    """Turns resume-notices as well as history tracking off!"""
    set_tracer(grammar, None)


#######################################################################
#
# Interrupt-Polling
#
#######################################################################


