#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8


cdef class Node:
    cdef public int _pos
    cdef public object _result
    cdef public tuple _children
    cdef public str name
    cdef public object _attributes

    # cpdef equals(self, other, ignore_attr_order)
    # cpdef get(self,  index_or_tagname, surrogate)
    # cpdef anonymous(self)
    # cpdef result(self)
    cpdef _set_result(self, result)
    cpdef _leaf_data(self)
    # cpdef pos(self)
    cpdef object with_pos(self, pos)
    # cpdef has_attr(self, attr)
    # cpdef attr(self)
    # cpdef get_attr(self, attribute, default)
    # cpdef has_equal_attr(self, other)
    # cpdef index(self, what, start, stop)
    # cpdef select_if(self, match_function, include_root, reverse)
    # cpdef select(self, criterion, include_root)
    # cpdef select_children(self, criterion)
    # cpdef pick(self, criterion, reverse)
    # cpdef locate(self, location)
    # cpdef find_parend(self, node)
    # cpdef select_path_if(self, match_function, include_root, reverse)
    # cpdef select_path(self, criterion, include_root)
    # cpdef pick_content(self, criterion, reverse)
    # cpdef locate_content(self, location)
    # cpdef _reconstruct_path_recursive(self, node)
    # cpdef reconstruct_path(self, node)
    # cpdef milestone_segment(self, begin, end)
    # cdef evaluate(self, actions)
    # cpdef _tree_repr(self, tab, open_fn, close_fn, data_fn, density, inline, inline_fn)
    # cpdef as_sxpr(self, src, indentation, compact)
    # cpdef as_xml(self, src, indentation, inline_tags, string_tags, empty_tags)
    cpdef to_json_obj(self)
    # cpdef serialize(self, how)


cdef class FrozenNode(Node):
    cpdef object with_pos(self, pos)


cdef class RootNode(Node):
    cdef public list errors
    cdef public object _error_set
    cdef public object error_nodes
    cdef public object error_positions
    cdef public int error_flag
    cdef public str source
    cdef public object source_mapping
    cdef public list lbreaks
    cdef public set inline_tags
    cdef public set string_tags
    cdef public set empty_tags
    cdef public str docname
    cdef public str stage
    cdef public str serialization_type
    cdef public object data


