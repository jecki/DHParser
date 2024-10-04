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


import std/[algorithm, strutils, unicode]


type
  Range* = tuple[min: uint32, max: uint32]
  RuneRange* = tuple[low: Rune, high: Rune]
  RuneSet* = tuple[negate: bool, ranges: seq[RuneRange]]



func toRange*(r: RuneRange): Range = (r.low.uint32, r.high.uint32)
func toRuneRange*(r: Range): RuneRange = (Rune(r.min), Rune(r.max))


func notEmpty(R: seq[RuneRange]): bool =
  ## Confirms that the sequence of ranges is not be empty and that
  ## for each range low <= high.
  if R.len <= 0: return false
  for r in R:
    if r.high <% r.low: return false
  return true

func isSortedAndMerged*(R: seq[RuneRange]): bool =
  ## Confirms that the ranges in the sequences are in ascending order
  ## and that there are no overlapping or adjacent ranges.
  for i in 1 ..< len(R):
    if R[i].low <=% R[i - 1].high: return false
  return true

proc sortAndMerge*(R: var seq[RuneRange]) =
  ## Sorts the sequence of ranges and merges overlapping regions
  ## in place so that the ranges are in ascending order,
  ## non-overlapping and non-adjacent. The sequence can be shortened
  ## in the process.
  assert notEmpty(R)
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

# TODO: Rename as basicRuneSet
proc rs*(rangesStr: string): RuneSet =
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
    for t in [r"\x", r"0x", r"\u", r"\U"]:
      if i+1 < s.len and s[i..i+1] == t:
        i += 2
        i0 = i
        while i < s.len:
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

proc rr*(rangeStr: string): RuneRange =
  let runes = rs(rangeStr)
  assert runes.ranges.len == 1
  return runes.ranges[0]


proc `+`*(A, B: seq[RuneRange]): seq[RuneRange] =
  result = newSeqOfCap[RuneRange](A.len + B.len)
  for r in A:  result.add(r)
  for r in B:  result.add(r)
  sortAndMerge(result)

proc `-`*(A, B: seq[RuneRange]): seq[RuneRange] =
  assert notEmpty(A)
  assert notEmpty(B)
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
