## Bitsets
## =======
## 
## A nim library for arbitrairly sized bitsets.
## (Implementation is inspired by and partly copy/pasted from:
## https://nim-lang.org/docs/destructors.html)


import std/strformat


type
  MaskOp = enum setBit, clear, invert
  bitset* {.acyclic.} = object
    first, last: uint32
    base: uint32 # first shr 6 shl 6
    cap: uint32
    data: ptr UncheckedArray[uint64]


proc init*(bitset: type bitset, first, last: uint32): bitset =
  let base = first shr 6 shl 6
  let cap = last shr 6 shl 6 - base + 1
  bitset(first: first,
         last: last,
         base: base,
         cap: cap,
         data: cast[ptr UncheckedArray[uint64]](alloc(cap.int * sizeof(uint64))))

proc mask(bs: var bitset, first, last: uint32, mask: MaskOp) =
  ## Sets or clears or inverts all bits in the interval [a, b].
  var (a, b) = if first <= last: (first, last) else: (last, first) 
  if b < bs.first or a > bs.last:  return
  if a < bs.first:  a = bs.first
  if b > bs.last:   b = bs.last
  let 
    ai = (a - bs.base) shr 6
    bi = (b - bs.base) shr 6
    maskA = (1u64 shl (a and 0b111111) - 1) xor 0xFFFFFFFFFFFFFFFFu64
    maskB = 1u64 shl ((b and 0b111111) + 1) - 1
  case mask
    of setBit:
      for i in (ai + 1)..(bi - 1):  bs.data[i] = 0xFFFFFFFFFFFFFFFFu64
      bs.data[ai] = bs.data[ai] or maskA
      bs.data[bi] = bs.data[bi] or maskB
    of invert:
      for i in (ai + 1)..(bi - 1):  bs.data[i] = bs.data[i] xor 0xFFFFFFFFFFFFFFFFu64
      bs.data[ai] = bs.data[ai] xor maskA
      bs.data[bi] = bs.data[bi] xor maskB
    of clear:
      for i in (ai + 1)..(bi - 1):  bs.data[i] = 0u64
      bs.data[ai] = bs.data[ai] and (maskA xor 0xFFFFFFFFFFFFFFFFu64)
      bs.data[bi] = bs.data[bi] and (maskB xor 0xFFFFFFFFFFFFFFFFu64)    

proc mask(bs: var bitset, first, last: uint32, mask: bool) =
  ## Sets or clears all bits in the interval [a, b].
  mask(bs, first, last, if mask: setBit else: clear) 

proc extend(bs: var bitset, first, last: uint32): bitset =  # TODO: Maybe this is not even needed
  ## Extend the bitset so that the interval [first, last] is also covered
  var (a, b) = if first <= last: (first, last) else: (last, first) 
  if a > bs.first: a = bs.first
  if b < bs.last: b = bs.last
  let newBase = a shr 6 shl 6
  let newCap = b shr 6 shl 6 - newBase + 1
  if newCap > bs.cap:
    var data = cast[ptr UncheckedArray[uint64]](alloc(newCap.int * sizeof(uint64)))
    let delta = (bs.base shr 6) - (newBase shr 6)
    assert delta <= newCap - bs.cap
    for i in 0..<bs.cap:
      data[i + delta] = bs.data[i]
    dealloc(bs.data)
    bs.first = a
    bs.last = b
    bs.base = newBase
    bs.cap = newCap
    bs.data = data

proc `=destroy`*(bs: bitset) =
  if bs.data != nil:
    dealloc(bs.data)

proc `=wasMoved`*(bs: var bitset) =
  bs.data = nil

# proc `=trace`(bs: var bitset; env: pointer) =
# not implemented, because bitsets cannot be cyclic

proc `=copy`*(a: var bitset; b: bitset) =
  # do nothing for self-assignments:
  if a.data == b.data: return
  `=destroy`(a)
  `=wasMoved`(a)
  a.first = b.first
  a.last = b.last
  a.base = b.base
  a.cap = b.cap
  if b.data != nil:
    a.data = cast[typeof(a.data)](alloc(a.cap.int * sizeof(uint64)))
    for i in 0..<a.cap:
      a.data[i] = b.data[i]

proc `=dup`*(a: bitset): bitset {.nodestroy.} =
  # an optimized version of `=wasMoved(tmp); `=copy(tmp, src)`
  # usually present if a custom `=copy` hook is overridden
  result = bitset(first: a.first, last: a.last, base: a.base, cap: a.cap, data: nil)
  if a.data != nil:
    result.data = cast[typeof(result.data)](alloc(result.cap.int * sizeof(uint64)))
    for i in 0..<result.cap:
      result.data[i] = `=dup`(a.data[i])

proc `=sink`*(a: var bitset; b: bitset) =
  # move assignment, optional.
  # Compiler is using `=destroy` and `copyMem` when not provided
  `=destroy`(a)
  a.first = b.first
  a.last = b.last
  a.base = b.base
  a.cap = b.cap
  a.data = b.data

proc `[]`*(bs: bitset; i: Natural): bool =
  let n = i.uint32
  if n < bs.first or n > bs.last:
    false
  else:
    let bit = n - bs.base
    let idx = bit shr 6
    let b = 1u64 shl (bit - (idx shl 6))
    bool(b and bs.data[idx])

proc `[]=`*(bs: var bitset; i: Natural; b: bool) =
  let n = i.uint32
  if n < bs.first or n > bs.last:
    # TODO: automatically extend bitset size, here
    raise newException(RangeDefect, fmt"Element {i} is out of bounds [{bs.first}, {bs.last}]")
  let bit = n - bs.base
  let idx = bit shr 6
  let b = 1u64 shl (bit - (idx shl 6))
  bs.data[idx] = bs.data[idx] or b
  
proc len*(bs: bitset): uint32 {.inline.} = bs.last - bs.first + 1

# TODO: Implement all set operators

proc `+`*(a, b: bitset): bitset = 
  discard

proc `*`*(a, b: bitset): bitset = 
  discard

proc `-`*(a, b: bitset): bitset = 
  discard

proc `^`*(bs: bitset): bitset =
  discard

proc `-+-`*(a, b: bitset): bitset =
  discard

proc `==`*(a, b: bitset): bool = 
  discard

proc `<=`*(a, b: bitset): bool = 
  discard

proc `<`*(a, b: bitset): bool = 
  discard

proc `in`*(i: Natural, bs: bitset): bool =
  discard

proc `notin`*(i: Natural, bs: bitset): bool =
  discard

proc contains(bs: bitset, i: Natural): bool =
  discard

proc card(bs: bitset): uint32 =
  discard

proc incl(bs: bitset, i: Natural): bool =
  discard

proc excl(bs: bitset, i: Natural): bool =
  discard

proc complement(bs: bitset): bitset =
  discard

proc invert(bs: var bitset) =  # inplace-complement
  discard

proc fullSet(slice: HSlice): bitset =
  discard

proc symmetricDifference(a, b: bitset): bitset =
  discard

proc toggle(a: var bitset, b: bitset) = 
  discard

template toSet(iter: untyped): untyped =
  discard

