# unit-tests for the runerange.nim module
# To run these tests, simply execute `nimble test`.

import std/[unittest, strutils, unicode, algorithm, strformat]

import nimparser/runerange

test "String code for Rune-Ranges (rr and sr)":
  assert (rr"Ä-Ö").toRange() == (196'u32, 214'u32)
  assert (rr"\xC4-\xD6").toRange() == (196'u32, 214'u32)
  assert rs"a-z0-9\xc4-\xd6".ranges == @[rr"0-9", rr"a-z", rr"Ä-Ö"]
  assert rs"abc0-9äöü".ranges == @[rr"0-9", rr"a-c", rr"ä", rr"ö", rr"ü"]

test "inRuneRange":
  var rr: seq[RuneRange] = @[rr"2-4", rr"B-D", rr"b-d"]
  assert inRuneRange("1".runeAt(0), rr) < 0
  assert inRuneRange("2".runeAt(0), rr) >= 0
  assert inRuneRange("3".runeAt(0), rr) >= 0
  assert inRuneRange("4".runeAt(0), rr) >= 0
  assert inRuneRange("5".runeAt(0), rr) < 0

  assert inRuneRange("A".runeAt(0), rr) < 0
  assert inRuneRange("B".runeAt(0), rr) >= 0
  assert inRuneRange("C".runeAt(0), rr) >= 0
  assert inRuneRange("D".runeAt(0), rr) >= 0
  assert inRuneRange("E".runeAt(0), rr) < 0

  assert inRuneRange("a".runeAt(0), rr) < 0
  assert inRuneRange("b".runeAt(0), rr) >= 0
  assert inRuneRange("c".runeAt(0), rr) >= 0
  assert inRuneRange("d".runeAt(0), rr) >= 0
  assert inRuneRange("e".runeAt(0), rr) < 0

  rr = @[rr"2-4", rr"B-D", rr"U-W", rr"b-d"]
  assert inRuneRange("1".runeAt(0), rr) < 0
  assert inRuneRange("2".runeAt(0), rr) >= 0
  assert inRuneRange("3".runeAt(0), rr) >= 0
  assert inRuneRange("4".runeAt(0), rr) >= 0
  assert inRuneRange("5".runeAt(0), rr) < 0

  assert inRuneRange("A".runeAt(0), rr) < 0
  assert inRuneRange("B".runeAt(0), rr) >= 0
  assert inRuneRange("C".runeAt(0), rr) >= 0
  assert inRuneRange("D".runeAt(0), rr) >= 0
  assert inRuneRange("E".runeAt(0), rr) < 0

  assert inRuneRange("T".runeAt(0), rr) < 0
  assert inRuneRange("U".runeAt(0), rr) >= 0
  assert inRuneRange("V".runeAt(0), rr) >= 0
  assert inRuneRange("W".runeAt(0), rr) >= 0
  assert inRuneRange("X".runeAt(0), rr) < 0

  assert inRuneRange("a".runeAt(0), rr) < 0
  assert inRuneRange("b".runeAt(0), rr) >= 0
  assert inRuneRange("c".runeAt(0), rr) >= 0
  assert inRuneRange("d".runeAt(0), rr) >= 0
  assert inRuneRange("e".runeAt(0), rr) < 0

test "sortAndMerge":
  var rr: seq[RuneRange] = @[rr"2-5", rr"B-E", rr"H-K", rr"b-e", rr"h-p"]
  sortAndMerge(rr)
  assert rr == @[rr"2-5", rr"B-E", rr"H-K", rr"b-e", rr"h-p"]
  rr = @[rr"b-e", rr"2-5", rr"B-E", rr"C-K", rr"f-p"]
  sortAndMerge(rr)
  assert rr == @[rr"2-5", rr"B-K", rr"b-p", ]

test "Joining and Subtracting or Rune-Ranges":
  var m: seq[RuneRange] = @[rr"2-5", rr"B-E", rr"H-K", rr"b-e", rr"h-p"]
  assert ((m + @[rr"6-8", rr"A-C", rr"I-K", rr"c-d", rr"h-i", rr"j", rr"l-n"]) ==
          @[rr"2-8", rr"A-E", rr"H-K", rr"b-e", rr"h-p"])
  assert ((m - @[rr"6-8", rr"A-C", rr"I-K", rr"c-d", rr"h-i", rr"j", rr"l-n"]) ==
          @[rr"2-5", rr"D-E", rr"H", rr"b", rr"e", rr"k", rr"o-p"])
 #         "@[(low: 2, high: 5), (low: D, high: E), (low: H, high: H), (low: b, high: b), (low: e, high: e), (low: k, high: k), (low: o, high: p)]")
  assert (rs"0-4F-Ha-c".ranges * rs"2-7B-Gb".ranges) == rs"2-4F-Gb".ranges

test "RuneSet":
  assert (rs"A-C" + rs"X-Z") == rs"A-CX-Z"
  assert (rs"^A-Z" + rs"B-E") == rs"^AF-Z"
  assert (rs"A-C" + rs"^X-Z") == rs"^X-Z"
  assert (rs"A-D" + rs"^C-Z") == rs"^E-Z"
  assert (rs"^A-D" + rs"^C-Z") == rs"^C-D"
  # assert (rs"^A-D" + rs"^X-Z") == rs"^C-D" -> Empty or All not allowed

  assert (rs"A-Z" - rs"D-E") == rs"A-CF-Z"
  assert (rs"^A-Z" - rs"B-E") == rs"^A-Z"
  assert (rs"^A-G" - rs"F-K") == rs"^A-K"
  assert (rs"^A-G" - rs"^F-K") == rs"H-K"
  assert (rs"A-G" - rs"^F-K") == rs"F-G"

  var r = rs(r"\s")
  assert r.ranges.len == 3  # 9-10, 12-13, 20
  r = rs(r"\n")
  assert r.ranges.len == 1
