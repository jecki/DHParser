# unit-tests for the parse.nim module

# To run these tests, simply execute `nimble test`.

import std/[unittest, strutils]

import nimparser/strslice
import nimparser/nodetree
import nimparser/parse

test "Text, simple test":
  check Text("A")("A").node.asSxpr == "(:Text \"A\")"

test "RegExp, simple test":
  check RegExp(rx"\w+")("ABC").node.asSxpr() == "(:RegExp \"ABC\")"

test "RegExp in sequence":
  let number = "number".assign RegExp(rx"\d+")
  let ws = "ws".assign RegExp(rx"\s*")
  let text = toStringSlice("1")
  check number(text, 0).node.asSxpr == "(number \"1\")"
  check ws(text, 1).node.asSxpr == "(ws \"\")"

test "Whitespace":
  let ws = ":ws".assign Whitespace(r"\s+", r"#.*")
  echo $ws("   # comment").node.asSxpr
  doAssert ws("   # comment").node.asSxpr == "(:ws \"   # comment\")"

test "Alternative":
  check Alternative(Text("A"), Text("B"))("B").node.asSxpr == "(:Text \"B\")"
  check $Alternative(Text("A"), Text("B")) == "\"A\"|\"B\""
  check $((Text("A")|Text("B"))|(Text("C")|Text("D")|Text("E"))) == "\"A\"|\"B\"|\"C\"|\"D\"|\"E\""

test "Series":
  check $Series(Text("A"), Text("B"), Text("C"), mandatory=1u32) == "\"A\" §\"B\" \"C\""
  check $(txt"A" & §(txt"B" & txt"C")) == "\"A\" §\"B\" \"C\""
  # check $(txt"A" & Required(txt"B", txt"C")) == "\"A\" §\"B\" \"C\""
  check $(txt"A" & txt"B" & § txt"C" & txt"D") == "\"A\" \"B\" §\"C\" \"D\""

test "parser-serialization":
  let root = "root".assign Forward()
  let t = "t".assign Text("A") & root
  let s = "s".assign root & t & t
  root.set(s)
  check $root == "s"
  check $t == "\"A\" s"
  check root.getSubParsers[0].getSubParsers.len == 3
  check $s == "s t t"
  check t.type == ":Series"

let WS  = "WS".assign                DROP(rxp"\s*")
let NUMBER = ":NUMBER".assign        rxp"(?:0|(?:[1-9]\d*))(?:\.\d+)?" & WS
let sign = "sign".assign             ((txt"+" | txt"-") & WS)
let expression = "expression".assign Forward()
let group = "group".assign           (txt"(" & WS & § expression & txt")" & WS)
let factor = "factor".assign         (Option(sign) & (NUMBER | group))
let term = "term".assign             (factor & ZeroOrMore((txt"*" | txt"/") & WS & § factor))
expression.set                       (term & ZeroOrMore((txt"+" | txt"-") & WS & § term))
expression.grammar = Grammar("Arithmetic")
let arithmetic = expression

test "arithmetic":
  var result = arithmetic("1 + 1")
  assert $result.node == """
(expression
  (term
    (factor "1"))
  (:Text "+")
  (term
    (factor "1")))"""

test "arithmetic error catching":
  var tree: NodeOrNil
  try:
    tree = expression("(3 + ) * 2").node
    check false
  except ParsingException as pe:
    check pe.error.pos == 5
  try:
    tree = expression("(3 + * 2").node
    check false
  except ParsingException as pe:
    check pe.error.pos == 5
  try:
    tree = expression("(3 + 4 * 2").node
    check false
  except ParsingException as pe:
    check pe.error.pos == 10


let traversalExpected = """
expression := expression
expression := term {("+"|"-") WS §term}
term := factor {("*"|"/") WS §factor}
factor := [sign] (NUMBER|group)
[sign]
sign := ("+"|"-") WS
"+"|"-"
"+"
"-"
WS := /\s*/
NUMBER|group
NUMBER := /(?:0|(?:[1-9]\d*))(?:\.\d+)?/ WS
/(?:0|(?:[1-9]\d*))(?:\.\d+)?/
group := "(" WS §expression ")" WS
"("
")"
{("*"|"/") WS §factor}
("*"|"/") WS §factor
"*"|"/"
"*"
"/"
{("+"|"-") WS §term}
("+"|"-") WS §term
"+"|"-"
"+"
"-""""

test "traversal":
  var s: seq[string]
  # for p in arithmetic.descendants():
  #   s.add(if p.name.len > 0:  $p.name & " := " & $p  else:  $p)
  # arithmetic.resetTraversalTracker()
  arithmetic.forEach(p, refdSubs):
    s.add(if p.name.len > 0:  $p.name & " := " & $p  else:  $p)
  var traversalOutput = s.join("\n")
  check traversalOutput == traversalExpected


