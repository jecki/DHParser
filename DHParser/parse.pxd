#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

# cpdef copy_parser_base_attrs(src, duplicate)

cdef class Parser:
    cdef public str pname
    cdef public bint disposable
    cdef public bint drop_content
    cdef public str node_name
    cdef public object eq_class
    cdef public object _grammar
    cdef object visited
    cdef public object cycle_detection
    cdef public object _parse_proxy
    cdef str _symbol

    cpdef reset(self)
    # cpdef __call__(self, location)
    # def __add__(self, other)
    # def __or__(self, other)
    # cpdef _parse(self, int location)
    cpdef set_proxy(self, proxy)
    # cpdef sub_parsers(self)
    # cpdef descendants(self)
    # cpdef _apply(self, func, ptrail, flip)
    cpdef apply(self, func)

# cpdef mixin_comment(whitespace, str)

# cpdef mixin_nonempty(whitespace)

cdef class Grammar:
    cdef dict __dict__
    cdef public set all_parsers__
    cdef public object comment_rx__
    cdef public object start_parser__
    # cdef public object unconnected_parsers__
    # cdef public object resume_parsers__
    cdef bint _dirty_flag__
    cdef public bint history_tracking__
    cdef public bint suspend_memoization__
    cdef public bint flatten_tree__
    cdef public int max_parser_dropouts__
#    cdef public object root_parser__  # do not uncomment this!!!
    cdef public object tree__
    cdef public object document__
    cdef public str text__
    cdef public object _reversed__
    cdef public int document_length__
    cdef public list _document_lbreaks__
    cdef public object variables__
    cdef public list rollback__
    cdef public int last_rb__loc__
    cdef public list call_stack__
    cdef public list history__
    cdef public bint moving_forward__
    cdef public int farthest_failure__
    # cdef public object static_analysis_pending__
    # cdef public object static_analysis_errors__
    # cdef public object parser_names

cdef class PreprocessorToken(Parser):
    pass

cdef class Text(Parser):
    cdef public str text
    cdef public int len

cdef class RegExp(Parser):
    cdef public object regexp

cdef class Whitespace(RegExp):
    pass

cdef class CombinedParser(Parser):
    cdef public object _return_value
    cdef public object _return_values

    cpdef _return_value_no_optimization(self, node)
    cpdef _return_value_flatten(self, node)
    cpdef _return_values_no_tree_reduction(self, results)
    cpdef _return_values_flatten(self, results)
    cpdef _return_values_merge_treetops(self, results)
    cpdef _return_values_merge_leaves(self, results)

cdef class UnaryParser(CombinedParser):
    cdef public object parser

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

cdef class MandatoryNary(NaryParser):
    cdef public int mandatory
    cdef public object err_msgs
    cdef public object skip

cdef class Series(MandatoryNary):
    pass

cdef class Alternative(NaryParser):
    pass

# cpdef longest_match(strings, text, n)

cdef class TextAlternative(Alternative):
    cdef public object heads
    cdef public object indices
    cdef public int min_head_size

cdef class Interleave(MandatoryNary):
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
    cpdef _rollback_location(self, int location, int location)

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

cdef class Forward(UnaryParser):
    cdef public bint cycle_reached
    cdef public object recursion_counter