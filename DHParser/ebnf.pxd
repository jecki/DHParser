#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8


cdef class EBNFDirectives:
    cdef public str whitespace
    cdef public str comment
    cdef public set literalws
    cdef public set tokens
    cdef public dict filter
    cdef public dict error
    cdef public dict skip
    cdef public dict resume
    cdef public str disposable
    cdef public set drop
    cdef public int reduction
    cdef public object _super_ws


# cdef class EBNFCompiler:
#     cdef public int grammar_id
#    cdef str _result
#    cdef public set re_flags
#    cdef public object rules
#    cdef public list current_symbols
#    cdef public dict symbols
#    cdef public set variables
#    cdef public set recursive
#    cdef public dict definitions
#    cdef public set required_keywords
#    cdef public list deferred_tasks
#    cdef public str root_symbol
#    cdef public object directives
#    cdef public set defined_directives
#    cdef public set consumed_custom_errors
#    cdef public set consumed_skip_rules

#    cpdef _check_rx(self, node, rx)
#    cpdef non_terminal(self, node, parser_class, custom_args)
#    cpdef _error_customization(self, node)
