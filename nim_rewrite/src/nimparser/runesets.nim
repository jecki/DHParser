## Rune Sets
## =========
##
## A module that defines data-types and functions for handling character
## ranges and sets on the basis of nim's unicode-runes.
##
## Rune ranges
## -----------
## 
## RuneRange is a very simple data tuple that defines a range of runes
## lowest and highest rune withing the range, e.g. [A-Z] or [\u037F-\u1FFF]. 
##
## There are a number of statis methods that allow to normalize (sortAndMerge()) 
## sequences of rune ranges, query for inclusion (isInRuneRange()) in 
## logarithmic time, perform basic algrbraic operations (like intersecting * , 
## joining +, building the difference -, negating ^), and finally to build 
## sequences of rune ranges from string-descriptions similar to regular 
## expression ranges, e.g. rs"abcdefg" rs"^A-F"
## 
## Rune sets
## ---------
## 
## A RuneSets is basically a sequnce of rune ranges that are non-overlapping,
## non-adjacent and sorted in ascending order. The "negate" flag indicates 
## whether the set is a positive or negative set. If true, the elements 
## outside the ranges are part of the set. Thus, the "ranges"-field and the 
## "negate"-flag of the RuneSet object define the set completely. All other 
## fields just serve to speed up the "contains" operation. 
## 
## The cache fields fields (cache256, cache4k, cache64k) are used to redundantly 
## store the elements in the whole sequence of ranges or of the lower part of
## it (upt to code point 0xFFFF) in set from which allows for very fast
## inclusion tests. Of these fields only one is active depening on wether the 
## highest code point covered by the ranges it is <= 0xFF, <= 0x0FFF or <= 0xFFFF. 
## The "uncached" field stores any "left-over" ranges that could not represented 
## in the cache, anymore, because its higher limit exceeds 0xFFFF.
## 
## The "contains" field is a procedure pointer that points to the procedure
## that is used to test for inclusion. It is set up when the RuneSet is
## initialized and may change the first time it is used, depending on
## the ranges that are present. 


{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}
# {.experimental: "codeReordering".}


import std/[algorithm, strformat, strutils, unicode]


# proc nilRefError(fieldName: string): ref AssertionDefect =
#   newException(AssertionDefect, fmt"{fieldName} unexpectedly nil!")


type
  ContainsProc = proc(rs: var RuneSet, r: Rune): bool {.nimcall.}
  RuneRange* = tuple[low: Rune, high: Rune]
  Set256* = set[0..255]
  Set4K* = set[0..4095]
  Set64K* = set[0..65535]
  RuneSet* {.acyclic.} = object  
    negate*: bool
    ranges*: seq[RuneRange]
    uncached: seq[RuneRange]
    cache256: ref Set256
    cache4k:  ref Set4k
    cache64k: ref Set64k
    contains*: ContainsProc not nil

const
  EmptyRuneRange* = (Rune('b'), Rune('a'))


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


proc inRanges(rs: var RuneSet, r: Rune): bool = rs.negate xor contains(rs.ranges, r)
proc inCache256(rs: var RuneSet, r: Rune): bool = rs.negate xor r.int32 in rs.cache256[]
proc inCache4k(rs: var RuneSet, r: Rune): bool = rs.negate xor r.int32 in rs.cache4k[]
proc inCache64k(rs: var RuneSet, r: Rune): bool = rs.negate xor r.int32 in rs.cache4k[]
proc inRangesOrCache256(rs: var RuneSet, r: Rune): bool = rs.negate xor (r.int32 in rs.cache256[] or contains(rs.uncached, r))
proc inRangesOrCache4k(rs: var RuneSet, r: Rune): bool = rs.negate xor (r.int32 in rs.cache4k[] or contains(rs.uncached, r))
proc inRangesOrCache64k(rs: var RuneSet, r: Rune): bool = rs.negate xor (r.int32 in rs.cache64k[] or contains(rs.uncached, r))


proc cacheAll[T: Set256|Set4k|Set64k](rs: var RuneSet, cache: var ref T) = 
  new(cache)
  cache[] = {rs.ranges[0].low.uint16..rs.ranges[0].high.uint16}
  for rr in rs.ranges[1..^1]:
    cache[] = cache[] + {rr.low.uint16..rr.high.uint16}

proc cacheSome[T: Set256|Set4k|Set64k](rs: var RuneSet, cache: var ref T, cacheSize: uint32) = 
  assert cacheSize == 256 or cacheSize == 4096 or cacheSize == 65536
  when T is Set256: assert cacheSize == 256
  when T is Set4k:  assert cacheSize == 4096
  when T is Set64k: assert cacheSize == 65536
  new(cache)
  let upperLimit = (cacheSize - 1).uint16
  for rr in rs.ranges:
    if rr.low.uint32 < cacheSize:
      cache[] = cache[] + {rr.low.uint16..min(rr.high.uint16, upperLimit)}
    else:
      rs.uncached.add(rr)

proc inRuneSet_firstRun(rs: var RuneSet, r: Rune): bool =
  if rs.ranges.len == 0:
    if not isNil(rs.cache256):  rs.contains = inCache256
    elif not isNil(rs.cache4k): rs.contains = inCache4k
    else:
      assert not isNil(rs.cache64k)
      rs.contains = inCache64k
  elif rs.ranges[^1].high.uint32 < 256:
    cacheAll(rs, rs.cache256)
    rs.contains = inCache256
  elif rs.ranges[^1].high.uint32 < 4096 and rs.ranges.len > 8:
    cacheAll(rs, rs.cache4k)
    rs.contains = inCache4k
  elif rs.ranges[^1].high.uint32 < 65536 and rs.ranges.len > 12:
    cacheAll(rs, rs.cache64k)
    rs.contains = inCache64k
  else:
    var s,m,l: int
    for rr in rs.ranges:
      if rr.high.uint32 < 256: s += 1
      elif rr.low.uint < 256:
        s += 1
        m += 1
        if rr.high.uint32 >= 4096:
          l += 1
      elif rr.low.uint32 < 4096:
        m += 1
        if rr.high.uint32 >= 4096:
          l += 1
      elif rr.low.uint32 < 65536:
        l += 1
    if l > 12:
      cacheSome(rs, rs.cache64k, 65536)
      rs.contains = inRangesOrCache64k
    elif m > 8:
      cacheSome(rs, rs.cache4k, 4096)
      rs.contains = inRangesOrCache4k
    elif s > 4:
      cacheSome(rs, rs.cache256, 256)
      rs.contains = inRangesOrCache256 
    else:
      rs.contains = inRanges
  rs.contains(rs, r)


func init*(RuneSet: type, neg: bool, ranges: seq[RuneRange]): RuneSet =
  RuneSet(negate: neg, ranges: ranges, uncached: @[],
          cache256: nil, cache4k: nil, cache64k: nil, 
          contains: inRuneSet_firstRun)

## The following init* functions are used to initialize rune sets
## directly with sets instead of ranges. The defining sequence of
## ranges is computed from the set. 
## In terms of startup speed this is the preferred method for
## initializing rune sets.

proc init*(RuneSet: type, neg: bool, cache: Set256): RuneSet =
  var cref = new(Set256)
  cref[] = cache
  RuneSet(negate: neg, 
          ranges: @[],  # toRanges(cache, Rune)
          uncached: @[],
          cache256: cref, cache4k: nil, cache64k: nil, 
          contains: inCache256)

proc init*(RuneSet: type, neg: bool, cache: Set4k): RuneSet =
  var cref = new(Set4k)
  cref[] = cache
  RuneSet(negate: neg, 
          ranges: @[], 
          uncached: @[],
          cache256: nil, cache4k: cref, cache64k: nil, 
          contains: inCache4k)

proc init*(RuneSet: type, neg: bool, cache: Set64k): RuneSet =
  var cref = new(Set64k)
  cref[] = cache
  RuneSet(negate: neg, 
          ranges: @[],
          uncached: @[],
          cache256: nil, cache4k: nil, cache64k: cref, 
          contains: inCache64k)

proc toRanges[T: Ordinal](s: ref set[T] not nil, RT: type): seq[(RT, RT)] =
  ## Converts a set to a sequence of ranges. The sequence is sorted in ascending order.
  result = newSeq[RuneRange](0)
  if s[].len > 0:
    var (a, b) = (T(0), T(0))
    for i in s[]:
      (a, b) = (i, i)
      break
    for i in s[]:
      if i > b + 1:
        result.add((RT(a), RT(b)))
        (a, b) = (i, i)
      else:
        b = i
    result.add((RT(a), RT(b)))

proc emptyCache(rs: RuneSet): RuneSet =
  ## Returns a copy of the RuneSet with all cache fields set to nil
  let ranges: seq[RuneRange]
  if rs.ranges.len == 0:
    if not isNil(rs.cache256):
      ranges = toRanges(rs.cache256, Rune) 
    elif not isNil(rs.cache4k):
      ranges = toRanges(rs.cache4k, Rune) 
    elif not isNil(rs.cache64k):
      ranges = toRanges(rs.cache64k, Rune)
    else:
      ranges = rs.ranges
  else:
    ranges = rs.ranges
  RuneSet(negate: rs.negate, 
          ranges: ranges,
          uncached: @[],
          cache256: nil, cache4k: nil, cache64k: nil, 
          contains: inRuneSet_firstRun)


proc `==`*(a, b: RuneSet): bool =
  a.negate == b.negate and a.ranges == b.ranges


proc `$`*(rs: RuneSet, verbose: bool = false): string =
  ## Serializes rune set. Use "runeset $ true" for a more
  ## verbose and easier-to-read serialization.

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

  var 
    s: seq[string] = newSeqOfCap[string](rs.ranges.len + 2)

  if not verbose:
    s.add("[")
    if rs.negate: s.add("^")
  for rr in rs.ranges:
    if rr.low >% rr.high:
      s.add("EMPTY")
    elif isAlphaNum(rr):
      let low = chr(rr.low.int8)
      if rr.high.uint32 - rr.low.uint32 <= 2:
        s.add(fmt"{low}")
        for n in rr.low.uint32 + 1 .. rr.high.uint32:
          s[^1] &= fmt"{Rune(n)}"
      else:
        let high = chr(rr.high.int8)
        s.add(fmt"{low}-{high}")
    else:
      let (l, marker) = hexlen(rr.high)
      if rr.high.uint32 - rr.low.uint32 <= 2:
        s.add(marker & toHex(rr.low.int32, l))
        for n in rr.low.uint32 + 1 .. rr.high.uint32:
          s[^1] &= marker & toHex(n, l)
      else:
        s.add(marker & toHex(rr.low.int32, l) & "-" & marker & toHex(rr.high.int32, l))
    if rr.high <% rr.low:  s.add("!") 
  if verbose:
    s = if rs.negate: @["[^", s.join("]-["), "]"] else: @["[", s.join("]|["), "]"]
  else:
    s.add("]")
  s.join("")


proc `$`*(rr: seq[RuneRange], verbose=false): string = RuneSet.init(false, rr) $ verbose
proc `$`*(rr: RuneRange): string = $(@[rr])


proc repr*(rs: RuneSet, asSet: bool=true): string =
  ## Serializes rune set with a set literal or range-sequence-literal
  var 
    s: seq[string] = newSeqOfCap[string](rs.ranges.len + 2)

  let setRepr = asSet and (rs.ranges[^1].high.uint32 <= 65535)

  if setRepr:
    for rr in rs.ranges:
      let digits = if rr.high.uint32 < 256: 2 else: 4
      if rr.high.uint32 - rr.low.uint32 <= 1:
        s.add(fmt"0x{toHex(rr.low.uint32, digits)}")
        if rr.high != rr.low:
          s.add(fmt"0x{toHex(rr.high.uint32, digits)}")
      else:
        s.add(fmt"0x{toHex(rr.low.uint32, digits)}..0x{toHex(rr.high.uint32, digits)}") 
    fmt"rs({not rs.negate}, " & "{" & s.join(", ") & "})"  
  else:
    for rr in rs.ranges:
      let digits = if rr.high.uint32 < 256: 2 else: 4
      s.add(fmt"(0x{toHex(rr.low.uint32, digits)}, 0x{toHex(rr.high.uint32, digits)})")
    fmt"rs({not rs.negate}, @[" & s.join(", ") & "])"


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

func size*(r: RuneRange): uint32 = r.high.uint32 - r.low.uint32 + 1

proc size*(R: seq[RuneRange]): uint32 =
  if not isSortedAndMerged(R):
    raise newException(AssertionDefect,
      fmt"Cannot determine size of unmerged and unsorted rune range: {R}")
  var sum: uint32 = 0
  for rr in R:
    sum += size(rr)
  return sum


# func inRuneRanges*(r: Rune, ranges: seq[RuneRange]): int32 =
#   ## Binary search to find out if rune r falls within one of the sorted ranges
#   ## Returns the index of the range or -1, if r does not fall into any range
#   ## It is assumed that the ranges are sorted and do not overlap.
#   let
#     highest: int32 = ranges.len.int32 - 1'i32
#   var
#     a = 0'i32
#     b = highest
#     last_i = -1'i32
#     i  = b div 2

#   while i != last_i:
#     if ranges[i].low <=% r:
#       if r <=% ranges[i].high:
#         return i
#       else:
#         a = min(i + 1, highest)
#     else:
#       b = max(i - 1, 0)
#     last_i = i
#     i = a + (b - a) div 2
#   return -1


## RuneRange Combinators

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


proc `*`*(A, B: seq[RuneRange]): seq[RuneRange] = A - (A - B) - (B - A)


## RuneSet Combinators


proc `^`*(runes: RuneSet): RuneSet = 
  RuneSet(negate: not runes.negate, ranges: runes.ranges, uncached: runes.uncached,
          cache256: runes.cache256, cache4k: runes.cache4k, cache64k: runes.cache64k,
          contains: runes.contains)


proc `+`*(A, B: RuneSet): RuneSet =
  let A = emptyCache(A)
  let B = emptyCache(B)
  let selector = (if A.negate: 2 else: 0) + (if B.negate: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      RuneSet.init(false, A.ranges + B.ranges)
    of 0b01:  # (false, true)
      RuneSet.init(true, B.ranges - A.ranges)
    of 0b10:  # (true, false)
      RuneSet.init(true, A.ranges - B.ranges)
    of 0b11:  # (true, true)
      RuneSet.init(true, A.ranges * B.ranges)
    else:  
      assert false
      RuneSet.init(true, @[])


proc `-`*(A, B: RuneSet): RuneSet =
  let A = emptyCache(A)
  let B = emptyCache(B)  
  let selector = (if A.negate: 2 else: 0) + (if B.negate: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      RuneSet.init(false, A.ranges - B.ranges)
    of 0b01:  # (false, true)
      RuneSet.init(false, A.ranges * B.ranges)
    of 0b10:  # (true, false)
      RuneSet.init(true, A.ranges + B.ranges)
    of 0b11:  # (true, true)
      RuneSet.init(false, B.ranges - A.ranges)
    else: 
      assert false
      RuneSet.init(false, @[])


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
  return RuneSet.init(neg, runeRanges)


proc rs*(s: string): RuneSet =
  ## parses "complex" rune sets that may be composed of unions or differences
  ## of basic rune sets. Examples:
  ## rs"""[_:]|[A-Z]|[a-z]|[\u00C0-\u00D6]|[\U00010000-\U000EFFFF]"""
  ## rs"[^<&\"]"
  ## rs"[\ufeff]|[\ufffe]|[\u0000][\ufeff]|[\ufffe][\u0000]"
  ## rs"[A-Za-z0-9._\-]"
  ## rs"A-Za-z"
  ## rs"[a-f][i-h]"
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

  template addOrSubtract(nextRC: RuneSet) = 
      if sign == '-':
        result = result - nextRC
      else:
        if result.ranges.len == 0:
          result = nextRC
        else:
          assert sign == '|', s[0..i]
          result = result + nextRC    
      sign = ' '

  result = RuneSet.init(false, @[])
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
      let nextRC = rs0(s[k ..< i])
      addOrSubtract(nextRC)
    else: 
      while i < s.len and s[i] in " \n":  i += 1
      if s[i] == '[' and sign == ' ':  sign = '|'
      addOrSubtract(parseRuneSet())

proc rs*(positive: bool, numberRanges: seq[(int, int)]): RuneSet = 
  var runeRanges: seq[RuneRange] = newSeqOfCap[RuneRange](numberRanges.len)
  for (a, b) in numberRanges:
    runeRanges.add((Rune(a), Rune(b)))
  RuneSet.init(not positive, runeRanges)

proc rs*(numberRanges: seq[(int, int)]): RuneSet = rs(true, numberRanges)

proc rs*(positive: bool, ranges: seq[RuneRange]): RuneSet = RuneSet.init(not positive, ranges)
proc rs*(ranges: seq[RuneRange]): RuneSet = rs(true, ranges)

proc rs*[T: Ordinal](positive: bool, s: set[T]): RuneSet = RuneSet.init(not positive, s)
proc rs*[T: Ordinal](s: set[T]): RuneSet = rs(true, s)


proc rr*(rangeStr: string): RuneRange =
  ## Parses a single rune range. Examples: rr"A-Z", rr"[a-z]".
  ##
  ## Inverse rune ranges are not possible. Neither are concatenations
  ## of rune ranges. The rune range may be enclosed by rectangular
  ## brackets, but does not need to be.
  let runes = rs(rangeStr)
  assert runes.ranges.len == 1
  return runes.ranges[0]


#######################################################################

when isMainModule:
  var rs1 = rs"""[_]|[:]|[A-Z]|[a-z]
                |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                |[\U00010000-\U000EFFFF]"""
  let rs2 = rs"[ace\sD-G]"
  let rs3 = rs"[a-f]|[^c-z0-9]|[24]"
  let rs6 = rs"[a-f][i-h]"
  let rs5 = rs"[a-z]-[d-g]"
  let rs7 = rs(false, {0x30, 0x31, 0x33, 0x35..0x39, 0x67..0x7A})
  let rs8 = rs(false, @[(0x30, 0x31), (0x33, 0x33), (0x35, 0x39), (0x67, 0x7A)])
  echo $rs3.ranges
  echo $rs7.ranges
  echo $rs8.ranges
  assert rs3.ranges == rs7.ranges
  assert rs3.negate == rs7.negate
  assert rs8 == rs3
  assert rs7 == rs3
  echo repr(rs3)
  echo repr(rs7)
  echo repr(rs8)
  echo $rs5
  echo repr(rs5)
  echo repr(rs5, false)
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
  echo repr(rs3)
  echo repr(rs3, false)
  let rs4 = rs"[acegikmo]"
  echo $rs4
  echo $rs4.ranges.len
  echo $(rs1.contains(rs1, Rune('a')))
  