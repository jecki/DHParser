# This is just an example to get you started. You may wish to put all of your
# tests into a single file, or separate them into multiple `test1`, `test2`
# etc. files (better names are recommended, just make sure the name starts with
# the letter 't').
#
# To run these tests, simply execute `nimble test`.

import unittest

import nimparser/strslice
import nimparser/nodetree
import nimparser/parse

test "Node.content":
  let slice = toStringSlice("ABC")
  var slice2 = toStringSlice(slice)
  var node = newNode("TEST", slice2[1..0])
  check node.content == ""
  node = newNode("TEXT", slice2[1..^1])
  check node.content == "BC"

test "Text, simple test":
  check Text("A")("A").node.asSxpr == "(:Text \"A\")"

test "Regex, simple test":
  check Regex(rx"\w+")("ABC").node.asSxpr() == "(:Regex \"ABC\")"

test "Regex in sequence":
  let number = "number".assign Regex(rx"\d+")
  let ws = "ws".assign Regex(rx"\s*")
  let text = toStringSlice("1")
  check number(text, 0).node.asSxpr == "(number \"1\")"
  check ws(text, 1).node.asSxpr == "(ws \"\")"

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

test "arithmetic":
  let WS  = ":WS".assign               Drop(Regex(rx"\s*"))
  let NUMBER = ":NUMBER".assign        (Regex(rx"(?:0|(?:[1-9]\d*))(?:\.\d+)?") & WS)
  let sign = "sign".assign             ((Text("+") | Text("-")) & WS)
  let expression = "expression".assign Forward()
  let group = "group".assign           (Text("(") & WS & expression & Text(")") & WS)
  let factor = "factor".assign         (Option(sign) & (NUMBER | group))
  let term = "term".assign             (factor & ZeroOrMore((Text("*") | Text("/")) & WS & factor))
  expression.set                       (term & ZeroOrMore((Text("+") | Text("-")) & WS & term))
  expression.grammar = Grammar("Arithmetic")

  echo $factor("1").node
  echo $term("1+1").node
  var result = expression("1 + 1")
  echo $result.node