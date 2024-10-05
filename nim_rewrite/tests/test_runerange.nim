# unit-tests for the runerange.nim module
# To run these tests, simply execute `nimble test`.

import std/[unittest, strutils, unicode, algorithm, strformat]

import nimparser/runerange

test "String code for Rune-Ranges (rr and sr)":
  assert (rr"Ä-Ö").toRange() == (196'u32, 214'u32)
  assert (rr"\xC4-\xD6").toRange() == (196'u32, 214'u32)
  assert rs0"a-z0-9\xc4-\xd6".ranges == @[rr"0-9", rr"a-z", rr"Ä-Ö"]
  assert rs0"abc0-9äöü".ranges == @[rr"0-9", rr"a-c", rr"ä", rr"ö", rr"ü"]

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
  assert (rs0"0-4F-Ha-c".ranges * rs0"2-7B-Gb".ranges) == rs0"2-4F-Gb".ranges

test "RuneSet":
  assert (rs0"A-C" + rs0"X-Z") == rs0"A-CX-Z"
  assert (rs0"^A-Z" + rs0"B-E") == rs0"^AF-Z"
  assert (rs0"A-C" + rs0"^X-Z") == rs0"^X-Z"
  assert (rs0"A-D" + rs0"^C-Z") == rs0"^E-Z"
  assert (rs0"^A-D" + rs0"^C-Z") == rs0"^C-D"
  # assert (rs"^A-D" + rs"^X-Z") == rs"^C-D" -> Empty or All not allowed

  assert (rs0"A-Z" - rs0"D-E") == rs0"A-CF-Z"
  assert (rs0"^A-Z" - rs0"B-E") == rs0"^A-Z"
  assert (rs0"^A-G" - rs0"F-K") == rs0"^A-K"
  assert (rs0"^A-G" - rs0"^F-K") == rs0"H-K"
  assert (rs0"A-G" - rs0"^F-K") == rs0"F-G"

  var r = rs0(r"\s")
  assert r.ranges.len == 3  # 9-10, 12-13, 20
  r = rs0(r"\n")
  assert r.ranges.len == 1
