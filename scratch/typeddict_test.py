try:
    from typing import TypedDict, Optional
except ImportError:
    class TypedDict:
        pass

class Point(TypedDict, total=False):
    x: int
    y: Optional[int]

if __name__ == '__main__':
    p = Point(x=1)
