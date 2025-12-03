## Rune ranges
## ===========
## 
## RuneRange is a very simple data tuple that defines a range of runes
## lowest and highest rune withing the range, e.g. [A-Z] or [\u037F-\u1FFF]. 
##
## There are a number of static methods that allow to normalize (sortAndMerge()) 
## sequences of rune ranges, query for inclusion (isInRuneRange()) in 
## logarithmic time, perform basic algrbraic operations (like intersecting * , 
## joining +, building the difference -, negating ^), and finally to build 
## sequences of rune ranges from string-descriptions similar to regular 
## expression ranges, e.g. rs"abcdefg" rs"^A-F"


import std/[algorithm, strformat, strutils, unicode]

type
  RuneRange* = tuple[low: Rune, high: Rune]

const
  EmptyRuneRange* = (Rune('b'), Rune('a'))


proc `$`*(range: RuneRange): string =
  let
    min = range.low.uint32
    max = range.high.uint32
  if min <= max:  fmt"{min}..{max}"  else: "EMPTY"


func toRanges*[T: Ordinal](s: set[T], RT: type): seq[(RT, RT)] =
  ## Converts a set to a sequence of ranges. The sequence is sorted in ascending order.
  result = newSeq[RuneRange](0)
  if s.len > 0:
    var (a, b) = (T(0), T(0))
    for i in s:
      (a, b) = (i, i)
      break
    for i in s:
      if i > b + 1:
        result.add((RT(a), RT(b)))
        (a, b) = (i, i)
      else:
        b = i
    result.add((RT(a), RT(b)))


func contains*(ranges: seq[RuneRange], r: Rune): bool =
  ## Binary search to find out if rune r is in one of the ranges
  ## It is assumed that the ranges are sorted and do not overlap.
  let
    highest: int32 = ranges.len.int32 - 1'i32
  var
    a = 0'i32
    b = highest
    last_i = -1'i32
    i = b shr 1  # div 2

  while i != last_i:
    let rng = ranges[i]
    if rng.low <=% r:
      if r <=% rng.high:
        return true
      else:
        a = min(i + 1, highest)
    else:
      b = max(i - 1, 0)
    last_i = i
    i = a + (b - a) shr 1  # div 2
  return false


func isSortedAndMerged*(rr: seq[RuneRange]): bool =
  ## Confirms that the ranges in the sequences are in ascending order
  ## and that there are no overlapping or adjacent ranges.
  for i in 1 ..< len(rr):
    if rr[i].low <=% rr[i - 1].high: return false
  return true


func neverEmpty*(rr: seq[RuneRange]): bool =
  ## Confirms that the sequence of ranges is not empty and that
  ## for each range low <= high.
  if rr.len <= 0: return false
  for r in rr:
    if r.high <% r.low: return false
  return true


proc sortAndMerge*(R: var seq[RuneRange]) =
  ## Sorts the sequence of ranges and merges overlapping regions
  ## in place so that the ranges are in ascending order,
  ## non-overlapping and non-adjacent. 
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


func size*(r: RuneRange): uint32 = r.high.uint32 - r.low.uint32 + 1

func size*(R: seq[RuneRange]): uint32 =
  if not isSortedAndMerged(R):
    raise newException(AssertionDefect,
      fmt"Cannot determine size of unmerged and unsorted rune range: {R}")
  var sum: uint32 = 0
  for rr in R:
    sum += size(rr)
  return sum


# Rune Range algebraic operations

func `+`*(A, B: seq[RuneRange]): seq[RuneRange] =
  result = newSeqOfCap[RuneRange](A.len + B.len)
  for r in A:  result.add(r)
  for r in B:  result.add(r)
  sortAndMerge(result)


func `-`*(A, B: seq[RuneRange]): seq[RuneRange] =
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


func `*`*(A, B: seq[RuneRange]): seq[RuneRange] = A - (A - B) - (B - A)


# Rune range algebraic operations with complement ranges
  

proc add*(Acompl, Bcompl: bool; A, B: seq[RuneRange]): (bool, seq[RuneRange]) =
  let selector = (if Acompl: 2 else: 0) + (if Bcompl: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      (false, A + B)
    of 0b01:  # (false, true)
      (true, B - A)
    of 0b10:  # (true, false)
      (true, A - B)
    of 0b11:  # (true, true)
      (true, A * B)
    else:  
      assert false
      (false, @[])


proc sub*(Acompl, Bcompl: bool; A, B: seq[RuneRange]): (bool, seq[RuneRange]) = 
  let selector = (if Acompl: 2 else: 0) + (if Bcompl: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      (false, A - B)
    of 0b01:  # (false, true)
      (false, A * B)
    of 0b10:  # (true, false)
      (true, A + B)
    of 0b11:  # (true, true)
      (false, B - A)
    else: 
      assert false
      (false, @[])


# Rune Range parsers

func rrs*(rangesStr: string): seq[RuneRange] =
  ## Parses "basic" rune ranges. The syntax for rangeStr is more or less the
  ## syntax you'd use inside rectangular brackets [ ] in regular expressions,
  ## only that the only allowed backslashed values are \s (whitespace)
  ## and \n (linefeed).
  ## Examples: rrs"a-z0-9\xc4-\xd6", rrs"^A-Z"
  ##
  ## Hexadecimal codes are allowed. They may be introduced with any of the
  ## following: "\x", "\u", "\U". 
  ## 
  ## A leading "^" is ignored. The caller will have to keep track of this
  ## and negate the resulting rune ranges if needed.
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
    neg = false
    runeRanges: seq[RuneRange] = @[]

  if rangesStr.len > 0 and rangesStr[0] == '^':
    neg = true
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
  return runeRanges

proc rr*(rangeStr: string): RuneRange =
  ## Parses a single rune range. Examples: rr"A-Z", rr"[a-z]".
  ##
  ## Inverse rune ranges are not possible. Neither are concatenations
  ## of rune ranges. The rune range may be enclosed by rectangular
  ## brackets, but does not need to be.
  assert rangeStr.len == 0 or rangeStr[0] != '^'  
  let ranges = rrs(rangeStr)
  assert ranges.len == 1
  return ranges[0]
