
from typing import TYPE_CHECKING, List, TypeAlias, cast

if TYPE_CHECKING:
    from circularTyping2 import MyClass


def f(m: MyClass|None) -> MyClass:
    n = MyClass()  # this will fail!!!
    return n

x = cast(MyClass, 1)

type T = List[MyClass]

f(None)
