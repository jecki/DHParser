import cython


# type hints for Cython python -> C compiler


cdef int first_char(text, int begin, int end)

cdef int last_char(text, int begin, int end)

cdef inline int pack_index(int index, int len)

@cython.locals(cbegin=cython.int, cend=cython.int)
cpdef real_indices(begin, end, int len)
