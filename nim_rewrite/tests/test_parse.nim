# unit-tests for the parse.nim module
# To run these tests, simply execute `nimble test`.

import std/[unittest, strutils, unicode, algorithm, strformat]

import nimparser/runesets
import nimparser/strslice
import nimparser/error
import nimparser/nodetree
import nimparser/parse

test "Text, simple test":
  check Text("A")("A").root.asSxpr == "(:Text \"A\")"

test "CharRange":
  let rr: seq[RuneRange] = @[rr"2-4", rr"ä-ü", rr"b-d"]
  check CharRange(RC(false, rr))("ö").root.asSxpr == "(:CharRange \"ö\")"
  let GermanAlphabet = "GermanAlphabet" ::= cr"([A-Z]|[a-z]|[ÄÖÜäöüß])+"
  assert $GermanAlphabet == r"[A-Za-z\xC4\xD6\xDC\xDF\xE4\xF6\xFC]+"
  assert GermanAlphabet("abeäßüÜXYZ").root.asSxpr == "(GermanAlphabet \"abeäßüÜXYZ\")"
  assert GermanAlphabet("Hunde-Hütte").root.asSxpr == "(GermanAlphabet \"Hunde\")"

  let GermanAlphabet2 = "GermanAlphabet" ::= +(cr"[A-Z]" + cr"[ßüöäÜÖÄ]" + cr"[a-z]")
  assert $GermanAlphabet2 == r"[A-Za-z\xC4\xD6\xDC\xDF\xE4\xF6\xFC]+"
  assert $(cr"A-Z" - cr"X") == "[A-WY-Z]"
  assert $(*(cr"[A-Z]" - cr"X")) == "[A-WY-Z]*"
  let char = "Char" ::= cr"[A-Z]"
  let special = *(char - cr"X")
  assert $special == "[A-WY-Z]*"

  let NameStartChar = "NameStartChar" ::= cr("""[_]|[:]|[A-Z]|[a-z]
                                             |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                             |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                             |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                             |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                             |[\U00010000-\U000EFFFF]""")
  assert $NameStartChar == r"[\x3AA-Z\x5Fa-z\xC0-\xD6\xD8-\xF6\u00F8-\u02FF\u0370-\u037D\u037F-\u1FFF\u200C-\u200D\u2070-\u218F\u2C00-\u2FEF\u3001-\uD7FF\uF900-\uFDCF\uFDF0-\uFFFD\U00010000-\U000EFFFF]"
  let NameChars    = "NameChars" ::=    cr"""([_:.-]|[A-Z]|[a-z]|[0-9]
                                             |[\u00B7]|[\u0300-\u036F]|[\u203F-\u2040]
                                             |[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]
                                             |[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]
                                             |[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]
                                             |[\uF900-\uFDCF]|[\uFDF0-\uFFFD]
                                             |[\U00010000-\U000EFFFF])+"""
  assert NameChars("-.:_").root.asSxpr == "(NameChars \"-.:_\")"
  let numbers = cr"[0-9]+"
  assert $numbers == "[0-9]+"
  let check = cr("[^<&\"]+")
  assert $check == r"[^\x22\x26\x3C]+"
  var s = cr"\s"
  assert $s == r"[\x09-\x0A\x0C-\x0D\x20]"
  s = cr"\n"
  assert $s == r"[\x0A]"
  s = cr"[^<&\]]"
  assert $s == r"[^\x26\x3C\x5D]"
  # s = cr"[^]"

test "RegExp, simple test":
  check RegExp(rx"\w+")("ABC").root.asSxpr() == "(:RegExp \"ABC\")"

test "RegExp in sequence":
  let number = "number".assign RegExp(rx"\d+")
  let ws = "ws".assign RegExp(rx"\s*")
  let text = toStringSlice("1")
  check number(text, 0).root.asSxpr == "(number \"1\")"
  check ws(text, 1).root.asSxpr == "(ws \"\")"

test "Whitespace":
  let ws = ":ws".assign Whitespace(r"\s+", r"#.*")
  doAssert ws("   # comment").root.asSxpr == "(:ws \"   # comment\")"

test "Alternative":
  check Alternative(Text("A"), Text("B"))("B").root.asSxpr == "(:Text \"B\")"
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

# test "name-assignment":
#   let open = "HIDE:open" ::= DROP(txt"(")
#   let close = "close" ::= DROP(txt")")
#   let content = ":content" ::= cr"[a-z]+"
#   let document = txt"A" & open & content & close
#   echo $document
#   echo open.name & " " &  open.pname & " " & open.ptype & " " & open.nodeName[]
#   echo close.name & " " &  close.pname & " " & close.ptype & " " & close.nodeName[]
#   echo content.name & " " &  content.pname & " " & content.ptype & " " & content.nodeName[]
#   let text = document.subParsers[0]
#   echo text.name & "-" &  text.pname & "-" & text.ptype & "-" & text.nodeName[]

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

expression.errors(@[(anyPassage, "Zahl oder Ausdruck erwartet, aber nicht {1}")])
term.errors(@[(anyPassage, "Zahl oder Ausdruck (in Klammern) erwartet, aber nicht {1}")])
group.errors(@[(anyPassage, "Schließende Klammer erwartet, aber nicht {1}")])

test "arithmetic":
  var result = arithmetic("1 + 1")
  assert $result.root == """
(expression
  (term
    (factor "1"))
  (:Text "+")
  (term
    (factor "1")))"""

test "arithmetic error catching":
  var tree: NodeOrNil
  try:
    tree = expression("(3 + ) * 2").root
    check false
  except ParsingException as pe:
    check pe.error.message == "Zahl oder Ausdruck erwartet, aber nicht ») * 2«"
    check pe.error.pos == 5
  try:
    tree = expression("(3 + * 2").root
    check false
  except ParsingException as pe:
    check pe.error.message == "Zahl oder Ausdruck erwartet, aber nicht »* 2«"
    check pe.error.pos == 5
  try:
    tree = expression("(3 + 4 * 2").root
    check false
  except ParsingException as pe:
    check pe.error.message == "Schließende Klammer erwartet, aber nicht EOF"
    check pe.error.pos == 10

test "arithmetic error resumption":
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

  expression.resume(atRe"(?=\d|\(|\)|$)")
  term.resume(atRe"(?=\d|\(|$)")
  group.resume(atRe"(?=\)|$)")

  var tree: NodeOrNil

  try:
    tree = expression("(3 + ) * 2").root
    check $expression.grammar.errors == "@[?:5:1010:term expected by parser expression, but ») * 2« found!]"
  except ParsingException as pe:
    check false
  try:
    tree = expression("(3 + * 2").root
    check $expression.grammar.errors == "@[?:5:1010:term expected by parser expression, but »* 2« found!, ?:7:1010:\")\" expected by parser group, but »2« found!]"
  except ParsingException as pe:
    check false
  try:
    tree = expression("(3 + 4 * 2").root
    check $expression.grammar.errors == "@[?:10:1010:\")\" expected by parser group, but EOF found!]"
  except ParsingException as pe:
    check false

  try:
    tree = expression("3 + * 2").root
    check expression.grammar.errors.len == 2
    check expression.grammar.errors[1].code == ParserStoppedBeforeEnd
  except ParsingException as pe:
    check false

  let gap = ":gap".assign(rxp"[^\d()]*(?=[\d(])")
  expression.skipUntil(after(gap))

  try:
    tree = expression("3 + * 2").root
    check expression.grammar.errors.len == 1
  except ParsingException as pe:
    check false


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


