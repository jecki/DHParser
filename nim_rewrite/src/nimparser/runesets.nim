## Rune Sets
## =========
##
## A module that defines data-types and functions for handling character
## ranges and sets on the basis of nim's unicode-runes.
##
## The data-types include plain rune-ranges, e.g. [A-Z]
## or, say [\u037F-\u1FFF], negative ranges, e.g. [^0-9] (not a digit) as
## well as unions or intersections of such ranges.
##
## The functions allow to normalize (sortAndMerge()) sequences of rune
## ranges, query for inclusion (isInRuneRange()) in logarithmic time,
## perform basic algrbraic operations (like intersecting * , joining + ,
## building the difference -, negating ^), and finally to build rune sets
## from string-descriptions similar to regular expression ranges,
## e.g. rs"abcdefg" rs"^A-F"


{.experimental: "strictNotNil".}
{.experimental: "strictFuncs".}
{.experimental: "strictDefs".}
{.experimental: "strictCaseObjects".}
# {.experimental: "codeReordering".}


import std/[algorithm, strformat, strutils, unicode]


proc nilRefError(fieldName: string): ref AssertionDefect =
  newException(AssertionDefect, fmt"{fieldName} unexpectedly nil!")


type
  IsContainedProc = proc(r: Rune, collection: var RuneCollection): bool {.nimcall.}

  RuneRange* = tuple[low: Rune, high: Rune]

  SetSize* = enum interval, size256, size4k, size64k
  RuneSet* = object
    low: Rune
    high: Rune
    case size: SetSize
    of size256: set256: ref set[0 .. 255]
    of size4k:  set4k:  ref set[0 .. 4095]
    of size64k: set64k: ref set[0 .. 65535]
    else: discard

  RuneCollection* = object
    negate*: bool
    ranges*: seq[RuneRange]  # if empty, only a single set will be used!
    sets: seq[RuneSet]  # if not empty, an optimized version of ranges!
    contains*: IsContainedProc not nil

const
  EmptyRuneRange* = (Rune('b'), Rune('a'))


proc `$`*(range: RuneRange): string =
  let
    min = range.low.uint32
    max = range.high.uint32
  if min <= max:  fmt"{min}..{max}"  else: "EMPTY"


proc init*(RuneSet: type RuneSet, low, high: Rune, size: SetSize): 
  RuneSet {.raises: [RangeDefect].} =
  var
    a: uint32 = low.uint32
    b: uint32 = high.uint32

  proc getFrame(frameSize: uint32): tuple[first: Rune, last: Rune] =
    assert frameSize in [256u32, 4069u32, 65536u32]
    var 
      i = a div frameSize
      k = b div frameSize
    if i != k:
      raise newException(RangeDefect, 
        fmt"Interval [{a}, {b}] does not fit into a single {frameSize}-runes-frame!")
    i *= frameSize
    k = i + frameSize - 1
    (Rune(i), Rune(k))    

  case size
    of interval:
      result = RuneSet(low: low, high: high, size: interval)
    of size256:
      var (i, k) = getFrame(256u32)
      result = RuneSet(low: i, high: i, size: size256, set256: new(ref set[0..255]))
      result.set256[] = {a..b}
    of size4k:
      var (i, k) = getFrame(4096u32)
      result = RuneSet(low: i, high: i, size: size4k, set4k: new(ref set[0..4095]))
      result.set4k[] = {a..b}
    of size64k:
      var (i, k) = getFrame(65536u32)
      result = RuneSet(low: i, high: i, size: size64k, set64k: new(ref set[0..65535]))
      result.set4k[] = {a..b}


template inRuneSet(code: uint32, runeSet: RuneSet): bool =
  # let rset = runeSet
  case runeSet.size
  of size256: code in runeSet.set256[]
  of size4k:  code in runeSet.set4k[]
  of size64k: code in runeSet.set64k[]
  else: 
    # if no set is specified, it is assumed that the set covers
    # the entire enclosing range
    true  


template inSetOf[T: RuneRange|RuneSet](r: Rune, ctnr: T): bool =
  ## Checks whether r also falls into the set attached to the rune
  ## container. It is assumed as a precondition that r already 
  ## falls into the range (low, high) of the container.
  when T is RuneRange:
    true
  else:
    inRuneSet(r.uint32 - ctnr.low.uint32, ctnr)


func inRuneRanges*[T: RuneRange|RuneSet](r: Rune, containers: seq[T]): bool =
  ## Binary search to find out if rune r is in one of the containers
  ## It is assumed that the containers are sorted and do not overlap.
  let
    highest: int32 = containers.len.int32 - 1'i32
  var
    a = 0'i32
    b = highest
    last_i = -1'i32
    i = b shr 1  # div 2

  while i != last_i:
    let rng = containers[i]
    if rng.low <=% r:
      if r <=% rng.high:
        return r.inSetOf(rng)
      else:
        a = min(i + 1, highest)
    else:
      b = max(i - 1, 0)
    last_i = i
    i = a + (b - a) shr 1  # div 2
  return false


proc inRanges(r: Rune, collection: var RuneCollection): bool =
  collection.negate xor inRuneRanges(r, collection.ranges)

proc inSingleRange(r: Rune, collection: var RuneCollection): bool =
  let rng = collection.ranges[0]
  collection.negate xor (rng.low <=% r and r <=% rng.high)

proc inSets(r: Rune, collection: var RuneCollection): bool =
  collection.negate xor inRuneRanges(r, collection.sets)

proc inSingleSet(r: Rune, collection: var RuneCollection): bool =
  let rset = collection.sets[0]
  collection.negate xor inRuneSet(r.uint32 - rset.low.uint32, rset)

proc inZeroBasedSet(r: Rune, collection: var RuneCollection): bool =
  let rset = collection.sets[0]
  collection.negate xor inRuneSet(r.uint32, rset)


proc initialContainedIn(r: Rune, collection: var RuneCollection): bool =
  # TODO: optimize and select the best isContainedProc.
  collection.negate xor inRuneRanges(r, collection.ranges)


func RC*(negate: bool, ranges: seq[RuneRange]): RuneCollection =
  RuneCollection(negate: negate, ranges: ranges, sets: @[], 
                 contains: initialContainedIn)

func RC*(negate: bool, rs: RuneSet): RuneCollection =
  if rs.low.uint32 == 0:
    RuneCollection(negate: negate, ranges: @[], sets: @[rs], 
                   contains: inZeroBasedSet)
  else:
    RuneCollection(negate: negate, ranges: @[], sets: @[rs], 
                   contains: inSingleSet)


proc `==`*(a, b: RuneCollection): bool =
  a.negate == b.negate and a.ranges == b.ranges


proc `$`*(rc: RuneCollection, verbose: bool = false): string =
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

  var s: seq[string] = newSeqOfCap[string](max(rc.ranges.len, rc.sets.len) + 2)
  let ranges: seq[RuneRange] = if rc.ranges.len > 0: rc.ranges 
                               else: @[(rc.sets[0].low, rc.sets[0].high)]  

  if rc.ranges.len == 0 and rc.sets[0].size != interval:
    assert rc.sets.len == 1
    let rs = rc.sets[0]
    s.add("{")
    case rs.size
    of size256: s.add($rs.set256[])
    of size4k:  s.add($rs.set4k[])
    of size64k: s.add($rs.set64k[])
    else: discard
    s.add("}")
  else:
    if not verbose:
      s.add("[")
      if rc.negate: s.add("^")
    for rr in ranges:
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
      s = if rc.negate: @["[^", s.join("]-["), "]"] else: @["[", s.join("]|["), "]"]
    else:
      s.add("]")
  s.join("")


proc `$`*(rr: seq[RuneRange], verbose=false): string = RC(false, rr) $ verbose
proc `$`*(rr: RuneRange): string = $(@[rr])
proc `$`*(rs: RuneSet): string = $RC(false, rs)


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
func size(R: seq[RuneRange]): uint32 =
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


## RuneSet Combinators

# proc `+`*(A, B: RuneSet): RuneSet =
#   discard



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


## Rune Collection Combinators


proc `^`*(runes: RuneCollection): RuneCollection = 
  RuneCollection(negate: not runes.negate, ranges: runes.ranges, sets: runes.sets, contains: runes.contains)


proc `+`*(A, B: RuneCollection): RuneCollection =
  let selector = (if A.negate: 2 else: 0) + (if B.negate: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      RC(false, A.ranges + B.ranges)
    of 0b01:  # (false, true)
      RC(true, B.ranges - A.ranges)
    of 0b10:  # (true, false)
      RC(true, A.ranges - B.ranges)
    of 0b11:  # (true, true)
      RC(true, A.ranges * B.ranges)
    else:  
      assert false
      RC(true, @[])


proc `-`*(A, B: RuneCollection): RuneCollection =
  let selector = (if A.negate: 2 else: 0) + (if B.negate: 1 else: 0)
  case selector:  # (A.negate, B.negate)
    of 0b00:  # (false, false)
      RC(false, A.ranges - B.ranges)
    of 0b01:  # (false, true)
      RC(false, A.ranges * B.ranges)
    of 0b10:  # (true, false)
      RC(true, A.ranges + B.ranges)
    of 0b11:  # (true, true)
      RC(false, B.ranges - A.ranges)
    else: 
      assert false
      RC(false, @[])


## Rune range and rune set parsers

proc rs0*(rangesStr: string): RuneCollection =
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
  return RC(negate, runeRanges)


proc rs*(s: string): RuneCollection =
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

  proc parseRuneCollection(): RuneCollection =
    assert i < s.len
    assert s[i] == '[', $i
    let k = i + 1
    while i < s.len and (s[i] != ']' or (i > 0 and s[i-1] == '\\')):  i += 1
    assert i < s.len
    result = rs0(s[k ..< i])
    i += 1

  template addOrSubtract(nextRC: RuneCollection) = 
      if sign == '-':
        result = result - nextRC
      else:
        if result.ranges.len == 0:
          result = nextRC
        else:
          assert sign == '|', s[0..i]
          result = result + nextRC    
      sign = ' '

  result = RC(false, @[])
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
      addOrSubtract(parseRuneCollection())


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
  var rs1 = rs"""[_]|[:]|[A-Z]|[a-z]
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
  let rs4 = rs"[acegikmo]"
  echo $rs4
  echo $rs4.ranges.len
  echo $(rs1.contains(Rune('a'), rs1))
  