#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

# cpdef copy_parser_attrs(src, duplicate)

cdef class Parser:
    cdef public str pname
    cdef public bint anonymous
    cdef public bint drop_content
    cdef public str tag_name
    cdef _grammar
    cdef object visited
    cdef object recursion_counter
    cdef object cycle_detection

    cpdef _parse(self, text)
    cpdef reset(self)
    # def __call__(self, text)
    # def __add__(self, other)
    # def __or__(self, other)
    cpdef _parse(self, text)
    cpdef _apply(self, func, flip)
    cpdef apply(self, func)

# cpdef mixin_comment(whitespace, str)

# cpdef mixin_noempty(whitespace)

cdef class Grammar:
    cdef dict __dict__
    cdef public set all_parsers__
    cdef public object comment_rx__
    cdef public object start_parser__
    cdef bint _dirty_flag__
    cdef public bint history_tracking__
    cdef public bint memoization__
    cdef public bint flatten_tree__
    cdef public int left_recursion_depth__
    cdef public int max_parser_dropouts__
#    cdef public object root_parser__  # do not uncomment this!!!
    cdef public object tree__
    cdef public object document__
    cdef public object _reversed__
    cdef public int document_length__
    cdef public list document_lbreaks__
    cdef public object variables__
    cdef public list rollback__
    cdef public int last_rb__loc__
    cdef public list call_stack__
    cdef public list history__
    cdef public bint moving_forward__
    cdef public set recursion_locations__
    cdef public int last_recursion_location__

cdef class PreprocessorToken(Parser):
    pass

cdef class Token(Parser):
    cdef public str text
    cdef public int len

cdef class RegExp(Parser):
    cdef public object regexp

cdef class Whitespace(RegExp):
    pass

cdef class MetaParser(Parser):
    cpdef _return_value(self, node)
    cpdef _return_values(self, results)

cdef class UnaryParser(MetaParser):
    cdef public object parser

cdef class NaryParser(MetaParser):
    cdef public object parsers

cdef class Option(UnaryParser):
    pass

cdef class ZeroOrMore(Option):
    pass

cdef class OneOrMore(UnaryParser):
    pass

cdef class Series(NaryParser):
    cdef public int mandatory
    cdef public object err_msgs
    cdef public object skip

cdef class Alternative(NaryParser):
    pass

cdef class AllOf(NaryParser):
    cdef public int num_parsers
    cdef public int mandatory
    cdef public object err_msgs
    cdef public object skip

cdef class SomeOf(NaryParser):
    pass

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

cdef class Capture(UnaryParser):
    pass

cdef class Retrieve(Parser):
    cdef public object symbol
    cdef public object filter

cdef class Pop(Retrieve):
    cdef public list values

cdef class Synonym(UnaryParser):
    pass

cdef class Forward(Parser):
    cdef public object parser
    cdef public bint cycle_reached
