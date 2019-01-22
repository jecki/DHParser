#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

cdef class Error:
    cdef str message
    cdef int _pos
    cdef object code
    cdef int orig_pos
    cdef int line
    cdef int column
