# unit-tests for the strslice.nim module

import unittest

import nimparser/strslice


test "basic tests":
  let
    s1 = "Hello world"
    s2 = makeStringSlice("Hello world")
    s3 = s2[6i32 .. ^1]
    s4 = s2[2i32 .. ^1]
    s5 = toStringSlice("")
    s6 = toStringSlice("a")

  assert s1.find("world") == 6
  assert s2.find("world") == 6
  assert s3.find("world") == 0
  assert s2.find(s3) == 6
  assert s2.find(s3, last = 8) == s1.find($s3, last = 8)
  assert s2.find(s3, start = 8) == s1.find($s3, start = 8)
  assert s3.find(s4) == -1

  var
    s = "0123456789"
    ss = s.toStringSlice
    upToFour = ss[0i32..4i32]
    upToFive = ss[0i32..5i32]
    upToSix = ss[0i32..6i32]
    threeToFive = ss[3i32..5i32]

  assert s.find("123", last = 5) == ss.find("123", last = 5)
  assert s.find("456", last = 5) == ss.find("456", last = 5)
  assert s.find("789", last = 5) == s.find("789", last = 5)
  assert s.find("123", start = 2) == ss.find("123", start = 2)
  assert s.find("123", start = 2, last = 5) == ss.find("123", start = 2, last = 5)

  assert s.find("456") != upToFive.find("456")
  assert upToFive.find("456") == -1
  assert s.find("456") == upToSix.find("456")

  assert s.find("4") == threeToFive.find("4") + 3
  assert upToFour.find(threeToFive) == -1

test "regular expression functions":
  let slice = makeStringSlice("abc 123 def 456 gh 78 ijk")
  assert slice.matchLen(re"\w+", 0) == 3
  assert slice.matchLen(re"[0-9]+", 0) == -1
  assert slice.matchLen(re"[0-9]+", 4) == 3
  assert slice.matchLen(re"[0-9]+", 19) == 2
  assert slice[19 .. ^1].matchLen(re"[0-9]+", 0) == 2

  assert slice.find(re"[0-9]+") == (4'i32, 6'i32)
  assert slice.find(re"[0-9]+", 7) == (12'i32, 14'i32)
  assert slice.find(re"[0-9]+", 7, 4) == (-1'i32, -2'i32)
  assert slice[19 .. ^1].find(re"[0-9]+") == (0'i32, 1'i32)

  assert slice[4..10].replace(re"\d", "?") == "??? def"