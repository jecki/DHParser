from enum import IntEnum
from typing import TypedDict, NotRequired, Literal

class Position(TypedDict):
    line: int
    character: int

class Range(TypedDict):
    start: Position
    end: Position

class SymbolTag(IntEnum):
    Deprecated = 1

SymbolTag = Literal[1]
SymbolKind = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]


class DocumentSymbol(TypedDict):
    name: str
    detail: NotRequired[str]
    kind: SymbolKind
    tags: NotRequired[list[SymbolTag]]
    deprecated: NotRequired[bool]
    range: Range
    selectionRange: Range
    children: NotRequired[list['DocumentSymbol']]

print(TypedDict, type(TypedDict))
print(DocumentSymbol, type(DocumentSymbol))
print(NotRequired, type(NotRequired))
print(DocumentSymbol.__required_keys__)

