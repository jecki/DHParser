# unit-tests for the strslice.nim module

import unittest

import nimparser/strslice


test "basic tests":
  let
    s1 = "Hello world"
    s2 = makeStringSlice("Hello world")
    s3 = s2.cut(6 .. ^1)
    s4 = s2.cut(2 .. ^1)
    s5 = toStringSlice("")
    s6 = toStringSlice("a")

  check s1.find("world") == 6
  check s2.find("world") == 6
  check s3.find("world") == 0
  check s2.find(s3) == 6
  check s2.find(s3, last = 8) == s1.find($s3, last = 8)
  check s2.find(s3, start = 8) == s1.find($s3, start = 8)
  check s3.find(s4) == -1

  var
    s = "0123456789"
    ss = s.toStringSlice
    upToFour = ss.cut(0..4)
    upToFive = ss.cut(0..5)
    upToSix = ss.cut(0..6)
    threeToFive = ss.cut(3..5)

  check s.find("123", last = 5) == ss.find("123", last = 5)
  check s.find("456", last = 5) == ss.find("456", last = 5)
  check s.find("789", last = 5) == s.find("789", last = 5)
  check s.find("123", start = 2) == ss.find("123", start = 2)
  check s.find("123", start = 2, last = 5) == ss.find("123", start = 2, last = 5)

  check s.find("456") != upToFive.find("456")
  check upToFive.find("456") == -1
  check s.find("456") == upToSix.find("456")

  check s.find("4") == threeToFive.find("4") + 3
  check upToFour.find(threeToFive) == -1

test "regular expression functions":
  let slice = makeStringSlice("abc 123 def 456 gh 78 ijk")
  check slice.matchLen(ure"\w+", 0) == 3
  check slice.matchLen(ure"[0-9]+", 0) == -1
  check slice.matchLen(ure"[0-9]+", 4) == 3
  check slice.matchLen(ure"[0-9]+", 19) == 2
  check slice.cut(19 .. ^1).matchLen(ure"[0-9]+", 0) == 2

  check slice.find(ure"[0-9]+") == (4'i32, 6'i32)
  check slice.find(ure"[0-9]+", 7) == (12'i32, 14'i32)
  check slice.find(ure"[0-9]+", 7, 4) == (-1'i32, -2'i32)
  check slice.cut(19 .. ^1).find(ure"[0-9]+") == (0'i32, 1'i32)

  check slice.cut(4..10).replace(ure"\d", "?") == "??? def"

test "edge cases":
  let one = makeStringSlice("1")
  check $one.cut(0..0) == "1"
  check $one.cut(0..1) == "1"
  check $one.cut(-1 .. 0) == "1"
  check $one.cut(-1 .. 1) == "1"
  check $one.cut(^1 .. 0) == "1"
  check $one.cut(^1 .. ^1) == "1"
  check $one.cut(0 .. ^1) == "1"
  check $one.cut(^2 .. ^1) == "1"  

  check $one.cut(1..1) == ""
  check $one.cut(1..0) == ""
  check $one.cut(1.. -1) == ""
