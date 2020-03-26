#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

# cpdef issubtype(subtype, base_type)
cpdef isgenerictype(t)

@cython.locals(i=cython.int)
cpdef linebreaks(text)

@cython.locals(line=cython.int, column=cython.int, pos=cython.int)
cpdef (cython.int, cython.int) line_col(object lbreaks, cython.int.pos)

@cython.locals(line=cython.int, column=cython.int, i=cython.int)
cpdef cython.int text_pos(object text, cython.int line, cython.int column, object lbreaks)

