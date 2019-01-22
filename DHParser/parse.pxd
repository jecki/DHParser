#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

# cdef class ParserError(Exception):
#     cdef bint first_throw

# cdef add_parser_guard(parser_func)

# cdef class Parser(syntaxtree.ParserBase):
#     pass

# cdef class Grammar:
#     cdef bint dirty_flag__
#     cdef bint history_tracking__
#     cdef bint memoization__
#     cdef bint left_recursion_handling__
#     cdef int document_length__
#     cdef int last_rb__loc__
#     cdef bint moving_forward__

# cdef class PreprocessorToken(Parser):
#     pass
#
# cdef class Token(Parser):
#     cdef int len
#
# cdef class RegExp(Parser):
#     pass
#
# cdef class Whitespace(RegExp):
#     pass
#
# cdef class UnaryOperator(Parser):
#     pass
#
# cdef class NaryOperator(Parser):
#     pass
#
# cdef class Option(UnaryOperator):
#     pass
#
# cdef class ZeroOrMore(Option):
#     pass
#
# cdef class OneOrMore(UnaryOperator):
#     pass
#
# cdef class Series(NaryOperator):
#     cdef int mandatory
#
# cdef class Alternative(NaryOperator):
#     pass
#
# cdef class SomeOf(NaryOperator):
#     pass
#
# cdef class AllOf(NaryOperator):
#     cdef int mandatory
#     cdef int num_parsers
#
# cdef class FlowOperator(UnaryOperator):
#     pass
#
# # cdef class Required(FlowOperator):
# #     pass
#
# cdef class Lookahead(FlowOperator):
#     pass
#
# cdef class NegativeLookahead(Lookahead):
#     pass
#
# cdef class Lookbehind(FlowOperator):
#     pass
#
# cdef class NegativeLookbehind(Lookbehind):
#     pass
#
# cdef class Capture(UnaryOperator):
#     pass
#
# cdef class Retrieve(Parser):
#     pass
#
# cdef class Pop(Retrieve):
#     pass
#
# cdef class Synonym(UnaryOperator):
#     pass
#
# cdef class Forward(Parser):
#     pass

