{.experimental: "strictNotNil".} 
{.experimental: "callOperator".}

import std/strformat
import std/strutils

import nodetree


type
  ParsingResult = tuple[node: NodeOrNil, location: int]
  ParseProc = proc(parser: Parser, location: int): ParsingResult
  Parser* = ref ParserObj not nil
  ParserObj = object of RootObj
    name: string
    nodeName: string
    parserType: string
    disposable: bool
    dropContent: bool
    eqClass: int
    grammar: GrammarRef
    symbol: string
    parseProxy: ParseProc not nil

  # the GrammarObj
  GrammarRef* = ref GrammarObj not nil
  GrammarObj = object of RootObj
    name: string
    document: string


let grammarPlaceholderSingleton = GrammarRef(name: "Placeholder")


proc `$`*(r: ParsingResult): string =
  let tree = $r.node
  if tree.find('\n') < 0:
    return fmt"node: {tree}, location: {r.location}"
  else:
    return fmt"node:\n{tree}\nlocation: {r.location}"


method parse*(parser: Parser, location: int): ParsingResult {.base.} =
  echo "Parser.parse"
  result = (nil, 0)


proc callParseMethod(parser: Parser, location: int): ParsingResult =
  return parser.parse(location)


proc init*(parser: Parser, ptype: string = ":Parser"): Parser =
  assert ptype != "" and ptype[0] == ':'

  parser.name = ""
  parser.nodeName = ptype
  parser.parserType = ptype
  parser.disposable = true
  parser.dropContent = false
  parser.grammar = grammarPlaceholderSingleton
  parser.symbol = ""
  parser.parseProxy = callParseMethod
  return parser

proc assignName*(name: string, parser: Parser): Parser =
  assert parser.name == ""
  assert name != ""

  parser.nodeName = name
  if name[0] == ':':
    parser.name = name[1 .. ^1]
  else:
    parser.disposable = false
    parser.name = name
  return parser

proc `()`*(parser: Parser, location: int): ParsingResult =
  # is this faster than simply calling parser.parseProxy?
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)


proc `()`*(parser: Parser, document: string, location: int = 0): ParsingResult =
  parser.grammar = GrammarRef(name: "adhoc", document: document)
  if parser.parseProxy == callParseMethod:
    return parser.parse(location)
  else:
    return parser.parseProxy(parser, location)







type
  TextRef = ref TextObj not nil
  TextObj = object of ParserObj
      text: string
      length: int

proc init*(textParser: TextRef, text: string): TextRef =
  discard Parser(textParser).init(":Text")
  textParser.text = text
  textParser.length = text.len
  return textParser

proc Text*(text: string): TextRef =
  return new(TextRef).init(text)

method parse(parser: TextRef, location: int): ParsingResult =
  if parser.grammar.document.continuesWith(parser.text, location):
    if parser.dropContent:
      return (EMPTY_NODE, location + parser.length)
    elif parser.text != "" or not parser.disposable:
      return (newNode(parser.nodeName, parser.text), location + parser.length)
    return (EMPTY_NODE, location)
  return (nil, location)



## Test-code


let
  t = "A".assignName Text("A")
#  t = new(Text).initText("A")
let cst = t("A")
echo $cst






