## Rune Sets
## =========
##
## A module that defines data-types and functions for handling character
## sets on the basis of nim's unicode-runes and rune ranges as defined in 
## runeranges.nim
##
## A RuneSet is basically a sequnce of rune ranges that are non-overlapping,
## non-adjacent and sorted in ascending order. The "negate" flag indicates 
## whether the set is a positive or negative set. If true, the elements 
## outside the ranges are part of the set. Thus, the "ranges"-field and the 
## "negate"-flag of the RuneSet object define the set completely. All other 
## fields just serve to speed up the "contains" operation. 
## 
## The cache fields fields (cache256, cache4k, cache64k) are used to redundantly 
## store the elements in the whole sequence of ranges or of the lower part of
## it (up to code point 0xFFFF) in set form which allows for very fast
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
import runeranges

type
  ContainsProc = proc(rs: var RuneSet, r: Rune): bool {.nimcall.}
  Set256* = set[0..255]
  Set4K* = set[0..4095]
  Set64K* = set[0..65535]
  RuneSet* {.acyclic.} = object  
    negate*: bool
    allRanges: seq[RuneRange]
    uncached: seq[RuneRange]
    cache256: ref Set256
    cache4k:  ref Set4k
    cache64k: ref Set64k
    contains*: ContainsProc not nil

func ranges*(rs: RuneSet): seq[RuneRange] =
  ## Returns the sequence of ranges that define the rune set.
  ## If the rune set was initialized with an empty sequence of ranges
  ## but with a cache, the sequence of ranges is computed from the cache.
  if rs.allRanges.len == 0:
    if not isNil(rs.cache256):
      result = toRanges(rs.cache256[], Rune) 
    elif not isNil(rs.cache4k):
      result = toRanges(rs.cache4k[], Rune) 
    elif not isNil(rs.cache64k):
      result = toRanges(rs.cache64k[], Rune)
    else:
      result = rs.allRanges
  else:
    result = rs.allRanges
    
proc inRanges(rs: var RuneSet, r: Rune): bool = rs.negate xor contains(rs.allRanges, r)
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

proc cacheSome[T: Set256|Set4k|Set64k](rs: var RuneSet, cache: var ref T) = 
  when T is Set256: 
    let cacheSize: uint32 = 256
  when T is Set4k:  
    let cacheSize: uint32 = 4096
  when T is Set64k: 
    let cacheSize: uint32 = 65536
  new(cache)
  let upperLimit = (cacheSize - 1).uint16
  for rr in rs.ranges:
    if rr.low.uint32 < cacheSize:
      cache[] = cache[] + {rr.low.uint16..min(rr.high.uint16, upperLimit)}
    else:
      rs.uncached.add(rr)

proc cache(rs: var RuneSet) =
  if rs.allRanges.len == 0:
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
      cacheSome(rs, rs.cache64k)
      rs.contains = inRangesOrCache64k
    elif m > 8:
      cacheSome(rs, rs.cache4k)
      rs.contains = inRangesOrCache4k
    elif s > 4:
      cacheSome(rs, rs.cache256)
      rs.contains = inRangesOrCache256 
    else:
      rs.contains = inRanges

proc precached*(rs: RuneSet): RuneSet =
  ## Returns a copy of the RuneSet with all cache fields and ranges set up.
  result = RuneSet(negate: rs.negate, 
                   allRanges: rs.ranges,
                   uncached: @[],
                   cache256: rs.cache256, 
                   cache4k: rs.cache4k, 
                   cache64k: rs.cache64k, 
                   contains: rs.contains)
  if isNil(rs.cache256) and isNil(rs.cache4k) and isNil(rs.cache64k):
    cache(result)

proc inRuneSet_firstRun(rs: var RuneSet, r: Rune): bool =
  cache(rs)
  rs.contains(rs, r)


func init*(RuneSet: type, neg: bool, ranges: seq[RuneRange]): RuneSet =
  RuneSet(negate: neg, allRanges: ranges, uncached: @[],
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
          allRanges: @[],  
          uncached: @[],
          cache256: cref, cache4k: nil, cache64k: nil, 
          contains: inCache256)

proc init*(RuneSet: type, neg: bool, cache: Set4k): RuneSet =
  var cref = new(Set4k)
  cref[] = cache
  RuneSet(negate: neg, 
          allRanges: @[], 
          uncached: @[],
          cache256: nil, cache4k: cref, cache64k: nil, 
          contains: inCache4k)

proc init*(RuneSet: type, neg: bool, cache: Set64k): RuneSet =
  var cref = new(Set64k)
  cref[] = cache
  RuneSet(negate: neg, 
          allRanges: @[],
          uncached: @[],
          cache256: nil, cache4k: nil, cache64k: cref, 
          contains: inCache64k)


func emptyCache(rs: RuneSet): RuneSet =
  ## Returns a copy of the RuneSet with all cache fields set to nil
  RuneSet(negate: rs.negate, 
          allRanges: rs.ranges,
          uncached: @[],
          cache256: nil, cache4k: nil, cache64k: nil, 
          contains: inRuneSet_firstRun)


func `==`*(a, b: RuneSet): bool =
  a.negate == b.negate and a.ranges == b.ranges


func `$`*(rs: RuneSet, verbose: bool = false): string =
  ## Serializes rune set. Use "runeset $ true" for a more
  ## verbose and easier-to-read serialization.

  func hexlen(r: Rune): (int8, string) =
    let i = r.int32
    if i < 1 shl 8: return (2, r"\x")
    elif i < 1 shl 16:  return (4, r"\u")
    else: return (8, r"\U")

  func isAlphaNum(rr: RuneRange): bool =
    func isIn(a, b, x, y: int32): bool =
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


func `$`*(rr: seq[RuneRange], verbose=false): string = RuneSet.init(false, rr) $ verbose
func `$`*(rr: RuneRange): string = $(@[rr])


func repr*(rs: RuneSet, asSet: bool=true): string =
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


## RuneSet Combinators

func `^`*(runes: RuneSet): RuneSet = 
  RuneSet(negate: not runes.negate, allRanges: runes.ranges, uncached: runes.uncached,
          cache256: runes.cache256, cache4k: runes.cache4k, cache64k: runes.cache64k,
          contains: runes.contains)

proc `+`*(A, B: RuneSet): RuneSet =
  let A = emptyCache(A)
  let B = emptyCache(B)
  let (negate, ranges) = add(A.negate, B.negate, A.ranges, B.ranges)
  RuneSet.init(negate, ranges)

proc `-`*(A, B: RuneSet): RuneSet =
  let A = emptyCache(A)
  let B = emptyCache(B)  
  let (negate, ranges) = sub(A.negate, B.negate, A.ranges, B.ranges)
  RuneSet.init(negate, ranges)


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

  let neg: bool = if rangesStr.len > 0 and rangesStr[0] == '^': true  else: false
  RuneSet.init(neg, rrs(rangesStr))


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


#######################################################################


const s: Set4K = {0x30, 0x31, 0x33, 0x35..0x39, 0x67..0x77A}
const t = toRanges(s, Rune)

# const rs7 = rs[uint16](s)
# const rs8 = rs(false, @[(0x30, 0x31), (0x33, 0x33), (0x35, 0x39), (0x67, 0x7A)])


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
  echo $rs6
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
  