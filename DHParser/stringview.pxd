#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8


import cython

# type hints for Cython python -> C compiler to speed up the most
# critical code paths of stringview.py.

cdef int first_char(text, int begin, int end)

cdef int last_char(text, int begin, int end)

cdef int pack_index(int index, int length)

@cython.locals(cbegin=cython.int, cend=cython.int)
cdef real_indices(begin, end, int length)
# cpdef real_indices(begin, end, int length)


# cdefs for class StringView: https://cython.readthedocs.io/en/latest/src/tutorial/pure.html

cdef class StringView:
    cdef str text
    cdef int begin, end, len
    cdef str fullstring

    cpdef __init__(self, text: str, begin: Optional[int] = 0, end: Optional[int] = None) -> None

    cpdef __bool__(self) -> bool

    cpdef __len__(self) -> int

    cpdef __str__(self) -> str

    cpdef __eq__(self, other) -> bool

    cpdef __hash__(self) -> int

    cpdef __add__(self, other) -> Union[str, 'StringView']

    cpdef __radd__(self, other) -> Union[str, 'StringView']

    @cython.locals(start=cython.int, stop=cython.int)
    cpdef __getitem__(self, index: Optional[slice, int]) -> StringView

    cpdef count(self, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int

    cpdef find(self, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int

    cpdef rfind(self, sub: str, start: Optional[int] = None, end: Optional[int] = None) -> int

    cpdef startswith(self, prefix: str, start: int = 0, end: Optional[int] = None) -> bool

    cpdef endswith(self, suffix: str, start: int = 0, end: Optional[int] = None) -> bool

    cpdef match(self, regex, flags=0)

    cpdef index(self, absolute_index: int) -> int

    cpdef indices(self, absolute_indices: Iterable[int]) -> Tuple[int, ...]

    cpdef search(self, regex)

    cpdef finditer(self, regex)

    @cython.locals(begin=cython.int, end=cython.int)
    cpdef strip(self)

    @cython.locals(begin=cython.int)
    cpdef lstrip(self)

    @cython.locals(end=cython.int)
    cpdef rstrip(self)

    @cython.locals(length=cython.int, k=cython.int, i=cython.int)
    cpdef split(self, sep=None)

    cpdef replace(self, old, new)