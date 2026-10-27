#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8
#cython: subinterpreters_compatible = own_gil

import cython
from Cython.Compiler.Parsing import p_assert_statement
from DHParser.parse_base cimport Parser, LeafParser, NoMemoizationParser

# cpdef copy_parser_base_attrs(src, duplicate)



cdef class PreprocessorToken(LeafParser):
    pass

cdef class Text(NoMemoizationParser):
    cdef public str text
    cdef public int len

cdef class RegExp(LeafParser):
    cdef public object regexp

cdef class Whitespace(RegExp):
    cdef public bint keep_comments

cdef class CombinedParser(Parser):
    cdef public object _return_value
    cdef public object _return_values

    cpdef _return_value_no_optimization(self, node)
    cpdef _return_value_flatten(self, node)
    cpdef _return_values_no_tree_reduction(self, results)
    cpdef _return_values_flatten(self, results)
    cpdef _return_values_merge_treetops(self, results)
    cpdef _return_values_merge_leaves(self, results)

cdef class SmartRE(CombinedParser):
    cdef public str repr_str
    cdef public object groups
    cdef public str pattern
    cdef public object is_lookahead_
    cdef public object regexp

cdef class UnaryParser(CombinedParser):
    cdef public object parser


cdef class LateBindingUnary(UnaryParser):
    cdef public str parser_name

cdef class NaryParser(CombinedParser):
    cdef public object parsers


cdef class Option(UnaryParser):
    pass

cdef class ZeroOrMore(Option):
    pass

cdef class OneOrMore(UnaryParser):
    pass

cdef class Counted(UnaryParser):
    cdef public (int, int) repetitions

cdef class ErrorCatchingNary(NaryParser):
    cdef public int mandatory
    cdef public object err_msgs
    cdef public object skip

cdef class Series(ErrorCatchingNary):
    pass

cdef class Alternative(NaryParser):
    pass

# cpdef longest_match(strings, text, n)

cdef class TextAlternative(Alternative):
    cdef public object heads
    cdef public object indices
    cdef public int min_head_size

cdef class Interleave(ErrorCatchingNary):
    cdef public object repetitions
    cdef public object non_mandatory
    cdef public object parsers_set

cdef class FlowParser(UnaryParser):
    pass

cdef class Lookahead(FlowParser):
    pass

cdef class NegativeLookahead(Lookahead):
    pass

cdef class Lookbehind(FlowParser):
    cdef public object regexp
    cdef public str text

cdef class NegativeLookbehind(Lookbehind):
    pass

cdef class BlackHoleDict(dict):
    pass

cdef class ContextSensitive(UnaryParser):
    cpdef _rollback_location(self, int location, int location_)

cdef class Capture(ContextSensitive):
    cdef public bint zero_length_warning
    cdef public object _can_capture_zero_length

cdef class Retrieve(ContextSensitive):
    cdef public object filter
    cdef public object match

cdef class Pop(Retrieve):
    cdef public list values

cdef class Synonym(UnaryParser):
    pass

cdef class ForwardBase(UnaryParser):
    cdef public bint cycle_reached

cdef class Forward(ForwardBase):
    cdef public object seed
    cdef public object versions
    cdef public object iteration
    cdef public int farthest

    cdef public object tracer_memo
    cdef public object tracer_init
    cdef public object tracer_loop
    cdef public object tracer_done

cdef class SimpleForward(ForwardBase):
    pass

cdef class SimpleForwardIterative(ForwardBase):
    cdef public object recursion_counter
