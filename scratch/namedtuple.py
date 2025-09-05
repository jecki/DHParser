from typing import NamedTuple

class T(NamedTuple):
    a: int
    b: str = 'abc'


x = T(42, "hello")

print(x)
