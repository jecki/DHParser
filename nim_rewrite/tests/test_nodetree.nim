# unit-tests for the nodetree.nim module

import unittest

import nimparser/strslice
import nimparser/nodetree

test "Node.content":
  let slice = toStringSlice("ABC")
  var slice2 = toStringSlice(slice)
  var node = newNode("TEST", slice2.cut(1..0))
  check node.content == ""
  node = newNode("TEXT", slice2.cut(1..^1))
  check node.content == "BC"


