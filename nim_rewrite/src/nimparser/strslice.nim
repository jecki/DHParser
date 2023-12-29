# adapted from from: https://github.com/PMunch/strslice
# written by Peter Munch-Elligsen, MIT-Lizense

## This is an implementation of string slices that works on a common underlying
## string shared through a reference instead of copying parts of the string.
## This has the benefit of not requiring the time and memory of copying parts
## of the string over and over. The only thing that get's copied is the
## reference of the underlying string, and two new indices for the start and
## stop of the string slice. This means that by changing the original string,
## any string slice that was created from it will be updated as well. The
## benefit of using string slices comes when copying parts of the string to
## pass on, for example in a combinatorial parser.

{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}

import std/strutils

when defined(js):
  import std/jsre
else:
  import std/re


type
  # StringSliceRef* = ref StringSlice not nil
  StringSlice* = object
    buf: ref string not nil
    start: int32
    stop: int32

# proc ensureStrRef(): ref string not nil =
#   ## Create a new ref string object that is sure to be not nil.
#   new(result)
#   # var s: ref string = new(string)
#   # if not isNil(s):  return s

# proc ensureEmptyStrRef(): ref string not nil =
#   ## Create a new empty ref string that is sure to be not nil.
#   result = ensureStrRef()
#   result[] = ""

# let EmptyStrSlice* = StringSlice(buf: ensureEmptyStrRef(), start: 0, stop: -1)


proc makeStringSlice*(str: ref string or string): StringSlice =
  ## Create a new string slice that references the string. This creates a new
  ## reference to the string, so any changes to the underlying string will be
  ## visible in all slices made from this string.
  # new result
  when str is ref string:
    # result = new StringSlice
    StringSLice(buf: str, start: 0, stop: str.len.int32 - 1)
  else:
    var strRef: ref string not nil
    new(strRef)
    strRef[] = str
    StringSlice(buf: strRef, start: 0, stop: str.len.int32 - 1)


let EmptyStringSlice* = makeStringSlice("")


converter toStringSlice*(str: StringSlice or ref string or string): StringSlice  =
  ## Automatic converter to create a string slice from a string
  when str is StringSlice: str  else:  makeStringSlice(str)


proc `$`*(str: StringSlice): string =
  ## Converts a string slice to a string
  if str.stop < 0:  return ""
  return str.buf[str.start .. str.stop]

func str*(str: StringSlice): ref string not nil = str.buf

func first*(str: StringSlice): int32 = str.start

func last*(str: StringSlice): int32 = str.stop

proc high*(str: StringSlice): int32 =
  ## Get the highest index of a string slice
  str.stop - str.start

proc len*(str: StringSlice): int32 =
  ## Get the length of a string slice
  str.high + 1

proc `[]`*(str: StringSlice,
           slc: HSlice[int32, int32 or BackwardsIndex]): StringSlice =
  ## Grab a slice of a string slice. This returns a new string slice that
  ## references the same underlying string.
  if slc.a < 0:
    raise newException(IndexDefect, "index out of bounds")
  var stop: int32
  when slc.b is BackwardsIndex:
    if slc.b.int > str.len + 1:
      raise newException(RangeDefect, "value out of range: " &
        $(str.len + 1 - slc.b.int))
    stop = str.stop - slc.b.int32 + 1
  else:
    if slc.b + 1 < slc.a or slc.b > str.high:
      raise newException(IndexDefect, "index out of bounds")
    stop = str.start + slc.b
  StringSlice(buf: str.buf, start: str.start + slc.a, stop: stop)

proc `[]`*(str: StringSlice,
           slc: HSlice[int, int]): StringSlice {.inline.} =
  str[slc.a.int32 .. slc.b.int32]

proc `[]`*(str: StringSlice,
           slc: HSlice[int32, int]): StringSlice {.inline.} =
  str[slc.a .. slc.b.int32]

proc `[]`*(str: StringSlice,
           slc: HSlice[int, int32 or BackwardsIndex]): StringSlice {.inline.} =
  str[slc.a.int32 .. slc.b]


proc `&`*(sl1, sl2: StringSlice): StringSlice =
  ## Concatenate two string slices like the regular `&` operator does for
  ## strings. WARNING: This creates a new underlying string.
  makeStringSlice($sl1 & $sl2)

proc startsWith*[T: StringSlice or string](str: StringSlice, sub: T): bool =
  ## Compares a string slice with a string or another string slice of shorter or
  ## equal length. Returns true if the first string slice starts with the next.
  if sub.len > str.len: return false
  when T is StringSlice:
    for i in sub.start..sub.stop:
      if str.buf[i + str.start - sub.start] != sub.buf[i]: return false
  else:
    for idx, c in sub:
      if str.buf[idx + str.start] != c: return false
  return true

proc `==`*[T: StringSlice or string](str: StringSlice, cmp: T): bool =
  ## Compare a string slice to a string or another string slice. Returns true
  ## if they are both identical.
  if str.len != cmp.len: return false
  when T is StringSlice:
    for i in cmp.start..cmp.stop:
      if str.buf[i + str.start - cmp.start] != cmp.buf[i]: return false
    return true
  else:
    return str.startsWith(cmp)

proc find*(a: SkipTable, s: StringSlice, sub: string,
  start: Natural = 0, last: Natural = 0): int32 =
  ## Finds a string in a string slice. Calls the similar procedure from
  ## ``strutils`` but with updated start and last references.
  result = strutils.find(a, s.buf[], sub, start + s.start, last + s.start).int32 - s.start
  if result < 0 or result > s.stop - sub.high:
    result = -1

proc find*(s: StringSlice, sub: char,
  start: Natural = 0, last: Natural = 0): int32 =
  ## Finds a string in a string slice. Calls the similar procedure from
  ## ``strutils`` but with updated start and last references.
  result = strutils.find(s.buf[], sub, start + s.start, last + s.start).int32 - s.start
  if result < 0 or result > s.stop:
    result = -1

proc find*(s: StringSlice, sub: string,
  start: Natural = 0, last: Natural = 0): int =
  ## Finds a string in a string slice. Calls the similar procedure from
  ## ``strutils`` but with updated start and last references.
  result = strutils.find(s.buf[], sub, start + s.start, s.start + (if last == 0: s.stop - s.start else: last.int32)) - s.start
  if result < 0 or result > s.stop - sub.high:
    result = -1

proc find*(s: StringSlice, sub: StringSlice,
  start: Natural = 0, last: Natural = 0): int32 =
  ## Finds a string slice in another string slice. This should be really fast
  ## when both string slices are from the same base string, as it will compare
  ## only the indices. Otherwise it will convert the string slice to find into
  ## a regular string and call the normal find operation.
  if s.buf == sub.buf:
    if sub.start >= s.start + start and sub.stop - s.start <= s.stop - (s.start + last):
      sub.start - s.start
    else:
      -1
  else:
    s.find($sub, start, last).int32

proc strip*(s: StringSlice, first = true, last = true): StringSlice {.noInit.} =
  ## Strips whitespace from both sides (controllable with the ``first`` and
  ## ``last`` arguments) of the string slice and returns a new string slice
  ## with the same underlying string.
  result = StringSlice(buf: s.buf, start: s.start, stop: s.stop)
  if first:
    for i in result.start..result.stop:
      if not (result.buf[i] in Whitespace): break
      result.start += 1
  if last:
    for i in countdown(result.stop, result.start):
      if not (result.buf[i] in Whitespace): break
      result.stop -= 1

iterator items*(a: StringSlice): char =
  ## Iterate over each character in a string slice
  for i in a.start..a.stop:
    yield a.buf[i]


when defined(js):
  type Regex = Regexp

  func re(pattern: string): Regex = newRegexp(pattern)

  func search(pattern: cstring; self: RegEx): int {.importjs: "(#.search(#) || [])".}

  func find(slice: StringSlice, pattern: RegEx,
            start: int32 = 0, size: int32 = -1): tuple[first, last: int32] =
    let last = if size < 0:  slice.len - 1  else: size + start
    let s = slice.str[start + slice.start .. last + slice.start]
    let a: int32 = search(s, pattern)
    if a < 0:  return (-1, -2)
    let m: seq[cstring] = match(s, pattern)
    assert m.len > 0
    let b: int32 = a + m[0].len
    return (a, b)

  func match(slice: StringSlice, pattern: RegExp, position: int32): int32 =
    let s = slice.str[slice.start + position ..< slice.start + slice.len]
    if startsWith(s, pattern):
      let m: seq[cstring] = match(s, pattern)
      assert m.len > 0
      return m[0].len
    return -1

else:
  func find(slice: StringSlice, pattern: RegEx,
            start: int32 = 0, size: int32 = -1): tuple[first, last: int32] =
    let a, b: int
    if size < 0:
      (a, b) = findBounds(slice.str[], pattern, slice.start + start)
    else:
      (a, b) = findBounds(slice.str[], pattern, slice.start + start, size)
    return (a.int32, b.int32)

  func match(slice: StringSlice, pattern: RegEx, location: int32): int32 =
    return matchLen(slice.str[], pattern, slice.start + location).int32


when isMainModule:
  let
    s1 = "Hello world"
    s2 = makeStringSlice("Hello world")
    s3 = s2[6i32 .. ^1]
    s4 = s2[2i32 .. ^1]
    s5 = toStringSlice("")
    s6 = toStringSlice("a")

  echo $s2
  echo $s5
  echo s5.len
  echo $s6
  echo s6.len

  assert s1.find("world") == 6
  assert s2.find("world") == 6
  assert s3.find("world") == 0
  echo "HERE: ", s2.find(s3)
  echo s2
  echo s3
  assert s2.find(s3) == 6
  assert s2.find(s3, last = 8) == s1.find($s3, last = 8)
  assert s2.find(s3, start = 8) == s1.find($s3, start = 8)
  assert s3.find(s4) == -1

  var
    s = "0123456789"
    ss = s.toStringSlice
    upToFour = ss[0i32..4i32]
    upToFive = ss[0i32..5i32]
    upToSix = ss[0i32..6i32]
    threeToFive = ss[3i32..5i32]

  assert s.find("123", last = 5) == ss.find("123", last = 5)
  assert s.find("456", last = 5) == ss.find("456", last = 5)
  assert s.find("789", last = 5) == s.find("789", last = 5)
  assert s.find("123", start = 2) == ss.find("123", start = 2)
  assert s.find("123", start = 2, last = 5) == ss.find("123", start = 2, last = 5)

  assert s.find("456") != upToFive.find("456")
  assert upToFive.find("456") == -1
  assert s.find("456") == upToSix.find("456")

  assert s.find("4") == threeToFive.find("4") + 3
  assert upToFour.find(threeToFive) == -1

  echo s2 == s1
  echo s2 != s1
