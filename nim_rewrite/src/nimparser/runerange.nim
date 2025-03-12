## Rune Ranges
## ===========
##
## A module that defines data-types and functions for handling character
## ranges on the basis of nim's unicode-runes.
##
## The data-types include plain rune-ranges, e.g. [A-Z]
## or, say [\u037F-\u1FFF], negative ranges, e.g. [^0-9] (not a digit) as
## well as unions or intersections of such ranges.
##
## The functions allow to normalize (sortAndMerge()) sets of rune
## ranges, query for inclusion (isInRuneRange()) in logarithmic time,
## perform basic algrbraic operations (like intersecting * , joining + ,
## building the difference -, negating ^), and finally to build rune sets
## from string-descriptions similar to regular expression ranges,
## e.g. rs"abcdefg" rs"^A-F"


{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}


import std/[algorithm, strformat, strutils, unicode]


proc nilRefError(fieldName: string): ref AssertionDefect =
  newException(AssertionDefect, fmt"{fieldName} unexpectedly nil!")


type
  Range* = tuple[min: uint32, max: uint32]
  RuneRange* = tuple[low: Rune, high: Rune]
  RuneSet* = tuple[negate: bool, ranges: seq[RuneRange]]

const
  EmptyRuneRange* = (Rune('b'), Rune('a'))

proc `$`*(range: Range): string =
  let
    min {.inject.} = range.min
    max {.inject.} = range.max
  if min <= max:  fmt"{min}..{max}"  else: "EMPTY"

proc `$`*(rs: RuneSet, verbose: bool = false): string =
  ## Serializes rune set. Use "runeset $ true" for a more
  ## verbose and easier to read serialization.
  proc hexlen(r: Rune): (int8, string) =
    let i = r.int32
    if i < 1 shl 8: return (2, r"\x")
    elif i < 1 shl 16:  return (4, r"\u")
    else: return (8, r"\U")

  proc isAlphaNum(rr: RuneRange): bool =
    proc isIn(a, b, x, y: int32): bool =
      a >= x and a <= y and b >= x and b <= y
    let
      a = rr.low.int32
      b = rr.high.int32
    isIn(a, b, 48, 57) or isIn(a, b, 65, 90) or isIn(a, b, 97, 122)

  var s: seq[string] = newSeqOfCap[string](len(rs.ranges) + 2)
  if not verbose:
    s.add("[")
    if rs.negate: s.add("^")
  for rr in rs.ranges:
    if isAlphaNum(rr):
      let low = chr(rr.low.int8)
      if rr.low == rr.high:
        s.add(fmt"{low}")
      else:
        let high = chr(rr.high.int8)
        s.add(fmt"{low}-{high}")
    else:
      let (l, marker) = hexlen(rr.high)
      if rr.low == rr.high:
        s.add(marker & toHex(rr.low.int32, l))
      else:
        s.add(marker & toHex(rr.low.int32, l) & "-" & marker & toHex(rr.high.int32, l))
    if rr.high <% rr.low:  s.add("!") 
  if verbose:
    (if rs.negate: @["[^", s.join("]-["), "]"] 
             else: @["[", s.join("]|["), "]"]).join("")
  else:
    s.add("]")
    return s.join("")

proc `$`*(rr: seq[RuneRange], verbose=false): string = (false, rr) $ verbose
proc `$`*(rr: RuneRange): string = $(@[rr])

func toRange*(r: RuneRange): Range = (r.low.uint32, r.high.uint32)
func toRuneRange*(r: Range): RuneRange = (Rune(r.min), Rune(r.max))

func neverEmpty*(rr: seq[RuneRange]): bool =
  ## Confirms that the sequence of ranges is not be empty and that
  ## for each range low <= high.
  if rr.len <= 0: return false
  for r in rr:
    if r.high <% r.low: return false
  return true

func isSortedAndMerged*(rr: seq[RuneRange]): bool =
  ## Confirms that the ranges in the sequences are in ascending order
  ## and that there are no overlapping or adjacent ranges.
  for i in 1 ..< len(rr):
    if rr[i].low <=% rr[i - 1].high: return false
  return true

func size*(range: Range): uint32 = range.max - range.min + 1
func size*(r: RuneRange): uint32 = size(toRange(r))
func size(R: seq[RuneRange]): uint32 =
  if not isSortedAndMerged(R):
    raise newException(AssertionDefect,
      fmt"Cannot determine size of unmerged and unsorted rune range: {R}")
  var sum: uint32 = 0
  for rr in R:
    sum += size(rr)
  return sum

proc sortAndMerge*(R: var seq[RuneRange]) =
  ## Sorts the sequence of ranges and merges overlapping regions
  ## in place so that the ranges are in ascending order,
  ## non-overlapping and non-adjacent. The sequence can be shortened
  ## in the process.
  assert neverEmpty(R)
  R.sort(proc (a, b: RuneRange): int =
           if a.low <% b.low: -1 else: 1)
  var
    a = 0
    b = 1
  while b < R.len:
    if R[b].low.int32 <= R[a].high.int32 + 1:
      if R[a].high <=% R[b].high:
        R[a].high = R[b].high
    else:
      a += 1
      if a != b:  R[a] = R[b]
    b += 1

  R.setLen(a + 1)
  # assert isSortedAndMerged(R)

proc `+`*(A, B: seq[RuneRange]): seq[RuneRange] =
  result = newSeqOfCap[RuneRange](A.len + B.len)
  for r in A:  result.add(r)
  for r in B:  result.add(r)
  sortAndMerge(result)

proc `-`*(A, B: seq[RuneRange]): seq[RuneRange] =
  assert neverEmpty(A)
  assert neverEmpty(B)
  assert isSortedAndMerged(A)
  assert isSortedAndMerged(B)

  result = newSeqOfCap[RuneRange](A.len * 2)
  var
    i = 1
    k = 0
    M = A[0]
    S = B[0]

  proc nextA(M: var RuneRange): bool =
    ## returns true, if last A has been passed
    if i < A.len:
      M = A[i]
      i += 1
      return false
    return true

  proc nextB(S: var RuneRange) =
    k += 1
    if k < B.len: S = B[k]

  while k < B.len:
    if S.low <=% M.high and M.low <=% S.high:
      if M.low <% S.low:
        result.add((M.low, Rune(S.low.int32 - 1)))
        if S.high <% M.high:
          M.low = Rune(S.high.int32 + 1)
          nextB(S)
        elif nextA(M): return
      elif S.high <% M.high:
        M.low = Rune(S.high.int32 + 1)
        nextB(S)
      elif nextA(M): return
    elif M.high <% S.low:
      result.add(M)
      if nextA(M): return
    else:
      assert S.high <% M.low
      nextB(S)
  result.add(M)
  while i < A.len:
    result.add(A[i])
    i += 1
  # assert isSortedAndMerged(result)

# intersection
proc `*`*(A, B: seq[RuneRange]): seq[RuneRange] = A - (A - B) - (B - A)


proc `^`*(runes: RuneSet): RuneSet = (not runes.negate, runes.ranges)

proc `+`*(A, B: RuneSet): RuneSet =
  let selector = (if A.negate: 2 else: 0) + (if B.negate: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      return (false, A.ranges + B.ranges)
    of 0b01:  # (false, true)
      return (true, B.ranges - A.ranges)
    of 0b10:  # (true, false)
      return (true, A.ranges - B.ranges)
    of 0b11:  # (true, true)
      return (true, A.ranges * B.ranges)
    else:  assert false

proc `-`*(A, B: RuneSet): RuneSet =
  let selector = (if A.negate: 2 else: 0) + (if B.negate: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      return (false, A.ranges - B.ranges)
    of 0b01:  # (false, true)
      return (false, A.ranges * B.ranges)
    of 0b10:  # (true, false)
      return (true, A.ranges + B.ranges)
    of 0b11:  # (true, true)
      return (false, B.ranges - A.ranges)
    else: assert false


func inRuneRange*(r: Rune, ranges: seq[RuneRange]): int32 =
  ## Binary search to find out if rune r falls within one of the sorted ranges
  ## Returns the index of the range or -1, if r does not fall into any range
  ## It is assumed that the ranges are sorted and do not overlap.
  let
    highest: int32 = ranges.len.int32 - 1'i32
  var
    a = 0'i32
    b = highest
    last_i = -1'i32
    i  = b div 2

  while i != last_i:
    if ranges[i].low <=% r:
      if r <=% ranges[i].high:
        return i
      else:
        a = min(i + 1, highest)
    else:
      b = max(i - 1, 0)
    last_i = i
    i = a + (b - a) div 2
  return -1


## Rune range and rune set parsers

proc rs0*(rangesStr: string): RuneSet =
  ## Parses "basic" rune sets. The syntax for rangeStr is more or less the
  ## syntax you'd use inside rectangular brackets [ ] in regular expressions,
  ## only that the only allowed backslashed values are \s (whitespace)
  ## and \n (linefeed).
  ## Examples: rs0"a-z0-9\xc4-\xd6", rs0"^A-Z"
  ##
  ## Hexadecimal codes are allowed. They may be introduced with any of the
  ## following: "\x", "\u", "\U". Inverse sets are built with a leading "^"
  var
    buf: string = ""
    bi: int32 = 1

  proc parseRune(s: string, i: var int): Rune =
    var
      r: Rune
      i0, i1: int
    if bi < buf.len:
      buf.fastRuneAt(bi, r)
      return r
    for (t, n) in [(r"\x", 2), (r"\u", 4), (r"\U", 8)]:
      if i+1 < s.len and s[i..i+1] == t:
        i += 2
        i0 = i
        while i < s.len and i - i0 < n:
          i1 = i
          s.fastRuneAt(i, r)
          if r.toUtf8 notin "0123456789ABCDEFabcdef":
            i = i1
            break
        return Rune(fromHex[int32](s[i0..<i]))
    s.fastRuneAt(i, r)
    if r.toUTF8 == r"\":
      s.fastRuneAt(i, r)
      case r.toUTF8:
        of "s":
          buf = " \t\r\n\f"
          bi = 0
          buf.fastRuneAt(bi, r)
        of "n":  r = "\n".runeAt(0)
        else:
          discard
    return r

  var
    i = 0
    i0: int
    low, high, delimiter: Rune
    negate = false
    runeRanges: seq[RuneRange] = @[]

  if rangesStr.len > 0 and rangesStr[0] == '^':
    negate = true
    i += 1
  while i < rangesStr.len or bi < buf.len:
    low = parseRune(rangesStr, i)
    if i < rangesStr.len:
      i0 = i
      delimiter = parseRune(rangesStr, i)
      if (i < rangesStr.len or bi < buf.len) and delimiter.toUtf8 == "-":
        high = parseRune(rangesStr, i)
        if high <% low:
          delimiter = low
          low = high
          high = delimiter
      else:
        i = i0
        high = low
    else:
      high = low
    runeRanges.add((low, high))
  assert runeRanges.len >= 1
  sortAndMerge(runeRanges)
  return (negate, runeRanges)


proc rs*(s: string): RuneSet =
  ## parses "complex" rune sets that may be composed of unions or differences
  ## of basic rune sets. Examples:
  ## rs"""[_:]|[A-Z]|[a-z]|[\u00C0-\u00D6]|[\U00010000-\U000EFFFF]"""
  ## rs"[^<&\"]"
  ## rs"[\ufeff]|[\ufffe]|[\u0000][\ufeff]|[\ufffe][\u0000]"
  ## rs"[A-Za-z0-9._\-]"
  ## rs"A-Za-z"
  ## rs"^<&'>\s"
  assert s.len > 0
  var 
    i = 0
    k = 0
    sign = ' '

  proc parseRuneSet(): RuneSet =
    assert i < s.len
    assert s[i] == '[', $i
    let k = i + 1
    while i < s.len and (s[i] != ']' or (i > 0 and s[i-1] == '\\')):  i += 1
    assert i < s.len
    result = rs0(s[k ..< i])
    i += 1

  template addOrSubtract(nextRS: RuneSet) = 
      if sign == '-':
        result = result - nextRS
      else:
        if result.ranges.len == 0:
          result = nextRS
        else:
          assert sign == '|', s[0..i]
          result = result + nextRS    
      sign = ' '

  result = (false, @[])
  while i < s.len:
    while i < s.len and s[i] in " \n":  i += 1
    if s[i] == '-':
      assert sign != '-', s[0..i]
      sign = '-'
      i += 1
    elif s[i] == '|':
      i += 1
      sign = '|'
    elif s[i] != '[':
      k = i      
      while i < s.len and not (s[i] in " \n|"):  i += 1
      # TODO: Ensure that rs0(s[k ..< i]) is a single character 
      addOrSubtract(rs0(s[k ..< i]))
    else: 
      while i < s.len and s[i] in " \n":  i += 1
      addOrSubtract(parseRuneSet())



proc rr*(rangeStr: string): RuneRange =
  ## Parses a single rune range. Examples: rr"A-Z", rr"[a-z]".
  ##
  ## Inverse rune ranges are not possible. Neither are concatenations
  ## of rune ranges. The rune range may be enclosed by rectangular
  ## brackets, but does not need to be.
  let runes = rs(rangeStr)
  assert runes.ranges.len == 1
  return runes.ranges[0]


when isMainModule:
  let rs1 = rs"""[_]|[:]|[A-Z]|[a-z]
                |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                |[\U00010000-\U000EFFFF]"""
  let rs2 = rs"[ace\sD-G]"
  let rs3 = rs"[a-f]|[^c-z0-9]|[24]"
  echo $rs1
  echo $rs($rs1)
  echo $rs(rs1 $ true)
  echo rs1 $ true
  echo $rs2
  echo $rs($rs2)
  echo $rs(rs2 $ true)
  echo rs2 $ true  
  echo $rs3
  echo $rs($rs3)
  echo rs3 $ true
  echo $rs(rs3 $ true)
  echo rs3 $ true
