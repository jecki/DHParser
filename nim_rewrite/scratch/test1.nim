# unit-tests for the parse.nim module

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

test "RegExp, simple test":
  check RegExp(rx"\w+")("ABC").node.asSxpr() == "(:RegExp \"ABC\")"

test "RegExp in sequence":
  let number = "number".assign RegExp(rx"\d+")
  let ws = "ws".assign RegExp(rx"\s*")
  let text = toStringSlice("1")
  check number(text, 0).node.asSxpr == "(number \"1\")"
  check ws(text, 1).node.asSxpr == "(ws \"\")"

test "Alternative":
  check Alternative(Text("A"), Text("B"))("B").node.asSxpr == "(:Text \"B\")"
  check $Alternative(Text("A"), Text("B")) == "\"A\"|\"B\""
  check $((Text("A")|Text("B"))|(Text("C")|Text("D")|Text("E"))) == "\"A\"|\"B\"|\"C\"|\"D\"|\"E\""

test "Series":
  check $Series(Text("A"), Text("B"), Text("C"), mandatory=1u32) == "\"A\" §\"B\" \"C\""
  check $(txt"A" & Required(txt"B" & txt"C")) == "\"A\" §\"B\" \"C\""
  check $(txt"A" & Required(txt"B", txt"C")) == "\"A\" §\"B\" \"C\""

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
  let WS  = "WS".assign                DROP(rxp"\s*")
  let NUMBER = ":NUMBER".assign         (rxp"(?:0|(?:[1-9]\d*))(?:\.\d+)?" & WS)
  let sign = "sign".assign             ((txt"+" | txt"-") & WS)
  let expression = "expression".assign Forward()
  let group = "group".assign           (txt"(" & WS & expression & txt")" & WS)
  let factor = "factor".assign         (Option(sign) & (NUMBER | group))
  let term = "term".assign             (factor & ZeroOrMore((txt"*" | txt"/") & WS & factor))
  expression.set                       (term & ZeroOrMore((txt"+" | txt"-") & WS & term))
  expression.grammar = Grammar("Arithmetic")

  var result = expression("1 + 1")
  assert $result.node == """
(expression
  (term
    (factor "1"))
  (:Text "+")
  (term
    (factor "1")))"""
