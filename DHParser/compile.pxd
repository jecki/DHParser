#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

# cpdef visitor_name(node_name)

cdef class Compiler:
    cdef public object tree
    cdef public list path
    cdef public bint has_attribute_visitors
    cdef public bint forbid_returning_None
    cdef public bint _dirty_flag
    cdef public bint _debug
    cdef public set _debug_already_compiled
    cdef public list finalizers
    cdef public dict method_dict

    # cpdef fallback_compiler(self, node)
    cpdef compile(self, node)
