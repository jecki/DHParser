import cython

# type hints for Cython python -> C compiler to speed up the most
# critical code paths of stringview.py.

cdef int first_char(text, int begin, int end)

cdef int last_char(text, int begin, int end)

cdef int pack_index(int index, int length)

@cython.locals(cbegin=cython.int, cend=cython.int)
cpdef real_indices(begin, end, int length)

