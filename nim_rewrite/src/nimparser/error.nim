{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}

import std/strformat

type
    ErrorCode* = uint16
    ErrorRef* = ref ErrorObj not nil
    ErrorOrNil* = ref ErrorObj
    ErrorObj* = object
      message*: string
      pos*: int32
      code*: ErrorCode
      line*: int32
      column*: int32
      length*: int32
      related*: seq[ErrorRef]
      origPos*: int32
      origDoc*: string

const
    NO_ERROR* = ErrorCode(0)
    A_NOTICE* = ErrorCode(1)
    A_WARNING* = ErrorCode(100)
    AN_ERROR* = ErrorCode(1000)
    A_FATALITY* = ErrorCode(10_000)

    MandatoryContinuation* = ErrorCode(1010)
    MandatoryContinuationAtEOF* = ErrorCode(1015)
    ParserStoppedBeforeEnd* = ErrorCode(1040)

    ErrorWhileRecovering* = ErrorCode(1301)
    # RecursionLimitReached* = ErrorCode(10_010)


proc init*(error: ErrorRef, message: string, pos: int32,
           code: ErrorCode=AN_ERROR,
           line: int32 = -1, column: int32 = -1, length: int32 = -1,
           related: seq[ErrorRef] = @[],
           origPos: int32 = -1, origDoc: string = ""): ErrorRef =
    assert pos >= 0
    error.message = message
    error.pos = pos
    error.code = code
    error.line = line
    error.column = column
    error.length = length
    error.related = related
    error.origPos = origPos
    error.origDoc = origDoc
    return error


template Error*(args: varargs[untyped]): ErrorRef =
    new(ErrorRef).init(args)


proc `$`*(error: ErrorRef): string =
  let code: uint16 = error.code.uint16
  if error.line >= 0:
    fmt"{error.line}:{error.column}:{code}:{error.message}"
  elif error.origPos >= 0:
    fmt"{error.origPos}:{code}:{error.message}"
  else:
    fmt"?:{error.pos}:{code}:{error.message}"
