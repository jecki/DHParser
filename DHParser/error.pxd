#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

@cython.locals(i=cython.int)
cpdef linebreaks(test)

@cython.locals(line=cython.int, column=cython.int)
cpdef line_col(lbreaks, pos)

