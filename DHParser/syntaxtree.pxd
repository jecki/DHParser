#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8


cdef class Node:
    cdef public int _pos
    cdef public object _result
    cdef public tuple children
    cdef public int _len
    cdef public str tag_name
    cdef object _xml_attr

    cpdef get(self,  index_or_tagname, surrogate)
    cpdef is_anonymous(self)
    cpdef _content(self)
    cpdef with_pos(self, pos)
    # cpdef has_attr(self, attr)
    # cpdef compare_attr(self, other)
    # cpdef _tree_repr(self, tab, open_fn, close_fn, data_fn, density, inline, inline_fn)
    # cpdef as_sxpr(self, src, indentation, compact)
    # cpdef as_xml(self, src, indentation, inline_tags, omit_tags, empty_tags)
    # cpdef select_if(self, match_function, include_root, reverse)
    # cpdef select(self, tag_names, include_root)
    # cpdef pick(self, criterion, reverse)
    # cpdef tree_size(self)
    cpdef to_json_obj(self)


cdef class FrozenNode(Node):
    cpdef with_pos(self, pos)


cdef class RootNode(Node):
    cdef public list errors
    cdef public object error_nodes
    cdef public object error_positions
    cdef public int error_flag
    cdef public set inline_tags
    cdef public set omit_tags
    cdef public set empty_tags

    # cpdef swallow(self, node)
    # cpdef add_error(self, node, error)
    # cpdef new_error(self, node, message, code)
    # cpdef get_errors(self, node)
    cpdef customized_XML(self)
