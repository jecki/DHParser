#cython: infer_types=True
#cython: language_level=3str
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

# type hints for Cython python -> C compiler to speed up the most
# critical code paths of stringview.py.
# see https://cython.readthedocs.io/en/latest/src/tutorial/pure.html

cdef int first_char(str text, int begin, int end, str chars)

cdef int last_char(str text, int begin, int end, str chars)

cdef int pack_index(int index, int length)

cdef (int, int) fast_real_indices(begin, end, int length)

cdef class StringView:
    cdef public str _text
    cdef public int _begin
    cdef public int _end
    cdef readonly int _len
    cdef str _fullstring


cdef class TextBuffer:
    cdef object _text
    cdef object _buffer
    cdef public int version
