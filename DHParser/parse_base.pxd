#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8
#cython: subinterpreters_compatible = own_gil

import cython
from Cython.Compiler.Parsing import p_assert_statement

# cpdef copy_parser_base_attrs(src, duplicate)

cdef class Parser:
    cdef public str pname
    cdef public str ptype
    cdef public bint disposable
    cdef public bint drop_content
    cdef public str node_name
    cdef public object eq_class
    cdef public object _sub_parsers
    cdef public object _parse_proxy
    cdef public object _grammar
    cdef public object visited
    cdef public str _symbol
    cdef public object _descendants_cache
    cdef public object _anon_desc_cache
    cdef public object _desc_trails_cache

    cpdef reset(self)
    # cpdef __call__(self, location)
    # def __add__(self, other)
    # def __or__(self, other)
    # cpdef _parse(self, int location)
    cpdef set_proxy(self, proxy)
    # cpdef sub_parsers(self)
    # cpdef descendants(self)
    # cpdef descendant_trails(self)
    # cpdef _apply(self, func, ptrail, flip)
    # cpdef apply(self, func, grammar)

cdef class LeafParser(Parser):
    pass

cdef class NoMemoizationParser(LeafParser):
    pass

