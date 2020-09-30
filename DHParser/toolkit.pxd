#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

cpdef isgenerictype(t)

@cython.locals(i=cython.int)
cpdef linebreaks(text)

@cython.locals(line=cython.int, column=cython.int, pos=cython.int)
cpdef line_col(object lbreaks, cython.int pos)

