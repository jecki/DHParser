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

import std/[strutils, strformat]

when defined(js):
  import std/jsre
# elif (compiles do: import external/regex):
#   import external/regex
elif (compiles do: import std/nre):
  import std/nre
else:
  import std/re

type
  # StringSliceRef* = ref StringSlice not nil
  StringSlice* = tuple
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
  var strRef: ref string not nil
  when str is ref string:
    strRef = str
  else:
    new(strRef)
    strRef[] = str
  # StringSlice(buf: strRef, start: 0, stop: str.len.int32 - 1)
  (strRef, 0, strRef[].len.int32 - 1)

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

proc forwardIndex(str: StringSlice, i: Backwardsindex): int32 = str.stop - i.int32 + 1

proc index(str: StringSlice, i: int32): int32 = str.start + i

proc cut(str: StringSlice; start, stop: int32): StringSlice =
  if start > stop or stop < 0 or start > str.stop:
    (EmptyStringSlice.buf, 0i32, -1i32)
  else:
    (str.buf, max(start, 0), min(stop, str.stop))

proc cut*(str: StringSlice, slc: HSlice[int32, int32]): StringSlice =
  str.cut(str.index(slc.a), str.index(slc.b))

proc cut*(str: StringSlice, slc: HSlice[int, int32]): StringSlice =
  str.cut(str.index(slc.a.int32), str.index(slc.b))

proc cut*(str: StringSlice, slc: HSlice[int32, int]): StringSlice =
  str.cut(str.index(slc.a), str.index(slc.b.int32))

proc cut*(str: StringSlice, slc: HSlice[int, int]): StringSlice =
  str.cut(str.index(slc.a.int32), str.index(slc.b.int32))

proc cut*(str: StringSlice, slc: HSlice[int32, BackwardsIndex]): StringSlice =
  str.cut(str.index(slc.a), str.forwardIndex(slc.b))

proc cut*(str: StringSlice, slc: HSlice[int, BackwardsIndex]): StringSlice =
  str.cut(str.index(slc.a.int32), str.forwardIndex(slc.b))

proc cut*(str: StringSlice, slc: HSlice[BackwardsIndex, int32]): StringSlice =
  str.cut(str.forwardIndex(slc.a), str.index(slc.b))

proc cut*(str: StringSlice, slc: HSlice[BackwardsIndex, int]): StringSlice =
  str.cut(str.forwardIndex(slc.a), str.index(slc.b.int32))

proc cut*(str: StringSlice, slc: HSlice[BackwardsIndex, BackwardsIndex]): StringSlice =
  str.cut(str.forwardIndex(slc.a), str.forwardIndex(slc.b))


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
  start: Natural = 0, last: Natural = 0): int32 =
  ## Finds a string in a string slice. Calls the similar procedure from
  ## ``strutils`` but with updated start and last references.
  result = strutils.find(s.buf[], sub, start + s.start, s.start + (if last == 0: s.stop - s.start else: last.int32)).int32 - s.start
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
  result = (s.buf, s.start, s.stop)
  # result = StringSlice(buf: s.buf, start: s.start, stop: s.stop)
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

# TODO: Add function to join string-slices

when defined(js):
  type Regex* = tuple[sticky: Regexp, nonSticky: Regexp]
  let PCREFlag = newRegexp(r"\(\*\w+\)", "g")
  let comment = newRegexp(r"#[^\n]*", "g")
  let whitespace = newRegexp(r"(?: *\n *)|(?:^ *)|(?: *$)", "g")
  let slashU = newRegexp(r"\\U([0-9a-fA-F]+)", "g")

  proc ure*(pattern: string or cstring): Regex =
    let cleanPattern = pattern.replace(PCREFlag, "").replace(slashU, r"\u{$1}")
    return (sticky: newRegexp(cleanPattern, "uy"),
            nonSticky: newRegexp(cleanPattern, "ug"))

  proc urex*(pattern: string or cstring): Regex =
    let flatPattern = pattern.replace(PCREFlag, "")
                             .replace(comment, "")
                             .replace(whitespace, "")
                             .replace(slashU, r"\u{$1}")
    return (sticky: newRegexp(flatPattern, "uy"),
            nonSticky: newRegexp(flatPattern, "ug"))

  func search(pattern: cstring; self: RegExp): int {.importjs: "(#.search(#) || [])".}

  proc find*(slice: StringSlice, pattern: RegEx,
             start: int32 = 0, size: int32 = -1): tuple[first, last: int32] =
    assert start >= 0 and start <= slice.stop - slice.start + 1
    pattern.nonSticky.lastIndex = start + slice.start
    let s = cstring(slice.str[])
    let m: seq[cstring] = pattern.nonSticky.exec(s)
    if m.len > 0:
      let l: int32 = ($m[0]).len
      let a: int32 = pattern.nonSticky.lastIndex - slice.start - m[0].len
      if size < 0 or a <= start + size:
        return (a, a + l - 1)
    return (-1, -2)

  proc matchLen*(slice: StringSlice, pattern: RegEx, location: int32): int32 =
    assert location >= 0 and location <= slice.stop - slice.start + 1
    pattern.sticky.lastIndex = location + slice.start
    let m: seq[cstring] = match(cstring(slice.str[]), pattern.sticky)
    if m.len > 0:
      assert m.len == 1
      return ($m[0]).len
    return -1

  proc replace*(slice: StringSlice, pattern: Regex, replacement: string): cstring =
    replace(cstring($slice), pattern.nonSticky, cstring(replacement))
#
# elif (compiles do: import external/regex):
#   type Regex* = Regex2
#
#   let slashU = re2"\\[uU]([0-9a-fA-F]+)"
#
#   proc ure*(pattern: string): Regex =
#     # re2(replace(pattern, slashU, r"\x{$1}"))
#     re2(pattern)
#   proc urex*(pattern: string): Regex =
#     # re2("(?x)" & replace(pattern, slashU, r"\x{$1}"))
#     re2("(?x)" & pattern)
#
#   func find*(slice: StringSlice, pattern: Regex,
#              start: int32 = 0, size: int32 = -1): tuple[first, last: int32] =
#     assert start >= 0 and start <= slice.stop - slice.start + 1
#     var m: RegexMatch2
#     if find(slice.buf[], pattern, m, slice.start + start):
#       let a = m.boundaries.a.int32 - slice.start
#       if size < 0 or a < start + size:
#         return (a, m.boundaries.b.int32 - slice.start)
#     return (-1, -2)
#
#   func matchLen*(slice: StringSlice, pattern: Regex, location: int32): int32 =
#     assert location >= 0 and location <= slice.stop - slice.start + 1
#     var m: RegexMatch2
#     if startswith(slice.buf[], pattern, m, slice.start + location):
#       assert m.boundaries.a.int32 == slice.start + location
#       return int32(m.boundaries.b - m.boundaries.a + 1)
#     return -1
#
#   func replace*(slice: StringSlice, pattern: Regex, replacement: string): string =
#     replace($slice, pattern, replacement)

elif (compiles do: import std/nre):
  export Regex

  const unicodePrefix = "(*UTF8)(*UCP)"
  let slashU = re"\\[uU]([0-9a-fA-F]+)"

  proc ure*(pattern: string): Regex =
    re(unicodePrefix & replace(pattern, slashU, r"\x{$1}"))
  proc urex*(pattern: string): Regex =
    re(unicodePrefix & "(?x)" & replace(pattern, slashU, r"\x{$1}"))

  func find*(slice: StringSlice, pattern: Regex,
             start: int32 = 0, size: int32 = -1): tuple[first, last: int32] =
    assert start >= 0 and start <= slice.stop - slice.start + 1
    var r: Option[RegexMatch]
    if size < 0:
      r = find(slice.str[], pattern, slice.start.int + start)
    else:
      r = find(slice.str[], pattern, slice.start.int + start,
               min(slice.len.int - 1, slice.start.int + start + size - 1))
    if r.isSome():
      let bounds = r.get().matchBounds
      return (bounds.a.int32 - slice.start, bounds.b.int32 - slice.start)
    return (-1, -2)

  func matchLen*(slice: StringSlice, pattern: Regex, location: int32): int32 =
    assert location >= 0 and location <= slice.stop - slice.start + 1
    let r = match(slice.str[], pattern, slice.start + location)
    if r.isSome():
      let bounds = r.get().matchBounds
      return int32(bounds.b - bounds.a + 1)
    return -1

  func replace*(slice: StringSlice, pattern: Regex, replacement: string): string =
    replace($slice, pattern, replacement)

else:
  export Regex

  const unicodePrefix = "(*UTF8)(*UCP)"
  let slashU = re"\\[uU]([0-9a-fA-F]+)"

  proc ure*(pattern: string): Regex =
    re(unicodePrefix & replacef(pattern, slashU, r"\x{$1}"))
  proc urex*(pattern: string): Regex =
    rex(unicodePrefix & replacef(pattern, slashU, r"\x{$1}"))

  func find*(slice: StringSlice, pattern: RegEx,
            start: int32 = 0, size: int32 = -1): tuple[first, last: int32] =
    assert start >= 0 and start <= slice.stop - slice.start + 1
    let a, b: int
    if size < 0:
      (a, b) = findBounds(slice.str[], pattern, slice.start + start)
    else:
      let buf = cstring(slice.str[])
      (a, b) = findBounds(buf, pattern, slice.start + start, min(buf.len, size))
    if a < 0:  return (-1, -2)
    return (a.int32 - slice.start, b.int32 - slice.start)

  func matchLen*(slice: StringSlice, pattern: RegEx, location: int32): int32 =
    assert location >= 0 and location <= slice.stop - slice.start + 1
    result = matchLen(slice.str[], pattern, slice.start + location).int32

  func replace*(slice: StringSlice, pattern: Regex, replacement: string): string =
    replace($slice, pattern, replacement)


when isMainModule:
  echo $EmptyStringSlice

  let one = makeStringSlice("1")
  assert $one.cut(0..0) == "1"
  assert $one.cut(0..1) == "1"
  assert $one.cut(-1 .. 0) == "1"
  assert $one.cut(-1 .. 1) == "1"
  assert $one.cut(^1 .. 0) == "1"
  assert $one.cut(^1 .. ^1) == "1"
  assert $one.cut(0 .. ^1) == "1"
  assert $one.cut(^2 .. ^1) == "1"
  assert $one.cut(1..1) == ""
  assert $one.cut(1..0) == ""
  assert $one.cut(1.. -1) == ""

  let
    s1 = "Hello world"
    s2 = makeStringSlice("Hello world")
    s3 = s2.cut(6 .. ^1)
    s4 = s2.cut(2 .. ^1)
    s5 = toStringSlice("")
    s6 = toStringSlice("a")

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
    upToFour = ss.cut(0..4)
    upToFive = ss.cut(0..5)
    upToSix = ss.cut(0..6)
    threeToFive = ss.cut(3..5)

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

  let slice = makeStringSlice("abc 123 def 456 gh 78 ijk")
  assert slice.matchLen(ure"\w+", 0) == 3
  assert slice.matchLen(ure"[0-9]+", 0) == -1
  echo $slice.matchLen(ure"[0-9]+", 4)
  assert slice.matchLen(ure"[0-9]+", 4) == 3
  assert slice.matchLen(ure"[0-9]+", 19) == 2
  assert slice.cut(19 .. ^1).matchLen(ure"[0-9]+", 0) == 2

  assert slice.find(ure"[0-9]+") == (4'i32, 6'i32), $slice.find(ure"[0-9]+")
  assert slice.find(ure"[0-9]+", 7) == (12'i32, 14'i32)
  assert slice.find(ure"[0-9]+", 7, 4) == (-1'i32, -2'i32)
  assert slice.cut(19i32 .. ^1i32).find(ure"[0-9]+") == (0'i32, 1'i32)

  assert slice.cut(4i32..10i32).replace(ure"\d", "?") == "??? def"

  let trivial = makeStringSlice("A")
  assert trivial.matchLen(ure"\w+", 0) == 1
  assert trivial.matchLen(ure"\w+", 1) == -1
  assert trivial.matchLen(ure"\w*", 1) == 0
  assert trivial.matchLen(ure"$", 1) == 0
  # assert trivial.matchLen(re"$", 2) < 0
  assert trivial.matchLen(ure"$", 0) == -1
  assert trivial.matchLen(ure"^", 0) == 0
  assert trivial.matchLen(ure"^", 1) == -1
  # assert trivial.matchLen(re"^", 2) < 0

  assert trivial.find(ure"\w+", 0) == (0'i32, 0'i32)
  assert trivial.find(ure"\w+", 1) == (-1'i32, -2'i32)

  when defined(js):
    assert $ure("(*UTF8)(*UCP) A   ")[0].toCString() == r"/ A   /uy"
    assert $urex("   A B   ")[0].toCString() == r"/A B/uy"
    let pattern = """
      ^       # match the beginning of the line
      (\w+)   # 1st capture group: match one or more word characters
      \s      # match a whitespace character
      (\w+)   # 2nd capture group: match one or more word characters
      """
    assert $urex(pattern)[0].toCString() == r"/^(\w+)\s(\w+)/uy"

  echo $replace(makeStringSlice("abc\ndef"), ure"\n", r"\n")
