#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8


cdef class Node:
    cdef public list errors
    cdef public int _pos
    cdef public object _result
    cdef str _content
    cdef public tuple children
    cdef public int _len
    cdef public str tag_name
    cdef object _xml_attr

cdef class RootNode(Node):
    cdef public list all_errors
    cdef public int error_flag
    cdef public set inline_tags
    cdef public set omit_tags
    cdef public set empty_tags
