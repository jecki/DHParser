{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}

type
    ErrorCode* = distinct int16
    ErrorRef* = ref ErrorObj not nil
    ErrorOrNil* = ref ErrorObj
    ErrorObj = object 
      message: string
      pos: int32
      code: ErrorCode
      line: int32
      column: int32
      length: int32
      related: seq[ErrorRef]
      origPos: int32
      origDoc: string

const
    NO_ERROR* = ErrorCode(0)
    A_NOTICE* = ErrorCode(1)
    A_WARNING* = ErrorCode(100)
    AN_ERROR* = ErrorCode(1000)
    A_FATALITY* = ErrorCode(10_000)

    RecursionLimitReached* = ErrorCode(10_010)


proc init*(error: ErrorRef, message: string, pos: int32,
           code: ErrorCode=AN_ERROR,
           line: int32 = -1, column: int32 = -1, length: int32 = -1,
           related: seq[ErrorRef] = @[],
           origPos: int32 = -1, origDoc: string = ""): ErrorRef = 
    error.message = message
    error.pos = pos
    error.line = line
    error.column = column
    error.length = length
    error.related = related
    error.origPos = origPos
    error.origDoc = origDoc
    return error


template Error*(args: varargs[untyped]): ErrorRef =
    new(ErrorRef).init(args)




