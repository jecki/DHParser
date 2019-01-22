#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython


# cdef class ParserBase:
#     cdef str name
#     cdef str ptype

# cdef class MockParser(ParserBase):
#     pass

# cdef class ZombieParser(MockParser):
#     pass 

# cdef class Node:
#     cdef object errors
#     cdef int _pos
#     cdef object _result
#     cdef str _content
#     cdef int _len
#     cdef object parser

# cdef class RootNode(Node):
#     pass
