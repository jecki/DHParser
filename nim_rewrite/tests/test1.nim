# This is just an example to get you started. You may wish to put all of your
# tests into a single file, or separate them into multiple `test1`, `test2`
# etc. files (better names are recommended, just make sure the name starts with
# the letter 't').
#
# To run these tests, simply execute `nimble test`.

import unittest

import nimparser/nodetree
import nimparser/parse

test "Text, simple test":
  check Text("A")("A").node.asSxpr == "(:Text \"A\")"

test "Regex, simple test":
  check Regex(rx"\w+")("ABC").node.asSxpr() == "(:Regex \"ABC\")"

test "Alternative":
  check Alternative(Text("A"), Text("B"))("B").node.asSxpr == "(:Text \"B\")"
  check $Alternative(Text("A"), Text("B")) == "\"A\"|\"B\""
  check $((Text("A")|Text("B"))|(Text("C")|Text("D")|Text("E"))) == "\"A\"|\"B\"|\"C\"|\"D\"|\"E\""

test "Series":
  check $Series(Text("A"), Text("B"), Text("C"), mandatory=1u32) == "\"A\" §\"B\" \"C\""


test "parser-serialization":
  let root = "root".assign Forward()
  let t = "t".assign Text("A") & root
  let s = "s".assign root & t & t
  root.set(s)
  check $root == "s"
  check $t == "\"A\" s"
  check root.getSubParsers[0].getSubParsers.len == 3
  check $s == "s t t"
  check t.parserType == ":Series"
