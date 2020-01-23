#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8


cdef class Node:
    cdef public int _pos
    cdef public object _result
    cdef public tuple children
    cdef public str tag_name
    cdef public object _xml_attr

    # cpdef equals(self, other, ignore_attr_order)
    # cpdef get(self,  index_or_tagname, surrogate)
    # cpdef anonymous(self)
    # cpdef result(self)
    cpdef _set_result(self, result)
    cpdef _leaf_data(self)
    # cpdef pos(self)
    cpdef with_pos(self, pos)
    # cpdef has_attr(self, attr)
    # cpdef attr(self)
    # cpdef get_attr(self, attribute, default)
    # cpdef compare_attr(self, other)
    # cpdef index(self, what, start, stop)
    # cpdef select_if(self, match_function, include_root, reverse)
    # cpdef select(self, criterion, include_root)
    # cpdef select_children(self, criterion)
    # cpdef pick(self, criterion, reverse)
    # cpdef locate(self, location)
    # cpdef find_parend(self, node)
    # cpdef select_context_if(self, match_function, include_root, reverse)
    # cpdef select_context(self, criterion, include_root)
    # cpdef pick_content(self, criterion, reverse)
    # cpdef locate_content(self, location)
    # cpdef _reconstruct_context_recursive(self, node)
    # cpdef reconstruct_context(self, node)
    # cpdef milestone_segment(self, begin, end)
    # cpdef _tree_repr(self, tab, open_fn, close_fn, data_fn, density, inline, inline_fn)
    # cpdef as_sxpr(self, src, indentation, compact)
    # cpdef as_xml(self, src, indentation, inline_tags, omit_tags, empty_tags)
    cpdef to_json_obj(self)
    # cpdef serialize(self, how)


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


# cpdef parse_sxpr(sxpr)
# cpdef parse_xml(xml, ignore_pos)
